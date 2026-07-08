# Research: Investigating the Relationship Between Brain Network Dynamics and Anticipatory Reward Processing

## 1. Research Question & Hypothesis

**Primary Question**: Is there an associational relationship between resting-state brain network flexibility (dynamic functional connectivity) and the magnitude of ventral striatum activation during reward anticipation?

**Hypothesis**: Higher network flexibility (frequent state switching) in resting-state networks is associated with greater ventral striatum activation during reward anticipation.

**Inference Type**: Observational/Associational. The study design does not involve random assignment or intervention. Results will be framed strictly as associations, not causal effects, in compliance with **FR-007** and **Assumption** (inference).

## 2. Dataset Strategy

### 2.1 Verified Datasets
The following datasets have been verified for availability and format. **Only these sources are used.**

| Dataset Name | Description | Verified URL | Usage in Plan |
|--------------|-------------|--------------|---------------|
| OpenNeuro ds001734 | Human Connectome Project (HCP) 1200 Subjects Release. Contains raw resting-state and task-fMRI (Monetary Incentive Delay) NIfTI files in BIDS format. | https://openneuro.org/datasets/ds001734 | **Primary Source**: Downloaded to `data/raw/`. Provides NIfTI files for both resting-state and task-fMRI for a cohort of subjects. |
| Power 264 Atlas | Standard atlas for functional connectivity analysis. | https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3060359/ | **Atlas Definition**: Coordinates used for node extraction. |
| HCP MNI Space | Reference space for HCP data (MNI152NLin2009cAsym). | | **Space Reference**: Confirms alignment with Power 264 coordinates. |

### 2.2 Dataset-Variable Fit Analysis
**Required Variables**:
1. **Resting-state fMRI**: Needed for dynamic connectivity (FR-003).
2. **Task-fMRI (Reward Paradigm)**: Needed for ventral striatum activation (FR-005).
3. **Subject ID & Session ID**: Needed to ensure distinct sessions (FR-008).
4. **Atlas Coordinates**: Power 264 nodes and Ventral Striatum ROI (MNI space).

**Fit Confirmation**:
- The **OpenNeuro ds001734** dataset is the canonical, verified source for the HCP S1200 release, containing both resting-state (`rfMRI`) and task-fMRI (`tfMRI`) NIfTI files in BIDS format.
- **Critical Check**: The plan verifies that the dataset contains both modalities for the same subjects. The ingestion script will scan the BIDS directory structure to confirm the presence of both `rfMRI` and `tfMRI` sessions for each subject ID. If a subject lacks either, they are skipped. If <50 valid subjects remain, the pipeline fails (FR-010).
- **Space Alignment**: The HCP data in OpenNeuro ds001734 is provided in MNI152NLin2009cAsym space. The Power 264 atlas coordinates are also defined in MNI space. A validation step in Phase 0 will confirm the coordinate systems match to prevent misalignment errors.

### 2.3 Data Access & Constraints
- **Access**: Public OpenNeuro data (no credentials required).
- **Volume**: 50 subjects. Assuming A substantial number of volumes per run and A substantial number of voxels (downsampled or masked), raw NIfTI size per subject is in the range of hundreds of megabytes.. Total ~GB raw.
- **Constraint**: Must fit in a disk and RAM footprint suitable for the target hardware constraints.
- **Strategy**:
 - Download only necessary files (resting and task NIfTI) using `bids` or `requests`.
 - Process subjects one-by-one or in small batches to keep RAM < 7GB.
 - Extract time series immediately and discard raw NIfTI to save disk space (or keep raw in `data/raw/` if disk permits, but delete after extraction if tight).
 - Use memory-mapped arrays (`nibabel` + `numpy`) to avoid loading entire volumes into RAM.

## 3. Methodology & Statistical Rigor

### 3.1 Dynamic Functional Connectivity (dFC) & Flexibility
- **Method**: Sliding window correlation followed by K-means clustering.
- **Parameters**:
 - Window Size: TRs (FR-003). **TR Verification**: The plan will confirm the TR of the downloaded data (expected ~s for HCP). TRs * TR_duration = ~21.6s, which is appropriate for capturing slow fluctuations. If TR differs, the window size in TRs will be adjusted to maintain ~21.6s.
 - Step Size: 1 TR.
 - Clustering: K-means (K=4), K-means++ init, seed=42 (FR-003a).
 - Atlas: Power 264 (nodes excluding VS) + VS ROI.
