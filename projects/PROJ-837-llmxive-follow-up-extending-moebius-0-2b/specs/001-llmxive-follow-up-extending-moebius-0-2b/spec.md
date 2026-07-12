# Feature Specification: llmXive follow-up: extending "Moebius: 0.2B Lightweight Image Inpainting Framework with 10B-Level Pe"

**Feature Branch**: `001-llmxive-moebius-dynamic`  
**Created**: 2026-07-12  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'Moebius: 0.2B Lightweight Image Inpainting Framework with 10B-Level Pe'"

## User Scenarios & Testing

### User Story 1 - Data Preparation and Human Complexity Annotation (Priority: P1)

The research pipeline must ingest the Places2 and CelebA-HQ datasets, generate synthetic masks with varying complexity, and collect human-rated structural complexity scores (1-5 Likert scale) for these masked regions to serve as the ground truth for training and validation.

**Why this priority**: This is the foundational step. Without independent human-annotated complexity labels, the hypothesis regarding the relationship between complexity and model rank cannot be tested, and the dynamic gating mechanism has no target for training.

**Independent Test**: Can be fully tested by verifying the existence of a dataset containing [deferred] images with corresponding synthetic masks and a CSV file of human-rated complexity scores, ensuring no model inference is required.

**Acceptance Scenarios**:

1. **Given** the Places2 and CelebA-HQ datasets are available, **When** the data preparation script runs with a seed of 42, **Then** a validation subset of a sufficient number of images is generated with synthetic masks, and the mask complexity metrics (gradient variance, texture entropy) are recorded.
2. **Given** the masked regions are prepared, **When** the crowdsourcing study interface is launched for N=50 participants, **Then** each participant assigns a 1-5 Likert score to the structural complexity of the masked region, and the aggregated scores are stored in a separate file from the model inputs.
3. **Given** the human annotations are complete, **When** the validation check runs, **Then** the system confirms that the human-rated scores are statistically independent of the model's internal feature representations (e.g., no correlation with intermediate activation maps).

---

### User Story 2 - Dynamic Rank Adjustment Mechanism Implementation (Priority: P2)

The system must implement the "Moebius-Dynamic" architecture, integrating a lightweight convolutional gating head that ingests masked context to output a scalar complexity score, which dynamically modulates the rank of the $L\lambda MI$ linear matrices during the forward pass.

**Why this priority**: This is the core innovation. It enables the efficiency-quality trade-off by adapting computational effort based on the input complexity, distinguishing this work from static baselines.

**Independent Test**: Can be fully tested by running the model on a single CPU core with a low-complexity mask and verifying that the effective rank of the linear matrices is reduced compared to the static high-capacity baseline, without requiring the full training loop to complete.

**Acceptance Scenarios**:

