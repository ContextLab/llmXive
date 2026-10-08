# Quickstart: Predicting Glass‑Forming Regions with Thermodynamic Descriptors

This guide walks you through reproducing the entire research pipeline on a fresh GitHub Actions runner (or locally on Linux/macOS).

## Prerequisites
- **Python 3.11** (or later)  
- **Git** (to clone the repository)  
- Internet access (to download OQMD data and the open CCR dataset from HuggingFace)  

All required packages are pinned in `requirements.txt`.

## Setup

```bash
# 1. Clone the repository
git clone https://github.com/your-org/predict-glass-forming-region.git
cd predict-glass-forming-region

# 2. Create a virtual environment
python -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
```

## Step‑by‑Step Execution

| Step | Command | Description | Output |
|------|---------|-------------|--------|
| **0** | `python -m pip install -U pip setuptools wheel` | Ensure build tools are up‑to‑date. | – |
| **1** | `python code/ingestion.py` | Downloads OQMD elemental tables **and** the open experimental CCR dataset, filters invalid rows, computes thermodynamic descriptors, writes `data/processed/processed_alloys.csv`. Also creates checksum file `data/checksums.txt`, logs (`ingestion.log`, `exclusion_log.txt`), and writes `data/logs/ingestion_hash.txt`. If the filtered dataset contains < 500 rows, the script aborts with a clear error and writes `data/logs/empty_dataset_error.log`. | `data/processed/processed_alloys.csv`, `data/checksums.txt`, `data/logs/ingestion.log`, `data/logs/exclusion_log.txt`, `data/logs/ingestion_hash.txt`, `data/logs/empty_dataset_error.log` (if triggered) |
| **2** | `python code/training.py` | Performs stratified 80/20 split, fits Random Forest, runs 5‑fold CV on the training set, evaluates on test set, saves model (`random_forest_model.pkl`) and metrics (`cv_metrics.json`). | `data/models/random_forest_model.pkl`, `data/models/cv_metrics.json` |
| **3** | `python code/analysis.py` | Computes permutation importance (`feature_importance.csv`), runs sensitivity sweep across `[50, 100, 150] K/s`, checks collinearity, writes reports. | `data/reports/feature_importance.csv`, `data/reports/sensitivity_report.json` |
| **4** | `python code/validate_schemas.py` | Validates **all** generated artifacts against their YAML contracts (`features.schema.yaml`, `processed_alloys.schema.yaml`, `metrics.schema.yaml`, `feature_importance.schema.yaml`, `sensitivity.schema.yaml`, `model_output.schema.yaml`). Fails the run if any error appears. | Console log “All schemas validated – 0 errors.” |
| **5** | `head data/reports/feature_importance.csv` | Quick peek at the top‑3 important descriptors. | (display) |
| **6** | `cat data/reports/sensitivity_report.json` | View RMSE stability across thresholds. | (display) |
| **7** | `cat data/checksums.txt` | Verify artifact hashes for reproducibility. | (display) |

## Re‑Running the Pipeline
All scripts are **idempotent**: re‑executing any step overwrites the corresponding outputs and updates the checksum file. Ensure you delete previous artifacts if you want a completely fresh run:

```bash
rm -rf data/processed/* data/models/* data/reports/* data/logs/*
python code/ingestion.py
# … continue with steps 2‑4
```

## Expected Runtime & Resources
- Total CPU time ≤ 5 hours on the GitHub Actions free tier.  
- Peak memory ≤ 2 GB (streamed OQMD loading).  
- No GPU is required.

## Troubleshooting
- **Empty dataset error**: Check `data/logs/empty_dataset_error.log`. If the experimental CCR dataset contains < 500 valid rows, the pipeline aborts with a clear error.  
- **Missing elemental property**: Verify that the OQMD revision hash matches the one recorded in `data/checksums.txt`.  
- **Schema validation failures**: Run `python code/validate_schemas.py --verbose` to see detailed mismatches.

## Reproducibility Checklist
- Random seeds are fixed (`random_state=42`).  
- All external data are fetched from the same URLs listed in the **Verified Datasets** table (see `plan.md`).  
- Checksums are recorded; any change triggers a CI failure.

You now have a fully reproducible end‑to‑end pipeline for assessing the predictive power of thermodynamic descriptors on glass‑forming ability. 🎉
