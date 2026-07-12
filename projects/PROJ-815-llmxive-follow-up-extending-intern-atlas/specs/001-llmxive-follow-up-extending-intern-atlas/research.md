# Research: llmXive follow-up: extending "Intern-Atlas: A Methodological Evolution Graph as Research Infrastruct"

## 1. Problem Formulation

The core hypothesis is that the topological structure of methodological evolution graphs predicts the stability of a research lineage. Specifically, we investigate if the **Bottleneck Resolution Ratio (BRR)** and **Branching Entropy** of a method node are predictive of its retraction status (Fragile vs. Robust), independent of citation volume.

**Research Question**: Does the ratio of 'bottleneck-resolving' edges to 'incremental-variant' edges within a local neighborhood predict the long-term reproducibility of a methodological lineage?

## 2. Dataset Strategy

### 2.1 Primary Data Sources

**Intern-Atlas Graph**:
*   **Description**: A research infrastructure graph representing the evolution of methods.
*   **Usage**: Source of nodes (methods) and edges (relationships: `improves`, `replaces`, `extends`).
*   **Verified Source**: **Intern-Atlas GitHub Repository (v1.0.0)**. The implementation MUST download the specific release containing human-annotated edge types. If the release only contains LLM-inferred edges, the pipeline MUST abort with: "Error: Intern-Atlas dataset contains only LLM-inferred edge types. Human-annotated types required per FR-002."
*   **Constraint**: Edge types MUST be human-annotated or from a validated ontology. LLM-inferred types are forbidden (FR-002).

**Retraction Watch Database / Replication Index**:
*   **Description**: External ground truth for paper stability.
*   **Usage**: To assign labels (Fragile=1, Retraction-Only=2, Robust=0) to method nodes.
*   **Verified Source**: **Retraction Watch Database CSV Dump** (latest version from `retractionwatch.com` or verified GitHub mirror). The implementation MUST download the specific CSV file covering the relevant multi-year window.

### 2.2 Feature Engineering Strategy

*   **Bottleneck Resolution Ratio (BRR)**: Count of outgoing `improves`/`replaces` edges / Total outgoing edges.
    *   *Scope*: Calculated over **immediate outgoing neighbors (1-hop)**.
    *   *Handling Edge Cases*: If a node has no outgoing edges, BRR = 0.0. Untyped edges are excluded from the denominator; if a node has only untyped edges, it is dropped with a log entry.
*   **Branching Entropy**: Shannon entropy of the distribution of downstream method types.
    *   *Scope*: Calculated over **immediate outgoing neighbors (1-hop)**.
    *   *Justification*: Methodological lineage stability is determined by immediate successors' diversity, not distant descendants.
*   **Citation Count**: Total incoming citations (for baseline model).

### 2.3 Labeling Strategy

*   **Mapping**: Match nodes to external DB using exact DOI match first. If no DOI, use fuzzy title/author match (Levenshtein ratio >= 0.85).
* **Validation**: **Manual spot-check of a random [deferred] sample of fuzzy matches**. If the error rate in the spot-check exceeds a predefined threshold, the fuzzy threshold is raised or the dataset is flagged.
*   **Conflict Resolution**: If multiple matches exist, select the earliest by publication date. If dates are identical, select alphabetically by journal name (FR-010).
*   **Label Definition**:
    *   `1` (Fragile): Methodological error or irreproducibility.
    *   `2` (Retraction-Only): Fraud or plagiarism.
    *   `0` (Robust): All others.
*   **Binary Conversion for Model**: The primary model (FR-005) predicts `Fragile` (1) vs `Robust` (0). **Label 2 (Retraction-Only) is mapped to 0 (Robust)**.
    *   *Justification*: The hypothesis targets "methodological stability". While Fraud (2) is a failure mode, it is distinct from Methodological Error (1). Grouping Fraud with Robustness (0) allows us to test if topology predicts *methodological* error specifically, rather than conflating it with fraud. We acknowledge this groups distinct failure modes, but it is necessary to test the specific "methodological stability" signal without conflating it with "fraud detection", which is a different research question.
    *   *Confounding Acknowledgement*: Fraudulent papers often have high citation/edge activity similar to robust papers. This grouping may mask the true relationship between topology and *methodological* stability. A sensitivity analysis will be discussed in the paper.
