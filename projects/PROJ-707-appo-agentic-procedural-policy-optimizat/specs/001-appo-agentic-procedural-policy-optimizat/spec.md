# Feature Specification: APPO: Agentic Procedural Policy Optimization

**Feature Branch**: `001-appo-branching-score`
**Created**: 2026-06-18
**Status**: Draft
**Input**: User description: "Investigate how the Branching Score (product of token-level entropy and future-value estimate) affects sample-efficiency of agentic RL agents in multi-step tool-use tasks, specifically measuring episodes-to-threshold on HotpotQA, MATH, and WebShop benchmarks using CPU-only training."

## User Scenarios & Testing

### User Story 1 - Core Training Loop with Branching Score (Priority: P1)

The system MUST execute the core training loop for an agentic RL agent on a tool-use benchmark (e.g., HotpotQA), implementing the Branching Score mechanism (product of token entropy and future-value estimate) as a credit-assignment heuristic, and recording the number of training steps required to reach a predefined performance threshold (80% of the maximum pilot score, where the pilot score is defined as the best success rate achieved by the `No-Score` baseline across 5 seeds).

**Why this priority**: This is the foundational experiment. Without a functional training loop that correctly computes and applies the Branching Score and tracks the primary metric (steps-to-threshold), no comparison or statistical analysis is possible. It directly addresses the core research question.

**Independent Test**: Can be fully tested by running the training script for a single seed on a small subset of the WebShop benchmark, verifying that the "steps-to-threshold" metric is logged correctly and that the Branching Score values are non-zero and vary per step.

**Acceptance Scenarios**:

1. **Given** a configured environment (WebShop) and a model (Llama 3.1 8B 4-bit), **When** the training script runs with the `Score-Default` variant, **Then** the system logs the cumulative training steps at the moment the agent's success rate first exceeds 80% of the maximum pilot score (derived from the `No-Score` baseline).
2. **Given** the same setup, **When** the training script runs with the `No-Score` baseline, **Then** the system logs the cumulative training steps at the moment the agent's success rate first exceeds 80% of the maximum pilot score (derived from the `No-Score` baseline), ensuring the metric is comparable.
3. **Given** a training run, **When** the system computes the Branching Score, **Then** the score is calculated as the product of the token-level entropy and the pre-trained, frozen future-value estimate for each step, and this value is recorded in the step log.

---

### User Story 2 - Hyperparameter Sensitivity Analysis (Priority: P2)

The system MUST execute the training loop for the `Score-Ablation` variant, systematically varying the Branching Score hyperparameters (clipping thresholds ε, ε′, and weighting b) across a defined grid (ε ∈ {0.05, 0.2}, ε′ ∈ {0.02, 0.1}, b ∈ {0.3, 0.5, 0.7}) to measure the sensitivity of sample efficiency to these parameters.

**Why this priority**: The research question explicitly mentions the lack of systematic evaluation of hyperparameter sensitivity. This story extends the core loop to explore the parameter space, providing the necessary data to determine if the heuristic's benefit is robust or fragile.

**Independent Test**: Can be tested by running the ablation script with a specific set of hyperparameters (e.g., ε=0.05, ε′=0.02, b=0.3) and verifying that the resulting performance curve and steps-to-threshold differ from the `Score-Default` run.

**Acceptance Scenarios**:

1. **Given** the ablation configuration, **When** the system runs a training variant with ε=0.2, **Then** the system records the steps-to-threshold for this specific configuration in the results table.
2. **Given** the ablation configuration, **When** the system runs a training variant with b=0.7, **Then** the system records the steps-to-threshold for this specific configuration, ensuring it is distinct from the b=0.5 default.
3. **Given** all ablation runs complete, **When** the results are aggregated, **Then** the system produces a summary table mapping each (ε, ε′, b) tuple to its corresponding steps-to-threshold value.

---

### User Story 3 - Statistical Validation and Reporting (Priority: P3)

The system MUST perform statistical analysis (Wilcoxon signed-rank tests) across independent random seeds to compare the sample efficiency (steps-to-threshold) and tool-call efficiency (mean tool calls per episode) between the `No-Score` baseline and each `Score` variant, generating a report with p-values and 95% confidence intervals.

**Why this priority**: The expected results section explicitly requires statistical significance (p < 0.05) to claim a genuine learning-speed benefit. This story ensures the experimental design is methodologically sound and the conclusions are statistically valid, not just anecdotal, specifically accounting for non-normal distributions in RL metrics.

**Independent Test**: Can be tested by providing a synthetic dataset of seed results for two conditions and verifying that the analysis script correctly computes the Wilcoxon signed-rank statistic, p-value, and confidence intervals.

**Acceptance Scenarios**:

1. **Given** the results from seeds for `No-Score` and `Score-Default`, **When** the analysis script runs, **Then** it outputs a p-value from a Wilcoxon signed-rank test comparing the steps-to-threshold metrics.
2. **Given** the results from seeds, **When** the analysis script runs, **Then** it calculates and reports the 95% confidence interval for the difference in median steps-to-threshold.
3. **Given** the full set of results, **When** the final report is generated, **Then** it includes a section summarizing the tool-call efficiency (mean tool calls per episode) at the threshold crossing for each variant.

---

### Edge Cases

