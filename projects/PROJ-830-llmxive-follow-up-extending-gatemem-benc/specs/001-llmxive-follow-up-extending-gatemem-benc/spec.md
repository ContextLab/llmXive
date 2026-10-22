# Feature Specification: llmXive follow-up: extending "GateMem: Benchmarking Memory Governance in Multi-Principal Shared-Memo"

**Feature Branch**: `001-gatekeeper-governance`  
**Created**: 2026-07-12  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending GateMem benchmark with modular governance layers"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Evaluate Gatekeeper vs. Baselines on Access Control (Priority: P1) (See US-1)

The researcher needs to execute the Gatekeeper pipeline and both standard retrieval baselines on the GateMem dataset to measure and compare unauthorized information leakage rates. This is the primary hypothesis test for the research question.

**Why this priority**: This directly addresses the core research question regarding the trade‑off between security (access control) and utility. Without this comparison, the study cannot determine if the modular approach resolves the identified tension.

**Independent Test**: Run the automated evaluation script on the "medical", "office", "education", and "household" domains of the GateMem dataset and verify that the Access Control score (rate of unauthorized exposure) is calculated and output for the Gatekeeper, Retrieval‑only, and Long‑Context configurations.

**Acceptance Scenarios**:

1. **Given** the GateMem dataset is downloaded and parsed, **When** the evaluation script runs the Gatekeeper + Agent pipeline, **Then** the system outputs an Access Control score for the Gatekeeper configuration.
2. **Given** the same dataset and agent backbone, **When** the evaluation script runs the "Retrieval‑only" baseline, **Then** the system outputs an Access Control score for the Retrieval‑only configuration.
3. **Given** the same dataset and agent backbone, **When** the evaluation script runs the "Long‑Context" baseline, **Then** the system outputs an Access Control score for the Long‑Context configuration.
4. **Given** all three configurations have been evaluated, **When** the results are aggregated, **Then** a paired comparison table is generated showing the difference in Access Control scores between Gatekeeper and each baseline.

---

### User Story 2 - Evaluate Gatekeeper vs. Baselines on Task Utility and Forgetting (Priority: P2) (See US-2)

The researcher needs to measure task success rates (Utility) and deletion‑compliance (Forgetting) to ensure that the proposed security filters do not degrade the agent's ability to perform its primary function or violate deletion requests.

**Why this priority**: A security mechanism that blocks all data (perfect access control) but also blocks all valid queries (zero utility) is useless. This story validates that the governance layer maintains acceptable performance while respecting deletions.

**Independent Test**: Run the evaluation script on the four domains and verify that the Utility score (exact‑match success rate) and Forgetting compliance rate are calculated for the Gatekeeper, Retrieval‑only, and Long‑Context configurations.

**Acceptance Scenarios**:

1. **Given** the dataset contains valid task queries, **When** the Gatekeeper pipeline processes these queries, **Then** the system correctly identifies and allows valid queries to reach the LLM and records the number of exact‑match successes.
2. **Given** the same queries processed by the Retrieval‑only baseline, **When** the results are compared, **Then** the Utility score for Retrieval‑only is recorded alongside the Gatekeeper score.
3. **Given** the same queries processed by the Long‑Context baseline, **When** the results are compared, **Then** the Utility score for Long‑Context is recorded alongside the Gatekeeper score.
4. **Given** the dataset contains deletion‑request episodes, **When** the Forgetting metric is calculated, **Then** the system outputs the Forgetting compliance rate for Gatekeeper, Retrieval‑only, and Long‑Context configurations.
5. **Given** the utility and forgetting scores are available, **When** the statistical analysis runs, **Then** the system reports the differences (with significance testing) between Gatekeeper and each baseline.

---

### User Story 3 - Profile Computational Cost and Latency (Priority: P3) (See US-3)

The researcher needs to measure the wall‑clock inference time and peak CPU/RAM usage to verify that the modular gatekeeper is computationally cheaper than the integrated baselines.

**Why this priority**: The hypothesis posits that decoupling governance reduces cost. This story provides the empirical evidence for the "computational cost reduction" claim in the expected results.

**Independent Test**: Execute the evaluation pipeline with instrumentation enabled and verify that peak memory usage and total wall‑clock time are logged for all three configurations.

**Acceptance Scenarios**:

1. **Given** the pipeline is running on a CPU‑only runner, **When** the Gatekeeper model (DistilBERT) and rule engine are active, **Then** the system logs the peak RAM usage in MB.
2. **Given** the same runner and dataset, **When** the Retrieval‑only baseline is processed, **Then** the system logs the peak RAM usage for the baseline.
3. **Given** the same runner and dataset, **When** the Long‑Context baseline is processed, **Then** the system logs the peak RAM usage for that baseline.
4. **Given** both logs are complete, **When** the report is generated, **Then** it displays the percentage reduction in inference latency and memory usage for the Gatekeeper compared to each baseline.

---

### Edge Cases

