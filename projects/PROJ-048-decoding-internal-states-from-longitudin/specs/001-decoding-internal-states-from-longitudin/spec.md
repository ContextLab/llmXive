# Feature Specification: Decoding Internal States from Longitudinal Calcium Imaging Data

**Feature Branch**: `001-decoding-internal-states`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Decoding Internal States from Longitudinal Calcium Imaging Data"

## User Scenarios & Testing

### User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1)

The researcher needs to automatically download a specific subset of longitudinal calcium imaging data from the Allen Brain Atlas, normalize the fluorescence traces (dF/F), and detrend the signal to prepare it for analysis, ensuring the dataset fits within the 5 GB memory limit of the CI runner.

**Why this priority**: Without a clean, memory-safe dataset, no downstream analysis (NMF or correlation) can occur. This is the foundational step for the entire research workflow.

**Independent Test**: The pipeline can be tested by executing the data loading script on a small sample file and verifying that the output is a normalized NumPy array with no NaN values and a memory footprint ≤ 5 GB.

**Acceptance Scenarios**:

1. **Given** a valid URL for the Allen Brain Atlas Visual Coding dataset subset, **When** the download script executes, **Then** the raw fluorescence traces and behavioral metadata are saved to the local `data/` directory.
2. **Given** raw fluorescence traces, **When** the preprocessing module runs, **Then** the output contains dF/F normalized values and detrended signals with a memory usage ≤ 5 GB.
3. **Given** a dataset exceeding the memory limit, **When** the system attempts to load it, **Then** the system raises a `MemoryExceededError` with a message containing the string "Memory limit exceeded" rather than crashing.

### User Story 2 - Latent State Extraction via NMF (Priority: P2)

The researcher needs to apply Non-negative Matrix Factorization (NMF) to the preprocessed time-by-ROI matrix to extract a set number of latent components (k=10 to 50) and compute their time-varying activation weights, ensuring the method runs on CPU without GPU acceleration.

**Why this priority**: This is the core analytical step that generates the "latent neural states" hypothesized to correlate with behavior. It must be computationally feasible on free-tier CI.

**Independent Test**: The NMF execution can be tested by running the decomposition on a synthetic or small real subset and verifying that the output matrices (components and weights) are non-negative and that the total runtime completes within the 6-hour CI time limit.

**Acceptance Scenarios**:

1. **Given** a preprocessed time-by-ROI matrix, **When** the NMF algorithm is executed with k=10, **Then** the system outputs a components matrix and a weight matrix of matching dimensions.
2. **Given** the NMF execution environment, **When** the job starts, **Then** the process runs exclusively on CPU (no CUDA/GPU calls) and completes within the 6-hour CI time limit.
3. **Given** a range of k values (10, 20, 30), **When** the user requests a sensitivity sweep, **Then** the system generates separate weight matrices for each k value.

### User Story 3 - Behavioral Alignment and Statistical Validation (Priority: P3)

The researcher needs to align the extracted component weights with behavioral metadata (e.g., running speed, stimulus onset) and perform Spearman correlation analysis with a permutation test (1000 iterations) to determine if the correlations are statistically significant (p < 0.05).

**Why this priority**: This validates the scientific hypothesis. Without the permutation test and significance threshold, the correlation results are merely descriptive and do not support the research question.

**Independent Test**: The statistical module can be tested by running it on data where the behavioral metadata is shuffled; the system must report p-values > 0.05 (no significant correlation) for the shuffled data.

**Acceptance Scenarios**:

1. **Given** NMF component weights and aligned behavioral metadata, **When** the correlation analysis runs, **Then** the system calculates Spearman correlation coefficients for each component-behavior pair.
2. **Given** the correlation results, **When** the permutation test (1000 iterations) executes, **Then** the system generates a null distribution and calculates a p-value for each correlation.
3. **Given** a significance threshold of p < 0.05, **When** the results are reported, **Then** the system explicitly flags which component-behavior pairs are statistically significant.

### Edge Cases

