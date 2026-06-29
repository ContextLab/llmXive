# Quickstart: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

## Prerequisites

- Python 3.11+
- Stable internet connectivity (for downloading data from Knot Atlas)
- GitHub Actions free‑tier runner or equivalent (2 CPU cores, ~7 GB RAM, ~14 GB disk, NO GPU)

## Installation

```bash
# Clone repository
git clone <repository-url>
cd projects/PROJ-552-quantifying-the-complexity-of-knot-diagr

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r code/requirements.txt
```

## Data Download

```bash
# Download knot data from Knot Atlas with retry logic (initial = 1 s, multiplier = 2, max = 32 s)
python code/download/knot_atlas_loader.py

# Output: data/raw/knot_atlas_raw.json
```

**Retry Logic**: Exponential back‑off (initial delay = 1 s, multiplier = 2, max delay = 32 s). Partial results are cached after three consecutive failures.

## Data Processing

```bash
# Parse and clean dataset
python code/data/parser.py

# Validate dataset
python code/data/validator.py

# Output: data/processed/knots_cleaned.csv, data/processed/knots_validated.csv
```

## Analysis

```bash
# Exploratory data analysis (scatter plots, stratified by alternating/non‑alternating)
python code/analysis/exploratory.py

# Output: data/plots/crossing_vs_braid_index.png (minimum resolution 1200×900 px)

# Fit regression models
python code/analysis/regression.py

# Output: regression results with R², AIC/BIC, MAE metrics

# Residual analysis
python code/analysis/residual_analysis.py

# Output: docs/reproducibility/residual_analysis.md
```

## Reproducibility

```bash
# Generate checksums for all data files
python code/reproducibility/checksum_generator.py

# Validate tie‑breaking rules
python docs/reproducibility/tie_breaking_validator.py

# Expected exit code: 0 on success (SC‑007)
```

## Expected Artifacts

| Artifact | Location | Description |
|----------|----------|-------------|
| Raw data | data/raw/knot_atlas_raw.json | Downloaded from Knot Atlas |
| Cleaned data | data/processed/knots_cleaned.csv | Parsed and cleaned dataset |
| Validated data | data/processed/knots_validated.csv | Validated dataset with quality flags |
| Hyperbolic data | data/processed/knots_hyperbolic.csv | Filtered to volume > 0 |
| Scatter plots | data/plots/*.png | Crossing number vs braid index plots |
| Data quality report | docs/reproducibility/data_quality_report.md | Null percentages, format validation, duplicates |
| Invariant coverage | docs/reproducibility/invariant_coverage.md | Coverage per invariant |
| Validation scope | docs/reproducibility/validation_scope.md | Completeness benchmark (≤ 10 vs ≤ 13) |
| Excluded knots | docs/reproducibility/excluded_knots.md | Torus/satellite knots filtered |
| Hyperbolic volume validation | docs/reproducibility/hyperbolic_volume_validation.md | Consistency check against KnotInfo |
| Core precision consistency | docs/reproducibility/core_precision_consistency.md | Core invariant agreement with KnotInfo |
| Multicollinearity assessment | docs/reproducibility/multicolinarity_assessment.md | VIF values |
| Residual analysis | docs/reproducibility/residual_analysis.md | Families deviating ≥ 2 SD |
| Tie‑breaking rules | docs/reproducibility/tie_breaking_rules.md | Documented rules |
| Tie‑breaking validator | docs/reproducibility/tie_breaking_validator.py | Validation script (SC‑007) |
| Missing invariants | docs/reproducibility/missing_invariants.md | Documentation of records excluded due to missing invariants |
| Random seeds | docs/reproducibility/random_seeds.md | Seed values |
| Logs | docs/reproducibility/logs/*.log | Timestamped operation logs |
| Checksums | data/checksums.sha256 | SHA‑256 checksums for all data files |
| Validation scope document | docs/reproducibility/validation_scope.md | Detailed completeness benchmark (≤ 10 vs ≤ 13) |
| Random seeds document | docs/reproducibility/random_seeds.md | List of all random seeds used |
| Derivation notes | docs/reproducibility/derivation_notes.md | Step‑by‑step transformation documentation |
| Logs directory | docs/reproducibility/logs/ | Detailed operation logs for each pipeline stage |

All artifacts are generated automatically by the pipeline; no manual intervention is required.
