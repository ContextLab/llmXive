# Quickstart: Predicting Plant Stress Response from Publicly Available Proteomic Data

## Prerequisites
- Python 3.11 or newer  
- R ≥ 4.2 with the `biomaRt` package installed (required for identifier mapping)  
- Git  
- Access to a GitHub Actions runner (or a local Linux environment with ≈ 7 GB RAM)  

## Installation

```bash
# Clone the repository
git clone <repo-url>
cd projects/PROJ-267-predicting-plant-stress-response-from-pu

# Set up a Python virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r code/requirements.txt
```

## Running the Pipeline

### 1. Data Ingestion & Preprocessing
```bash
# Ingest (will attempt to download the verified dummy datasets)
python code/data/ingest.py --species Arabidopsis --stress Drought

# Preprocess (normalization, filtering, LCM imputation, biomaRt mapping)
python code/data/preprocess.py
```
*If no paired plant data are found, the script logs a clear “Data Unavailable” message and exits gracefully.*

### 2. Model Training
```bash
# Random Forest (5‑fold CV; falls back to LOOCV if n < 50)
python code/models/train.py --model random_forest --cv_folds 5

# Support Vector Regression
python code/models/train.py --model svr --cv_folds 5
```

### 3. Evaluation & Reporting
```bash
# Cross‑stress evaluation (example: train on Drought, test on Salinity)
python code/models/evaluate.py --train_stress Drought --test_stress Salinity

# Generate all figures
python code/viz/plots.py
```

### 4. Runtime Metrics
```bash
cat results/runtime_metrics.json
```
The JSON file contains `total_time_seconds` and `peak_memory_mb`. The pipeline aborts automatically if limits are exceeded.

## Data Availability Limitation
Given the current lack of verified open paired proteomic‑transcriptomic datasets for the target species‑stress combinations, the pipeline will run on the dummy datasets only for validation of the code. When appropriate data become available, replace the dummy URLs in `code/data/ingest.py` with the new sources; the rest of the pipeline requires no changes.

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `biomaRt` import error | R or the package not installed | Install R ≥ 4.2 and run `install.packages("biomaRt")` in R. |
| No files under `data/raw/` | Ingestion could not locate a verified paired dataset | Check `logs/pipeline.log` for “Data Unavailable” and verify the URLs in `research.md`. |
| MemoryError | Dataset larger than RAM | Re‑run `preprocess.py` with `--sample_size 1000` to limit to a random subset. |
| Runtime exceeds 6 h | Model complexity too high | Reduce `n_estimators` in Random Forest (via `--n_estimators 100`). |

---

