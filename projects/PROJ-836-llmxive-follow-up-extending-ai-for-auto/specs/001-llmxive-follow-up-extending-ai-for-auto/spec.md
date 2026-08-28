# Feature Specification: llmXive follow-up: extending "AI for Auto-Research: Roadmap & User Guide"

**Feature Branch**: `001-llmxive-followup`  
**Created**: 2026-07-10  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'AI for Auto-Research: Roadmap & User Guide'"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Graph Construction and Metric Extraction (Priority: P1)

The system must ingest the "Creation" phase logs from the "AI for Auto-Research" benchmark, parse the literature review sections to extract entity-relation triplets, and compute topological metrics (cycle density, citation isolation, semantic distance) for each idea.

**Why this priority**: This is the foundational step; without the structural features extracted from the text, no predictive analysis can occur. It delivers the core dataset required for all subsequent modeling.

**Independent Test**: Can be fully tested by running the extraction pipeline on a known subset of the benchmark data and verifying that the output CSV contains the correct columns (cycle density, isolation score, semantic distance) and that the values are non-null and within expected mathematical bounds for the given graph sizes.

**Acceptance Scenarios**:

1. **Given** a literature review text from the benchmark dataset, **When** the NLP parser processes it, **Then** a directed graph is constructed containing nodes for concepts and edges for claims.
2. **Given** a constructed graph, **When** the metric engine calculates cycle density, **Then** the output is a float between 0.0 and 1.0 representing the ratio of actual cycles to maximum possible cycles.
3. **Given** a graph with disconnected components, **When** the isolation metric is calculated, **Then** nodes with zero incoming edges from external sources are correctly identified and scored.
4. **Given** a literature review text that is empty or too short to form a graph, **When** the metric engine processes it, **Then** the system assigns default metric values of 0.0 and logs a warning.

---

### User Story 2 - Predictive Model Training and Evaluation (Priority: P2)

The system must train an interpretable classifier (Logistic Regression) using the extracted topological metrics as predictors and the ground-truth experimental failure labels as the target, evaluating performance via 5-fold cross-validation.

**Why this priority**: This step determines if the structural anomalies actually predict failure. It validates the core hypothesis and provides the primary performance metric (AUC) required for the research conclusion.

**Independent Test**: Can be fully tested by training the model on the processed dataset and verifying that the cross-validation AUC score is calculated and reported, and that the model coefficients are non-zero for at least one topological metric (if the hypothesis holds) or that the model reports a null result (if the hypothesis is false).

**Acceptance Scenarios**:

1. **Given** the feature matrix of topological metrics and the label vector, **When** the model training process runs, **Then** a trained Logistic Regression model object is produced without runtime errors related to dimension mismatch or memory overflow.
2. **Given** a trained model, **When** 5-fold cross-validation is executed, **Then** an Area Under the Curve (AUC) score is reported with a standard deviation across folds.
3. **Given** the model output, **When** feature importance (coefficients) is inspected, **Then** the system reports the magnitude of each coefficient, allowing verification of whether any metric has a magnitude ≥ 0.05.

---

### User Story 3 - Statistical Significance Verification (Priority: P3)

The system must perform a permutation test to verify that the observed correlation between graph metrics and failure labels is not due to chance, ensuring the validation target is independent of the graph construction process.

**Why this priority**: This addresses the methodological requirement for inference framing. It confirms that the predictive power is genuine and not an artifact of the data generation process, strengthening the scientific validity of the results.

**Independent Test**: Can be fully tested by running the permutation test on the final model results and verifying that a p-value is calculated and reported, indicating whether the null hypothesis (random correlation) can be rejected.

**Acceptance Scenarios**:

1. **Given** the trained model and the dataset, **When** the permutation test is executed (shuffling labels [deferred] times), **Then** a distribution of AUC scores under the null hypothesis is generated.
2. **Given** the observed AUC and the null distribution, **When** the p-value is calculated, **Then** the result indicates whether the observed correlation is statistically significant (e.g., p < 0.05).
3. **Given** the permutation results, **When** the report is generated, **Then** the p-value and the observed AUC are explicitly compared in the output summary.

---

### Edge Cases

