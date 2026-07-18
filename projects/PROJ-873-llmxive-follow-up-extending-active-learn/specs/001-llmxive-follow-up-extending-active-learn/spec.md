# Feature Specification: llmXive follow-up: extending "Active Learners as Efficient PRP Rerankers"

**Feature Branch**: `001-llmxive-prp-redundancy`  
**Created**: 2026-07-11  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'Active Learners as Efficient PRP Rerankers'"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Quantify Redundancy-Induced Efficiency Loss (Priority: P1)

**User Journey**: A researcher needs to determine if active Pairwise Ranking Prompting (PRP) rankers waste LLM call budgets when processing retrieval lists containing near-duplicate documents. The researcher must observe a measurable degradation in ranking quality (NDCG@10) relative to the number of calls spent on redundant pairs.

**Why this priority**: This is the core hypothesis validation. Without establishing that redundancy actually degrades performance, the subsequent optimization (pre-clustering) has no justification. It directly addresses the "What is NOT known" gap regarding the interaction between input noise and active selection.

**Independent Test**: Can be tested by running the baseline active ranker on artificially inflated datasets with varying redundancy levels ([deferred], [deferred], [deferred]) and comparing the ratio of "wasted" calls (high similarity pairs) to NDCG@10 scores.

**Acceptance Scenarios**:

1. **Given** a retrieval candidate list with [deferred] near-duplicate passages (similarity > 0.95), **When** the baseline active ranker executes its query budget of 100 calls, **Then** the system MUST measure and report the ratio of "wasted" calls and the NDCG@10 drop; the hypothesis is that at least 35% of those calls will be classified as "wasted" (comparing near-duplicates), and the resulting NDCG@10 will be at least 15% lower than the NDCG@10 achieved by a full-baseline run on the unique subset of the same list.
2. **Given** a retrieval candidate list with [deferred] redundancy, **When** the baseline active ranker executes the same query budget, **Then** the system MUST measure and report the ratio of "wasted" calls; the hypothesis is that the ratio will be < 5%, and the NDCG@10 will remain within 5% of the NDCG@10 achieved by a full-baseline run on the unique subset.

---

### User Story 2 - Validate CPU-Tractable Pre-Clustering Recovery (Priority: P2)

**User Journey**: A researcher needs to verify that a lightweight MinHash-LSH pre-clustering step can filter redundant comparisons, allowing the active ranker to focus on informative pairs, thereby restoring NDCG@10 performance without exceeding the 7GB RAM or 6-hour runtime limits of a CPU-only CI runner.

**Why this priority**: This validates the proposed solution. It proves that the method is not only theoretically sound but also computationally feasible in the target environment (GitHub Actions free tier) and effectively mitigates the problem identified in US-1.

**Independent Test**: Can be tested by running the full pipeline (MinHash-LSH + Active Ranker) on the same high-redundancy dataset used in US-1 and comparing the "wasted" call ratio and NDCG@10 against the baseline.

**Acceptance Scenarios**:

1. **Given** a retrieval candidate list with [deferred] near-duplicate passages, **When** the pre-clustering step (threshold Jaccard > 0.95) reduces the candidate pool size by at least 30%, **Then** the system MUST measure and report the "wasted" call ratio and NDCG@10 recovery; the hypothesis is that the "wasted" call ratio will drop to < 10%, and the NDCG@10 will recover to within 5% of the unique-only baseline performance (derived from the unique subset of the redundant list).
2. **Given** the full pipeline execution on a standard GitHub Actions free-tier runner (2 CPU, 7GB RAM), **When** processing a dataset of N=100 candidates with redundancy level >= 40%, **Then** the total execution time must be ≤ 6 hours, and peak memory usage must remain ≤ 7GB.

---

### User Story 3 - Statistical Significance of Efficiency Gains (Priority: P3)

**User Journey**: A researcher needs to confirm that the observed improvements in call efficiency and ranking quality are statistically significant and not due to random variance in the dataset sampling or LLM stochasticity.

**Why this priority**: Essential for scientific rigor. It ensures the results are robust and publishable, addressing the "Multiplicity & power" methodological requirement by validating the hypothesis with appropriate statistical testing.

**Independent Test**: Can be tested by running the baseline and clustering-aided variants over multiple random seeds and performing a Wilcoxon signed-rank test on the resulting NDCG@10 and efficiency metrics.

**Acceptance Scenarios**:

1. **Given** 5 independent runs of both the baseline and clustering-aided variants on the same dataset configuration, **When** a Wilcoxon signed-rank test is performed on the NDCG@10 scores, **Then** the p-value must be < 0.05, indicating a statistically significant difference favoring the clustering-aided variant.
2. **Given** the same set of runs, **When** a Wilcoxon signed-rank test is performed on the "wasted call" ratios, **Then** the p-value must be < 0.05, confirming the reduction in wasted budget is statistically significant.

### Edge Cases

