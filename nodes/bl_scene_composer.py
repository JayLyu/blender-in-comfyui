import json
import os
import subprocess
import folder_paths

from .blender_manager import BlenderManager

class BL_Scene_Composer:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "models": ("MODELS",),
                "use_full_path": ("BOOLEAN", {"default": True}),
                "output_folder": ("STRING", {"default": "blender"}),
                "output_filename": ("STRING", {"default": "scene"}),
            },
            "optional": {
                "blend_path": ("STRING", {"default": ""}),
            },
            "hidden": {
                "background_color": ("STRING", {"default": "white", "multiline": False}),
            }
        }

    RETURN_TYPES = ("STRING", "STRING",)
    RETURN_NAMES = ("blend_path", "log",)
    FUNCTION = "compose_scene"
    CATEGORY = "Blender"
    DESCRIPTION = "Compose 3D models into a Blender scene"

    def compose_scene(self, models, output_folder="blender", output_filename="scene", 
                     blend_path="", background_color="white", use_full_path=True):
        # 初始化日志
        log_messages = []
        log_messages.append(f"Starting scene composition...")
        log_messages.append(f"Use full path: {use_full_path}")
        
        # 检查输入模型
        if models is None:
            error_msg = "No models provided"
            log_messages.append(f"ERROR: {error_msg}")
            return ("", "\n".join(log_messages))
        
        # 标准化模型列表
        if isinstance(models, dict):
            models_list = [models]
        else:
            models_list = models
        
        log_messages.append(f"Processing {len(models_list)} objects")
        
        # Path configuration
        blender_bin = BlenderManager().get_blender_path()
        
        # 获取ComfyUI输出目录
        output_dir = folder_paths.get_output_directory()
        output_dir = os.path.join(output_dir, output_folder)
        os.makedirs(output_dir, exist_ok=True)
        
        # 计算完整输出路径
        full_output_path = os.path.join(output_dir, f"{output_filename}.blend")
        
        # 确定输出blend文件路径
        if blend_path and blend_path.strip():
            # 检查源文件是否存在
            if not os.path.exists(blend_path):
                error_msg = f"Source blend file not found: {blend_path}"
                log_messages.append(f"ERROR: {error_msg}")
                return ("", "\n".join(log_messages))
            
            # 复制源文件到输出目录
            import shutil
            try:
                shutil.copy2(blend_path, full_output_path)
                log_messages.append(f"Copied source blend file: {blend_path} -> {full_output_path}")
            except Exception as e:
                error_msg = f"Failed to copy blend file: {e}"
                log_messages.append(f"ERROR: {error_msg}")
                return ("", "\n".join(log_messages))
            
            # 根据设置确定返回的路径格式
            if use_full_path:
                output_blend = full_output_path
            else:
                output_blend = f"{output_folder}/{output_filename}.blend"
            
            log_messages.append(f"Using copied blend file: {output_blend}")
            mode = "append"
        else:
            # 根据设置确定返回的路径格式
            if use_full_path:
                output_blend = full_output_path
            else:
                output_blend = f"{output_folder}/{output_filename}.blend"
            log_messages.append(f"Creating new blend file: {output_blend}")
            mode = "create"
        
        # 检查所有模型文件是否存在（跳过摄像机）
        for model in models_list:
            if model.get("type") != "camera" and not os.path.exists(model["file_path"]):
                error_msg = f"Model file not found: {model['file_path']}"
                log_messages.append(f"ERROR: {error_msg}")
                return (output_blend, "\n".join(log_messages))
        
        # 准备模型数据，确保浮点数格式正确
        def format_float(value):
            if isinstance(value, (list, tuple)):
                return [format_float(v) for v in value]
            elif isinstance(value, float):
                return round(value, 6)  # 限制小数位数
            return value
        
        formatted_models = []
        for model in models_list:
            if model.get("type") == "camera":
                # 摄像机数据
                formatted_model = {
                    "type": "camera",
                    "name": model["name"],
                    "position": format_float(model["position"]),
                    "rotation": format_float(model["rotation"]),
                    "scale": format_float(model["scale"]),
                    "collection_name": model["collection_name"],
                    "focal_length": model["focal_length"]
                }
            else:
                # 3D模型数据
                formatted_model = {
                    "type": "model",
                    "file_path": model["file_path"],
                    "position": format_float(model["position"]),
                    "rotation": format_float(model["rotation"]),
                    "scale": format_float(model["scale"]),
                    "name": model["name"],
                    "file_format": model.get("file_format", os.path.splitext(model["file_path"])[1].lower())
                }
            formatted_models.append(formatted_model)
        
        # 准备参数数据
        params = {
            "output_blend": output_blend,
            "output_dir": output_dir,
            "mode": mode,
            "background_color": background_color,
            "models_data": formatted_models
        }
        
        # 将参数写入JSON文件
        param_json_path = os.path.join(output_dir, f"{output_filename}_composer_params.json")
        with open(param_json_path, "w", encoding="utf-8") as f:
            json.dump(params, f, ensure_ascii=False, indent=2)
        
        # 准备Blender脚本内容
        script_content = _BLENDER_COMPOSER_SCRIPT
        
        # 写入临时脚本文件
        script_path = os.path.join(output_dir, f"{output_filename}_composer_script.py")
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(script_content)
        
        # 调用Blender执行脚本
        cmd = [blender_bin, "--background", "--factory-startup", "--python", script_path, "--", param_json_path]
        try:
            subprocess.run(cmd, check=True)
            log_messages.append(f"Blender scene composition successful: {output_blend}")
            log_messages.append(f"Full path: {full_output_path}")
            
            # 添加处理信息到日志
            for model in models_list:
                log_messages.append(f"Model: {model['name']}")
                log_messages.append(f"  Position: {model['position']}")
                log_messages.append(f"  Rotation: {model['rotation']}")
                log_messages.append(f"  Scale: {model['scale']}")
            
        except Exception as e:
            log_messages.append(f"Blender call failed: {e}")
            return (output_blend, "\n".join(log_messages))
        
        return (output_blend, "\n".join(log_messages))

