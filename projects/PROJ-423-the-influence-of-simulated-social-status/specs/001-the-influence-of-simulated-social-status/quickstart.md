# Quickstart: Simulated Social Status on Risk-Taking

## Prerequisites

- Python 3.11+
- `pip`
- Access to a Linux environment (GitHub Actions or local WSL)

## Installation

1. **Clone the repository** (if applicable) or navigate to the project root.
2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```
   *Dependencies include: `pandas`, `numpy`, `statsmodels`, `scipy`, `matplotlib`, `seaborn`, `pyyaml`.*

## Execution Workflow

### Step 1: Data Simulation
Run the simulation script to generate the synthetic dataset.
```bash
python code/simulation.py --seed 42 --n 400
```
- **Output**: `data/raw/simulated_data.csv`
- **Verification**: Check that the file contains a sufficient number of rows and 4 unique conditions.

### Step 2: Preprocessing
Clean the data and detect the data structure.
```bash
python code/preprocess.py --input data/raw/simulated_data.csv
```
- **Output**: `data/processed/cleaned_data.csv`, `data/processed/structure_config.json`, `data/processed/validation_report.json`.

### Step 3: Analysis
Fit the mixed-effects model and run sensitivity analysis.
```bash
python code/analysis.py --input data/processed/cleaned_data.csv
```
- **Output**: `data/processed/model_output.json`, `data/processed/sensitivity_analysis.csv`, `data/processed/posthoc_results.json`.

### Step 4: Reporting
Generate visualizations and final reports.
```bash
python code/reporting.py --model data/processed/model_output.json --plot data/processed/forest_plot.png
```
- **Output**: `data/processed/forest_plot.png`, `data/processed/report.html` (if configured).

## Verification

To verify the pipeline:
1. Check that `data/processed/model_output.json` contains a non-null `interaction_p_value`.
2. Ensure `data/processed/sensitivity_analysis.csv` has 3 rows (thresholds 2.5, 3.0, 3.5).
3. Confirm `data/processed/forest_plot.png` exists and displays 4 error bars.

## Troubleshooting

- **Memory Error**: If `statsmodels` fails due to memory, reduce `--n` in the simulation step.
- **Singular Fit**: If the random effect variance is zero, the script automatically switches to a fixed-effects model (between-subjects logic) and logs a warning.
- **Missing Columns**: Ensure the simulation output matches the `contracts/data.schema.yaml` definition.
