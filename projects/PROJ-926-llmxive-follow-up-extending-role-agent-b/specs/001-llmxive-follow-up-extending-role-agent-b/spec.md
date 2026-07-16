# Feature Specification: llmXive follow-up: extending "Role-Agent: Bootstrapping LLM Agents via Dual-Role Evolution"

**Feature Branch**: `001-llmxive-followup`  
**Created**: 2026-07-16  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'Role-Agent: Bootstrapping LLM Agents via Dual-Role Evolution'"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate and Validate Baseline Failure Trajectories (Priority: P1)

The research system MUST generate a dataset of at least 500 failed agent trajectories in the ALFWorld environment using a baseline Llama-3-8B model and validate that these failures correspond to known ground-truth state transitions.

**Why this priority**: This is the foundational dataset for all subsequent analysis. Without verified failure trajectories and their corresponding ground-truth root causes, no comparison between degraded and intervention conditions is possible.

**Independent Test**: Can be fully tested by running the data generation script and verifying that the output file contains at least 500 entries, each with a valid trajectory ID, a failure step, and a linked ground-truth state transition from the ALFWorld simulator.

**Acceptance Scenarios**:

1. **Given** the ALFWorld environment is initialized and the Llama-3-8B model is loaded, **When** the generation script executes, **Then** at least 500 failed trajectories are saved to the local dataset with unique identifiers.
2. **Given** a generated failed trajectory, **When** the validation module checks the trajectory against the simulator's state log, **Then** the failure point is confirmed to match a ground-truth state transition where the agent deviated from the optimal path.
3. **Given** the dataset is complete, **When** a random sample of 10 trajectories is inspected, **Then** each contains a clear "failed to pick up object X after Y steps" pattern or equivalent semantic failure description.

---

### User Story 2 - Execute Degraded World Model Condition (Priority: P2)

The research system MUST simulate the "Degraded" experimental condition by processing the baseline failure trajectories with a World-in-Agent (WIA) prediction horizon set to zero (or randomized prompt) and record the resulting retrieval relevance scores.

**Why this priority**: This establishes the negative control condition to measure the performance drop caused by the lack of predictive context, which is the primary variable of interest.

**Independent Test**: Can be fully tested by running the degraded condition script on the P1 dataset and verifying that the output contains retrieval relevance scores that are statistically consistent with the failure modes observed in the Baseline trajectories (US-1) and distinct from the Intervention condition (US-3).

**Acceptance Scenarios**:

1. **Given** the 500 baseline failure trajectories, **When** the WIA module is configured with a prediction horizon of 0, **Then** the system generates failure analyses that lack predictive context (e.g., no future state prediction).
2. **Given** the degraded failure analyses, **When** they are fed into the AIW retrieval module, **Then** the system calculates a retrieval relevance score for each trajectory based on ground-truth root causes.
3. **Given** the retrieval scores, **When** the system aggregates the results, **Then** the mean retrieval relevance score for the degraded condition is recorded and stored for statistical comparison.

---

### User Story 3 - Apply Syntactic Abstraction Intervention (Priority: P3)

The research system MUST apply the rule-based "failure abstraction layer" to the degraded failure trajectories and measure the recovery in retrieval relevance and task completion rates.

**Why this priority**: This tests the core hypothesis that lightweight syntactic abstractions can substitute for deep predictive modeling, addressing the research gap regarding resource-constrained environments.

**Independent Test**: Can be fully tested by running the intervention script on the degraded dataset and verifying that the output shows a measurable increase in retrieval relevance scores compared to the degraded condition alone.

**Acceptance Scenarios**:

1. **Given** the degraded failure analyses, **When** the rule-based parser extracts syntactic patterns (e.g., "failed to pick up object X after Y steps"), **Then** the system generates an abstracted failure signal for each trajectory.
2. **Given** the abstracted failure signals, **When** they are fed into the AIW retrieval module, **Then** the system calculates a new retrieval relevance score for each trajectory.
3. **Given** the intervention retrieval scores, **When** the system re-executes the retrieved tasks in the simulator, **Then** the task completion rate is recorded and compared against the degraded condition.

### Edge Cases

