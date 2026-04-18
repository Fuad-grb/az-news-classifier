import pandas as pd
import torch
from torch.utils.data import Dataset
from sklearn.preprocessing import LabelEncoder
from transformers import AutoTokenizer


class NewsDataset(Dataset):
    def __init__(self, texts, labels, tokenizer, max_length):
        # Convert pandas Series to list to avoid issues with indexing
        self.texts = texts.tolist()
        self.labels = labels.tolist()
        self.tokenizer = tokenizer
        self.max_length = max_length
        
    def __len__(self):
            return len(self.texts)
        
    def __getitem__(self, idx):
        text = self.texts[idx]
        label = self.labels[idx]
        
        encoding = self.tokenizer(
            text,
            add_special_tokens=True,
            max_length=self.max_length,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )
        
        return {
            'input_ids': encoding['input_ids'].flatten(), # Flatten the tensor to remove the batch dimension
            'attention_mask': encoding['attention_mask'].flatten(), # to identify which tokens are padding
            'labels': torch.tensor(label, dtype=torch.long) # Convert label to tensor
        }


# Load configuration
def prepare_data(config):
    # Load datasets
    train_df = pd.read_csv(config.train_path)
    val_df = pd.read_csv(config.val_path)
    
    # Encode labels
    le = LabelEncoder()
    train_df['label'] = le.fit_transform(train_df['category'])
    val_df['label'] = le.transform(val_df['category'])
    
    # Initialize tokenizer
    tokenizer = AutoTokenizer.from_pretrained(config.model_name)
    tokenizer.save_pretrained(f"{config.output_dir}/final_best_model") # Save tokenizer for later use during inference
    # Create datasets
    train_dataset = NewsDataset(train_df['content'], train_df['label'], tokenizer, config.max_length)
    val_dataset = NewsDataset(val_df['content'], val_df['label'], tokenizer, config.max_length)
    
    return train_dataset, val_dataset, le.classes_