1. **Given** a masked image with low structural complexity (human score ≤ 2), **When** the Moebius-Dynamic model performs a forward pass on a 2-core CPU, **Then** the gating head outputs a low complexity score, and the $L\lambda MI$ matrices operate at a reduced rank (≤ 50% of max capacity).
2. **Given** a masked image with high structural complexity (human score ≥ 4), **When** the model performs a forward pass, **Then** the gating head outputs a high complexity score, and the $L\lambda MI$ matrices operate at full or near-full rank to preserve fidelity.
3. **Given** the model is trained on the complexity regression loss, **When** the training loop completes, **Then** the gating head weights converge such that the predicted complexity correlates with the human-rated ground truth (Spearman's rho ≥ 0.6).

---

### User Story 3 - Efficiency and Fidelity Evaluation (Priority: P3)

The system must evaluate the trained dynamic model against static baselines (0.2B and 50M parameters) by measuring wall-clock inference latency and image quality (FID, LPIPS) across complexity bins to quantify the efficiency gains.

**Why this priority**: This validates the research hypothesis. It provides the empirical evidence required to claim that dynamic scaling bridges the performance gap and reduces latency without significant quality degradation.

**Independent Test**: Can be fully tested by running the evaluation script on the held-out test set, generating a report that compares latency and FID scores between the dynamic and static models, without requiring further training.

**Acceptance Scenarios**:

1. **Given** the trained Moebius-Dynamic model and static baselines, **When** inference is run on the [deferred]-image validation set on a standard 2-core CPU, **Then** the average latency for low-complexity regions (score ≤ 2) is reduced by ≥ 30% compared to the static 0.2B baseline.
2. **Given** the generated inpainted images, **When** FID and LPIPS scores are computed against the ground truth, **Then** the FID score of the dynamic model is within 0.5 points of the static 0.2B baseline across all complexity bins.
3. **Given** the paired results, **When** a paired t-test is performed, **Then** the difference in quality metrics for low-complexity regions is statistically insignificant (p-value > 0.05) compared to the static high-capacity baseline.

### Edge Cases

- What happens when the human-rated complexity score is exactly 3 (neutral)? The gating mechanism must interpolate the rank linearly or use a defined threshold to ensure smooth transitions.
- How does the system handle images where the synthetic mask covers > 50% of the image? The model must fallback to the static high-capacity rank to prevent hallucination, as low-rank approximation may fail on large missing regions.
- How does the system handle participant disagreement (e.g., standard deviation > 1.0 for a specific mask)? The system must flag these samples for exclusion or use a majority vote to resolve the ground truth label.

## Requirements

### Functional Requirements

- **FR-001**: System MUST generate synthetic masks with varying complexity levels based on pre-calculated gradient variance, texture entropy, and structural similarity metrics from the Places2 and CelebA-HQ datasets (See US-1).
- **FR-002**: System MUST support a crowdsourcing interface for N=50 participants to assign 1-5 Likert scale structural complexity scores to masked regions (See US-1).
- **FR-003**: System MUST implement a lightweight convolutional gating head (≤5M parameters) that outputs a scalar complexity score to modulate the rank of $L\lambda MI$ matrices (See US-2).
- **FR-004**: System MUST train the dynamic model using a multi-task loss combining reconstruction error and regression loss against human-rated complexity labels (See US-2).
- **FR-005**: System MUST measure wall-clock inference latency (ms) on a 2-core CPU environment for both dynamic and static models across all complexity bins (See US-3).
- **FR-006**: System MUST compute FID and LPIPS scores for all generated outputs and perform a paired t-test to determine statistical significance of quality differences (See US-3).
- **FR-007**: System MUST ensure that evaluation targets (FID/LPIPS) are mathematically independent of the gating mechanism's input features and training labels to prevent circular validation (See US-3).

### Key Entities

- **MaskedRegion**: Represents a specific masked area in an image, containing attributes: `image_id`, `mask_geometry`, `gradient_variance`, `texture_entropy`, `human_complexity_score`.
- **InferenceResult**: Represents the output of a model run, containing attributes: `model_type` (dynamic/static), `latency_ms`, `fid_score`, `lpps_score`, `complexity_bin`.
- **GatingState**: Represents the internal state of the gating mechanism during inference, containing attributes: `input_context_features`, `predicted_complexity`, `active_matrix_rank`.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The correlation between human-rated structural complexity and the minimum model rank required for perceptual fidelity is measured against the Spearman's rank correlation coefficient (See US-1).
- **SC-002**: The reduction in average CPU inference latency for low-complexity regions is measured against the static 0.2B baseline (See US-3).
- **SC-003**: The quality degradation of the dynamic model is measured against the static high-capacity baseline using the Fréchet Inception Distance (FID) score difference (See US-3).
- **SC-004**: The statistical significance of quality differences in low-complexity regions is measured against the p-value from a paired t-test (See US-3).
- **SC-005**: The efficiency gain (latency reduction) vs. quality trade-off is measured against the target of 30-40% latency reduction with ≤ 0.5 FID point difference (See US-3).

## Assumptions

- The Places2 and CelebA-HQ datasets are available and accessible without requiring GPU-accelerated downloaders; The validation subset fits within the 7 GB RAM limit of the CI runner..
- The crowdsourcing study for N=50 participants can be conducted externally or simulated with high-quality synthetic labels, as the CI environment does not host a live human participant platform.
- The 0.2B parameter Moebius architecture and the 50M parameter sub-network can be loaded and executed on a standard 2-core CPU with ~7 GB RAM using PyTorch in default precision (no 8-bit quantization or CUDA required).
- The "Moebius" architecture details (specifically the $L\lambda MI$ linear matrices) are sufficiently documented in the referenced "Moebius" preprint to allow for correct implementation of the dynamic rank modulation.
- The synthetic masks generated based on gradient variance and texture entropy are valid proxies for human-perceived structural complexity, justifying the initial correlation analysis.
- The training protocol using curriculum learning (gating head first, then end-to-end) converges within the time limit of the GitHub Actions free-tier runner.
- The FID and LPIPS metrics can be computed on the CPU within the time budget, as they rely on a pre-trained Inception network which is known to be CPU-tractable for small batches.
