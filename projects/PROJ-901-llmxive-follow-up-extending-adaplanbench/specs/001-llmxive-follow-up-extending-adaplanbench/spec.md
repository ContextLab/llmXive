# Feature Specification: llmXive follow-up: extending "AdaPlanBench: Evaluating Adaptive Planning in Large Language Model Age"

**Feature Branch**: `001-gene-regulation`  
**Created**: 2026-07-14  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'AdaPlanBench: Evaluating Adaptive Planning in Large Language Model Age'"

## User Scenarios & Testing

### User Story 1 - Dataset Preparation and Constraint Filtering (Priority: P1)

The researcher needs to isolate the specific subset of the AdaPlanBench dataset where constraints are revealed progressively (5+ constraints) to ensure the experiment tests the exact failure mode of interest (context management under accumulation).

**Why this priority**: This is the foundational data layer. Without a correctly filtered dataset where the "number of constraints" variable is explicitly defined and measurable, no subsequent analysis of architecture performance is possible. It establishes the independent variable.

**Independent Test**: Can be fully tested by loading the raw dataset, applying the filter logic for tasks with ≥5 revealed constraints, and verifying the output count and the "constraint_count" field for a sample of 10 tasks against the original dataset metadata.

**Acceptance Scenarios**:

1. **Given** the raw AdaPlanBench dataset of 307 household tasks, **When** the system filters for tasks with ≥5 progressive constraint reveals, **Then** the output subset contains only those specific tasks and includes a metadata column recording the exact number of constraints for each task.
2. **Given** a task with exactly 4 constraints, **When** the filtering logic is applied, **Then** the task is excluded from the working dataset.

---

### User Story 2 - Dual-Track Agent Execution and Constraint Logging (Priority: P2)

The researcher needs to execute the dual-track architecture (SLM generator + deterministic constraint store) on the filtered dataset, ensuring that every generated plan is checked against the explicit constraint store as constraints are revealed during the task.

**Why this priority**: This implements the core experimental intervention. It distinguishes the "dual-track" condition from the "monolithic" baseline and generates the primary data (violation rates) needed for the hypothesis test.

**Independent Test**: Can be fully tested by running the agent on a single known task with a specific constraint violation, verifying that the rule-based module intercepts the violation, triggers a correction, and logs the interaction in the constraint store.

**Acceptance Scenarios**:

1. **Given** a task with a known constraint "Do not use the microwave," **When** the SLM proposes an action "Heat soup in microwave," **Then** the rule-based module detects the violation, rejects the output, and logs the correction event.
2. **Given** a task with no conflicting constraints, **When** the SLM generates a plan, **Then** the system accepts the plan immediately without triggering the correction module.

---

### User Story 3 - Statistical Analysis of Architecture Interaction (Priority: P3)

The researcher needs to perform a Generalized Linear Mixed Model (GLMM) with a binomial link function to determine if there is a statistically significant interaction between "number of constraints" and "agent architecture" on the constraint violation rate.

**Why this priority**: This answers the research question. It transforms the raw execution logs into a scientific conclusion regarding whether explicit constraint tracking mitigates performance degradation, using a methodologically sound approach for binary repeated measures.

**Independent Test**: Can be fully tested by feeding the execution logs (architecture type, constraint count, violation boolean, task ID) into the analysis script and verifying that the output includes the fixed effect estimates, p-values for the interaction term, and model convergence diagnostics.

**Acceptance Scenarios**:

1. **Given** execution logs showing monolithic models failing at high constraint counts while dual-track models succeed, **When** the GLMM is run, **Then** the output reports a significant interaction effect (p < 0.05) between architecture and constraint count.
2. **Given** a dataset where both architectures fail equally regardless of constraint count, **When** the GLMM is run, **Then** the output reports a non-significant interaction effect.

---

### Edge Cases

- What happens if the SLM generates a response that violates a constraint but the rule-based module fails to parse the intent (false negative in detection)?
- How does the system handle tasks where the constraint is implicit or requires common-sense reasoning rather than explicit keyword matching?
- What is the behavior if the HuggingFace model download fails or exceeds the 7GB RAM limit during initialization?

## Requirements

### Functional Requirements

