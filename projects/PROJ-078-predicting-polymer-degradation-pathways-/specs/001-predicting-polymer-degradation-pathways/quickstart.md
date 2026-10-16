# Quickstart: Predicting Polymer Degradation Pathways with Graph Neural Networks

## Prerequisites
- **Python 3.11** (or newer)  
- **GitHub Actions free‑tier** (2 CPU cores, ~7 GB RAM) – the steps below have been tested on this environment.  
- Internet access (no authentication required).

## Installation
```bash
# 1️⃣ Clone the repository
git clone <repo‑url>
cd projects/PROJ-078-predicting-polymer-degradation-pathways-/

# 2️⃣ Create a fresh virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3️⃣ Install pinned dependencies
pip install -r code/requirements.txt
```

## Step‑by‑Step Execution

### 0️⃣ Verify Setup (Reproducibility)
```bash
# Generate directory tree and timestamp (T001b)
find . -type f | sort > state/file_list.txt
date > state/setup_timestamp.txt
cat state/file_list.txt state/setup_timestamp.txt > state/setup_log.txt

# Lint check (should exit 0)
ruff check code/

# Run pytest with seeded environment (T008c)
pytest -q
# The test suite uses `tests/conftest.py` which pins numpy, torch, and random seeds to 42.
```

### 1️⃣ Data Download & Initial Validation  
> **NOTE:** A suitable open polymer degradation dataset is currently pending. Replace `<DATASET_URL>` with the verified URL once available.
```bash
python code/ingest.py \
  --url <DATASET_URL> \
  --output data/raw/polymer_records.csv
```
- Implements exponential backoff (max 3 retries).  
- Logs to `state/ingest.log`.

### 2️⃣ Label Scan & Curation Flagging
```bash
python code/label_validation.py \
  --input data/raw/polymer_records.csv \
  --output data/processed/records.parquet
```
- Flags missing `degradation_pathway` entries; **records without a curated label are excluded from training**.  
- If *all* records lack a label, the script aborts with a clear error.

### 3️⃣ SMILES Handling (no synthetic generation)
```bash
python code/preprocess.py \
  --input data/processed/records.parquet \
  --graph-dir data/processed/graphs/
```
- Skips any record with an invalid SMILES; logs SMILES to `state/invalid_smiles.log`.  
- Filters for polyesters using SMARTS `C(=O)O`.  

### 4️⃣ Power‑Analysis (ratified amendment)
```bash
python code/power_analysis.py \
  --records data/processed/records.parquet \
  --output state/power_analysis.json
# Verify ratification in state/amendments.yaml
```

### 5️⃣ Data Augmentation (bond rotation + atom masking)
```bash
python code/augment.py \
  --graph-dir data/processed/graphs/ \
  --output data/augmented/graphs/ \
  --method bond_rotation_atom_masking \
  --factor 2
```
- Verification step:
  ```bash
  python -c "import pyarrow.parquet as pq; n_pre = len(pq.read_table('data/processed/records.parquet')); n_aug = len(pq.read_table('data/augmented/records.parquet')); assert n_aug == 2*n_pre"
  ```
- Logs to `state/augment_check.log`.

### 6️⃣ Model Training
```bash
python code/train.py \
  --graph-dir data/augmented/graphs/ \
  --folds 5 \
  --epochs 100 \
  --seed 42
```
- Performs 5‑fold CV (source 2604.10702) or LOO if *n* < 150.  
- Early‑stops when loss change < 5 % over last 5 epochs.  
- Saves checkpoint to `code/models/model.pt` and metrics to `state/training_metrics.json`.

### 7️⃣ External Validation (≥30 records)
```bash
python code/evaluate_external.py \
  --model code/models/model.pt \
  --external-url <EXTERNAL_VALIDATION_URL> \
  --output state/external_metrics.json
```
- Computes macro‑F1 on the external set and logs the result.

### 8️⃣ Integrated Gradients Attribution
```bash
python code/attribution.py \
  --model code/models/model.pt \
  --graph-dir data/augmented/graphs/ \
  --output data/attribution/
```
- Generates node‑level IG maps and aggregated motif scores.  
- Requires ≥ 10 real hydrolysis records; otherwise logs a warning.

### 9️⃣ Null Distribution & χ² Test
```bash
python code/null_distribution.py \
  --attribution-dir data/attribution/ \
  --iterations 1000 \
  --output state/null_distribution.npy

python code/chi2_test.py \
  --null state/null_distribution.npy \
  --attribution data/attribution/ \
  --output data/reports/chi2_results.json
```

### 🔟 Sensitivity Analysis (confounding check)
```bash
python code/sensitivity.py \
  --graph-dir data/augmented/graphs/ \
  --output data/sensitivity/
```
- Reports macro‑F1 differences across three imputation strategies.

### 📊 Final Report
```bash
python code/report.py \
  --metrics state/training_metrics.json \
  --external state/external_metrics.json \
  --chi2 data/reports/chi2_results.json \
  --sensitivity data/sensitivity/summary.json \
  --output docs/reports/final_report.md
```
The markdown report includes:
- Macro‑F1 ± 95 % CI (both internal and external).  
- Power‑analysis warning (if applicable).  
- Top 3‑5 motifs with importance scores and χ² p‑values.  
- Low‑confidence flag summary (threshold 0.6).  
- Data ingestion success rate (≥ 95 %).  
- Augmentation verification summary.  
- Sensitivity‑analysis outcomes.

### 🛠️ Contract Validation (optional)
```bash
pytest tests/contract/ -q
```
Ensures all generated artifacts conform to the JSON‑Schema contracts in `contracts/`.

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| **API rate‑limit errors** | Backoff exhausted | Check `state/ingest.log`; re‑run `ingest.py`. |
| **All records flagged for missing labels** | Source truly lacks pathway info | Review `state/label_flags.json`; pipeline will abort per FR‑008. |
| **Invalid SMILES warnings** | Missing or malformed SMILES | Inspect `state/invalid_smiles.log`; records are skipped. |
| **Memory > 7 GB** | Dataset too large after augmentation | Reduce augmentation factor (`--factor 1`) or enable streaming (`--stream`). |
| **Training does not converge** | Learning rate unsuitable | Adjust `--lr` in `train.py` (default 1e‑3). |
| **χ² p‑value missing** | Null distribution file not generated | Rerun `null_distribution.py` with correct `--iterations`. |
| **Sensitivity analysis missing** | `sensitivity.py` not executed | Run step 10. |

Enjoy reproducible polymer degradation research!  

---
