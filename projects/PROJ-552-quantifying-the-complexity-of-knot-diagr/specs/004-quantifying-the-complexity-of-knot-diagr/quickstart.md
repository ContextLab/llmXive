# Quickstart: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

## Prerequisites

- Python 3.11 or higher
- pip (Python package manager)
- Git (for version control)
- Internet connectivity (for downloading knot data from Knot Atlas)

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd projects/PROJ-552-quantifying-the-complexity-of-knot-diagr
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r code/requirements.txt
```

### 4. Verify Installation

```bash
python -c "import pandas; import numpy; import scipy; print('All dependencies installed successfully')"
```

## Quick Start Guide

### Step 1: Download Knot Data

```bash
python code/download/knot_atlas_downloader.py \
 --max-crossing-number 13 \
 --output-dir data/raw/ \
 --retry-max 3 \
 --backoff-initial 1 \
 --backoff-max 60 \
 --primary-source https://katlas.org \
 --fallback-source https://arxiv.org/abs/2402.02717
```

This command will:

- Download **all** prime knots with crossing number ≤13 from the canonical Knot Atlas URL (https://katlas.org).
- **API Endpoint**: Knot Atlas web tables (Parquet format).
- If the Knot Atlas endpoint is unreachable, automatically fall back to the Hoste-Thistlethwaite-Weeks tables (arXiv 2402.02717).
- **Fallback Availability Guarantee**: arXiv 2402.02717 contains tabulated invariants for all prime knots up to crossing 13 [UNRESOLVED-CLAIM: c_f3dc0711 — status=not_enough_info], ensuring data availability.
- Apply exponential backoff retry logic (initial 1 s, max 60 s, multiplier 2).
- Cache partial results after 3 consecutive failures.
- Generate SHA-256 checksums for all downloaded files.

**Expected Output**: `data/raw/knot_atlas_full.parquet` (≈10,000+ records).

**Scope Boundary Clarification**: This command performs **data collection (≤13)**, but **validated completeness (≤10)** applies only to the subset with crossing number ≤10 per SC-001. Phase 1 analyses are limited to the validated ≤10 subset.

### Step 2: Compute Additional Invariants

```bash
python code/compute/invariant_calculator.py \
 --input data/raw/knot_atlas_full.parquet \
 --output data/processed/knots_with_invariants.parquet \
 --invariants arc_index seifert_circle_count bridge_number \
 --completeness-threshold 0.99
```

This will:

- Retrieve tabulated invariants where available; compute missing `arc_index`, `seifert_circle_count`, and `bridge_number` only for those records.
- Flag records with `missing_invariant_flags` rather than excluding them (FR-011).
- Validate that **≥99%** of the ≤10 subset have all required fields populated (SC-006).
- Produce a validation report at `docs/reproducibility/algorithm_validation.md`.

**Expected Output**: `data/processed/knots_with_invariants.parquet`.

### Step 3: Run Exploratory Analysis

```bash
python code/analysis/exploratory.py \
 --input data/processed/knots_with_invariants.parquet \
 --output-dir data/plots/ \
 --resolution 1200x900
```

This will:

- Generate scatter plots of crossing number vs. braid index stratified by alternating/non-alternating classification.
- Save PNG files to `data/plots/` with minimum 1200 × 900 resolution.

**Expected Output**: `data/plots/crossing_vs_braid_alternating.png`, `data/plots/crossing_vs_braid_non_alternating.png`.

### Step 4: Fit Regression Models

```bash
python code/analysis/regression.py \
 --input data/processed/knots_with_invariants.parquet \
 --models linear polynomial logarithmic \
 --output-dir data/processed/ \
 --random-seed 42