- What happens if the agent fails to reach the 80% performance threshold within the 2 million step limit? (The system MUST record the final performance and steps, and flag the run as "threshold-not-reached" rather than crashing or reporting infinity).
- How does the system handle a situation where the token-level entropy is zero for a sequence of steps? (The Branching Score calculation MUST handle this gracefully, resulting in a score of zero for those steps, without causing division by zero or NaN errors).
- What happens if the `datasets` library fails to download the WebShop benchmark due to network issues? (The system MUST exit with a clear error message indicating the missing data dependency and not proceed with training).

## Requirements

### Functional Requirements

- **FR-001**: The system MUST implement a training loop for an agentic RL agent that computes the Branching Score as the product of token-level entropy and a pre-trained, frozen future-value estimate at every step. (See US-1)
- **FR-002**: The system MUST support two distinct training configurations: a `No-Score` baseline (standard PPO) and a `Score-Default` configuration using the APPO Branching Score with ε=0.1, ε′=0.05, b=0.5. (See US-1)
- **FR-003**: The system MUST execute a `Score-Ablation` configuration that iterates through the hyperparameter grid: ε ∈ {0.05, 0.2}, ε′ ∈ {0.02, 0.1}, b ∈ {0.3, 0.5, 0.7}, running a separate training instance for each combination. (See US-2)
- **FR-004**: The system MUST record the exact number of training steps (interpolated if necessary) at which the agent's task success rate first crosses [deferred] of the maximum pilot score (derived from the `No-Score` baseline) for every training run. (See US-1)
- **FR-005**: The system MUST calculate and log the mean number of tool calls per episode at the point of threshold crossing for every training run. (See US-3)
- **FR-006**: The system MUST execute multiple independent training runs (seeds) for the `No-Score` and `Score-Default` configurations, and multiple independent training runs (seeds) for each `Score-Ablation` variant, to enable statistical testing while managing computational load. (See US-3)
- **FR-007**: The system MUST perform Wilcoxon signed-rank tests comparing the steps-to-threshold and tool-call efficiency metrics between the `No-Score` baseline and each `Score` variant across the defined seeds. (See US-3)
- **FR-008**: The system MUST generate a final report containing the p-values and 95% confidence intervals for all statistical comparisons performed. (See US-3)

### Key Entities

- **TrainingRun**: Represents a single execution of the training loop with a specific configuration (variant, seed, benchmark). Attributes: `variant`, `seed`, `benchmark`, `steps_to_threshold`, `final_success_rate`, `mean_tool_calls`.
- **BranchingScoreConfig**: Represents the hyperparameters for the Branching Score. Attributes: `epsilon`, `epsilon_prime`, `beta_weight`.
- **StatisticalResult**: Represents the outcome of a comparison between two configurations. Attributes: `config_a`, `config_b`, `metric`, `p_value`, `confidence_interval`.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The difference in median steps-to-threshold between the `No-Score` baseline and the `Score-Default` variant is measured against the null hypothesis of no difference using a Wilcoxon signed-rank test across seeds. (See US-3)
- **SC-002**: The sensitivity of the steps-to-threshold metric to variations in ε, ε′, and b is measured by the range of observed steps-to-threshold values across the ablation grid. (See US-2)
- **SC-003**: The tool-call efficiency improvement (reduction in mean tool calls per episode) of the `Score` variants relative to the `No-Score` baseline is measured at the threshold crossing point. (See US-3)
- **SC-004**: The statistical significance of the observed improvements is measured by the p-value (target < 0.05) derived from the Wilcoxon signed-rank test. (See US-3)
- **SC-005**: The computational feasibility of the experiment is measured by the total runtime of the training runs on a 4-core CPU runner with 16GB RAM, ensuring the full suite (5 seeds baseline/default + 3 seeds ablation) completes within the allocated CI runner time budget (typically 24 hours). (See Assumptions)

## Assumptions

- The Llama 3.1 8B model (quantized to 4-bit, ggml-compatible) is available on the HuggingFace Hub and can be loaded and run on a 4-core CPU environment with 16GB RAM using batch size 4 and sequence length 256.
- The HotpotQA (`hotpotqa`), MATH (`math`), and WebShop (`webshop`) benchmarks are accessible via the HuggingFace `datasets` library and fit within the disk limit of the GitHub Actions runner.
- The WebShop benchmark DOI () is the canonical source for the dataset.
- The `trl` library (or equivalent) is available and compatible with the CPU-only execution environment for implementing the PPO baseline and agentic RL logic.
- The maximum step limit per training run is sufficient to reach the 80% performance threshold for at least some configurations; if not, the run is capped and flagged.
- The "future-value estimate" component of the Branching Score is a pre-trained, frozen heuristic (or a separate, frozen value network trained on a distinct reward signal) that does not require GPU acceleration or heavy training overhead during the main RL loop.
- The statistical power of 5 seeds for baseline/default and 3 seeds for ablation variants is considered adequate for the initial exploratory study, acknowledging that a larger sample size might be required for definitive conclusions in future work.
- The "maximum pilot score" is defined as the highest success rate achieved by the `No-Score` baseline across its 5 seeds in a preliminary run, ensuring the threshold is fixed and independent of the treatment variants.
- The token-level entropy is computed directly from the model's logits during generation and does not require additional model passes or significant computational overhead.
- The total runtime for the full experimental suite (baseline/default seeds plus seeds for 12 ablation variants) is estimated at [deferred] on the specified hardware, fitting within the 24-hour CI budget.