- What happens when the GateMem dataset contains a `leak-target` annotation that is ambiguous (e.g., the user role is not clearly defined)? The system must log this as a "validation error" and exclude it from the final metric calculation rather than failing the run.
- How does the system handle a scenario where the frozen DistilBERT model fails to load due to local cache corruption? The system must retry the download once. If the retry fails, the system MUST exit with error code 1 and log "Critical: Model Unavailable", treating the entire evaluation run as a failure.
- What happens if the regex‑based logic engine encounters a malformed deletion‑log entry? The system must default to "deny" for that specific entry (fail‑safe) and log the anomaly for manual review.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download and parse the GateMem dataset (medical, office, education, household) to extract `leak-target` annotations, role definitions, and deletion‑request flags, ensuring these fields are present for every episode (See US-1).
- **FR-002**: System MUST implement a CPU‑tractable gatekeeper pipeline consisting of a frozen DistilBERT intent classifier (distilbert-base-uncased-finetuned-sst-2-english [2501.00241]) and a regex‑based rule engine for role validation and deletion‑log checking (See US-1).
- **FR-003**: System MUST execute the Gatekeeper pipeline and the "Retrieval‑only" and "Long‑Context" baselines using identical prompt templates, retrieval parameters, and a fixed random seed (42) to ensure a fair comparison. The LLM backbone will be a lightweight 2.7 B open‑source model (e.g., Llama‑3‑2B‑int8) that can run on a CPU‑only free‑tier runner (See US-1, US-2, US-3).
- **FR-004**: System MUST calculate the three core GateMem metrics for every test episode: Utility (exact‑match success rate against human‑annotated ground‑truth), Access Control (unauthorized exposure rate against independent ground‑truth), and Forgetting (deletion‑compliance rate for episodes with explicit deletion requests) (See US-2).
- **FR-005**: System MUST perform statistical comparison of mean scores between Gatekeeper and each baseline:
  - For **Utility** (continuous proportion), a linear mixed‑effects model `Utility ~ Method + Domain` will be fitted (Gaussian error).
  - For **Access Control** and **Forgetting** (binary), a Generalized Linear Mixed‑Effects Model with logit link `Outcome ~ Method + Domain` will be used.
  - Because only four domains are available, **Domain** will be treated as a fixed effect rather than a random intercept.
  - Normality checks (Shapiro‑Wilk, α = 0.05) will determine whether parametric or non‑parametric post‑hoc tests are appropriate.
  - A power analysis targeting a medium effect size (Cohen’s h = 0.3) with α = 0.05 and power = 0.8 requires ≥ 100 episodes per domain; the study will ensure this sample size (See US-1, US-2).  
  - Multiple‑comparison correction will be performed across **six** hypothesis tests (Access Control vs. each baseline, Utility vs. each baseline, Forgetting vs. each baseline) using Holm‑Bonferroni (family‑wise α = 0.05) (See SC‑004). (See US-2).
- **FR-006**: System MUST profile and report wall‑clock inference time and peak CPU/RAM usage for the Gatekeeper pipeline versus each baseline (See US-3).
- **FR-007**: System MUST output a simple random sample of failure cases (stratified by domain if N > 50) with a fixed random seed (42) for manual error analysis. A 'False Positive' is defined as a valid query blocked by the Gatekeeper; a 'False Negative' is defined as a leak allowed by the Gatekeeper (See US-2).

### Key Entities

- **Episode**: A single interaction instance from the GateMem dataset containing user intent, memory state, leak‑target annotation, role information, and optional deletion‑request flag.
- **Gatekeeper**: The modular pipeline component comprising the intent classifier and rule engine that filters memory access before the LLM generation step.
- **Baseline**: The reference implementations (Retrieval‑only and Long‑Context) without the modular governance layer.
- **False Positive**: A test episode where the Gatekeeper blocks a query that the ground‑truth `leak_target=True` indicates should be allowed (valid query blocked).
- **False Negative**: A test episode where the Gatekeeper allows a query that the ground‑truth `leak_target=False` indicates should be blocked (leak allowed).

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Access Control score = **unauthorized exposures / total requests** (both numerator and denominator are counted across all episodes). Measured for Gatekeeper, Retrieval‑only, and Long‑Context configurations (See US-1).
- **SC-002**: Utility score = **exact‑match correct answers / total evaluated queries** (exact match after whitespace and case normalization). Measured for Gatekeeper, Retrieval‑only, and Long‑Context configurations (See US-2).
- **SC-003**: Computational overhead = wall‑clock time (seconds) and peak RAM (MB) measured for each configuration; percentage reduction relative to each baseline will be reported (See US-3).
- **SC-004**: Statistical significance of differences in Access Control, Utility, and Forgetting scores will be assessed using the models described in FR‑005 with Holm‑Bonferroni‑adjusted α = 0.0083 (≈ 0.05/6) (See US-2).
- **SC-005**: Forgetting compliance rate = **deletion requests correctly denied / total deletion requests**. Measured for Gatekeeper, Retrieval‑only, and Long‑Context configurations (See US-2).

## Assumptions

- The GateMem dataset (arXiv:2606.18829) is publicly accessible via the linked repository, is licensed under **CC‑BY‑4.0**, and the license permits redistribution and commercial‑free use.
- The dataset contains the required fields: `leak-target` annotation, role definitions, and a boolean deletion‑request flag. No “outcome, predictors, covariates” or post‑task anxiety variables are present.
- The analysis will run on a CPU‑only environment (GitHub Actions free tier: limited cores, constrained RAM); therefore, the DistilBERT model and the 2.7 B LLM backbone must be run in default precision without GPU acceleration, and the dataset must be processed in a memory‑efficient manner (e.g., streaming or batching) to fit within available memory constraints.
- The frozen DistilBERT model used for intent classification is small enough to load and run within the available RAM constraint alongside the agent’s context window.
- The regex‑based rule engine can handle the format of the deletion log defined in the GateMem dataset without requiring a full database implementation.
- **Independence of Ground Truth**: The ground‑truth labels for ‘leakage’ and ‘deletion’ used to calculate Access Control and Forgetting metrics are derived from the original human annotations in the GateMem dataset and are independent of the Gatekeeper’s specific rule logic, ensuring validation is not circular.
- The power analysis assumes a medium effect size (Cohen’s h = 0.3); with ≥ 100 episodes per domain the study achieves ≥ 0.8 power at α = 0.05.
- All random sampling (failure‑case sample, model seeds) uses a fixed seed of 42 for reproducibility.
