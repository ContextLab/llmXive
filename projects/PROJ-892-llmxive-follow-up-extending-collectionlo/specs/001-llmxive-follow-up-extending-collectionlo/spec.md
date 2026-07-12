# Feature Specification: Quantization Robustness of Multi-Effect LoRA Adapters

**Feature Branch**: `001-lora-quantization-robustness`  
**Created**: 2026-07-06  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'CollectionLoRA: Collecting Multiple Effects in 1 LoRA via Multi-Teacher On-P'"

## User Scenarios & Testing

### User Story 1 - Baseline Fidelity Measurement (Priority: P1)

As a researcher, I need to generate images using the original FP CollectionLoRA adapter and a diverse set of 10 test prompts, then compute the cosine similarity between prompt embeddings and image features, so that I can establish a ground-truth baseline for concept adherence before applying any quantization.

**Why this priority**: This is the foundational control condition. Without a verified FP16 baseline, no subsequent comparison of quantization effects (INT8/INT4) is scientifically valid. It directly addresses the "Expected results" requirement to measure fidelity loss relative to the original.

**Independent Test**: Can be fully tested by running the generation pipeline on the CPU-only runner with FP16 weights, extracting CLIP embeddings, and calculating similarity scores. Success is defined by the successful completion of the ANOVA baseline group and the generation of a non-empty results CSV.

**Acceptance Scenarios**:

1. **Given** the FP16 CollectionLoRA adapter and base model are loaded on a CPU-only runner, **When** the system generates 10 images using distinct effect prompts, **Then** CLIP image embeddings are extracted and cosine similarity scores are computed and logged without errors.
2. **Given** the FP16 baseline generation is complete, **When** the system computes the LPIPS distance against a known reference (self-consistency check), **Then** the system outputs a scalar fidelity metric for each prompt to verify the generation pipeline is functional.

---

### User Story 2 - Quantization Impact Analysis (Priority: P2)

As a researcher, I need to apply post-training quantization (INT8 and INT4) to the LoRA weights without re-distillation, generate the same test images, and measure the drop in concept adherence, so that I can determine if quantization noise induces cross-effect interference (concept bleeding).

**Why this priority**: This is the core experimental variable. It directly tests the research question regarding the interaction between quantization noise and Asymmetric Orthogonal Prompting. It requires the baseline from US-1 to be valid for comparison.

**Independent Test**: Can be fully tested by running the quantization pipeline (FP16 -> INT8/INT4) on the CPU runner, generating images, and computing the delta in cosine similarity compared to the FP16 baseline. Success is defined by the ability to load quantized weights on CPU and produce a statistically significant dataset.

**Acceptance Scenarios**:

1. **Given** the FP16 weights are available, **When** the system applies zero-shot post-training quantization to INT8 and INT4 using `torch.ao.quantization` on a CPU-compatible backend, **Then** the system successfully loads the quantized adapters without GPU/CUDA dependencies.
2. **Given** the INT8 and INT4 adapters are loaded, **When** the system generates images for the 10 test prompts, **Then** the system computes the cosine similarity for each and records the difference (delta) from the FP16 baseline in the results dataset.
3. **Given** the quantized images are generated, **When** the system calculates LPIPS distance between quantized outputs and FP16 outputs, **Then** the system logs a pixel-fidelity loss metric for each quantization level to quantify pixel-space degradation.

---

### User Story 3 - Bayesian Statistical Analysis & Subspace Correlation (Priority: P3)

As a researcher, I need to perform a Bayesian hierarchical model analysis to test for significant differences across quantization levels and correlate the per-effect LoRA subspace rank with concept bleeding magnitude, so that I can confirm if low-rank subspaces are the specific failure point for INT4 quantization.

**Why this priority**: This transforms raw data into a scientific conclusion. It validates the "Expected results" hypothesis regarding INT4 bleeding and identifies the specific structural vulnerability (low-rank subspaces). The Bayesian approach is required to handle the small sample size (N=10) and high variance of generative data, replacing the underpowered ANOVA approach.

**Independent Test**: Can be fully tested by running the statistical analysis script on the generated CSV data. Success is defined by the output of Bayesian posterior distributions for quantization effects and a correlation coefficient with credible intervals, confirming the analysis logic works.

**Acceptance Scenarios**:

