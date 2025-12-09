# Source Data & Derived Metrics

This directory contains the raw biological data, metadata surveys, and intermediate processed files used in the analysis.

## File Descriptions

### Raw Source Data (American Gut Project)
* **`ag-cleaned.txt`**: The primary metadata file containing patient demographics, diet surveys, BMI, antibiotic history, and medication frequency.
* **`ag-gg-100nt.biom`**: The sparse biological matrix containing 16S rRNA sequence counts (Taxonomy) for all samples.
* **`*.7z` files**: Compressed backups of the large text and biom files to save space.

### Alpha Diversity Metrics (Target Variables)
These text files contain pre-calculated diversity scores for each sample ID:
* **`shannon.txt`**: Shannon Entropy (measures species richness and evenness). This is the primary target variable for the Machine Learning model.
* **`PD_whole_tree.txt`**: Phylogenetic Diversity (measures evolutionary distance between species).
* **`observed_otus.txt`**: A count of unique species observed per sample.

### Processed/Intermediate Files
* **`species_counts.csv`**: The output of `extract_species.py`. It contains the aggregated counts for specific keystone genera (e.g., *Akkermansia*, *Prevotella*, *Faecalibacterium*) extracted from the massive `.biom` file.
* **`drug_mapping.csv`**: Helper file used during the ETL process to normalize medication frequency inputs.
