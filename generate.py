import os
import sys
import yaml
from SteamworksParser import steamworksparser

def main(parser, outputDir):
	algamationinclude = []
	algamationdecl = []
	algamationinit = []
	algamationrunframe = []

	for f in parser.files:
		if f.name != "isteamscreenshots.h":
		#and f.name != "isteamutils.h":
			continue

		cppname = f.name[:-2] + ".cpp"
		algamationinclude.append("#include \"" + cppname + "\"")

		functionsOutput = []
		for interface in f.interfaces:
			classname = "CS" + interface.name[2:]
			globalname = "g_s" + interface.name[2:]

			algamationdecl.append(classname + " *" + globalname + ";")
			algamationinit.append("\t" + globalname + " = new " + classname + "();")
			algamationrunframe.append("\t" + globalname + "->RunFrame();")

			for func in interface.functions:
				if func.private:
					continue

				functionOutput = []

				functionOutput.append("\tif(ImGui::Button(\"" + func.name + "\")) {")
				functionOutput.append("\t\t" + interface.name[1:] + "()->" + func.name + "();")
				functionOutput.append("\t}")

				functionsOutput.append(functionOutput)


		callbackdecl = []
		callbackimpl = []
		for callback in f.callbacks:
			callbackdecl.append("\tSTEAM_CALLBACK(" + classname + ", On" + callback.name + ", " + callback.name + ");")
			impl = []
			impl.append("void " + classname + "::On" + callback.name + "(" + callback.name + " *pCallback) {")
			impl.append("\tPlayground_Print(\"" + callback.name + "\");")
			impl.append("}")
			callbackimpl.append(impl)

		with open(outputDir + cppname, "w") as out:
			print("#include \"renameme.h\"", file=out)
			print(file=out)
			print("class " + classname + " {", file=out)
			print("public:", file=out)
			#print("\t" + classname + "()", file=out)
			print("\tvoid RunFrame();", file=out)
			print(file=out)
			print("private:", file=out)

			for line in callbackdecl:
				print(line, file=out)

			print("};", file=out)
			print(file=out)
			print("void " + classname + "::RunFrame() {", file=out)
			print("\tImGui::SetNextWindowSize(ImVec2(1271, 527), ImGuiSetCond_Always);", file=out)
			print("\tImGui::SetNextWindowPos(ImVec2(3, 3), ImGuiSetCond_Always);", file=out)
			print("\tImGui::Begin(\"" + classname + "\");", file=out)

			for functionOutput in functionsOutput:
				for line in functionOutput:
					print(line, file=out)

			print("\tImGui::End();", file=out)
			print("}", file=out)
			print(file=out)

			for impl in callbackimpl:
				for line in impl:
					print(line, file=out)
				print(file=out)

	with open(outputDir + "algamation.cpp", "w") as out:
		for line in algamationinclude:
			print(line, file=out)

		print(file=out)

		for line in algamationdecl:
			print(line, file=out)

		print(file=out)
		print("void Gen_Init() {", file=out)
		
		for line in algamationinit:
			print(line, file=out)

		print("}", file=out)
		print(file=out)
		print("void Gen_RunFrame() {", file=out)	

		for line in algamationrunframe:
			print(line, file=out)

		print("}", file=out)

def ParseCallbacks():
	pass

def OutputCSharpFile(outputDir, ):

	with open(outputDir + "test", "w") as out:
		out.write()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("TODO: Usage Instructions")
        exit()

    main(steamworksparser.parse(sys.argv[1]), sys.argv[2])