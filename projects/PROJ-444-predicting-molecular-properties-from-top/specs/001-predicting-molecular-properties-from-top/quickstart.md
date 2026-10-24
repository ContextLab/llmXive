# Quickstart: Predicting Molecular Properties from Topological Data Analysis

## Prerequisites
- Python 3.11+
- `git`
- Linux environment (local machine or GitHub Actions runner)

## Installation

```bash
# 1. Clone the repository
git clone <repo-url>
cd projects/PROJ-444-predicting-molecular-properties-from-top

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install exact dependencies (CPU wheels only)
pip install -r code/requirements.txt
```

## Data Preparation

```bash
# Stream the PubChem dataset, shuffle, randomly sample a large set of valid molecules,
# extract SMILES & logP, and write the validated CSV
python code/01_download_pubchem.py \
    --source huggingface \
    --dataset sagawa/pubchem-10m-canonicalized \
    --max-molecules 5000 \
    --seed 42 \
    --sample-mode random   # ensures shuffling + unbiased sampling
```

- **Note**: The script shuffles the record order with a **fixed seed (= 42)** before sampling, ensuring an unbiased random sample rather than simply taking the first N records.
- The script streams the Hugging Face dataset, shuffles the stream using the fixed seed, keeps only rows where `canonical_smiles` and `XLogP3` are present, renames them to `smiles` and `logP`, validates each SMILES with RDKit, and writes `data/processed/molecules.csv`.  
- Invalid SMILES are logged in `data/processed/exclusions.csv` (idempotent).  
- A SHA‑256 checksum file `data/checksums.txt` is updated; you can verify it with:

```bash
python code/00_checksum_verify.py
```

- **Contract validation**: Immediately after download, run the pytest contract test to ensure `molecules.csv` conforms to `contracts/dataset.schema.yaml`:

```bash
pytest tests/contract/test_dataset_schema.py
```

## Full Pipeline

```bash
# 1. Compute topological descriptors (baseline square grid of moderate resolution)
python code/02_tda_computation.py --grid 10

# Contract validation for persistence images:
pytest tests/contract/test_feature_matrix_schema.py --grid 10

# 2. Compute traditional RDKit descriptors and merge with topological features
python code/03_feature_engineering.py

# 3. Train and evaluate models (multiple repeats of 10‑fold scaffold CV)
python code/04_model_training.py

# 4. Extract feature importance (outputs conform to model_metrics.schema.yaml)
python code/07_feature_importance.py

# 5. Run statistical diagnostics (Bonferroni, VIF for Linear Regression, MI)
python code/06_diagnostics.py

# 6. Sensitivity sweep over grid resolutions (assert σ < 0.02)
python code/05_sensitivity_analysis.py --grids 10 20 30

# 7. Record resource usage for SC‑004
python code/08_resource_monitor.py
```

All artifacts are written under `reports/`:

- `metrics/model_metrics.json`
- `metrics/feature_importance.json`
- `diagnostics/vif_report.json`
- `diagnostics/mi_report.json`
- `diagnostics/sensitivity_report.json`
- `metrics/resource_usage.json`

## Verification

```bash
# Contract tests (schema validation)
pytest tests/contract/

# Unit tests for core utilities
pytest tests/unit/
```

Re‑running the pipeline yields identical results (within floating‑point tolerance) because:

- Random seeds are fixed (`random.seed(42)`, `np.random.seed(42)`).  
- The dataset is streamed from a single, immutable Hugging Face source.  
- All `molecule_id` fields are stored as strings before any merge.  
- Checksums guarantee data integrity across runs.

---
