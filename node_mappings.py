import importlib

# define colors
blue = "\033[34m"
green = "\033[92m"
color_end = "\033[0m"

node_module_mappings = {
    'bl_camera_creator': 'BL_Camera_Creator',
    'bl_model_param': 'BL_Model_Param',
    'bl_model_merger': 'BL_Model_Merger',
    'bl_scene_composer': 'BL_Scene_Composer',
    'bl_render': 'BL_Render',
    'bl_export_model': 'BL_Export_Model',
}

imported_classes = {}

for module_name, class_name in node_module_mappings.items():
    try:
        module = importlib.import_module(f'.nodes.{module_name}', package=__package__)
        imported_class = getattr(module, class_name)
        imported_classes[class_name] = imported_class
    except ImportError as e:
        print(f"{blue}Blender in ComfyUI:{green} Import {module_name} failed: {str(e)}{color_end}")
    except AttributeError:
        print(f"{blue}Blender in ComfyUI:{green} On {module_name} cannot find {class_name}{color_end}")


NODE_CLASS_MAPPINGS = {class_name: imported_classes.get(class_name) for class_name in node_module_mappings.values()}


NODE_DISPLAY_NAME_MAPPINGS = {
    "BL_Camera_Creator": "Camera Creator",
    "BL_Model_Param": "3D Model Param",
    "BL_Model_Merger": "3D Model Merger",
    "BL_Scene_Composer": "Blender Scene Composer",
    "BL_Render": "Blender Render",
    "BL_Export_Model": "Blender Export Model",
}