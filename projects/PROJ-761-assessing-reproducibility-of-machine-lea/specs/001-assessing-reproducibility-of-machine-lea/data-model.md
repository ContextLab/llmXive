# Data Model: Assessing Reproducibility of Machine‑Learned Reaction Yield Models

## 1. Overview
This document defines the data structures used throughout the pipeline, ensuring traceability from the input manifest to the final statistical summary. All data is stored in JSON/YAML formats to facilitate validation against the contracts defined in `contracts/`.

## 2. Entity Definitions

### 2.1 PaperManifest
Represents a single target publication to be audited.
-   **Source**: `data/manifest.yaml`
-   **Fields**:
    -   `doi`: string (Unique identifier)
    -   `repo_url`: string (URL to code repository)
    -   `dataset_name`: string (e.g., "USPTO-Extract v1.0")
    -   `dataset_version`: string (e.g., "v1.0")
    -   `data_url`: string (Direct URL to the specific CSV/Parquet file or script to generate it. **Required** if the dataset is not fully available in a verified source).
    -   `reported_metrics`: object
        -   `mae`: float
        -   `r2`: float
        -   `spearman_rho`: float
    -   `hyperparameters`: object (Key-value pairs of model settings)
    -   `seed`: integer (Optional; default 42 if missing)
    -   `covariates_required`: list of strings (e.g., ["temperature", "solvent"])

### 2.2 ReproResult
The output of the re-implementation phase for a single paper.
-   **Source**: `artifacts/reports/repro_results.json`
-   **Fields**:
    -   `doi`: string
    -   `reproduced_metrics`: object
        -   `mae`: float
        -   `r2`: float
        -   `spearman_rho`: float
    -   `deviations`: object
        -   `mae`: float (|reproduced - reported|)
        -   `r2`: float
        -   `spearman_rho`: float
    -   `deviation_index`: float (S ∈ [0,1], normalized absolute deviation as per FR-009. **Note**: This is a descriptive ranking metric, not a statistical test result).
    -   `metric_std`: object (Standard deviation from seed sweep, used for meta-analysis weights)
        -   `mae`: float
        -   `r2`: float
        -   `spearman_rho`: float
    -   `flags`: list of strings (e.g., "missing_seed", "covariate_gap", "model_substituted", "data_unavailable")
    -   `environment_hash`: string (Docker image hash)
    -   `seed_used`: integer

### 2.3 StatSummary
Aggregated statistical analysis results.
-   **Source**: `artifacts/reports/stat_summary.json`
-   **Fields**:
    -   `equivalence_test`: object (TOST results)
        -   `mae`: { `t_statistic_lower`: float, `t_statistic_upper`: float, `p_value`: float, `p_corrected`: float, `tolerance_delta`: float }
        -   `r2`: { ... }
        -   `spearman_rho`: { ... }
    -   `meta_analysis`: object (Fixed-Effects Meta-Analysis results)
        -   `pooled_effect`: float (Mean deviation)
        -   `confidence_interval`: list [lower, upper]
        -   `heterogeneity_i2`: float
        -   `weights`: object (List of weights used, derived from `metric_std`)
    -   `bland_altman`: object (Summary stats for plotting)
        -   `mae`: { `mean_diff`: float, `std_diff`: float, `limits_of_agreement`: list }
        -   ...
    -   `sensitivity_analysis`: object
        -   `max_std_mae`: float
        -   `max_std_r2`: float
        -   `max_std_spearman_rho`: float

## 3. Data Flow
1.  **Ingest**: `PaperManifest` is read and validated (including `data_url`).
2.  **Process**: For each manifest entry, `ReproResult` is generated (including `metric_std` from seed sweep).
3.  **Aggregate**: All `ReproResult` objects are collected to compute `StatSummary` (using `metric_std` for inverse-variance weighting).
4.  **Output**: `StatSummary` and individual `ReproResult` files are written to `artifacts/reports/`.

## 4. Constraints
-   All floating point metrics must be rounded to 4 decimal places for reporting.
-   `deviation_index` must be clamped to [0, 1].
-   If a metric cannot be computed (e.g., NaN), the result must be flagged, and the score set to 0.
-   `metric_std` is required for all papers included in the meta-analysis.