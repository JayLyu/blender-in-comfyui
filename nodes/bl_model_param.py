import os
import folder_paths

class BL_Model_Param:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model_file_path": ("STRING", {"default": ""}),
            },
            "optional": {
                "position_x": ("FLOAT", {"default": 0.0, "min": -1000, "max": 1000, "step": 0.1}),
                "position_y": ("FLOAT", {"default": 0.0, "min": -1000, "max": 1000, "step": 0.1}),
                "position_z": ("FLOAT", {"default": 0.0, "min": -1000, "max": 1000, "step": 0.1}),
                "rotation_x": ("FLOAT", {"default": 0.0, "min": -360, "max": 360, "step": 0.1}),
                "rotation_y": ("FLOAT", {"default": 0.0, "min": -360, "max": 360, "step": 0.1}),
                "rotation_z": ("FLOAT", {"default": 0.0, "min": -360, "max": 360, "step": 0.1}),
                "scale_x": ("FLOAT", {"default": 1.0, "step": 0.01}),
                "scale_y": ("FLOAT", {"default": 1.0, "step": 0.01}),
                "scale_z": ("FLOAT", {"default": 1.0, "step": 0.01}),
                "collection_name": ("STRING", {"default": "3D_Model", "multiline": False}),
            }
        }

    RETURN_TYPES = ("MODELS",)
    RETURN_NAMES = ("model",)
    FUNCTION = "load_model"
    CATEGORY = "Blender"
    DESCRIPTION = "Load 3D model (GLB, FBX, OBJ) and set transform parameters"

    def load_model(self, model_file_path, position_x=0.0, position_y=0.0, position_z=0.0,
                  rotation_x=0.0, rotation_y=0.0, rotation_z=0.0,
                  scale_x=1.0, scale_y=1.0, scale_z=1.0, collection_name="3D_Model"):
        # 获取ComfyUI输入目录
        input_dir = folder_paths.get_input_directory()
        full_model_path = os.path.join(input_dir, model_file_path)
        
        # 检查文件是否存在
        if not os.path.exists(full_model_path):
            print(f"ERROR: Model file not found: {full_model_path}")
            return (None,)
        
        # 检查文件格式
        file_ext = os.path.splitext(model_file_path)[1].lower()
        supported_formats = ['.glb', '.gltf', '.fbx', '.obj']
        
        if file_ext not in supported_formats:
            print(f"ERROR: Unsupported file format: {file_ext}")
            print(f"Supported formats: {', '.join(supported_formats)}")
            return (None,)
        
        # 创建模型数据字典
        model_data = {
            "file_path": full_model_path,
            "position": (position_x, position_y, position_z),
            "rotation": (rotation_x, rotation_y, rotation_z),
            "scale": (scale_x, scale_y, scale_z),
            "name": os.path.splitext(os.path.basename(model_file_path))[0],
            "collection_name": collection_name,
            "file_format": file_ext
        }
        
        print(f"Loaded {file_ext.upper()} model: {model_data['name']}")
        print(f"Collection: {collection_name}")
        print(f"Position: ({position_x}, {position_y}, {position_z})")
        print(f"Rotation: ({rotation_x}, {rotation_y}, {rotation_z})")
        print(f"Scale: ({scale_x}, {scale_y}, {scale_z})")
        
        return (model_data,) 