"""
Smash Hit Segment Tool by Knot126

See bl_info for more information.
"""

# The max string length that will be allowed.
SH_MAX_STR_LEN = 300

# Data for the included MeshBake copy
PLANE_COORDS = (
	# (x, y, z, u, v),
	(-1.0, 1.0, 0.0, 0.0, 0.0), # top left
	(-1.0, -1.0, 0.0, 0.0, 0.125), # bottom left
	(1.0, -1.0, 0.0, 0.125, 0.125), # bottom right
	(1.0, 1.0, 0.0, 0.125, 0.0), # top right
)

PLANE_INDEX_BUFFER = (
	0, 1, 2, # first triangle
	0, 2, 3, # second triangle
)

bl_info = {
	"name": "Knot Segment Tools",
	"description": "Knot's personal version of Smash Hit Blender Tools",
	"author": "Knot126",
	"version": (1, 0, 1),
	"blender": (2, 92, 0),
	"location": "File > Import/Export and 3D View > Tools",
	"warning": "",
	"wiki_url": "https://smashingmods.fandom.com/wiki/Knot126/Smash_Hit_Blender_Tools",
	"tracker_url": "",
	"category": "Development",
}

import xml.etree.ElementTree as et
import bpy
import bpy_extras
import gzip
import json
import os.path as ospath

# Needed for mesh baking, if not already imported
import struct
import math
import zlib

from bpy.props import (StringProperty, BoolProperty, IntProperty, FloatProperty,
	FloatVectorProperty, EnumProperty, PointerProperty)
from bpy.types import (Panel, Menu, Operator, PropertyGroup)

## Segment Export
## All of the following is related to exporting segments.

def sh_create_root(scene, params):
	"""
	Creates the main root and returns it
	"""
	
	size = {"X": scene.sh_len[0],
		    "Y": scene.sh_len[1],
		    "Z": scene.sh_len[2]}
	
	# Initial segment properties, like size
	seg_props = {
		"size": str(size["X"]) + " " + str(size["Y"]) + " " + str(size["Z"]),
	}
	
	if (scene.sh_light[0] != 1.0): seg_props["lightLeft"] = str(scene.sh_light[0])
	if (scene.sh_light[1] != 1.0): seg_props["lightRight"] = str(scene.sh_light[1])
	if (scene.sh_light[2] != 1.0): seg_props["lightTop"] = str(scene.sh_light[2])
	if (scene.sh_light[3] != 1.0): seg_props["lightBottom"] = str(scene.sh_light[3])
	if (scene.sh_light[4] != 1.0): seg_props["lightFront"] = str(scene.sh_light[4])
	if (scene.sh_light[5] != 1.0): seg_props["lightBack"] = str(scene.sh_light[5])
	
	if (scene.sh_lightfactor != 0.5):
		seg_props["meshbake-legacy-light-factor"] = str(scene.sh_lightfactor)
	
	if (params["disable_lighting"]):
		seg_props["meshbake-legacy-disable-lighting"] = "yes"
	
	# Check for the template attrib and set
	if (scene.sh_template):
		seg_props["template"] = scene.sh_template
	
	# Check for softshadow attrib and set
	if (scene.sh_softshadow >= 0.0):
		seg_props["softshadow"] = str(scene.sh_softshadow)
	
	# Create main root and return it
	level_root = et.Element("segment", seg_props)
	level_root.text = "\n\t"
	
	return level_root

