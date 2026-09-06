# Feature Specification: llmXive follow-up: extending "Infinite Worlds with Versatile Interactions"

**Feature Branch**: `001-llmxive-followup`  
**Created**: 2026-08-26  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'Infinite Worlds with Versatile Interactions'"

## User Scenarios & Testing

### User Story 1 - Execute CPU-Constrained Simulation Baseline (Priority: P1)

A researcher needs to run the comparative simulation between the neural baseline and the deterministic Cellular Automaton (CA) "Eco-Director" on a standard GitHub Actions free-tier runner (2 CPU cores, ~7 GB RAM, no GPU) to establish the performance bounds and latency metrics.

**Why this priority**: This is the foundational step. Without successfully executing the simulation within the strict hardware constraints, no data can be collected to answer the research question. It validates the feasibility of the entire methodology.

**Independent Test**: The system can be tested by running the simulation script for a fixed duration on the CI runner and verifying that the job completes without OOM (Out Of Memory) errors or timeout, while logging latency per step.

**Acceptance Scenarios**:

1. **Given** a standard GitHub Actions runner with 2 CPU cores and no GPU, **When** the simulation script is executed with the B pilot agent and the B neural baseline (throttled), **Then** the job completes within the specified time limit and records a latency baseline for the neural approach.
2. **Given** the same runner environment, **When** the simulation is swapped to use the CA Eco-Director module, **Then** the job completes without requiring CUDA acceleration or exceeding substantial RAM usage.
3. **Given** the simulation environment, **When** the system runs for a sufficient number of time-steps, **Then** the system logs `coherence_score`, `diversity_score`, and `step_latency` at regular intervals without crashing or producing NaN values.

---

### User Story 2 - Sweep Algorithmic Parameters for Coherence Analysis (Priority: P2)

A researcher needs to systematically vary the CA parameters (neighborhood radius, memory depth, non-linearity) to identify which specific algorithmic properties correlate with high environmental coherence and diversity scores comparable to the neural baseline.

**Why this priority**: This addresses the core research question. It moves beyond a simple "can it run" test to the actual empirical investigation of the relationship between rule-based properties and emergent complexity.

**Independent Test**: The system can be tested by running a single parameter sweep (e.g., varying only memory depth while holding locality constant) and verifying that the output dataset contains distinct entries for each parameter configuration with corresponding metric scores.

**Acceptance Scenarios**:

1. **Given** a defined grid of CA parameters (e.g., memory depth ∈ {2, 3}), **When** the simulation runs for each configuration, **Then** the output dataset contains a unique row for each configuration with recorded coherence and diversity scores.
2. **Given** the simulation results, **When** a Linear Mixed-Effects Model (LMM) is applied to the collected data, **Then** the system identifies statistically significant interaction effects between at least one parameter (e.g., memory depth) and the coherence metric, accounting for temporal autocorrelation.
3. **Given** the simulation environment, **When** the system detects that a specific parameter configuration leads to system instability (e.g., state explosion), **Then** the system logs a warning and excludes that specific run from the statistical analysis rather than crashing the entire job.

---

### User Story 3 - Validate Statistical Parity and Latency Trade-offs (Priority: P3)

A researcher needs to confirm whether the optimal CA configuration achieves statistical parity with the neural baseline in terms of coherence/diversity while meeting the target of ≥90% latency reduction, and document the trade-off in semantic novelty.

**Why this priority**: This synthesizes the findings to answer the "gap" in the literature. It determines the boundary conditions for rule-based sufficiency and provides the final comparative data required for the project's conclusion.

**Independent Test**: The system can be tested by comparing the aggregate metrics of the best-performing CA variant against the neural baseline and verifying that the latency reduction calculation is explicitly reported.

**Acceptance Scenarios**:

1. **Given** the collected metrics for the neural baseline and the best CA variant, **When** the statistical analysis is performed, **Then** the system reports a p-value indicating whether the difference in coherence scores is statistically insignificant (parity) or significant.
2. **Given** the latency logs for both systems, **When** the reduction is calculated, **Then** the system explicitly reports if the CA variant achieves ≥90% latency reduction compared to the neural baseline.
3. **Given** the event logs, **When** the "semantic novelty" of rare events is analyzed, **Then** the system provides a qualitative or quantitative assessment of whether the CA variant produces fewer high-complexity events than the neural baseline.

### Edge Cases

- **What happens when** the CA parameters (e.g., non-linearity) are set to extreme values that cause the state space to grow exponentially, potentially exceeding the RAM limit?
  - *Handling*: The system must detect memory usage exceeding a predefined high threshold and terminate the specific run gracefully, logging it as an "Out of Bounds" configuration rather than crashing the CI job.
- **How does the system handle** a scenario where the neural baseline (throttled) still exceeds the 6-hour job limit due to the sheer size of the 14B model?
  - *Handling*: The system must enforce a hard timeout on the neural baseline run (e.g., a predefined duration) and record the result as a "Time-Bound Baseline" rather than failing the entire study.
