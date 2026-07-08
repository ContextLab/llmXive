# Quickstart: Assessing the Reliability of Statistical Significance in Openly Available Genomic Datasets

## Prerequisites

- Python 3.11+
- R 4.3+ (with `DESeq2` and `edgeR` installed)
- `git`, `curl`, `make`

## Installation

1. **Clone and Setup Environment**
   ```bash
   git checkout 001-assess-significance-reliability
   cd projects/PROJ-330-assessing-the-reliability-of-statistical
   python -m venv venv
   source venv/bin/activate
   pip install -r code/requirements.txt
   ```

2. **Install R Dependencies**
   ```bash
   # Ensure R is installed, then run:
   Rscript -e "if (!requireNamespace('BiocManager', quietly = TRUE)) install.packages('BiocManager'); BiocManager::install(c('DESeq2', 'edgeR'))"
   ```

3. **Verify Data Sources**
   Ensure you have network access to fetch datasets from the verified URLs (HuggingFace).
   The pipeline will automatically download and checksum data on first run.

## Running the Pipeline

Execute the main analysis script:

```bash
python code/main.py
```

**Expected Output**:
- `data/raw/`: Downloaded datasets.
- `data/processed/`: Filtered count matrices and metadata.
- `artifacts/results/`:
  - `stability_summary.json`: Stability correlations and inflation metrics.
  - `plots/`: Bland-Altman plots and histograms.
  - `report.md`: Final summary.

## Configuration

Edit `code/src/config.py` to:
- Change `MAX_RUNTIME_HOURS` (default: 6).
- Set `MIN_PERMUTATIONS` (default: 100).
- Toggle `USE_RPY2` (True/False) to switch between R and Python DE methods.

## Troubleshooting

- **Runtime Error**: "Memory Limit Exceeded".
  - *Solution*: The pipeline should automatically reduce permutation count. If it fails, reduce `MIN_PERMUTATIONS` in config.
- **Missing Metadata**: "Batch metadata absent".
  - *Solution*: The pipeline will default to random stratification. Check logs for warning.
- **R Script Failure**:
  - *Solution*: Ensure R packages `DESeq2` and `edgeR` are installed in the system R environment. If `rpy2` fails, the pipeline will fallback to `subprocess`.
