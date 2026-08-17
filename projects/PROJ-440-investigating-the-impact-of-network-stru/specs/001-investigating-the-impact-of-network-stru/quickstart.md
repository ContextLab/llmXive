# Quickstart: Investigating the Impact of Network Structure on Energy Dissipation in Driven Oscillators

## Prerequisites

- Python 3.11+
- `pip` or `venv`
- Git

## Setup

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-440-investigating-the-impact-of-network-stru
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```

## Running the Pipeline

### Step 1: Generate Networks
```bash
python code/generate_networks.py --n_samples 50 --node_count 150 --output data/raw/networks.csv
```
- Generates multiple networks (several per class).
- Validates metrics against theoretical expectations.

### Step 2: Simulate Oscillators
```bash
python code/simulate_oscillators.py --input data/raw/networks.csv --output data/processed/energy_decay.csv --time 200 --damping 0.1
```
- Runs ODE integration for each network.
- Extracts decay rates and validates fit quality (R² ≥ 0.95).

### Step 3: Analyze Regression
```bash
python code/analyze_regression.py --input data/processed/energy_decay.csv --output data/analysis/regression_results.json
```
- Performs PCR, applies Bonferroni correction, and runs sensitivity analysis.
- Generates convergence plots and VIF diagnostics.

### Step 4: Validate Results
```bash
pytest tests/
```
- Runs unit tests for generation, simulation, and regression.
- Verifies convergence and statistical validity.

## Output Files

- `data/raw/networks.csv`: Generated topologies and metrics.
- `data/processed/energy_decay.csv`: Energy time-series and decay rates.
- `data/analysis/regression_results.json`: PCR coefficients, p-values, and diagnostics.
- `code/output/`: Plots (convergence, sensitivity, regression coefficients).

## Troubleshooting

- **Convergence Failure**: If `solve_ivp` fails, check `data/processed/energy_decay.csv` for "failed" status. Adjust `rtol`/`atol` in `simulate_oscillators.py`.
- **Collinearity**: If VIF > 5, results are reported descriptively. Check `data/analysis/regression_results.json` for `vif_scores`.
- **Resonance**: If energy grows (negative decay rate), flagged as "resonant" and excluded from regression.

## Reproducibility

- **Random Seeds**: All scripts use fixed seeds (e.g., `np.random.seed(42)`).
- **Dependencies**: `requirements.txt` pins all versions.
- **Checksums**: All data files are checksummed and recorded in `state/`.
