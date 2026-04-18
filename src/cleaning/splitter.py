import pandas as pd
from pathlib import Path
import logging
import re
from sklearn.model_selection import train_test_split

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

class Splitter:
    def __init__(self, input_file='data/cleaned/cleaned_data.csv', output_dir='data/final'):
        self.input_file = input_file
        self.output_dir = output_dir
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)

        self.months_az = {
            'yanvar': 'January', 'fevral': 'February', 'mart': 'March',
            'aprel': 'April', 'may': 'May', 'iyun': 'June',
            'iyul': 'July', 'avqust': 'August', 'sentyabr': 'September',
            'oktyabr': 'October', 'noyabr': 'November', 'dekabr': 'December'
        }

    def clean_date_str(self, date_str):
        if pd.isna(date_str) or str(date_str).strip().lower() == 'nan':
            return None
        
        d_str = str(date_str).lower().strip()
        
        # Translate Azerbaijani month names to English
        for az, en in self.months_az.items():
            if az in d_str:
                d_str = d_str.replace(az, en)
        
        # If month and year are stuck together (mart2020)
        d_str = re.sub(r'([a-z]+),(\d{4})', r'\1 \2 ', d_str)
        # If year and time are stuck together (202616:13)
        d_str = re.sub(r'(\d{4})(\d{2}:\d{2})', r'\1 \2', d_str)
        
        return " ".join(d_str.split())

    def split(self):
        df = pd.read_csv(self.input_file)
        initial_count = len(df)
        logging.info(f'Loaded {initial_count} records from {self.input_file}')

        # Parse dates
        logging.info("Cleaning published_date column...")
        df['published_date_clean'] = df['published_date'].apply(self.clean_date_str)
        df['parsed_date'] = pd.to_datetime(df['published_date_clean'], utc=True, errors='coerce')

        # Split into dated and undated
        dated = df[df['parsed_date'].notna()].sort_values('parsed_date')
        undated = df[df['parsed_date'].isna()]
        logging.info(f"Dated: {len(dated)}, Undated: {len(undated)}")

        # Temporal split for dated
        t1 = int(0.7 * len(dated))
        t2 = int(0.85 * len(dated))
        train_d = dated.iloc[:t1]
        val_d = dated.iloc[t1:t2]
        test_d = dated.iloc[t2:]

        # Stratified random split for undated
        train_u, temp_u = train_test_split(
            undated, test_size=0.3, stratify=undated['category'], random_state=42
        )
        val_u, test_u = train_test_split(
            temp_u, test_size=0.5, stratify=temp_u['category'], random_state=42
        )

        # Combine
        train = pd.concat([train_d, train_u])
        val = pd.concat([val_d, val_u])
        test = pd.concat([test_d, test_u])

        # Drop helper columns and save
        drop_cols = ['published_date_clean', 'parsed_date']
        train.drop(columns=drop_cols).to_csv(f'{self.output_dir}/train.csv', index=False)
        val.drop(columns=drop_cols).to_csv(f'{self.output_dir}/val.csv', index=False)
        test.drop(columns=drop_cols).to_csv(f'{self.output_dir}/test.csv', index=False)

        # Log results
        logging.info("-" * 30)
        logging.info(f"Train: {len(train)}, Val: {len(val)}, Test: {len(test)}")
        logging.info(f"Dated split - Train: {len(train_d)}, Val: {len(val_d)}, Test: {len(test_d)}")
        logging.info(f"Undated split - Train: {len(train_u)}, Val: {len(val_u)}, Test: {len(test_u)}")
        if len(dated) > 0:
            logging.info(f"Date range: {dated['parsed_date'].min().date()} to {dated['parsed_date'].max().date()}")
            logging.info(f"Train dates: up to {train_d['parsed_date'].max().date()}")
            logging.info(f"Val dates: {val_d['parsed_date'].min().date()} to {val_d['parsed_date'].max().date()}")
            logging.info(f"Test dates: {test_d['parsed_date'].min().date()} to {test_d['parsed_date'].max().date()}")
        logging.info("-" * 30)

        # Distribution by category
        print("\nCategory distribution:")
        dist = pd.DataFrame({
            'Train': train['category'].value_counts(),
            'Val': val['category'].value_counts(),
            'Test': test['category'].value_counts()
        }).fillna(0).astype(int)
        dist['Total'] = dist.sum(axis=1)
        print(dist)

if __name__ == "__main__":
    splitter = Splitter()
    splitter.split()