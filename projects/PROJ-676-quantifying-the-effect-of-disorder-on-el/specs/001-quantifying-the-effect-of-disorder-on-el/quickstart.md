# Quickstart: Quantifying the Effect of Disorder on Electronic Transport in 1D Chains

## Prerequisites

*   Python 3.11+
*   pip (Python package installer)
*   Git

## Installation

1.  **Clone the repository** (or navigate to the project root):
    ```bash
    cd projects/PROJ-676-quantifying-the-effect-of-disorder-on-el
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Dependencies include: `numpy`, `scipy`, `matplotlib`, `pandas`, `h5py`, `pytest`, `joblib`.*

## Running the Analysis

The project is designed to run end‑to‑end via the `main.py` script.

### 1. Generate Data and Compute Localization Lengths (PR Scaling & TM)

This step generates Hamiltonians for a **grid of system sizes** and disorder widths, computes eigenstates, extracts participation ratios, performs finite-size scaling, and runs the transfer-matrix analysis.

```bash
python code/main.py \
    --mode generate_and_analyze \
    --Llist 100 200 400 800 1600 \
    --Wlist 0.5 1.0 2.0 \
    --realizations 100 \
    --seed 42
```

*   `--Llist`: Space‑separated list of system sizes to include in the PR scaling fit.
*   `--Wlist`: Disorder widths of interest.
*   `--realizations`: Number of disorder samples per $(W, L)$.
*   `--seed`: Random seed for reproducibility.

### 2. Run Scaling Analysis (fit $\log\xi$ vs $\log W$)

After data generation for all $L$ values, run the regression:

```bash
python code/main.py \
    --mode scaling_analysis \
    --output data/processed/scaling_results.csv
```

### 3. Generate Visualizations (Feynman‑style eigenstate plot)

```bash
python code/main.py \
    --mode visualize \
    --L 200 \
    --W 2.0 \
    --realization 5 \
    --output figures/eigenstate_decay.png
```

### 4. Run Tests

Verify the implementation against contract schemas:

```bash
pytest tests/contract/ -v
pytest tests/unit/ -v
```

## Output Files

*   `data/raw/h_W{W}_L{L}.h5`: Raw Hamiltonian and eigenstate data.
*   `data/processed/localization_lengths.csv`: Aggregated $\xi$ values (PR and TM).
*   `data/processed/scaling_results.csv`: Regression results (slope, $R^2$, etc.).
*   `figures/eigenstate_decay.png`: Visualization of $|\psi|^2$ vs site index.

## Troubleshooting

*   **Memory Error**: If `scipy.linalg.eigh` fails for $L=1600$, the script automatically switches to `scipy.sparse.linalg.eigsh`. Reduce `--Llist` or `--realizations` if RAM issues persist.
*   **Numerical Underflow**: The Transfer Matrix method uses QR‑based logarithmic accumulation; warnings about singular values indicate a need to increase the number of orthogonalization steps (handled automatically).
*   **Reproducibility**: Ensure the same `--seed` is used to regenerate identical data; the seed is recorded in `data/metadata/provenance.json`.