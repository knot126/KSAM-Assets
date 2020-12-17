"""
Place this script in the root of KSAM assets and then run it to build.

Usage: python3 build.py [dest location]
"""

import sys
import os
import shutil
import json
import util.mtxtool as mtx
import configparser as cp

config = cp.ConfigParser()

def loadConfig(name):
	config.read(name);

def main(dest):
	# Load config
	loadConfig("build.ini")
	
	pngfiles = config["Textures"]["files"].split(" ")
	cwd = os.getcwd()
	
	# Copy the base assets folder (requirement should be obsolete)
	print(" → Copying assets to new directory...")
	os.mkdir("build", mode = 0o755) # TODO: Make the entire APK folder structure here...
	shutil.copytree(cwd + "/assets", cwd + "/build/assets", dirs_exist_ok = True)
	
	# Generate baked images
	print(" → Generating textures and images...")
	
	# TODO: Remove needing Textures:dirs setting
	for i in config["Textures"]["dirs"].split(" "):
		os.mkdir("build/assets/" + i, mode = 0o755)
	
	for i in pngfiles:
		filein = "textures/" + i + ".png"
		fileout = "build/assets/" + i + ".png.mtx.mp3"
		print("   → Baking", filein, "to", fileout, "...")
		mtx.bakeMtxFromPng(filein, fileout)
	
	# Install packages
	packages = config["General"]["packages"].split(" ")
	print(" → Installing", len(packages), "package(s)...")
	
	for p in packages:
		f = open(p + "/package.json", "r")
		package_info = json.load(f)
		f.close();
		
		print("   → Installing package", package_info["packageName"], "version", package_info["packageVersion"], "...")
		shutil.copytree(cwd + "/" + p + "/assets", cwd + "/build/assets", dirs_exist_ok = True)
	
	# Overlay the files of the APK
	print(" → Copying files over APK's files...")
	shutil.copytree(cwd + "/build/assets", dest + "/assets", dirs_exist_ok = True)
	
	# Cleanup
	if (not config["General"].getboolean("keepAssets")):
		print(" → Removing temporary build tree...")
		shutil.rmtree(cwd + "/build")
	else:
		print(" → Skip deleting temporary assets...")
	
	print(" → Build completed successfully!")
	return 0

if (__name__ == "__main__"):
	sys.exit(main(sys.argv[1]))
