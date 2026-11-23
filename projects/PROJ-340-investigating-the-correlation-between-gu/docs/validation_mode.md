# Validation Mode Guide

## Overview
Validation mode allows the pipeline to run with **synthetic data** for local testing and development. This mode is **disabled by default** in production environments.

## Enabling Validation Mode
To run the pipeline with synthetic data:

```bash
# Step 1: Generate synthetic data
python code/ingest.py --mode synthetic --output data/raw/synthetic_data.csv

# Step 2: Run the main pipeline on synthetic data
python code/main.py --input data/raw/synthetic_data.csv --output data/results/
```

## Synthetic Data Characteristics
The synthetic data generator (`code/generate_synthetic_data.py`) creates:
- **Microbiome Data**: Zero-inflated negative binomial distribution (mimicking real count data).
- **Sleep Data**: Normal distribution with realistic means and variances.
- **Missing Values**: Randomly injected to test validation logic.
- **Outliers**: Injected to test outlier detection.

## Limitations of Validation Mode
- **Results are not real**: Correlation coefficients and p-values are random artifacts of the synthetic generation process.
- **Not for publication**: Do not use synthetic data results for scientific claims.
- **Causal Language Scan**: The causal language scanner will still run, but the content is synthetic.

## Verification
After running in validation mode, verify that:
1. `data/processed/filtered_data.parquet` exists.
2. `data/results/outlier_report.json` contains detected outliers.
3. `data/results/correlation_matrix.json` is generated (even if values are random).
4. No "Fabricated Results" errors are raised (the system knows it's synthetic).

## Switching to Real Data
To switch to real data:
1. Remove the `--mode synthetic` flag.
2. Ensure `data/config/real_data_sources.yaml` is configured.
3. Run `python code/main.py`.
