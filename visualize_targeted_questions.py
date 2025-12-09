import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from sqlalchemy import create_engine
from scipy.stats import ttest_ind

# 1. Connect
engine = create_engine('postgresql://postgres:password@localhost:5432/microbiome_db')

print("Fetching Targeted Data...")

# 2. DATASET A: VEGANS & VITAMIN B
# We grab only Vegans to see if B-Vitamins change their specific ecosystem
query_vegan = """
SELECT 
    vitamin_b_freq,
    m.shannon_entropy
FROM samples s
JOIN gut_metrics m ON s.sample_id = m.sample_id
WHERE diet_type = 'Vegan'
"""
df_vegan = pd.read_sql(query_vegan, engine)

# 3. DATASET B: POST-ANTIBIOTIC USERS
# We grab only people in the "Danger Zone" (Week/Month after antibiotics)
# We want to see if Probiotics help THIS specific group
query_abx = """
SELECT 
    probiotic_freq,
    m.shannon_entropy
FROM samples s
JOIN gut_metrics m ON s.sample_id = m.sample_id
WHERE antibiotic_history IN ('Week', 'Month')
"""
df_abx = pd.read_sql(query_abx, engine)

# --- HELPER: CLEANING FUNCTION ---
def clean_and_prep(df, col):
    # Map messy text to clean "User" vs "Non-User"
    clean_map = {
        'Daily': 'Daily User', 'Regularly (3-5 times/week)': 'Daily User',
        'Never': 'Non-User', 'Rarely (less than once/week)': 'Non-User',
        'Yes': 'Daily User', 'true': 'Daily User',
        'No': 'Non-User', 'false': 'Non-User'
    }
    df['status'] = df[col].map(clean_map)
    return df.dropna(subset=['status'])

# Clean both datasets
df_vegan_clean = clean_and_prep(df_vegan, 'vitamin_b_freq')
df_abx_clean = clean_and_prep(df_abx, 'probiotic_freq')

# 4. SETUP PLOTS
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# --- PLOT 1: VEGANS & VITAMIN B ---
sns.boxplot(data=df_vegan_clean, x='status', y='shannon_entropy', ax=axes[0], 
            palette=['#e74c3c', '#2ecc71'], order=['Non-User', 'Daily User'], showfliers=False)
axes[0].set_title('Do Vegans need Vitamin B for Gut Health?', fontsize=13)
axes[0].set_ylabel('Diversity Score')
axes[0].set_xlabel('Vitamin B Supplementation')

# Stats for Plot 1
v_user = df_vegan_clean[df_vegan_clean['status'] == 'Daily User']['shannon_entropy']
v_non = df_vegan_clean[df_vegan_clean['status'] == 'Non-User']['shannon_entropy']
if len(v_user) > 1 and len(v_non) > 1:
    t1, p1 = ttest_ind(v_user, v_non, equal_var=False)
    axes[0].text(0.5, 0.9, f'p={p1:.4f}', transform=axes[0].transAxes, ha='center', 
                 fontsize=12, color='red' if p1 < 0.05 else 'black')
    axes[0].text(0.5, 0.85, f'(n={len(v_user)} vs {len(v_non)})', transform=axes[0].transAxes, ha='center', fontsize=10)

# --- PLOT 2: PROBIOTIC RESCUE ---
sns.boxplot(data=df_abx_clean, x='status', y='shannon_entropy', ax=axes[1], 
            palette=['#e74c3c', '#3498db'], order=['Non-User', 'Daily User'], showfliers=False)
axes[1].set_title('Do Probiotics Rescue Gut Diversity\n(After Recent Antibiotics)?', fontsize=13)
axes[1].set_ylabel('Diversity Score')
axes[1].set_xlabel('Probiotic Supplementation')

# Stats for Plot 2
a_user = df_abx_clean[df_abx_clean['status'] == 'Daily User']['shannon_entropy']
a_non = df_abx_clean[df_abx_clean['status'] == 'Non-User']['shannon_entropy']
if len(a_user) > 1 and len(a_non) > 1:
    t2, p2 = ttest_ind(a_user, a_non, equal_var=False)
    axes[1].text(0.5, 0.9, f'p={p2:.4f}', transform=axes[1].transAxes, ha='center', 
                 fontsize=12, color='red' if p2 < 0.05 else 'black')
    axes[1].text(0.5, 0.85, f'(n={len(a_user)} vs {len(a_non)})', transform=axes[1].transAxes, ha='center', fontsize=10)

plt.tight_layout()
plt.savefig('results/targeted_analysis.png')
print("Analysis Complete. Check 'results/targeted_analysis.png'")