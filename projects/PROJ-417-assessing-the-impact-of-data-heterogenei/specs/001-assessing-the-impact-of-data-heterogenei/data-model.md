# Data Model: Assessing the Impact of Data Heterogeneity on Meta-Analysis Results

## 1. Overview
This document defines the data structures for the simulation engine, ensuring strict typing and validation via YAML schemas.

## 2. Entities

### 2.1 SimulatedDataset
Represents a single synthetic meta-analysis instance.
*   **Fields**:
    *   `replicate_id`: Unique integer identifier.
    *   `tau_squared`: The injected between-study variance (ground truth).
    *   `true_effect`: The fixed true effect size used for generation.
    *   `study_effects`: List of floats (generated effect sizes).
    *   `study_se`: List of floats (standard errors).
    *   `study_sizes`: List of integers (sample sizes, used for SE derivation).
    *   `k`: Number of studies.
    *   `sweep_type`: Enum (`primary`, `sensitivity`) to distinguish SC-004 sweep.

### 2.2 EstimationResult
Represents the output of applying an estimator to a `SimulatedDataset`.
*   **Fields**:
    *   `dataset_id`: Reference to the source dataset.
    *   `estimator_type`: Enum (`FixedEffects`, `DerSimonianLaird`, `REML`).
    *   `pooled_effect`: Calculated pooled effect size.
    *   `ci_lower`: Lower bound of 95% CI.
    *   `ci_upper`: Upper bound of 95% CI.
    *   `tau_squared_est`: Estimated between-study variance.
    *   `i_squared`: Heterogeneity statistic $I^2$.
    *   `q_statistic`: Cochran's Q.
    *   `coverage_flag`: Boolean (True if `true_effect` $\in$ [CI_lower, CI_upper]).
    *   `convergence_warning`: Boolean (True if REML failed to converge).

### 2.3 AggregatedMetric
Summary statistics for a specific $\tau^2$ level and estimator.
*   **Fields**:
    *   `tau_squared`: The heterogeneity level.
    *   `estimator_type`: The estimator used.
    *   `sweep_type`: Enum (`primary`, `sensitivity`).
    *   `mean_bias`: Average of (pooled_effect - true_effect).
    *   `coverage_rate`: Proportion of `coverage_flag` = True.
    *   `coverage_deviation`: `coverage_rate` - 0.95.
    *   `coverage_ci_lower`: Lower bound of Wilson Score Interval for coverage.
    *   `coverage_ci_upper`: Upper bound of Wilson Score Interval for coverage.
    *   `binomial_p_value`: Result of exact binomial test against nominal coverage.
    *   `bias_test_p_value`: Result of Kruskal-Wallis or Dunn's test.
    *   `report_framing`: String (e.g., "associational") for SC-005 compliance.

## 3. File Formats
*   **Raw/Processed Data**: CSV (for study-level data).
*   **Simulation Output**: JSON (for `SimulatedDataset` and `EstimationResult` records) to preserve float precision and structure.
*   **Aggregated Results**: CSV (for `AggregatedMetric` tables).

## 4. Validation Strategy
All data written to `data/results/` must pass validation against the schemas defined in `contracts/`.
*   **Schema Enforcement**: Python `pydantic` or `jsonschema` will be used to validate JSON outputs before aggregation.
*   **Checksums**: SHA-256 checksums generated for all files in `data/results/`.