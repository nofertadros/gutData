-- 1. Clean Slate
DROP TABLE IF EXISTS key_species;
DROP TABLE IF EXISTS gut_metrics;
DROP TABLE IF EXISTS samples CASCADE;

-- 2. Patient Dimension Table (Demographics + Diet + Lifestyle + Polypharmacy)
CREATE TABLE samples (
    sample_id VARCHAR(50) PRIMARY KEY,
    age NUMERIC,
    sex VARCHAR(20),
    bmi NUMERIC,
    country VARCHAR(50),
    antibiotic_history VARCHAR(100),
    diet_type VARCHAR(100),
    plant_types_count NUMERIC,
    alcohol_freq VARCHAR(100),
    red_meat_freq VARCHAR(100),
    -- Polypharmacy Columns
    probiotic_freq VARCHAR(100),
    vitamin_b_freq VARCHAR(100),
    vitamin_d_freq VARCHAR(100),
    multivitamin_freq VARCHAR(100),
    acne_med_freq VARCHAR(100)
);

-- 3. Lab Metrics Fact Table
CREATE TABLE gut_metrics (
    sample_id VARCHAR(50) PRIMARY KEY REFERENCES samples(sample_id),
    shannon_entropy NUMERIC,
    phylogenetic_diversity NUMERIC,
    species_count NUMERIC
);

-- 4. Taxonomy Fact Table (Key Biomarkers)
CREATE TABLE key_species (
    sample_id VARCHAR(50) PRIMARY KEY REFERENCES samples(sample_id),
    prevotella NUMERIC,
    bacteroides NUMERIC,
    roseburia NUMERIC,
    bifidobacterium NUMERIC,
    alistipes NUMERIC,
    akkermansia NUMERIC,
    faecalibacterium NUMERIC,
    lactobacillus NUMERIC
);