# PROJ-019: Exploring the Mechanisms of Gene Regulation Across Different Cell Types

## Overview
This project implements an automated pipeline to analyze gene regulation mechanisms across five distinct cell types (GM, K562, HepG2, H1-hESC, IMR90). The pipeline ingests ATAC-seq/ChIP-seq peak data from ENCODE, performs motif scanning using FIMO against the JASPAR database, calculates enrichment scores, and validates findings against independent ChIP-seq data.

## Key Features
- **Data Ingestion**: Downloads and normalizes ENCODE peak data into a unified BED-like format.
- **Motif Scanning**: Scans peaks for transcription factor motifs using FIMO (p-value ≤ 0.0001).
- **Enrichment Analysis**: Computes enrichment scores using Fisher's exact test with Benjamini-Hochberg correction.
- **Visualization**: Generates heatmaps of enrichment results with clustering.
- **Validation**: Validates findings against independent ChIP-seq data with overlap calculations.

## Requirements
- Python 3.11+
- ≥14GB free disk space
- CPU-only execution (no GPU required)
- External dependencies: ENCODE, JASPAR, FIMO

## Installation
1. Clone the repository
2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```
3. Ensure FIMO is installed and available in PATH

## Usage
Run the main pipeline:
```bash
python code/main.py
```

This will:
1. Perform pre-flight disk space checks
2. Download ENCODE peak files
3. Preprocess and annotate peaks
4. Scan for motifs
5. Calculate enrichment scores
6. Generate visualizations
7. Validate results

## Output Files
- `data/processed/ingestion_summary.json`: Peak counts per cell type
- `data/processed/enrichment_matrix.csv`: Enrichment results with p-values and q-values
- `data/processed/heatmap.png`: Visualization of enrichment results
- `data/processed/validation_report.json`: Validation statistics
- `data/processed/summary_table.csv`: Final summary with all metrics

## Project Structure
```
code/
 ├── config.py # Configuration constants
 ├── main.py # Orchestration logic
 ├── download.py # Data download utilities
 ├── preprocess.py # Data preprocessing and annotation
 ├── scan.py # Motif scanning with FIMO
 ├── enrichment.py # Enrichment analysis
 ├── visualize.py # Visualization generation
 ├── validate.py # Validation against independent data
 ├── summary_table.py # Summary table generation
 └── utils/
 ├── disk_check.py # Disk space verification
 └── network.py # Network utilities with retry logic
data/
 ├── raw/ # Downloaded raw files
 ├── interim/ # Intermediate processed files
 └── processed/ # Final output files
tests/
 ├── unit/ # Unit tests
 ├── integration/ # Integration tests
 └── contract/ # Contract tests
```

## Dependencies
See `requirements.txt` for the complete list of dependencies.

## License
This project is part of the llmXive automated science pipeline.
