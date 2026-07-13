# Feature Specification: llmXive Follow-up: Dynamic Socio-Cognitive State Injection

**Feature Branch**: `001-dynamic-state-injection`  
**Created**: 2026-07-14  
**Status**: Draft  
**Input**: User description: "Does the explicit injection of dynamically inferred socio-cognitive state signals into an LLM mediator's context significantly increase consensus gap closure in high-emotion, culturally diverse conflict scenarios compared to static prompting?"

## User Scenarios & Testing

### User Story 1 - Generate Conflict Trajectories with Targeted Oversampling (Priority: P1)

The system MUST generate synthetic conflict dialogue trajectories using the SoCRATES pipeline, specifically oversampling scenarios with "high emotional reactivity" and "diverse cultural identity" attributes to ensure statistical power for the primary hypothesis.

**Why this priority**: Without a sufficiently large and targeted dataset, the subsequent statistical analysis (paired t-tests) cannot validly detect the effect of the adapter. This is the foundational data layer for the entire study.

**Independent Test**: This can be tested by running the data generation script and verifying the distribution of the generated dataset against the target oversampling parameters (e.g., checking that >40% of samples fall into the high-difficulty axes) without needing the LLM or adapter running.

**Acceptance Scenarios**:

1. **Given** the SoCRATES scenario generation pipeline is configured, **When** the script executes with the oversampling flags enabled, **Then** the output includes a JSON summary file with counts per category, explicitly showing that at least 40% of the trajectories fall into the "high emotional reactivity" or "diverse cultural identity" categories.
2. **Given** the generation script runs on a CPU-only runner, **When** the process completes, **Then** the total memory usage remains within the allocated system capacity and the process finishes within 30 minutes.

### User Story 2 - Execute Paired Mediation Experiments (Adapter vs. Static) (Priority: P2)

The system MUST run a representative set of conflict trajectories through eight distinct LLMs under two conditions: (A) with the dynamic socio-cognitive state adapter enabled, and (B) with a static baseline prompt, ensuring all inference runs occur on CPU-only environments.

**Why this priority**: This is the core experimental execution. It isolates the "dynamic injection" variable against the "static" baseline across multiple model architectures to determine generalizability.

**Independent Test**: This can be tested by running the experiment script for a single LLM and a subset of trajectories, verifying that the "Adapter" log contains the injected state signals (e.g., "de-escalate") while the "Static" log does not, and that the output files are generated correctly.

**Acceptance Scenarios**:

1. **Given** a specific LLM model and a trajectory from the dataset, **When** the experiment runner executes the "Adapter" condition, **Then** the system prompt injected into the LLM context includes a dynamic style instruction derived from the inferred socio-cognitive state, where the instruction string matches a predefined set of templates (e.g., "validate cultural norms", "de-escalate") and the specific state label that triggered it is logged.
2. **Given** the same trajectory and LLM, **When** the experiment runner executes the "Static" condition, **Then** the system prompt remains fixed and contains no dynamic state injection.
3. **Given** the full experiment suite, **When** the job runs on the GitHub Actions free-tier runner, **Then** the total wall-clock compute time for all LLMs and a representative set of trajectories across 2 conditions (excluding external API queue wait times) does not exceed a reasonable duration in local simulation mode, and no GPU-specific errors (CUDA) occur.

### User Story 3 - Compute Consensus Gap Closure and Statistical Significance (Priority: P3)

The system MUST calculate the "consensus gap closure" metric for every run using the topic-localized evaluator and perform a paired t-test comparing the Adapter vs. Static conditions for each LLM and socio-cognitive axis.

**Why this priority**: This transforms raw output into the research answer. It validates whether the dynamic injection statistically significantly improves the outcome.

