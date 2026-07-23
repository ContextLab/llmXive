# Quickstart: Single-Cell Trajectories of T-Cell Exhaustion

## Prerequisites

- Python 3.10+
- R 4.3+ (for Seurat preprocessing)
- Git
- Access to GitHub Actions runner (or local environment with 2 CPU cores, 7 GB RAM)

## Installation

1. **Clone Repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-003-single-cell-trajectories-of-t-cell-exhau
   ```

2. **Create Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```

## Data Download

**Critical Step**: Verify dataset availability before proceeding.

```bash
# Attempt to download raw count matrices (replace with actual download commands)
python code/download_data.py --datasets GSE136103,GSE127465,GSE111075,GSE138852
```

**Note**: If any dataset fails to download (due to access restrictions), the pipeline will halt and report the gap.

## Running the Pipeline

### 1. Preprocessing (Seurat v4)
```bash
python code/preprocess.py --input data/raw/ --output data/processed/
```

### 2. Velocity Estimation (scVelo)
```bash
python code/velocity.py --input data/processed/ --output data/processed/
```

### 3. Fork-Point Identification
```bash
python code/forkpoint.py --input data/processed/ --output data/results/fork_points/
```

### 4. Validation & Reporting
```bash
python code/validate.py --input data/results/fork_points/ --output data/results/validation/
python code/report.py --input data/results/validation/ --output data/results/report/
```

## Expected Outputs

- `data/results/fork_points/ranked_genes.csv`: List of fork-point genes with timing ranks.
- `data/results/validation/enrichment_report.json`: Bootstrap enrichment statistics.
- `data/results/report/final_report.html`: Final report with heatmaps and disclaimers.

## Troubleshooting

- **Dataset Download Failed**: Check GEO/SRA status; verify accession IDs; abort if no open substitute exists.
- **Memory Overflow**: Reduce dataset size via sampling; enable streaming.
- **scVelo Convergence Failed**: Increase regularization; retry; flag as "Alignment Failed".
- **No Significant Fork-Points**: Check divergence threshold; verify data quality.
