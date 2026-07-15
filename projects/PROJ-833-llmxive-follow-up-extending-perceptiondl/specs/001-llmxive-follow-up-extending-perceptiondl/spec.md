# Feature Specification: llmXive Follow-up: Extending PerceptionDLM Parallel Region Perception

**Feature Branch**: `001-llmxive-perceptiondlm-overflow`  
**Created**: 2026-07-12  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'PerceptionDLM: Parallel Region Perception with Multimodal Diffusion La'"

## User Scenarios & Testing

### User Story 1 - Parallel vs. Sequential Coherence Degradation Analysis (Priority: P1)

The researcher needs to run the core comparative experiment where the PerceptionDLM model processes images with multiple regions in parallel batches (simulating context overflow) and compare the semantic coherence of the output against a sequential autoregressive baseline. This is the primary research question: determining if and how coherence degrades non-linearly as region count exceeds the native context window.

**Why this priority**: This addresses the central hypothesis of the project (the "coherence tax"). Without this data, the project cannot validate or refute the claim of non-linear degradation. It is the minimum viable product for the research inquiry.

**Independent Test**: The system can be tested by executing the analysis pipeline on a single synthetic image with multiple regions, generating both parallel and sequential outputs, and computing the Semantic Coherence Score, BLEU-4, and the degradation curve. If the scores are generated and the degradation curve can be plotted, the core functionality is valid.

**Acceptance Scenarios**:

1. **Given** a synthetic image with 30 non-overlapping bounding masks, **When** the system runs the parallel batched inference (batch size 8) and the sequential baseline inference (processing all 30 regions sequentially), **Then** the system must output two distinct JSON files containing the generated captions, the calculated Semantic Coherence Score, and the BLEU-4 score for each method.
2. **Given** the generated JSON files, **When** the regression analysis script is executed, **Then** the system must produce a CSV file containing the region count, parallel coherence score, sequential coherence score, and parallel/sequential BLEU-4 scores, enabling the plotting of the degradation curve.

---

### User Story 2 - Synthetic Overflow Dataset Generation (Priority: P2)

The researcher needs a mechanism to programmatically synthesize "overflow" test cases by randomly placing 20–50 non-overlapping bounding masks on images from the ParaDLC-Bench dataset. The current dataset may not naturally contain enough regions per image to test the overflow hypothesis, necessitating synthetic augmentation.

**Why this priority**: This is a prerequisite for User Story 1. Without a dataset that explicitly exceeds the 8–16 region native context window, the degradation analysis cannot be performed. It enables the specific stress-testing required by the research question.

**Independent Test**: The system can be tested by running the dataset generation script on a small subset of images and verifying that the output contains images with exactly 20, 30, and 50 bounding boxes respectively, and that no boxes overlap.

**Acceptance Scenarios**:

1. **Given** a source image from the ParaDLC-Bench dataset, **When** the synthesis script is run with a target region count of 40, **Then** the system must generate a new image file with 40 non-overlapping bounding masks and a corresponding JSON annotation file listing their coordinates.
2. **Given** the generated annotation file, **When** the overlap validation script is executed, **Then** the system must return a boolean `true` indicating zero overlaps between any pair of bounding boxes.

---

### User Story 3 - Pareto Frontier Visualization and Tipping Point Identification (Priority: P3)

The researcher needs to visualize the trade-off between inference time (speed) and semantic coherence (quality) to identify the "tipping point" where the efficiency of parallelism is outweighed by the loss of coherence. This visualization is required to support the final conclusions and paper figures.

**Why this priority**: While the raw data (US-1) is sufficient for the scientific claim, the visualization is necessary for the "Expected Results" deliverable and for communicating the "coherence tax" concept clearly. It is the final step in the research workflow.

**Independent Test**: The system can be tested by running the plotting script on the CSV output from User Story 1. If the script generates a PNG file showing the Pareto frontier with the identified tipping point marked, the feature is complete.

**Acceptance Scenarios**:

