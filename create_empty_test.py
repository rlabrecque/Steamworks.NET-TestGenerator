#!/usr/bin/env python3
import os
import sys
from SteamworksParser import steamworksparser

def main(parser, headerName, configDir):
	for f in parser.files:
		if f.name != headerName:
			continue

		if not f.interfaces:
			print("[ERROR] Header has no interfaces")
			return

		for interface in f.interfaces:
			with open(configDir + '/' + interface.name[1:] + '.json', 'w') as out:
				out.write('{\n')
				out.write('\t"functions":\n')
				out.write('\t[\n')
				for func in interface.functions:
					out.write('\t\t{\n')
					out.write('\t\t\t"name": "{}"\n'.format(func.name))
					out.write('\t\t},\n')
				out.write('\t]\n')
				out.write('}\n')

		print('Success!')
		return
	
	print("[ERROR] Could not find file: {}".format(headerName))

if __name__ == '__main__':
	if len(sys.argv) != 4:
		print(' generate.py "path/to/sdk/public/steam" "isteam*.h" "configs"')
		exit()

	steamSDKPath = sys.argv[1]
	headerName = sys.argv[2]
	configDir = sys.argv[3]
	main(steamworksparser.parse(steamSDKPath), headerName, configDir)
