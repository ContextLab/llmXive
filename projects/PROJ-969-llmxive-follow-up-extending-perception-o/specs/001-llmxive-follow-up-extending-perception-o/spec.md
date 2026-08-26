# Feature Specification: llmXive follow-up: extending "Perception or Prejudice: Can MLLMs Go Beyond First Impressions of Pers"

**Feature Branch**: `001-gene-regulation`  
**Created**: 2026-07-19  
**Status**: Draft  
**Input**: User description: "Does augmenting Multimodal Large Language Models (MLLMs) with explicit, text-based social priors (e.g., cultural norms, situational context) via retrieval-augmented prompting significantly reduce the 'Prejudice Gap'—where correct trait ratings lack behavioral grounding—or is this failure mode strictly inherent to the models' visual feature extraction capabilities?"

## User Scenarios & Testing

### User Story 1 - Baseline Prejudice Rate Calculation (Priority: P1)

The research team needs to establish the baseline "Prejudice Rate" (PR) and "Holistic-Grounding Rate" (HR) for a selected ensemble of 27 MLLMs using the standard prompting protocol on the MM-OCEAN validation subset. This step is critical to quantify the magnitude of the "Prejudice Gap" before any intervention is applied, ensuring the study has a valid control condition.

**Why this priority**: Without a rigorous baseline measurement, the study cannot determine if the intervention has any effect. This is the foundational data point for all subsequent analysis and hypothesis testing.

**Independent Test**: The system can be tested by running the baseline prompt on a subset of video samples and verifying that the output includes a trait rating, a reasoning string, and a grounding score derived from the metadata, with the PR calculated as the percentage of correct ratings lacking valid behavioral evidence.

**Acceptance Scenarios**:

1. **Given** the MM-OCEAN validation subset and the standard prompt template, **When** the system processes a video sample through an MLLM, **Then** the output contains a trait rating, a textual justification, and a grounding score that matches the definition of "Prejudice" (correct rating, invalid grounding) or "Holistic-Grounding" (correct rating, valid grounding).
2. **Given** a batch of 27 MLLMs, **When** the baseline execution completes, **Then** the system reports a baseline Prejudice Rate (PR) and Holistic-Grounding Rate (HR) for each model, calculated over the full validation subset.

---

### User Story 2 - Context-Grounded Intervention Execution (Priority: P2)

The research team needs to execute the "Context-Grounded Chain-of-Thought" intervention, where a static JSON knowledge base of social norms and situational scripts is retrieved and injected into the prompt for each video sample. This allows the team to measure if adding external context reduces the reliance on visual heuristics.

**Why this priority**: This is the core experimental intervention. It tests the primary hypothesis that the "Prejudice Gap" is a reasoning deficit solvable by context injection rather than a visual limitation.

**Independent Test**: The system can be tested by processing a single video sample with the intervention prompt and verifying that the retrieved context profile (e.g., "job interview," "East Asian setting") is present in the input and that the model's reasoning explicitly references this context.

**Acceptance Scenarios**:

1. **Given** a video sample and its metadata, **When** the system retrieves the corresponding context profile from the static JSON knowledge base and injects it into the prompt, **Then** the model's output reasoning explicitly cites or incorporates the injected social norms before deriving the trait rating.
2. **Given** the full validation subset, **When** the intervention execution completes, **Then** the system calculates the new Prejudice Rate (PR_intervention) for each model and stores the results alongside the baseline metrics.

---

### User Story 3 - Statistical Significance and Ablation Analysis (Priority: P3)

The research team needs to perform a paired statistical test (t-test or Wilcoxon signed-rank) to compare the baseline and intervention Prejudice Rates across the model ensemble, and run a control ablation with random noise to isolate the effect of relevant social priors.

**Why this priority**: This step transforms raw data into a scientific conclusion, determining if the observed reduction in the Prejudice Gap is statistically significant and not due to random variation or prompt length effects.

**Independent Test**: The system can be tested by generating a synthetic dataset with known effect sizes and verifying that the statistical test correctly identifies significance (or lack thereof) and that the ablation condition shows no significant improvement compared to the baseline.

**Acceptance Scenarios**:

1. **Given** the baseline and intervention PRs for all 27 models, **When** the statistical analysis module runs a paired t-test (or Wilcoxon signed-rank test), **Then** the system outputs a p-value and a confidence interval indicating whether the reduction in PR is statistically significant (p < 0.05).
2. **Given** the control condition (random noise prompt), **When** the ablation analysis is performed, **Then** the system confirms that the PR in the control condition does not differ significantly from the baseline, isolating the effect of the relevant social priors.

---

### Edge Cases

