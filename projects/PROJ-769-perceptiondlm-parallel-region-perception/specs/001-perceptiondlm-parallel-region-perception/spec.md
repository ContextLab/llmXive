# Feature Specification: Parallel Region Perception with Multimodal Diffusion Language Models

**Feature Branch**: `001-parallel-region-perception-dlm`  
**Created**: 2026-06-30  
**Status**: Draft  
**Input**: User description: "PerceptionDLM: Parallel Region Perception with Multimodal Diffusion Language Models"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Baseline Autoregressive Inference (Priority: P1)

The system must successfully execute a standard autoregressive (AR) vision-language model to generate captions for a variable number of image regions sequentially, establishing a baseline for latency and quality.

**Why this priority**: This is the control condition. Without a verified, reproducible AR baseline running on the target hardware (CPU-only), no comparison with the diffusion approach is scientifically valid. It validates the data pipeline and measurement infrastructure.

**Independent Test**: The system can be tested by running the AR pipeline on a fixed subset of COCO validation images with 1 region per image, measuring wall-clock time (median of 3 runs on the target hardware) and generating a CLIPScore and BLEU-4 against ground truth, independent of the diffusion model.

**Acceptance Scenarios**:

1. **Given** a COCO 2017 validation image with 1 annotated region, **When** the AR model (LLaVA-1.5-7B in GGUF Q4_K_M format) processes the region sequentially, **Then** the system records the total wall-clock time (median of 3 runs) and outputs a generated caption with valid CLIPScore ≥ 0.65 AND BLEU-4 ≥ 0.15 calculated against ground truth.
2. **Given** a batch of 5 images, **When** the system processes regions sequentially for each, **Then** the total latency scales linearly with the number of regions, and no CUDA/GPU errors occur during execution.

---

### User Story 2 - Parallel Diffusion Inference (Priority: P2)

The system must execute a lightweight multimodal diffusion language model to generate captions for multiple regions simultaneously, measuring the throughput gain relative to the AR baseline.

**Why this priority**: This implements the core hypothesis: that parallel generation reduces latency. It is the primary variable being tested (degree of parallelism).

**Independent Test**: The system can be tested by running the DLM on the same set of images but with N regions per image in parallel, measuring the throughput (tokens/second) and comparing the total time against the sequential AR baseline time (median of 3 runs on the same hardware) for the same workload.

**Acceptance Scenarios**:

1. **Given** a COCO image with 4 annotated regions, **When** the DLM processes all 4 regions in a single parallel batch, **Then** the system outputs 4 distinct captions and records the total wall-clock time.
2. **Given** a batch of 5 images with N=4 regions each, **When** the DLM runs with N=4 parallel prompts, **Then** the system calculates a speedup ratio > 1.0 (total time < N * single_region_baseline_time) and completes without exceeding the total runtime constraint.

---

### User Story 3 - Trade-off Analysis and Threshold Identification (Priority: P3)

The system must aggregate latency and quality metrics across varying region counts (N=1, 4, 8, 16) and diffusion steps to identify the "break-even" point where parallelism benefits are negated by diffusion overhead.

**Why this priority**: This delivers the scientific output: the trade-off curve. It synthesizes the data from US-1 and US-2 to answer the research question.

**Independent Test**: The system can be tested by generating a CSV report containing latency, tokens/second, and CLIPScore for all N values, and verifying that a non-linear regression analysis identifies a specific N where the speedup ratio crosses 1.0, or confirms no such point exists within the range.

**Acceptance Scenarios**:

1. **Given** the collected metrics for N=1, 4, 8, 16 regions, **When** the analysis script runs, **Then** it produces a throughput vs. region count curve and identifies the specific N value where the DLM speedup ratio drops below 1.0 (break-even), or reports "No break-even in range [1, 16]" if the ratio remains >1.0 or <1.0 throughout.
2. **Given** the same dataset, **When** the script analyzes the impact of diffusion steps (varying K_steps), **Then** it outputs the minimum number of steps required to maintain a CLIPScore within 5% of the AR baseline AND a BLEU-4 score within 10% of the AR baseline.

---

### Edge Cases

