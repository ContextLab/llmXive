# Quickstart: Exploring the Relationship Between Code Complexity Metrics and Bug Prediction Accuracy

## Prerequisites

* **Python**: 3.11+
* **Java**: JDK 11+ (required for Defects4J and PMD)
* **Git**: Installed and configured
* **Memory**: Minimum 8 GB RAM recommended (though pipeline targets 7 GB)
* **Disk**: Minimum 10 GB free space

## Installation

1. **Clone the Repository**:
 ```bash
 git clone https://github.com/your-org/your-repo.git
 cd your-repo
 ```

2. **Create Virtual Environment**:
 ```bash
 python -m venv.venv
 source.venv/bin/activate # On Windows:.venv\Scripts\activate
 ```

3. **Install Dependencies**:
 ```bash
 pip install -r code/requirements.txt
 ```

4. **Install Defects4J CLI**:
 Follow the official instructions at ` to install the `defects4j` command-line tool globally or in the project path.

## Running the Pipeline

Execute the full end-to-end pipeline:

```bash
./code/run_pipeline.sh
```

This script performs the following steps in order:
1. **Ingest**: Clones Defects4J, selects 5-10 projects, and extracts source code.
2. **Metrics**: Calculates Cyclomatic Complexity, Halstead Volume, and LOC for all files.
3. **Label**: Tags files as buggy/clean based on commit history.
4. **Analyze**: Runs correlation analysis (including VIF), baseline modeling, and Sign-Flip Permutation Test.
5. **Report**: Generates `correlation_report.json`, `model_results.csv`, and `output.json`.

## Expected Outputs

After successful execution, check the `code/data/results/` directory:

* `features.csv`: The labeled feature matrix.
* `exclusions.log`: Log of files skipped (syntax errors, etc.).
* `correlation_report.json`: Correlation coefficients, p-values, VIF, and partial correlations.
* `model_results.csv`: Model performance metrics (ROC-AUC, F1).
* `output.json`: Final results including the `p_value` for SC-003.

## Troubleshooting

* **Memory Error**: If the pipeline fails with OOM, reduce the number of selected projects in `code/src/config.py` (variable `MAX_PROJECTS`).
* **Java Errors**: Ensure `JAVA_HOME` is set correctly and points to JDK 11+.
* **Defects4J Missing**: Verify that the `defects4j` command is in your `PATH`.
