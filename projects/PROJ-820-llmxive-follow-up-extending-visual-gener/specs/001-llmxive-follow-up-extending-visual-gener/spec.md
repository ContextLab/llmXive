# Feature Specification: llmXive follow-up: extending "Visual Generation in the New Era: An Evolution from Atomic Mapping to "

**Feature Branch**: `001-llmxive-followup`  
**Created**: 2026-07-11  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'Visual Generation in the New Era: An Evolution from Atomic Mapping to '"

## User Scenarios & Testing

### User Story 1 - Generate Physics-Constrained Prompts (Priority: P1)

**Journey**: A researcher prepares a dataset of 500 complex scene descriptions and uses the system to generate corresponding "Symbolic-Physics" prompts. The system simulates basic physics (gravity, collision) on a CPU to create JSON constraints, then appends natural language descriptors of these constraints to the original text prompts.

**Why this priority**: This is the core data preparation step. Without the ability to generate the experimental condition prompts (Text + Physics), the comparative study cannot exist. It is the foundation for all downstream generation and analysis.

**Independent Test**: Can be fully tested by running the `pymunk` simulation script on a single CPU core and verifying that the output JSON files contain valid bounding box and collision data, and that the prompt engineering script successfully concatenates these rules into the text prompts without syntax errors.

**Acceptance Scenarios**:

1. **Given** a list of 500 scene descriptions (e.g., "a cup balancing on a tilted book"), **When** the system processes them through the CPU simulation engine, **Then** it must output a set of valid JSON files containing minimal physics constraints (bounding boxes, center-of-gravity, collision rules) for every scene.
2. **Given** a scene description and its corresponding physics JSON, **When** the prompt engineering script runs, **Then** it must append a natural language string describing the physical rules (e.g., "Object A must be strictly above Object B; no interpenetration allowed") to the original prompt, resulting in a new prompt string.

---

### User Story 2 - Generate Image Baselines and Experimental Groups (Priority: P2)

**Journey**: The researcher executes the image generation pipeline. The system takes the original text prompts (Baseline Group) and the physics-enhanced prompts (Experimental Group) and generates images using a CPU-optimized diffusion model. The system ensures identical random seeds are used where possible to isolate the effect of the prompt.

**Why this priority**: This executes the core experiment. It produces the visual data required to measure the reduction in causal hallucinations. It is dependent on US-1 but independent of the analysis logic.

**Independent Test**: Can be fully tested by running the generation script with a small subset (e.g., 5 scenes) and verifying that two distinct image sets are produced (one from text-only, one from physics-enhanced) and that the generation process completes within the 6-hour CPU limit without GPU errors.

**Acceptance Scenarios**:

1. **Given** the dataset of 500 baseline prompts and 500 experimental prompts, **When** the generation script is executed on a CPU-only runner, **Then** it must produce a sufficient number of images (per group) using a distilled/quantized model that runs in default precision without CUDA dependencies.
2. **Given** a specific scene ID, **When** the system generates both the baseline and experimental images, **Then** it must use the same random seed for both generations (where the model architecture permits) to ensure the only variable difference is the prompt content.

---

### User Story 3 - Evaluate Geometric Consistency and Statistical Significance (Priority: P3)

**Journey**: The researcher runs the evaluation pipeline. The system uses a lightweight object detector (YOLOv8n) to extract bounding boxes from the generated images, compares them against the original JSON physics rules, calculates violation rates for both groups, and performs a two-proportion z-test to determine statistical significance.

**Why this priority**: This provides the answer to the research question. It transforms raw images into a measurable result (violation rate reduction) and validates the hypothesis. It is the final step that delivers the "World-Modeling" evidence.

**Independent Test**: Can be fully tested by feeding a small set of pre-generated images with known ground-truth violations into the evaluation script and verifying that the violation counts match manual inspection and the statistical test output includes a p-value.

**Acceptance Scenarios**:

