import pandas as pd
from pathlib import Path
import logging
import re

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

class Splitter:
    def __init__(self, input_file = 'data/cleaned/cleaned_data.csv', output_dir = 'data/final'):
        self.input_file = input_file
        self.output_dir = output_dir
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        
    def split(self):
        df = pd.read_csv(self.input_file)
        initial_count = len(df)
        logging.info(f'Loaded {initial_count} records from {self.input_file}')
        
        # Mapping of Azerbaijani month names to English for date parsing
        
        months_az = {
            'yanvar': 'January', 'fevral': 'February', 'mart': 'March',
            'aprel': 'April', 'may': 'May', 'iyun': 'June',
            'iyul': 'July', 'avqust': 'August', 'sentyabr': 'September',
            'oktyabr': 'October', 'noyabr': 'November', 'dekabr': 'December'
        }
        
        def clean_date_str(date_str):
            if pd.isna(date_str):
                return None
            
            d_str = str(date_str).lower().strip()
            
            # Replace Azerbaijani month names with English
            
            for az, en in months_az.items():
                if az in d_str:
                    d_str = d_str.replace(az, en)
                    
            # Handle cases like "mart,2023" -> "March 2023"
            
            d_str = re.sub(r'([a-z]+),(\d{4})', r'\1 \2 ', d_str)
            
            return d_str
        
        logging.info("Cleaning published_date column...")
        df['published_date'] = df['published_date'].apply(clean_date_str)
            
        
        # Convert published_date to datetime
        df['published_date'] = pd.to_datetime(df['published_date'], utc = True, errors='coerce')
        
        # Drop rows with invalid dates
        df = df.dropna(subset=['published_date'])
        
        if len(df) < initial_count:
            logging.warning(f'Dropped {initial_count - len(df)} records due to invalid dates')
            
        # Sort by published_date
        df = df.sort_values(by='published_date').reset_index(drop=True)
        
        #   Index for splitting train, validation, and test sets
        train_end = int(0.7 * len(df))
        val_end = int(0.85 * len(df))
        # Split the data
        train_df = df.iloc[:train_end]
        val_df = df.iloc[train_end:val_end]
        test_df = df.iloc[val_end:]
        
        # Save the splits
        train_df.to_csv(f'{self.output_dir}/train.csv', index=False)
        val_df.to_csv(f'{self.output_dir}/validation.csv', index=False)
        test_df.to_csv(f'{self.output_dir}/test.csv', index=False)
        
        logging.info("-" * 30)
        logging.info(f"Total records after date fix: {len(df)}")
        logging.info(f"Train: {len(train_df)} ({df['published_date'].min().date()} to {train_df['published_date'].max().date()})")
        logging.info(f"Val:   {len(val_df)} ({val_df['published_date'].min().date()} to {val_df['published_date'].max().date()})")
        logging.info(f"Test:  {len(test_df)} ({test_df['published_date'].min().date()} to {test_df['published_date'].max().date()})")
        logging.info("-" * 30)
        
        # Distrbution by category
        print("Category distribution:")
        
        dist = pd.DataFrame({
            'Train': train_df['category'].value_counts(normalize=True),
            'Val': val_df['category'].value_counts(normalize=True),
            'Test': test_df['category'].value_counts(normalize=True)
        }).fillna(0).astype(float).round(4)
        
        print(dist)
        
if __name__ == "__main__":
    splitter = Splitter()
    splitter.split()
        