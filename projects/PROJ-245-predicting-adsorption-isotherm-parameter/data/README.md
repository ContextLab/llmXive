# Data Directory

This directory stores all data artifacts generated during the pipeline execution.

## Subdirectories

- `raw/`: Unprocessed raw data (e.g., from NIST or synthetic generation)
- `processed/`: Cleaned and normalized data ready for modeling
- `external/`: Manually curated external validation datasets
- `generated/`: Intermediate files or synthetic datasets

## Expected Files

- `processed/curated_adsorption.csv`: The main dataset for training
- `processed/outliers.csv`: Flagged outlier entries
- `external/kr_cnt.csv`: Krypton on Carbon Nanotubes validation data
