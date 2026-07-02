# Research: Assessing the Impact of Network Centrality on Age‑Related Cognitive Decline

## 1. Problem Definition & Hypotheses

**Primary Question**: Do network centrality metrics (degree, betweenness, closeness) derived from resting-state fMRI in older adults predict performance on standardized cognitive assessments (ADAS-Cog, MMSE, processing speed), specifically within the Default Mode Network (DMN) and Frontoparietal Network (FPN)?

**Hypotheses**:
- H1: Higher centrality (degree/betweenness) in DMN nodes is associated with better cognitive performance (lower ADAS-Cog, higher MMSE).
- H2: Higher centrality in FPN nodes is associated with better processing speed.
- H3: These associations remain significant after controlling for age, sex, education, and diagnosis (CN vs. MCI).

## 2. Dataset Strategy

**Target Data Source**: Alzheimer's Disease Neuroimaging Initiative (ADNI).
**Required Variables**:
- **Imaging**: Resting-state fMRI (rs-fMRI) scans.
- **Cognitive**: ADAS-Cog, MMSE, Trail Making Test A (TMT-A) or WAIS-R Digit Symbol (processing speed).
- **Demographics**: Age, Sex, Education years.
- **Clinical**: Diagnosis (CN, MCI, AD).

**Dataset Availability & Gap Analysis**:
- **Status**: The prompt's "Verified datasets" block lists URLs for `adasgaleus` and `MMS-e` datasets. These are **NOT** the ADNI rs-fMRI dataset required for this study. They contain unrelated data (e.g., resume data, chlorophyll sensors).
- **Action**: The implementation **cannot** use the provided URLs for the primary analysis. The plan relies on the official ADNI LONI IDGK portal (requires registration and credentials) as per the spec's assumptions.
- **Fallback Strategy for CI**: Since the GitHub Actions runner cannot access the private ADNI portal without credentials, the `code/download` module will support two modes:
  1. **Production**: Authenticates to ADNI portal (requires `ADNI_USER`, `ADNI_PASS` env vars).
  2. **CI/Simulation**: Generates a synthetic dataset mimicking the ADNI schema (90 ROIs, centrality metrics, cognitive scores) to validate the pipeline logic and statistical tests. This synthetic data will be used for automated testing.

**Data Volume Estimation**:
- A single rs-fMRI run (a standard number of volumes, isotropic voxels) is ~50-100MB. 
- A cohort of participants will generate a substantial volume of raw data. 
- **Constraint**: The GitHub runner has sufficient disk space. Processing must delete raw NIfTI files after preprocessing to fit the dataset.

## 3. Methodology & Statistical Rigor

### 3.1 Preprocessing (FR-002)
- **Tools**: 
  - **Production**: Docker container with FSL/AFNI (MCFLIRT, BET, FLIRT, FNIRT) for motion correction, normalization, and filtering.
  - **CI**: `nilearn.signal.clean` and `nilearn.image.resample_img` (downsampled to 4mm) for validation.
- **Motion Control**: 
  - **Scrubbing**: Remove volumes with Framewise Displacement (FD) > 0.5mm.
  - **Nuisance Regression**: Regress out 6 motion parameters, WM, and CSF signals before connectivity estimation.
- **QC**: Exclude if mean FD > 0.5mm or >20% volumes > 0.5mm (FR-013).
- **Validation Note**: While Nilearn is used for CI to meet runtime constraints, production runs must use FSL/AFNI to ensure scientific fidelity of the centrality metrics.

### 3.2 Connectivity & Centrality (FR-003, FR-004, FR-005)
- **Atlas**: AAL90 (Automated Anatomical Labeling).
- **Connectivity**: Pearson correlation matrix (90x90).
- **Metrics**: Degree, Betweenness, Closeness centrality (NetworkX).
- **Aggregation**: Mean centrality per participant for DMN and FPN ROIs.
- **Output**: Separate columns for `dmn_mean_degree`, `fpn_mean_degree`, etc., in the analysis dataset.

