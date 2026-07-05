# Research: Brain Network Efficiency and Fluid Intelligence

## 1. Dataset Strategy

### Verified Datasets
The following datasets have been verified for availability and format compatibility. The plan strictly adheres to these sources.

| Dataset Name | Description | Verified URL / Loader | Status |
|:--- |:--- |:--- |:--- |
| **HCP Subjects** | Resting-state fMRI, NIH Toolbox Fluid Intelligence, demographics. | `https://db.humanconnectome.org/` (Requires credentials) | **Verified**: HCP data is the primary source. Access requires manual application. **CI Limitation**: Not available via public API or HuggingFace for automated CI. The pipeline MUST use a 'Mock/Simulated Data' mode for CI testing (generating synthetic time series matching the HCP schema) to validate logic. Final results require manual HCP access. |
| **Schaefer Atlas** | 200 and 400 ROI parcellations based on Yeo-7 networks. | ` | **Verified**: Publicly available GitHub repository. |
| **Yeo-7 Networks** | Definition of frontoparietal subgraph. | ` (Original Paper) | **Verified**: Standard reference for network definition. |

### Dataset Fit & Variable Confirmation
- **Required Variables**: Resting-state fMRI (4D NIfTI), Fluid Intelligence Score (NIH Toolbox), Age, Sex, Mean Framewise Displacement (FD).
- **Fit Confirmation**: The HCP 1200 release contains all required variables.
 - *fMRI*: Preprocessed minimally (HCP pipelines) or raw (if preprocessing is required by FR-002).
 - *Fluid Intelligence*: NIH Toolbox Fluid Composites are included in the behavioral data.
 - *Covariates*: Age, Sex, and FD are standard HCP metadata.
- **Gap Handling**: If a specific subject lacks a Fluid Intelligence score, the system will exclude them (Edge Case handling). If the HCP data is inaccessible in the CI environment (due to authentication), the plan includes a fallback to a **Mock Data Generator** that creates synthetic time series matching the HCP schema (verified by checksums) to validate the pipeline logic, while flagging the gap in the final report.

## 2. Methodological Rationale

### Preprocessing (FR-002)
- **Nuisance Regression**: Standard HCP minimally preprocessed data includes ICA-FIX. We will add nuisance regression for white matter, CSF, and global signal (if specified) + motion parameters.
- **Band-pass Filter**: 0.01–0.1 Hz to isolate low-frequency fluctuations.
- **FD Calculation**: Computed from motion parameters to exclude subjects with mean FD > 0.5 mm (Edge Case) and use as a covariate.

### Graph Construction (FR-003, FR-014)
- **Parcellation**: Schaefer 200-ROI (primary) and 400-ROI (robustness).
- **Connectivity**: Pearson correlation of time series.
 - **Primary**: Positive edges only (as per spec).
 - **Robustness**: Absolute value edges (to check bias from discarding negative correlations).
- **Thresholding**: Proportional thresholding at % density.
 - **Sensitivity Analysis**: We will vary density thresholds across a range of values to ensure results are not artifacts of the specific 20% threshold.
- **Disconnected Components**: If a graph is disconnected after thresholding (due to positive-edge-only constraint), the system will compute **Harmonic Mean Efficiency** (which handles infinite path lengths) instead of standard Global Efficiency. Subjects with >10% disconnected nodes will be excluded.
- **Subgraph Definition**: Frontoparietal network defined by Yeo-7 atlas mapping to Schaefer labels. This avoids circularity (FR-014).

### Statistical Analysis (FR-005, FR-006, FR-007, FR-009)
- **Correlation**: Pearson (primary) and Spearman (robustness) between efficiency metrics and fluid intelligence.
- **Regression**: Multiple linear regression: `Fluid_Intelligence ~ Global_Efficiency + Frontoparietal_Efficiency + Age + Sex + FD`.
- **FWE Correction**: **Max-statistic permutation testing (a sufficient number of permutations)**.
 - **Family of Tests**: The max-statistic is computed across the **two primary tests only**: (1) Global Efficiency vs. Fluid Intelligence, and (2) Frontoparietal Efficiency vs. Fluid Intelligence, both on the **200-ROI binary graph**.
 - **Robustness Checks**: 400-ROI and weighted graph results are **NOT** included in this FWE correction. They are reported as exploratory, uncorrected findings to avoid inflating the family-wise error rate.
- **Collinearity**: VIF calculation. If VIF > 5, orthogonalization or ridge regression will be applied and reported.
- **Causal Framing**: All results framed as associational (FR-008) due to observational design.

## 3. Compute Feasibility & Constraints

- **Hardware**: GitHub Actions Free Tier (multi-core CPU, moderate RAM).
- **Memory Management**:
 - fMRI data loading: Stream processing or memory mapping (`nibabel` + `numpy.memmap`).
 - Graph metrics: Computed per subject to avoid holding all matrices in memory.
- **Time Limit**: 6 hours per job.
- **Permutation Cost**:
 - **Target**: 1,000 permutations on N=500 subjects.
 - **Fallback**: If runtime exceeds a predefined buffer threshold, the system will automatically reduce N to a smaller cohort size..
 - **Rationale**: 10,000 permutations is computationally prohibitive on 2 CPUs. A sufficient number of permutations provides a valid null distribution while ensuring CI completion. The reduction from a large-scale baseline to a significantly smaller subset is documented as a feasibility trade-off.
- **Sampling Logic**: Adaptive sampling (N=500 -> N=200) ensures the 6-hour hard limit is never breached.

## 4. Statistical Rigor & Limitations

- **Multiple Comparisons**: Addressed via max-statistic permutation testing (1,000 permutations) for the two primary tests. Robustness checks are uncorrected.
- **Power**: Target ≥80% power for r=0.25 (SC-005) with N=500. If sampling reduces N to 200, power will be re-calculated and limitations explicitly stated.
- **Causal Inference**: No causal claims. Observational design acknowledged (FR-008).
- **Measurement Validity**: NIH Toolbox Fluid Intelligence is validated (FR-010).
- **Collinearity**: VIF check and remediation (FR-009) prevent spurious independent effects claims.
- **Dataset-Variable Fit**: Confirmed HCP contains all variables. No mismatch found.
- **Edge Sign Bias**: Addressed via absolute value robustness check.
- **Thresholding Bias**: Addressed via density sensitivity analysis ([deferred], [deferred], [deferred]).

## 5. Decision Log

| Decision | Rationale |
|:--- |:--- |
| **Use Schaefer 200-ROI as Primary** | Standard resolution for HCP studies; balances spatial specificity and signal-to-noise. |
| **Positive Edges Only (Primary)** | Spec requirement (FR-003) to simplify graph interpretation. |
| **Absolute Value (Robustness)** | Checks for bias introduced by discarding negative correlations. |
| **Harmonic Mean Efficiency** | Handles disconnected components caused by positive-edge-only thresholding. |
| **Max-Statistic Permutation (1,000)** | Controls FWE across the two primary tests. [deferred] is the feasible maximum for CI. |
| **Adaptive Sampling (N=500 -> N=200)** | Ensures CI completion within 6 hours if runtime exceeds 4 hours. |
| **Mock Data for CI** | HCP is controlled-access; mock data validates pipeline logic in CI without credentials. |