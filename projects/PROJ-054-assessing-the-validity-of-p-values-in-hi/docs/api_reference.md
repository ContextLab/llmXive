# API Reference

## `code/generate_data.py`

### `generate_correlated_data(n, p, rho, seed)`
Generates an $n \times p$ data matrix with correlation structure defined by $\rho$.
- **Returns**: `numpy.ndarray`
- **Raises**: `HighDimensionalInstabilityError` if condition number is too high.

### `generate_distribution_violations(data, distribution_type)`
Transforms Gaussian data into heavy-tailed or skewed distributions.
- **Parameters**:
 - `data`: Input Gaussian matrix.
 - `distribution_type`: 't_dist' or 'skew_normal'.
- **Returns**: Transformed `numpy.ndarray`.

### `write_dataset_metadata(seed, n, p, rho, distribution, sha256)`
Writes the metadata JSON file for a generated dataset.

## `code/run_tests.py`

### `run_hypothesis_tests(data, groups)`
Performs t-tests and F-tests for each feature.
- **Parameters**:
 - `data`: $n \times p$ data matrix.
 - `groups`: Binary vector of group assignments.
- **Returns**: Dictionary of p-values.

### `run_hypothesis_tests_batch(iterations, n, p, rho, distribution)`
Orchestrates the generation and testing loop for a single parameter set.

## `code/analyze_pvalues.py`

### `generate_permutation_reference(data, groups, n_permutations)`
Computes the empirical p-value distribution via permutation.
- **Returns**: Array of permutation p-values.

### `calculate_ks_statistic(pvalues, reference_type)`
Calculates the KS statistic against Uniform(0,1) or a permutation reference.
- **Returns**: `float` (KS statistic).

## `code/plot_qq.py`

### `generate_qq_plot(pvalues, output_path)`
Creates a QQ-plot comparing empirical p-values to Uniform(0,1).
- **Output**: Saves PNG to `output_path`.

## `code/sensitivity_analysis.py`

### `run_sensitivity_analysis(rho_values, n, p)`
Executes the full sensitivity sweep over correlation values.
- **Output**: `data/results/sensitivity.csv`.

## `code/utils/exceptions.py`

### `HighDimensionalInstabilityError`
Raised when covariance matrix condition number exceeds $10^{12}$.

### `HypothesisTestError`
Raised when a statistical test fails to converge or produces invalid results.

### `SimulationError`
Generic error for simulation orchestration failures.