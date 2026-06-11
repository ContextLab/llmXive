# Quickstart: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

## Prerequisites

- Python 3.11 or higher
- pip (Python package manager)
- Stable internet connection (for Knot Atlas download)
- 4 GB available disk space (for data and plots)

## Installation

1. Clone the repository and navigate to the project directory:
   ```bash
   git clone https://github.com/your-org/PROJ-552-quantifying-the-complexity-of-knot-diagr.git
   cd projects/PROJ-552-quantifying-the-complexity-of-knot-diagr/code/
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Verify installation:
   ```bash
   python -c "import pandas; import numpy; import sklearn; print('All dependencies installed successfully')"
   ```

## Running the Pipeline

### Step 1: Download Knot Data

```bash
python download/download_knot_atlas.py --output ../data/raw/knot_atlas_raw.csv
```

- Downloads prime knot data (crossings 1‑13) from Knot Atlas **or** a verified mirror.
- Includes exponential backoff retry logic (3 attempts) and logs simulated failure verification (SC‑005).

### Step 2: Compute Invariants

```bash
python compute/compute_invariants.py --input ../data/raw/knot_atlas_raw.csv --output ../data/processed/invariants_complete.parquet
```

- Computes arc index, Seifert circle count, bridge number.
- Flags records with missing invariants (not silent exclusion).

### Step 3: Validate Algorithms

```bash
python validate/algorithm_validation.py --input ../data/processed/invariants_complete.parquet
```

- Validates computed invariants against KnotInfo reference values.
- Documents coverage; skips if coverage (FR‑003).

### Step 4: Tie‑Breaking Validation

```bash
python validate/validate_tie_breaking.py --input ../data/processed/invariants_complete.parquet
```

- Ensures deterministic handling of multiple diagram representations per SC‑008.

### Step 5: Exploratory Analysis

```bash
python analyze/exploratory_analysis.py --input ../data/processed/invariants_complete.parquet
```

- Generates scatter plots of crossing number vs. braid index, stratified by alternating class.
- Outputs: `data/plots/crossing_vs_braid_alternating.png`, `data/plots/crossing_vs_braid_non_alternating.png`

### Step 6: Regression Modeling

```bash
python analyze/regression_models.py --input ../data/processed/invariants_complete.parquet
```

- Fits linear, polynomial, and logarithmic models.
- Performs 5‑fold cross‑validation; selects model by AIC → BIC → MAE.
- Conducts ANOVA for group differences (SC‑011).

### Step 7: Composite Score Validation

```bash
python analyze/regression_models.py --input ../data/processed/invariants_complete.parquet --compute-composite-score
```

- Constructs composite complexity score (default 1:1 weights).
- Validates correlation with hyperbolic volume (reports Pearson & Spearman, effect sizes).

### Step 8: Reproducibility Check

```bash
python validate/reproducibility_check.py --data-dir ../data/ --docs-dir ../docs/reproducibility/
```

- Verifies SHA‑256 checksums, derivation notes, timestamps.
- Produces `docs/reproducibility/validation_status.md`.

## Verifying Success Criteria

### SC‑001: Dataset Completeness

```bash
python -c "
import pandas as pd
df = pd.read_parquet('../data/processed/invariants_complete.parquet')
print(f'Total records: {len(df)}')
print(f'Crossing number range: {df.crossing_number.min()} to {df.crossing_number.max()}')
print(f'Knots with complete invariants: {(df.missing_invariant_flags.isna() | (df.missing_invariant_flags.apply(len) == 0)).sum()}')
"
```

### SC‑009: Plot Generation

```bash
ls -lh ../data/plots/
# Should show crossing_vs_braid_alternating.png and crossing_vs_braid_non_alternating.png
# Minimum resolution 1200x900 pixels
```

### SC‑004: Reproducibility Artifacts

```bash
ls ../docs/reproducibility/
# Should include: invariant_algorithms.md, algorithm_validation.md, validation_scope.md,
# tie_breaking_rules.md, validate_tie_breaking.md, excluded_knots.md,
# uncomputable_invariants.md, validation_status.md
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Knot Atlas download fails | Check network; retry with exponential backoff; partial results cached after 3 failures |
| Missing invariant computation | Check diagram representation availability; records flagged in `uncomputable_invariants.md` |
| Hyperbolic volume = 0 | Torus/satellite knots excluded per FR‑014; documented in `excluded_knots.md` |
| Algorithm validation coverage | Skip validation per FR‑003; limitation documented in `algorithm_validation.md` |
| ANOVA assumption violations | Use Welch's ANOVA or Kruskal‑Wallis; document deviation |

## Next Steps

1. Review `docs/reproducibility/validation_scope.md` for Phase 1 scope boundaries.  
2. Examine `docs/reproducibility/algorithm_validation.md` for algorithm validation results.  
3. Check `data/plots/` for exploratory visualizations.  
4. Read generated model metrics in analysis logs.  
5. Proceed to paper writing with all statistics traced to `data/` (Constitution Principle IV).
