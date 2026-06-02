# Quickstart: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

## Prerequisites

- Python 3.11 or higher
- pip or poetry for dependency management
- Internet connectivity for downloading data from Knot Atlas
- At least 2GB available disk space for data storage

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd projects/PROJ-552-quantifying-the-complexity-of-knot-diagr

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Quick Start Commands

### Step 1: Download Knot Data

```bash
python src/cli/main.py download --crossing-max 13 --output data/raw/knots.parquet
```

This downloads all prime knots with crossing number ≤13 from Knot Atlas, applies retry logic with exponential backoff, and writes the output to `data/raw/knots.parquet`.

### Step 2: Compute Invariants

```bash
python src/cli/main.py compute-invariants --input data/raw/knots.parquet --output data/processed/knots_with_invariants.parquet
```

Computes arc index, Seifert circle count, and bridge number where diagram representations are available. Records missing_invariant_flags for uncomputable values.

### Step 3: Generate Exploratory Plots

```bash
python src/cli/main.py plot --input data/processed/knots_with_invariants.parquet --output data/plots/
```

Generates scatter plots of crossing number vs. braid index stratified by alternating/non-alternating classification (minimum resolution 1200x900 pixels).

### Step 4: Fit Regression Models

```bash
python src/cli/main.py regress --input data/processed/knots_with_invariants.parquet --output data/processed/regression_results.json
```

Fits linear and polynomial regression models, computes VIF values, and outputs model metrics.

### Step 5: Generate Reproducibility Documentation

```bash
python src/cli/main.py reproducibility --output docs/reproducibility/
```

Generates checksums, derivation notes, random seed documentation, and logs.

## Validation

```bash
# Verify dataset completeness for crossing number ≤10
python src/cli/main.py validate --input data/processed/knots_with_invariants.parquet --target-crossing 10

# Verify tie-breaking rule consistency
python src/cli/main.py validate-tiebreaking --input data/processed/knots_with_invariants.parquet
```

## Output Files

| File | Description |
|------|-------------|
| `data/raw/knots.parquet` | Raw downloaded dataset |
| `data/processed/knots_with_invariants.parquet` | Dataset with computed invariants |
| `data/processed/regression_results.json` | Regression model metrics |
| `data/plots/*.png` | Exploratory analysis plots |
| `docs/reproducibility/checksums.json` | SHA-256 checksums for all data files |
| `docs/reproducibility/derivation_notes.md` | Step-by-step transformation documentation |
| `docs/reproducibility/validation_scope.md` | Phase 1 scope boundaries documentation |
