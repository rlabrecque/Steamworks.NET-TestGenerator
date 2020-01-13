#!/usr/bin/env python3

import os
import sys
import json
from SteamworksParser import steamworksparser

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_warning(msg):
	print(bcolors.WARNING + "[WARNING] " + msg + bcolors.ENDC)

def print_error(msg):
	print(bcolors.FAIL + "[ERROR] " + msg + bcolors.ENDC)

g_skippedfiles = (
	"isteamappticket.h",
	"isteamgamecoordinator.h"
)

g_csharptypemap = {
	'uint32': 'uint',
	'int32': 'int',
	'const char *': 'string',
	'gameserveritem_t *': 'gameserveritem_t',
	'void *': 'System.IntPtr'
}

g_skipScroll = (
	'SteamHTMLSurface'
)

class State:
	def __init__(self):
		self.config = None
		self.interfacename = ''
		self.csharp_callbackdecl = []
		self.csharp_callbackcreation = []
		self.csharp_callbacks = []
		self.csharp_callresultdecl = []
		self.csharp_callresultcreation = []
		self.csharp_functions = []
		self.csharp_constants = []
		self.csharp_variables = []
		self.csharp_variablesdisplay = []
		self.csharp_onenablecode = []
		self.csharp_extrafunctions = []

	def LoadConfig(self, configDir):
		try:
			with open(configDir + self.interfacename + ".json") as stream:
				self.config = json.load(stream)
			return True
		except OSError:
			return False

	def ParseConstants(self):
		if 'constants' in self.config:
			for var in self.config['constants']:
				self.csharp_constants.append('const {0} {1} = {2};'.format(var[0], var[1], var[2]))

	def ParseVariables(self):
		if self.interfacename not in g_skipScroll:
			self.csharp_variables.append('private Vector2 m_ScrollPos;')

		if 'variables' in self.config:
			self.csharp_variablesdisplay.append('GUILayout.BeginArea(new Rect(Screen.width - 200, 0, 200, Screen.height));')
			self.csharp_variablesdisplay.append('GUILayout.Label("Variables:");')
			for var in self.config['variables']:
				self.csharp_variables.append('private {0} {1};'.format(var[0], var[1]))

				# Does this variable need to have it's variable drawn on a seperate line from the name?
				if len(var) == 3:
					self.csharp_variablesdisplay.append('GUILayout.Label("{0}:");'.format(var[1]))
					self.csharp_variablesdisplay.append('{0}'.format(var[2]))
				else:
					self.csharp_variablesdisplay.append('GUILayout.Label("{0}: " + {0});'.format(var[1]))

			self.csharp_variablesdisplay.append('GUILayout.EndArea();')

	def ParseOnEnableCode(self):
		if 'onenablecode' in self.config:
			for i, elem in enumerate(self.config['onenablecode']):
				indent = ('' if i == 0 or not elem else '\t\t')
				self.csharp_onenablecode.append(indent + elem + '\n')

	def ParseExtraFunctions(self):
		if 'extrafunctions' in self.config:
			for i, elem in enumerate(self.config['extrafunctions']):
				indent = ('' if i == 0 or not elem else '\t')
				self.csharp_extrafunctions.append(indent + elem + '\n')

	def ParseCallbacks(self, callbacks):
		for callback in callbacks:
			skipMessage = ''

			# Skip callbacks for other interfaces when multiple interfaces are in the same file.
			if 'callbackid' in self.config:
				if self.config['callbackid'] not in callback.callbackid:
					continue

			if 'callbacks' in self.config and callback.name in self.config['callbacks']:
				if 'skip' in self.config['callbacks'][callback.name]:
					if self.config['callbacks'][callback.name]['skip'] == True:
						return

					skipMessage = ' // ' + self.config['callbacks'][callback.name]['skip']

				if 'both' in self.config['callbacks'][callback.name]:
					self.ParseCallbackCSharp(callback, skipMessage)
					self.ParseCallResultCSharp(callback, skipMessage)
					continue

			if 'callresults' in self.config and callback.name in self.config['callresults']:
				self.ParseCallResultCSharp(callback, skipMessage)
			else:
				self.ParseCallbackCSharp(callback, skipMessage)

	def ParseCallResultCSharp(self, callresult, skipMessage):
		self.csharp_callresultdecl.append('{2}private CallResult<{0}> On{1}CallResult;'.format(callresult.name, callresult.name[:-2], '//' if skipMessage else ''))
		self.csharp_callresultcreation.append('{2}On{1}CallResult = CallResult<{0}>.Create(On{1});{3}'.format(callresult.name, callresult.name[:-2], '//' if skipMessage else '', skipMessage))

		self.ParseCallbackCallResultFields(callresult, True, '//' if skipMessage else '')

	def ParseCallbackCSharp(self, callback, skipMessage):
		self.csharp_callbackdecl.append('{2}protected Callback<{0}> m_{1};'.format(callback.name, callback.name[:-2], '//' if skipMessage else ''))
		self.csharp_callbackcreation.append('{2}m_{1} = Callback<{0}>.Create(On{1});{3}'.format(callback.name, callback.name[:-2], '//' if skipMessage else '', skipMessage))

		self.ParseCallbackCallResultFields(callback, False, '//' if skipMessage else '')

	def ParseCallbackCallResultFields(self, callback, bCallResult, skip):
		if callback.fields:
			fields = ' - " + pCallback.'
			fields += ' + " -- " + pCallback.'.join([x.name for x in callback.fields])
		else:
			fields = '"'

		callbackfunction = '{3}void On{1}({0} pCallback{2}) {{\n'.format(callback.name, callback.name[:-2], (', bool bIOFailure' if bCallResult else ''), skip)
		callbackfunction += '\t{3}\tDebug.Log("[" + {0}.k_iCallback + " - {1}]{2});\n'.format(callback.name, callback.name[:-2], fields, skip)

		if 'callbacks' in self.config and callback.name in self.config['callbacks']:
			if 'customcode' in self.config['callbacks'][callback.name]:
				callbackfunction += '{0}\n'.format(skip)
				for line in self.config['callbacks'][callback.name]['customcode']:
					callbackfunction += ('\t\t{0}'.format(skip) if line else '{0}'.format(skip)) + line + '\n'

		callbackfunction += '\t{0}}}'.format(skip)

		self.csharp_callbacks.append(callbackfunction)

	def ParseFunctions(self, interface):
		if 'functions' not in self.config:
			print_error("{0} has no 'functions' block in the config!".format(self.interfacename))
			return

		if self.interfacename not in g_skipScroll:
			self.csharp_functions.append('\t\tGUILayout.BeginVertical("box");')
			self.csharp_functions.append('\t\tm_ScrollPos = GUILayout.BeginScrollView(m_ScrollPos, GUILayout.Width(Screen.width - 215), GUILayout.Height(Screen.height - 33));\n')

		numPrivateFunctions = 0
		indentLevel = 2
		for i, func in enumerate(interface.functions):
			if func.private:
				numPrivateFunctions += 1
				continue

			curFunctionIndex = i - numPrivateFunctions

			if curFunctionIndex >= len(self.config['functions']):
				print_error("Function missing from the config: {0}".format(func.name))
				return

			funcconfig = self.config['functions'][curFunctionIndex]
			if func.name != funcconfig['name']:
				print_error("Function missmatch, expected: {0} but got {1} instead!".format(func.name, funcconfig['name']))
				return

			if 'indent' in funcconfig:
				indentLevel += funcconfig['indent']

			function = self.ParseFunctionCSharp(func, funcconfig, indentLevel)
			self.csharp_functions.append(function)

		if self.interfacename not in g_skipScroll:
			self.csharp_functions.append('\t\tGUILayout.EndScrollView();')
			self.csharp_functions.append('\t\tGUILayout.EndVertical();')

		if len(self.config['functions']) != len(interface.functions) - numPrivateFunctions:
			print_warning("The number of functions in the config does not match the number of non private functions in the interface. Interface: {0}, Config: {1}".format(len(interface.functions) - numPrivateFunctions, len(self.config['functions'])))

	def ParseFunctionCSharp(self, func, funcconfig, indentLevel):
		args = ''
		guiargs = ''
		printargs = ''
		if 'args' in funcconfig:
			args += ', '.join(funcconfig['args'])
			guiargs += ', '.join([x.replace('"', '\\"') for x in funcconfig['args']])
			printargs += '" + '
			printargs += ' + ", " + '.join([('"\\"' + x.strip('"') + '\\""' if x.startswith('"') else '"{}"'.format(x) if x.startswith('out') or x.startswith('ref') else x) for x in funcconfig['args']])
			printargs += ' + "'

		indent = '\t' * indentLevel

		preindent = ''
		if 'preindent' in funcconfig:
			oldIndentLevel = indentLevel
			if 'indent' in funcconfig:
				oldIndentLevel = indentLevel - funcconfig['indent']

			oldIndentStr = '\t' * oldIndentLevel

			for elem in funcconfig['preindent']:
				preindent += oldIndentStr + elem + '\n'

		postindent = ''
		if 'postindent' in funcconfig:
			oldIndentLevel = indentLevel
			if 'indent' in funcconfig:
				oldIndentLevel = indentLevel - funcconfig['indent']

			oldIndentStr = '\t' * oldIndentLevel

			for elem in funcconfig['postindent']:
				postindent += oldIndentStr + elem + '\n'

		prebutton = ''
		if 'prebutton' in funcconfig:
			for elem in funcconfig['prebutton']:
				if elem:
					prebutton += indent + elem + '\n'
				else:
					prebutton += '\n'

		postbutton = ''
		if 'postbutton' in funcconfig:
			for elem in funcconfig['postbutton']:
				if elem:
					postbutton += indent + elem + '\n'
				else:
					postbutton += '\n'

		precall = ''
		if 'precall' in funcconfig:
			for elem in funcconfig['precall']:
				if elem:
					precall += indent + '\t' + elem + '\n'
				else:
					precall += '\n'

		postcall = ''
		if 'postcall' in funcconfig:
			for elem in funcconfig['postcall']:
				if elem:
					postcall += indent + '\t' + elem + '\n'
				else:
					postcall += '\n'

		postprint = ''
		if 'postprint' in funcconfig:
			for elem in funcconfig['postprint']:
				if elem:
					postprint += indent + '\t' + elem + '\n'
				else:
					postprint += '\n'

		if 'override' in funcconfig:
			function = ''
			for elem in funcconfig['override']:
				if elem:
					function += indent + elem + '\n'
				else:
					function += '\n'

			return function

		if funcconfig.get('skip', False):
			function = ''
			function += prebutton
			function += precall
			function += indent + "//{0}.{1}() // {2}\n".format(self.interfacename, func.name, funcconfig['skip'])
			function += postcall
			function += postprint
			function += postbutton
			return function

		printadditional = '"'
		if func.returntype == 'void':
			ret = ''
		elif 'returnname' in funcconfig:
			returnname = funcconfig['returnname']
			ret = returnname + ' = '
			printadditional = ' : " + ' + returnname
		elif func.returntype == 'SteamAPICall_t':
			ret = g_csharptypemap.get(func.returntype, func.returntype) + ' handle = '
			printadditional = ' : " + handle'

			for attrib in func.attributes:
				if attrib.name == 'STEAM_CALL_RESULT':
					postcall += indent + '\t' + 'On' + attrib.value[:-2] + 'CallResult.Set(handle);' + '\n'
					break
			else:
				print_warning('Function {} returns a SteamAPICall_t but does not have attrib STEAM_CALL_RESULT!'.format(func.name))
		elif func.returntype.startswith("ISteam"):
			ret = 'System.IntPtr ret = '
			printadditional = ' : " + ret'
		else:
			ret = g_csharptypemap.get(func.returntype, func.returntype) + ' ret = '
			printadditional = ' : " + ret'

		bHasOutArgs = False
		if 'args' in funcconfig:
			for elem in funcconfig['args']:
				if elem.startswith('out') or elem.startswith('ref'):
					bHasOutArgs = True
					printadditional += ' + " -- " + ' + elem.lstrip('out ').lstrip('ref ')

		if 'outargs' in funcconfig:
			for elem in funcconfig['outargs']:
				precall += indent + '\t' + elem[0] + ' ' + elem[1] + ';\n'

		function = ''
		if funcconfig.get('label', False):
			if precall or postcall or 'returnname' in funcconfig or bHasOutArgs:
				function += preindent
				function += prebutton
				function += indent + '{\n'
				function += precall
				function += indent + '\t{1}{0}.{2}({3});\n'.format(self.interfacename, ret, func.name, args)
				function += postcall
				function += indent + '\tGUILayout.Label("{0}({1}){2});\n'.format(func.name, guiargs, printadditional)
				function += postprint
				function += indent + '}\n'
				function += postbutton
				function += postindent
			else:
				function += preindent
				function += prebutton
				function += precall
				function += indent + 'GUILayout.Label("{1}({2}) : " + {0}.{1}({3}));\n'.format(self.interfacename, func.name, guiargs, args)
				function += postcall
				function += postprint
				function += postbutton
				function += postindent
		else:
			function += preindent
			function += prebutton
			function += indent + 'if (GUILayout.Button("{0}({1})")) {{\n'.format(func.name, guiargs)
			function += precall
			function += indent + '\t{1}{0}.{2}({3});\n'.format(self.interfacename, ret, func.name, args)
			function += postcall
			function += indent + '\tprint("{0}.{1}({2}){3});\n'.format(self.interfacename, func.name, printargs, printadditional)
			function += postprint
			function += indent + '}\n'
			function += postbutton
			function += postindent

		return function

	def OutputCSharpFile(self, outputDir):
		def ReplaceTemplate(template, placeholderString, newString):
			if len(newString.strip()) == 0:
				splitlines = template.splitlines()
				for i, line in enumerate(splitlines):
					if placeholderString in line:
						splitlines.remove(line)
				return '\n'.join(splitlines)

			return template.replace(placeholderString, newString)

		try:
			os.mkdir(outputDir)
		except:
			pass

		with open('template_csharp.txt', 'r') as stream:
			template = stream.read()

		template = ReplaceTemplate(template, '[[INTERFACENAME]]', self.interfacename)

		template = ReplaceTemplate(template, '[[ONENABLECODE]]', ''.join(self.csharp_onenablecode))

		template = ReplaceTemplate(template, '[[EXTRAFUNCTIONS]]', ''.join(self.csharp_extrafunctions))

		template = ReplaceTemplate(template, '[[CONSTANTS]]', '\n\t'.join(self.csharp_constants) + '\n')

		template = ReplaceTemplate(template, '[[VARIABLES]]', '\n\t'.join(self.csharp_variables) + '\n')
		template = ReplaceTemplate(template, '[[VARIABLESDISPLAY]]', '\n\t\t'.join(self.csharp_variablesdisplay) + '\n')

		template = ReplaceTemplate(template, '[[CALLBACKDECL]]', '\n\t'.join(self.csharp_callbackdecl) + '\n')
		template = ReplaceTemplate(template, '[[CALLBACKCREATION]]', '\n\t\t'.join(self.csharp_callbackcreation) + ('\n' if self.csharp_callresultcreation else ''))
		template = ReplaceTemplate(template, '[[CALLBACKS]]', '\n\n\t'.join(self.csharp_callbacks))

		template = ReplaceTemplate(template, '[[CALLRESULTDECL]]', '\n\t'.join(self.csharp_callresultdecl) + '\n')
		template = ReplaceTemplate(template, '[[CALLRESULTCREATION]]', '\n\t\t'.join(self.csharp_callresultcreation))

		template = ReplaceTemplate(template, '[[FUNCTIONS]]', '\n'.join(self.csharp_functions).rstrip('\n'))

		with open(outputDir + self.interfacename + 'Test.cs', 'w') as out:
			out.write(template)

def main(parser, configDir, outputDir):
	for f in parser.files:
		if f.name in g_skippedfiles:
			print("[INFO] Skipping: {}".format(f.name))
			continue

		print("[INFO] Opening: {}".format(f.name))

		for interface in f.interfaces:
			state = State()
			print("[INFO] Parsing Interface: {}".format(interface.name))
			state.interfacename = interface.name[1:]
			if not state.LoadConfig(configDir):
				print_warning("Interface config does not exist: {}.json".format(state.interfacename))
				continue
			state.ParseConstants()
			state.ParseVariables()
			state.ParseOnEnableCode()
			state.ParseExtraFunctions()
			state.ParseFunctions(interface)

			state.ParseCallbacks(f.callbacks)

			state.OutputCSharpFile(outputDir)

if __name__ == '__main__':
	if len(sys.argv) != 4:
		print(' generate.py "path/to/sdk/public/steam" "configDir/" "outputDir/"')
		exit()

	steamSDKPath = sys.argv[1]
	configDir = sys.argv[2]
	outputDir = sys.argv[3]
	main(steamworksparser.parse(steamSDKPath), configDir, outputDir)