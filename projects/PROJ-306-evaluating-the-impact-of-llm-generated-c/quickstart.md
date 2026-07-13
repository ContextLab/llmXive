# Quickstart Guide

This guide provides the commands to run the full pipeline and generate all required artifacts.

## Prerequisites

1. Ensure you have Python 3.8+ installed.
2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```
3. Set your API key if using external models:
 ```bash
 export LLM_API_KEY="your-api-key-here"
 ```

## Step 1: Load and Prepare Datasets

Download and process the MBPP and HumanEval datasets.

```bash
python code/dataset_loader.py
```

This will create:
- `data/benchmarks/raw/mbpp/`
- `data/benchmarks/raw/humaneval/`
- `data/benchmarks/processed/catalog.json`

## Step 2: Run Generation and Coverage Pipeline

Generate code using the LLM and run coverage tests.

```bash
python code/main.py --mode generate --dataset all --model gpt-4 --output-dir data/coverage_reports
```

*Note: Use `--limit N` to process only the first N tasks for testing.*

This will produce:
- `data/coverage_reports/{task_id}.json`

## Step 3: Run Statistical Analysis (User Story 2)

Perform statistical comparisons and sensitivity analysis.

```bash
python code/main.py --mode sensitivity
```

This will produce:
- `data/processed/stats_summary.csv`
- `data/processed/sensitivity_report.csv`
- `data/processed/corrected_pvalues.csv`

## Step 4: Run Stratification and Visualization (User Story 3)

Generate stratified reports and visualizations.

```bash
python code/visualizer.py
```

This will produce:
- `outputs/stratified_*.csv`
- `outputs/*.png`

## Verification

To verify all artifacts are present:

```bash
python code/task_t050_validate_quickstart.py
```

Expected outputs:
- `data/coverage_reports/*.json`
- `data/processed/stats_summary.csv`
- `data/processed/sensitivity_report.csv`
- `outputs/*.csv`
- `outputs/*.png`
