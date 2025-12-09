import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from sqlalchemy import create_engine

# 1. Connect
engine = create_engine('postgresql://postgres:password@localhost:5432/microbiome_db')

# 2. Get the Data (The query you just ran)
query = """
SELECT 
    CASE 
        WHEN diet_type = 'Vegan' THEN 'Vegan'
        WHEN diet_type = 'Omnivore' AND red_meat_freq IN ('Rarely (less than once/week)', 'Occasionally (1-2 times/week)') THEN 'Moderate Omnivore'
        WHEN diet_type = 'Omnivore' AND red_meat_freq IN ('Daily', 'Regularly (3-5 times/week)') THEN 'High-Meat Omnivore'
        ELSE 'Other'
    END as diet_group,
    prevotella,
    bacteroides
FROM samples s
JOIN key_species k ON s.sample_id = k.sample_id
WHERE diet_type IN ('Vegan', 'Omnivore')
"""
df = pd.read_sql(query, engine)

# Filter out "Other"
df = df[df['diet_group'] != 'Other']

# 3. Reshape for Plotting (Melt)
# We convert "Prevotella" and "Bacteroides" columns into a single "Bacteria Type" column
df_melted = df.melt(id_vars=['diet_group'], value_vars=['prevotella', 'bacteroides'], 
                    var_name='Bacteria Genus', value_name='Count')

# 4. Create Bar Plot
plt.figure(figsize=(10, 6))
sns.barplot(data=df_melted, x='diet_group', y='Count', hue='Bacteria Genus', 
            order=['Vegan', 'Moderate Omnivore', 'High-Meat Omnivore'],
            palette=['#2ecc71', '#e74c3c']) # Green for Prevotella, Red for Bacteroides

plt.title('Gut Bacteria Composition: Vegans vs. Meat Eaters')
plt.ylabel('Abundance Count')
plt.xlabel('Diet Tribe')
plt.legend(title='Bacteria Genus')
plt.grid(axis='y', linestyle='--', alpha=0.3)

plt.savefig('results/species_comparison.png')
print("Chart saved as 'species_comparison.png'")