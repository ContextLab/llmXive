# Feature Specification: llmXive follow-up: extending "OrbitQuant: Data-Agnostic Quantization for Image and Video Diffusion T"

**Feature Branch**: `001-llmxive-followup`  
**Created**: 2026-09-19  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'OrbitQuant: Data-Agnostic Quantization for Image and Video Diffusion T'"

## User Scenarios & Testing

### User Story 1 - Establish Correlation between Prompt Entropy and Activation Variance (Priority: P1)

**Description**: The researcher must be able to compute semantic entropy for a diverse set of text prompts and measure the corresponding variance of intermediate activation distributions in a Diffusion Transformer (DiT) to empirically determine if a correlation exists. This is the foundational hypothesis test; without this data, the dynamic router cannot be justified.

**Why this priority**: This addresses the core research question. If no correlation exists, the subsequent engineering effort to build a dynamic router is unnecessary. This is the primary scientific contribution of the study.

**Independent Test**: Can be fully tested by running the correlation analysis pipeline on the MS-COCO validation set with a curated set of prompts, outputting a correlation coefficient and p-value., without implementing any rotation selection logic. Execution requires either a GPU-enabled environment for float32 forward passes on large models (FLUX.1-dev, Wan 2.1) or a fallback to a CPU-feasible DiT variant (e.g., Stable Diffusion 2.1) if GPU is unavailable.

**Acceptance Scenarios**:
1. **Given** a dataset of 200 diverse text prompts and the MS-COCO 2017 validation set (500 images) with a pre-trained DiT model (FLUX.1-dev, Wan 2.1, or Stable Diffusion 2.1), **When** the system computes semantic entropy for each prompt and records the variance of intermediate activation layers during a float32 forward pass, **Then** the system outputs a Pearson correlation coefficient and a p-value indicating the statistical significance of the relationship.
2. **Given** the computed correlation data, **When** the researcher visualizes the relationship (e.g., scatter plot of entropy vs. variance), **Then** the plot clearly shows the distribution of points and allows for visual inspection of the trend.

### User Story 2 - Implement Dynamic Rotation Router based on Entropy (Priority: P2)

**Description**: The system must implement a lightweight router that maps a prompt's semantic entropy score to a specific pre-optimized rotation matrix from a set of $K=16$ candidates. This router replaces the static rotation basis used in the original OrbitQuant method for the inference of new prompts. The router logic is derived from a **Training Phase** where unquantized activation variances are clustered to create a lookup table, and an **Inference Phase** where the table is queried.

**Why this priority**: This is the proposed solution to the problem identified in User Story 1. It represents the "dynamic adaptation" mechanism that aims to reduce quantization error for high-entropy inputs while maintaining the data-agnostic efficiency of the baseline.

**Independent Test**: Can be fully tested by feeding a prompt with a known entropy score into the router and verifying that the correct rotation matrix index is selected from the pre-computed lookup table and applied to the activation tensors during a forward pass, independent of the final image quality metrics.

**Acceptance Scenarios**:
1. **Given** a pre-computed set of 16 rotation matrices and a prompt with a calculated semantic entropy of $E$, **When** the router processes $E$ against the pre-computed lookup table (derived from clustering MS-COCO activation histograms), **Then** the system selects the rotation matrix $M_i$ corresponding to the entropy bin containing $E$.
2. **Given** the selected rotation matrix, **When** the DiT performs a forward pass on a sample image, **Then** the activation tensors are rotated using $M_i$ instead of the static OrbitQuant basis, and the quantization (W2A4) is applied correctly.

### User Story 3 - Evaluate Fidelity Gains and Runtime Overhead (Priority: P3)

**Description**: The system must compare the generated images from the dynamic router method against the static OrbitQuant baseline using perceptual metrics (FID, CLIP score) and measure the wall-clock inference time to ensure the adaptive method does not introduce significant latency.

**Why this priority**: This validates the practical utility of the solution. Even if the correlation exists and the router works, the method is only viable if it improves generation quality (FID/CLIP) without breaking the efficiency constraints (runtime overhead < 2%).

**Independent Test**: Can be fully tested by running both the static baseline and the dynamic router on the same set of prompts., generating images, computing metrics, and calculating the percentage increase in inference time.

**Acceptance Scenarios**:
1. **Given** a set of 200 prompts and their corresponding generated images from both the static baseline and the dynamic router, **When** the system computes FID, CLIP scores, and Mean Squared Error (MSE) quantization error, **Then** the system outputs the metric distributions and the p-values from the statistical tests for the researcher to analyze.
2. **Given** the inference logs for both methods, **When** the system calculates the average wall-clock time per image, **Then** the dynamic router's overhead is ≤ 2% compared to the static baseline.

### Edge Cases

- **Entropy Out-of-Range**: What happens when a prompt's semantic entropy falls outside the range covered by the 16 pre-optimized rotation matrices (e.g., extremely low or extremely high)? The system MUST clamp the entropy value to the nearest boundary and select the corresponding matrix (index 0 for min, index 15 for max) based on absolute scalar distance.
- **Activation Outliers**: How does the system handle prompts that result in activation variances that are outliers relative to the training distribution of the rotation matrices? The system MUST log these instances for potential future re-clustering and default to the median rotation matrix.
- **Proxy Failure**: What happens if the lightweight language model proxy fails to compute semantic entropy for a specific prompt (e.g., timeout or error)? The system MUST fall back to the static OrbitQuant rotation (the median index) for that specific prompt to ensure pipeline continuity..

