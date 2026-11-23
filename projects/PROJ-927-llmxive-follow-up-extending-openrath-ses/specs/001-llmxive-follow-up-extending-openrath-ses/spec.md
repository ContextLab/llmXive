# Feature Specification: llmXive follow-up: extending "OpenRath: Session-Centered Runtime State for Agent Systems"

**Feature Branch**: `001-session-first-reconstruction`  
**Created**: 2026-07-09  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'OpenRath: Session-Centered Runtime State for Agent Systems'"

## User Scenarios & Testing

### User Story 1 - Synthetic Workflow Generation and Ground-Truth Capture (Priority: P1)

The researcher MUST be able to generate a reproducible set of synthetic multi-agent debugging workflows using deterministic logic and capture their exact, uncorrupted final states and decision trees as ground truth.

**Why this priority**: This is the foundational step. Without a mathematically independent ground truth, no subsequent reconstruction accuracy can be measured, rendering the entire study invalid.

**Independent Test**: Can be fully tested by running the generation script once and verifying that the output JSON files contain valid workflow structures and that the "ground truth" hash of the final state matches a pre-computed reference for the deterministic seed.

**Acceptance Scenarios**:

1. **Given** a fixed random seed and a defined set of agent roles, **When** the workflow generator executes, **Then** it produces a set of unique workflow definitions with a corresponding ground-truth state file for each.
2. **Given** the same fixed random seed, **When** the generator is run a second time, **Then** the resulting workflow definitions and ground-truth states are byte-for-byte identical to the first run.

---

### User Story 2 - Dual-Architecture Execution with Stress Injection (Priority: P2)

The researcher MUST be able to execute the generated workflows through two distinct architectures (Baseline Event-Log vs. Experimental Session-First) while simultaneously injecting stochastic network delays and randomly corrupting a subset of log entries.

**Why this priority**: This implements the core experimental manipulation. It allows for the comparison of the two architectural hypotheses under controlled, failure-prone conditions.

**Independent Test**: Can be tested by running a single workflow through both architectures, verifying that the "corruption injection" module successfully modifies a [deferred] subset of the log files (by checksum) and that the execution completes despite the simulated jitter.

**Acceptance Scenarios**:

1. **Given** a specific workflow and a corruption rate of 10%, **When** the stress simulator runs, **Then** [deferred] of the generated log entries (transcripts, snapshots, or outputs) are modified or deleted, and the remaining logs are marked with a corruption flag.
2. **Given** the two architecture implementations, **When** the same workflow is executed, **Then** the Session-First model records all state mutations atomically in a single object, while the Event-Log model writes disparate files asynchronously.

---

### User Story 3 - Reconstruction and Fidelity Scoring (Priority: P3)

The researcher MUST be able to attempt to reconstruct the final state and decision path for each workflow using only the corrupted logs and compare the result against the ground truth to calculate a binary success rate and replay latency.

**Why this priority**: This generates the primary metrics (Reconstruction Success Rate and Replay Latency) required to answer the research question.

**Independent Test**: Can be tested by feeding a single corrupted log set and its corresponding ground truth into the reconstruction engine, verifying that it outputs a binary pass/fail status and a latency timestamp.

**Acceptance Scenarios**:

1. **Given** a corrupted log set and the ground-truth state, **When** the reconstruction protocol runs, **Then** it outputs a boolean indicating if the reconstructed state matches the ground truth exactly (including decision tree structure) for all *recoverable* data points; if a critical data point required for the decision path was deleted, the workflow is marked as "Unrecoverable" and excluded from the success rate calculation.
2. **Given** a successful reconstruction, **When** the timing module executes, **Then** it records the total time in seconds required to parse the logs and restore the state.

---

### Edge Cases

- What happens if the corruption injection deletes the *only* copy of a critical tool output required for state mutation? (The reconstruction MUST fail gracefully and be recorded as "Unrecoverable", not crash the script, and be excluded from the success rate calculation).
- How does the system handle a workflow where the "[deferred] corruption injection" accidentally corrupts the ground-truth file itself? (The ground truth MUST be stored in a read-only, separate directory to prevent accidental overwriting during the corruption phase).
- What occurs if the CPU load spikes during the 500-workflow run, causing a timeout? (The system MUST implement a checkpoint mechanism to resume from the last completed workflow ID).

