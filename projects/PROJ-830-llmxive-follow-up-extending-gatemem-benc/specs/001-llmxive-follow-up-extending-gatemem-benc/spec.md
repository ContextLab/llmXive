# Feature Specification: llmXive follow-up: extending "GateMem: Benchmarking Memory Governance in Multi-Principal Shared-Memo"

**Feature Branch**: `001-gatekeeper-governance`  
**Created**: 2026-07-12  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending GateMem benchmark with modular governance layers"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Evaluate Gatekeeper vs. Baseline on Access Control (Priority: P1)

The researcher needs to execute the Gatekeeper pipeline and standard retrieval baselines on the GateMem dataset to measure and compare unauthorized information leakage rates. This is the primary hypothesis test for the research question.

**Why this priority**: This directly addresses the core research question regarding the trade-off between security (access control) and utility. Without this comparison, the study cannot determine if the modular approach resolves the identified tension.

**Independent Test**: Run the automated evaluation script on the "medical" and "office" domains of the GateMem dataset and verify that the Access Control score (rate of unauthorized exposure) is calculated and output for both the Gatekeeper and Baseline configurations.

**Acceptance Scenarios**:

1. **Given** the GateMem dataset is downloaded and parsed, **When** the evaluation script runs the Gatekeeper + Agent pipeline, **Then** the system outputs an Access Control score for the Gatekeeper configuration.
2. **Given** the same dataset and agent backbone, **When** the evaluation script runs the "Retrieval-only" baseline, **Then** the system outputs an Access Control score for the baseline configuration.
3. **Given** both configurations have been evaluated, **When** the results are aggregated, **Then** a paired comparison table is generated showing the difference in Access Control scores between the two methods.

---

### User Story 2 - Evaluate Gatekeeper vs. Baseline on Task Utility (Priority: P2)

The researcher needs to measure task success rates (Utility) to ensure that the proposed security filters do not degrade the agent's ability to perform its primary function.

**Why this priority**: A security mechanism that blocks all data (perfect access control) but also blocks all valid queries (zero utility) is useless. This story validates that the governance layer maintains acceptable performance.

**Independent Test**: Run the evaluation script on the "education" and "household" domains and verify that the Utility score (task success rate) is calculated and that the Gatekeeper's score is compared against the baseline using a human-annotated ground-truth answer key.

**Acceptance Scenarios**:

1. **Given** the dataset contains valid task queries, **When** the Gatekeeper pipeline processes these queries, **Then** the system correctly identifies and allows valid queries to reach the LLM.
2. **Given** the baseline pipeline processes the same queries, **When** the results are compared, **Then** the Utility score for the Gatekeeper is recorded alongside the baseline score.
3. **Given** the utility scores are available, **When** the statistical analysis runs, **Then** the system reports the difference in utility between the Gatekeeper and the baseline.
4. **Given** the dataset contains deletion request episodes, **When** the Forgetting metric is calculated, **Then** the system outputs the deletion compliance rate for the Gatekeeper and Baseline configurations.

---

### User Story 3 - Profile Computational Cost and Latency (Priority: P3)

The researcher needs to measure the wall-clock inference time and peak CPU/RAM usage to verify that the modular gatekeeper is computationally cheaper than the integrated baselines.

**Why this priority**: The hypothesis posits that decoupling governance reduces cost. This story provides the empirical evidence for the "computational cost reduction" claim in the expected results.

**Independent Test**: Execute the evaluation pipeline with instrumentation enabled and verify that peak memory usage and total wall-clock time are logged for both the Gatekeeper and Baseline configurations.

**Acceptance Scenarios**:

1. **Given** the pipeline is running on a CPU-only runner, **When** the Gatekeeper model (DistilBERT) and rule engine are active, **Then** the system logs the peak RAM usage in MB.
2. **Given** the same runner and dataset, **When** the baseline (Long-Context) is processed, **Then** the system logs the peak RAM usage for the baseline.
3. **Given** both logs are complete, **When** the report is generated, **Then** it displays the percentage reduction in inference latency and memory usage for the Gatekeeper compared to the baseline.

---

### Edge Cases