- **What happens when** the MM-OCEAN metadata lacks a specific situational tag required for context retrieval? **System handles** this by injecting a generic "neutral context" profile and logging a warning, ensuring the pipeline does not crash but flags the data gap.
- **How does system handle** MLLMs that fail to generate a valid JSON response or reasoning string due to timeout or hallucination? **System handles** this by marking the sample as "invalid" for that specific model, excluding it from the PR calculation, and logging the failure reason for later review.
- **What happens when** the dataset contains video samples with ambiguous or conflicting behavioral evidence in the metadata? **System handles** this by applying a "grounding uncertainty" flag and excluding these samples from the primary PR calculation to maintain measurement validity.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and parse the MM-OCEAN validation subset (~200 video samples) and associated metadata from the specified repository to serve as the primary data source (See US-1).
- **FR-002**: System MUST construct and maintain a static, CPU-accessible JSON knowledge base mapping video metadata (e.g., setting, culture) to curated social norms and situational scripts for retrieval (See US-2).
- **FR-003**: System MUST execute the baseline prompting protocol on 27 distinct MLLMs to generate trait ratings, reasoning strings, and grounding scores for each sample (See US-1).
- **FR-004**: System MUST implement the "Context-Grounded Chain-of-Thought" prompt template that retrieves and injects the relevant social prior before the reasoning step (See US-2).
- **FR-005**: System MUST perform a paired statistical test (t-test or Wilcoxon signed-rank) to compare baseline and intervention Prejudice Rates across the model ensemble and report p-values (See US-3).
- **FR-006**: System MUST execute a control ablation condition using random noise in place of the social prior to isolate the effect of context relevance (See US-3).
- **FR-007**: System MUST validate that all inference runs and evaluations complete within the 6-hour GitHub Actions free-tier limit by processing samples in batches of ≤20 (See Assumptions).

### Key Entities

- **Video Sample**: A unit of data containing the video file (or reference), metadata (transcript, setting, culture), and ground-truth behavioral evidence.
- **Context Profile**: A structured text object retrieved from the JSON knowledge base containing situational norms and scripts relevant to a specific video sample.
- **Model Output**: The generated response from an MLLM containing a trait rating, a reasoning string, and a grounding justification.
- **Metric Record**: A derived data point containing the calculated Prejudice Rate (PR) and Holistic-Grounding Rate (HR) for a specific model and condition.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The reduction in Prejudice Rate (PR) from baseline to intervention is measured against the statistical significance threshold (p < 0.05) using a paired t-test or Wilcoxon signed-rank test (See US-3).
- **SC-002**: The difference in Prejudice Rate between the intervention condition and the random-noise control condition is measured against the null hypothesis of no difference to isolate the effect of relevant social priors (See US-3).
- **SC-003**: The computational feasibility of the analysis is measured against the GitHub Actions free-tier constraint (≤6 hours total runtime, ≤7 GB RAM) by tracking total execution time and peak memory usage (See Assumptions).
- **SC-004**: The validity of the "Prejudice Gap" measurement is assessed by ensuring that ≥95% of model outputs include a valid reasoning string and grounding score derivable from the metadata (See US-1).
- **SC-005**: The robustness of the results is measured by performing a sensitivity analysis on the grounding threshold, sweeping the cutoff over a range of absolute differences (See Methodological Soundness).

## Assumptions

- **Assumption about data availability**: The MM-OCEAN validation subset (~200 samples) is accessible via the specified repository (arXiv:2605.22109) and contains all necessary metadata (transcripts, setting, culture) required to construct the context profiles. If specific variables (e.g., specific cultural norms) are missing, the project will use the closest available proxy or flag `[NEEDS CLARIFICATION: does MM-OCEAN contain <specific variable>?]`.
- **Assumption about computational resources**: The analysis relies on CPU-tractable methods; no GPU acceleration, CUDA, or 8-bit/4-bit quantization requiring specialized hardware is used. The 27 MLLMs are selected from open-source models that can run on a standard CPU within the 6-hour limit (e.g., smaller variants like LLaVA-1.5-7B or similar, potentially with sampling).
- **Assumption about inference constraints**: The total runtime for 27 models × 200 samples (plus control and ablation) is assumed to fit within the 6-hour GitHub Actions free-tier limit by processing in batches of ≤20 samples per job and using efficient inference pipelines (e.g., `transformers` with `device_map="cpu"`).
- **Assumption about statistical power**: A sample size of sufficient magnitude is assumed to provide adequate power to detect a moderate effect size (Cohen's d ≈ 0.5) in the reduction of the Prejudice Rate, given the paired design across 27 models.
- **Assumption about grounding validity**: The "grounding score" derived from the model's textual justification is assumed to be a valid proxy for behavioral evidence, as the metadata provides the ground truth for what constitutes "valid" grounding in the context of the study.
- **Assumption about threshold justification**: The threshold for classifying a "Prejudice" error (correct rating, invalid grounding) is based on the community-standard definition from the original "Perception or Prejudice" work, and a sensitivity analysis will be performed to ensure robustness against minor threshold variations.
