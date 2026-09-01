# Quickstart Guide

This guide provides the essential steps to run the cognitive load prediction pipeline.

## Step 1: Environment Setup

Ensure you have Python 3.11+ and install the required dependencies:

```bash
pip install -r requirements.txt
```

## Step 2: Data Preparation

The pipeline will automatically download the `ds000246` dataset from OpenNeuro if it is not already present in `data/raw`. The download script verifies the presence of `gaze.tsv` and will halt with a clear error message if the required behavioral data is missing.

## Step 3: Run the Pipeline

Execute the main pipeline script with the following command:

```bash
python code/main.py --data-dir data/processed --output-dir results
```

### Arguments

- `--data-dir`: Path to the directory containing processed data (default: `data/processed`)
- `--output-dir`: Path to the directory where results will be saved (default: `results`)

## Step 4: Verify Outputs

After the pipeline completes successfully, check the `results/` directory for:

- `model_metrics.json`: Contains R², RMSE, and baseline comparison
- `channel_importance.json`: Statistical significance of channel contributions
- `sensitivity_report.csv`: Model performance across different gaze window sizes

## Troubleshooting

### Missing `gaze.tsv`

If the pipeline halts with a `FileNotFoundError` regarding `gaze.tsv`, the dataset specification may need to be updated. The current implementation does not support automatic fallback to alternative datasets.

### Memory Constraints

If you encounter memory issues, ensure your system has at least 8GB of RAM. The pipeline uses chunked loading to stay within ~6.5GB, but large datasets may require more resources.

### Data Integrity

Run `python code/utils/verify_data_integrity.py` (if available) to perform pre-flight checks on your data before processing.

## Next Steps

- Review `results/model_metrics.json` for model performance
- Examine `results/channel_importance.json` to identify significant EEG channels
- Analyze `results/sensitivity_report.csv` to understand label stability

For detailed documentation on individual modules, refer to the docstrings in the `code/` directory.