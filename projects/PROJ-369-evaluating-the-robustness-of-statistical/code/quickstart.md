# Quickstart Guide

This guide provides the commands to run the full pipeline end-to-end.

## Prerequisites

1. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

2. Ensure the project structure is set up:
 ```bash
 python code/scripts/setup_project_structure.py
 ```

## Running the Pipeline

Execute the following commands in order to run the full analysis pipeline.

### 1. Ingestion
```bash
python code/scripts/run_ingestion.py
```

### 2. Preprocessing
```bash
python code/scripts/run_preprocessing.py
```

### 3. Synthesis
```bash
python code/scripts/run_synthetic_grid.py
```

### 4. Metrics (Real)
```bash
python code/scripts/run_metrics_real.py
```

### 5. Metrics (Synthetic)
```bash
python code/scripts/run_metrics_synthetic.py
```

### 6. Hypothesis Testing
```bash
python code/scripts/run_hypothesis_testing.py
```

### 7. Regression & Feature Filtering (T037b)
This step filters features and runs the regression model.
```bash
python code/src/analysis/regression.py
```

### 8. Visualization
```bash
python code/scripts/run_viz.py
```

## Output Artifacts

After running the pipeline, the following files should be generated in `data/results/`:

- `filtered_features.json`: List of included and excluded features (T037b).
- `regression_model.json`: Regression coefficients and statistics (T037a).
- `final_summary.json`: Summary of all results (T041).
- `error_rates.json`: Type I error rates for synthetic series.
- `hurst_estimates.json`: Estimated Hurst exponents for real series.

## Verification

To verify the results, run the contract tests:
```bash
pytest tests/contract/
```

To check the full pipeline integrity:
```bash
pytest tests/integration/test_data_pipeline.py
```
