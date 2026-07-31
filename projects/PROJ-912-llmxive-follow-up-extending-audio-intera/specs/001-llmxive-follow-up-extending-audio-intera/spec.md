# Feature Specification: llmXive follow-up: extending "Audio Interaction Model"

**Feature Branch**: `001-audio-compression-robustness`  
**Created**: 2026-07-31  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'Audio Interaction Model' - Research on acoustic feature robustness in compressed audio-language models for safety-critical edge deployment."

## User Scenarios & Testing

### User Story 1 - Construct and Train Compressed Student Models with Variable Quantization (Priority: P1)

As a researcher, I need to instantiate, compress, and train pre-trained Audio-Language Model (teacher) into student variants with varying precision levels (FP32, INT8, INT4) and specific pruning ratios, using Knowledge Distillation, so that I can systematically evaluate the impact of compression and training on model capacity.

**Why this priority**: This is the foundational step; without generating specific trained student variants via distillation, no evaluation or analysis of feature robustness can occur. It directly enables the core experimental design.

**Independent Test**: Can be fully tested by running the compression and training script and verifying that distinct model checkpoints are saved with the correct parameter counts, quantization types, and training loss convergence, and that they load without CUDA errors on a CPU-only environment.

**Acceptance Scenarios**:

1. **Given** a pre-trained DeSTA2.5-Audio model and a target compression config (e.g., INT4, pruning [deferred]), **When** the compression and distillation module executes, **Then** a new student model checkpoint is saved with the specified bit-width and parameter reduction, and the model loads successfully on a 2-core CPU runner.
2. **Given** a list of compression targets (FP32, INT8, INT4) and pruning steps ([deferred], [deferred], [deferred], [deferred], [deferred], [deferred]), **When** the batch process runs, **Then** distinct model variants are generated, each with a unique file signature and verified parameter count, without triggering GPU allocation errors.

---

### User Story 2 - Evaluate Feature Robustness on Subtle Cue Dataset (Priority: P2)

As a researcher, I need to run inference on a curated subset of the ESC-50/AudioSet dataset containing high-frequency transients and low-amplitude events using all student models, so that I can measure the detection performance (AUC) for each compression level.

**Why this priority**: This step generates the primary data (performance metrics) required to answer the research question. It is the core "experiment" phase.

**Independent Test**: Can be fully tested by executing the evaluation script on a small sample of the dataset and confirming that an AUC score is calculated for each model variant against the ground-truth labels, with no dependency on model internal states for the metric calculation.

**Acceptance Scenarios**:

1. **Given** a set of compressed student models and a held-out "subtle cue" test set, **When** the evaluation pipeline runs, **Then** the system outputs a table of AUC scores for each model, where the scores are derived strictly from the model's final classification logits and the external dataset labels.
2. **Given** a specific model variant (e.g., INT4), **When** inference is performed on a 10-second audio clip of "glass breaking", **Then** the system records the inference latency (ms) and peak RAM usage (GB) within the 6-hour CI time limit and 7GB RAM constraint.

---

### User Story 3 - Generate Robustness Curve and Sensitivity Report (Priority: P3)

As a researcher, I need to perform trend analysis on the collected metrics to map the relationship between compression intensity and performance drop, including a sensitivity analysis on decision thresholds, so that I can identify the "breaking point" for safe edge deployment.

**Why this priority**: This synthesizes the raw data into the final research output (the robustness curve) and validates the stability of the findings, fulfilling the "Expected Results" requirement.

**Independent Test**: Can be fully tested by running the analysis script on the collected metrics and verifying that a trend plot is generated showing the AUC vs. compression level, and that a sensitivity report is produced for at least three threshold variations.

**Acceptance Scenarios**:

1. **Given** the collected AUC scores and compression parameters, **When** the analysis script executes, **Then** a step-change detection test is performed, and the point where detection sensitivity collapses (defined as >10% relative AUC drop) is identified and reported.
2. **Given** a decision threshold for "subtle cue detection", **When** the sensitivity analysis runs, **Then** the system sweeps the threshold over values {0.01, 0.05, 0.1} and reports the variation in false-positive and false-negative rates, confirming the stability of the primary finding.

---

### User Story 4 - Execute Ablation Study on Architectural Components (Priority: P4)

As a researcher, I need to systematically vary specific architectural components (e.g., freezing early attention heads vs. pruning late feed-forward layers) while maintaining constant compression levels, so that I can isolate the contribution of each component to feature robustness.

**Why this priority**: This directly addresses the research question regarding "how robustness varies across different architectural components," which is a core requirement of the methodology sketch.

**Independent Test**: Can be fully tested by running the ablation script on a subset of the dataset and confirming that distinct performance metrics are recorded for each architectural configuration (e.g., "Attention Frozen" vs. "FFN Pruned") with no cross-contamination of results.

**Acceptance Scenarios**:

1. **Given** a student model variant, **When** the ablation module executes with a "freeze early attention" config, **Then** the system records the AUC for this specific configuration and verifies that attention gradients are zeroed during the forward pass.
2. **Given** a student model variant, **When** the ablation module executes with a "prune late feed-forward" config, **Then** the system records the AUC for this configuration and verifies that the specified feed-forward layers are removed or zeroed.

