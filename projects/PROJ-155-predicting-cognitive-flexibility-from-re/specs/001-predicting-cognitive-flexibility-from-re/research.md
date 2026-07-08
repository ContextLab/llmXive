# Research: Predicting Cognitive Flexibility from Resting‑State Functional Connectivity Variability

## Executive Summary

This research plan operationalizes the hypothesis that inter-individual variability in resting-state functional connectivity (RSFC) predicts cognitive flexibility. The core methodology involves computing the standard deviation and Shannon entropy of sliding-window correlation matrices derived from fMRI data. The analysis is strictly constrained to CPU-only execution on GitHub Actions, necessitating efficient batching and optimized numerical libraries.

**Critical Data Constraint**: The project relies **strictly** on verified datasets. If the verified data sources do not contain the required raw fMRI NIfTI files and specific NIH Toolbox Dimensional Change Card Sort scores, the primary hypothesis test (FR-005) **cannot** be performed. The project will halt at Phase 0 with a "Data Gap" report. No synthetic data will be used to validate the biological hypothesis.

## Dataset Strategy

### Source Verification
The project relies on the **HCP 1200-subject release** for resting-state fMRI and behavioral data. The "Verified datasets" block provides the following sources:
- **HCP (Raw fMRI & Behavior)**: 
  - **Status**: **NO VERIFIED SOURCE FOUND** in the provided list.
  - **Note**: The provided URLs (e.g., `Lexica.art.parquet`, `NIH-Chest-X-ray-dataset`) do not contain the required raw fMRI NIfTI files or the specific NIH Toolbox Dimensional Change Card Sort scores.
  - **Action**: The pipeline will attempt to load the verified URLs. If they fail to provide the required data, the project will **halt** and generate a "Data Gap Report". No simulation will be used for hypothesis testing.

### Gap Analysis & Mitigation
**Critical Gap**: The verified URLs do not contain the required raw fMRI or specific behavioral scores.

**Mitigation Strategy**:
1.  **Phase 0 Validation**: The `data/download.py` script will attempt to load the verified URLs and inspect columns for `Flexibility_Score` and fMRI time-series data.
2.  **Halt Condition**: If the required data is missing, the pipeline will:
    *   Generate a `data/gap_report.md` detailing the missing variables.
    *   **Stop execution** of the hypothesis test (FR-005).
    *   **Do NOT** fabricate a URL or assume the data exists.
    *   **Do NOT** use synthetic data to claim biological validity.

### Variable Mapping
| Variable | Source | Description |
| :--- | :--- | :--- |
| **RSFC Time-Series** | HCP (Verified Source Check) | Preprocessed fMRI time-series (MNI space). **Required**. |
| **Schaefer Atlas** | Local/External (Verified) | 200-region parcellation (Schaefer et al.,). |
| **Flexibility Score** | NIH Toolbox (Verified Source Check) | Dimensional Change Card Sort score. **Required**. |
| **Age, Sex** | HCP (Verified Source Check) | Demographic covariates. |
| **Mean FD** | HCP (Verified Source Check) | Motion metric for exclusion/covariate. |

## Methodology & Statistical Rigor

### 1. Data Preprocessing (FR-001, FR-002)
- **Ingestion**: Download and verify checksums.
- **Parcellation**: Apply Schaefer atlas to extract mean time-series per region.
- **Motion Control**: Exclude subjects with Mean FD > 0.2mm (Constitution Principle VI).
- **SNR Filter**: Exclude subjects with low temporal SNR (tSNR < 50) to reduce noise artifacts.
- **Missing Data**: Drop subjects missing Flexibility Scores; log count.

### 2. Dynamic Connectivity Metrics (FR-003, FR-004)
- **Sliding Window**: **60-second window**, 1-second step.
  - **Justification**: A 30s window (Constitution default) yields ~41 time points (TR=0.72s), which is mathematically insufficient to estimate a 200x200 correlation matrix (rank deficiency). A window of appropriate duration provides a sufficient number of time points for analysis., stabilizing the estimate. This deviation is documented in the Constitution Check.
- **Metric Calculation**:
  - Pearson correlation matrix per window.
  - Standard Deviation (SD) per edge across windows.
  - Shannon Entropy per edge (base 2).
