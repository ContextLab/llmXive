# Data Model: Investigating the Influence of Network Topology on Spontaneous Brain Activity Patterns

## Overview

This document defines the data structures, schemas, and file formats used throughout the project. All data is stored in CSV, JSON, or Parquet formats to ensure interoperability and reproducibility.

## Key Entities

### 1. Subject
Represents a single participant from the HCP dataset.
- **Attributes**: `subject_id` (str), `data_available` (bool), `exclusion_reason` (str or null).

### 2. StructuralMetric
Derived graph properties for a specific subject.
- **Attributes**: `subject_id`, `global_efficiency`, `clustering_coefficient`, `modularity`, `threshold_density`.

### 3. DynamicMetric
Derived state properties for a specific subject.
- **Attributes**: `subject_id`, `mean_dwell_time_state1`, `mean_dwell_time_state2`, ..., `num_visited_states`, `window_length`.

### 4. CorrelationResult
Statistical association between a structural and dynamic metric.
- **Attributes**: `structural_metric_name`, `dynamic_metric_name`, `correlation_coefficient`, `p_value`, `fdr_corrected_p`, `significance_flag`.

### 5. SensitivityComparison
Comparison of correlation results under different parameters.
- **Attributes**: `structural_metric_name`, `dynamic_metric_name`, `baseline_r`, `sensitivity_r`, `absolute_difference`, `parameter_type` (window/density), `is_robust` (bool).

### 6. DataCompletenessReport
Aggregated data completeness metrics.
- **Attributes**: `subject_id`, `status` (included/excluded), `reason` (str).

## File Formats

### Raw Data
- **Format**: Parquet/CSV (from OpenNeuro).
- **Location**: `data/raw/`.
- **Validation**: Checksummed; schema validated against `contracts/dataset.schema.yaml`.

### Derived Metrics
- **Format**: CSV.
- **Location**: `data/derived/`.
- **Files**:
  - `structural_metrics.csv`: One row per subject.
  - `dynamic_metrics.csv`: One row per subject.
  - `correlation_results.csv`: One row per metric pair.
  - `sensitivity_window.csv`: One row per metric pair for window sensitivity.
  - `sensitivity_density.csv`: One row per metric pair for density sensitivity.
  - `sensitivity_comparison.csv`: Aggregated sensitivity results.
  - `data_completeness_report.csv`: Aggregated exclusion logs.

### Reports
- **Format**: Markdown.
- **Location**: `artifacts/`.
- **Files**: `final_report.md`, `README.md`.

## Data Flow Diagram

```mermaid
graph TD
    A[Raw Data (OpenNeuro)] -->|Download & Verify| B(data/raw)
    B -->|Structural Pipeline| C[Structural Metrics CSV]
    B -->|Functional Pipeline (LOSO)| D[Dynamic Metrics CSV]
    C -->|Join | E[Correlation Analysis]
    D -->|Join | E
    E -->|Primary Output| F[Correlation Results CSV]
    E -->|Re-run (Window)| G[Sensitivity Window CSV]
    E -->|Re-run (Density)| H[Sensitivity Density CSV]
    G & H -->|Aggregate| I[Sensitivity Comparison CSV]
    C & D & B -->|Parse Logs| J[Data Completeness Report CSV]
    F & I & J -->|Report Gen| K[Final Report]
```

## Constraints

- **Data Independence**: Structural and dynamic metrics are computed in separate pipelines. LOSO ensures functional states are independent of the subject's own data.
- **Missing Data**: Subjects with missing dMRI or fMRI are excluded and logged.
- **Sparsity**: Subjects with structural sparsity >90% are excluded.
- **Convergence**: Subjects with k-means non-convergence are excluded.
- **Completeness**: Exclusion logs are parsed to generate `data_completeness_report.csv` (Phase 0.5).