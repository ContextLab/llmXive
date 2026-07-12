# Feature Specification: llmXive follow-up: extending "GateMem: Benchmarking Memory Governance in Multi-Principal Shared-Memo"

**Feature Branch**: `001-gatekeeper-memory-governance`  
**Created**: 2026-07-12  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending GateMem benchmark with a lightweight, CPU-tractable rule-based gatekeeper to reduce leakage and improve deletion compliance."

## User Scenarios & Testing

### User Story 1 - Gatekeeper Pipeline Execution (Priority: P1)

The research system must successfully execute the end-to-end pipeline where user queries are intercepted by the gatekeeper module, validated against role-based rules and deletion logs, and then passed to the retrieval engine only if authorized. This is the core functionality that enables the comparison between the baseline and the governed system.

**Why this priority**: Without a functioning gatekeeper pipeline, no security or compliance metrics can be measured. This is the foundational capability required to test the hypothesis that decoupling governance improves outcomes.

**Independent Test**: Can be fully tested by running a single query against the GateMem test set with a known unauthorized access pattern and verifying the gatekeeper blocks the retrieval, and a known authorized pattern and verifying it passes.

**Acceptance Scenarios**:

1. **Given** a query containing a request for "patient medical records" by a user role "student" (unauthorized), **When** the system processes the query, **Then** the gatekeeper MUST block the retrieval of sensitive memory chunks before they reach the LLM.
2. **Given** a query containing a request for "general course materials" by a user role "instructor" (authorized), **When** the system processes the query, **Then** the gatekeeper MUST allow the retrieval of relevant memory chunks to proceed to the LLM.
3. **Given** a query where the target memory chunk has been flagged in the active deletion log, **When** the system processes the query, **Then** the gatekeeper MUST filter out the deleted chunk regardless of user role.

---

### User Story 2 - Quantitative Metric Calculation (Priority: P2)

The system must calculate the three core metrics (Utility, Access Control, and Forgetting scores) by comparing the gatekeeper-enhanced system's outputs against the ground-truth annotations in the GateMem dataset. This enables the statistical comparison required to validate the research question.

**Why this priority**: This story delivers the primary research output—the data needed to determine if the gatekeeper reduces leakage and improves compliance without sacrificing utility.

**Independent Test**: Can be fully tested by running the evaluation script on a fixed subset of the GateMem dataset and verifying that the output CSV contains the three required metrics with non-null values.

**Acceptance Scenarios**:

1. **Given** the system outputs for 100 test queries, **When** the metric calculation module runs, **Then** it MUST compute an "Access Control" score representing the percentage of unauthorized data exposures prevented, calculated as `(1 - (empirical_leaks / total_unauthorized_attempts_in_ground_truth)) * 100`.
2. **Given** the system outputs for 100 test queries, **When** the metric calculation module runs, **Then** it MUST compute a "Forgetting" score representing the percentage of deleted data successfully suppressed, calculated as `(1 - (empirical_leaks_of_deleted_content / total_deleted_targets_in_ground_truth)) * 100`.
3. **Given** the system outputs for 100 test queries, **When** the metric calculation module runs, **Then** it MUST compute a "Utility" score representing the helpfulness of the answers compared to the baseline, measured via LLM-as-a-Judge evaluation.

---

### User Story 3 - Statistical Significance & Cost Profiling (Priority: P3)

The system must perform statistical testing (paired t-test or Wilcoxon) to compare the metrics between the baseline and gatekeeper systems, and profile the computational cost (latency, CPU memory) to ensure feasibility on free-tier runners.

**Why this priority**: This story provides the rigorous scientific validation and feasibility proof required to conclude the research, ensuring results are not due to chance and are deployable in resource-constrained environments.

**Independent Test**: Can be fully tested by running the analysis script on the full test set and verifying the generation of a p-value < 0.05 for the primary hypothesis (Access Control improvement) and a latency report within the 6-hour CI limit.

**Acceptance Scenarios**:

1. **Given** the Access Control scores for both baseline and gatekeeper systems across all domains, **When** the statistical analysis runs, **Then** it MUST output a p-value < 0.05 indicating whether the improvement in Access Control (primary hypothesis) is statistically significant.
2. **Given** the full execution logs, **When** the cost profiler runs, **Then** it MUST report the total inference latency and peak CPU memory usage for the gatekeeper-enhanced system.
3. **Given** the utility scores, **When** the analysis runs, **Then** it MUST verify that the utility drop is within the 10% margin, specifically checking that `baseline_utility - new_utility <= 0.10 * baseline_utility`.

---

### Edge Cases

- What happens when the GateMem dataset is incomplete or missing specific `leak-target` annotations for a test case? (System must log the missing annotation and exclude the case from the specific metric calculation, while reporting the exclusion count).
- How does the system handle a query that matches multiple conflicting rules (e.g., a role is authorized but the content is deleted)? (The gatekeeper MUST prioritize the deletion log over role authorization, enforcing the "forgetting" requirement).
- How does the system behave if the DistilBERT model inference exceeds the 6-hour CI time limit? (The system must detect the timeout and fail gracefully with a "Compute Exceeded" error, preventing a silent failure).

