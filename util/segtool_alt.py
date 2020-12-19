"""
Smash Hit Segment Tool version 0.102.0

This works for Blender 2.8x and 2.90
"""

bl_info = {
	"name": "Smash Hit Tools (KSAM Mod)",
	"description": "Smash Hit segment exporter and property editor addon for blender, edited for KSAM enhancements",
	"author": "Knot126",
	"version": (0, 102, 1),
	"blender": (2, 80, 0),
	"location": "File > Export and 3D View > Tools",
	"warning": "",
	"wiki_url": "https://smashingmods.fandom.com/wiki/Knot126/Smash_Hit_Blender_Tools",
	"tracker_url": "",
	"category": "Level Editing"
}

import bpy
import bpy_extras
import xml.etree.ElementTree as et
import gzip

from bpy.props import (StringProperty, BoolProperty, IntProperty, FloatProperty,
	FloatVectorProperty, EnumProperty, PointerProperty)
from bpy.types import (Panel, Menu, Operator, PropertyGroup)

class Segment:
	"""
	Segment object class
	
	NOTE:
	The design of this class is a bit odd at the moment. The "add_sometype" are
	not very good in terms of not repeating code, but they work very well when
	actually reading it because it's possible to decipher what it's saying 
	instead of trying to figure out which if statement corresponds to which 
	line. Then again, maybe this is caused by bad software design?
	
	NOTE:
	I hope that this class can be split into two pices: one that constructs the
	segment, and the other that gets the data from blender. This would mean 
	that the Segment class is portable and the Blender class only needs to stay
	with blender.
	"""
	
	def __init__(self):
		self.level_content = None
		self.add_formatting = True
		self.scene = None
	
	def set_formmating(self, setting):
		"""
		Set the formatting to the passed value
		"""
		self.add_formatting = setting
	
	def add_root_element(self, scene):
		"""
		Adds the initial root element based on the current settings. Anything
		under the "Segment Properties" panel will be exported here, except for
		the default stone color, since that is part of the stonehack.
		"""
		properties = {}
		
		sh_scene = scene.sh_properties
		
		# Size param
		properties["size"] = str(sh_scene.sh_len[0]) + " " + str(sh_scene.sh_len[1]) + " " + str(sh_scene.sh_len[2])
		
		# Template param
		if (sh_scene.sh_template):
			properties["template"] = str(sh_scene.sh_template)
		
		# Softshadow param
		# If the softshadow param is negitive, then the default is used
		if (sh_scene.sh_softshadow >= 0.0):
			properties["softshadow"] = str(sh_scene.sh_softshadow)
		
		# Create root element
		self.level_content = et.Element("segment", properties)
		
		# Add formatting if set
		if (self.add_formatting):
			self.level_content.text = "\n\t"
	
	def add_box(self, scene, obj, isLast):
		"""
		Adds a box to the exported segment.
		"""
		properties = {}
		
		# Add pos param
		properties["pos"] = str(obj.location[1]) + " " + str(obj.location[2]) + " " + str(obj.location[0])
		
		# Add hidden param
		if (obj.sh_properties.sh_hidden):
			properties["hidden"] = "1"
		else:
			properties["hidden"] = "0"
		
		# Add size
		properties["size"] = str((obj.dimensions[1] / 2)) + " " + str((obj.dimensions[2] / 2)) + " " + str((obj.dimensions[0] / 2))
		
		# Add template
		if (obj.sh_properties.sh_template):
			properties["template"] = obj.sh_properties.sh_template
		
		# Add reflection
		if (obj.sh_properties.sh_reflective):
			properties["reflection"] = "1"
		
		if (obj.sh_properties.sh_visible):
			# Set visible to enabled
			properties["visible"] = "1"
			
			# Set tile color
			properties["color"] = str(obj.sh_properties.sh_tint[0]) + " " + str(obj.sh_properties.sh_tint[1]) + " " + str(obj.sh_properties.sh_tint[2])
			
			# Set tile number
			properties["tile"] = str(obj.sh_properties.sh_tile)
			
			# Set tile size
			properties["tileSize"] = str(obj.sh_properties.sh_tilesize[0]) + " " + str(obj.sh_properties.sh_tilesize[1]) + " " + str(obj.sh_properties.sh_tilesize[2])
			
			# Set tile rotation
			if (obj.sh_properties.sh_tilerot[0] > 0.0 or
				obj.sh_properties.sh_tilerot[1] > 0.0 or
				obj.sh_properties.sh_tilerot[2] > 0.0):
				properties["tileRot"] = str(obj.sh_properties.sh_tilerot[1]) + " " + str(obj.sh_properties.sh_tilerot[2]) + " " + str(obj.sh_properties.sh_tilerot[0])
		
		# Add to level
		main_element = et.SubElement(self.level_content, "box", properties)
		
		if (self.add_formatting):
			main_element.tail = "\n\t"
		
		#######################################################################
		#   Stone Hack Section
		#######################################################################
		if (scene.sh_properties.sh_stonehack):
			if (self.add_formatting):
				main_element.tail = "\n\t\t"
			
			props = {
				"pos": str(obj.location[1]) + " " + str(obj.location[2]) + " " + str(obj.location[0]),
				"type": "stone",
				"param0": "sizeX=" + str((obj.dimensions[1] / 2)),
				"param1": "sizeY=" + str((obj.dimensions[2] / 2)),
				"param2": "sizeZ=" + str((obj.dimensions[0] / 2)),
			}
			
			# Check if a local color is set, otherwise use the global color
			if (obj.sh_properties.sh_havetint):
				# Use local color
				props["param3"] = "color=" + str(obj.sh_properties.sh_tint[0]) + " " + str(obj.sh_properties.sh_tint[1]) + " " + str(obj.sh_properties.sh_tint[2])
			else:
				# Use global color
				props["param3"] = "color=" + str(scene.sh_properties.sh_color[0]) + " " + str(scene.sh_properties.sh_color[1]) + " " + str(scene.sh_properties.sh_color[2])
			
			stone_element = et.SubElement(self.level_content, "obstacle", props)
			stone_element.tail = "\n\t"
			if (isLast): stone_element.tail = "\n"
	
	def add_obstacle(self, scene, obj, isLast):
		"""
		Add an obstacle to the segment
		"""
		properties = {}
		
		# Add pos param
		properties["pos"] = str(obj.location[1]) + " " + str(obj.location[2]) + " " + str(obj.location[0])
		
		# Add type
		properties["type"] = obj.sh_properties.sh_obstacle
		
		# Add hidden param
		if (obj.sh_properties.sh_hidden):
			properties["hidden"] = "1"
		else:
			properties["hidden"] = "0"
		
		# Add template
		if (obj.sh_properties.sh_template):
			properties["template"] = obj.sh_properties.sh_template
		
		# Add mode appearance tag
		if (obj.sh_properties.sh_mode and obj.sh_properties.sh_mode != "0"):
			properties["mode"] = obj.sh_properties.sh_mode
		
		# Add rotation
		if (   obj.rotation_euler[1] > 0.0 
			or obj.rotation_euler[2] > 0.0 
			or obj.rotation_euler[0] > 0.0):
			properties["rot"] = str(obj.rotation_euler[1]) + " " + str(obj.rotation_euler[2]) + " " + str(obj.rotation_euler[0])
		
		# Add param params
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
		if (obj.sh_properties.sh_param7):
			properties["param8"] = obj.sh_properties.sh_param8
		if (obj.sh_properties.sh_param7):
			properties["param9"] = obj.sh_properties.sh_param9
		if (obj.sh_properties.sh_param7):
			properties["param10"] = obj.sh_properties.sh_param10
		if (obj.sh_properties.sh_param7):
			properties["param11"] = obj.sh_properties.sh_param11
		
		# Add to level
		main_element = et.SubElement(self.level_content, "obstacle", properties)
		
		if (self.add_formatting):
			main_element.tail = "\n\t"
			if (isLast): main_element.tail = "\n"
	
	def add_decal(self, scene, obj, isLast):
		"""
		Add a decal to the segment
		"""
		properties = {}
		
		# Add pos param
		properties["pos"] = str(obj.location[1]) + " " + str(obj.location[2]) + " " + str(obj.location[0])
		
		# Add hidden param
		if (obj.sh_properties.sh_hidden):
			properties["hidden"] = "1"
		else:
			properties["hidden"] = "0"
		
		# Add tile param
		properties["tile"] = str(obj.sh_properties.sh_decal)
		
		# Add size param
		properties["size"] = str(obj.sh_properties.sh_size[0]) + " " + str(obj.sh_properties.sh_size[1])
		
		# Add color param
		if (obj.sh_properties.sh_havetint):
			properties["color"] = str(obj.sh_properties.sh_tint[0]) + " " + str(obj.sh_properties.sh_tint[1]) + " " + str(obj.sh_properties.sh_tint[2]) + " " + str(obj.sh_properties.sh_tintalpha)
		
		# Add to level
		main_element = et.SubElement(self.level_content, "decal", properties)
		
		if (self.add_formatting):
			main_element.tail = "\n\t"
			if (isLast): main_element.tail = "\n"
	
	def add_powerup(self, scene, obj, isLast):
		"""
		Add a power-up to the segment
		"""
		properties = {}
		
		# Add pos param
		properties["pos"] = str(obj.location[1]) + " " + str(obj.location[2]) + " " + str(obj.location[0])
		
		# Add hidden param
		if (obj.sh_properties.sh_hidden):
			properties["hidden"] = "1"
		else:
			properties["hidden"] = "0"
		
		# Add type
		properties["type"] = obj.sh_properties.sh_powerup
		
		# Add to level
		main_element = et.SubElement(self.level_content, "powerup", properties)
		
		if (self.add_formatting):
			main_element.tail = "\n\t"
			if (isLast): main_element.tail = "\n"
	
	def add_water(self, scene, obj, isLast):
		"""
		Add a water plane to the segment
		"""
		properties = {}
		
		# Add pos param
		properties["pos"] = str(obj.location[1]) + " " + str(obj.location[2]) + " " + str(obj.location[0])
		
		# Add hidden param
		if (obj.sh_properties.sh_hidden):
			properties["hidden"] = "1"
		else:
			properties["hidden"] = "0"
		
		# Add size param
		properties["size"] = str(obj.sh_properties.sh_size[0]) + " " + str(obj.sh_properties.sh_size[1])
		
		# Add to level
		main_element = et.SubElement(self.level_content, "water", properties)
		
		if (self.add_formatting):
			main_element.tail = "\n\t"
			if (isLast): main_element.tail = "\n"
	
	def add_object(self, scene, obj, isLast):
		"""
		Function to add objects without specifiying type
		"""
		
		if (obj.sh_properties.sh_type == "BOX"):
			self.add_box(scene, obj, isLast)
		
		elif (obj.sh_properties.sh_type == "OBS"):
			self.add_obstacle(scene, obj, isLast)
		
		elif (obj.sh_properties.sh_type == "DEC"):
			self.add_decal(scene, obj, isLast)
		
		elif (obj.sh_properties.sh_type == "POW"):
			self.add_powerup(scene, obj, isLast)
		
		elif (obj.sh_properties.sh_type == "WAT"):
			self.add_water(scene, obj, isLast)
	
	def write_file(self, path):
		"""
		Write the segment file(s)
		"""
		with open(path, "w") as f:
			f.write(et.tostring(self.level_content, encoding = "unicode"))
	
	def save_compressed(self, path):
		"""
		Save compressed segment file
		"""
		with gzip.open(path, "wb") as f:
			f.write(et.tostring(self.level_content, encoding = "unicode").encode())

