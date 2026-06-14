# Quickstart: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

**Feature Branch**: `001-knot-complexity-analysis`  
**Date**: 2026-06-12  

## Prerequisites

- Python 3.11 or higher
- pip package manager
- Stable internet connection (for data download)

## Installation

1.  Clone the repository and navigate to the project directory.
2.  Create a virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate  # Linux/macOS
    # venv\Scripts\activate  # Windows
    ```
3.  Install dependencies (pinned versions):
    ```bash
    pip install pandas>=2.0.0 statsmodels>=0.14.0 matplotlib>=3.8.0 pyyaml>=6.0 requests>=2.31.0 numpy>=1.24.0 pytest>=7.4.0
    ```

## Execution Workflow

### 1. Data Download
Download Knot Atlas data with retry logic:
```bash
python code/download/knot_atlas_loader.py --output data/raw/knot_atlas_raw.json
```
*Note: Implements exponential backoff per FR-008.*

### 2. Data Cleaning & Validation
Parse, clean, and validate invariants:
```bash
python code/analysis/invariant_validation.py --input data/raw/knot_atlas_raw.json --output data/processed/cleaned_knots.parquet
```
*Generates `docs/reproducibility/data_quality_report.md` and `docs/reproducibility/invariant_coverage.md`.*

### 3. Analysis & Modeling
Run regression analysis and generate plots:
```bash
python code/analysis/regression_models.py --input data/processed/cleaned_knots.parquet --output data/processed/regression_results.json
python code/analysis/plots.py --input data/processed/cleaned_knots.parquet --output data/plots/
```
*Generates `docs/reproducibility/multicollinearity_assessment.md` and `docs/reproducibility/residual_analysis.md`.*

### 4. Reproducibility Check
Verify checksums and logs:
```bash
python code/reproducibility/checksums.py --data-dir data/ --output docs/reproducibility/validation_status.md
```

## Reproducibility Requirements

- **Random Seeds**: Pinned in code; values documented in `docs/reproducibility/random_seeds.md`.
- **Checksums**: SHA-256 for all data files; recorded in `data/` manifest.
- **Logs**: Timestamped operation logs in `docs/reproducibility/`.
- **Derivation Notes**: Step-by-step transformation logic in `docs/reproducibility/derivation_notes.md`.

## Troubleshooting

- **API Unavailable**: Retry logic applies exponential backoff; partial results cached to disk.
- **Missing Invariants**: Records flagged with `missing_invariant_flags` rather than excluded.
- **Validation Failure**: If `docs/reproducibility/validation_status.md` reports errors, re-run cleaning step.
