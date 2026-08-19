# PROJ-019: Exploring the Mechanisms of Gene Regulation Across Different Cell Types

## Overview

This project investigates gene regulation mechanisms by analyzing ATAC-seq and ChIP-seq peak data across five distinct cell types: GM12878, K562, HepG2, H1-hESC, and IMR90. The pipeline downloads raw data from ENCODE, preprocesses it into a unified format, scans for transcription factor motifs using FIMO/JASPAR, calculates enrichment scores, and generates visualizations.

## Prerequisites

- **Python**: 3.11+
- **Disk Space**: Minimum 14GB free space required for intermediate files and downloads.
- **RAM**: ~7GB recommended for processing large datasets.
- **External Tools**:
 - `FIMO` (MEME Suite): Required for motif scanning. Install via `conda install -c bioconda meme` or `apt-get install meme`.
 - `JASPAR` database: Downloaded automatically or provided via environment variable.

## Installation

1. **Clone the repository** and navigate to the project root.
2. **Create a virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```
3. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

## Directory Structure

```text
PROJ-019-exploring-the-mechanisms-of-gene-regulat/
├── code/ # Source code
│ ├── config.py # Configuration and path constants
│ ├── main.py # Orchestration logic
│ ├── download.py # ENCODE data ingestion
│ ├── preprocess.py # BED parsing and gene annotation
│ ├── scan.py # FIMO motif scanning
│ ├── enrichment.py # Fisher's exact test and BH correction
│ ├── visualize.py # Heatmap generation
│ ├── validate.py # Cross-validation against ChIP-seq
│ ├── summary_table.py # Final summary generation
│ ├── ingest.py # BED parsing utilities
│ ├── provenance.py # Data provenance tracking
│ └── utils/ # Utility modules
│ ├── disk_check.py # Disk space verification
│ └── network.py # Retry logic for downloads
├── data/
│ ├── raw/ # Downloaded ENCODE files
│ ├── interim/ # Intermediate processed files
│ ├── processed/ # Final outputs (JSON, CSV, PNG)
│ └── provenance.json # Data lineage record
├── specs/
│ └── 001-gene-regulation/
│ ├── quickstart.md # Detailed execution guide
│ └──...
├── tests/ # Unit and contract tests
├── requirements.txt # Python dependencies
└── pyproject.toml # Linting and formatting config
```

## Quick Start

To run the full pipeline end-to-end:

```bash
python code/main.py
```

This command executes the following stages in order:
1. **Disk Check**: Verifies sufficient free space.
2. **Ingestion**: Downloads ENCODE peak files and parses them.
3. **Preprocessing**: Annotates peaks with gene symbols and builds background models.
4. **Scanning**: Runs FIMO to identify motif occurrences.
5. **Enrichment**: Calculates statistical significance of motif enrichment.
6. **Visualization**: Generates heatmaps and calculates clustering quality.
7. **Validation**: Cross-references with independent ChIP-seq data.
8. **Reporting**: Generates final summary tables and JSON reports.

**Outputs** are saved to `data/processed/`:
- `ingestion_summary.json`: Peak counts and metadata.
- `enrichment_matrix.csv`: Motif enrichment scores per cell type.
- `heatmap.png`: Clustering visualization of enrichment profiles.
- `validation_report.json`: Overlap statistics and top motifs.
- `summary_table.csv`: Consolidated results.

## Configuration

Edit `code/config.py` to modify:
- `TMP_DIR`: Directory for temporary files (default: `data/interim/`).
- `DATA_RAW_DIR`, `DATA_INTERIM_DIR`, `DATA_PROCESSED_DIR`: Output paths.
- `ENCODE_VERSION`: Dataset version to download.
- `JASPAR_VERSION`: Motif database version.

## Testing

Run the test suite with `pytest`:

```bash
pytest tests/ -v
```

Specific test modules:
- `tests/unit/test_ingest.py`: BED parsing edge cases.
- `tests/unit/test_network.py`: Network retry logic.
- `tests/unit/test_background.py`: Background model aggregation.
- `tests/unit/test_motifs.py`: Fisher's exact test and BH correction.
- `tests/unit/test_viz.py`: Heatmap silhouette scoring.
- `tests/unit/test_validate.py`: ChIP-seq overlap calculation.

## License

This project is for research purposes. Data from ENCODE and JASPAR is subject to their respective licenses.