def sh_add_object(level_root, scene, obj, params):
	"""
	This will add an obstacle to level_root
	"""
	
	# These positions are swapped
	position = {"X": obj.location[1], 
	            "Y": obj.location[2],
	            "Z": obj.location[0]}
	
	# The only gaurrented to exsist is pos
	properties = {
		"pos": str(position["X"]) + " " + str(position["Y"]) + " " + str(position["Z"]),
	}
	
	# Type for obstacles
	if (obj.sh_properties.sh_type == "OBS"):
		properties["type"] = obj.sh_properties.sh_obstacle
	
	# Type for power-ups
	if (obj.sh_properties.sh_type == "POW"):
		properties["type"] = obj.sh_properties.sh_powerup
		
	# Hidden for all types
	if (obj.sh_properties.sh_hidden):
		properties["hidden"] = "1"
	else:
		properties["hidden"] = "0"
	
	# Add size for boxes
	if (obj.sh_properties.sh_type == "BOX"):
		# Again, swapped becuase of Smash Hit's dimensions
		size = {"X": obj.dimensions[1] / 2,
		        "Y": obj.dimensions[2] / 2,
		        "Z": obj.dimensions[0] / 2}
		
		properties["size"] = str(size["X"]) + " " + str(size["Y"]) + " " + str(size["Z"])
	
	# Add rotation paramater if any rotation has been done and this is a box
	# FIXME: Axies are diffrent in Smash Hit and I am awful at rotation, please check my work
	if (obj.sh_properties.sh_type == "OBS" or obj.sh_properties.sh_type == "DEC"):
		if (obj.rotation_euler[1] > 0.0 or obj.rotation_euler[2] > 0.0 or obj.rotation_euler[0] > 0.0):
			properties["rot"] = str(obj.rotation_euler[1]) + " " + str(obj.rotation_euler[2]) + " " + str(obj.rotation_euler[0])
	
	# Add template for all types of objects
	if (obj.sh_properties.sh_template):
		properties["template"] = obj.sh_properties.sh_template
	
	# Add mode appearance tag
	if (obj.sh_properties.sh_type == "OBS" and obj.sh_properties.sh_mode and obj.sh_properties.sh_mode != "0"):
		properties["mode"] = obj.sh_properties.sh_mode
	
	# Add reflection property for boxes if not default
	if (obj.sh_properties.sh_type == "BOX" and obj.sh_properties.sh_reflective):
		properties["reflection"] = "1"
	
	# Add decal number if this is a decal
	if (obj.sh_properties.sh_type == "DEC"):
		properties["tile"] = str(obj.sh_properties.sh_decal)
	
	# Add decal size if this is a decal (based on sh_size)
	if (obj.sh_properties.sh_type == "DEC"):
		properties["size"] = str(obj.sh_properties.sh_size[0]) + " " + str(obj.sh_properties.sh_size[1])
	
	# Add water size if this is a water (based on physical plane properties)
	if (obj.sh_properties.sh_type == "WAT"):
		size = {"X": obj.dimensions[1] / 2,
		        "Z": obj.dimensions[0] / 2}
		
		properties["size"] = str(size["X"]) + " " + str(size["Z"])
	
	# Set each of the tweleve paramaters if they're needed.
	if (obj.sh_properties.sh_type == "OBS"):
		if (obj.sh_properties.sh_param0):
			properties["param0"] = obj.sh_properties.sh_param0
		if (obj.sh_properties.sh_param1):
			properties["param1"] = obj.sh_properties.sh_param1
		if (obj.sh_properties.sh_param2):
			properties["param2"] = obj.sh_properties.sh_param2
		if (obj.sh_properties.sh_param3):
			properties["param3"] = obj.sh_properties.sh_param3
		if (obj.sh_properties.sh_param4):
			properties["param4"] = obj.sh_properties.sh_param4
		if (obj.sh_properties.sh_param5):
			properties["param5"] = obj.sh_properties.sh_param5
		if (obj.sh_properties.sh_param6):
			properties["param6"] = obj.sh_properties.sh_param6
		if (obj.sh_properties.sh_param7):
			properties["param7"] = obj.sh_properties.sh_param7
		if (obj.sh_properties.sh_param8):
			properties["param8"] = obj.sh_properties.sh_param8
		if (obj.sh_properties.sh_param9):
			properties["param9"] = obj.sh_properties.sh_param9
		if (obj.sh_properties.sh_param10):
			properties["param10"] = obj.sh_properties.sh_param10
		if (obj.sh_properties.sh_param11):
			properties["param11"] = obj.sh_properties.sh_param11
	
	# Set tint for decals
	if (obj.sh_properties.sh_havetint and obj.sh_properties.sh_type == "DEC"):
		properties["color"] = str(obj.sh_properties.sh_tint[0]) + " " + str(obj.sh_properties.sh_tint[1]) + " " + str(obj.sh_properties.sh_tint[2]) + " " + str(obj.sh_properties.sh_tint[3])
	
	# Set tile info for boxes
	if (obj.sh_properties.sh_type == "BOX" and obj.sh_properties.sh_visible):
		properties["visible"] = "1"
		properties["color"] = str(obj.sh_properties.sh_tint[0]) + " " + str(obj.sh_properties.sh_tint[1]) + " " + str(obj.sh_properties.sh_tint[2]) + " " + str(obj.sh_properties.sh_tint[3])
		properties["tile"] = str(obj.sh_properties.sh_tile)
		properties["tileSize"] = str(obj.sh_properties.sh_tilesize[0]) + " " + str(obj.sh_properties.sh_tilesize[1]) + " " + str(obj.sh_properties.sh_tilesize[2])
		if (obj.sh_properties.sh_tilerot[1] > 0.0 or obj.sh_properties.sh_tilerot[2] > 0.0 or obj.sh_properties.sh_tilerot[0] > 0.0):
			properties["tileRot"] = str(obj.sh_properties.sh_tilerot[1]) + " " + str(obj.sh_properties.sh_tilerot[2]) + " " + str(obj.sh_properties.sh_tilerot[0])
	
	# Set the tag name
	element_type = "MISSING"
	
	if (obj.sh_properties.sh_type == "BOX"):
		element_type = "box"
	elif (obj.sh_properties.sh_type == "OBS"):
		element_type = "obstacle"
	elif (obj.sh_properties.sh_type == "DEC"):
		element_type = "decal"
	elif (obj.sh_properties.sh_type == "POW"):
		element_type = "powerup"
	elif (obj.sh_properties.sh_type == "WAT"):
		element_type = "water"
	
	# Add the element to the document
	el = et.SubElement(level_root, element_type, properties)
	el.tail = "\n\t"
	if (params["isLast"]): # Fixes the issues with the last line of the file
		el.tail = "\n"

