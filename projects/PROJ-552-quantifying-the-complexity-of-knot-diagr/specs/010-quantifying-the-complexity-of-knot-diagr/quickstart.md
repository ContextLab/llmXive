# Quickstart: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

## Prerequisites

- Python 3.11+
- `pip` (package manager)
- Internet connection (for downloading data via `database-knotinfo`)

## Installation

1. **Clone the Repository**:
 ```bash
 git clone
 cd quantifying-knot-complexity
 ```

2. **Install Dependencies**:
 ```bash
 pip install -r requirements.txt
 ```
 *Note: `requirements.txt` includes `database-knotinfo`, `pandas`, `numpy`, `scipy`, `scikit-learn`, `matplotlib`, `pyyaml`, `requests`.*

3. **Verify Installation**:
 ```bash
 python -c "from database_knotinfo import link_list; print(f'Records loaded: {len(list(link_list()))}')"
 ```
 *Expected output: "Records loaded: [variable count]" (or similar, depending on database version).*

## Running the Pipeline

### Full Pipeline

Execute the entire data download, processing, analysis, and reporting pipeline:

```bash
python code/main.py
```

This will:
1. Download knot data from `database-knotinfo`.
2. Parse, validate, and filter the data.
3. Generate exploratory plots.
4. Fit regression models.
5. Perform residual analysis.
6. Generate reproducibility artifacts (checksums, logs, reports).

### Individual Steps

#### Data Download & Parsing

```bash
python code/download/knot_info_loader.py
python code/data/parser.py
```

#### Filtering

```bash
python code/data/filter.py
```

#### Exploratory Analysis

```bash
python code/analysis/exploratory.py
```

#### Regression Modeling

```bash
python code/analysis/regression.py
```

#### Residual Analysis

```bash
python code/analysis/residual.py
```

#### Reproducibility Check

```bash
python code/reproducibility/checksums.py
python code/reproducibility/logs.py
```

## Output Files

After running the pipeline, the following files will be generated:

- `data/raw/knot_atlas_raw.json` (Raw data)
- `data/processed/knots_cleaned.csv` (Cleaned data)
- `data/processed/knots_hyperbolic.csv` (Filtered data)
- `data/analysis/regression_results.json` (Model metrics)
- `data/analysis/residuals.csv` (Residual data)
- `docs/reproducibility/data_quality_report.md`
- `docs/reproducibility/validation_scope.md`
- `docs/reproducibility/excluded_knots.md`
- `docs/reproducibility/random_seeds.md`
- `docs/reproducibility/hyperbolic_volume_validation.md`
- `docs/reproducibility/core_precision_consistency.md`
- `docs/reproducibility/tie_breaking_rules.md`
- `docs/reproducibility/residual_analysis.md`
- `docs/reproducibility/multicollinearity_assessment.md`
- `data/plots/` (Generated PNG plots)

## Troubleshooting

### API Unavailability

If the `database-knotinfo` library fails to fetch data, the pipeline will:
1. Retry with exponential backoff (initial 1s, multiplier 2, max 32s).
2. Cache partial results after 3 consecutive failures.
3. Log the error in `docs/reproducibility/logs.py`.

### Missing Invariants

Records with missing invariants are flagged with `missing_invariant_flags` and included in the dataset. Check `docs/reproducibility/data_quality_report.md` for details.

### Ambiguous Classifications

Knots with ambiguous alternating/non-alternating classification are either excluded from stratified analysis (with count logged) or marked as "unclassifiable".

### Tie-Breaking Validation

If tie-breaking rules are inconsistent, the validation script `docs/reproducibility/tie_breaking_validator.py` will fail. Re-run invariant computations with consistent rules.

## Reproducibility

To ensure reproducibility:
- Random seeds are pinned in `code/` (see `docs/reproducibility/random_seeds.md`).
- All data files are checksummed (SHA-256) and recorded in `data/`.
- Derivation notes and logs are stored in `docs/reproducibility/`.
- Re-run `python code/main.py` on a fresh environment to reproduce all results.

## Next Steps

- **Phase 2**: Compute additional invariants (arc index, Seifert circle count, bridge number) and validate against KnotInfo.
- **Phase 3**: Extend analysis to crossing number > 13 (if data becomes available).
- **Phase 4**: Publish results and share code/data with the community.
