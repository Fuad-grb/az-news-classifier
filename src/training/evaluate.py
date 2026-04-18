import pandas as pd
import numpy as np
import json
from sklearn.metrics import classification_report, confusion_matrix
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from data_prep import NewsDataset
from config import TrainingConfig
from transformers import Trainer

def main():
    config = TrainingConfig()
    model_path = f"{config.output_dir}/final_best_model"
    
    # Load model and tokenizer
    model = AutoModelForSequenceClassification.from_pretrained(model_path)
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    
    # Load label mapping
    with open(f"{model_path}/label_mapping.json") as f:
        label_map = json.load(f)
    label_names = [label_map[str(i)] for i in range(len(label_map))]
    
    # Load test data
    test_df = pd.read_csv("data/final/test.csv")
    from sklearn.preprocessing import LabelEncoder
    le = LabelEncoder()
    le.classes_ = np.array(label_names)
    test_df['label'] = le.transform(test_df['category'])
    
    test_dataset = NewsDataset(test_df['content'], test_df['label'], tokenizer, config.max_length)
    
    trainer = Trainer(model=model)
    predictions = trainer.predict(test_dataset)
    preds = np.argmax(predictions.predictions, axis=-1)
    
    print("Test Set Classification Report:")
    print(classification_report(test_df['label'], preds, target_names=label_names))
    
    print("Confusion Matrix:")
    cm = confusion_matrix(test_df['label'], preds)
    print(pd.DataFrame(cm, index=label_names, columns=label_names))

if __name__ == "__main__":
    main()