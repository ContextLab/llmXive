# Analysis Technical Specification

## Module: `code/analyze_pvalues.py`

### Functions

#### `calculate_ks_statistic(p_values, reference='uniform')`
Calculates the Kolmogorov-Smirnov statistic comparing observed p-values to a reference.

**Parameters:**
- `p_values` (numpy.ndarray): Array of observed p-values.
- `reference` (str): Either `'uniform'` or `'permutation'`.

**Returns:**
- `float`: The KS statistic $D$.
- `float`: The p-value of the KS test itself.

#### `generate_permutation_reference(data, n_permutations=1000)`
Generates a reference distribution of p-values using permutation testing.

**Parameters:**
- `data` (numpy.ndarray): The observed data matrix.
- `n_permutations` (int): Number of permutations to perform.

**Returns:**
- `numpy.ndarray`: Array of empirical p-values from permutations.

## Output Artifacts

### `data/results/ks_stats.json`
Contains the KS statistics for all parameter configurations.
Structure:
```json
{
 "results": [
 {
 "seed": 123,
 "n": 100,
 "p": 500,
 "rho": 0.5,
 "ks_stat": 0.045,
 "ks_pvalue": 0.12
 }
 ]
}
```

### `docs/plots/qq_{seed}.png`
QQ-plots comparing observed p-value quantiles to theoretical uniform quantiles.