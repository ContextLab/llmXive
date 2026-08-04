# Quickstart: The Influence of Simulated Social Status on Risk-Taking Behavior

## 1. Prerequisites

- Python 3.11+
- `pip` or `conda`
- Access to a terminal (local or GitHub Actions)

## 2. Installation

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

## 3. Running the Pipeline

### Step 1: Generate Synthetic Data
```bash
python code/generate_data.py --seed 42 --mode recovery --output data/raw/simulated_data.csv
```
*Output*: `data/raw/simulated_data.csv` (or directly to processed if configured).

### Step 2: Preprocess and Detect Types
```bash
python code/preprocess.py --input data/raw/simulated_data.csv --output data/processed/cleaned_data.csv
```
*Output*: `data/processed/cleaned_data.csv`, `data/processed/outcome_type.json`, `data/processed/design_type.json`, `data/processed/simulation_parameters.json`.

### Step 3: Fit Adaptive Model & Sensitivity Analysis
```bash
python code/analysis.py --data data/processed/cleaned_data.csv --config data/processed/model_config.json
```
*Output*: `data/processed/model_results.json`, `data/processed/sensitivity_results.json`, `data/processed/vif_scores.json`, `data/processed/stability_metric.json`.

### Step 4: Generate Report
```bash
python code/reporting.py --results data/processed/model_results.json --sensitivity data/processed/sensitivity_results.json --output report/final_report.pdf
```
*Output*: `report/final_report.pdf`, `report/forest_plot.png`.

### Step 5: Update State Hashes
```bash
python code/hash_update.py
```
*Output*: Updates `state/projects/PROJ-423-...yaml` with content hashes.

## 4. Verification

- Check `data/processed/cleaned_data.csv` for expected columns.
- Verify `data/processed/model_results.json` contains the interaction term p-value and `ci_width`.
- Confirm `data/processed/stability_metric.json` indicates stability.
- Confirm `report/final_report.pdf` includes the forest plot.

## 5. Troubleshooting

- **Missing dependencies**: Ensure `requirements.txt` is installed in the active venv.
- **Memory errors**: Reduce `--n_subjects` in `generate_data.py`.
- **Model convergence**: Check `data/processed/vif_scores.json` for collinearity (>5.0).
- **Bootstrap failure**: If bootstrap fails, the system logs a warning and uses asymptotic errors (flagged in report).