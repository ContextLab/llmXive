# Quickstart: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

## Prerequisites

- Python 3.11 or later
- Access to stable internet connectivity (for downloading Knot Atlas data)
- Sufficient available disk space (for data storage and reproducibility artifacts)

## Installation

```bash
# Navigate to project directory
cd projects/PROJ-552-quantifying-the-complexity-of-knot-diagr/

# Create isolated virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r code/requirements.txt

# Verify installation
python -m pytest tests/contract/ -v
```

## Running the Pipeline

### Step 1: Download Knot Atlas Data

```bash
# Download raw data from Knot Atlas
python code/main.py --step download

# Output: data/raw/knot_atlas_raw.json (checksummed)
```

### Step 2: Parse and Validate Data

```bash
# Parse raw data and apply validation rules
python code/main.py --step parse

# Output: data/processed/knots_validated.parquet
```

### Step 3: Filter to Hyperbolic Knots

```bash
# Filter dataset to hyperbolic prime knots only (volume > 0)
python code/main.py --step filter_hyperbolic

# Output: data/processed/knots_hyperbolic.parquet
```

### Step 4: Exploratory Analysis

```bash
# Generate exploratory plots (crossing number vs. braid index)
python code/main.py --step exploratory

# Output: data/plots/*.png (1200x900 minimum resolution)
```

### Step 5: KnotInfo Cross-Check (FR-013/SC-014)

```bash
# Validate hyperbolic volume against KnotInfo reference values
python code/main.py --step knotinfo_crosscheck

# Output: docs/reproducibility/data_consistency_report.md
```

### Step 6: Regression Analysis

```bash
# Fit and compare regression models
python code/main.py --step regression

# Output: RegressionModel entities in memory; results logged
```

### Step 7: Residual Analysis

```bash
# Identify knot families with significant deviations
python code/main.py --step residual_analysis

# Output: docs/reproducibility/residual_analysis.md
```

### Step 8: Tie-Breaking Validation (SC-007)

```bash
# Verify tie-breaking rules applied consistently
python code/main.py --step validate_tie_breaking

# Output: docs/reproducibility/validation_status.md
```

### Step 9: Reproducibility Check

```bash
# Verify all reproducibility artifacts
python code/main.py --step reproducibility_check

# Output: docs/reproducibility/validation_status.md
```

## Reproducibility Artifacts

All reproducibility artifacts are in `data/reproducibility/`:

| Artifact | Location | Description |
|----------|----------|-------------|
| Checksums | `data/checksums.txt` | SHA-256 checksums for all data files |
| Logs | `data/reproducibility/logs/` | Timestamped operation logs |
| Derivation Notes | `data/reproducibility/derivation_notes/` | Step-by-step transformation documentation |
| Random Seeds | `data/reproducibility/random_seeds.md` | All random seed values used |
| Data Quality Report | `data/reproducibility/data_quality_report.md` | Null percentages, format pass rates, duplicates |
| Validation Scope | `data/reproducibility/validation_scope.md` | Crossing number ≤ 10 vs. ≤ 13 distinction |
| Excluded Knots | `data/reproducibility/excluded_knots.md` | Torus/satellite knots filtered out |
| Tie-Breaking Rules | `data/reproducibility/tie_breaking_rules.md` | Documented tie-breaking rules |
| Data Consistency Report | `data/reproducibility/data_consistency_report.md` | KnotInfo cross-check results |

## Testing

### Contract Tests

```bash
# Validate data against YAML schemas
python -m pytest tests/contract/ -v
```

### Integration Tests

```bash
# Test download pipeline with retry logic
python -m pytest tests/integration/test_download_pipeline.py -v
```

### Unit Tests

```bash
# Test parser and validator components
python -m pytest tests/unit/ -v
```

## Common Issues

### API Unavailability

If Knot Atlas is unavailable:
- Retry logic with exponential backoff is automatically applied (FR-008)
- Partial results cached to disk after multiple consecutive failures
- Check `data/reproducibility/logs/` for retry sequence details

### Missing Invariant Data

Records with missing invariants are flagged (not silently excluded):
- Check `data_quality_flags` and `missing_invariant_flags` fields
- See `data/reproducibility/data_quality_report.md` for summary

### Hyperbolic Volume Filtering

Torus and satellite knots (volume = 0) are filtered for volume prediction analysis:
- Excluded records documented in `data/reproducibility/excluded_knots.md`
- Original dataset preserved in `data/processed/knots_validated.parquet`

### KnotInfo Cross-Check Failure

If KnotInfo coverage < 90%:
- Cross-check skipped and limitation documented per FR-013
- See `data/reproducibility/data_consistency_report.md` for coverage statistics

## Next Steps

After completing the pipeline:
1. Review `data/reproducibility/validation_status.md` for validation results
2. Check `data/reproducibility/residual_analysis.md` for identified knot families
3. Examine `data/plots/` for exploratory visualizations
4. Review `data/reproducibility/data_consistency_report.md` for KnotInfo cross-check results
5. Proceed to Phase 2+ for additional invariant computation (arc index, Seifert circle count, bridge number)