# Feature Specification: llmXive follow-up: extending "FashionChameleon: Towards Real-Time and Interactive Human-Garment Vide"

**Feature Branch**: `001-garment-text-fidelity`  
**Created**: 2026-07-11  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'FashionChameleon: Towards Real-Time and Interactive Human-Garment Vide'"

## User Scenarios & Testing

### User Story 1 - Feature-Stratified Fidelity Benchmarking (Priority: P1)

**User Journey**: A researcher needs to run a controlled experiment to determine exactly which garment attributes (color, pattern, texture) degrade when switching from image references to text prompts in the FashionChameleon pipeline. The system must ingest a stratified dataset, run the text-driven adapter, and output a comparative fidelity report broken down by feature class.

**Why this priority**: This is the core scientific contribution of the project. Without isolating fidelity by feature class, the research question ("which specific classes... suffer the most significant fidelity loss") cannot be answered. This is the Minimum Viable Research (MVR).

**Independent Test**: The system can be tested by running the evaluation pipeline on a fixed subset of Human3.6M clips with known feature tags and verifying that the output report contains distinct fidelity scores for color, pattern, and texture categories, showing a measurable difference between the text-driven and image-driven baselines.

**Acceptance Scenarios**:

1. **Given** a test dataset of 500 clips tagged with feature classes (color, pattern, texture), **When** the benchmarking pipeline executes the text-driven adapter against the frozen FashionChameleon backbone, **Then** the system outputs a JSON report containing distinct mean CLIP-T fidelity scores for each feature class.
2. **Given** the same test dataset, **When** the system compares the text-driven scores against the image-driven baseline scores, **Then** the report explicitly lists the relative fidelity loss percentage for each feature class (e.g., "Texture: -40%", "Color: -5%").
3. **Given** the pipeline is configured for CPU-only execution, **When** the benchmark runs on a standard 8-core CPU instance, **Then** the total execution time for the 500-clip subset remains [deferred], and no GPU-related errors occur.

---

### User Story 2 - Real-Time Latency Verification (Priority: P2)

**User Journey**: A developer needs to verify that the proposed lightweight cross-attention adapter does not introduce prohibitive latency, ensuring the system remains viable for "real-time" interactive applications (target <50ms/frame) on CPU hardware.

**Why this priority**: The project's premise relies on "real-time" performance. If the text adapter slows inference beyond the interactive threshold, the method is not viable for the intended use case (e-commerce/virtual fitting rooms), regardless of fidelity.

**Independent Test**: The system can be tested by running the text-driven generation on a single video clip and measuring the end-to-end inference time per frame, verifying it meets the <50ms constraint on a CPU-only environment.

**Acceptance Scenarios**:

1. **Given** a pre-trained FashionChameleon model with the text adapter inserted, **When** the model processes a 10-second video clip (300 frames) on a CPU-only runner, **Then** the average inference time per frame is recorded and reported.
2. **Given** the recorded average inference time, **When** the value is compared against the 50ms threshold, **Then** the system flags the result as "Pass" if ≤50ms and "Fail" if >50ms.
3. **Given** a failure scenario where latency exceeds 50ms, **When** the system logs the bottleneck, **Then** it identifies whether the delay originates from the text encoder, the cross-attention adapter, or the generation backbone.

---

### User Story 3 - Statistical Significance & Sensitivity Analysis (Priority: P3)

**User Journey**: A peer reviewer needs to confirm that the observed fidelity differences between feature classes are statistically significant and that any decision thresholds used in the analysis are robust to small variations.

**Why this priority**: To ensure methodological soundness, the project must move beyond descriptive statistics to inferential statistics (ANOVA) and validate that results are not artifacts of arbitrary threshold choices.

**Independent Test**: The system can be tested by executing the statistical analysis module on the benchmark results, verifying that ANOVA p-values are calculated and that a sensitivity sweep of the consistency threshold is performed.

**Acceptance Scenarios**:

1. **Given** the fidelity scores stratified by feature class, **When** the ANOVA test is executed, **Then** the system outputs a p-value indicating whether the difference in fidelity between at least two feature classes is statistically significant (p < 0.05).
2. **Given** a defined consistency threshold (e.g., optical flow divergence), **When** the sensitivity analysis sweeps the threshold across values {0.01, 0.05, 0.1}, **Then** the system generates a table showing how the false-positive and false-negative rates vary across these values.
3. **Given** the statistical results, **When** the system checks for multiplicity issues, **Then** it applies a family-wise error correction (e.g., Bonferroni) if more than 3 hypothesis tests are conducted simultaneously.

---

### Edge Cases

