# Quickstart: Assessing the Sensitivity of Regression Coefficients to Dataset Subset Selection

## Prerequisites
- Python 3.11+
- `pip` or `poetry`
- Git

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd <project-dir>
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Install pre-commit hooks**:
   ```bash
   pre-commit install
   ```

## Running the Pipeline

The pipeline is executed via the CLI entry point. It automatically handles data ingestion, per-subset profiling, resampling, stratified analysis, and **generates stability curves**.

```bash
# Run the full analysis
python src/cli.py run --datasets california_housing,delaney,wine_quality --output artifacts/
```

**Arguments**:
- `--datasets`: Comma-separated list of dataset keys (e.g., `california_housing`, `delaney`, `wine_quality`).
- `--output`: Output directory for artifacts (default: `artifacts/`).

### Step-by-Step Breakdown

1. **Ingestion & Per-Subset Profiling**:
   - Downloads datasets from verified HuggingFace/UCI URLs.
   - For each tier (low, medium, high), generates a representative set of subsets.
   - For **each subset**, computes Condition Number, Breusch-Pagan, and Cook's Distance.
   - Saves `artifacts/profiles/{dataset}_{tier}_{id}.json`.

2. **Resampling & Stability**:
   - Fits OLS models to each subset.
   - Computes SD of coefficients across multiple subsets per tier.
   - Checks convergence (SE of SD < 7%).
   - **Excludes** tiers that fail convergence from the final analysis.
   - Saves `artifacts/stability/coefficient_sd.json` and `artifacts/convergence.log`.

3. **Stratified Analysis & Visualization**:
   - Bins subsets by violation severity (Low/Med/High).
   - Runs Kruskal-Wallis tests to compare stability across bins.
   - **Generates stability curves** (Mean SD vs Severity Bin) and saves them as `artifacts/figures/stability_curves.csv` and `artifacts/figures/stability_curves.png`.
   - Saves `artifacts/stratified_analysis/results.json`.

## Verification

1. **Check Convergence**:
   ```bash
   cat artifacts/convergence.log
   ```
   Ensure lines show `PASSED`. If `FAILED (Excluded)` appears, that tier was correctly excluded from the final analysis.

2. **View Stratified Results**:
   - Open `artifacts/stratified_analysis/results.json` to see binning statistics and test p-values.
   - Or inspect `artifacts/figures/stability_curves.png` to visualize the relationship between violation severity and coefficient stability.

3. **Validate Artifacts**:
   ```bash
   python -m pytest tests/
   ```
   This runs unit and integration tests to verify the pipeline logic and artifact structure.

4. **Reproducibility Check**:
   Re-run the command with the same arguments. The output files in `artifacts/` should have identical content hashes.