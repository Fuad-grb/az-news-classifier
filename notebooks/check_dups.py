import pandas as pd
import json
from pathlib import Path

files = list(Path("data/raw").glob("*.json"))
data = [json.load(open(f, encoding="utf-8")) for f in files]
df = pd.DataFrame(data)
df['title_lower'] = df['title'].str.lower().str.strip()

# Duplicates
dupes = df[df.duplicated(subset=['title_lower'], keep=False)]
sample_title = dupes['title_lower'].value_counts().index[0]
sample = dupes[dupes['title_lower'] == sample_title][['title', 'source', 'category', 'word_count']]
print("=== Sample duplicate ===")
print(sample.to_string())

# Idman breakdown
idman_raw = df[df['category'].isin(['idman-xeberleri', 'idman-9'])]
print(f"\n=== Idman breakdown ===")
print(f"Idman raw: {len(idman_raw)}")
print(f"Idman short (< 50 words): {(idman_raw['word_count'] < 50).sum()}")
print(f"Idman title dupes: {idman_raw.duplicated(subset=['title_lower']).sum()}")

print(f"Empty titles total: {(df['title'].str.strip() == '').sum()}")
print(f"Empty titles qafqazinfo: {(df[df['source']=='qafqazinfo_az']['title'].str.strip() == '').sum()}")