# Implementation Plan: Feature Importance Drift Analysis

## Objective
Detect statistical drift in feature importance rankings of Random Forest models
trained on sequential time windows of electricity load data.

## Data Source
- **Dataset**: UCI Electricity Load Diagrams 2011-2014
- **URL**: https://archive.ics.uci.edu/ml/datasets/ElectricityLoadDiagrams20112014
- **Format**: CSV with hourly readings for 370 customers over 4 years

## Methodology
1. **Preprocessing**:
 - Handle missing values via median imputation
 - Split data into sequential 30-day windows
 - Drop zero-variance features per window
2. **Model Training**:
 - Train RandomForestRegressor (n_estimators=100, max_depth=10, seed=42)
 - Validate R² > 0.8; skip window if failed
3. **Importance Calculation**:
 - Compute permutation importance per window
 - Aggregate stability metrics
4. **Drift Analysis**:
 - Calculate Spearman rank correlation between consecutive windows
 - Apply Mann-Kendall trend test
 - Perform block permutation significance test

## Output Artifacts
- `outputs/importance_profiles.csv`: Per-window feature importance scores
- `outputs/drift_metrics.csv`: Spearman rho, p-values, trend direction
- `outputs/null_baseline.json`: Shuffled baseline statistics
- `outputs/global_stats.json`: Aggregated drift metrics

## Constraints
- CPU-only execution
- No deep learning models
- Memory usage < 4GB
