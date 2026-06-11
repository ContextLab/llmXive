# Quickstart: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

## Prerequisites

- Python 3.11+
- Access to Knot Atlas (https://katlas.org)
- Stable internet connection for data download
- ~100MB disk space for dataset and plots

## Installation

```bash
# Clone repository
git clone <repository-url>
cd projects/PROJ-552-quantifying-the-complexity-of-knot-diagr

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r src/requirements.txt
```

## Quick Run

```bash
# Step 1: Download knot data (Phase 0)
python src/cli/main.py download --crossing-max 13 --output data/raw/knot_atlas_export.csv

# Step 2: Compute invariants (Phase 1)
python src/cli/main.py compute-invariants --input data/raw/knot_atlas_export.csv --output data/processed/invariants_dataset.parquet

# Step 3: Generate exploratory plots (Phase 1)
python src/cli/main.py plot --input data/processed/invariants_dataset.parquet --output-dir data/plots/

# Step 4: Fit regression models (Phase 1)
python src/cli/main.py fit-models --input data/processed/invariants_dataset.parquet --output models/regression_models.json

# Step 5: Compute composite complexity score (Phase 1)
python src/cli/main.py composite-score --input data/processed/invariants_dataset.parquet --config config/complexity_weights.yaml --output models/composite_complexity_score.json

# Step 6: Generate reproducibility documentation (Phase 1)
python src/cli/main.py reproducibility --data-dir data/ --docs-dir docs/reproducibility/
```

## Configuration

Edit `config/complexity_weights.yaml` to customize composite score weights:

```yaml
crossing_weight: 1.0
braid_weight: 1.0
```

## Validation

```bash
# Run contract tests
pytest tests/contract/

# Run integration tests
pytest tests/integration/

# Verify dataset completeness
python src/cli/main.py validate-completeness --input data/processed/invariants_dataset.parquet --expected-cumulative-counts https://oeis.org/A002863
```

## Output Artifacts

| Artifact | Location | Description |
|----------|----------|-------------|
| Raw dataset | `data/raw/knot_atlas_export.csv` | Downloaded Knot Atlas export |
| Processed dataset | `data/processed/invariants_dataset.parquet` | Dataset with computed invariants |
| Exploratory plots | `data/plots/*.png` | Scatter plots (1200x900 pixels) |
| Regression models | `models/regression_models.json` | Fitted model coefficients and metrics |
| Composite score | `models/composite_complexity_score.json` | Complexity scores and validation correlations |
| Reproducibility docs | `docs/reproducibility/` | Checksums, derivation notes, logs |

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Knot Atlas unavailable | Retry logic with exponential backoff (→ → →... → max); partial results cached after 3 failures |
| Missing invariant data | Records flagged with `missing_invariant_flags`; check `docs/reproducibility/uncomputable_invariants.md` |
| Algorithm validation fails | Check `docs/reproducibility/algorithm_validation.md` for pass/fail status and coverage constraints |
| ANOVA assumptions violated | System automatically uses Welch's ANOVA or Kruskal-Wallis; results documented in output |
| Murasugi's theorem constraint | Alternating knots excluded from joint regression; only non-alternating knots used for joint modeling |