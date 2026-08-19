# Quickstart Guide: Gene Regulation Mechanisms Analysis

This guide details the step-by-step execution of the PROJ-019 pipeline, from data ingestion to final validation.

## 1. Environment Setup

Ensure you have at least **14GB of free disk space** and **7GB of RAM**.

```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Ensure FIMO is available in PATH
fimo --version
```

## 2. Data Ingestion (User Story 1)

The pipeline automatically downloads peak data from ENCODE for the following cell types:
- GM12878
- K562
- HepG2
- H1-hESC
- IMR90

**Execution**:
```bash
python code/download.py
```
*Output*: Raw files saved to `data/raw/`.

**Preprocessing**:
```bash
python code/preprocess.py
```
*Output*: Standardized BED files and gene annotations in `data/interim/`.
*Note*: This step also constructs the dynamic background model (union of peaks from other cell types) as required by FR-004.

**Verification**:
Check `data/processed/ingestion_summary.json` for peak counts.
```bash
cat data/processed/ingestion_summary.json
```

## 3. Motif Scanning & Enrichment (User Story 2)

**Scanning**:
```bash
python code/scan.py
```
*Tool*: FIMO (p-value ≤ 0.0001).
*Database*: JASPAR CORE.
*Output*: Motif matches in `data/interim/motif_matches/`.

**Enrichment Calculation**:
```bash
python code/enrichment.py
```
*Method*: Fisher's Exact Test against the background model, followed by Benjamini-Hochberg correction.
*Output*: `data/processed/enrichment_matrix.csv` containing `motif_id`, `cell_type`, `p_value`, `q_value`.

## 4. Visualization & Validation (User Story 3)

**Heatmap Generation**:
```bash
python code/visualize.py
```
*Method*: Euclidean distance clustering (average linkage).
*Output*: `data/processed/heatmap.png`.
*Metric*: Silhouette score is calculated and logged. A score < 0.4 triggers a warning but does not stop execution.

**Validation**:
```bash
python code/validate.py
```
*Process*:
1. Filters motifs with `q_value < 0.05`.
2. Maps motif IDs to TF names and retrieves independent ChIP-seq peaks from ENCODE.
3. Calculates overlap percentage (Intersection over Union).
*Output*: `data/processed/validation_report.json`.

**Summary Table**:
```bash
python code/summary_table.py
```
*Output*: `data/processed/summary_table.csv` combining enrichment scores and validation overlaps.

## 5. Full Pipeline Execution

To run the entire workflow sequentially:

```bash
python code/main.py
```

This script:
1. Checks disk space (`code/utils/disk_check.py`).
2. Orchestrates ingestion, preprocessing, scanning, enrichment, visualization, and validation.
3. Generates all final artifacts in `data/processed/`.

## 6. Troubleshooting

- **Disk Space Error**: If you encounter `InsufficientDiskSpaceError`, free up space or update `TMP_DIR` in `code/config.py`.
- **Network Failure**: The pipeline uses exponential backoff (max 3 retries) for downloads. If it fails, check your internet connection or proxy settings.
- **FIMO Not Found**: Ensure MEME Suite is installed and `fimo` is in your system PATH.
- **Silhouette Score Warning**: A low score (< 0.4) indicates weak clustering but is not a fatal error. Review `data/processed/enrichment_matrix.csv` for data quality.

## 7. Data Provenance

All data sources are tracked in `data/provenance.json`, including:
- ENCODE Accession IDs
- JASPAR Version
- Download Timestamps
- Processing Steps

This ensures reproducibility and compliance with data integrity requirements.