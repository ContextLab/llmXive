# Feature Specification: NatureBench Abstraction Distance Analysis

**Feature Branch**: `001-naturebench-abstraction-distance`  
**Created**: 2026-07-01  
**Status**: Draft  
**Input**: User description: "How does the 'abstraction distance' between a scientific paper's textual method description and standard library implementations predict the failure modes of automated code reconstruction in cross-disciplinary scientific domains?"

## User Scenarios & Testing

### User Story 1 - Data Acquisition and Agent Execution (Priority: P1)

**Journey**: The system downloads the NatureBench dataset and executes three open-source coding agents (SWE-agent, OpenHands, etc.) on these tasks within a strict time limit per task. to generate execution logs and numerical results.

**Why this priority**: This is the foundational data generation step. Without the execution logs and result comparisons, no analysis of failure modes or correlation with abstraction distance can occur. It delivers the raw evidence required for the entire study.

**Independent Test**: The system can be tested by verifying that 90 task directories exist initially, and that ≥ 85 valid task directories remain after filtering for missing ground truth, each containing agent execution logs, a generated code artifact (or error log), and a parsed result file comparing the agent's output to the ground-truth SOTA value.

**Acceptance Scenarios**:

1. **Given** the NatureBench HuggingFace repository URL is valid, **When** the data acquisition script runs, **Then** all 90 task directories are populated with the original method descriptions, ground-truth SOTA values, and task-specific data files.
2. **Given** a specific task and an agent configuration, **When** the agent execution process starts, **Then** the process terminates within 4 hours (wall-clock) and produces either a successful code artifact with a numerical result or a failure log indicating the specific error type (Syntax, Timeout, etc.).
3. **Given** a completed execution, **When** the result parser runs, **Then** it extracts the final numerical output and calculates the relative error gap ($g$) against the ground-truth SOTA value, storing this in a structured JSON result file.

---

### User Story 2 - Abstraction Distance Scoring (Priority: P2)

**Journey**: The system applies an automated scoring rubric (defined by domain experts) to rate each of the 90 tasks on a 1–5 scale based on the "abstraction distance," measuring the frequency of standard library usage versus the need for novel algorithmic derivation.

**Why this priority**: This creates the independent variable (predictor) for the study. It transforms the qualitative textual descriptions into a quantitative metric required for the correlation analysis.

**Independent Test**: The system can be tested by running the scoring rubric on a subset of tasks and verifying that the output is a numeric score between 1 and 5 for each task, with a clear mapping to the specific textual criteria used (stdlib call frequency).

**Acceptance Scenarios**:

1. **Given** a task's method description text, **When** the abstraction scoring rubric is applied, **Then** the system outputs a single integer score (1–5) and a justification string citing the calculated standard library call percentage and the corresponding score band (e.g., "[deferred] stdlib calls -> Score 1").
2. **Given** the full set of 90 tasks, **When** the scoring process completes, **Then** a master CSV file is generated containing `task_id`, `method_description`, and `abstraction_distance_score` for every task.
3. **Given** a specific score of 1 or 5, **When** reviewed, **Then** the justification explicitly confirms the task relies almost entirely on standard libraries (≥80% calls) or requires significant novel algorithmic derivation (≤19% calls).

---

### User Story 3 - Statistical Correlation Analysis (Priority: P3)

**Journey**: The system performs a Spearman's Rank Correlation test between the "abstraction distance" scores and the binary "Wrong Method Choice" failure outcome, calculating confidence intervals and generating a visualization of the relationship.

**Why this priority**: This delivers the primary research finding. It answers the core research question by quantifying the relationship between the predictor and the specific failure mode using a method suitable for ordinal data.

**Independent Test**: The system can be tested by running the analysis script on the generated result and score datasets, verifying that a correlation coefficient ($\rho$) and p-value are output, and that the "Wrong Method Choice" failures are correctly isolated using the defined hierarchy.

**Acceptance Scenarios**:

1. **Given** the dataset containing `abstraction_distance_score` and `failure_category` for all 90 tasks, **When** the analysis script runs, **Then** it correctly filters for the "Wrong Method Choice" failures (using the Failure Hierarchy) and calculates the Spearman's Rank Correlation coefficient ($\rho$) and p-value.
2. **Given** the correlation results, **When** the binomial proportion confidence interval (Clopper-Pearson for n < 30, Wilson for n ≥ 30) is calculated for domain clusters, **Then** the output includes the lower and upper bounds for the failure rate in each cluster. If any cluster has n < 10, the system aggregates them into a 'Cross-Domain' group for the primary test.
3. **Given** the final analysis, **When** the report is generated, **Then** it includes a scatter plot of abstraction distance vs. failure rate (binary) with the regression line and a text summary stating whether the correlation is statistically significant ($p < 0.05$).

---

### Edge Cases

