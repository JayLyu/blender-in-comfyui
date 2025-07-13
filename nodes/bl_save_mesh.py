import json
import os
import struct
import numpy as np
import torch
import folder_paths

class BL_Save_Mesh:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "mesh": ("MESH",),
                "filename_prefix": ("STRING", {"default": "mesh/ComfyUI"}),
            },
            "hidden": {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"},
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("glb_path",)
    FUNCTION = "save_mesh"
    CATEGORY = "Blender"
    DESCRIPTION = "保存 MESH 为 GLB 文件"

    def save_mesh(self, mesh, filename_prefix, prompt=None, extra_pnginfo=None):
        # 获取保存路径
        full_output_folder, filename, counter, subfolder, filename_prefix = folder_paths.get_save_image_path(
            filename_prefix, folder_paths.get_output_directory()
        )
        
        # 准备元数据
        metadata = {}
        if prompt is not None:
            metadata["prompt"] = json.dumps(prompt)
        if extra_pnginfo is not None:
            for x in extra_pnginfo:
                metadata[x] = json.dumps(extra_pnginfo[x])
        
        # 保存第一个 mesh（如果有多个的话）
        if mesh.vertices.shape[0] > 0:
            f = f"{filename}_{counter:05}.glb"
            filepath = os.path.join(full_output_folder, f)
            
            # 保存 GLB 文件
            self.save_glb(mesh.vertices[0], mesh.faces[0], filepath, metadata)
            
            # 返回相对路径
            relative_path = os.path.join(subfolder, f)
            print(f"Saved mesh to GLB: {relative_path}")
            
            return (relative_path,)
        else:
            print("No mesh data to save")
            return ("",)

    def save_glb(self, vertices, faces, filepath, metadata=None):
        """
        保存 PyTorch tensor vertices 和 faces 为 GLB 文件

        参数:
        vertices: torch.Tensor of shape (N, 3) - 顶点坐标
        faces: torch.Tensor of shape (M, 3) - 面索引（三角形面）
        filepath: str - 输出文件路径（应该以 .glb 结尾）
        metadata: dict - 可选的元数据
        """
        # 转换 tensor 为 numpy 数组
        vertices_np = vertices.cpu().numpy().astype(np.float32)
        faces_np = faces.cpu().numpy().astype(np.uint32)

        vertices_buffer = vertices_np.tobytes()
        indices_buffer = faces_np.tobytes()

        def pad_to_4_bytes(buffer):
            padding_length = (4 - (len(buffer) % 4)) % 4
            return buffer + b'\x00' * padding_length

        vertices_buffer_padded = pad_to_4_bytes(vertices_buffer)
        indices_buffer_padded = pad_to_4_bytes(indices_buffer)

        buffer_data = vertices_buffer_padded + indices_buffer_padded

        vertices_byte_length = len(vertices_buffer)
        vertices_byte_offset = 0
        indices_byte_length = len(indices_buffer)
        indices_byte_offset = len(vertices_buffer_padded)

        gltf = {
            "asset": {"version": "2.0", "generator": "ComfyUI Blender Plugin"},
            "buffers": [
                {
                    "byteLength": len(buffer_data)
                }
            ],
            "bufferViews": [
                {
                    "buffer": 0,
                    "byteOffset": vertices_byte_offset,
                    "byteLength": vertices_byte_length,
                    "target": 34962  # ARRAY_BUFFER
                },
                {
                    "buffer": 0,
                    "byteOffset": indices_byte_offset,
                    "byteLength": indices_byte_length,
                    "target": 34963  # ELEMENT_ARRAY_BUFFER
                }
            ],
            "accessors": [
                {
                    "bufferView": 0,
                    "byteOffset": 0,
                    "componentType": 5126,  # FLOAT
                    "count": len(vertices_np),
                    "type": "VEC3",
                    "max": vertices_np.max(axis=0).tolist(),
                    "min": vertices_np.min(axis=0).tolist()
                },
                {
                    "bufferView": 1,
                    "byteOffset": 0,
                    "componentType": 5125,  # UNSIGNED_INT
                    "count": faces_np.size,
                    "type": "SCALAR"
                }
            ],
            "meshes": [
                {
                    "primitives": [
                        {
                            "attributes": {
                                "POSITION": 0
                            },
                            "indices": 1,
                            "mode": 4  # TRIANGLES
                        }
                    ]
                }
            ],
            "nodes": [
                {
                    "mesh": 0
                }
            ],
            "scenes": [
                {
                    "nodes": [0]
                }
            ],
            "scene": 0
        }

        if metadata is not None:
            gltf["asset"]["extras"] = metadata

        # 转换 JSON 为字节
        gltf_json = json.dumps(gltf).encode('utf8')

        def pad_json_to_4_bytes(buffer):
            padding_length = (4 - (len(buffer) % 4)) % 4
            return buffer + b' ' * padding_length

        gltf_json_padded = pad_json_to_4_bytes(gltf_json)

        # 创建 GLB 头部
        # Magic glTF
        glb_header = struct.pack('<4sII', b'glTF', 2, 12 + 8 + len(gltf_json_padded) + 8 + len(buffer_data))

        # 创建 JSON chunk 头部 (chunk type 0)
        json_chunk_header = struct.pack('<II', len(gltf_json_padded), 0x4E4F534A)  # "JSON" in little endian

        # 创建 BIN chunk 头部 (chunk type 1)
        bin_chunk_header = struct.pack('<II', len(buffer_data), 0x004E4942)  # "BIN\0" in little endian

        # 写入 GLB 文件
        with open(filepath, 'wb') as f:
            f.write(glb_header)
            f.write(json_chunk_header)
            f.write(gltf_json_padded)
            f.write(bin_chunk_header)
            f.write(buffer_data)

        return filepath 