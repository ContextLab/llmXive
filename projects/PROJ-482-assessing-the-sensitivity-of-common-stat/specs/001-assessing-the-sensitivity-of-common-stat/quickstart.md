# Quickstart: Assessing the Sensitivity of Common Statistical Tests to Dataset Size

## Prerequisites

- Python 3.11+
- Git
- Access to a terminal (local or GitHub Actions runner)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-482-assessing-the-sensitivity-of-common-stat
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *Note: `requirements.txt` pins specific versions of `numpy`, `scipy`, `pandas`, `matplotlib`, `seaborn`, `statsmodels`, and `pytest`.*

## Running the Simulation

### Step 1: Validate Data Generation (Ground Truth Check)
Before running the full simulation, verify the data generator produces correct distributions.
```bash
python code/run_data_gen.py --validate
```
- **Expected Output**: `data/raw/sample_validation.csv` is created.
- **Verification**: Check that `observed_mean_diff` matches `expected_mean_diff` within tolerance (1e-6) for the `normal` distribution.
- **Note**: This script invokes `code/data_generator.py` to perform the generation and validation logic, then writes the CSV with MD5 checksums.

### Step 2: Run Full Simulation
Execute the adaptive Monte Carlo simulation.
```bash
python code/main.py
```
- **Process**:
  1. Generates data for all configurations.
  2. Runs adaptive replicates until CI width ≤ 0.01 (using Clopper-Pearson).
  3. Aggregates results.
  4. Fits Beta Regression models.
- **Output**: `data/processed/aggregated_results.csv`, `data/processed/regression_results.csv`, and plots in `data/figures/`.

### Step 3: Visualize Results
Generate publication-ready plots.
```bash
python code/visualization.py
```
- **Output**: PNG/SVG files in `data/figures/` showing error rates vs. sample size.

## Testing

Run the test suite to ensure correctness:
```bash
pytest tests/ -v
```
- **Unit Tests**: Verify data generation statistics.
- **Integration Tests**: Verify simulation loop convergence logic.

## Troubleshooting

- **Convergence Timeout**: If a configuration takes > 10,000 replicates to converge, check `code/simulation_engine.py` for the `max_replicates` limit. This usually indicates a bug in the test logic or extreme skewness.
- **Memory Error**: The simulation is designed to be memory-efficient. If memory errors occur, reduce `max_replicates` in `config.py` (not recommended for final runs).
- **Missing Dependencies**: Ensure `requirements.txt` is up to date and installed in the correct virtual environment.