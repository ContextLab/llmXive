# Feature Specification: llmXive follow-up: extending "Code as Agent Harness"

**Feature Branch**: `001-llmxive-harness-extension`  
**Created**: 2026-07-11  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'Code as Agent Harness' - Investigating correlation between code structural complexity and verification necessity to enable scalable, safe iteration on agent harnesses using CPU-only hardware."

## User Scenarios & Testing

### User Story 1 - Dataset Ingestion and Ground Truth Generation (Priority: P1)

The system MUST ingest the SWE-bench and AgentBench datasets, parse a representative set of agent tasks, and generate a ground-truth label for each task indicating whether a code modification requires dynamic re-execution based on full-environment execution results.

**Why this priority**: This is the foundational data layer. Without ground-truth labels (Pass/Fail from dynamic execution), no structural analysis or predictive modeling can be validated. It establishes the "truth" against which all static analysis claims are measured.

**Independent Test**: This story is testable by verifying that the pipeline successfully downloads the specified datasets, parses a substantial set of tasks, and produces a CSV containing `task_id`, `code_diff`, and `dynamic_execution_outcome` (Pass/Fail) for every record.

**Acceptance Scenarios**:
1. **Given** a valid HuggingFace token and network access, **When** the ingestion script runs, **Then** the system downloads SWE-bench and AgentBench subsets and extracts a substantial set of unique agent tasks with code artifacts and execution traces.
2. **Given** a parsed task with a code modification, **When** the baseline execution module runs, **Then** the system executes the code in the full environment and records a definitive "Pass" or "Fail" outcome as the ground truth.
3. **Given** a dataset of 500 tasks, **When** the ingestion completes, **Then** the output file contains zero missing values in the `dynamic_execution_outcome` column.

---

### User Story 2 - Structural Feature Extraction and Graph Construction (Priority: P2)

The system MUST convert extracted code artifacts into dependency graphs using `tree-sitter` and calculate specific structural metrics (semantic complexity, dependency depth, cyclomatic complexity) for every code modification.

**Why this priority**: This transforms raw code into the predictor variables required for the research question. It is the core "static analysis" component that determines if a lightweight check is sufficient.

**Independent Test**: This story is testable by verifying that for a known code snippet with a specific complexity, the system outputs the correct calculated metrics (e.g., cyclomatic complexity of 5) without needing to run the dynamic baseline.

**Acceptance Scenarios**:
1. **Given** a code modification snippet, **When** the `tree-sitter` parser processes it, **Then** the system generates a dependency graph capturing function calls and variable dependencies.
2. **Given** a parsed dependency graph, **When** the feature engineer module runs, **Then** it outputs a JSON object containing `dependency_depth`, `cyclomatic_complexity`, and `semantic_complexity_score` for that modification.
3. **Given** a batch of 500 tasks, **When** feature extraction completes, **Then** every task record has a corresponding feature vector with no missing metric values.

---

### User Story 3 - Predictive Modeling and Threshold Decision Boundary (Priority: P3)

The system MUST train a logistic regression or random forest model to predict the "need for dynamic execution" (defined operationally as observed failure in the baseline) based on structural features and determine the specific feature thresholds that minimize dynamic execution while maintaining a false-negative rate below [deferred].

**Why this priority**: This delivers the research outcome: the decision boundary model. It answers the core research question by defining *when* static analysis is safe.

**Independent Test**: This story is testable by running the trained model on a held-out validation set and verifying that the predicted "Need Dynamic" labels match the ground truth with the specified false-negative constraint.

**Acceptance Scenarios**:
1. **Given** a dataset of 500 tasks with features and ground truth, **When** the model training module runs, **Then** it fits a logistic regression or random forest model and outputs model weights/feature importance.
2. **Given** a trained model, **When** the threshold analysis runs, **Then** it identifies a specific cutoff value (e.g., `dependency_depth > 5`) that achieves the target false-negative rate.
3. **Given** the identified threshold, **When** applied to the validation set, **Then** the rate of static-approval failures (false negatives) is ≤ 0.1%, or if no threshold meets this target, the system reports the minimum achievable false-negative rate.

### Edge Cases

