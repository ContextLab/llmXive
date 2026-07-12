# Feature Specification: llmXive follow-up: extending "Agents' Last Exam"

**Feature Branch**: `001-llmxive-ale-extension`  
**Created**: 2026-07-12  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'Agents' Last Exam': Does decomposing long-horizon professional workflows into atomic steps reveal that agent failures are driven primarily by state persistence errors rather than reasoning deficits, and does explicit state recovery (via mechanisms like context checkpointing) significantly improve pass rates on these tasks?"

## User Scenarios & Testing

### User Story 1 - Automated Failure Mode Classification (Priority: P1)

**User Journey**: A researcher uploads a raw ALE execution trace log. The system parses the log, compares agent actions against the simulated environment state at each step, and outputs a structured classification of every failure as either "State Persistence Error" or "Reasoning Deficit."

**Why this priority**: This is the foundational diagnostic capability. Without accurately distinguishing between memory failures and reasoning failures, the subsequent intervention (checkpointing) cannot be evaluated, and the core research question remains unanswered.

**Independent Test**: Can be fully tested by feeding a pre-annotated "golden set" of 10 synthetic traces with known failure modes (derived from manual human review of raw logs, blind to script output) and verifying the script's classification accuracy against the ground truth labels.

**Acceptance Scenarios**:
1. **Given** a trace log where the agent attempts to edit a file that was deleted in step 2, **When** the classification script runs, **Then** the failure at the edit step is labeled "State Persistence Error."
2. **Given** a trace log where the agent attempts to perform a logical operation that contradicts the task goal despite having correct context, **When** the classification script runs, **Then** the failure is labeled "Reasoning Deficit."
3. **Given** a trace log with mixed errors, **When** the script runs, **Then** it outputs a JSON report containing keys `state_persistence_count`, `reasoning_deficit_count`, `total_failures`, and `classification_confidence`.

---

### User Story 2 - Context Checkpointing Intervention (Priority: P2)

**User Journey**: A researcher configures a lightweight wrapper around a 7B parameter model. The wrapper intercepts the agent's execution loop, forces a state summary regeneration every N steps, and injects this summary into the context window to test if pass rates improve on long-horizon tasks.

**Why this priority**: This implements the proposed solution to the diagnosed problem. It allows for the empirical test of whether state management is the bottleneck.

**Independent Test**: Can be tested by running a fixed set of short ALE tasks with the checkpointing wrapper enabled vs. disabled. and comparing the "Step Success Rate" for the specific steps where state persistence is critical.

**Acceptance Scenarios**:
1. **Given** an agent execution loop configured with `checkpoint_interval = 3`, **When** the agent completes the 3rd step, **Then** the wrapper forces a state summary generation and injects it into the prompt for the 4th step.
2. **Given** a task requiring the agent to recall a file path created 10 steps ago, **When** the checkpointing wrapper is active, **Then** the summary injected at step 11 contains the correct file path.
3. **Given** a CPU-only environment with 7GB RAM, **When** the wrapper runs with a 7B model, **Then** the execution does not exceed the memory limit or crash due to context window overflow.

---

### User Story 3 - Statistical Significance & Reporting (Priority: P3)

