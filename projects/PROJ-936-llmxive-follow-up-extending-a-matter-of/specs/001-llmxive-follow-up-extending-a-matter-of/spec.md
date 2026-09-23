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

### User Story 3 - Task Evolution & Reward Modeling (Priority: P3)

**Journey**: The researcher trains a lightweight regression tree to predict efficiency penalties based on task features, then uses this model to generate "evolved" task variations (via the TASTE evolution process) that maximize the gap between minimal and agent sequences, creating a harder subset for trade-off validation.

**Why this priority**: This step implements the core "Task Evolution" mechanism from the methodology sketch. It transforms the static filtered list into a dynamic, evolved set of tasks specifically designed to stress-test the efficiency-reasoning trade-off, enabling the generation of new data points for the hypothesis test.

**Independent Test**: The system can be tested by providing a small set of tasks; the system must train a regression model, generate at least 5 evolved variations, and output a log showing the predicted vs. actual penalty increase for the new tasks.

**Acceptance Scenarios**:

1. **Given** a filtered set of high-penalty tasks, **When** the reward model is trained, **Then** the system outputs a regression tree with a validation score (R²) ≥ 0.6 on a hold-out set.
2. **Given** a trained model, **When** the evolution process runs, **Then** the system generates task variations that increase the predicted efficiency penalty by ≥ 10% compared to the original tasks.
3. **Given** the evolved tasks, **When** the baseline agent is run on them, **Then** the system logs the new efficiency penalties, confirming the evolution successfully increased task difficulty/redundancy.

---

### User Story 4 - Trade-off Evaluation & Statistical Significance (Priority: P4)

**Journey**: The researcher re-runs agents on the "Evolved" task subset, computes the correlation between the baseline efficiency penalty and the change in task success rate (baseline vs. evolved), and performs McNemar's test to determine if the performance drop on complex tasks is statistically significant.

**Why this priority**: This is the core hypothesis testing step. It directly answers the research question by quantifying the trade-off curve on the *evolved* data and establishing statistical confidence in the observed degradation using a method appropriate for binary outcomes.

**Independent Test**: The system can be tested by running the evaluation on a synthetic dataset where the relationship between efficiency and success is hard-coded (e.g., success rate drops by [deferred] for high-efficiency tasks); the statistical module must report a significant p-value (< 0.05) for the difference.

**Acceptance Scenarios**:

1. **Given** the baseline and evolved results for the same set of complex tasks, **When** McNemar's test is executed, **Then** the system outputs a p-value and indicates if the difference in success rates is statistically significant.
2. **Given** a correlation analysis between baseline efficiency penalty and the change in success rate, **When** the calculation completes, **Then** the system reports the Pearson correlation coefficient and indicates if the relationship is statistically significant.
3. **Given** the sample size is too small for McNemar's test (e.g., < 10 discordant pairs), **When** the analysis is attempted, **Then** the system flags a power limitation warning and reports the descriptive statistics instead of a p-value.

### Edge Cases

