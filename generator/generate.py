#!/usr/bin/env python3
import os
import sys
import json
import re
from SteamworksParser import steamworksparser

g_csharptypemap = {
	'uint32': 'uint',
	'const char *': 'string'
}

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
		self.csharp_variables = []
		self.csharp_variablesdisplay = []
		self.csharp_onenablecode = []

	def LoadConfig(self, configDir):
		with open(configDir + self.interfacename + ".json") as stream:
			self.config = json.load(stream)

	def ParseVariables(self):
		self.ParseVariablesCSharp()

	def ParseVariablesCSharp(self):
		if "variables" in self.config:
			self.csharp_variablesdisplay.append('GUILayout.BeginArea(new Rect(Screen.width - 120, 0, 120, Screen.height));')
			self.csharp_variablesdisplay.append('GUILayout.Label("Variables:");')
			for var in self.config["variables"]:
				self.csharp_variables.append('private {0} {1};'.format(var[0], var[1]))
				self.csharp_variablesdisplay.append('GUILayout.Label("{0}: " + {0});'.format(var[1]))
			self.csharp_variablesdisplay.append('GUILayout.EndArea();')

	def ParseOnEnableCode(self):
		if 'onenablecode' in self.config:
			self.csharp_onenablecode.extend(self.config['onenablecode'])

	def ParseCallbacks(self, callbacks):
		for callback in callbacks:
			if 'callresults' in self.config and callback.name in self.config['callresults']:
				self.ParseCallResultCSharp(callback)
			else:
				self.ParseCallbackCSharp(callback)

	def ParseCallResultCSharp(self, callresult):
		self.csharp_callresultdecl.append('private CallResult<{0}> On{1}CallResult;'.format(callresult.name, callresult.name[:-2]))
		self.csharp_callresultcreation.append('On{1}CallResult = CallResult<{0}>.Create(On{1});'.format(callresult.name, callresult.name[:-2]))

		self.ParseCallbackCallResultFields(callresult, True)

	def ParseCallbackCSharp(self, callback):
		self.csharp_callbackdecl.append('protected Callback<{0}> m_{1};'.format(callback.name, callback.name[:-2]))
		self.csharp_callbackcreation.append('m_{1} = Callback<{0}>.Create(On{1});'.format(callback.name, callback.name[:-2]))

		self.ParseCallbackCallResultFields(callback, False)

	def ParseCallbackCallResultFields(self, callback, bCallResult):
		if callback.fields:
			fields = ' - " + pCallback.'
			fields += ' + " -- " + pCallback.'.join([x.name for x in callback.fields])
		else:
			fields = '"'

		callbackfunction = 'void On{1}({0} pCallback{2}) {{\n'.format(callback.name, callback.name[:-2], (', bool bIOFailure' if bCallResult else ''))
		callbackfunction += '\t\tDebug.Log("[" + {0}.k_iCallback + " - {1}]{2});\n'.format(callback.name, callback.name[:-2], fields)

		if 'callbacks' in self.config and callback.name in self.config['callbacks']:
			if 'customcode' in self.config['callbacks'][callback.name]:
				callbackfunction += '\n'
				for line in self.config['callbacks'][callback.name]['customcode']:
					callbackfunction += '\t\t' + line + '\n'

		callbackfunction += '\t}'

		self.csharp_callbacks.append(callbackfunction)

	def ParseFunctions(self, interface):
		if 'functions' not in self.config:
			print("[ERROR] {0} has no 'functions' block in the config!".format(self.interfacename))
			return

		numPrivateFunctions = 0
		for i, func in enumerate(interface.functions):
			if func.private:
				numPrivateFunctions += 1
				continue

			if i - numPrivateFunctions >= len(self.config['functions']):
				print("[ERROR] Function missing from the config: {0}".format(func.name))
				return

			funcconfig = self.config['functions'][i - numPrivateFunctions]
			if func.name != funcconfig['name']:
				print("[ERROR] Function missmatch, expected: {0} but got {1} instead!".format(func.name, funcconfig['name']))
				return

			self.ParseFunctionCSharp(func, funcconfig)

		if len(self.config['functions']) != len(interface.functions) - numPrivateFunctions:
			print("[WARNING] The number of functions in the config does not match the number of non private functions in the interface. Interface: {0}, Config: {1}".format(len(interface.functions) - numPrivateFunctions, len(self.config['functions'])))

	def ParseFunctionCSharp(self, func, funcconfig):
		label = funcconfig.get('label', False)

		args = ''
		guiargs = ''
		printargs = ''
		if 'args' in funcconfig:
			args += ', '.join(funcconfig['args'])
			guiargs += ', '.join([x.replace('"', '\\"') for x in funcconfig['args']])
			printargs += '" + '
			printargs += ' + ", " + '.join([('"\\"' + x.strip('"') + '\\""' if x.startswith('"') else x) for x in funcconfig['args']])
			printargs += ' + "'

		precall = ''
		if 'precall' in funcconfig:
			for elem in funcconfig['precall']:
				precall += '\t\t\t' + elem + '\n'

		postcall = ''
		if 'postcall' in funcconfig:
			for elem in funcconfig['postcall']:
				postcall += '\t\t\t' + elem + '\n'

		postprint = ''
		if 'postprint' in funcconfig:
			for elem in funcconfig['postprint']:
				postprint += '\t\t\t' + elem + '\n'

		override = ''
		if 'override' in funcconfig:
			for elem in funcconfig['override']:
				override = '\n\t\t'.join(funcconfig['override'])

		printadditional = '"'
		if func.returntype != 'void':
			ret = g_csharptypemap.get(func.returntype, func.returntype) + ' ret = '
			printadditional = ' : " + ret'
		else:
			ret = ''

		if 'outargs' in funcconfig:
			for elem in funcconfig['outargs']:
				precall += '\t\t\t' + elem[0] + ' ' + elem[1] + ';\n'
				printadditional += ' + " -- " + ' + elem[1]

		function = ''
		if override:
			function += override
		elif label:
			if precall or postcall:
				function += '{\n'
				function += precall
				function += '\t\t\t{1}{0}.{2}({3});\n'.format(self.interfacename, ret, func.name, args)
				function += postcall
				function += '\t\t\tGUILayout.Label("{0}({1}){2});\n'.format(func.name, guiargs, printadditional)
				function += postprint
				function += '\t\t}'
			else:
				function += 'GUILayout.Label("{1}({2}) : " + {0}.{1}({2}));'.format(self.interfacename, func.name, guiargs)
		else:
			function += 'if (GUILayout.Button("{0}({1})")) {{\n'.format(func.name, guiargs)
			function += precall
			function += '\t\t\t{1}{0}.{2}({3});\n'.format(self.interfacename, ret, func.name, args)
			function += postcall
			function += '\t\t\tprint("{0}.{1}({2}){3});\n'.format(self.interfacename, func.name, printargs, printadditional)
			function += postprint
			function += '\t\t}'
		self.csharp_functions.append(function)

