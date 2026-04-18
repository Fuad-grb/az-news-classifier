import pandas as pd
import torch
from sklearn.preprocessing import LabelEncoder
from transformers import AutoTokenizer, AutoModelForSequenceClassification, Trainer, TrainingArguments
from config import TrainingConfig

def prepare_data(config):
    # Load datasets
    train_df = pd.read_csv(config.train_path)
    val_df = pd.read_csv(config.val_path)
    
    # Encode labels
    label_encoder = LabelEncoder()
    train_df['label'] = label_encoder.fit_transform(train_df['label'])
    val_df['label'] = label_encoder.transform(val_df['label'])
    
    label_mapping = dict(zip(label_encoder.classes_, label_encoder.transform(label_encoder.classes_)))
    return train_df, val_df, label_mapping

if __name__ == "__main__":