import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from sqlalchemy import create_engine

# 1. Connect
engine = create_engine('postgresql://postgres:password@localhost:5432/microbiome_db')

print("Fetching Biomarker Data...")

# 2. Get Data for Plot 1 (Obesity vs Akkermansia)
query_bmi = """
SELECT 
    CASE 
        WHEN bmi BETWEEN 18.5 AND 25 THEN 'Normal Weight'
        WHEN bmi > 30 THEN 'Obese'
    END as bmi_group,
    akkermansia
FROM samples s
JOIN key_species k ON s.sample_id = k.sample_id
WHERE bmi > 0 AND bmi < 60
  AND (bmi BETWEEN 18.5 AND 25 OR bmi > 30)
"""
df_bmi = pd.read_sql(query_bmi, engine)

# 3. Get Data for Plot 2 (Antibiotics vs Faecalibacterium)
query_abx = """
SELECT 
    CASE 
        WHEN antibiotic_history = 'Week' THEN 'Recent Antibiotics'
        WHEN antibiotic_history = 'I have not taken antibiotics in the past year.' THEN 'No Antibiotics (1 Yr+)'
    END as status,
    faecalibacterium
FROM samples s
JOIN key_species k ON s.sample_id = k.sample_id
WHERE antibiotic_history IN ('Week', 'I have not taken antibiotics in the past year.')
"""
df_abx = pd.read_sql(query_abx, engine)

# 4. Create the Chart (2 Side-by-Side Plots)
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Plot A: Obesity
sns.boxplot(data=df_bmi, x='bmi_group', y='akkermansia', ax=axes[0], palette='Blues', showfliers=False)
axes[0].set_title('Impact of Obesity on Akkermansia (p=0.011)', fontsize=14)
axes[0].set_ylabel('Abundance Count')
axes[0].set_xlabel('')

# Plot B: Antibiotics
sns.boxplot(data=df_abx, x='status', y='faecalibacterium', ax=axes[1], palette='Reds', showfliers=False)
axes[1].set_title('Impact of Recent Antibiotics on Faecalibacterium (p=0.016)', fontsize=14)
axes[1].set_ylabel('Abundance Count')
axes[1].set_xlabel('')

plt.tight_layout()
plt.savefig('results/medical_biomarkers.png')
print("Final chart saved as 'medical_biomarkers.png'")