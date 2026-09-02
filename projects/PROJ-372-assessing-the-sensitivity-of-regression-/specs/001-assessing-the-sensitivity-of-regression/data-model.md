# Data Model: Assessing the Sensitivity of Regression Coefficients to Dataset Subset Selection

## 1. Overview
This document defines the data structures used for ingestion, profiling, resampling, and hierarchical analysis. All artifacts are serialized to JSON or Parquet.

## 2. Core Entities

### 2.1 DatasetProfile
Represents the violation profile of a full dataset.
- **Source**: `src/ingestion/profiler.py`
- **Format**: JSON (`artifacts/profiles/{dataset_id}_profile.json`)
- **Fields**:
  - `dataset_id`: Unique identifier (e.g., "uci_bike_sharing").
  - `source_url`: Verified URL of the dataset.
  - `n_rows`: Total rows after cleaning.
  - `n_cols`: Total numerical columns used.
  - `condition_number`: Float (Condition Number of $X$).
  - `bp_statistic`: Float (Breusch-Pagan statistic).
  - `bp_p_value`: Float.
  - `max_cooks_distance`: Float.
  - `severity_heteroscedasticity`: Enum ["Low", "Medium", "High"].
  - `severity_outliers`: Enum ["Low", "Medium", "High"].
  - `severity_multicollinearity`: Enum ["Low", "Medium", "High"].

### 2.2 StabilityResult (Individual Subset)
Represents the result of a single OLS fit on a specific subset. **This is the Level 1 unit for HLM.**
- **Source**: `src/resampling/stability.py`
- **Format**: JSON (`artifacts/stability/stability_subset_{dataset_id}_{tier}_{iteration}.json`)
- **Fields**:
  - `dataset_id`: String.
  - `tier_percentage`: Int (10, 25, 50, 75, 90).
  - `iteration`: Int (0-199).
  - `subset_size`: Int.
  - `coefficients`: Dict<string, Float> (e.g., `{"temp": 0.45, "humidity": -0.12}`).
  - `r_squared`: Float.
  - `runtime_ms`: Int.

### 2.3 AggregatedStability
Aggregated statistics per tier (for descriptive reporting and convergence check).
- **Source**: `src/resampling/stability.py`
- **Format**: JSON (`artifacts/stability/coefficient_sd.json`)
- **Fields**:
  - `dataset_id`: String.
  - `tier_percentage`: Int.
  - `coefficients_sd`: Dict<string, Float> (Empirical SD of each coefficient across 200 iterations).
  - `coefficients_se_sd`: Dict<string, Float> (Standard Error of the SD).
  - `convergence_met`: Boolean (True if all `se_sd < 0.05 * sd`).

### 2.4 HLMResults
Results of the Hierarchical Linear Model.
- **Source**: `src/analysis/hlm_analysis.py`
- **Format**: JSON (`artifacts/hlm_results/hlm_results.json`)
- **Fields**:
  - `model_type`: String ("HierarchicalLinearModel").
  - `fixed_effects`: Dict<string, Float> (e.g., `{"intercept": 0.5, "size": -0.02, "severity_high": 0.1, "size_x_severity_high": 0.05`).
  - `fixed_effects_p_values`: Dict<string, Float>.
  - `random_effects_variance`: Float (Variance of random intercepts).
  - `interaction_significant`: Boolean.
  - `methodology_note`: String (Explanation of the HLM approach and how it resolves the confound).

## 3. Data Flow
1.  **Ingestion**: `source_url` -> `DatasetProfile`.
2.  **Resampling**: `DatasetProfile` + `source_url` -> 1000 `StabilityResult` (individual coefficients) -> `AggregatedStability` (for convergence check).
3.  **HLM Analysis**: All `StabilityResult` (Level 1) + `DatasetProfile` (Level 2) -> `HLMResults`.

## 4. Constraints
- **Immutability**: Raw data in `data/raw` is never modified.
- **Checksums**: All files in `data/raw` and `artifacts/` must have corresponding SHA-256 hashes in `state/...yaml`.
- **Schema Validation**: All JSON artifacts must match the schemas defined in `contracts/`.