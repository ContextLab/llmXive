# Quickstart: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

## Prerequisites

- Python 3.11 or later
- pip package manager
- Stable internet connection (for Knot Atlas download)

## Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r code/requirements.txt
```

## Quick Run

```bash
# Download knot data with retry logic
python code/download/download_knot_data.py

# Run exploratory analysis
python code/analysis/exploratory_analysis.py

# Fit regression models
python code/analysis/regression_analysis.py

# Validate reproducibility artifacts
python code/validation/data_quality_check.py
```

## Output Locations

- Raw data: `data/raw/`
- Processed data: `data/processed/`
- Plots: `data/plots/`
- Reproducibility docs: `docs/reproducibility/`

## Verification

```bash
# Verify checksums
python code/reproducibility/checksums.py

# Check validation status
cat docs/reproducibility/validation_status.md
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Knot Atlas timeout | Retry logic applies exponential backoff automatically |
| Missing invariant data | Check docs/reproducibility/data_quality_report.md |
| Validation failure | Check docs/reproducibility/validation_status.md for details |
