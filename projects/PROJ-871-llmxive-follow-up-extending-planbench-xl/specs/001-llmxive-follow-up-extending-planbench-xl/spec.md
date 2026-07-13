# Feature Specification: llmXive follow-up: extending "PlanBench-XL: Evaluating Long-Horizon Planning of LLM Tool-Use Agents "

**Feature Branch**: `001-gene-regulation`  
**Created**: 2026-07-13  
**Status**: Draft  
**Input**: User description: "Does augmenting LLM tool-use agents with lightweight, rule-based 'failure signature' retrieval significantly improve recovery rates from implicit tool failures in large-scale, dynamic tool ecosystems compared to agents relying solely on internal reasoning?"

## User Scenarios & Testing

### User Story 1 - Baseline Agent Execution on Implicit Failure Subset (Priority: P1)

The system must execute the baseline agent (relying solely on internal LLM reasoning) on the specific "implicit failure" subset of the PlanBench-XL dataset to establish a performance baseline. This is the critical control condition; without it, no comparative analysis of the augmentation can be performed.

**Why this priority**: This is the primary control variable. The entire research hypothesis rests on comparing the augmented agent against this specific baseline. If the baseline fails to run or produce valid results, the study cannot proceed.

**Independent Test**: The system can be fully tested by running the baseline agent on a pre-defined subset of tasks containing known implicit failures (derived from the PlanBench-XL ground truth) and verifying that it produces a completion log with a measurable success rate ([deferred]) measured against the PlanBench-XL task completion status ground truth. Note: While the *data selection* relies on the same ground truth used for the signature index, the *execution* is independent of the *runtime* signature index.

**Acceptance Scenarios**:

1. **Given** the PlanBench-XL implicit failure subset is loaded, **When** the baseline agent executes the tasks using only internal reasoning, **Then** the system generates a JSON execution log containing the final task status (success/failure) for each task.
2. **Given** a task with a known silent tool failure, **When** the baseline agent attempts recovery via internal reasoning, **Then** the agent either succeeds or fails, and the outcome is recorded in the log without referencing any external failure signature index.

---

### User Story 2 - Augmented Agent Execution with Signature Retrieval (Priority: P1)

The system must execute the augmented agent, which performs a lightweight string-matching check against a static JSON "failure signature" index immediately after tool invocation, on the same implicit failure subset.

**Why this priority**: This implements the experimental condition. It validates the core hypothesis that external, low-compute metadata signals improve recovery rates. It must be testable independently to ensure the augmentation logic functions correctly before statistical comparison.

**Independent Test**: The system can be tested by running the augmented agent on the same set of tasks used in the baseline test and verifying that the agent logs outcomes for all tasks, detects known implicit failures via the JSON index, triggers a recovery path, and potentially results in a different outcome than the baseline for specific cases.

**Acceptance Scenarios**:

1. **Given** a task triggers a known implicit tool failure, **When** the augmented agent invokes the tool and checks the JSON signature index, **Then** the agent identifies the mismatch and executes the predefined recovery strategy (e.g., retry, fallback, or error reporting).
2. **Given** the augmented agent completes the task, **When** the execution log is generated, **Then** the log must include a flag indicating whether the "failure signature" retrieval was triggered and if it contributed to the final outcome.

---

### User Story 3 - Statistical Comparison and Significance Reporting (Priority: P2)