- **What happens when** the number of regions exceeds the model's context window or memory limit? The system MUST monitor memory usage and clamp N to the maximum supported when usage exceeds 90% of the *detected available system RAM*, logging the actual clamped N and the threshold used.
- **How does the system handle** images where the region detector fails or returns 0 regions? The system MUST skip such images and log the count of skipped samples to ensure the denominator in the throughput calculation remains accurate.
- **What happens if** the CLIPScore or BLEU calculation fails due to a missing embedding model? The system MUST fall back to a placeholder metric or terminate with a clear error code, ensuring no silent data corruption.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST load the COCO 2017 validation set and extract region coordinates via the official API to ensure data reproducibility (See US-1).
- **FR-002**: System MUST execute an autoregressive baseline (LLaVA-1.5-7B in GGUF Q4_K_M format) to generate captions sequentially for N regions, recording wall-clock time (See US-1).
- **FR-003**: System MUST execute a lightweight multimodal diffusion language model (e.g., LLaVA-Diffusion or equivalent open-weights text-generating diffusion model) to generate captions for N regions in parallel, varying N across {1, 4, 8, 16}. If no suitable text-generating DLM is available, the system MUST record the hypothesis as untestable with the current model set and proceed with the AR baseline only (See US-2).
- **FR-004**: System MUST calculate semantic coherence using CLIPScore AND BLEU-4 for every generated caption against the ground truth to ensure both image-text alignment and text fluency are measured (See US-3).
- **FR-005**: System MUST perform a non-linear scaling law fit (e.g., power law or exponential decay) on the throughput vs. region count data to model the physical limits of parallelism, rather than assuming linearity (See US-3).
- **FR-006**: System MUST implement a sensitivity analysis sweeping the diffusion step count over a set {5, 10, 20} to determine the minimum steps for acceptable quality (See US-3).

### Key Entities

- **RegionSample**: Represents a single image region, containing attributes: `image_id`, `region_bbox`, `ground_truth_caption`.
- **InferenceRun**: Represents a single execution instance, containing attributes: `model_type` (AR/DLM), `n_regions`, `diffusion_steps`, `wall_clock_time`, `throughput_tokens_per_sec`, `hardware_config`.
- **QualityMetric**: Represents the evaluation result, containing attributes: `sample_id`, `clipscore`, `bleu4_score`, `generated_text`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Latency reduction (speedup ratio) is measured against the sequential AR baseline time (median of 3 runs on the same hardware) for the same N regions (See US-2, US-3).
- **SC-002**: Semantic coherence is measured against the AR baseline's CLIPScore and BLEU-4. If the parallel generation degrades CLIPScore by more than 5% (relative) OR BLEU-4 by more than 10% (relative) compared to the AR baseline, the run is marked as failed for that N value and the limit is recorded (See US-3).
- **SC-003**: The "break-even" threshold (N) is identified by finding the point where the DLM speedup ratio drops below 1.0. If the ratio never drops below 1.0 or never exceeds 1.0 within the range [1, 16], the result is recorded as "No break-even in range" (See US-3).
- **SC-004**: The minimum diffusion steps required are measured by finding the lowest step count where CLIPScore remains within the 5% tolerance AND BLEU-4 remains within the 10% tolerance of the AR baseline (See US-3).
- **SC-005**: Computational feasibility is measured by ensuring the total runtime for the full experiment (all N values) does not exceed 6 hours on a standard CPU environment (≥2 cores). If a 2-core target is unfeasible, a 4-core environment is permitted, provided the hardware configuration and scaling trend are explicitly reported (See US-1, US-2).

## Assumptions

- The COCO validation set and region annotations are available via the official API and fit within the 14GB disk constraint when downloaded.
- A lightweight, open-weights multimodal diffusion language model (capable of text generation from image+text input, e.g., LLaVA-Diffusion) is available. If no such model exists, the hypothesis is recorded as untestable, and the experiment proceeds with the AR baseline only.
- The "break-even" point may or may not exist within the tested range of N=1 to N=16; if no break-even is found, the result is recorded as a boundary condition rather than a failure.
- CLIPScore and BLEU-4 provide sufficient proxies for human semantic alignment for this study, avoiding the need for expensive human annotation or closed-source LLM judges.
- The multi-core CPU runner provides sufficient memory to load the quantized AR model and the DLM sequentially without OOM errors.
- Latency is not deterministic; it depends on system load. Therefore, all latency measurements are the median of 3 independent runs on the target hardware.
- If the 2-core CPU target is scientifically unfeasible (e.g., runtime > 6 hours), a 4-core CPU runner is permitted to complete the experiment, provided the hardware configuration is explicitly recorded in the results.