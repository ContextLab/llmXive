# Data Model: Investigating the Impact of Visual Complexity on Prefrontal Cortex Activity

## Overview

This document defines the data structures, schemas, and relationships used in the project. It ensures consistency between the ingestion, processing, and analysis stages.

## Key Entities

### 1. Stimulus Complexity Record

Represents a single stimulus frame with computed complexity metrics, confounds, and HRF-convolved scores.

- **Attributes**:
  - `frame_id`: Unique identifier for the frame (int).
  - `timestamp`: Time of stimulus onset (float).
  - `entropy_score`: Shannon entropy of the image (float).
  - `fractal_dimension`: Fractal dimension of the image (float).
  - `luminance`: Mean luminance of the image (float).
  - `contrast`: RMS contrast of the image (float).
  - `hrf_convolved_entropy`: Entropy convolved with HRF (float).
  - `hrf_convolved_fractal`: Fractal dimension convolved with HRF (float).
  - `hrf_convolved_luminance`: Luminance convolved with HRF (float).
  - `hrf_convolved_contrast`: Contrast convolved with HRF (float).

### 2. Subject-Level GLM Result

Represents the statistical output for a single subject after GLM fitting.

- **Attributes**:
  - `subject_id`: Identifier for the subject (str).
  - `metric_name`: Name of the metric (e.g., "entropy", "fractal") (str).
  - `beta_weight`: Estimated effect size from the GLM (float).
  - `t_statistic`: T-statistic from the GLM (float).
  - `p_value`: Raw p-value (float).
  - `vif`: Variance Inflation Factor if calculated (float, optional).
  - `model_type`: "multiple" or "univariate" (str).

### 3. Group-Level Result

Represents the aggregated statistical output across subjects.

- **Attributes**:
  - `metric_name`: Name of the metric (str).
  - `mean_beta`: Mean beta-weight across subjects (float).
  - `std_beta`: Standard deviation of beta-weights (float).
  - `t_statistic`: Group-level t-statistic (float).
  - `p_value`: Raw p-value (float).
  - `fdr_corrected_p`: FDR-corrected p-value (float).
  - `permutation_p`: p-value from permutation test (float).
  - `is_significant`: Boolean indicating significance (bool).

## File Formats

### 1. Input Data

- **BOLD Data**: NIfTI format (`.nii` or `.nii.gz`).
- **Stimulus Logs**: JSON or TSV format.
- **Atlas Mask**: NIfTI format (`.nii` or `.nii.gz`).

### 2. Intermediate Data

- **Complexity Metrics**: CSV format.
- **Subject-Level Beta-Weights**: CSV format.

### 3. Output Data

- **Results**: JSON format.
- **Plots**: PNG format.

## Data Flow

1.  **Ingestion**: Download raw data from OpenNeuro ds000248.
2.  **Processing**:
    - Compute complexity metrics, luminance, and contrast for stimulus images.
    - Convolve metrics with HRF.
    - Extract PFC time-series from BOLD data.
3.  **Analysis**:
    - Fit Subject-Level GLM with AR(1) pre-whitening.
    - Calculate VIF; determine if multiple or univariate models are needed.
    - Perform Group-Level t-test on beta-weights.
    - Run permutation tests.
4.  **Output**: Save results and plots.

## Data Integrity

- **Checksums**: All raw data files are checksummed upon download.
- **Immutability**: Raw data is never modified. All transformations produce new files.
- **Versioning**: All data files are versioned with content hashes.