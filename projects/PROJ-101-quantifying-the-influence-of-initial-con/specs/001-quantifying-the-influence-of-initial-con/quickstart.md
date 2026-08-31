# Quickstart: Quantifying the Influence of Initial Conditions on Chaotic Systems

## Prerequisites

- Python 3.11+
- `pip` (or `conda`)
- 4GB+ RAM (recommended for larger $N$)
- Standard CPU (no GPU required)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-101-quantifying-the-influence-of-initial-con
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
    *Dependencies*: `numpy`, `scipy`, `pandas`, `matplotlib`, `pytest`, `pyyaml`, `mpmath`, `statsmodels`.

## Running the Analysis

### Option 1: Full Pipeline (Recommended)
Runs the entire workflow: generation, baseline validation, FTLE calculation, and regression.
```bash
python code/orchestrator.py --config code/config.py
```
- **Output**: Results saved to `data/processed/`.
- **Validation**: The pipeline will halt if the baseline is not converged, if the system is non-chaotic, or if the shadowing lemma check fails.

### Option 2: Generate Trajectories Only
Generates synthetic data without analysis.
```bash
python code/generator.py --noise [low magnitude] --dim 5 --steps 5000
```

### Option 3: Compute Baseline Only
Computes the asymptotic Lyapunov spectrum for a clean system.
```bash
python code/baseline.py --dim [dimension]
```

### Option 4: Run Tests
Execute the full test suite, including the runtime benchmark.
```bash
pytest tests/ -v
```
- **Performance Check**: `tests/performance/test_runtime_benchmark.py` verifies that $N=5$ generation completes in $\le 30$s.

## Verifying Results

1.  **Check Baseline Convergence**:
    ```bash
    cat data/processed/baseline_N.json
    # Ensure "validated": true and "convergence_error" < 0.05 and "richardson_error" is small
    ```

2.  **View Regression Results**:
    ```bash
    cat data/processed/regression_summary_N<sample_size>.json
    # Check "selected_model" and "bias_significant"
    ```

3.  **Generate Plots**:
    ```bash
    python code/visualize.py --input data/processed/regression_summary_N.json --output plots/
    ```

## Troubleshooting

- **Error: `NonChaoticSystemError`**: The parameter $\rho$ is too low ($\lambda_{max} \le 0$). Check `code/config.py`.
- **Error: `UnphysicalTrajectoryError`**: Noise level is too high or trajectory diverged. Reduce `--noise` or check bounds.
- **Error: `ShadowingFailureError`**: The noisy trajectory no longer shadows a true orbit. Reduce `--noise`.
- **Runtime > 30s for N=5**: Your CPU may be slower than the standard. The benchmark test will flag this.
