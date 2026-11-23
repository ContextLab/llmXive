# Feature Specification: llmXive follow-up: extending "TransitLM: A Large-Scale Dataset and Benchmark for Map-Free Transit Ro"

**Feature Branch**: `001-transitlm-cognitive-horizon`  
**Created**: 2026-08-03  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending TransitLM to determine the route length and topological complexity threshold where local station adjacency statistics fail to uniquely determine valid global transit paths."

## User Scenarios & Testing

### User Story 1 - Local vs. Global Performance Threshold Identification (Priority: P1)

**User Journey**: As a researcher, I want to evaluate the lightweight, encoder-only retrieval-augmented model against the original LLM baseline across stratified route lengths (short, medium, long) so that I can identify the specific "cognitive horizon" where local adjacency statistics become insufficient for valid global path generation.

**Why this priority**: This is the core scientific objective of the project. Without establishing the inflection point where performance degrades, the hypothesis regarding "implicit grounding" remains untested.

**Independent Test**: The system can be tested by running the evaluation pipeline on the stratified test set and generating a performance comparison report that clearly shows the divergence in route validity between the lightweight model and the LLM baseline at specific stop counts.

**Acceptance Scenarios**:

1. **Given** a test set stratified into short-haul (<15 stops), medium-haul (15-30 stops), and long-haul (>30 stops), **When** the evaluation script runs the lightweight model and the LLM baseline on all categories, **Then** the output report MUST display route validity percentages for each category and identify the specific route length (inflection point) where the lightweight model's validity drops below the LLM baseline by a margin of ≥15%.
2. **Given** a specific route length of 25 stops, **When** the system predicts the next station using only local adjacency statistics, **Then** the system MUST flag the prediction as "high risk of global context failure" if the route validity for this length in the stratified analysis falls below the LLM baseline validity for that category (measured empirically on the identical stratified test set) minus the 95% confidence interval lower bound of the baseline validity for that category.

---

### User Story 2 - Statistical Significance of Topological Limits (Priority: P2)

**User Journey**: As a researcher, I want to apply a Kaplan-Meier survival analysis to the route validity decay across route-length categories so that I can statistically confirm whether the observed performance degradation is a significant effect of topological complexity rather than random variance, accounting for the cumulative nature of route validity.

**Why this priority**: Scientific rigor requires that the observed "threshold" is statistically significant. Treating route validity as a cumulative survival probability addresses the independence violation inherent in chi-squared tests for sequential data.

**Independent Test**: The system can be tested by executing the statistical analysis module and verifying that a survival curve is generated with a log-rank test p-value comparing the lightweight model and the baseline.

**Acceptance Scenarios**:

1. **Given** the route validity status (valid/invalid at each hop) for both the lightweight model and the LLM baseline across the route lengths, **When** the Kaplan-Meier survival analysis is executed, **Then** the system MUST output survival curves and a log-rank test p-value indicating whether the difference in route survival probability is statistically significant (p < 0.05). Routes truncated by the model or reaching the maximum hop count without error are censored at the final observed hop.
2. **Given** a scenario where the lightweight model performs equally well across all categories, **When** the test is run, **Then** the system MUST report a non-significant result (p ≥ 0.05) and flag that no "cognitive horizon" was detected within the tested range.

---

### User Story 3 - Resource Feasibility and Edge-Device Simulation (Priority: P3)

**User Journey**: As a deployment engineer, I want to profile the inference latency and memory usage of the lightweight model on a simulated 2-core CPU environment so that I can verify the model is viable for edge devices without requiring GPU acceleration.

**Why this priority**: The project's motivation hinges on the ability to replace heavy LLMs with efficient CPU-based models. If the lightweight model fails to run within resource constraints, the practical value of the research is nullified.

**Independent Test**: The system can be tested by running the model inference on a GitHub Actions free-tier runner (simulating the target environment) and logging the peak memory usage and average inference time per route.

**Acceptance Scenarios**:

1. **Given** a standard test route of 20 stops, **When** the model performs inference on a 2-core CPU environment with ≤7 GB RAM, **Then** the process MUST complete within 60 seconds and consume no more than 4 GB of RAM.
2. **Given** a memory limit of 7 GB, **When** the model loads the vocabulary-restricted dataset and the encoder, **Then** the system MUST NOT trigger an Out-Of-Memory (OOM) error.

---

### Edge Cases