### 3.3 Regression Analysis (FR-007, FR-008, FR-009, FR-016)
- **Model Strategy**: Hierarchical Linear Regression.
  - **Model 1**: Covariates only (Age, Sex, Education, Diagnosis).
  - **Model 2**: Covariates + All 3 Centrality Metrics (Degree, Betweenness, Closeness) simultaneously.
  - **Goal**: Test the unique variance explained by each metric while controlling for the others.
- **Collinearity Handling Protocol**:
  - Calculate Variance Inflation Factor (VIF) for predictors in Model 2.
  - **If VIF > 5**: Trigger fallback to Principal Component Analysis (PCA) on the three metrics. Use the first 2-3 orthogonal components as predictors instead of the raw metrics to ensure stable coefficients.
- **Multiple Comparison Correction**:
  - **Method**: Benjamini-Yekutieli (BY) correction.
  - **Rationale**: The tests (3 metrics x 3 outcomes) are not independent due to shared outcomes and correlated predictors. BY is valid for arbitrary dependence.
  - **Scope**: Applied to the 9 specific p-values from the centrality predictors in Model 2.
- **Assumption Checks**: 
  - Linearity (Residual plots).
  - Normality (Shapiro-Wilk).
  - Homoscedasticity (Breusch-Pagan).
  - Independence (Durbin-Watson).
  - **Non-Linearity Protocol**: If a quadratic term is significant, the pipeline will flag a 'Warning' in the report but **continue** with the mandated Linear Regression (FR-007) for the primary output to satisfy the spec.
- **Power Analysis (FR-014)**:
 - **Threshold**: Minimum **120** participants required for [deferred] power to detect f² = 0.15 (medium effect) with 7 predictors (3 metrics + 4 covariates) at α = 0.05.
  - **CI Fallback**: N=20 for logic validation only (not powered for hypothesis testing).

### 3.4 Correlation Matrix (FR-016, SC-007)
- **Action**: Compute Pearson correlation matrix among Degree, Betweenness, and Closeness.
- **Storage**: This matrix is explicitly stored in the `regression_results.json` file under the key `predictor_correlation_matrix` to satisfy SC-007.

## 4. Compute Feasibility & Constraints

- **Hardware**: GitHub Actions Free Tier (limited vCPU, 7GB RAM, No GPU).
- **Memory Management**:
  - Process participants in batches or stream data.
  - Delete raw NIfTI files immediately after preprocessing.
  - Use `pandas` with `dtype` optimization (float32 instead of float64 where possible).
- **Runtime Optimization (CI)**:
  - **Downsampling**: fMRI data resampled to 4mm resolution for CI runs to reduce processing time.
  - **Sample Limit**: CI runs limited to N=20 participants.
  - **Estimation**: 20 subjects @ 4mm resolution ~ 15-20 mins total on 2 vCPU, well within 6-hour SLA.
- **Target**: < 6 hours for N=20 (CI) or N=120 (Production with Docker/FSL).

## 5. Decision Log

| Decision | Rationale |
| :--- | :--- |
| **Use Docker for FSL/AFNI** | Ensures FR-002 compliance in production without relying on pre-installed binaries. |
| **Nilearn for CI** | Pure Python stack ensures portability and speed for logic validation on 2 vCPU. |
| **Hierarchical Regression** | Addresses collinearity by testing unique variance of metrics simultaneously. |
| **PCA Fallback** | Ensures model stability if VIF > 5, preventing unstable coefficients. |
| **BY Correction** | Handles arbitrary dependence among the 9 tests, more robust than BH. |
| **Non-Linearity Flag** | Acknowledges biological complexity without violating the mandatory Linear Regression requirement (FR-007). |
| **Synthetic Data for CI** | ADNI requires authentication. Automated CI tests cannot run without credentials. Synthetic data validates the logic without violating data policies. |
| **Drop raw data post-processing** | Disk constraints are tight for 100+ participants. Deleting raw files after creating connectivity matrices is necessary. |