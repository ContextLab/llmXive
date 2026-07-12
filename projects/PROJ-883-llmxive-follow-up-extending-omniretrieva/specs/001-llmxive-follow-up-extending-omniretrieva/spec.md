# Feature Specification: llmXive Follow-up: Structural Mismatch Cost in Heterogeneous Retrieval

**Feature Branch**: `001-structural-mismatch-cost`  
**Created**: 2026-07-10  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'OmniRetrieval: Unified Retrieval across Heterogeneous Knowledge Source'"

## User Scenarios & Testing

### User Story 1 - Quantify Latency Penalties of High-Complexity Queries on CPU (Priority: P1)

**Description**: As a system architect evaluating edge deployment, I need to measure the end-to-end latency difference between low-complexity (single-hop) and high-complexity (multi-hop/recursive) queries when executed on a strictly CPU-constrained environment, so that I can determine the non-linear scaling of the "structural mismatch cost" for graph-based sources.

**Why this priority**: This is the core research question. Without quantifying the latency gap between complexity levels, the hypothesis regarding structural mismatch costs cannot be validated or refuted.

**Independent Test**: Can be fully tested by executing a predefined set of synthetic queries (partitioned by plan depth) against a simulated CPU-throttled environment and recording the mean latency difference between the two complexity groups.

**Acceptance Scenarios**:

1. **Given** a dataset of 500 queries partitioned into "low" (depth 1-2) and "high" (depth 3+) complexity, **When** executed on a 2-core CPU with 7GB RAM limit, **Then** the system must record end-to-end latency for every query instance.
2. **Given** the recorded latency data, **When** a Generalized Additive Model (GAM) is performed to test for non-linear interaction effects, **Then** the system must output the p-value and 95% confidence interval for the interaction term between query complexity and source type.

---

### User Story 2 - Measure Translation Error Rates Under Resource Constraints (Priority: P2)

**Description**: As a reliability engineer, I need to track the frequency of translation errors (incorrect source selection or malformed execution plans) when the unified router operates under CPU throttling, so that I can verify if the accuracy penalty correlates with query complexity or remains stable.

**Why this priority**: The hypothesis posits that latency increases while accuracy remains stable. Validating this distinction is critical to proving the bottleneck is *translation overhead* rather than *retrieval capability*.

**Independent Test**: Can be fully tested by comparing the ground-truth execution plan for a query (derived from an independent, deterministic, exhaustive, rule-based solver) against the system's generated plan for the same query under load, counting mismatches.

**Acceptance Scenarios**:

1. **Given** a query with a known ground-truth execution plan (from a deterministic, exhaustive, rule-based solver), **When** the system generates a plan under CPU throttling, **Then** the system must log whether the generated plan matches the ground truth (success) or deviates (error).
2. **Given** a set of 100 high-complexity graph queries, **When** processed, **Then** the system must report a translation error rate that can be compared against the error rate of low-complexity queries.

---

### User Story 3 - Visualize Non-Linear Scaling and Interaction Effects (Priority: P3)

**Description**: As a data analyst, I need to generate interaction plots showing latency vs. query complexity for each source type (text, relational, graph), so that I can visually demonstrate the "structural mismatch cost" and identify specific complexity thresholds where latency spikes.

**Why this priority**: Visualization is the primary output for the research paper. It transforms raw statistical data into the evidence required to support the "non-linear increase" claim.

**Independent Test**: Can be fully tested by generating a plot file (e.g., PNG/PDF) where the X-axis is query complexity, Y-axis is latency, and lines are grouped by source type.

**Acceptance Scenarios**:

1. **Given** the aggregated latency data grouped by source type and complexity level, **When** the visualization script runs, **Then** it must produce a plot where the interaction effect between source type and complexity is clearly visible.
2. **Given** the plot, **When** reviewed, **Then** it must clearly display the intersection point or threshold where the latency gap between low and high complexity widens significantly for graph sources.

---

### Edge Cases

- **What happens when** a query complexity exceeds the maximum recursion depth supported by the synthetic generator? (System should drop the query or cap the depth and log a warning, not crash).
- **How does the system handle** a native execution engine (e.g., SPARQL) that fails to respond within the enforced 60-second timeout? (The query should be recorded as a "timeout" failure, counted as a latency outlier, and not block the batch).
- **What happens when** the simulated CPU throttling (`cgroups`) fails to apply correctly due to container permissions? (The test suite must detect the lack of throttling and fail the run with a specific error code, preventing invalid data collection).

## Requirements

### Functional Requirements

