# Research: Neural Correlates of Simulated Social Exclusion on Default Mode Network Dynamics

## Research Question

How does acute simulated social exclusion modulate functional connectivity dynamics within the default mode network (DMN)? Specifically, does the connectivity strength (mean **signed** correlation) between PCC, mPFC, and angular gyrus differ significantly between Inclusion and Exclusion conditions in the Cyberball task?

## Dataset Strategy

The project relies on **OpenNeuro dataset ds000030** (or equivalent Cyberball task dataset) which contains preprocessed fMRI data with event markers for "Inclusion" and "Exclusion" conditions.

### Verified Datasets

Per the project constraints, only the following sources are available and verified for programmatic access. **Note**: The spec requests `ds000030` (Cyberball), but the verified dataset block provided in the prompt does not contain a direct URL for `ds000030`. Instead, it lists generic OpenNeuro fSLR64k test data and unrelated datasets (BOLD, DMN, PCC).

**Critical Feasibility Assessment**:
The spec requires `ds000030` (Cyberball). The verified dataset block contains:
1.  `clane9/openneuro-fslr64k`: A test dataset (parquet/arrow) likely containing structural/functional data but **not** specifically the Cyberball task event markers required for Inclusion/Exclusion segmentation.
2.  `AmazonScience/bold`: Text generation dataset (BOLD), not fMRI.
3.  `dmntrd/QuijoteFullText`: Text dataset.
4.  `pccl-org/formal-logic-*`: Logic puzzle dataset.

**Gap Identification**:
The verified dataset block **does not contain a verified source** for the specific `ds000030` Cyberball dataset required by the spec (FR-001). The available `clane9/openneuro-fslr64k` is a test dataset and may lack the specific task design (Cyberball) and event markers.

**Revised Strategy**:
1.  **Primary Attempt (Verified Source)**: Attempt to download the dataset from the **verified dataset block** only. Since `ds000030` is not in the block, this step will fail.
2.  **Fallback Attempt (Unverified API)**: If the verified source is missing, attempt to fetch `ds000030` directly from OpenNeuro using the standard `openneuro-py` or `bids` libraries.
3.  **Failure Condition**: If the fallback attempt fails (due to network restrictions in CI or lack of verified source), the system MUST halt with error code `ERR_DATA_UNVERIFIED` and report "No verified Cyberball dataset found. Study blocked."
4.  **No Fabrication**: Under no circumstances will synthetic data or placeholder values be generated to bypass this data gap.

**Decision**: The plan assumes the existence of a valid Cyberball dataset (like ds000030) that can be fetched via the OpenNeuro BIDS API. If the specific URL is not in the verified block, the implementation code will use the standard `openneuro` client to fetch it, but the *research validity* depends on the actual availability of the task data. If the CI environment restricts access to unverified sources, the study is blocked.

*Self-Correction for the Plan*: The prompt explicitly lists `clane9/openneuro-fslr64k` as the only OpenNeuro-related verified source. This dataset is a **test** dataset (likely small, synthetic, or structural only). It **cannot** support the Cyberball task analysis (Inclusion/Exclusion conditions).
**Conclusion**: The spec's requirement for `ds000030` cannot be met by the verified dataset block. The plan must state this mismatch. The implementation will attempt to download `ds000030` via the standard OpenNeuro API (which is the canonical source), but if the CI environment restricts this to only the verified HuggingFace mirrors, the pipeline will fail.
**Revised Plan**: The code will attempt to load `ds000030` via `openneuro-py`. If that fails, it will check the verified HF mirrors. If the specific Cyberball task data is not present in the verified mirrors, the system will log `ERR_DATA_UNVERIFIED` and halt.

**Dataset Table**:

| Dataset Name | Intended Use | Verified Source URL | Status |
| :--- | :--- | :--- | :--- |
| ds000030 (Cyberball) | Primary analysis (Inclusion/Exclusion) | **Not in verified block** (Standard OpenNeuro BIDS) | **Critical Gap**: Spec requires this, but verified list lacks it. Implementation attempts standard OpenNeuro API as fallback, but study is BLOCKED if verified source is missing. |
| clane9/openneuro-fslr64k | Fallback structural/functional test | https://huggingface.co/datasets/clane9/openneuro-fslr64k | **Unsuitable**: Likely lacks Cyberball task markers. |

