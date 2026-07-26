# Quickstart Guide for llmXive Research Pipeline

## Prerequisites

- Python 3.11+
- pip

## Setup

1. Clone the repository.
2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```
3. Ensure the project structure is created (run T001/T002 if needed).

## Execution

Run the full research pipeline using the orchestration script:

```bash
python code/pipeline.py --config code/config.py
```

This command will:
1. Download the TELBench dataset.
2. Parse trajectories and build graphs.
3. Calculate metrics (Connectivity, Branching).
4. Split data into Train/Test sets.
5. Perform evaluation (Thresholds, Predictions, Sensitivity Analysis, Linear Reasoning Check).
6. Generate final reports.

All output files will be written to `data/processed/`.

## Verification

After execution, verify the presence of the following files in `data/processed/`:
- `metrics.csv`
- `train_metrics.csv`, `test_metrics.csv`
- `linear_reasoning_report.json`
- `results_report.json`
- `baseline_report.json`
- `threshold_config.json`
- `f1_max_threshold.json`
- `sensitivity_threshold_matrix.json`
- `sensitivity_percentile_matrix.json`
- `sc_002_result.json`
- `power_analysis.json`
- `comparative_report.json`
