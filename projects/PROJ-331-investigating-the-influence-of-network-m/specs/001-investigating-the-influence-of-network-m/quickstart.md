# Quickstart: Investigating the Influence of Network Motifs on Resting‑State Functional Connectivity

## Prerequisites

- Python 3.11+
- Git
- Access to HCP S1200 data (or pre-downloaded data in `data/raw/`)
- 7GB+ RAM, 14GB+ Disk

## Installation

1. **Clone and Setup**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-331-investigating-the-influence-of-network-m
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r code/requirements.txt
   ```

2. **Data Preparation**:
   - **CI Note**: For CI runs, ensure HCP data is pre-seeded in `data/raw/` via a GitHub Secret volume mount or pre-run script, as interactive login is not supported.
   - Download Schaefer atlas files and place in `data/raw/atlas/`.
   - Create a `subjects.txt` file with a set of HCP IDs (one per line).
   - **Generate Checksums**: Run `python code/utils.py --generate-checksums` to create `data/raw/.checksums.json` before running the pipeline. This is required for Phase 1 data hygiene checks.

## Running the Pipeline

### 1. Preprocessing (Download & Parcellation)
```bash
python code/download.py --subjects data/subjects.txt --output data/processed/
python code/preprocess.py --input data/processed/ --atlas data/raw/atlas/
```
*Output*: `structural.npy`, `structural_weighted.npy`, `rsfc.npy`, `metrics.json` for each subject.

### 2. Motif Quantification
```bash
python code/motifs.py --input data/processed/ --output data/processed/ --null-iterations 100
```
*Output*: `motifs.json` per subject. **Note**: This step targets 100 null iterations to ensure ≤300s/subject. Multi-threshold aggregation is performed.

### 3. Statistical Analysis
```bash
python code/stats.py --input data/processed/ --output results/analysis_results.csv
```
*Output*: `analysis_results.csv` with correlations and p-values.

### 4. Report Generation
```bash
python code/report.py --input results/analysis_results.csv --output results/report.pdf
```
*Output*: `results/report.pdf` (scatter plots, disclaimers, power analysis).

## Verification

- Check `pipeline.log` for any "skipped" subjects.
- Verify `results/report.pdf` contains the mandatory disclaimer.
- Run unit tests:
  ```bash
  pytest tests/unit/
  ```

## Troubleshooting

- **Motif Timeout**: If `code/motifs.py` takes >300s, verify CPU load or reduce `--null-iterations` to a minimal testing value.
- **Missing Data**: The pipeline automatically skips subjects missing raw files. Check `pipeline.log` for warnings.
- **Zero Variance**: If a motif has no variance across subjects, it will be flagged in the report as "insufficient variance".