## Requirements

### Functional Requirements

- **FR-001**: System MUST generate a substantial set of synthetic multi-agent workflows using deterministic logic and store their exact final states as ground truth, ensuring the ground truth is mathematically independent of the execution logs. (See US-1)
- **FR-002**: System MUST implement a corruption injection mechanism that randomly selects and modifies or deletes a configurable percentage of log entries (default a moderate percentage) across transcripts, state snapshots, and tool outputs to simulate data loss. (See US-2)
- **FR-003**: System MUST execute workflows using two distinct architectures: a Baseline Event-Log model (asynchronous, fragmented storage) and an Experimental Session-First model (atomic, single-object state recording). (See US-2)
- **FR-004**: System MUST simulate stochastic network delays (jitter) during tool calls in both architectures to ensure non-deterministic latency conditions are present. (See US-2)
- **FR-005**: System MUST calculate a binary "Reconstruction Success Rate" by comparing the reconstructed final state and decision tree against the ground truth for every workflow, excluding cases where critical ground-truth data was explicitly deleted by the corruption mechanism. (See US-3)
- **FR-006**: System MUST measure "Replay Latency" in seconds for every successful reconstruction attempt. (See US-3)
- **FR-007**: System MUST identify and flag workflows as "Unrecoverable" if a critical dependency required for the decision path was deleted by the corruption injection, ensuring these cases are excluded from the "Recoverable State Fidelity" metric. (See US-3)

### Key Entities

- **Workflow Definition**: The structured input describing the agent roles, tasks, and deterministic logic for a single run.
- **Ground Truth**: The immutable record of the exact final state and decision path generated before any corruption.
- **Log Artifact**: The individual pieces of data (transcript, snapshot, output) generated during execution, subject to corruption.
- **Reconstruction Result**: The output containing the binary success status, the reconstructed state, and the latency timestamp.
- **Unrecoverable Flag**: A status indicating that a workflow cannot be reconstructed due to missing critical data, excluded from fidelity calculations.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation phase.

- **SC-001**: Recoverable State Fidelity is measured against the ground-truth state for each workflow to determine the percentage of exact matches among workflows where critical data was *not* deleted. (See FR-005, FR-007)
- **SC-002**: Replay Latency is measured against the zero-time baseline (start of reconstruction process) to determine the time cost of state restoration. (See FR-006)
- **SC-003**: Statistical significance of the difference in Recoverable State Fidelity between the two architectures is measured using McNemar's test for paired nominal data, with multiplicity correction applied if multiple hypothesis tests are performed. (See FR-005, FR-007)
- **SC-004**: Sensitivity of the success rate to the corruption threshold is measured by sweeping the corruption rate over a concrete set (e.g., {low, medium, high}) to verify stability. (See FR-002)
- **SC-005**: Dataset-variable fit is verified by ensuring the synthetic workflow generator produces all necessary variables (tool outputs, state snapshots) required for the reconstruction protocol. (See FR-001)
- **SC-006**: The rate of "Unrecoverable" workflows is measured to quantify the proportion of cases where data loss was physically impossible to recover from, serving as a baseline for the corruption severity. (See FR-007)

## Assumptions

- The synthetic benchmark generator can create a substantial set of complex, multi-agent debugging workflows that fit within the RAM limit of the GitHub Actions free runner.
- The "Session-First" and "Event-Log" architectures can be implemented as pure Python scripts or lightweight libraries without requiring external GPU resources or heavy model training.
- The random number generator used for workflow generation and corruption injection is seeded to ensure full reproducibility across CI runs.
- The "Reconstruction Success" metric (Recoverable State Fidelity) applies only to workflows where the ground-truth data required for the decision path was *not* deleted; cases where critical data is deleted are marked "Unrecoverable" and excluded from the fidelity calculation to ensure the metric measures architectural resilience rather than the impossibility of recovering from physical deletion.
- A fixed corruption rate is applied uniformly across all log types. (transcripts, snapshots, outputs) unless the specific workflow logic dictates otherwise.
- The analysis will use standard Python statistical libraries (e.g., `scipy`, `statsmodels`) which are compatible with CPU-only execution and fit within the memory constraints.
- The "Unrecoverable" classification is determined by checking if any node in the decision tree path references a log entry marked as "deleted" in the corruption log.