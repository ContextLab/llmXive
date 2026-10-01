# Feature Specification: llmXive follow-up: extending "LocateAnything: Fast and High-Quality Vision-Language Grounding with P"

**Feature Branch**: `001-llmxive-followup`  
**Created**: 2026-09-19  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'LocateAnything: Fast and High-Quality Vision-Language Grounding with P'"

## User Scenarios & Testing

### User Story 1 - Quantify Geometric Coherence Degradation under Attention Sparsity (Priority: P1)

**User Journey**: A researcher configures a vision-language grounding model to run with restricted attention windows (simulating edge-device constraints) and executes an inference pass on a dataset of dense, cluttered scenes to measure the resulting drop in bounding box accuracy compared to global attention.

**Why this priority**: This is the core scientific objective. Without establishing the baseline relationship between attention sparsity and geometric coherence (mIoU), no further analysis of feature importance or tipping points is possible. It directly addresses the "What is NOT known" gap regarding the causal impact of attention sparsification.

**Independent Test**: The system can be tested by running a single inference job on a fixed subset of dense images with a specific sparsity mask (e.g., 32-patch window) and comparing the output bounding boxes against ground truth to calculate mIoU. Success is defined by the ability to produce a valid mIoU score for the restricted configuration.

**Acceptance Scenarios**:
1. **Given** a pre-loaded LocateAnything-based model and a dense-scene image subset (≥5 overlapping boxes), **When** the inference engine applies a local-only attention mask (e.g., 32-patch window), **Then** the system outputs predicted bounding boxes and calculates a mean Intersection-over-Union (mIoU) score that is numerically lower than the global-attention baseline.
2. **Given** the same dense-scene subset, **When** the inference engine applies a global attention mask, **Then** the system outputs predicted bounding boxes and calculates a baseline mIoU score that serves as the control for comparison.

### User Story 2 - Identify the "Tipping Point" for Ambiguity Resolution (Priority: P2)

**User Journey**: A researcher iteratively adjusts the attention window size (from global down to local-only) across a grid of sparsity levels to pinpoint the specific threshold where the model fails to resolve geometric ambiguities in overlapping objects, distinguishing between dense and non-dense scenes.

**Why this priority**: This refines the P1 finding into an actionable design constraint. It moves from "it gets worse" to "it gets worse at X," enabling the definition of minimum hardware requirements for specific accuracy targets.

**Independent Test**: The system is tested by executing a batch of inference runs across a defined grid of attention window sizes (e.g., Global, 64, 32, 16 patches) and plotting the mIoU degradation curve. Success is defined by identifying a non-linear drop or "knee" in the curve where the ambiguity resolution rate falls below a specific threshold.

**Acceptance Scenarios**:
1. **Given** a sequence of sparsity configurations (Global, 64, 32, 16 patches), **When** the system processes the dense-scene subset, **Then** it generates a dataset of mIoU scores per configuration that reveals a non-linear degradation pattern.
2. **Given** the calculated mIoU scores, **When** the system compares the performance on images with overlapping objects versus non-overlapping objects, **Then** it reports a statistically significant difference in degradation rates (p < 0.05 via repeated-measures ANOVA) indicating that dense scenes are disproportionately affected by sparsity.

### User Story 3 - Attribute Failure Modes to Structural Visual Features (Priority: P3)

**User Journey**: A researcher uses gradient-based attribution methods (e.g., Grad-CAM or attention rollout) on the model's failure cases (from P2) to determine which visual features (texture, edges, global tokens) the model relied on, and how this reliance shifts as global context is removed.

**Why this priority**: This explains *why* the degradation occurs (P2), fulfilling the research question's second part about "specific structural features." It provides the theoretical basis for future architectural improvements.

**Independent Test**: The system is tested by selecting a set of images where the model failed under local attention but succeeded under global attention, running an attribution algorithm, and visualizing the activation maps. Success is defined by the ability to generate and save these attribution maps showing a shift in focus from global context tokens to local texture/edges.

**Acceptance Scenarios**:
1. **Given** a set of "failure" images (high overlap, local attention), **When** the system applies Grad-CAM or attention rollout, **Then** it produces heatmaps indicating that the model's predictions rely heavily on local texture gradients rather than long-range dependency markers.
2. **Given** a set of "success" images (high overlap, global attention), **When** the system applies the same attribution method, **Then** the heatmaps show significant activation on global context tokens that are absent in the local-attention failure cases.

### Edge Cases

