# Research: Investigate Brain Network Dynamics and VR Therapy Response

## Executive Summary

This research plan addresses the feasibility of investigating the relationship between resting-state brain network dynamics and VR therapy response using open-source data. The core challenge is the scarcity of longitudinal datasets containing *both* resting-state fMRI and paired pre/post clinical anxiety scores in public repositories. The plan prioritizes rigorous data validation, power analysis, and robust statistical methods to ensure scientific validity even in a pilot setting.

## Dataset Strategy

### Verified Datasets & Availability Analysis

Based on the `# Verified datasets` block provided and external knowledge of open neuroimaging repositories:

| Dataset Name | Verified URL / ID | Suitability for Study | Status |
|:--- |:--- |:--- |:--- |
| **OpenNeuro (BIDS)** | `https://openneuro.org/datasets/` (Search for `anxiety` + `fMRI` + `longitudinal`) | **Primary Target**. Requires manual verification of paired pre/post scores and raw NIfTI. | **Pending Verification** |
| **OpenNeuro ds000246** | `https://openneuro.org/datasets/ds000246` | **Potential**. Known to contain anxiety-related fMRI, but requires verification of longitudinal VR data. | **Candidate** |
| **GAD-7** | No direct dataset URL; standard instrument. | **Reference Only**. Used for validation whitelist. | **N/A** |
| **HAM-A** | ` | **Unsuitable**. Points to anime data. | **REJECTED** |
| **HCP-Young-Adults** | `https://openneuro.org/datasets/ds000224` | **Secondary**. Contains fMRI but lacks clinical anxiety scores. | **Fallback for fMRI only** |

### Critical Feasibility Gap (FR-013)

The spec requires a dataset with **paired pre/post fMRI and clinical scores**.
- **Risk**: Most open fMRI datasets lack paired clinical scores or specific VR therapy interventions.
- **Action**: The implementation MUST execute `data/validate.py` to check for `pre_treatment_score`, `post_treatment_score`, and `anxiety_instrument`.
- **Fallback Protocol**:
 1. **Aggregation**: Check 3 sources (OpenNeuro, HCP, Secondary) for *any* paired data.
 2. **Proxy Strategy**: If no VR-specific data exists, use a proxy dataset (e.g., general anxiety treatment) to validate the *pipeline logic*, explicitly noting the modality mismatch.
 3. **Halt**: If no suitable data (even proxy) is found after 3 sources, halt with "Data Unavailable: No longitudinal dataset found".

### Data Source Fallback Protocol

If the primary OpenNeuro BIDS link fails (missing clinical scores or raw fMRI):
1. **Search** for specific OpenNeuro dataset IDs known to contain anxiety scores (e.g., `ds000246`, `ds001234`).
2. **Verify** raw NIfTI availability (not just parquet/test subsets).
3. **Synthetic Data Generator**: If real data is unavailable, generate synthetic fMRI time series and clinical scores **strictly for pipeline testing** (not hypothesis testing) to validate code logic.
4. **Reframing Strategy**: If no open longitudinal VR dataset exists, reframe the study as a "Methodological Demonstration on Proxy Data" or halt.

## Methodology

### 1. Data Preprocessing (US-1)
- **Tool**: `nilearn` (CPU-optimized).
- **Steps**:
 1. Load raw NIfTI (streaming if large).
 2. Motion Correction (Realignment).
 3. Slice Timing Correction.
 4. Spatial Normalization (MNI space).
 5. **Quality Control**: Compute FD (Framewise Displacement). Exclude subjects with FD > 3mm/3° (SC-002).
- **Feasibility**: `nilearn` runs on CPU. Processing N=20 subjects within 6 hours is feasible if using a subset of volumes or a small ROI atlas.

### 2. Network Metric Computation (US-2)
- **Parcellation**: Schaefer-100 or AAL (standard, low dimensionality).
- **Connectivity**: Pearson correlation of ROI time series.
- **Metrics**:
 - Modularity (Q): Community detection (Louvain algorithm).
 - Global Efficiency: Inverse of average shortest path length.
 - Local Efficiency: Average local clustering.
- **Validation**: Ensure values are non-negative/finite (SC-003). Handle NaNs by exclusion.
- **Collinearity Handling**:
 - **Primary**: Report univariate associations for each metric (Modularity, Global Efficiency, Local Efficiency) with FDR correction.
 - **Secondary (Exploratory)**: If VIF > 5, run PCA on metrics. Use PC1/PC2 **only** for visualization or robustness checks, explicitly noting they are composite variables and not direct biological proxies.

### 3. Statistical Analysis (US-3)
- **Outcome Definition**:
 - **Primary**: Change Score (Post - Pre) to isolate treatment effect.
 - **Secondary**: Residual of Post on Pre (to control for baseline).
 - **Tertiary**: Raw Post Score (for sensitivity analysis).
- **Model**: ANCOVA.
 - Outcome: Change Score / Residual.
 - Predictors: Network Metric (univariate), Pre-treatment Score (covariate).
 - Confounders: Age, Medication (if available).
- **Collinearity**: If VIF > 5, run PCA **only for exploratory visualization**. Do not replace primary predictors with PCs.
- **Correction**: Bonferroni or FDR for >1 metric tested (FR-006).
- **Framing**: Check `metadata.randomized` or `study_design`. If absent, frame as **ASSOCIATIONAL** (FR-008).
- **Power**: Calculate required N (G*Power, α=0.05, f²=0.15). If N < 5, halt. If 5 ≤ N < required, warn and frame as exploratory (SC-004).
- **Biomarker Claim**: Only if p < 0.05 AND Cohen's d > 0.5 AND FDR corrected. Else, report as non-significant.

### 4. Sensitivity Analysis (US-3)
- **Sweep**:
 - Motion: {2.0, 3.0} mm.
 - P-value: {0.01, 0.05, 0.1}.
 - Outcome Definition: {Change Score, Residual, Raw Post}.
- **Output**: Table of effect sizes and CIs across sweeps (FR-010) in `reports/sensitivity_analysis.md`.

## Compute Feasibility & Rationale

- **CPU-First Strategy**: All selected methods (nilearn, scikit-learn, statsmodels) are CPU-tractable.
- **Memory**: Streaming `datasets.load_dataset(..., streaming=True)` ensures memory < 7GB.
- **Disk**: Intermediate files (preprocessed NIfTI) are large. We will process subject-by-subject and delete intermediate NIfTI after metric extraction to stay within 14GB.
- **GPU Escape Hatch**: Not required. No deep learning or large model inference is planned. If a future iteration requires a large transformer for denoising, the plan would need to be updated to use a scaled-down 8-bit model on Kaggle, but for this spec, CPU is sufficient and preferred.

## References

- **OpenNeuro Data**: `https://openneuro.org/datasets/` (Search for `anxiety` + `fMRI` + `longitudinal`).
- **GAD-7**: No verified URL. Cited by name only as a standard instrument.
- **HAM-A**: ` (Rejected: Anime data).
- **BCT**: Brain Connectivity Toolbox (v0.5+).
- **Nilearn**: `.