# Feature Specification: llmXive follow-up: extending "Video2GUI"

**Feature Branch**: `001-tutorial-bias-analysis`  
**Created**: 2026-07-12  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'Video2GUI: Synthesizing Large-Scale Interaction Trajectories for Gener' - investigating tutorial bias in video-derived GUI datasets"

## User Scenarios & Testing

### User Story 1 - Construct the Non-Linear GUI Benchmark (Priority: P1)

As a researcher, I need a synthetic benchmark containing 500 tasks with explicit error states and branching logic so that I can isolate the "tutorial bias" in agent performance.

**Why this priority**: Without a controlled, non-linear test set, it is impossible to distinguish between general agent failure and specific failure due to the lack of error-recovery training data. This is the foundational dataset for the entire study.

**Independent Test**: The system can be fully tested by running the benchmark generator script and verifying that the output JSON contains 500 tasks, each with at least one "error injection" point and a defined "recovery path" that diverges from the linear happy path.

**Acceptance Scenarios**:
1. **Given** the rule-based simulator is initialized, **When** the generator runs, **Then** it produces a dataset of exactly 500 tasks with unique IDs.
2. **Given** a generated task, **When** the task is inspected, **Then** it contains at least one state where the agent must recover from an invalid input or modal dialog (non-linear branch).
3. **Given** the benchmark dataset, **When** a linear "happy path" task is selected, **Then** it is marked distinctly from non-linear tasks to allow for comparative analysis.

---

### User Story 2 - Evaluate Agent Variants on the Benchmark (Priority: P2)

As a researcher, I need to execute three specific agent variants (Baseline, WildGUI-trained, Hybrid) on the benchmark so that I can measure performance divergence on error-recovery tasks.

**Why this priority**: This is the core experimental step. It generates the raw data (success/failure trajectories) required to test the hypothesis that video-derived data introduces fragility.

**Independent Test**: The system can be tested by running the evaluation loop against a representative subset of tasks and verifying that all three agents produce action trajectories and a final success/failure flag for each.

**Acceptance Scenarios**:
1. **Given** the three agent models are loaded in CPU-only mode, **When** the evaluation script runs, **Then** each agent attempts all 500 benchmark tasks without crashing due to hardware constraints.
2. **Given** an agent encounters an injected error state, **When** the agent takes an action, **Then** the system logs the action and the resulting GUI state change.
3. **Given** the execution completes, **When** the results are aggregated, **Then** the system outputs a matrix of (Agent, TaskID, Outcome) for statistical analysis.

---

### User Story 3 - Statistical Analysis of Tutorial Bias (Priority: P3)

As a researcher, I need to apply McNemar's test to the paired success/failure outcomes so that I can determine if the performance difference between WildGUI-only and Hybrid agents on non-linear tasks is statistically significant.

**Why this priority**: This transforms raw performance data into a scientific conclusion, validating or refuting the "tutorial bias" hypothesis with statistical rigor.

**Independent Test**: The system can be tested by providing a synthetic dataset of paired outcomes (where the Hybrid agent succeeds on 10 tasks the WildGUI agent fails, and vice versa) and verifying the script outputs a p-value and the test statistic.

**Acceptance Scenarios**:
1. **Given** the paired outcomes for non-linear tasks, **When** the statistical module runs, **Then** it calculates the McNemar's test statistic and p-value.
2. **Given** a p-value < 0.05, **When** the results are reported, **Then** the system flags the difference as statistically significant.
3. **Given** the full results, **When** the report is generated, **Then** it includes the specific success rates for "linear" vs. "non-linear" sub-tasks for each agent.

---

### Edge Cases

- What happens if the CPU-only quantized model exceeds the 6-hour time limit on the GitHub Actions runner? (System must abort and report timeout, not hang).
- How does the system handle a task where the agent enters an infinite loop of error recovery? (System must enforce a step-count limit, e.g., 50 steps, and mark as failure).
- What if the simulated GUI state becomes inconsistent with the agent's internal representation? (The simulator must log the state divergence and mark the task as a "simulation failure" rather than an agent failure).

## Requirements

### Functional Requirements