1. **Given** the full dataset of similarity scores and fidelity losses for FP16, INT8, and INT4, **When** the system executes a Bayesian hierarchical model, **Then** the system outputs posterior distributions indicating the probability of quantization level effects on concept adherence.
2. **Given** the Bayesian analysis results and the per-effect LoRA subspace ranks, **When** the system computes the correlation between rank and bleeding magnitude (mean adherence loss per effect), **Then** the system outputs a correlation coefficient and a 95% credible interval, testing significance via the posterior distribution.

### Edge Cases

- What happens if the quantized model fails to load on the CPU runner due to memory constraints (exceeding available system RAM)? The system must catch the `MemoryError` (Exit Code 137) and log a "Quantization Failure" flag for that specific quantization level rather than crashing the entire job.
- How does the system handle a test prompt that yields identical CLIP embeddings for both FP16 and INT4 (zero difference)? The system must correctly compute the delta as 0.0 and include it in the analysis without causing division-by-zero errors in variance calculations.
- What if the `torch.ao.quantization` backend is not available in the free-tier runner environment? The system must fallback to a pure `torch` quantization method or skip the specific quantization level with a clear "Backend Unavailable" log entry.

## Requirements

### Functional Requirements

- **FR-001**: System MUST load the pre-trained CollectionLoRA adapter (FP16) and the base model (e.g., Stable Diffusion 1.5) into CPU memory (minimum 16GB RAM) without requiring GPU/CUDA acceleration. (See US-1)
- **FR-002**: System MUST apply zero-shot post-training quantization to convert LoRA weights from FP16 to INT8 and INT4 formats using `torch.ao.quantization` without performing any gradient updates or re-distillation, ensuring quantization noise isolation. (See US-2)
- **FR-003**: The system shall generate a set of distinct images, each corresponding to a unique effect category prompt, utilizing the FP16, INT8, and INT4 adapters respectively. (See US-1, US-2)
- **FR-004**: System MUST extract CLIP image embeddings for all generated outputs and compute the cosine similarity between the prompt text embedding and the image embedding. (See US-1, US-2)
- **FR-005**: System MUST compute the LPIPS (Learned Perceptual Image Patch Similarity) distance between the quantized outputs and the FP16 baseline outputs to quantify pixel-space fidelity loss. (See US-2)
- **FR-006**: System MUST perform a Bayesian hierarchical model analysis as the primary statistical method to test for significant differences in concept adherence and fidelity loss across the three quantization levels (FP16, INT8, INT4), replacing Repeated-Measures ANOVA. (See US-3)
- **FR-007**: System MUST calculate the correlation between the per-effect LoRA subspace rank and the mean magnitude of concept bleeding for that effect across all prompts, testing significance via the Bayesian posterior distribution. (See US-3)
- **FR-008**: System MUST detect and log any memory overflow errors (Exit Code 137) on the CPU runner and gracefully skip the affected quantization level rather than terminating the entire pipeline. (See Edge Cases)
- **FR-009**: System MUST use a deterministic prompt selection procedure (e.g., a fixed seed list of prompts defined in the configuration) to ensure prompt diversity and reproducibility. (See FR-003, US-1)
- **FR-010**: System MUST retrieve the LoRA subspace rank for each distinct effect matrix within the CollectionLoRA adapter; if unavailable, the system MUST compute the effective rank via Singular Value Decomposition (SVD) on each per-effect weight matrix with a tolerance threshold of 1e-5. (See FR-007, US-3)
- **FR-011**: System MUST compute the Cross-Effect Similarity Ratio (CESR) by measuring the cosine similarity between a quantized output image embedding and the IMAGE embeddings of FP16 ReferenceImages for *other* effect prompts (excluding the target prompt) to detect concept bleeding. (See US-2, US-3)
- **FR-012**: System MUST utilize a Bayesian hierarchical model to account for the high variance and limited sample size (N=10) in the statistical validation of quantization effects. (See US-3, FR-006)
- **FR-013**: System MUST record content hashes (SHA-256) for all model weights and generated data artifacts in the `state/` YAML file to ensure versioning discipline. (See Constitution Principle V)
- **FR-014**: System MUST perform a posterior width analysis to verify that the Bayesian credible intervals for the quantization effect are sufficiently narrow (width ≤ 0.2) to justify the N=10 sample size; if not, the system MUST flag the result as "Underpowered". (See US-3)

