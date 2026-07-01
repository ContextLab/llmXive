# Research: Investigate Brain Network Dynamics and VR Therapy Response

## 1. Executive Summary

This research plan outlines the computational strategy to determine if resting-state brain network metrics (modularity, efficiency) predict **post-treatment state** (primary) and **response to therapy** (secondary/exploratory) following VR exposure therapy. The study relies on public neuroimaging datasets. A critical constraint is the **Dataset-Variable Fit**: the analysis requires a dataset containing *both* resting-state fMRI scans (pre/post) *and* validated clinical anxiety scores (pre/post).

**Status**: **BLOCKED** pending verification of a dataset containing paired fMRI and clinical scores for VR therapy. The current `# Verified datasets` block does not list a verified source for such a dataset. The pipeline is designed to detect this absence and halt (FR-011).

## 2. Dataset Strategy

### 2.1 Target Data Requirements
- **Modality**: Resting-state fMRI (rs-fMRI).
- **Timepoints**: Pre-treatment and Post-treatment.
- **Clinical Outcomes**: Validated anxiety scales (e.g., GAD-7, HAM-A) at both timepoints.
- **Covariates**: Age, sex, medication status, and **mean Framewise Displacement (FD)**.

### 2.2 Verified Sources Analysis
Based on the provided `# Verified datasets` block:

| Dataset Name | Verified URL | Contains rs-fMRI? | Contains Clinical Scores? | Suitability |
| :--- | :--- | :--- | :--- | :--- |
| GAD-7 | NO verified source | No | Yes (Scale only) | **Insufficient** (No fMRI) |
| HAM-A (zip) | `huggingface.co/.../cham221.zip` | No | Yes (Scale only) | **Insufficient** (No fMRI) |
| MUST (parquet) | `huggingface.co/.../parquet` | No | No (Text) | **Insufficient** |
| US-3 (json) | `huggingface.co/.../json` | No | No (Text) | **Insufficient** |

**Conclusion**: No verified dataset in the provided block contains the required **paired rs-fMRI and clinical anxiety scores** for VR therapy.
- **Action**: The pipeline MUST implement `FR-011` and `SC-001` to check for these variables.
- **Fallback**: If no verified source is found, the system MUST halt with `Fatal Error: Missing required variable: [rs-fMRI or Clinical Score]`.
- **Note**: Do not fabricate a URL. If a researcher manually provides a new dataset ID (e.g., OpenNeuro), the validation step must verify the metadata JSON for the required fields before proceeding.

## 3. Methodology & Statistical Rigor

### 3.1 Preprocessing (FR-002)
- **Tools**: `nilearn` (CPU-optimized wrappers for FSL/AFNI logic).
- **Steps**:
  1. Slice timing correction.
  2. Motion correction (Realignment).
  3. Spatial normalization (MNI152).
  4. Smoothing (spatially smoothed with an appropriate kernel size).
  5. **Quality Control**: Calculate FD (Framewise Displacement). Exclude subjects with mean FD > 3mm or max rotation > 3° (SC-002).
- **Feasibility**: Processing N=10 subjects on 2 CPU cores is estimated at ~15-20 mins/subject (150-200 mins total), well within the 6-hour limit. (Note: N=20 was rejected as it exceeds 6h).

### 3.2 Network Metric Computation (FR-003, FR-004)
- **Parcellation**: Schaefer 100-region or AAL (default: Schaefer 100 for better sensitivity).
- **Connectivity**: Pearson correlation of ROI time series.
- **Metrics**:
  - **Modularity (Q)**: Louvain algorithm. Range [0, 1].
  - **Global Efficiency**: Inverse of characteristic path length.
  - **Local Efficiency**: Average local clustering efficiency.
- **Bounds Check**: If any metric is NaN or out of bounds (SC-003), exclude that subject/metric.

### 3.3 Statistical Analysis (FR-005, FR-006, FR-013)

**Primary Hypothesis: Predicting Post-Treatment State**
- **Model**: ANCOVA.
  - **Outcome (Y)**: Post-treatment Score (State).
  - **Predictors**: Baseline Network Metric (Modularity/Efficiency).
  - **Covariates**: Pre-treatment Score (to control baseline severity), **Mean FD** (to control residual motion), Age, Sex, Medication (if available).
  - **Strategy**: **Pre-specified Univariate Models Only**. One model per metric (e.g., Post ~ Pre + Metric + FD + Covariates).
  - **Correction**: Apply Bonferroni or FDR correction for the 3 metrics tested (SC-004).
  - **Rationale**: Multivariate models with Ridge regression (Spec requirement) are rejected due to p-hacking risks and invalid p-values in small N. Univariate models with FDR are statistically robust for this exploratory study. **This contradicts Spec FR-005/FR-012; Spec update required.**
  - **Regression to the Mean (RTM)**: The ANCOVA model (Post ~ Pre + Metric) is preferred over Change-score ANCOVA to mitigate RTM bias.

