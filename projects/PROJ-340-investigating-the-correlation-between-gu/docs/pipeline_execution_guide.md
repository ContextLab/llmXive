# Pipeline Execution Guide

This guide provides detailed instructions for executing the PROJ-340 analysis pipeline.

## 1. Execution Modes

The pipeline supports two primary modes:

### Real Data Mode (Default)
- **Purpose**: Production analysis on verified real data.
- **Behavior**: Fetches data from `data/config/real_data_sources.yaml`. Fails loudly if data is missing or invalid. No synthetic fallback.
- **Command**:
 ```bash
 python code/main.py --output data/results/
 ```

### Synthetic Mode (Testing)
- **Purpose**: Local validation of pipeline logic.
- **Behavior**: Generates synthetic data using `code/generate_synthetic_data.py`.
- **Command**:
 ```bash
 python code/generate_synthetic_data.py --output data/raw/synthetic_test_data.csv
 python code/main.py --input data/raw/synthetic_test_data.csv --output data/results/
 ```

## 2. Step-by-Step Execution

### Step 1: Data Ingestion & Validation
- **Script**: `code/ingest.py` (called internally by `main.py`)
- **Tasks**:
 - Fetch data (real or synthetic).
 - Validate required variables against `data/config/required_variables.yaml`.
 - Detect and report outliers (IQR method).
 - Filter outliers and save `data/processed/filtered_data.parquet`.
 - Generate `data/results/outlier_report.json`.

### Step 2: Analysis
- **Script**: `code/analysis.py` (called internally by `main.py`)
- **Tasks**:
 - Check data distribution (normality, zero-inflation).
 - Select correlation method (Pearson, Spearman, ZINB).
 - Run correlation analysis.
 - Apply Benjamini-Hochberg FDR correction.
 - Save `data/results/correlation_results.csv` and `data/metadata/method_selection_log.json`.

### Step 3: Diagnostics
- **Script**: `code/diagnostics.py` (called internally by `main.py`)
- **Tasks**:
 - Detect perfect multicollinearity.
 - Calculate VIF for remaining predictors.
 - Run power analysis.
 - Run sensitivity analysis across p-value thresholds.
 - Save `data/results/vif_report.json`, `power_analysis_report.json`, `sensitivity_analysis.csv`.

### Step 4: Reporting
- **Script**: `code/report.py` (called internally by `main.py`)
- **Tasks**:
 - Generate `data/results/report_draft.md`.
 - Scan for causal language.
 - Save `data/results/causal_scan_report.json`.

## 3. Output Artifacts

| Artifact | Path | Description |
|----------|------|-------------|
| Filtered Data | `data/processed/filtered_data.parquet` | Cleaned dataset with outliers removed. |
| Correlation Results | `data/results/correlation_results.csv` | Main statistical outputs. |
| Outlier Report | `data/results/outlier_report.json` | Details of excluded data points. |
| Method Selection Log | `data/metadata/method_selection_log.json` | Log of chosen statistical methods. |
| Power Analysis | `data/results/power_analysis_report.json` | Statistical power metrics. |
| Sensitivity Analysis | `data/results/sensitivity_analysis.csv` | Stability of findings across thresholds. |
| Causal Scan Report | `data/results/causal_scan_report.json` | Verification of no causal language. |
| Final Report | `data/results/report_draft.md` | Human-readable interpretation. |

## 4. Error Handling

- **RealDataFetchError**: Raised if the real data source is unreachable.
- **MissingVariableError**: Raised if required predictors/outcomes are missing.
- **CausalLanguageError**: Raised if prohibited terms are found in reports.
- **TimeoutError**: Raised if the pipeline exceeds the 6-hour limit.

## 5. Verification

After execution, run the integrity check:
```bash
python scripts/verify_integrity.py
```
This script verifies checksums of all artifacts against `state/projects/PROJ-340-investigating-the-correlation-between-gu.yaml`.
