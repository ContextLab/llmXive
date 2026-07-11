# Feature Specification: llmXive follow-up: extending "Training Long-Context Vision-Language Models Effectively with Generali"

**Feature Branch**: `001-modality-balance-attention`  
**Created**: 2026-07-11  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'Training Long-Context Vision-Language Models Effectively with Generali'"

## User Scenarios & Testing

### User Story 1 - Synthetic Data Generation with Controlled Modality Balance (Priority: P1)

The system must generate a synthetic dataset of long-context samples (128K–256K text-only tokens) where the "visual density" (total number of visual tokens derived from unique images) is systematically varied from 0 to 20 images, while strictly holding total **text-only** token count and "needle" difficulty constant. Images must be fixed resolution (336x336) to ensure linear scaling of visual tokens. This is the foundational step required to isolate the variable of interest.

**Why this priority**: Without a controlled dataset where visual density is the only independent variable changing (and text length is held constant), no causal or associational claims about modality balance can be made. This is the prerequisite for all subsequent analysis.

**Independent Test**: A script can be run to generate a batch of samples.. The output can be validated by parsing the metadata of each sample to confirm that the **text-only** token count variance is <1%, the needle difficulty score is identical across all samples, and the visual token count varies exactly as specified by the image count.

**Acceptance Scenarios**:

1. **Given** the configuration for 128K text-only token contexts, **When** the generator runs for density levels 0, 5, 10, and 20, **Then** the resulting dataset contains equal numbers of samples for each level with identical text-only token counts.
2. **Given** a generated sample with 20 images, **When** the sample is inspected, **Then** it contains exactly 20 unique image references (fixed resolution) and the text content is padded to maintain the target text-only token length without altering the "needle" placement.

---

### User Story 2 - CPU-Feasible Inference and Retrieval Execution (Priority: P2)

The system must execute "needle-in-a-haystack" retrieval tasks on the generated dataset using the MMProLong-7B-1.0 model (HuggingFace ID: mmpro/MMProLong-7B-1.0) loaded with low-bit quantization via `llama.cpp` or `ONNX Runtime`, ensuring the entire inference process completes within the 6-hour CI limit on a 2-core CPU runner with ≤7GB RAM.

**Why this priority**: This validates the "Compute Feasibility" constraint. If the model cannot run on the target hardware, the research cannot proceed. This story ensures the infrastructure supports the scientific inquiry.

**Independent Test**: A single sample can be processed end-to-end. The test verifies that the process does not OOM (Out of Memory), completes with an average time per sample ≤ 21.6 seconds (derived from 6h / 10k samples), and outputs a retrieval result (correct/incorrect).

**Acceptance Scenarios**:

1. **Given** a 256K text-only token sample with 15 images, **When** the inference engine loads the 7B model in 4-bit mode, **Then** the process completes without exceeding 7GB RAM usage.
2. **Given** a batch of 100 samples, **When** the inference loop runs on a 2-core CPU runner with ≤7GB RAM, **Then** the total execution time ≤ 6 hours for the full batch, and every sample yields a binary retrieval outcome (match/no match).

---

### User Story 3 - Statistical Analysis of Modality Saturation (Priority: P3)

The system must aggregate retrieval accuracy across visual density buckets and perform a logistic regression or ANOVA to test for a significant interaction effect between **visual density** and **text-only context length** (if varied) or treat text length as a covariate, specifically looking for a non-linear degradation "cliff" rather than linear scaling.

**Why this priority**: This delivers the core scientific answer to the research question. It transforms raw inference logs into the evidence required to confirm or refute the hypothesis of modality-specific attention saturation.

**Independent Test**: A statistical script can be run on a mock dataset of accuracy scores. The test verifies that the script correctly identifies a non-linear trend (e.g., a sharp drop at density >10) and outputs the p-value for the interaction term.

**Acceptance Scenarios**:

1. **Given** the aggregated accuracy data per visual density bucket, **When** the logistic regression model is fitted, **Then** the output includes the interaction coefficient between visual density and text-only length with a calculated p-value reported.
2. **Given** a scenario where accuracy drops sharply after 15 images, **When** the analysis runs, **Then** the result explicitly flags a "non-linear degradation" pattern rather than a linear slope.

---

### User Story 4 - Short-Context Grounding Check (Priority: P4)

The system must include and evaluate a subset of short-context visual grounding questions (e.g., "What is in the first image?") to monitor for catastrophic forgetting of short-range visual capabilities, ensuring the model's degradation is specific to long-context saturation and not general capability loss.

**Why this priority**: This acts as a control mechanism to validate that any observed long-context failure is not due to a general collapse of the model's visual grounding abilities.

**Independent Test**: A script can run a set of short-context questions.. The test verifies that the system correctly processes these short inputs and outputs binary success/failure outcomes for visual grounding.

