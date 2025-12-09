import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from sqlalchemy import create_engine
from scipy.stats import ttest_ind

# 1. Connect
engine = create_engine('postgresql://postgres:password@localhost:5432/microbiome_db')

print("Fetching Lifestyle Data...")

# 2. Get Data
query = """
SELECT 
    vitamin_d_freq,
    vitamin_b_freq,
    multivitamin_freq,
    acne_med_freq,
    m.shannon_entropy
FROM samples s
JOIN gut_metrics m ON s.sample_id = m.sample_id
"""
df = pd.read_sql(query, engine)

# --- DEBUG: Print unique values so we know what to fix ---
print("\n--- Unique Values found in Database ---")
print(f"Multivitamin: {df['multivitamin_freq'].unique()}")
print(f"Acne Meds:    {df['acne_med_freq'].unique()}")

# 3. Setup Grid
fig, axes = plt.subplots(2, 2, figsize=(16, 12))
fig.suptitle('Impact of Supplements & Acne Meds on Gut Diversity (Cleaned)', fontsize=16)

# --- HELPER: CLEANER FUNCTION ---
def clean_and_plot_generic(df, col, ax, title):
    # Standardize values: Map synonyms to a common name
    # We use a dictionary to merge "Yes"/"true" and "No"/"false"
    clean_map = {
        'Daily': 'Daily', 'Regularly (3-5 times/week)': 'Daily',
        'Never': 'Never', 'Rarely (less than once/week)': 'Never',
        'Yes': 'User', 'true': 'User', 'True': 'User',
        'No': 'Non-User', 'false': 'Non-User', 'False': 'Non-User'
    }
    
    # Create a new temporary column with cleaned values
    df['clean_group'] = df[col].map(clean_map)
    
    # Drop rows that didn't match our map (like "Unspecified" or "Unknown")
    subset = df.dropna(subset=['clean_group']).copy()
    
    if len(subset) == 0:
        ax.text(0.5, 0.5, 'No Matching Data', ha='center')
        return

    # Sort order depends on the type of group
    if 'User' in subset['clean_group'].values:
        order = ['Non-User', 'User']
    else:
        order = ['Never', 'Daily']

    # Plot
    sns.boxplot(data=subset, x='clean_group', y='shannon_entropy', ax=ax, palette='Set2', order=order, showfliers=False)
    ax.set_title(title)
    ax.set_xlabel('')
    ax.set_ylabel('Diversity Score')

    # Stats (T-Test)
    group1 = subset[subset['clean_group'] == order[0]]['shannon_entropy'] # e.g. Never
    group2 = subset[subset['clean_group'] == order[1]]['shannon_entropy'] # e.g. Daily
    
    if len(group1) > 1 and len(group2) > 1:
        t, p = ttest_ind(group1, group2, equal_var=False)
        # Color code the P-value: Red if significant, Black if not
        color = 'red' if p < 0.05 else 'black'
        ax.text(0.5, 0.9, f'p={p:.4f}', transform=ax.transAxes, ha='center', fontsize=12, color=color, fontweight='bold')

# --- PLOT 1: VITAMIN D ---
clean_and_plot_generic(df, 'vitamin_d_freq', axes[0, 0], 'Vitamin D')

# --- PLOT 2: MULTIVITAMIN ---
clean_and_plot_generic(df, 'multivitamin_freq', axes[0, 1], 'Multivitamin')

# --- PLOT 3: VITAMIN B ---
clean_and_plot_generic(df, 'vitamin_b_freq', axes[1, 0], 'Vitamin B')

# --- PLOT 4: ACNE MEDICATION ---
clean_and_plot_generic(df, 'acne_med_freq', axes[1, 1], 'Acne Medication')

plt.tight_layout()
plt.savefig('results/lifestyle_analysis_cleaned.png')
print("\nCleaned Analysis Complete! Saved to 'results/lifestyle_analysis_cleaned.png'")