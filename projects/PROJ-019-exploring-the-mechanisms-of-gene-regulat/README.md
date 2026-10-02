# PROJ-019: Exploring the Mechanisms of Gene Regulation Across Different Cell Types

## Overview
This project implements an automated pipeline to analyze ATAC-seq and ChIP-seq peak data across multiple human cell types. It downloads real data from ENCODE, scans for transcription factor motifs using FIMO, calculates enrichment scores against a dynamic background model, and validates findings against independent ChIP-seq data.

## Requirements
- Python 3.11+
- ≥16GB RAM (SC-004 requirement)
- ≥14GB free disk space (FR-002 requirement)
- FIMO (from MEME suite) installed and in PATH
- Internet connection for data download

## Installation
1. Clone the repository
2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```
3. Ensure FIMO is installed and accessible via `fimo --version`

## Running the Pipeline
Execute the full pipeline end-to-end:
```bash
python -m code.main
```

## Output Artifacts
The pipeline produces the following artifacts in `data/processed/`:

1. **ingestion_summary.json**: Summary of downloaded and parsed peak data
 - `total_peaks`: Total number of peaks across all cell types
 - `cell_types`: List of cell types processed
 - `parsed_count`: Number of successfully parsed files

2. **enrichment_matrix.csv**: Motif enrichment results
 - Columns: `motif_id`, `cell_type`, `p_value`, `q_value`
 - Motif IDs in JASPAR format (e.g., 'MA0001.1')
 - Cell types: GM12878, K562, HepG2, H1-hESC, IMR90

3. **validation_report.json**: Validation metrics
 - `overlap_pct`: Percentage overlap with independent ChIP-seq data
 - `top_motifs`: List of top enriched motifs with q-values and overlap
 - `silhouette_score`: Clustering quality metric
 - `silhouette_test_passed`: Boolean (True if score ≥ 0.4)
 - `overlap_test_passed`: Boolean (True if overlap ≥ 60%)
 - `validation_passed`: True only if both tests pass

4. **summary_table.csv**: Final summary of top enriched motifs
 - Columns: `motif_id`, `p_value_raw`, `q_value_adj`, `chip_overlap_pct`

5. **heatmap.png**: Visual representation of enrichment patterns

## System Checks
The pipeline performs pre-flight checks for:
- Available RAM (≥16GB)
- Available disk space (≥14GB)
- Runtime duration (<6 hours)

If any check fails, the pipeline exits with a clear error message.

## Data Sources
- ENCODE: ATAC-seq/ChIP-seq peak files for human cell lines
- JASPAR: Transcription factor motif database

## License
See LICENSE file for details.