def sh_export_segment(fp, context, *, compress = False, params = {"sh_exportmode": "NON"}):
	"""
	This function exports the blender scene to a Smash Hit compatible XML file.
	"""
	context.window.cursor_set('WAIT')
	
	scene = context.scene.sh_properties
	b_scene = context.scene
	level_root = sh_create_root(scene, params)
	
	for i in range(len(bpy.data.objects)):
		obj = bpy.data.objects[i]
		
		params["isLast"] = False
		if (i == (len(bpy.data.objects) - 1)):
			params["isLast"] = True
		
		sh_add_object(level_root, scene, obj, params)
	
	# Write the file
	
	file_header = "<!-- Exported with Smash Hit Blender FX v" + str(bl_info["version"][0]) + "." + str(bl_info["version"][1]) + "." + str(bl_info["version"][2]) + " -->\n"
	c = file_header + et.tostring(level_root, encoding = "unicode")
	
	# Set the file path for the mesh file
	meshfile = ospath.splitext(ospath.splitext(ospath.splitext(fp)[0])[0])[0] + ".mesh.mp3"
	
	# Cook the mesh file if we need to
	if (params["sh_exportmode"] == "NEW"):
		sh_cookMesh041(et.fromstring(c), meshfile)
	
	with gzip.open(fp, "wb") as f:
		f.write(c.encode())
	
	context.window.cursor_set('DEFAULT')
	return {"FINISHED"}

## UI-related classes

# Common values between export types
class sh_ExportCommon:
	sh_exportmode: EnumProperty(
		name = "Box Export Mode (READ TOOLTIP)",
		description = "This will control how the boxes should be exported. Hover over each option for an explation of how it works",
		items = [ 
			('NEW', "Mesh Bake", "Bakes a mesh file alongside the normal segment file"),
			('NON', "None", "This will skip exporting stone in any way"),
		],
		default = "NEW"
		)
	
	templates: StringProperty(
		name = "Templates",
		description = "The path to the templates file that will be merged into the segment on export",
		default = "",
		options = {"HIDDEN"},
		maxlen = SH_MAX_STR_LEN,
		)
	
	nolighting: BoolProperty(
		name = "Legacy lighting",
		description = "Effectively disables lighting, only for legacy MeshBake",
		default = False
		)

# Compressed segment export

class sh_export_gz(bpy.types.Operator, bpy_extras.io_utils.ExportHelper, sh_ExportCommon):
	bl_idname = "sh.export_compressed"
	bl_label = "Export Segment"
	
	filename_ext = ".xml.gz.mp3"
	filter_glob = StringProperty(
		default = '*.xml.gz.mp3',
		options = {'HIDDEN'},
		maxlen = 255)
	
	def execute(self, context):
		return sh_export_segment(self.filepath, context, compress = True, params = { "sh_exportmode": self.sh_exportmode, "templates_path": self.templates, "disable_lighting": self.nolighting})

