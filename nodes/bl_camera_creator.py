import os
import folder_paths

class BL_Camera_Creator:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "camera_name": ("STRING", {"default": "Camera", "multiline": False}),
            },
            "optional": {
                "position_x": ("FLOAT", {"default": 0.0, "min": -1000, "max": 1000, "step": 0.1}),
                "position_y": ("FLOAT", {"default": -20.0, "min": -1000, "max": 1000, "step": 0.1}),
                "position_z": ("FLOAT", {"default": 2.0, "min": -1000, "max": 1000, "step": 0.1}),
                "rotation_x": ("FLOAT", {"default":90.0, "min": -360, "max": 360, "step": 0.1, "display": "slider"}),
                "rotation_y": ("FLOAT", {"default": 0.0, "min": -360, "max": 360, "step": 0.1, "display": "slider"}),
                "rotation_z": ("FLOAT", {"default": 0.0, "min": -360, "max": 360, "step": 0.1, "display": "slider"}),
                "focal_length": ("FLOAT", {"default": 50.0, "min": 1.0, "max": 500.0, "step": 1.0}),
                "collection_name": ("STRING", {"default": "Cameras", "multiline": False}),
            }
        }

    RETURN_TYPES = ("MODELS",)
    RETURN_NAMES = ("camera",)
    FUNCTION = "create_camera"
    CATEGORY = "Blender"
    DESCRIPTION = "Create a camera with specified transform parameters"

    def create_camera(self, camera_name, position_x=0.0, position_y=-20.0, position_z=2.0,
                     rotation_x=9.0, rotation_y=0.0, rotation_z=0.0,
                     focal_length=50.0, collection_name="Cameras"):
        # 创建摄像机数据字典
        camera_data = {
            "type": "camera",
            "name": camera_name,
            "position": (position_x, position_y, position_z),
            "rotation": (rotation_x, rotation_y, rotation_z),
            "scale": (1.0, 1.0, 1.0),  # 摄像机不需要缩放
            "collection_name": collection_name,
            "focal_length": focal_length
        }
        
        print(f"Created camera: {camera_name}")
        print(f"Collection: {collection_name}")
        print(f"Position: ({position_x}, {position_y}, {position_z})")
        print(f"Rotation: ({rotation_x}, {rotation_y}, {rotation_z})")
        print(f"Focal length: {focal_length}mm")
        
        return (camera_data,) 