# Feature Specification: llmXive Follow-up: OPD Generalization Gap in Unified Diffusion

**Feature Branch**: `001-opd-generalization-gap`  
**Created**: 2026-07-15  
**Status**: Draft  
**Input**: User description: "Does the on-policy distillation (OPD) stage in unified diffusion frameworks induce a measurable degradation in zero-shot generalization performance when evaluated on prompts strictly outside the training distribution of the reward-guided teachers?"

## User Scenarios & Testing

### User Story 1 - Data Acquisition and Prompt Curation (Priority: P1)

As a researcher, I need to acquire the pre-trained base Qwen-Image-2.0 weights, the unified Qwen-Image-2.0-RL student weights, and two curated prompt sets (in-distribution and out-of-distribution) so that I can establish the ground truth for comparing model generalization.

**Why this priority**: Without the correct model weights and a rigorously defined, leakage-free prompt set, no subsequent analysis can be performed. The validity of the entire study hinges on the OOD prompts being distinct from the training distribution.

**Independent Test**: The system can be tested by verifying the existence of the model weights in the local cache and confirming that the OOD prompt set contains zero items from the known Qwen-Image-Bench training distribution.

**Acceptance Scenarios**:

1. **Given** the model repositories are accessible, **When** the data acquisition script runs, **Then** both the base and RL-unified model weights are downloaded and verified to match the expected SHA-256 checksums.
2. **Given** the prompt curation module, **When** it generates the [deferred] prompts (balanced in-distribution and OOD samples), **Then** the OOD set contains only abstract physics concepts and obscure historical artifacts with no overlap with the Qwen-Image-Bench training corpus, and the latent-space embedding similarity check confirms a cosine similarity < 0.3 to the training set centroids.

---

### User Story 2 - CPU-Only Inference Execution (Priority: P2)

As a researcher, I need to run the image generation pipelines for both models on a CPU-only environment using `diffusers` with float16 precision and CPU offloading so that I can generate evaluation samples within the free-tier compute constraints.

**Why this priority**: The core hypothesis testing requires generating images. This step must be feasible on the free GitHub Actions runner (CPU, ~7GB RAM) without requiring GPU acceleration, which is unavailable.

**Independent Test**: The system can be tested by running the inference script on a single CPU core and verifying that multiple images are generated per prompt for both models without running out of memory (OOM) or exceeding the job time limit.

**Acceptance Scenarios**:

1. **Given** the models are loaded in CPU mode, **When** the inference loop processes an initial set of prompts, **Then** images are generated within a reasonable time window (e.g., < 10 minutes per batch) and the process does not crash due to memory constraints.
2. **Given** a prompt from the OOD set, **When** the RL-unified model generates an image, **Then** the output is saved to the local filesystem in a structured directory format (e.g., `outputs/rl-unified/prompt-id.png`).

---

### User Story 3 - Statistical Analysis of Generalization Gap (Priority: P3)

As a researcher, I need to compute the mean score degradation between the base and RL models across both datasets and perform a non-parametric test on the "Generalization Gap" so that I can determine if the OPD stage caused a statistically significant loss in zero-shot generalization.

**Why this priority**: This is the final analytical step that directly answers the research question. It transforms raw generation scores into a scientific conclusion regarding the trade-off between specialization and generalization.

**Independent Test**: The system can be tested by providing a synthetic dataset with known mean differences and verifying that the statistical analysis module correctly calculates the Wilcoxon statistic, p-value, and the "Generalization Gap" metric.

**Acceptance Scenarios**:

1. **Given** the scored image data for both models on both datasets, **When** the analysis script runs, **Then** it outputs a report containing the mean score degradation (Base - RL) for In-Distribution and OOD sets.
2. **Given** the calculated degradation values, **When** the Wilcoxon signed-rank test is performed on the difference (OOD degradation - In-Distribution degradation) with A large number of bootstrap iterations, **Then** the script reports whether the "Generalization Gap" is statistically significant (p < 0.05) or null.

---

### Edge Cases