# Blender scene composition script
_BLENDER_COMPOSER_SCRIPT = r'''
import bpy
import sys
import os
import json
import math

# Get parameters
param_json = None
for i, arg in enumerate(sys.argv):
    if arg.endswith("_composer_params.json"):
        param_json = arg
        break
if not param_json:
    print("No param json found!")
    sys.exit(1)

with open(param_json, "r", encoding="utf-8") as f:
    params = json.load(f)

output_blend = params["output_blend"]
output_dir = params["output_dir"]
mode = params["mode"]
background_color = params["background_color"]
models_data = params["models_data"]

# Initialize Blender scene
if mode == "create":
    # Create new empty scene
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.unit_settings.system = 'METRIC'
    bpy.context.scene.unit_settings.scale_length = 1.0
    print("Initialized empty Blender scene")
else:
    # Load existing blend file (which is now a copy in the output directory)
    try:
        bpy.ops.wm.open_mainfile(filepath=output_blend)
        print(f"Loaded copied blend file: {output_blend}")
    except Exception as e:
        print(f"Error loading blend file: {e}")
        # Fallback to empty scene if loading fails
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.context.scene.unit_settings.system = 'METRIC'
        bpy.context.scene.unit_settings.scale_length = 1.0
        print("Fallback to empty scene")

# Function to get unique collection name
def get_unique_collection_name(base_name):
    if base_name not in bpy.data.collections:
        return base_name
    
    counter = 1
    while f"{base_name}_{counter}" in bpy.data.collections:
        counter += 1
    
    return f"{base_name}_{counter}"

# Import all 3D models and create cameras
total_imported = 0
for model_data in models_data:
    try:
        object_type = model_data.get("type", "model")
        position = model_data["position"]
        rotation = model_data["rotation"]
        scale = model_data["scale"]
        name = model_data["name"]
        
        if object_type == "camera":
            # Create camera
            focal_length = model_data["focal_length"]
            collection_name = model_data["collection_name"]
            
            print(f"Creating camera: {name}")
            
            # Get unique collection name
            unique_collection_name = get_unique_collection_name(collection_name)
            
            # Create or get collection
            if unique_collection_name in bpy.data.collections:
                target_collection = bpy.data.collections[unique_collection_name]
                print(f"Using existing collection: {unique_collection_name}")
            else:
                target_collection = bpy.data.collections.new(unique_collection_name)
                bpy.context.scene.collection.children.link(target_collection)
                print(f"Created new collection: {unique_collection_name}")
            
            # Create camera data
            camera_data = bpy.data.cameras.new(name=name)
            camera_data.lens = focal_length
            
            # Create camera object
            camera_obj = bpy.data.objects.new(name, camera_data)
            target_collection.objects.link(camera_obj)
            
            # Apply position and rotation to camera
            camera_obj.location = position
            
            # Set rotation using XYZ Euler (convert degrees to radians)
            def normalize_rotation(angle_degrees):
                """Convert degrees to radians and normalize to -π to π range"""
                angle_rad = math.radians(angle_degrees)
                # Normalize to -π to π range
                while angle_rad > math.pi:
                    angle_rad -= 2 * math.pi
                while angle_rad < -math.pi:
                    angle_rad += 2 * math.pi
                return angle_rad
            
            # Calculate normalized rotations
            x_rot = normalize_rotation(rotation[0])
            y_rot = normalize_rotation(rotation[1])
            z_rot = normalize_rotation(rotation[2])
            
            # Ensure rotation mode is set to XYZ Euler
            camera_obj.rotation_mode = 'XYZ'
            camera_obj.rotation_euler = (x_rot, y_rot, z_rot)
            
            print(f"Created camera '{name}' with focal length {focal_length}mm at position {position} with rotation {rotation}")
            total_imported += 1
            
        else:
            # Import 3D model
            model_file_path = model_data["file_path"]
            file_format = model_data.get("file_format", "")
            collection_name = model_data.get("collection_name", "3D_Model")
            
            print(f"Importing {file_format.upper()} model: {name}")
            
            # Get unique collection name
            unique_collection_name = get_unique_collection_name(collection_name)
            
            # Create or get collection
            if unique_collection_name in bpy.data.collections:
                target_collection = bpy.data.collections[unique_collection_name]
                print(f"Using existing collection: {unique_collection_name}")
            else:
                target_collection = bpy.data.collections.new(unique_collection_name)
                bpy.context.scene.collection.children.link(target_collection)
                print(f"Created new collection: {unique_collection_name}")
            
            # Record objects before import
            objects_before = set(bpy.context.scene.objects)
            
            # Import model based on file format
            if file_format in ['.glb', '.gltf']:
                bpy.ops.import_scene.gltf(filepath=model_file_path)
            elif file_format == '.fbx':
                bpy.ops.import_scene.fbx(filepath=model_file_path)
            elif file_format == '.obj':
                bpy.ops.import_scene.obj(filepath=model_file_path)
            else:
                print(f"Unsupported file format: {file_format}")
                continue
        
            # Get newly imported objects
            objects_after = set(bpy.context.scene.objects)
            new_objects = objects_after - objects_before
            
            # Find root objects (objects without parents or with parents not in the new objects)
            root_objects = []
            for obj in new_objects:
                if obj.type in ['MESH', 'EMPTY', 'ARMATURE']:
                    # Check if this is a root object
                    is_root = True
                    if obj.parent is not None:
                        # If parent is also in new_objects, this is not a root
                        if obj.parent in new_objects:
                            is_root = False
                    
                    if is_root:
                        root_objects.append(obj)
            
            print(f"Found {len(root_objects)} root objects from {name} (total {len(new_objects)} objects)")
            
            # Create a parent Empty object to contain all imported objects as a group
            parent_empty = bpy.data.objects.new(f"{name}_container", None)
            parent_empty.empty_display_type = 'ARROWS'
            target_collection.objects.link(parent_empty)

            # Set parent empty transformations
            parent_empty.location = position
            def normalize_rotation(angle_degrees):
                angle_rad = math.radians(angle_degrees)
                while angle_rad > math.pi:
                    angle_rad -= 2 * math.pi
                while angle_rad < -math.pi:
                    angle_rad += 2 * math.pi
                return angle_rad
            x_rot = normalize_rotation(rotation[0])
            y_rot = normalize_rotation(rotation[1])
            z_rot = normalize_rotation(rotation[2])
            parent_empty.rotation_mode = 'XYZ'
            parent_empty.rotation_euler = (x_rot, y_rot, z_rot)
            parent_empty.scale = scale

            print(f"Created parent container '{parent_empty.name}' with transformations: pos{position} rot{rotation} scale{scale}")

            # Parent all new_objects to container, and restore hidden state
            for obj in new_objects:
                # Save original hidden state
                original_hide_viewport = obj.hide_viewport
                original_hide_render = obj.hide_render
                original_hide_set = obj.hide_set

                # Move to target collection
                for collection in obj.users_collection:
                    collection.objects.unlink(obj)
                target_collection.objects.link(obj)

                # parent to container
                obj.parent = parent_empty

                # Restore hidden state
                obj.hide_viewport = original_hide_viewport
                obj.hide_render = original_hide_render
                obj.hide_set = original_hide_set

                print(f"Parented {obj.name} to container '{parent_empty.name}' (hidden: {original_hide_viewport})")
            
            total_imported += len(root_objects)
        
    except Exception as e:
        print(f"Error processing object {name}: {e}")

# Set world background
if bpy.context.scene.world is None:
    bpy.context.scene.world = bpy.data.worlds.new("World")
bpy.context.scene.world.use_nodes = True
bg = bpy.context.scene.world.node_tree.nodes.get("Background")
if bg:
    if background_color.lower() == "white":
        bg.inputs[0].default_value = (1, 1, 1, 1)
    elif background_color.lower() == "black":
        bg.inputs[0].default_value = (0, 0, 0, 1)
    elif background_color.lower() == "gray":
        bg.inputs[0].default_value = (0.5, 0.5, 0.5, 1)
    else:
        # Try to parse color values
        try:
            color_values = [float(x) for x in background_color.split(',')]
            if len(color_values) >= 3:
                bg.inputs[0].default_value = (color_values[0], color_values[1], color_values[2], 1)
        except:
            bg.inputs[0].default_value = (1, 1, 1, 1)  # Default white
    print(f"Set background color: {background_color}")

# Create output directory
os.makedirs(output_dir, exist_ok=True)

# Save blend file (direct overwrite)
bpy.ops.wm.save_as_mainfile(filepath=output_blend)
print(f"Saved blend file: {output_blend}")
print(f"Successfully composed scene with {total_imported} objects from {len(models_data)} items")
''' 