## Requirements

### Functional Requirements

- **FR-001**: System MUST compute semantic entropy for each input prompt using a lightweight language model proxy and a sampling-based estimation method (See US-1).
- **FR-002**: System MUST measure the variance of intermediate activation layers in a pre-trained Diffusion Transformer during a float32 forward pass (See US-1).
- **FR-003**: System MUST generate and store $K=16$ pre-optimized rotation matrices derived from clustering activation histograms of the MS-COCO 2017 validation set (See US-2).
- **FR-004**: System MUST implement a router module that maps a prompt's semantic entropy score to the index of the most appropriate pre-optimized rotation matrix using a pre-computed lookup table (See US-2).
- **FR-005**: System MUST apply the selected rotation matrix to activation tensors during the quantization process (W2A4) before the layer output (See US-2).
- **FR-006**: System MUST compute FID and CLIP scores for generated images using CPU-compatible implementations (See US-3).
- **FR-007**: System MUST measure and record the wall-clock inference time for both the static baseline and the dynamic router methods (See US-3).
- **FR-008**: System MUST perform a paired t-test to compare metric distributions between the dynamic and static methods with a significance threshold of p < 0.05 (See US-3).
- **FR-009**: System MUST compute Mean Squared Error (MSE) quantization error on a subset of activations to validate the assumption that activation variance correlates with quantization sensitivity (See US-1, US-3).

### Key Entities

- **Prompt**: The text input driving the generation, characterized by its semantic entropy score.
- **Activation Variance**: The statistical variance of intermediate tensor values within the DiT layers during inference, measured on the float32 pass.
- **Rotation Matrix**: A $K=16$ set of pre-computed orthogonal matrices derived from clustering activation histograms of the MS-COCO 2017 validation set, used to rotate activation distributions for quantization.
- **Router**: The logic component that selects the rotation matrix based on the prompt's entropy via a pre-computed lookup table.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The correlation coefficient between prompt semantic entropy and activation variance is measured against a null hypothesis of zero correlation (See US-1).
- **SC-002**: The reduction in quantization error (measured via MSE, FID, and CLIP score improvements) for high-entropy prompts is measured against the static OrbitQuant baseline (See US-3).
- **SC-003**: The inference runtime overhead of the dynamic router is measured against the static baseline, with a target of ≤ 2% (See US-3).
- **SC-004**: The statistical significance of the performance improvement is measured using a paired t-test with a threshold of p < 0.05 (See US-3).
- **SC-005**: The sensitivity of the rotation selection is measured by sweeping the entropy cut-off points by ±5% of the total observed entropy range and reporting the variance in FID scores (See US-2).

## Assumptions

- **Dataset Availability**: The MS-COCO validation set and diverse text prompts from public repositories (e.g., HuggingFace) are available and sufficient to represent the distribution of real-world inputs for correlation analysis.
- **Compute Constraints**: The analysis requires a GPU-enabled environment for float32 forward passes on large models (FLUX.1-dev, Wan 2.1). If GPU is unavailable, the system MUST default to a CPU-feasible DiT variant (e.g., Stable Diffusion 2.1) for the float32 pass. Lightweight entropy proxy and metric computation remain CPU-bound.
- **Model Access**: Pre-trained DiT models (FLUX.1-dev, Wan 2.1, Stable Diffusion 2.1) are accessible and can be loaded into memory for the purpose of measuring activation variance.
- **Semantic Entropy Proxy**: A lightweight language model proxy (e.g., a small transformer or LLM with <1B parameters) is sufficient to estimate semantic entropy with enough fidelity to distinguish between low and high complexity prompts for the purpose of this study.
- **Rotation Matrix Generation**: Clustering activation histograms from the MS-COCO 2017 validation set yields $K=16$ distinct regimes that adequately cover the variance spectrum induced by the target prompt distribution.
- **Methodological Framing**: The relationship between prompt entropy and activation variance is treated as associational; no causal claims are made regarding the effect of entropy on model geometry, only the statistical correlation.
- **Threshold Justification**: The selection of $K=16$ rotation matrices is based on a trade-off between granularity and computational overhead, justified by the diminishing returns of clustering beyond this number in similar quantization studies.
- **Sensitivity Analysis**: The router's decision boundaries (entropy thresholds) will be swept over a range of minor variations (±5% of total range) to ensure the performance gains are robust to minor variations in entropy estimation.
- **Collinearity**: If multiple activation layers are analyzed, their variances are assumed to be correlated but not definitionally identical, requiring a collinearity diagnostic before claiming independent predictive effects.
- **Multiplicity Correction**: Given the multiple hypothesis tests (FID, CLIP, runtime, MSE), a family-wise error correction (e.g., Bonferroni) will be applied if the number of comparisons is substantial..
- **Variance-Sensitivity Hypothesis**: It is hypothesized that higher activation variance in the unquantized (float32) pass correlates with higher sensitivity to quantization error in the W2A4 regime, justifying the use of variance as a proxy for selecting rotation matrices.