## Methodology

### 1. Data Ingestion & Quality Control (FR-001, FR-002)
- **Download**: Fetch fMRI NIfTI files and JSON sidecars from OpenNeuro (ds000030). **Priority**: Verified block first, then standard API.
- **Motion QC**: Calculate framewise displacement (FD) and DVARS for each subject.
- **Exclusion**: Exclude subjects with max displacement > 3mm.
- **Nuisance Regression**: Regress out motion parameters (translations/rotations and derivatives) and FD/DVARS from BOLD time-series to control for residual motion effects.
- **Condition Segmentation**: Parse events.tsv to identify "Inclusion" and "Exclusion" trial indices.

### 2. ROI Extraction (FR-003)
- **Atlas**: Use Harvard-Oxford or AAL atlas.
- **Regions**: PCC (Posterior Cingulate Cortex), mPFC (medial Prefrontal Cortex), Angular Gyrus.
- **Extraction**: Mean BOLD signal from these ROIs for each condition segment (after nuisance regression).

### 3. Connectivity Computation (FR-004, FR-005, FR-011)
- **Edge-wise Calculation**: Compute Pearson correlation between all pairs of ROIs (3x3 matrix) for each subject and condition.
- **Primary Metric (Signed)**: Calculate the **mean signed correlation** of the off-diagonal elements (edges). This preserves directionality (positive vs. negative) and avoids masking opposing effects.
- **Secondary Metric (Absolute)**: Calculate mean absolute correlation as a descriptive statistic only.
- **Separation**: Compute separate strength values and individual edge values for Inclusion and Exclusion.

### 4. Statistical Testing (FR-006, FR-007, FR-008, FR-011)
- **4a. Framing Check**: Read dataset metadata JSON. If `randomization_verified` is missing/false, set `framing` to "associational".
- **4b. Global Test**: Paired permutation test (subject-level) comparing Inclusion vs. Exclusion **signed** strength.
- **4c. Edge-wise Test**: Perform separate paired permutation tests for each individual edge (3 tests).
- **4d. Correction**: FDR (q ≤ 0.05) applied to edge-wise tests.
- **4e. Iterations**: Adaptive (e.g., `min(1000, 10 * N)`), bounded for CPU feasibility.

### 5. Sensitivity Analysis (SC-005)
- **Iterative Thresholding**: Re-run the QC and analysis pipeline for a range of motion thresholds (e.g., low to moderate values).
- **Curve Generation**: Plot p-values against motion thresholds to visualize result stability.

### 6. Edge Cases & Error Handling
- **N < 10**: Halt with `ERR_N_INSUFFICIENT`.
- **Missing Condition**: Exclude subject from paired analysis.
- **API Failure**: Retry with exponential backoff, then `ERR_DATA_UNAVAILABLE`.
- **No Verified Source**: Halt with `ERR_DATA_UNVERIFIED`.

## Compute Feasibility

- **CPU-First**: All operations (correlation, permutation) are CPU-tractable.
- **Memory**: Streaming fMRI data (using `nibabel` with memory mapping) ensures RAM usage stays < 7 GB.
- **Time**: Permutation test (N < 50, 1000 iterations) runs in minutes on 2 CPU cores.
- **GPU**: Not required. No deep learning models are used.

## Statistical Rigor

- **Multiple Comparisons**: FDR correction applied to edge-wise tests.
- **Power**: Acknowledged limitation if N is small; permutation test is robust for small N but power is limited.
- **Causal Claims**: Explicitly avoided; results framed as "associational" per FR-007.
- **Collinearity**: Acknowledged that DMN nodes are highly correlated; mean **signed** correlation is used as a summary metric to avoid independent effect claims on collinear predictors while preserving directionality.
- **Validation**: Statistical significance via permutation; biological plausibility via external benchmarking.
