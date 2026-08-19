# Quick Start Guide

This guide provides instructions to set up and run the code complexity and bug prediction pipeline for the llmXive project **PROJ-038**.

## Prerequisites

- Python 3.11+ installed
- `defects4j` CLI tool (installed via `setup_cli.sh`)
- PMD (Java static analysis tool) (installed via `setup_cli.sh`)
- Sufficient disk space (~10GB+) and RAM (7GB+) for data ingestion

## Setup

1. **Clone the repository** and navigate to the project root.

2. **Initialize the Python environment**:
 ```bash
 python3.11 -m venv venv
 source venv/bin/activate
 ```

3. **Install Python dependencies**:
 ```bash
 pip install --upgrade pip
 pip install -r code/requirements.txt
 ```

4. **Install system tools** (Defects4J and PMD):
 ```bash
 chmod +x code/setup_cli.sh
./code/setup_cli.sh
 ```
 *Note: This script installs `defects4j` and `pmd` and verifies their availability.*

5. **Verify environment setup**:
 Ensure `defects4j --version` and `pmd --version` return valid version strings.

## Running the Pipeline

The entire pipeline is orchestrated by `run_pipeline.sh`. This script executes the following stages in order:
1. **Ingest**: Downloads a subset of Defects4J projects.
2. **Metrics**: Calculates Cyclomatic Complexity, Halstead Volume, and LOC.
3. **Labeling**: Maps bug-introduction commits to file-level labels.
4. **Validation**: Ensures no NaN values in the resulting dataset.
5. **Analysis**: Computes correlations and trains baseline models.
6. **Reporting**: Generates final JSON reports and visualizations.

To run the full pipeline:

```bash
chmod +x code/run_pipeline.sh
./code/run_pipeline.sh
```

### Output Artifacts

Upon successful completion, the following files will be generated in the `code/data/` and `code/data/results/` directories:

- `code/data/processed/features.csv`: The main feature matrix with metrics and bug labels.
- `code/data/results/correlation_report.json`: Statistical correlation analysis results.
- `code/data/results/baseline_metrics.json`: Model performance metrics (ROC-AUC, F1).
- `code/data/results/feature_importance_ranking.json`: Ranked feature importance.
- `code/data/results/statistical_significance_report.json`: Paired permutation test results.
- `code/results/final_report.md`: Comprehensive summary of findings.

## Troubleshooting

- **Memory Errors**: The pipeline enforces a 7GB RAM limit. If you encounter memory errors, ensure no other heavy processes are running, or reduce the subset size in `code/src/config.py`.
- **Defects4J Errors**: Ensure the `DEFECTS4J_HOME` environment variable is correctly set if the CLI fails to locate the installation.
- **PMD Errors**: Verify that Java 11+ is installed and the `pmd` binary is in your `PATH`.

## Testing

Run the test suite to verify individual components:

```bash
pytest code/tests/ -v
```

## Next Steps

- Review `code/results/final_report.md` for insights.
- Analyze the `features.csv` for specific project patterns.
- Extend `code/src/analysis.py` for additional statistical tests.