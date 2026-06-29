# Quickstart: Predicting Molecular Packing Efficiency

This guide shows how to run the full end‑to‑end pipeline on a fresh GitHub Actions runner (or locally) using the provided scripts.

## Prerequisites
```bash
# Clone the repository
git clone
cd PROJ-511-predicting-molecular-packing-efficiency

# Create a virtual environment
python -m venv.venv
source.venv/bin/activate

# Install exact pinned dependencies
pip install -r requirements.txt
```

## Step‑by‑Step Execution
```bash
# 1. Download and filter COD data (≥500 records expected)
python code/download_cif.py --max_atoms 50 --min_records 500

# 2. Parse CIFs, extract/generate SMILES, and compute basic geometry
python code/parse_cif.py

# 3. Compute packing coefficients, CAPE, and 3‑D descriptors (from molecule conformers)
python code/compute_features.py

# 4. **Validate** the generated CSV against the schema
python code/validate_dataset.py data/dataset.csv contracts/dataset.schema.yaml

# 5. Train the lightweight MLP (20% validation split, confounders included)
python code/train_mlp.py --seed 42

# 6. Evaluate model and run statistical tests (VIF on PCA components, permutation test)
python code/evaluate.py

# 7. **Optional ablation**: train without 3‑D descriptors to check circularity
python code/ablation.py --seed 42

# 8. Sensitivity analysis over high‑packing thresholds
python code/sensitivity.py

# 9. Generate the final HTML report
python code/generate_report.py

# 10. Validate outputs against schemas
python -m jsonschema -i results/validation_report.json contracts/validation_report.schema.yaml
```

## Expected Outputs
| File | Description |
|------|-------------|
| `data/dataset.csv` | Cleaned dataset with ≥ 500 rows, all required columns present. |
| `models/mlp_regressor.pt` | Trained MLP checkpoint. |
| `results/validation_report.json` | JSON metrics adhering to `validation_report.schema.yaml`. |
| `results/report.html` | Reproducible HTML report (view in a browser). |
| `results/ablation_report.json` *(optional)* | Metrics from the ablation run (no 3‑D descriptors). |

## Runtime & Resource Summary
- **Total runtime**: ≤ 6 hours on GitHub Actions free tier (2 CPU cores, ~7 GB RAM).
- **Memory usage**: < 4 GB during feature encoding; < 1 GB during MLP training.
- **No GPU**: All libraries are CPU‑only.

If any step aborts due to insufficient records (< 500 after filtering), the script will emit a clear warning and stop, satisfying the edge‑case handling described in the spec.

---

