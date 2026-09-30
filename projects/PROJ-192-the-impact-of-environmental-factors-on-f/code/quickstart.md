# Quickstart Guide: Impact of Environmental Factors on Fungal Community Structure

This guide explains how to run the full analysis pipeline for User Story 1 (MVP) and subsequent user stories.

## Prerequisites

Ensure all dependencies are installed:
```bash
pip install -r requirements.txt
# Ensure CLI tools are available: cutadapt, vsearch, seqkit, fasterq-dump (from sra-tools)
```

## Running the Full Analysis (User Story 1)

The pipeline consists of three main stages: Ingestion, Preprocessing, and Analysis/Reporting.
Run them sequentially to generate the required artifacts.

### 1. Ingest and Harmonize Metadata
Downloads raw data (if in Research Mode) and harmonizes environmental metadata.
This step produces `data/metadata/harmonized_matrix.csv`.

```bash
python code/src/pipelines/ingest.py --mode research
```

*Note: In Validation Mode, it expects existing data in `data/raw-seq/`.*

### 2. Preprocess and Impute Data
Performs denoising (via vsearch), MICE imputation, VIF calculation, and diversity analysis.
This step depends on the output of Step 1.

```bash
python code/src/pipelines/preprocess.py
```

### 3. Run Analysis and Generate Reports
Executes PERMANOVA, db-RDA, variance partitioning, and generates plots.
This step depends on the output of Step 2.

```bash
python code/src/pipelines/analysis.py
python code/src/pipelines/report.py
```

## Running Stratified Analysis (User Story 2)

To analyze data stratified by biome:

```bash
python code/src/pipelines/analysis.py --stratify-by biome
python code/src/pipelines/report.py --stratify-by biome
```

## Running Sensitivity Analysis (User Story 3)

To perform threshold sensitivity analysis:

```bash
python code/src/pipelines/report.py --sweep-thresholds
```

## Verifying Data Integrity

Use the checksum utility to verify downloaded files:

```bash
# Calculate checksum
python code/utils/checksums.py calculate --file data/raw-seq/<dataset_id>.fastq.gz

# Generate checksum file
python code/utils/checksums.py generate --file data/raw-seq/<dataset_id>.fastq.gz

# Verify checksum
python code/utils/checksums.py verify --file data/raw-seq/<dataset_id>.fastq.gz --checksum <sha256_hash>
```

## Expected Outputs

- `data/metadata/harmonized_matrix.csv`
- `data/qc/asv_table.tsv`
- `results/permanova_summary.csv`
- `results/db_rda_variance.csv`
- `results/plots/db_rda_triplot.png`
- `results/plots/correlation_matrix.png`

## Troubleshooting

- **Missing `harmonized_matrix.csv`**: Ensure Step 1 (`ingest.py`) completed successfully. Check logs for metadata validation errors.
- **Checksum Verification Failed**: Ensure the `--checksum` argument matches the exact SHA256 hash. Use `calculate` first to verify.
- **RAM Errors**: The pipeline includes memory projection logic. If subsampling is triggered, check `results/sampling_report.csv`.
