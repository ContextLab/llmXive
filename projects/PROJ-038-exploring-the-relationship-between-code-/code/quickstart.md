# Quickstart Guide: Code Complexity & Bug Prediction Pipeline

This guide provides instructions to set up and run the automated research pipeline for exploring the relationship between code complexity metrics and bug prediction accuracy.

## Prerequisites

- **Python 3.11+** installed on your system.
- **Java Development Kit (JDK) 11+** required for PMD and JavaParser tools.
- **System Tools**: `wget`, `curl`, `git`, `unzip`.
- **Memory**: At least 8GB RAM recommended for processing the Defects4J dataset subset.

## Setup Instructions

1. **Clone the Repository** (if not already done):
 ```bash
 git clone <repository-url>
 cd PROJ-038-exploring-the-relationship-between-code-
 ```

2. **Run the Setup Script**:
 The setup script creates the necessary directory structure, installs Python dependencies, and configures system tools (PMD, Defects4J CLI).
 ```bash
 cd code
 chmod +x setup_structure.sh
./setup_structure.sh
 ```
 *Note: Ensure you have `sudo` privileges if installing system tools like PMD.*

3. **Activate the Virtual Environment**:
 ```bash
 source.venv/bin/activate
 ```

4. **Verify Configuration**:
 Ensure the `specs/001-code-complexity-bug-prediction/amendment_ratified.md` file exists. The pipeline will halt if this constitutional artifact is missing.
 ```bash
 ls -l../specs/001-code-complexity-bug-prediction/amendment_ratified.md
 ```

## Running the Pipeline

Execute the main orchestration script from the `code/` directory:

```bash
cd code
./run_pipeline.sh
```

### Execution Flow
The script performs the following steps in order:
1. **Constitutional Check**: Verifies the amendment artifact.
2. **Ingestion**: Downloads a subset of Defects4J projects (limited by RAM).
3. **Metrics Extraction**: Calculates Cyclomatic Complexity (PMD), Halstead Volume (JavaParser), and LOC.
4. **Labeling**: Cross-references commits to label buggy files.
5. **Validation**: Ensures no NaN values and correct schema.
6. **Analysis & Modeling**: Computes correlations and trains baseline models.
7. **Reporting**: Generates final JSON and Markdown reports.

## Expected Output Paths

Upon successful completion, the following artifacts will be generated:

| Artifact | Path | Description |
|:--- |:--- |:--- |
| **Feature Matrix** | `code/data/processed/features.csv` | CSV with metrics (`cc`, `halstead`, `loc`) and bug label (`is_buggy`). |
| **Correlation Report** | `code/data/results/correlation_report.json` | Point-Biserial and Spearman correlations with p-values. |
| **Baseline Metrics** | `code/data/results/baseline_metrics.json` | Mean ROC-AUC and F1 scores from Repeated 5-Fold CV. |
| **Statistical Significance** | `code/data/results/statistical_significance_report.json` | Paired Permutation Test results (p-value). |
| **Feature Importance** | `code/data/results/feature_importance_ranking.json` | Ranked importance weights from Random Forest. |
| **Final Report** | `code/results/final_report.md` | Comprehensive summary of all findings. |

## Error Handling & Troubleshooting

### "ConstitutionalBlockError: Amendment not ratified"
- **Cause**: The file `specs/001-code-complexity-bug-prediction/amendment_ratified.md` is missing.
- **Fix**: Contact the governance body to ratify the amendment or verify the file path.

### "DataFetchError: Defects4J CLI not found"
- **Cause**: The `defects4j` command is not in your system PATH.
- **Fix**: Re-run `./setup_cli.sh` or manually install Defects4J v2.0+.

### "Memory Limit Exceeded"
- **Cause**: The ingestion step attempted to load more data than the configured RAM limit.
- **Fix**: The pipeline automatically reduces the project subset size. If it fails completely, increase the `MEMORY_LIMIT_GB` environment variable in `code/src/config.py` or ensure you are running on a machine with sufficient RAM.

### "PMD Syntax Error"
- **Cause**: A Java file in the dataset could not be parsed by PMD.
- **Fix**: These files are logged and skipped. Check `code/data/logs/ingest.log` for specific file paths.

## Running Tests

To verify the implementation:
```bash
cd code
source.venv/bin/activate
pytest tests/ -v
```

## Notes
- The pipeline uses a **random seed of 42** for all stochastic processes to ensure reproducibility.
- No synthetic data is generated; all analysis is performed on real Defects4J data.
- If the pipeline fails mid-execution, you can often resume by re-running `./run_pipeline.sh` as it checks for existing artifacts, though a clean run is recommended for consistency.