- What happens when the test set contains routes that are longer than 30 stops but the model's training data only covers up to 25 stops? (The system MUST handle this by excluding such routes from the "long-haul" analysis or flagging them as "out-of-distribution" to prevent invalid extrapolation).
- How does the system handle stations that are mapped to the `<UNKNOWN>` token due to the top-N station vocabulary restriction (N deferred)? (The system MUST treat `<UNKNOWN>` as a valid but low-confidence prediction and exclude it from "station validity" metrics unless the ground truth also contains `<UNKNOWN>`).
- What if the survival analysis assumptions (e.g., proportional hazards) are violated? (The system MUST report a diagnostic warning and fall back to a non-parametric comparison of median survival lengths).

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and preprocess the TransitLM SFT dataset, filtering for the four Chinese cities and applying a top-N station vocabulary restriction (N deferred, default set to a sufficient magnitude per Idea) (See US-1).
- **FR-002**: System MUST implement a lightweight, encoder-only retrieval-augmented model capable of predicting the next station using local adjacency statistics retrieved from a pre-indexed graph without GPU acceleration (See US-1).
- **FR-003**: System MUST stratify the test set into short-haul (<15 stops), medium-haul (15-30 stops), and long-haul (>30 stops) categories and compute route validity for each (See US-1).
- **FR-004**: System MUST execute a Kaplan-Meier survival analysis (with log-rank test) to compare the probability of route validity between the lightweight model and the LLM baseline across route lengths, using an empirical baseline run on the same stratified test set (See US-2).
- **FR-005**: System MUST profile inference latency and memory usage on a 2-core CPU environment to verify compliance with the ≤60s time and ≤7GB RAM constraints (See US-3).
- **FR-006**: System MUST handle `<UNKNOWN>` tokens gracefully by excluding them from station validity metrics or treating them as a distinct low-confidence category (See US-1).
- **FR-007**: System MUST apply a multiple-comparison correction (e.g., Bonferroni) if multiple hypothesis tests are conducted across different city networks to control family-wise error rate, ensuring the statistical significance claims in US-2 are robust (See US-2).
- **FR-008**: System MUST validate the "local adjacency" graph derived from the training data against the TransitLM ground truth to ensure completeness (edge overlap ≥95%) before analysis, ensuring the 'local adjacency' construct is sound for US-1 (See US-1).
- **FR-009**: System MUST compute an independent measure of topological complexity (e.g., path-level betweenness centrality calculated on the local adjacency subgraph) for each route to distinguish between local edge coverage and global reasoning limits, as requested in US-1 (See US-1).

### Key Entities

- **Route**: A sequence of station IDs representing a transit path, with attributes for `start_station`, `end_station`, `stop_count`, `validity_score`, and `topological_complexity`.
- **Station**: A unique identifier for a transit stop, mapped to either a specific ID or the `<UNKNOWN>` token based on frequency.
- **AdjacencyGraph**: A pre-indexed graph structure containing local adjacency edges retrieved for the model, used for FR-002 and FR-009.
- **ModelOutput**: The predicted next station and confidence score generated by the lightweight model for a given context.
- **StatisticalResult**: The output of the survival analysis, including `survival_curve`, `log_rank_p_value`, and `median_survival_length`.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The inflection point is defined as the shortest route length where the lightweight model's validity is statistically significantly lower than the baseline (p < 0.05) AND the absolute drop is ≥15% (minimum effect size of practical significance), measured against the stratified route-length categories (See FR-003, FR-004).
- **SC-002**: The difference in route survival probability between models is measured against the null hypothesis of equal survival curves using a log-rank test (See FR-004).
- **SC-003**: Inference latency and peak memory usage are measured against the 60-second and 7 GB RAM constraints of the GitHub Actions free-tier runner (See FR-005).
- **SC-004**: The rate of `<UNKNOWN>` token predictions is measured against the total number of predictions to assess the impact of vocabulary restriction on model performance (See FR-006).
- **SC-005**: The adjusted p-values resulting from the multiple-comparison correction must be reported and compared to the nominal alpha level to determine significance. (See FR-007).
- **SC-006**: The completeness of the local adjacency graph is measured against the TransitLM ground truth as 'edge overlap percentage' (target ≥95%) to validate the ground truth (See FR-008).

## Assumptions

- The TransitLM SFT dataset is publicly available and contains sufficient data for the four Chinese cities to support stratified analysis without significant data sparsity.
- The "local adjacency statistics" derived from the training corpus are representative of the true topological structure of the transit networks in the test set, provided that the graph is validated against the TransitLM ground truth (see FR-008).
- The top-N station vocabulary restriction (N deferred, default set to a sufficient magnitude per Idea) is sufficient to capture the majority of high-frequency transitions while keeping memory usage within the 7 GB RAM limit.
- The lightweight encoder-only model architecture (e.g., distilled BERT-base) is capable of learning the necessary next-hop prediction patterns on CPU-only hardware within the standard CI job time limit.
- The survival analysis assumptions (proportional hazards) will be met for the majority of comparisons; if not, a non-parametric fallback will be used.
- The "cognitive horizon" threshold, if it exists, will fall within the tested range of 0 to 30+ stops; if no threshold is found, the result will be interpreted as "local statistics suffice for the tested range."
- The original LLM baseline performance metrics are available or can be reliably reproduced from the TransitLM paper for comparison, but the baseline MUST be run empirically on the same stratified test set for the survival analysis.
- The GitHub Actions free-tier runner provides consistent multi-core CPU performance and 7 GB RAM availability for the duration of the job.
- The TransitLM ground truth is the authoritative source for route validity and local adjacency validation.