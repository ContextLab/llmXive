# Quickstart: Predicting Polymer Degradation Pathways with Graph Neural Networks

## Prerequisites
- **Python 3.11** (or newer)  
- **GitHub Actions free‑tier** (2 CPU cores, ~7 GB RAM) – the steps below have been verified on this environment.  
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
# Create required directory tree and timestamped setup log (T001a/T001b)
mkdir -p code data/raw data/processed data/augmented data/external data/reports data/output tests state/projects
ls -R > state/setup_log.txt && date >> state/setup_log.txt

# Lint check (should exit 0) – satisfies FR‑014 (T003a/T003b)
ruff check code/ > state/ruff_check.log
echo $?  # should output 0

# Run pytest with deterministic seed (satisfies FR‑015, T008c)
pytest -q
# Logs written to state/pytest.log
```

### 1️⃣ Data Download & Initial Validation  
> **NOTE:** The open **Polymer Genome** dataset is used as the primary source; it contains polymer SMILES, temperature, pH, UV exposure, and curated degradation pathway labels.
```bash
python code/ingest.py \
  --polymer-genome-url https://huggingface.co/datasets/PolymerGenome/polymer_degradation/resolve/main/data.parquet \
  --materials-url https://materialsproject.org/rest/v2/materials \
  --output data/raw/combined.parquet
```
- Implements exponential backoff (max 3 retries).  
- Logs to `state/ingest.log` and `state/ingest_error.log`.

### 2️⃣ Label Scan, Synthetic Labeling & Frequency Check
```bash
python code/label_validation.py \
  --input data/raw/combined.parquet \
  --output data/processed/records.parquet
```
- Generates synthetic labels **only for augmentation**; validates class frequencies (≤ 10 % deviation), flags records, and aborts if all labels are synthetic (FR‑008).

### 3️⃣ SMILES Handling (no synthetic SMILES generation)
```bash
python code/preprocess.py \
  --input data/processed/records.parquet \
  --graph-dir data/processed/graphs/
```
- Skips any record with an invalid SMILES; logs SMILES to `state/invalid_smiles.log`.  
- Filters for polyesters using SMARTS `C(=O)O` and outputs boolean `is_polyester`.

### 4️⃣ Power‑Analysis & Minimum Sample‑Size Check
```bash
python code/power_analysis.py \
  --records data/processed/records.parquet \
  --output state/power_analysis.json
# If n < 150 the script aborts with a clear under‑powered warning.
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
- Logs to `state/augment_check.log` and writes metadata to `state/augmentation_metadata.json`.

### 6️⃣ External Validation Set Creation (mandatory)
```bash
python code/create_external_validation.py \
  --input data/processed/records.parquet \
  --output data/external/validation.parquet \
  --min-curated 30
```
- Ensures the set is de‑duplicated against the training data; aborts if < 30 curated records.

### 7️⃣ Model Training
```bash
python code/train.py \
  --graph-dir data/augmented/graphs/ \
  --folds 5 \
  --epochs 100 \
  --seed 42
```
- Performs 5‑fold CV (source 2604.10702) **or aborts** if the power‑analysis cutoff triggered.  
- Early‑stops when loss change < 5 % over the last 5 epochs.  
- Saves checkpoint to `code/models/model.pt` and metrics to `state/training_metrics.json`.

### 8️⃣ External Validation Evaluation
```bash
python code/evaluate_external.py \
  --model code/models/model.pt \
  --external data/external/validation.parquet \
  --output state/external_metrics.json
```
- Computes macro‑F1 on the external set and logs the result.

### 9️⃣ Integrated Gradients Attribution
```bash
python code/attribution.py \
  --model code/models/model.pt \
  --graph-dir data/augmented/graphs/ \
  --output data/attribution/
```
- Generates node‑level IG maps and aggregated motif scores.  
- Requires ≥ 10 **curated** hydrolysis records in the external validation set; otherwise logs a warning.

