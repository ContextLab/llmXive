# Feature Specification: llmXive Follow-up: Reward Fidelity vs. Error Recovery Density

**Feature Branch**: `001-reward-fidelity-error-recovery`  
**Created**: 2026-09-08  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending Long-Horizon-Terminal-Bench to test the trade-off between reward signal fidelity and context pruning density for error recovery."

## User Scenarios & Testing

### User Story 1 - Baseline Execution & Ground Truth Establishment (Priority: P1)

**Description**: The researcher downloads the Long-Horizon-Terminal-Bench dataset and executes a lightweight open-source agent (Llama via vLLM on CPU) on the full available subset of error-prone tasks to establish ground-truth success rates and identify context segments required for error recovery.

**Why this priority**: This is the foundational step. Without a verified baseline of how the agent behaves with full context and dense rewards, no comparison to "pruned" scenarios is possible. It establishes the "truth" against which fidelity loss is measured.

**Independent Test**: Can be fully tested by running all available tasks (N=46) with full context retention and verifying that the system logs the exact context tokens required for the agent to self-correct from a known error state, and records the baseline success rate as the reference point.

**Acceptance Scenarios**:

1. **Given** the Long-Horizon-Terminal-Bench dataset is downloaded and all 46 tasks are selected, **When** the agent runs with full context and dense rewards, **Then** the system logs the exact context tokens required for the agent to self-correct from a known error state.
2. **Given** an error is programmatically injected into a task trajectory, **When** the agent attempts recovery with full context, **Then** the agent successfully completes the task and the system records the specific "recovery segment" from the history.

---

### User Story 2 - Reward Fidelity Manipulation & Pruning Execution (Priority: P2)

**Description**: The researcher configures the context manager to simulate varying reward fidelities (e.g., binning continuous rewards into binary "progress/stagnant" labels) and executes the agent with dynamic pruning enabled, where pruning logic is driven *only* by these manipulated signals.

**Why this priority**: This implements the core experimental variable. It allows the system to test the hypothesis that low-fidelity signals lead to the removal of critical context.

**Independent Test**: Can be fully tested by running the same tasks with "low-fidelity" reward signals (binary) and verifying that the pruning logic aggressively removes segments that were previously identified as "recovery-critical" in the baseline.

**Acceptance Scenarios**:

1. **Given** the reward signal is coarsened to binary "progress/stagnant" labels, **When** the agent encounters a "stagnant" segment that contains a subtle state transition, **Then** the pruning logic removes that segment from the context window.
2. **Given** a specific fidelity level (e.g., 3-bin rewards), **When** the agent executes the task, **Then** the system logs the total token consumption and the specific context segments discarded compared to the baseline.

---

### User Story 3 - Threshold Identification & Statistical Analysis (Priority: P3)

**Description**: The researcher analyzes the collected data to identify the non-linear threshold where reward fidelity drops below the density required for state recovery, causing a sharp decline in success rates, and performs logistic regression (or fallback non-parametric test) to model this relationship.

**Why this priority**: This delivers the research answer. It transforms raw execution logs into the "inflection point" metric requested in the research question.

**Independent Test**: Can be fully tested by running the statistical analysis script on the collected logs and verifying that it outputs a specific fidelity threshold value or a valid fallback statistical result with a documented limitation.

**Acceptance Scenarios**:

1. **Given** the execution logs from baseline and manipulated fidelity runs, **When** the analysis script calculates recovery success rates per fidelity level, **Then** it identifies a specific fidelity level where the logistic regression coefficient for fidelity becomes statistically significant (p < 0.05) or the point of maximum curvature.
2. **Given** the dataset of (fidelity, success) pairs, **When** the statistical test is performed, **Then** the model outputs an inflection point where token savings begin to degrade recovery capability, or reports a fallback non-parametric result if sample size constraints are met.

### Edge Cases

- **What happens when** the dataset lacks a specific variable required to define "stagnant" vs. "critical" context segments? (The system MUST fail gracefully with error code `ERR_MISSING_VAR` and log the name of the missing variable).
- **How does system handle** a task where the agent fails to recover even with full context (baseline failure)? (These tasks are excluded from the "recovery success" metric calculation but logged as "unrecoverable errors" to avoid skewing the fidelity threshold).
- **What happens when** the CPU memory limit (7 GB) is exceeded during the baseline execution of all tasks? (The system MUST sample or subset the dataset to fit within 6 hours, prioritizing the most error-prone tasks, and log the sampling strategy).