- **What happens when** the dataset (LingBot-World 2.0) is unavailable or the synthetic generation fails to produce [deferred] valid state transitions?
  - *Handling*: The system must fall back to a smaller synthetic dataset (e.g., a reduced number of steps) and flag the result as "Power-Limited" in the final report, ensuring the methodological comparison still proceeds.

## Requirements

### Functional Requirements

- **FR-001**: System MUST implement a modular "Eco-Director" engine that allows dynamic configuration of rule locality (neighborhood radius), state memory depth (history window), and non-linearity (update function) without code recompilation. (See US-1)
- **FR-002**: System MUST execute the multi-agent simulation for a minimum of 10,000 time-steps per configuration while recording coherence and diversity metrics at regular intervals. (See US-2)
- **FR-003**: System MUST enforce a a strict memory ceiling and a time limit of a reasonable duration per CI job, gracefully terminating any run that exceeds these bounds. (See US-1)
- **FR-004**: System MUST perform a Linear Mixed-Effects Model (LMM) analysis on the collected metrics to assess the interaction effects of CA parameters on coherence and diversity, treating 'time-step' as a random effect to account for temporal autocorrelation. (See US-2)
- **FR-005**: System MUST calculate and report the latency reduction percentage of the optimal CA variant relative to the throttled neural baseline, explicitly checking against the ≥90% target. (See US-3)
- **FR-006**: System MUST generate a sensitivity analysis report that sweeps the decision cutoff for "coherence" (e.g., absolute diff ∈ {0.01, 0.05, 0.1}) and reports how the inconsistency rate varies across these thresholds. (See US-3)
- **FR-007**: System MUST validate the independence of time-series samples by computing the Autocorrelation Function (ACF) and ensuring the lag-1 autocorrelation is < 0.1 before applying parametric tests, or adjust the model accordingly. (See US-2)
- **FR-008**: System MUST validate "coherence" against an external physics oracle (e.g., conservation of mass/energy constraints) rather than the neural baseline, ensuring the metric is not tautologically derived from the CA rules. (See US-3)
- **FR-009**: System MUST perform a Random Forest feature importance analysis on the CA parameters to detect non-linear interactions that the LMM might miss, reporting the top drivers of coherence. (See US-2)

### Key Entities

- **SimulationRun**: Represents a single execution of the world simulator, containing the specific CA parameter configuration, the agent weights used, and the raw time-series data of state transitions.
- **MetricRecord**: A snapshot of the simulation state at a specific time-step, containing the calculated coherence score, diversity score, and latency timestamp.
- **ParameterGrid**: The defined set of values for neighborhood radius, memory depth, and non-linearity that the system iterates through during the sweep.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The latency of the optimal CA variant is measured against the throttled neural baseline to verify a reduction of ≥90%. (See US-3)
- **SC-002**: The coherence and diversity scores of the CA variants are measured against the neural baseline to determine statistical parity via LMM p-values (accounting for temporal autocorrelation). (See US-2)
- **SC-003**: The false-positive rate of the "coherence" classification is measured against a sensitivity sweep of thresholds (0.01, 0.05, 0.1) to ensure robustness of the metric definition. (See US-3)
- **SC-004**: The number of valid time-steps completed is measured against the target of [deferred] to ensure sufficient data density for long-term coherence analysis. (See US-2)
- **SC-005**: The memory footprint of the simulation is measured against the system memory limit to ensure all runs complete without OOM errors. (See US-1)
- **SC-006**: The independence of coherence metrics from input parameters is measured via partial correlation analysis, ensuring the correlation coefficient between 'memory depth' and 'diversity' (controlling for other factors) is < 0.05. (See US-2)

## Assumptions

- The open-source LingBot-World training corpus or a sufficiently representative synthetic dataset can be generated to simulate a large number of environmental state transitions within the GB disk limit.
- The pilot agent weights are available and can be loaded into CPU memory without requiring quantization or CUDA acceleration.
- The "coherence" metric is defined as the deviation from expected physical constraints (e.g., conservation of mass/energy) provided by an external physics oracle, not as tautological rule adherence.
- The "diversity" metric is defined as event entropy calculated from the state transition log, independent of the specific input parameters used to generate the state.
- The "neural baseline" can be effectively throttled to match CPU latency constraints, or a proxy model with similar behavioral characteristics is used if the 14B model is infeasible to run directly.
- The GitHub Actions free-tier runner provides a stable multi-core CPU environment with consistent memory allocation for the duration of the job.
- The relationship between CA parameters and emergent complexity is non-linear and requires the full parameter sweep (LMM + Random Forest) to identify, rather than a simple linear extrapolation.
- The temporal autocorrelation in the [deferred]-step time-series is significant enough to require a Mixed-Effects Model rather than a standard ANOVA.