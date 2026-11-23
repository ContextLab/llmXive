# Data Directory

This directory stores all data artifacts generated or consumed by the pipeline.

## Subdirectories
- `raw/`: Original downloaded datasets (e.g., from Zenodo).
- `processed/`: Cleaned, transformed, and intermediate data files.
- `generated/`: Outputs from specific scripts (e.g., descriptors, predictions).

## Note
Do not commit large binary files to git. Add `data/raw/*` and `data/processed/*` to `.gitignore`.
