# Quickstart: Predicting the Yield Strength of Steel Alloys

## Prerequisites

- Python 3.11+
- Git
- 6 GB RAM available (for CI or local run)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-210-predicting-the-yield-strength-of-steel-a
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

The pipeline is orchestrated via `code/main.py`.

### 1. Ingest and Preprocess Data
This step fetches data (or uses local cache), cleans it, and engineers features.
```bash
python code/main.py --step ingest
```
- **Output**: `data/processed/engineered_dataset.parquet`
- **Note**: If no verified dataset is found in the `# Verified datasets` block, this step will exit with a 'Data Source Missing' error. Literature mining is not performed.

### 2. Train Models
Trains GAM, Linear, RF, and XGBoost models with 10-fold repeated CV (if N < 500) or 5-fold CV.
```bash
python code/main.py --step train
```
- **Output**: `data/results/model_metrics.json`, `data/results/shap_values.pkl`

### 3. Validate Interactions
Runs nested permutation tests (with constant spline complexity) and generates PDPs.
```bash
python code/main.py --step validate
```
- **Output**: `data/results/pdp_plots/`, `data/results/significance_report.json`

### 4. Sensitivity Analysis
Sweeps p-value thresholds and computes stability metrics (Kuncheva index).
```bash
python code/main.py --step sensitivity
```
- **Output**: `data/results/sensitivity_report.json`

## Verification

To verify the pipeline on a small subset (for testing):
```bash
python code/main.py --step test --subset 50
```
This runs the full pipeline on 50 rows to ensure no crashes occur.

## Troubleshooting

- **Memory Error**: Reduce `MAX_ROWS` in `code/utils/config.py` to 5000.
- **Missing Data**: Check `data/raw/` for downloaded files. If empty, verify network access. If no verified source exists, the build will fail (as per Constitution Principle I).
- **GPU Error**: Ensure `XGB_USE_GPU=False` in config (default is CPU).