###############################################################################

def sh_export_segment(fp, context, compress = False):
	"""
	This function exports the XML porition of the Smash Hit segment.
	"""
	
	context.window.cursor_set('WAIT')
	
	scene = context.scene
	
	level = Segment()
	level.add_root_element(scene)
	
	for i in range(len(bpy.data.objects)):
		obj = bpy.data.objects[i]
		
		# Skip if not being exported
		if (not obj.sh_properties.sh_export):
			continue
		
		# NOTE KSAM enhancement: hack to make last line not indented
		isLast = False
		if (i == (len(bpy.data.objects) - 1)):
			isLast = True
		
		# TODO: Update so only obj and scene need to be passed.
		level.add_object(scene, obj, isLast)
	
	# Write the file
	if (not compress):
		level.write_file(fp)
	else:
		level.save_compressed(fp)
	
	context.window.cursor_set('DEFAULT')
	return {"FINISHED"}

# Normal export segment

class sh_export(bpy.types.Operator, bpy_extras.io_utils.ExportHelper):
	bl_idname = "sh.export"
	bl_label = "Export Smash Hit Segment"
	
	filename_ext = ".xml.mp3"
	filter_glob = bpy.props.StringProperty(default='*.xml.mp3', options={'HIDDEN'}, maxlen=255)
	
	def execute(self, context):
		return sh_export_segment(self.filepath, context)

