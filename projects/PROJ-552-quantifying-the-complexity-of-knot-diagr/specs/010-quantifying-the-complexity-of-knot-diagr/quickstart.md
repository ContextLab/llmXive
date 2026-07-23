# Quickstart: Quantifying the Complexity of Knot Diagrams

## Prerequisites

- Python 3.11+
- `pip` or `poetry`
- Internet access (for Knot Atlas download)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd PROJ-552-quantifying-the-complexity-of-knot-diagr
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Pipeline

### 1. Download Data
```bash
python code/main.py --action download
```
- Downloads raw JSON from Knot Atlas.
- Implements exponential backoff on failure.
- Saves to `data/raw/knot_atlas_raw.json`.
- Generates checksum in `data/raw/checksums.json`.

### 2. Parse and Validate
```bash
python code/main.py --action parse
```
- Parses JSON, extracts invariants.
- Applies tie-breaking rules.
- Flags missing data/quality issues.
- Saves to `data/processed/knots_cleaned.csv`.
- Generates `docs/reproducibility/data_quality_report.md`.

### 3. Filter for Hyperbolic Knots
```bash
python code/main.py --action filter
```
- Filters for `hyperbolic_volume > 0`.
- Logs excluded knots to `docs/reproducibility/excluded_knots.md`.
- Saves to `data/processed/knots_hyperbolic.csv`.

### 4. Run Analysis
```bash
python code/main.py --action analyze
```
- Generates scatter plots (`data/plots/`).
- Fits regression models (linear, poly, log).
- Computes correlations and effect sizes.
- Performs residual analysis.
- Saves results to `data/processed/regression_results.json`.

### 5. Generate Reports
```bash
python code/main.py --action report
```
- Generates all reproducibility documents in `docs/reproducibility/`.
- Validates schema compliance.
- Outputs final summary.

## Verification

1. **Check Data Quality**:
   ```bash
   python code/data/quality_report.py --validate
   ```
   - Verifies null percentage ≤ 5%, format pass rate ≥ 99%, no duplicates.

2. **Validate Tie-Breaking**:
   ```bash
   python docs/reproducibility/tie_breaking_validator.py
   ```
   - Ensures consistent application of tie-breaking rules.

3. **Reproducibility Check**:
   ```bash
   python code/reproducibility/checksums.py --verify
   ```
   - Verifies all data files match recorded checksums.

## Troubleshooting

- **API Rate Limiting**: The downloader automatically retries with exponential backoff. If it fails after max retries, partial results are cached.
- **Missing Invariants**: Records are flagged in `data_quality_flags` and `missing_invariant_flags`, not excluded.
- **Plot Resolution**: All plots are generated at 1200x900 px minimum.
