# Feature Specification: llmXive follow-up: extending "Heterogeneous Scientific Foundation Model Collaboration"

**Feature Branch**: `001-llmxive-cache-optimization`  
**Created**: 2026-07-11  
**Status**: Draft  
**Input**: User description: "How does the introduction of a semantic similarity-based caching mechanism affect the computational efficiency and scientific reasoning accuracy of the EywaOrchestra framework when processing iterative, multi-turn hypothesis-testing tasks?"

## User Scenarios & Testing

### User Story 1 - Semantic Cache Implementation and Hit-Rate Measurement (Priority: P1)

The system must implement a lightweight semantic caching layer that intercepts prompt queries, computes embeddings using a CPU-tractable model, and retrieves cached outputs when cosine similarity exceeds a defined threshold.

**Why this priority**: This is the core innovation. Without the cache mechanism itself, no efficiency gains can be measured. It establishes the baseline functionality required to test the research hypothesis.

**Independent Test**: Can be fully tested by running a batch of synthetic iterative queries (BenchmarkQuery entities) against the cache module in isolation. The test verifies that the observed hit-rate matches the theoretical probability distribution derived from the cosine similarity threshold and the semantic variance of the query set.

**Acceptance Scenarios**:

1. **Given** a set of 500 iterative sub-task queries (BenchmarkQuery entities) with varying input parameters, **When** the Semantic Cache module processes them with a threshold of 0.95, **Then** the system must record the total number of requests served from the cache and calculate the hit-rate percentage relative to the total requests.
2. **Given** a query with a semantic similarity score of 0.96 to a cached entry, **When** the system processes the query, **Then** the system must return the cached result and log the event as a "Cache Hit" without triggering a new model inference.
3. **Given** a query with a semantic similarity score of 0.90 to any cached entry, **When** the system processes the query, **Then** the system must bypass the cache, invoke the standard EywaOrchestra pipeline, and log the event as a "Cache Miss".

---

### User Story 2 - Efficiency and Accuracy Trade-off Quantification (Priority: P2)

The system must execute the EywaOrchestra pipeline on a benchmark dataset twice (with and without caching) and quantitatively compare the reduction in model invocations and runtime against the degradation in scientific reasoning accuracy.

**Why this priority**: This directly addresses the research question. It transforms the cache mechanism into empirical data, validating whether the efficiency gains come at an unacceptable cost to accuracy.