- **What happens when** the image density is too low (no overlapping objects)? The system must still process the image but should not report an "ambiguity resolution failure" metric, as the condition for ambiguity is not met.
- **How does the system handle** images where the ground-truth bounding boxes are themselves ambiguous or poorly annotated? The system must flag these samples and exclude them from the mIoU calculation to prevent skewing the "tipping point" analysis.
- **What happens when** the attention window size is set to 1 (single patch)? The system must handle the edge case where no context exists, likely resulting in near-random predictions, and record this as the lower bound of the degradation curve.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST implement a parameterized "sparsity knob" that dynamically restricts the attention window size (ranging from global to local-only) and masks global context tokens during inference (See US-1).
- **FR-002**: The system MUST calculate the mean Intersection-over-Union (mIoU) for predicted bounding boxes against ground-truth annotations for every inference run across all sparsity levels (See US-1).
- **FR-003**: The system MUST filter the input dataset to ensure a minimum density of ≥5 overlapping bounding boxes per image for the "dense scene" subset (See US-2).
- **FR-004**: The system MUST execute a repeated-measures ANOVA to determine if the reduction in global context significantly impacts mIoU in dense scenes compared to sparse scenes (See US-2).
- **FR-005**: The system MUST implement gradient-based attribution (e.g., Grad-CAM or attention rollout) to generate visual heatmaps of feature importance for selected failure cases (See US-3).
- **FR-006**: The system MUST enforce a CPU-only execution mode with `torch.set_num_threads(2)` and memory-mapped loading to ensure compatibility with the 2-core/7GB RAM constraint (See US-1).

### Key Entities

- **Sparsity Configuration**: An object defining the attention window size (e.g., 32 patches) and the specific mask pattern applied to the transformer layers.
- **Dense Scene Sample**: An image from the dataset containing ≥5 overlapping bounding boxes, used specifically to test geometric ambiguity resolution.
- **Attribution Map**: A visual representation of the model's internal attention weights or gradients, highlighting which image regions influenced the prediction.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The degradation in mIoU as attention window size decreases is measured against the global-attention baseline to identify the specific "tipping point" where geometric ambiguity resolution fails (See US-1, US-2).
- **SC-002**: The statistical significance of the difference in mIoU degradation between dense and non-dense scenes is measured against a p-value threshold of 0.05 using repeated-measures ANOVA (See US-2).
- **SC-003**: The correlation between attention window size and ambiguity resolution rate is measured against a defined set of sparsity levels (Global, 64, 32, 16) to establish the non-linear relationship (See US-2).
- **SC-004**: The reliance on long-range dependencies versus local features is measured by comparing the spatial distribution of activation in Grad-CAM/attention rollout maps between successful global-attention runs and failed local-attention runs (See US-3).
- **SC-005**: The total inference latency per image is measured against a maximum bound of 6 hours for the entire batch run on a 2-core CPU to ensure feasibility (See US-1).

## Assumptions

- **Dataset Variable Fit**: It is assumed that the VRSBench validation split and the curated COCO/RefCOCO+ subset contain sufficient ground-truth bounding box annotations to accurately calculate mIoU for overlapping objects. [NEEDS CLARIFICATION: Does the specific RefCOCO+ split used contain explicit annotations for overlapping objects, or must this be programmatically derived from spatial overlap of existing boxes?]
- **Inference Framing**: The study is observational; findings regarding the "impact" of attention sparsity are framed as associational relationships between configuration and performance, not causal claims about architectural superiority, due to the lack of random assignment in the dataset generation.
- **Threshold Justification**: The grid of sparsity levels (Global, 64, 32, 16) is selected based on common architectural window sizes in efficient attention literature. A sensitivity analysis will sweep the window size by ±8 patches around the identified "tipping point" to ensure the result is robust to small parameter changes.
- **Compute Feasibility**: The analysis assumes that the selected model architecture (LocateAnything variant) can be run in default precision (FP32) on a 2-core CPU without requiring 8-bit quantization or GPU acceleration. If memory pressure exceeds 7GB, the dataset will be sampled to fit.
- **Measurement Validity**: The mIoU metric is assumed to be a valid proxy for "geometric coherence" in this context, as it directly measures the spatial alignment of predicted boxes against ground truth.
- **Predictor Collinearity**: Since "attention window size" and "global context tokens" are definitionally linked (reducing the window reduces global tokens), the analysis will treat them as a single joint predictor rather than claiming independent effects for each.
