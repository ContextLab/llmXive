# Quick Start Guide

This guide provides a quick overview of how to use the Statistical Analysis of Chess Game Data pipeline.

## Prerequisites

- Python 3.11 or higher
- pip package manager

## Installation

1. Clone the repository:
 ```bash
 git clone <repository-url>
 cd PROJ-283-statistical-analysis-of-publicly-availab
 ```

2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Running the Pipeline

The pipeline consists of several stages:

### 1. Data Download and Verification

The data download module verifies dataset availability and checks for required metadata:

```python
from src.data.download import download_chess_data

# Download and verify data
data_path = download_chess_data(limit=1000) # Download 1000 games for testing
```

### 2. Feature Extraction

Parse PGN files and extract features:

```python
from src.data.parse import extract_features_from_pgn
from src.data.process import process_game_records

# Extract features from PGN files
games_df = extract_features_from_pgn(data_path)

# Process and calculate derived metrics
processed_df = process_game_records(games_df)
```

### 3. Model Fitting

Fit statistical models to the data:

```python
from src.models.fit import fit_gaussian_glm, fit_ridge_regression
from src.models.metrics import apply_benjamini_hochberg_fdr

# Prepare features
X, y = prepare_features_for_model(processed_df)

# Fit models
glm_results = fit_gaussian_glm(X, y)
ridge_results = fit_ridge_regression(X, y)

# Apply FDR correction
corrected_pvalues = apply_benjamini_hochberg_fdr(glm_results.pvalues)
```

### 4. Cross-Validation and Validation

Validate model stability:

```python
from src.models.validate import perform_cross_validation

# Perform 5-fold cross-validation
cv_results = perform_cross_validation(glm_results, X, y, n_folds=5)

# Check model stability (raises error if unstable)
cv_results.check_stability()
```

### 5. Generate Reports and Plots

Generate diagnostic plots and reports:

```python
from src.reports.generate_plots import generate_all_plots
from src.reports.sensitivity import run_sensitivity_analysis

# Generate plots
generate_all_plots(processed_df, glm_results, output_dir="data/results")

# Run sensitivity analysis
sensitivity_results = run_sensitivity_analysis(glm_results, output_dir="data/results")
```

## Output Files

The pipeline produces the following outputs in `data/results/`:

- `model_metrics.json`: Model coefficients, p-values, R², AIC
- `diagnostics.json`: Cross-validation results and stability metrics
- `residuals.png`: Residual plots
- `feature_importance.png`: Feature importance rankings
- `predicted_vs_actual.png`: Predicted vs. actual scatterplots
- `sensitivity_analysis.json`: Threshold sweep results

## Validation

All outputs are validated against schema definitions in `specs/contracts/`:

```python
from src.validation.validate_contracts import assert_game_records_valid, assert_model_output_valid

# Validate game records
assert_game_records_valid(processed_df)

# Validate model output
assert_model_output_valid(model_metrics_dict)
```

## Troubleshooting

### Dataset Verification Failed

If the dataset verification fails (T009), it means either:
- The dataset URL is unreachable
- More than 5% of games lack `move_time` metadata

Check the error message for details and verify your internet connection or dataset source.

### Model Instability Detected

If cross-validation detects model instability (SC-003), the standard deviation of R² across folds exceeds 0.05. Consider:
- Reducing model complexity
- Increasing sample size
- Checking for data quality issues

## Next Steps

- Explore the `code/src/` modules for detailed implementation
- Review `specs/contracts/` for data schema definitions
- Check `tests/` for comprehensive test coverage