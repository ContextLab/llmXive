# Feature Specification: llmXive follow-up: extending "Intern-Atlas: A Methodological Evolution Graph as Research Infrastruct"

**Feature Branch**: `001-methodological-evolution-fragility`  
**Created**: 2026-07-06  
**Status**: Draft  
**Input**: User description: "Does the topological structure of methodological evolution graphs—specifically the ratio of 'bottleneck-resolving' edges to 'incremental-variant' edges within a local neighborhood—predict the long-term reproducibility or stability of a methodological lineage, independent of its initial citation volume?"

## User Scenarios & Testing

### User Story 1 - Data Extraction and Feature Engineering (Priority: P1)

**Journey**: The system ingests the Intern-Atlas graph snapshot and external retraction/replication databases to compute topological features (Bottleneck Resolution Ratio, Branching Entropy) for every method node published between 2010 and 2018, resulting in a structured dataset ready for modeling.

**Why this priority**: Without a clean, labeled dataset derived from the graph and external truth sources, no analysis or prediction is possible. This is the foundational data pipeline.

**Independent Test**: The pipeline can be tested by running the extraction script on a small subset of the graph and verifying that the output CSV contains the computed features and the correct binary labels (Fragile/Robust) for a known set of papers.

**Acceptance Scenarios**:

1. **Given** the Intern-Atlas graph snapshot and the Retraction Watch Database, **When** the extraction script runs, **Then** the output dataset contains exactly one row per method node published between 2010-2018 with computed `bottleneck_resolution_ratio`, `branching_entropy`, and `retraction_status` fields.
2. **Given** a method node with no outgoing edges, **When** the feature calculation runs, **Then** the `bottleneck_resolution_ratio` is recorded as 0.0 and the `branching_entropy` as 0.0, without causing a runtime error.
3. **Given** a method node that matches a paper in the Retraction Watch Database, **When** the label mapping runs, **Then** the `retraction_status` field is set to `1` (Fragile) if the retraction reason is methodological error/irreproducibility, or `2` (Retraction-Only) if due to fraud/plagiarism, and `0` (Robust) otherwise, regardless of citation count.

---

### User Story 2 - Model Training and Validation (Priority: P2)

**Journey**: The system trains a lightweight logistic regression model to predict "Fragile" vs "Robust" labels using only the topological features, and validates its performance against a baseline model using only citation counts.

**Why this priority**: This delivers the core research insight: whether topology predicts stability better than citations. It is the primary analytical engine.

**Independent Test**: The training script can be run in isolation with a fixed random seed; the output report must show the AUC-ROC and Precision-Recall scores for both the topological model and the citation baseline.

**Acceptance Scenarios**:

1. **Given** the prepared dataset split into training and validation sets, **When** the logistic regression model trains, **Then** the model converges within 1000 iterations and outputs coefficients for `bottleneck_resolution_ratio` and `branching_entropy`.
2. **Given** the trained topological model and the validation set, **When** the evaluation runs, **Then** the AUC-ROC score is calculated and reported, and the Precision-Recall curve is generated.
3. **Given** the baseline model (citation count only) and the topological model, **When** the comparison runs, **Then** the system outputs a delta metric showing the improvement (or degradation) in AUC-ROC provided by the topological features.

---

### User Story 3 - Robustness and Sensitivity Analysis (Priority: P3)

**Journey**: The system performs permutation tests to ensure the predictive power is not an artifact of graph density, and sweeps the classification threshold to assess sensitivity to decision boundaries.

**Why this priority**: This addresses methodological soundness (multiplicity, threshold justification) and ensures the findings are not spurious, which is critical for scientific validity.

**Independent Test**: The robustness script can be run to generate a distribution of AUC scores from permuted labels; the result must show that the observed AUC is significantly higher than the permuted distribution mean.

**Acceptance Scenarios**:

1. **Given** the trained model and the validation set, **When** the permutation test runs (shuffling labels 100 times), **Then** the observed AUC-ROC is > mean_permuted_AUC + 2 * std_dev of the permuted models.
2. **Given** the model's predicted probabilities, **When** the threshold sweep runs over cutoffs {0.3, 0.5, 0.7}, **Then** the system reports the False Positive Rate and False Negative Rate for each cutoff, demonstrating how performance varies with the decision boundary.
3. **Given** the dataset, **When** the collinearity diagnostic runs, **Then** the Variance Inflation Factor (VIF) and Mutual Information (MI) are calculated for `bottleneck_resolution_ratio` and `branching_entropy`, and the model is flagged as potentially unstable if VIF > 5 or MI > 0.1.

---

### Edge Cases

- **What happens when** a paper in the Intern-Atlas graph matches multiple entries in the Retraction Watch Database?
  - **Handling**: The system MUST select the earliest match by publication date. If multiple entries share the same date, the system MUST select the first entry alphabetically by journal name.
- **How does the system handle** nodes with missing `outgoing_edge_type` data (e.g., untyped edges)?
  - **Handling**: Untyped edges must be excluded from the `bottleneck_resolution_ratio` denominator, or the node must be dropped from the analysis with a log entry.
