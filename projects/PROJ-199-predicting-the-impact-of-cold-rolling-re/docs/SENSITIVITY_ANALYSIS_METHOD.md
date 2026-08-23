# Sensitivity Analysis Methodology

## Objective
To quantify the impact of data sparsity and interpolation tolerance on the predictive model's performance (R²). This analysis ensures that the model's accuracy is stable across reasonable variations in data density.

## Method
The sensitivity analysis is implemented in `code/analysis/robustness.py`.

### 1. Tolerance Sweep
The analysis sweeps the interpolation tolerance parameter over a set of representative values:
- **Values**: {0.01, 0.05, 0.1}
- **Purpose**: These values represent different levels of strictness in data interpolation and neighborhood definition during model training/prediction.

### 2. Metric Calculation
For each tolerance value:
1. The model is re-trained (or re-evaluated) using the specified tolerance.
2. The R² score is calculated on a held-out test set.
3. The result is recorded.

### 3. Variance Check
- **Calculation**: The variation in R² is computed as:
 `Variation = max(R²_values) - min(R²_values)`
- **Acceptance Criteria**: The model is considered robust if `Variation ≤ 0.02`.
- **Failure**: If the variation exceeds 0.02, the model is deemed sensitive to data sparsity, and predictions in sparse regions may be unreliable.

## Output
The results are saved to `data/processed/sensitivity_analysis.csv` with the following columns:
- `tolerance`: The interpolation tolerance value used.
- `r2_score`: The resulting R² score for that tolerance.
- `variation`: The cumulative variation from the baseline (optional).

## Usage
To run the analysis:
```bash
python code/analysis/robustness.py
```
This script will:
1. Load the trained model and descriptors.
2. Iterate through the tolerance values.
3. Compute and log R² scores.
4. Write the results to `data/processed/sensitivity_analysis.csv`.
5. Print a summary indicating whether the robustness criteria (variation ≤ 0.02) was met.

## Interpretation
- **Low Variation (< 0.02)**: The model is stable and robust to minor changes in data density.
- **High Variation (> 0.02)**: The model is sensitive. Users should be cautious when interpreting predictions in regions with sparse data coverage.
- **Action**: If high variation is observed, consider collecting more data for sparse reduction levels or simplifying the model complexity.
