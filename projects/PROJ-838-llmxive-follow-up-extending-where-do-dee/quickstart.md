# Quickstart Guide for llmXive Follow-up Project

## Prerequisites

- Python 3.11+
- pip

## Setup

1. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

2. Ensure the project structure is correct:
 ```bash
 mkdir -p code data tests data/raw data/processed graphs data/processed/graphs
 ```

## Execution

Run the full pipeline:

```bash
python code/pipeline.py --config code/config.py
```

This command will:
1. Download and validate the TELBench dataset
2. Build graphs for all trajectories
3. Calculate metrics (connectivity and branching)
4. Split data into train/test sets
5. Run evaluation and generate reports

## Output Artifacts

The pipeline produces the following artifacts in `data/processed/`:
- `metrics.csv`: Metrics for all trajectories
- `train_metrics.csv`, `test_metrics.csv`: Split datasets
- `threshold_config.json`: 20th percentile threshold
- `baseline_report.json`: Baseline connectivity
- `results_report.json`: Final evaluation results
- `sensitivity_threshold_matrix.json`, `sensitivity_percentile_matrix.json`: Sensitivity analysis
- `sc_002_result.json`: Correlation significance result
- `power_analysis.json`: Power analysis results
- `comparative_report.json`: Comparative threshold analysis
- `linear_reasoning_report.json`: Linear reasoning analysis (if applicable)
- `f1_max_threshold.json`: F1-max threshold for comparison

## Validation

To validate the pipeline:
```bash
python -m pytest tests/ -v
```

To check reproducibility:
```bash
python tests/integration/test_reproducibility.py
```

## Notes

- All seeds are read from `code/config.py`
- The pipeline runs on CPU only
- Real data from `NJU-LINK/TELBench` is required
- The pipeline will fail loudly if the dataset is missing
