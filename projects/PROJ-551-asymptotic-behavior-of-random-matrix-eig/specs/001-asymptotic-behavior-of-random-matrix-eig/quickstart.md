# Quickstart: Asymptotic Behavior of Random Matrix Eigenvalues with Sparse Perturbations

## Prerequisites

- Python 3.11+
- pip (package installer)
- A terminal with at least 14 GB free disk space (for intermediate data) and 7 GB RAM.

## Installation

1. **Clone the Repository** (or navigate to the project directory):
   ```bash
   cd projects/PROJ-551-asymptotic-behavior-of-random-matrix-eig
   ```

2. **Create a Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```
   *Note: `requirements.txt` pins `numpy`, `scipy`, `pandas`, `pytest`, `pyyaml`, `scikit-learn`.*

## Running the Simulation

### 1. Single Instance Test (FR-001, FR-002)
Verify the system can generate a matrix and detect an outlier.

```bash
python code/main.py --mode single --N 1000 --theta 2.5 --k 1 --pattern diagonal
```
**Expected Output**: A JSON report showing at least one eigenvalue $> \text{empirical\_bulk\_edge} + 0.05$.

### 2. Full Parameter Sweep (FR-005, FR-006)
Execute the full study (100 iterations per configuration). This may take 1-2 hours.

```bash
python code/main.py --mode sweep --N 2000 --iterations 100 --patterns diagonal,block-sparse,random-sparse
```
**Output**: Aggregated results saved to `data/processed/sweep_results.parquet`, including $\theta_c$ estimates.

### 3. Sensitivity Analysis (FR-006)
Run the sensitivity sweep on sparsity density.

```bash
python code/main.py --mode sensitivity --N 1000 --theta 1.5 --densities 0.1,0.2,0.3
```

## Verifying Results

1. **Check Checksums**:
   Ensure data integrity by running:
   ```bash
   python code/utils/checksum.py --verify
   ```
   This compares file hashes against `state/...yaml`.

2. **Visualize Thresholds**:
   Use the provided notebook (if available) or a simple script:
   ```python
   import pandas as pd
   import matplotlib.pyplot as plt

   df = pd.read_parquet("data/processed/sweep_results.parquet")
   # Plot outlier_probability vs theta for different patterns
   for pattern in df['pattern_type'].unique():
       subset = df[df['pattern_type'] == pattern]
       plt.plot(subset['theta'], subset['outlier_probability'], label=pattern)
       # Plot estimated theta_c
       if 'theta_c_estimate' in subset.columns:
           plt.axvline(x=subset['theta_c_estimate'].mean(), label=f'{pattern} theta_c')
   plt.axvline(x=1.0, color='r', linestyle='--', label='Theoretical Threshold (Dense)')
   plt.legend()
   plt.show()
   ```

## Troubleshooting

- **Memory Error**: If you encounter `MemoryError`, reduce `--N` to 1000 or 500. The iterative solver should handle $N=2000$, but system overhead can vary.
- **Solver Non-Convergence**: If `eigsh` fails to converge, check the `tol` parameter in `code/analysis/eigen_solver.py`. The default is `1e-10`.
- **No Outliers**: If $\theta < 1.0$, no outliers are expected. Ensure $\theta \ge 1.0$ for the sweep.
- **Dense Matrix Warning**: The system uses dense matrices for Wigner ensembles. Ensure sufficient RAM (7GB is sufficient for N=2000).
