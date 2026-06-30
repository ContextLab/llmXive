# Data Model: Investigating the Relationship Between Brain Network Dynamics and Creative Problem Solving

## Overview

This document defines the data structures, schemas, and flow for the project. It ensures that all artifacts (raw data, processed metrics, results) are consistent, validated, and traceable.

## Entity Definitions

### Participant
Represents a single subject in the HCP dataset.
- **Attributes**:
  - `subject_id` (str): Unique HCP ID.
  - `age` (int): Age in years.
  - `sex` (str): 'M' or 'F'.
  - `education` (int): Years of education.
  - `creativity_score` (float): CAQ score (or proxy).
  - `fmr_path` (str): Path to raw fMRI file.
  - `motion_flag` (bool): True if excluded due to motion.

### FlexibilityMetric
Output of the dynamic connectivity analysis for a participant.
- **Attributes**:
  - `subject_id` (str): Foreign key to Participant.
  - `flexibility_score` (float): Mean proportion of community changes.
  - `null_flexibility_mean` (float): Mean flexibility from phase-randomized null model.
  - `excess_flexibility` (float): `flexibility_score - null_flexibility_mean`.
  - `static_strength` (float): Mean absolute correlation (full window).
  - `window_length` (int): Window length used (20, 30, or 40).
  - `roi_changes` (dict): Map of ROI -> change count (optional).

### RegressionResult
Output of the statistical modeling.
- **Attributes**:
  - `model_id` (str): Identifier for the model run.
  - `coefficient_flexibility` (float): Beta for excess flexibility.
  - `p_value_flexibility` (float): Two-tailed p-value.
  - `r_squared` (float): Model R².
  - `delta_r_squared` (float): R² change from static-only baseline.
  - `permutation_p_value` (float): Empirical p-value from 10k shuffles.
  - `ci_lower` (float): 95% CI lower bound.
  - `ci_upper` (float): 95% CI upper bound.

## Data Flow

1. **Ingestion**: `data/loader.py` fetches HCP data from OpenNeuro, validates CAQ presence (FR-011).
2. **Preprocessing**: `data/preprocess.py` generates cleaned fMRI time series (NIFTI).
3. **Feature Extraction**: `analysis/connectivity.py` & `analysis/dynamics.py` compute Flexibility and Static Strength (with consensus clustering).
4. **Null Modeling**: `analysis/dynamics.py` generates phase-randomized null flexibility.
5. **Analysis**: `analysis/statistics.py` tests association between *Excess Flexibility* and CAQ.
6. **Output**: `viz/plots.py` generates PNGs; `data/interim/results.csv` stores final metrics.

## File Schema

| File Path | Format | Description |
| :--- | :--- | :--- |
| `data/raw/manifest.json` | JSON | HCP participant list with metadata. |
| `data/checksums.json` | JSON | **Registry of SHA-256 checksums for all raw data files.** |
| `data/processed/fmri_clean/{id}.nii.gz` | NIFTI | Preprocessed fMRI data. |
| `data/interim/flexibility_metrics.csv` | CSV | Per-subject flexibility and static strength. |
| `data/interim/sensitivity_summary.csv` | CSV | Results for window lengths 20s, 30s, 40s. |
| `data/interim/permutation_results.csv` | CSV | Permutation p-values. |
| `data/interim/data_exclusion_log.txt` | TXT | Log of excluded subjects and reasons. |
| `docs/outputs/flexibility_vs_creativity.png` | PNG | Scatter plot. |
| `docs/outputs/model_residuals.png` | PNG | Residual diagnostics. |
| `docs/outputs/model_qq.png` | PNG | QQ plot. |

## Constraints & Validation

- **CAQ Presence**: If `creativity_score` is null for all subjects, the system exits with `DATA_MISSING_CREATIVITY`.
- **Motion**: Subjects with `motion_flag=True` are excluded from analysis.
- **Data Integrity**: All derived files must have a checksum recorded in `data/checksums.json`.
- **Versioning**: `code/utils/versioning.py` updates `state/projects/PROJ-518-investigating-the-relationship-between-b.yaml` with artifact hashes.