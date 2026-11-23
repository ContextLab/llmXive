# Evaluation Module API Documentation

This document provides detailed API documentation for the `code/eval/` module, covering the implementation of Functional Requirements FR-001 to FR-007 related to sensitivity analysis, metrics calculation, and reporting.

## Overview

The evaluation module implements:
- **FR-001**: Sensitivity analysis on MAE thresholds
- **FR-002**: Multiple-comparison correction (Bonferroni/FDR)
- **FR-003**: Model performance metrics (MAE, RMSE, R²)
- **FR-004**: Statistical comparison between models
- **FR-005**: Conformer stability analysis
- **FR-006**: Scale analysis of SASA values
- **FR-007**: Oracle evaluation against ground truth

## Modules

### `code/eval/metrics.py`

Implements core evaluation metrics and statistical tests.

#### Functions

**`calculate_mae(y_true: np.ndarray, y_pred: np.ndarray) -> float`**
Calculates Mean Absolute Error.
- Implements FR-003: Primary metric for threshold analysis
- Formula: `mean(|y_true - y_pred|)`

**`calculate_rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float`**
Calculates Root Mean Squared Error.
- Implements FR-003: Secondary metric for model evaluation
- Formula: `sqrt(mean((y_true - y_pred)²))`

**`calculate_r2(y_true: np.ndarray, y_pred: np.ndarray) -> float`**
Calculates R-squared coefficient of determination.
- Implements FR-003: Model fit metric
- Formula: `1 - SS_res/SS_tot`

**`calculate_all_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]`**
Calculates all three metrics at once for efficiency.
- Returns dict with `mae`, `rmse`, `r2`

**`paired_ttest(y_true: np.ndarray, y_pred_a: np.ndarray, y_pred_b: np.ndarray) -> Tuple[float, float]`**
Performs paired t-test between two model predictions.
- Compares error distributions of two models
- Implements FR-004: Statistical significance testing
- Returns (t-statistic, p-value)

**`cohen_d(y_true: np.ndarray, y_pred_a: np.ndarray, y_pred_b: np.ndarray) -> float`**
Calculates Cohen's d effect size between two models.
- Measures magnitude of difference between models
- Implements FR-004: Effect size reporting
- Interpretation: 0.2=small, 0.5=medium, 0.8=large

**`compare_models(y_true: np.ndarray, y_pred_gcn: np.ndarray, y_pred_baseline: np.ndarray) -> Dict[str, Any]`**
Comprehensive model comparison:
- Paired t-test
- Cohen's d
- Individual metrics for each model
- Implements FR-004: Complete model comparison report

**`bonferroni_correction(p_values: List[float], n_tests: int) -> List[float]`**
Applies Bonferroni correction for multiple comparisons.
- Used when n <= 5 tests
- Implements FR-007: Multiple-comparison correction
- Formula: `p_corrected = min(p * n_tests, 1.0)`

**`fdr_correction(p_values: List[float]) -> List[float]`**
Applies False Discovery Rate (Benjamini-Hochberg) correction.
- Used when n > 5 tests
- Implements FR-007: Multiple-comparison correction
- Controls expected proportion of false discoveries

---

### `code/eval/sensitivity.py`

Implements sensitivity analysis on MAE thresholds.

#### Functions

**`load_predictions(path: Path) -> pd.DataFrame`**
Loads predictions from Parquet file with columns: `smiles`, `predicted_sasa`, `error`.

**`calculate_success_rates(errors: np.ndarray, thresholds: List[float]) -> List[float]`**
Calculates success rates for each threshold.
- Formula: `success_rate = count(errors < threshold) / total_count`
- Implements FR-001: Absolute threshold analysis
- Primary verification path per Spec FR-006

**`run_sensitivity_analysis_absolute(predictions_path: Path, thresholds: List[float]) -> pd.DataFrame`**
Runs complete sensitivity analysis on absolute thresholds {0.01, 0.05, 0.1}.
- Loads predictions
- Calculates success rates for each threshold
- Returns DataFrame with columns: `threshold`, `success_rate`, `sample_size`
- Implements FR-001: Primary sensitivity analysis

**`run_sensitivity_analysis_relative(predictions_path: Path, percentiles: List[float]) -> pd.DataFrame`**
Runs sensitivity analysis on relative thresholds (percentiles).
- Note: This is secondary to absolute thresholds per FR-006

**`run_multiple_comparison_correction(success_rates: pd.DataFrame) -> Dict[str, Any]`**
Applies multiple-comparison correction to sensitivity results.
- Uses Bonferroni if n <= 5, FDR if n > 5
- Implements FR-007: Correction for multiple tests
- Returns dict with corrected p-values and method used

