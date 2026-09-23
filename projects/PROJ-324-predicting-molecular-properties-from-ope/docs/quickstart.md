# Quickstart Guide: Predicting Molecular Properties from Open Babel Fingerprints

This guide provides the exact commands to run the full pipeline for predicting molecular properties (LogP, Solubility, Boiling Point) using Random Forests and Open Babel fingerprints.

## Prerequisites

1. Ensure you are in the project root: `projects/PROJ-324-predicting-molecular-properties-from-ope/`
2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```
3. Ensure `obabel` (Open Babel) is installed and available in your PATH.

## Execution Order

The pipeline must be run in the following order to ensure data integrity and prevent data leakage.

### 1. Data Download & Preprocessing
Fetch real data from PubChem and filter for high-confidence measurements.
```bash
python code/data/download.py
python code/data/preprocess.py
```

### 2. Baseline Prediction (Crippen's Model)
Compute additive baseline predictions on the full dataset.
```bash
python code/models/baseline.py
```

### 3. Fingerprint Generation
Generate Open Babel fingerprints (ECFP4, MACCS, FP2) for the training set.
```bash
python code/data/fingerprint.py
```

### 4. Random Forest Training & Evaluation
Train the Random Forest model using nested cross-validation and evaluate on the held-out test set.
**This step produces `data/derived/final_model.pkl`, `data/derived/rf_test_predictions.csv`, and `data/derived/model_comparison.png`.**
```bash
python code/models/rf.py
```

### 5. Statistical Analysis & Reporting
Perform statistical tests (Wilcoxon) and generate final comparison plots.
```bash
python code/analysis/stats.py
```

### 6. Explainability & Interaction Mapping
Generate SHAP interaction heatmaps and map bits to chemical substructures.
```bash
python code/analysis/explainability.py
```

## Expected Outputs

After successful completion, the following artifacts will be generated in the `data/derived/` directory:
- `data_quality_report.csv`
- `train_set.csv`, `test_set.csv`
- `baseline_test_predictions.csv`
- `rf_test_predictions.csv`
- `final_model.pkl`
- `baseline_residuals.png`
- `model_comparison.png`
- `shap_interactions.png`
- `interaction_zone_map.md`