## Requirements

### Functional Requirements

- **FR-001**: System MUST download the Long-Horizon-Terminal-Bench dataset (a set of tasks) and generate baseline execution logs by executing the agent on all 46 available tasks using only CPU resources (See US-1).
- **FR-002**: System MUST execute a lightweight open-source model (Llama-3-8B via vLLM) on the full available subset of tasks (N=46) to maximize statistical power (See US-1).
- **FR-003**: System MUST implement a context manager that can coarsen dense reward signals into discrete fidelity levels (e.g., binary, 3-bin) to drive pruning decisions (See US-2).
- **FR-004**: System MUST tag and log specific context segments identified as "recovery-critical" during baseline execution and verify their retention or removal during pruned execution (See US-2).
- **FR-005**: System MUST perform logistic regression to model the probability of task success as a function of reward fidelity and retained context density, identifying the inflection point (See US-3).
- **FR-006**: System MUST apply a multiple-comparison correction (e.g., Bonferroni or Benjamini-Hochberg) specifically to the p-values for the logistic regression coefficients when evaluating significance across multiple fidelity levels (See US-3).
- **FR-007**: System MUST identify "recovery-critical" segments by calculating the absolute state vector difference between pre-error and post-recovery states, attributing contribution to context segments via attention-weighted token overlap, and tagging segments where the overlap contribution is significant relative to the total state change magnitude (See US-1, US-2).
- **FR-008**: System MUST define the "inflection point" as the specific reward fidelity level where the first derivative of the fitted logistic curve reaches its maximum absolute value, or where the 95% confidence interval of the success rate no longer overlaps with the baseline; if the calculated power for the logistic regression is < 0.8, the system MUST fallback to a Cochran-Armitage trend test and report the EPV limitation (See US-3).
- **FR-009**: System MUST execute a "Random Pruning" control condition where context segments are removed randomly (independent of reward signals) to isolate the effect of reward fidelity from general information density loss (See US-2).

### Key Entities

- **TaskTrajectory**: A sequence of agent actions, observations, and rewards for a single benchmark task.
- **RewardFidelityLevel**: A categorical parameter defining the granularity of the reward signal (e.g., "Dense", "Binary", "3-Bin").
- **RecoverySegment**: A specific slice of the context window containing information necessary for the agent to self-correct from an error state.
- **SuccessMetric**: A binary outcome (1/0) indicating whether the agent completed the task after a potential error.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation/research phase.

- **SC-001**: Recovery success rate is measured against the baseline success rate (full context, dense rewards) to quantify the degradation caused by pruning (See US-1, US-3).
- **SC-002**: The inflection point (fidelity threshold) is measured as the specific reward granularity level where the recovery success rate drops by a statistically significant margin (See US-3).
- **SC-003**: Token consumption reduction is measured against the baseline token count to quantify the efficiency gain of the pruning strategy (See US-2).
- **SC-004**: The statistical significance of the fidelity-success relationship is measured against a corrected p-value threshold (α ≤ 0.05 after multiple-comparison correction) (See US-3).

## Assumptions

- The Long-Horizon-Terminal-Bench dataset contains all necessary variables (observations, actions, rewards) to define "stagnant" segments and "error recovery" events.
- The Llama model (via vLLM) can execute a representative task subset on a free-tier GitHub Actions runner with limited CPU resources and constrained RAM within the 6-hour limit, without GPU acceleration.
- The "recovery-critical" context segments can be programmatically identified by comparing trajectories where the agent succeeds with full context vs. those where it fails after pruning using the state-diff heuristic defined in FR-007.
- The relationship between reward fidelity and recovery success is monotonic or non-linear but detectable via logistic regression or the fallback Cochran-Armitage test within a sufficient sample size of tasks.
- The dataset's reward signals are granular enough to be coarsened into meaningful discrete levels (binary, ternary) without losing all semantic meaning.
- The "stagnant" segments identified by low rewards are the primary candidates for pruning, and their removal is the mechanism of failure (not other factors like token limits).