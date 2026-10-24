# Feature Specification: llmXive follow-up: extending "Perception or Prejudice: Can MLLMs Go Beyond First Impressions of Pers"

**Feature Branch**: `001-gene-regulation`  
**Created**: 2026-07-19  
**Status**: Draft  
**Input**: User description: "Does augmenting Multimodal Large Language Models (MLLMs) with explicit, text-based social priors (e.g., cultural norms, situational context) via retrieval-augmented prompting significantly reduce the 'Prejudice Gap'—where correct trait ratings lack behavioral grounding—or is this failure mode strictly inherent to the models' visual feature extraction capabilities?"

## User Scenarios & Testing

### User Story 1 - Baseline Prejudice Rate Calculation (Priority: P1) (See US-1)

The research team needs to establish the baseline “Prejudice Rate” (PR) and “Holistic‑Grounding Rate” (HR) for a selected ensemble of MLLMs using the standard prompting protocol on the MM‑OCEAN validation subset. This step is critical to quantify the magnitude of the "Prejudice Gap" before any intervention is applied, ensuring the study has a valid control condition.

**Why this priority**: Without a rigorous baseline measurement, the study cannot determine if the intervention has any effect. This is the foundational data point for all subsequent analysis and hypothesis testing.

**Independent Test**: The system can be tested by running the baseline prompt on a subset of video samples and verifying that the output includes a trait rating, a reasoning string, and a grounding score derived from the metadata, with the PR calculated as the percentage of correct ratings lacking valid behavioral evidence.

**Acceptance Scenarios**:

1. **Given** the MM-OCEAN validation subset and the standard prompt template, **When** the system processes a video sample through an MLLM, **Then** the output contains a trait rating, a textual justification, and a grounding score that matches the definition of "Prejudice" (correct rating, invalid grounding) or "Holistic‑Grounding" (correct rating, valid grounding).
2. **Given** a batch of 27 MLLMs, **When** the baseline execution completes, **Then** the system reports a baseline Prejudice Rate (PR) and Holistic‑Grounding Rate (HR) for each model, calculated over the full validation subset.

### User Story 2 - Context‑Grounded Intervention Execution (Priority: P2) (See US-2)

The research team needs to execute the "Context‑Grounded Chain-of-Thought" intervention, where a static JSON knowledge base of social norms and situational scripts is retrieved and injected into the prompt for each video sample. This allows the team to measure if adding external context reduces the reliance on visual heuristics.

**Why this priority**: This is the core experimental intervention. It tests the primary hypothesis that the "Prejudice Gap" is a reasoning deficit solvable by context injection rather than a visual limitation.

**Independent Test**: The system can be tested by processing a single video sample with the intervention prompt and verifying that the retrieved context profile (e.g., "job interview," "East Asian setting") is present in the input and that the model's reasoning explicitly references this context.

**Acceptance Scenarios**:

1. **Given** a video sample and its metadata, **When** the system retrieves the corresponding context profile from the static JSON knowledge base and injects it into the prompt, **Then** the model's output reasoning explicitly cites or incorporates the injected social norms before deriving the trait rating.
2. **Given** the full validation subset, **When** the intervention execution completes, **Then** the system calculates the new Prejudice Rate (PR_intervention) for each model and stores the results alongside the baseline metrics.

### User Story 3 - Statistical Significance and Ablation Analysis (Priority: P3) (See US-3)

The research team needs to perform a paired statistical test (mixed‑effects model as primary analysis) to compare the baseline and intervention Prejudice Rates across the model ensemble, and run a control ablation with random noise to isolate the effect of relevant social priors.

**Why this priority**: This step transforms raw data into a scientific conclusion, determining if the observed reduction in the Prejudice Gap is statistically significant and not due to random variation or prompt length effects.

**Independent Test**: The system can be tested by generating a synthetic dataset with known effect sizes and verifying that the statistical test correctly identifies significance (or lack thereof) and that the ablation condition shows no significant improvement compared to the baseline.

**Acceptance Scenarios**:

