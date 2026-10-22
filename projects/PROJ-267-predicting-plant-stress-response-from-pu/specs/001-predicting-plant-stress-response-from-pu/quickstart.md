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
source venv/bin/activate   # Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r code/requirements.txt
```

## Running the Pipeline

### 1. Data Ingestion & Preprocessing
```bash
# Ingest (downloads the verified dummy datasets)
python code/data/ingest.py --species Arabidopsis --stress Drought

# Preprocess (fold‑wise preprocessing; see code/comments for details)
python code/data/preprocess.py --mode fit_transform
```
*If no paired plant data are found, the script logs a clear “**Data Unavailable**” notice and exits gracefully.*

### 2. Model Training (Regression Path)
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
The JSON file contains `total_time_seconds`, `peak_memory_mb`, and a `power_sufficient` flag. The pipeline aborts automatically if limits are exceeded.

## Fallback Classification (When Paired Data Are Insufficient)
If the data‑inventory check (FR‑009) reports fewer than three paired samples for every species‑stress combination, the pipeline automatically runs:

```bash
python code/models/train_classifier.py --model random_forest
```

This trains a **proteomics‑only Random Forest classifier** to predict the stress condition (Drought, Salinity, Heat) and outputs `results/runtime_metrics.json` with `accuracy` and `f1_score`. If no proteomics‑only data are available, the script logs “**Data Unavailable**” and stops.

## Contract Validation
```bash
# Validate that the processed dataset and model output conform to the JSON schemas
python code/tasks/schema_validate.py \
  --dataset contracts/dataset.schema.yaml \
  --model_output contracts/model_output.schema.yaml
```

## Data Availability Limitation
Given the current **absence of verified open paired proteomic‑transcriptomic plant‑stress datasets** for Arabidopsis, rice, or wheat under drought, salinity, or heat, the pipeline will run on the **dummy NCBI zip and GEO JSON** only for code‑validation **and** will emit **“Data Unavailable”** when appropriate data are missing. The fallback classification will be attempted if any proteomics‑only data are present.

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `ImportError: cannot import name 'biomaRt'` | R or the package not installed | Install R ≥ 4.2 and run `install.packages("biomaRt")` in an R session. |
| No files under `data/raw/` | Ingestion could not locate a verified paired dataset | Check `logs/pipeline.log` for the “Data Unavailable” notice and verify the URLs in `research.md`. |
| `MemoryError` | Dataset larger than RAM | Re‑run `preprocess.py` with `--sample_size 1000` to limit to a random subset (adds `--sample_size` flag). |
| Runtime exceeds 6 h | Model complexity too high | Reduce `n_estimators` in Random Forest (`--n_estimators 100`). |
| Missing entries in `pipeline.log` | Logger not imported in a module | Ensure each script starts with `from utils.logger import get_logger; logger = get_logger(__name__)`. |
| Validation fails | Schema mismatch | Run the validation command above; fix any schema violations reported. |

---
