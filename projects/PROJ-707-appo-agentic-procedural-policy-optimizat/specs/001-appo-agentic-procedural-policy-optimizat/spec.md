# Feature Specification: APPO: Agentic Procedural Policy Optimization

**Feature Branch**: `001-appo-branching-score`  
**Created**: 2026-06-18  
**Status**: Draft  
**Input**: User description: "Investigate how the Branching Score (token-entropy × future-value) affects sample-efficiency in agentic RL tool-use tasks using HotpotQA, MATH, and WebShop benchmarks on CPU-only runners."

## User Scenarios & Testing

### User Story 1 - Baseline & Score-Default Execution (Priority: P1)

The researcher MUST be able to execute the training pipeline for the "No-Score" baseline and the "Score-Default" configuration on the GitHub Actions runner to establish a comparative baseline for sample efficiency.

**Why this priority**: This is the core MVP. Without establishing the performance gap between the standard PPO and the APPO default configuration, no further ablation or analysis is possible. It directly addresses the primary research question.

**Independent Test**: The system can be tested by running the training script with `--config=default` and `--config=baseline` flags. The test passes if the script completes within the 6-hour limit, produces log files containing step-wise success rates and tool-call counts, and outputs a CSV summary of "episodes to reach 80% threshold" for both runs.

**Acceptance Scenarios**:

1. **Given** the HuggingFace datasets (HotpotQA, MATH, WebShop) are downloaded and the Llama 3.1 8B model is loaded in CPU mode, **When** the training script is executed with the "No-Score" configuration for 5 seeds, **Then** the system must complete training within 6 hours and record the number of steps to reach the 80% performance threshold for each seed.
2. **Given** the same environment, **When** the training script is executed with the "Score-Default" configuration (ε=0.1, ε′=0.05, b=0.5) for 5 seeds, **Then** the system must complete training within 6 hours and record the corresponding steps-to-threshold metrics.
3. **Given** both runs complete, **When** the results are aggregated, **Then** a Kaplan-Meier survival analysis comparing the two configurations must be generated and logged, including the log-rank test statistic and p-value.

---

### User Story 2 - Hyperparameter Ablation & Sensitivity Analysis (Priority: P2)

The researcher MUST be able to run the "Score-Ablation" suite to vary clipping thresholds (ε, ε′) and weighting (b) and perform a sensitivity analysis to determine if the observed effects are robust to small changes in these hyperparameters.

**Why this priority**: The research question explicitly asks about the sensitivity of the Branching Score. Without this, the findings could be dismissed as artifacts of a single lucky parameter set. This validates the robustness of the heuristic.

**Independent Test**: The system can be tested by running the ablation loop over a specified grid of hyperparameters, including a range of values for ε, ε′, and b, as detailed in standard RL ablation practices and HuggingFace Datasets documentation. The test passes if the system generates a sensitivity report showing how the "episodes to threshold" metric varies across the grid and identifies the optimal configuration.

**Acceptance Scenarios**:

1. **Given** the baseline results are established, **When** the ablation script iterates through the defined grid of hyperparameters (ε ∈ {0.05, 0.2}, ε′ ∈ {0.02, 0.1}, b ∈ {0.3, 0.7}), **Then** the system must execute each configuration (or a representative subset if CPU time is constrained) and log the resulting sample efficiency.
2. **Given** the ablation runs complete, **When** the sensitivity analysis is triggered, **Then** the system must generate a report showing the variance in the headline success rate (binary success/failure proxy) as the thresholds sweep across the defined grid, explicitly noting if the trend holds.
3. **Given** the sensitivity report, **When** the researcher reviews the data, **Then** the report must clearly indicate whether the performance gain is monotonic or if there is a sharp drop-off at specific threshold values.
4. **Given** the ablation results, **When** the "Best Ablation" is selected, **Then** the system must select the configuration with the lowest mean steps-to-threshold among those that achieve ≥ 80% success rate, ensuring a deterministic selection criteria.

---

### User Story 3 - Statistical Significance & Reporting (Priority: P3)

