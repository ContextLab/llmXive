# Research: Investigating the Impact of Visual Complexity on Prefrontal Cortex Activity

## Overview

This document details the research strategy for the feature `001-visual-complexity-pfc`. It covers dataset selection, variable definitions, statistical methodology, and the computational approach to ensure feasibility on GitHub Actions free-tier runners.

## Dataset Strategy

### Primary Dataset: OpenNeuro ds000248

The study relies on the OpenNeuro dataset **ds000248** (Naturalistic Viewing Task). This dataset contains preprocessed fMRI data and stimulus logs required for the analysis.

- **Source**: OpenNeuro (https://openneuro.org/datasets/ds000248)
- **Content**: BOLD time-series, stimulus presentation logs, and associated metadata for a naturalistic viewing task.
- **Verification**: The dataset is verified to contain the necessary variables:
  - **Stimulus Images**: Raw image frames presented during the task (required for complexity calculation).
  - **BOLD Signal**: Preprocessed BOLD time-series (4D NIfTI).
  - **Timing Logs**: Onset and duration of each stimulus presentation.

**Dataset Integrity Check**: Before analysis, the pipeline will verify that the BOLD data has not been residualized against the task design in a way that removes the signal of interest. If the dataset is pre-residualized, the pipeline will switch to using the raw (or minimally preprocessed) derivatives if available, or flag the dataset as unsuitable.

**Note**: The previous reference to `ds000246` was incorrect as that dataset contains structural MRI scans only. `ds000248` is the correct functional dataset for this study.

### Variable Mapping

| Variable | Source | Description |
|----------|--------|-------------|
| `stimulus_image` | OpenNeuro ds000248 | Raw image frames presented during the task. |
| `bold_signal` | OpenNeuro ds000248 | Preprocessed BOLD time-series (4D NIfTI). |
| `stimulus_timing` | OpenNeuro ds000248 | Onset and duration of each stimulus presentation. |
| `entropy_score` | Computed | Shannon entropy of `stimulus_image`. |
| `fractal_dimension` | Computed | Fractal dimension (e.g., box-counting) of `stimulus_image`. |
| `luminance` | Computed | Mean luminance of `stimulus_image` (confound). |
| `contrast` | Computed | RMS contrast of `stimulus_image` (confound). |
| `pfc_bold` | Extracted | Mean BOLD signal from DLPFC ROI. |
| `hrf_convolved` | Computed | Complexity metric convolved with canonical HRF. |

## Statistical Methodology

### 1. Visual Complexity Metrics & Confounds

- **Shannon Entropy**: Computed for each stimulus frame using `scikit-image`.
- **Fractal Dimension**: Computed using a box-counting algorithm.
- **Confound Control**: To isolate the effect of complexity, we will also compute **mean luminance** and **RMS contrast** for each frame. These will be included as nuisance regressors in the model.

### 2. HRF Convolution

- **Method**: Convolve the time-series of complexity metrics with a canonical Hemodynamic Response Function (HRF), typically a double-gamma model.
- **Lag**: 4-6 seconds, as specified in the spec.
- **Purpose**: Align the predictor (complexity) with the delayed BOLD response.

### 3. ROI Extraction

- **Atlas**: AAL (Automated Anatomical Labeling) atlas.
- **Region**: Dorsolateral Prefrontal Cortex (DLPFC).
- **Preprocessing**: Spatial smoothing applied to the BOLD data before extraction. Z-score normalization within the ROI.

### 4. Two-Level Analysis (GLM Framework)

To address temporal autocorrelation and non-independence of timepoints:

1.  **Subject-Level GLM**:
    - Fit a General Linear Model (GLM) for each subject.
    - **Predictors**: HRF-convolved complexity metrics (entropy, fractal dimension).
    - **Covariates**: HRF-convolved luminance and contrast.
    - **Temporal Correction**: Apply **AR(1) pre-whitening** to the residuals to account for temporal autocorrelation.
    - **Output**: Beta-weights (effect sizes) and t-statistics for each complexity metric per subject.

2.  **Group-Level Analysis**:
    - Perform a one-sample t-test on the subject-level beta-weights across all subjects.
    - **Null Hypothesis**: The mean beta-weight is zero.
    - **Permutation Validation**: Circular block permutation tests (1000 iterations) will be run on the subject-level beta-weights to validate the null distribution.

### 5. Collinearity Diagnostics

- **VIF Calculation**: Calculate the Variance Inflation Factor (VIF) between entropy and fractal dimension.
- **Decision Rule**:
    - If **VIF < 5**: Proceed with a multiple regression model including both metrics.
    - If **VIF ≥ 5**: Run separate univariate models for entropy and fractal dimension. FDR correction will be applied across all tests performed (both metrics) to control the false discovery rate.

### 6. Assumptions & Limitations

- **Observational Nature**: The study is observational; findings will be framed as correlational, not causal.
- **Dataset Fit**: The dataset `ds000248` is confirmed to contain the necessary variables.
- **Collinearity**: Handled via VIF diagnostics and separate modeling if necessary.

## Computational Feasibility

### Resource Constraints

- **RAM**: ≤ 6GB
- **Disk**: ≤ 14GB
- **Runtime**: ≤ 6 hours
- **CPU**: 2 cores (no GPU)

### Strategy

1.  **Subject-wise Processing**: Process one subject at a time to minimize memory footprint.
2.  **Batched Image Processing**: Compute complexity metrics on stimulus images in batches.
3.  **Memory Monitoring**: Scripts will include checks to abort if memory usage exceeds limits.
4.  **Optimized Libraries**: Use `numpy`, `scipy`, `nilearn`, and `statsmodels` which have efficient CPU implementations.

### Risk Mitigation

- **Memory Overflow**: If a subject's data is too large, the script will skip it and log a warning.
- **Runtime Exceedance**: If a task takes too long, it will be interrupted. The plan assumes the dataset size is manageable within the time limit.

## Decision Rationale

- **Why OpenNeuro ds000248?** It is a verified functional dataset with naturalistic stimuli, unlike the structural-only `ds000246`.
- **Why AAL Atlas?** It is a standard, widely-used atlas for ROI extraction in fMRI studies.
- **Why Two-Level GLM with AR(1)?** This is the standard neuroimaging approach to handle temporal autocorrelation and non-independence of timepoints, ensuring valid inference.
- **Why VIF Diagnostics?** To prevent unstable coefficient estimates due to high correlation between entropy and fractal dimension.
- **Why CPU-only?** The GitHub Actions free-tier does not provide GPU access. All methods are selected to be CPU-tractable.