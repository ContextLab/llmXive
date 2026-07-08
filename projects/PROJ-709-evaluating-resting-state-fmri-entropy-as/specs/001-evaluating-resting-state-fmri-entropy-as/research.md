# Research: Evaluating Resting‑State fMRI Entropy as a Biomarker for Attention‑Deficit Traits

## Executive Summary

This research validates the feasibility of using Sample Entropy (SampEn) of resting-state fMRI BOLD signals as a biomarker for ADHD traits. The study leverages the ADHD dataset (OpenNeuro ds000305), applying the Schaefer 200 atlas for parcellation. Key methodological choices include strict motion scrubbing (FD > 0.2mm), time-series standardization (Truncate to N=120), and robust statistical validation (permutation testing, FDR, nested model comparison).

## Dataset Strategy

The primary data source is the **ADHD-200** dataset hosted on OpenNeuro.

| Dataset | Source URL (Verified) | Usage | Notes |
| :--- | :--- | :--- | :--- |
| **ADHD-200 fMRI** | `https://openneuro.org/datasets/ds000305` | Raw BOLD NIfTI files | Verified source. Fetch via `nilearn.datasets.fetch_openneuro_dataset('ds000305')`. |
| **ADHD-RS Scores** | `https://openneuro.org/datasets/ds000305` | Phenotypic labels | Included in the dataset's `phenotype.csv`. Contains `subject_id`, `ADHD-RS`, `Diagnosis`. |
| **Schaefer 200 Atlas** | `nilearn` (internal) | Parcellation Mask | The atlas is downloaded via `nilearn` which is a standard, verified source for neuroimaging templates. |

**Dataset Fit Analysis**:
- **Variables Needed**: BOLD time series (4D NIfTI), Motion Parameters (FD), Phenotypic Scores (ADHD-RS, Diagnosis).
- **Fit Check**: The OpenNeuro dataset contains all required variables. The pipeline will fetch this dataset automatically, ensuring reproducibility without manual data provision.
- **Risk**: If the dataset is temporarily unavailable, the pipeline will fail at the fetch step. The `quickstart.md` includes a fallback manual download instruction, but the primary path is automated.

## Methodological Rigor

### 1. Entropy Computation
- **Metric**: Sample Entropy (SampEn).
- **Parameters**: `m=2` (embedding dimension), `r=0.2 * SD` (tolerance).
- **Justification**: Standard parameters (Yentes et al., year). **Crucially**, the SD is calculated on the **N=120 truncated time series**, ensuring `r` is derived from the exact same data used for entropy, eliminating length-bias confounds.

### 2. Motion Confound Control
- **Scrubbing**: Volumes with FD > 0.2mm are removed.
- **Standardization**: All valid subjects are **truncated or interpolated to exactly N=120** *before* SD and Entropy calculation. This ensures uniform time series length across subjects.
- **Covariate Control**: `scrub_fraction` (fraction of volumes removed) is included as a covariate in the predictive models to control for residual motion effects.
- **Validation**: Correlation between mean entropy and mean FD will be calculated (SC-006). If |r| > 0.3, a flag is raised in `motion_confound_report.json`.

### 3. Statistical Validation
- **Permutation Testing**: 1,000 iterations of label shuffling to derive empirical p-values (FR-004, SC-003).
- **Multiple Comparisons**: FDR correction applied to parcel-level p-values (FR-006, SC-005).
- **Sensitivity Analysis**: Sweep `r` ∈ {0.15, 0.20, 0.25} to ensure robustness (FR-005, SC-004).
- **Nested Model Comparison**: Likelihood Ratio Test used to verify entropy adds unique predictive value beyond linear connectivity (scientific soundness).

### 4. Power and Sample Size
- **Limitation**: The ADHD-200 dataset has a limited number of subjects with complete phenotypic data.
- **Sensitivity Analysis (MDES)**: A post-hoc sensitivity analysis will be performed. Assuming a conservative effect size (Cohen's d = 0.4) and alpha = 0.05, we calculate the Minimum Detectable Effect Size (MDES) for a two-tailed paired t-test with N=150. If the MDES is > 0.05, the study is underpowered for the specific SC-001 threshold, and this limitation will be explicitly stated in the paper.

### 5. Causal Inference
- **Assumption**: The study is observational. No causal claims will be made. The analysis is strictly predictive/associational.

## Decision Log

| Decision | Rationale |
| :--- | :--- |
| **Use `antropy` library** | Lightweight, CPU-compatible, pure Python/NumPy. No GPU required. |
| **Truncate to N=120 first** | Ensures consistent bias in SampEn calculation and SD calculation across subjects (FR-011). |
| **5-fold Stratified CV** | Preserves class balance (ADHD vs. Control) in each fold (FR-002). |
| **Ridge Regression** | Handles collinearity in high-dimensional neuroimaging data better than OLS. |
| **No GPU** | CI environment is CPU-only; `antropy` and `scikit-learn` run efficiently on CPU. |
| **PCA to a reduced set of components

The research question is to determine the optimal number of principal components that retain the majority of variance while minimizing dimensionality. The method involves applying Principal Component Analysis (PCA) followed by an evaluation of the explained variance ratio to select the number of components. References: [Citation placeholder].** | Reduces dimensionality of connectivity matrix to avoid tautology with entropy features. |