# llmXive Quickstart

## Prerequisites
- Python 3.8+
- pip
- Virtual environment (recommended)

## Setup
1. Clone the repository.
2. Create a virtual environment:
 ```bash
 python -m venv code/.venv
 source code/.venv/bin/activate # On Windows: code\.venv\Scripts\activate
 ```
3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Execution
Run the full research pipeline using the orchestration script:
```bash
python code/pipeline.py --config code/config.py
```

Alternatively, run individual stages:
1. Download Data: `python code/run_downloader.py`
2. Build Graphs: `python code/run_build_graphs.py`
3. Calculate Metrics: `python code/run_metrics.py`
4. Evaluate: `python code/run_evaluator.py`

## Validation
Run the validation script to ensure quickstart commands are valid:
```bash
bash scripts/validate_quickstart.sh
```

## Output Artifacts
The pipeline produces the following artifacts in `data/processed/`:
- `metrics.csv`
- `train_metrics.csv`, `test_metrics.csv`
- `threshold_config.json`
- `results_report.json`
- `baseline_report.json`
- `sc_002_result.json`
- `linear_reasoning_report.json`
- `power_analysis.json`
- `comparative_report.json`
- `sensitivity_threshold_matrix.json`
- `sensitivity_percentile_matrix.json`
