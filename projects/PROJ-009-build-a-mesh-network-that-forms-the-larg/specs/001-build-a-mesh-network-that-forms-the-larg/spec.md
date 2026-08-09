# Feature Specification: Mesh Network Supercomputer Using Pooled Idle Computing Resources

**Feature Branch**: `001-mesh-supercomputer`  
**Created**: 2026-07-31  
**Status**: Draft  
**Input**: User description: "Mesh Network Supercomputer Using Pooled Idle Computing Resources"

## User Scenarios & Testing

### User Story 1 - Physical Testbed Orchestration & Data Acquisition (Priority: P1)

The researcher MUST be able to deploy a dynamic scheduler to a physical mesh of heterogeneous consumer devices (laptops, Raspberry Pis, mobile devices) over a local Wi-Fi network, inject controlled network impairments, and collect raw execution logs including wall-clock time, packet counts, and CPU utilization.

**Why this priority**: The research question explicitly demands "real execution logs" from a "physical testbed" to falsify linear scaling hypotheses. Without the ability to orchestrate real hardware and capture the specific metrics (network latency, CPU variance) required for the regression model, the core empirical investigation cannot proceed.

**Independent Test**: The system can be tested by launching a single benchmark job across multiple physical nodes with injected latency, verifying that the system successfully distributes tasks, records `tcpdump` packet counts and `mpstat` CPU usage per node, and outputs a CSV file matching the schema defined in Key Entities (PhysicalNode, TaskChunk) within the specified CI time limit.

**Acceptance Scenarios**:

1. **Given** a list of 20 reachable IP addresses representing heterogeneous devices, **When** the orchestrator initiates a Monte Carlo integration benchmark with injected 100ms latency, **Then** the system distributes tasks, records a non-zero packet count for every node, and outputs a CSV containing `node_id`, `wall_clock_time`, `cpu_utilization_pct`, and `packet_count`.
2. **Given** a node that disconnects mid-execution (simulating unreliable consumer hardware), **When** the scheduler detects the heartbeat loss, **Then** the system re-assigns the failed task chunk to an active node and logs the re-assignment event with a timestamp.
3. **Given** a workload size that exceeds the memory of a specific low-end device (e.g., Raspberry Pi), **When** the scheduler assigns a task chunk, **Then** the system detects the memory constraint (via local log or OOM signal) and splits the chunk into smaller units that fit the device's available RAM.

---

### User Story 2 - Dynamic Scheduler & Granularity Parameter Sweep (Priority: P2)

The researcher MUST be able to execute a parameter sweep varying task chunk sizes (fine/medium/coarse), node counts (10–20), and network conditions to generate the dataset required to identify the "sweet spot" where coordination overhead is minimized.

**Why this priority**: The core hypothesis relies on identifying a non-linear relationship between granularity and overhead. This story enables the systematic variation of the independent variables (granularity, heterogeneity) required to generate the throughput curve and validate the scaling law.

**Independent Test**: The system can be tested by running three distinct execution campaigns (fine, medium, coarse granularity) with identical node sets and network conditions, verifying that the output contains three distinct throughput measurements and that the coordination overhead (handshake time vs. compute time) differs between them.

**Acceptance Scenarios**:

1. **Given** a configuration specifying "fine" granularity (small chunk size), **When** the execution campaign runs on 15 nodes, **Then** the system logs a higher ratio of coordination overhead time relative to total execution time compared to the "coarse" run.
2. **Given** a configuration specifying "coarse" granularity (large chunk size), **When** the execution campaign runs on 15 nodes with high heterogeneity, **Then** the system logs a higher variance in completion times (straggler effect) compared to the "fine" run.
3. **Given** a series of runs varying only the number of active nodes (10, 15, 20) with fixed granularity, **When** the analysis script aggregates the results, **Then** it generates a dataset containing `node_count`, `throughput_tasks_per_sec`, and `coordination_overhead_ratio` for regression analysis.

---

### User Story 3 - Statistical Analysis & Theoretical Validation (Priority: P3)

The researcher MUST be able to execute a multiple linear regression and ANOVA on the collected physical data to quantify the interaction effects, and validate the observed scaling laws against the theoretical capacity bounds from the Ong & Motani mesh network literature.

