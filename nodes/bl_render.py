import json
import os
import subprocess
import torch
import numpy as np

from PIL import Image, ImageOps
from .blender_manager import BlenderManager


class BL_Render:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "blend_file_path": ("STRING", {"default": ""}),
                "camera_name": ("STRING", {"default": "camera"}),
                "use_cycles": ("BOOLEAN", {"default": False}),
                "samples": ("INT", {"default": 256, "min": 32, "max": 4096, "step": 8}),
                "image_format": (["PNG", "JPEG"], {"default": "PNG"}),
                "resolution_x": ("INT", {"default": 1536, "min": 400, "max": 2048, "step": 8, "display": "slider"}),
                "resolution_y": ("INT", {"default": 846, "min": 400, "max": 2048, "step": 8, "display": "slider"}),
            },
            "optional": {
                "output_folder": ("STRING", {"default": "blender"}),
                "output_filename": ("STRING", {"default": "render"}),
            }
        }

    RETURN_TYPES = ("STRING", "IMAGE", "STRING",)
    RETURN_NAMES = ("blend_path", "image", "log",)
    FUNCTION = "render_scene"
    CATEGORY = "Blender"
    DESCRIPTION = "从指定blend文件中渲染3D场景"

    def render_scene(self, blend_file_path, camera_name="camera", output_filename="render", samples=256,
                     output_folder="renders", use_cycles=False, image_format="PNG", resolution_x=1536, 
                     resolution_y=846):
        # 初始化日志
        log_messages = []
        log_messages.append(f"Starting render process...")
        log_messages.append(f"Blend file: {blend_file_path}")
        log_messages.append(f"Camera name: {camera_name}")
        log_messages.append(f"Samples: {samples}")
        log_messages.append(f"Resolution: {resolution_x}x{resolution_y}")
        log_messages.append(f"Format: {image_format}")
        log_messages.append(f"Engine: {'Cycles' if use_cycles else 'Eevee Next'}")
        
        # Path configuration - 使用ComfyUI标准路径
        blender_bin = BlenderManager().get_blender_path()
        
        # 获取ComfyUI输出目录
        import folder_paths
        output_dir = folder_paths.get_output_directory()
        output_dir = os.path.join(output_dir, output_folder)
        os.makedirs(output_dir, exist_ok=True)
        
        # Check if source blend file exists
        if not os.path.exists(blend_file_path):
            error_msg = f"Source blend file not found: {blend_file_path}"
            log_messages.append(f"ERROR: {error_msg}")
            # 返回全黑图片
            black_image = torch.zeros((1, resolution_y, resolution_x, 3), dtype=torch.float32)
            return (blend_file_path, black_image, "\n".join(log_messages))
        
        # Prepare parameters for Blender script
        params = {
            "blend_file_path": blend_file_path,
            "output_dir": output_dir,
            "camera_name": camera_name,
            "use_cycles": use_cycles,
            "samples": samples,
            "resolution_x": resolution_x,
            "resolution_y": resolution_y,
            "image_format": image_format,
            "output_filename": output_filename
        }
        
        # Write parameters to JSON file
        param_json = os.path.join(output_dir, "_render_params.json")
        with open(param_json, "w") as f:
            json.dump(params, f, default=str)
        
        # Write Blender script
        script_path = os.path.join(output_dir, "_render_blender_script.py")
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(_BLENDER_RENDER_SCRIPT)
        
        # Call Blender
        cmd = [blender_bin, "--background", "--factory-startup", "--python", script_path, "--", param_json]
        try:
            subprocess.run(cmd, check=True)
            log_messages.append(f"Blender render successful")
        except Exception as e:
            log_messages.append(f"Blender call failed: {e}")
            # 返回全黑图片
            black_image = torch.zeros((1, resolution_y, resolution_x, 3), dtype=torch.float32)
            return (blend_file_path, black_image, "\n".join(log_messages))
        
        # Read render results
        rendered_json = os.path.join(output_dir, "render_result.json")
        if os.path.exists(rendered_json):
            with open(rendered_json, "r") as f:
                render_result = json.load(f)
                log_messages.append(f"Render result: {render_result.get('status', 'unknown')}")
        else:
            render_result = {"status": "error", "message": "Render result file not found"}
            log_messages.append(f"ERROR: Render result file not found")
        
        # Read image as ComfyUI IMAGE format
        def pil2tensor(image):
            image = ImageOps.exif_transpose(image)
            arr = np.array(image).astype(np.float32) / 255.0  # (H, W, 3)
            if arr.ndim == 2:  # Grayscale image
                arr = np.stack([arr]*3, axis=-1)
            if arr.shape[-1] == 4:  # RGBA to RGB
                arr = arr[..., :3]
            arr = arr[None, ...]  # (1, H, W, 3)
            return torch.from_numpy(arr).float()
        
        # Check if camera was found and image was rendered
        if render_result.get("status") == "success" and render_result.get("image_path"):
            image_path = render_result["image_path"]
            if os.path.exists(image_path):
                try:
                    img = Image.open(image_path).convert("RGB")
                    tensor = pil2tensor(img)
                    log_messages.append(f"Image loaded successfully: {image_path}")
                    return (blend_file_path, tensor, "\n".join(log_messages))
                except Exception as e:
                    log_messages.append(f"ERROR: Failed to load image: {e}")
            else:
                log_messages.append(f"ERROR: Rendered image file not found: {image_path}")
        else:
            log_messages.append(f"ERROR: {render_result.get('message', 'Unknown render error')}")
        
        # 返回全黑图片
        black_image = torch.zeros((1, resolution_y, resolution_x, 3), dtype=torch.float32)
        return (blend_file_path, black_image, "\n".join(log_messages))