**Independent Test**: This can be tested by providing a pre-computed CSV of "gap closure" scores for a single LLM and verifying that the script outputs the correct t-statistic, p-value, and effect size (Cohen's d) for the paired comparison.

**Acceptance Scenarios**:

1. **Given** the evaluation scores for the Adapter and Static conditions for a specific LLM, **When** the statistical analysis script runs, **Then** it outputs a JSON report containing a boolean field `is_significant` set to `true` if the p-value is < 0.05, and includes the t-statistic, p-value, and Cohen's d.
2. **Given** multiple LLM results, **When** the summary report is generated, **Then** it lists the "Consensus Gap Closure Improvement" percentage for each LLM, specifically highlighting the high-difficulty axes.

### Edge Cases

- **What happens when** the lightweight state classifier fails to predict a state (low confidence)?
  - *System handles this by* defaulting to a neutral "monitoring" state instruction rather than injecting a specific directive, ensuring the static baseline comparison remains valid (no "hallucinated" intervention). This logic applies specifically to the inference trigger defined in FR-002 (every few turns).
- **How does the system handle** an LLM API timeout or local inference crash during the -run batch?
  - *System handles this by* implementing a retry mechanism (limited number of attempts) with exponential backoff; if all retries fail, the specific trajectory is logged as "skipped" and excluded from the statistical analysis, with a count of skipped samples reported.
- **What happens when** the consensus gap closure score is identical for both conditions?
  - *System handles this by* reporting a p-value indicating no statistical significance and an effect size indicating no observable effect, correctly interpreting this as no significant improvement.

## Requirements

### Functional Requirements

- **FR-001**: System MUST generate a representative set of conflict trajectories. with ≥40% oversampling in "high emotional reactivity" or "diverse cultural identity" axes (See US-1).
- **FR-002**: System MUST implement a lightweight logistic regression classifier to infer socio-cognitive states (e.g., "escalating," "cultural friction") from dialogue history every few turns. The classifier must be trained on metadata tags (e.g., user-provided conflict types) that are distinct from and independent of the consensus-gap evaluation metric used in FR-005 (See US-2).
- **FR-003**: System MUST inject dynamic style instructions into the LLM system prompt based on the inferred state, ensuring the static baseline receives no such injection (See US-2).
- **FR-004**: System MUST execute inference for all target LLMs in a CPU-only environment without requiring CUDA, quantization libraries (bitsandbytes), or GPU accelerators (See US-2).
- **FR-005**: System MUST calculate the "consensus gap closure" metric using the original topic-localized evaluator for every generated trajectory. The evaluator's definition of "ideal resolution" must NOT encode the specific socio-cognitive state labels being injected, ensuring the outcome is independent of the predictor (See US-3).
- **FR-006**: System MUST perform a statistical comparison of the Adapter and Static conditions. The system MUST first verify the normality of the difference scores (e.g., Shapiro-Wilk test); if normality is rejected (p < 0.05), the system MUST use the Wilcoxon signed-rank test instead of a paired t-test. Results must be reported with p-values < 0.05 flagged as significant (See US-3).
- **FR-007**: System MUST apply a multiple-comparison correction (e.g., Bonferroni or Holm-Bonferroni) when aggregating results across the multiple LLMs to control family-wise error rate (See US-3).

### Key Entities

- **ConflictTrajectory**: A dialogue history between two parties with metadata including emotional reactivity score and cultural identity tags.
- **SocioCognitiveState**: An inferred label (e.g., "escalating", "neutral", "cultural-friction") derived from the dialogue history using independent metadata tags.
- **ConsensusGapScore**: A numerical value (0.0–1.0) representing the gap between the LLM's output and the ideal resolution, as measured by the evaluator. The ideal resolution is defined independently of the socio-cognitive state labels being injected to prevent circular validation.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation/research phase.

- **SC-001**: The difference in mean consensus gap closure between the Adapter and Static conditions is measured against the null hypothesis (no difference) using a paired t-test or Wilcoxon signed-rank test (See FR-006).
- **SC-002**: The validity of the dataset-variable fit is measured by verifying that the SoCRATES dataset contains all required variables (emotional reactivity, cultural identity) for the analysis (See FR-001).
- **SC-003**: The computational feasibility is measured by ensuring the local inference time per trajectory is ≤45 seconds and the throughput is ≥40 trajectories per hour on a standard CPU instance (quantifying the feasibility requirement of FR-004) (See FR-004).
- **SC-004**: The statistical robustness is measured by the application of a family-wise error correction method across multiple LLM comparisons (See FR-007).
- **SC-005**: The sensitivity of the state classifier threshold is measured by sweeping the confidence cutoff (e.g., varying thresholds) and reporting the variation in the number of injected directives (See FR-002).

## Assumptions

- **Assumption about data availability**: The SoCRATES dataset and evaluation pipeline are available and contain the specific variables "emotional reactivity" and "cultural identity" required for the oversampling and analysis; if these are missing, the project scope will be adjusted to use the available metadata.
- **Assumption about model inference**: The eight target LLMs can be accessed via API or run via local CPU quantization (e.g., GGML/GGUF) that fits within 7 GB RAM; if a specific model requires >7 GB RAM, it will be excluded from the study.
- **Assumption about evaluation ground truth**: The topic-localized evaluator from the original SoCRATES work provides a valid proxy for "consensus gap" and can be executed locally without GPU.
- **Assumption about statistical power**: A sample size of A set of trajectories provides sufficient power (≥0.80) to detect a medium effect size (Cohen's d of moderate magnitude) in the paired t-test; if the observed effect is smaller, the result will be reported as "underpowered to detect small effects."
- **Assumption about threshold justification**: The confidence threshold for the state classifier (default value) is based on standard logistic regression practice; a sensitivity analysis will be performed to confirm that minor variations do not alter the headline conclusion.
- **Assumption about independence**: The metadata tags used to train the state classifier (e.g., user-provided conflict types) are distinct from and do not overlap with the logic used by the topic-localized evaluator to score "consensus gap," ensuring the study avoids circular validation.