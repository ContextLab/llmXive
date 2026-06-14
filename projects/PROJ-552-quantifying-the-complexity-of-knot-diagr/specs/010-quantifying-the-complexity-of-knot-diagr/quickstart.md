# Quickstart: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

## Prerequisites

*   Python 3.11+
*   Stable internet connectivity (for data download)
*   Access to Knot Atlas (spec reference: `https://katlas.org`)

## Installation

1.  Clone the repository and navigate to the project directory.
2.  Create a virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate
    ```
3.  Install dependencies from `code/requirements.txt`:
    ```bash
    pip install -r code/requirements.txt
    ```

## Execution Steps

### Step 1: Data Download

Run the data download script to fetch knot data from Knot Atlas.

```bash
python code/download/fetch_knot_data.py
```

*   **Output**: `data/raw/knot_atlas_export.json`
*   **Robustness**: Implements retry logic with exponential backoff (FR-008). Partial results cached on failure.

### Step 2: Data Validation & Cleaning

Run the invariant validation script to parse and clean the dataset.

```bash
python code/analysis/validate_invariants.py
```

*   **Output**: `data/processed/invariants_dataset.csv`
*   **Flags**: Records with missing invariants flagged in `missing_invariant_flags`.
*   **Quality Check**: Null percentage ≤ 5% per field (SC-013).

### Step 3a: Exploratory Analysis

Generate scatter plots of crossing number vs. braid index.

```bash
python code/analysis/plot_generation.py
```

*   **Output**: `data/plots/crossing_vs_braid.png`
*   **Resolution**: Minimum 1200x900 pixels (FR-004).
*   **Stratification**: Alternating vs. non-alternating classification.

### Step 3b: Correlation Analysis

Compute correlation coefficients (Spearman primary, Pearson supplementary) and effect sizes.

```bash
python code/analysis/correlation_analysis.py
```

*   **Output**: `docs/reproducibility/correlation_results.json`
*   **Metrics**: Spearman r, Pearson r, Cohen's d for group comparisons (FR-006).
*   **Note**: P-values marked as "not applicable for census data".

### Step 3c: Hyperbolic Volume Cross-Check

Cross-check hyperbolic volume values against KnotInfo reference values.

```bash
python code/analysis/validate_hyperbolic_volume.py
```

*   **Output**: `docs/reproducibility/hyperbolic_volume_validation.md`
*   **Threshold**: ≥ 90% match against reference values (SC-014).

### Step 3d: Group Comparison Metrics

Compute descriptive comparison metrics for alternating vs. non-alternating groups.

```bash
python code/analysis/group_comparison.py
```

*   **Output**: `docs/reproducibility/group_comparison_metrics.json`
*   **Metrics**: Mean difference, variance ratio, Cohen's d (SC-009).

### Step 3e: Residual Analysis

Identify outlier knot families with residuals ≥ 2 standard deviations.

```bash
python code/analysis/residual_analysis.py
```

*   **Output**: `docs/reproducibility/residual_analysis.md`
*   **Threshold**: ≥ 2 std dev from model fit (SC-011).

### Step 4: Regression Modeling

Fit and compare regression models.

```bash
python code/analysis/regression_models.py
```

*   **Output**: `docs/reproducibility/regression_results.json`
*   **Models**: Linear, Polynomial, Logarithmic (FR-005).
*   **Metrics**: R², AIC/BIC, MAE reported.
*   **Control**: Alternating/non-alternating classification included as control variable.

### Step 5: Reproducibility Check

Verify checksums and logs.

```bash
python code/reproducibility/checksums.py
```

*   **Output**: `docs/reproducibility/checksums.md`
*   **Validation**: SHA-256 hashes recorded for all data files.
*   **Random Seeds**: Documented in `docs/reproducibility/random_seeds.md`.
*   **Tie-Breaking Rules**: Documented in `docs/reproducibility/tie_breaking_rules.md`.

## Troubleshooting

*   **API Unavailable**: Check `docs/reproducibility/logs.md` for retry attempts. Partial results should be cached to disk.
*   **Missing Invariants**: Records flagged in `data/processed/invariants_dataset.csv` under `missing_invariant_flags` column.
*   **Ambiguous Classification**: Records marked as "unclassifiable" or excluded from stratified analysis (FR-010).