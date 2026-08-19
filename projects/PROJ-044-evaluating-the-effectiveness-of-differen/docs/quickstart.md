# Quickstart Guide

This guide provides a minimal end-to-end workflow to reproduce the core results of the project.

## Prerequisites

- Python 3.10+
- `pip`
- 16GB+ RAM (recommended for FEMNIST processing)

## Step 1: Setup

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Initialize pre-commit
pre-commit install
```

## Step 2: Data Download and Partitioning

Download the FEMNIST dataset and generate partitions with a high heterogeneity level (α=0.1).

```bash
# Download FEMNIST
python code/data/download.py --dataset femnist

# Verify download
ls -lh data/raw/femnist.parquet data/raw/femnist.sha256

# Generate partitions
python code/data/partition.py --dataset femnist --seed 42 --alpha 0.1
```

## Step 3: Run a Single Training Configuration

Run a quick experiment with a single seed and configuration to verify the pipeline.

```bash
python code/training/orchestrate_experiment.py \
 --dataset femnist \
 --seeds 42 \
 --alphas 0.1 \
 --epsilons 0.5 \
 --output results/quick_test_logs.csv
```

## Step 4: Analyze Results

Run the analysis script on the quick test logs.

```bash
python code/analysis/stats.py \
 --input results/quick_test_logs.csv \
 --output results/quick_test_summary.csv \
 --plots-dir results/quick_test_plots/
```

## Step 5: Verify Outputs

Check that the expected artifacts were generated:

```bash
# Check for summary CSV
cat results/quick_test_summary.csv

# Check for plots
ls -lh results/quick_test_plots/
```

## Troubleshooting

- **Dataset Download Fails**: Ensure you have a stable internet connection. The script retries 3 times with exponential backoff.
- **OOM Errors**: The training loop implements dynamic batch sizing (T031) which automatically reduces batch size if Out-Of-Memory errors occur.
- **Shakespeare Error**: If you see a `ValueError` regarding Shakespeare, this is expected. The dataset is excluded per plan.md.

## Next Steps

For a full experiment with all seeds and configurations, run:

```bash
python code/training/orchestrate_experiment.py \
 --dataset femnist \
 --seeds 42 43 44 45 46 \
 --alphas 0.1 0.5 1.0 \
 --epsilons 0.1 0.5 1.0 5.0 10.0 \
 --output results/raw_logs.csv
```

Then run the full analysis pipeline as described in Step 4.
