# Quickstart: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

## Prerequisites

- Python 3.11 or higher
- Stable internet connection (for downloading data from Knot Atlas)
- At least 2GB available disk space
- Git for version control

## Installation

### Step 1: Clone Repository

```bash
git clone <repository-url>
cd projects/PROJ-552-quantifying-the-complexity-of-knot-diagr
```

### Step 2: Create Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

**Dependencies** (pinned in requirements.txt):
- pandas
- numpy
- scipy
- statsmodels
- matplotlib
- seaborn
- requests
- pyyaml
- pytest

### Step 4: Verify Installation

```bash
pytest tests/unit/
```

## Running the Analysis Pipeline

### Step 1: Download Knot Data

```bash
python code/main.py --task download
```

**Expected Behavior**:
- Downloads knot data from Knot Atlas (https://katlas.org)
- Implements retry logic with exponential backoff (initial=1s, max=32s, multiplier=2)
- Caches partial results after 3 consecutive failures
- Saves raw data to data/raw/knot_atlas_raw.json

**Note**: If Knot Atlas is unavailable, check docs/reproducibility/validation_scope.md for status.

### Step 2: Parse and Clean Data

```bash
python code/main.py --task clean
```

**Expected Behavior**:
- Parses raw JSON and extracts consistent representations
- Flags records with data quality issues
- Filters to hyperbolic knots (volume > 0)
- Saves cleaned data to data/processed/knots_cleaned.csv

### Step 3: Generate Exploratory Plots

```bash
python code/main.py --task exploratory
```

**Expected Behavior**:
- Creates scatter plots of crossing number vs. braid index
- Stratifies by alternating/non-alternating classification
- Saves PNG files to data/plots/ with minimum resolution 1200x900 pixels

### Step 4: Fit Regression Models

```bash
python code/main.py --task regression
```

**Expected Behavior**:
- Fits linear, polynomial, and logarithmic regression models
- Computes goodness-of-fit metrics (R², AIC/BIC, MAE)
- Performs multicollinearity assessment (VIF)
- Saves model results to analysis/regression_models/

### Step 5: Perform Residual Analysis

```bash
python code/main.py --task residuals
```

**Expected Behavior**:
- Identifies knot families with residuals ≥2 standard deviations from global trend
- Documents specific hyperbolic knot families that deviate significantly
- Saves results to docs/reproducibility/residual_analysis.md

### Step 6: Generate Reproducibility Documentation

```bash
python code/main.py --task reproducibility
```

**Expected Behavior**:
- Generates SHA-256 checksums for all data files
- Creates timestamped logs
- Documents random seed values
- Generates derivation notes with formula citations

## Verifying Results

### Contract Tests

```bash
pytest tests/contract/
```

**Expected**: All contract tests pass against schema definitions in contracts/

### Integration Tests

```bash
pytest tests/integration/
```

**Expected**: Pipeline executes end-to-end without errors

### Validation Status

Check validation status in:
- docs/reproducibility/validation_status.md (tie-breaking validation)
- docs/reproducibility/data_quality_report.md (data quality metrics)
- docs/reproducibility/hyperbolic_volume_validation.md (volume validation against KnotInfo)

## Common Issues

### Issue 1: Knot Atlas Unavailable

**Symptom**: Download fails with connection error

**Solution**: 
- Retry logic automatically applies exponential backoff
- Partial results cached after 3 consecutive failures
- Check docs/reproducibility/validation_scope.md for status

### Issue 2: Missing Invariant Data

**Symptom**: Records flagged with missing_invariant_flags

**Solution**:
- Records are NOT silently excluded
- Check docs/reproducibility/data_quality_report.md for flag summary
- Phase 1 conclusions limited to validated crossing number ≤10 data

### Issue 3: Validation Script Fails

**Symptom**: Non-zero exit code from validation script

**Solution**:
- Check docs/reproducibility/validation_status.md for error details
- Re-run invariant computations before proceeding to downstream analysis
- Ensure tie-breaking rules applied consistently

## Next Steps

After completing the quickstart:

1. Review docs/reproducibility/ for full reproducibility documentation
2. Examine data/plots/ for exploratory analysis visualizations
3. Read analysis/regression_models/ for model comparison results
4. Consult docs/reproducibility/residual_analysis.md for outlier family identification

For Phase 2+ scope (additional invariants: arc index, Seifert circle count, bridge number), refer to FR-003 for implementation requirements.