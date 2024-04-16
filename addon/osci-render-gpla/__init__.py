bl_info = {
    "name": "osci-render GPLA exporter",
    "blender": (4, 0, 0),
    "category": "Render",
}

import bpy
import os
import bmesh
import atexit
import json
from bpy.app.handlers import persistent
from bpy_extras.io_utils import ImportHelper

filename = None
extension = None
FilePath = None

class or_gpla_export(bpy.types.Panel):
    """Export grease pencil frames to a file for osci-render"""      # Use this as a tooltip for menu items and buttons.
    bl_idname = "or_gpla_export"        # Unique identifier for buttons and menu items to reference.
    bl_label = "Export GPLA to file"         # Display name in the interface.
    bl_space_type = "PROPERTIES"  
    bl_region_type = "WINDOW"
    bl_context = "render"
    
    def draw_header(self,context):
        layout = self.layout

    def draw(self, context):
        global filename
        global extension
        if filename is None or extension is None:
            self.layout.operator("render.or_gpla_choose_file", text="Choose File")
        else:
            self.layout.operator("render.or_gpla_close_file", text="Close File")
            self.layout.operator("render.or_gpla_save", text="Save Line Art")

class or_gpla_choose_file(bpy.types.Operator, ImportHelper):
    bl_label = "Choose File"
    bl_idname = "render.or_gpla_choose_file"
    bl_description = "Choose File"
    filter_glob: bpy.props.StringProperty(
        default='*.gpla',
        options={'HIDDEN'}
    )
    
    def execute(self,context):
        global filename
        global extension
        global FilePath
        try:
            FilePath = self.filepath
            filename, extension = os.path.splitext(self.filepath)
            if (extension != ".gpla"):
                extension = ".gpla"
                FilePath = FilePath + ".gpla"
            self.report({"INFO"}, FilePath)
        except:
            flename = None
            extension = None
            self.report({"WARNING"},"Something got screwed up when choosing a filename")
            return {"CANCELLED"}
        return {"FINISHED"}
    
class or_gpla_close_file(bpy.types.Operator):
    bl_label = "Close File"
    bl_idname = "render.or_gpla_close_file"
    bl_description = "Close File"
    
    def execute(self,context):
        if (close_file == False):
            return {"FINISHED"}
        else:
            return {"CANCELLED"}
    
class or_gpla_save(bpy.types.Operator):
    bl_label = "Save Line Art"
    bl_idname = "render.or_gpla_save"
    bl_description = "Save line art to the chosen file"
    
    def execute(self,context):
        global filename
        global extension
        if filename is not None and extension is not None:
            fin = save_scene_to_file(bpy.context.scene)
            if (fin == 0):
                self.report({"INFO"}, "File write successful!")
                return {"FINISHED"}
            else:
                self.report({"WARNING"}, "Something went wrong in saving the file")
        else:
            filename = None
            extension = None
            self.report({"WARNING"}, "The filename or extension isn't right, action stopped for your own safety")
            return {"CANCELLED"}
    
@persistent
def close_file():
    global filename
    global extension
    filename = None
    extension = None
    return 0

def append_matrix(object_info, obj):
    camera_space = bpy.context.scene.camera.matrix_world.inverted() @ obj.matrix_world
    object_info["matrix"] = [camera_space[i][j] for i in range(4) for j in range(4)]
    return object_info

@persistent
def save_scene_to_file(scene):
    global filename
    global extension
    global FilePath
    returnFrame = scene.frame_current
    
    scene_info = {"frames": []}
    for frame in range(0, scene.frame_end - scene.frame_start):
        frame_info = {"objects": []}
        scene.frame_set(frame + scene.frame_start)
        for obj in bpy.data.objects:
            if obj.visible_get() and obj.type == 'GPENCIL':
                object_info = {"name": obj.name}
                strokes = obj.data.layers.active.frames.data.frames[frame+1].strokes                    
                
                object_info["vertices"] = []
                for stroke in strokes:
                    object_info["vertices"].append([{
                        "x": vert.co[0],
                        "y": vert.co[1],
                        "z": vert.co[2],
                    } for vert in stroke.points])
                
                frame_info["objects"].append(append_matrix(object_info, obj))
        
        frame_info["focalLength"] = -0.05 * bpy.data.cameras[0].lens
        scene_info["frames"].append(frame_info)

    json_str = json.dumps(scene_info, separators=(',', ':'))
    
    if (FilePath is not None):
        f = open(FilePath, "w")
        f.write(json_str)
        f.close()
    else:
        return 1
        
    scene.frame_set(returnFrame)
    return 0

operations = [or_gpla_export, or_gpla_choose_file, or_gpla_close_file, or_gpla_save]

def register():
    atexit.register(close_file)
    for op in operations:
        bpy.utils.register_class(op)

def unregister():
    bpy.utils.unregister_class(ObjectMoveX)


# This allows you to run the script directly from Blender's Text editor
# to test the add-on without having to install it.
if __name__ == "__main__":
    register()