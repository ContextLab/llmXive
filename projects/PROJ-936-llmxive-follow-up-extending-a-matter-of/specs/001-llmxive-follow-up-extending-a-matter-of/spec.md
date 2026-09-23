# Feature Specification: LLM Agent Efficiency vs. Reasoning Trade-off Analysis

**Feature Branch**: `002-efficiency-reasoning-tradeoff`  
**Created**: 2026-07-31  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'A Matter of TASTE: Improving Coverage and Difficulty of Agent Benchmar'"

## User Scenarios & Testing

### User Story 1 - Baseline Execution & Metric Logging (Priority: P1)

**Journey**: The researcher downloads the $\tau^c$-Bench dataset, executes a suite of CPU-tractable agents (e.g., Llama-3-8B via `ollama`), and automatically logs success status, total API calls, and token consumption for each task step to enable the calculation of efficiency penalties.

**Why this priority**: This is the foundational data acquisition step. Without accurate logs of both success/failure and resource expenditure (calls/tokens), no trade-off analysis can be performed. It delivers the raw dataset required for all subsequent modeling.

**Independent Test**: The system can be tested by running the baseline agent on a small, fixed subset of 10 tasks and verifying that a CSV log is generated containing `task_id`, `success` (bool), `total_calls` (int), and `total_tokens` (int) for each run.

**Acceptance Scenarios**:

1. **Given** the $\tau^c$-Bench dataset is downloaded and parsed, **When** the baseline agent executes a task, **Then** the system logs a record with the task outcome and exact resource usage metrics.
2. **Given** an execution fails, **When** the agent halts, **Then** the log records the failure status and the cumulative resource cost up to the point of failure.
3. **Given** a successful execution, **When** the task completes, **Then** the log records the success status and the total resource cost, ensuring no steps are omitted from the count.

---

### User Story 2 - Efficiency Penalty Calculation & Task Filtering (Priority: P2)

**Journey**: The researcher calculates the "efficiency penalty" (ratio of agent calls to optimal calls) for each task, identifies tasks where this ratio exceeds a threshold of 2.0x, and filters the dataset to focus on "inefficiently solved" tasks for further analysis.

**Why this priority**: This step transforms raw logs into a structured variable (the predictor) and defines the specific subset of the problem space (high redundancy) where the trade-off is hypothesized to exist. It is necessary to isolate the phenomenon of interest.

**Independent Test**: The system can be tested by providing a mock dataset of 5 tasks with known "optimal call" counts and "agent call" counts; the system must correctly calculate the ratio, flag tasks with ratio > 2.0, and output the filtered list.

**Acceptance Scenarios**:

1. **Given** a task with an optimal path of 5 calls and an agent path of 12 calls, **When** the efficiency penalty is calculated, **Then** the system assigns a penalty score of 2.4 and includes the task in the "high redundancy" set.
2. **Given** a task with an optimal path of 5 calls and an agent path of 4 calls (over-optimization or error), **When** the penalty is calculated, **Then** the system assigns a score of 0.8 and excludes the task from the high-redundancy set.
3. **Given** the optimal path length is missing or zero for a task, **When** the calculation is attempted, **Then** the system logs a warning and excludes the task to prevent division-by-zero errors.

---

### User Story 3 - Trade-off Evaluation & Statistical Significance (Priority: P3)

**Journey**: The researcher re-runs agents on the "Efficiency-Tuned" subset, computes the correlation between efficiency penalty reduction and task success rate, and performs a paired t-test to determine if the performance drop on complex tasks is statistically significant.

**Why this priority**: This is the core hypothesis testing step. It directly answers the research question by quantifying the trade-off curve and establishing statistical confidence in the observed degradation.

**Independent Test**: The system can be tested by running the evaluation on a synthetic dataset where the relationship between efficiency and success is hard-coded (e.g., [deferred] success drop for high-efficiency tasks); the statistical module must report a significant p-value (< 0.05) for the difference.

**Acceptance Scenarios**:

1. **Given** the baseline and re-run results for the same set of complex tasks, **When** the paired t-test is executed, **Then** the system outputs a p-value and a confidence interval for the difference in success rates.
2. **Given** a correlation analysis between efficiency penalty and success rate, **When** the calculation completes, **Then** the system reports the Pearson correlation coefficient and indicates if the relationship is statistically significant.
3. **Given** the sample size is too small for a t-test (e.g., < 5 pairs), **When** the analysis is attempted, **Then** the system flags a power limitation warning and reports the descriptive statistics instead of a p-value.

