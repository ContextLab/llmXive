# Quickstart Guide

This guide explains how to run the full analysis pipeline for investigating the validity of the equipartition theorem in driven granular systems.

## Prerequisites

- Python 3.11+
- Install dependencies: `pip install -r requirements.txt`

## Running the Pipeline

The pipeline is orchestrated by `code/main.py`. You can run specific stages or the full pipeline.

### Full Run

To run the entire pipeline from raw data ingestion to regression analysis:

```bash
python code/main.py --stage all --sample-ratio 0.1
```

This command will:
1. Generate checksums for raw data.
2. Ingest data (sampling 10% of rows for speed).
3. Run statistical analysis (KS and Chi-squared tests).
4. Run sensitivity analysis.
5. Run regression analysis.
6. Hash artifacts.

### Individual Stages

You can also run individual stages:

```bash
# Ingest data
python code/main.py --stage ingest --sample-ratio 0.1

# Run statistical analysis
python code/main.py --stage stats --alpha 0.01

# Run sensitivity analysis
python code/main.py --stage sensitivity --thresholds 0.01,0.05,0.10

# Run regression analysis
python code/main.py --stage regression
```

## Output Artifacts

After a successful run, you will find the following artifacts:

- `data/derived/energy_samples.csv`: Calculated energy components per particle.
- `artifacts/statistical_results.json`: Results of KS and Chi-squared tests.
- `artifacts/sensitivity_analysis_report.json`: Sensitivity analysis results.
- `artifacts/regression_results.json`: Regression model parameters.

## Troubleshooting

- **Missing Data**: Ensure `data/raw/` contains valid CSV files with the required columns (`particle_id`, `x`, `y`, `z`, `theta`, `timestamp`).
- **Configuration Errors**: Check `data/config.yaml` for valid material properties and frequency bins.
- **Memory Issues**: Use `--sample-ratio` to reduce data size if running out of memory.