**`generate_reproducibility_report(sample_size: int, streaming_rule: str) -> str`**
Generates limitations section for reproducibility report.
- Discusses statistical power of sample size
- Addresses biases from chunked streaming
- Implements FR-007: Transparency requirement

**`main() -> None`**
Entry point for sensitivity analysis pipeline.

---

### `code/eval/conformer_stability.py`

Analyzes conformer generation stability.

#### Functions

**`load_subset_for_pilot(path: Path, n_samples: int = 100) -> pd.DataFrame`**
Loads a subset of data for pilot stability analysis.

**`generate_multiple_conformers_and_sasa(smiles: str, n_conformers: int = 10) -> List[float]`**
Generates multiple conformers for a molecule and calculates SASA for each.
- Measures variance in SASA across conformers
- Implements FR-005: Conformer stability analysis

**`run_stability_check(data_path: Path, n_samples: int = 100) -> Dict[str, Any]`**
Runs stability analysis on a dataset subset.
- Calculates mean and std of SASA variance
- Identifies unstable molecules
- Returns stability statistics

**`main() -> None`**
Entry point for conformer stability analysis.

---

### `code/eval/oracle_evaluation.py`

Implements oracle evaluation against ground truth SASA.

#### Functions

**`load_test_indices(path: Path) -> List[int]`**
Loads test set indices from split file.

**`calculate_sasa_rdkit(smiles: str) -> float`**
Calculates reference SASA using RDKit's oracle method.
- Implements FR-007: Ground truth calculation
- Uses high-precision conformer generation

**`run_oracle_evaluation(predictions_path: Path, ground_truth_path: Path) -> Dict[str, float]`**
Compares model predictions against oracle ground truth.
- Calculates MAE, RMSE, R² against oracle
- Implements FR-007: Oracle validation

**`main() -> None`**
Entry point for oracle evaluation.

---

### `code/eval/scale_analysis.py`

Analyzes the scale and distribution of SASA values.

#### Functions

**`load_processed_data_stats(path: Path) -> pd.DataFrame`**
Loads processed dataset and calculates statistics.

**`analyze_sasa_scale(df: pd.DataFrame) -> Dict[str, Any]`**
Analyzes SASA value distribution:
- Mean, median, std, min, max
- Quartiles and percentiles
- Skewness and kurtosis
- Implements FR-006: Scale understanding

**`main() -> None`**
Entry point for scale analysis.

---

## Traceability to Functional Requirements

| FR-ID | Description | Implemented In |
|-------|-------------|----------------|
| FR-001 | Sensitivity analysis on thresholds | `sensitivity.py` - `run_sensitivity_analysis_absolute()` |
| FR-002 | Multiple-comparison correction | `sensitivity.py` - `run_multiple_comparison_correction()` |
| FR-003 | Model performance metrics | `metrics.py` - `calculate_mae()`, `calculate_rmse()`, `calculate_r2()` |
| FR-004 | Statistical model comparison | `metrics.py` - `paired_ttest()`, `cohen_d()`, `compare_models()` |
| FR-005 | Conformer stability analysis | `conformer_stability.py` - `run_stability_check()` |
| FR-006 | Scale analysis of SASA | `scale_analysis.py` - `analyze_sasa_scale()` |
| FR-007 | Oracle evaluation | `oracle_evaluation.py` - `run_oracle_evaluation()` |

## Usage Examples

### Calculating Metrics
```python
from code.eval.metrics import calculate_all_metrics

y_true = df['surface_area'].values
y_pred = df['predicted_sasa'].values
metrics = calculate_all_metrics(y_true, y_pred)
print(f"MAE: {metrics['mae']:.3f}, R²: {metrics['r2']:.3f}")
```

### Running Sensitivity Analysis
```python
from code.eval.sensitivity import run_sensitivity_analysis_absolute, run_multiple_comparison_correction

thresholds = [0.01, 0.05, 0.1]
results = run_sensitivity_analysis_absolute('results/predictions/gcn_predictions.parquet', thresholds)
corrected = run_multiple_comparison_correction(results)
print(f"Method: {corrected['method']}")
```

### Comparing Models
```python
from code.eval.metrics import compare_models

comparison = compare_models(y_true, y_pred_gcn, y_pred_baseline)
print(f"p-value: {comparison['p_value']:.4f}, Cohen's d: {comparison['cohen_d']:.3f}")
```

## Error Handling

All evaluation functions implement robust error handling:
- Missing predictions raise `FileNotFoundError`
- Invalid data types raise `ValueError`
- Statistical tests handle edge cases (constant predictions, zero variance)
- All errors are logged with context

## Dependencies

- `scipy.stats`: Statistical tests (t-test, KS test)
- `numpy`: Numerical operations
- `pandas`: Data loading and manipulation
- `scikit-learn`: Metric calculations
