# Feature Specification: llmXive follow-up: extending "DomainShuttle: Freeform Open Domain Subject-driven Text-to-video Gener"

**Feature Branch**: `001-gene-regulation`  
**Created**: 2026-07-13  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'DomainShuttle: Freeform Open Domain Subject-driven Text-to-video Gener'"

## User Scenarios & Testing

### User Story 1 - Data Acquisition and Feature Extraction (Priority: P1)

The research system MUST download a curated subset of diverse subjects from the WebVid-10M dataset, calculate a visual complexity score for each, and extract high-dimensional "intrinsic subject feature" embeddings using the frozen DomainShuttle encoder.

**Why this priority**: This is the foundational data layer. Without valid, complexity-scored embeddings, no compression analysis or identity fidelity testing can occur. It represents the "Input" phase of the scientific method.

**Independent Test**: The pipeline can be tested by running the data loader and encoder, then verifying that the output directory contains a complete set of tensors and a corresponding CSV of complexity scores, with no missing values.

**Acceptance Scenarios**:

1. **Given** the WebVid-10M dataset is accessible, **When** the system processes the subset of 100 subjects, **Then** it must generate a CSV file containing 100 rows with unique IDs and pre-computed visual complexity scores.
2. **Given** the DomainShuttle encoder is loaded in frozen mode, **When** the system processes the reference images, **Then** it must output high-dimensional tensor files (e.g., `.pt` or `.npy`) for each subject without modifying the encoder weights.

---

### User Story 2 - CPU-Optimized Compression and Dimensionality Sweep (Priority: P2)

The system MUST train lightweight, CPU-only Autoencoders to compress the extracted high-dimensional embeddings into latent vectors of varying dimensions (specifically 16, 32, 64, 128, and 256), using a reconstruction loss prioritizing cosine similarity between the reconstructed output vector and the original input embedding.

**Why this priority**: This implements the core hypothesis test: scaling dimensionality against identity preservation. It must run on free CPU hardware to be feasible.

**Independent Test**: The training loop can be tested independently by verifying that for each target dimension, a trained model checkpoint is saved, and the training log shows convergence of the cosine similarity loss without GPU utilization.

**Acceptance Scenarios**:

1. **Given** the high-dimensional embeddings from User Story 1, **When** the Autoencoder is trained for a target dimension of 32, **Then** the system must save a model checkpoint that reconstructs the input with a mean cosine similarity measured against a configurable fidelity target (default [deferred]) on the validation split.
2. **Given** the training environment has no GPU, **When** the compression model trains, **Then** the training duration is measured against the CI job time limit.

---

### User Story 3 - Identity Fidelity Validation and Phase Transition Detection (Priority: P3)

The system MUST generate synthetic videos using the compressed vectors and text prompts, compute CLIP Image Similarity scores (image-image) to quantify identity preservation, and correlate these scores with visual complexity to identify a "phase transition" point using segmented regression.

**Why this priority**: This delivers the final scientific result: the relationship between complexity and the minimum dimensionality required for fidelity. It validates the "Phase Transition" hypothesis.

**Independent Test**: The validation pipeline can be tested by running the generation for a single subject at a single dimension, generating the video, computing the CLIP Image Similarity score, and verifying the output metric matches the expected range for that complexity level.

**Acceptance Scenarios**:

1. **Given** a trained Autoencoder for dimension 64 and a reference subject, **When** the system generates a video in a distinct style domain, **Then** the CLIP Image Similarity score between the generated frames and the reference image must be recorded and stored.
2. **Given** the full set of scores across all dimensions and complexities, **When** the analysis script runs, **Then** it must output a plot or table identifying if a non-linear degradation (phase transition) occurs, detected via segmented regression breakpoint analysis.

### Edge Cases

- **What happens when** a subject's visual complexity score is an outlier (e.g., extreme texture density) that causes the Autoencoder to fail convergence? The system must flag this subject as "failed training" and exclude it from the final correlation analysis, logging the specific error.
- **How does the system handle** a situation where the CPU-only generation pipeline exceeds the 6-hour CI job limit? The system must implement a timeout mechanism per sample (e.g., a configurable duration) and record the result as "timeout" rather than crashing the entire job.
- **What happens when** the CLIP Image Similarity score is ambiguous? The system must treat the fidelity retention threshold as a configurable value (default [deferred]) but log the exact value to allow for sensitivity analysis later.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download exactly 100 diverse subjects from WebVid-10M and compute a visual complexity score for each using a pre-defined metric (e.g., edge density or texture variance) (See US-1).
- **FR-002**: System MUST extract high-dimensional embeddings using the frozen DomainShuttle encoder and store them as persistent tensors without modifying the encoder weights (See US-1).
- **FR-003**: System MUST implement a CPU-only Autoencoder architecture that supports compression targets of 16, 32, 64, 128, and 256 dimensions (See US-2).
- **FR-004**: System MUST train the Autoencoders using a loss function that calculates cosine similarity between the reconstructed output vector and the original input embedding to prioritize subject identity over pixel-perfect reconstruction (See US-2).
- **FR-005**: System MUST generate synthetic videos for each compressed latent vector across 3 distinct style domains (specifically: 'Anime', 'Photorealistic', 'Sketch') using the frozen DomainShuttle generator (See US-3).
- **FR-006**: System MUST compute CLIP Image Similarity scores (image-image) between generated video frames and the original reference image to quantify identity preservation (See US-3).
- **FR-007**: System MUST perform a correlation analysis between the pre-computed visual complexity scores and the minimum dimensionality required to maintain identity fidelity, explicitly modeling the degradation curve and identifying the breakpoint where non-linear degradation occurs (See US-3).

### Key Entities

- **Subject**: A unique video/image entity containing a visual representation of a specific object or person, characterized by a `complexity_score` and `raw_embedding`.
- **CompressedVector**: A reduced-dimensionality tensor derived from the `Subject`'s embedding, characterized by `target_dimension` and `reconstruction_loss`.
- **GeneratedVideo**: A synthetic video output produced by the `CompressedVector` and a text prompt, characterized by `style_domain` and `identity_score`.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The Autoencoder convergence loss is measured against a configurable target defined in the implementation phase (See US-2).
- **SC-002**: The minimum dimensionality required to achieve a CLIP Image Similarity score >= [configurable fidelity threshold] is measured against the pre-computed visual complexity score for each subject (See US-3).
- **SC-003**: The presence of a "phase transition" (non-linear degradation) in identity fidelity is measured by the segmented regression breakpoint or second derivative of the fidelity curve for high-complexity subjects (See US-3).
- **SC-004**: The total compute time for the full pipeline (extraction, training, generation, analysis) is measured against the 6-hour free-tier CI limit (See US-2).

## Assumptions

- The WebVidM dataset is accessible via the provided download links and contains sufficient metadata to filter for 100 diverse subjects with varying visual complexity.
- The pre-trained DomainShuttle encoder weights are available in a format compatible with CPU-only PyTorch inference without requiring CUDA-specific quantization or loading flags.
- The visual complexity score derived from the reference images (e.g., based on edge density) is a valid proxy for "semantic complexity" as defined in the research question.
- The CLIP model used for identity validation is sufficiently lightweight to run on a multi-core CI runner with limited RAM resources. without exceeding memory limits.
- The "phase transition" hypothesis assumes that identity is concentrated in a compact manifold; if the data shows linear degradation, the assumption of a compact manifold is falsified, which is a valid scientific outcome.
- The 3 distinct style domains required for validation (Anime, Photorealistic, Sketch) are available in the DomainShuttle documentation without requiring additional fine-tuning.