def sh_draw_export(self, context):
	self.layout.operator("sh.export", text="Smash Hit (.xml.mp3)")

# Compressed segment export

class sh_export_gz(bpy.types.Operator, bpy_extras.io_utils.ExportHelper):
	bl_idname = "sh.gzexport"
	bl_label = "Export Compressed Smash Hit Segment"
	
	filename_ext = ".xml.gz.mp3"
	filter_glob = bpy.props.StringProperty(default='*.xml.gz.mp3', options={'HIDDEN'}, maxlen=255)
	
	def execute(self, context):
		return sh_export_segment(self.filepath, context, True)

def sh_draw_export_gz(self, context):
	self.layout.operator("sh.gzexport", text="Smash Hit Compressed (.xml.gz.mp3)")

# What follows is mostly from the forementioned example, since I can't really
# be bothred to re-write the old exporter tool right now. Perhaps I will re-write
# it if there is a serious legal issue, but I doubt there will be.

SH_MAX_STR_LEN = 256

# Segment (scene) properties

class sh_scn_props(PropertyGroup):
	
	sh_stonehack: BoolProperty(
		name = "Export using stone hack",
		description = "Export using stone hack (requires stone obstacle to be in APK, not compatible with mesh files but needed for walls to visually appear)",
		default = True
		)
	
	sh_color: FloatVectorProperty(
		name = "Color",
		description = "Color when stone is exported (passed as param1 with name \'color\')",
		subtype = "COLOR",
		default = (0.0, 0.0, 0.0), 
		min = -1.0,
		max = 2.0
	) 
	
	sh_len: FloatVectorProperty(
		name = "Size",
		description = "Segment size (Width, Height, Depth). Hint: Last paramater changes the length (depth) of the segment",
		default = (12.0, 10.0, 8.0), 
		min = -1024.0,
		max = 1024.0
	) 

	sh_template: StringProperty(
		name = "Template",
		description = "The template paramater that is passed for the entire segment. This may not work.",
		default = "",
		maxlen = SH_MAX_STR_LEN,
		)
	
	sh_softshadow: FloatProperty(
		name = "Soft Shadow",
		description = "Shadow appearance",
		default = -0.001,
		min = -0.001,
		max = 1.0
		)

