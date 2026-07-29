# Quickstart: Exploring the Correlation Between Musical Preference and Personality Traits

This guide shows how to run the full analysis on a fresh GitHub Actions runner (or locally) using the provided scripts.

## Prerequisites
- Python 3.11
- Internet access (to download the OpenML Personality‑Music dataset)
- GitHub Actions free‑tier runner (2 CPU cores, ≤ 6 GB RAM)

## Setup

```bash
# 1. Clone the repository
git clone https://github.com/your-org/PROJ-049-exploring-the-correlation-between-musica.git
cd PROJ-049-exploring-the-correlation-between-musica

# 2. Create a virtual environment and install dependencies
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt   # pins exact versions
```

## Run the Full Pipeline

```bash
# Step 0: Ingest raw data (download + checksum verification)
python -m code.ingest

# Step 1: Preprocess (genre mapping, proportion, log transform, imputation)
python -m code.preprocess

# Step 2: Power analysis (reports required sample size)
python -m code.analysis --power

# Step 3: Statistical analysis (correlation, regression, diagnostics, corrections)
python -m code.analysis

# Step 4: Visualizations (heatmaps, coefficient plots, diagnostics)
python -m code.visualize

# Step 5: Generate final report CSV
python -m code.report
```

All intermediate and final artifacts will appear under `data/processed/` and `results/`.

## Verify Outputs (Contract Tests)

```bash
pytest -q tests/contract
```

Successful tests confirm that:
- `data/processed/merged_clean.csv` matches `contracts/processed_dataset.schema.yaml`.
- `data/processed/analysis_results.csv` matches `contracts/analysis_output.schema.yaml`.
- `data/processed/coefficient_deltas.csv` matches `contracts/results.schema.yaml`.
- `results/results_report.csv` matches `contracts/report.schema.yaml`.
- Required figures (`*.png`) exist.

## Reproducibility
- Random seeds are fixed in `code/utils.py`.
- External downloads are deterministic (same OpenML ID, same dataset version).
- Checksums are stored in `data/checksums.txt`; the ingest script aborts if mismatched.

---



