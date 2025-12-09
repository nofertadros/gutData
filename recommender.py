import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler

# 1. Connect
engine = create_engine('postgresql://postgres:password@localhost:5432/microbiome_db')

print("--- Building the 'Healthy Twin' Recommender ---")

# 2. Get the Data
# Fixed the "Ambiguous Column" error by using "s.sample_id"
query = """
SELECT 
    s.sample_id,
    s.age, 
    s.bmi, 
    s.sex,
    s.plant_types_count,
    s.red_meat_freq,
    s.alcohol_freq,
    m.shannon_entropy
FROM samples s
JOIN gut_metrics m ON s.sample_id = m.sample_id
WHERE s.age IS NOT NULL 
  AND s.bmi > 0
  AND s.sex IN ('male', 'female')
  AND s.plant_types_count IS NOT NULL
"""
df = pd.read_sql(query, engine)

# 3. Define "Success" (High Diversity)
# We define "Healthy" as the top 25% of the population
healthy_threshold = df['shannon_entropy'].quantile(0.75)
print(f"Target Diversity Score: > {healthy_threshold:.2f}")

# Split into "Candidates" (Healthy People)
candidates = df[df['shannon_entropy'] > healthy_threshold].copy()
print(f"Pool of Healthy Twins: {len(candidates)} people")

# 4. Prepare for Machine Learning
# Convert Sex to numbers (Male=0, Female=1)
candidates['sex_code'] = candidates['sex'].apply(lambda x: 1 if x == 'female' else 0)

# Features we match on: Age, BMI, Sex
features = ['age', 'bmi', 'sex_code']
X = candidates[features]

# Scale data (Age 50 vs BMI 25 are different scales, scaling makes them equal weight)
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# 5. Train the Nearest Neighbors Model
knn = NearestNeighbors(n_neighbors=5, metric='euclidean')
knn.fit(X_scaled)

# --- INTERACTIVE USER INPUT ---
print("\n" + "="*30)
print("   FIND YOUR MICROBIOME TWIN")
print("="*30)

try:
    my_age = float(input("1. Enter your Age: "))
    my_bmi = float(input("2. Enter your BMI (e.g. 24.5): "))
    sex_input = input("3. Enter your Sex (male/female): ").lower().strip()
    
    # Simple validation for sex
    if sex_input not in ['male', 'female']:
        print("Invalid sex entered. Defaulting to 'male'.")
        sex_input = 'male'
        
    my_sex = sex_input
    
except ValueError:
    print("\nError: Please enter numbers for Age and BMI.")
    exit()

print(f"\nSearching database for Healthy Twins ({my_age} y/o {my_sex}, BMI {my_bmi})...")

# Format the input
my_sex_code = 1 if my_sex == 'female' else 0
my_profile = pd.DataFrame([[my_age, my_bmi, my_sex_code]], columns=features)
my_profile_scaled = scaler.transform(my_profile)

# 6. Find Twins
distances, indices = knn.kneighbors(my_profile_scaled)
twins = candidates.iloc[indices[0]]

print("\n--- Found 5 'Healthy Twins' ---")
# Show who they are
print(twins[['age', 'sex', 'bmi', 'shannon_entropy', 'plant_types_count']].to_string(index=False))

# 7. Generate Recommendations
print("\n" + "="*30)
print("   YOUR PERSONALIZED PLAN")
print("="*30)

# Calculate the average habits of your "Twins"
avg_plants = twins['plant_types_count'].mean()
print(f"1. Plant Diversity: Your twins eat {avg_plants:.0f} types of plants per week.")

# Find the most common habits
if not twins['red_meat_freq'].mode().empty:
    common_meat = twins['red_meat_freq'].mode()[0]
    print(f"2. Meat Frequency:  Most of them eat meat '{common_meat}'.")

if not twins['alcohol_freq'].mode().empty:
    common_alcohol = twins['alcohol_freq'].mode()[0]
    print(f"3. Alcohol:         Most of them drink '{common_alcohol}'.")

print("\nGoal: Match these habits to reach a Diversity Score of > 6.0! (not medical advice! :) )")