- What happens when the ALFWorld simulator fails to generate a failure within the timeout limit for a specific prompt? (System logs the error and retries up to 3 times before skipping the trajectory).
- How does the system handle a failure trajectory where the ground-truth root cause is ambiguous or not directly linked to a single state transition? (The system flags the trajectory as "excluded" and excludes it from the final statistical analysis).
- What happens if the rule-based parser fails to match any syntactic patterns in a degraded failure analysis? (The system falls back to the raw degraded analysis for that specific trajectory and logs the event).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST generate at least 500 failed agent trajectories in the ALFWorld environment using a Llama-3-8B model (See US-1).
- **FR-002**: System MUST validate that every generated failure trajectory corresponds to a ground-truth state transition in the ALFWorld simulator (See US-1).
- **FR-003**: System MUST simulate a "Degraded" condition by setting the WIA prediction horizon to 0 and processing the baseline trajectories (See US-2).
- **FR-004**: System MUST calculate a retrieval relevance score for each trajectory in the Degraded condition based on ground-truth root causes mapped to a human-annotated task ID in a frozen task bank (See US-2).
- **FR-005**: System MUST implement a rule-based parser to extract syntactic patterns (e.g., "failed to pick up object X after Y steps") from degraded failure analyses (See US-3).
- **FR-006**: System MUST re-calculate retrieval relevance scores using the syntactic abstractions and measure the recovery in task completion rate upon re-execution (See US-3).
- **FR-007**: System MUST perform a statistical test to compare mean retrieval relevance scores across Baseline, Degraded, and Intervention groups, selecting the test based on normality: IF Shapiro-Wilk p-value < 0.05 THEN Mann-Whitney U test, ELSE independent samples t-test (See US-3).
- **FR-008**: System MUST perform a power analysis (target power ≥ 0.8) to justify the sample size of 500 trajectories for the planned statistical tests (See US-3).

### Key Entities

- **Failure Trajectory**: A sequence of agent actions in ALFWorld ending in a failure, containing the action log, the failure step, and the ground-truth root cause.
- **Retrieval Relevance Score**: A quantitative metric (0.0 to 1.0) representing the semantic similarity between the retrieved task and the ground-truth root cause of the failure, where the ground-truth root cause is mapped to a human-annotated task ID in a frozen task bank.
- **Syntactic Abstraction**: A lightweight, rule-based representation of a failure event (e.g., "failed to pick up object X after Y steps") used as a substitute for predictive context.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Retrieval relevance score is measured against the ground-truth state transitions from the ALFWorld simulator (See FR-004, FR-006).
- **SC-002**: Task completion rate is measured against the re-executed retrieved tasks in the ALFWorld simulator (See FR-006).
- **SC-003**: Statistical significance of the difference in mean retrieval relevance scores between Degraded and Intervention conditions is measured using an independent samples t-test or Mann-Whitney U test (See FR-007).
- **SC-004**: Recovery rate of the retrieval relevance score (Intervention vs. Degraded) is measured against the observed baseline degradation in the Degraded condition (See FR-006).

## Assumptions

- The ALFWorld environment and the Llama-3-8B model are available via PyPI/GitHub and can be executed on a CPU-only runner without GPU acceleration.
- The "ground-truth root cause" for each failure is derivable from the ALFWorld simulator's state transition log using a deterministic priority rule for ambiguous cases (See Key Entities).
- The rule-based parser can extract syntactic patterns from the failure logs with sufficient accuracy to serve as a valid substitute for predictive context.
- A sufficient number of generated trajectories will be produced to achieve statistical power for the planned t-test or Mann-Whitney U test, assuming a medium effect size (Cohen's d)..
- The total compute time for data generation, condition execution, and statistical analysis will be constrained to a duration feasible for execution on a GitHub Actions free-tier runner (2 CPU cores, ~7 GB RAM).
- The Llama-8B model will be run in default precision (float32) without quantization (8-bit or 4-bit) to ensure CPU compatibility.
- The "retrieval relevance score" calculation uses a frozen, small classifier or similarity search on a pre-built task bank, which fits within the 7 GB RAM limit.
- The syntactic abstraction layer is implemented as a lightweight Python script that does not require external dependencies beyond standard libraries (e.g., `re`, `json`).
- The statistical analysis will use the `scipy` library, which is compatible with CPU-only execution and fits within the memory constraints.
- The ALFWorld simulator provides a deterministic environment where the same input produces the same output, ensuring reproducibility.
- The "ground-truth root cause" is not influenced by the agent's internal predictions or the synthetic failure logs, ensuring validation independence.