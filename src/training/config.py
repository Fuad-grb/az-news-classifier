from dataclasses import dataclass

@dataclass
class TrainingConfig:
    
    model_name: str = "xlm-roberta-base"
    
    train_path: str = "data/final/train.csv"
    val_path: str = "data/final/val.csv"
    max_length: int = 256 # texts contains 120-250 words as it seen from EDA, so 256 tokens can be not enough for some texts, but it is a good balance between performance and memory usage."
    
    batch_size: int = 16
    num_epochs: int = 3
    learning_rate: float = 2e-5
    weight_decay: float = 0.01
    
    output_dir: str = "models/checkpoints"
    onnx_dir: str = "models/final_model"
    
    