- **What happens when** the text prompt contains ambiguous or conflicting feature descriptors (e.g., "red plaid" where the plaid pattern is actually blue)? The system must log these as "Low Confidence" samples and exclude them from the primary fidelity calculation or flag them for manual review.
- **How does the system handle** a dataset subset where a specific feature class (e.g., "texture") has fewer than 10 samples? The system must raise a warning and skip the statistical significance test for that specific class to avoid Type I errors due to low power.
- **What happens when** the CPU memory limit (7 GB) is exceeded during the batch processing of the [deferred]-clip dataset? The system must automatically switch to a streaming/batched processing mode, processing clips in chunks of 50 to stay within memory bounds.

## Requirements

### Functional Requirements

- **FR-001**: System MUST ingest the FashionChameleon pre-trained weights and insert a lightweight cross-attention adapter module that maps frozen CLIP text embeddings to the reference KV slots. (See US-1)
- **FR-002**: System MUST process a curated dataset of [deferred] Human3.6M clips paired with synthetic multi-garment descriptions, explicitly tagged by feature class (color, pattern, texture). (See US-1)
- **FR-003**: System MUST compute CLIP-T similarity scores between generated frames and input text, and optical flow variance relative to input motion, for every generated frame. (See US-1)
- **FR-004**: System MUST execute the entire inference and evaluation pipeline on a CPU-only environment (2 cores, ~7 GB RAM) without requiring CUDA or GPU acceleration. (See US-2)
- **FR-005**: System MUST perform an ANOVA test on the fidelity scores across the three feature categories to determine statistical significance, applying family-wise error correction if multiple tests are run. (See US-3)
- **FR-006**: System MUST conduct a sensitivity analysis by sweeping the optical flow consistency threshold over the set {0.01, 0.05, 0.1} and reporting the variation in false-positive/negative rates. (See US-3)
- **FR-007**: System MUST measure and log the end-to-end inference latency per frame, flagging any frame exceeding 50ms as a violation of the real-time constraint. (See US-2)

### Key Entities

- **GarmentFeatureClass**: An enumeration representing the visual attribute being tested (e.g., `COLOR`, `PATTERN`, `TEXTURE`).
- **FidelityScore**: A quantitative metric representing the semantic alignment (CLIP-T) or motion coherence (optical flow) of a generated frame.
- **TextPrompt**: A natural language description generated by a lightweight LLM, tagged with its corresponding `GarmentFeatureClass`.
- **InferenceLog**: A record containing the timestamp, frame ID, latency, and fidelity scores for a single inference step.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The relative fidelity score for global color attributes is measured against the image-driven baseline, expecting a degradation of <10% (See US-1).
- **SC-002**: The relative fidelity score for local pattern density and texture roughness is measured against the image-driven baseline, expecting a degradation of >40% (See US-1).
- **SC-003**: The end-to-end inference latency is measured against the 50ms per frame threshold on a standard 8-core CPU, expecting ≤50ms for [deferred] of frames (See US-2).
- **SC-004**: The statistical significance of fidelity differences between feature classes is measured against a p-value threshold of 0.05 using ANOVA with Bonferroni correction (See US-3).
- **SC-005**: The sensitivity analysis is measured by the stability of the false-positive rate across the threshold sweep {0.01, 0.05, 0.1}, expecting no more than a [deferred] variance in the headline inconsistency rate (See US-3).
- **SC-006**: The total computational cost is measured against the free-tier CI limits (≤6 hours runtime, ≤7 GB RAM), expecting full completion within these bounds (See US-2).

## Assumptions

- The FashionChameleon pre-trained weights and codebase are accessible and compatible with the Python environment provided in the GitHub Actions free-tier runner.
- The Human3D dataset and the synthetic multi-garment descriptions generated by the lightweight LLM are available and fit within the disk limit when sampled or subsetted..
- The CLIP text encoder used for embedding generation and scoring is a standard, pre-trained model (e.g., ViT-B/32) that can run on CPU without quantization or CUDA acceleration.
- The "lightweight cross-attention adapter" added to the backbone does not significantly increase the model's memory footprint beyond the ~7 GB RAM limit when processing batches of 50 frames.
- The synthetic text descriptions generated by the lightweight LLM accurately reflect the ground-truth garment features (color, pattern, texture) and do not introduce systematic bias in the prompt generation process.
- The optical flow calculation for motion consistency can be performed using a CPU-tractable method (e.g., OpenCV's Farneback or a small pre-trained flow model) within a feasible time limit..
- The dataset of [deferred] clips is sufficiently balanced across the three feature classes (color, pattern, texture) to allow for valid ANOVA testing without requiring additional data augmentation.
- The "real-time" constraint of <50ms per frame is achievable on a standard 8-core CPU runner without requiring model pruning or distillation beyond the proposed lightweight adapter.
