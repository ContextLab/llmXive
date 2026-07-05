# Feature Specification: Evaluating the Statistical Validity of Common Ranking Metrics

**Feature Branch**: `001-statistical-validity-ranking-metrics`
**Created**: 2023-10-27
**Status**: Draft
**Input**: User description: "Evaluating the Statistical Validity of Common Ranking Metrics"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Permutation Test Execution (Priority: P1)

The system must execute the core permutation test workflow on TREC benchmark data to generate null distributions for NDCG and MAP metrics.

**Why this priority**: This is the foundational research step; without generating the null distributions via shuffling, no statistical comparison or power analysis can occur. It delivers the primary data required to answer the research question.

**Independent Test**: Can be fully tested by running the permutation script on a single query and verifying the generation of [deferred] permuted metric scores and a baseline permutation p-value result.

**Acceptance Scenarios**:

1. **Given** a valid TREC query-document set with relevance labels, **When** the permutation engine runs, **Then** it generates [deferred] permuted relevance label sets per query.
2. **Given** [deferred] permuted relevance sets, **When** NDCG@10 and MAP are computed, **Then** a null distribution table is produced containing metric scores for all permutations.
3. **Given** original and permuted metric scores, **When** permutation p-value calculations run, **Then** p-values are calculated (rank of observed value in null) and recorded for each query-metric pair.

---

### User Story 2 - Power Analysis & Inference Framing (Priority: P2)

The system must calculate the Minimum Detectable Effect Size (MDES) and apply statistical corrections to ensure findings are methodologically sound and associational.

**Why this priority**: This step transforms raw metric scores into valid statistical claims. It addresses the research gap regarding statistical power and prevents false positives through multiplicity correction.

**Independent Test**: Can be tested by verifying the bootstrap calculation output and checking that significance claims reference the corrected p-values rather than raw p-values.

**Acceptance Scenarios**:

1. **Given** null and original distributions, **When** bootstrap power analysis runs (500 resamples), **Then** the MDES at α=0.05 and Power=0.8 is calculated and stored.
2. **Given** multiple metric tests (NDCG, MAP), **When** results are aggregated, **Then** a multiple-comparison correction (Benjamini-Hochberg) is applied to the p-values across the set of queries for each metric independently.
3. **Given** statistical significance results, **When** findings are reported, **Then** they are framed as evidence of statistical association between the metric score and relevance judgments, explicitly noting this does not imply causal algorithmic improvement.

---

### User Story 3 - Reporting & Visualization (Priority: P3)

The system must produce human-readable visualizations and machine-readable summary tables within the compute budget.

**Why this priority**: This delivers the final artifacts for review and publication. It ensures the results are interpretable and fits within the free-tier CI constraints.

**Independent Test**: Can be tested by checking the output directory for required CSV files and PNG plots after the script completes within 6 hours.

**Acceptance Scenarios**:

1. **Given** completed analysis data, **When** the reporting module runs, **Then** a CSV summary table of all queries and metrics is generated.
2. **Given** null and original distributions, **When** visualization runs, **Then** density plots comparing original vs. permuted metric scores are saved as PNGs.
3. **Given** runtime constraints, **When** execution exceeds 5 hours or memory exceeds 6 GB, **Then** the system triggers query subsampling (n=100) to complete within the limit.

---

### Edge Cases

