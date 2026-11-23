# Sensitivity Analysis Methodology

This document describes the sensitivity analysis performed to ensure the robustness of the predictive models against variations in interpolation tolerance.

## Objective
To quantify the stability of the model's performance metrics ($R^2$ and RMSE) when the interpolation tolerance parameter is varied. A robust model should exhibit minimal variation in performance across reasonable tolerance settings.

## Methodology

### 1. Parameter Definition
The interpolation tolerance parameter controls the sensitivity of the model's interpolation logic (used in cross-validation and extrapolation checks).
- **Swept Values**: The tolerance is swept over the set: $\{0.01, 0.05, 0.1\}$.
- **Rationale**: These values represent a range from strict (0.01) to lenient (0.1) interpolation criteria, covering typical operational ranges for texture data.

### 2. Execution Flow
1. **Model Loading**: The trained model (Polynomial or Gaussian Process) is loaded from `data/processed/models/`.
2. **Cross-Validation Loop**: For each tolerance value $t \in \{0.01, 0.05, 0.1\}$:
 - The `code/analysis/robustness.py` module executes a k-fold cross-validation.
 - The interpolation tolerance $t$ is applied during the validation step.
 - The $R^2$ and RMSE are calculated for the held-out folds.
3. **Aggregation**: The mean $R^2$ and RMSE for each tolerance are recorded.

### 3. Stability Criteria
- **Acceptance**: The model is considered robust if the variation in $R^2$ across the swept tolerances is $\le 0.02$.
- **Failure**: If the variation exceeds 0.02, the model is flagged as sensitive to interpolation settings, indicating potential instability in the prediction logic.

### 4. Output Artifacts
The results are written to `data/processed/sensitivity_analysis.csv` with the following columns:
- `tolerance`: The interpolation tolerance value used.
- `r_squared`: The coefficient of determination ($R^2$) for this run.
- `rmse`: The root mean squared error.
- `status`: "PASS" if the variation criteria is met, "FAIL" otherwise.

## Interpretation
- **Low Variation**: Indicates that the model's predictions are stable and not overly dependent on the specific interpolation threshold. This increases confidence in the model's generalizability.
- **High Variation**: Suggests that the model's performance is highly sensitive to the interpolation logic. This may indicate overfitting to specific data points or a need to refine the interpolation algorithm.

## Relation to SC-001
This analysis supports the testability requirement (SC-001) by providing a quantitative measure of model stability. The "total available" baseline for testing is calculated based on the actual data found, and the sensitivity analysis ensures that the model's performance is consistent regardless of minor parameter tuning within the defined range.

## Implementation Details
The analysis is implemented in `code/analysis/robustness.py` via the `run_sensitivity_analysis` function.
- **Input**: Path to the trained model and the processed descriptor dataset.
- **Output**: `data/processed/sensitivity_analysis.csv`.
- **Dependencies**: `scikit-learn`, `pandas`, `numpy`.

## Future Improvements
- Expand the swept tolerance range to include more granular values (e.g., 0.001, 0.005).
- Perform sensitivity analysis on other hyperparameters (e.g., polynomial degree, kernel bandwidth).
- Visualize the $R^2$ variation as a line plot to identify trends.
