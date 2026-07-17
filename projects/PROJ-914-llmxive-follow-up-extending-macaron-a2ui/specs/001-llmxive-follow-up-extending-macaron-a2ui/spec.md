# Feature Specification: llmXive follow-up: extending "Macaron-A2UI: A Model for Generative UI in Personal Agents"

**Feature Branch**: `001-llmxive-a2ui-latency-study`  
**Created**: 2026-07-15  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'Macaron-A2UI: A Model for Generative UI in Personal Agents'"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Ingestion and Intent Annotation (Priority: P1)

The system must ingest the A2UI-Bench dataset and provide an integrated manual annotation interface for researchers to label N=500 interaction turns as "High-Confidence" or "Ambiguous" to create the ground truth for training the router.

**Why this priority**: Without a labeled dataset, the router cannot be trained, and the hybrid system cannot distinguish between intents. This is the foundational data layer required for all subsequent analysis.

**Independent Test**: This story is complete when a CSV file exists containing N=500 rows with columns for `query`, `ground_truth_intent`, and `complexity_score`, validated by a script that checks for ≥95% coverage of the target sample size and no missing labels. The sample size N=500 is determined by a power calculation (power ≥ 0.8, α=0.05, effect size d=0.5) to detect a medium effect in alignment scores.

**Acceptance Scenarios**:

1. **Given** the raw A2UI-Bench dataset is available, **When** the ingestion script processes 500 random interaction turns, **Then** the output file contains 500 annotated records with valid intent labels.
2. **Given** the annotation interface, **When** a researcher labels a query as "Ambiguous" due to novel synthesis requirements, **Then** the record is stored with the specific complexity metadata required for the density analysis.

---

### User Story 2 - Hybrid Routing and Latency Simulation (Priority: P2)

The system must implement a routing pipeline that uses a lightweight CPU-optimized classifier to direct queries to either a generative model (for High-Confidence) or a deterministic rule-based generator (for Ambiguous). The "Ambiguous" state covers both complex intents and ontology mismatches. The system must also artificially inject latency steps (ranging from negligible to significant) to simulate network/compute variance, while modeling user patience (exponential decay, mean=2s) and cancellation behavior.

**Why this priority**: This is the core experimental engine. It allows the investigation of the non-linear relationship between delay and user trust by varying the system's response time, generation path, and user abandonment.

**Independent Test**: This story is complete when a simulation run processes a batch of queries, logs the routing decision, the actual generation time, the *injected* latency, and the *user abandonment* event (if any), producing a log file where the total response time equals `generation_time + injected_latency` (or `abandonment_time` if cancelled).

**Acceptance Scenarios**:

1. **Given** a query labeled "High-Confidence", **When** the system routes it, **Then** it invokes a large-scale generative model and records the generation latency.
2. **Given** a query labeled "Ambiguous", **When** the system routes it, **Then** it invokes the deterministic rule-based generator. If no ontology match is found, it returns a safe, minimal fallback UI (element) and logs the "no-match" event.
3. **Given** a specific latency step (e.g., 200ms), **When** the simulation runs, **Then** the recorded total latency for that step is within ±10ms of the target injected value.
4. **Given** a latency delay exceeding the user's patience threshold (modeled as exponential decay, mean=2s), **When** the simulation runs, **Then** the system records a "user abandon" event and sets the alignment score to 0 for that trial.
5. **Given** the router's confidence score, **When** the sensitivity analysis runs, **Then** it sweeps the confidence cutoff over a range of high thresholds and reports the variation in inconsistency rates.

---

### User Story 3 - Alignment Scoring and Pareto Analysis (Priority: P3)

The system must calculate task success rates, latency metrics, and alignment scores (based on the "Human-Agent Alignment" rubric) for all configurations, then generate a Pareto frontier plot showing the trade-off between alignment and latency. The system must identify the latency threshold where generative fidelity degrades using a statistical test.

**Why this priority**: This story delivers the primary research output: the quantification of the "minimum viable" deterministic interface and the identification of the latency threshold where generative fidelity degrades.

**Independent Test**: This story is complete when a report is generated containing the Pareto frontier plot and a table showing the alignment score for each information density level (low, medium, and high element counts) across all latency steps. The threshold must be identified via a statistical test (non-overlapping confidence intervals).

**Acceptance Scenarios**:

1. **Given** the simulation logs from multiple runs with varying information densities, **When** the analysis script runs, **Then** it calculates the alignment score for each configuration using the predefined rubric.
2. **Given** the calculated metrics, **When** the plot is generated, **Then** it clearly displays the Pareto frontier where the hybrid model outperforms both pure baselines in the high-latency regime.
3. **Given** the threshold analysis, **When** the results are aggregated, **Then** the specific latency threshold is identified as the first step where the 95% confidence interval of the generative baseline's alignment score drops below the lower bound of the hybrid model's interval (p < 0.05).