### Edge Cases

- **What happens when the "optimal path length" is ambiguous?** If multiple valid minimal sequences exist with different lengths, the system must use the shortest valid sequence to define the optimal path, ensuring the penalty is maximized (conservative estimate).
- **How does the system handle agents that exceed the 6-hour time limit?** If an agent run exceeds the 6-hour CI limit, the system must terminate the process, log the task as "timeout" (failure), and record the resource cost up to the termination point to avoid hanging the pipeline.
- **What happens if the dataset lacks the "optimal path" ground truth?** If the $\tau^c$-Bench supplement does not provide optimal paths, the system must default to a heuristic (e.g., 1 step per tool type used) and flag this as a `[NEEDS CLARIFICATION]` or record it as a methodological assumption.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and parse the $\tau^c$-Bench dataset from the official HuggingFace repository, extracting task definitions and execution logs. (See US-1)
- **FR-002**: System MUST execute a suite of CPU-tractable agents (e.g., Llama-3-8B via `ollama`) on the dataset and record success/failure, total API calls, and token consumption per step. (See US-1)
- **FR-003**: System MUST calculate the efficiency penalty for each task as the ratio of (agent calls / optimal calls) and filter tasks where this ratio exceeds 2.0. (See US-2)
- **FR-004**: System MUST re-run agents on the filtered "Efficiency-Tuned" subset and compute the correlation between efficiency penalty reduction and the change in task success rate. (See US-3)
- **FR-005**: System MUST perform a paired t-test to determine if the drop in success rate on complex tasks is statistically significant (p < 0.05) compared to the baseline. (See US-3)
- **FR-006**: System MUST detect and handle cases where the dataset lacks the required "optimal path" variable by flagging a `[NEEDS CLARIFICATION: does $\tau^c$-Bench contain optimal path lengths for all tasks?]` and using a conservative heuristic if proceeding. (See US-2)

### Key Entities

- **Task**: A single unit of work from $\tau^c$-Bench, defined by a goal and environment state.
- **Execution Log**: A record of a single agent run, containing `task_id`, `success`, `total_calls`, `total_tokens`, and `duration`.
- **Efficiency Penalty**: A derived metric representing the ratio of agent resource usage to the optimal resource usage for a given task.
- **Trade-off Curve**: A statistical relationship (correlation/regression) linking efficiency penalties to success rates across the task subset.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Task success rate on complex, multi-hop tasks is measured against the baseline success rate to quantify performance degradation. (See FR-005)
- **SC-002**: Efficiency penalty (agent calls / optimal calls) is measured against the theoretical minimum valid sequence length to identify redundant strategies. (See FR-003)
- **SC-003**: Statistical significance of the trade-off is measured against the standard null hypothesis (p < 0.05) via paired t-test. (See FR-005)
- **SC-004**: Correlation strength between efficiency penalty and success rate is measured against a null correlation (r = 0) to validate the non-linear trade-off hypothesis. (See FR-004)
- **SC-005**: Computational feasibility is measured against the constraint of ≤6 hours total runtime on a 2-core CPU runner with no GPU. (See FR-002)

## Assumptions

- The $\tau^c$-Bench dataset (or its supplementary materials) contains the "optimal path length" or sufficient ground truth to derive a minimal valid tool sequence for every task; if not, the analysis will use a heuristic based on tool diversity, which may inflate the efficiency penalty.
- Open-source models like Llama-3-8B can be executed via `ollama` on a CPU-only GitHub Actions runner within the 6-hour time limit for the selected subset size (e.g., ≤ 200 tasks).
- The "brute-force" strategies observed in the baseline are not artifacts of the specific agent implementation but reflect a broader limitation in current LLM agents' meta-cognitive pruning capabilities.
- The dataset size and complexity are such that the full analysis (baseline + re-run + statistical testing) fits within ~7 GB RAM and ~14 GB disk, allowing for the use of `scikit-learn` regression trees without sampling.
- The "optimal path" is defined as the shortest sequence of valid tool calls that achieves the task goal, regardless of the agent's internal reasoning process.
