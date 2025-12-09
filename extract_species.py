import biom
import pandas as pd
import numpy as np

print("--- Starting Keystone Species Extraction ---")

# 1. Load BIOM (Lazy load)
table = biom.load_table('data/ag-gg-100nt.biom')

print(f"   -> Table found. Samples: {table.shape[1]}")

# 2. Define our Expanded Target List (Genus level)
# Note: 'Faecalibacterium' is the genus for F. prausnitzii
# 'Akkermansia' is the genus for A. muciniphila
target_genera = [
    'prevotella', 'bacteroides', 'roseburia', 'bifidobacterium', 'alistipes', # The Originals
    'akkermansia', 'faecalibacterium', 'lactobacillus' # The New Keystones
]

ids_to_keep = []
id_to_genus = {}

print("2. Scanning taxonomy for Keystone species...")
for obs_id in table.ids(axis='observation'):
    meta = table.metadata(obs_id, axis='observation')
    if meta and 'taxonomy' in meta:
        tax_str = ';'.join(meta['taxonomy']).lower()
        
        for target in target_genera:
            # Look for strict genus match "g__target"
            if f'g__{target}' in tax_str:
                ids_to_keep.append(obs_id)
                id_to_genus[obs_id] = target
                break

# 3. Filter and Convert
print(f"   -> Found {len(ids_to_keep)} matching strains.")
subtable = table.filter(ids_to_keep, axis='observation', inplace=False)
df = subtable.to_dataframe(dense=True)
df.rename(index=id_to_genus, inplace=True)

# 4. Aggregate
print("4. Aggregating counts...")
df_genus = df.groupby(df.index).sum().T
df_genus.index.name = 'sample_id'

# 5. Save
print("5. Saving to CSV...")
df_genus.to_csv('data/species_counts.csv')
print("--- Success! Created expanded 'species_counts.csv' ---")