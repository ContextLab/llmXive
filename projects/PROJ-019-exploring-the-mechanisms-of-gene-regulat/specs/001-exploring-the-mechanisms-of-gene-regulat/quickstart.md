# Quickstart Guide: Gene Regulation Pipeline

## Prerequisites
- Python 3.11+
- ≥16GB RAM (SC-004 requirement)
- ≥14GB free disk space (FR-002 requirement)
- FIMO (MEME suite) installed and in PATH
- Internet connection for data download

## Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Verify FIMO installation
fimo --version
```

## Running the Pipeline
Execute the complete pipeline end-to-end:
```bash
python -m code.main
```

This command will:
1. Run pre-flight checks (RAM, disk, time)
2. Download ENCODE peak data for 5 cell types
3. Parse and annotate peaks with gene symbols
4. Scan peaks for TF motifs using FIMO
5. Calculate motif enrichment against dynamic background
6. Generate heatmaps and validation reports
7. Produce final summary table

## Expected Output Artifacts
Upon successful completion, the following files will be created in `data/processed/`:

### 1. ingestion_summary.json
```json
{
 "total_peaks": 123456,
 "cell_types": ["GM12878", "K562", "HepG2", "H1-hESC", "IMR90"],
 "parsed_count": 5
}
```

### 2. enrichment_matrix.csv
Columns:
- `motif_id`: JASPAR ID format (e.g., 'MA0001.1')
- `cell_type`: One of ['GM12878', 'K562', 'HepG2', 'H1-hESC', 'IMR90']
- `p_value`: Raw p-value from Fisher's exact test
- `q_value`: Benjamini-Hochberg adjusted q-value

### 3. validation_report.json
```json
{
 "overlap_pct": 65.50,
 "top_motifs": [
 {
 "motif_id": "MA0001.1",
 "q_value": 0.0001,
 "overlap_pct": 70.25
 }
 ],
 "silhouette_score": 0.45,
 "silhouette_test_passed": true,
 "overlap_test_passed": true,
 "validation_passed": true
}
```

### 4. summary_table.csv
Columns:
- `motif_id`: JASPAR ID
- `p_value_raw`: Raw p-value
- `q_value_adj`: Adjusted q-value
- `chip_overlap_pct`: Percentage overlap with ChIP-seq data (2 decimal places)

### 5. heatmap.png
Visual heatmap of motif enrichment across cell types.

## Resource Requirements
- **RAM**: ≥16GB required (SC-004). The pipeline will exit with an error if less is available.
- **Disk**: ≥14GB free space required (FR-002). Intermediate files are stored in TMP_DIR (default: /tmp).
- **Time**: Pipeline should complete within 6 hours on CPU-only hardware.
- **Note**: Plan.md targets ~7GB RAM usage during execution, but SC-004 mandates 16GB minimum.

## Troubleshooting
- **RAM error**: Ensure system has ≥16GB available memory
- **Disk error**: Free up disk space or configure TMP_DIR to a larger partition
- **FIMO not found**: Install MEME suite and ensure `fimo` is in PATH
- **Network errors**: Check internet connection; the pipeline uses exponential backoff for retries