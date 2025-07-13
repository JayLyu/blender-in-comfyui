import json
import os
import subprocess

# 尝试导入 ComfyUI 的 folder_paths，如果失败则使用备用方案
try:
    import folder_paths
    FOLDER_PATHS_AVAILABLE = True
except ImportError:
    FOLDER_PATHS_AVAILABLE = False
    print("Warning: folder_paths not available, using fallback path handling")

from .blender_manager import BlenderManager

class BL_Export_Model:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "blend_file_path": ("STRING", {"default": ""}),
                "export_format": (["GLB"], {"default": "GLB"}),
                "use_full_path": ("BOOLEAN", {"default": False}),
                "output_folder": ("STRING", {"default": "exported_models"}),
                "output_filename": ("STRING", {"default": "exported_model"}),
            },
            "optional": {
                "export_selected_only": ("BOOLEAN", {"default": False}),
                "apply_transforms": ("BOOLEAN", {"default": True}),
                "include_animations": ("BOOLEAN", {"default": True}),
                "include_textures": ("BOOLEAN", {"default": True}),
            }
        }

    RETURN_TYPES = ("STRING", "STRING",)
    RETURN_NAMES = ("exported_path", "log",)
    FUNCTION = "export_model"
    CATEGORY = "Blender"
    DESCRIPTION = "将Blender文件导出为GLB格式"

    def _get_output_directory(self, output_folder):
        """获取输出目录路径，支持 ComfyUI 环境和独立调试环境"""
        if FOLDER_PATHS_AVAILABLE:
            # 在 ComfyUI 环境中使用 folder_paths
            base_dir = folder_paths.get_output_directory()
        else:
            # 在独立调试环境中使用当前目录
            base_dir = os.path.join(os.getcwd(), "output")
        
        output_dir = os.path.join(base_dir, output_folder)
        os.makedirs(output_dir, exist_ok=True)
        return output_dir
    
    def _resolve_blend_file_path(self, blend_file_path):
        """解析blend文件路径，支持相对路径和绝对路径"""
        if not blend_file_path or not blend_file_path.strip():
            return None
        
        # 如果是绝对路径且文件存在，直接返回
        if os.path.isabs(blend_file_path) and os.path.exists(blend_file_path):
            return blend_file_path
        
        # 尝试在 ComfyUI 输出目录中查找
        if FOLDER_PATHS_AVAILABLE:
            try:
                comfyui_output = folder_paths.get_output_directory()
                full_path = os.path.join(comfyui_output, blend_file_path)
                if os.path.exists(full_path):
                    return full_path
            except:
                pass
        
        # 尝试在当前工作目录中查找
        current_dir_path = os.path.join(os.getcwd(), blend_file_path)
        if os.path.exists(current_dir_path):
            return current_dir_path
        
        # 如果都找不到，返回原始路径（让调用者处理错误）
        return blend_file_path

    def export_model(self, blend_file_path, export_format="GLB", output_folder="exported_models", 
                    output_filename="exported_model", export_selected_only=False, 
                    apply_transforms=True, include_animations=True, include_textures=True, use_full_path=False):
        # 初始化日志
        log_messages = []
        log_messages.append(f"Starting model export...")
        log_messages.append(f"Format: {export_format}")
        log_messages.append(f"Selected only: {export_selected_only}")
        log_messages.append(f"Apply transforms: {apply_transforms}")
        log_messages.append(f"Include animations: {include_animations}")
        log_messages.append(f"Include textures: {include_textures}")
        log_messages.append(f"Use full path: {use_full_path}")
        
        # 解析blend文件路径
        resolved_blend_path = self._resolve_blend_file_path(blend_file_path)
        if not resolved_blend_path:
            error_msg = "No blend file path provided"
            log_messages.append(f"ERROR: {error_msg}")
            return ("", "\n".join(log_messages))
        
        # 检查文件是否存在
        if not os.path.exists(resolved_blend_path):
            error_msg = f"Blend file not found: {resolved_blend_path}"
            log_messages.append(f"ERROR: {error_msg}")
            return ("", "\n".join(log_messages))
        
        log_messages.append(f"Using blend file: {resolved_blend_path}")
        
        # 获取输出目录
        output_dir = self._get_output_directory(output_folder)
        
        # 确定输出文件路径
        file_extension = "glb"
        
        full_output_path = os.path.join(output_dir, f"{output_filename}.{file_extension}")
        
        # 根据设置确定返回的路径格式
        if use_full_path:
            output_file = full_output_path
        else:
            output_file = f"{output_folder}/{output_filename}.{file_extension}"
        
        log_messages.append(f"Output file: {output_file}")
        log_messages.append(f"Full path: {full_output_path}")
        
        # Path configuration
        blender_bin = BlenderManager().get_blender_path()
        
        # 准备Blender脚本内容
        script_content = _BLENDER_EXPORT_SCRIPT.replace(
            "{blend_file_path}", resolved_blend_path
        ).replace(
            "{output_path}", full_output_path
        ).replace(
            "{export_format}", export_format
        ).replace(
            "{export_selected_only}", str(export_selected_only)
        ).replace(
            "{apply_transforms}", str(apply_transforms)
        ).replace(
            "{include_animations}", str(include_animations)
        ).replace(
            "{include_textures}", str(include_textures)
        )
        
        # 写入临时脚本文件
        script_path = os.path.join(output_dir, f"{output_filename}_export_script.py")
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(script_content)
        
        # 调用Blender执行脚本
        cmd = [blender_bin, "--background", "--factory-startup", "--python", script_path]
        try:
            subprocess.run(cmd, check=True)
            log_messages.append(f"Blender export successful: {output_file}")
            
        except Exception as e:
            log_messages.append(f"Blender call failed: {e}")
            return (output_file, "\n".join(log_messages))
        
        # 检查输出文件是否存在
        if os.path.exists(full_output_path):
            file_size = os.path.getsize(full_output_path)
            log_messages.append(f"Exported file size: {file_size} bytes")
        else:
            log_messages.append(f"WARNING: Exported file not found: {full_output_path}")
        
        return (output_file, "\n".join(log_messages))

