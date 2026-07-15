# Feature Specification: llmXive follow-up: extending "Memory is Reconstructed, Not Retrieved: Graph Memory for LLM Agents"

**Feature Branch**: `001-llmxive-memory-optimization`  
**Created**: 2026-07-13  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'Memory is Reconstructed, Not Retrieved: Graph Memory for LLM Agents'"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Baseline Active Reconstruction Execution (Priority: P1)

The system MUST successfully execute the "Full" active reconstruction strategy on the LoCoMo benchmark tasks using a CPU-only environment, establishing a ground-truth baseline for accuracy, latency, and node visitation counts.

**Why this priority**: This is the foundational control condition. Without a verified, reproducible baseline of the MRAgent framework's performance, any comparison with heuristic strategies (Lazy/Greedy) is scientifically invalid. This story delivers the reference point for all subsequent analysis.

**Independent Test**: The system runs the baseline algorithm on a fixed subset of LoCoMo tasks and outputs a CSV containing `task_id`, `accuracy`, `nodes_visited`, and `inference_time_seconds` without requiring the heuristic implementations to be present.

**Acceptance Scenarios**:

1. **Given** a configured CPU-only Python environment and the LoCoMo benchmark dataset, **When** the baseline active reconstruction script is executed, **Then** the system completes all tasks (or logs a timeout if >30 minutes) and outputs a results file where every task has a recorded accuracy (0.0–1.0) and a recorded latency value in seconds.
2. **Given** a noisy synthetic graph dataset, **When** the baseline script is run, **Then** the system correctly processes the graph structure without crashing and reports a non-zero node visitation count for every task.

---

### User Story 2 - Heuristic Strategy Comparison (Priority: P2)

The system MUST execute the "Greedy" and "Lazy" traversal strategies on the same benchmark tasks as the baseline, logging comparative metrics to determine if reduced-depth strategies preserve reasoning accuracy while lowering computational cost.

**Why this priority**: This delivers the core research value: quantifying the trade-off between efficiency (nodes visited/latency) and effectiveness (accuracy). It directly answers the research question regarding the functional relationship between `nodes_visited` and reasoning stability.

**Independent Test**: The system runs the two heuristic implementations on the benchmark and generates a comparison report showing the accuracy delta and efficiency gain relative to the P1 baseline.

**Acceptance Scenarios**:

1. **Given** the baseline results from P1 and the configured "Lazy" heuristic parameters, **When** the system executes the Lazy strategy, **Then** it outputs a results file containing the node count and accuracy for each task.
2. **Given** the same tasks and baseline results, **When** the system executes the "Greedy" strategy, **Then** it outputs a results file containing the accuracy delta relative to the baseline, allowing the hypothesis (accuracy within 2% of baseline) to be tested.

---

### User Story 3 - Statistical Significance and Threshold Analysis (Priority: P3)

The system MUST perform statistical hypothesis testing (paired t-test or Wilcoxon) on the accuracy distributions of the heuristic methods versus the baseline and report the correlation between `nodes_visited` and success rate using Point-Biserial correlation.

**Why this priority**: This transforms raw data into scientific evidence. It validates whether observed differences are statistically significant or due to random noise, and identifies the specific `nodes_visited` threshold where heuristic strategies fail.

**Independent Test**: The system ingests the results CSVs from P1 and P2 and generates a statistical report containing p-values, confidence intervals, Point-Biserial correlation coefficients, and the calculated inflection point bin.

**Acceptance Scenarios**:

1. **Given** the paired accuracy results from the Baseline and Lazy strategies, **When** the statistical analysis script is run, **Then** it outputs a p-value for the paired t-test (or Wilcoxon) and the test statistic (t or W).
2. **Given** the full dataset of `nodes_visited` and `success` flags, **When** the correlation analysis is run, **Then** the system reports a Point-Biserial correlation coefficient and identifies the specific `nodes_visited` threshold where accuracy drops below 95% of the baseline IF the trend is statistically significant (p < 0.05). The system MUST determine this threshold by binning tasks by `nodes_visited` count into bins such that each bin contains at least 3 tasks (n ≥ 3), and finding the first bin with a mean accuracy < 95% of the baseline; otherwise, it reports the overall trend without asserting a specific threshold.

---

### User Story 4 - System Robustness and Error Handling (Priority: P1)

The system MUST handle edge cases such as disconnected graphs, timeouts, and degenerate inputs gracefully, ensuring the experiment pipeline does not crash and logs all errors for post-hoc analysis.

**Why this priority**: Research pipelines must be robust to ensure data integrity. If a single task causes a crash, the entire experiment is invalidated. This story ensures the system captures all data points or explicitly logs failures.

**Independent Test**: The system is run against a dataset containing known edge cases (disconnected graphs, zero-edge graphs) and tasks designed to exceed the timeout limit.

**Acceptance Scenarios**:

1. **Given** a task where the target node is unreachable in the "Lazy" strategy, **When** the system executes, **Then** it defaults to a full traversal or flags the task as "unresolved" in the results file without crashing.
2. **Given** a task that exceeds the 30-minute per-task limit, **When** the system executes, **Then** it terminates the task, logs a "TIMEOUT" status, and proceeds to the next task without hanging the entire job.
3. **Given** a degenerate graph (zero edges or single node), **When** the system executes, **Then** it handles the case without division-by-zero errors and reports the result (or a specific "degenerate" flag).

---

### Edge Cases

