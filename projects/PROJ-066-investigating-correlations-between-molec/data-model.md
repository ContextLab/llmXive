# Data Model

## Raw Data
- Source: ChEMBL 33 (SQLite)
- Format: `.db`
- Key Tables: `molecule_dictionary`, `activities`, `assays`

## Processed Data
- Format: CSV
- Columns: `smiles`, `experimental_value`, `target_name`, `mw`, `logp`, `tpsa`, `hbd`, `hba`, `rotatable_bonds`, `ring_count`

## Model Artifacts
- `model_lr.pkl`: Pickled Linear Regression model.
- `model_rf.pkl`: Pickled Random Forest model.
- `feature_importance.json`: JSON report of feature importances.

## Metrics
- `metrics_summary.json`: Contains RMSE, Pearson r, and baseline comparisons.
