# Data Model: The Impact of Simulated Social Exclusion on Neural Responses to Reward

## Overview

This document defines the data structures used throughout the pipeline, from raw download to final statistical output. All data is stored in `data/` with checksums.

## Entity Definitions

### Participant
Represents a single subject in the study.
-   `participant_id`: string (e.g., "sub-01")
-   `group`: string ("excluded" | "included")
-   `dataset_id`: string (e.g., "ds000246" or "ds004738" for merged datasets)
-   `condition_label`: string (e.g., "Cyberball_Excluded")
-   `motion_max`: float (max translation in mm)
-   `excluded_from_analysis`: boolean (if motion > 3mm or missing data)

### ROI (Region of Interest)
Represents a brain region mask.
-   `roi_name`: string ("ventral_striatum" | "orbitofrontal_cortex")
-   `atlas_source`: string ("AAL" | "Harvard-Oxford")
-   `mni_coords`: object {x: float, y: float, z: float}
-   `mask_path`: string (relative path to NIfTI mask)

### Beta Estimate
First-level GLM result for a participant in an ROI.
-   `participant_id`: string
-   `dataset_id`: string (for merged datasets)
-   `roi_name`: string
-   `event_type`: string ("anticipation" | "receipt")
-   `beta_value`: float
-   `t_stat`: float (optional, from GLM)

### Group Analysis Result
Second-level statistical output.
-   `roi_name`: string
-   `event_type`: string
-   `group_excluded_mean`: float
-   `group_included_mean`: float
-   `t_statistic`: float
-   `p_value_uncorrected`: float
-   `p_value_corrected`: float (Bonferroni)
-   `cohens_d`: float
-   `n_excluded`: int
-   `n_included`: int
-   `dataset_id_effect`: float (if merged, random effect estimate)

### Sensitivity Result
Output of threshold sweeps.
-   `smoothing_mm`: int
-   `roi_mask_prob`: float (if applicable)
-   `beta_excluded`: float
-   `beta_included`: float
-   `significant`: boolean
-   `consistent_with_primary`: boolean

### Preprocessing Metrics
Output of preprocessing phase.
-   `total_participants`: int
-   `completed_participants`: int
-   `failed_participants`: int
-   `completion_rate`: float (target ≥0.90)
-   `provenance_files_generated`: int

### Power Limitations Report
Output of power analysis phase.
-   `n_per_group`: int
-   `power_estimate`: float
-   `is_exploratory`: boolean
-   `recommendation`: string (e.g., "Future studies with ≥30 participants per group")

## File Formats

### `data/raw-fmri/`
-   **Format**: BIDS (NIfTI + JSON + TSV)
-   **Checksum**: SHA-256 recorded in `state/`.

### `data/processed-fmri/`
-   **Format**: NIfTI (preprocessed)
-   **Naming**: `sub-{id}_space-MNI152_res-2mm_desc-preproc_bold.nii.gz`
-   **Sidecars**: `sub-{id}_space-MNI152_res-2mm_desc-preproc_bold.yaml` (Provenance)

### `data/results/`
-   **Format**: CSV / JSON
-   **Files**:
    -   `beta_estimates.csv`: Aggregated first-level betas.
    -   `group_analysis.json`: Second-level stats.
    -   `sensitivity_analysis.csv`: Threshold sweep results.
    -   `preprocessing_metrics.json`: Completion rate and provenance count.
    -   `power_limitations_report.json`: Power analysis and recommendations.

## Data Flow

1.  **Download**: Raw BIDS data → `data/raw-fmri/`
2.  **Preprocess**: Raw → `data/processed-fmri/` + Provenance Sidecars
3.  **Extract**: Preprocessed + ROI Masks → `data/results/beta_estimates.csv`
4.  **Analyze**: Beta Estimates → `data/results/group_analysis.json`
5.  **Sensitivity**: Variations of Preprocess/Extract → `data/results/sensitivity_analysis.csv`
6.  **Report**: Generate `preprocessing_metrics.json` and `power_limitations_report.json`