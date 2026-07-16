# Feature Specification: llmXive Follow-up: Extending WeaveBench with Modality Orchestration

**Feature Branch**: `001-llmxive-modality-orchestration`  
**Created**: 2026-07-16  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'WeaveBench: A Long-Horizon, Real-World Benchmark for Computer-Use Agents'"

## User Scenarios & Testing

### User Story 1 - Baseline Trajectory Analysis & Error Tagging (Priority: P1)

The researcher needs to ingest the WeaveBench dataset, parse the JSONL trajectory logs, and automatically tag instances where an agent performs an action on the wrong interface immediately following a modality switch (e.g., typing in a GUI field when the CLI prompt is active).

**Why this priority**: This is the foundational step. Without accurately identifying the "context-switch errors" and quantifying the frequency of modality switches, the correlation analysis and subsequent intervention testing cannot occur. It establishes the ground truth for the study.

**Independent Test**: The system can be fully tested by processing a small, manually verified subset of the WeaveBench logs to ensure the rule-based classifier correctly identifies "typing in GUI when CLI is pending" versus valid actions, producing a JSON report with error counts and switch frequencies.

**Acceptance Scenarios**:

1. **Given** a valid WeaveBench JSONL trajectory file containing mixed GUI/CLI actions, **When** the parsing script processes the file, **Then** it outputs a structured report listing every modality switch and flagging subsequent actions as "valid" or "context-switch error" based on the rule "action interface != current active interface".
2. **Given** a trajectory with zero modality switches, **When** the script runs, **Then** it reports zero context-switch errors and a switch frequency of 0, without raising exceptions.
3. **Given** a trajectory where the agent switches from CLI to GUI and immediately types, **When** the script analyzes the sequence, **Then** it tags this specific action as a "context-switch error" and increments the error counter for that task.

---

### User Story 2 - Rule-Based Modality Scheduler Simulation (Priority: P2)

The researcher needs to simulate a "Modality Scheduler" that intercepts the agent's decision loop, enforcing a "verify-before-switch" protocol (e.g., blocking GUI input if CLI output is pending) and re-evaluating the task pass/fail status against the baseline.

**Why this priority**: This implements the core hypothesis test: whether a lightweight, CPU-tractable orchestration strategy can recover tasks that failed due to poor execution strategy rather than lack of reasoning.

**Independent Test**: The system can be tested by taking a set of baseline-failed trajectories, applying the scheduler heuristics, and verifying that the simulated execution path diverges from the baseline only at switch points, resulting in a new pass/fail label for the task.

**Acceptance Scenarios**:

1. **Given** a trajectory that failed in the baseline due to a context-switch error, **When** the scheduler applies the "block input if pending" heuristic, **Then** the simulation delays the invalid action, waits for the interface state to update, and proceeds with the correct action, resulting in a "Recovered" status for that task.
2. **Given** a trajectory that succeeded in the baseline, **When** the scheduler runs, **Then** the simulation confirms that no unnecessary blocks were applied, and the task remains "Passed" (no false negatives introduced by the scheduler).
3. **Given** a task where the scheduler blocks an action but the agent eventually times out or fails due to a different reason, **When** the simulation completes, **Then** the task is labeled "Scheduler-Blocked-Failure" to distinguish from baseline failures.

---

### User Story 3 - Statistical Correlation & Significance Reporting (Priority: P3)

The researcher needs to compute the Pearson correlation between context-switch frequency and task failure rate, and perform a McNemar's test to determine if the scheduler significantly reduces failure rates compared to the baseline.

**Why this priority**: This provides the empirical evidence required to validate the research question. It transforms the simulation results into a statistically defensible conclusion about the relationship between switching frequency and failure.

**Independent Test**: The system can be tested by running the statistical module on the aggregated results of US-1 and US-2, outputting a correlation coefficient and a p-value, which can be manually verified against the raw data counts.

**Acceptance Scenarios**:

1. **Given** the aggregated dataset of tasks with switch counts and error flags, **When** the correlation analysis runs, **Then** it outputs a Pearson correlation coefficient (r) and a p-value indicating the significance of the relationship between switch frequency and task failure rate.
2. **Given** the paired pass/fail outcomes of the baseline and the scheduler-intervened runs, **When** McNemar's test is executed, **Then** it outputs a chi-square statistic and p-value determining if the improvement is statistically significant (p < 0.05).
3. **Given** the results, **When** the visualization module runs, **Then** it generates a bar chart comparing error rates by modality transition type and a line plot showing recovery rate vs. scheduler strictness.

---

### Edge Cases

- What happens if the WeaveBench dataset is incomplete or missing specific trajectory logs? (System should skip missing files and log a warning, not crash).
- How does the system handle a trajectory where the modality switch is ambiguous (e.g., rapid switching within a single second)? (System must apply a time-threshold rule: a switch is only valid if the time delta between the last action of modality A and the first action of modality B is >500ms. If ≤500ms, it is treated as a single continuous interaction).
- How does the system handle a task where the "verify-before-switch" rule causes an infinite loop (e.g., waiting for a condition that never occurs)? (The scheduler must enforce a maximum retry count before failing the task).
- How does the system handle "pending output" ambiguity? (Pending output is defined as: the presence of a CLI prompt string (regex: `^\s*[$#]\s*`) in the log within a short, recent temporal window., OR the absence of any GUI update event within 500ms of the last CLI action).