def sh_draw_export_gz(self, context):
	self.layout.operator("sh.export_compressed", text="Smash Hit (.xml.gz.mp3)")

## MESH BAKE
## This is just taken from meshbake

#MESHBAKE_START

def sh_cookMesh041(seg, outfile):
	"""
	Builds a mesh file from an XML node
	
	Try to keep functions used only in this function within the scope of this
	function so its easier to embed.
	"""
	
	mesh_vert = b""
	mesh_vert_count = 0
	mesh_index = b""
	mesh = open(outfile, "wb")
	light_factor = 0.5
	
	def add_vert(x, y, z, u, v, r, g, b, a):
		"""
		Adds a vertex
		"""
		# print(f"{x}, {y}, {z}, {u}, {v}")
		
		nonlocal mesh_vert_count
		nonlocal mesh_vert
		nonlocal mesh_index
		mesh_vert_count += 1
		
		vert = b""
		index = b""
		
		# The position of this vertex
		vert += struct.pack("f", x)
		vert += struct.pack("f", y)
		vert += struct.pack("f", z)
		
		vert += struct.pack("f", u)
		vert += struct.pack("f", v)
		
		vert += struct.pack("B", r)
		vert += struct.pack("B", g)
		vert += struct.pack("B", b)
		vert += struct.pack("B", a)
		
		assert(len(vert) == 24)
		
		mesh_vert += vert
		
		return mesh_vert_count
	
	def add_cube(x, y, z, sx, sy, sz, t, tx, ty, c, lgt):
		"""
		Adds a cube
		"""
		nonlocal mesh_index
		nonlocal light_factor # the multiply of the light to make sure it's not too bright
		
		# Calculate position for the texture coordinates
		tile_u_offset = ((t % 8) + 1) / 8 - 0.125
		tile_v_offset = ((math.floor(((t + 1) / 8) - 0.125) + 1) / 8) - 0.125
		
		# Front and back faces
		for z_sign in [1.0, -1.0]:
			y_left = (sy * 2.0)
			y_offset = (sy * 1.0)
			
			while (y_left > 0.0):
				x_left = (sx * 2.0)
				x_offset = (sx * 1.0)
				
				y_cut = 1.0
				if (y_left < 1.0):
					y_cut = y_left
				
				while (x_left > 0.0):
					x_cut = 1.0
					if (x_left < 1.0):
						x_cut = x_left
					
					# Add indexes for one plane
					for i in range(len(PLANE_INDEX_BUFFER)):
						mesh_index += struct.pack("I", PLANE_INDEX_BUFFER[i] + mesh_vert_count)
					
					# Add verts for one plane
					for i in range(len(PLANE_COORDS)):
						add_vert(
							((PLANE_COORDS[i][0] * x_cut) * (tx * 0.5) + x + x_offset + ((1.0 - x_cut) * 0.5)) - 0.5,
							((PLANE_COORDS[i][1] * y_cut) * (ty * 0.5) + y + y_offset + ((1.0 - y_cut) * 0.5)) - 0.5,
							z + (sz * z_sign),
							(PLANE_COORDS[i][3] * x_cut) + tile_u_offset,
							(PLANE_COORDS[i][4] * y_cut) + tile_v_offset,
							int(c[0] * 0.5 * (lgt[int((z_sign-1.0)/-2)])), 
							int(c[1] * 0.5 * (lgt[int((z_sign-1.0)/-2)])), 
							int(c[2] * 0.5 * (lgt[int((z_sign-1.0)/-2)])), 
							c[3])
					
					x_left -= tx
					x_offset -= tx
				# END while (x_left > 0.0)
				
				y_left -= ty
				y_offset -= ty
			# END while (y_left > 0.0)
		
		# Top and bottom faces
		# NOTE: This is only partially working...
		for j in [(0, 1), (1, 0)]:
			for y_sign in [1.0, -1.0]:
				z_left = (sz * 2.0)
				z_offset = (sz * 1.0)
				
				while (z_left > 0.0):
					x_left = (sx * 2.0)
					x_offset = (sx * 1.0)
					
					z_cut = 1.0
					if (z_left < 1.0):
						z_cut = z_left
					
					while (x_left > 0.0):
						x_cut = 1.0
						if (x_left < 1.0):
							x_cut = x_left
						
						# Add indexes for one plane
						for i in range(len(PLANE_INDEX_BUFFER)):
							mesh_index += struct.pack("I", PLANE_INDEX_BUFFER[i] + mesh_vert_count)
						
						# Add verts for one plane
						for i in range(len(PLANE_COORDS)):
							add_vert(
								(PLANE_COORDS[i][j[0]] * (tx * 0.5) + x + x_offset + ((1.0 - x_cut) * 0.5)) - 0.5,
								y + (sy * y_sign),
								(PLANE_COORDS[i][j[1]] * (ty * 0.5) + z + z_offset + ((1.0 - z_cut) * 0.5)) - 0.5,
								PLANE_COORDS[i][3] + tile_u_offset,
								PLANE_COORDS[i][4] + tile_v_offset,
								int(c[0] * 0.5 * (lgt[2 + j[1]])), 
								int(c[1] * 0.5 * (lgt[2 + j[1]])), 
								int(c[2] * 0.5 * (lgt[2 + j[1]])), 
								c[3])
						
						x_left -= tx
						x_offset -= tx
					# END while (x_left > 0.0)
					
					z_left -= ty
					z_offset -= ty
				# END while (y_left > 0.0)
			# END for y_sign
		
		# Left and right side faces
		for j in [(0, 1), (1, 0)]:
			for x_sign in [1.0, -1.0]:
				y_left = (sy * 2.0)
				y_offset = (sy * 1.0)
				
				while (y_left > 0.0):
					y_cut = 1.0
					if (y_left < 1.0):
						y_cut = y_left
					
					z_left = (sz * 2.0)
					z_offset = (sz * 1.0)
					
					while (z_left > 0.0):
						z_cut = 1.0
						if (z_left < 1.0):
							z_cut = z_left
						
						# Add indexes for one plane
						for i in range(len(PLANE_INDEX_BUFFER)):
							mesh_index += struct.pack("I", PLANE_INDEX_BUFFER[i] + mesh_vert_count)
						
						# Add verts for one plane
						for i in range(len(PLANE_COORDS)):
							add_vert(
								x + (sx * x_sign),
								(PLANE_COORDS[i][j[0]] * (ty * 0.5) + y + y_offset + ((1.0 - y_cut) * 0.5)) - 0.5,
								(PLANE_COORDS[i][j[1]] * (tx * 0.5) + z + z_offset + ((1.0 - z_cut) * 0.5)) - 0.5,
								PLANE_COORDS[i][3] + tile_u_offset,
								PLANE_COORDS[i][4] + tile_v_offset,
								int(c[0] * 0.5 * (lgt[4 + j[1]])), 
								int(c[1] * 0.5 * (lgt[4 + j[1]])), 
								int(c[2] * 0.5 * (lgt[4 + j[1]])), 
								c[3])
						
						z_left -= tx
						z_offset -= tx
					# END while (z_left > 0.0)
					
					y_left -= ty
					y_offset -= ty
				# END while (y_left > 0.0)
			# END for x_sign
	
	light_multiply = (
		float(seg.attrib.get("lightLeft", "1")), 
		float(seg.attrib.get("lightRight", "1")), 
		float(seg.attrib.get("lightTop", "1")), 
		float(seg.attrib.get("lightBottom", "1")), 
		float(seg.attrib.get("lightFront", "1")), 
		float(seg.attrib.get("lightBack", "1"))
	)
	
	if (seg.attrib.get("meshbake-legacy-disable-lighting", "n") == "yes"):
		light_multiply = (2.0, 2.0, 2.0, 2.0, 2.0, 2.0)
	
	if ("meshbake-legacy-light-factor" in seg.attrib):
		light_factor = float(seg.attrib["meshbake-legacy-light-factor"])
	
	# Iterate through all the entities, and make boxes into meshes
	for entity in seg:
		if (entity.tag == "box"):
			properties = entity.attrib
			
			visible = properties.get("visible", "0")
			
			# Check if this box will be visible. If it is not visible, then
			# it will not be included in the mesh.
			if (visible == "1"):
				pos = properties.get("pos", "0.0 0.0 0.0")
				size = properties.get("size", "1.0 1.0 1.0")
				color = properties.get("color", "1.0 1.0 1.0")
				tile = properties.get("tile", "0")
				tileSize = properties.get("tileSize", "1.0 1.0")
				
				# Convert to numbers
				# Position
				pos = pos.split(" ")
				pos[0] = float(pos[0])
				pos[1] = float(pos[1])
				pos[2] = float(pos[2])
				
				# Size
				size = size.split(" ")
				size[0] = float(size[0])
				size[1] = float(size[1])
				size[2] = float(size[2])
				
				# Colour
				color = color.split(" ")
				color[0] = int(float(color[0]) * 255)
				color[1] = int(float(color[1]) * 255)
				color[2] = int(float(color[2]) * 255)
				if (len(color) == 4):
					color[3] = int(float(color[3]) * 255)
				else:
					color.append(255)
				
				# Tile
				tile = int(tile)
				
				# Tile Size
				tileSize = tileSize.split(" ")
				tileSize[0] = float(tileSize[0])
				tileSize[1] = float(tileSize[1])
				
				add_cube(pos[0], pos[1], pos[2], size[0], size[1], size[2], tile, tileSize[0], tileSize[1], color, light_multiply)
	
	mesh_data = (struct.pack("I", len(mesh_vert) // 24))
	mesh_data += (mesh_vert)
	mesh_data += (struct.pack("I", len(mesh_index) // 12))
	mesh_data += (mesh_index)
	
	mesh_data = zlib.compress(mesh_data)
	
	print(f"Exported {mesh_vert_count} verts.")
	
	mesh.write(mesh_data)
	mesh.close()

#MESHBAKE_END

## EDITOR
## The following things are more related to the editor and are not specifically
## for exporting or importing segments.

class sh_SceneProperties(PropertyGroup):
	"""
	Segment (scene) properties
	"""
	
	sh_len: FloatVectorProperty(
		name = "Size",
		description = "Segment size (Width, Height, Depth). Hint: Last paramater changes the length (depth) of the segment",
		default = (12.0, 10.0, 8.0), 
		min = 0.0,
		max = 750.0
	) 
	
	sh_template: StringProperty(
		name = "Template",
		description = "The template paramater that is passed for the entire segment",
		default = "",
		maxlen = SH_MAX_STR_LEN,
		)
	
	sh_softshadow: FloatProperty(
		name = "Soft Shadow",
		description = "Exact function unknown, probably shadow transparency",
		default = -0.001,
		min = -0.001,
		max = 1.0
		)
	
	sh_light: FloatVectorProperty(
		name = "Lighting",
		description = "Light intensity, in this order: left, right, top, bottom, front, back",
		default = (1.0, 1.0, 1.0, 1.0, 1.0, 1.0),
		min = 0.0,
		max = 2.0,
		size = 6,
		)
	
	sh_lightfactor: FloatProperty(
		name = "Light Factor",
		description = "Changes the way that light is multiplied so that things do not look too bright",
		default = 0.5,
		min = 0.333,
		max = 1.0
		)

# Object (obstacle/powerup/decal/water) properties

class sh_EntityProperties(PropertyGroup):
	sh_type: EnumProperty(
		name = "Kind",
		description = "The kind of object that the currently selected object should be treated as.",
		items = [ ('BOX', "Box", ""),
				  ('OBS', "Obstacle", ""),
				  ('DEC', "Decal", ""),
				  ('POW', "Power-up", ""),
				  ('WAT', "Water", ""),
				],
		default = "BOX"
		)
	
	sh_template: StringProperty(
		name = "Template",
		description = "The template for the obstacle/box (see templates.xml), remember that this can be easily overridden per obstacle/box",
		default = "",
		maxlen = SH_MAX_STR_LEN,
		)
	
	sh_obstacle: StringProperty(
		name = "Obstacle",
		description = "Name of the obstacle to be used",
		default = "",
		maxlen = SH_MAX_STR_LEN,
		)
	
	sh_powerup: EnumProperty(
		name = "Power-up",
		description = "The type of power-up that will appear",
		items = [ ('ballfrenzy', "Ball Frenzy", ""),
				  ('slowmotion', "Slow Motion", ""),
				  ('nitroballs', "Nitro Balls", ""),
				],
		default = "ballfrenzy"
		)
	
	sh_hidden: BoolProperty(
		name = "Hidden",
		description = "If the obstacle will show in the level",
		default = False
		)
	
	sh_mode: EnumProperty(
		name = "Mode",
		description = "Broken",
		items = [ ("0", "All Modes", ""),
				  ("1", "Training", ""),
				  ("2", "Classic", ""),
				  ("3", "Mayhem", ""),
				  ("4", "Zen", ""),
				  ("5", "Versus", ""),
				  ("6", "Co-op", ""),
				],
		default = "0"
		)
	
	sh_visible: BoolProperty(
		name = "Visible",
		description = "If the box will appear in the exported mesh",
		default = True
		)
	
	sh_tile: IntProperty(
		name = "Tile",
		description = "The texture that will appear on the surface of the box or decal",
		default = 0,
		min = 0,
		max = 63
		)
	
	sh_tilerot: FloatVectorProperty(
		name = "Rotation",
		description = "Rotation of the tile, in radians (PI = 1/2 rotation)",
		default = (0.0, 0.0, 0.0), 
		min = -6.28318530718,
		max = 6.28318530718
	) 
	
	sh_tilesize: FloatVectorProperty(
		name = "Size",
		description = "The appearing size of the tiles on the box when exported (third paramater is ignored)",
		default = (1.0, 1.0, 0.0), 
		min = 0.0,
		max = 128.0
	)
	
	sh_decal: IntProperty(
		name = "Decal",
		description = "The image ID for the decal (negitive numbers are doors)",
		default = 0,
		min = -4,
		max = 63
		)
	
	sh_reflective: BoolProperty(
		name = "Reflective",
		description = "If this box should show reflections",
		default = False
		)
	
	sh_param0: StringProperty(
		name = "param0",
		description = "key=value",
		default = "",
		maxlen = SH_MAX_STR_LEN,
		)
	
	sh_param1: StringProperty(
		name = "param1",
		description = "key=value",
		default = "",
		maxlen = SH_MAX_STR_LEN,
		)
	
	sh_param2: StringProperty(
		name = "param2",
		description = "key=value",
		default = "",
		maxlen = SH_MAX_STR_LEN,
		)
	
	sh_param3: StringProperty(
		name = "param3",
		description = "key=value",
		default = "",
		maxlen = SH_MAX_STR_LEN,
		)
	
	sh_param4: StringProperty(
		name = "param4",
		description = "key=value",
		default = "",
		maxlen = SH_MAX_STR_LEN,
		)
	
	sh_param5: StringProperty(
		name = "param5",
		description = "key=value",
		default = "",
		maxlen = SH_MAX_STR_LEN,
		)
	
	sh_param6: StringProperty(
		name = "param6",
		description = "key=value",
		default = "",
		maxlen = SH_MAX_STR_LEN,
		)
	
	sh_param7: StringProperty(
		name = "param7",
		description = "key=value",
		default = "",
		maxlen = SH_MAX_STR_LEN,
		)
	
	sh_param8: StringProperty(
		name = "param8",
		description = "key=value",
		default = "",
		maxlen = SH_MAX_STR_LEN,
		)
	
	sh_param9: StringProperty(
		name = "param9",
		description = "key=value",
		default = "",
		maxlen = SH_MAX_STR_LEN,
		)
	
	sh_param10: StringProperty(
		name = "param10",
		description = "key=value",
		default = "",
		maxlen = SH_MAX_STR_LEN,
		)
	
	sh_param11: StringProperty(
		name = "param11",
		description = "key=value",
		default = "",
		maxlen = SH_MAX_STR_LEN,
		)
	
	sh_havetint: BoolProperty(
		name = "Add decal colourisation",
		description = "Changes the tint (colourisation) of the decal",
		default = False
		)
	
	sh_tint: FloatVectorProperty(
		name = "Colour",
		description = "The colour to be used for tinting, colouring and mesh data",
		subtype = "COLOR",
		default = (0.5, 0.5, 0.5, 1.0), 
		min = 0.0,
		max = 1.0,
		size = 4,
	) 
	
	sh_size: FloatVectorProperty(
		name = "Size",
		description = "The size of the object when exported (third paramater is ignored). For boxes this is the tileSize property",
		default = (1.0, 1.0, 0.0), 
		min = 0.0,
		max = 128.0
	)

class sh_SegmentPanel(Panel):
	bl_label = "Segment"
	bl_idname = "OBJECT_PT_segment_panel"
	bl_space_type = "VIEW_3D"
	bl_region_type = "UI"
	bl_category = "Smash Hit"
	
	@classmethod
	def poll(self, context):
		return context.object is not None
	
	def draw(self, context):
		layout = self.layout
		scene = context.scene
		sh_properties = scene.sh_properties
		
		layout.prop(sh_properties, "sh_len")
		layout.prop(sh_properties, "sh_template")
		layout.prop(sh_properties, "sh_softshadow")
		layout.prop(sh_properties, "sh_light")
		layout.prop(sh_properties, "sh_lightfactor")
		layout.separator()

class sh_ObstaclePanel(Panel):
	bl_label = "Entity"
	bl_idname = "OBJECT_PT_obstacle_panel"
	bl_space_type = "VIEW_3D"   
	bl_region_type = "UI"
	bl_category = "Smash Hit"
	bl_context = "objectmode"
	
	@classmethod
	def poll(self, context):
		return context.object is not None
	
	def draw(self, context):
		layout = self.layout
		object = context.object
		sh_properties = object.sh_properties
		
		# VER 0.110.0: Hid some options that don't work in a compatible way.
		
		# All objects will have all properties, but only some will be used for
		# each of obstacle there is.
		layout.prop(sh_properties, "sh_type")
		
		# Obstacle type for obstacles
		if (sh_properties.sh_type == "OBS"):
			layout.prop(sh_properties, "sh_obstacle")
		
		# Decal number for decals
		if (sh_properties.sh_type == "DEC"):
			layout.prop(sh_properties, "sh_decal")
		
		# Template for boxes and obstacles
		if (   sh_properties.sh_type == "OBS"
		    or sh_properties.sh_type == "BOX"):
			layout.prop(sh_properties, "sh_template")
		
		# Refelective and tile property for boxes
		if (sh_properties.sh_type == "BOX"):
			layout.prop(sh_properties, "sh_visible")
			if (sh_properties.sh_visible):
				layout.prop(sh_properties, "sh_tile")
				layout.prop(sh_properties, "sh_tint")
			layout.prop(sh_properties, "sh_reflective")
		
		# Colorization for decals
		if (sh_properties.sh_type == "DEC"):
			layout.prop(sh_properties, "sh_havetint")
			if (sh_properties.sh_havetint):
				layout.prop(sh_properties, "sh_tint")
				layout.prop(sh_properties, "sh_tintalpha")
		
		# Power-up name for power-ups
		if (sh_properties.sh_type == "POW"):
			layout.prop(sh_properties, "sh_powerup")
		
		# Size for decal
		if (sh_properties.sh_type == "DEC"):
			layout.prop(sh_properties, "sh_size")
		
		# Paramaters for boxes
		if (sh_properties.sh_type == "OBS"):
			layout.prop(sh_properties, "sh_param0")
			layout.prop(sh_properties, "sh_param1")
			layout.prop(sh_properties, "sh_param2")
			layout.prop(sh_properties, "sh_param3")
			layout.prop(sh_properties, "sh_param4")
			# After item five, dinamically update the items that appear to enforce
			# good ordering
			if (sh_properties.sh_param4 or sh_properties.sh_param5):
				layout.prop(sh_properties, "sh_param5")
			if (sh_properties.sh_param5 or sh_properties.sh_param6):
				layout.prop(sh_properties, "sh_param6")
			if (sh_properties.sh_param6 or sh_properties.sh_param7):
				layout.prop(sh_properties, "sh_param7")
			if (sh_properties.sh_param7 or sh_properties.sh_param8):
				layout.prop(sh_properties, "sh_param8")
			if (sh_properties.sh_param8 or sh_properties.sh_param9):
				layout.prop(sh_properties, "sh_param9")
			if (sh_properties.sh_param9 or sh_properties.sh_param10):
				layout.prop(sh_properties, "sh_param10")
			if (sh_properties.sh_param10 or sh_properties.sh_param11):
				layout.prop(sh_properties, "sh_param11")
		
		# Option to export object or not
		layout.prop(sh_properties, "sh_hidden")
		
		layout.separator()

classes = (
	# Ignore the naming scheme for classes, please
	sh_SceneProperties,
	sh_EntityProperties,
	sh_SegmentPanel,
	sh_ObstaclePanel,
	sh_export_gz,
)

def register():
	from bpy.utils import register_class
	for cls in classes:
		register_class(cls)
	
	bpy.types.Scene.sh_properties = PointerProperty(type=sh_SceneProperties)
	bpy.types.Object.sh_properties = PointerProperty(type=sh_EntityProperties)
	
	# Add the export operator to menu
	bpy.types.TOPBAR_MT_file_export.append(sh_draw_export_gz)

def unregister():
	from bpy.utils import unregister_class
	for cls in reversed(classes):
		unregister_class(cls)
	del bpy.types.Scene.sh_properties