- **What happens when** the external retraction database has no entries for the 2010-2018 window?
  - **Handling**: The system must abort with a clear error message: "No ground truth labels found for the specified time window; analysis cannot proceed."

## Requirements

### Functional Requirements

- **FR-001**: System MUST extract the Intern-Atlas graph and filter nodes to those published between 2010-01-01 and 2018-12-31 (See US-1).
- **FR-002**: System MUST compute `bottleneck_resolution_ratio` as the count of outgoing `improves`/`replaces` edges divided by total outgoing edges. Edge types MUST be derived from human-annotated metadata or a validated ontology; LLM-inferred edge types MUST be excluded to prevent semantic leakage (See US-1).
- **FR-003**: System MUST compute `branching_entropy` as the Shannon entropy of the distribution of downstream method types (See US-1).
- **FR-004**: System MUST map nodes to external retraction/replication databases to assign a label: `1` (Fragile) if retraction is due to methodological error or irreproducibility, `2` (Retraction-Only) if due to fraud/plagiarism, and `0` (Robust) otherwise (See US-1).
- **FR-005**: System MUST train a logistic regression model using only topological features to predict `retraction_status` (See US-2).
- **FR-006**: System MUST train a baseline logistic regression model using only `citation_count` and `publication_year` to predict `retraction_status` (See US-2).
- **FR-007**: System MUST perform a permutation test (n=100) by shuffling labels to verify that the topological model's AUC is > mean_permuted_AUC + 2 * std_dev of the permuted models (See US-3).
- **FR-008**: System MUST perform a threshold sensitivity analysis by sweeping classification cutoffs at {0.3, 0.5, 0.7} and reporting FPR/FNR for each (See US-3).
- **FR-009**: System MUST calculate Variance Inflation Factor (VIF) and Mutual Information (MI) for the topological predictors; the system MUST flag the model as potentially unstable in the output report if VIF > 5 or MI > 0.1 (See US-3).
- **FR-010**: System MUST resolve duplicate matches in external databases by selecting the earliest match by publication date; if dates are identical, select the first entry alphabetically by journal name (See Edge Cases).
- **FR-011**: System MUST match nodes to external databases using an exact DOI match; if no DOI match is found, the system MUST use a fuzzy title/author match with a Levenshtein ratio threshold of >= 0.85 (See FR-004).
- **FR-012**: System MUST perform a stratified permutation test or covariate adjustment for 'field of study' and 'publication venue' to control for confounding variables (See US-3).

### Key Entities

- **MethodNode**: A node in the Intern-Atlas graph representing a specific research method, with attributes: `paper_id`, `title`, `year`, `outgoing_edges` (list of edge types), `incoming_citations`.
- **RetractionLabel**: An external truth label mapped to a MethodNode, with attributes: `paper_id`, `status` (Fragile/Robust/Retraction-Only), `source` (Retraction Watch/Replication Index), `retraction_reason`.
- **TopologicalFeatures**: A derived record for each MethodNode, with attributes: `bottleneck_resolution_ratio`, `branching_entropy`, `citation_count`.
- **ModelResult**: A record storing the performance metrics of a trained model, with attributes: `model_type`, `auc_roc`, `precision`, `recall`, `f1_score`, `stability_flag`.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The AUC-ROC of the topological model is measured against the AUC-ROC of the citation-baseline model to determine if topology provides independent predictive power (See FR-006, US-2).
- **SC-002**: The False Positive Rate and False Negative Rate are measured across the threshold sweep {0.3, 0.5, 0.7} to assess the stability of the decision boundary (See FR-008, US-3).
- **SC-003**: The mean AUC of the permutation test (n=100) is measured against the observed AUC of the trained model to verify statistical significance (See FR-007, US-3).
- **SC-004**: The Variance Inflation Factor (VIF) and Mutual Information (MI) for `bottleneck_resolution_ratio` and `branching_entropy` are measured to ensure predictors are not definitionally collinear (See FR-009, US-3).

## Assumptions

- The Intern-Atlas graph snapshot contains typed edges (e.g., `improves`, `extends`, `replaces`) for at least 80% of the nodes published between 2010 and 2018.
- The edge types in the Intern-Atlas graph are derived from human-annotated metadata or a validated ontology, not from LLM inference on paper text, to prevent semantic leakage with the retraction label.
- The Retraction Watch Database and Replication Index contain sufficient records for papers published between 2010 and 2018 to create a balanced or near-balanced dataset for binary classification.
- The "Bottleneck Resolution Ratio" and "Branching Entropy" are computable within the ~7 GB RAM limit of the CI runner using standard Python libraries (networkx, numpy) without requiring GPU acceleration.
- The relationship between graph topology and retraction status is associational, not causal, given the observational nature of the data (no random assignment of research methods).
- The dataset fits within the disk limit of the CI runner; if the graph is larger, a random sample of [deferred] nodes will be used for the analysis.
- The classification threshold of 0.5 is used as the default, with sensitivity analysis performed to justify any deviation (as per FR-008).