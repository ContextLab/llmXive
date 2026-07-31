# Investigating the Correlation Between Gut Microbiome Composition and Sleep Architecture

## Overview

This project implements a robust, reproducible pipeline to analyze the associational relationships between gut microbiome composition and sleep architecture metrics.

## ⚠️ Real-Data Policy

**This pipeline is designed for REAL DATA ONLY.**

- **No Synthetic Data**: The production pipeline **will not run** on synthetic or mock data.
- **Fail Loudly**: If a verified real dataset is not provided, the pipeline will halt immediately with a clear error.
- **No Fabrication**: All results must be derived from actual measurements. Invented numbers are strictly prohibited.

### How to Obtain Real Data
To run this analysis, you must provide a dataset from a verified source:
1. **NCBI SRA / GenBank**: Search for metagenomic sequencing data linked with clinical sleep studies.
2. **Zenodo / Figshare**: Look for open-access datasets with DOI citations.
3. **Requirements**: The dataset must include:
 - **Predictors**: Taxa abundance counts (e.g., Bacteroides, Firmicutes, etc.)
 - **Outcomes**: Sleep metrics (e.g., REM duration, SWS duration, etc.)
 - **Citation**: A valid DOI or reference ID for verification.

Place your verified dataset at `data/raw/real_data.csv` before running the pipeline.

## Project Structure

```
.
├── code/ # Pipeline implementation
│ ├── main.py # Orchestration entry point
│ ├── ingest.py # Data loading & validation
│ ├── analysis.py # Correlation analysis logic
│ ├── diagnostics.py # VIF, Power, Sensitivity checks
│ └── report.py # Report generation
├── data/
│ ├── raw/ # Input data (real_data.csv)
│ ├── processed/ # Intermediate processed data
│ ├── results/ # Final outputs (JSON, MD)
│ └── config/ # Schema and variable definitions
├── specs/ # Design documents & schemas
├── tests/ # Unit and integration tests
├── quickstart.md # Execution guide
└── README.md # This file
```

## Quick Start

1. **Install Dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

2. **Provide Real Data**:
 Ensure `data/raw/real_data.csv` exists with a valid DOI/citation.

3. **Run Analysis**:
 ```bash
 python code/main.py --input data/raw/real_data.csv --output data/results/
 ```

4. **View Results**:
 Check `data/results/final_report.md` for the associational analysis summary.

## Architecture Highlights

- **Dynamic Method Selection**: Automatically selects ZINB, Spearman, or Pearson based on data distribution.
- **Compositional Correction**: Applies CLR transformation for microbiome data.
- **Robust Diagnostics**: Includes VIF, Power Analysis, and Sensitivity checks.
- **Constitution Compliance**: Enforces associational framing and prevents causal language in reports.
- **Fail-Loudly Design**: Stops immediately on missing data or invalid schemas.

## Contributing

When contributing:
- **Never** introduce synthetic data fallbacks for production logic.
- **Always** ensure new data loaders fetch from real, verifiable sources.
- **Update** documentation if new required variables are added.

## License

[Project License]