- **Metric**: Flexibility = (Number of state transitions) / (Actual number of windows for that subject).
 - **Normalization**: This rate-based metric accounts for varying scan lengths across subjects, ensuring the score reflects switching frequency rather than total scan duration.
- **Statistical Rigor**:
 - **Determinism**: Fixed seed (42) ensures reproducibility (Constitution I).
 - **Collinearity**: The VS ROI is excluded from the Power 264 nodes used for dFC to prevent double-dipping (Assumption). The flexibility score is derived from the *resting* network, while the outcome is *task* activation. These are distinct measures.
 - **Validity**: Power 264 is a standard, validated atlas for network analysis.

### 3.2 Correlation & Significance Testing
- **Method**: Pearson correlation between Flexibility Score and Ventral Striatum Activation.
- **Activation Metric**: Mean beta value from the first-level GLM contrast (Reward > Neutral) averaged across the bilateral Ventral Striatum ROI. This approach accounts for temporal autocorrelation and HRF dynamics inherent in fMRI, providing a robust summary statistic per subject.
- **Significance**: Permutation test (iterations) (FR-006).
- **Statistical Rigor**:
 - **Multiple Comparisons**: The sensitivity analysis (FR-009) acts as a robustness check against window size choice, mitigating the risk of overfitting to a single parameter.
 - **Causal Assumption**: Explicitly avoided. The plan frames results as "associational" (FR-007). No randomization exists.
 - **Sample Size**: 50 subjects. Power is likely low for small effects. The plan will report the effect size (r) and the empirical p-value, acknowledging the limitation if the p-value is marginal.
 - **Zero Variance**: Subjects with constant flexibility (0 variance) will be excluded (Edge Case logic) to avoid undefined statistics.

### 3.3 Sensitivity Analysis
- **Requirement**: Repeat correlation for window sizes, 30, 40 TRs (FR-009).
- **Rationale**: To demonstrate that the observed association is robust to the choice of sliding window length, addressing the sensitivity of dFC metrics to this parameter.

## 4. Computational Feasibility

- **Hardware**: GitHub Actions Free Tier (limited CPU resources, 7 GB RAM, no GPU).
- **Library Selection**:
 - `numpy`, `scipy`, `scikit-learn`: CPU-optimized, standard for this analysis.
 - `nibabel`: Efficient for NIfTI I/O (memory mapping).
 - `pandas`: For data manipulation.
 - `bids`: For parsing OpenNeuro structure.
 - **Avoid**: `torch`, `tensorflow`, `bitsandbytes` (require GPU/CUDA).
- **Runtime Estimate**:
 - 50 subjects.
 - Per subject: Extract time series (short duration), Sliding window + K-means (moderate duration), Correlation (negligible).
 - Total: ~50 * 4 min = 200 minutes ([deferred]).
 - **Buffer**: Well within the time limit.
- **Memory**:
 - Streaming processing (one subject at a time) ensures RAM usage is dominated by a single subject's data (order of magnitude of hundreds of megabytes), well under 7 GB.

## 5. Decision Log

| Decision | Rationale |
|----------|-----------|
| **Use OpenNeuro ds001734** | Canonical, verified source for HCP NIfTI data. Avoids unreliable mirrors. |
| **Seed=42** | Ensures reproducibility (Constitution I). |
| **K=4 States** | Specified in FR-003a; standard for small-scale dFC. |
| **Permutation Test** | Non-parametric, robust for small N=50 (FR-006). |
| **Sensitivity Analysis** | Addresses parameter uncertainty (FR-009). |
| **Associational Framing** | Mandatory for observational data (FR-007, Assumption). |
| **Memory Mapping** | Essential to fit 50 subjects in 7 GB RAM. |
| **Bilateral VS Activation** | Standard approach for small subcortical ROIs to maximize signal-to-noise. |
| **Scan-Length Normalization** | Ensures flexibility is a rate, not a function of scan duration. |
| **TR Verification** | Ensures physiological validity of the sliding window. |