# Independent Blender script content
_BLENDER_RENDER_SCRIPT = r'''
import bpy
import sys
import os
import json
import math

# Get parameters
param_json = None
for i, arg in enumerate(sys.argv):
    if arg.endswith("_render_params.json"):
        param_json = arg
        break
if not param_json:
    print("No param json found!")
    sys.exit(1)

with open(param_json, "r") as f:
    params = json.load(f)

blend_file_path = params["blend_file_path"]
output_dir = params["output_dir"]
camera_name = params["camera_name"]
use_cycles = params["use_cycles"]
samples = params["samples"]
resolution_x = params["resolution_x"]
resolution_y = params["resolution_y"]
image_format = params["image_format"]
output_filename = params["output_filename"]

# Initialize Blender scene
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.scene.unit_settings.system = 'METRIC'
bpy.context.scene.unit_settings.scale_length = 1.0

# Load the blend file
try:
    bpy.ops.wm.open_mainfile(filepath=blend_file_path)
    print(f"Successfully loaded blend file: {blend_file_path}")
except Exception as e:
    print(f"Error loading blend file: {e}")
    result = {"status": "error", "message": f"Failed to load blend file: {e}"}
    with open(os.path.join(output_dir, "render_result.json"), "w") as f:
        json.dump(result, f)
    sys.exit(1)

# Find camera by name
target_camera = None
for obj in bpy.data.objects:
    if obj.type == "CAMERA" and obj.name.lower() == camera_name.lower():
        target_camera = obj
        break

if not target_camera:
    print(f"Camera '{camera_name}' not found in blend file")
    result = {"status": "error", "message": f"Camera '{camera_name}' not found"}
    with open(os.path.join(output_dir, "render_result.json"), "w") as f:
        json.dump(result, f)
    sys.exit(1)

print(f"Found camera: {target_camera.name}")

# Set render engine
if use_cycles:
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.cycles.samples = samples
    bpy.context.scene.cycles.use_denoising = True
    bpy.context.scene.cycles.device = 'GPU'
    print("Using Cycles render engine")
else:
    bpy.context.scene.render.engine = 'BLENDER_EEVEE_NEXT'
    bpy.context.scene.eevee.taa_render_samples = samples
    bpy.context.scene.eevee.use_raytracing = True
    bpy.context.scene.eevee.ray_tracing_options.resolution_scale = '1'
    bpy.context.scene.eevee.fast_gi_resolution = '1'
    print("Using Eevee Next render engine")

# Set image size and format
bpy.context.scene.render.resolution_x = resolution_x
bpy.context.scene.render.resolution_y = resolution_y
bpy.context.scene.render.image_settings.file_format = image_format
print(f"Set resolution: {resolution_x}x{resolution_y}, format: {image_format}")

# Set world background to white
if bpy.context.scene.world is None:
    bpy.context.scene.world = bpy.data.worlds.new("World")
bpy.context.scene.world.use_nodes = True
bg = bpy.context.scene.world.node_tree.nodes.get("Background")
if bg:
    bg.inputs[0].default_value = (1,1,1,1)
print("Set white background")

# Set camera
bpy.context.scene.camera = target_camera
print(f"Set active camera: {target_camera.name}")

# Create output directory
os.makedirs(output_dir, exist_ok=True)

# Render image
img_path = os.path.join(output_dir, f"{output_filename}.{image_format.lower()}")
bpy.context.scene.render.filepath = img_path

try:
    bpy.ops.render.render(write_still=True)
    print(f"Render completed: {img_path}")
    result = {
        "status": "success",
        "image_path": img_path,
        "camera_name": target_camera.name,
        "resolution": f"{resolution_x}x{resolution_y}",
        "format": image_format,
        "engine": bpy.context.scene.render.engine
    }
except Exception as e:
    print(f"Render failed: {e}")
    result = {"status": "error", "message": f"Render failed: {e}"}

# Output render results
with open(os.path.join(output_dir, "render_result.json"), "w") as f:
    json.dump(result, f, indent=2)
''' 