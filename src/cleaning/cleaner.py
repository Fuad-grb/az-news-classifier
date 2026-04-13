import os
import pandas as pd
from pathlib import Path
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

class Cleaner:
    def __init__(self, raw_data_path: str = "data/raw", cleaned_data_path: str = "data/cleaned"):
        self.raw_data_path = Path(raw_data_path)
        self.cleaned_data_path = Path(cleaned_data_path)
        self.cleaned_data_path.mkdir(parents=True, exist_ok=True)
        
        self.category_mapping = {
            "iqtisadiyyat-xeberleri": "iqtisadiyyat",
            "sosial-xeberler": "sosial",
            "cemiyyet": "sosial",
            "siyaset-xeberleri": "siyaset",
            "siyasi-xeberler": "siyaset",
            "siyaset-2": "siyaset",
            "idman-xeberleri": "idman",
            "idman-9": "idman",
            "dunya-xeberleri": "dunya",
            "dunya-6": "dunya",
            
        }
        
    def load_data(self):
        all_data = []
        files = list(self.raw_data_path.glob("*.json"))
        logging.info(f"Found {len(files)} files in {self.raw_data_path}")
        
        for file in files:
            with open(file, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                    all_data.append(data)
                except json.JSONDecodeError as e:
                    logging.error(f"Error decoding JSON from {file}: {e}")
        
        return pd.DataFrame(all_data)
        
    
    def clean_data(self):
        df = self.load_data()
        initial_count = len(df)
        logging.info(f"Loaded {initial_count} records")
        
        logging.info(f"No category mapping: {df['category'].map(self.category_mapping).isna().sum()}")
        logging.info(f"No Content: {(df['content'] == 'No Content').sum()}")
        logging.info(f"Word count < 50: {(df['word_count'] < 50).sum()}")
        logging.info(f"URL duplicates: {df.duplicated(subset=['url']).sum()}")
        df_temp = df.copy()
        df_temp['title_lower'] = df_temp['title'].str.lower().str.strip()
        logging.info(f"Title duplicates: {df_temp.duplicated(subset=['title_lower']).sum()}")
        
        df['category'] = df['category'].map(self.category_mapping)
        df = df.dropna(subset=['category'])
        # To avoid keeping records with empty content or very short content, we can filter them out
        df = df[df['content'] != "No Content"]
        df = df[df['word_count'] >= 50]
        # Remove duplicates based on URL and title (after converting to lowercase and stripping whitespace)
        df = df.drop_duplicates(subset=['url'])
        df['title_lower'] = df['title'].str.lower().str.strip()
        df = df.drop_duplicates(subset=['title_lower'])
        df = df.drop(columns=['title_lower'])
        
        final_count = len(df)
        logging.info(f"Cleaned data: {final_count} records remaining (removed {initial_count - final_count})")
        
        cleaned_file = self.cleaned_data_path / "cleaned_data.csv"
        df.to_csv(cleaned_file, index=False, encoding="utf-8")
        
        logging.info(f"Saved cleaned data to {cleaned_file}")
        
        logging.info("-" * 30)
        logging.info(f"Initial articles: {initial_count}")
        logging.info(f"Removed (short/empty/duplicates): {initial_count - final_count}")
        logging.info(f"Final articles: {final_count}")
        logging.info("-" * 30)
        
        logging.info("final category distribution:")
        logging.info(df['category'].value_counts())
        
        return df
        
if __name__ == "__main__":
    cleaner = Cleaner()
    cleaner.clean_data()