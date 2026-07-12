# Feature Specification: State-Guided Curriculum for MobileGym

**Feature Branch**: `001-state-guided-curriculum`  
**Created**: 2026-07-12  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'MobileGym: A Verifiable and Highly Parallel Simulation Platform for Mo'"

## User Scenarios & Testing

### User Story 1 - Dynamic Curriculum Scheduler (Priority: P1)

As a researcher training mobile GUI agents, I need a scheduler that dynamically selects task parameters based on real-time state-space coverage so that the training process prioritizes under-explored or moderately difficult scenarios rather than random sampling.

**Why this priority**: This is the core innovation distinguishing the experimental condition from the baseline. Without the dynamic selection logic, the "State-Guided" aspect of the research question cannot be tested.

**Independent Test**: The scheduler can be tested in isolation by feeding it a mock history of state coverage vectors and verifying that it outputs a batch of task parameters that maximizes the entropy of the selected states or targets the 30-70% success rate "sweet spot" as defined in the methodology.

**Acceptance Scenarios**:

1. **Given** a set of 100 task parameters with recorded state coverage vectors showing [deferred] of states are "mastered" (success rate > 80%), **When** the scheduler requests the next batch, **Then** it MUST select parameters targeting the bottom [deferred] of states by coverage (low-coverage states).
2. **Given** a set of tasks where the success rate distribution is bimodal (many failures, many successes, few medium), **When** the scheduler runs, **Then** it MUST prioritize parameters falling into the 30-70% success rate range such that at least 70% of the selected batch falls within this range.
3. **Given** the scheduler has been running for 1 hour, **When** the coverage vector updates, **Then** the scheduler MUST complete its selection logic without blocking the parallel rollout workers for more than 10% of the batch execution time.

---

### User Story 2 - State Coverage Instrumentation (Priority: P2)

As a developer, I need the MobileGym environment to automatically track a binary "State Coverage Vector" after every rollout so that the scheduler has the necessary data to make informed decisions.

**Why this priority**: The curriculum is only as good as its data. This feature provides the ground truth (state transitions) required for the P1 scheduler to function.

**Independent Test**: The instrumentation can be tested by running a fixed sequence of known state transitions in the simulator and verifying that the resulting JSON state handler output correctly flips the corresponding bits in the coverage vector.

**Acceptance Scenarios**:

1. **Given** a task starts with `app_settings.dark_mode` as False and ends with it as True, **When** the rollout completes, **Then** the coverage vector MUST record a transition for `app_settings.dark_mode` from initial to final state.
2. **Given** a parallel rollout of 32 tasks, **When** the batch completes, **Then** the system MUST aggregate the state transitions into a single coverage update without race conditions or data loss.
3. **Given** a task parameter that does not affect any tracked variables (e.g., a cosmetic change not in the vector), **When** the rollout completes, **Then** the coverage vector MUST remain unchanged for those specific bits.

---

### User Story 3 - Comparative Convergence Analysis (Priority: P3)

As a researcher, I need to compare the convergence speed (steps to target success rate) and Sim-to-Real transfer robustness between the dynamic curriculum agent and a static random sampling baseline.

**Why this priority**: This validates the research hypothesis. While the scheduler and instrumentation are necessary, the comparative analysis is the ultimate deliverable that answers the research question.

**Independent Test**: The analysis pipeline can be tested by running two pre-recorded training logs (one dynamic, one static) through the evaluation script to ensure it correctly generates the "Success Rate vs. Steps" plots and calculates the variance metrics.

**Acceptance Scenarios**:

1. **Given** training logs for both the dynamic curriculum and static baseline agents, **When** the evaluation script runs, **Then** it MUST calculate and report the difference in total environment steps required to reach the 50% success rate threshold, including the magnitude of improvement (e.g., percentage difference).
2. **Given** a held-out test set of 256 tasks with high state-dependency, **When** the policies are evaluated, **Then** the system MUST calculate and report the variance of success rates across apps, showing lower variance for the dynamic curriculum agent if the hypothesis holds.
3. **Given** the training runs are capped at 6 hours, **When** the time limit is reached, **Then** the system MUST stop training gracefully and record the final metrics for both agents to ensure a fair comparison within the compute budget.

---

### User Story 4 - Methodological Validity & Sensitivity Analysis (Priority: P2)

As a researcher, I need to validate that the chosen "State Coverage Vector" variables are a statistically significant proxy for task difficulty to ensure the curriculum is not optimizing for trivial state transitions.

**Why this priority**: Addresses scientific soundness concerns regarding the reduction of high-dimensional state space to binary flags. Without this validation, the "convergence" claim may be measuring optimization on a trivial subset rather than general agent capability.

