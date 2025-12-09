# Archived & Deprecated Code

This directory contains scripts from "Phase 1" of development or utility tools that are no longer part of the final production pipeline. They are preserved here for documentation and version history.

## File Descriptions

### Deprecated Analysis Scripts
* **`etl_pipeline.py`**: The original, simpler ETL script. Replaced by `etl_advanced.py` (which handles the Snowflake schema and Polypharmacy columns).
* **`ml_model.py`**: The baseline Logistic Regression model (53% accuracy). Replaced by `ml_gradient_boost.py` (96% accuracy).
* **`stats_test.py`** & **`stats_anova.py`**: Early statistical experiments. Replaced by `stats_new_targets.py` which includes the clinical T-tests.
* **`visualize_results.py`**: Early plotting script. Replaced by the specific visualization modules in the root directory.

### Utility Tools
* **`scan_for_drugs.py`**: A one-time utility script used to scan the metadata headers to discover the exact column names for Vitamin D, Acne medication, etc. Not needed for the main pipeline execution.
