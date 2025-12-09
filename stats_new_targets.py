import pandas as pd
from scipy.stats import f_oneway, ttest_ind
from sqlalchemy import create_engine

# 1. Connect
engine = create_engine('postgresql://postgres:password@localhost:5432/microbiome_db')

print("--- Running Statistics on New Medical Biomarkers ---")

# ==========================================
# TEST 1: OBESITY vs. AKKERMANSIA (ANOVA)
# ==========================================
print("\n1. Testing: Does BMI impact Akkermansia levels?")
query_bmi = """
SELECT 
    CASE 
        WHEN bmi BETWEEN 18.5 AND 25 THEN 'Normal'
        WHEN bmi > 30 THEN 'Obese'
        ELSE 'Other'
    END as bmi_group,
    akkermansia
FROM samples s
JOIN key_species k ON s.sample_id = k.sample_id
WHERE bmi > 0 AND bmi < 60
"""
df_bmi = pd.read_sql(query_bmi, engine)

group_normal = df_bmi[df_bmi['bmi_group'] == 'Normal']['akkermansia']
group_obese = df_bmi[df_bmi['bmi_group'] == 'Obese']['akkermansia']

print(f"   Normal Weight Samples: {len(group_normal)} (Mean: {group_normal.mean():.1f})")
print(f"   Obese Samples:         {len(group_obese)} (Mean: {group_obese.mean():.1f})")

# Run T-Test (comparing just these two distinct groups is cleaner than ANOVA here)
t_stat, p_val_bmi = ttest_ind(group_normal, group_obese, equal_var=False)

print(f"   P-Value: {p_val_bmi:.10f}")
if p_val_bmi < 0.05:
    print("   RESULT: SIGNIFICANT. Obesity is linked to lower Akkermansia.")
else:
    print("   RESULT: Not significant.")

# ==========================================
# TEST 2: ANTIBIOTICS vs. FAECALIBACTERIUM (T-TEST)
# ==========================================
print("\n2. Testing: Do recent antibiotics wipe out Faecalibacterium?")
query_abx = """
SELECT antibiotic_history, faecalibacterium
FROM samples s
JOIN key_species k ON s.sample_id = k.sample_id
WHERE antibiotic_history IN ('Week', 'I have not taken antibiotics in the past year.')
"""
df_abx = pd.read_sql(query_abx, engine)

group_recent = df_abx[df_abx['antibiotic_history'] == 'Week']['faecalibacterium']
group_healthy = df_abx[df_abx['antibiotic_history'] != 'Week']['faecalibacterium']

print(f"   Recent Abx Samples: {len(group_recent)} (Mean: {group_recent.mean():.1f})")
print(f"   Healthy Samples:    {len(group_healthy)} (Mean: {group_healthy.mean():.1f})")

t_stat, p_val_abx = ttest_ind(group_recent, group_healthy, equal_var=False)

print(f"   P-Value: {p_val_abx:.10f}")
if p_val_abx < 0.05:
    print("   RESULT: SIGNIFICANT. Recent antibiotics significantly reduce Faecalibacterium.")
else:
    print("   RESULT: Not significant.")

# ==========================================
# TEST 3: THE RATIO (VEGAN vs HIGH MEAT)
# ==========================================
# We found the means were close, but let's test the RATIO itself distribution
print("\n3. Testing: P/B Ratio (Vegan vs High-Meat)")
query_ratio = """
SELECT 
    CASE 
        WHEN diet_type = 'Vegan' THEN 'Vegan'
        WHEN diet_type = 'Omnivore' AND red_meat_freq IN ('Daily', 'Regularly (3-5 times/week)') THEN 'High_Meat'
        ELSE 'Other'
    END as diet_group,
    (prevotella / NULLIF(bacteroides, 0)) as pb_ratio
FROM samples s
JOIN key_species k ON s.sample_id = k.sample_id
WHERE diet_type IN ('Vegan', 'Omnivore')
"""
df_ratio = pd.read_sql(query_ratio, engine)
# Drop infinity or NaNs from division by zero
df_ratio = df_ratio.dropna()
df_ratio = df_ratio[df_ratio['pb_ratio'] < 100] # Remove extreme outliers

group_vegan = df_ratio[df_ratio['diet_group'] == 'Vegan']['pb_ratio']
group_meat = df_ratio[df_ratio['diet_group'] == 'High_Meat']['pb_ratio']

t_stat, p_val_ratio = ttest_ind(group_vegan, group_meat, equal_var=False)
print(f"   P-Value: {p_val_ratio:.4f}")
if p_val_ratio < 0.05:
    print("   RESULT: Significant Difference in Ratio.")
else:
    print("   RESULT: No significant difference in Ratio.")