**User Journey**: After running the baseline and intervention experiments, the system aggregates the pass rates, performs a statistical test (McNemar's or Bootstrap), and generates a final report indicating whether the improvement is statistically significant.

**Why this priority**: This provides the scientific validity of the findings, transforming raw data into a publishable result that addresses the research question.

**Independent Test**: Can be tested by providing the system with two sets of binary outcomes (Pass/Fail) for the same tasks (Baseline vs. Intervention) and verifying the calculated p-value matches the expected result from a standard statistical library.

**Acceptance Scenarios**:
1. **Given** baseline pass rates of [deferred] and intervention pass rates of [deferred] on 100 tasks, **When** the statistical analysis module runs, **Then** it outputs a p-value and a conclusion regarding statistical significance (e.g., "Significant at p < 0.05").
2. **Given** a dataset with multiple hypothesis tests (e.g., analyzing different task categories), **When** the analysis runs, **Then** it applies a multiple-comparison correction (e.g., Bonferroni or FDR) to the reported p-values.
3. **Given** the experimental results, **When** the report is generated, **Then** it includes a sensitivity analysis showing how the pass rate changes if the checkpoint interval is varied (e.g., N=1, N=3, N=5).

### Edge Cases

- **What happens when** the execution trace is incomplete or corrupted? The system must skip the corrupted entry and log a warning rather than crashing, ensuring the rest of the dataset is processed.
- **How does the system handle** a checkpoint summary that exceeds the model's context window limit? The system must truncate the summary or use a compression heuristic to ensure the prompt remains valid.
- **What happens when** the statistical test yields a p-value exactly on the threshold (e.g., 0.05)? The system must report the exact p-value and the raw counts, avoiding binary "pass/fail" language in the raw output.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST parse ALE execution logs to identify the environment state (file system, variables) at every atomic step and compare it against the agent's claimed context. This comparison MUST follow a **Normalization Protocol**: (a) floating-point values are compared with a tolerance of 1e-6, (b) timestamps and random IDs are stripped, and (c) object references are canonicalized before comparison. (See US-1)
- **FR-002**: The system MUST classify every detected agent failure into exactly one of two categories: "State Persistence Error" or "Reasoning Deficit." A "State Persistence Error" occurs when the agent's action contradicts the reconstructed environment state (per FR-001). A "Reasoning Deficit" occurs when the agent's action is logically invalid relative to the task goal, as defined by static constraints extracted from the `task_description` field of the input log (See FR-007), independent of the environment state. (See US-1)
- **FR-003**: The system MUST implement a Context-Checkpointing wrapper that forces a state summary regeneration and injection into the prompt at a configurable interval (N steps). (See US-2)
- **FR-004**: The system MUST execute the agent tasks on a CPU-only environment using a 7B parameter model, ensuring total memory usage stays within 7GB RAM. The system MUST attempt execution within the target time window and log a timeout event if exceeded, rather than failing the functional contract. (See US-2)
- **FR-005**: The system MUST perform statistical significance testing (e.g., McNemar's test) on the pass rates of the baseline vs. the intervention, including a correction for multiple comparisons if >1 hypothesis is tested. This test is valid ONLY if the tasks are strictly paired (See FR-008). (See US-3)
- **FR-006**: The system MUST perform a sensitivity analysis on the checkpoint interval (N) by testing exactly three values: N=1, N=3, and N=5, and reporting the variation in pass rates. (See US-3)
- **FR-007**: The system MUST implement a Task Goal Validator that extracts logical constraints exclusively from the static `task_description` field of the input ALE log using a deterministic template matcher, ensuring constraints are independent of agent execution or state reconstruction. (See FR-002)
- **FR-008**: The system MUST ensure that baseline and intervention runs use identical task instances with fixed random seeds to guarantee strict pairing for statistical analysis. (See FR-005)
- **FR-009**: The system MUST validate the environment state reconstruction accuracy against a human-annotated subset of logs. The reconstruction MUST achieve an accuracy of ≥95% before the full classification analysis proceeds. (See US-1)

### Key Entities

- **Execution Trace**: A sequential record of agent actions, environment states, and outcomes for a single ALE task.
- **Failure Label**: A categorical attribute assigned to a failed step, indicating either "State Persistence Error" or "Reasoning Deficit."
- **Checkpoint Summary**: A compressed text representation of the current environment state (files, variables, goals) injected into the context window.
- **Pass Rate**: The proportion of tasks completed successfully out of the total attempted tasks.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation phase.

- **SC-001**: The proportion of failures classified as "State Persistence Error" is measured against the total number of failures to determine the dominant failure mode. (See FR-002)
- **SC-002**: The Full Pass Rate of the agent with the Context-Checkpointing intervention is measured against the Full Pass Rate of the baseline agent (no intervention). (See FR-003)
- **SC-003**: The statistical significance (p-value) of the pass rate difference is measured against the standard alpha threshold of 0.05, with correction for multiplicity applied. (See FR-005)
- **SC-004**: The sensitivity of the pass rate to the checkpoint interval (N) is measured by comparing the pass rates across the set {1, 3, 5}. (See FR-006)
- **SC-005**: The memory footprint of the 7B model with the checkpointing wrapper is measured against the 7GB RAM limit to ensure CPU feasibility. (See FR-004)
- **SC-006**: The reconstruction accuracy is measured against a human-annotated subset to verify it meets the ≥95% threshold. (See FR-009)

## Assumptions

- **Assumption about dataset availability**: The public ALE dataset and logs are available via the official repository and contain sufficient execution traces (≥5 steps) with partial failure data to perform the analysis.
- **Assumption about model capability**: A 7B parameter open-weight model (e.g., Llama-3-8B or similar) is capable of running on a CPU-only GitHub Actions runner within 7GB RAM using 4-bit quantization (if supported by CPU-only backends) or standard precision on a sampled subset, without requiring GPU acceleration.
- **Assumption about inference engine**: The local inference engine (e.g., `llama.cpp` or `transformers` with CPU device) supports the selected model size and quantization method without requiring CUDA.
- **Assumption about trace granularity**: The ALE logs contain sufficient granularity (step-by-step environment state snapshots) to reliably distinguish between "State Persistence" and "Reasoning" failures via rule-based heuristics.
- **Assumption about statistical power**: The available subset of ALE tasks (filtered for complexity) is large enough to perform a meaningful statistical test (e.g., N ≥ 30 tasks per condition) to detect a moderate effect size, or the study will explicitly report power limitations.
- **Assumption about human annotation**: The "golden set" of 10 synthetic traces used for validation is manually curated by human experts who review raw logs without executing the classification script, ensuring independent ground truth.
- **Assumption about performance constraint**: The target execution time per task is a benchmark for resource estimation and experimental planning, not a functional requirement.; the system is designed to log timeouts rather than fail if this limit is exceeded due to hardware variance.