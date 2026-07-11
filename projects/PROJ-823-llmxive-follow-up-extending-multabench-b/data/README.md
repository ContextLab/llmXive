# Data Directory for llmXive Project

This directory stores all input data, processed artifacts, and generated outputs.

## Structure

- `raw/`: Original datasets downloaded from MulTaBench or other sources.
- `processed/`: Intermediate and final processed data (e.g., Parquet files).
- `artifacts/`: Generated reports, metrics, and analysis results.
- `figures/`: Plots and visualizations.

## Instructions

1. Download raw MulTaBench data into `raw/`.
2. Run `code/data_loader.py` to verify checksums and ingest data.
3. Processed outputs will be written to `processed/`.
4. Analysis artifacts will be written to `artifacts/`.

## Checksums

SHA-256 checksums for raw data files should be placed in `raw/checksums.txt`.
