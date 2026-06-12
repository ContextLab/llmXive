# Quickstart: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

## Prerequisites

- Python 3.11 or higher
- Stable internet connectivity (for Knot Atlas download)
- At least 10GB disk space (for data and intermediate files)
- Git (for version control)

## License Compatibility

- Knot Atlas: CC BY-NC-SA (compatible with research use)
- OEIS: CC BY (compatible with research use)
- Both licenses permit research and documentation with attribution

## Quick Start Guide

### Step 1: Clone and Setup

```bash
# Clone the repository
git clone https://github.com/your-org/quantifying-knot-complexity.git
cd quantifying-knot-complexity

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r code/requirements.txt
```

### Step 2: Download Knot Data

```bash
# Run the download script with retry logic
python code/download/knot_atlas_downloader.py \
  --output data/raw/knot_atlas_export.csv \
  --max-crossings 13 \
  --retry-initial 1 \
  --retry-max 32 \
  --retry-multiplier 2
```

This will:
- Download all prime knots with crossing number ≤13 from Knot Atlas
- Apply exponential backoff retry if Knot Atlas is unavailable
- Cache partial results after 3 consecutive failures
- Generate SHA-256 checksum for downloaded file

### Step 3: Validate and Clean Data

```bash
# Run data validation and cleaning
python code/data/parser.py \
  --input data/raw/knot_atlas_export.csv \
  --output data/processed/knots_cleaned.parquet \
  --validate-crossings 10 \
  --report docs/reproducibility/data_quality_report.md
```

This will:
- Parse and clean the dataset (FR-002)
- Flag records with missing invariant data (FR-009)
- Generate data quality report with null percentages and format validation results
- Document validation scope (≤10 vs ≤13 distinction)

### Step 4: Filter to Hyperbolic Knots

```bash
# Filter dataset to hyperbolic knots only
python code/data/filter_hyperbolic.py \
  --input data/processed/knots_cleaned.parquet \
  --output data/processed/knots_hyperbolic.parquet \
  --min-volume 0 \
  --exclusions docs/reproducibility/excluded_knots.md
```

This will:
- Filter to knots with hyperbolic volume > 0 (FR-012)
- Document excluded knots (torus and satellite)
- Log selection bias in final reports

### Step 5: Generate Exploratory Plots

```bash
# Generate scatter plots stratified by alternating classification
python code/analysis/exploratory.py \
  --input data/processed/knots_hyperbolic.parquet \
  --output data/plots/ \
  --resolution 1200x900
```

This will create:
- `crossing_vs_braid_alternating.png`
- `crossing_vs_braid_nonalternating.png`

### Step 6: Fit Regression Models

```bash
# Fit multiple regression model types
python code/analysis/regression.py \
  --input data/processed/knots_hyperbolic.parquet \
  --models linear,polynomial,logarithmic \
  --output analysis/regression_models.parquet \
  --metrics r_squared,aic,bic,mae
```

This will:
- Fit linear, polynomial, and logarithmic models (FR-005)
- Compute VIF for multicollinearity assessment
- Document model selection based on goodness-of-fit metrics

### Step 7: Statistical Analysis

```bash
# Run correlation tests and effect size calculations
python code/analysis/statistics.py \
  --input data/processed/knots_hyperbolic.parquet \
  --output analysis/statistics_summary.parquet \
  --correlation spearman,pearson \
  --effect-size cohens-d,r
```

This will:
- Compute Spearman correlation (primary) and Pearson correlation (supplementary) (FR-006)
- Calculate effect sizes (Cohen's d for group comparisons)
- Document census data interpretation limitations

### Step 8: Reproducibility Documentation

```bash
# Generate reproducibility artifacts
python code/utils/checksum_utils.py --data-dir data/
python code/utils/logging_utils.py --output docs/reproducibility/
```

This will create:
- SHA-256 checksums for all data files
- Derivation notes with formula citations
- Timestamped logs with operation details
- Random seed documentation

## Validation

```bash
# Run all contract tests
pytest code/tests/contract/ -v

# Run tie-breaking validation (SC-007)
python code/data/reproducibility/tie_breaking_validation.py
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Knot Atlas unavailable | Retry logic will apply exponential backoff; check `docs/reproducibility/validation_status.md` for partial results |
| Missing invariant data | Records are flagged with `missing_invariant_flags`; see `docs/reproducibility/data_quality_report.md` |
| Ambiguous alternating classification | Records marked as "unclassifiable"; excluded from stratified analysis |
| API rate limiting | Retry sequence: initial=1s, max=32s, multiplier=2 (FR-008) |

## Next Steps

- Review `docs/reproducibility/data_quality_report.md` for data quality metrics
- Examine `docs/reproducibility/validation_scope.md` for Phase 1 scope limitations
- Check `analysis/regression_models.parquet` for model fit statistics
- Read `docs/reproducibility/residual_analysis.md` for family deviation analysis