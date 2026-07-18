# Data Model: Can Publicly Available Data Reveal Subtle Violations of Time-Reversal Symmetry in Beta Decay?

## Overview

This document defines the data structures used to represent the published D-coefficients, the meta-analytic results, and the intermediate states of the analysis pipeline. The model is designed to be schema-validated via YAML contracts to ensure data hygiene and reproducibility.

**Note on Spec Inconsistency**: The spec defines `RawObservable` and `FusionResult` as active entities. However, the implementation plan pivots to `DMeasurement` and `MetaAnalysisResult` because the "cross-modal fusion" method is physically invalid. The `RawObservable` and `FusionResult` schemas are retained here as **Legacy/Deprecated** for compatibility but are not used in the primary analysis. The spec requires an update to deprecate these entities.

## Key Entities

### 1. Nucleus
Represents a specific atomic nucleus being analyzed.

- **Attributes**:
  - `name`: String (e.g., "6He", "19Ne")
  - `mass_number`: Integer
  - `atomic_number`: Integer
  - `experimental_conditions`: String (summary of conditions)

### 2. DMeasurement
Represents a single published measurement of the T-violation D-coefficient.

- **Attributes**:
  - `nucleus`: String (e.g., "6He")
  - `value`: Float (the reported D-coefficient value)
  - `uncertainty`: Float (the reported standard error)
  - `source_experiment`: String (citation/experiment ID)
  - `reference_id`: String (DOI or unique identifier)
  - `retrieval_status`: Enum ["success", "failed", "range_inferred", "static_fallback"]

### 3. MetaAnalysisResult
Represents the statistical output of the meta-analysis for a specific nucleus.

- **Attributes**:
  - `nucleus`: String
  - `weighted_average`: Float (inverse-variance weighted mean of D-coefficients)
  - `combined_uncertainty`: Float (uncertainty of the weighted mean)
  - `p_value_heterogeneity`: Float (from Cochran's Q test)
  - `d_upper_bound_95`: Float (95% CI upper bound)
  - `n_measurements`: Integer (number of measurements included)
  - `is_consistent`: Boolean (True if p_value_heterogeneity > 0.05)
  - `sensitivity_limit`: Float (SE of the weighted mean)
  - `model_type`: Enum ["fixed_effect", "random_effects"]

### 4. FusionResult (Legacy)
Represents the statistical output of the data fusion analysis (legacy/placeholder for compatibility).

- **Attributes**:
  - `nucleus_id`: String
  - `d_coefficient_estimate`: Float (derived D-coefficient estimate)
  - `p_value_null`: Float (from permutation test)
  - `d_upper_bound_95`: Float (95% CI upper bound)
  - `sensitivity_limit`: Float (SE of weighted mean)
  - `pdg_comparison_status`: Enum ["better", "worse", "comparable", "no_data"]
  - `fusion_status`: Enum ["success", "invalid_for_fusion", "insufficient_data"]
  - `shuffles_count`: Integer (number of permutations performed)

### 5. RawObservable (Legacy)
Represents a raw/semi-raw measurement from ENSDF (legacy/placeholder for compatibility).

- **Attributes**:
  - `value`: Float
  - `uncertainty`: Float
  - `modality_type`: Enum ["momentum_spectrum", "polarization_asymmetry"]
  - `source_experiment`: String
  - `reference_id`: String
  - `data_granularity`: Enum ["event_level", "binned_granular", "binned_aggregate"]
  - `covariance_available`: Boolean
  - `nucleus_name`: String

## Data Flow

1. **Input**: Raw text/XML from NNDC ENSDF.
2. **Parsed**: `DMeasurement` objects (stored in `data/processed/d_measurements.json`).
3. **Validated**: Filtered for `retrieval_status` == "success".
4. **Fused**: `MetaAnalysisResult` objects generated (stored in `data/processed/meta_analysis_results.json`).
5. **Output**: Final report generated from `MetaAnalysisResult` objects.

## Validation Rules

- **Completeness**: Every `MetaAnalysisResult` must have a non-null `p_value_heterogeneity` and `d_upper_bound_95`.
- **Range**: `p_value_heterogeneity` must be in $[0, 1]$.
- **Consistency**: `d_upper_bound_95` must be $\ge 0$ (absolute value bound).
- **Model Consistency**: If `is_consistent` is False, `model_type` must be "random_effects".