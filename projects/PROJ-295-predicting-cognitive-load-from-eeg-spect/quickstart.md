# Quickstart Guide

This guide provides the exact steps to run the cognitive load prediction pipeline from start to finish.

## Step 1: Install Dependencies

Ensure you have Python 3.11+ and install the required packages:

```bash
pip install -r requirements.txt
```

## Step 2: Download and Verify Dataset

Download the OpenNeuro ds000246 dataset and verify its integrity:

```bash
python code/data/download.py
python code/data/verify_dataset.py
```

Expected output:
- Dataset downloaded to `data/raw/`
- Verification report generated at `results/verification_report.json`
- If `gaze.tsv` is missing, the process will halt with a clear error message.

## Step 3: Run Power Analysis

Verify that the dataset has sufficient statistical power:

```bash
python code/data/power_analysis.py
```

This will:
- Read the verification report
- Calculate minimum required sample size for R²=0.2
- Halt if the dataset is underpowered

## Step 4: Run Memory Check

Validate that chunked loading stays within memory limits:

```bash
python code/data/memory_check.py
```

## Step 5: Run the Full Pipeline

Execute the complete end-to-end pipeline:

```bash
python code/main.py --data-dir data/processed --output-dir results
```

This single command will:
1. Preprocess EEG data (filtering, ICA, epoching)
2. Extract spectral power features
3. Generate cognitive load labels
4. Train and evaluate the model
5. Perform statistical validation
6. Generate all output reports

## Step 6: Verify Outputs

Check that all expected files were generated:

```bash
ls results/
```

Expected files:
- `model_metrics.json`
- `channel_importance.json`
- `permutation_test.json`
- `sensitivity_report.csv`
- `baseline_comparison.json`
- `runtime_profile.json`

## Troubleshooting

### Missing `gaze.tsv`

If the download fails due to missing `gaze.tsv`, the pipeline will halt. This is expected behavior per the specification. Check the dataset source or update the spec for fallback options.

### Memory Errors

If you encounter memory issues, ensure the chunked loading logic is working correctly. The pipeline should automatically chunk data when estimated usage exceeds 6.5 GB.

### Runtime Exceeds 6 Hours

The pipeline includes a runtime profiler. If execution exceeds 6 hours, it will halt and report the issue in `results/runtime_profile.json`.

## Next Steps

- Review `results/model_metrics.json` for final performance metrics
- Examine `results/channel_importance.json` to understand which EEG channels/bands are most predictive
- Check `results/permutation_test.json` to verify statistical significance
- Analyze `results/sensitivity_report.csv` for window size effects