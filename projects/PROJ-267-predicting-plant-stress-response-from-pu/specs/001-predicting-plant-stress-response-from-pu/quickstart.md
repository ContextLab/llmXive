# Quickstart: Predicting Plant Stress Response from Publicly Available Proteomic Data

## Prerequisites
- Python 3.11 or newer  
- R ≥ 4.2 with the `biomaRt` package installed (required for identifier mapping)  
- Git  
- Access to a GitHub Actions runner (or a local Linux environment with sufficient RAM)  

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
# Ingest (downloads the dummy NCBI zip and the GEO GSE14784 metadata)
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

This trains **proteomics‑only** Random Forest **classifier** to predict the stress condition (Drought, Salinity, Heat) and outputs `results/runtime_metrics.json` with `accuracy` and `f1_score`. If **no** proteomics‑only data are available, the script logs “**Data Unavailable**” and stops.

## Contract Validation
```bash
# Validate that the processed dataset and model output conform to the JSON schemas
python code/tasks/schema_validate.py \
  --dataset contracts/dataset.schema.yaml \
  --model_output contracts/model_output.schema.yaml
```

**Note:** The model performance report is written **`results/model_output.json`** and must conform to `contracts/model_output.schema.yaml`.

---

