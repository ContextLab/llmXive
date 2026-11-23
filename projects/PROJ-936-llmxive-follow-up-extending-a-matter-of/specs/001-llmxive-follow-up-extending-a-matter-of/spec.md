# Feature Specification: LLM Agent Efficiency vs. Reasoning Trade-off Analysis

**Feature Branch**: `002-efficiency-reasoning-tradeoff`  
**Created**: 2026-07-31  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'A Matter of TASTE: Improving Coverage and Difficulty of Agent Benchmar'"

## User Scenarios & Testing

### User Story 1 - Baseline Execution & Metric Logging (Priority: P1) (Identifier: US-1)

**Journey**: The researcher downloads the $\tau^c$-Bench dataset, executes a suite of CPU-tractable agents (e.g., Llama-3-8B via `ollama`), and automatically logs success status, total API calls, and token consumption for each task step to enable the calculation of efficiency penalties.

**Why this priority**: This is the foundational data acquisition step. Without accurate logs of both success/failure and resource expenditure (calls/tokens), no trade-off analysis can be performed. It delivers the raw dataset required for all subsequent modeling.

**Independent Test**: The system can be tested by running the baseline agent on a small, fixed subset of tasks and verifying that a CSV log is generated containing `task_id`, `success` (bool), `total_calls` (int), and `total_tokens` (int) for each run.

**Acceptance Scenarios**:

1. **Given** the $\tau^c$-Bench dataset is downloaded and parsed, **When** the baseline agent executes a task, **Then** the system logs a record with the task outcome and exact resource usage metrics.
2. **Given** an execution fails, **When** the agent halts, **Then** the log records the failure status and the cumulative resource cost up to the point of failure.
3. **Given** a successful execution, **When** the task completes, **Then** the log records the success status and the total resource cost, ensuring no steps are omitted from the count.

---

### User Story 2 - Efficiency Penalty Calculation & Task Filtering (Priority: P2) (Identifier: US-2)

**Journey**: The researcher calculates the "efficiency penalty" (ratio of agent calls to optimal path length) for each task, identifies tasks where this ratio exceeds a substantially elevated threshold, and filters the dataset to focus on "inefficiently solved" tasks for further analysis.

**Why this priority**: This step transforms raw logs into a structured variable (the predictor) and defines the specific subset of the problem space (high redundancy) where the trade-off is hypothesized to exist. It is necessary to isolate the phenomenon of interest.

**Independent Test**: The system can be tested by providing a mock dataset of 5 tasks with known "optimal path length" counts and "agent call" counts; the system must correctly calculate the ratio, flag tasks with ratio > 2.0, and output the filtered list.

**Acceptance Scenarios**:

1. **Given** a task with an optimal path length of 5 calls and an agent path of 12 calls, **When** the efficiency penalty is calculated, **Then** the system assigns a penalty score of 2.4 and includes the task in the "high redundancy" set.
2. **Given** a task with an optimal path length of 5 calls and an agent path of 4 calls (over‑optimization or error), **When** the penalty is calculated, **Then** the system assigns a score of 0.8 and excludes the task from the high‑redundancy set.
3. **Given** the optimal path length is missing or zero for a task, **When** the calculation is attempted, **Then** the system logs a warning and excludes the task to prevent division‑by‑zero errors.

---

### User Story 3 - Task Evolution & Reward Modeling (Priority: P3) (Identifier: US-3)

**Journey**: The researcher trains a lightweight regression tree to predict efficiency penalties based on task features, then uses this model to generate "evolved" task variations (via the TASTE evolution process) that maximize the gap between minimal and agent sequences, creating a harder subset for trade‑off validation.

**Why this priority**: This step implements the core "Task Evolution" mechanism from the methodology sketch. It transforms the static filtered list into a dynamic, evolved set of tasks specifically designed to stress‑test the efficiency‑reasoning trade‑off, enabling the generation of new data points for the hypothesis test.

**Independent Test**: The system can be tested by providing a small set of tasks; the system must train a regression model, generate at least 5 evolved variations, and output a log showing the predicted vs. actual penalty increase for the new tasks.

**Acceptance Scenarios**:

1. **Given** a filtered set of high‑penalty tasks, **When** the reward model is trained, **Then** the system outputs a regression tree with a validation R² ≥ 0.6 on a hold‑out set.
2. **Given** a trained model, **When** the evolution process runs, **Then** the system generates task variations that increase the *observed* efficiency penalty by ≥ 10 % compared to the source tasks.
3. **Given** the evolved tasks, **When** the baseline agent is run on them, **Then** the system logs the new efficiency penalties, confirming the evolution successfully increased task difficulty/redundancy.

