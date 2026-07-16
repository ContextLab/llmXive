# User Guide

This guide provides practical information for users of the grain boundary diffusivity project.

## Understanding the Pipeline

The pipeline transforms raw crystal structure data into a trained machine learning model that predicts atomic diffusivity based on grain boundary characteristics.

### Input Data Sources

The pipeline fetches data from:
- **Materials Project**: Database of computed materials properties
- **OpenKIM**: Open Knowledgebase of Interatomic Models
- **NIST**: National Institute of Standards and Technology databases

Search criteria include:
- Keywords: "grain boundary", "bicrystal"
- Properties: "diffusivity"

### Feature Engineering

The pipeline extracts the following features from crystal structures:

1. **Geometric Features**
 - Misorientation angle (degrees)
 - Σ value (Coincidence Site Lattice)
 - Boundary plane normal (Miller indices)
 - Rodrigues vector (rotation representation)
 - Boundary width (Å)
 - Excess volume (Å³/atom)

2. **Environmental Features**
 - Temperature (K)
 - Composition (chemical formula)

3. **Metadata Features**
 - Simulation method (DFT, MD, KMC)
 - Potential ID (interatomic potential identifier)

### Model Architecture

The project uses **XGBoost** (Extreme Gradient Boosting) for prediction:
- Gradient-boosted decision trees
- Handles non-linear relationships
- Robust to outliers
- Provides feature importance via SHAP

Hyperparameter tuning is performed using:
- RandomizedSearchCV with 5-fold cross-validation
- Search space: max_depth [3, 10], learning_rate [0.01, 0.3], n_estimators [50, 300]
- Optimization metric: R²

## Running the Pipeline

### Quick Start

```bash
# 1. Setup
python code/setup_env.py

# 2. Run full pipeline
python code/download.py
python code/geometry_parser.py
python code/preprocess.py
python code/train.py
python code/validate.py
python code/interpret.py
```

### Customizing the Pipeline

#### Changing Data Sources

Edit `code/download.py` to modify search parameters:

```python
fetch_materials_project_data(
 keywords=["grain boundary", "interface"], # Custom keywords
 properties=["diffusivity", "mobility"] # Additional properties
)
```

#### Adjusting Model Parameters

Edit `code/train.py` to change hyperparameter search space:

```python
param_dist = {
 'max_depth': [5, 15], # Custom range
 'learning_rate': [0.05, 0.2], # Custom range
 'n_estimators': [100, 500] # Custom range
}
```

#### Modifying Validation Thresholds

Edit `code/config/threshold_config.py` to change R² threshold:

```python
R2_THRESHOLD = 0.75 # Custom threshold
```

## Interpreting Results

### Training Metrics

The `artifacts/reports/training_metrics.json` file contains:
- **R²**: Coefficient of determination (target: > 0.7)
- **RMSE**: Root Mean Square Error
- **MAPE**: Mean Absolute Percentage Error

### Validation Report

The `artifacts/reports/validation_report.json` includes:
- Cross-validation metrics (mean and std)
- Bias test results (intercept, slope, p-values)
- Bias assessment conclusion

**Acceptance Criteria:**
- R² std ≤ 0.05 (indicates stable model)
- Bias test p-values > 0.017 (Bonferroni-corrected)

### SHAP Analysis

The SHAP summary plot (`artifacts/figures/shap_summary.png`) shows:
- Feature importance (vertical axis)
- Impact on prediction (color: red=high, blue=low)
- Distribution of SHAP values

### Threshold Sensitivity

The `artifacts/reports/threshold-variation-table.csv` shows:
- How many folds pass each R² threshold
- Helps assess model robustness

## Common Use Cases

### Case 1: Adding New Materials

1. Update search keywords in `code/download.py`
2. Re-run the download step
3. Re-run the entire pipeline

### Case 2: Testing Different Models

1. Modify `code/train.py` to use a different estimator
2. Adjust hyperparameter search space accordingly
3. Re-run training and validation

### Case 3: Investigating Specific Grain Boundaries

1. Filter the cleaned dataset:
 ```python
 import pandas as pd
 df = pd.read_parquet("data/processed/cleaned_dataset.parquet")
 subset = df[df['material_id'] == 'mp-12345']
 ```
2. Use the model to make predictions on the subset

## Best Practices

### Data Quality

- Always verify API keys before running downloads
- Check the collinearity diagnostic before training
- Review the validation report for bias issues

### Model Performance

- Target R² > 0.7 for reliable predictions
- Monitor R² std across folds (should be ≤ 0.05)
- Use SHAP to understand feature contributions

### Reproducibility

- Set random seeds (handled automatically by the pipeline)
- Record metadata with each run
- Version control your code and configuration

## Troubleshooting

### Low R² Score

Possible causes:
- Insufficient data (check record count)
- High collinearity (check MI diagnostic)
- Inappropriate features (review SHAP analysis)

Solutions:
- Increase data volume
- Remove redundant features
- Try different feature engineering

### High Bias in Predictions

Possible causes:
- Model underfitting
- Data distribution shift

Solutions:
- Increase model complexity (max_depth, n_estimators)
- Check data preprocessing
- Verify target distribution

### Memory Errors

Solutions:
- Close other applications
- Use a machine with more RAM
- Process data in chunks (if supported)

## Performance Considerations

### Runtime

Expected runtime on 2 CPU cores:
- Download: 30-60 minutes (depends on API limits)
- Parsing: 10-20 minutes
- Preprocessing: 5 minutes
- Training: 30-60 minutes
- Validation: 10-15 minutes
- Interpretation: 5-10 minutes

**Total: ~1.5-3 hours**

### Memory Usage

Peak memory usage: ~7 GB
- Ensure sufficient swap space
- Monitor with `htop` or similar tools

## Support

For issues or questions:
1. Check the [Troubleshooting](#troubleshooting) section
2. Review the [API Reference](api_reference.md)
3. Examine error logs in `project.log`
4. Check GitHub issues for known problems