**Independent Test**: Can be fully tested by running the paired execution pipeline on the "Eywa" benchmark subset (BenchmarkQuery entities) and generating a report containing the exact percentage reduction in runtime, the exact percentage deviation in accuracy, and the results of the statistical significance tests (McNemar's test for accuracy, t-test for runtime).

**Acceptance Scenarios**:

1. **Given** the "Eywa" benchmark subset of 500 iterative tasks (BenchmarkQuery entities), **When** the system runs the pipeline with the Semantic Cache enabled, **Then** the system must record the total wall-clock time and calculate the percentage reduction relative to the baseline (non-cached) execution time.
2. **Given** the same benchmark subset, **When** the system compares the cached results against the independent ground-truth scientific outcomes, **Then** the system must calculate and report the percentage deviation in scientific reasoning accuracy relative to the baseline.
3. **Given** a statistical test configuration, **When** the system analyzes the data, **Then** it must output a p-value for runtime differences using a paired t-test and a p-value for accuracy differences using McNemar's test for paired proportions (significance level α = 0.05).

---

### User Story 3 - Threshold Sensitivity Analysis and Visualization (Priority: P3)

The system must perform a sensitivity analysis by sweeping the cosine similarity threshold across a defined range and visualize the resulting trade-off curve between cache hit-rate, runtime reduction, and accuracy degradation.

**Why this priority**: This provides the methodological robustness required to justify the chosen threshold. It ensures the results are not an artifact of a single arbitrary parameter choice and allows future users to tune the system for their specific constraints.

**Independent Test**: Can be fully tested by running the pipeline with thresholds set to {0.90, 0.95, 0.99} and verifying that the generated visualization correctly plots the three metrics (hit-rate, runtime, accuracy) against the threshold values, and that the optimal threshold is identified based on the defined optimization rule.

**Acceptance Scenarios**:

1. **Given** a set of thresholds {0.90, 0.95, 0.99}, **When** the system executes the sensitivity analysis, **Then** it must generate a CSV or JSON report detailing the hit-rate, runtime reduction, and accuracy deviation for each threshold.
2. **Given** the sensitivity analysis data, **When** the system generates the trade-off curve plot, **Then** the plot must clearly show the inflection point where accuracy degradation begins to exceed the 2% margin as the threshold decreases.
3. **Given** the analysis results, **When** a user reviews the output, **Then** they must be able to identify the optimal threshold that maximizes runtime reduction while keeping accuracy deviation ≤ 2%.

---

### Edge Cases

- What happens when the embedding model fails to compute a similarity score due to an input format error? (System must log the error, treat it as a cache miss, and proceed with standard inference).
- How does the system handle a scenario where the cache memory limit (e.g., 1GB) is exceeded during the 500-query run? (System must implement an LRU eviction policy or stop caching new entries, logging the event).
- What happens if the benchmark dataset contains ambiguous ground-truth outcomes where multiple scientific answers are valid? (System must use a fuzzy matching or tolerance-based comparison for accuracy evaluation, documented in the sensitivity analysis).

## Requirements

### Functional Requirements

- **FR-001**: System MUST implement a semantic caching module that computes cosine similarity between incoming prompt embeddings and cached entries using a CPU-tractable model (e.g., `all-MiniLM-L6-v2`) to ensure compatibility with free-tier CI environments. The module must process BenchmarkQuery entities. (See US-1)
- **FR-002**: System MUST execute the EywaOrchestra pipeline on the benchmark dataset (BenchmarkQuery entities) in two distinct modes: (a) standard execution without caching, and (b) execution with the semantic cache enabled, logging all metrics for comparison. (See US-2)
- **FR-003**: System MUST perform a sensitivity analysis by automatically running the pipeline with similarity thresholds set to a discrete set of values (e.g., a range of high-confidence thresholds) to validate the robustness of the efficiency-accuracy trade-off. (See US-3)
- **FR-004**: System MUST calculate and report the percentage reduction in specialized model invocations and total wall-clock time relative to the baseline, and the percentage deviation in scientific reasoning accuracy against ground-truth outcomes. (See US-2)
- **FR-005**: System MUST generate a visualization (e.g., line plot) depicting the trade-off curve between cache hit-rate, runtime reduction, and accuracy degradation across the tested similarity thresholds. (See US-3)
- **FR-006**: System MUST perform a paired t-test on the runtime metrics and McNemar's test on the accuracy metrics (binary success/failure outcomes) from the cached and non-cached runs to determine statistical significance (p < 0.05). (See US-2)
- **FR-007**: If the "Eywa" benchmark lacks independent ground-truth numerical outcomes, the system MUST implement a deterministic synthetic ground-truth generator that produces numerical outcomes with a precision of ≥ 0.01, validated against a subset of known analytical solutions (n ≥ 10). The synthetic generation logic MUST be epistemologically independent of the EywaOrchestra pipeline's heuristics. If independence cannot be verified, the system MUST flag the inability to perform a valid scientific accuracy test. (See US-2)
- **FR-008**: System MUST validate that the ground-truth source (whether external or synthetic) is independent of the EywaOrchestra pipeline's inference logic before calculating accuracy metrics. (See US-2)

### Key Entities

- **BenchmarkQuery**: Represents a single iterative sub-task from the "Eywa" dataset, containing the input prompt, expected ground-truth outcome, and metadata for the specific scientific domain. Used in US-1, US-2, FR-001, FR-002.
- **CacheEntry**: Represents a stored result in the semantic cache, containing the prompt embedding, the original output, and the timestamp of insertion.
- **ExecutionRun**: Represents a single execution of the pipeline (either cached or baseline), containing aggregated metrics for runtime, invocation count, and accuracy.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The reduction in specialized model invocations is measured against the baseline count from the non-cached execution run. (See FR-004, US-2)
- **SC-002**: The total wall-clock runtime reduction is measured against the baseline runtime from the non-cached execution run. (See FR-004, US-2)
- **SC-003**: The scientific reasoning accuracy deviation is measured against the independent ground-truth outcomes provided in the "Eywa" benchmark dataset or the validated synthetic generator. (See FR-004, FR-007, US-2)
- **SC-004**: The statistical significance of the performance differences is measured against the standard threshold of p < 0.05 via paired t-test (runtime) and McNemar's test (accuracy). (See FR-006, US-2)
- **SC-005**: The sensitivity of the system to threshold changes is measured by the variation in accuracy deviation and hit-rate across the discrete set of tested thresholds {0.90, 0.95, 0.99}. (See FR-005, US-3)

## Assumptions

- **Assumption about data availability**: The "Eywa" benchmark subset containing iterative tasks (e.g., multi-step chemical reaction prediction, climate variable correlation) is accessible via the official repository or supplementary materials associated with the arXiv paper (2604.27351) and fits within the 7GB RAM / 14GB disk constraints of the GitHub Actions free runner.
- **Assumption about compute environment**: The analysis will be executed on a GitHub Actions free-tier runner (limited CPU cores, ~7 GB RAM, no GPU), requiring all models (including the embedding model and Eywa components) to run in default precision on CPU without CUDA dependencies.
- **Assumption about threshold justification**: The initial similarity threshold of 0.95 is selected based on community standards for semantic similarity in retrieval tasks, and the sensitivity analysis (FR-003) will empirically validate or adjust this value.
- **Assumption about independence**: The ground-truth scientific outcomes in the benchmark are independent of the prompt embeddings and the cache mechanism, ensuring that accuracy evaluation is not circular.
- **Assumption about dataset-variable fit**: The "Eywa" benchmark contains all necessary variables (input prompts, ground-truth outcomes) to evaluate the efficiency and accuracy of the caching mechanism; no additional external data sources are required.
- **Hypothesis on Performance**: The research hypothesis posits that the semantic caching mechanism will achieve a hit-rate of ≥ 40% at a 0.95 threshold, resulting in a ≥ 40% reduction in wall-clock runtime, while maintaining accuracy deviation ≤ 2%. These values are targets for validation, not functional requirements.
- **Hypothesis on Ground Truth**: The "Eywa" benchmark dataset contains specific ground-truth numerical outcomes for all 500 generated iterative sub-tasks. If the official repository provides only qualitative outcomes, the synthetic ground-truth generator (FR-007) will be used, subject to the independence constraint.

# Panel concerns to address (R1 output)

- [concern internal_consistency-9e31d841] severity=requirement reviewer=internal_consistency location=spec.md:User Story 1, Acceptance Scenario 1
 Contradiction in empirical values: US-1 Acceptance Scenario 1 mandates 'at least 40% of requests' served from cache with a 0.95 threshold. However, the 'Expected results' section in the Idea Md and the 'Assumptions' section in the spec claim a [deferred] reduction in invocations (implying [deferred] hit-rate) and a [deferred] runtime reduction. The spec sets a hard acceptance criterion ([deferred] hit-rate) that conflicts with the projected research outcome ([deferred] hit-rate) without clarifying if the 40% is a minimum viable threshold or a target. Furthermore, US-2 Acceptance Scenario 1 sets a [deferred] runtime reduction target, which is numerically identical to the US-1 hit-rate target, creating ambiguity on whether these are independent metrics or conflated.
- [concern internal_consistency-bb994c64] severity=requirement reviewer=internal_consistency location=spec.md:User Story 3, Acceptance Scenario 3
 Unresolved placeholder in acceptance criteria: US-3 Acceptance Scenario 3 states 'keeping accuracy deviation below [deferred]'. While the spec template allows deferring empirical values, the surrounding text in US-2 and the 'Expected results' section explicitly define a 2% margin. Using '[deferred]' here creates a contradiction with the established [deferred] constraint found in US-2 Acceptance Scenario 2 and the 'Expected results' section, leaving the acceptance criteria for the optimal threshold undefined.
- [concern internal_consistency-1f2d7f1b] severity=writing reviewer=internal_consistency location=spec.md:Assumptions (last bullet)
  Inconsistent terminology and scope: The assumption states 'The 'Eywa' benchmark dataset is assumed to contain specific ground-truth numerical outcomes... If the official repository provides only qualitative outcomes... the system MUST implement a deterministic synthetic ground-truth generator'. This shifts the scope from 'benchmarking' to 'synthetic data generation' without a corresponding User Story or Functional Requirement explicitly mandating the *generation* logic (FR-004 only mentions calculating deviation against ground-truth). The requirement to generate synthetic data is buried in an assumption rather than defined as a functional capability.
- [concern internal_consistency-61f90d86] severity=writing reviewer=internal_consistency location=spec.md:Key Entities
  Terminology inconsistency: The 'Key Entities' section defines 'BenchmarkQuery' and 'CacheEntry', but the 'User Scenarios' and 'Functional Requirements' frequently refer to 'iterative sub-task queries' and 'prompt queries' without explicitly linking them to the 'BenchmarkQuery' entity. While likely implied, the lack of explicit cross-referencing (e.g., 'See BenchmarkQuery') creates a minor disconnect between the data model and the functional descriptions.
- [concern testability-1c895a76] severity=requirement reviewer=testability location=spec.md:User Story 1 - Acceptance Scenario 1
  Acceptance Scenario 1 states: 'Then the system must serve at least 40% of requests from the cache'. This sets a specific empirical threshold (40%) in the spec. Per the 'Measurable Outcomes' note and Constitution Principle I, planning docs must defer specific empirical values to the implementation phase. The criterion is currently untestable because the target value is arbitrary and not derived from a baseline or hypothesis in the spec itself. It should be rephrased to measure the *actual* hit-rate against the *expected* distribution defined by the threshold, or the 40% should be moved to a hypothesis section, not an acceptance criterion.
- [concern testability-d6692cd4] severity=requirement reviewer=testability location=spec.md:User Story 2 - Acceptance Scenario 1
 Acceptance Scenario 1 states: 'Then the total wall-clock time must be at least 40% lower than the baseline'. Similar to US-1, this imposes a specific empirical target ([deferred] reduction) as a pass/fail criterion. This is untestable as a functional requirement because the spec does not define the baseline performance or the conditions under which this [deferred] is guaranteed. It conflates a research hypothesis with a functional acceptance criterion. It should be changed to: 'Then the system must record the wall-clock time and calculate the percentage reduction relative to the baseline'.
- [concern testability-5df1731e] severity=requirement reviewer=testability location=spec.md:User Story 2 - Acceptance Scenario 2
 Acceptance Scenario 2 states: 'Then the accuracy... must remain within 2% of the baseline'. This sets a specific empirical threshold (2%) as a pass/fail criterion. Without a pre-defined baseline accuracy or a statistical power analysis in the spec, this is an unmeasurable success criterion for the *spec* stage. It should be rephrased to require the *measurement* and *reporting* of the deviation, leaving the '[deferred]' as a hypothesis to be tested, not a hard requirement for the system to meet.
- [concern testability-0ea43688] severity=requirement reviewer=testability location=spec.md:User Story 3 - Acceptance Scenario 3
  Acceptance Scenario 3 states: 'Then they must be able to identify the optimal threshold... while keeping accuracy deviation below [deferred]'. The use of '[deferred]' here makes the criterion untestable. A human judge cannot verify if the user 'can identify' a threshold if the constraint (accuracy deviation) is undefined. The spec must define the *method* for identifying the optimal threshold (e.g., 'maximize runtime reduction subject to accuracy deviation < X') or remove the specific constraint from the acceptance scenario, replacing it with 'report the trade-off curve'.
- [concern testability-8d3e0840] severity=writing reviewer=testability location=spec.md:User Story 1 - Independent Test
  The 'Independent Test' mentions 'verifying that the hit-rate... matches the expected distribution'. The spec does not define what this 'expected distribution' is. To be verifiable, the test procedure must specify how this distribution is derived (e.g., 'based on the theoretical probability of cosine similarity > 0.95 for the given query set') or remove the reference to 'expected distribution' and focus on the mechanical verification of the cache hit logic.
- [concern scope-0d455d22] severity=requirement reviewer=scope location=spec.md:User Story 1 - Acceptance Scenario 1
 US-1 Acceptance Scenario 1 mandates 'at least 40% of requests' served from cache. The idea's 'Expected results' section projects a [deferred] reduction in invocations (implying [deferred] hit-rate). Hard-coding a 40% acceptance threshold in the spec creates a potential conflict with the research hypothesis (which expects [deferred]) and risks validating a sub-optimal outcome as 'success' without justification. The spec should defer this specific empirical target or align it with the hypothesis range.
- [concern scope-9d21ec3a] severity=requirement reviewer=scope location=spec.md:User Story 2 - Acceptance Scenario 1
 US-2 Acceptance Scenario 1 mandates 'total wall-clock time must be at least 40% lower'. Similar to US-1, this hard-codes a specific efficiency target ([deferred]) that matches the 'Expected results' but contradicts the 'Methodology sketch' which suggests a pilot to determine the optimal threshold. If the pilot shows only [deferred] reduction, the spec's acceptance criteria would fail the project despite valid scientific findings. This empirical value should be deferred to the implementation phase or framed as a hypothesis to be tested, not a hard requirement.
- [concern scope-c0d5edd5] severity=requirement reviewer=scope location=spec.md:User Story 3 - Acceptance Scenario 3
 US-3 Acceptance Scenario 3 states the user must identify the optimal threshold keeping accuracy deviation below '[deferred]'. While '[deferred]' is a sanctioned marker, the context implies a specific numerical bound (likely the [deferred] mentioned in US-2) is missing. The spec should explicitly reference the 2% margin from US-2 or clarify that the bound is the variable being optimized, rather than leaving it as an ambiguous placeholder in a critical acceptance criterion.
- [concern scientific_soundness-7a1fc2dd] severity=science reviewer=scientific_soundness location=spec.md:User Story 2, Acceptance Scenario 2
  The validation target 'accuracy' is defined by comparing cached results against 'ground-truth scientific outcomes'. However, the cache mechanism retrieves *pre-computed* outputs from the EywaOrchestra pipeline. If the 'ground-truth' is merely the output of the non-cached pipeline (as implied by the 'baseline' comparison in SC-001/SC-002), the validation is circular: it tests if the cache returns the same answer the pipeline *would have* given, not if the answer is scientifically correct. The spec must explicitly define 'ground-truth' as an independent, external scientific reference (e.g., analytical solutions, experimental data, or a verified oracle) distinct from the EywaOrchestra model's own inference, otherwise the 'accuracy' metric is tautological.
- [concern scientific_soundness-5294bca5] severity=science reviewer=scientific_soundness location=spec.md:Assumptions (last bullet)
  The assumption states: 'The 'Eywa' benchmark dataset is assumed to contain specific ground-truth numerical outcomes... If... only qualitative outcomes... the system MUST implement a deterministic synthetic ground-truth generator'. This introduces a fatal circularity risk. If the 'ground-truth' is synthetically generated by a deterministic function, and the EywaOrchestra pipeline (or the cache) is evaluated against it, the 'accuracy' metric becomes a measure of how well the system matches a known function, not its scientific reasoning capability. If the EywaOrchestra pipeline itself uses similar heuristics or models to generate the 'synthetic' truth, the validation is trivial. The spec must ensure the 'ground-truth' source is epistemologically independent of the system being tested.
- [concern scientific_soundness-b8edecfa] severity=methodology reviewer=scientific_soundness location=spec.md:User Story 2, Acceptance Scenario 3
  The spec mandates a 'paired t-test' on 'runtime and accuracy metrics'. While appropriate for runtime (continuous), applying a t-test to 'accuracy' (a proportion/success rate derived from 500 binary outcomes) is statistically suboptimal. A paired t-test assumes normally distributed differences in continuous variables. For binary success/failure data, a McNemar's test or a bootstrap confidence interval for the difference in proportions is the standard methodological approach in this field. Using a t-test on proportions may violate assumptions of normality and independence of errors, leading to invalid p-values.

# Remaining `[NEEDS CLARIFICATION]` markers

(no `[NEEDS CLARIFICATION]` markers remain)

# Recent reviewer / personality comments

(no recent comments)