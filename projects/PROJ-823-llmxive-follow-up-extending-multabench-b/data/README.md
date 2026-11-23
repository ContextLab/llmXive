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

## Acquiring `data/raw/multabench_baselines.csv`

The file `data/raw/multabench_baselines.csv` contains the "GPU-Tuned" baseline metrics required for the Recovery Ratio calculation (US3). This file is **not** available via a public URL or programmatic download. It must be obtained manually from the MulTaBench supplementary materials.

**Manual Acquisition Steps:**

1. **Download the MulTaBench supplementary material** from the official repository or the associated paper's data release page.
2. **Unzip the archive** to a temporary location.
3. **Locate `multabench_baselines.csv`** within the extracted contents.
4. **Place the file** into the `data/raw/` directory of this project.

**Verification:**

After placing the file, verify its presence:
```bash
ls -l data/raw/multabench_baselines.csv
```

If this file is missing, the pipeline will fail with an explicit error (see `code/pipelines/fetch_baselines.py`) and will generate a "Data Availability Gap" report (`data/artifacts/data_availability_gap_report.json`) documenting the missing baseline.