1. **Given** the baseline and intervention PRs for all 27 models, **When** the statistical analysis module runs a mixed‑effects model (model as random effect, video sample as random effect), **Then** the system outputs a p‑value and a confidence interval indicating whether the reduction in PR is statistically significant (p < 0.05).
2. **Given** the control condition (random noise prompt), **When** the ablation analysis is performed, **Then** the system confirms that the PR in the control condition does not differ significantly from the baseline, isolating the effect of the relevant social priors.

### User Story 4 - Feasibility and Resource Constraints (Priority: P2) (See US-4)

The research team must ensure that the full experimental pipeline completes within the computational budget provided by GitHub Actions free tier (≤6 hours total runtime, ≤7 GB RAM) while processing all models and conditions.

**Why this priority**: Without meeting the runtime and memory constraints, the experiment cannot be executed reproducibly in the CI environment, jeopardizing reproducibility and reproducibility reporting.

**Independent Test**: The system can be tested by instrumenting the pipeline to record total wall‑clock time and peak memory usage; a successful run must report ≤6 hours total runtime and ≤7 GB peak RAM.

**Acceptance Scenarios**:

1. **Given** the full set of 27 models, 200 video samples, and three conditions (baseline, intervention, noise control), **When** the pipeline executes, **Then** the logged runtime ≤ 6 hours and peak RAM ≤ 7 GB.
2. **Given** a scenario where the projected runtime exceeds 6 hours, **When** the fallback strategy (reduce to top‑15 models or sample 10 frames per video) is applied, **Then** the pipeline completes within the resource limits.

---

### Edge Cases

