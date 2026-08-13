# Data Model: Investigate Brain Network Dynamics and VR Therapy Response

## Overview

This document defines the data structures for the neuroimaging analysis pipeline. It ensures alignment with the spec's requirements for variable fit, collinearity handling, and result reporting.

## Key Entities

### Subject
Represents an individual participant.
- **Attributes**:
  - `subject_id`: Unique identifier (string).
  - `pre_treatment_score`: Float (anxiety scale).
  - `post_treatment_score`: Float (anxiety scale).
  - `anxiety_instrument`: String (e.g., "GAD-7", "HAM-A").
  - `age`: Integer (optional).
  - `medication_status`: String (optional).
  - `motion_fd`: Float (mean Framewise Displacement).
  - `excluded`: Boolean (True if motion > 3mm or data missing).
  - `exclusion_reason`: String (if excluded).

### Network Metric
Computed brain network properties per subject.
- **Attributes**:
  - `subject_id`: String.
  - `metric_name`: Enum ["modularity", "global_efficiency", "local_efficiency"].
  - `value`: Float.
  - `atlas`: String (e.g., "Schaefer-100").
  - `valid`: Boolean (False if NaN or out of bounds).

### Regression Result
Output of the ANCOVA model.
- **Attributes**:
  - `model_id`: String.
  - `outcome`: String ("post_treatment_score").
  - `predictors`: List[String].
  - `coefficients`: Dict[String, Float].
  - `p_values`: Dict[String, Float].
  - `corrected_p_values`: Dict[String, Float].
  - `effect_size_cohen_d`: Float.
  - `confidence_interval_95`: Tuple[Float, Float].
  - `framing`: Enum ["associational", "causal"].
  - `collinearity_handled`: Boolean (True if PCA was used).

### Sensitivity Analysis Log
Records results of cutoff sweeps.
- **Attributes**:
  - `motion_threshold`: Float.
  - `p_value_threshold`: Float.
  - `effect_size`: Float.
  - `ci_lower`: Float.
  - `ci_upper`: Float.
  - `n_subjects`: Integer.

## Data Flow

1.  **Raw Data**: Downloaded NIfTI/Parquet (immutable).
2.  **Preprocessed**: Normalized fMRI, Motion metrics.
3.  **Metrics**: Connectivity matrices -> Network metrics (JSON/CSV).
4.  **Analysis**: Regression outputs -> Sensitivity logs.
5.  **Reports**: Markdown/Plots generated from Analysis outputs.
