# Quick Start Guide

This guide provides a step-by-step walkthrough to run the Feature Importance Drift Analysis Pipeline from start to finish.

## Prerequisites

- Python 3.11+ installed
- pip package manager
- Internet connection (for dataset download)

## Step 1: Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd PROJ-092-statistical-analysis-of-feature-importan

# Create virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r code/requirements.txt
```

## Step 2: Initialize Directory Structure

```bash
python code/setup_directories.py
```

Expected output:
```
Directory structure created successfully.
```

## Step 3: Download the Dataset

```bash
python code/download.py
```

Expected output:
```
Downloading from https://archive.ics.uci.edu/ml/machine-learning-databases/00321/LD2011_2014.txt.zip to data/raw/LD2011_2014.txt.zip
Download completed: data/raw/LD2011_2014.txt.zip
Dataset downloaded and verified: Hash: <sha256>
```

**Note**: The dataset is approximately 50MB. Download time depends on your internet connection.

## Step 4: Run the Full Pipeline

```bash
python code/main.py
```

This command executes the complete pipeline:

1. Loads raw data
2. Preprocesses and splits into 30-day windows
3. Trains Random Forest models on each window
4. Calculates permutation importance
5. Saves importance profiles to `outputs/importance_profiles.csv`

Expected output (abbreviated):
```
2024-01-15 10:30:00 - main - INFO - Starting pipeline execution
2024-01-15 10:30:01 - preprocess - INFO - Loaded 4 years of data
2024-01-15 10:30:02 - preprocess - INFO - Split into 48 windows
2024-01-15 10:30:05 - train_and_importance - INFO - Window 1: R² = 0.85, Success
2024-01-15 10:30:08 - train_and_importance - INFO - Window 2: R² = 0.82, Success
...
2024-01-15 10:35:00 - main - INFO - Pipeline completed successfully
```

## Step 5: Run Drift Analysis

```bash
python code/drift_analysis.py
```

This calculates Spearman rank correlations between consecutive windows.

Expected output:
```
2024-01-15 10:35:05 - drift_analysis - INFO - Computing pairwise drift
2024-01-15 10:35:10 - drift_analysis - INFO - Generated null baseline
2024-01-15 10:35:15 - drift_analysis - INFO - Drift metrics saved to outputs/drift_metrics.csv
```

## Step 6: Run Significance Tests

```bash
python code/significance_test.py
```

This performs Mann-Kendall trend test and block permutation test.

Expected output:
```
2024-01-15 10:35:20 - significance_test - INFO - Running Mann-Kendall test
2024-01-15 10:35:22 - significance_test - INFO - Kendall's Tau: -0.15
2024-01-15 10:35:25 - significance_test - INFO - Block permutation p-value: 0.03
2024-01-15 10:35:26 - significance_test - INFO - Significance tests completed
```

## Step 7: Generate Final Report

```bash
python code/generate_final_report.py
```

This aggregates all metrics and generates the final summary.

Expected output:
```
2024-01-15 10:35:30 - generate_final_report - INFO - Aggregating global statistics
2024-01-15 10:35:32 - generate_final_report - INFO - Final report saved to outputs/global_stats.json
```

## Step 8: Review Results

Examine the generated outputs:

```bash
# View importance profiles
head outputs/importance_profiles.csv

# View drift metrics
cat outputs/drift_metrics.csv

# View global statistics
cat outputs/global_stats.json
```

Example `global_stats.json`:
```json
{
 "mean_rho": -0.05,
 "trend_direction": "monotonic decrease",
 "p_value": 0.03,
 "stable_window_count": 45,
 "total_window_count": 48,
 "success_rate": 0.9375
}
```

## Troubleshooting

### Dataset Download Fails

If the download fails, try:
```bash
# Check internet connection
ping archive.ics.uci.edu

# Download manually and place in data/raw/
# URL: https://archive.ics.uci.edu/ml/machine-learning-databases/00321/LD2011_2014.txt.zip
```

### Memory Issues

If you encounter memory errors:
- Reduce window size in `code/utils/config.py`
- Process data in smaller batches
- Increase available RAM

### Module Import Errors

Ensure you're running from the project root:
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)/code"
```

## Next Steps

- Review the [README.md](README.md) for detailed usage
- Read the [ARCHITECTURE.md](ARCHITECTURE.md) for system design
- Explore the [tasks.md](../tasks.md) for implementation details
- Run `pytest tests/` to verify the installation

## Support

For issues or questions:
- Check the [Troubleshooting](#troubleshooting) section
- Review the [FAQ](#faq) in the main README
- Open an issue on the repository