### Key Entities

- **EffectAdapter**: A structured record containing the specific effect category (e.g., "oil painting"), the associated LoRA weight matrices, and the computed subspace rank.
- **ReferenceImage**: A record containing the image path and CLIP embedding generated using the FP16 baseline adapter, serving as ground truth for bleeding detection.
- **GenerationResult**: A record containing the generated image path, the quantization level (FP16/INT8/INT4), the CLIP cosine similarity score, the LPIPS distance, and the CESR score.
- **AnalysisMetric**: A derived record containing the statistical outputs (Bayesian posterior mean, credible intervals, correlation coefficient, correlation credible interval) for a specific comparison.
- **StateRecord**: A record containing the SHA-256 hashes of all input models and output artifacts.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Concept adherence is measured by the cosine similarity between prompt text embeddings and generated image embeddings, referenced against the FP16 baseline values. (See FR-004, US-1)
- **SC-002**: Pixel fidelity loss is measured by the LPIPS distance between quantized outputs and FP16 baseline outputs, referenced against the zero-difference ideal. Semantic fidelity loss is measured by the CESR (image-to-image similarity), referenced against the zero-bleeding ideal. (See FR-005, FR-011, US-2)
- **SC-003**: Statistical significance of quantization impact is measured by the Bayesian posterior probability of effect, referenced against the alpha threshold of 0.05. (See FR-006, US-3)
- **SC-004**: Subspace vulnerability is measured by the Pearson correlation coefficient between the per-effect LoRA subspace rank and mean concept bleeding magnitude per effect, referenced against the null hypothesis of zero correlation (verified via 95% credible interval). (See FR-007, FR-010, US-3)
- **SC-005**: Compute feasibility is measured by the total job duration on the GitHub Actions `ubuntu-latest` runner (multi-core CPU, 16GB RAM), referenced against the hard limit of ≤6 hours. (See FR-001, US-1)
- **SC-006**: Concept bleeding is measured by the Cross-Effect Similarity Ratio (CESR), referenced against the baseline FP16 CESR values. (See FR-011, US-2)

## Assumptions

- **Assumption about data/environment**: The free-tier GitHub Actions runner provides sufficient RAM (≥16GB) to load the base Stable Diffusion model and the quantized LoRA adapters in CPU mode without swapping to disk.
- **Assumption about scope boundaries**: The study assumes that "post-training quantization" implies zero-shot quantization; any requirement for re-distillation or fine-tuning after quantization is explicitly out of scope for this experiment.
- **Assumption about target users**: The primary "user" is the research pipeline itself; the output is a statistical report, not a user-facing application interface.
- **Assumption about model availability**: The specific CollectionLoRA adapter containing a set of effects and the corresponding base model (Stable Diffusion 1.5 or 2.1) are publicly available on HuggingFace and can be downloaded within the 6-hour job limit.
- **Assumption about metric validity**: CLIP embeddings and LPIPS distances are accepted as valid proxies for "concept adherence" and "pixel fidelity loss" respectively. CESR (image-to-image) is accepted as a valid proxy for "concept bleeding" when comparing against FP16 ReferenceImages.
- **Assumption about quantization backend**: The system assumes that `torch.ao.quantization` is available in the runner environment to load INT8/INT4 weights and perform the quantization step; `auto-gptq` is explicitly excluded due to CUDA requirements.
- **Assumption about statistical power**: The sample size of a limited number of distinct prompts is acknowledged; the system MUST employ Bayesian hierarchical modeling with informative priors to mitigate low statistical power risks.
- **Assumption about threshold justification**: The selection of INT8 and INT4 as the quantization levels is based on community standards for edge deployment; no additional sensitivity analysis is required for the choice of these specific bit-widths as they represent the standard trade-off points.
- **Assumption about input data**: The input CollectionLoRA adapter MUST contain at least 5 distinct effects to ensure statistical validity for the per-effect correlation analysis.
- **Assumption about reference generation**: ReferenceImages used for CESR calculation MUST be generated using the FP16 baseline adapter to serve as a valid ground truth for visual bleeding detection.
- **Assumption about noise isolation**: Zero-shot quantization via `torch.ao.quantization` is assumed to isolate quantization noise as required by Constitution Principle VI, without introducing confounding variables from re-distillation.