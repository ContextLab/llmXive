# Feature Specification: Cosmos 3: Omnimodal World Models for Physical AI

**Feature Branch**: `001-omnimodal-world-models`  
**Created**: 2026-06-16  
**Status**: Draft  
**Input**: User description: "Cosmos 3: Omnimodal World Models for Physical AI"

## User Scenarios & Testing

### User Story 1 - Train and Evaluate Omnimodal vs. Unimodal Baselines (Priority: P1)

The researcher must be able to train a single large-scale omnimodal world model on a subset of heterogeneous data (text, image, video, audio, action) and compare its embodied task success rate against three distinct unimodal baselines (text-only, vision-only, action-only) using the same architecture and data budget.

**Why this priority**: This is the core scientific inquiry. Without a direct, controlled comparison of the omnimodal approach against unimodal variants, the research question regarding the benefit of multimodal integration cannot be answered.

**Independent Test**: The system can be fully tested by executing the training pipeline for a large-scale omnimodal model and the three baselines on a 2-core runner with 5GB of data, then running the evaluation script on the Mini-World "Collect-Objects" and Habitat environments to produce a comparative table of success rates.

**Acceptance Scenarios**:

1. **Given** the 5GB sampled datasets for all modalities, **When** the 150M omnimodal model and three unimodal baselines are trained for 3 epochs on the 2-core runner, **Then** all four models complete training within the specified wall-clock budget and produce valid checkpoints.
2. **Given** the trained checkpoints, **When** the policy head is lightly adapted (frozen backbone) and evaluated on 5 random seeds in Mini-World "Collect-Objects", **Then** the system outputs a success rate and episode length for each model variant.
3. **Given** the evaluation results, **When** the statistical analysis module runs paired t-tests and calculates confidence intervals, **Then** the system reports p-values, 95% CIs, and effect sizes (Cohen's d) indicating whether the omnimodal model significantly outperforms the unimodal baselines (target p < 0.05).

---

### User Story 2 - Validate Cross-Modal Representation Quality (Priority: P2)

The researcher must verify that the learned omnimodal representation effectively fuses modalities by measuring cross-modal retrieval performance on standard benchmarks using zero-shot inference.

**Why this priority**: Success in embodied tasks could theoretically occur by chance or due to specific modality dominance; cross-modal retrieval scores provide evidence that the model has formed a unified, rich representation of the world.

**Independent Test**: The system can be tested independently by loading the trained 150M omnimodal checkpoint and running zero-shot retrieval queries on the COCO-Cap and AudioCaps datasets without requiring the embodied simulation environment or additional fine-tuning.

**Acceptance Scenarios**:

1. **Given** the trained omnimodal model, **When** the system processes the COCO-Cap dataset, **Then** it computes and reports Recall@1 and Recall@5 for image-text retrieval.
2. **Given** the trained omnimodal model, **When** the system processes the AudioCaps dataset, **Then** it computes and reports Recall@1 and Recall@5 for audio-text retrieval.
3. **Given** the retrieval metrics, **When** the results are compared against the unimodal baselines, **Then** the omnimodal model demonstrates equal or superior performance in at least one cross-modal retrieval task.

---

### User Story 3 - Perform Modality Ablation Study (Priority: P3)

The researcher must isolate the contribution of each specific modality by systematically removing one modality at a time from the trained omnimodal checkpoint and re-evaluating embodied performance.

**Why this priority**: This determines which modalities are driving the performance gains, providing actionable insights for future model design and resource allocation.

**Independent Test**: The system can be tested by taking the final 150M omnimodal checkpoint, masking specific modality inputs, and running the evaluation suite to observe the drop in task success.

**Acceptance Scenarios**:

1. **Given** the trained omnimodal checkpoint, **When** the text modality is masked during inference, **Then** the system records the change in success rate compared to the full omnimodal model.
2. **Given** the trained omnimodal checkpoint, **When** the vision modality is masked during inference, **Then** the system records the change in success rate compared to the full omnimodal model.
3. **Given** the ablation results for all modalities, **When** the report is generated, **Then** it clearly ranks the modalities by their impact on embodied task success.

---

### Edge Cases

- What happens if the 5GB dataset subset is too small to converge the 150M parameter model within 6 hours on 2 CPU cores? (System must detect non-convergence and report a timeout/failure).
- How does the system handle modalities with missing data in the TFRecord stream (e.g., a video clip without audio)? (System must skip the sample or impute zeros without crashing).
- What if the statistical test assumptions (normality) are violated due to small sample size (5 seeds)? (System must fall back to a non-parametric test like Mann-Whitney U).

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and preprocess a pre-sharded [deferred] subset (approx. 5GB total) of the specified datasets (LAION-2B-en, AudioSet, HowTo100M, RoboSet) into a unified TFRecord format. (See US-1)
- **FR-002**: System MUST implement a "Lightweight Mixture-of-Transformers" architecture (150M parameters) capable of ingesting text, image, video, audio, and action tokens simultaneously, configured for CPU-only execution with gradient checkpointing. (See US-1)
- **FR-003**: System MUST train three unimodal variants (text-only, vision-only, action-only) using the exact same architecture, hyperparameters, and data budget as the omnimodal model to ensure a fair comparison. (See US-1)
- **FR-004**: System MUST execute the lightly adapted policy head on Mini-World "Collect-Objects" and Habitat-ObjectNav environments for 5 random seeds per model variant and record success rates and episode lengths. (See US-1)
- **FR-005**: System MUST perform statistical analysis (paired t-tests) on the evaluation results to determine significance (p < 0.05), calculate effect sizes (Cohen's d), and report 95% confidence intervals. (See US-1)
- **FR-006**: System MUST compute cross-modal retrieval metrics (Recall@1/5) on COCO-Cap and AudioCaps datasets using the trained omnimodal model in a zero-shot manner. (See US-2)
- **FR-007**: System MUST perform an ablation study by masking individual modalities in the omnimodal model and re-evaluating embodied task performance. (See US-3)
- **FR-008**: System MUST enforce a hard timeout of 6 hours for the entire training and evaluation pipeline to ensure feasibility on free-tier CI runners. (See US-1)

### Key Entities

- **WorldModelCheckpoint**: The saved state of the trained model (omnimodal or unimodal) containing weights and architecture configuration.
- **EmbodiedTaskResult**: A record containing the environment name, seed ID, success rate, and episode length for a single evaluation run.
- **RetrievalMetric**: A record containing the dataset name, modality pair, and Recall@K scores.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The omnimodal model's embodied task success rate is measured against the average success rate of the three unimodal baselines to determine the absolute improvement percentage. (See US-1)
- **SC-002**: The statistical significance of the performance difference is measured against the threshold of p < 0.05 and 95% confidence intervals using paired t-tests across 5 seeds. (See US-1)
- **SC-003**: The cross-modal retrieval quality is measured against the Recall@1 and Recall@5 scores on COCO-Cap and AudioCaps to validate representation fusion. (See US-2)
- **SC-004**: The computational feasibility is measured against the 6-hour wall-clock limit and 7 GB RAM constraint on the 2-core runner (sufficient for 150M model). (See US-1)
- **SC-005**: The modality contribution is measured by the delta in success rate when each modality is ablated compared to the full omnimodal model. (See US-3)

## Assumptions

- The pre-sharded [deferred] subset of the heterogeneous datasets (LAION-2B-en, AudioSet, HowTo100M, RoboSet) contains sufficient signal for a 150M parameter model to learn a unified representation within the 6-hour CPU time budget.
- The "Lightweight Mixture-of-Transformers" codebase (github.com/open-ml/mixture-transformers) is available, functional, and compatible with the specified CPU-only training constraints (gradient checkpointing).
- The Mini-World and Habitat-ObjectNav simulation environments can be executed on the GitHub Actions free-tier runner without requiring GPU acceleration or external dependencies.
- The datasets provided in the related work section are accessible via the specified URLs and do not require authentication or special licensing beyond public access.
- A set of random seeds used for evaluation provides a statistically robust sample size for calculating effect sizes and p-values in the absence of a larger compute budget.
- Zero-shot retrieval performance on COCO-Cap and AudioCaps is a valid proxy for cross-modal representation quality without additional fine-tuning.