### Edge Cases

- What happens if the B parameter model fails to load on the CPU-only environment? (System must fallback to a smaller distilled model or abort with a clear error).
- How does the system handle queries that are borderline between "High-Confidence" and "Ambiguous" where the router's confidence score is near the decision boundary? (The system must log the confidence score and allow for a sensitivity analysis on the router threshold).
- What if the deterministic rule-based generator cannot find a matching ontology entry for an "Ambiguous" query? (The system must return a safe, minimal fallback UI (1 element) and log the "no-match" event for safety analysis. This is treated as an "Ambiguous" case with a specific sub-flag).
- What happens if the user cancels the request due to high latency? (The system must record an "abandonment" event and set the alignment score to 0 for that trial).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide a manual annotation interface to label N=500 interaction turns as "High-Confidence" or "Ambiguous" to establish ground truth (See US-1).
- **FR-002**: The system MUST implement a lightweight, CPU-optimized classifier (e.g., DistilBERT) to route queries to the appropriate generation path based on intent, treating "Ambiguous" as covering both complex intents and ontology mismatches (See US-2).
- **FR-003**: The system MUST support artificial latency injection at specific steps (various time delays ranging from immediate to extended intervals) and model user patience (exponential decay, mean=2s) to trigger abandonment events (See US-2).
- **FR-004**: The system MUST vary the information density of the deterministic fallback by rendering a small number of UI elements to determine the minimum viable density (See US-2).
- **FR-005**: The system MUST calculate alignment scores using a rubric derived from the "Designing for Human-Agent Alignment" paper (Section 4.2) and generate a Pareto frontier plot of alignment vs. latency (See US-3).
- **FR-006**: The system MUST perform multiple-comparison correction (e.g., Bonferroni or FDR) on the statistical analysis of alignment scores across the different latency and density configurations to control family-wise error (See US-3).
- **FR-007**: The system MUST conduct a sensitivity analysis on the router's decision threshold, sweeping the confidence cutoff over a concrete set (e.g., {0.6, 0.7, 0.8}) and reporting the variation in inconsistency rates (See US-2).
- **FR-008**: The system MUST validate the generative baseline's output quality against a human-annotated gold standard (N=50) at 0ms latency before the experiment begins, ensuring the "degradation" claim is empirically grounded (See US-2).

### Key Entities

- **InteractionTurn**: Represents a single user-agent exchange, containing the query, ground truth intent, and complexity score.
- **RoutingDecision**: Records the intent classification, the chosen generation path (Generative/Deterministic), and the router's confidence score.
- **SimulationRun**: Aggregates metrics (latency, alignment, success rate, abandonment) for a specific configuration of injected latency and information density.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The alignment score for the hybrid model is measured against the pure generative baseline at high-latency steps (See FR-005).
- **SC-002**: The minimum information density required for task completion is measured against the "Human-Agent Alignment" rubric criteria for user satisfaction, operationalized as a scoring function: `score = 0.4 * intent_match + 0.3 * (1 - latency_penalty) + 0.3 * ui_completeness` (See FR-004).
- **SC-003**: The latency threshold for fidelity degradation is measured against the point where the generative baseline's alignment score drops below the hybrid model's performance with statistical significance (p < 0.05, non-overlapping 95% CIs) (See FR-005).
- **SC-004**: The family-wise error rate is measured against the nominal alpha level (e.g., 0.05) after applying the multiple-comparison correction method (See FR-006).
- **SC-005**: The router's robustness is measured by the variance in inconsistency rates across the swept confidence thresholds (0.6, 0.7, 0.8) (See FR-007).

## Assumptions

- The A2UI-Bench dataset contains all necessary variables (queries, ground truth intents, and complexity indicators) required to train the router and simulate the scenarios; if specific complexity metadata is missing, it will be derived from query length or token count.
- The medium-scale generative model and the DistilBERT classifier can run within the GitHub Actions free-tier constraints (a limited number of CPU cores and constrained RAM) without requiring GPU acceleration or quantization.
- The "Human-Agent Alignment" rubric can be operationalized into a deterministic scoring function for the simulation, as human-in-the-loop testing is not feasible within the CI/CD environment. **Validation**: This rubric is validated against a hold-out set of N=50 human-annotated examples, requiring a correlation (r) ≥ 0.7 to ensure it is a valid proxy for "alignment" and not just "rule adherence".
- The deterministic rule-based generator has a sufficiently rich ontology of common UI components to handle the majority of "Ambiguous" intents without falling back to a generic error state.
- The latency injection method (sleep/delay) accurately simulates real-world network/compute variance, and the user patience model (exponential decay, mean=2s) accurately captures the behavioral impact of delay on user trust.
- The dataset is representative of real-world personal agent interactions, allowing the findings to be generalized to edge-device deployment scenarios.