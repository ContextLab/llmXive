# Quickstart: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

## Prerequisites

- Python 3.11 or higher
- Stable internet connection (for downloading from KnotInfo/HTW)
- At least 500MB disk space for data and processed outputs

## Installation

1. Clone the repository and navigate to the project directory:
   ```bash
   git clone <repository-url>
   cd projects/PROJ-552-quantifying-the-complexity-of-knot-diagr
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r code/requirements.txt
   ```

## Quick Start

### Step 1: Download Knot Data

```bash
python code/data/download_knot_data.py --crossing-limit 13
```

This downloads all prime knots with crossing number ≤13 from KnotInfo/HTW. Data is saved to `data/raw/knot_atlas_export.csv`.

**Retry Verification**: Exponential backoff (2s, [deferred], [deferred]...) applied; partial results cached after 3 consecutive failures.

### Step 2: Parse and Clean Data

```bash
python code/data/parse_knot_data.py
```

Parses the raw data and creates:
- `data/processed/invariants_dataset.parquet` (processed dataset)
- `docs/reproducibility/excluded_knots.md` (hyperbolic volume filtering log)
- `docs/reproducibility/classification_counts.md` (ambiguous classification counts)
- `docs/reproducibility/validation_scope.md` (Phase 1 scope boundaries)

### Step 3: Compute Additional Invariants

```bash
python code/data/compute_invariants.py
```

Computes arc index, Seifert circle count, and bridge number where diagram representations are available. Records with missing invariants are flagged. Produces:
- `docs/reproducibility/uncomputable_invariants.md` (coverage metrics per SC-006/SC-010)
- `docs/reproducibility/algorithm_validation.md` (pass/fail status per SC-012)

### Step 4: Exploratory Analysis

```bash
python code/analysis/exploratory_analysis.py
```

Generates scatter plots of crossing number vs. braid index, stratified by alternating/non-alternating classification. Performs ANOVA with effect sizes (Cohen's d, r). Plots saved to `data/plots/`.

### Step 5: Fit Regression Models

```bash
python code/analysis/regression_models.py
```

Fits linear, polynomial (degree=2), and logarithmic (base e) regression models. Results conform to `contracts/regression_output.schema.yaml`.

### Step 6: Construct and Validate Composite Score

```bash
python code/analysis/composite_score.py
```

Constructs composite complexity score with configurable weights. Validates against exploratory validation sample.

## Reproducibility

All analysis is reproducible with pinned random seeds. To verify:

```bash
python code/utils/reproducibility_utils.py --verify
```

This checks that all checksums match and derivation notes are complete.

## Output Files

| File | Location | Description |
|------|----------|-------------|
| knot_atlas_export.csv | data/raw/ | Raw downloaded data |
| invariants_dataset.parquet | data/processed/ | Processed dataset with invariants |
| exploratory_validation_sample.parquet | data/processed/ | Stratified validation sample |
| crossing_vs_braid_stratified.png | data/plots/ | Exploratory scatter plot |
| checksums.md | docs/reproducibility/ | SHA-256 checksums for all data files |
| derivation_notes.md | docs/reproducibility/ | Step-by-step transformation documentation |
| logs/ | docs/reproducibility/logs/ | Timestamped execution logs |
| excluded_knots.md | docs/reproducibility/ | Hyperbolic volume filtering log |
| classification_counts.md | docs/reproducibility/ | Ambiguous classification counts |
| validation_scope.md | docs/reproducibility/ | Phase 1 scope boundaries |
| uncomputable_invariants.md | docs/reproducibility/ | Coverage metrics per invariant |
| algorithm_validation.md | docs/reproducibility/ | Algorithm validation pass/fail |
| tie_breaking_rules.md | docs/reproducibility/ | Tie-breaking policy documentation |

## Troubleshooting

### KnotInfo Unavailable

If KnotInfo is unavailable, the download script will retry with exponential backoff (2s, [deferred], [deferred], etc.). After 3 consecutive failures, partial results are cached to disk. See `docs/reproducibility/logs/` for retry logs.

### Missing Invariants

Records with missing invariants are flagged in the dataset rather than silently excluded. See `docs/reproducibility/uncomputable_invariants.md` for details.

### Ambiguous Classification

Knots with ambiguous alternating/non-alternating classification are marked as "unclassifiable" or excluded from stratified analysis. Count logged in `docs/reproducibility/classification_counts.md`.

### Tie-Breaking

Crossing number ties are handled per documented rules in `docs/reproducibility/tie_breaking_rules.md`.

## Next Steps

- Review `docs/reproducibility/validation_scope.md` for Phase 1 scope boundaries
- Check `docs/reproducibility/algorithm_validation.md` for algorithm validation status
- Examine `docs/reproducibility/excluded_knots.md` for filtered records (torus/satellite knots)