- **Dimensionality Reduction**:
 - **Primary Predictor**: Instead of a single "Mean SD" scalar (which dilutes signal), we perform **PCA** on the edge-wise variability matrix ([deferred] edges) to retain the top components explaining [deferred] variance.
  - **Rationale**: This preserves network-specific signal while managing dimensionality, addressing the risk of false negatives from aggregation.
- **Collinearity Check**: SD and Entropy are mathematically related; the primary analysis will use **PCA Components** to capture the joint variability structure.

### 3. Null Model Validation (FR-008)
- **Method**: **Autoregressive (AR) Surrogate** time series.
  - **Procedure**: Fit an AR model to the original time series to preserve the power spectrum and variance, then generate surrogate data that destroys specific temporal correlations.
  - **Test**: Compare variability metric of real data vs. AR surrogate (p < 0.05).
  - **Rationale**: Phase-shuffling preserves variance, making the test trivial. AR surrogates destroy temporal structure while preserving variance, providing a non-trivial test of "neural dynamics" vs. noise.

### 4. Motion-Noise Orthogonalization
- **Method**: Regress the variability metric against a "Motion-Noise Proxy" (high-frequency power in the time series) and use the **residuals** as the predictor.
- **Rationale**: Motion can artificially inflate variability. This step removes the variance component explained by motion, ensuring the predictor reflects neural dynamics rather than noise artifacts.

### 5. Statistical Association (FR-005, FR-006)
- **Model**: Linear Regression: `Flexibility_Score ~ PCA_Component_1 + ... + PCA_Component_10 + Age + Sex + Mean_FD + Scan_Time`.
- **Inference**: 
  - **Permutation Test**: 10,000 iterations shuffling the outcome variable.
  - **P-value**: Empirical p-value = (count(perm_stat >= obs_stat) + 1) / (N + 1).
  - **Correction**: If post-hoc network-specific tests are run, apply FDR (q ≤ 0.05) (FR-009).
- **Causal Framing**: Explicitly state findings are **associational** (observational study).

### 6. Sample Size & Power
- **Justification**: HCP 1200 is a large sample. However, after motion exclusion (a small but non-negligible proportion), SNR filtering ([deferred]), and missing data, the effective N may be substantial.
- **Power**: With N=800, the study has >80% power to detect a small effect size (r=0.05) on the top PCA component at α=0.05.
- **Limitation**: If the verified data sources yield a smaller sample, power will be recalculated and reported.

## Compute Feasibility (CPU-Only)

- **Memory Management**: Data is processed in batches to stay within available RAM constraints..
- **Library Selection**: `numpy` and `scipy` for numerical operations; `statsmodels` for regression. No GPU libraries (PyTorch/CUDA) used.
- **Runtime**: Permutation test (10k iterations) on N=800 is computationally intensive.
  - **Optimization**: Use vectorized operations for permutation; parallelize across multiple CPU cores if possible (or sequential if overhead is high).
  - **Fallback**: If runtime exceeds a significant threshold, reduce iterations to a lower, computationally feasible count. (still robust) and report.

## Decision Rationale

| Decision | Rationale |
| :--- | :--- |
| **PCA Components as Primary Metric** | Preserves network-specific signal; avoids signal dilution from aggregation. |
| **60s Window** | Necessary to avoid rank deficiency in 200-region matrix estimation (vs. 30s default). |
| **AR Surrogate Null Model** | Non-trivial test that distinguishes neural dynamics from variance-preserving noise. |
| **Motion-Noise Orthogonalization** | Removes motion-induced artifacts from the variability metric. |
| **Halt on Missing Data** | Adheres to Verified Accuracy (Principle II); no simulation for hypothesis testing. |

## Risks & Mitigations

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| **Verified URLs lack required data** | High (Pipeline cannot run) | **Halt** with "Data Gap Report". No simulation. |
| **Runtime > 6 hours** | High (CI failure) | Optimize permutation loop; reduce iterations if necessary. |
| **Motion exclusion too aggressive** | Medium (Low N) | Log exclusion count; report power analysis for final N. |
| **Noise Floor** | Medium (False Positive) | SNR Filter and Motion-Noise Orthogonalization steps. |