- **FR-001**: System MUST generate 500 synthetic GUI tasks containing explicit error states (e.g., invalid inputs, modals) and branching logic, ensuring no overlap with standard linear video trajectories. The Baseline agent must be trained on standard linear trajectories ONLY. The benchmark must utilize a hold-out set of error patterns disjoint from any used in the Hybrid agent's training data (See US-1).
- **FR-002**: System MUST load and execute three distinct agent variants (Baseline, WildGUI-trained, Hybrid) using CPU-only inference with GGUF quantization (minimum 4-bit) to fit within 7GB RAM (See US-2).
- **FR-003**: System MUST log the full action trajectory and intermediate GUI state for every step taken by each agent during benchmark execution (See US-2).
- **FR-004**: System MUST calculate success rates separately for "linear" (happy-path) and "non-linear" (error-recovery/branching) sub-tasks for each agent (See US-3).
- **FR-005**: System MUST perform a McNemar's test on the paired success/failure outcomes of the WildGUI-only agent versus the Hybrid agent specifically on the non-linear task subset (using the hold-out error set) to determine statistical significance (See US-3).
- **FR-006**: System MUST enforce a maximum step limit of 50 actions per task to prevent infinite loops during evaluation (See Edge Cases).
- **FR-007**: System MUST report the count of discordant pairs and perform a post-hoc power analysis (target power ≥ 0.8) to validate the sample size sufficiency for the McNemar's test result (See US-3).
- **FR-008**: System MUST validate the synthetic error patterns against a documented real-world error taxonomy (e.g., "GUI Error Taxonomy v1.0") to ensure external validity, citing the source of the taxonomy (See US-1).

### Key Entities

- **BenchmarkTask**: A synthetic interaction scenario defined by an initial state, a goal state, and a set of injected error conditions requiring non-linear recovery.
- **AgentVariant**: A specific model configuration (Baseline, WildGUI-trained, Hybrid) used for evaluation.
- **TrajectoryLog**: A structured record of the sequence of actions, states, and final outcome for a single task execution.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation phase.

- **SC-001**: The "Non-Linear Coverage Gap" is measured as the difference in success rates between the WildGUI-only agent and the Baseline agent on the non-linear subset of the benchmark, with a 95% confidence interval. The gap is considered significant only if the lower bound of the CI is > 5% (See US-1, US-2).
- **SC-002**: The "Hybrid Recovery Rate" is measured as the percentage of non-linear tasks where the Hybrid agent successfully recovers from an injected error. Success is defined as the Hybrid Recovery Rate being ≥ 10% higher than the WildGUI-only agent (See US-2, US-3).
- **SC-003**: Statistical significance of the performance divergence is measured by the p-value from McNemar's test on paired non-linear outcomes, with a threshold of p < 0.05, AND the report must include the count of discordant pairs and a power analysis result (power ≥ 0.8) (See US-3).
- **SC-004**: Computational feasibility is measured by the total wall-clock time of the evaluation phase, which must be ≤ 6 hours on a CPU-only runner (See US-2).
- **SC-005**: Methodological validity is measured by a sensitivity analysis where error-injection thresholds are varied by ±10%. The system must demonstrate that success rates vary by < 5% under this variation (See US-3).

## Assumptions

- The WildGUI dataset (or a representative subset) is accessible and can be used for fine-tuning a small open-weight model (e.g., Qwen-VL-Chat) within the 6-hour CI window.
- The "Non-Linear GUI Benchmark" can be simulated using a lightweight HTML/JS environment or headless browser that fits within the 14GB disk and 7GB RAM constraints of the GitHub Actions free tier.
- The "tutorial bias" hypothesis assumes that video-derived data lacks explicit error states; if the source data already contains significant error recovery examples, the benchmark must be adjusted to ensure a clear distinction between training and testing distributions.
- A sufficiently large task benchmark size is sufficient to achieve statistical power for McNemar's test given the expected effect size of the bias.; if power is insufficient, the sample size may need to be increased, potentially impacting the 6-hour runtime limit.
- Quantization (4-bit/8-bit) on CPU will result in acceptable inference latency; if latency is too high, the task timeout (50 steps) may need to be reduced, potentially altering the complexity of recoverable errors.