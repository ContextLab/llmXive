# T030: Save Permutation and Sensitivity Results

## Overview
This task implements the functionality to save permutation test results and sensitivity analysis summaries to CSV files.

## Files Created

### `code/analysis/saving.py`
Contains functions for saving analysis results:
- `save_permutation_results()`: Saves permutation test results (p-values and max statistics)
- `save_sensitivity_summary()`: Saves sensitivity analysis DataFrame
- `save_fwe_corrected_results()`: Saves FWE-corrected p-values

### `code/scripts/save_results.py`
Demonstration script that runs the full pipeline and saves results.

### `tests/unit/test_saving.py`
Unit tests for the saving functionality.

## Output Files

### `data/interim/permutation_results.csv`
Contains:
- `p_value`: Empirical p-values from permutation tests
- `max_stat`: Max statistics from the permutation distribution

### `data/interim/sensitivity_summary.csv`
Contains:
- `window_length`: Window length used in the analysis
- `correlation`: Pearson correlation coefficient
- `p_value`: P-value for the correlation

### `data/interim/fwe_corrected_results.csv`
Contains:
- `original_p_value`: Original p-values before correction
- `adjusted_p_value`: FWE-corrected p-values
- `correction_method`: Method used for correction (e.g., 'max-t', 'bonferroni')

## Usage

```python
from analysis.saving import save_permutation_results, save_sensitivity_summary
from analysis.statistics import construct_sensitivity_df

# Save permutation results
save_permutation_results(p_values, max_stats)

# Save sensitivity summary
sensitivity_df = construct_sensitivity_df(data)
save_sensitivity_summary(sensitivity_df)
```

## Dependencies
- T027: `run_permutation_test` (provides p-values and max statistics)
- T046: `run_sensitivity_analysis` (provides sensitivity data)
- T046.1: `construct_sensitivity_df` (transforms sensitivity data to DataFrame)

## Error Handling
- Empty input lists raise `ValueError`
- Mismatched list lengths raise `ValueError`
- Missing required columns in DataFrame raise `ValueError`
- All functions ensure output directories exist before writing