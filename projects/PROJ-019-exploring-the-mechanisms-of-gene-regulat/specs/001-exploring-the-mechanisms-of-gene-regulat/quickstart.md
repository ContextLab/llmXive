# Quickstart: Exploring the Mechanisms of Gene Regulation Across Different Cell Types

## Prerequisites

*   Python 3.11+
*   `memsuite` (for FIMO) installed in PATH or via `conda`
*   `pybedtools` installed (via pip)
*   Access to a Linux environment (GitHub Actions or local)

## Installation

1.  **Clone the repository** and navigate to the project directory.
2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: Ensure `fimo` is available in your PATH. If not, install via `conda install -c bioconda fimo`.*

## Configuration

Set the `TMP_DIR` environment variable if you need to use a non-default temporary directory (default is `/tmp`). Ensure at least 14GB of free space is available in the chosen directory.

```bash
export TMP_DIR="/tmp/gene-regulation"
```

## Running the Pipeline

Execute the main orchestrator script:

```bash
python code/main.py
```

This will:
1.  Download peak data from ENCODE (with retry logic).
2.  Parse and annotate peaks.
3.  Generate GC-matched background regions.
4.  Scan for motifs using FIMO.
5.  Compute enrichment and apply BH correction.
6.  Generate visualizations and validation reports.

## Output

Results are stored in `data/processed/`:
*   `enrichment_matrix.parquet`: Motif enrichment scores per cell type.
*   `heatmap.png`: Clustering visualization.
*   `validation_report.json`: Cross-validation statistics.
*   `provenance.json`: Checksums and version info.

## Troubleshooting

*   **ENCODE 403 Error**: The script will retry with exponential backoff. If it fails after 3 retries, check your network or ENCODE status.
*   **Disk Space**: If the script fails due to low disk space, increase `TMP_DIR` space or clean up `/tmp`.
*   **FIMO Not Found**: Ensure `fimo` is installed and in your `PATH`.
