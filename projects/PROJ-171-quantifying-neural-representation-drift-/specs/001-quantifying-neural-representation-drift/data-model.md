# Data Model: Quantifying Neural Representation Drift During Skill Learning

## Overview

This document defines the data structures used throughout the pipeline. All data flows from raw ingestion to processed matrices, RDMs, and final statistical results.

## Core Entities

### 1. Raw Data (Ingested)

**Source**: OpenNeuro (Parquet)  
**Format**: Pandas DataFrame  
**Schema**:
- `subject_id`: str (e.g., "sub-01")
- `session_id`: str (e.g., "ses-day1")
- `day_index`: int (0, 1, 2...)
- `trial_id`: str
- `spike_counts`: array[float] (Units × Bins) or list of spike times
- `trial_success`: bool (1/0)
- `kinematics`: array[float] (Optional, for future expansion)

### 2. NeuralPopulationMatrix (Processed)

**Definition**: A 2D array representing averaged spike rates for a specific training day, excluding performance-modulated units.  
**Shape**: (Units × Conditions) or (Units × TimeBins)  
**Attributes**:
- `subject_id`: str
- `day_index`: int
- `unit_ids`: list[str] (Filtered units, ≥80% presence)
- `data`: np.ndarray (float32)
- `excluded_units`: list[str] (Reason: "low_presence" or "performance_modulated")

**Storage**: `data/processed/neural_matrix_{subject_id}_day_{day_index}.parquet`

### 3. RepresentationalDissimilarityMatrix (RDM)

**Definition**: A symmetric matrix representing the distance between neural population activity patterns across different training days.  
**Shape**: (Days × Days)  
**Attributes**:
- `subject_id`: str
- `distance_metric`: str ("pearson", "cosine", "mahalanobis")
- `data`: np.ndarray (float32)
- `labels`: list[int] (Day indices)

**Storage**: `data/processed/rdm_{subject_id}_{metric}.parquet`

### 4. DriftResult (Analysis Output)

**Definition**: The extracted drift rate parameter `b` and model fit statistics.  
**Attributes**:
- `subject_id`: str
- `drift_rate_b`: float (Slope of linear fit)
- `intercept_a`: float
- `r_squared`: float
- `model_type`: str ("linear", "exponential", "constant")
- `convergence_status`: str ("success", "failed_fallback")
- `stability_threshold`: float (e.g., 0.80)
- `distance_metric`: str

**Storage**: `data/results/drift_rates.csv`

### 5. CorrelationResult (Hypothesis Testing Output)

**Definition**: Results of the correlation between drift rate and learning speed.  
**Attributes**:
- `correlation_r`: float
- `p_value_permutation`: float
- `p_value_lmm`: float
- `lmm_fixed_effect_coeff`: float
- `lmm_random_effect_variance`: float
- `sample_size`: int
- `power_warning`: bool (True if N < 15)
- `bonferroni_corrected_p`: float (if applicable)

**Storage**: `data/results/correlation_summary.csv`

## Data Flow

1.  **Ingest**: Raw Parquet → `loader.py` → `DataFrame` (streamed).
2.  **Preprocess**: `DataFrame` → `preprocessor.py` → `NeuralPopulationMatrix` (Parquet).
    -   *Filtering*: Units < 80% presence excluded.
    -   *Imputation*: Missing `trial_success` interpolated.
    -   *Exclusion*: Performance-modulated units identified and removed.
3.  **Drift**: `NeuralPopulationMatrix` → `drift.py` → `RDM` → `DriftResult`.
    -   *Distance*: Pearson, Cosine, Mahalanobis.
    -   *Fit*: Linear (primary), Exponential (secondary).
4.  **Correlate**: `DriftResult` + `BehavioralData` → `correlation.py` → `CorrelationResult`.
    -   *Metrics*: Pearson `r`, Permutation `p`, LMM `p`.
5.  **Validate**: `CorrelationResult` → `validation/` → Sensitivity plots, Split-half checks.

## Constraints & Validation

-   **Unit Stability**: All `NeuralPopulationMatrix` instances must have `unit_ids` that were present in ≥80% of sessions.
-   **Data Integrity**: No in-place modifications. Every transformation produces a new file.
-   **Missing Variables**: If `spike_counts` or `trial_success` are missing in raw data, `loader.py` raises `RuntimeError` (FR-009).
-   **Memory**: All operations on `NeuralPopulationMatrix` must be chunked or streamed to stay within 7 GB RAM.
