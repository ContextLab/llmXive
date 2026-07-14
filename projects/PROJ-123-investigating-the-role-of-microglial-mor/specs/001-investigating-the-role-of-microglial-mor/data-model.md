# Data Model: Investigating the Role of Microglial Morphology in Age-Related Cognitive Decline

## 1. Overview

This document defines the data structures used throughout the pipeline, from raw image ingestion to final regression output. The model emphasizes strict typing for morphological metrics, cognitive scores, and metadata to ensure reproducibility and contract compliance.

## 2. Entity Definitions

### 2.1 MicroglialImage
Represents a single microscopy image and its metadata.
*   `image_id`: Unique identifier (string).
*   `file_path`: Path to the raw image file (string).
*   `brain_region`: Enum (`"Hippocampus"`, `"Prefrontal Cortex"`).
*   `pathology_status`: Enum (`"Normal"`, `"Early AD"`).
*   `resolution_um_per_pixel`: Float (calibration factor).

### 2.2 MorphologicalMetrics
Derived quantitative features for a single image.
*   `image_id`: Foreign key to `MicroglialImage`.
*   `branch_point_count`: Integer (count of branch nodes).
*   `total_process_length_um`: Float (total skeleton length).
*   `soma_area_um2`: Float (soma area).
*   `sholl_intersections`: Dictionary `{radius_um: count}`.
*   `extraction_error`: Float (deviation from manual ground truth, if available).

### 2.3 CognitiveScore
Behavioral metric linked to a subject.
*   `subject_id`: Unique identifier.
*   `raw_score`: Float (e.g., MWM latency in seconds).
*   `cohort_id`: String (study cohort).
*   `z_score`: Float (normalized score: $(x - \mu)/\sigma$).
*   `cohort_mean`: Float.
*   `cohort_std`: Float.

### 2.4 PathologyClassification
Logic for classifying pathology status.
*   `subject_id`: Foreign key.
*   `amyloid_beta_load`: Float (raw load).
*   `threshold_used`: Float (e.g., 75th percentile).
*   `classification_method`: String (`"Label"` or `"DynamicThreshold"`).
*   `pathology_status`: Enum (`"Normal"`, `"Early AD"`).
*   `training_set_id`: String (ID of the training set used for threshold calculation, to prevent leakage).

### 2.5 RegressionResult
Output of the statistical model.
*   `model_id`: Unique identifier.
*   `coefficients`: Dictionary `{feature: value}`.
*   `p_values`: Dictionary `{feature: value}`.
*   `interaction_p_value`: Float (specific to `Pathology * Region`).
*   `r_squared`: Float.
*   `vif_scores`: Dictionary `{feature: value}`.
*   `causality_warning`: Boolean (always `true` unless randomization flagged).
*   `sholl_sensitivity_results`: List of `{step_um: interaction_p_value}`.
*   `pc_loadings`: Dictionary `{pc_component: {original_feature: loading}}` (for interpretability).
*   `observed_power`: Float (calculated for the interaction term).