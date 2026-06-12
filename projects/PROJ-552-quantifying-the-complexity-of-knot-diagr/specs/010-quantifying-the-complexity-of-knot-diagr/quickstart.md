# Quickstart: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

## Prerequisites

- Python 3.11 or higher
- Access to stable internet connectivity for downloading data from Knot Atlas
- Git for version control
- Standard CI/runner resources (GitHub Actions compatible)

## Installation

1. Clone the repository and navigate to the project directory:
```bash
cd projects/PROJ-552-quantifying-the-complexity-of-knot-diagr
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Pipeline

### Step 1: Download Knot Data

```bash
python code/download/download_knot_data.py
```

This will:
- Download prime knot data from Knot Atlas (https://katlas.org)
- Apply retry logic with exponential backoff on failures
- Cache partial results after 3 consecutive failures
- Save raw data to `data/raw/knot_atlas_export.csv`

### Step 2: Validate and Clean Data

```bash
python code/analysis/precision_validation.py
```

This will:
- Parse and clean the dataset
- Flag records with missing invariant data
- Apply tie-breaking rules for diagram representation ties
- Save cleaned data to `data/processed/cleaned_knots.csv`

### Step 3: Run Exploratory Analysis

```bash
python code/analysis/exploratory_analysis.py
```

This will:
- Generate scatter plots of crossing number vs. braid index
- Stratify by alternating/non-alternating classification
- Save plots to `data/plots/` directory (minimum 1200x900 pixels)

### Step 4: Fit Regression Models

```bash
python code/analysis/regression_models.py
```

This will:
- Fit linear, polynomial, and logarithmic regression models
- Compute goodness-of-fit metrics (R², AIC/BIC, MAE)
- Perform residual analysis to identify deviating knot families
- Save results to `data/processed/regression_results.json`

### Step 5: Generate Reproducibility Documentation

```bash
python code/reproducibility/checksums.py
python code/reproducibility/logs.py
```

This will:
- Generate SHA-256 checksums for all data files
- Create timestamped logs for all operations
- Document random seed values used

## Verifying Results

Run the validation script to ensure reproducibility:

```bash
python code/reproducibility/validation_scripts.py
```

This checks:
- All checksums match recorded values
- Tie-breaking rules applied consistently
- All required documentation files present
- Exit code 0 on successful validation

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Knot Atlas unavailable | Check network connectivity; retry logic will apply exponential backoff automatically |
| Missing invariant data | Check `docs/reproducibility/data_quality_report.md` for flagged records |
| Ambiguous alternating classification | Records marked "unclassifiable" in dataset; excluded from stratified analysis |
| Zero hyperbolic volume | Records filtered out for volume prediction analysis; count logged in `docs/reproducibility/excluded_knots.md` |
