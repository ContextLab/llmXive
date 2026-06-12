# Quickstart: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

## Prerequisites

- Python 3.11 or higher
- Stable internet connectivity (for Knot Atlas data download)
- 2GB available disk space (for data and plots)
- Git for version control

## Installation

```bash
# Clone the repository
git clone
cd quantifying-knot-complexity

# Create virtual environment
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r projects/PROJ-552-quantifying-the-complexity-of-knot-diagr/requirements.txt
```

## Quick Start

### Step 1: Download Knot Data

```bash
# Execute download with retry logic (exponential backoff: initial=1s, max=32s, multiplier=2)
python projects/PROJ-552-quantifying-the-complexity-of-knot-diagr/code/download.py \
 --output data/raw/knot_atlas_raw.csv \
 --max-retries 3
```

This will:
- Download prime knot data from Knot Atlas (crossing number ≤13)
- Apply exponential backoff retry logic on failures
- Cache partial results to disk after 3 consecutive failures
- Generate checksum file: `data/raw/knot_atlas_raw.csv.sha256`

### Step 2: Parse and Clean Data

```bash
python projects/PROJ-552-quantifying-the-complexity-of-knot-diagr/code/parse.py \
 --input data/raw/knot_atlas_raw.csv \
 --output data/processed/knots_cleaned.csv
```

This will:
- Parse Knot Atlas data format
- Clean and validate invariant fields
- Flag records with data quality issues
- Generate checksum file: `data/processed/knots_cleaned.csv.sha256`

### Step 3: Exploratory Analysis

```bash
python projects/PROJ-552-quantifying-the-complexity-of-knot-diagr/code/analysis.py \
 --input data/processed/knots_cleaned.csv \
 --plots-dir data/plots \
 --random-seed 42
```

This will:
- Generate scatter plots (crossing number vs. braid index)
- Stratify by alternating/non-alternating classification
- Output PNG files with minimum resolution 1200x900 pixels

### Step 4: Regression Analysis

```bash
python projects/PROJ-552-quantifying-the-complexity-of-knot-diagr/code/analysis.py \
 --input data/processed/knots_cleaned.csv \
 --models linear,polynomial,logarithmic \
 --output-dir data/models \
 --random-seed 42
```

This will:
- Fit linear, polynomial, and logarithmic regression models
- Compute goodness-of-fit metrics (R², AIC/BIC, MAE)
- Compute Variance Inflation Factor (VIF) for multicollinearity assessment
- Save fitted models to `data/models/`

### Step 5: Generate Reproducibility Artifacts

```bash
python projects/PROJ-552-quantifying-the-complexity-of-knot-diagr/code/reproducibility.py \
 --data-dir data \
 --output-dir docs/reproducibility
```

This will generate:
- SHA-256 checksums for all data files
- Derivation notes with formula citations
- Timestamped operation logs
- Random seed documentation

## Validation

### Data Quality Check

```bash
python projects/PROJ-552-quantifying-the-complexity-of-knot-diagr/code/parse.py \
 --validate-only \
 --input data/processed/knots_cleaned.csv
```

Checks:
- Null percentage <5% in required invariant fields
- Format validation pass rate ≥95%
- Zero duplicates in output dataset

### Tie-Breaking Validation (FR-011)

```bash
python projects/PROJ-552-quantifying-the-complexity-of-knot-diagr/code/reproducibility.py \
 --validate-tie-breaking \
 --input data/processed/knots_cleaned.csv
```

Validates:
- Tie-breaking rules applied consistently across all records
- Returns exit code 0 on consistency check

## Output Files

After successful execution, you should have:

```
data/
├── raw/
│ ├── knot_atlas_raw.csv
│ └── knot_atlas_raw.csv.sha256
├── processed/
│ ├── knots_cleaned.csv
│ ├── knots_cleaned.csv.sha256
│ └── knots_hyperbolic.csv
├── plots/
│ ├── crossing_vs_braid.png
│ └── alternating_stratified.png
└── models/
 ├── regression_linear.pkl
 ├── regression_polynomial.pkl
 └── regression_logarithmic.pkl

docs/reproducibility/
├── checksums.md
├── derivation_notes.md
├── logs/
│ └── pipeline_run_2026-06-12.log
├── random_seeds.md
├── data_quality_report.md
├── excluded_knots.md
├── hyperbolic_volume_validation.md
├── invariant_coverage.md
├── multicollinearity_assessment.md
├── residual_analysis.md
├── tie_breaking_rules.md
├── validation_status.md
└── alternating_comparison.md
```

## Troubleshooting

### Knot Atlas Unavailable

If the Knot Atlas is unavailable during download:
- Retry logic applies exponential backoff (1s → 2s → 4s → 8s → 16s → 32s)
- After 3 consecutive failures, partial results are cached to disk
- Check `data/raw/knot_atlas_raw_partial.csv` for available data

### Missing Invariant Data

If invariants are missing for some knots:
- Records are flagged with `missing_invariant_flags` rather than silently excluded
- Check `docs/reproducibility/uncomputable_invariants.md` for details

### Validation Fails

If validation scripts return non-zero exit code:
- Check `docs/reproducibility/validation_status.md` for error details
- Re-run invariant computations before proceeding to downstream analysis