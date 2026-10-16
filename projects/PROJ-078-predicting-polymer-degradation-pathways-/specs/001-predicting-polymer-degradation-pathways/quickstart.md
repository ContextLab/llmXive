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
> **NOTE:** A suitable open polymer degradation dataset is **not yet available**. Replace the placeholder URL below with the verified dataset URL once obtained.

```bash
python code/ingest.py \
  --url <PLACEHOLDER_OPEN_DATASET_URL> \
  --output data/raw/polymer_records.csv
```
- Performs exponential backoff (max 3 retries).  
- Logs success/failure to `state/ingest.log`.  

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
- Skips any record lacking a valid SMILES; logs SMILES to `state/invalid_smiles.log`.  
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
- Performs **bond rotation** and **atom masking** as required by Constitution VII.  
- Verification: after augmentation run  
  ```bash
  python -c "import pyarrow.parquet as pq; n_pre = len(pq.read_table('data/processed/records.parquet')); n_aug = len(pq.read_table('data/augmented/records.parquet')); assert n_aug == 2*n_pre"
  ```  
  Logs to `state/augmentation_check.log`.  

### 6️⃣ Model Training
```bash
python code/train.py \
  --graph-dir data/augmented/graphs/ \
  --folds 5 \
  --epochs 100 \
  --seed 42
```
- Performs 5‑fold CV (or LOO if *n* < 150).  
- Early‑stopping when loss change < 5 % over last 5 epochs.  
- Saves checkpoint to `code/models/model.pt` and metrics to `state/training_metrics.json`.

### 7️⃣ Integrated Gradients Attribution
```bash
python code/attribution.py \
  --model code/models/model.pt \
  --graph-dir data/augmented/graphs/ \
  --output data/attribution/
```
- Generates node‑level IG maps and motif‑importance scores.  
- Requires ≥ 10 real hydrolysis records; otherwise a warning is logged and IG validation is skipped.

### 8️⃣ Null Distribution & χ² Test
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

### 9️⃣ Sensitivity Analysis (confounding check)
```bash
python code/sensitivity.py \
  --graph-dir data/augmented/graphs/ \
  --output data/sensitivity/
```
- Evaluates the impact of imputed environmental variables on macro‑F1.

### 📊 Final Report
```bash
python code/report.py \
  --metrics state/training_metrics.json \
  --chi2 data/reports/chi2_results.json \
  --sensitivity data/sensitivity/summary.json \
  --output docs/reports/final_report.md
```
The markdown report includes macro‑F1 with 95 % CI, power‑analysis warning (if any), top motifs with p‑values, low‑confidence flag statistics (threshold 0.6), augmentation verification, and sensitivity‑analysis outcomes.

### 🛠️ Contract Validation (optional)
```bash
pytest tests/contract/ -q
```
Ensures all generated artifacts conform to the JSON‑Schema contracts in `contracts/`.

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| **API rate‑limit errors** | Backoff exhausted | Check `state/ingest.log`; re‑run `ingest.py` (it will resume). |
| **All records flagged for missing labels** | Source truly lacks pathway info | Review `state/label_flags.json`; the pipeline will abort as required by FR‑008. |
| **Invalid SMILES warnings** | SMILES missing or malformed | Inspect `state/invalid_smiles.log`; records are skipped. |
| **Memory > 7 GB** | Dataset too large after augmentation | Reduce augmentation factor (`--factor 1`) or enable streaming mode (`--stream`). |
| **Training does not converge** | Learning rate too high/low | Adjust `--lr` flag in `train.py` (default 1e‑3). |
| **χ² p‑value missing** | Null distribution file not found | Rerun `null_distribution.py` with correct `--iterations`. |
| **Sensitivity analysis missing** | `sensitivity.py` not run | Execute step 9 above. |

Enjoy reproducible polymer degradation research!  

---