**Independent Test**: The analysis script can be tested by correlating the binary coverage vectors of a held-out validation set against the actual success rates of those tasks, verifying a correlation coefficient (Pearson's r) ≥ 0.5.

**Acceptance Scenarios**:

1. **Given** a set of 500 tasks with recorded coverage vectors and final success outcomes, **When** the sensitivity analysis runs, **Then** it MUST compute the Pearson correlation coefficient between the number of unique states covered and the task success rate, reporting the value.
2. **Given** the correlation coefficient is < 0.3, **When** the analysis completes, **Then** the system MUST flag the curriculum methodology as "Invalid Proxy" and recommend expanding the variable set to include navigation or action-sequence complexity metrics.
3. **Given** the correlation coefficient is ≥ 0.5, **When** the analysis completes, **Then** the system MUST log "Proxy Validated" and proceed with the curriculum training metrics.

---

### Edge Cases

- **What happens when** the state coverage vector indicates all states are fully explored ([deferred] coverage) before the 6-hour limit? The scheduler MUST default to a random selection strategy to prevent deadlock, logging a warning that the curriculum has exhausted its novelty signal.
- **How does the system handle** a failure in the state instrumentation where the JSON handler returns malformed data? The system MUST skip the specific rollout's coverage update for that batch to prevent crashing the scheduler, while logging the error for later debugging.
- **What happens when** the "30-70% sweet spot" contains no tasks (e.g., all tasks are either <10% or >90% success rate)? The scheduler MUST widen the search window to 10-90% dynamically. If no tasks exist in the 10-90% range, the scheduler MUST fallback to maximum entropy selection.

## Requirements

### Functional Requirements

- **FR-001**: System MUST compute a binary State Coverage Vector tracking specific high-impact UI variables (e.g., `app_settings.dark_mode`, `message_list.unread_count`) after every parallel rollout to enable dynamic task selection. These variables are defined as "semantic state proxies" rather than exhaustive state descriptors. (See US-002)
- **FR-002**: System MUST implement a CPU-tractable scheduler that prioritizes task selection using a two-phase logic: Phase 1 targets states with coverage < 5% (low novelty); Phase 2 targets states with estimated training-time success rates between 30-70% (difficulty). If no states meet the Phase 2 criteria, the scheduler MUST expand the range to 10-90% or fallback to maximum entropy. The scheduler MUST distinguish between training-time success rate (for selection) and held-out test success rate (for validation). (See US-001)
- **FR-003**: System MUST support two distinct training modes: "Static Random" (baseline) and "State-Guided" (experimental) using the identical Qwen3-VL-4B-Instruct model configuration (including quantization level and context window) to ensure experimental control. (See US-003)
- **FR-004**: System MUST enforce a hard wall-clock time limit for both training runs to adhere to GitHub Actions free-tier constraints. (See US-003)
- **FR-005**: System MUST evaluate both trained policies on a held-out test set of tasks that includes state variables NOT present in the training-time State Coverage Vector, to measure Sim-to-Real transfer robustness independently. (See US-003)
- **FR-006**: System MUST record the total number of environment steps taken by each agent to reach a predefined success rate threshold for convergence comparison. (See US-003)
- **FR-007**: System MUST calculate the variance of success rates across high state-dependency apps for the transfer robustness metric. (See US-003)
- **FR-008**: System MUST perform a sensitivity analysis that correlates the binary State Coverage Vector (number of unique states covered) with the task success rate on a held-out validation set (minimum 500 tasks). If the Pearson correlation coefficient (r) is < 0.3, the system MUST flag the methodology as invalid and recommend expanding the variable set. (See US-004)

### Key Entities

- **State Coverage Vector**: A binary array representing the exploration status of tracked environment variables (0 = unexplored, 1 = explored). These are defined as "semantic state proxies" selected for their high impact on UI complexity, not as a complete representation of the full state space.
- **Task Parameter**: A configuration object defining the specific instance of a MobileGym task (e.g., specific app, specific initial state).
- **Policy**: The trained neural network weights for the mobile GUI agent, distinct between the baseline and experimental runs.
- **Coverage History**: A time-series log of coverage vectors used by the scheduler to determine task selection trends.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation phase.

- **SC-001**: Convergence efficiency is measured by the total number of environment steps required to reach a [deferred] success rate, compared between the State-Guided Curriculum and the Static Random Baseline. The metric must report the absolute and percentage difference in steps. (See FR-006, US-003)
- **SC-002**: Sim-to-Real transfer robustness is measured by the variance of success rates across high state-dependency apps on the held-out test set (distinct from training variables), comparing the experimental policy against the baseline. (See FR-007, US-003)
- **SC-003**: Curriculum effectiveness is measured by the percentage of training batches where the scheduler's estimated success rate falls between 30-70%, compared against the static baseline. (See FR-002, US-001)
- **SC-004**: Compute feasibility is measured by the total wall-clock time of the training run, ensuring it remains within a practical and acceptable duration on the specified CPU-only runner. (See FR-004, US-003)
- **SC-005**: Data integrity is measured by the completeness of the State Coverage Vector updates, ensuring no rollout transitions are lost due to instrumentation errors. (See FR-001, US-002)
- **SC-006**: Methodological validity is measured by the Pearson correlation coefficient (r) between the State Coverage Vector complexity and task success rate on a held-out validation set. The system MUST report r ≥ 0.5 to validate the proxy selection; if r < 0.3, the study design is flagged for revision. (See FR-008, US-004)

## Assumptions

- The MobileGym source code and task definitions (a set of test and train tasks) are accessible via the official repository associated with the arXiv preprint and can be downloaded within the available disk limit.
- The Qwen-VL-Instruct model can be loaded and run on a CPU-only environment with limited computational resources (a minimal number of cores and modest RAM) without requiring CUDA or GPU acceleration, likely via quantization or a smaller context window if necessary.
- The "State Coverage Vector" variables (e.g., `app_settings.dark_mode`) are sufficient to capture the complexity required for the research question as "high-impact semantic proxies" known to correlate with task success in MobileGym, based on prior empirical findings. This assumption is subject to validation via the sensitivity analysis defined in FR-008 and SC-006.
- The GitHub Actions free-tier runner provides sufficient CPU throughput to complete the GRPO training for both baselines within a standard time window, assuming the dataset is sampled or the batch size is adjusted if necessary.
- The "Sim-to-Real" transfer evaluation can be approximated using MobileGym's high-fidelity mode, as actual physical device testing is out of scope for this simulation-based study.
- The 30-70% success rate "sweet spot" is a hypothesized optimal range for curriculum learning in this domain; the system treats this as a target to be tested rather than a fixed law, with defined fallbacks if the data distribution does not support it.