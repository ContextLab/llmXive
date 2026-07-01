# Research: Investigating the Impact of Network Structure on Neural Avalanche Dynamics

## 1. Dataset Strategy

The study relies on the **HCP-Aging** dataset, specifically the OpenNeuro subsets **ds004230** (dMRI) and **ds004231** (EEG).

| Dataset | Modality | Source Status | URL / Loader Strategy | Variable Availability Check |
|:--- |:--- |:--- |:--- |:--- |
| **HCP-Aging (dMRI)** | Structural Connectome | **NO verified source found** in the provided list. | Use `openneuro-py` to fetch `ds004230` programmatically. Do NOT invent a URL. | **Required**: Diffusion-weighted images, T1w, parcellation template (HCP 360). **Expected**: Available in HCP-Aging. If missing, the plan halts with a "Data Gap" report. |
| **HCP-Aging (EEG)** | Resting-State EEG | **NO verified source found** in the provided list. | Use `openneuro-py` to fetch `ds004231` programmatically. Do NOT invent a URL. | **Required**: Resting-state EEG, channel locations, sampling rate. **Expected**: Available in HCP-Aging. |
| **OpenNeuro (Generic)** | Reference | Verified | ` | **Note**: This verified dataset is for cortical surface/fslr64k, not the specific dMRI/EEG pair needed. It is **NOT** used for the primary analysis but may serve as a reference for parcellation logic if needed. |

**Critical Mismatch Warning**: The prompt's "Verified datasets" block explicitly states "HCP-Aging: NO verified source found". The implementation MUST NOT fabricate a URL. The strategy is to use the `openneuro-py` library to access the canonical OpenNeuro API for `ds004230` and `ds004231`. If the API fails or the matched sample size is < 50, the study proceeds with the available N and reports power limitations, as per the spec.

**Subject ID Overlap Verification**:
Before processing, the pipeline will query the OpenNeuro API metadata for both datasets to compute the intersection of subject IDs.
- If N < 50: Proceed with available N, log power limitation.
- If N = 0: Halt with "Data Gap: No matched subjects found".

**Sample Size & Power**:
- Target: N=50 matched participants.
- Constraint: If matched N < 50, proceed with available N.
- Power Limitation: Explicitly acknowledged in the final report. No post-hoc power calculation will be used to "fix" low power; the limitation is a primary finding of the feasibility study.

## 2. Methodological Approach

### 2.1 Data Preprocessing
- **dMRI**:
 - Tool: `MRtrix3` (via subprocess).
 - Steps: Denoising, Gibbs ringing removal, bias field correction, response function estimation, multi-tissue constrained spherical deconvolution (CSD), probabilistic tractography (a sufficient number of streamlines per subject to ensure robust connectivity mapping).
 - Parcellation: HCP-MMP mapped to diffusion space.
 - Output: Weighted adjacency matrix (360x360) per subject.
- **EEG**:
 - Tool: `MNE-Python`.
 - Steps: Band-pass filter (1–40 Hz), downsample to a reduced sampling rate consistent with the Nyquist criterion for the target signal bandwidth, as described in [Reference]., ICA for artifact removal (EOG/EMG), bad channel interpolation (if < 30% channels removed).
 - Output: Cleaned time series (channels x time).

### 2.2 Metric Computation
- **Network Metrics** (FR-003):
 - Node Degree: Mean degree of the weighted graph (normalized by max possible weight).
 - Clustering Coefficient: Global clustering coefficient (degree-independent).
 - Rich-Club Coefficient: **Area Under the Curve (AUC)** of the normalized rich-club coefficient (phi(k)) across k > k_min, normalized against a **degree-preserving null model** (randomized graphs with same degree distribution). This avoids trivial correlation with degree distribution.
 - Library: `networkx`.
- **Avalanche Statistics** (FR-004, FR-005):
 - Threshold: 75th percentile amplitude (per-channel, as per spec FR-004).
 - Binning: Fixed Δt = 4 ms (as per spec).
 - **Circularity Mitigation**: Sensitivity analysis will test **absolute** thresholds (fixed amplitude values) to verify if correlations hold regardless of the relative threshold.
 - Detection: Contiguous spatiotemporal events.
 - Distribution Fitting: `powerlaw` package.
 - Validation: KS-test against log-normal and exponential alternatives.
 - Output: Scaling exponents (α) for size and duration.

### 2.3 Statistical Analysis
- **Association** (FR-006, FR-007):
 - Method: Spearman rank correlation (non-parametric, robust to outliers).
 - Uncertainty: **Bootstrap Uncertainty Propagation** (1000 iterations) for confidence intervals. (Deming regression removed due to unmet error variance assumptions).
 - Significance: Permutation test (sufficient shuffles of subject labels) to control family-wise error rate.
- **Robustness** (FR-008):
 - Sensitivity: Repeat avalanche detection at varying thresholds.
 - **Bin Size Sensitivity**: Repeat avalanche detection at bin sizes Δt = 4ms, 8ms, 12ms to assess construct validity of exponents.
 - Metric: Correlation coefficient stability across thresholds and bin sizes.
- **Collinearity** (FR-009):
 - Diagnostic: Variance Inflation Factor (VIF) for degree and clustering coefficient.
 - Interpretation: If VIF > 5, results framed as descriptive; no independent effect claims.

## 3. Compute Feasibility Plan

- **Hardware**: GitHub Actions Free Tier (standard CPU, sufficient RAM, 14 GB disk).
- **Disk-Space Management Strategy**:
 - **Selective Download**: Use `openneuro-py` to download only the specific subjects identified in the overlap check.
 - **Immediate Cleanup**: Delete raw files immediately after preprocessing to free space.
 - **Precision**: Use 16-bit float precision for intermediate arrays where possible.
 - **No GPU**: All operations are CPU-native (`scipy`, `networkx`, `powerlaw`).
 - **Runtime**: Target < 6 hours. If processing a subject takes > 5 mins, the pipeline will skip or downsample.
 - **Memory**: Peak RAM monitored; if > 6 GB, trigger garbage collection or reduce sample size dynamically.

## 4. Risk Assessment

| Risk | Impact | Mitigation |
|:--- |:--- |:--- |
| **Matched N < 50** | High (Power loss) | Proceed with available N; explicitly report power limitation. |
| **Power-law Fit Failure** | Medium | Exclude subject from correlation analysis; report exclusion rate. |
| **Memory Overflow** | High (Job crash) | Implement chunked processing; reduce streamline count; use 16-bit floats; immediate raw file deletion. |
| **Dataset Unavailable** | Critical | Use `openneuro-py` API; if fails, halt with "Data Access Error". |
| **Collinearity** | Medium | Report VIF; frame results as descriptive associations, not independent predictors. |
| **Circularity (Threshold)** | Medium | Sensitivity analysis with absolute thresholds to decouple from global signal magnitude. |

## 5. Decision Log

- **Dataset**: Chose OpenNeuro ds004230/31 (HCP-Aging) as per spec. No verified URL exists in the provided list; programmatic access is the only valid path.
- **Threshold**: 75th percentile chosen as standard; sensitivity analysis added for robustness and to address circularity concerns.
- **Correlation**: Spearman chosen over Pearson due to non-normal distribution of network metrics and avalanche exponents.
- **Uncertainty**: Bootstrap chosen over Deming regression due to non-Gaussian error structure of power-law exponents.
- **Permutation**: 1000 shuffles chosen as the minimum for stable p-value estimation within 6-hour runtime.
- **Rich-Club**: AUC of normalized coefficient chosen to capture topological nuance and avoid trivial correlation with degree.