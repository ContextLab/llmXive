# Quickstart Guide

## Prerequisites

- Python 3.11+
- Virtual environment with dependencies installed

## Installation

```bash
python -m venv code/.venv
source code/.venv/bin/activate # On Windows: code\.venv\Scripts\activate
pip install -r requirements.txt
```

## Running the Pipeline

The main entry point for the full analysis pipeline is `code/main.py`.
This script orchestrates all steps from data acquisition to final report generation.

```bash
python code/main.py
```

### Expected Outputs

Upon successful execution, the following artifacts will be generated:

- `data/processed/baseline_metrics.json`: Baseline statistical metrics for all datasets.
- `data/processed/cleaned_metrics.json`: Metrics after applying cleaning strategies.
- `data/processed/null_fpr_metrics.json`: False positive rate metrics from permutation tests.
- `figures/`: Generated visualizations (forest plot, heatmap).
- `data/reports/`: Per-dataset and final comparison reports.

## Individual Task Execution

If you need to run specific steps independently, you can execute the corresponding script directly:

- Data Acquisition: `python code/t011_ensure_data.py`
- Baseline Analysis: `python code/t012_run_baseline_analysis.py`
- Save Cleaned Datasets: `python code/t022_save_cleaned_datasets.py`
- Re-analyze Cleaned Variants: `python code/t023_reanalyze_cleaned_variants.py`
- Comparison Analysis: `python code/t027_run_comparison.py`
- Visualizations: `python code/t034_generate_forest_plot.py`, `python code/t035_generate_ci_heatmap.py`
- Null FPR: `python code/t032_permutation_null_fpr.py`
- Final Report: `python code/t041_generate_final_report.py`

## Troubleshooting

If the pipeline fails, check the logs in the console output. Ensure that:
1. The `data/raw` directory contains valid CSV files or the download step succeeds.
2. All dependencies are installed correctly.
3. The `code/main.py` script is the entry point, not individual scripts unless running in isolation.