- **What happens when** the MM-OCEAN metadata lacks a specific situational tag required for context retrieval? **System handles** this by injecting a generic "neutral context" profile and logging a warning, ensuring the pipeline does not crash but flags the data gap.
- **How does system handle** MLLMs that fail to generate a valid JSON response or reasoning string due to timeout or hallucination? **System handles** this by marking the sample as "invalid" for that specific model, excluding it from the PR calculation, and logging the failure reason for later review.
- **What happens when** the dataset contains video samples with ambiguous or conflicting behavioral evidence in the metadata? **System handles** this by applying a "grounding uncertainty" flag (see FR‑011) and excluding these samples from the primary PR calculation to maintain measurement validity.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and parse the MM-OCEAN validation subset and associated metadata from the specified repository to serve as the primary data source (See US-1).
- **FR-002**: System MUST construct and maintain a static, CPU‑accessible JSON knowledge base mapping video metadata (e.g., setting, culture) to curated social norms and situational scripts for retrieval (See US-2).
- **FR-003**: System MUST execute the baseline prompting protocol on the 27 distinct MLLMs listed in Table 2 of arXiv:2605.22109 to generate trait ratings, reasoning strings, and grounding scores for each sample (See US-1). *Ground‑truth trait ratings are obtained from expert annotations provided with MM‑OCEAN; a rating is considered correct when it matches the expert label exactly.* (See FR-018)
- **FR-004**: System MUST implement the "Context‑Grounded Chain‑of‑Thought" prompt template that retrieves and injects the relevant social prior before the reasoning step (See US-2).
- **FR-005**: System MUST perform a mixed‑effects statistical analysis (primary) comparing baseline and intervention Prejudice Rates, treating model and video sample as random effects, and report p‑values and confidence intervals; a paired t‑test or Wilcoxon test may be used as a secondary check (See US-3).
- **FR-006**: System MUST execute a control ablation condition using random noise in place of the social prior to isolate the effect of context relevance (See US-3).
- **FR-007**: System MUST validate that all inference runs and evaluations complete within the 6‑hour GitHub Actions free‑tier limit by processing samples in batches of ≤20 and by applying the fallback strategy defined in FR‑022 if needed (See US-4).
- **FR-008**: System MUST compute the Integration‑failure Rate (IR), defined as the proportion of model outputs that do NOT cite any injected context phrase, for each model and condition (See US-2).
- **FR-009**: System MUST apply the neutral‑context fallback when a video’s metadata lacks a specific situational tag, and must log the fallback occurrence (See US-2).
- **FR-010**: System MUST detect and exclude invalid model outputs (e.g., malformed JSON, timeouts) from PR/HR calculations, logging each exclusion (See US-1).
- **FR-011**: System MUST flag samples with ambiguous or contradictory behavioral evidence in the metadata (≥2 contradictory behavior tags) as "grounding‑uncertainty" and exclude them from primary PR/HR calculations (See US-1).
- **FR-018**: System MUST source ground‑truth trait ratings from the expert‑annotated MM‑OCEAN labels and define correctness as exact label match; it MUST also specify the algorithms for computing:
  - **Prejudice Rate (PR)** = (# correct ratings with invalid grounding) / (total # ratings)
  - **Accuracy Rate (AR)** = (# correct ratings) / (total # ratings)
  (See US-1).
- **FR-019**: System MUST conduct a formal a priori power analysis targeting **≥ 80 % power** to detect a moderate effect size (Cohen’s d ≈ 0.5) for the paired comparison across 27 models; the required sample size (videos) shall be recorded and met (See US-3).
- **FR-020**: System MUST assess grounding validity using semantic similarity between the model’s reasoning string and the ground‑truth behavioral evidence tags (sentence‑embedding cosine similarity). The embedding model shall be a frozen, publicly available sentence‑transformer (e.g., “all‑MiniLM‑L6‑v2”) that is not fine‑tuned on any evaluated MLLM, ensuring independence. A grounding is deemed valid when similarity ≥ 0.70 (adjustable via sensitivity analysis) (See US-1, US-2).
- **FR-021**: System MUST quantify the impact of low‑precision quantisation by re‑running a representative subset of 5 models in 8‑bit (or full‑precision) mode for both baseline and intervention; the difference in Prejudice Rate must be ≤ 5 % (See US-3). **Rationale**: Low‑precision quantisation can alter model reasoning; quantifying its impact guarantees that any observed reduction in the Prejudice Gap is attributable to the social‑prior intervention rather than precision artifacts.
- **FR-022**: System MUST pre‑specify a stratified sampling fallback (top‑15 models or 10‑frame per video) before any data is processed; the same fallback is applied uniformly across all conditions to avoid selection bias (See US-4).
- **FR-023**: System MUST randomise and counterbalance the order of condition application (baseline, intervention, control) per model and per video sample, ensuring no systematic order effects (See US-3).

### Key Entities

- **Video Sample**: A unit of data containing the video file (or reference), metadata (transcript, setting, culture, behavior tags), and ground‑truth behavioral evidence.
- **Context Profile**: A structured text object retrieved from the JSON knowledge base containing situational norms and scripts relevant to a specific video sample.
- **Model Output**: The generated response from an MLLM containing a trait rating, a reasoning string, and a grounding justification.
- **Metric Record**: A derived data point containing the calculated Prejudice Rate (PR), Holistic‑Grounding Rate (HR), Integration‑failure Rate (IR), and associated condition flags for a specific model.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The reduction in Prejudice Rate (PR) from baseline to intervention is measured using the mixed‑effects primary analysis; statistical significance is declared when p < 0.05 (See US-3).
- **SC-002**: The difference in Prejudice Rate between the intervention condition and the random‑noise control condition is measured against the null hypothesis of no difference to isolate the effect of relevant social priors (See US-3).
- **SC-003**: The computational feasibility of the analysis is measured against the GitHub Actions free‑tier constraint (≤6 hours total runtime, ≤7 GB RAM) by tracking total execution time and peak memory usage (See US-4).
- **SC-004**: ≥ 95 % of model outputs must include a valid reasoning string (containing at least one citation to an injected context phrase) **and** a grounding score derived via semantic similarity ≥ 0.70 to the ground‑truth evidence (See US-1, US-2).
- **SC-005**: A sensitivity analysis shall sweep the semantic‑similarity grounding threshold over the set {0.65, 0.70, 0.75} and report how false‑positive/false‑negative rates vary (See US-3, FR-020).
- **SC-006**: The Integration‑failure Rate (IR) must be ≤ 10 % for the intervention condition, demonstrating that the majority of model outputs properly cite the injected context (See US-2).
- **SC-007**: The neutral‑context fallback coverage must be ≥ 90 % of samples matched to a specific context profile; if coverage falls below this, the data‑gap report must flag potential under‑coverage (See US-2).
- **SC-008**: Invalid model outputs must constitute ≤ 5 % of total inference calls; higher rates trigger a failure of SC‑004 (See US-1).
- **SC-009**: The proportion of samples flagged with grounding‑uncertainty must be reported; it must not exceed 10 % of the dataset, otherwise a supplemental data‑quality analysis is required (See US-1).
- **SC-010**: The power analysis (FR‑019) must demonstrate **≥ 80 % power** for detecting Cohen’s d ≈ 0.5 given the final sample size; the analysis report is attached to the final deliverable (See US-3).
- **SC-011**: Quantisation impact (FR‑021) must show ΔPR ≤ 5 % between 4‑bit and higher‑precision runs; larger deviations cause a methodological revision (See US-3).
- **SC-012**: Randomisation logs must confirm that condition order was shuffled per model/video with a documented seed; any deviation invalidates the primary statistical test (See US-3).

## Assumptions

- **Assumption about data availability**: The MM-OCEAN validation subset (~200 samples) is accessible via the specified repository (arXiv:2605.22109) and contains all necessary metadata (transcripts, setting, culture, behavior tags) required to construct the context profiles. If a specific situational tag is missing, the system MUST inject the generic 'neutral context' profile, log a warning, and count such samples in a data‑gap report; the pipeline MUST NOT crash on missing variables, and the final report MUST state the proportion of samples resolved via the neutral‑context fallback (target: ≥ 90 % of samples matched to a specific context profile; if fewer than 90 % match, the data‑gap report MUST flag potential under‑coverage of the intervention).

- **Assumption about computational resources**: The analysis relies on CPU‑tractable methods; quantization (e.g., 8‑bit or 4‑bit) that runs on standard CPUs is permitted, but hardware‑dependent quantization requiring specialized GPUs is prohibited. The 27 MLLMs are selected from open‑source models that can run on a standard CPU within the 6‑hour limit (e.g., smaller variants like LLaVA‑1.5‑7B or similar, potentially with sampling).

- **Assumption about inference constraints**: The total runtime for 27 models × 200 samples (plus control and ablation) is assumed to fit within the 6‑hour GitHub Actions free‑tier limit by processing in batches of ≤20 samples per job and using efficient inference pipelines (e.g., `transformers` with `device_map="cpu"`). If projected runtime exceeds the limit, the fallback strategy in US‑4 (reduce to top‑15 models or sample 10 frames per video) will be applied.

- **Assumption about statistical power**: A sample size that is sufficiently large provides adequate power to detect a moderate effect size (Cohen's d ≈ 0.5) in the reduction of the Prejudice Rate, given the paired design across 27 models and the mixed‑effects secondary analysis.

- **Assumption about grounding validity**: The grounding score is computed by measuring semantic similarity (cosine similarity of sentence embeddings) between the model’s reasoning string and the ground‑truth behavioral evidence in the metadata. For ambiguous cases, a blinded gpt‑4‑turbo judge evaluates the justification; inter‑rater reliability on a 30‑sample pilot must be ≥ 0.8.

- **Assumption about threshold justification**: The threshold for classifying a "Prejudice" error (correct rating, invalid grounding) follows the community‑standard definition from the original "Perception or Prejudice" work. A sensitivity analysis (SC‑005) will sweep the grounding‑threshold similarity over {0.65, 0.70, 0.75} to ensure robustness.

- **Assumption about ambiguous evidence detection**: A video sample is flagged with "grounding‑uncertainty" when its metadata contains two or more contradictory behavior tags (e.g., both "smiles" and "frowns" for the same temporal segment). Such samples are excluded from primary PR/HR calculations.

- **Assumption about model selection**: The 27 models are exactly those enumerated in Table 2 of arXiv:2605.22109, representing a diverse set of architectures and training data to enable meaningful ensemble analysis.