# PROJ-340: Investigating the Correlation Between Gut Microbiome Composition and Sleep Architecture

**Status**: Pipeline Ready for Real Data Execution (Validation Mode Active)

## Overview
This project implements a rigorous, automated pipeline to investigate correlations between gut microbiome taxa abundance and sleep architecture metrics. The pipeline enforces strict data integrity checks, compositional data corrections (SparCC/SpiecEasi), and causal language validation.

## Key Features
- **Strict Real-Data Enforcement**: The pipeline will fail loudly if real data is not found; no synthetic fallbacks are permitted in production runs.
- **Compositional Correction**: Automatic detection and correction for microbiome compositionality.
- **Robust Statistical Analysis**: ZINB/Hurdle models for zero-inflated data, Spearman/Pearson for normal distributions.
- **Causal Language Guardrails**: Automated scanning of reports to prevent causal over-interpretation.
- **Chain of Custody**: Full audit trail from ingestion to final report.

## Project Structure
```
.
├── code/ # Core pipeline logic
│ ├── ingest.py # Data loading, validation, outlier detection
│ ├── analysis.py # Correlation analysis, method selection
│ ├── diagnostics.py # Collinearity checks, power analysis
│ ├── report.py # Report generation
│ └──...
├── data/
│ ├── raw/ # Raw input data (CSV/TSV)
│ ├── processed/ # Cleaned/filtered data (Parquet)
│ ├── results/ # Analysis outputs (JSON, CSV, MD)
│ ├── config/ # Configuration files
│ └── citations/ # Verified DOI records
├── tests/ # Unit and integration tests
├── specs/ # Design documents and contracts
├── docs/ # Detailed documentation
└── quickstart.md # Execution instructions
```

## Prerequisites
- Python 3.11+
- `pip install -r requirements.txt`

## Quick Start
### 1. Configuration
Ensure `data/config/real_data_sources.yaml` points to a valid, real data source.
```yaml
# Example: data/config/real_data_sources.yaml
sources:
 - name: "GutMicrobiomeSleep_CohortA"
 type: "csv"
 url: "" # Replace with real URL
 checksum: "sha256:..."
```

### 2. Running the Pipeline
The pipeline executes in two modes:
- **Validation Mode**: Generates synthetic data for local testing (disabled by default in CI).
- **Real Data Mode**: Fetches and processes real data. **Requires valid source config.**

**Run Full Pipeline:**
```bash
# Note: This will fail if real data is not configured.
python code/main.py
```

**Run with Synthetic Data (Local Testing Only):**
```bash
python code/ingest.py --mode synthetic --output data/raw/synthetic_data.csv
python code/main.py --input data/raw/synthetic_data.csv --output data/results/
```

## Known Limitations
- **Data Availability**: The pipeline requires a real, programmatically accessible dataset. If `data/config/real_data_sources.yaml` is missing or points to an invalid URL, execution halts immediately.
- **Compute Resources**: The full 6-hour stress test is skipped in standard runs; timing evidence is recorded for the actual execution time.
- **GPU Requirements**: If specific deep learning models are enabled (future work), the pipeline will detect GPU requirements and fail on CPU-only runners.

## Verification
- Run `python scripts/verify_integrity.py` to validate artifact checksums.
- Run `python scripts/final_validation.py` to ensure statistical methods match data distributions.
- Run `python scripts/review_power_sensitivity.py` to check power analysis completeness.

## Citation
See `data/citations/verified_dois.yaml` for verified sources used in this analysis.