**Acceptance Scenarios**:

1. **Given** a short-context sample (≤4K tokens) with 1 image, **When** the inference engine runs, **Then** the system correctly identifies the visual content with ≥95% accuracy (baseline check).
2. **Given** the full dataset run, **When** the analysis aggregates results, **Then** the short-context accuracy is reported separately from the long-context results to enable comparison.

---

### Edge Cases

- **What happens when** the visual density is 0 (text-only)? The system must correctly handle this as the baseline control group and ensure the "needle" retrieval logic remains valid without image processing overhead.
- **How does the system handle** a model OOM event during inference on a 256K sample? The system must catch the exception, log the failure with the specific sample ID and memory state, and skip to the next sample rather than crashing the entire CI job.
- **What happens when** the "needle" is buried directly within an image description (text embedded in image alt-text) vs. pure text? The system must distinguish these cases if the hypothesis implies different degradation rates, or ensure the needle is strictly text-based as per the methodology.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST generate a large-scale set of synthetic long-context samples (K–high-token text-only) with visual density varying from 0 to 20 images (fixed resolution) distributed evenly across density buckets, while holding total text-only token count constant (See US-1).
- **FR-002**: The system MUST load the MMProLongB model (HuggingFace ID: mmpro/MMProLong-7B-1.0) using 4-bit quantization (via `llama.cpp` or `ONNX Runtime`) and freeze all parameters to prevent training (See US-2).
- **FR-003**: The system MUST execute "needle-in-a-haystack" retrieval tasks on every generated sample and record a binary success/failure outcome for the specific target token (See US-2).
- **FR-004**: The system MUST aggregate retrieval accuracy results by visual density bucket and perform a logistic regression or ANOVA to test for interaction effects between visual density and text-only context length (See US-3).
- **FR-005**: The system MUST implement a memory guardrail that detects OOM conditions and gracefully skips the current sample while logging the error, ensuring the total job does not exceed the 6-hour CI limit on the 2-core CPU runner with ≤7GB RAM (See US-2).
- **FR-006**: The system MUST include a subset of short-context visual grounding questions (e.g., "What is in the first image?") to monitor for catastrophic forgetting of short-range visual capabilities (See US-4).

### Key Entities

- **SyntheticSample**: Represents a single long-context input containing text, a variable number of images, and a hidden "needle" token. Attributes: `sample_id`, `text_token_count`, `image_count`, `visual_token_count`, `needle_location`, `needle_value`.
- **InferenceResult**: Represents the output of the model on a specific sample. Attributes: `sample_id`, `retrieved_value`, `is_correct` (boolean), `inference_time_ms`, `peak_memory_mb`.
- **DensityBucket**: Represents a grouping of samples by their visual density count. Attributes: `density_level` (0-20), `total_samples`, `accuracy_rate`.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Retrieval accuracy is measured against the visual density level to identify non-linear degradation patterns (See US-3).
- **SC-002**: Memory usage during inference is measured against the ≤7GB RAM limit of the target runner to ensure feasibility (See US-2).
- **SC-003**: Total inference time for the full dataset is measured against the 6-hour CI job limit on the 2-core CPU runner (See US-2).
- **SC-004**: The statistical significance of the interaction effect (visual density × text-only length) is measured against a conventional p-value threshold. (based on standard scientific convention) (See US-3).
- **SC-005**: The validity of the "needle" retrieval is measured against the ground truth needle location provided in the synthetic sample metadata (See US-2).

## Assumptions

- The MMProLong-7B-1.0 weights (HuggingFace ID: mmpro/MMProLong-7B-1.0) are available and can be successfully loaded in 4-bit quantization on the target runner (2-core CPU, ≤7GB RAM) without requiring CUDA or GPU acceleration.
- The synthetic data generation process can produce valid, high-quality text and image references that simulate the complexity of technical manuals without introducing artifacts that confuse the model unrelated to visual density.
- The "needle" token is strictly text-based and its retrieval is the primary metric; the system assumes the model's visual grounding capabilities are not the primary failure mode for text retrieval in this specific experimental setup.
- The target runner (2-core CPU, ≤7GB RAM) provides sufficient compute power to process the [deferred] samples within 6 hours, provided the 4-bit quantization is applied and the dataset is not excessively large in file size (disk I/O limits).
- The "visual density" variable is defined as the total number of visual tokens derived from images (fixed resolution 336x336), ensuring a linear relationship with image count.
- The logistic regression or ANOVA models used for analysis are computationally lightweight enough to run on the target runner without exceeding memory limits.
- The 4-bit quantization method used (e.g., via `llama.cpp`) does not introduce a performance degradation in retrieval accuracy that is indistinguishable from the hypothesized "modality saturation" effect.