# Quickstart: Assessing the Stability of Statistical Model Performance Across Data Subsets

## Prerequisites

- Python 3.11+
- Git
- Access to a GitHub Actions runner or a local machine with 7 GB+ RAM.

## Installation

1. **Clone the Repository**:
 ```bash
 git clone
 cd your-project
 ```

2. **Create Virtual Environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install Dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

## Execution

### 1. Run the Full Pipeline (GitHub Actions)

The pipeline is configured to run automatically on push to the `001-assess-model-stability` branch.
- **Trigger**: `git push origin 001-assess-model-stability`
- **Output**: Artifacts in `results/` and `data/` will be cached and downloadable from the Actions tab.

### 2. Run Locally (Debug Mode)

To run the pipeline locally on a subset of data:

```bash
# Set environment variables for debugging (optional)
export DEBUG_MODE=true
export DATASET_LIMIT=2 # Only process 2 datasets

# Run the main pipeline script
python code/pipeline.py
```

### 3. Verify Results

After completion, verify the outputs:

```bash
# Check for schema compliance
pytest tests/contract/test_schemas.py

# View the final report
cat results/final_report.md
```

## Troubleshooting

- **OOM Error**: If you encounter `MemoryError`, ensure `streaming=True` is enabled in `code/data_loader.py`.
- **Dataset Download Failure**: Check network connectivity. The pipeline will skip failed datasets and log warnings.
- **Zero Variance Warning**: If a model has 0 variance, it is handled gracefully; no action needed.

## Output Artifacts

| File | Description |
|------|-------------|
| `results/raw_evaluations.csv` | A substantial number of rows of individual fold results. |
| `results/stability_metrics.csv` | A set of aggregated metrics spanning multiple datasets and models. |
| `results/correlation_results.csv` | Correlation coefficients and p-values. |
| `results/permutation_results.csv` | Variance comparison test results. |
| `results/final_report.md` | Human-readable summary of findings. |
