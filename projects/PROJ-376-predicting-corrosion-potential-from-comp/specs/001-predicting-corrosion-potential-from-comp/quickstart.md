# Quickstart: Predicting Corrosion Potential from Composition and Environment

## Prerequisites
- Python 3.11+  
- `git`  
- Access to GitHub Actions (or a local Linux environment with ≥ 2 CPU cores and ~7 GB RAM).  

## Installation

```bash
# Clone the repository
git clone <repo-url>
cd projects/PROJ-376-predicting-corrosion-potential-from-comp

# Create a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Install dependencies
pip install -r code/requirements.txt
```

## Configuration

Create the required config files (if not already present):

```yaml
# code/config/seeds.yaml
random_seed: 42
numpy_seed: 42
```

```yaml
# code/config/paths.yaml
raw_data_dir: "data/raw"
processed_data_dir: "data/processed"
logs_dir: "data/logs"
contracts_dir: "contracts"
```

## Running the Pipeline

The pipeline is orchestrated via `run_pipeline.py`. Each stage can be run independently; the pipeline will stop automatically if any validation fails.

```bash
# 1️⃣ Data ingestion (will attempt NIST‑IR‑8200; expect a halt if unavailable)
python code/cli/run_pipeline.py --stage download

# 2️⃣ Schema validation (checks record count & required fields)
python code/cli/run_pipeline.py --stage validate

# 3️⃣ Preprocessing & train‑test split (includes environment balancing)
python code/cli/run_pipeline.py --stage preprocess

# 4️⃣ Model training (Random Forest & Gradient Boosting)
python code/cli/run_pipeline.py --stage train

# 5️⃣ Evaluation (R², RMSE, learnability classification)
python code/cli/run_pipeline.py --stage evaluate

# 6️⃣ Interpretability (Conditional Permutation Importance & ALE plots)
python code/cli/run_pipeline.py --stage interpret
```

**Important**:  
- If the ingestion stage cannot retrieve ≥ 500 valid records with ≥ 10 distinct alloys, the pipeline will raise `SchemaMismatchError` and stop, per FR‑014 and FR‑017.  
- No synthetic data are generated; the failure is reported in `data/logs/pipeline.log`.  

## Expected Outputs
- `data/processed/clean_dataset.parquet` – ready‑to‑train dataset.  
- `results/metrics.json` – R², RMSE, learnability flag.  
- `results/feature_importance.png` – top‑5 conditional importance plot.  
- `results/ale_plots/` – ALE plots for key composition‑environment interactions.  
- `data/logs/pipeline.log` – full execution trace, including any back‑off retries (FR‑015).  

## Troubleshooting
- **`SchemaMismatchError`** – Check `data/logs/schema_validation.log` for the exact record count and missing fields.  
- **Network errors (429)** – The downloader automatically retries with exponential backoff; see `data/logs/download.log`.  
- **Memory errors** – The downloader streams data (`streaming=True`) to stay within the 7 GB RAM limit.  

---