The researcher MUST be able to generate a final report containing statistically significant results (p < 0.05) comparing the best Score variant against the baseline, including confidence intervals and a summary of tool-call efficiency.

**Why this priority**: This synthesizes the experimental data into a scientific conclusion. It is necessary to answer the "How does it affect..." question with scientific rigor, distinguishing signal from noise.

**Independent Test**: The system can be tested by parsing the aggregated CSV logs from all seeds and configurations. The test passes if the output includes a table of means, standard deviations, t-statistics, p-values, and confidence intervals for the primary metric (episodes to threshold).

**Acceptance Scenarios**:

1. **Given** the log files from all 5 seeds for both "No-Score" and "Score-Default" (and best ablation), **When** the analysis script runs, **Then** it must output a summary table comparing the mean steps-to-threshold and the mean tool-calls-per-episode.
2. **Given** the summary statistics, **When** the statistical test is performed, **Then** the system must report the p-value from a Kaplan-Meier log-rank test and state whether the null hypothesis (no difference in sample efficiency) can be rejected at the α=0.05 level.
3. **Given** the results, **When** the final report is generated, **Then** it must include a visualization (e.g., learning curve plot) showing the convergence speed of the best Score variant versus the baseline.

---

### Edge Cases

- **What happens when** the training process exceeds the 6-hour GitHub Actions timeout? The system MUST detect the timeout, log the current progress, and save a partial checkpoint to allow manual inspection or resumption (though resumption logic is out of scope for this spec, the logging is required).
- **How does system handle** the scenario where the Llama 3.1 8B model fails to load in CPU mode due to memory constraints (OOM)? The system MUST catch the OOM error, log a specific "Memory Limit Exceeded" message, and abort gracefully rather than hanging the runner.
- **What happens when** the "80% performance threshold" is never reached within the 2M step limit? The system MUST record the final performance score and flag the episode count as "censored" or ">2M steps" in the results CSV, rather than crashing or returning a null value.

## Requirements

### Functional Requirements

- **FR-001**: System MUST load the Llama 3.1 8B model in CPU-only mode (no CUDA/GPU) and process inputs with a maximum sequence length of 256 tokens to ensure memory footprint remains < 7 GB RAM. (See US-1)
- **FR-002**: System MUST implement the Branching Score calculation as the product of per-step token-level entropy and a learned future-value estimate (V(s)), where V(s) is the standard value function trained on task rewards. The Branching Score serves as an exploration bonus and does not replace the task reward signal. (See US-1)
- **FR-003**: System MUST support three distinct configuration modes: "No-Score" (baseline PPO), "Score-Default" (ε=0.1, ε′=0.05, b=0.5), and "Score-Ablation" (iterating over specified hyperparameter grids). (See US-1, US-2)
- **FR-004**: System MUST execute training for multiple independent random seeds for each configuration to enable paired statistical analysis. (See US-1, US-3)
- **FR-005**: System MUST log step-wise metrics (task success rate, average tool calls, mean Branching Score) at regular intervals to a structured CSV file. (See US-1, US-3)
- **FR-006**: System MUST calculate the "episodes to reach [deferred] of the theoretical maximum success rate (1.0)" by interpolating between logged steps if the exact threshold is not hit. (See US-1, US-3)
- **FR-007**: System MUST perform a Kaplan-Meier survival analysis with a log-rank test across multiple seeds for each comparison (Baseline vs. Score-Default, Baseline vs. Best Ablation) and output the p-value and 95% confidence intervals. (See US-3)
- **FR-008**: System MUST enforce a hard limit of [deferred] environment steps per training run to prevent exceeding the 6-hour CI time limit. (See US-1)
- **FR-009**: System MUST calculate and log the Pearson correlation coefficient between token-level entropy and future-value estimates for each seed to verify they are not perfectly collinear (|r| < 0.9). (See US-2)

### Key Entities

