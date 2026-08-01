# Feature Specification: llmXive Follow-up: Extending ProRL for Zero-Shot Proactive Recommendation

**Feature Branch**: `001-llmxive-prorl-zero-shot`  
**Created**: 2026-07-10  
**Status**: Draft  
**Input**: User description: "Does applying ProRL's 'Stepwise Reward Centering' and 'Position-Specific Advantage Estimation' mechanisms as a post-hoc path-scoring filter on a static item-similarity graph improve the precision and diversity of proactive recommendations in cold-start (zero-shot) scenarios compared to standard greedy heuristics?"

## User Scenarios & Testing

### User Story 1 - Zero-Shot Path Generation and Scoring (Priority: P1)

The system must be able to ingest a cold-start user seed (a single item or category), construct a static item-similarity graph from a public dataset, generate candidate recommendation paths using a greedy heuristic, and apply the ProRL-derived rectification formulas (Stepwise Reward Centering and Position-Specific Advantage) as a post-hoc scoring filter to rank these paths without any model training.

**Why this priority**: This is the core research intervention. Without the ability to generate paths and apply the specific bias-correction formulas in a zero-shot setting, the hypothesis cannot be tested. This forms the Minimum Viable Product (MVP) of the research pipeline.

**Independent Test**: Can be fully tested by running the pipeline on a small subset of the Amazon Books dataset with a fixed seed, verifying that the output is a ranked list of paths where the scores differ from the raw greedy scores due to the applied formulas.

**Acceptance Scenarios**:

1. **Given** a cold-start seed item and a pre-processed similarity graph, **When** the system generates candidate paths of length L=5 and applies the ProRL scoring filter, **Then** it outputs a ranked list of paths with rectified scores distinct from the baseline greedy scores.
2. **Given** a seed item with no historical interaction data in the held-out test set, **When** the system executes the path generation and scoring, **Then** it successfully returns a top-K list without raising "missing data" errors related to user history.

---

### User Story 2 - Baseline Comparison and Metric Calculation (Priority: P2)

The system must compare the top-K paths selected by the ProRL rectified scoring against the top-K paths selected by the standard greedy heuristic, calculating offline metrics (Precision@K, Recall@K, Diversity, and Coverage) against a held-out test set of user sessions to determine performance differences. The ground-truth target for Precision@K is defined as the *single next item* the user interacted with in the session following the seed item.

**Why this priority**: This enables the quantitative evaluation required to answer the research question. It validates whether the new method actually improves upon the baseline in the defined cold-start scenario.

**Independent Test**: Can be tested by running the evaluation module on a fixed test set, comparing the metric values of the "ProRL-scored" list against the "Greedy" list, and verifying that the output includes the calculated metrics for both methods.

**Acceptance Scenarios**:

1. **Given** two ranked lists (one from ProRL scoring, one from Greedy scoring) and a ground-truth test set of user sessions (where the target is the next item after the seed), **When** the evaluation module runs, **Then** it outputs Precision@K, Recall@K, Diversity, and Coverage for both lists.
2. **Given** the calculated metrics, **When** the system performs a statistical test, **Then** it reports the p-value and the direction of the difference (e.g., "ProRL is higher/lower") for each metric.

---

### User Story 3 - Statistical Significance and Sensitivity Analysis (Priority: P3)

The system must perform a statistical significance test (paired t-test or Wilcoxon signed-rank test) on the metric differences and conduct a sensitivity analysis by sweeping the decision cutoffs (e.g., path length or similarity thresholds) to observe how the headline rates (Precision, Diversity) vary across the sweep. The unit of analysis for the statistical test is the seed item.

**Why this priority**: This ensures methodological soundness by addressing multiplicity, power, and threshold justification, preventing the results from being dismissed as statistical flukes or artifacts of arbitrary parameter choices.

**Independent Test**: Can be tested by modifying the sensitivity analysis configuration to sweep a parameter (e.g., path length) and verifying that the output includes a report of how metrics change across the sweep range.

**Acceptance Scenarios**:

1. **Given** the metric differences aggregated per seed item, **When** the statistical analysis module runs, **Then** it outputs a p-value < 0.05 (or reports non-significance) and the confidence interval for the difference, using a Wilcoxon test if normality assumptions are violated.
2. **Given** a defined threshold range (e.g., similarity cutoff ∈ {0.01, 0.05, 0.1}), **When** the sensitivity analysis runs, **Then** it produces a summary showing how the false-positive/negative rates or inconsistency rates vary across these values.

### Edge Cases

- What happens when the similarity graph is disconnected such that no path of length L exists from the seed item? (System must handle gracefully, e.g., by returning a shorter path or a null result).
- What occurs if the held-out test set contains no sessions matching the cold-start seed items?

## Requirements

### Functional Requirements

