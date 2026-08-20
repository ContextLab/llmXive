# Quickstart: Predicting Molecular Packing Efficiency Pipeline

This guide runs the full pipeline from raw CIF downloads to final dataset and model evaluation.

## Prerequisites

- Python 3.8+
- Install dependencies: `pip install -r requirements.txt`

## Run the Pipeline

Execute the following commands in order:

```bash
# 1. Setup directories
python code/setup.py

# 2. Download CIF files
python code/download_cif.py

# 3. Parse CIFs and generate intermediate dataset
python code/parse_cif.py

# 4. Compute raw metrics (PC_raw, CAPE)
python code/compute_RAW_metrics.py

# 5. Filter dataset
python code/filter_dataset.py

# 6. Add 3D descriptors (T018)
python code/add_3d_descriptors.py

# 7. Validate dataset
python code/validate_dataset.py

# 8. Assemble features
python code/feature_assembly.py

# 9. Train model
python code/train.py

# 10. Evaluate model
python code/evaluate.py

# 11. Generate report
python code/generate_report.py

# 12. Sensitivity analysis
python code/sensitivity.py
```

## Expected Outputs

- `data/dataset_intermediate.csv`
- `data/dataset_with_metrics.csv`
- `data/dataset_filtered.csv`
- `data/dataset.csv` (final dataset with 3D descriptors)
- `models/mlp.pt`
- `results/validation_report.json`
- `results/report.html`
- `results/sensitivity_sweep.csv`