## Requirements

### Functional Requirements

- **FR-001**: System MUST parse JSONL trajectory logs to extract modality sequences and identify transitions between GUI and CLI interfaces (See US-1).
- **FR-002**: System MUST implement a rule-based classifier that tags an action as a "context-switch error" if the action interface does not match the current active interface immediately following a modality switch (See US-1).
- **FR-003**: System MUST simulate a "Modality Scheduler" that intercepts agent actions and enforces a "verify-before-switch" protocol. Specifically, it must block GUI input if CLI output is pending. "CLI output is pending" is defined as: the presence of a CLI prompt string (regex: `^\s*[$#]\s*`) in the log within the last 500ms, OR the absence of any GUI update event within 500ms of the last CLI action (See US-2).
- **FR-004**: System MUST re-evaluate task success/fail status for every trajectory after applying the scheduler intervention, distinguishing between baseline failures, recovered tasks, and scheduler-induced failures (See US-2).
- **FR-005**: System MUST compute the Pearson correlation coefficient between the number of context switches per task and the *task failure rate* (binary: task completed successfully vs. failed as per WeaveBench ground truth) to determine if high switching frequency predicts independent task failure (See US-3).
- **FR-006**: System MUST perform a McNemar's test to compare the pass/fail rates of the baseline versus the scheduler-intervened trajectories. The pass/fail label for the scheduler-intervened trajectory MUST be determined by re-evaluating the task against the *original* WeaveBench success criteria (e.g., goal state achievement), not merely the absence of the switch error (See US-3).
- **FR-007**: System MUST generate visualizations including a bar chart of error rates by modality transition type (See US-3).
- **FR-008**: System MUST implement a configurable "scheduler strictness" parameter (integer 1-3) that controls the maximum wait time for pending output (1=500ms, 2=1000ms, 3=2000ms) and the number of retry attempts before failure (See US-2).
- **FR-009**: System MUST generate a line plot of recovery rate vs. scheduler strictness, plotting the recovery rate for strictness levels 1, 2, and 3 (See US-3).
- **FR-010**: System MUST enforce a time-threshold rule for valid modality switches: a switch is only recorded if the time delta between the last action of modality A and the first action of modality B is >500ms. Actions within ≤500ms are treated as a single continuous interaction (See Edge Cases).

### Key Entities

- **Trajectory**: A sequence of agent actions and environment states for a single task, containing modality flags (GUI/CLI).
- **Context-Switch Event**: A specific point in a trajectory where the active interface changes from one modality to another, occurring only when the time delta >500ms (per FR-010).
- **Scheduler Intervention**: A simulated modification to the execution path where an action is delayed or redirected based on interface state.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The correlation coefficient (r) between context-switch frequency and *task failure rate* (independent ground truth) is measured against the null hypothesis of no correlation (r=0) to determine if high switching frequency predicts failure (See US-3, FR-005).
- **SC-002**: The statistical significance (p-value) of the error reduction achieved by the scheduler is measured against the standard alpha threshold of 0.05 using McNemar's test to validate the intervention's efficacy (See US-3, FR-006).
- **SC-003**: The recovery rate of previously failed tasks is measured against the baseline failure count to quantify the percentage of tasks salvaged by the "verify-before-switch" protocol (See US-2, FR-004).
- **SC-004**: The false-positive rate of the "context-switch error" classifier is measured against a manually annotated subset of at least 50 trajectories. The annotation protocol requires 2 independent raters; ground truth is established by majority vote only if Cohen's kappa ≥ 0.8. If kappa < 0.8, a third rater adjudicates (See US-1, FR-002).
- **SC-005**: The computational runtime of the full analysis pipeline (parsing, simulation, statistics) is measured against the free-tier CI limit of a standard duration to ensure CPU-tractability (See Methodological Soundness).

## Methodological Constraints

- The correlation analysis assumes a linear relationship between switch frequency and task failure rate for the purpose of the Pearson coefficient calculation. This is a modeling decision, not a property of the data.

## Assumptions

- The WeaveBench dataset (a collection of tasks) is accessible via the official repository or arXiv supplementary materials and contains complete JSONL trajectory logs with modality flags.
- The "verify-before-switch" heuristic (blocking GUI input if CLI output is pending) is a valid approximation of the proposed "lightweight, rule-based orchestration strategy" without requiring model retraining.
- The analysis will be performed on a sampled subset of the dataset if the full dataset exceeds the memory and disk constraints of the free-tier CI runner, with the sampling method documented.
- The "context-switch error" definition (action on wrong interface immediately after switch) is sufficient to capture the primary failure mode of interest without requiring complex semantic understanding of the task content.
- No GPU acceleration is required for the rule-based parsing, simulation, or statistical analysis, as these operations are CPU-tractable.