- **FR-001**: System MUST construct a static item-similarity graph using cosine similarity on content features from the specified public datasets (Amazon Books, Last.fm, MovieLens) and support path generation of a fixed length $L$. (See US-1)
- **FR-002**: System MUST implement the "Stepwise Reward Centering" (SRC) and "Position-Specific Advantage Estimation" (PSA) formulas as a deterministic, post-hoc scoring function. SRC is defined as $S_{rect} = S_{raw} - \mu_{batch}$, where $\mu_{batch}$ is the mean of all raw scores in the current candidate batch. PSA is defined as $S_{final} = S_{rect} \times (1 + \alpha \times pos)$, where $pos$ is the 0-indexed position in the path and $\alpha = 0.1$. This calculation must occur without updating model parameters. (See US-1)
- **FR-003**: System MUST generate candidate paths using a standard greedy heuristic based on immediate similarity to the seed item for the baseline comparison. (See US-2)
- **FR-004**: System MUST calculate offline evaluation metrics: Precision@K (ratio of recommended items that match the next ground-truth item), Recall@K (ratio of ground-truth items found in top-K), Diversity (defined as $1 - \frac{1}{K(K-1)} \sum_{i \neq j} \cos(\vec{v}_i, \vec{v}_j)$), and Coverage (defined as $\frac{|\text{unique items in top-K}|}{|\text{unique items in candidate pool}|}$). (See US-2)
- **FR-005**: System MUST perform a statistical significance test on metric differences aggregated per seed item. The system MUST first perform a Shapiro-Wilk test for normality; if $p < 0.05$, it MUST use the Wilcoxon signed-rank test. Otherwise, it MUST use a paired t-test. (See US-3)
- **FR-006**: System MUST execute a sensitivity analysis sweeping the decision cutoff (e.g., absolute difference threshold or path length) over a concrete set (e.g., {0.01, 0.05, 0.1}) and report the variation in headline rates. (See US-3)
- **FR-007**: System MUST handle disconnected graph components by either truncating the path or returning a null result without crashing the pipeline. (See US-1)
- **FR-008**: System MUST ensure all data processing and analysis steps fit within the RAM and disk constraints of a standard GitHub Actions runner. (See US-1)
- **FR-009**: System MUST assign a default similarity score of 0.0 to any neighbor with zero feature overlap and MUST skip such nodes during path generation to prevent infinite loops or crashes. (See US-1)

### Key Entities

- **ItemNode**: Represents an item in the graph, containing metadata features (e.g., genre, artist) and a unique identifier.
- **SimilarityEdge**: Represents the weighted connection between two items, storing the cosine similarity score.
- **RecommendationPath**: An ordered sequence of ItemNodes representing a potential proactive recommendation list, associated with a raw greedy score and a rectified ProRL score.
- **EvaluationMetric**: A record of calculated performance values (Precision, Diversity, etc.) for a specific path list against a ground-truth session.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The difference in Precision@K between the ProRL-scored and Greedy-scored lists is measured against the null hypothesis of zero difference using a paired t-test or Wilcoxon signed-rank test. (See FR-005, US-2)
- **SC-002**: The variation in Diversity and Coverage rates across the sensitivity sweep (threshold values {0.01, 0.05, 0.1}) is measured and reported to assess threshold robustness. (See FR-006, US-3)
- **SC-003**: The computational runtime of the full pipeline (graph construction, path generation, scoring, evaluation) is measured against the predefined time limit of the GitHub Actions runner. (See FR-008, US-1)
- **SC-004**: The memory usage peak during the execution of the analysis is measured against the available RAM limit to ensure feasibility. (See FR-008, US-1)
- **SC-005**: The mean absolute difference between rectified and raw greedy scores across the test set MUST be ≥ 0.01, or the system MUST output a warning flag. Verification is performed by running the pipeline with a fixed random seed (seed=42) and comparing outputs. (See FR-002, US-1)

## Assumptions

- The public datasets (Amazon Books, Last.fm, MovieLens) contain sufficient item metadata (e.g., genre, tags, or audio features) to compute meaningful cosine similarity scores for the graph construction.
- The "Stepwise Reward Centering" and "Position-Specific Advantage Estimation" formulas from the ProRL paper are adapted for this zero-shot context by using the *empirical batch mean* as the baseline for centering and a *fixed linear decay* for position advantage, rather than learned value functions. This makes the formulas deterministic and independent of a trained policy.
- The cold-start scenario is adequately simulated by using a single seed item per user session, with the ground truth being the *next* item in the session.
- The static item-similarity graph constructed from content features is a valid proxy for the user preference space in the absence of behavioral data.
- The GitHub Actions free-tier runner (2 CPU, 7 GB RAM) is sufficient to process the sampled datasets (capped to fit memory) and complete the analysis within 6 hours.
- The held-out test set of user sessions contains enough data points (at least 30 unique seed items) to perform a statistically valid non-parametric test (Wilcoxon) if normality assumptions are violated.