---

### Edge Cases

- **Dataset Variability**: What happens if the ESC-50 subset lacks sufficient samples for a specific "low-amplitude" class (e.g., "whisper")? The system must skip that class and log a warning, ensuring the AUC calculation remains valid for the remaining classes without crashing.
- **Resource Exhaustion**: How does the system handle a compression variant that exceeds the 7GB RAM limit during inference? The system must catch the `MemoryError`, terminate that specific variant's evaluation gracefully, and log the failure as "OOM" rather than crashing the entire CI job.
- **Collinearity in Predictors**: If two architectural components (e.g., early attention and late projection) are highly correlated in their impact on performance, the analysis must not claim independent causal effects but must report the joint relationships descriptively.

## Requirements

### Functional Requirements

- **FR-001**: System MUST load a pre-trained Audio-Language Model (e.g., DeSTA2.5-Audio) and instantiate student variants with specific quantization levels (FP32, INT8, INT4) using `torch.ao.quantization` (no CUDA/bit8bit dependencies) and pruning ratios in [deferred] increments from [deferred] to [deferred], ensuring all operations are compatible with CPU-only execution (See US-1).
- **FR-002**: System MUST filter the ESC-50 or AudioSet dataset to create a "subtle cue" testbed containing only classes with dominant frequency content > 8kHz OR amplitude < -40dBFS (e.g., "glass breaking," "alarm," "whisper") (See US-2).
- **FR-003**: System MUST calculate the Area Under the Curve (AUC) of the ROC for each student model variant against the external ground-truth labels of the "subtle cue" dataset, ensuring the metric is independent of internal model weights (See US-2).
- **FR-004**: System MUST measure and log inference latency (ms) and peak RAM usage (GB) for each model variant on a 2-core CPU environment to verify compliance with GitHub Actions free-tier constraints (See US-2).
- **FR-005**: System MUST perform a step-change detection analysis correlating compression intensity (bits/parameters) with AUC drop to identify the point where detection sensitivity collapses (defined as a >10% relative drop from the FP32 baseline) (See US-3).
- **FR-006**: System MUST execute a sensitivity analysis sweeping the decision threshold over the set {0.01, 0.05, 0.1} and report the variation in false-positive and false-negative rates for each model variant (See US-3).
- **FR-007**: System MUST support selective freezing of early attention heads and pruning of late feed-forward layers to execute an ablation study isolating architectural contributions to feature robustness (See US-4).

### Key Entities

- **StudentModel**: A compressed variant of the teacher model, defined by its bit-width, pruning ratio, and parameter count.
- **SubtleCueSample**: An audio file from the filtered dataset, annotated with a class label indicating a high-frequency transient or low-amplitude event.
- **RobustnessMetric**: A data record containing the AUC score, inference latency, and peak RAM usage for a specific StudentModel on the SubtleCueSample set.
- **AblationConfig**: A configuration specifying which architectural components (attention heads, feed-forward layers) are frozen or pruned for a specific test run.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The drop in AUC performance is measured against the full-precision (FP32) baseline to quantify the robustness of specific acoustic features under compression (See FR-003, FR-005).
- **SC-002**: The resource efficiency (inference latency and peak RAM) is measured against the GitHub Actions free-tier constraints (≤6h job time, ≤7GB RAM, 2 CPU cores) to ensure feasibility (See FR-004).
- **SC-003**: The stability of the detection threshold is measured against the variation in false-positive/false-negative rates across the sensitivity sweep {0.01, 0.05, 0.1} to validate the robustness curve (See FR-006).
- **SC-004**: The identification of the "breaking point" is measured against the step-change detection where the AUC drops by >10% relative to the FP32 baseline AUC to determine safe deployment boundaries (See FR-005).
- **SC-005**: The architectural contribution to feature loss is measured against the ablation study results comparing early attention heads vs. late feed-forward layers to determine critical components (See FR-007, US-4).

## Assumptions

- The ESC-50 or AudioSet dataset contains sufficient samples for the specific high-frequency transient and low-amplitude classes (e.g., "glass breaking," "whisper") to support a statistically valid AUC calculation.
- The pre-trained DeSTA2.5-Audio model (or compatible variant) is available via HuggingFace and can be loaded into memory on a standard CPU runner without requiring GPU acceleration or 8-bit quantization libraries that depend on CUDA.
- The "subtle cue" detection task can be framed as an associational study; no causal claims will be made regarding the architectural components, only correlations between compression levels and performance drop.
- The GitHub Actions free-tier runner provides sufficient disk space to store the compressed model checkpoints and the filtered dataset subset simultaneously.
- The decision threshold for "subtle cue detection" is set to 0.5 by default for single-run baselines, but the primary 'breaking point' analysis (SC-004) relies on the sensitivity sweep results defined in FR-006.
- The "teacher" model's output distribution is a valid proxy for ground truth in the distillation loss, assuming the teacher is sufficiently capable for the specific "subtle cue" classes.
- The design distinguishes between 'robustness to compression' (quantization noise) and 'robustness to distillation error' (teacher bias); the validation target (AUC against external labels) is independent of the training signal (teacher logits).