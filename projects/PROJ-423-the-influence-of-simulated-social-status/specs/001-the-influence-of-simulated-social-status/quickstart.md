# Quickstart: Simulated Social Status & Risk-Taking

## Prerequisites
- Python 3.11+
- Git
- Access to a GitHub Actions runner (or local environment with same dependencies).

## Installation
1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-423-the-influence-of-simulated-social-status
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

### 1. Run Power Analysis
Calculates the required sample size for [deferred] power.
```bash
python code/power_analysis.py
```
*Output*: Updates `code/config.py` with the calculated `N_PARTICIPANTS`.

### 2. Generate Data
Simulates the dataset based on the calculated N and hypothesized effect sizes.
```bash
python code/simulate.py
```
*Output*: `data/raw/simulation_output.csv`

### 3. Preprocess Data
Cleans data, handles missing values, and validates structure.
```bash
python code/preprocess.py
```
*Output*: `data/processed/cleaned_data.csv`

### 4. Run Analysis
Fits the appropriate model (OLS or LMM based on data structure), calculates VIF, and runs sensitivity analysis. **This step also dynamically generates `structure_config.json`.**
```bash
python code/analysis.py
```
*Output*: Model summaries, VIF report, sensitivity tables, `data/processed/structure_config.json`.

### 5. Generate Report
Creates the forest plot and final summary.
```bash
python code/report.py
```
*Output*: `data/processed/report.html`, `data/processed/forest_plot.png`

## Verification
Run the test suite to ensure all contracts are met:
```bash
pytest tests/ -v
```
*Expected*: All contract tests pass, specifically `test_model_output.py` which validates `structure_config.json` against `contracts/model_output.schema.yaml`.

## Troubleshooting
- **Missing `structure_config.json`**: Ensure `code/analysis.py` runs successfully. The file is generated dynamically from the data, not hardcoded.
- **Model Convergence Warning**: Check `data/processed/cleaned_data.csv` for collinearity. The script should automatically switch to a fixed-effects model if random effects cause singular fit.
- **Outlier Threshold Error**: Verify that `code/analysis.py` sweeps the thresholds {2.5, 3.0, 3.5} correctly.