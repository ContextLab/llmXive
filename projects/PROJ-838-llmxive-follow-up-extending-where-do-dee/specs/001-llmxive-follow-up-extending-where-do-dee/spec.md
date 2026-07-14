# Feature Specification: llmXive follow-up: extending "Where Do Deep-Research Agents Go Wrong? Span-Level Error Localization "

**Feature Branch**: `001-gene-regulation`  
**Created**: 2026-07-12  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'Where Do Deep-Research Agents Go Wrong? Span-Level Error Localization '"

## User Scenarios & Testing

### User Story 1 - Extract Topological Metrics from Early Trajectory Spans (Priority: P1)

As a researcher analyzing agent failure modes, I need the system to parse the first [deferred] of a deep-research trajectory from the TELBench dataset and construct a directed acyclic graph (DAG) of claim dependencies using only textual co-reference and citation logic, so that I can quantify the structural integrity of the reasoning process before the final outcome is known.

**Why this priority**: This is the foundational data transformation step. Without accurate graph construction from the early spans (independent of error labels), no topological metrics can be calculated, rendering the predictive study impossible.

**Independent Test**: The pipeline can be tested by running it on a single trajectory file, verifying the generated graph nodes match the first [deferred] of claims, and confirming the edge count matches manual inspection of co-reference links, without needing the final success/failure label.

**Acceptance Scenarios**:

1. **Given** a JSON trajectory file from TELBench containing 100 semantic spans, **When** the parser processes the file with a `cutoff_depth=0.30` parameter, **Then** the output DAG contains exactly the nodes corresponding to the first 30 spans and edges derived solely from textual co-reference/citation within that subset.
2. **Given** a trajectory where the first [deferred] of spans contain no explicit citations or co-references, **When** the parser processes the file, **Then** the resulting DAG has zero edges but retains the correct node count for that subset.
3. **Given** a trajectory with malformed JSON or missing span text, **When** the parser encounters the error, **Then** the system logs a warning and skips that specific trajectory without crashing the entire batch process.

---

### User Story 2 - Calculate Connectivity and Branching Metrics (Priority: P2)

As a researcher, I need the system to compute the Average Branching Factor (out-degree) and Global Connectivity (edge-to-possible-edge ratio) for each processed early-stage graph, normalized by the number of nodes, so that I can generate a structured dataset of topological features for statistical analysis that distinguishes structural density from text volume.

**Why this priority**: This transforms the raw graph data into the specific quantitative variables (predictors) required to test the hypothesis. It must be deterministic, reproducible, and normalized to avoid conflating graph size with structural integrity.

**Independent Test**: The calculation module can be tested by feeding it a known small graph (e.g., 3 nodes, 2 edges) and verifying the output metrics match the mathematically derived values (Branching Factor = 2/3, Connectivity = 2/6) exactly, ensuring normalization is applied.

**Acceptance Scenarios**:

1. **Given** a DAG with 10 nodes and 5 edges, **When** the metric calculator runs, **Then** it outputs an Average Branching Factor of 0.5 and a Global Connectivity of 0.05 (5/90), normalized by node count.
2. **Given** a DAG where a single node has 0 outgoing edges, **When** the metric calculator runs, **Then** the Average Branching Factor is calculated as the sum of out-degrees divided by the total node count (including the zero-degree node).
3. **Given** a batch of 100 trajectories, **When** the calculator processes them, **Then** it outputs a CSV/JSON file containing one row per trajectory with columns for `trajectory_id`, `avg_branching_factor`, and `global_connectivity`.

---

### User Story 3 - Predict Collapse and Validate Against Ground Truth (Priority: P3)

As a researcher, I need the system to apply a data-driven threshold (the 20th percentile of the connectivity/branching distribution of trajectories labeled as "success" in the training split) to the calculated metrics to predict "collapse" and compare these predictions against the ground-truth final trajectory labels, so that I can quantify the precision and recall of the topological predictor.

**Why this priority**: This completes the research loop by testing the hypothesis. It validates whether the structural signatures actually correlate with failure, providing the final empirical result.

**Independent Test**: The validation module can be tested by providing a synthetic dataset with known labels and metrics, verifying that the confusion matrix (Precision, Recall, F1) matches the expected values based on the applied threshold.

**Acceptance Scenarios**:

1. **Given** a dataset of the full TELBench dataset (approx. [deferred] trajectories) where 200 are known failures and the threshold is set to the 20th percentile of success-connectivity (calculated from the training split), **When** the predictor runs, **Then** it correctly flags trajectories below the threshold as "predicted failure" and outputs a confusion matrix.
2. **Given** a trajectory where the early-stage connectivity is above the threshold but the final outcome is failure, **When** the system evaluates it, **Then** it records a "False Positive" (predicts success, actual failure) in the metrics.
3. **Given** the full TELBench dataset, **When** the analysis completes, **Then** the system outputs a summary report including Precision, Recall, F1-score, and the specific threshold values used.

