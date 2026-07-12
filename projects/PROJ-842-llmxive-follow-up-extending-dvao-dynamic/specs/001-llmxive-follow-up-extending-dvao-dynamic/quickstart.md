# Quickstart: llmXive follow-up: extending "DVAO: Dynamic Variance-adaptive Advantage Optimization for Multi-reward"

## Prerequisites

- Python 3.11+
- pip / virtualenv

## Installation

1.  **Clone the repository** (or navigate to the project root).
2.  **Create a virtual environment**:
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `requirements.txt` pins `numpy`, `scipy`, `sympy`, `pandas`, `pyyaml`, `pytest`, `pytest-cov`.*

## Running the Experiment Suite

### 1. Generate Theoretical Bound
Run the symbolic derivation to generate the theoretical curve.
```bash
python src/main.py --task derive
```
*Output*: `data/processed/theoretical_bound.json`

### 2. Run Simulations
Execute the full experiment suite (N=5, 10, 20, 50) with default parameters.
```bash
python src/main.py --task simulate --config defaults.yaml
```
*Output*: `data/raw/` (trajectories), `data/processed/` (variance estimates).

### 3. Statistical Analysis
Perform paired t-tests and sensitivity analysis.
```bash
python src/main.py --task analyze
```
*Output*: `data/processed/statistical_results.csv`, `data/processed/sensitivity_report.json`.

### 4. Update State (Versioning)
Run the post-run script to update project state hashes.
```bash
python scripts/update_state.py
```
*Output*: Updates `state/projects/PROJ-842-llmxive-follow-up-extending-dvao-dynamic.yaml`.

### 5. Validate Contracts
Ensure generated data matches the schema.
```bash
pytest tests/contract/
```

## Configuration
Edit `src/config/defaults.yaml` to change:
- `num_objectives`: List of $N$ values.
- `window_ratios`: List of $k$ ratios (e.g., `[0.01, 0.05, 0.1]`).
- `noise_correlation`: List of $\rho$ values.
- `seed`: Random seed for reproducibility.

## Troubleshooting
- **OOM Error**: Reduce `state_space_size` in `defaults.yaml` or reduce `num_episodes`.
- **Slow Runtime**: Ensure you are not running on a heavy I/O disk; use `--parallel` if supported by CI.
- **Import Error**: Verify `requirements.txt` is up to date and virtualenv is active.