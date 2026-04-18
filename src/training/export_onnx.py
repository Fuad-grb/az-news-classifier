from optimum.onnxruntime import ORTModelForSequenceClassification
from transformers import AutoTokenizer
from config import TrainingConfig
import os
import shutil

def main():
    config = TrainingConfig()
    
    # Using the checkpoint with better inference performance
    model_path = f"{config.output_dir}/checkpoint-1332" 
    
    os.makedirs(config.onnx_dir, exist_ok=True)
    
    # Export using optimum
    model = ORTModelForSequenceClassification.from_pretrained(
        model_path, export=True
    )
    model.save_pretrained(config.onnx_dir)
    
    # Copy tokenizer and label map
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    tokenizer.save_pretrained(config.onnx_dir)
    shutil.copy(f"{model_path}/label_mapping.json", config.onnx_dir)
    
    # Size comparison
    pytorch_size = sum(
        os.path.getsize(f"{model_path}/{f}") 
        for f in os.listdir(model_path) if f.endswith(".safetensors")
    ) / 1024 / 1024
    onnx_size = os.path.getsize(f"{config.onnx_dir}/model.onnx") / 1024 / 1024
    print(f"PyTorch model: {pytorch_size:.1f} MB")
    print(f"ONNX model: {onnx_size:.1f} MB")
    print("Export complete.")

if __name__ == "__main__":
    main()