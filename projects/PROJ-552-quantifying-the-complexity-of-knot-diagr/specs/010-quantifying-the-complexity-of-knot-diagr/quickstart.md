# Quickstart: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

## Prerequisites

- Python 3.11 or higher
- pip package manager
- Internet connectivity for data download
- Sufficient available disk space

## Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r code/requirements.txt
```

## Quick Test

```bash
# Run data download with retry logic
python code/download/knot_data_downloader.py

# Verify data integrity
python code/reproducibility/validate_checksums.py

# Run exploratory analysis
python code/analysis/exploratory_analysis.py

# Check reproducibility artifacts
ls docs/reproducibility/
```

## Directory Structure

```text
projects/PROJ-552-quantifying-the-complexity-of-knot-diagr/
├── code/
│   ├── download/           # Data download scripts
│   ├── analysis/           # Analysis and modeling scripts
│   ├── reproducibility/    # Validation and reproducibility tools
│   └── requirements.txt    # Python dependencies
├── data/
│   ├── raw/               # Unmodified downloaded data
│   ├── processed/         # Cleaned and derived datasets
│   └── plots/             # Generated visualization files
├── docs/
│   └── reproducibility/   # Reproducibility documentation
└── specs/
    └── 001-knot-complexity-analysis/
        ├── plan.md
        ├── research.md
        ├── data-model.md
        ├── quickstart.md
        └── contracts/
```

## Configuration

### Random Seeds

All random seeds are pinned in code. Current values documented in:
- `docs/reproducibility/random_seeds.md`

### Retry Parameters

- Initial delay: 1 second
- Maximum delay: 32 seconds
- Multiplier: 2x
- Max retries: 3 consecutive failures before caching partial results

### Validation Thresholds

| Metric | Threshold |
|--------|-----------|
| Null percentage (required fields) | <1% |
| Format validation pass rate | ≥95% |
| Match threshold (algorithm validation) | ≥90% |
| KnotInfo coverage (feasibility) | ≥50% |
| Residual deviation threshold | ≥2 standard deviations |

### Statistical Reporting

- **Effect sizes**: Always reported (Cohen's d, r, r²)
- **p-values**: NOT reported for census data (not applicable for complete enumeration)
- **Multicollinearity**: VIF values documented; regression interpreted as variance partitioning only

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Knot Atlas unavailable | Retry logic applies exponential backoff; check `docs/reproducibility/retry_logs.md` |
| Missing invariant flags | Records flagged but not excluded; check `docs/reproducibility/missing_invariant_flags.md` |
| Validation script fails | Re-run invariant computations; check `docs/reproducibility/validation_status.md` |
| Checksum mismatch | Re-download raw data; verify source integrity |
| KnotInfo coverage <50% | Validation skipped; limitation documented in `docs/reproducibility/hyperbolic_volume_validation.md` |

## Critical Spec.md Issues Requiring Kickback

**WARNING**: The source spec.md contains unresolved issues that block Verified Accuracy Gate:

1. **FR-013 Corrupted URL**: Contains `( nodename nor servname provided, or not known)'))])` instead of valid KnotInfo URL
2. **FR-013 Unquantified Threshold**: States "high match threshold" without quantification (plan specifies ≥90%)
3. **FR-006 P-Value Policy Conflict**: States p-values documented for convention (plan explicitly excludes them for census data)

These issues require spec.md correction before project can proceed.