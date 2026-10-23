# Quickstart: Predicting Molecular Properties from Topological Data Analysis

## Prerequisites
- Python 3.11+
- `git`
- Access to a Linux environment (GitHub Actions runner or local machine)

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
# Download the Lipophilicity dataset from the official MoleculeNet repository
# (no direct verified URL; obtain the CSV manually or via the MoleculeNet API)
python code/01_data_ingestion.py --source lipophilicity
```

- The script downloads from the official MoleculeNet source **only** (no alternative sources).  
- Writes `data/raw/lipophilicity.csv`, computes cryptographic checksums (`data/checksums.txt`).  
- Validates that `smiles` and `logP` columns exist (renaming if necessary).  
- Logs any invalid SMILES using idempotent append logic (no duplicates).  
- Aborts with **Data Gap** error if required columns are missing.

## Running the Full Pipeline

```bash
# 0. Verify checksums (optional but required for SC‑004)
python code/00_checksum_verify.py

# 1. Compute topological descriptors (baseline 10×10 grid)
# Output includes target_property and target_value fields per feature_matrix.schema.yaml
python code/02_tda_computation.py --grid 10

# 2. Compute traditional descriptors and merge
# molecule_id is cast to string before merge; target column is dropped before training
python code/03_feature_engineering.py

# 3. Train and evaluate models (5‑fold scaffold CV)
python code/04_model_training.py

# 4. Extract feature importance for traditional and topological descriptors
# Output conforms to model_metrics.schema.yaml
python code/06_feature_importance.py

# 5. Run statistical diagnostics (Bonferroni, VIF for Linear Regression only, MI)
python code/06_diagnostics.py

# 6. Sensitivity sweep over grid resolutions
python code/05_sensitivity_analysis.py --grids 10 20 30

# 7. Record resource usage for SC‑004
python code/07_resource_monitor.py
```

All outputs are written under `reports/`:
- `metrics/model_metrics.json`
- `metrics/feature_importance.json`
- `diagnostics/vif_report.json` (Linear Regression only)
- `diagnostics/mi_report.json`
- `diagnostics/sensitivity_report.json`
- `metrics/resource_usage.json`

## Verification

```bash
# Contract tests ensure schemas are respected
pytest tests/contract/

# Unit tests for core utilities
pytest tests/unit/
```

Re‑running the pipeline should produce identical numeric results (within floating‑point tolerance) because:
- Seeds are fixed (`random.seed(42)`, `np.random.seed(42)`, `torch.manual_seed(42)` where applicable).
- Dataset is obtained from a single, consistent source (official MoleculeNet repository).
- All molecule_id fields are cast to string consistently.
- Checksums prevent re-processing of unchanged data.

---

