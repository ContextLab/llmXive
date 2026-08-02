# Quickstart Guide

This guide provides a step-by-step walkthrough to reproduce the core experiments of the Differential Privacy in Federated Learning evaluation.

## Prerequisites

- Python 3.10+
- pip
- A GPU (recommended) or sufficient CPU resources

## Step 1: Setup Environment

```bash
# Clone and navigate to project
cd projects/PROJ-044-evaluating-the-effectiveness-of-differen

# Create virtual environment
python -m venv venv
source venv/bin/activate # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Download Datasets

Download the FEMNIST dataset (LEAF benchmark):

```bash
python code/data/download.py --dataset femnist --output data/raw
```

Download the Shakespeare dataset (LEAF benchmark):

```bash
python code/data/download.py --dataset shakespeare --output data/raw
```

*Note: This may take a few minutes depending on your internet connection.*

## Step 3: Generate Data Partitions

Create client partitions with high heterogeneity (α=0.1) for FEMNIST:

```bash
python code/data/partition.py --dataset femnist --alpha 0.1 --seed 42
```

Create client partitions with moderate heterogeneity (α=0.5) for Shakespeare:

```bash
python code/data/partition.py --dataset shakespeare --alpha 0.5 --seed 42
```

This generates JSON files in `data/partitions/` containing client-specific data distributions.

## Step 4: Run Training Experiment

Execute a single training run with Differential Privacy:

```bash
python code/training/fedavg.py \
 --dataset femnist \
 --alpha 0.1 \
 --epsilon 0.5 \
 --seed 42 \
 --output results/experiment_001
```

*Note: Training may take 10-30 minutes depending on hardware.*

## Step 5: Analyze Results

Generate statistical analysis and validation reports:

```bash
python code/analysis/stats.py --input results/experiment_001/metrics.csv
```

Generate visualizations:

```bash
python code/analysis/plots.py --input results/experiment_001/metrics.csv --output results/figures
```

## Step 6: Review Output

Check the generated files:

- `results/summary.csv`: Aggregated metrics across runs.
- `results/validation_report.md`: Statistical power analysis.
- `results/figures/`: Plots showing accuracy gaps and sensitivity.

## Troubleshooting

### Out of Memory (OOM)

If you encounter OOM errors during training:
- Reduce the `--batch_size` in the training command.
- Ensure you are using a GPU with sufficient VRAM.
- The system includes automatic batch size reduction logic if OOM is detected.

### Data Download Failures

If dataset downloads fail:
- Check your internet connection.
- Ensure you have sufficient disk space in `data/raw/`.
- The downloader includes retry logic (3 attempts with exponential backoff).

### Statistical Test Errors

If statistical tests fail due to insufficient data:
- The system automatically falls back to Mann-Whitney U tests.
- Check `results/validation_report.md` for `power_reduced` flags.

## Next Steps

- Run experiments across multiple ε values (0.1, 0.5, 1.0, 5.0, 10.0).
- Test different α values to explore the "critical heterogeneity" hypothesis.
- Compare DP vs. Non-DP performance using the analysis scripts.