- **Missing Data**: If the downloaded dataset contains missing time points or NaN values in the fluorescence traces, the system MUST perform linear interpolation if the missing rate is ≤ 5%; otherwise, the system MUST raise an error.
- **NMF Convergence Failure**: If the NMF convergence fails for a specific k value, the system MUST retry with a different initialization (max 3 retries) or skip that k value, logging the failure.
- **Sampling Rate Mismatch**: If the behavioral metadata has a different sampling rate than the imaging data, the system MUST resample the faster signal to match the slower one using linear interpolation.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download the specific subset of fluorescence traces and behavioral metadata from the Allen Brain Atlas Open Data Portal, ensuring the total dataset size does not exceed 5 GB in memory (≤ 5 GB). (See US-1)
- **FR-002**: System MUST normalize raw fluorescence traces to dF/F, apply a detrending algorithm to remove slow drifts, and perform linear interpolation for missing values if the missing rate is ≤ 5%; otherwise, the system MUST raise an error. (See US-1)
- **FR-003**: System MUST execute Non-negative Matrix Factorization (NMF) on the time-by-ROI matrix to extract k latent components, where k is configurable between 10 and 50. (See US-2)
- **FR-004**: System MUST compute time-varying activation weights for each NMF component and align these weights with the corresponding behavioral metadata timestamps. (See US-2)
- **FR-005**: System MUST perform Spearman correlation analysis between component weights and behavioral metrics, followed by a permutation test with exactly 1000 iterations to establish significance. (See US-3)
- **FR-006**: System MUST report p-values for all correlations and flag those with p < 0.05 as statistically significant. (See US-3)
- **FR-007**: System MUST ensure all computations run on CPU only, explicitly avoiding any GPU/CUDA dependencies. (See US-2)
- **FR-008**: System MUST validate NMF components using a held-out dataset split (e.g., [deferred] training, [deferred] testing) to ensure correlation with behavior is not a tautological artifact of the decomposition. (See US-3)
- **FR-009**: System MUST compare NMF-derived correlations against a null model (linear mixing of behavior) to ensure the identified 'states' are non-trivial and not simply linear artifacts. (See US-3)
- **FR-010**: System MUST apply temporal smoothness regularization (e.g., SparseNMF or ConvNMF) during decomposition to ensure extracted activation weights represent biologically plausible dynamics. (See US-2)
- **FR-011**: System MUST perform deconvolution (e.g., OASIS) on raw fluorescence traces to estimate spike rates before applying NMF, ensuring input reflects neural dynamics rather than indicator kinetics. (See US-2)

### Key Entities

- **FluorescenceTrace**: Represents the time-series signal of a specific Region of Interest (ROI), containing raw intensity and derived dF/F values.
- **LatentComponent**: Represents a row in the NMF components matrix, describing a spatial pattern of neural activity.
- **ComponentWeight**: Represents the time-varying activation strength of a specific LatentComponent over the recording session.
- **BehavioralMetric**: Represents an external variable (e.g., running speed, stimulus onset) aligned temporally with the neural data.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation/research phase.

- **SC-001**: The memory usage of the preprocessing pipeline is measured against the 5 GB limit (≤ 5 GB) to ensure feasibility on the CI runner. (See FR-001)
- **SC-002**: The runtime of the NMF decomposition is measured against the 6-hour CI job limit to ensure the analysis completes without timeout. (See FR-003)
- **SC-003**: The statistical significance of state-behavior correlations is measured against the p < 0.05 threshold derived from the 1000-iteration permutation test. (See FR-005)
- **SC-004**: The stability of NMF components is measured against the cosine similarity of component vectors across different random seeds, requiring a similarity ≥ 0.95. (See FR-003)
- **SC-005**: The alignment accuracy is measured against the temporal resolution of the behavioral metadata, requiring an alignment error ≤ 1 frame. (See FR-004)

## Assumptions

- The Allen Brain Atlas Open Data Portal provides a pre-extracted ROI fluorescence dataset with associated behavioral metadata that is publicly accessible via `wget` without complex authentication.
- The selected subset of the Visual Coding dataset contains sufficient temporal resolution and signal-to-noise ratio to support NMF decomposition.
- The behavioral metadata (e.g., running speed) is sampled at a frequency compatible with the imaging data, or can be reliably resampled without introducing significant artifacts.
- The NMF algorithm implemented in `sklearn` (with regularization extensions) is sufficient to capture the relevant latent neural states without requiring deep learning architectures.
- The "longitudinal" aspect of the data is represented by a single long recording session or a concatenation of sessions that the NMF can process as a continuous time series.
- The permutation test with 1000 iterations will complete within the allocated CI time budget alongside the NMF execution.
- The dataset does not require imputation for missing values beyond simple interpolation; if >5% of data is missing, the analysis will be halted.