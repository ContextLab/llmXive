# Quickstart: Predicting Avian Migration Patterns

## Prerequisites
- **Python** ≥ 3.11
- **Git** (any recent version)
- **Disk space**: ≥ 10 GB (raw downloads)
- **RAM**: ≥ 7 GB (pipeline uses streaming; 8 GB recommended)
- **NASA Earthdata token**: *Not required* – MODIS data are obtained from the **verified** HuggingFace NPZ (see Dataset Strategy).

## Installation

```bash
# 1. Clone the repository
git clone <REPO_URL>
cd projects/PROJ-126-predicting-avian-migration-patterns-from

# 2. Create and **activate** a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install **pinned** dependencies
pip install -r code/requirements.txt
```

## Data Setup (automated)

```bash
# Run the data loader (downloads eBird, MODIS, and GHCN)
./code/run_pipeline.sh --stage data_loader
```

The script will:
1. Stream the eBird Basic Dataset, filter complete checklists, and write `data/raw/ebd_subset.csv`.
2. Download the MODIS weekly raster archive and the GHCN daily temperature dataset.
3. Verify checksums and validate the raw eBird CSV against the `contracts/dataset.schema.yaml` contract.
4. Produce a provenance log entry.

## Full Pipeline Execution

```bash
# Execute the entire workflow (data preparation, modeling, evaluation, visualization)
./code/run_pipeline.sh
```

The pipeline will:
- Build the spatiotemporal grid and compute lagged environmental predictors.
- Derive the primary “first‑arrival” week using the **raw** cumulative‑count threshold (3, 5, 10) and record the `threshold_used` column.
- Train XGBoost models (primary environmental, secondary bias‑adjusted) and apply a Gaussian Process correction.
- Perform spatial block bootstrap testing, HAC‑corrected Diebold‑Mariano testing (supplemental), SHAP, permutation importance, and threshold sensitivity analyses.
- Generate continental‑scale PNG maps (`migration_map.png`, `predictor_gradient.png`).
- Validate all outputs against the JSON‑Schema contracts in `contracts/`.
- Log runtime and memory usage; CI will enforce the ≤ 6 h / ≤ 7 GB limits.

## Expected Outputs (saved under `data/outputs/`)

- `first_arrival_sweep.csv` (processed dataset with `threshold_used` and `effort_covariate`)
- `predictions.csv` (final forecasts with GP correction)
- `metrics.json` (model performance, statistical tests, feasibility diagnostics)
- `shap_summary.png`, `shap_interaction.png`
- `migration_map.png`, `predictor_gradient.png`
- `provenance.log` (traceability manifest)

All files are version‑hashed and will be recorded in `state/...yaml` for reproducibility.
