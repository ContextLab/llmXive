# Quickstart: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

## Prerequisites

- Python 3.11 or higher
- Stable internet connectivity (for downloading Knot Atlas data)
- At least 2GB available disk space
- Git (for version control)

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd projects/PROJ-552-quantifying-the-complexity-of-knot-diagr
```

### 2. Create Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r code/requirements.txt
```

Dependencies are pinned in `code/requirements.txt` (per Constitution Principle I):
- `pandas==2.2.0`
- `numpy==1.26.0`
- `scipy==1.12.0`
- `statsmodels==0.14.1`
- `requests==2.31.0`
- `pyyaml==6.0.1`
- `matplotlib==3.8.0`
- `seaborn==0.13.0`
- `pytest==8.0.0`

## Running the Analysis

### Step 1: Download Knot Data

```bash
python code/data/download_knots.py --crossing-max 13 --output data/raw/knot_atlas.parquet
```

This downloads all prime knots with crossing number ≤13 from Knot Atlas. Retry logic with exponential backoff is implemented (initial:, max:, multiplier: 2).

**Version Tracking**: Knot Atlas version captured from API response headers and stored in `data_source_version` field.

### Step 2: Parse and Clean Data

```bash
python code/data/parse_knots.py --input data/raw/knot_atlas.parquet --output data/processed/cleaned.parquet
```

### Step 3: Compute Additional Invariants

```bash
python code/data/compute_invariants.py --input data/processed/cleaned.parquet --output data/processed/invariants.parquet
```

Computes arc index, Seifert circle count, and bridge number where diagram representations are available.

**Inequality Verification**: Before analysis, known mathematical inequalities (bridge ≤ crossing, etc.) are verified empirically. Discrepancies logged to `data/derivation_notes.md`.

### Step 4: Exploratory Analysis

```bash
python code/analysis/exploratory.py --input data/processed/invariants.parquet --output-dir data/plots/
```

Generates scatter plots of crossing number vs. braid index stratified by alternating/non-alternating classification.

### Step 5: Regression Modeling

```bash
python code/analysis/regression.py --input data/processed/invariants.parquet --output data/processed/regression_results.parquet
```

Fits linear, polynomial, and logarithmic regression models. Output conforms to `contracts/regression_output.schema.yaml` (CANONICAL).

**Training Scope**: Models trained on c≤10 data only; c=11-13 data used for exploratory evaluation only.

### Step 6: Validation

```bash
python code/analysis/validation.py --input data/processed/invariants.parquet --output data/processed/validation_results.parquet
```

Validates composite complexity score against exploratory validation sample. CompositeComplexityScore records stored in this file.

## Reproducibility Verification

### Checksums

All data files under `data/` are checksummed. Verify with:

```bash
python code/utils/reproducibility.py verify-checksums --data-dir data/
```

### Logs

Timestamped logs stored in `docs/reproducibility/logs/`. Each log entry includes:
- `timestamp`
- `operation`
- `input_file`
- `output_file`
- `parameters`
- `status`
- `duration_ms`

### Derivation Notes

Complete derivation notes available in `docs/reproducibility/derivation_notes.md`, including:
- Formula citations with page/section references
- Step-by-step transformation logic with intermediate values
- All parameter values used
- Justification for non-standard choices
- Empirical inequality verification results

### Power Analysis

Full power analysis documented in `docs/reproducibility/power_analysis.md`:
- Sample size calculations
- Minimum detectable effect sizes
- Power at α=0.05
- Filtering logic for torus/satellite exclusion (exact counts from source dataset)

### License Compliance

Dataset license terms documented in `docs/reproducibility/license_compliance.md`:
- Knot Atlas data license
- Redistribution permissions
- Attribution requirements

### Spec Defects Documentation

All spec defects tracked in `docs/reproducibility/spec_defects.md`:
- SC-006 threshold (provisional) - pending spec amendment
- SC-012 threshold (provisional) - pending spec amendment
- OEIS count factual error - pending spec amendment

## Configuration

### Complexity Weights

Edit `config/complexity_weights.yaml` to configure composite complexity score weights:

```yaml
crossing_weight: 1.0  # Default: 1.0 (equal weight)
braid_weight: 1.0     # Default: 1.0 (equal weight)
```

### Random Seeds

All random seeds are pinned in code. Seed values documented in `docs/reproducibility/seed_values.md`.

## Testing

Run all tests:

```bash
pytest tests/
```

Run contract tests specifically:

```bash
pytest tests/contract/
```

Contract tests validate that output files conform to schemas in `contracts/`.

## Troubleshooting

### Knot Atlas Unavailable

If Knot Atlas is unavailable, the system implements retry logic with exponential backoff. After 3 consecutive failures, partial results are cached to disk.

### Missing Invariants

Records with missing computable invariants are flagged with `missing_invariant_flags` rather than silently excluded. See `docs/reproducibility/uncomputable_invariants.md` for details.

### Ambiguous Classification

Knots with ambiguous alternating/non-alternating classification are either excluded from stratified analysis (with count logged) or marked as "unclassifiable" in the output dataset.

### Data Version Mismatch

If `data_source_version` differs from expected version, data must be re-downloaded. Version mismatch logged in `docs/reproducibility/logs/`.

### Spec Defect Blockers

If spec defects (SC-006, SC-012) remain uncorrected, validation checks will use provisional values (and) but cannot be marked as complete. See `docs/reproducibility/spec_defects.md` for status.

## Next Steps

1. Review results in `data/processed/`
2. Check reproducibility documentation in `docs/reproducibility/`
3. Read full implementation plan in `specs/001-knot-complexity-analysis/plan.md`
4. Proceed to Phase 2+ for multi-class prime knot exploration (torus, satellite, hyperbolic)
5. **Critical**: Verify spec defects have been corrected via kickback before final validation