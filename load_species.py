import pandas as pd
from sqlalchemy import create_engine

# 1. Connect to Database
engine = create_engine('postgresql://postgres:password@localhost:5432/microbiome_db')

print("1. Fetching valid Patient IDs from Database...")
# We only want to upload data for patients who exist in our metadata table
valid_ids = pd.read_sql("SELECT sample_id FROM samples", engine)
# Convert to a set for faster checking
valid_set = set(valid_ids['sample_id'].astype(str))

print(f"   -> Found {len(valid_set)} valid patients.")

print("2. Loading Species CSV...")
try:
    df = pd.read_csv('data/species_counts.csv')
    # Ensure ID is string to match DB
    df['sample_id'] = df['sample_id'].astype(str)
    
    print(f"   -> Raw species data: {len(df)} rows.")

    # Filter: Keep only rows where sample_id is in the valid_set
    df_clean = df[df['sample_id'].isin(valid_set)].copy()

    print(f"   -> Filtered species data: {len(df_clean)} rows (Dropped {len(df) - len(df_clean)} orphans).")

    print("3. Uploading to SQL...")
    df_clean.to_sql('key_species', engine, if_exists='replace', index=False)
    print("--- Success! Species data loaded. ---")

except FileNotFoundError:
    print("Error: 'species_counts.csv' not found. Did you run extract_species.py?")