- What happens when a literature review section is empty or too short to form a graph with cycles? (System must handle zero-node or single-node graphs gracefully, assigning default metric values of 0.0 and logging a warning).
- How does the system handle duplicate entities in the extracted triplets? (System must merge nodes with identical labels before calculating metrics).
- What happens if the benchmark dataset lacks ground-truth failure labels for a specific entry? (System must exclude that entry from the training set and log a warning).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST parse literature review sections from the "AI for Auto-Research" benchmark to extract entity-relation triplets and construct directed graphs. (See US-1)
- **FR-002**: System MUST compute topological metrics including cycle density, citation isolation (degree centrality of nodes with no external incoming edges), and average semantic distance (defined as the mean pairwise cosine distance between concept embeddings using the `all-MiniLM-L6-v2` model within the same graph component) for each graph. (See US-1)
- **FR-003**: System MUST map extracted graphs to the ground-truth binary labels ("novelty degradation"/"experimental failure" vs. "valid") provided in the benchmark validation phase. (See US-1, US-2)
- **FR-004**: System MUST train an interpretable classifier using Logistic Regression as the primary model; if Logistic Regression fails to converge, it MUST fall back to Random Forest. The system MUST report model coefficients (for LR) or SHAP values (for RF) for all topological metrics. (See US-2)
- **FR-005**: System MUST perform 5-fold cross-validation to estimate predictive accuracy and report the Area Under the Curve (AUC) as the primary performance metric. (See US-2)
- **FR-006**: System MUST execute a permutation test with a sufficient number of permutations to verify that the observed correlation between graph metrics and failure labels is statistically significant and not due to chance. (See US-3)
- **FR-007**: System MUST handle datasets with missing ground-truth labels by excluding them from training and logging a warning, ensuring no data leakage occurs. (See US-2)
- **FR-008**: System MUST log every instance where default metric values (0.0) are assigned due to empty or short input text, including the ID of the affected graph. (See US-1)
- **FR-009**: System MUST verify that the ground-truth labels are derived from external experimental outcomes (e.g., wet-lab results) and not from the text analysis itself, ensuring no circular validation. (See US-2)
- **FR-010**: System MUST report the "citation isolation" metric as a hypothesized proxy for hallucination, explicitly stating this as a limitation if no ground-truth hallucination data is available for validation. (See US-1)

### Key Entities

- **LiteratureReviewGraph**: A directed graph representing the structure of a literature review, with nodes as concepts/methods and edges as claims.
- **TopologicalFeatureSet**: A structured record containing computed metrics (cycle density, isolation score, semantic distance) for a specific graph.
- **ValidationLabel**: The ground-truth binary outcome (Failure/Valid) associated with a specific research idea from the benchmark.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Predictive accuracy (AUC) of the topological metrics model is measured against the baseline of random guessing (AUC = 0.5) to determine if structural anomalies provide signal. (See US-2)
- **SC-002**: Statistical significance (p-value) of the correlation between graph metrics and failure labels is measured against the null hypothesis distribution generated by the permutation test. (See US-3)
- **SC-003**: Computational feasibility is measured against the constraint of running the entire pipeline (graph construction, training, validation) within 6 hours on a CPU-only runner with ≤7 GB RAM. (See US-2, US-3)
- **SC-004**: Model performance is measured by reporting the AUC and p-value; a null result (AUC ≈ 0.5, p > 0.05) is a valid and recorded outcome, not a failure. (See US-2)
- **SC-005**: Data completeness is measured against the requirement that all graphs constructed must have valid metric values (no NaNs) and be successfully mapped to a ground-truth label, including those assigned default values (0.0) as per the edge case strategy. (See US-1, US-3)

## Assumptions

- The "AI for Auto-Research" benchmark dataset is available and contains both the "Creation" phase logs (literature review text) and the "Validation" phase results (binary failure labels) in a format that can be programmatically accessed.
- The NLP pipeline (e.g., spaCy) and graph library (e.g., NetworkX) can be installed and run within the GitHub Actions free-tier environment (CPU-only, ≤7 GB RAM) without requiring GPU acceleration or large model downloads.
- The extracted entity-relation triplets are sufficient to construct meaningful graphs where topological metrics (cycle density, isolation) vary across the dataset; if the text is too uniform, the metrics may lack variance, limiting predictive power.
- The ground-truth labels provided in the benchmark are reliable and accurately reflect "experimental failure" or "novelty degradation" as defined in the original study, and are derived from external experimental outcomes (not text analysis).
- The permutation test will be computationally feasible within the 6-hour runtime limit, assuming the number of permutations is capped at a manageable level and the dataset size is manageable.
- The "citation isolation" metric is hypothesized to be a proxy for "hallucination" or "lack of grounding" in the context of this specific dataset, but this link is not proven and will be reported as a limitation if no ground-truth hallucination data is available.
- The dataset contains a sufficient number of samples (n ≥ 30) to perform 5-fold cross-validation and permutation testing with statistical power, though the exact number is deferred to the data exploration phase.