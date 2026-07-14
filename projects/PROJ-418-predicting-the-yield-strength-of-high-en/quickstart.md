# Quick Start Guide: HEA Yield Strength Prediction

This guide walks you through the execution of the HEA yield strength prediction pipeline, from environment setup to final report generation.

## 1. Environment Setup

```bash
# Ensure Python 3.9+ is installed
python --version

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## 2. Configuration

Before running the pipeline, you must configure the verified dataset URL.

1. Open `code/utils/config.py`.
2. Locate the `RESEARCH_VERIFIED_DATASETS` dictionary.
3. Add or update the `hea_compositions` key with a valid, accessible URL to the HEA dataset (e.g., a CSV file hosted on a secure server or a direct download link).

**Note:** The pipeline will terminate immediately with error code `DATA_SOURCE_MISSING` if this URL is not configured or unreachable.

## 3. Running the Pipeline

The pipeline executes in three main phases corresponding to the User Stories.

### Phase 1: Data Acquisition & Descriptor Engineering (US1)

This phase downloads the raw data, filters for single-phase room-temperature alloys, normalizes units, and calculates compositional descriptors.

```bash
# Run the pipeline orchestrator
python code/data/pipeline.py
```

**Outputs:**
- `data/processed/hea_descriptors.csv`: The processed dataset with all descriptors.
- `output/data_status.json`: Status report including sample count and power warnings.

### Phase 2: Model Training & Evaluation (US2)

This phase trains Linear Regression, Random Forest, and Gradient Boosting models with hyperparameter tuning and evaluates them on a hold-out test set.

```bash
# Run the training pipeline
python code/models/train.py

# Run the evaluation pipeline
python code/models/evaluate.py
```

**Outputs:**
- `output/metrics.json`: R², MAE, RMSE for all models.
- `output/power_analysis.json`: Sample size and power status.

### Phase 3: Statistical Validation & Reporting (US3)

This phase performs permutation testing, bootstrap resampling, VIF diagnostics, and generates the final research report.

```bash
# Run the evaluation pipeline (includes validation steps)
python code/models/evaluate.py

# Generate the final report
python code/models/report_generator.py
```

**Outputs:**
- `output/report.md`: Comprehensive research report with all statistical results and disclaimers.
- `output/plots/`: Generated figures with disclaimers.

## 4. Verification

After running the pipeline, verify the outputs:

1. Check `output/metrics.json` for model performance.
2. Check `output/power_analysis.json` to ensure sample size is sufficient (N ≥ 50).
3. Review `output/report.md` for the final analysis and mandatory disclaimers.

## Troubleshooting

- **Error: DATA_SOURCE_MISSING**: The verified dataset URL is missing in `code/utils/config.py`.
- **Error: ImportError**: Ensure all `__init__.py` files are present and dependencies are installed.
- **Low Power Warning**: If `N < 50`, statistical tests (permutation, bootstrap) will be skipped, and `output/power_analysis.json` will reflect `status: 'insufficient_power'`.

## Next Steps

For detailed API documentation, refer to the docstrings in the `code/` modules. For development tasks, see `tasks.md`.