- **What happens when** an agent execution times out exactly at 4 hours? The system must classify this as a "Timeout" failure (lowest priority), not a "Wrong Method Choice," and exclude it from the correlation analysis for that specific metric.
- **How does the system handle** a task where the agent produces a numerical result but the ground-truth SOTA value is missing or malformed? The system must flag the task as "Invalid Ground Truth" and exclude it from the correlation calculation, recording the exclusion reason.
- **What happens when** the abstraction distance scoring rubric yields a tie or ambiguous score? The system uses the calculated standard library percentage to deterministically assign the score based on the defined thresholds (no ambiguity possible).
- **Failure Hierarchy**: When multiple failure modes occur (e.g., a wrong method call leads to a syntax error), the system MUST classify the task using this strict priority: 1. Syntax Error, 2. Wrong Method Choice, 3. Data Mismatch, 4. Timeout. Only the highest-priority failure is recorded.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download the NatureBench dataset (90 tasks) from the specified HuggingFace repository and validate the integrity of the ground-truth SOTA values for all tasks (See US-1).
- **FR-002**: System MUST execute three distinct open-source coding agents on each of the tasks with a hard 4-hour wall-clock timeout per task, running on a **paid GitHub Actions plan** or equivalent private runner infrastructure to support **15 concurrent runners** (See US-1).
- **FR-003**: System MUST parse agent execution logs to classify failures into exactly four categories using the **Failure Hierarchy**: "Syntax Error" (highest), "Wrong Method Choice" (AttributeError/ModuleNotFoundError in valid code), "Data Mismatch" (valid code with relative error > 0.05), and "Timeout" (See US-1).
- **FR-004**: System MUST calculate the relative error gap ($g$) between the agent's numerical output and the ground-truth SOTA value for every successful or partial execution (See US-1).
- **FR-005**: System MUST apply a 1–5 scoring rubric to the method description of every task to generate an "abstraction distance" score, where the score is determined by the percentage of standard library calls: Score 1 (≥80%), Score 2 (50-79%), Score 3 (20-49%), Score 4 (1-19%), Score 5 (See US-2).
- **FR-006**: System MUST perform a **Spearman's Rank Correlation** test between the "abstraction distance" scores and the binary "Wrong Method Choice" failure outcome (0=No, 1=Yes), isolating this specific failure mode from others (See US-3).
- **FR-007**: System MUST calculate binomial proportion confidence intervals (Clopper-Pearson if cluster n < 30, Wilson if n ≥ 30) for the failure rates within each domain cluster; if any cluster has n < 10, the system MUST aggregate clusters into a 'Cross-Domain' group for the primary significance test (See US-3).
- **FR-008**: System MUST validate the automated rubric by calculating Krippendorff's Alpha on a 10% random subset of tasks rated by two independent domain experts; the system must only proceed if Alpha ≥ 0.7 (See US-2).

### Key Entities

- **Task**: A unit of work from NatureBench, containing `task_id`, `method_description` (text), `ground_truth_sota` (float), and `domain_cluster`.
- **ExecutionResult**: The outcome of an agent run on a Task, containing `agent_name`, `status` (Success/Timeout/Error), `failure_category` (if failed, respecting hierarchy), `numerical_output` (if generated), and `relative_error_gap`.
- **AbstractionScore**: The system-rated metric for a Task, containing `task_id`, `score` (1–5), `stdlib_percentage` (float), and `justification` (text).

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The Spearman's Rank Correlation coefficient ($\rho$) between "abstraction distance" and "Wrong Method Choice" failure outcome is measured against the null hypothesis ($\rho=0$) to determine statistical significance (See FR-006, US-3).
- **SC-002**: The binomial proportion confidence interval (Clopper-Pearson/Wilson) for "Wrong Method Choice" failure rates in each domain cluster (or Cross-Domain group) is measured against a standard 95% confidence level to validate the robustness of the cluster-specific findings (See FR-007, US-3).
- **SC-003**: The distribution of "abstraction distance" scores (1–5) across the 90 tasks is measured against the rubric criteria to ensure a sufficient variance exists to perform a meaningful correlation analysis (See FR-005, US-2).
- **SC-004**: The relative error gap ($g$) distribution for successful runs is measured against the ground-truth SOTA values to confirm the accuracy of the result parsing logic (See FR-004, US-1).
- **SC-005**: The total execution time for all 90 agent runs is measured against the **24-hour** total runtime budget (90 tasks / 15 concurrent runners * 4 hours) to confirm compute feasibility on the **paid GitHub Actions plan** (See FR-002, US-1).

## Assumptions

- The NatureBench dataset (a comprehensive suite of tasks) is available on HuggingFace and contains valid ground-truth SOTA numerical values for all tasks.; if a value is missing, the task is excluded from the correlation analysis.
- The "abstraction distance" can be reliably quantified by the defined 1–5 rubric based on standard library call frequency alone, without requiring the execution of the code to determine the difficulty of the method.
- The **paid GitHub Actions plan** (or private runners) is available to support 15 concurrent runners, ensuring the total 24-hour runtime budget is met; the free tier (1-2 concurrent jobs) is insufficient for this study design.
- The "Wrong Method Choice" failure category is distinct and identifiable in agent logs via `AttributeError` or `ModuleNotFoundError` in syntactically valid code, and does not overlap significantly with "Syntax Error" due to the defined Failure Hierarchy.
- The analysis runs entirely on CPU-only resources (a limited number of cores and memory) within the allocated paid compute budget, as the agents and statistical libraries used are CPU-tractable.
- The dataset variables (method description text, SOTA values) are sufficient for the analysis; no additional external data sources are required.
- The correlation analysis assumes that the "abstraction distance" score and the failure outcome are independent variables derived from separate processes (rubric application vs. agent execution).