# Quickstart: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

## Prerequisites

- Python 3.11 or higher
- Stable internet connection (for data download)
- ≥2GB available disk space
- Git for version control

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd projects/PROJ-552-quantifying-the-complexity-of-knot-diagr

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r code/requirements.txt
```

## Running the Analysis

### Step 1: Download Knot Data

```bash
python code/download/knot_atlas_downloader.py --output data/raw/knot_atlas_raw.json
```

This will:
- Attempt to download from Knot Atlas with retry logic (exponential backoff: 1s → 2s → 4s →... → 60s max)
- Cache partial results after 3 consecutive failures
- Log all operations to docs/reproducibility/logs/download.log

### Step 2: Compute Invariants

```bash
python code/compute/invariant_computer.py \
    --input data/raw/knot_atlas_raw.json \
    --output data/processed/invariants_computed.csv \
    --seed 42
```

This will:
- Compute arc index, Seifert circle count, and bridge number where diagram representations are available
- Flag records with missing_invariant_flags rather than silent exclusion
- Apply tie-breaking rules (braid word preferred over DT code; lexicographically first DT code)
- Record checksums in data/checksums.json

### Step 3: Run Exploratory Analysis

```bash
python code/analysis/exploratory.py \
    --input data/processed/invariants_computed.csv \
    --output data/plots/
```

This will generate:
- `crossing_vs_braid_alternating.png` (1200x900+ pixels)
- `crossing_vs_braid_non_alternating.png` (1200x900+ pixels)

### Step 4: Fit Regression Models

```bash
python code/analysis/regression.py \
    --input data/processed/invariants_computed.csv \
    --output data/processed/regression_models.pkl \
    --seed 42
```

### Step 5: Validate Composite Score

```bash
python code/analysis/validation.py \
    --input data/processed/invariants_computed.csv \
    --models data/processed/regression_models.pkl \
    --output data/validation_results.json \
    --seed 42
```

### Step 6: Generate Reproducibility Documentation

```bash
python code/reproducibility/checksums.py \
    --data-dir data/ \
    --output docs/reproducibility/checksums.json

python code/reproducibility/validation_scripts.py \
    --input data/processed/invariants_computed.csv \
    --output docs/reproducibility/validation_status.md
```

## Verifying Results

### Dataset Completeness Check

```bash
python code/reproducibility/validation_scripts.py \
    --check completeness \
    --expected-crossing-max 10 \
    --min-completeness 0.95
```

Expected: ≥95% completeness for crossing numbers ≤10

### Algorithm Validation Check

```bash
python code/reproducibility/validation_scripts.py \
    --check algorithm_validation \
    --min-match-threshold 0.95
```

Expected: ≥95% match with KnotInfo reference values where coverage ≥10%

### Tie-Breaking Consistency Check

```bash
python code/reproducibility/validation_scripts.py \
    --check tie_breaking \
    --require-consistency true
```

Expected: 100% consistency across all records with multiple diagram representations

## Configuration

Edit `config/complexity_weights.yaml` to customize composite score weights:

```yaml
crossing_weight: 0.5
braid_weight: 0.5
```

## Troubleshooting

### Knot Atlas Unavailable

If Knot Atlas returns HTTP 404 or rate-limits requests:
- The downloader will automatically retry with exponential backoff
- After 3 consecutive failures, partial results are cached to disk
- Check `docs/reproducibility/logs/download.log` for error details
- The system will continue with partial data rather than failing completely

### Missing Invariant Data

If invariants cannot be computed:
- Records are flagged with `missing_invariant_flags` rather than excluded
- See `docs/reproducibility/uncomputable_invariants.md` for details
- Coverage should be ≥99% (SC-006)

### Ambiguous Classification

If alternating/non-alternating classification is ambiguous:
- Records are either excluded from stratified analysis (with count logged) or marked as "unclassifiable"
- See `docs/reproducibility/validation_status.md` for exclusion counts
