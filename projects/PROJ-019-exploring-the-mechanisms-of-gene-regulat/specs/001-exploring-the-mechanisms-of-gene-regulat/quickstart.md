# Quickstart Guide: Gene Regulation Analysis Pipeline

## Prerequisites
- Python 3.11 or higher
- At least 14GB of free disk space
- FIMO tool installed and available in PATH
- Network access to ENCODE and JASPAR databases

## Quick Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Verify Environment
The pipeline will automatically check for:
- Sufficient disk space (≥14GB)
- Required tools (FIMO)
- Network connectivity

### 3. Run the Pipeline
```bash
python code/main.py
```

The pipeline will execute the following stages:

#### Stage 1: Data Ingestion (US1)
- Downloads ENCODE peak files for 5 cell types
- Parses and normalizes data to standardized BED format
- Annotates peaks with gene symbols (hg38)
- Generates `data/processed/ingestion_summary.json`

#### Stage 2: Motif Scanning (US2)
- Scans peaks for TF motifs using FIMO
- Uses JASPAR CORE database
- Applies p-value threshold of 0.0001
- Creates background model from union of other cell types

#### Stage 3: Enrichment Analysis (US2)
- Calculates enrichment using Fisher's exact test
- Applies Benjamini-Hochberg correction for multiple testing
- Generates `data/processed/enrichment_matrix.csv`

#### Stage 4: Visualization (US3)
- Creates heatmap of enrichment q-values
- Performs Euclidean distance clustering
- Outputs `data/processed/heatmap.png`

#### Stage 5: Validation (US3)
- Fetches independent ChIP-seq peaks for top motifs
- Calculates overlap percentage
- Computes silhouette score (warning if < 0.4)
- Generates `data/processed/validation_report.json` and `data/processed/summary_table.csv`

## Expected Outputs
After successful completion, you will find:
- `data/processed/ingestion_summary.json` - Peak counts per cell type
- `data/processed/enrichment_matrix.csv` - Enrichment results
- `data/processed/heatmap.png` - Visualization
- `data/processed/validation_report.json` - Validation statistics
- `data/processed/summary_table.csv` - Final summary table

## Troubleshooting

### Disk Space Error
If you receive an insufficient disk space error, ensure you have at least 14GB free in the `TMP_DIR` (default: `/tmp`).

### Network Errors
The pipeline includes automatic retry logic with exponential backoff (max 3 retries) for network requests.

### FIMO Not Found
Ensure FIMO is installed and available in your PATH. Download from: https://meme-suite.org/meme/tools/fimo

### Memory Constraints
The pipeline includes chunked processing logic to stay under 7GB RAM usage.

## Next Steps
- Review the enrichment matrix to identify cell-type-specific motifs
- Examine the heatmap for clustering patterns
- Analyze validation results to confirm motif predictions
- Extend the pipeline with additional cell types or analysis methods