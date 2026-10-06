# Quickstart: Autocorrelation of the Möbius Function in Short Intervals

## Prerequisites

- Python 3.11+
- `pip` package manager
- Sufficient disk space (~500 MB)

## Installation

1.  **Clone the repository** and navigate to the project directory.
2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Dependencies include: `numpy`, `scipy`, `matplotlib`, `pandas`, `pytest`.*

## Running the Pipeline

The full pipeline (Sieve -> Correlation -> Permutation -> Viz) can be run via the main entry point:

```bash
python code/main.py
```

This will:
1.  Generate $\mu(n)$ for $N=10^7$ and save to `data/raw/mobius_array.npy`.
2.  Compute autocorrelation for varying system sizes $L$.
3.  Run multiple permutations per window.
4.  Calculate the **Theoretical Variance Benchmark** (PNT) for comparison.
5.  Generate heatmaps in `outputs/figures/`.
6.  Save statistics to `data/processed/autocorrelation_stats.csv`.

### Running Specific Stages

- **Generate Möbius Sequence Only**:
  ```bash
  python code/sieve.py --generate
  ```
- **Run Permutation Test Only** (requires existing `mobius_array.npy`):
  ```bash
  python code/permutation.py --run
  ```
- **Generate Visualizations Only**:
  ```bash
  python code/viz.py --run
  ```

## Verification

To verify the results:

1.  **Check the sieve**:
    ```bash
    python -c "import numpy as np; a = np.load('data/raw/mobius_array.npy'); print(f'Unique values: {np.unique(a)}')"
    # Expected: [-1  0  1]
    ```
2.  **Run unit tests**:
    ```bash
    pytest tests/unit/
    ```
3.  **Run integration tests**:
    ```bash
    pytest tests/integration/
    ```

## Troubleshooting

- **Memory Error**: Ensure you are using `int8` for the Möbius array. The default `int` type would require approximately 80 MB, which is still safe, but `int8` is preferred.
- **Timeout**: The full pipeline may take several hours. If running on a local machine with slower CPU, consider reducing the number of windows tested (modify `config.yaml` or `main.py` arguments).
- **P-value 0.0**: If the observed autocorrelation is more extreme than all permutations in the resampling distribution, the p-value will be reported as the reciprocal of the total number of permutations. to avoid false certainty.
- **Interpretation Note**: The results include both a **permutation-based p-value** (testing the random-sign heuristic) and a **theoretical variance benchmark** (testing arithmetic consistency against the Prime Number Theorem). Uniform p-values indicate the data is indistinguishable from a shuffled version, but deviations from the theoretical variance may indicate arithmetic structure.