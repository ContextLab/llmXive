# Quickstart: Predicting Rate Constants of SN1 Reactions from Molecular Structure

## Prerequisites

- Python 3.10+
- pip
- 2 CPU cores, ~7 GB RAM, ~14 GB disk
- Internet access (for HuggingFace datasets)

## Installation

```bash
cd projects/PROJ-373-predicting-rate-constants-of-sn1-reactio/code/
pip install -r requirements.txt
```

## Running the Pipeline

```bash
python main.py
```

This will:
1. Download and validate datasets from HuggingFace.
2. Compute descriptors and clean data.
3. Train MPNN with Nested CV (scaffold splitting).
4. Evaluate against baselines.
5. Generate interpretability reports (SHAP, sensitivity, perturbation, VIF).
6. Check SC-001 success criteria.

## Output Artifacts

- `data/processed/cleaned.csv`: Cleaned dataset.
- `data/processed/descriptors.csv`: Molecular descriptors.
- `data/processed/split_train.csv`, `split_val.csv`, `split_test.csv`: Stratified splits.
- `artifacts/model.pt`: Trained MPNN weights.
- `artifacts/metrics.json`: R², MAE, and comparison results.
- `artifacts/final_report.md`: Comprehensive report with all metrics and limitations.
- `artifacts/shap_report.md`, `sensitivity_report.md`, `perturbation_report.md`, `vif_report.json`, `shap_consistency_report.md`: Interpretability outputs.

## Troubleshooting

- **Missing Metadata**: If the dataset lacks temperature, solvent, or substrate class, the script will exit with a fatal error.
- **SMILES Parsing Errors**: Check `exclusion_log.csv` for rows excluded due to parsing issues.
- **Memory Issues**: If RAM is exceeded, the script automatically reduces inner CV folds or config count to fit the 6h budget.