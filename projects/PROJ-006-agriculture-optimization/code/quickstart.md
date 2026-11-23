# Quickstart Guide: Climate-Smart Agriculture Optimization Pipeline

This guide details how to run the full pipeline to generate the analysis dataset, regression results, and final report.

## Prerequisites

- Python 3.9+
- Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Running the Pipeline

The pipeline is orchestrated by `src/cli/run_pipeline.py`. It supports different stages and synthetic data generation for structural validation.

### Full Execution (Recommended)

To run the entire pipeline (Ingest -> Analysis -> Report) with synthetic data fallback if real data is missing:

```bash
export CI=true
python src/cli/run_pipeline.py --stage full
```

This command will:
1. Validate citations in `research.md`.
2. Check for real data. If missing and `CI=true`, generate synthetic data.
3. Run the ingestion stage (Survey Collector -> Spatial Join -> Feature Engineering).
4. Run the analysis stage (Regression).
5. Run the sensitivity analysis and report generation.

### Individual Stages

#### Ingestion Stage
```bash
python src/cli/run_pipeline.py --stage ingest
```
Produces: `data/processed/analysis_dataset.csv`

#### Analysis Stage
```bash
python src/cli/run_pipeline.py --stage analysis
```
Requires: `data/processed/analysis_dataset.csv`
Produces: `data/processed/regression_results.json`

#### Report Stage
```bash
python src/cli/run_pipeline.py --stage report
```
Requires: `data/processed/regression_results.json`
Produces: `reports/final_report.pdf`

## Expected Artifacts

After a successful run, the following files should exist:

- `data/processed/analysis_dataset.csv`
- `data/processed/regression_results.json`
- `data/logs/linkage_validation.json`
- `reports/final_report.pdf`

## Troubleshooting

- **Citation Validation Failed**: Ensure `research.md` contains valid DOIs.
- **Missing Data**: If `CI=true` is not set and real data is missing, the pipeline will fail. Set `CI=true` to enable synthetic fallback.
- **Logging**: Check `data/logs/pipeline.log` for detailed error messages.
