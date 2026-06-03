# Quickstart: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

## Prerequisites

- Python 3.11 or higher
- pip package manager
- Internet connectivity for downloading Knot Atlas data
- At least 500MB disk space for data artifacts

## Installation

1. Clone the repository and navigate to the project directory:
```bash
cd projects/PROJ-552-quantifying-the-complexity-of-knot-diagr
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
```

3. Install dependencies from requirements file:
```bash
pip install -r code/requirements.txt
```

The `requirements.txt` file at `code/` pins every Python dependency per Constitution Principle I (Reproducibility).

## Quick Start Commands

### Step 1: Download Knot Data

```bash
python code/download/download_knot_atlas.py
```

This downloads all prime knots with crossing number ≤13 from Knot Atlas. The script implements retry logic with exponential backoff (1s → 2s → 4s →... → 60s max) and caches partial results after 3 consecutive failures.

**Output**: `data/raw/knot_atlas_raw.json`

### Step 2: Verify Retry Logic (SC-005)

```bash
python code/reproducibility/retry_verification.py
```

This script verifies that the retry logic with exponential backoff executes correctly on simulated API failures. Test passes if backoff intervals follow the specified pattern (1s, 2s, 4s, 8s, 16s, 32s, 60s max).

**Output**: Verification log in `docs/reproducibility/retry_verification_log.md`

### Step 3: Compute Additional Invariants

```bash
python code/compute/compute_invariants.py
```

Computes arc index, Seifert circle count, and bridge number from available diagram representations. Records with missing invariants are flagged rather than excluded.

**Output**: `data/processed/knots_with_invariants.csv`

### Step 4: Document Invariant Discrepancies (Constitution Principle VI)

```bash
python code/compute/validate_discrepancies.py
```

Compares computed invariant values against canonical reference values from KnotInfo. Documents any discrepancies in `docs/reproducibility/discrepancy_notes.md` with derivation notes as required by Constitution Principle VI.

**Output**: Discrepancy report in `docs/reproducibility/discrepancy_notes.md`

### Step 5: Verify Invariant Coverage (SC-006)

```bash
python code/reproducibility/coverage_measurement.py
```

This script measures invariant computation coverage and verifies the ≥99% threshold for knots with computable invariants. Reports coverage statistics per invariant type.

**Output**: Coverage report in `docs/reproducibility/coverage_report.md`

### Step 6: Filter by Hyperbolic Volume (FR-014/SC-014)

```bash
python code/reproducibility/volume_completeness.py
```

Filters dataset to exclude torus/satellite knots with zero/undefined hyperbolic volume. Documents excluded knots and verifies ≥95% volume completeness threshold per SC-014.

**Output**: Filtered dataset `data/processed/knots_filtered_volume.csv` and exclusion log `docs/reproducibility/excluded_knots.md`

### Step 7: Run Exploratory Analysis

```bash
python code/analyze/exploratory_analysis.py
```

Generates scatter plots of crossing number vs. braid index stratified by alternating/non-alternating classification.

**Output**: `data/plots/crossing_vs_braid_alternating.png`, `data/plots/crossing_vs_braid_nonalternating.png`

### Step 8: Fit Regression Models

```bash
python code/analyze/regression_models.py
```

Fits linear, polynomial, and logarithmic regression models to test relationships between crossing number, braid index, and hyperbolic volume. Includes knot family covariates.

**Output**: `data/processed/regression_results.json`

### Step 9: Run Statistical Tests

```bash
python code/analyze/statistical_tests.py
```

Performs ANOVA testing, correlation analysis (Pearson AND Spearman), and composite complexity score validation.

**Output**: `data/processed/validation_results.json`

### Step 10: Verify Tie-Breaking Rules (SC-008)

```bash
python code/reproducibility/tie_breaking_validation.py
```

This script automates the validation check for tie-breaking rules as required by SC-008. Verifies that when multiple diagram representations exist, braid word is preferred over DT code, and lexicographically first DT code is selected.

**Output**: Validation report in `docs/reproducibility/tie_breaking_validation_report.md`

### Step 11: Verify Reproducibility

```bash
python code/reproducibility/checksums.py
python code/reproducibility/random_seeds.py
python code/reproducibility/reference_validator.py
```

Verifies SHA-256 checksums for all data files, confirms random seed pinning, and validates all external citations per Constitution Principle II.

**Output**: Checksums recorded in `state/projects/PROJ-552-quantifying-the-complexity-of-knot-diagr.yaml`

## Verification

Run the test suite to verify all components:

```bash
pytest tests/ -v
```

Contract tests verify schema compliance:
```bash
pytest tests/contract/ -v
```

Integration tests verify download pipeline and retry logic:
```bash
pytest tests/integration/ -v
```

Unit tests verify invariant computation, statistical tests, tie-breaking validation, and volume filtering:
```bash
pytest tests/unit/ -v
```

## Troubleshooting

### Knot Atlas Unavailable

If the download fails due to API unavailability, check `data/raw/knot_atlas_partial.json` for cached partial results. The script automatically applies exponential backoff and retries.

### Missing Invariants

Records with missing invariants are flagged in `docs/reproducibility/uncomputable_invariants.md`. Review this file to understand which invariants could not be computed and why.

### Ambiguous Classification

Knots with ambiguous alternating/non-alternating classification are marked as "unclassifiable" in the output dataset. The count is logged in the analysis output.

### Multicollinearity Warning

If VIF > 5 for any predictor, coefficient interpretation caveats are documented in the regression output. This is expected given that braid index ≤ crossing number for most knots.

### Algorithm Computational Infeasibility

If arc index or bridge number computation fails for >5% of the pre-computation sample, review `docs/reproducibility/validation_status.md` for fallback strategy documentation.

### Hyperbolic Volume Filtering

If hyperbolic volume is missing or undefined for a knot, it is excluded from volume prediction analysis per FR-014. Excluded knots are documented in `docs/reproducibility/excluded_knots.md` with reason codes.

## Next Steps

After completing the quickstart workflow:

1. Review `docs/reproducibility/derivation_notes.md` for transformation documentation
2. Check `docs/reproducibility/discrepancy_notes.md` for Constitution Principle VI compliance
3. Check `docs/reproducibility/excluded_knots.md` for SC-014 compliance
4. Check `docs/reproducibility/validation_scope.md` for Phase 1 scope boundaries
5. Examine `data/processed/validation_results.json` for correlation analysis results
6. Review `docs/reproducibility/tie_breaking_validation_report.md` for SC-008 compliance
7. Proceed to `tasks.md` for detailed implementation tasks
