# Quick Start Guide - SN1 Rate Constant Prediction

## Overview

This project implements an automated pipeline to predict rate constants of SN1 reactions from molecular structure using Graph Neural Networks (GNNs). The pipeline includes data ingestion, preprocessing, model training, evaluation, and interpretability analysis.

## Prerequisites

- Python 3.9+
- pip package manager
- 8GB+ RAM (for full dataset processing)
- CPU-only execution (no GPU required)

## Installation

1. Clone the repository and navigate to the project directory:
```bash
cd projects/PROJ-373-predicting-rate-constants-of-sn1-reactio
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Pipeline

The full pipeline can be run end-to-end with a single command:

```bash
python code/main.py
```

This will execute the following stages in sequence:
1. Schema validation
2. Data download from HuggingFace
3. Column mapping and cleaning
4. SMILES canonicalization and filtering
5. Descriptor computation (Gasteiger charges, topological indices)
6. Exclusion report generation
7. Dataset finalization
8. Stratified train/val/test splitting
9. MPNN model training with hyperparameter optimization
10. Model evaluation and baseline comparison
11. Artifact saving (model weights, metrics)
12. Collinearity analysis
13. Interpretability analysis (SHAP values, perturbation studies)
14. Sensitivity analysis
15. Hyperparameter sensitivity analysis
16. Consistency analysis
17. Final report generation

## Output Artifacts

After successful execution, the following artifacts will be generated:

### Data Artifacts (under `data/processed/`)
- `cleaned_sn1.csv`: Final cleaned and processed dataset
- `exclusion_report.csv`: List of excluded rows with reasons
- `success_rate.json`: Pipeline success rate metrics
- `post_filter_distribution.json`: Distribution of substrate classes after filtering
- `clean.log`: Detailed cleaning log
- `exclusion_raw.log`: Raw exclusion logs from various stages

### Model Artifacts (under `artifacts/`)
- `best_model.pt`: Saved PyTorch model weights
- `metrics.json`: Model performance metrics (R², MAE)
- `hyperparameter_search.csv`: Hyperparameter search results
- `collinearity_report.json`: VIF analysis results
- `sensitivity_report.csv`: Sensitivity analysis results
- `perturbation_results.csv`: Perturbation study results
- `shap_consistency_report.md`: SHAP consistency analysis
- `final_report.md`: Comprehensive final report
- `feasibility_test_log.json`: Execution timing and status

### Logs (under `artifacts/logs/`)
- Pipeline execution logs with timestamps

## Validation

To validate the quickstart guide and ensure all artifacts are generated correctly:

```bash
python code/validation/validate_quickstart.py
```

## Troubleshooting

### Common Issues

1. **Missing dependencies**: Ensure all packages from `requirements.txt` are installed.
2. **Memory errors**: The full dataset may require significant RAM. Consider running on a subset if memory is limited.
3. **Network errors**: Data download requires internet access. Check your connection if downloads fail.
4. **Schema validation failures**: Ensure the input data matches the expected schema defined in `specs/`.

### Getting Help

If you encounter issues not covered here, check the pipeline logs in `artifacts/logs/` for detailed error messages.

## Next Steps

After running the pipeline:
1. Review the `artifacts/final_report.md` for comprehensive results
2. Examine the model performance in `artifacts/metrics.json`
3. Analyze feature importance from the SHAP analysis results
4. Use the trained model for predictions on new molecules (extend the code as needed)