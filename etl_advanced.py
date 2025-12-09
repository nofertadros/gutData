import pandas as pd
from sqlalchemy import create_engine
from functools import reduce

# CONFIGURATION
DB_CONNECTION = 'postgresql://postgres:password@localhost:5432/microbiome_db'
engine = create_engine(DB_CONNECTION)

print("--- Starting Ultimate Multi-Omics ETL ---")

# ==========================================
# PART A: LOAD & CLEAN PATIENT METADATA
# ==========================================
print("1. Loading Patient Metadata (ag-cleaned.txt)...")
try:
    df_meta = pd.read_csv('data/ag-cleaned.txt', sep='\t', encoding='latin1', low_memory=False)
except FileNotFoundError:
    df_meta = pd.read_csv('ag-cleaned.txt', sep='\t', encoding='latin1', low_memory=False)

# Rename columns to match our SQL schema
rename_map = {
    df_meta.columns[0]: 'sample_id',
    'AGE_YEARS': 'age', 
    'SEX': 'sex', 
    'BMI': 'bmi', 
    'COUNTRY': 'country', 
    'ANTIBIOTIC_HISTORY': 'antibiotic_history',
    'DIET_TYPE': 'diet_type', 
    'TYPES_OF_PLANTS': 'plant_types_count',
    'ALCOHOL_FREQUENCY': 'alcohol_freq',
    'RED_MEAT_FREQUENCY': 'red_meat_freq',
    'PROBIOTIC_FREQUENCY': 'probiotic_freq',
    'VITAMIN_B_SUPPLEMENT_FREQUENCY': 'vitamin_b_freq',
    'VITAMIN_D_SUPPLEMENT_FREQUENCY': 'vitamin_d_freq',
    'MULTIVITAMIN': 'multivitamin_freq',
    'ACNE_MEDICATION': 'acne_med_freq'
}
df_meta.rename(columns=rename_map, inplace=True)

# Clean Numeric Columns
for col in ['age', 'bmi']:
    df_meta[col] = pd.to_numeric(df_meta[col], errors='coerce')

# Clean "Plant Types"
df_meta['plant_types_count'] = df_meta['plant_types_count'].astype(str).str.extract(r'(\d+)').astype(float)

# Select ALL columns we want (The "Master List")
patient_cols = [
    'sample_id', 'age', 'sex', 'bmi', 'country', 'antibiotic_history', 
    'diet_type', 'plant_types_count', 'alcohol_freq', 'red_meat_freq',
    'probiotic_freq', 'vitamin_b_freq', 'vitamin_d_freq', 'multivitamin_freq', 'acne_med_freq'
]

# Filter columns that actually exist in the file
existing_cols = [c for c in patient_cols if c in df_meta.columns]
df_samples = df_meta[existing_cols].copy().dropna(subset=['sample_id'])

print(f"   -> Loaded {len(df_samples)} patient records with Polypharmacy data.")

# ==========================================
# PART B: LOAD THE 3 LAB METRICS
# ==========================================
def load_metric(filename, sql_col_name):
    print(f"2. Processing {filename}...")
    try:
        # Check if file is in data folder or root
        try:
            df = pd.read_csv(f'data/{filename}', sep='\t')
        except FileNotFoundError:
            df = pd.read_csv(filename, sep='\t')
            
        depth_col = [c for c in df.columns if 'sequences' in c.lower()][0]
        df_10k = df[df[depth_col] == 10000].copy()
        data = df_10k.iloc[:, 3:].mean(axis=0).to_frame(name=sql_col_name)
        data.index.name = 'sample_id'
        return data.reset_index()
    except Exception as e:
        print(f"   ERROR loading {filename}: {e}")
        return pd.DataFrame(columns=['sample_id', sql_col_name])

df_shannon = load_metric('shannon.txt', 'shannon_entropy')
df_pd = load_metric('PD_whole_tree.txt', 'phylogenetic_diversity')
df_otus = load_metric('observed_otus.txt', 'species_count')

# ==========================================
# PART C: MERGE & UPLOAD
# ==========================================
print("3. Merging Lab Data...")
lab_dfs = [df_shannon, df_pd, df_otus]
df_lab_final = reduce(lambda left, right: pd.merge(left, right, on='sample_id', how='inner'), lab_dfs)

# Ensure IDs match
df_samples['sample_id'] = df_samples['sample_id'].astype(str)
df_lab_final['sample_id'] = df_lab_final['sample_id'].astype(str)

# Filter
final_patients = df_samples[df_samples['sample_id'].isin(df_lab_final['sample_id'])]
final_lab = df_lab_final[df_lab_final['sample_id'].isin(final_patients['sample_id'])]

print(f"4. Uploading {len(final_patients)} rows to SQL...")
final_patients.to_sql('samples', engine, if_exists='append', index=False)
final_lab.to_sql('gut_metrics', engine, if_exists='append', index=False)

print("--- SUCCESS! Database Fully Synced. ---")