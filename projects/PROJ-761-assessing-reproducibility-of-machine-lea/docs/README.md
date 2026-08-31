# PROJ-761: Assessing Reproducibility of Machine-Learned Reaction Yield Models

Automated pipeline to reproduce, validate, and statistically analyze machine learning models for chemical reaction yields.

## Overview

This project implements a reproducible science pipeline that:
1. Ingests data from published papers (via manifest)
2. Re-implements reported models on CPU
3. Computes reproduced metrics (MAE, R², Spearman ρ)
4. Calculates a Deviation Index (S) against reported results
5. Performs statistical meta-analysis (t-tests, mixed-effects, Bland-Altman)
6. Generates community guidelines based on failure modes

## Prerequisites

- Python 3.11
- pip

## Installation

1. Clone the repository:
 ```bash
 git clone <repository-url>
 cd PROJ-761-assessing-reproducibility-of-machine-lea
 ```

2. Install dependencies:
 ```bash
 pip install -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu
 ```

 **Note**: The `requirements.txt` includes CPU-only PyTorch. If using GPU, modify the index URL and version accordingly.

3. (Optional) Run linting/formatting checks:
 ```bash
 python code/run_lint_checks.py
 ```

## Quick Start

The pipeline consists of three main stages: Ingest, Reproduce, and Analyze.

### 1. Ingest Data

Prepare a `data/manifest.yaml` file describing the target papers (DOI, dataset, reported metrics).
Then run the ingestion pipeline:

```bash
python code/ingest.py
```

This will:
- Validate the manifest against `contracts/PaperManifest.json`
- Fetch datasets (or supplementary files)
- Save processed data to `data/processed/`
- Log any data gaps or missing variables

### 2. Reproduce Metrics

Run the model runner to re-implement models and compute metrics:

```bash
python code/model_runner.py
```

This will:
- Load processed data
- Train models (enforcing ≤1M parameter limit; substituting baseline if needed)
- Run sensitivity analysis (seeds: 42, 123, 999)
- Output `artifacts/reports/repro_results.json` with MAE, R², ρ, deviations, and score S

### 3. Analyze & Generate Guidelines

Run the statistical analysis and guideline generation:

```bash
python code/stats.py
python code/guidelines.py
```

This will:
- Perform paired t-tests, TOST, and mixed-effects modeling
- Generate Bland-Altman plots in `artifacts/plots/`
- Output `artifacts/reports/stat_summary.json`
- Generate `artifacts/reports/reproducibility_checklist.md`

## Project Structure

```
.
├── code/ # Main implementation
│ ├── main.py # Orchestration & environment logging
│ ├── ingest.py # Data fetching & validation
│ ├── model_runner.py # Model training & evaluation
│ ├── stats.py # Statistical analysis
│ ├── metrics.py # Metric calculations (MAE, R², S)
│ ├── guidelines.py # Checklist generation
│ └──...
├── data/
│ ├── raw/ # Raw fetched data
│ ├── processed/ # Preprocessed datasets
│ └── manifest.yaml # Input manifest
├── artifacts/
│ ├── logs/ # Execution logs
│ ├── plots/ # Generated figures (Bland-Altman)
│ └── reports/ # JSON results & markdown checklists
├── contracts/ # JSON Schemas
├── tests/ # Unit & integration tests
├── docs/ # Documentation
├── requirements.txt
└── pyproject.toml
```

## Configuration

- **Random Seeds**: Default is 42. Sensitivity analysis runs on {42, 123, 999}.
- **Parameter Limit**: Models > 1M parameters are automatically substituted with a baseline.
- **Tolerance Delta**: TOST equivalence tests use δ = 0.1 (configurable in `code/stats.py`).

## Troubleshooting

- **Missing Data**: Check `artifacts/logs/failure_log.json` for detailed flags on missing variables or datasets.
- **Model Substitution**: If a model exceeds the parameter limit, a baseline is used and logged in the results.
- **Environment**: Run `python code/main.py` to capture environment details in `artifacts/logs/env.log`.

## License

[Insert License Here]
