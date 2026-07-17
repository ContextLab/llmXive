# Quickstart Guide

This guide provides the minimum steps to reproduce the analysis and generate the final report.

## Prerequisites

- Python 3.9+
- pip
- ~8GB RAM (for local model loading)
- Internet connection (for data download and API fallback)

## Step 1: Setup Environment

```bash
# Clone and enter
cd PROJ-294-evaluating-the-impact-of-code-generation

# Create virtual environment
python -m venv venv
source venv/bin/activate # Windows: venv\Scripts\activate

# Install dependencies
pip install -r code/requirements.txt
```

## Step 2: Initialize Directories

```bash
python code/setup_data_dirs.py
python code/create_results_dirs.py
```

## Step 3: Download Data

```bash
python code/download_data.py
```
*Expected Output*: Downloaded `humaneval.jsonl` and created `sampled_tasks.json` (50 tasks).

## Step 4: Generate Code

```bash
python code/generate_code.py
```
*Note*: This step may take 10-30 minutes depending on the model and hardware. It generates code for the 50 sampled tasks.

## Step 5: Analyze Metrics

```bash
python code/analyze_metrics.py
```
*Note*: This step executes the generated code against test suites. It may take 5-15 minutes.

## Step 6: Merge Sensitivity Data

```bash
python code/merge_sensitivity_metrics.py
```
*Note*: If sensitivity analysis was performed, this merges the results.

## Step 7: Run Statistical Tests

```bash
python code/statistical_tests.py
```
*Output*: `results/statistical_results.json`

## Step 8: Generate Report

```bash
python code/report_generator.py
```
*Output*: `results_report.md`, `results/figures/`

## Verification

Check the final report:
```bash
cat results_report.md
```

Verify the metrics file:
```bash
cat data/analysis/metrics.json | python -m json.tool | head -n 20
```

## Troubleshooting

- **Missing Data**: If `data/raw/` is empty, re-run `download_data.py`.
- **Empty Metrics**: If `metrics.json` is empty, check `errors.log` for generation/analysis failures.
- **No Figures**: Ensure `matplotlib` is installed and `X11` forwarding is not required (backend Agg backend is used by default).
