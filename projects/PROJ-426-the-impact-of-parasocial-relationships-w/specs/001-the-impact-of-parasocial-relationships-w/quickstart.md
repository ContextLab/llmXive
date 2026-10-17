# Quickstart: The Impact of Parasocial Relationships with AI Companions on Loneliness

## Prerequisites
- Python 3.11 or newer  
- Git (or local copy of the repository)  
- Access to a GitHub Actions runner **or** a local machine with ≥ 7 GB RAM  

## Installation

```bash
# 1. Clone the repository (or navigate to the project directory)
cd projects/PROJ-426-the-impact-of-parasocial-relationships-w

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install pinned dependencies
pip install -r requirements.txt
```

## Running the End‑to‑End Pipeline

### Step 1 – Data Ingestion & Matching
```bash
python src/main.py --mode ingest_and_match
```
- **Output**: `data/processed/matched_users.parquet`  
- **Log**: `logs/ingest.log` (includes match‑rate, validation warnings, and any username‑hash mismatch report).  

### Step 2 – Model Fitting & Bootstrapping
```bash
python src/main.py --mode fit_model
```
- **Output**: `data/results/model_summary.json`  
- **Note**: This step runs **1 000** bootstrap iterations (seed = 42) and is optimized to complete ≤ 6 h on a CPU‑only runner (parallelized with `joblib`). If memory usage exceeds 7 GB, the pipeline will automatically down‑sample to [deferred] of users (validated by the power simulation).

### Step 3 – Contract Validation
```bash
pytest tests/contract/
```
All schemas under `contracts/` are validated against the generated artifacts.

## Expected Outputs

| Artifact | Description |
|---|---|
| `data/processed/matched_users.parquet` | Unified dataset with ≥ 80 % match rate (SC‑001). |
| `data/results/model_summary.json` | Fixed‑effect estimates, p‑values, 95 % bootstrap CIs, marginal R², and subgroup results (SC‑002, SC‑003). |
| `logs/model.log` | Runtime duration; should be ≤ 6 h (SC‑004). |

## Project Directory Structure
```
PROJECT_ROOT/
├─ code/
│  ├─ main.py
│  ├─ ingest/
│  │  └─ ... (data fetching scripts)
│  ├─ match/
│  │  └─ ... (user matching scripts)
│  ├─ utils/
│  │  └─ ... (helper utilities)
│  ├─ validation/
│  │  └─ ... (data validation scripts)
│  └─ models/
│     └─ mixed_effects.py
├─ data/
│  ├─ raw/
│  │  ├─ zenodo_loneliness.csv   # downloaded from Zenodo (if available)
│  │  └─ pushshift_logs.jsonl   # streamed from Pushshift API
│  ├─ processed/
│  │  └─ matched_users.parquet
│  └─ results/
│     └─ model_summary.json
├─ docs/
│  └─ ... (documentation, figures)
├─ contracts/
│  ├─ dataset.schema.yaml
│  ├─ model_output.schema.yaml
│  └─ unified_dataset.schema.yaml
├─ tests/
│  └─ contract/
│     └─ ... (schema validation tests)
├─ logs/
│  ├─ ingest.log
│  └─ model.log
├─ requirements.txt
└─ README.md
```

## Troubleshooting

| Symptom | Likely Cause | Remedy |
|---|---|---|
| `Data Linkage Impossible` | Zenodo DOI invalid or required columns missing. | Verify DOI; if unavailable, the study cannot proceed. |
| `Power Insufficient` | Matched users < 500 or match rate < 80 %. | Review data availability; consider expanding the download window or using an alternative open dataset. |
| `Lexicon Missing` | ECAR lexicon file not found at the verified URL. | Ensure internet connectivity; the URL is `https://huggingface.co/datasets/12ml/e-CARE/resolve/main/train.csv`. |
| Model fails to converge | Random‑slope structure too complex for data. | The pipeline will automatically fallback to a random‑intercept‑only model and log a warning. |
| Subgroup analysis skipped | Fewer than 80 users aged ≥ 60. | The pipeline will report a power warning and omit subgroup results. |

---


