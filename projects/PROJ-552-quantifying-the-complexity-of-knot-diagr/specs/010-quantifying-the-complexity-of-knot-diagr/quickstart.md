# Quickstart: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

## Prerequisites

- Python 3.11 or higher
- Git for version control
- Stable internet connectivity (for downloading Knot Atlas data)
- At least 5GB disk space for data and analysis artifacts

## Installation

### 1. Clone Repository

```bash
git clone <repository-url>
cd projects/PROJ-552-quantifying-the-complexity-of-knot-diagr
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

**requirements.txt** contains pinned versions of all dependencies:
- pandas
- numpy
- scikit-learn
- matplotlib
- seaborn
- requests
- pyyaml
- jsonschema
- arxiv

## Data Download

### Run Download Script

```bash
python code/src/download.py --crossing-limit 13 --output data/raw/knot_atlas_raw.parquet
```

**Options**:
- `--crossing-limit`: Maximum crossing number to download (default: 13, validated for ≤10 in Phase 1)
- `--output`: Output file path for downloaded data

**Retry Behavior**: Exponential backoff (initial=1s, max=32s, multiplier=2) on API failures. Partial results cached after 3 consecutive failures.

### Verify Download

```bash
python code/src/reproducibility.py --verify-checksums data/raw/knot_atlas_raw.parquet
```

Expected output: Checksum verification passed, null percentage <1%.

## Data Cleaning

### Run Cleaning Script

```bash
python code/src/clean.py --input data/raw/knot_atlas_raw.parquet --output data/processed/knot_records_clean.parquet
```

**Actions**:
- Parse and clean dataset
- Flag records with data quality issues
- Apply tie-breaking rules for diagram representation ties
- Generate `data_quality_report.md` in `docs/reproducibility/`
- Generate `excluded_knots.md` with exclusion counts and percentages

### Validate Cleaned Data

```bash
python code/src/reproducibility.py --validate-schema data/processed/knot_records_clean.parquet
```

Expected output: Schema validation passed, no duplicates detected.

## Exploratory Analysis

### Generate Scatter Plots

```bash
python code/src/analysis.py --task exploratory --input data/processed/knot_records_clean.parquet
```

**Outputs**:
- `data/plots/crossing_vs_braid_alternating.png`
- `data/plots/crossing_vs_braid_non_alternating.png`

**Resolution**: Minimum 1200x900 pixels (per FR-004).

## Regression Analysis

### Fit Regression Models

```bash
python code/src/analysis.py --task regression --input data/processed/knot_records_clean.parquet --model-types linear,polynomial,logarithmic
```

**Outputs**:
- `data/processed/regression_results.json`
- `docs/reproducibility/multicollinearity_assessment.md`
- `docs/reproducibility/residual_analysis.md`

**Model Types**: Linear, polynomial, and logarithmic regression (per FR-005).

### Filter to Hyperbolic Knots

```bash
python code/src/clean.py --filter hyperbolic --input data/processed/knot_records_clean.parquet --output data/processed/knot_records_hyperbolic.parquet
```

**Note**: This applies FR-012 filtering (volume > 0). Excluded knots documented in `docs/reproducibility/excluded_knots.md` with percentage of total dataset.

## Reproducibility Documentation

### Generate All Artifacts

```bash
python code/src/reproducibility.py --generate-all --input data/processed/
```

**Outputs**:
- SHA-256 checksums for all data files
- Derivation notes with formula citations
- Timestamped logs
- Random seed documentation

### Verify Reproducibility

```bash
python code/src/reproducibility.py --verify-reproducibility
```

Expected output: All reproducibility artifacts present and verified.

## Testing

### Run Contract Tests

```bash
pytest tests/contract/ -v
```

Tests validate that all data files conform to schema definitions in `contracts/` directory.

### Run Integration Tests

```bash
pytest tests/integration/ -v
```

Tests validate end-to-end pipeline execution.

### Run Unit Tests

```bash
pytest tests/unit/ -v
```

Tests validate individual functions and modules.

## Phase 1 Scope Limitation

**Important**: All Phase 1 conclusions must be explicitly qualified as limited to validated crossing number ≤10 data. Any analysis using crossing number 11-13 data must be marked as exploratory/unvalidated in final reports.

To restrict analysis to validated data:

```bash
python code/src/analysis.py --validated-only --input data/processed/knot_records_clean.parquet
```

**Note**: The `--validated-only` flag strictly enforces `crossing_number <= 10` filter before any statistical computation, preventing cross-contamination between validated and exploratory data.

## Statistical Output Disclaimer

All statistical outputs include explicit disclaimer: "p-values are not applicable for census data. This dataset represents complete enumeration of prime knots ≤13 crossings. Effect sizes are the primary metrics for all statistical claims."

## Troubleshooting

### API Unavailable

If Knot Atlas is unavailable, the download script will:
1. Retry with exponential backoff (1s, 2s, 4s, 8s, 16s, 32s)
2. Cache partial results after 3 consecutive failures
3. Log all retry attempts in timestamped logs

Check `docs/reproducibility/download_logs.md` for retry details.

### Missing Invariants

If knots have missing invariant data, they will be flagged with `missing_invariant_flags` rather than silently excluded. Check `docs/reproducibility/uncomputable_invariants.md` for details.

### Ambiguous Classification

If knots have ambiguous alternating/non-alternating classification, they will either be excluded from stratified analysis (with count logged) or marked as "unclassifiable". Check `docs/reproducibility/data_quality_report.md` for counts.

## Next Steps

1. Review `docs/reproducibility/data_quality_report.md` for data quality metrics
2. Review `docs/reproducibility/excluded_knots.md` for exclusion counts and percentages
3. Review `docs/reproducibility/hyperbolic_volume_validation.md` for validation results
4. Proceed to regression analysis with filtered hyperbolic dataset
5. Document findings with explicit acknowledgment of Phase 1 scope limitations and census data statistical disclaimer