# Pipeline Flow Documentation

This document describes the data flow and processing stages of the `llmXive` automated science pipeline for the gut microbiome and sleep quality investigation.

## Overview

The pipeline is designed as a sequence of independent, testable stages. Each stage consumes specific inputs, performs a defined transformation, and produces artifacts that serve as inputs for subsequent stages.

## Stage 1: Data Ingestion and Preprocessing

**Input**: Raw data source defined by `DATA_URL`.
**Module**: `src.ingestion`

1. **Verification**: Checks for the existence of the data URL and validates the schema (presence of `antibiotic_use_last_3m`, `sleep_efficiency`, `sleep_duration_hours`).
2. **Download**: Fetches the data with exponential backoff.
3. **Filtering**:
 - Excludes samples where `antibiotic_use_last_3m` is True.
 - Excludes samples with missing `sleep_efficiency` or `sleep_duration_hours`.
4. **Merging**: Combines OTU tables with sleep metadata.
5. **Output**:
 - `data/processed/cleaned_microbiome_sleep.csv`: The filtered, merged dataset.
 - `data/processed/ingestion_report.json`: Logs of exclusion counts and proportions.

## Stage 2: Alpha-Diversity Calculation

**Input**: `data/processed/cleaned_microbiome_sleep.csv`
**Module**: `src.diversity`

1. **Rarefaction**: Subsamples OTU tables to a fixed sequencing depth to normalize for sequencing effort.
2. **Index Calculation**: Computes Shannon, Simpson, and Observed OTUs indices.
3. **Output**: Updates the processed dataset with diversity indices or prepares them for correlation.

## Stage 3: Statistical Correlation Analysis

**Input**: Diversity indices and sleep metrics.
**Module**: `src.correlation`

1. **Spearman Correlation**: Computes rank correlation coefficients between each diversity index and sleep metrics.
2. **FDR Correction**: Applies Benjamini-Hochberg correction to p-values.
3. **Flagging**: Marks correlations as `is_moderate` (|r| > 0.3) and `is_meaningful` (q < 0.05 AND |r| > 0.3).
4. **Output**:
 - `data/processed/correlation_results.csv`: Detailed results including r, p, q, and flags.

## Stage 4: Visualization

**Input**: `data/processed/correlation_results.csv` and cleaned data.
**Module**: `src.viz`

1. **Scatterplots**: Generates plots with regression lines for significant correlations.
2. **Boxplots**: Generates boxplots of diversity indices grouped by sleep quartiles.
3. **Output**: Plot images saved to `data/processed/plots/`.

## Stage 5: Reporting

**Input**: Correlation results, ingestion reports, and plots.
**Module**: `src.report` (text) and `src.report_final` (HTML/PDF)

1. **Compilation**: Aggregates findings into a summary table.
2. **Generation**: Produces a human-readable text report and a formatted HTML/PDF report.
3. **Output**: `data/processed/report.txt`, `data/processed/report.html` (or `.pdf`).

## Data Integrity and Reproducibility

- **Hashing**: `src/utils/hashing.py` provides `compute_sha256` to verify artifact integrity.
- **Reproducibility Test**: `tests/integration/test_reproducibility.py` runs the pipeline twice and compares hashes of key outputs to ensure deterministic behavior.