- **TrainingRun**: Represents a single execution of the RL agent with specific hyperparameters and a random seed. Attributes: `config_id`, `seed`, `steps_executed`, `final_success_rate`, `steps_to_threshold`.
- **BranchingScore**: A scalar value computed at each token generation step. Attributes: `token_entropy`, `future_value_estimate`, `branching_score_value`.
- **BenchmarkDataset**: Represents the external tool-use environment (HotpotQA, MATH, WebShop). Attributes: `name`, `split`, `total_episodes`.
- **ComparisonResult**: The aggregated statistical output comparing two configurations. Attributes: `config_a`, `config_b`, `mean_diff`, `log_rank_statistic`, `p_value`, `ci_lower`, `ci_upper`.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The system MUST output the p-value and log-rank statistic from a Kaplan-Meier survival analysis comparing the "episodes to reach [deferred] of the theoretical maximum success rate (1.0)" for the "Score-Default" configuration against "No-Score". The reduction in steps is considered statistically significant if p < 0.05. (See US-1, US-3)
- **SC-002**: The sensitivity of the sample efficiency to hyperparameter variations (ε, ε′, b) is measured against the "Score-Default" performance to determine if the effect is robust; specifically, the variance in steps-to-threshold across the grid must be < 15% of the mean. (See US-2)
- **SC-003**: The average number of tool calls per episode at the threshold crossing is measured against the baseline to assess if the Branching Score improves tool-call efficiency while maintaining success. (See US-1, US-3)
- **SC-004**: The total compute time per training run is measured against the designated time limit to ensure the methodology is feasible on free-tier CI runners. (See US-1)
- **SC-005**: The memory footprint of the training process is measured against a constrained RAM limit to verify CPU-only feasibility without GPU offloading. (See US-1)
- **SC-006**: The consistency of results across multiple random seeds is measured (standard deviation of steps-to-threshold) to ensure the observed effect is not an artifact of a specific seed. (See US-3)
- **SC-007**: The system MUST output the Pearson correlation coefficient between entropy and value estimates; if |r| ≥ 0.9, the system MUST flag a warning that the Branching Score may be ineffective due to collinearity. (See US-2)

## Assumptions

- **Assumption about dataset-variable fit**: The HotpotQA, MATH, and WebShop datasets available on HuggingFace contain sufficient interaction traces (tool calls, success/failure states) to compute the "future-value estimate" required for the Branching Score without needing external annotations.
- **Assumption about compute constraints**: The 8-billion parameter Llama 3.1 model, when loaded in default precision (float32 or float16) with batch size 4 and sequence length 256, will fit within the ~7 GB RAM limit of a GitHub Actions free runner.
- **Assumption about inference framing**: Since the experiment involves training an agent (intervention) rather than observing a static dataset, the comparison of "No-Score" vs. "Score" configurations allows for causal claims regarding the *effect of the algorithm* on sample efficiency, provided the random seeds are fixed.
- **Assumption about threshold justification**: The 80% performance threshold (relative to theoretical maximum 1.0) is a community-standard proxy for "convergence" in RL benchmarks when the theoretical optimum is unknown or difficult to reach; the 2M step limit is a standard budget for lightweight experiments.
- **Assumption about power**: The sample size of 5 seeds is sufficient to detect a large effect size (Cohen's d > 0.8) with 80% power at α=0.05; smaller effects may be underpowered, which is acknowledged as a limitation.
- **Assumption about collinearity**: While token-level entropy and the future-value estimate are treated as distinct components of the Branching Score, the system assumes they are not perfectly collinear (|r| < 0.9). If they are highly collinear, the product may be noise; FR-009 and SC-007 are implemented to detect and flag this condition.
- **Assumption about model availability**: The Llama checkpoint (ggml-compatible) is publicly available on HuggingFace and can be downloaded within the 14 GB disk limit of the runner.
- **Assumption about circularity**: The "future-value estimate" is the standard V(s) trained on task rewards. The Branching Score is an *exploration bonus* derived from the product of entropy and V(s), not a replacement for the reward signal. The validation target (success rate) is an outcome measure, while the Branching Score is an internal signal; the comparison tests if the internal signal accelerates the outcome, not if they are independent signals.