- What happens when a TREC query has zero relevance labels in the qrels file? (System MUST skip query and log warning).
- How does system handle network failure during TREC data download? (System MUST retry up to 3 times, then fail gracefully with error code).
- What happens if memory usage approaches 7 GB during bootstrap resampling? (System MUST process queries in batches to stay within limit).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download relevant TREC Robust and Web Track 2009-2012 qrels from ` without requiring authentication. (See US-1)
- **FR-002**: System MUST implement a permutation engine that shuffles relevance labels a sufficient number of times per query to ensure statistical robustness. (See US-1)
- **FR-003**: System MUST compute NDCG@10 and MAP scores for both original and all permuted relevance sets. (See US-1)
- **FR-004**: System MUST calculate a permutation p-value for each query-metric pair by determining the rank of the observed metric score within the null distribution generated by a sufficient number of permutations, using the formula (r + 1) / (N + 1), where r is the rank of the observed score and N is the total number of permutations, and MUST log the exact count of permutations executed (target: a predefined sufficient number). (See US-1)
- **FR-005**: System MUST apply the Benjamini-Hochberg (BH) procedure to control the False Discovery Rate (FDR) at a predefined significance threshold across the set of queries for each metric independently (two families of tests: one for NDCG@10, one for MAP). Justification: BH is standard for exploratory studies to maintain statistical power while controlling false positives, unlike Bonferroni which is overly conservative for large numbers of tests. (See US-2)
- **FR-006**: System MUST calculate Minimum Detectable Effect Size (MDES) using 500 bootstrap resamples at α=0.05 and Power=0.8. The system MUST simulate an alternative hypothesis by applying a known ranking improvement (e.g., swapping top-k positions) to the relevance labels, then perform a binary search over effect sizes (initial range [0.001, 0.500], tolerance ≤ 0.001) to find the smallest shift detectable with Power ≥ 0.8. (See US-2)
- **FR-007**: System MUST perform a sensitivity analysis on the significance threshold by sweeping α across a relevant range and reporting the count of queries where the significance status changes between α values. Justification: Essential for robustness verification against threshold selection bias. (See US-2)
- **FR-008**: System MUST frame all findings regarding metric performance as evidence of statistical association between the metric score and relevance judgments, explicitly noting this does not imply causal algorithmic improvement. (See US-2)
- **FR-009**: System MUST limit total runtime to ≤ 6 hours on a 2 CPU core runner. (See US-3)
- **FR-010**: System MUST restrict memory usage to ≤ 7 GB RAM during execution by processing queries in batches if needed. (See US-3)
- **FR-011**: System MUST implement query subsampling (n=100 max) if runtime exceeds 5 hours or memory usage exceeds 6 GB during the initial batch processing of the full TREC collection. (See US-3)
- **FR-012**: System MUST execute analysis on CPU-only environment without requiring CUDA, GPU, or low-bit quantization dependencies. (See US-3)

### Key Entities

- **Query**: Represents a single search topic ID from the TREC collection, associated with a set of documents and relevance judgments.
- **Metric**: Represents the evaluation score (NDCG@10 or MAP) computed for a specific query-document ranking.
- **Distribution**: Represents the set of metric scores generated either from the original ranking (signal) or permuted rankings (null).

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* is measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Permutation test completion rate is measured against the total number of queries processed (Target: all selected queries). (See US-1)
- **SC-002**: Permutation p-value calculation completeness is measured against the total number of query-metric pairs analyzed. (See US-1)
- **SC-003**: MDES estimate stability is measured against the width of the 95% confidence interval of the MDES value (Target: width < 0.02 in NDCG@10 or MAP units, respectively). (See US-2)
- **SC-004**: Runtime compliance is measured against the 6-hour GHA free-tier limit (Target: ≤ 6 hours). (See US-3)
- **SC-005**: Memory usage is measured against the 7 GB RAM limit (Target: Peak usage ≤ 7 GB). (See US-3)
- **SC-006**: Output artifact completeness is measured against the required deliverables (CSV summary, PNG plots) (Target: complete generation of required files). (See US-3)

## Assumptions

- TREC qrels data is publicly accessible via ` without requiring special authentication or API keys.
- The GitHub Actions free-tier runner provides a Python 3.9+ environment with `numpy`, `pandas`, and `scipy` pre-installed or installable within the 6-hour window.
- Query subsampling (n=100) preserves statistical representativeness sufficient for the power analysis goal.
- Network bandwidth on the runner is sufficient to download the required TREC subsets within the runtime budget.
- Permutation test computation is CPU-tractable on 2 cores for [deferred] iterations and up to 500 queries (before subsampling).