# API Reference

## `code/config.py`

### `Config`
Dataclass holding simulation parameters.
- `seed`: int
- `openml_ids`: List[int]
- `snr_levels`: List[float]
- `sparsity_levels`: List[float]
- `simulations_per_condition`: int
- `output_path`: str

### `get_config()`
Returns the global `Config` instance.

## `code/data/downloader.py`

### `DatasetMetadata`
Dataclass for dataset info: `id`, `name`, `n_rows`, `n_features`, `X`, `y`, `checksum`.

### `fetch_datasets(ids: List[int]) -> List[DatasetMetadata]`
Fetches datasets from OpenML. Raises `RuntimeError` if validation fails.

## `code/data/simulators.py`

### `SimulatorConfig`
Configuration for synthetic outcome generation.

### `generate_synthetic_outcomes(X, true_coefficients, snr, sparsity, seed)`
Generates Y vectors with specified SNR and sparsity. Returns `SimulatedDataset`.

## `code/analysis/selectors.py`

### `lasso_selection(X, y, alpha)`
Performs LASSO selection. Returns list of selected feature indices.

### `forward_stepwise(X, y, max_features)`
Performs forward stepwise selection using AIC. Returns list of selected feature indices.

### `backward_elimination(X, y, min_features)`
Performs backward elimination. Returns list of selected feature indices.

## `code/analysis/metrics.py`

### `calculate_empirical_power(selected_vars, true_coefficients, p_values, alpha)`
Calculates power rate. Returns float.

### `calculate_vif(X)`
Computes Variance Inflation Factor for all features. Returns dict.

### `calculate_condition_number(X)`
Computes condition number of X. Returns float.

## `code/analysis/comparators.py`

### `kruskal_wallis_test(df, group_col, value_col)`
Performs Kruskal-Wallis H-test. Returns (statistic, p-value).

### `dunn_post_hoc(df, group_col, value_col, method='holm')`
Performs Dunn's post-hoc test with specified correction. Returns DataFrame of pairwise comparisons.

## `code/viz/plots.py`

### `plot_power_curves(df, output_path)`
Generates power vs. SNR curves faceted by sparsity. Saves to `output_path`.
