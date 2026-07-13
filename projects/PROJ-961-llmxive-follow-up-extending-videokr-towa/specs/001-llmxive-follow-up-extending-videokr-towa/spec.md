# Feature Specification: llmXive follow-up: extending "VideoKR: Towards Knowledge- and Reasoning-Intensive Video Understandin"

**Feature Branch**: `001-video-reasoning-threshold`  
**Created**: 2026-07-13  
**Status**: Draft  
**Input**: User description: "Does the structural complexity of video QA questions, defined by the number of distinct entity hops required in the ground-truth knowledge graph, exhibit a non-linear threshold effect on the reasoning accuracy of models trained on knowledge-intensive video datasets?"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Structural Annotation (Priority: P1)

As a researcher, I need to download the VideoKR-SFT dataset and its associated knowledge graph, then programmatically annotate each question with its "structural chain length" (1-hop, 2-hop, 3+ hops) based strictly on the ground-truth graph structure, so that I can stratify the data by reasoning complexity before any model analysis.

**Why this priority**: This is the foundational step. Without accurate, non-circular structural labels derived from the ground truth, the subsequent analysis of the "reasoning cliff" cannot be performed. It isolates the predictor variable (complexity) from the outcome (accuracy).

**Independent Test**: The pipeline can be tested by running the annotation script on a small, manually verified subset of the dataset and confirming that the generated `chain_length` column matches manual graph-traversal counts for 50 randomly selected records.

**Acceptance Scenarios**:

1. **Given** the VideoKR-SFT dataset and knowledge graph are downloaded, **When** the annotation script processes the data, **Then** every question record is assigned a discrete integer or categorical label representing the number of hops required to reach the answer in the ground-truth graph.
2. **Given** a question with a known 3-hop path in the graph, **When** the script runs, **Then** the record is labeled as "3+ hops" (or equivalent) and the label is stored independently of any model prediction logs.
3. **Given** the dataset contains all records from the input dataset, **When** the full ingestion runs, **Then** the output file contains all records from the input dataset with no missing values in the `chain_length` field.

---

### User Story 2 - Accuracy Stratification and Threshold Detection (Priority: P2)

As a researcher, I need to calculate the model's binary correctness rate for each chain-length bin (1-hop, 2-hop, 3+ hops) and perform a statistical test (e.g., likelihood ratio test) to determine if the drop in accuracy between 2-hop and 3+ hops is statistically significant and non-linear, so that I can confirm the existence of a "reasoning cliff."

**Why this priority**: This addresses the core research question. It transforms the annotated data into the primary evidence for the hypothesis, distinguishing between linear degradation and a catastrophic failure point.

**Independent Test**: The analysis can be tested by generating a plot of accuracy vs. hop count and a statistical report; a human reviewer can verify the trend and the p-value of the non-linearity test against the raw data summary.

**Acceptance Scenarios**:

1. **Given** the annotated dataset with correctness labels, **When** the analysis script runs, **Then** it outputs a summary table showing the accuracy percentage for each hop-count bin (1, 2, 3+).
2. **Given** the stratified accuracies, **When** the statistical test is performed, **Then** the system reports whether a piecewise linear model (with a knot at the optimal hop count) fits the data significantly better than a standard linear model (p < 0.05).
3. **Given** the existence of a "cliff" hypothesis, **When** the analysis completes, **Then** the output explicitly quantifies the observed accuracy drop between bins and reports whether the drop exceeds a [deferred] absolute difference, quantifying the severity of the cliff.

---

### User Story 3 - Sensitivity Analysis of Threshold Definition (Priority: P3)

As a researcher, I need to re-run the threshold detection analysis by shifting the "cliff" definition to alternative boundaries (e.g., 2-hop vs. 3-hop, or 3-hop vs. 4-hop) and report how the statistical significance and effect size vary, so that I can justify the robustness of the identified threshold.

**Why this priority**: This ensures methodological soundness by preventing overfitting to a specific arbitrary cutoff (e.g., exactly 3 hops). It demonstrates that the "reasoning cliff" is a stable phenomenon, not an artifact of the chosen binning.

**Independent Test**: The sensitivity analysis can be tested by manually changing the threshold parameter in the config and verifying that the output report shows the variation in p-values and accuracy drops across the tested range.

**Acceptance Scenarios**:

1. **Given** the primary threshold is set at 3 hops, **When** the sensitivity analysis runs with offsets of ±1 hop, **Then** the system generates a table comparing the significance (p-value) and effect size (accuracy drop) for thresholds at 2, 3, and 4 hops.
2. **Given** the sensitivity results, **When** the report is generated, **Then** it explicitly states whether the "reasoning cliff" phenomenon remains statistically significant (p < 0.05) across the tested range of thresholds.
3. **Given** the analysis is complete, **When** the final report is rendered, **Then** it includes a plot overlaying the accuracy curves for the different threshold definitions to visualize the stability of the drop-off point.

---

### Edge Cases