1. **Given** a set of generated images and their corresponding ground-truth physics JSON, **When** the evaluation script runs, **Then** it must detect objects using a lightweight detector and calculate a "violation rate" (percentage of images with floating objects or interpenetration) for both the baseline and experimental groups.
2. **Given** the calculated violation rates, **When** the statistical analysis module runs, **Then** it must perform a two-proportion z-test (or Fisher's Exact Test if sample size constraints apply) and output a p-value to determine if the reduction in violations in the experimental group is statistically significant (p < 0.05).

### Edge Cases

- **What happens when** the object detector fails to identify an object in a complex scene? The system MUST default to counting the image as a violation if the object is not detected with confidence ≥0.7. If confidence is <0.7, the image is flagged for manual review, but the default automated metric treats it as a violation to be conservative.
- **How does the system handle** prompts where the physics simulation generates contradictory constraints (e.g., "A is above B" and "B is above A")? The system must detect logical contradictions during the JSON generation phase (US-1) and exclude such scenes from the dataset, logging them as "Invalid Physics Rules."
- **What happens when** the CPU-only diffusion model fails to generate an image within the 6-hour window or runs out of memory? The system must retry the generation up to 3 times; if it fails again, it must mark the specific scene as "Generation Failure" and exclude it from the final statistical denominator, recording the failure count.

## Requirements

### Functional Requirements

- **FR-001**: System MUST simulate basic physics (bounding boxes, collision rules) for a representative set of scene descriptions using `pymunk` on a single CPU core to generate JSON constraints. (See US-1)
- **FR-002**: System MUST append natural language descriptors of the generated physics constraints to the original text prompts to create the experimental condition. (See US-1)
- **FR-003**: System MUST generate images for both baseline (text-only) and experimental (physics-enhanced) groups using a CPU-optimized, distilled diffusion model without requiring GPU or CUDA hardware. (See US-2)
- **FR-004**: System MUST extract object bounding boxes from generated images using a lightweight object detector (e.g., YOLOv8n) and compare them against the ground-truth JSON physics rules to calculate a geometric violation rate. (See US-3)
- **FR-005**: System MUST perform a two-proportion z-test on the violation rates of the two groups to determine if the difference is statistically significant (p < 0.05). (See US-3)
- **FR-006**: System MUST log any scenes where the physics simulation produces logical contradictions or where image generation fails, excluding them from the final statistical analysis while recording the count. (See US-3)
- **FR-007**: System MUST utilize a CPU-optimized diffusion model that supports deterministic generation via explicit random seed locking. If the specific model architecture only permits approximate seed control, the system MUST implement a fallback mechanism: generate N=5 candidate images per prompt using the same seed and select the one with the highest structural similarity to a reference geometry. The reference geometry is defined as the set of 2D bounding box coordinates projected from the `pymunk` JSON onto a virtual canvas matching the generation output resolution (e.g., 512x512). The baseline and experimental groups MUST be generated with identical seeds to isolate the prompt variable, with a tolerance for deviation of ≤ 1 pixel in bounding box coordinates due to unavoidable floating-point variance. (See US-2)
- **FR-008**: System MUST perform a power analysis to confirm that N=500 per group provides sufficient statistical power (≥0.8) to detect a [deferred] reduction in violation rates. If the expected cell counts in the contingency table are <5, the system MUST switch to Fisher's Exact Test instead of the z-test. (See US-3)
- **FR-009**: System MUST explicitly label the "violation rate" metric as "Prompt Adherence Rate" in all reports to acknowledge that the study measures consistency between prompt instructions and output, not the model's internal understanding of physics. (See US-3)
- **FR-010**: System MUST report the detection confidence distribution for all objects. If the False Negative Rate (FNR) of the detector on a held-out validation set exceeds a predefined acceptable threshold, the system MUST apply a conservative correction factor to the violation rate or switch to a qualitative 'Pass/Fail' assessment. (See US-3)

### Key Entities

- **SceneDescription**: A text string describing a complex visual scene (e.g., "a cup balancing on a tilted book").
- **PhysicsConstraint**: A JSON object containing bounding box coordinates, center-of-gravity, and collision rules derived from `pymunk` simulation.
- **GeneratedImage**: An image file produced by the diffusion model, associated with either a baseline or experimental prompt.
- **ViolationInstance**: A boolean flag and metadata indicating whether a generated image violates the ground-truth physics rules (e.g., floating object, intersection).

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The reduction in geometric violation rate (percentage of images with floating objects or interpenetration) is measured against the baseline group's violation rate. (See FR-005)
- **SC-002**: The statistical significance of the improvement is measured against the standard threshold of p < 0.05 using a two-proportion z-test (or Fisher's Exact Test if required by FR-008). (See FR-005, FR-008)
- **SC-003**: The computational feasibility of the pipeline is measured against the constraint of running on a CPU-only runner with ≤ 7 GB RAM and completing within 6 hours. (See FR-003)
- **SC-004**: The validity of the physics simulation is measured against the logical consistency of the generated JSON constraints (contradiction rate must be < 5% in valid scenes). (See FR-001)
- **SC-005**: The "Prompt Adherence Rate" (violation rate) is reported with a confidence interval derived from the binomial proportion, acknowledging the measurement noise defined in FR-010. (See FR-009, FR-010)

## Assumptions

- The dataset of scenes is curated such that the required physics variables (gravity, collision) are inferable from the text description without needing external sensor data.
- The CPU-optimized diffusion model (e.g., a distilled SD variant) is capable of generating images of sufficient resolution for YOLOv8n object detection to extract bounding boxes reliably.
- The `pymunk` library is available in the execution environment and can run a sufficient number of simulations within the 6-hour time budget.
- The geometric evaluation (object detection) is treated as the operational ground truth for "visual reality" for the purpose of this study, acknowledging that detection errors may introduce noise but are necessary for automated evaluation.
- The study is observational in nature regarding the model's internal state; findings are framed as associational between prompt conditioning and output geometry, not causal regarding the model's internal "understanding" of physics.
- The "Symbolic-Physics Prompter" assumes that natural language models can reliably interpret and inject the appended physics rules into the generation process without ignoring them.
- The system relies on the Law of Large Numbers (N=500) to average out the variance introduced by diffusion model stochasticity. While identical random seeds are used to control the noise input, the change in prompt conditioning vector fundamentally alters the generation trajectory; thus, the comparison of geometry relies on statistical aggregation across the sample rather than seed-locking alone to ensure "apples-to-apples" correspondence.