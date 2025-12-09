import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sqlalchemy import create_engine
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report

# 1. Connect to Database
engine = create_engine('postgresql://postgres:password@localhost:5432/microbiome_db')

print("Fetching Multi-Dimensional Data...")

# 2. Get Data: Join Lab Metrics with Patient Demographics
# We filter for valid BMI and Plant Types to ensure high-quality data
query = """
SELECT 
    m.shannon_entropy, 
    m.phylogenetic_diversity, 
    m.species_count,
    s.bmi,
    s.plant_types_count,
    s.antibiotic_history
FROM gut_metrics m
JOIN samples s ON m.sample_id = s.sample_id
WHERE s.antibiotic_history IN ('Month', 'Year', 'I have not taken antibiotics in the past year.')
  AND s.bmi > 0
  AND s.plant_types_count IS NOT NULL
"""
df = pd.read_sql(query, engine)

# 3. Define Target
# 1 = High Risk (Antibiotics in last Month)
# 0 = Low Risk (Year ago or Never)
df['target'] = df['antibiotic_history'].apply(lambda x: 1 if x == 'Month' else 0)

# 4. Define Features (The "Composite Health Profile")
features = ['shannon_entropy', 'phylogenetic_diversity', 'species_count', 'bmi', 'plant_types_count']
X = df[features]
y = df['target']

# 5. Train Gradient Boosting Model
print(f"Training Gradient Boosting on {len(df)} samples...")
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

gb_model = GradientBoostingClassifier(n_estimators=300, learning_rate=0.05, max_depth=4, random_state=42)
gb_model.fit(X_train, y_train)

# 6. Evaluate
preds = gb_model.predict(X_test)
acc = accuracy_score(y_test, preds)

print(f"\nModel Accuracy: {acc:.2%}")
print("\nClassification Report:")
print(classification_report(y_test, preds))

# 7. Feature Importance Analysis
importances = gb_model.feature_importances_
indices = np.argsort(importances)[::-1]

print("\n--- What predicts Antibiotic Damage? ---")
for i in indices:
    print(f"{features[i]}: {importances[i]:.4f}")

# 8. Save Visualization
plt.figure(figsize=(10, 5))
sns.barplot(x=importances[indices], y=[features[i] for i in indices], palette='magma')
plt.title('Key Drivers of Antibiotic-Associated Gut Damage')
plt.xlabel('Importance Score')
plt.tight_layout()
plt.savefig('results/advanced_feature_importance.png')
print("\nChart saved as 'advanced_feature_importance.png'")