### Edge Cases

- What happens when a trajectory is shorter than [deferred] of the trajectory depth (e.g., only 5 spans total)? The system must handle this by using the entire trajectory as the "early stage" rather than failing or returning nulls.
- How does the system handle trajectories with zero edges in the early stage? The connectivity metric must be defined as 0.0, not NaN, to ensure the threshold comparison works correctly.
- What if the TELBench dataset format changes slightly (e.g., field names for spans)? The parser must fail gracefully with a clear error message indicating the specific missing field rather than a generic traceback.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST parse the TELBench JSON dataset to extract semantic spans and filter them to the first [deferred] of the trajectory depth for graph construction (See US-1).
- **FR-002**: The system MUST construct a directed acyclic graph (DAG) where edges are inferred solely from textual co-reference and citation logic within the filtered subset, explicitly excluding any pre-labeled error annotations (See US-1).
- **FR-003**: The system MUST calculate the Average Branching Factor (sum of out-degrees divided by node count) and Global Connectivity (ratio of existing edges to possible edges) for each trajectory's early-stage subgraph, ensuring metrics are normalized by node count to distinguish structural density from text volume (See US-2).
- **FR-004**: The system MUST determine a prediction threshold based on the 20th percentile of the connectivity/branching distribution of trajectories labeled as "success" in the training split (See US-3).
- **FR-005**: The system MUST compare predicted collapse outcomes against the ground-truth final trajectory labels to generate a confusion matrix and calculate Precision, Recall, and F1-score (See US-3).
- **FR-006**: The system MUST execute the entire pipeline (parsing, graph construction, metric calculation, and validation) on a CPU-only environment without requiring GPU acceleration or CUDA libraries (See Assumptions).
- **FR-007**: The system MUST calculate and report the mean connectivity of the "success" class to establish a baseline for the "low connectivity" hypothesis before applying the prediction threshold (See US-3).
- **FR-008**: The system MUST test for the presence of linear reasoning patterns (low branching, low connectivity) in the "success" class to rule out the misclassification of valid linear reasoning as "collapse" (See US-3).

### Key Entities

- **Trajectory**: A single agent reasoning path from TELBench, consisting of an ordered list of semantic spans and a final success/failure label.
- **Claim-Dependency Graph**: A directed acyclic graph where nodes represent semantic claims and edges represent dependency relations inferred from text.
- **Topological Metrics**: The quantitative features (Branching Factor, Connectivity) derived from the graph structure, normalized by node count.
- **Prediction Label**: The binary outcome (Collapse/No Collapse) generated by applying the threshold to the topological metrics.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The prediction precision for trajectory collapse is measured against the ground-truth final outcome labels provided in the TELBench dataset (See FR-005).
- **SC-002**: The correlation between early-stage topological connectivity and final trajectory collapse is measured against the statistical significance threshold (p < 0.05) derived from the dataset (See FR-005).
- **SC-003**: The computational efficiency of the graph construction and metric calculation is measured against the constraint of completing 100 trajectories within 30 minutes on a standard CPU (See FR-006).
- **SC-004**: The robustness of the predictor is measured by the stability of the F1-score across a sensitivity analysis where the decision threshold is swept over the set {0.01, 0.05, 0.1} and the percentile cutoff is varied (e.g., 10th, 20th, 30th) (See FR-004).

## Assumptions

- **Assumption about data availability**: The TELBench dataset (a collection of annotated trajectories) is publicly accessible and the JSON/CSV format remains stable for the duration of the project.
- **Assumption about compute environment**: The analysis will run on a GitHub Actions free-tier runner (limited CPU cores, ~7 GB RAM, no GPU), requiring all graph algorithms to be implemented using standard Python libraries (e.g., `networkx`, `pandas`) without heavy deep learning frameworks.
- **Assumption about threshold justification**: The 20th percentile is chosen as the initial data-driven threshold based on community standards for anomaly detection in sparse graphs; a sensitivity analysis (SC-004) will be performed to validate this choice.
- **Assumption about dataset-variable fit**: The TELBench dataset contains sufficient textual context within the first [deferred] of spans to infer co-reference and citation edges; if a trajectory lacks these early, the system assumes a "sparse" topology by default.
- **Assumption about inference framing**: Since the study uses observational data (no random assignment of topological structures), all conclusions regarding the relationship between topology and collapse will be framed as associational, not causal.
- **Assumption about hypothesis validity**: The study is exploratory; it does not assume "low connectivity" is a universal precursor to collapse but seeks to empirically determine if such a correlation exists distinct from valid linear reasoning patterns (See FR-008).