- **What happens when** a code artifact contains syntax errors preventing `tree-sitter` parsing?
  - The system MUST flag the task as "Unparseable" and exclude it from the structural analysis but retain it in the ground truth set for baseline comparison.
- **How does system handle** a task where dynamic execution times out (e.g., > 600 seconds) on the CPU runner?
  - The system MUST record the outcome as "Timeout/Fail" to maintain safety conservatism, rather than treating it as "Unknown."
- **What happens when** the dataset lacks specific variables required for the "semantic complexity" score?
  - The system MUST use a simplified metric set (dependency_depth, cyclomatic_complexity, lines_of_code) if the dataset lacks specific syntactic nodes required for the full 'semantic_complexity' score. This fallback ensures robustness against dataset variation while maintaining the core structural analysis goal. (See FR-002)

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and parse a representative set of agent tasks from SWE-bench and AgentBench datasets, extracting code artifacts and execution traces to establish ground truth. (See US-1)
- **FR-002**: System MUST convert code artifacts into dependency graphs using `tree-sitter` and calculate dependency depth, cyclomatic complexity, and semantic complexity scores for every modification. If semantic complexity is unavailable, the system MUST fall back to a simplified metric set (dependency_depth, cyclomatic_complexity, lines_of_code). (See US-2)
- **FR-003**: System MUST execute a full-environment re-execution baseline on all tasks to record Pass/Fail safety outcomes, ensuring no GPU or CUDA dependencies are used. (See US-1)
- **FR-004**: System MUST train a logistic regression or random forest model on CPU-only hardware to predict the necessity of dynamic re-execution (defined as observed baseline failure) based on extracted structural features. (See US-3)
- **FR-005**: System MUST perform a sensitivity analysis sweeping the decision threshold over values {0.01, 0.05, 0.1} to verify that the false-negative rate remains below ≤ 0.1% across the sweep. If no threshold meets this safety constraint, the system MUST report the minimum achievable false-negative rate and flag the model as "unsafe for static-only classification". (See US-3)
- **FR-006**: System MUST explicitly frame all reported correlations as ASSOCIATIONAL rather than causal, given the observational nature of the dataset (no random assignment of code complexity). (See US-3)

### Key Entities

- **TaskArtifact**: Represents a single agent task containing the code modification, the original code, and the execution environment context.
- **StructuralMetric**: Represents the calculated features (depth, complexity, etc.) derived from a specific `TaskArtifact`.
- **VerificationOutcome**: Represents the ground-truth result (Pass/Fail/Timeout) from the dynamic execution baseline.
- **DecisionBoundary**: Represents the specific threshold values derived from the model that separate "Static Only" from "Dynamic Required" classifications.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The false-negative rate of the static-analysis-only classification is measured against the full-environment re-execution baseline ground truth (where "false negative" is defined as a static approval of a task that fails the baseline). (See FR-005)
- **SC-002**: The reduction in dynamic execution cycles (percentage of tasks skipped) is measured against the total number of tasks in the dataset. (See FR-004)
- **SC-003**: The correlation coefficient between structural complexity features and the necessity of dynamic execution is measured against the logistic regression model weights. (See FR-004)
- **SC-004**: The computational feasibility (runtime and memory usage) is measured against the GitHub Actions free-tier constraints (≤6h, ~7GB RAM, CPU-only). (See FR-003)

## Assumptions

- The SWE-bench and AgentBench datasets provided via HuggingFace contain sufficient syntactic and execution trace data to compute `tree-sitter` dependency graphs and determine Pass/Fail outcomes.
- The "semantic complexity" metric can be approximated using standard static analysis tools (e.g., `radon`, `semgrep`) without requiring a large language model or GPU acceleration.
- The GitHub Actions free-tier runner is sufficient to execute a representative set of dynamic code tests sequentially or in small batches within the job time limit, provided the test environments are lightweight (e.g., Python virtual environments, no heavy Docker images).
- The correlation between code structure and verification necessity is observable in the existing datasets; if the data shows no correlation, the outcome is a valid null result.
- The [deferred] false-negative rate is a defensible community-standard safety threshold for agent verification, balancing safety with computational efficiency.
- The observational nature of the data (no random assignment of code complexity) precludes causal claims; findings will be strictly framed as associations.