The system must compute the success rates for both agents on the target subset and perform a statistical test (Fisher's Exact Test if n < 30, otherwise two-proportion z-test) to determine if the difference in recovery rates is statistically significant (p < 0.05).

**Why this priority**: This is the scientific output. It transforms raw execution data into a research finding. It validates the "Expected Results" section of the idea by confirming whether the observed improvement is statistically robust or due to chance.

**Independent Test**: The system can be tested by providing the full execution logs from both agents and verifying that the entire pipeline (execution + analysis) produces a final report containing the success rates, the appropriate statistical test result, and a conclusion on the hypothesis validity.

**Acceptance Scenarios**:

1. **Given** the execution logs from the baseline and augmented agents, **When** the statistical analysis module runs, **Then** it outputs a summary report containing the success rate for each agent, the absolute difference, the test statistic, and the p-value.
2. **Given** the calculated p-value is less than 0.05, **When** the report is generated, **Then** the system explicitly flags the result as "Statistically Significant" and notes the direction of improvement (Augmented > Baseline).

---

### Edge Cases

- What happens when the PlanBench-XL dataset is partially corrupted or missing specific tool definitions required for the signature index?
- How does the system handle a scenario where the LLM API (if used) times out or returns a non-standard error during the 6-hour execution window?
- What is the behavior if the "failure signature" index contains a false positive (flags a correct tool output as a failure)?

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and parse the PlanBench-XL dataset and extract the specific subset of tasks containing implicit tool failures for execution. (See US-1)
- **FR-002**: System MUST construct a static, CPU-tractable JSON index mapping tool identifiers to their "failure signatures" (expected success vs. failure output patterns) derived from the benchmark ground truth. This index is used *only* for detection; the final success metric is validated against the independent ground-truth task completion status. (See US-2)
- **FR-003**: System MUST implement a baseline agent that executes tasks using only internal LLM reasoning without accessing the failure signature index. (See US-1)
- **FR-004**: System MUST implement an augmented agent that performs a lightweight string-matching check against the JSON signature index immediately after every tool invocation to detect implicit failures. (See US-2)
- **FR-005**: System MUST execute both agents on the target subset using a standard open-source LLM hosted locally or via a free-tier API, ensuring the total runtime remains feasible within a CPU-only environment. (See US-1, US-2)
- **FR-006**: System MUST calculate the task completion success rate for both the baseline and augmented agents. If the number of events is < 30, the system MUST perform Fisher's Exact Test; otherwise, it MUST perform a two-proportion z-test to determine statistical significance (p < 0.05). (See US-3)
- **FR-007**: System MUST generate a final report containing the success rates, absolute difference, test statistic, p-value, and a conclusion on the hypothesis validity. (See US-3)
- **FR-008**: System MUST implement a recovery strategy that involves agent re-planning or tool substitution upon failure detection. The system MUST NOT simply return the ground-truth correct answer upon signature match, ensuring the recovery is a non-trivial agent capability. (See US-2)

### Key Entities

- **Task**: A single planning problem from PlanBench-XL, containing the goal, tool definitions, and ground-truth success criteria.
- **Failure Signature**: A rule-based pattern (e.g., specific error string, output structure) extracted from ground truth indicating a silent tool failure.
- **Execution Log**: A structured record of a task run, including the tool sequence, LLM reasoning traces, signature checks (if applicable), and final success/failure status.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Task completion success rate for the baseline agent is measured against the ground-truth task completion status defined in the PlanBench-XL dataset. (See US-1)
- **SC-002**: Task completion success rate for the augmented agent is measured against the ground-truth task completion status defined in the PlanBench-XL dataset. (See US-2)
- **SC-003**: The statistical significance of the difference in recovery rates is measured against the standard alpha threshold of 0.05 using the appropriate test (Fisher's Exact or z-test). (See US-3)
- **SC-004**: The total compute time for the full experiment (data download, index construction, dual-agent execution, analysis) is measured against the 6-hour time limit defined in Assumptions. (See US-1, US-2)
- **SC-005**: The memory footprint of the execution environment is measured against the 7 GB RAM limit defined in Assumptions to ensure no OOM errors occur during dataset loading or LLM inference. (See US-1, US-2)

## Assumptions

- The PlanBench-XL dataset and its associated tool ecosystem definitions are available via the official repository linked in the original preprint and can be downloaded within the free-tier bandwidth limits.
- The "failure signatures" can be accurately extracted from the benchmark's ground truth using deterministic string matching or simple pattern recognition without requiring complex semantic analysis.
- The LLM used for agent reasoning (e.g., Llama-3-8B) can be hosted locally on the CPU-only runner or accessed via a free-tier API within the 6-hour time budget and 7 GB RAM constraint.
- The "implicit failure" subset of PlanBench-XL contains a sufficient number of tasks to perform a statistically valid test (power analysis deferred to implementation, but assumed >30 events per group; if <30, Fisher's Exact Test is used).
- The GitHub Actions free-tier runner provides sufficient CPU cycles to complete the sequential execution of both agents without timing out.
- The comparison between agents is associational; the study does not claim causal proof of "improvement" beyond the statistical significance of the observed difference in this specific experimental setup.