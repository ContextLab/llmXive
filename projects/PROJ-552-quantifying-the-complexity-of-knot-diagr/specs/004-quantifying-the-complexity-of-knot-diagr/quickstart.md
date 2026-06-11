# Quickstart: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

## Prerequisites

- Python 3.11 or later
- Access to internet (for downloading data from Knot Atlas)
- 2GB+ available disk space (for data storage and processing)

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd projects/PROJ-552-quantifying-the-complexity-of-knot-diagr

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Configuration

### Environment Variables

```bash
# Optional: Set Knot Atlas API timeout (default: 30 seconds)
export KNOT_ATLAS_TIMEOUT=30

# Optional: Set retry configuration (default: initial=1s, max=60s, multiplier=2)
export RETRY_INITIAL=1
export RETRY_MAX=60
export RETRY_MULTIPLIER=2
```

### Composite Score Weights

Edit `config/complexity_weights.yaml` to customize the composite complexity score:

```yaml
# Default equal weights (1:1 ratio)
weight_crossing: 1.0
weight_braid: 1.0
```

## Running the Pipeline

### Step 1: Download Data

```bash
python -m code.download.knot_atlas_downloader --crossing-number 13 --output data/raw/knot_atlas_download.csv
```

This will:
- Download all prime knots with crossing number ≤13 from Knot Atlas (via HTML scraping)
- Apply exponential backoff retry logic if the API is unavailable
- Save raw data to `data/raw/knot_atlas_download.csv`
- Generate checksum file at `data/checksums.txt`
- Expected output: the number of prime knots at a specified crossing number (source: OEIS A002863, https://oeis.org/A002863)

### Step 2: Compute Invariants

```bash
python -m code.compute.invariant_computation --input data/raw/knot_atlas_download.csv --output data/processed/invariants_dataset.csv
```

This will:
- Compute arc index, Seifert circle count, and bridge number where diagram representations are available
- Flag records with missing invariants
- Generate validation report at `docs/reproducibility/algorithm_validation.md`

### Step 3: Validate Tie-Breaking Rules (SC-008 Deliverable)

```bash
python -m code.compute.tie_breaking_validator --input data/processed/invariants_dataset.csv --output docs/reproducibility/tie_breaking_validation.md
```

This will:
- Verify tie-breaking rules are applied consistently across all invariant computations
- Generate validation report documenting any violations
- Required deliverable per SC-008

### Step 4: Exploratory Analysis

```bash
python -m code.analysis.exploratory_analysis --input data/processed/invariants_dataset.csv --output data/plots/
```

This will:
- Generate scatter plots of crossing number vs. braid index stratified by alternating classification
- Save plots to `data/plots/` with minimum resolution 1200x900 pixels

### Step 5: Regression Modeling (Full Dataset)

```bash
python -m code.analysis.regression_models --input data/processed/invariants_dataset.csv --output data/processed/regression_models.json
```

This will:
- Fit linear, polynomial, and logarithmic regression models on FULL DATASET (no train/validation split)
- Compute VIF for multicollinearity assessment
- Identify residual outliers (knot families deviating from global trend)

### Step 6: Composite Score Validation (Exploratory Only)

```bash
python -m code.analysis.composite_score --input data/processed/invariants_dataset.csv --config config/complexity_weights.yaml --output data/processed/composite_scores.json
```

This will:
- Compute composite complexity scores with configured weights
- Validate against full dataset (exploratory ranking only, no predictive claims)
- Report Pearson and Spearman correlations with effect sizes

### Step 7: Reproducibility Check

```bash
python -m code.utils.reproducibility --data-dir data/ --output docs/reproducibility/
```

This will:
- Verify all random seeds are pinned
- Generate SHA-256 checksums for all data files
- Document all transformations with derivation notes
- Generate timestamped logs

## Output Files

| File | Description |
|------|-------------|
| `data/raw/knot_atlas_download.csv` | Raw downloaded data from Knot Atlas |
| `data/processed/invariants_dataset.csv` | Dataset with computed invariants |
| `data/plots/crossing_vs_braid_*.png` | Exploratory scatter plots |
| `data/processed/regression_models.json` | Fitted regression models with metrics |
| `data/processed/composite_scores.json` | Composite complexity scores (exploratory only) |
| `data/checksums.txt` | SHA-256 checksums for all data files |
| `docs/reproducibility/*.md` | Reproducibility documentation |
| `docs/reproducibility/tie_breaking_validation.md` | Tie-breaking rule validation report (SC-008) |

## Troubleshooting

### Knot Atlas Unavailable

If the download fails due to API unavailability:
- Check `docs/reproducibility/validation_status.md` for retry status
- Partial results are cached after 3 consecutive failures
- Retry logic applies exponential backoff (→ → →... → max)
- Timeline extended if rate limits exceeded

### Missing Invariants

If invariant computation fails for some knots:
- Check `docs/reproducibility/uncomputable_invariants.md` for flagged records
- Records are not silently excluded; they are flagged with `missing_invariant_flags`

### ANOVA Assumption Violations

If Levene's test or Shapiro-Wilk test fails:
- System automatically uses robust alternatives (Welch's ANOVA, Kruskal-Wallis)
- Deviation is documented in `docs/reproducibility/validation_status.md`

## Validation

Run the validation suite to verify all success criteria:

```bash
pytest tests/contract/ -v
```

This verifies:
- SC-001: Dataset completeness for crossing number ≤10
- SC-005: Retry logic with exponential backoff
- SC-008: Tie-breaking rule consistency (via test_tie_breaking_validation.py)
- SC-012: Algorithm validation against KnotInfo
- Contract schemas: knot_record, regression_output, composite_score