- **What happens when the graph is disconnected?** The system must handle cases where the target node is unreachable in the "Lazy" strategy by defaulting to a full traversal or flagging the task as "unresolved" rather than crashing.
- **How does the system handle timeout limits?** If a specific task exceeds the 30-minute per-task limit (enforced by FR-007), the system must log a timeout error and skip the task rather than hanging the entire CI job. The total job limit is set to a reasonable duration appropriate for the study's scope.
- **What happens with degenerate graphs?** If the synthetic noisy dataset contains graphs with zero edges or single nodes, the system must handle these without division-by-zero errors in the traversal logic.
- **How is noise injected?** The synthetic noisy graph dataset MUST be generated by injecting random edges at a fixed density, adding a proportion of random edges to the original graph (i.e., if the original graph has E edges, a fraction of random edges are added). This ensures the robustness test is reproducible and neither trivial nor destructive.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download and parse the LoCoMo benchmark subset and generate the associated synthetic noisy graph dataset from public repositories without manual intervention. The synthetic noisy graph dataset MUST be generated by injecting noise such that a small, reproducible proportion of the edges in the graph are replaced with random edges to ensure reproducibility and valid stress testing. (See US-1)
- **FR-002**: System MUST implement a "Full" active reconstruction algorithm that traverses the entire relevant subgraph for each query, logging nodes visited and execution time. (See US-1)
- **FR-003**: System MUST implement a "Lazy" traversal heuristic that defers edge expansion until an evidence threshold is triggered, logging the reduced node count and the specific evidence threshold value used for that run (e.g., confidence score > 0.7) in the execution log. (See US-2)
- **FR-004**: System MUST implement a "Greedy" traversal heuristic that selects only the top-k confidence edges, logging the reduced node count and accuracy. (See US-2)
- **FR-005**: System MUST perform a paired statistical test (t-test or Wilcoxon) comparing the accuracy distributions of the heuristic strategies against the baseline and output the p-value and test statistic. (See US-3)
- **FR-006**: System MUST calculate the Point-Biserial correlation coefficient between `nodes_visited` and reasoning success rate across all tasks. (See US-3)
- **FR-007**: System MUST enforce a hard timeout of 30 minutes per individual task (measured from start to finish) to prevent CI job exhaustion. Upon timeout, the system MUST log the event and proceed to the next task. (See US-4)

### Key Entities

- **Task**: A multi-hop reasoning query containing a question, context, and ground-truth answer.
- **Memory Graph**: A directed graph structure representing the agent's retrieved knowledge, where nodes are facts and edges are relationships.
- **Traversal Strategy**: An algorithmic policy (Full, Lazy, Greedy) determining which edges to explore during memory reconstruction.
- **Execution Log**: A structured record containing `task_id`, `strategy`, `accuracy`, `nodes_visited`, `latency_ms`, and `evidence_threshold` (for heuristic strategies).

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The reduction in nodes visited by the "Lazy" and "Greedy" strategies is measured against the "Full" baseline node count, and the system MUST report the percentage reduction. (See US-2)
- **SC-002**: The accuracy of the heuristic strategies is measured against the baseline accuracy, and the system MUST report the accuracy delta (heuristic - baseline). (See US-2)
- **SC-003**: The statistical significance of the accuracy difference is measured, and the system MUST output the p-value and the test statistic (t or W) for the paired comparison. (See US-3)
- **SC-004**: The correlation between `nodes_visited` and reasoning stability is measured, and the system MUST report the Point-Biserial correlation coefficient and the inflection point IF statistically significant. The inflection point MUST be estimated by binning tasks by `nodes_visited` count into bins such that each bin contains at least 3 tasks (n ≥ 3) and identifying the first bin with a mean accuracy < 95% of the baseline. (See US-3)
- **SC-005**: The total inference latency per task is measured against the 30-minute timeout constraint, and the system MUST report the count of tasks that timed out versus completed. (See US-4)

## Assumptions

- **Assumption about compute constraints**: The analysis assumes the use of a quantized small-to-medium parameter LLM (e.g., via `llama.cpp`) running in default precision on a CPU-only environment, as the project must run within GitHub Actions free-tier limits (limited CPU resources, constrained RAM, no GPU).
- **Assumption about data availability**: It is assumed that the LoCoMo benchmark subset and the synthetic noisy graph dataset are publicly accessible via HuggingFace or the MRAgent GitHub repository and do not require authentication or proprietary access. The synthetic noisy graph dataset generation method is defined and reproducible (see FR-001).
- **Assumption about inference framing**: Since the study is observational (comparing algorithmic strategies on a fixed dataset without random assignment of agents), all findings regarding the relationship between `nodes_visited` and accuracy will be framed as associational, not causal.
- **Assumption about threshold justification**: The "evidence threshold" for the Lazy heuristic will be set to a community-standard default (e.g., confidence score > 0.7) and will be subject to a sensitivity analysis sweeping values {0.5, 0.7, 0.9} to ensure robustness, as required by the methodology panel.
- **Assumption about measurement validity**: The LoCoMo benchmark answers are treated as the ground truth for accuracy measurement. However, it is acknowledged that the benchmark may contain hallucinated or ambiguous ground truths; therefore, the "accuracy" metric is interpreted as "alignment with the benchmark's provided answers" rather than absolute reasoning stability. No additional validation of the benchmark's own validity is performed within this scope.
- **Assumption about power and multiplicity**: Given the fixed size of the LoCoMo benchmark subset, the study acknowledges a potential power limitation; a post-hoc power analysis will be included in the final report, but the sample size is treated as fixed and not adjustable.
- **Assumption about research hypothesis**: The research hypothesis posits that heuristic strategies will achieve a substantial reduction in node visits. while maintaining accuracy within 2% of the baseline. This is a hypothesis to be tested by the data, not a system requirement to be enforced.
- **Assumption about noise injection**: The synthetic noisy graph dataset MUST be generated by injecting random edges at a low, controlled density relative to the total edge count (i.e., if the original graph has E edges, a small fraction of random edges are added). This ensures the robustness test is reproducible and statistically valid.