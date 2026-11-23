# Quickstart: Assessing the Sensitivity of Common Statistical Tests to Dataset Size

## Prerequisites
- Python 3.11+
- `pip` or `conda`

## Installation

1. **Clone the repository** and navigate to the project directory:
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
   pip install -r code/requirements.txt
   ```
   *Note: `requirements.txt` is located in `projects/PROJ-482-assessing-the-sensitivity-of-common-stat/code/`.*

## Running the Simulation

### Step 1: Generate and Validate Data
Run the data generator to create synthetic datasets and validate them against ground truth.
```bash
python code/run_data_gen.py --config code/config.yaml
```
- This will generate `data/raw/sample_validation.csv` and verify the ground truth parameters.
- **Expected Output**: A CSV file with columns `sample_size`, `distribution`, `mean`, `variance`, `skewness`, `ground_truth_mean`, `ground_truth_var`, `pass`.

### Step 2: Run Monte Carlo Simulations
Execute the adaptive simulation loop.
```bash
python code/simulation_runner.py --config code/config.yaml
```
- This will iterate through all configurations (multiple sizes × 3 dists × 3 tests).
- It will automatically extend replicates until the confidence interval width meets the predefined precision threshold.
- **Output**: `data/processed/error_rates.csv`.

### Step 3: Analyze and Visualize
Generate plots and fit the regression model.
```bash
python code/analyzers.py --input data/processed/error_rates.csv --output data/analysis/
```
- **Outputs**:
  - `data/visualizations/error_rate_curves.png`
  - `data/visualizations/power_curves.png`
  - `data/analysis/regression_results.yaml`

## Verification

To verify the installation and data generation:
1. Check that `data/raw/sample_validation.csv` exists and has the correct columns.
2. Run the unit tests:
   ```bash
   pytest tests/unit/
   ```
3. Verify the checksum of the generated data matches the one recorded in the state file.

## Troubleshooting

- **ImportError**: Ensure you are using Python 3.11+ and the virtual environment is activated.
- **Convergence Failure**: If the adaptive loop fails to converge for a specific configuration, check the logs in `data/logs/simulation.log`. This may indicate a numerical instability in the distribution generation.
- **Memory Error**: The script is designed to stream data. If memory errors occur, reduce the `batch_size` in `code/config.yaml`.