# Object (obstacle/powerup/decal/water) properties

class sh_obj_props(PropertyGroup):
	
	sh_template: StringProperty(
		name = "Template",
		description = "The template for the obstacle (see templates.xml)",
		default = "",
		maxlen = SH_MAX_STR_LEN,
		)
	
	sh_obstacle: StringProperty(
		name = "Type",
		description = "Obstacle type",
		default = "",
		maxlen = SH_MAX_STR_LEN,
		)
	
	sh_powerup: EnumProperty(
		name = "Power-up",
		description = "Power-up type",
		items = [ ('ballfrenzy', "Ball Frenzy", ""),
				  ('slowmotion', "Slow Motion", ""),
				  ('nitroballs', "Nitro Balls", ""),
				],
		default = "ballfrenzy"
		)
	
	sh_export: BoolProperty(
		name = "Export object",
		description = "If the object should be exported to the XML at all. Change hidden if you'd like it just to be hidden",
		default = True
		)
	
	sh_hidden: BoolProperty(
		name = "Hidden",
		description = "If the obstacle will show in the level",
		default = False
		)
	
	sh_mode: EnumProperty(
		name = "Mode",
		description = "The game mode that the obstacle will be shown in",
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
	
	##################
	# Mesh properties
	##################
	
	sh_visible: BoolProperty(
		name = "Visible",
		description = "If the box will have the tiles fixed to it (Note: does not work)",
		default = False
		)
	
	sh_tile: IntProperty(
		name = "Tile",
		description = "Tile",
		default = 1,
		min = 0,
		max = 63
		)
	
	sh_tilerot: FloatVectorProperty(
		name = "Tile Rotation",
		description = "Rotation of the tile, in radians (PI = 1/2 rotation)",
		default = (0.0, 0.0, 0.0), 
		min = 0.0,
		max = 6.28318530718
	) 
	
	sh_tilesize: FloatVectorProperty(
		name = "Tile size",
		description = "The appearing size of the tiles on the box when exported (third paramater is ignored)",
		default = (1.0, 1.0, 0.0), 
		min = 0.0,
		max = 128.0
	) 
	
	########################
	# Back to normal things
	########################
	
	sh_decal: IntProperty(
		name = "Decal",
		description = "The image ID for the decal (negitive numbers are doors)",
		default = 1,
		min = -4,
		max = 63
		)
	
	sh_reflective: BoolProperty(
		name = "Reflective",
		description = "If this box should show reflections",
		default = False
		)
	
	sh_type: EnumProperty(
		name = "This is a...",
		description = "The type of object that the currently selected object should be treated as",
		items = [ ('BOX', "Box", ""),
				  ('OBS', "Obstacle", ""),
				  ('DEC', "Decal", ""),
				  ('POW', "Power-up", ""),
				  ('WAT', "Water", ""),
				],
		default = "BOX"
		)
	
	#############
	# Paramaters
	#############
	
	sh_param0: StringProperty(
		name = "param0",
		description = ":",
		default = "",
		maxlen = SH_MAX_STR_LEN,
		)
	
	sh_param1: StringProperty(
		name = "param1",
		description = ":",
		default = "",
		maxlen = SH_MAX_STR_LEN,
		)
	
	sh_param2: StringProperty(
		name = "param2",
		description = ":",
		default = "",
		maxlen = SH_MAX_STR_LEN,
		)
	
	sh_param3: StringProperty(
		name = "param3",
		description = ":",
		default = "",
		maxlen = SH_MAX_STR_LEN,
		)
	
	sh_param4: StringProperty(
		name = "param4",
		description = ":",
		default = "",
		maxlen = SH_MAX_STR_LEN,
		)
	
	sh_param5: StringProperty(
		name = "param5",
		description = ":",
		default = "",
		maxlen = SH_MAX_STR_LEN,
		)
	
	sh_param6: StringProperty(
		name = "param6",
		description = ":",
		default = "",
		maxlen = SH_MAX_STR_LEN,
		)
	
	sh_param7: StringProperty(
		name = "param7",
		description = ":",
		default = "",
		maxlen = SH_MAX_STR_LEN,
		)
	
	sh_param8: StringProperty(
		name = "param8",
		description = ":",
		default = "",
		maxlen = SH_MAX_STR_LEN,
		)
	
	sh_param9: StringProperty(
		name = "param9",
		description = ":",
		default = "",
		maxlen = SH_MAX_STR_LEN,
		)
	
	sh_param10: StringProperty(
		name = "param10",
		description = ":",
		default = "",
		maxlen = SH_MAX_STR_LEN,
		)
	
	sh_param11: StringProperty(
		name = "param11",
		description = ":",
		default = "",
		maxlen = SH_MAX_STR_LEN,
		)
	
	###############
	# Other values
	###############
	
	sh_havetint: BoolProperty(
		name = "Colorise object",
		description = "Sets custom local wall color or changes the tint of the decal",
		default = False
		)
	
	sh_tint: FloatVectorProperty(
		name = "Color",
		description = "The color to be used for tinting or coloring",
		subtype = "COLOR",
		default = (1.0, 1.0, 1.0), 
		min = -1.0,
		max = 2.0
	) 
	
	sh_tintalpha: FloatProperty(
		name = "Tint alpha",
		description = "Alpha of the tint",
		default = 1.0,
		min = 0.0,
		max = 1.0
		)
	
	sh_size: FloatVectorProperty(
		name = "Size",
		description = "The size of the object when exported (third paramater is ignored). For boxes this is the tileSize property",
		default = (1.0, 1.0, 0.0), 
		min = 0.0,
		max = 128.0
	) 

class sh_panel_seg(Panel):
	bl_label = "Segment Properties"
	bl_idname = "OBJECT_PT_segment_panel"
	bl_space_type = "VIEW_3D"
	bl_region_type = "UI"
	bl_category = "Smash Hit"
	# bl_context = "objectmode"
	
	@classmethod
	def poll(self, context):
		return context.object is not None
	
	def draw(self, context):
		layout = self.layout
		scene = context.scene
		sh_properties = scene.sh_properties
		
		layout.prop(sh_properties, "sh_stonehack")
		if (sh_properties.sh_stonehack):
			layout.prop(sh_properties, "sh_color")
		layout.prop(sh_properties, "sh_len")
		layout.prop(sh_properties, "sh_template")
		layout.prop(sh_properties, "sh_softshadow")
		layout.separator()

class sh_panel_obs(Panel):
	bl_label = "Object Properties"
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
		
		# All objects will have all properties, but only some will be used for
		# each of obstacle there is.
		layout.prop(sh_properties, "sh_type")
		
		# Obstacle type for obstacles
		if (sh_properties.sh_type == "OBS"):
			layout.prop(sh_properties, "sh_obstacle")
		
		# Decal number for decals
		if (sh_properties.sh_type == "DEC"):
			layout.prop(sh_properties, "sh_decal")
		
		# Colorization for decals and boxes
		if (   sh_properties.sh_type == "DEC"
			or sh_properties.sh_type == "BOX"):
			layout.prop(sh_properties, "sh_havetint")
			if (sh_properties.sh_havetint):
				layout.prop(sh_properties, "sh_tint")
				if (sh_properties.sh_type == "DEC"):
					layout.prop(sh_properties, "sh_tintalpha")
		
		# Template for obstacles
		if (sh_properties.sh_type == "OBS"):
			layout.prop(sh_properties, "sh_template")
			layout.prop(sh_properties, "sh_mode")
		
		# Power-up name for power-ups
		if (sh_properties.sh_type == "POW"):
			layout.prop(sh_properties, "sh_powerup")
		
		# Size for water and decals
		if (   sh_properties.sh_type == "WAT"
			or sh_properties.sh_type == "DEC"):
			layout.prop(sh_properties, "sh_size")
		
		# Hidden property
		layout.prop(sh_properties, "sh_hidden")
		
		# Refelective and tile property for boxes
		if (sh_properties.sh_type == "BOX"):
			layout.prop(sh_properties, "sh_reflective")
			layout.prop(sh_properties, "sh_visible")
			if (sh_properties.sh_visible):
				layout.prop(sh_properties, "sh_tile")
				layout.prop(sh_properties, "sh_tilesize")
				layout.prop(sh_properties, "sh_tint")
				layout.prop(sh_properties, "sh_tilerot")
		
		# Paramaters for boxes
		if (sh_properties.sh_type == "OBS"):
			layout.prop(sh_properties, "sh_param0")
			layout.prop(sh_properties, "sh_param1")
			layout.prop(sh_properties, "sh_param2")
			layout.prop(sh_properties, "sh_param3")
			layout.prop(sh_properties, "sh_param4")
			layout.prop(sh_properties, "sh_param5")
			layout.prop(sh_properties, "sh_param6")
			layout.prop(sh_properties, "sh_param7")
			layout.prop(sh_properties, "sh_param8")
			layout.prop(sh_properties, "sh_param9")
			layout.prop(sh_properties, "sh_param10")
			layout.prop(sh_properties, "sh_param11")
		
		# Option to export object or not
		layout.prop(sh_properties, "sh_export")
		
		# Separator
		layout.separator()
		
classes = (
	# Ignore the naming scheme for classes, please
	sh_scn_props,
	sh_obj_props,
	sh_panel_seg,
	sh_panel_obs,
	sh_export,
	sh_export_gz
)

def register():
	from bpy.utils import register_class
	for cls in classes:
		register_class(cls)

	bpy.types.Scene.sh_properties = PointerProperty(type=sh_scn_props)
	bpy.types.Object.sh_properties = PointerProperty(type=sh_obj_props)
	
	# Add the export operator to menu
	bpy.types.TOPBAR_MT_file_export.append(sh_draw_export)
	bpy.types.TOPBAR_MT_file_export.append(sh_draw_export_gz)

def unregister():
	from bpy.utils import unregister_class
	for cls in reversed(classes):
		unregister_class(cls)
	del bpy.types.Scene.sh_properties
