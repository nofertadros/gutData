import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler

class MicrobiomeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Microbiome Twin Recommender")
        self.root.geometry("800x650")
        
        # Style configuration
        self.style = ttk.Style()
        self.style.theme_use('clam') 

        # --- DATA LOADING & TRAINING ---
        self.status_var = tk.StringVar()
        self.status_var.set("Status: Initializing...")
        
        # Load data and train model immediately on startup
        self.load_data_and_train()

        # --- GUI LAYOUT ---
        self.create_widgets()

    def load_data_and_train(self):
        """
        Attempts to connect to DB. If fails, creates dummy data so the UI still works.
        """
        try:
            # 1. Connect
            engine = create_engine('postgresql://postgres:password@localhost:5432/microbiome_db')
            
            query = """
            SELECT s.sample_id, s.age, s.bmi, s.sex, s.plant_types_count, 
                   s.red_meat_freq, s.alcohol_freq, m.shannon_entropy
            FROM samples s
            JOIN gut_metrics m ON s.sample_id = m.sample_id
            WHERE s.age IS NOT NULL AND s.bmi > 0 AND s.sex IN ('male', 'female')
              AND s.plant_types_count IS NOT NULL
            """
            self.df = pd.read_sql(query, engine)
            self.status_var.set("Status: Connected to Database.")
            
        except Exception as e:
            print(f"DB Connection failed: {e}")
            print("Generating DUMMY data for demonstration...")
            # GENERATE MOCK DATA if DB fails
            data = {
                'sample_id': range(100),
                'age': np.random.randint(18, 80, 100),
                'bmi': np.random.uniform(18.5, 35.0, 100),
                'sex': np.random.choice(['male', 'female'], 100),
                'plant_types_count': np.random.randint(5, 40, 100),
                'red_meat_freq': np.random.choice(['Daily', 'Weekly', 'Rarely', 'Never'], 100),
                'alcohol_freq': np.random.choice(['Daily', 'Weekly', 'Rarely'], 100),
                'shannon_entropy': np.random.uniform(2.0, 7.0, 100)
            }
            self.df = pd.DataFrame(data)
            self.status_var.set("Status: Using Dummy Data (DB Connection Failed)")

        # 2. Logic: Define Healthy
        healthy_threshold = self.df['shannon_entropy'].quantile(0.75)
        self.candidates = self.df[self.df['shannon_entropy'] > healthy_threshold].copy()
        
        # 3. Prepare ML
        self.candidates['sex_code'] = self.candidates['sex'].apply(lambda x: 1 if x == 'female' else 0)
        self.features = ['age', 'bmi', 'sex_code']
        
        X = self.candidates[self.features]
        
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)
        
        self.knn = NearestNeighbors(n_neighbors=5, metric='euclidean')
        self.knn.fit(X_scaled)

    def create_widgets(self):
        # --- Header ---
        header_frame = ttk.Frame(self.root, padding="20")
        header_frame.pack(fill='x')
        
        title_lbl = ttk.Label(header_frame, text="Find Your Microbiome Twin", font=("Helvetica", 18, "bold"))
        title_lbl.pack()
        
        subtitle_lbl = ttk.Label(header_frame, text="Enter your stats to find healthy people biologically similar to you.", font=("Helvetica", 10))
        subtitle_lbl.pack()

        # --- Input Section ---
        input_frame = ttk.LabelFrame(self.root, text="Your Profile", padding="15")
        input_frame.pack(fill='x', padx=20, pady=10)

        # Grid layout for inputs
        ttk.Label(input_frame, text="Age:").grid(row=0, column=0, padx=5, pady=5, sticky='e')
        self.age_entry = ttk.Entry(input_frame)
        self.age_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(input_frame, text="BMI:").grid(row=0, column=2, padx=5, pady=5, sticky='e')
        self.bmi_entry = ttk.Entry(input_frame)
        self.bmi_entry.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(input_frame, text="Sex:").grid(row=0, column=4, padx=5, pady=5, sticky='e')
        self.sex_combo = ttk.Combobox(input_frame, values=["Male", "Female"], state="readonly")
        self.sex_combo.grid(row=0, column=5, padx=5, pady=5)
        self.sex_combo.current(0)

        # Button
        search_btn = ttk.Button(input_frame, text="Find Healthy Twins", command=self.find_twins)
        search_btn.grid(row=1, column=0, columnspan=6, pady=15)

        # --- Results Section ---
        results_frame = ttk.Frame(self.root, padding="10")
        results_frame.pack(fill='both', expand=True, padx=20)

        # 1. The Table (Treeview)
        ttk.Label(results_frame, text="Your 5 Healthy Twins:", font=("Helvetica", 11, "bold")).pack(anchor='w')
        
        cols = ('Age', 'Sex', 'BMI', 'Diversity Score', 'Plants/Week')
        self.tree = ttk.Treeview(results_frame, columns=cols, show='headings', height=5)
        
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, anchor='center')
            
        self.tree.pack(fill='x', pady=5)

        # 2. Recommendations
        rec_frame = ttk.LabelFrame(self.root, text="Personalized Recommendations", padding="15")
        rec_frame.pack(fill='x', padx=20, pady=10)

        self.lbl_plants = ttk.Label(rec_frame, text="Plant Diversity: --", font=("Helvetica", 12))
        self.lbl_plants.pack(anchor='w', pady=2)

        self.lbl_meat = ttk.Label(rec_frame, text="Meat Frequency: --", font=("Helvetica", 12))
        self.lbl_meat.pack(anchor='w', pady=2)

        self.lbl_alcohol = ttk.Label(rec_frame, text="Alcohol Frequency: --", font=("Helvetica", 12))
        self.lbl_alcohol.pack(anchor='w', pady=2)

        # --- Status Bar ---
        status_lbl = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor='w')
        status_lbl.pack(side='bottom', fill='x')

    def find_twins(self):
        # 1. Get User Input
        try:
            my_age = float(self.age_entry.get())
            my_bmi = float(self.bmi_entry.get())
            my_sex_str = self.sex_combo.get().lower()
        except ValueError:
            messagebox.showerror("Input Error", "Please enter valid numbers for Age and BMI.")
            return

        # 2. Format Input for Model
        my_sex_code = 1 if my_sex_str == 'female' else 0
        my_profile = pd.DataFrame([[my_age, my_bmi, my_sex_code]], columns=self.features)
        
        # 3. Scale & Predict
        my_profile_scaled = self.scaler.transform(my_profile)
        distances, indices = self.knn.kneighbors(my_profile_scaled)
        
        # 4. Retrieve Twins Data
        twins = self.candidates.iloc[indices[0]]

        # 5. Update UI - Table
        # Clear old data
        for i in self.tree.get_children():
            self.tree.delete(i)
            
        # Insert new data
        for _, row in twins.iterrows():
            self.tree.insert("", "end", values=(
                int(row['age']), 
                row['sex'].capitalize(), 
                f"{row['bmi']:.1f}", 
                f"{row['shannon_entropy']:.2f}", 
                int(row['plant_types_count'])
            ))

        # 6. Update UI - Recommendations (Standard Text Only)
        # Avg Plants
        avg_plants = twins['plant_types_count'].mean()
        self.lbl_plants.config(text=f">> Plant Diversity Target: Eat {avg_plants:.0f} types per week")
        
        # Mode Habits
        if not twins['red_meat_freq'].mode().empty:
            common_meat = twins['red_meat_freq'].mode()[0]
            self.lbl_meat.config(text=f">> Recommended Meat Freq: {common_meat}")
        
        if not twins['alcohol_freq'].mode().empty:
            common_alcohol = twins['alcohol_freq'].mode()[0]
            self.lbl_alcohol.config(text=f">> Recommended Alcohol Freq: {common_alcohol}")
            
        self.status_var.set(f"Success: Found 5 twins for a {int(my_age)} y/o {my_sex_str}.")

if __name__ == "__main__":
    root = tk.Tk()
    app = MicrobiomeApp(root)
    root.mainloop()