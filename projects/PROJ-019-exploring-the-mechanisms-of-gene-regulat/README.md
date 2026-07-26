# llmXive Project: Exploring the Mechanisms of Gene Regulation Across Different Cell Types

**Project ID**: PROJ-019
**Status**: MVP Implementation Complete

## Overview

This project implements an automated pipeline to explore gene regulation mechanisms by analyzing ATAC-seq and ChIP-seq data across five distinct cell types (GM, K562, HepG2, H1-hESC, IMR90). The pipeline downloads raw peak data from ENCODE, preprocesses it into a unified format, scans for transcription factor motifs using JASPAR and FIMO, calculates enrichment scores, and validates findings against independent ChIP-seq data.

## Prerequisites

- **Python**: 3.11+
- **Disk Space**: Minimum 14GB free space in the temporary directory (configurable).
- **RAM**: Minimum 7GB available (pipeline includes chunked processing to respect this limit).
- **External Tools**:
 - [FIMO](http://meme-suite.org/doc/fimo.html) (MEME Suite) must be installed and available in `PATH`.
 - [BEDTools](https://bedtools.readthedocs.io/) recommended for auxiliary operations.

## Installation

1. Clone the repository and navigate to the project root.
2. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```
3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```
4. Ensure `fimo` is in your system PATH.

## Project Structure

```text
.
├── code/
│ ├── config.py # Configuration constants and paths
│ ├── main.py # Orchestration entry point
│ ├── download.py # ENCODE data ingestion
│ ├── preprocess.py # BED parsing and background model generation
│ ├── scan.py # FIMO motif scanning
│ ├── enrichment.py # Fisher's exact test and BH correction
│ ├── visualize.py # Heatmap generation
│ ├── validate.py # ChIP-seq overlap validation
│ ├── summary_table.py # Final summary generation
│ └── utils/
│ ├── disk_check.py # Disk space verification
│ └── network.py # Retry logic for downloads
├── data/
│ ├── raw/ # Downloaded ENCODE files
│ ├── interim/ # Standardized BED files and background models
│ └── processed/ # Final results (CSV, JSON, PNG)
├── tests/
│ ├── unit/ # Unit tests
│ └── integration/ # Integration tests
├── requirements.txt # Python dependencies
└── README.md # This file
```

## Usage

### Running the Full Pipeline

Execute the main orchestration script:

```bash
python code/main.py
```

This will:
1. Verify disk space requirements.
2. Download peak data for all 5 cell types from ENCODE.
3. Preprocess data and generate background models.
4. Scan peaks for motifs using FIMO.
5. Calculate enrichment scores and adjust p-values.
6. Generate visualizations and validation reports.

### Output Artifacts

Upon successful completion, the `data/processed/` directory will contain:
- `ingestion_summary.json`: Peak counts per cell type.
- `enrichment_matrix.csv`: Motif enrichment scores (q-values) per cell type.
- `heatmap.png`: Clustered visualization of enrichment results.
- `validation_report.json`: Overlap statistics against independent ChIP-seq data.
- `summary_table.csv`: Consolidated final results with motif IDs, p-values, q-values, and ChIP-seq overlap percentages.

## Configuration

Edit `code/config.py` to customize:
- `TMP_DIR`: Temporary directory for large downloads (default: system temp).
- `MIN_DISK_SPACE_BYTES`: Minimum required free space (default: ~14GB).
- `ENCODE_VERSION`: Version of ENCODE data to fetch.
- `JASPAR_VERSION`: Version of JASPAR database to use.

## Testing

Run the test suite using `pytest`:

```bash
pytest tests/ -v
```

## Dependencies

Key dependencies include:
- `pandas`: Data manipulation.
- `pybedtools`: BED file handling.
- `scipy`, `statsmodels`: Statistical tests (Fisher's exact, BH correction).
- `seaborn`, `matplotlib`: Visualization.
- `biopython`: Sequence handling.
- `requests`: HTTP operations.

## License

[Insert License Information Here]
