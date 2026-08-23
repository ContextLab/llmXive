# Sensitivity Analysis Methodology

## Purpose

This document describes the sensitivity analysis methodology implemented in `code/analysis/robustness.py` to quantify model stability under data sparsity and varying interpolation tolerances.

## Background

Machine learning models trained on texture evolution data may exhibit sensitivity to:
- **Interpolation Tolerance**: The threshold used to match orientations to texture components.
- **Data Sparsity**: Limited data points in certain reduction levels or materials.
- **Noise**: Measurement errors in EBSD data.

Sensitivity analysis ensures that model predictions remain stable across reasonable variations in these parameters (FR-007, SC-004).

## Methodology

### 1. Interpolation Tolerance Sweep

**Parameter**: Interpolation tolerance (angular distance threshold for component matching).

**Values Tested**: {0.01, 0.05, 0.1} radians.

**Procedure**:
1. Load processed descriptors from `data/processed/descriptors.csv`.
2. For each tolerance value `t` in {0.01, 0.05, 0.1}:
 - Re-calculate texture descriptors using tolerance `t` (if applicable).
 - Train the predictive models (Polynomial Regression, Gaussian Process).
 - Perform k-fold cross-validation (5-fold).
 - Record R² and RMSE metrics.
3. Store results in `data/processed/sensitivity_analysis.csv`.

**Expected Output**:
```csv
tolerance,model_type,r_squared,rmse,timestamp
0.01,polynomial,0.87,0.05,2026-06-12T10:00:00Z
0.01,gp,0.89,0.04,2026-06-12T10:00:05Z
0.05,polynomial,0.86,0.05,2026-06-12T10:00:10Z
0.05,gp,0.88,0.04,2026-06-12T10:00:15Z
0.10,polynomial,0.85,0.06,2026-06-12T10:00:20Z
0.10,gp,0.87,0.05,2026-06-12T10:00:25Z
```

### 2. Stability Criterion (SC-004)

**Requirement**: R² variation across tolerances must remain ≤ 0.02.

**Calculation**:
```
R²_variation = max(R²_tolerances) - min(R²_tolerances)
Pass if R²_variation ≤ 0.02
```

**Interpretation**:
- **Pass**: Model is robust to interpolation tolerance changes.
- **Fail**: Model is sensitive; consider regularization, more data, or tolerance refinement.

### 3. Variance Decomposition

**Objective**: Quantify the percentage of residual variance attributable to missing microstructural variables (e.g., grain size, SFE).

**Method**: Shapley values or hierarchical modeling (T035, T036).

**Procedure**:
1. Train a baseline model with available features (reduction, material).
2. Simulate or estimate the impact of adding missing variables (if data available).
3. Calculate the reduction in residual variance.
4. Report the percentage of unexplained variance.

**Output**: A metric in the final report indicating, e.g., "15% of variance attributable to missing microstructural variables."

## Implementation Details

### Code Structure

```python
# code/analysis/robustness.py
class RobustnessAnalysis:
 def __init__(self, descriptors_path: Path):
 self.descriptors = self.load_descriptors(descriptors_path)

 def run_sensitivity_analysis(self, tolerances: List[float] = [0.01, 0.05, 0.1]):
 results = []
 for tol in tolerances:
 metrics = self.evaluate_model_at_tolerance(tol)
 results.append(metrics)
 return self.save_results(results)

 def evaluate_model_at_tolerance(self, tolerance: float) -> Dict:
 # Re-calculate descriptors if needed
 # Train models
 # Cross-validate
 # Return R², RMSE
 pass

 def check_stability(self, results: List[Dict]) -> bool:
 r2_values = [r['r_squared'] for r in results]
 variation = max(r2_values) - min(r2_values)
 return variation <= 0.02
```

### Execution

Run the analysis via:
```bash
python code/analysis/robustness.py
```

**Input**: `data/processed/descriptors.csv`
**Output**: `data/processed/sensitivity_analysis.csv`

## Interpretation Guidelines

### R² Variation ≤ 0.02
- **Implication**: Model predictions are stable; the choice of interpolation tolerance does not significantly affect outcomes.
- **Action**: Proceed with standard tolerance (e.g., 0.05) for final model training.

### R² Variation > 0.02
- **Implication**: Model is sensitive to tolerance; predictions may be unreliable.
- **Actions**:
 1. Investigate data sparsity in specific reduction levels.
 2. Consider regularization (e.g., L2 penalty for polynomial models).
 3. Refine tolerance selection based on physical constraints.
 4. Collect more data to reduce uncertainty.

### Component-Specific Sensitivity
- Some texture components (e.g., Brass) may be more sensitive than others (e.g., Goss).
- Analyze R² variation per component to identify weak points.

## Integration with Validation Pipeline

1. **After Model Training**: Run sensitivity analysis to assess robustness.
2. **Before Deployment**: Verify SC-004 criterion is met.
3. **In Reports**: Include sensitivity analysis results to demonstrate model stability.

## Limitations of Sensitivity Analysis

- **Scope**: Only tests interpolation tolerance; does not assess sensitivity to other hyperparameters (e.g., GP kernel length scales).
- **Data Dependency**: Results depend on the quality and coverage of the input dataset.
- **Computational Cost**: Re-training models for each tolerance may be expensive for large datasets.

## Future Enhancements

1. **Hyperparameter Sweeps**: Extend sensitivity analysis to other model parameters.
2. **Cross-Validation Robustness**: Assess stability across different CV folds.
3. **Out-of-Distribution Testing**: Evaluate performance on materials/reductions outside the training set.
4. **Uncertainty Propagation**: Quantify how measurement errors propagate through the pipeline.

---
*This methodology ensures that model predictions are robust and reliable, supporting the project's goal of accurate texture evolution prediction.*
