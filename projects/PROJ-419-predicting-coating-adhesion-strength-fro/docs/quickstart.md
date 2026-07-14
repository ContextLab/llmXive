# Quick Start Guide: Predicting Coating Adhesion Strength

This guide provides the essential steps to set up and run the coating adhesion prediction pipeline.

## Prerequisites

- Python 3.11+
- pip (package manager)
- Access to the internet (for fetching real data from Materials Project and NIST repositories)

## Installation

1. Clone the repository:
 ```bash
 git clone <repository-url>
 cd <project-directory>
 ```

2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

3. Verify installation:
 ```bash
 python -c "import pandas, sklearn, shap; print('All dependencies installed successfully.')"
 ```

## Configuration

Before running the pipeline, ensure the following:
- The `state/` directory exists (created automatically by `code/setup_directories.py` if missing).
- Data source URLs are valid and accessible (verified by T009, T010).
- If data sources are missing, the pipeline will halt with a `state/HALT_SIGNAL.yaml` file.

## Running the Pipeline

Execute the main pipeline script:

```bash
python code/main.py
```

This script will:
1. Check for halt signals.
2. Fetch and ingest data from Materials Project and NIST repositories.
3. Preprocess and align the data.
4. Train predictive models (Gradient Boosting and Random Forest).
5. Evaluate model performance and generate SHAP rankings.
6. Output results to `data/processed/` and `results/`.

## Output Files

After successful execution, you will find:
- `data/processed/coating_adhesion_dataset.csv`: Unified, cleaned dataset.
- `results/model_performance.json`: Model metrics (R², RMSE, MAE).
- `results/feature_importance.json`: SHAP-based feature rankings.
- `results/statistical_comparison.json`: Baseline comparison results.

## Troubleshooting

### Data Access Issues
If the pipeline halts with "Data Gap: Missing Verified Sources", check:
- Internet connectivity.
- API keys (if required for specific data sources).
- Validity of URLs in `code/utils.py`.

### Memory Errors
If you encounter memory errors:
- Reduce `MAX_ROWS` in `code/__init__.py`.
- Ensure your system has at least 7GB of available RAM (as per `RAM_LIMIT_GB`).

### Validation Failures
If the pipeline halts due to validation failures:
- Check `exclusion_ratio` (must be < 10%).
- Check `processing_success_rate` (must be ≥ 95%).
- Review logs for specific exclusion reasons.

## Next Steps

- Explore `docs/data-model.md` for detailed schema information.
- Review `specs/001-predicting-coating-adhesion/` for full feature specifications.
- Run unit tests: `pytest tests/`
