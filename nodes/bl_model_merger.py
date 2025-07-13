class BL_Model_Merger:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model_1": ("MODELS",),
                "model_2": ("MODELS",),
            }
        }

    RETURN_TYPES = ("MODELS",)
    RETURN_NAMES = ("models",)
    FUNCTION = "merge_models"
    CATEGORY = "Blender"
    DESCRIPTION = "Merge 3D models and cameras"

    def merge_models(self, model_1, model_2):
        # 检查输入模型是否有效
        if model_1 is None or model_2 is None:
            print("ERROR: One or both 3D models are None")
            return (None,)
        
        # 标准化输入为列表格式
        def normalize_models(models):
            if models is None:
                return []
            elif isinstance(models, dict):
                return [models]
            elif isinstance(models, list):
                return models
            else:
                print(f"WARNING: Unexpected model format: {type(models)}")
                return []
        
        # 验证模型数据格式
        def validate_model(model):
            if not isinstance(model, dict):
                return False
            
            # 检查是否是摄像机
            if model.get("type") == "camera":
                required_keys = ['type', 'name', 'position', 'rotation', 'scale', 'collection_name', 'focal_length']
            else:
                # 检查是否是3D模型
                required_keys = ['file_path', 'position', 'rotation', 'scale', 'name']
            
            return all(key in model for key in required_keys)
        
        # 获取模型列表
        models_1 = normalize_models(model_1)
        models_2 = normalize_models(model_2)
        
        # 合并模型列表并验证
        merged_models = models_1 + models_2
        
        # 验证所有模型
        valid_models = []
        invalid_models = []
        
        for model in merged_models:
            if validate_model(model):
                valid_models.append(model)
            else:
                invalid_models.append(model)
                print(f"WARNING: Invalid model format: {model}")
        
        if not valid_models:
            print("ERROR: No valid models found after merging")
            return (None,)
        
        print(f"Merged objects:")
        for model in valid_models:
            if model.get("type") == "camera":
                print(f"  - Camera: {model['name']}")
            else:
                print(f"  - Model: {model['name']}")
        print(f"Total valid objects: {len(valid_models)}")
        
        if invalid_models:
            print(f"WARNING: {len(invalid_models)} invalid models were skipped")
        
        return (valid_models,) 