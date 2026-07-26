# Quickstart Guide: Gene Regulation Mechanisms Pipeline

This guide provides a step-by-step walkthrough to run the gene regulation analysis pipeline on a local machine or CI environment.

## 1. Environment Setup

Ensure you have the following:
- Python 3.11 or higher.
- At least **14GB** of free disk space.
- At least **7GB** of available RAM.
- **FIMO** (from MEME Suite) installed and accessible via the command line.

### Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate # Windows: venv\Scripts\activate

# Install project requirements
pip install -r requirements.txt
```

## 2. Data Sources

The pipeline automatically downloads real data from the following sources:
- **ENCODE**: ATAC-seq/ChIP-seq peak files for GM, K562, HepG2, H1-hESC, and IMR90 cell types.
- **JASPAR**: Transcription factor motif database (CORE set).

*Note: No synthetic data is used. All analysis relies on these real biological datasets.*

## 3. Running the Pipeline

Execute the main script from the project root:

```bash
python code/main.py
```

### What Happens During Execution?

1. **Preflight Checks**: Verifies disk space and network connectivity.
2. **Ingestion**: Downloads raw peak files to `data/raw/`.
3. **Preprocessing**: Converts files to standardized BED format in `data/interim/` and builds a background model (union of peaks from other cell types).
4. **Motif Scanning**: Runs FIMO against the JASPAR database to identify motif occurrences in peaks.
5. **Enrichment Analysis**: Computes Fisher's exact test p-values and applies Benjamini-Hochberg correction to generate q-values.
6. **Validation**: Fetches independent ChIP-seq data to validate top motifs and calculates overlap percentages.
7. **Visualization**: Generates a heatmap of enrichment results and a final summary table.

## 4. Expected Outputs

After the script completes successfully, check the `data/processed/` directory for:

| File | Description |
|:--- |:--- |
| `ingestion_summary.json` | Summary of peak counts per cell type. |
| `enrichment_matrix.csv` | Matrix of motif q-values across cell types. |
| `heatmap.png` | Clustered heatmap of enrichment scores. |
| `validation_report.json` | Statistics on motif validation against ChIP-seq data. |
| `summary_table.csv` | Final consolidated table with motif IDs, p-values, q-values, and ChIP-seq overlap %. |

## 5. Troubleshooting

### Disk Space Error
If you see an error about insufficient disk space, ensure `TMP_DIR` in `code/config.py` points to a partition with >14GB free space.

### FIMO Not Found
Ensure the `fimo` command is available in your system PATH. You can install it via the MEME Suite package manager or conda.

### Network Timeouts
The pipeline includes exponential backoff for network requests. If downloads fail repeatedly, check your internet connection or firewall settings.

## 6. Verification

To verify the pipeline ran correctly:
1. Check that `data/processed/summary_table.csv` exists and contains rows with `q_value_adj` < 0.05.
2. Open `data/processed/heatmap.png` to see distinct clustering of cell types.
3. Review `data/processed/validation_report.json` to confirm the silhouette score is logged (warning if < 0.4, but execution continues).

## 7. Next Steps

- **Analyze Results**: Use `data/processed/summary_table.csv` to identify top regulatory motifs.
- **Extend Analysis**: Modify `code/validate.py` to include additional independent datasets.
- **Performance**: For larger datasets, consider increasing the `CHUNK_SIZE` in `code/enrichment.py` or running FIMO in parallel (if hardware permits).