**Why this priority**: This story delivers the final scientific output: the mathematical model explaining the trade-offs and the external validation against information-theoretic bounds, which is required to falsify the hypothesis of linear scaling.

**Independent Test**: The system can be tested by feeding the physical execution logs into the analysis module and verifying that the system outputs a regression model object containing an R² value, p-values for the interaction terms, and a comparison metric against the theoretical capacity bound, regardless of the magnitude of R².

**Acceptance Scenarios**:

1. **Given** a dataset containing throughput, latency, CPU variance, and chunk size for 50 independent runs, **When** the regression analysis is executed, **Then** the output includes a regression equation, an R² value, and p-values for the interaction term between heterogeneity and granularity.
2. **Given** the observed throughput scaling curve and the theoretical capacity formula from Ong & Motani (2007) parameterized with the testbed's measured bandwidth and SNR, **When** the validation script runs, **Then** it calculates the deviation between the empirical curve and the theoretical bound and flags if the empirical performance exceeds the theoretical limit (which would indicate a measurement error).
3. **Given** the full set of granularity settings, **When** the ANOVA test is run, **Then** it outputs a p-value indicating whether the differences in throughput between granularity settings are statistically significant (p < 0.05).

---

### Edge Cases

- **What happens when** a "straggler" node (extremely high latency or low CPU) causes the entire job to stall in a synchronous barrier?
  - *Handling*: The scheduler MUST implement an asynchronous timeout (e.g., 2x median task time) and re-assign the straggler's task to the next available node, logging the event as a "heterogeneity penalty."
- **How does the system handle** a scenario where the local Wi-Fi network is saturated by external traffic, causing packet loss > 20%?
  - *Handling*: The system MUST detect the high packet loss via `tcpdump` analysis, abort the current run, and log the failure with a "network saturation" error code to prevent corrupted data from entering the regression analysis.
- **What happens when** a consumer device (e.g., mobile phone) enters sleep mode or loses power during a long-running task?
  - *Handling*: The system MUST detect the heartbeat loss, mark the task as "failed," re-queue it for another node, and record the "dropout rate" metric to be used as a covariate in the regression model.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST enable the researcher to deploy and manage a dynamic task scheduler across a physical mesh of 10–20 heterogeneous consumer devices connected via local Wi-Fi, collecting real-time heartbeat and completion feedback (See US-1).
- **FR-002**: The system MUST enable the researcher to instrument every node to capture wall-clock execution time, network packet counts (via `tcpdump`), and CPU utilization (via `mpstat`) during benchmark execution (See US-1).
- **FR-003**: The system MUST enable the researcher to implement a configurable parameter sweep to vary task chunk sizes (fine/medium/coarse), active node counts (a scalable range), and artificially injected network latency/packet loss. (See US-2).
- **FR-004**: The system MUST enable the researcher to calculate and log the coordination overhead ratio (time spent in handshake/management vs. actual computation) for every task execution to enable trade-off analysis (See US-2).
- **FR-005**: The system MUST enable the researcher to perform multiple linear regression and ANOVA on the aggregated physical data to quantify the interaction effects between measured heterogeneity (CPU speed variance, latency) and task granularity on throughput, treating injected latency as an experimental factor and hardware class as an observational covariate, and output a JSON file containing the model coefficients, p-values, and R² value (See US-3).
- **FR-006**: The system MUST enable the researcher to validate the observed throughput scaling laws against the theoretical capacity bounds derived from the Ong & Motani mesh network literature, using measured testbed parameters (bandwidth, SNR, node count) to parameterize the bound as a general upper limit for wireless channel capacity (See US-3).
- **FR-007**: The system MUST enable the researcher to enforce a hard timeout for the entire execution and analysis pipeline to ensure compatibility with free-tier CI runners (See US-1).

### Key Entities

