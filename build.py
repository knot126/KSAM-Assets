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

def main(dest):
	# Load config
	config.read("build.ini")
	
	pngfiles = config["Textures"]["files"].split(" ")
	cwd = os.getcwd()
	
	# Create folders for the entire APK structure
	print(" → Creating folders for build...")
	
	permmode = 0o755
	
	os.mkdir("build", mode=permmode)
	os.mkdir("build/assets", mode=permmode)
	os.mkdir("build/assets/about", mode=permmode)
	os.mkdir("build/assets/effects", mode=permmode)
	os.mkdir("build/assets/fonts", mode=permmode)
	os.mkdir("build/assets/gfx", mode=permmode)
	os.mkdir("build/assets/hud", mode=permmode)
	os.mkdir("build/assets/levels", mode=permmode)
	os.mkdir("build/assets/menu", mode=permmode)
	os.mkdir("build/assets/meshes", mode=permmode)
	os.mkdir("build/assets/music", mode=permmode)
	os.mkdir("build/assets/obstacles", mode=permmode)
	os.mkdir("build/assets/rooms", mode=permmode)
	os.mkdir("build/assets/segments", mode=permmode)
	os.mkdir("build/assets/shaders", mode=permmode)
	os.mkdir("build/assets/snd", mode=permmode)
	
	# Generate baked images
	if (config["Textures"].getboolean("enable")):
		# TODO: This needs to be redone!
		print(" → Generating textures and images...")
		
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
	print(" → Copying new files to APK...")
	shutil.copytree(cwd + "/build/assets", dest + "/assets", dirs_exist_ok = True)
	
	# Cleanup
	if (not config["General"].getboolean("keepAssets")):
		print(" → Removing temporary build tree...")
		shutil.rmtree(cwd + "/build")
	
	print(" → Build completed successfully!")
	return 0

if (__name__ == "__main__"):
	if (len(sys.argv) >= 2):
		sys.exit(main(sys.argv[1]))
	else:
		print("Usage: python3 ./build.py (location to apk root)")
