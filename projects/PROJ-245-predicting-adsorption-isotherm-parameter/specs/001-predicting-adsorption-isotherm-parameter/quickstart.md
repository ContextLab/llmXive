# Quickstart: Predicting Adsorption Isotherm Parameters from Molecular Features

## Prerequisites

*   Python 3.11+
*   GitHub repository cloned locally
*   Virtual environment created and activated (`python -m venv .venv; source .venv/bin/activate`)

## Installation

```bash
pip install -r requirements.txt
```

## Data Download & Preparation

The pipeline automatically downloads and preprocesses the NIST dataset:

```bash
python src/main.py --data-dir data/raw --task curate_data
```

This command will download the dataset, filter for Type I isotherms, calculate molecular descriptors using RDKit, fit Langmuir/Henry parameters, and output a cleaned CSV file to `data/processed`.

## Model Training & Evaluation

Train and evaluate machine learning models:

```bash
python src/main.py --data-dir data/processed --task train_model --target langmuir_capacity
```

Replace `langmuir_capacity` with the desired target parameter (e.g., `henry_constant`). This command will perform 5-fold cross-validation, train a reduced model with top 3 features, and report performance metrics on a held-out test set.

## SHAP Analysis & Interpretation

Generate SHAP plots to identify key drivers of adsorption behavior:

```bash
python src/main.py --data-dir data/processed --model trained_models/best_model.pkl --task shap_analysis
```

Replace `trained_models/best_model.pkl` with the path to your trained model file. This command will generate SHAP summary plots, partial dependence plots, and perform cluster-aware permutation testing.

## Output Files

*   `data/processed/cleaned_dataset.csv`: Cleaned and preprocessed dataset
*   `trained_models/best_model.pkl`: Trained machine learning model
*   `data/benchmarks/runtime_log.json`: Runtime benchmark log (FR-009)
*   `shap_plots/summary_plot.png`: SHAP summary plot
*   `shap_plots/partial_dependence_plot.png`: Partial dependence plot
*   `reports/feature_importance_report.json`: **Contains adjusted p-values (q-values)** for top features (SC-005)

## Troubleshooting

*   **Missing dependencies**: Ensure all required packages are installed using `pip install -r requirements.txt`.
*   **Data download errors**: Check your internet connection and verify the dataset URLs in the configuration file.
*   **Memory issues**: The pipeline will automatically sample the data if memory limits are exceeded. No external GPU services are used.