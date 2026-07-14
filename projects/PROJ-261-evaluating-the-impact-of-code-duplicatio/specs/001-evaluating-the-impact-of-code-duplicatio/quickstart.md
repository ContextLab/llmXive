# Quickstart Guide

This document outlines the commands required to run the full analysis pipeline
for the *Evaluating the Impact of Code Duplication on LLM Code Understanding*
project.

## Prerequisites

- Python 3.11
- All dependencies installed via `pip install -r requirements.txt`
- Internet access (required for dataset streaming)

## Step‑by‑step execution

1. **Download a sample of the GitHub code dataset**
 ```bash
 python code/data_loader.py
 ```

2. **Run the PII scanner** (optional, can be disabled in `config.py`)
 ```bash
 python code/pii_scanner.py
 ```

3. **Compute clone density**
 ```bash
 python code/ast_cloner.py
 ```

4. **Compute model perplexity scores**
 ```bash
 python code/model_metrics.py
 ```

5. **Run bug‑detection evaluation**
 ```bash
 python code/bug_detection.py
 ```

6. **Perform correlation analysis and save results**
 ```bash
 python code/correlation_analysis.py
 ```

7. **Generate visualizations**
 ```bash
 python code/visualization/plotting.py
 ```

8. **Validate that all expected output files are present**
 ```bash
 python code/quickstart_validation.py
 ```

After step 6 the file `data/analysis/correlation_results.csv` will be created,
containing the Spearman correlation coefficients and p‑values required by the
research claims.

## Notes

- The scripts are idempotent; re‑running them will overwrite previous results.
- All intermediate and final artifacts are recorded in the checksum manifest
 via `code/checksum_manifest.py`.
- Logging output is written to the console and to the appropriate CSV files
 (e.g., `data/parse_failures.csv`).