# Blender export script
_BLENDER_EXPORT_SCRIPT = r'''
import bpy
import sys
import os
import json

# Embedded parameters
blend_file_path = "{blend_file_path}"
output_path = "{output_path}"
export_format = "{export_format}"
export_selected_only = {export_selected_only}
apply_transforms = {apply_transforms}
include_animations = {include_animations}
include_textures = {include_textures}

print(f"Loading blend file: {blend_file_path}")

# Load the blend file
try:
    bpy.ops.wm.open_mainfile(filepath=blend_file_path)
    print(f"Successfully loaded blend file: {blend_file_path}")
except Exception as e:
    print(f"Error loading blend file: {e}")
    sys.exit(1)

# Get objects to export
if export_selected_only:
    # Export only selected objects
    objects_to_export = [obj for obj in bpy.context.selected_objects if obj.type in ['MESH', 'EMPTY', 'ARMATURE']]
    print(f"Exporting {len(objects_to_export)} selected objects")
else:
    # Export all objects
    objects_to_export = [obj for obj in bpy.context.scene.objects if obj.type in ['MESH', 'EMPTY', 'ARMATURE']]
    print(f"Exporting {len(objects_to_export)} all objects")

if not objects_to_export:
    print("No objects to export")
    sys.exit(1)

# Select objects for export
bpy.ops.object.select_all(action='DESELECT')
for obj in objects_to_export:
    obj.select_set(True)
    print(f"Selected object: {obj.name}")

# Set active object
if objects_to_export:
    bpy.context.view_layer.objects.active = objects_to_export[0]

# Create output directory
os.makedirs(os.path.dirname(output_path), exist_ok=True)

# Export based on format
if export_format == "GLB":
    print("Exporting as GLB...")
    
    # GLB export settings
    bpy.ops.export_scene.gltf(
        filepath=output_path,
        export_format='GLB',
        export_selected='SELECTED' if export_selected_only else 'ALL',
        export_apply=apply_transforms,
        export_animations=include_animations,
        export_texcoords=True,
        export_normals=True,
        export_tangents=True,
        export_materials=include_textures,
        export_colors=True,
        export_attributes=True,
        export_force_sampling=True,
        export_nla_strips=True,
        export_def_bones=False,
        export_current_frame=False,
        export_rest_position_armature=False,
        export_anim_single_armature=False,
        export_reset_pose_bones=True,
        export_anim_step=1.0,
        export_anim_simplify_factor=1.0,
        export_joints=False,
        export_leaf_bones=False,
        export_all_influences=False,
        export_morph=True,
        export_morph_normal=True,
        export_morph_tangent=False,
        export_lights=False,
        export_cameras=False,
        export_extras=False,
        export_yup=True,
        export_apply_scale=True
    )



print(f"Export completed: {output_path}")
'''