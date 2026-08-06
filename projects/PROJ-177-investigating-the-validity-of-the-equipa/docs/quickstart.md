# Quick Start Guide

This guide describes how to run the granular system analysis pipeline end-to-end.

## Prerequisites

- Python 3.11+
- Dependencies installed via `pip install -r requirements.txt`
- A valid dataset ID configured in `data/config.yaml` (see T062)

## Running the Pipeline

The main entry point is `code/main.py`. It supports specific pipeline stages via the `--stage` flag.

### Step 1: Ingestion

Ingest raw particle tracking and driving signal data, compute energy components, and output `data/derived/energy_samples.csv`.

```bash
python code/main.py --stage ingest --sample-ratio 0.1
```

*Note: The `--sample-ratio` flag is optional. If omitted, the script uses the full dataset or applies default sampling rules defined in `data/config.yaml`.*

### Step 2: Statistical Analysis

Perform KS and Chi-squared tests on the energy data.

```bash
python code/main.py --stage stats --alpha 0.01
```

### Step 3: Sensitivity Analysis

Run sensitivity sweeps on significance thresholds.

```bash
python code/main.py --stage sensitivity --thresholds 0.01,0.05,0.10
```

### Step 4: Regression Analysis

Perform regression to relate deviation magnitude to driving frequency and material roughness.

```bash
python code/main.py --stage regression
```

### Full Run

Execute the entire pipeline (Ingestion -> Stats -> Sensitivity -> Regression -> Hashing) in one command:

```bash
python code/main.py --stage all --sample-ratio 0.1
```

## Output Artifacts

- `data/derived/energy_samples.csv`: Computed energy components per particle/frame.
- `artifacts/statistical_results.json`: Results of KS and Chi-squared tests.
- `artifacts/sensitivity_analysis_report.json`: Sensitivity sweep results.
- `artifacts/regression_results.json`: Regression model parameters.
