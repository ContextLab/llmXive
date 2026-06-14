# Quickstart: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

**Branch**: `001-knot-complexity-analysis` | **Date**: 2026-06-12

## Prerequisites

- Python 3.11+
- Stable internet connection (for Knot Atlas download)
- 4GB+ RAM recommended (A large-scale prime knots dataset)

## Installation

```bash
# Clone repository
git clone <repository-url>
cd projects/PROJ-552-quantifying-the-complexity-of-knot-diagr

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Quick Run

### Step 1: Download Data

```bash
python -m code.download.knot_atlas --output data/raw/knot_atlas_raw.json
```

This will:
- Download all prime knots with crossing number ≤ 13 from Knot Atlas
- Apply exponential backoff retry logic if Knot Atlas is unavailable (FR-008)
- Cache partial results on consecutive failures
- Generate SHA-256 checksum and save to `data/raw/knot_atlas_checksum.txt`

### Step 2: Clean and Validate Data

```bash
python -m code.data.clean --input data/raw/knot_atlas_raw.json --output data/processed/knots_cleaned.csv
```

This will:
- Parse and extract invariants (crossing number, braid index, hyperbolic volume)
- Validate format (DT code, braid word)
- Flag records with data quality issues
- Generate `data/processed/knots_checksum.txt`

### Step 3: Filter to Hyperbolic Knots

```bash
python -m code.data.filter --input data/processed/knots_cleaned.csv --output data/processed/knots_hyperbolic.csv --min-volume 0
```

This will:
- Filter to knots with hyperbolic volume > 0 (FR-012)
- Document excluded knots (torus/satellite) in `docs/reproducibility/excluded_knots.md`

### Step 4: Generate Exploratory Plots

```bash
python -m code.analysis.exploratory --input data/processed/knots_hyperbolic.csv --output-dir data/plots/
```

This will:
- Generate scatter plots of crossing number vs. braid index (FR-004)
- Stratify by alternating/non-alternating classification
- Save PNG files with minimum resolution 1200x900 pixels

### Step 5: Fit Regression Models

```bash
python -m code.analysis.regression --input data/processed/knots_hyperbolic.csv --output-dir models/
```

This will:
- Fit linear, polynomial, and logarithmic models (FR-005)
- Compute goodness-of-fit metrics (R², AIC/BIC, MAE)
- Calculate VIF for multicollinearity assessment
- Document results in `docs/reproducibility/multicollinearity_assessment.md`

### Step 6: Run Statistical Analysis

```bash
python -m code.analysis.statistics --input data/processed/knots_hyperbolic.csv --output-dir docs/reproducibility/
```

This will:
- Compute Spearman and Pearson correlations (FR-006)
- Calculate effect sizes (Cohen's d, r)
- Perform descriptive comparison (alternating vs. non-alternating)
- Note: p-values NOT reported for census data (Constitution VII exception)

### Step 7: Generate Reproducibility Artifacts

```bash
python -m code.reproducibility.checksums --data-dir data/ --output docs/reproducibility/
python -m code.reproducibility.logs --output-dir docs/reproducibility/logs/
python -m code.reproducibility.validation --output docs/reproducibility/
```

This will:
- Generate SHA-256 checksums for all data files (FR-007)
- Create timestamped execution logs
- Run tie-breaking validation (SC-007)
- Generate data quality report (SC-013)

## Full Pipeline

```bash
# Run complete pipeline (single command)
python -m code.pipeline.run --output-dir docs/reproducibility/
```

## Verification

```bash
# Run tests
pytest tests/

# Validate schema
python -m tests.contract.test_knot_record_schema --input data/processed/knots_cleaned.csv
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Knot Atlas unavailable | Retry logic applies exponential backoff; check `docs/reproducibility/logs/` for failure details |
| Missing invariant data | Records flagged with `missing_invariant_flags`; not silently excluded (FR-009) |
| Plot resolution too low | Verify matplotlib backend supports high resolution; adjust `dpi` parameter |
| Schema validation fails | Check `data/processed/knots_cleaned.csv` against `contracts/knot_record.schema.yaml` |