def OutputCSharpFile(outputDir, state):
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

	template = ReplaceTemplate(template, '[[INTERFACENAME]]', state.interfacename)

	template = ReplaceTemplate(template, '[[ONENABLECODE]]', '\n\t\t'.join(state.csharp_onenablecode) + '\n')

	template = ReplaceTemplate(template, '[[VARIABLES]]', '\n\t'.join(state.csharp_variables) + '\n')
	template = ReplaceTemplate(template, '[[VARIABLESDISPLAY]]', '\n\t\t'.join(state.csharp_variablesdisplay) + '\n')

	template = ReplaceTemplate(template, '[[CALLBACKDECL]]', '\n\t'.join(state.csharp_callbackdecl) + '\n')
	template = ReplaceTemplate(template, '[[CALLBACKCREATION]]', '\n\t\t'.join(state.csharp_callbackcreation) + ('\n' if state.csharp_callresultcreation else ''))
	template = ReplaceTemplate(template, '[[CALLBACKS]]', '\n\n\t'.join(state.csharp_callbacks))

	template = ReplaceTemplate(template, '[[CALLRESULTDECL]]', '\n\t'.join(state.csharp_callresultdecl) + '\n')
	template = ReplaceTemplate(template, '[[CALLRESULTCREATION]]', '\n\t\t'.join(state.csharp_callresultcreation))

	template = ReplaceTemplate(template, '[[FUNCTIONS]]', '\n\n\t\t'.join(state.csharp_functions))

	with open(outputDir + state.interfacename + 'Test.cs', 'w') as out:
		out.write(template)

def main(parser, configDir, outputDir):
	for f in parser.files:
		if f.name not in ['isteamapplist.h', 'isteamapps.h', 'isteamclient.h', 'isteamscreenshots.h', 'isteamuser.h', 'isteamutils.h', 'isteamvideo.h']:
			continue

		print("[INFO] Opening: {}".format(f.name))

		state = State()

		for interface in f.interfaces:
			print("[INFO] Parsing Interface: {}".format(interface.name))
			state.interfacename = interface.name[1:]
			state.LoadConfig(configDir)
			state.ParseVariables()
			state.ParseOnEnableCode()
			state.ParseFunctions(interface)

		state.ParseCallbacks(f.callbacks)

		if f.interfaces:
			OutputCSharpFile(outputDir, state)

if __name__ == '__main__':
	if len(sys.argv) != 4:
		print(' generate.py "path/to/sdk/public/steam" "configDir/" "outputDir/"')
		exit()

	steamSDKPath = sys.argv[1]
	configDir = sys.argv[2]
	outputDir = sys.argv[3]
	main(steamworksparser.parse(steamSDKPath), configDir, outputDir)