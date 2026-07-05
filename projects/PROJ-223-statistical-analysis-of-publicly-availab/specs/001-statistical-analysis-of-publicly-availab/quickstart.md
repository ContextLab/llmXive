# Quickstart: Statistical Analysis of Publicly Available Traffic Accident Data

## Prerequisites

- Python 3.11+
- `pip` package manager
- Access to GitHub Actions (for CI execution)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd specs/001-statistical-analysis-of-publicly-available-traffic-accident-data
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

The pipeline is executed sequentially via the provided scripts.

### Step 1: Data Ingestion
Downloads and merges raw data. Includes schema validation for FARS and NOAA.
```bash
python code/01_data_ingestion.py
```
*Output*: `data/processed/merged_data.csv`

### Step 2: Preprocessing
Handles missing data via MICE and encodes data.
```bash
python code/02_preprocessing.py
```
*Output*: `data/processed/preprocessed_data.csv`

### Step 3: Model Fitting
Fits the regression model (Ordinal, Multinomial, or Penalized GLM).
```bash
python code/03_model_fitting.py
```
*Output*: `output/models/model_results.pkl`

### Step 4: Diagnostics
Runs VIF, LRT, CRSE, and Sensitivity Analysis (MDE).
```bash
python code/04_diagnostics.py
```
*Output*: `output/reports/diagnostics.json`

### Step 5: Visualization
Generates plots and tables.
```bash
python code/05_visualization.py
```
*Output*: `output/plots/`

## Verification

To verify the pipeline on a small dataset:
1. Run the `tests/test_data_ingestion.py` unit tests.
2. Check `output/reports/diagnostics.json` for the `convergence` flag and `mde` value.
3. Ensure `output/plots/` contains `coefficient_plot.png` and `odds_ratio_table.png`.

## Troubleshooting

- **Memory Error**: If the pipeline fails due to memory, reduce the sampling ratio in `02_preprocessing.py`.
- **Model Non-Convergence**: Check `output/reports/diagnostics.json` for the `fallback_model` flag. If true, the system switched to Multinomial Logistic Regression or Penalized GLM.
- **Data Mismatch**: If the ingestion step fails, verify that the FARS dataset URL in `research.md` points to valid traffic data and that the NOAA schema matches.
- **Missing Weather Data**: If imputation fails, check `data/processed/preprocessed_data.csv` for NaN values. Ensure the MICE parameters are appropriate for the dataset size.