1. **Given** the regression analysis CSV file containing time and coherence metrics, **When** the visualization script is executed, **Then** the system must generate a PNG plot showing Inference Time (x-axis) vs. Semantic Coherence Score (y-axis) with distinct lines for Parallel and Sequential methods.
2. **Given** the generated plot, **When** the researcher inspects the curve, **Then** the system must clearly mark the "tipping point" (the region count where the parallel method's coherence drops below [deferred] of the sequential baseline score).

---

### Edge Cases

- What happens when the synthetic placement algorithm fails to fit the requested number of non-overlapping boxes on a small image? The system must retry with a reduced region count or report a specific failure for that image, ensuring the dataset does not contain corrupted entries.
- How does the system handle images where the ground-truth annotations are missing for specific regions? The system must skip those regions in the coherence calculation or flag the sample as invalid to prevent skewed metrics.
- What if the HuggingFace `diffusers` library fails to load on the CPU-only runner due to missing dependencies? The system must fail gracefully with a clear error message indicating the missing dependency, rather than crashing silently.

## Requirements

### Functional Requirements

- **FR-001**: System MUST generate synthetic test images with 20–50 non-overlapping bounding boxes derived from the ParaDLC-Bench dataset to simulate context overflow (See US-2).
- **FR-002**: System MUST execute the PerceptionDLM model in a parallel batched mode (batch size 8) without cross-batch context to simulate fragmented global view (See US-1).
- **FR-003**: System MUST execute a sequential autoregressive baseline using a standard Transformer-based MLLM (e.g., LLaVA) via HuggingFace on CPU for the same input images (processing all regions sequentially) to establish the "Sequential Overflow" ground-truth quality (See US-1).
- **FR-004**: System MUST calculate a "Semantic Coherence Score" by extracting all spatial prepositional phrases indicating relations (e.g., "to the left of") using spaCy from generated captions, comparing them against ground-truth relations derived from bounding box centroids, and computing the score as (matches / total_relations) (See US-1).
- **FR-005**: System MUST perform regression analysis to model the relationship between region count and Semantic Coherence Score, comparing the degradation slope between parallel and sequential methods (See US-1).
- **FR-006**: System MUST generate a Pareto frontier plot visualizing inference time versus semantic coherence to identify the tipping point (See US-3).
- **FR-007**: System MUST run the entire analysis pipeline on a CPU-only environment where Peak RSS measured via `/proc/self/status` during the longest inference step must not exceed 7 GB RAM and disk usage must not exceed 14 GB (See Assumptions).
- **FR-008**: System MUST calculate BLEU-4 scores for both parallel and sequential outputs to provide a standard n-gram baseline metric (See US-1).

### Key Entities

- **SyntheticImage**: An image file augmented with a set of non-overlapping bounding boxes and corresponding ground-truth annotations.
- **CoherenceMetric**: A numerical score derived from the consistency of relational terms in generated captions against ground-truth relationships.
- **DegradationCurve**: A dataset mapping region count to coherence scores for both parallel and sequential inference modes.

## Success Criteria

- **SC-001**: The Semantic Coherence Score is measured against the geometrically derived ground-truth relational annotations to quantify the loss of structural dependencies (See US-1).
- **SC-002**: The degradation pattern (linear vs. non-linear) is measured by comparing the regression slope of the parallel method against the sequential baseline (See US-1).
- **SC-003**: The "coherence tax" tipping point is identified as the specific region count N where the parallel method's coherence score drops below [deferred] (0.9) of the sequential baseline score (See US-3).
- **SC-004**: The inference time is measured against the sequential baseline to quantify the speedup efficiency at varying region counts (See US-3).
- **SC-005**: The analysis is completed within 6 hours on a standard CPU-only CI runner without GPU acceleration (See Assumptions).

## Assumptions

- **Assumption about data**: The ParaDLC-Bench dataset is available and accessible via the HuggingFace repository, and the ground-truth annotations contain sufficient relational data to compute the Semantic Coherence Score. If the dataset only provides bounding boxes without relational labels, the system MUST generate synthetic relational ground-truth based on the geometric centroids of the bounding boxes (e.g., deriving "left of", "above" from coordinate comparisons) to ensure the metric calculation is computable. This synthetic derivation is validated by ensuring the generated relationships match the geometric reality of the synthetic image layout. In this context, the "Semantic Coherence Score" measures "Geometric Consistency" (the ability to describe the input layout), which serves as a necessary lower-bound proxy for semantic coherence when human labels are absent (See US-2 for synthetic generation guarantees).
- **Assumption about compute**: The entire analysis (model inference, metric calculation, regression) can be executed on a CPU-only environment with 2 cores and 7 GB RAM by using a statistically powered sampled subset of the dataset (n ≥ 30 images per region count bin) and a lightweight model configuration. If the 6-hour limit is approached, the system MUST automatically reduce the image count per bin to ensure a valid regression curve is produced, even with lower statistical power, to prevent total methodology failure.
- **Assumption about model**: The PerceptionDLM model weights can be loaded in default precision (FP32 or FP16) without requiring 8-bit quantization or CUDA acceleration, ensuring compatibility with the free-tier runner.
- **Assumption about baseline**: A standard sequential autoregressive captioning loop using a Transformer-based MLLM (e.g., LLaVA) can be implemented and run on CPU within the 6-hour time limit for the test set size.
- **Assumption about metrics**: The "Semantic Coherence Score" based on relational term consistency is a valid and computable metric using standard NLP libraries (e.g., `spaCy` or `NLTK`) without requiring external APIs or heavy LLM-based evaluation.
- **Assumption about threshold**: The "tipping point" is defined as the region count where parallel coherence drops to [deferred] of the sequential baseline, a community-standard default for "significant degradation" in performance trade-off studies.
- **Assumption about multiplicity**: Since multiple region counts are tested, the analysis will apply a Bonferroni correction or similar family-wise error rate control to the regression significance tests to account for multiple comparisons.