---

### User Story 4 - Trade‑off Evaluation & Statistical Significance (Priority: P4) (Identifier: US-4)

**Journey**: The researcher re‑runs agents on the "Evolved" task subset, computes the correlation between the baseline efficiency penalty and the change in task success rate (baseline vs. evolved), and performs a chi‑squared test of independence to determine if the success‑rate difference between baseline and evolved groups is statistically significant.

**Why this priority**: This is the core hypothesis‑testing step. It directly answers the research question by quantifying the trade‑off curve on the *evolved* data and establishing statistical confidence in the observed degradation using a method appropriate for independent binary outcomes.

**Independent Test**: The system can be tested by running the evaluation on a synthetic dataset where the success‑rate difference between baseline and evolved groups is known; the statistical module must report a significant chi‑squared p‑value (< 0.05) for the difference.

**Acceptance Scenarios**:

1. **Given** the baseline and evolved results for the same set of complex tasks, **When** the chi‑squared test is executed, **Then** the system outputs a p‑value and indicates whether the difference in success rates is statistically significant.
2. **Given** a correlation analysis between baseline efficiency penalty and the change in success rate, **When** the calculation completes, **Then** the system reports the partial correlation coefficient (controlling for difficulty) and indicates if the relationship is statistically significant (p < 0.05).
3. **Given** the sample size is too small for reliable chi‑squared inference (e.g., any cell count < 5), **When** the analysis is attempted, **Then** the system flags a warning about low expected counts and reports only the descriptive statistics.

### Edge Cases

- **What happens when the "optimal path length" is ambiguous?** If multiple valid minimal sequences exist with different lengths, the system MUST use the **minimum number of steps** among all valid optimal paths as the definition of optimal path length. This ensures a conservative denominator for the efficiency penalty.

- **How does the system handle agents that exceed the 6‑hour time limit?** If an agent run exceeds the 6‑hour CI limit, the system must terminate the process, log the task as "timeout" (failure), and record the resource cost up to the termination point to avoid hanging the pipeline.

- **What happens if the dataset lacks the "optimal path length" ground truth?** The specification now assumes the dataset provides optimal path lengths; if any task is missing this value, the run aborts with a clear error message indicating the missing field.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and parse the $\tau^c$-Bench dataset from the official HuggingFace repository, extracting task definitions and execution logs. (See US-1)

- **FR-002**: System MUST execute a suite of CPU‑tractable agents (e.g., Llama‑3‑8B via `ollama`) on the dataset and record success/failure, total API calls, and token consumption per step. (See US-1)

- **FR-003**: System MUST calculate the efficiency penalty for each task as **agent_calls / optimal_path_length** and filter tasks where this ratio exceeds **2.0** for downstream analyses; correlation and other global analyses will use the full, unfiltered task set. (See US-2)

- **FR-004**: System MUST compute a **partial correlation** (Spearman) between the continuous efficiency‑penalty score and the binary baseline success rate **controlling for a difficulty score** (derived independently from task features). The system must report the correlation coefficient and its two‑tailed p‑value. (See US-4)

- **FR-005**: System MUST perform a **chi‑squared test of independence** to assess whether success rates differ between baseline and evolved task groups, reporting the chi‑squared statistic, degrees of freedom, and p‑value. Significance is declared at **p < 0.05**. (See US-4)

- **FR-007**: System MUST train a lightweight **DecisionTreeRegressor** on the **filtered high‑penalty task set** (ratio > 2.0), using a hold‑out validation split (e.g., [deferred] of the filtered set). The model must achieve **R² ≥ 0.6** on the hold‑out data before being used to generate evolved tasks. (See US-3)

- **FR-008**: System MUST generate evolved task variations using the trained regression model, ensuring that the **observed** efficiency penalty of each evolved task is **≥ 10 %** higher than that of its source task. Each evolved task is emitted as a full Task record conforming to `evolved_task.schema.yaml`, including `optimal_path_length`, `features`, etc. (See US-3)

- **FR-009**: System MUST conduct a **formal power analysis** (targeting **≥ 80 % power** to detect a medium effect size **d = 0.5** at **α = 0.05**) and document the required sample size. The analysis justifies the cap of **≤ 200** tasks for the filtered subset. (See SC‑011)

- **FR-010**: System MUST compute a **task‑difficulty score** using a model trained **exclusively on task‑feature data** (excluding any penalty‑derived features). This difficulty score is used as the covariate in FR‑004’s partial‑correlation computation. (See US-4)