- What happens if the MinHash-LSH threshold (Jaccard > 0.95) is too strict, causing unique documents to be incorrectly merged into clusters, thereby reducing the effective candidate pool too much?
- How does the system handle the scenario where the artificial paraphrasing fails to generate sufficient semantic similarity (similarity < 0.95) despite being near-duplicates, leading to false negatives in the "wasted" classification?
- How does the system behave if the LLM call budget (e.g., 20 calls) is so low that the active ranker cannot explore the candidate pool sufficiently to distinguish between redundant and unique items?
- What happens if the LLM consensus validation step (used to verify the cosine proxy) exceeds the runtime budget? The system MUST fall back to using only the cosine proxy for the main loop if the validation sample exceeds a significant portion of the budget.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST implement a MinHash-LSH algorithm to group near-duplicate passages with a Jaccard similarity threshold of > 0.95 prior to ranking, serving US-2.
- **FR-002**: System MUST inject semantic redundancy into the BEIR "nfcorpus" and "scifact" datasets by creating at least 20 clusters of 3–5 near-duplicate items via synonym replacement and sentence shuffling, serving US-1.
- **FR-003**: System MUST log every pairwise comparison made by the active ranker and compute the cosine similarity of the compared pairs using a CPU-tractable embedding model (e.g., `all-MiniLM-L6-v2`) to *flag* potential "wasted" calls (similarity > 0.95); additionally, the system MUST validate this proxy by running LLM consensus on a random [deferred] sample of flagged calls to estimate ground truth accuracy, serving US-1.
- **FR-004**: System MUST calculate NDCG@k scores for both the baseline and clustering-aided variants against the original BEIR relevance judgments at fixed LLM call budgets spanning a range of values., serving US-2.
- **FR-005**: System MUST execute a Wilcoxon signed-rank test comparing the NDCG@10 scores and wasted call ratios between the baseline and clustering-aided conditions with a significance level of p < 0.05, serving US-3.
- **FR-006**: System MUST enforce a hard runtime limit of hours and a memory limit of a predefined magnitude during execution to ensure compatibility with the GitHub Actions free-tier runner, serving US-2.
- **FR-007**: System MUST apply a multiple-comparison correction (e.g., Bonferroni) when evaluating the significance of multiple hypotheses (NDCG and efficiency) to control the family-wise error rate, serving US-3.
- **FR-008**: System MUST validate the correlation between Jaccard similarity (MinHash) and Cosine similarity (Embeddings) on a labeled subset of pairs before relying on them interchangeably for scientific reporting, serving US-2.
- **FR-009**: System MUST validate the synthetic redundancy proxy against a small set of real-world near-duplicates (e.g., from the BEIR "trec-covid" dataset) to ensure generalizability, serving US-1.

### Key Entities

- **Candidate List**: A collection of N=100 retrieval passages, potentially containing clusters of near-duplicates generated by the injection process.
- **Comparison Pair**: A tuple of two documents selected by the active ranker for LLM-based comparison, annotated with a similarity score and a "wasted/informative" label.
- **Redundancy Level**: A quantitative metric representing the percentage of near-duplicate items in the candidate list; the system MUST test varying levels to validate robustness.
- **Ranking Quality**: The NDCG@10 score calculated against ground truth relevance judgments.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The ratio of "wasted" LLM calls (comparisons with similarity > 0.95) is measured against the total call budget to quantify efficiency loss in high-redundancy scenarios, serving US-1.
- **SC-002**: The NDCG@10 score of the clustering-aided variant is measured against the NDCG@10 of the baseline active ranker on the same high-redundancy dataset to quantify performance recovery, serving US-2.
- **SC-003**: The statistical significance (p-value) of the difference in NDCG@10 and wasted call ratios between the two variants is measured against the alpha threshold of 0.05 to validate the hypothesis, serving US-3.
- **SC-004**: The total execution time and peak memory usage of the full pipeline are measured against the GitHub Actions free-tier constraints (6h, 7GB) to verify compute feasibility, serving US-2.
- **SC-005**: The sensitivity of NDCG@k recovery to the MinHash-LSH threshold is measured by sweeping the threshold over a set of representative values, with the research question focusing on how threshold selection impacts ranking quality and the method employing a systematic parameter sweep. References: [Citation to be inserted]. to validate the robustness of the clustering decision, serving US-2.

## Assumptions

- The BEIR "nfcorpus" and "scifact" datasets contain sufficient semantic variety to allow for the creation of meaningful near-duplicate clusters via the described paraphrasing methods (synonym replacement, sentence shuffling) without destroying the original semantic intent.
- The `all-MiniLM-L6-v2` embedding model is sufficiently accurate on CPU to distinguish near-duplicates (similarity > 0.95) from unique documents, serving as a reliable proxy for LLM-based similarity in the "wasted" call classification.
- The active ranker implementation (based on the Mohajer preprint) is available and compatible with the Python environment provided by the GitHub Actions runner, requiring no GPU-specific dependencies.
- The artificial injection of redundancy (clusters of 3–5 items) accurately simulates the behavior of real-world retrievers that return noisy, near-duplicate lists, serving as a valid proxy for production data.
- The Jaccard similarity threshold of > 0.95 for MinHash-LSH is a defensible community standard for identifying "near-duplicates" in text clustering, justifying the specific cutoff used for the sensitivity analysis.
- The unique-only baseline performance is derived from the unique subset of the redundant list to ensure a fair comparison of ranking quality independent of pool size.