### 🔟 McNemar’s Test for Significance
```bash
python code/mcnemar_test.py \
  --predictions data/attribution/predictions.parquet \
  --labels data/external/validation.parquet \
  --output state/mcnemar_results.json
```
- Reports McNemar’s χ² statistic and p‑value (α = 0.05).

### 1️⃣1️⃣ Permutation Test for Motif Significance
```bash
python code/null_distribution.py \
  --attribution-dir data/attribution/ \
  --iterations 1000 \
  --output state/null_distribution.npy

python code/permutation_test.py \
  --null state/null_distribution.npy \
  --attribution data/attribution/ \
  --output data/reports/perm_test_results.json
```

### 1️⃣2️⃣ Expanded Confounding Assessment
```bash
python code/confounding_assessment.py \
  --attribution-dir data/attribution/ \
  --output state/confounding_report.json
```
- Checks whether IG importance scores are driven by imputed `temp_c`/`ph`/`uv_exposure` **or** polymer size, degree distribution, aromatic ring count; any significant association (p < 0.05) is reported.

### 1️⃣3️⃣ Ablation Study (No Synthetic Labels)
```bash
python code/ablation.py \
  --graph-dir data/processed/graphs/ \
  --external data/external/validation.parquet \
  --output state/ablation_results.json
```
- Trains the GNN **without** any synthetically labeled records and evaluates macro‑F1 difference relative to the full‑training run.

### 1️⃣4️⃣ Visualization of Top Pathways
```bash
python code/visualization.py \
  --motif-importance data/output/model_output.json \
  --output data/reports/visualizations/top5_pathways.png
```
- Saves a NetworkX PNG of the top 5 degradation pathways with associated motifs.

### 1️⃣5️⃣ Final Report
```bash
python code/report.py \
  --metrics state/training_metrics.json \
  --external state/external_metrics.json \
  --mcnemar state/mcnemar_results.json \
  --perm_test data/reports/perm_test_results.json \
  --confounding state/confounding_report.json \
  --ablation state/ablation_results.json \
  --output docs/reports/final_report.md
```
The markdown report includes:
- Macro‑F1 ± 95 % CI (internal & external).  
- Power‑analysis warning (if *n* < 150).  
- McNemar’s statistic and p‑value.  
- Top 3‑5 motifs with importance scores and permutation‑test p‑values.  
- Low‑confidence flag summary (threshold 0.6).  
- Data ingestion success rate (≥ 95 %).  
- Augmentation verification, confounding assessment, and ablation‑study outcome.  

### 🛠️ Contract Validation (optional)
```bash
pytest tests/contract/ -q
```
Ensures all generated artifacts conform to the JSON‑Schema contracts in `contracts/`.

### Reference‑Validator Execution
```bash
python -m llmxive.reference_validator \
  --files plan.md research.md quickstart.md \
  --log state/reference_validator.log
```
Runs the Reference‑Validator on all citation‑containing files to satisfy Constitution II.

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| **API rate‑limit errors** | Backoff exhausted | Check `state/ingest.log`; re‑run `ingest.py`. |
| **All records flagged for missing labels** | Source truly lacks pathway info | Review `state/label_flags.json`; pipeline will abort per FR‑008. |
| **Invalid SMILES warnings** | Missing or malformed SMILES | Inspect `state/invalid_smiles.log`; records are skipped. |
| **Memory > 7 GB** | Dataset too large after augmentation | Reduce augmentation factor (`--factor 1`) or enable streaming (`--stream`). |
| **Training does not converge** | Learning rate unsuitable | Adjust `--lr` in `train.py` (default 1e‑3). |
| **Permutation test results missing** | Null distribution not generated | Rerun `null_distribution.py` with correct `--iterations`. |
| **Confounding assessment warning** | Imputed variable correlated with IG | Review `state/confounding_report.json` and consider alternative imputation. |

Enjoy reproducible polymer degradation research!  

---


