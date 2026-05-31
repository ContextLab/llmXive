# Quickstart: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

**Feature Branch**: `001-knot-complexity-analysis` | **Date**: 2026-05-29

## Prerequisites

- Python 3.11 or higher
- pip package manager
- Stable internet connection (for Knot Atlas download)
- ~500MB disk space for dataset and outputs

## Installation

1. **Clone the repository** (or navigate to project root):
   ```bash
   cd projects/PROJ-552-quantifying-the-complexity-of-knot-diagr
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```

4. **Verify installation**:
   ```bash
   python -c "import pandas, numpy, scipy, matplotlib; print('All dependencies installed')"
   ```

## Running the Analysis

### Step 1: Download Knot Data

```bash
python code/data_download.py
```

This will:
- Attempt to download from Knot Atlas with exponential backoff retry logic
- Cache partial results after 3 consecutive failures
- Save raw data to `data/raw/knot_atlas_raw.jsonl`
- Record checksum in `docs/reproducibility/checksums.json`

**Expected Output**: Raw dataset with all prime knots crossing number ≤13

### Step 2: Parse and Clean Data

```bash
python code/invariant_computation.py --stage parse
```

This will:
- Extract crossing number, braid index, alternating classification
- Save processed data to `data/processed/knots_crossing_1_to_10.parquet`
- Flag records with missing invariant data

**Expected Output**: Cleaned dataset ready for invariant computation

### Step 3: Compute Additional Invariants

```bash
python code/invariant_computation.py --stage compute
```

This will:
- Compute arc index (Birman-Menasco method)
- Compute Seifert circle count (Seifert's algorithm)
- Compute bridge number (Schubert's decomposition)
- Flag uncomputable records with `missing_invariant_flags`

**Expected Output**: `data/processed/invariants_computed.parquet` with all invariants

### Step 4: Exploratory Analysis

```bash
python code/exploratory_analysis.py
```

This will:
- Generate scatter plots of crossing number vs. braid index
- Stratify by alternating/non-alternating classification
- Save PNG files to `data/plots/` (minimum 1200x900 pixels)

**Expected Output**: 
- `data/plots/crossing_vs_braid_alternating.png`
- `data/plots/crossing_vs_braid_non_alternating.png`

### Step 5: Regression Modeling

```bash
python code/regression_models.py
```

This will:
- Fit linear regression model
- Fit polynomial/non-linear regression model
- Compare goodness-of-fit metrics (R², AIC/BIC)
- Save model objects to `data/processed/regression_models/`

**Expected Output**: Regression model objects with documented metrics

### Step 6: Composite Score Construction

```bash
python code/composite_score.py
```

This will:
- Construct composite complexity score with default equal weights (1:1)
- Split dataset 20% held-out test set (stratified by crossing number)
- Compute correlations with arc index and Seifert circle count
- Report Pearson AND Spearman coefficients

**Expected Output**: `data/processed/composite_score_validation.parquet` with validation metrics

### Step 7: Reproducibility Documentation

```bash
python code/reproducibility/generate_docs.py
```

This will:
- Generate SHA-256 checksums for all data files
- Create derivation notes for all transformations
- Record timestamped logs
- Generate validation status report

**Expected Output**: 
- `docs/reproducibility/checksums.json`
- `docs/reproducibility/reproducibility_logs.jsonl`
- `docs/reproducibility/validation_status.md`

## Configuration

### Customizing Weights

Edit `config/complexity_weights.yaml`:

```yaml
crossing_weight: 1.0
braid_weight: 1.0
```

### Random Seed

Edit `config/random_seed.yaml`:

```yaml
random_seed: 42
```

## Validation

### Dataset Completeness Check

```bash
python tests/unit/test_dataset_completeness.py
```

Expected: ≥95% completeness for crossing numbers ≤10

### Algorithm Validation Check

```bash
python tests/unit/test_algorithm_validation.py
```

Expected: ≥95% match with reference values where coverage ≥10%

### Tie-Breaking Consistency Check

```bash
python docs/reproducibility/validate_tie_breaking.py
```

Expected: 100% consistency across all records

### Contract Tests

```bash
pytest tests/contract/
```

Expected: All schema validations pass

## Troubleshooting

### Knot Atlas Unavailable

If download fails after 3 retries:
1. Check `docs/reproducibility/reproducibility_logs.jsonl` for error details
2. Manual data extraction may be required
3. Document "NO verified source found" in `docs/reproducibility/validation_scope.md`

### Missing Invariant Data

Check `docs/reproducibility/uncomputable_invariants.md` for summary of records with missing data.

### Validation Failures

If any validation script fails:
1. Review error message in log output
2. Check `docs/reproducibility/validation_status.md` for detailed failure report
3. Re-run the affected stage before proceeding

## Next Steps

After completing Phase 1:
1. Review results in `docs/reproducibility/validation_status.md`
2. Evaluate whether to proceed to Phase 2 (multi-class exploration)
3. Update project documentation with findings
