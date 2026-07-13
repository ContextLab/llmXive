# Quickstart: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

## Prerequisites

- Python 3.11 or higher
- pip package manager
- Stable internet connection (for downloading Knot Atlas data)
- ≥ 14GB disk space, ≥ 7GB RAM

## Installation

1. **Clone Repository**:
   ```bash
   git clone <repository-url>
   cd projects/PROJ-552-quantifying-the-complexity-of-knot-diagr
   ```

2. **Create Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```

4. **Verify Installation**:
   ```bash
   python -c "import pandas; import numpy; import sklearn; print('All dependencies installed successfully')"
   ```

## Data Download

Run the data download script with retry logic:

```bash
python code/download/knot_atlas_loader.py
```

**Output**: `data/raw/knot_atlas_raw.json` (~190MB)

**Features**:
- Exponential backoff retry (initial 1s, multiplier 2, max 32s)
- Partial result caching after 3 consecutive failures
- Checksum generation (SHA-256)

## Data Processing

Run the data pipeline:

```bash
python code/main.py
```

**Steps**:
1. Parse raw data (`code/data/parser.py`)
2. Clean and validate (`code/data/validator.py`)
3. Apply tie-breaking rules (FR-011)
4. Filter hyperbolic knots (FR-012)
5. Generate checksums and logs (FR-007)

**Outputs**:
- `data/processed/knots_cleaned.csv`
- `data/processed/knots_validated.csv`
- `data/processed/hyperbolic_knots.csv`
- `docs/reproducibility/data_quality_report.md`
- `docs/reproducibility/excluded_knots.md`

## Exploratory Analysis

Generate scatter plots and correlation analysis:

```bash
python code/analysis/exploratory.py
```

**Outputs**:
- `data/processed/plots/crossing_vs_braid_alternating.png`
- `data/processed/plots/crossing_vs_braid_non_alternating.png`
- `docs/reproducibility/plot_validation_report.md`

## Regression Modeling

Fit and compare regression models:

```bash
python code/analysis/regression.py
```

**Outputs**:
- `data/processed/model_results.json`
- `docs/reproducibility/multicolinearity_assessment.md`
- `docs/reproducibility/residual_analysis.md`

## Validation & Reproducibility

Run all validation checks:

```bash
python code/reproducibility/checksums.py
python code/reproducibility/logs.py
python docs/reproducibility/tie_breaking_validator.py
```

**Outputs**:
- `data/checksums/manifest.json`
- `docs/reproducibility/validation_status.md`
- `docs/reproducibility/random_seeds.md`

## Expected Results

- **Dataset Size**: ~9,988 prime knots ≤ 13 crossings (source: OEIS A002863, https://oeis.org/A002863)
- **Hyperbolic Subset**: [deferred] knots (volume > 0, exact count varies)
- **Data Quality**: ≥ 95% completeness for required fields (SC-013)
- **Model Selection**: Best-fitting model based on R², AIC/BIC, MAE (SC-002)
- **Residual Analysis**: Specific knot families with residuals ≥ 2σ documented (SC-011)

## Troubleshooting

### API Unavailability
- Retry logic automatically applies exponential backoff
- Partial results cached to disk after 3 failures
- Check `docs/reproducibility/logs.py` for error details

### Missing Invariants
- Records flagged with `missing_invariant_flags`
- Not excluded from dataset; documented in `data_quality_report.md`

### Memory Constraints
- Data processed in chunks if needed
- Intermediate results written to disk
- No GPU-dependent operations

## Next Steps

1. Review `docs/reproducibility/data_quality_report.md` for data quality metrics
2. Examine `docs/reproducibility/residual_analysis.md` for deviation patterns
3. Read `docs/reproducibility/validation_scope.md` for Phase 1 vs. exploratory scope
4. Consult `research.md` for methodological details and statistical rigor considerations
