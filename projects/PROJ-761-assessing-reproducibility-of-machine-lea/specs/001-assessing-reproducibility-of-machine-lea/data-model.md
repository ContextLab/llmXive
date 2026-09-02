# Data Model: Assessing Reproducibility of Machine‑Learned Reaction Yield Models

## Overview

This document defines the data structures used for input, processing, and output. All data interchange is governed by YAML schemas located in `contracts/` (project root). The system enforces strict versioning of datasets and reproducibility of results.

## Entities

### 1. PaperManifest
Represents a single target publication to be audited.

- **Fields**:
  - `doi`: string (ISO format)
  - `repo_url`: string (GitHub URL)
  - `dataset_name`: string (e.g., "USPTO-Extract v1.0")
  - `dataset_version`: string (Required. e.g., "v1.0". Satisfies Constitution Principle VI).
  - `dataset_url`: string (Optional; verified URL if different from standard)
  - `reported_metrics`: object
    - `mae`: float
    - `r2`: float
    - `spearman_rho`: float
  - `hyperparameters`: object (key-value pairs)
  - `seed`: integer (optional; default = 42 if missing. Defined as fallback in spec).
  - `replicates`: integer (Optional. Number of experimental replicates reported).
  - `conditions`: string (Optional. Text description of temperature, solvent, etc.).
  - `covariates_required`: list of strings (e.g., ["temperature", "solvent"])

### 2. ReproResult
The primary output for a single paper's audit.

- **Fields**:
  - `doi`: string
  - `reproduced_metrics`: object
    - `mae`: float
    - `r2`: float
    - `spearman_rho`: float
  - `reported_metrics`: object (copy of input)
  - `absolute_deviations`: object
    - `mae`: float
    - `r2`: float
    - `spearman_rho`: float
  - `reproducibility_score`: float (0.0 to 1.0)
  - `seed_used`: integer
  - `flags`: list of strings (e.g., "missing_seed", "covariate_missing", "model_substituted", "sweep_incomplete")
  - `sensitivity`: object
    - `max_metric_std`: float (from seed sweep. Required for FR-010).
  - `environment`: object (Python version, Docker hash, library versions)
  - `model_substituted`: boolean (True if model was replaced due to GPU/param limits).
  - `covariate_missing`: boolean (True if required covariates were not found).

### 3. StatSummary
Aggregate statistical results across all papers.

- **Fields**:
  - `paired_ttest`: list of objects (one per metric)
    - `metric`: string
    - `t_statistic`: float
    - `p_value_raw`: float
    - `p_value_corrected`: float
    - `significant`: boolean
  - `tost_equivalence`: list of objects (one per metric)
  - `bland_altman`: list of objects (one per metric)
  - `mixed_effects`: object
    - `fixed_effects`: dict (coefficients for ModelSubstitution, CovariateMissing)
    - `variance_components`: dict (random intercept variance, residual variance)
    - `r2_marginal`: float
    - `r2_conditional`: float
  - `heterogeneity`: object
    - `i_squared`: float
    - `pooled_effect_size`: float
  - `failure_log`: list of strings (qualitative issues)

## Data Flow

1.  **Ingestion**: `code/ingest.py` reads `manifest.csv` and validates against `PaperManifest.schema.yaml`.
2.  **Processing**: `code/model_runner.py` generates `ReproResult` for each paper.
3.  **Aggregation**: `code/main.py` collects all `ReproResult` objects and triggers `code/stats.py`.
4.  **Analysis**: `code/stats.py` computes meta-analysis and writes `StatSummary`.
5.  **Reporting**: `code/guidelines.py` consumes `StatSummary` and failure logs to generate the checklist.

## Schema Locations

- `contracts/PaperManifest.schema.yaml`
- `contracts/ReproResult.schema.yaml`
- `contracts/StatSummary.schema.yaml`