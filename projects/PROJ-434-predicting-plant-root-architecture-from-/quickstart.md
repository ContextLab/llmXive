# Quickstart Guide: Predicting Plant Root Architecture from Soil Nutrient Profiles

This guide provides step-by-step instructions to set up the environment, run the data ingestion pipeline, train models, and generate reports.

## Prerequisites

- Python 3.9+
- `pip` package manager
- Access to the internet (for data fetching)
- (Optional) API keys for specific data providers if required by `research.md`

## 1. Setup Environment

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Configure Environment Variables

Create a `.env` file in the project root based on the template (if provided) or set the following variables:

```bash
# Run Mode: 'production' (default) or 'test'
export RUN_MODE=production
```

*Note: In `production` mode, the pipeline will fail if real data cannot be fetched. In `test` mode, it uses synthetic data for structural validation.*

## 2. Initialize Project Structure

Ensure the directory structure exists:

```bash
python code/setup_directories.py
```

This creates `code/`, `data/`, `data/raw`, `data/processed`, `data/logs`, `tests/`, `artifacts/`, and `figures/`.

## 3. Verify Data Sources (Optional but Recommended)

Before running the full pipeline, verify that the external data sources listed in `specs/001-predict-root-architecture/research.md` are accessible:

```bash
python code/ingestion/source_validation.py
```

This logs the status of all sources to `data/logs/source_validation.log`.

## 4. Run the Full Pipeline

Execute the main pipeline script to run ingestion, modeling, and reporting:

```bash
python code/main.py
```

**What this script does:**
1. **Ingestion**: Fetches root trait data and SoilGrids data, merges them, and filters for valid species.
2. **Modeling**: Trains Random Forest models (Soil-Only and Soil+Species) using Stratified 5-Fold CV and LOSO.
3. **Validation**: Runs permutation tests to validate SC-002 compliance.
4. **Reporting**: Generates feature importance plots and sensitivity analysis reports.

**Expected Outputs:**
- `data/processed/merged_dataset.csv`: The final unified dataset.
- `artifacts/model_metrics.json`: Performance metrics (R², RMSE).
- `artifacts/sc002_status.json`: Pass/Fail status for statistical significance.
- `figures/feature_importance.png`: Visualization of feature importance.
- `artifacts/sensitivity_report.md`: Final analysis report.

## 5. Inspect Results

- **Metrics**: Open `artifacts/model_metrics.json` to view model performance.
- **Logs**: Check `data/logs/` for execution details and error logs.
- **Reports**: Read `artifacts/sensitivity_report.md` for the final scientific justification.

## Troubleshooting

- **Data Fetch Errors**: Ensure `RUN_MODE=production` is set correctly and you have internet access. If a specific source fails, check `data/logs/source_validation.log`.
- **Missing Dependencies**: Re-run `pip install -r requirements.txt`.
- **Timeout**: If the pipeline exceeds the 6-hour limit, check `data/logs/timing.log` for stage-specific timing.

## References

- See `specs/001-predict-root-architecture/research.md` for dataset citations and community standards.
- See `docs/architecture.md` (if available) for system design details.