- **FR-001**: System MUST download the AdaPlanBench dataset and filter for the subset of tasks containing ≥5 progressive constraint reveals (See US-1).
- **FR-002**: System MUST implement a deterministic key-value store to log and resolve constraints as they are revealed during task execution (See US-2).
- **FR-003**: System MUST implement a rule-based conflict resolution module that checks the SLM's proposed action against the stored constraint state and forces a revision if a violation is detected (See US-2).
- **FR-004**: System MUST execute the dual-track agent and the monolithic baseline on the filtered dataset using the original AdaPlanBench automated judges to score task success and constraint adherence (See US-2).
- **FR-005**: System MUST perform a Generalized Linear Mixed Model (GLMM) with a binomial link function to test for the interaction between "number of constraints" and "agent architecture" on the constraint violation rate (See US-3).
- **FR-006**: System MUST log CPU usage and memory footprint during execution to verify the process remains within the 2 vCPU and 7GB RAM limits (See US-3).
- **FR-007**: System MUST define violation detection logic using exact string matching, case-insensitive substring matching, and explicit negation patterns; if a constraint is implicit or the pattern fails, the system MUST log the event as "unverified" and flag it for human review (See US-2).
- **FR-008**: If the rule-based module fails to parse the intent of a generated action, the system MUST log a "false_negative" event, retain the original plan, and increment a "parsing_failure" counter (See US-2).
- **FR-009**: For tasks where constraints are implicit or require common-sense reasoning, the system MUST NOT classify them as violations; instead, it MUST log them as "implicit_unverified" and exclude them from the primary violation rate calculation (See US-2).
- **FR-010**: System MUST randomly select a sample of 50 tasks from the filtered dataset for manual human annotation to establish an independent ground truth for constraint violations, independent of the rule-based module (See US-3).
- **FR-011**: System MUST perform a power analysis on the filtered subset to confirm the sample size is sufficient to detect a medium effect size (Cohen's f² ≥ 0.15) with power ≥ 0.80 for the chosen GLMM (See US-3).

### Key Entities

- **Task Instance**: A specific household task from AdaPlanBench, containing the initial prompt, the sequence of progressive constraints, and the ground-truth solution.
- **Constraint Log**: A structured record of all active constraints for a specific task instance, used by the conflict resolution module.
- **Execution Trace**: A record of the agent's output, the constraint check result (pass/fail/unverified), and the final adherence score.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The constraint violation rate for the dual-track architecture is measured against the violation rate of the monolithic baseline across increasing constraint counts, validated against an independent human-annotated ground truth sample (See US-3).
- **SC-002**: The statistical significance of the interaction effect between architecture type and constraint count is measured against the alpha level of 0.05 using a Generalized Linear Mixed Model (GLMM) with a binomial link function (See US-3).
- **SC-003**: The memory footprint of the dual-track agent is measured against the 2 vCPU and 7GB RAM limits to ensure feasibility (See US-3).
- **SC-004**: The adherence rate of the dual-track agent is measured against the target threshold of >85% (lower bound of the [deferred] Wilson score interval) on the filtered subset (≥5 constraints) to confirm the hypothesis that explicit memory mitigates degradation (See US-2).
- **SC-005**: The agreement rate between the rule-based detection module and the independent human-annotated ground truth is measured to validate the precision of the violation detection logic (See US-3).

## Assumptions

- The AdaPlanBench dataset (specifically the household tasks) is publicly accessible via the official repository or arXiv supplementary materials and contains the necessary variables for progressive constraint tracking.
- The Phi-mini model (or similar SLM) can be loaded and run on a CPU-only environment within the 2 vCPU and 7GB RAM limits without requiring GPU acceleration or 8-bit quantization.
- The "constraint violation" can be reliably detected via a rule-based module using keyword matching and simple logical inference for explicit constraints; implicit constraints are handled by logging as "unverified" rather than forcing a binary decision.
- The Generalized Linear Mixed Model (GLMM) is the appropriate statistical test for the experimental design, assuming the data meets convergence criteria for binary repeated measures.
- The monolithic baseline models (e.g., GPT-4, Llama-3-70b) will be evaluated using the same API or weights available at the time of execution, acknowledging potential availability constraints.
- The "interaction effect" hypothesis assumes that the number of constraints is treated as a categorical factor (levels: 5, 6, 7+) if the distribution is sparse, or as a continuous ordinal variable if sufficient data exists.
- A sample size of 50 human-annotated tasks is sufficient to validate the rule-based detection logic with a margin of error ≤ 10% for the violation rate.