"""
mtxbake - python implementation of mtx baker, version 1.1

Usage: python3 ./mtxtool.py [input file] [output file]
"""

import zlib
import struct
import sys
import io
from PIL import Image

def printUsageAndExit():
	print("Usage     :", sys.argv[0], "[input type] [input file] [output file]")
	print("Input type:", "Currently only -png")
	sys.exit(1)

def printJpegSupportMsg():
	print("Error: JPEG bake support has been removed starting with version 1.1. If you still need to convert JPEG images to MTX, please use an old version or convert your files to PNG before running them through this tool.")
	sys.exit(-1)

def bakeMtxFromPng(filename_in, filename_out):
	"""
	Convert PNG to MTX image
	"""
	
	# Open image
	image_in = Image.open(filename_in, "r")
	image_in.load()
	
	width = image_in.width
	height = image_in.height
	
	# MTX header data
	mtx_header = b"\x01\x00\x00\x00\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\x01\x00\x00\x00"
	mtx_header = mtx_header + struct.pack("I", width) + struct.pack("I", height)
	
	image_bytes = image_in.tobytes()
	
	# Split RGB and Alpha channels
	alpha_data = image_in.getchannel("A").tobytes()
	rgb_data = image_in.convert("RGB").tobytes()
	
	# Compress alpha data
	alpha_data = zlib.compress(alpha_data, -1)
	alpha_size = struct.pack("I", len(alpha_data))
	
	# Create bytes object that will be used to store JPEG data
	jpeg_data = io.BytesIO(b"")
	
	# Create a new image with RGB data
	t = Image.frombytes("RGB", (width, height), bytes(rgb_data))
	t.save(jpeg_data, format = "JPEG")
	t.close()
	
	jpeg_data = jpeg_data.getvalue()
	jpeg_size = struct.pack("I", len(jpeg_data))
	
	# Create the final output
	write_out = mtx_header + jpeg_size + jpeg_data + alpha_size + alpha_data
	
	with open(filename_out, "wb") as f:
		f.write(write_out)

def main():
	if (len(sys.argv) != 4):
		printUsageAndExit()
	if (sys.argv[1] == "-png"):
		bakeMtxFromPng(sys.argv[2], sys.argv[3])
	elif (sys.argv[1] == "-jpg"):
		printJpegSupportMsg()
	else:
		printUsageAndExit()

if (__name__ == "__main__"):
	main()