- **FR-001**: System MUST execute synthetic queries against heterogeneous sources (Text, Relational, Graph) while enforcing a strict CPU time limit per query and a bounded memory cap. (See US-1)
- **FR-002**: System MUST classify every input query into "low-complexity" (plan depth ≤ 2) or "high-complexity" (plan depth ≥ 3) based on the parsed query plan structure. (See US-1)
- **FR-003**: System MUST record the end-to-end latency (in milliseconds) for every query attempt, distinguishing between successful execution and timeout failures. (See US-1)
- **FR-004**: System MUST compare the generated execution plan against a ground-truth plan derived from an independent, deterministic, exhaustive, rule-based solver to calculate a binary translation error (0=match, 1=mismatch) for every query. (See US-2)
- **FR-005**: System MUST perform a Generalized Additive Model (GAM) regression to test for non-linear interaction effects between "query complexity" (continuous) and "source type" (categorical) on the dependent variable "latency". The system MUST output the p-value and 95% confidence interval for the interaction term. (See US-1)
- **FR-006**: System MUST generate an interaction plot visualizing latency vs. complexity for each source type, explicitly highlighting the slope difference for graph sources. (See US-3)
- **FR-007**: System MUST implement a sensitivity analysis for the complexity threshold, sweeping the depth cutoff over the initial mandatory values {2, 3, 4} and outputting a JSON object for each cutoff containing: `{"cutoff": <int>, "spike_point": <float>, "slope_change": <float>}`. (See US-1)
- **FR-008**: System MUST utilize a deterministic, exhaustive, rule-based reference engine to generate independent ground-truth execution plans for all query types, ensuring that translation error measurement is not circular. (See US-2)

### Key Entities

- **Query Instance**: Represents a single retrieval request, containing attributes: `query_id`, `logical_plan`, `source_type`, `complexity_level`, `ground_truth_plan`.
- **Execution Metric**: Represents the outcome of a query run, containing attributes: `query_id`, `latency_ms`, `translation_error` (boolean), `timeout_flag` (boolean).
- **Source Engine**: Represents the native execution environment (e.g., SQLite, SPARQL endpoint, Elasticsearch), containing attributes: `engine_type`, `throttling_config`.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The non-linear latency scaling of graph queries is confirmed if the interaction term p-value in the GAM model is < 0.05 and the interaction term coefficient is positive, indicating a statistically significant non-linear interaction effect between query complexity and source type. (See US-1)
- **SC-002**: The translation error rate for high-complexity queries is measured by calculating the absolute difference in error rates between low and high complexity groups; this difference is reported with a 95% confidence interval to assess stability. (See US-2)
- **SC-004**: The robustness of the identified complexity threshold is measured against the sensitivity analysis results (sweeping cutoffs 2, 3, 4) to ensure the "spike" is not an artifact of a single arbitrary cutoff. (See US-1)

## Assumptions

- **Assumption about data/environment**: Public datasets (MS MARCO subset, Spider benchmark subset, DBpedia/Wikidata subset) are available via HuggingFace/GitHub/Zenodo and can be downloaded and loaded into the 7GB RAM limit without requiring full dataset ingestion; sampling strategies will be used if necessary.
- **Assumption about scope boundaries**: The "unified router" logic is simulated using a lightweight Python script; the focus is strictly on the *execution* latency and *translation* overhead, not on training new models or optimizing the router's internal neural architecture.
- **Assumption about target users**: The primary output is a research artifact (data and plots) for the academic community, not a production-ready API for end-users.
- **Assumption about compute constraints**: The GitHub Actions free-tier runner (multi-core CPU, sufficient RAM) is sufficient to run the synthetic query generator, the lightweight SQL/SPARQL engines, and the statistical analysis (scipy/statsmodels) within the 6-hour job limit, provided no GPU-dependent libraries are imported.
- **Assumption about dataset-variable fit**: The selected subsets of MS MARCO, Spider, and DBpedia contain the necessary structural metadata (e.g., join keys, graph edges) to construct valid high-complexity synthetic queries. If a specific dataset lacks required structural depth, the rule-based synthetic query generator serves as the mandatory fallback to ensure structural depth is always available. This generator constructs queries *matching the required structural depth parameters* (e.g., exact depth 3, 4, etc.) while randomizing other parameters (result-set sizes, syntax complexity) to ensure the 'complexity' label is a controlled independent variable and not confounded by other structural features.
- **Assumption about inference framing**: Since the study uses synthetic queries and controlled throttling (observational in the sense of no random assignment to "hardware" but experimental in query generation), findings regarding latency penalties are framed as associational measurements of system behavior under constraint, not causal claims about general hardware performance across all possible workloads.
- **Assumption about measurement validity**: The "ground truth" execution plans are generated by an independent, deterministic, exhaustive, rule-based solver (FR-008), ensuring the validity of the translation error metric is established by the method of independent comparison, while the empirical error rate is measured at runtime.
- **Assumption about statistical methodology**: The research hypothesis posits a "non-linear" increase in latency, which necessitates the use of Generalized Additive Models (GAM) to model smooth interaction effects. A standard two-way ANOVA is insufficient for this hypothesis as it assumes linear main effects and cannot capture non-linear smooth terms. Therefore, GAM is the mandated statistical approach, aligning with Constitution Principle VII's requirement to match the method to the research question.