- **FR-011**: System MUST log completeness – **≥ 99 %** of tasks must have non‑null `task_id`, `success`, `total_calls`, and `total_tokens` fields recorded; any missing field causes the run to be flagged as failed. (See FR‑001, FR‑002)

### Key Entities

- **Task**: A single unit of work from $\tau^c$-Bench, defined by a goal and environment state.
- **Execution Log**: A record of a single agent run, containing `task_id`, `success`, `total_calls`, `total_tokens`, and `duration`.
- **Efficiency Penalty**: A derived metric representing the ratio of agent resource usage to the optimal resource usage for a given task.
- **Difficulty Score**: A numeric estimate of intrinsic task difficulty produced by an independent model trained on task features only.
- **Evolved Task**: A generated variation of an original task, modified to increase the gap between minimal and agent sequences.
- **Trade‑off Curve**: A statistical relationship (partial correlation/regression) linking efficiency penalties to success rates across the task subset.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Task success rate on complex, multi‑hop tasks must drop by at least **[deferred]** when comparing evolved to baseline results (success_evolved ≤ 0.90 × success_baseline) and this drop must be statistically significant (**p < 0.05**) per **SC‑010**. (See FR‑005)

- **SC-002**: Efficiency penalty (agent_calls / optimal_path_length) is measured against the theoretical minimum valid sequence length; at least **[deferred]** of tasks must have a penalty **> 2.0** to ensure sufficient coverage of redundant strategies. (See FR‑003)

- **SC-003**: Statistical significance of the chi‑squared test is measured against the null hypothesis of independence (p < 0.05). (See FR‑005)

- **SC-004**: Partial correlation strength between efficiency penalty and baseline success rate, **controlling for difficulty**, must be statistically significant (**p < 0.05**) and have absolute value **≥ 0.2**. (See FR‑004)

- **SC-005**: Computational feasibility is measured against the constraint of **≤ 6 hours** total runtime on a 2‑core CPU runner with no GPU, for the filtered subset of **≤ 200** tasks. (See FR‑002)

- **SC-006**: Log completeness – **≥ 99 %** of tasks must have non‑null `task_id`, `success`, `total_calls`, and `total_tokens` fields recorded; any missing field causes the run to be flagged as failed. (See FR‑011)

- **SC-007**: Regression‑tree validation – hold‑out R² must be **≥ 0.6**, confirming the model captures sufficient variance to be useful for evolution. (See FR‑007)

- **SC-008**: Evolved‑task penalty increase – the **observed** efficiency penalty of evolved tasks must be **≥ 10 %** higher than that of their source tasks, demonstrating effective difficulty amplification. (See FR‑008)

- **SC-009**: Correlation significance – the partial correlation reported in SC‑004 must satisfy the numeric thresholds described above. (See FR‑004)

- **SC-010**: Statistical significance of success‑rate difference – the chi‑squared test reported in FR‑005 must yield **p < 0.05**. (See FR‑005)

- **SC-011**: Power analysis – the formal power analysis (FR‑009) must demonstrate that the chosen sample size (≤ 200 tasks) provides **≥ 80 % power** to detect an effect size **d = 0.5** at **α = 0.05**. (See FR‑009)

## Assumptions

- The $\tau^c$-Bench dataset (or its supplementary materials) provides the **optimal path length** for every task; this value is used as the denominator of the efficiency penalty.
- Open‑source models like Llama‑3‑8B can be executed via `ollama` on a CPU‑only GitHub Actions runner within the 6‑hour time limit for the selected subset size (e.g., ≤ 200 tasks).
- The "brute‑force" strategies observed in the baseline are not artifacts of the specific agent implementation but reflect a broader limitation in current LLM agents' meta‑cognitive pruning capabilities.
- The dataset size and complexity are such that the full analysis (baseline + evolution + re‑run + statistical testing) fits within ~7 GB RAM and ~14 GB disk, allowing for the use of `scikit-learn` regression trees without sampling.
- The "optimal path" is defined as the **minimum number of steps** required to achieve the task goal, as provided by the benchmark; when multiple optimal sequences exist, the shortest length is used.
- The "Evolved" task variations generated in US‑3 are statistically representative of the difficulty distribution required to test the trade‑off hypothesis.
- **Difficulty scores** used as covariates in FR‑004 are derived from a model trained **only on raw task features** (e.g., tool count, state‑space size) and **do not incorporate** the efficiency‑penalty metric, thereby avoiding circularity.
- Partial correlation is preferred over simple point‑biserial correlation to control for the confounding influence of task difficulty on both penalty and success outcomes.
