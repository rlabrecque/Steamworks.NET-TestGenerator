import os
import sys
import json
from SteamworksParser import steamworksparser

g_csharptypemap = {
	'uint32': 'uint',
}

class State:
	def __init__(self):
		self.config = None
		self.interfacename = ''
		self.csharp_callbackdecl = []
		self.csharp_callbackcreation = []
		self.csharp_callbacks = []
		self.csharp_functions = []
		self.csharp_variables = []
		self.csharp_variablesdisplay = []
		self.csharp_onenablecode = []

	def LoadConfig(self):
		with open("configs/" + self.interfacename + ".json") as stream:
			self.config = json.load(stream)

	def ParseVariables(self):
		self.ParseVariablesCSharp()

	def ParseVariablesCSharp(self):
		if "variables" in self.config:
			for var in self.config["variables"]:
				self.csharp_variables.append('private {0} {1};'.format(var[0], var[1]))
				self.csharp_variablesdisplay.append('GUILayout.Label("{0}: " + {0});'.format(var[1]))

	def ParseOnEnableCode(self):
		if 'onenablecode' in self.config:
			self.csharp_onenablecode.extend(self.config['onenablecode'])

	def ParseCallbackCSharp(self, callback):
		self.csharp_callbackdecl.append('protected Callback<{0}> m_{1};'.format(callback.name, callback.name[:-2]))
		self.csharp_callbackcreation.append('m_{1} = Callback<{0}>.Create(On{1});'.format(callback.name, callback.name[:-2]))

		if callback.fields:
			fields = ' - " + pCallback.'
			fields += ' + " -- " + pCallback.'.join([x.name for x in callback.fields])
		else:
			fields = '"'

		callbackfunction = 'void On{1}({0} pCallback) {{\n'.format(callback.name, callback.name[:-2])
		callbackfunction += '\t\tDebug.Log("[" + {0}.k_iCallback + " - {1}]{2});\n'.format(callback.name, callback.name[:-2], fields)
		callbackfunction += '\t}'
		self.csharp_callbacks.append(callbackfunction)

	def ParseFunctionCSharp(self, func):
		label = False
		args = ''
		guiargs = ''
		printargs = ''
		precall = ''
		postcall = ''
		printadditional = '"'

		if func.returntype != 'void':
			ret = g_csharptypemap.get(func.returntype, func.returntype) + ' ret = '
			printadditional = ' : " + ret'
		else:
			ret = ''

		if 'functions' in self.config and func.name in self.config['functions']:
			funcconfig = self.config['functions'][func.name]
			label = funcconfig.get('label', False)
			if 'args' in funcconfig:
				args += ', '.join(funcconfig['args'])
				guiargs += ', '.join([x.replace('"', '\\"') for x in funcconfig['args']])
				printargs += '" + '
				printargs += ' + ", " + '.join(funcconfig['args'])
				printargs += ' + "'
			if 'precall' in funcconfig:
				for elem in funcconfig['precall']:
					precall += '\t\t\t' + elem + '\n'
			if 'postcall' in funcconfig:
				for elem in funcconfig['postcall']:
					postcall += '\t\t\t' + elem + '\n'
			if 'outargs' in funcconfig:
				for elem in funcconfig['outargs']:
					precall += '\t\t\t' + elem[0] + ' ' + elem[1] + ';\n'
					printadditional += ' + " -- " + ' + elem[1]

		function = ''
		if label:
			if precall or postcall:
				function += '{\n'
				function += precall
				function += '\t\t\t{1}{0}.{2}({3});\n'.format(self.interfacename, ret, func.name, args)
				function += '\t\t\tGUILayout.Label("{0}({1}){2});\n'.format(func.name, guiargs, printadditional)
				function += postcall
				function += '\t\t}'
			else:
				function += 'GUILayout.Label("{1}({2}) : " + {0}.{1}({2}));\n'.format(self.interfacename, func.name, guiargs)
		else:
			function += 'if (GUILayout.Button("{0}({1})")) {{\n'.format(func.name, guiargs)
			function +=  precall
			function += '\t\t\t{1}{0}.{2}({3});\n'.format(self.interfacename, ret, func.name, args)
			function += '\t\t\tprint("{0}.{1}({2}){3});\n'.format(self.interfacename, func.name, printargs, printadditional)
			function +=  postcall
			function += '\t\t}'
		self.csharp_functions.append(function)

def main(parser, outputDir):
	for f in parser.files:
		if f.name != 'isteamscreenshots.h' and f.name != 'isteamapplist.h': # and f.name != 'isteamapps.h':
			continue

		state = State()

		for interface in f.interfaces:
			state.interfacename = interface.name[1:]
			state.LoadConfig()
			state.ParseVariables()
			state.ParseOnEnableCode()

			for func in interface.functions:
				if func.private:
					continue

				state.ParseFunctionCSharp(func)

		for callback in f.callbacks:
			state.ParseCallbackCSharp(callback)

		if f.interfaces:
			OutputCSharpFile(outputDir, state)

def OutputCSharpFile(outputDir, state):
	with open('template_csharp.txt', 'r') as stream:
		template = stream.read()

	template = template.replace('[[INTERFACENAME]]', state.interfacename)

	template = template.replace('[[ONENABLECODE]]', '\n\t\t'.join(state.csharp_onenablecode))

	template = template.replace('[[VARIABLES]]', '\n\t'.join(state.csharp_variables))
	template = template.replace('[[VARIABLESDISPLAY]]', '\n\t\t'.join(state.csharp_variablesdisplay))

	template = template.replace('[[CALLBACKDECL]]', '\n\t'.join(state.csharp_callbackdecl))
	template = template.replace('[[CALLBACKCREATION]]', '\n\t\t'.join(state.csharp_callbackcreation))
	template = template.replace('[[CALLBACKS]]', '\n\n\t'.join(state.csharp_callbacks))

	template = template.replace('[[FUNCTIONS]]', '\n\n\t\t'.join(state.csharp_functions))

	with open(outputDir + state.interfacename + 'Test.cs', 'w') as out:
		out.write(template)

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('TODO: Usage Instructions')
        exit()

    main(steamworksparser.parse(sys.argv[1]), sys.argv[2])