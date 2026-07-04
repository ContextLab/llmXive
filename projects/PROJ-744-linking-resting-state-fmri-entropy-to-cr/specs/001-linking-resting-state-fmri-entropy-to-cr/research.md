# Research: Linking Resting‑State fMRI Entropy to Creative Problem Solving

## 1. Scientific Background

### 1.1 Resting-State Entropy and Creativity
Resting-state functional MRI (rs-fMRI) captures the brain's intrinsic activity. Recent theories suggest that the complexity (entropy) of these fluctuations reflects the brain's capacity for flexible information processing, a core component of creativity. Multiscale Sample Entropy (MSE) quantifies this complexity across multiple temporal scales, offering a more robust metric than single-scale entropy by capturing dynamics at both short and long time scales.

### 1.2 The Alternative Uses Test (AUT)
The Alternative Uses Test is a standard psychometric measure of divergent thinking, requiring participants to generate novel uses for common objects. Scores typically reflect fluency, originality, and flexibility. In the HCP dataset, these scores serve as the behavioral outcome for linking neural complexity to creative performance.

### 1.3 Methodological Rigor
* **Motion Artifacts**: Head motion is a major confound in rs-fMRI, artificially inflating entropy estimates. Rigorous scrubbing (framewise displacement) and exclusion criteria are mandatory. Additionally, motion parameters will be regressed out of the time series *before* entropy calculation to address non-linear motion effects. Mean_FD is included as a covariate only to control for residual linear effects, acknowledging that non-linear motion artifacts are best handled by pre-processing scrubbing.
* **Multiple Comparisons**: Testing entropy across multiple canonical networks (DMN, FPN, CON, etc.) increases the risk of false positives. Benjamini-Hochberg (BH) FDR correction is required.
* **Parameter Sensitivity**: The tolerance parameter `r` in Sample Entropy is arbitrary (default 0.2*SD). A sensitivity analysis is required to ensure findings are not artifacts of this specific choice, including surrogate data validation to rule out noise.
* **Statistical Modeling**: Per Spec User Story 2, a Linear Mixed-Effects model is statistically invalid for cross-sectional data (1 observation per subject). The primary analysis uses **Ordinary Least Squares (OLS) with Robust Standard Errors** to account for heteroscedasticity while respecting the data structure.

## 2. Dataset Strategy

### 2.1 Source Verification
The project relies on the **HCP (Human Connectome Project)** dataset. Per the "Verified datasets" block provided, the following sources are available.

| Dataset Component | Verified Source URL | Status | Notes |
|:--- |:--- |:--- |:--- |
| **HCP 4-D fMRI (S3)** | `https://openneuro.org/datasets/ds000030` | **Verified** | Pre-processed 4-D NIfTI volumes. Downloaded automatically by T001b. |
| **HCP Phenotypes (HCP-1200)** | `https://db.humanconnectome.org/app/action/Download?datasetId=HCP1200` | **Verified** | Behavioral data including AUT scores. |
| **HCP Metadata** | ` | **Verified** | Supplemental metadata. |

*Note: The 'Lexica.art.parquet' source has been removed as it is irrelevant to neuroimaging.*

### 2.2 Dataset-Variable Fit Analysis
* **Predictor Variables**: The spec requires pre-processed 4-D fMRI volumes (NIfTI) to compute MSE. The verified OpenNeuro S bucket (ds000030) contains these volumes.
 * *Action*: The pipeline downloads these volumes automatically (T001b) as per Constitution Principle VI. Manual injection is not assumed; the pipeline halts if the verified source is unreachable.
* **Outcome Variable**: The spec requires `Creative_Problem_Solving.csv` (AUT scores). The verified HCP-1200 release contains these scores.
 * *Action*: The pipeline extracts AUT scores from the HCP-1200 behavioral data. If missing, the pipeline halts with a specific error code.

### 2.3 Sample Representativeness Check
* **Protocol**: Compare the demographic (age, sex) and motion (Mean FD) characteristics of the final sample (those with AUT scores) against the full HCP cohort using t-tests and chi-square tests.
* **Action**: If significant bias is found (p < 0.05), results will be weighted or interpreted with explicit caveats regarding generalizability.

## 3. Statistical Approach

### 3.1 Primary Model
* **Method**: **Ordinary Least Squares (OLS) with Robust Standard Errors (HC1)**.
* **Justification**: Spec User Story 2 explicitly states that LMM is invalid for cross-sectional data (1 observation per subject). OLS with Robust SEs is the correct approach to handle heteroscedasticity without violating independence assumptions.
* **Formula**: `AUT_Score ~ Global_Entropy + Age + Sex + Mean_FD`
* **Covariates**: Age, Sex, Mean Framewise Displacement (FD).
* **Motion Correction**: Time-series scrubbing and motion parameter regression are applied *before* entropy calculation. Mean_FD is included as a secondary covariate to control for residual linear motion effects.
* **Outcome Transformation**: If AUT scores are skewed, a Rank-Based Inverse Normal Transformation (INT) is applied to satisfy normality assumptions.
* **Collinearity Check**: Variance Inflation Factor (VIF) will be computed. If VIF > 5, the model will be re-specified.

### 3.2 Multiple Comparison Correction
* **Method**: Benjamini-Hochberg (BH) FDR.
* **Application**: Applied to the 7 p-values derived from network-specific models (DMN, FPN, CON, etc.).
* **Threshold**: q < 0.05.

### 3.3 Sensitivity Analysis
* **Parameter**: Tolerance `r` ∈ {0.15*SD, 0.20*SD, 0.25*SD}.
* **Procedure**:
 1. Re-compute **Multiscale Sample Entropy (AUC across scales 1-20)** for *each* `r` value.
 2. Re-fit the OLS model for each `r` value.
 3. Compare the headline p-value stability.
 4. **Surrogate Validation**: Generate phase-randomized surrogates of the fMRI time series to ensure the entropy metric captures non-linear structure and not just noise properties.
* **Metric**: Variation in p-value and coefficient magnitude.

### 3.4 Power Analysis
* **Assumption**: HCP sample size (N > 1000) is sufficient.
* **Projection**: After motion exclusion (estimated to be a substantial proportion), N is expected to be approximately 700-800.
* **Detectable Effect**: With N=700 and alpha=0.05 (FDR corrected), the study is powered to detect small effect sizes (r > 0.10) with power > 0.80.
* **Constraint**: If the filtered N drops below 30, the analysis halts (SC-005).

## 4. Compute Feasibility & Constraints

* **Hardware**: GitHub Actions Free Tier (2 CPU, 7 GB RAM, 14 GB Disk).
* **Memory Management**:
 * fMRI data is loaded in chunks (one subject at a time).
 * Entropy computation is vectorized but memory-intensive; `numpy` operations will be optimized to avoid copies.
 * Peak RAM will be instrumented using `tracemalloc` or `psutil`.
* **Runtime**:
 * Target: < 6 hours.
 * Strategy: If runtime exceeds a predefined threshold, the sensitivity sweep may be limited to a subset of subjects (if statistically valid) or the scale range reduced (with explicit logging).
* **No GPU**: All computations must use CPU-optimized libraries (`scipy`, `numpy`, `statsmodels`).