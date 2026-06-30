# Quickstart: Exploring the Mechanisms of Gene Regulation Across Different Cell Types

## Prerequisites

*   Python 3.11+
*   MEME Suite (FIMO) installed and in `PATH` (or use Docker/conda).
*   14GB free disk space.
*   Internet access (for ENCODE download).

## Installation

1.  **Clone the repository** (or navigate to the project directory).
2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: If FIMO is not installed system-wide, you may need to install MEME Suite via conda or download binaries.*

## Configuration

Edit `src/utils/config.py` or set environment variables:
*   `TMP_DIR`: Path for temporary files (default: `/tmp`).
*   `DATA_DIR`: Path to `data/` (default: `./data`).
*   `ENCODE_API_URL`: Base URL for ENCODE (default: `https://www.encodeproject.org`).

## Running the Pipeline

### Step 1: Data Ingestion
Download and parse peak files for all 5 cell types.
```bash
python -m src.ingest.download --cell-types GM12878,K562,HepG2,H1-hESC,IMR90
python -m src.ingest.parse --input-dir data/raw --output-dir data/processed
```
*This step includes exponential backoff for ENCODE API and checksum verification.*

### Step 2: Motif Scanning
Scan peaks for TF motifs using FIMO.
```bash
python -m src.analysis.motif_scan --peaks data/processed/annotated_peaks.parquet --motifs JASPAR2024 --pval 0.0001
```

### Step 3: Enrichment Analysis
Compute Fisher's exact test and BH correction.
```bash
python -m src.analysis.enrichment --matches data/processed/motif_matches.jsonl --output data/results/enrichment.csv
```

### Step 4: Visualization & Validation
Generate heatmap and cross-validate with ChIP-seq.
```bash
python -m src.viz.heatmap --input data/results/enrichment.csv --output data/results/heatmap.png
python -m src.viz.validation --enrichment data/results/enrichment.csv --output data/results/validation.csv
```

### Step 5: Generate Report
```bash
python -m src.main --full-run
```

## Troubleshooting

*   **Disk Space Error**: Ensure `TMP_DIR` has ≥14GB free.
*   **ENCODE Rate Limit**: The script automatically retries with exponential backoff. If it fails after 3 retries, check your network or provide raw files manually.
*   **FIMO Not Found**: Install MEME Suite: `conda install -c bioconda meme`.
