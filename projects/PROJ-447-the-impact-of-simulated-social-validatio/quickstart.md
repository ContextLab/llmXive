# Quickstart Guide

## 1. Setup

Ensure you have Python 3.11+ installed.

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## 2. Run the Pipeline

From the project root:

```bash
cd code
python main.py
```

This will:
1. Attempt to load real data (fails if none available).
2. Generate synthetic data using SEM.
3. Validate data integrity.
4. Run regression analysis.
5. Perform robustness checks.
6. Generate diagnostic plots.

## 3. Check Outputs

Results are saved in `data/processed/`:
- `pipeline_data.csv`: Processed data with PSV scores.
- `model_results.json`: Regression coefficients and VIF results.
- `sensitivity_analysis.json`: Sensitivity analysis results.
- `scatter_plot.png`, `residuals.png`: Diagnostic plots.
- `pipeline_run_log.json`: Execution log.

## 4. Verification

Ensure all linting passes:
```bash
ruff check code/
black --check code/
```

Run tests:
```bash
pytest tests/
```