- **What happens when the knowledge graph is disconnected?** The system must handle questions where the answer node is unreachable from the query entity (infinite hops or disconnected) by excluding them from the analysis or assigning a specific "unresolvable" label, ensuring they do not skew the accuracy metrics.
- **How does the system handle questions with multiple valid paths of different lengths?** The system must define a deterministic rule (e.g., "use the shortest path") for calculating the hop count to ensure a single, reproducible label per question.
- **What if the dataset size is insufficient for the 3+ hop bin?** If the multi-hop bin contains fewer than 50 examples (minimum n=50 required for asymptotic test validity), the system must flag this limitation in the output and potentially merge bins or defer the statistical test for that specific comparison.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST parse the ground-truth knowledge graph associated with the VideoKR-SFT dataset to calculate the shortest path length (number of hops) between the query entity and the answer entity for every question, explicitly ignoring model rationales. (See US-1)
- **FR-002**: The system MUST generate a structured output file (CSV/JSON) that maps each dataset record to its calculated structural chain length (1, 2, or 3+ hops) and its original binary correctness label. (See US-1)
- **FR-003**: The system MUST calculate the accuracy rate (correct predictions / total predictions) for each distinct chain-length bin (1-hop, 2-hop, 3+ hops). (See US-2)
- **FR-004**: The system MUST perform a grid-search change-point detection algorithm over hop counts 1-5 to identify the optimal knot location, comparing a linear model against a piecewise linear model at that location, and apply a Bonferroni correction for multiple comparisons to detect non-linear degradation. (See US-2)
- **FR-005**: The system MUST execute a sensitivity analysis sweeping the threshold definition across at least three values (e.g., 2, 3, and 4 hops) AND include a continuous plot of accuracy vs. exact hop count (without binning) to verify the robustness of the identified threshold. (See US-3)
- **FR-006**: The system MUST handle large datasets by processing the VideoKR-SFT data in chunks or sampling if necessary, ensuring the analysis completes within the 6-hour CI limit on a 2-core CPU runner. (See US-1, US-2)
- **FR-007**: The system MUST fit a Generalized Additive Model (GAM) with a smooth spline term for hop count to test for non-linearity in the continuous domain, ensuring the "cliff" is not an artifact of discrete binning. (See US-2)

### Key Entities

- **QuestionRecord**: Represents a single entry from the VideoKR-SFT dataset, containing the text query, the ground-truth answer, and the associated model prediction correctness label.
- **KnowledgeGraph**: The static graph structure where nodes are entities and edges represent relationships; used exclusively to derive the `chain_length` attribute.
- **AccuracyMetric**: A calculated value representing the ratio of correct predictions to total predictions for a specific subset of data (e.g., all 2-hop questions).
- **ThresholdResult**: A structured output containing the p-value, effect size, and direction of the relationship for a specific hypothesis test regarding the "reasoning cliff."

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The proportion of questions successfully annotated with a valid `chain_length` is measured against the total number of records in the VideoKR-SFT dataset (Target: [deferred] coverage (all input records must have a valid chain_length)). (See US-1)
- **SC-002**: The statistical significance (p-value) of the non-linear drop in accuracy between the 2-hop and 3+ hop bins is measured against the standard alpha level of 0.05 (p < 0.05) to confirm the "reasoning cliff" hypothesis. (See US-2)
- **SC-003**: The stability of the identified threshold is measured by the consistency of the p-value and effect size across the sensitivity analysis range (2, 3, and 4 hops); a result is considered robust if the significance holds (p < 0.05) in at least 2 of the 3 tested thresholds. (See US-3)
- **SC-004**: The total runtime of the end-to-end analysis (ingestion, annotation, modeling, and reporting) is measured against the GitHub Actions free-tier limit of 6 hours. (See US-1, US-2, US-3)
- **SC-005**: The memory footprint of the processing pipeline is measured against the 7 GB RAM constraint of the CI runner, ensuring no OOM errors occur during the full dataset load. (See US-1, US-2)

## Assumptions

- The VideoKR-SFT dataset and its associated ground-truth knowledge graph are publicly available and accessible via the official repository or arXiv supplementary materials without authentication barriers.
- The "structural chain length" can be unambiguously derived from the provided knowledge graph metadata; if the graph is incomplete or lacks necessary edges, the analysis will be limited to the subset of questions with fully connected paths.
- The model correctness labels provided in the evaluation logs are accurate and representative of the model's performance on the specific questions; no re-evaluation of the model outputs is performed.
- The dataset size and the complexity of the graph traversal operations fit within the ~7 GB RAM and ~14 GB disk constraints of the free-tier GitHub Actions runner when processed with standard Python libraries (pandas, networkx).
- The "reasoning cliff" phenomenon, if it exists, is distinct enough to be detected with the available sample size in the 3+ hop bin; if the 3+ hop bin is too small (< 50 samples), the statistical power will be noted as a limitation in the final report.
- The analysis assumes that the "chain length" metric is the primary driver of difficulty; other factors (e.g., video length, visual complexity) are treated as noise or controlled for via the statistical model's intercept, but are not explicitly modeled in this scope.