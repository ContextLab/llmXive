# Data Generation Technical Specification

## Module: `code/generate_data.py`

### Functions

#### `generate_correlated_data(n, p, rho, seed)`
Generates an $n \times p$ matrix with correlation structure determined by $\rho$.

**Parameters:**
- `n` (int): Number of samples.
- `p` (int): Number of features.
- `rho` (float): Target correlation coefficient (0.0 to 0.9).
- `seed` (int): Random seed for reproducibility.

**Returns:**
- `numpy.ndarray`: Data matrix $X$.

**Algorithm:**
1. Construct a Toeplitz-like correlation matrix $\Sigma$ where $\Sigma_{ij} = \rho^{|i-j|}$.
2. Perform Cholesky decomposition $L = \text{cholesky}(\Sigma)$.
3. Generate $Z \sim N(0, I_{n \times p})$.
4. Return $X = Z L^T$.

#### `generate_distribution_violations(n, p, dist_type, seed)`
Generates data with specific non-Gaussian properties.

**Parameters:**
- `n` (int): Number of samples.
- `p` (int): Number of features.
- `dist_type` (str): One of `'t_dist'`, `'skew_normal'`.
- `seed` (int): Random seed.

**Returns:**
- `numpy.ndarray`: Data matrix with specified distributional properties.

### Output Formats

#### Metadata JSON (`data/synthetic/{seed}.json`)
```json
{
 "seed": 12345,
 "n": 1000,
 "p": 2000,
 "rho": 0.5,
 "distribution_type": "normal",
 "sha256": "abc123..."
}
```

#### Trajectory Data (`data/synthetic/trajectories/{seed}.npy`)
- **Format**: NumPy binary (`.npy`).
- **Shape**: `(N_iterations, p)`.
- **Dtype**: `float32`.
- **Content**: All p-values generated across iterations for this configuration.