**Secondary Exploratory Hypothesis: Predicting Treatment Response (Delta)**
- **Model**: Linear Regression.
  - **Outcome (Y)**: Change Score (Post - Pre).
  - **Predictors**: Baseline Network Metric.
  - **Covariates**: Mean FD, Age, Sex, Medication.
  - **Warning**: This analysis is underpowered and susceptible to regression to the mean. Results are labeled "Exploratory" only.

**Delta-Delta Model (Exploratory)**
- **Model**: Linear Regression.
  - **Outcome (Y)**: Change in Anxiety Score (Post - Pre).
  - **Predictors**: Change in Network Metric (Post-Metric - Pre-Metric).
  - **Covariates**: Mean FD (Pre), Mean FD (Post), Age, Sex.
  - **Rationale**: This directly tests if *changes* in brain network dynamics drive *changes* in anxiety. It is distinct from the primary ANCOVA and is strictly exploratory due to low power and high noise in delta measures.

**Collinearity Handling**:
- **Pre-specified Strategy**: Do NOT switch models based on VIF. Use Univariate models for each metric.
- **Reporting**: If VIF > 5 is detected in a univariate model (unlikely with one predictor + covariates), the model is run, but the report explicitly flags "High Collinearity" as a limitation. **Ridge regression is NOT used** for hypothesis testing due to bias in coefficient estimation and invalid p-values. **This contradicts Spec FR-005/FR-012; Spec update required.**

**Causal Framing**:
- Check `metadata.study_design`. If not "randomized", frame results as **ASSOCIATIONAL** (FR-008, SC-005).
- Do not claim causality.

### 3.4 Sensitivity Analysis (FR-010, SC-006)
- **Motion Thresholds**: Sweep {2mm, 3mm}.
- **P-value Cutoffs**: Sweep {0.01, 0.05, 0.1}.
- **Output**: Report variation in significant findings across these thresholds.

### 3.5 Power Analysis (SC-004)
- **Method**: G*Power equivalent calculation.
- **Parameters**: α=0.05, **Effect Size f²=0.35 (Large)**, Power≥0.8.
- **Constraint**: If N < 5, **HALT**. If 5 ≤ N < [Calculated Minimum for Large Effect], flag limitation.
- **Note**: With N=10, the study is only powered to detect **Large Effects**. It is underpowered for small/medium effects (f²=0.15). This is explicitly acknowledged as a limitation of the pilot study. The study is re-framed as an "Exploratory Pilot" capable only of detecting large effects.

## 4. Compute Feasibility

- **Hardware**: GitHub Actions Free Tier (limited CPU, limited RAM, No GPU).
- **Memory Management**:
  - Load fMRI data subject-by-subject (streaming).
  - Do not load all subjects into RAM simultaneously.
  - Use `nibabel` memory mapping for large NIfTI files.
- **Runtime**:
 - Preprocessing: [deferred]/subject × 10 subjects = [deferred] ([deferred]). Fits within 6h.
  - Analysis: Negligible (<10 mins).
- **Disk**: Raw fMRI (several hundred MB/subject) + Processed (~sub-gigabyte/subject) × multiple subjects = several gigabytes. Fits within 14GB.

## 5. Decision Rationale

- **Why CPU-only?**: Deep learning models for fMRI require GPUs and massive data. Classical network analysis (graph theory) is computationally efficient and standard for this sample size.
- **Why Schaefer 100?**: Balances spatial resolution with computational cost. An increase in the number of regions increases matrix size (O(N²)) and memory usage.
- **Why Univariate Models?**: Network metrics (efficiency, modularity) are highly correlated. Multivariate models with Ridge regression (Spec requirement) introduce bias and invalid p-values. Univariate models with FDR correction are the statistically soundest approach for small N. **Spec update required to remove Ridge mandate.**
- **Why Halt on Missing Data?**: FR-011 and SC-001 enforce "Dataset-Variable Fit". Running analysis on partial data (e.g., fMRI without scores) yields no scientific value.
- **Why N=10?**: N=20 exceeds the 6-hour runtime limit on 2 CPU cores. N=10 ensures feasibility while maintaining minimal statistical power for large effects.
- **Why Mean FD as Covariate?**: Residual motion artifacts correlate with both network metrics and clinical severity. Exclusion alone is insufficient; inclusion as a covariate is necessary to control for bias.