## Requirements

### Functional Requirements

- **FR-001**: The system MUST implement a pre-filtering gatekeeper module that intercepts queries and retrieves the active deletion log and role definitions before passing data to the retrieval engine. (See US-1)
- **FR-002**: The system MUST utilize a frozen DistilBERT model running in default precision on CPU to classify semantic intent for access control validation. (See US-1)
- **FR-003**: The system MUST enforce a deterministic rule engine that blocks any memory chunk flagged in the active deletion log, regardless of user role. (See US-1)
- **FR-004**: The system MUST calculate the Access Control score by comparing the number of *empirical unauthorized data exposures* detected in the LLM output against the total number of *unauthorized attempts defined in the GateMem ground-truth set*. (See US-2)
- **FR-005**: The system MUST calculate the Forgetting score by comparing the number of *empirical instances of deleted content appearing in the LLM output* against the total number of *deleted chunks targeted in the GateMem ground-truth set*. (See US-2)
- **FR-006**: The system MUST perform a paired statistical test (t-test or Wilcoxon) to compare the Access Control and Forgetting scores between the baseline and gatekeeper systems. (See US-3)
- **FR-007**: The system MUST measure and report the total inference latency and peak CPU memory usage for the entire pipeline execution. (See US-3)
- **FR-008**: The system MUST apply a multiple-comparison correction (e.g., Bonferroni or Holm-Bonferroni) when evaluating significance across the multiple domains (medical, office, education, household) to control family-wise error rate. (See US-3)
- **FR-009**: The system MUST include a sensitivity analysis that sweeps the semantic similarity threshold (confidence cutoff) for the DistilBERT classifier (e.g., {0.85, 0.90, 0.95}) and reports the variation in false-positive and false-negative rates against the ground-truth annotations. (See US-3)
- **FR-010**: The system MUST validate that the *frozen DistilBERT model* (as defined in FR-002) does not require GPU acceleration or quantization libraries (e.g., bitsandbytes) that are incompatible with CPU-only runners. (See US-1)
- **FR-011**: The system MUST calculate the Utility score by evaluating the LLM output against a standardized rubric using an LLM-as-a-Judge model, producing a normalized score between 0.0 and 1.0. (See US-2)
- **FR-012**: The system MUST include a "Leakage Detector" component that scans the final LLM output for strings matching the `leak-target` annotations in the ground truth to enable empirical measurement of Access Control and Forgetting scores. (See FR-004, FR-005)

### Key Entities

- **Query**: An input request from a user containing text and an associated user role.
- **Memory Chunk**: A segment of retrieved text from the shared memory index, containing metadata about its origin and access permissions.
- **Deletion Log**: A structured record of memory chunks that have been requested for deletion and must be suppressed.
- **Access Policy**: A set of rules defining which user roles can access which categories of memory data.
- **Metric Score**: A quantitative value (0.0 to 1.0) representing performance in Utility, Access Control, or Forgetting.
- **Leakage Detector**: A component that identifies if sensitive or deleted content from the ground truth appears in the LLM's generated response.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The reduction in unauthorized leakage (Access Control score) is measured against the baseline retrieval system's score using the GateMem dataset annotations as the ground truth. (See FR-004, FR-012)
- **SC-002**: The improvement in deletion compliance (Forgetting score) is measured against the baseline system's score using the `leak-target` annotations in the GateMem dataset, validated by empirical output analysis. (See FR-005, FR-012)
- **SC-003**: The change in retrieval utility is measured against the baseline system's utility score to ensure it does not degrade by more than 10% (i.e., `new_utility >= 0.90 * baseline_utility`). (See FR-011)
- **SC-004**: The statistical significance of the observed improvements is measured against a p-value threshold of 0.05, corrected for multiple comparisons across domains. (See FR-008)
- **SC-005**: The computational feasibility is measured against the constraint of completing the full inference and analysis pipeline within 6 hours on a 2-core CPU runner with ≤7 GB RAM. (See FR-010)
- **SC-006**: The robustness of the semantic threshold is measured by the variance in false-positive rates across the sensitivity sweep range of {0.85, 0.90, 0.95}. (See FR-009)

## Assumptions

- The GateMem dataset is publicly available and can be downloaded via the official repository without requiring proprietary credentials or paid access.
- The DistilBERT model used for intent classification is small enough to fit within the 7 GB RAM limit of the GitHub Actions free-tier runner when loaded in default precision.
- The "10% margin" for utility loss is a defensible community standard for acceptable trade-offs in security-critical AI systems, as no specific industry standard was provided in the idea.
- The GateMem dataset contains the necessary `leak-target` annotations and role definitions to accurately compute the Access Control and Forgetting metrics without requiring external data augmentation.
- The statistical power of the test is sufficient to detect a meaningful effect size with the existing GateMem test set size; if not, the analysis will report the observed effect size and confidence interval as a limitation.
- The "rule-based" component of the gatekeeper relies on regex patterns and logical checks that are deterministic and do not introduce non-deterministic variability in the results.
- The "Leakage Detector" (FR-012) is capable of identifying exact string matches and near-duplicates of sensitive content in the LLM output with sufficient accuracy to validate the hypotheses.