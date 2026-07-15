# Quickstart: Predicting Phase Transitions in Amorphous Solids Using Machine Learning

## Prerequisites

- Python 3.11+
- LAMMPS (installed and in PATH)
- CPU cores, sufficient RAM (GitHub Actions Free Tier compatible)
- **Hard-Coded Data**: The repository includes `data/raw/literature_subset.csv` with experimental Tg and Tx values. No manual download is required.

## Installation

```bash
cd projects/PROJ-203-predicting-phase-transitions-in-amorphou/code
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Data Setup

1. **Verify Literature Subset**:
   - Ensure `data/raw/literature_subset.csv` exists in the repo.
   - The pipeline will abort if this file is missing or corrupted.

2. **Prepare Composition List**:
   - Create `data/raw/compositions.csv` with columns: `composition_id`, `formula`, `family`.
   - Include a sufficient number of compositions to fit the allocated time budget.

## Running the Pipeline

### 1. Run MD Simulations (CPU)
```bash
python -m data.run_md_sim --config config.yaml
```
- **Timeout**: 30 minutes per composition.
- **Truncation**: If timeout, keeps final steps.

The research question, method, and references remain unchanged as required.
- **Output**: `data/raw/md_trajectories/` and `data/logs/truncation_log.csv`.

### 2. Extract Descriptors
```bash
python -m data.extract_descriptors --input data/raw/md_trajectories/ --output data/processed/descriptors.csv
```

### 3. Merge and Label
```bash
python -m data.merge_labels --descriptors data/processed/descriptors.csv --experimental data/raw/literature_subset.csv --output data/processed/final_dataset.csv
```

### 4. Train Models
```bash
python -m models.train_rf --input data/processed/final_dataset.csv --output artifacts/models/
```
- **Time Limit**: [deferred] for 100 compositions.
- **Output**: `artifacts/models/regressor.pkl`, `artifacts/models/classifier.pkl`.

### 5. Evaluate & Interpret
```bash
python -m models.evaluate --model artifacts/models/regressor.pkl --data data/processed/final_dataset.csv
python -m models.interpret --model artifacts/models/regressor.pkl --data data/processed/final_dataset.csv
```
- **Output**: `artifacts/figures/shap_summary.png`, `artifacts/reports/sensitivity_report.json`, `artifacts/reports/collinearity_report.json`.

## Verification

- Check `artifacts/reports/metrics.json` for RMSE ≤ 15 K (vs. Null Model) and ROC-AUC > 0.7.
- Verify `data/logs/truncation_log.csv` for any truncated simulations.
- Ensure no synthetic data was used (check `data/raw/` checksums).