*   **Abort Condition**: In `code/labeling.py`, if no ground truth labels are found for the 2010-2018 window, the system MUST raise `ValueError` with the exact message: "No ground truth labels found for the specified time window; analysis cannot proceed."

## 3. Statistical Methodology

### 3.1 Model Architecture
*   **Primary Model**: Logistic Regression (Interpretable, CPU-efficient).
    *   Predictors: `bottleneck_resolution_ratio`, `branching_entropy`.
*   **Baseline Model**: Logistic Regression.
    *   Predictors: `citation_count`, `publication_year`.
*   **Output**: Coefficients, AUC-ROC, Precision-Recall.

### 3.2 Statistical Rigor & Robustness
*   **Permutation Test (FR-007)**:
    *   **n=100** (Strictly adhering to spec, not 1000).
    *   **Method**: **Stratified permutation** within `field_of_study` and `venue` strata to control for confounding (FR-012). Labels are permuted *within* each stratum.
    *   **Criterion**: **Non-parametric rank-based p-value**. p = (count of permuted AUCs >= observed AUC + 1) / (n + 1). Significance if p < 0.05. (Acknowledges n=100 provides p-resolution of a fine-grained scale, mitigated by stratification).
*   **Threshold Sensitivity (FR-008)**:
    *   Sweep cutoffs at **{0.3, 0.5, 0.7}**.
    *   Report FPR and FNR for each.
*   **Collinearity Diagnostics (FR-009)**:
    *   Calculate **VIF** and **Mutual Information (MI)** for predictors.
    *   Flag if VIF > 5 or MI > 0.1.
*   **Covariate Adjustment (FR-012)**:
    *   **Mandatory and Unconditional**: The system MUST perform stratified permutation test for 'field of study' and 'publication venue' to control for confounding variables, regardless of initial model performance.

### 3.3 Circularity Risk Mitigation
*   **Temporal Independence**: Edge types (`improves`/`replaces`) are derived **solely from the publication text at the time of publication** (or the graph's original human-annotated metadata) and **NOT** from post-hoc retraction knowledge. This ensures the predictor (BRR) is not mathematically determined by the outcome (Retraction).
*   **Epistemic Independence**: Edges are typed based on the **claim of improvement** at the time of publication, not the actual outcome. This prevents the predictor from being a tautology of the outcome.

### 3.4 Compute Feasibility
*   **CPU-Only**: All models use `scikit-learn` with default CPU settings.
*   **Memory**: Data will be loaded in chunks or sampled if the graph exceeds available memory capacity.
*   **Time**: Permutation (n=100) and threshold sweep are lightweight. Logistic regression is fast. Total runtime expected < 2 hours.

## 4. Decision Rationale

*   **Why Logistic Regression?** The Constitution Principle VII requires interpretability. Black-box models (NNs) would obscure the link between topology and stability. LR provides explicit coefficients for BRR and Entropy.
*   **Why n=100 for Permutation?** Spec FR-007 explicitly mandates n=100. We acknowledge the statistical limitation (p-resolution 0.01) but mitigate it via stratified permutation.
*   **Why Mandatory Covariate Adjustment?** Spec FR-012 requires this to control for confounding. It is unconditional.
*   **Why Binarization?** The core hypothesis (US-2) is "Fragile vs Robust". While Retraction-Only exists, the primary predictive power test is for Fragility (methodological error). Grouping Fraud with Robustness is a necessary trade-off to test the specific "methodological stability" signal.

## 5. Risks & Mitigations

*   **Risk**: Missing edge types in Intern-Atlas.
    *   *Mitigation*: Log nodes with untyped edges; drop them if they constitute >20% of the dataset. Abort if <80% have typed edges (Assumption).
*   **Risk**: No ground truth labels for 2010-2018.
    *   *Mitigation*: Abort with explicit error message (Edge Case).
*   **Risk**: Graph too large for RAM.
    *   *Mitigation*: Implement streaming processing or random sampling (documented in `research.md`).
*   **Risk**: Label noise from fuzzy matching.
 * *Mitigation*: Manual spot-check of [deferred] of fuzzy matches.