- **What happens when the "optimal path length" is ambiguous?** If multiple valid minimal sequences exist with different lengths, the system MUST use the **minimum number of distinct tool types required to achieve the task goal** (tool diversity count, k) as the definition of optimal path length. This heuristic ensures the efficiency penalty is maximized (conservative estimate) and aligns with the benchmark's focus on reasoning depth, acknowledging that this is a constructed proxy metric rather than an absolute physical minimum.
- **How does the system handle agents that exceed the 6-hour time limit?** If an agent run exceeds the 6-hour CI limit, the system must terminate the process, log the task as "timeout" (failure), and record the resource cost up to the termination point to avoid hanging the pipeline.
- **What happens if the dataset lacks the "optimal path" ground truth?** If the $\tau^c$-Bench supplement does not provide optimal paths, the system MUST default to the tool diversity heuristic (k) and log a specific warning code `OPTIMAL_PATH_MISSING` with the message: "Optimal path length not provided; using tool diversity heuristic (k)."

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and parse the $\tau^c$-Bench dataset from the official HuggingFace repository, extracting task definitions and execution logs. (See US-1)
- **FR-002**: System MUST execute a suite of CPU-tractable agents (e.g., Llama-3-8B via `ollama`) on the dataset and record success/failure, total API calls, and token consumption per step. (See US-1)
- **FR-003**: System MUST calculate the efficiency penalty for each task as the ratio of (agent calls / optimal calls) and filter tasks where this ratio exceeds 2.0. (See US-2)
- **FR-004**: System MUST re-run agents on the **evolved task variations** generated in US-3 and compute the correlation between the **baseline efficiency penalty** and the **change in task success rate**. (See US-4)
- **FR-005**: System MUST perform **McNemar's test** to determine if the drop in success rate on complex, evolved tasks is statistically significant (p < 0.05) compared to the baseline run of the *same* tasks. (See US-4)
- **FR-006**: System MUST detect cases where the dataset lacks the required "optimal path length" variable, apply the **tool diversity heuristic** (k) to derive the value, and log a warning with the code `OPTIMAL_PATH_MISSING` and the message "Optimal path length not provided; using tool diversity heuristic (k)." (See US-2, SC-002)
- **FR-007**: System MUST train a lightweight regression tree on the filtered task set to predict efficiency penalties and use this model to drive the generation of "evolved" task variations that maximize the penalty gap. (See US-3)
- **FR-008**: System MUST perform a sensitivity analysis by comparing the primary results (using tool diversity heuristic) against an alternative metric (e.g., minimum step count) to validate that the trade-off hypothesis holds regardless of the "optimal" definition. (See US-4)

### Key Entities

- **Task**: A single unit of work from $\tau^c$-Bench, defined by a goal and environment state.
- **Execution Log**: A record of a single agent run, containing `task_id`, `success`, `total_calls`, `total_tokens`, and `duration`.
- **Efficiency Penalty**: A derived metric representing the ratio of agent resource usage to the optimal resource usage for a given task.
- **Evolved Task**: A generated variation of an original task, modified to increase the gap between minimal and agent sequences.
- **Trade-off Curve**: A statistical relationship (correlation/regression) linking efficiency penalties to success rates across the task subset.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Task success rate on complex, multi-hop tasks is measured against the baseline success rate to quantify performance degradation. (See FR-005)
- **SC-002**: Efficiency penalty (agent calls / optimal calls) is measured against the theoretical minimum valid sequence length (tool diversity count) to identify redundant strategies. (See FR-003)
- **SC-003**: Statistical significance of the trade-off is measured against the standard null hypothesis (p < 0.05) via McNemar's test. (See FR-005)
- **SC-004**: Correlation strength between efficiency penalty and success rate is measured against a null correlation (r = 0) to validate the non-linear trade-off hypothesis. (See FR-004)
- **SC-005**: Computational feasibility is measured against the constraint of ≤6 hours total runtime on a 2-core CPU runner with no GPU, for the filtered subset of ≤200 tasks. (See FR-002)

## Assumptions

- The $\tau^c$-Bench dataset (or its supplementary materials) contains the "optimal path length" or sufficient ground truth to derive a minimal valid tool sequence for every task; if not, the analysis will use a heuristic based on **tool diversity** (minimum number of distinct tool types), which is acknowledged as a proxy metric for reasoning depth and may inflate the efficiency penalty.
- Open-source models like Llama-3-8B can be executed via `ollama` on a CPU-only GitHub Actions runner within the 6-hour time limit for the selected subset size (e.g., ≤ 200 tasks).
- The "brute-force" strategies observed in the baseline are not artifacts of the specific agent implementation but reflect a broader limitation in current LLM agents' meta-cognitive pruning capabilities.
- The dataset size and complexity are such that the full analysis (baseline + evolution + re-run + statistical testing) fits within ~7 GB RAM and ~14 GB disk, allowing for the use of `scikit-learn` regression trees without sampling.
- The "optimal path" is defined as the minimum number of **distinct tool types** required to achieve the task goal, serving as a constructed proxy for reasoning depth rather than an absolute step-count minimum.
- The "Evolved" task variations generated in US-3 are statistically representative of the difficulty distribution required to test the trade-off hypothesis.