- What happens when the GateMem dataset contains a `leak-target` annotation that is ambiguous (e.g., the user role is not clearly defined)? The system must log this as a "validation error" and exclude it from the final metric calculation rather than failing the run.
- How does the system handle a scenario where the frozen DistilBERT model fails to load due to local cache corruption? The system must retry the download once. If the retry fails, the system MUST exit with error code 1 and log "Critical: Model Unavailable", treating the entire evaluation run as a failure.
- What happens if the regex-based logic engine encounters a malformed deletion log entry? The system must default to "deny" for that specific entry (fail-safe) and log the anomaly for manual review.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download and parse the GateMem dataset (medical, office, education, household) to extract `leak-target` annotations and authorization boundaries, ensuring all required variables (outcome, predictors, covariates) are present for the analysis (See US-1).
- **FR-002**: System MUST implement a CPU-tractable gatekeeper pipeline consisting of a frozen DistilBERT intent classifier and a regex-based rule engine for role validation and deletion log checking (See US-1).
- **FR-003**: System MUST execute the Gatekeeper pipeline and the "Retrieval-only" and "Long-Context" baselines using identical prompt templates, retrieval parameters, and random seeds to ensure a fair comparison (See US-1).
- **FR-004**: System MUST calculate the three core GateMem metrics for every test episode: Utility (task success rate against human-annotated ground-truth), Access Control (unauthorized exposure rate against independent ground-truth), and Forgetting (deletion compliance rate for episodes with explicit deletion requests) (See US-2).
- **FR-005**: System MUST perform statistical comparison of mean scores between Gatekeeper and baselines using a Linear Mixed-Effects Model (LMM) with 'Domain' as a random intercept to account for hierarchical data structure. If LMM is not feasible, a domain-stratified analysis MUST be performed. Normality checks (Shapiro-Wilk, α=0.05) MUST be performed to determine if parametric or non-parametric post-hoc tests are appropriate (See US-2).
- **FR-006**: System MUST profile and report wall-clock inference time and peak CPU/RAM usage for the Gatekeeper pipeline versus the baselines (See US-3).
- **FR-007**: System MUST output a simple random sample of failure cases. (stratified by domain if N > 50) with a fixed random seed for manual error analysis. A 'False Positive' is defined as a valid query blocked by the Gatekeeper; a 'False Negative' is defined as a leak allowed by the Gatekeeper (See US-2).

### Key Entities

- **Episode**: A single interaction instance from the GateMem dataset containing user intent, memory state, and ground-truth labels for leakage and deletion.
- **Gatekeeper**: The modular pipeline component comprising the intent classifier and rule engine that filters memory access before the LLM generation step.
- **Baseline**: The reference implementation (Retrieval-only or Long-Context) without the modular governance layer.
- **False Positive**: A test episode where the Gatekeeper blocks a query that the ground-truth `leak-target` annotation indicates should be allowed (valid query blocked).
- **False Negative**: A test episode where the Gatekeeper allows a query that the ground-truth `leak-target` annotation indicates should be blocked (leak allowed).

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Access Control score (unauthorized exposure rate) is measured against the Baseline "Retrieval-only" configuration to quantify the reduction in leakage (See US-1).
- **SC-002**: Task Utility score (success rate) is measured against the Baseline "Long-Context" configuration to verify the maintenance of task performance (See US-2).
- **SC-003**: Computational overhead (wall-clock time and peak RAM) is measured against the Baseline configurations to verify the cost reduction hypothesis (See US-3).
- **SC-004**: Statistical significance of the differences in Access Control and Utility scores is measured using Linear Mixed-Effects Models (LMM) with Domain as a random intercept (See US-2).
- **SC-005**: Forgetting compliance rate is measured against the Baseline to verify the system's ability to handle deletion requests correctly (See US-2).

## Assumptions

- The GateMem dataset (arXiv:2606.18829) is publicly accessible via the linked repository and contains all necessary `leak-target` annotations and role definitions required to compute Access Control and Forgetting metrics.
- The analysis will run on a CPU-only environment (GitHub Actions free tier: limited cores, constrained RAM); therefore, the DistilBERT model must be run in default precision without GPU acceleration, and the dataset must be processed in a memory-efficient manner (e.g., streaming or batching) to fit within ~7 GB RAM.
- The "Retrieval-only" and "Long-Context" baselines can be replicated using the same LLM backbone (e.g., Llama-3-8B) as the Gatekeeper agent to ensure a fair comparison, assuming the LLM backbone is available via a local cache or a compatible free-tier inference endpoint.
- The frozen DistilBERT model used for intent classification is small enough to load and run within the available RAM constraint. alongside the agent's context window.
- The dataset does not require post-task anxiety/rumination variables; the analysis relies solely on the explicit `leak-target` and role annotations provided in the GateMem dataset.
- The statistical power for the mixed-effects models is sufficient given the sample size of the GateMem test set; if the sample size is too small, the results will be interpreted as exploratory rather than definitive (power limitation acknowledged).
- The regex-based rule engine can handle the complexity of the "deletion log" format defined in the GateMem dataset without requiring a full database implementation.
- **Independence of Ground Truth**: The ground-truth labels for 'leakage' and 'deletion' used to calculate Access Control and Forgetting metrics are derived from the original human annotations in the GateMem dataset and are independent of the Gatekeeper's specific rule logic, ensuring validation is not circular.