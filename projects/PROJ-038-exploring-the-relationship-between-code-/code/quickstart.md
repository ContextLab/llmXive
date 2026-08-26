# Quickstart Guide: Code Complexity vs Bug Prediction Pipeline

This guide provides instructions to set up and run the automated research pipeline for exploring the relationship between code complexity metrics and bug prediction accuracy.

## Prerequisites

- **Python 3.11+** installed on your system.
- **Java JDK 11+** (required for PMD and custom Halstead calculation).
- **Git** installed and available in PATH.
- Sufficient disk space (~10GB) and RAM (minimum 8GB recommended).

## Step 1: Clone and Setup Environment

1. Navigate to the project root directory.
2. Create a Python virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```
3. Install Python dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```

## Step 2: Install System Tools

Run the setup script to install required CLI tools (Defects4J and PMD):

```bash
bash code/setup_cli.sh
```

This script verifies the installation of:
- `defects4j` (for bug dataset access)
- `pmd` (for Cyclomatic Complexity calculation)

Ensure both commands return valid version numbers:
```bash
defects4j --version
pmd --version
```

## Step 3: Configure Paths (Optional)

If your tools are installed in non-standard locations, set the following environment variables before running the pipeline:

```bash
export DEFECTS4J_HOME=/path/to/defects4j
export PMD_HOME=/path/to/pmd
```

## Step 4: Run the Pipeline

Execute the main orchestration script:

```bash
bash code/run_pipeline.sh
```

### Pipeline Stages
The script executes the following stages in order:
1. **Ingest**: Downloads a subset of Defects4J projects (limited by RAM).
2. **Metrics**: Calculates LOC, Cyclomatic Complexity (CC), and Halstead Volume.
3. **Labeling**: Cross-references commits to label buggy files.
4. **Validation**: Ensures no NaN values and validates schema.
5. **Analysis**: Computes correlations and trains baseline models.
6. **Modeling**: Runs statistical significance tests (Paired Permutation).
7. **Reporting**: Generates final JSON and Markdown reports.

## Step 5: Verify Outputs

Upon successful completion, check the `code/data/results/` directory for:
- `features.csv`: The processed dataset with metrics and labels.
- `correlation_report.json`: Point-Biserial and Spearman correlation results.
- `baseline_metrics.json`: Model performance (ROC-AUC, F1) across folds.
- `statistical_significance_report.json`: Permutation test p-values.
- `final_report.md`: Comprehensive summary of findings.

## Troubleshooting

- **Memory Errors**: The pipeline automatically limits data ingestion based on available RAM. If you encounter errors, reduce the `MAX_MEMORY_BYTES` in `code/src/config.py`.
- **Defects4J Issues**: Ensure `DEFECTS4J_HOME` is set correctly and `defects4j` is in your PATH.
- **Java Errors**: Verify that `java` and `javac` are accessible and compatible with the project requirements.

## Next Steps

- Review `specs/001-code-complexity-bug-prediction/methodology_rationale.md` for statistical justification.
- Examine `code/data/results/final_report.md` for detailed analysis.
- Extend `code/src/modeling.py` to test additional algorithms.