```

This will:

- Fit separate linear, polynomial, and logarithmic regression models for alternating and non-alternating knots, and an optional combined model with interaction terms.
- Compute VIF scores and flag any predictor with VIF > 5.
- Generate goodness-of-fit metrics (R², AIC/BIC, MAE).
- Document results in `data/processed/regression_result.json`.

**Expected Output**: `data/processed/regression_result.json` with model metrics.

### Step 5: Compute Composite Complexity Score

```bash
python code/analysis/composite_score.py \
 --input data/processed/knots_with_invariants.parquet \
 --weights-crossing 0.5 \
 --weights-braid 0.5 \
 --validation-split 0.2 \
 --random-seed 42 \
 --output data/processed/composite_score_results.json
```

This will:

- Create a weighted combination of crossing number and braid index (default 1:1).
- Randomly split 20% of the validated ≤10 subset for an **exploratory correlation subset** (not a predictive validation).
- Compute Pearson and Spearman correlations with hyperbolic volume and report effect sizes.
- Output results to `data/processed/composite_score_results.json`.

### Step 6: Validate Tie-Breaking Rules

```bash
python code/validation/tie_breaking_validator.py \
 --input data/processed/knots_with_invariants.parquet \
 --output docs/reproducibility/validation_status.md
```

This script checks that the hierarchy (braid word > DT code; lexicographically first DT code) is applied consistently across all records and writes a status report.

### Step 7: Generate Reproducibility Documentation

```bash
python code/docs/generate_reproducibility_docs.py \
 --data-dir data/ \
 --output-dir docs/reproducibility/ \
 --random-seed 42
```

This will:

- Generate SHA-256 checksums for all data files.
- Create derivation notes with formula citations.
- Record timestamped logs of all operations.
- Produce `docs/reproducibility/checksums.md`, `derivation_notes.md`, etc.

## Verification

### Check Dataset Completeness

```bash
python -c "
import pandas as pd
df = pd.read_parquet('data/processed/knots_with_invariants.parquet')
subset = df[df.crossing_number <= 10]
print(f'Total knots ≤10: {len(subset)}')
print(f'Completeness (required fields): {(subset[['crossing_number','braid_index','hyperbolic_volume','alternating_classification']].notna().all(axis=1).mean()*100):.2f}%')
"
```

### Validate Contract Compliance

```bash
python -m pytest tests/contract/ -v
```

### Check Constitution Compliance

```bash
python code/docs/validate_constitution.py \
 --constitution projects/PROJ-552-quantifying-the-complexity-of-knot-diagr/.specify/memory/constitution.md \
 --output docs/reproducibility/constitution_check.md
```

## Troubleshooting

### Knot Atlas Unavailable

If the download fails due to API unavailability:

1. Retry logic automatically applies exponential backoff (1 s → 2 s → 4 s → … → 60 s max).
2. After 3 consecutive failures, the pipeline switches to the fallback source (arXiv 2402.02717).
3. Check `docs/reproducibility/validation_status.md` for download status.
4. **Fallback Guarantee**: arXiv 3,250 contains complete tabulated data for prime knots up to crossing 13.

### Missing Invariant Computations

If invariants cannot be computed:

1. Records are flagged with `missing_invariant_flags` (not excluded).
2. Review `docs/reproducibility/uncomputable_invariants.md` for details.
3. Verify diagram representation availability (braid word or DT code).

### Multicollinearity Warning

If VIF > 5 for any predictor:

1. This is expected given the braid index ≤ crossing number relationship.
2. Document in final reports as per FR-005.
3. Coefficient interpretation may be affected; focus on overall model fit (R²).

## Next Steps

1. **Phase 2+**: Incorporate additional knot classes (torus, satellite, hyperbolic).
2. **Validation Extension**: Full validation for crossing numbers 11-13.
3. **Composite Score Refinement**: Explore alternative weighting schemes beyond 1:1 ratio.
4. **Paper Production**: Generate final research paper with all validated results.

## Support

For issues or questions:

1. Check `docs/reproducibility/` for detailed documentation.
2. Review `code/` for implementation details.
3. Consult the project constitution for governance procedures.