- **PhysicalNode**: Represents a real device with attributes: `ip_address`, `hardware_spec` (CPU model, RAM), `current_latency` (ms), `packet_loss_rate`, `cpu_utilization` (pct), `bandwidth_Mbps`, `snr_db`.
- **TaskChunk**: A unit of work with attributes: `task_id`, `estimated_ops`, `actual_duration`, `assigned_node_id`, `status` (pending, running, failed, completed, re-assigned).
- **ExecutionRun**: A collection of data for a specific parameter set, containing: `node_count`, `granularity_setting`, `injected_latency`, `total_throughput`, `coordination_overhead_ratio`, `straggler_count`, `bandwidth_Mbps`, `snr_db`.
- **RegressionModel**: The statistical output object containing: `coefficients`, `p_values`, `r_squared`, `residuals`, `theoretical_bound_deviation`.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The system's ability to calculate and report an R² value from a regression model trained on the physical execution data is measured against the requirement to produce valid statistical output explaining the variance in throughput (See US-3).
- **SC-002**: The validation module's ability to calculate the deviation between the empirical throughput curve and the theoretical capacity bound (Ong & Motani, 2007, parameterized with measured bandwidth and SNR) is measured against the requirement to confirm the empirical data does not violate information-theoretic limits (See US-3).
- **SC-003**: The coordination overhead ratio is measured across varying granularity settings to identify the non-linear "sweet spot" where overhead is minimized relative to parallelism gains (See US-2).
- **SC-004**: The total wall-clock time of the physical execution and analysis pipeline is measured against a predefined CI time limit to ensure feasibility on free-tier hardware. (See US-1).
- **SC-005**: The statistical significance of granularity differences is measured against a p-value threshold of <0.05 via ANOVA to confirm that observed effects are not due to chance (See US-3).
- **SC-006**: The dataset-variable fit is measured by verifying that every predictor variable (CPU variance, latency, packet loss, throughput) and outcome (throughput) is present in the collected logs; if any required variable is missing from the physical logs, the run is flagged as WARN and the dataset is excluded from regression analysis ONLY IF the missing variable is critical (e.g., throughput, latency); otherwise, the run proceeds with reduced model complexity using the available variables (See US-1).

## Assumptions

- **Assumption about data/environment**: The physical testbed will consist of a set of heterogeneous consumer devices (laptops, Raspberry Pis, mobile devices) available on a local Wi-Fi network; the system assumes these devices can be remotely accessed and instrumented via standard CLI tools (`ssh`, `tcpdump`, `mpstat`).
- **Assumption about scope boundaries**: The research focuses on "embarrassingly parallel" scientific workloads (e.g., Monte Carlo integration); complex multi-stage pipelines requiring low-latency inter-node communication are out of scope for this iteration.
- **Assumption about target users**: The primary user is a researcher running batch jobs on a CI/CD pipeline; the system does not require a real-time interactive UI or dashboard, only log aggregation and analysis scripts.
- **Assumption about compute constraints**: The analysis assumes that the statistical modeling (regression, ANOVA) and data aggregation can complete within 6 hours on a standard 2-core, 7GB RAM free-tier runner without GPU acceleration; no large model training is required.
- **Assumption about dataset-variable fit**: The "heterogeneity" variable is assumed to be fully captured by the measured parameters (CPU speed variance from `mpstat`, network latency/packet loss from `tcpdump`); unmodeled variables like thermal throttling are acknowledged as potential confounders but are assumed to be captured implicitly in the `actual_duration` metric.
- **Assumption about threshold justification**: The "sweet spot" detection will use a standard statistical inflection point analysis (e.g., derivative of the throughput curve); the specific cutoff for "diminishing returns" will be defined as the point where the marginal gain in throughput drops below a negligible threshold per [deferred] increase in node count, a value chosen as a community-standard default for sensitivity analysis and subject to adjustment.
- **Assumption about physical validation limitations**: The physical validation acknowledges that unmodeled variables (thermal throttling, OS noise, Wi-Fi interference) exist; the physical deployment MUST measure these variables directly on real hardware to account for the discrepancy between the simplified theoretical model and real-world physics.
- **Assumption about inference framing**: Since the study involves both observational covariates (hardware class) and experimental factors (injected latency), the statistical analysis plan MUST distinguish between the two: hardware class is treated as an observational covariate, while injected latency is treated as an experimental factor in the regression model.
- **Assumption about theoretical bound applicability**: The Ong & Motani () bound is used as a general upper limit for wireless channel capacity, not a direct comparison of application throughput. The validation serves as a sanity check to ensure empirical performance does not exceed physical layer limits, acknowledging that the specific topology (pooled idle resources) may differ from the paper's single-source-multiple-relay model.