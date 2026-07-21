# Quickstart Guide: Predicting Molecular Properties from Open Babel Fingerprints

This guide walks you through setting up and running the molecular property prediction pipeline.
The project predicts logP, aqueous solubility, and boiling point using Random Forest models
trained on Open Babel fingerprints, with a baseline comparison against Crippen's additive model.

## Prerequisites

- Python 3.10 or higher
- `obabel` (Open Babel command-line tool) installed and available in your PATH
- A Unix-like environment (Linux/macOS) or WSL on Windows

## 1. Installation

Clone the repository and install dependencies:

```bash
cd projects/PROJ-324-predicting-molecular-properties-from-ope
pip install -r requirements.txt
```

Ensure `obabel` is accessible:

```bash
obabel -h
```

## 2. Data Preparation

The pipeline requires a diverse set of molecules with experimental property data.
The data is fetched from ChEMBL and/or MoleculeNet, preprocessed, and split into
training and test sets.

Run the data pipeline:

```bash
python code/setup_data_dirs.py
python code/data/download.py
python code/data/preprocess.py
```

**Output Artifacts:**
- `data/raw/dataset_metadata.json`: Metadata about the fetched data source and schema validation.
- `data/derived/data_quality_report.csv`: Log of excluded entries and missing covariates.
- `data/derived/train_set.csv`: Training set (diverse subset, ~5000 molecules).
- `data/derived/test_set.csv`: Held-out test set (stratified by logP quartiles).

## 3. Baseline Model (Crippen's Additive Model)

Compute baseline predictions using Crippen's atomic contributions on the test set.

```bash
python code/models/baseline.py
```

**Output Artifacts:**
- `data/derived/baseline_predictions.csv`: Predicted vs. experimental values.
- `data/derived/baseline_residuals.png`: Residual distribution plot.

## 4. Random Forest Model Training

Generate fingerprints, train the model with nested cross-validation, and evaluate.

```bash
python code/data/fingerprints.py
python code/models/random_forest.py
```

**Output Artifacts:**
- `data/derived/fingerprints.parquet`: Fingerprints for the training set.
- `data/derived/final_model.pkl`: Trained Random Forest model.
- `data/derived/rf_predictions.csv`: Out-of-fold predictions for statistical testing.
- `data/derived/model_comparison.png`: Comparison of Baseline vs. RF performance.

## 5. Statistical Analysis

Perform the Wilcoxon signed-rank test to compare Baseline and RF errors.

```bash
python code/analysis/stats.py
```

**Output Artifacts:**
- `data/derived/statistical_results.csv`: MAE, RMSE, and p-values.
- `data/derived/validation_protocol_summary.csv`: Summary of validation steps and data provenance.

## 6. Explainability (SHAP Analysis)

Analyze feature importance and interaction zones using SHAP.

```bash
python code/analysis/explainability.py
```

**Output Artifacts:**
- `data/derived/shap_interactions.png`: Heatmap of top interacting bit pairs.
- `data/derived/stability_analysis.csv`: Jaccard similarity across bootstrap resamples.
- `data/derived/shap_substructure_mapping.csv`: Mapping of bits to chemical substructures.
- `data/derived/conformational_limitation_report.csv`: Analysis of 2D fingerprint limitations.

## 7. Validation and Reporting

The pipeline includes explicit checks for:
- **Data Integrity**: Runtime schema checks for measurement uncertainty and quantity fields (T031).
- **Conformational Limitations**: Identification of molecules where 2D topology likely fails (T033, T045).
- **Associational Nature**: Explicit framing of findings as correlations, not causal mechanisms (T039).

Review the generated reports in `data/derived/` to understand the model's performance and limitations.

## Troubleshooting

- **obabel not found**: Ensure Open Babel is installed and in your PATH.
- **Data fetch failures**: Check network connectivity and verify the ChEMBL/MoleculeNet endpoints.
- **Memory errors**: The pipeline is optimized for 2-core runners; reduce dataset size if necessary (see `code/models/random_forest.py`).

## Next Steps

- Explore the `docs/research.md` for detailed methodology and reviewer responses.
- Extend the pipeline with additional fingerprints or models.
- Validate findings against external experimental datasets.
