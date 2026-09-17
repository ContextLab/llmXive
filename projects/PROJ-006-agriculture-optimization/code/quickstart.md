# Quickstart Guide: Climate-Smart Agriculture Optimization Pipeline

## Prerequisites

- Python 3.9+
- pip
- (Optional) Docker for containerized execution

## Installation

1. Clone the repository and navigate to the project root:
 ```bash
 git clone <repo-url>
 cd llmXive/projects/PROJ-006-agriculture-optimization
 ```

2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Execution

The pipeline is orchestrated by `src/cli/run_pipeline.py`. It supports three stages:

- `--stage ingest`: Run data collection, spatial join, and feature engineering.
- `--stage analysis`: Run regression analysis and sensitivity checks.
- `--stage full`: Run the entire pipeline (ingest + analysis).

### Running the Full Pipeline

```bash
python src/cli/run_pipeline.py --stage full
```

If real data is unavailable, the pipeline will automatically invoke the structural validation generator (T010) to create synthetic data for testing, provided `CI=true` is set.

### Running with Synthetic Data (Local Testing)

```bash
export CI=true
python src/cli/run_pipeline.py --stage full
```

### Running Individual Stages

**Ingest Stage:**
```bash
python src/cli/run_pipeline.py --stage ingest
```
This runs:
- `src/data/collectors/survey_collector.py`
- `src/data/collectors/remote_sensing_collector.py`
- `src/data/processing/spatial_join.py`
- `src/data/processing/feature_engineering.py`
- `src/data/processing/final_assembly.py` (T017d)

**Analysis Stage:**
```bash
python src/cli/run_pipeline.py --stage analysis
```
This runs:
- `src/analysis/run_regression.py`
- `src/analysis/sensitivity_check.py`
- `src/services/report_generator.py`

## Validation

Validate the final dataset:
```bash
python src/cli/validate.py --schema-type dataset data/processed/analysis_dataset.csv
```

Validate regression results:
```bash
python src/cli/validate.py --schema-type regression data/processed/regression_results.json
```

## Output Artifacts

The pipeline generates the following key artifacts:

- `data/processed/analysis_dataset.csv`: Final analysis-ready dataset.
- `data/processed/regression_results.json`: Regression coefficients, p-values, VIF scores.
- `reports/final_report.pdf`: Comprehensive report with sensitivity analysis and disclaimers.
- `data/logs/linkage_validation.json`: Spatial join validation metrics.

## Troubleshooting

- **Citation Validation Failed**: Ensure `research.md` contains valid citations with DOIs. Run `python src/cli/validate_citations.py` to debug.
- **Missing Data**: If real data is missing and `CI=false`, the pipeline will fail. Set `CI=true` to enable synthetic fallback.
- **Schema Validation Errors**: Check `contracts/dataset.schema.yaml` for required columns.

## CI/CD

The pipeline is tested in CI via `.github/workflows/ci.yml`. The CI job runs:
```bash
export CI=true
python src/cli/run_pipeline.py --stage full
```