- **What happens when the CPU memory limit is exceeded?** The system MUST implement automatic garbage collection and process images in smaller batches (e.g., A batch of prompts processed simultaneously.) to prevent OOM crashes.
- **How does the system handle a model weight download failure?** The system MUST retry the download up to 3 times with exponential backoff before failing the job and logging the specific error code.
- **What happens if the OOD prompt set is accidentally contaminated?** The validation script MUST detect any prompt overlap with the training distribution (textual or latent) and abort the analysis with a `[CRITICAL: DATA LEAKAGE DETECTED]` error.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download the pre-trained base Qwen-Image-2.0 weights and the unified Qwen-Image-2.0-RL student weights from the Hugging Face model hub, verifying SHA-256 checksums against the repository manifest. (See US-1)
- **FR-002**: System MUST generate two distinct prompt sets of sufficient size to ensure statistical robustness: one in-distribution (mirroring Qwen-Image-Bench) and one out-of-distribution (abstract physics/historical artifacts). (See US-1)
- **FR-003**: System MUST execute image generation using `diffusers` with `torch_dtype=torch.float16` and CPU offloading, ensuring no GPU usage. (See US-2)
- **FR-004**: System MUST generate a set of multiple images per prompt for both the base and RL-unified models to ensure statistical robustness within memory constraints. (See US-2)
- **FR-005**: System MUST score all generated images using quantized (INT8) VLM-based reward models (Aesthetics, Prompt Adherence, Identity Preservation) loaded in CPU mode. (See US-3)
- **FR-006**: System MUST compute the mean score degradation (Base Score - RL Score) separately for the in-distribution and OOD datasets. (See US-3)
- **FR-007**: System MUST perform a Wilcoxon signed-rank test with a substantial number of bootstrap resampling iterations to determine if the "Generalization Gap" (OOD degradation minus In-Distribution degradation) is significantly different from zero. (See US-3)
- **FR-008**: System MUST validate the "Generalization Gap" against an independent ground-truth metric (e.g., a subset of human evaluations or an external unbiased benchmark) to rule out circular dependency on the reward models. (See US-3)
- **FR-009**: System MUST verify the OOD prompt set's latent-space independence by ensuring the cosine similarity between OOD prompt embeddings and the training set centroids is < 0.3. (See US-1)

### Key Entities

- **ModelWeights**: Represents the binary state of the neural network (Base vs. RL-Unified), containing the architecture definition and learned parameters.
- **PromptSet**: A collection of text prompts categorized by distribution type (In-Distribution or Out-of-Distribution), used as input for generation.
- **GeneratedImage**: An image artifact produced by a model in response to a prompt, associated with a specific prompt ID and model version.
- **EvaluationScore**: A numeric value (0-1) assigned to a generated image by a VLM reward model, representing a specific metric (e.g., Aesthetics).

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The "Generalization Gap" (difference in mean score degradation between OOD and In-Distribution sets) is measured against a null hypothesis of zero using a Wilcoxon signed-rank test with bootstrap validation. (See US-3)
- **SC-002**: The statistical power of the test is measured against the requirement for a minimum sample size sufficient for statistical power per set to detect a medium effect size (Cohen's d = 0.5) with [deferred] power. (See US-3)
- **SC-003**: The computational feasibility is measured against the constraint of completing the full inference and analysis pipeline within 6 hours on a 2-core CPU runner with ≤7 GB RAM. (See US-2)
- **SC-004**: The validity of the OOD set is measured against the requirement of Zero overlap with the known training distribution of the reward-guided teachers (textual and latent). (See US-1)
- **SC-005**: The consistency of the evaluation is measured by the variance of scores across the generated images per prompt; if the variance exceeds a predefined threshold, the prompt is flagged for manual review. (See US-3)

## Assumptions

- **Assumption about dataset-variable fit**: The pre-trained Qwen-Image-2.0 and Qwen-Image-2.0-RL weights are available and compatible with the `diffusers` library version used in the runner; if the model architecture requires a specific, unlisted dependency, the analysis will fail.
- **Assumption about inference feasibility**: Running the quantized (INT8) VLM-based reward models (Aesthetics, Prompt Adherence, Identity Preservation) in CPU mode with float16 precision will not exceed the 7 GB RAM limit when processing multiple images per prompt; if memory usage spikes, the batch size will be reduced dynamically.
- **Assumption about prompt curation**: The manually curated OOD prompt set (abstract physics and obscure historical artifacts) is sufficiently distinct from the Qwen-Image-Bench training distribution to serve as a valid out-of-distribution test; the latent-space verification step (FR-009) ensures >99% accuracy in preventing leakage.
- **Assumption about statistical validity**: The score distributions generated by the VLM reward models are handled by the non-parametric Wilcoxon test and bootstrap resampling, making the normality assumption unnecessary; if the data is heavily skewed, the bootstrap method accounts for it.
- **Assumption about compute constraints**: The total number of generated images ([deferred] prompts * 3 images * 2 models = 6,000 images) can be processed within the job limit on the free-tier runner; if the runtime exceeds 6 hours, the sample size will be reduced to a manageable number of prompts per set.