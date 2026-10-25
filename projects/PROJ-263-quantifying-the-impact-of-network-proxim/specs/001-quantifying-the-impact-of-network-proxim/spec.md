# Feature Specification: Quantifying the Impact of Network Proximity on Epidemic Spreading in Scale-Free Networks

**Feature Branch**: `001-network-proximity-epidemic`  
**Created**: 2026-08-10  
**Status**: Draft  
**Input**: User description: "Quantifying the Impact of Network Proximity on Epidemic Spreading in Scale-Free Networks"

## User Scenarios & Testing

### User Story 1 - Reproducible Baseline and Spatial SIR Simulation (Priority: P1) (US-1)

As a computational physicist, I need to run a standard SIR simulation on a real-world scale-free network with and without geographic constraints so that I can establish the baseline epidemic threshold and compare it against the spatially constrained model.

**Why this priority**: This is the core scientific engine of the project. Without a working simulation that correctly implements the topology-only and spatially-modified transmission probabilities, no data can be generated to answer the research question.

**Independent Test**: The system can be tested by executing the simulation script on a small, fixed test network (e.g., a modest number of nodes) and verifying that the output CSV contains the expected columns. (`simulation_id`, `beta_0`, `peak_infection`, `final_size`, `threshold_hit`) and that the spatial model produces different results than the topology-only model for the same $\beta_0$ when $\lambda > 0$.

**Acceptance Scenarios**:

1. **Given** a loaded scale-free network with node coordinates, **When** the simulation runs with $\lambda=0$ (topology-only), **Then** the transmission probability $\beta_{ij}$ is uniform across all edges, and the output records the peak infection rate.

2. **Given** the same network with $\lambda=0.5$, **When** the simulation runs, **Then** the transmission probability $\beta_{ij}$ is scaled by $e^{-0.5 \cdot d_{ij}}$. The reduction in peak infection rate relative to the $\lambda=0$ run must **exceed** the reduction observed in the synthetic‑control (random‑coordinate) condition for the same $\beta_0$, demonstrating a non‑trivial spatial effect. *(See FR-011)*

3. **Given** a configuration where $\beta_0$ is set below the empirically estimated epidemic threshold (as defined in FR-015), **When** 10 Monte Carlo runs are executed, **Then** at least 95% of runs result in no epidemic outbreak (peak infection < 1% of nodes). *(See FR-003)*

4. **Given** the simulation is configured to sweep the base transmission rate $\beta_0$ over the range $[0.01, 0.51]$ in increments of $0.05$ and initialise $5\%$ of nodes as infected, **When** the simulation runs, **Then** the system records the outcome metrics (peak infection, final size, threshold hit) for each $\beta_0$ value across the sweep. *(See FR-013)*

---

### User Story 2 - Statistical Significance and Null Model Generation (Priority: P2) (US-2)

As a researcher, I need to generate a null distribution by randomizing node coordinates and perform statistical tests so that I can quantitatively validate that the observed differences in epidemic thresholds are due to the specific empirical spatial arrangement and not random chance.

**Why this priority**: The research question explicitly asks to isolate the effect of *empirical* proximity. Without the null model (randomized coordinates) and statistical testing, the results are merely descriptive observations rather than a quantified scientific finding.

**Independent Test**: The system can be tested by running the analysis pipeline on a static dataset and verifying that the output includes a computed p‑value, an effect‑size metric (Cohen’s d), and that the result is correctly flagged as “significant” or “not statistically significant” relative to $\alpha = 0.05$ (see FR-010).

**Acceptance Scenarios**:

1. **Given** the results from the empirical spatial simulation, **When** the null model generation runs 10 coordinate randomizations, **Then** the distribution of peak infection rates from the null model is distinct from the empirical model distribution. *(See FR-004)*

2. **Given** results from the empirical spatial model and the null model across the configured runs, **When** a two‑sample permutation test is performed, **Then** the output includes the test statistic, p‑value, and effect size. *(See FR-014)*

3. **Given** a p‑value > 0.05, **When** the results are reported, **Then** the system explicitly flags the finding as “not statistically significant”. *(See FR-010)*

---

### User Story 3 - Resource-Constrained Execution and Sensitivity Analysis (Priority: P3) (US-3)

As a CI/CD engineer, I need the analysis to complete within 6 hours on a 2-core, 7GB RAM runner without GPU usage, while performing a sensitivity analysis on the spatial decay parameter $\lambda$, so that the project remains feasible and the results are robust to parameter choice.

**Why this priority**: The project must pass the compute feasibility gate. If the simulation exceeds memory or time limits, the project cannot reach `research_complete`. Additionally, the methodology panel requires sensitivity analysis for any introduced thresholds or parameters.

**Independent Test**: The system can be tested by running the full pipeline on the GitHub Actions free-tier runner and verifying the job completes successfully (exit code 0) within 6 hours, with memory usage reported under 7GB.

**Acceptance Scenarios**:

1. **Given** a network with >10,000 nodes, **When** the simulation starts, **Then** the system automatically downsamples the network to a size that fits within 7GB RAM (e.g., via subgraph extraction) and logs this action. *(See FR-008)*

2. **Given** the default spatial decay $\lambda=0.1$, **When** the sensitivity analysis runs, **Then** the system sweeps $\lambda$ over the set $\{0.05, 0.1, 0.2\}$ and records how the epidemic threshold shifts for each value. *(See FR-006)*

3. **Given** a total runtime exceeding 5 hours as measured by elapsed wall‑clock time logged after each Monte Carlo batch, **When** the job is still running, **Then** the system reduces the remaining number of Monte Carlo iterations by 50 % (rounded down) to ensure completion before the 6‑hour limit, and logs the reduction. *(See FR-007)*

### Edge Cases

- What happens when the input dataset lacks node coordinates? The system MUST abort and report that a suitable real‑world dataset with geographic coordinates is required; no synthetic coordinates are generated for primary analysis. *(See FR-001)*

- How does the system handle a network where the graph is disconnected? The system MUST simulate on the largest connected component only and record the size of the discarded components. *(See FR-008)*

- What happens if the epidemic threshold is not reached in any of the **configured number of Monte Carlo runs**? The system MUST report the threshold as “undefined” or “> max tested β_0” rather than returning a null value that crashes the statistical analysis. *(See FR-009)*

## Requirements

### Functional Requirements

- **FR-001**: System MUST load a real‑world scale‑free network dataset that includes *genuine* geographic coordinates (e.g., latitude/longitude). If coordinates are missing, the system MUST abort and report that a suitable dataset is required; no synthetic coordinate generation is permitted for the primary analysis. *(See US-1)*

- **FR-002**: System MUST implement a discrete-time SIR model where transmission probability $\beta_{ij}$ is modulated by Euclidean distance $d_{ij}$ via $\beta_{ij} = \beta_0 \cdot e^{-\lambda d_{ij}}$. *(See US-1)*

- **FR-003**: System MUST execute **10** independent Monte Carlo simulations per configuration ($\beta_0$, $\lambda$) to generate robust outcome distributions (See US-2). Ten runs provide ≥ 80 % power to detect a ≥ 0.1 effect size at $\alpha = 0.05$ (convention in epidemiological simulation literature).

- **FR-004**: System MUST generate a null distribution by randomizing node coordinates **10** times while preserving network topology (random uniform sampling in the unit square, independent of topology). *(See US-2)*

- **FR-005**: System MUST perform statistical tests (per FR-014) and calculate effect‑size metrics to compare empirical spatial results against topology‑only and null baselines (See US-2).

- **FR-006**: System MUST perform a sensitivity analysis on the spatial decay parameter $\lambda$ over the set $\{0.05, 0.1, 0.2\}$ to verify result stability (See US-3).

- **FR-007**: System MUST enforce a hard runtime limit of 6 hours and memory limit of 7 GB. If elapsed wall‑clock time exceeds 5 hours, the system MUST halve the remaining Monte Carlo iterations (rounded down) and log the reduction. If memory usage exceeds 6 GB, the system MUST downsample the network to a size that fits within 7 GB RAM and log this action. *(See US-3)*

- **FR-008**: System MUST extract the largest connected component from the loaded network and log the size of any discarded components. *(See US-1)*

- **FR-009**: System MUST report the epidemic threshold as “undefined” or “> max tested β_0” when no outbreak occurs in the configured Monte Carlo runs, providing a sentinel value for downstream analysis. *(See US-2)*

- **FR-010**: System MUST flag statistical findings as “not statistically significant” when the p‑value exceeds 0.05, and include this flag in the output report. *(See US-2)*

- **FR-011**: System MUST generate a synthetic‑control dataset by assigning each node a random 2‑D coordinate sampled uniformly from the unit square, independent of the network topology. This synthetic control is used solely for comparative analysis against the empirical spatial model. *(See US-1)*

- **FR-012**: System MUST generate visualizations: (a) epidemic‑threshold curve vs. $\beta_0$, (b) infection‑trajectory over time, and (c) spatial heatmap of infection spread, saving each as a PNG file. *(See US-1)*

- **FR-013**: System MUST sweep the base transmission rate $\beta_0$ over the range $[0.01, 0.51]$ in increments of $0.05$ and initialise $5\%$ (i.e., $0.05$) of nodes as infected at the start of each simulation. The planned set of simulations, comprising multiple parameter combinations and Monte Carlo repetitions, is expected to fit comfortably within the available computational budget (empirically validated). *(See US-1)*

- **FR-014**: System MUST perform two‑sample permutation (or rank‑based) tests to compare outcome distributions between the empirical spatial model and the null model, reporting test statistic, p‑value, and effect size. *(See US-2)*

- **FR-015**: System MUST estimate the epidemic threshold as the smallest $\beta_0$ at which at least 5 % of nodes become infected in >50 % of Monte Carlo runs, using a binary‑search interpolation over the $\beta_0$ sweep. *(See US-1)*

- **FR-016**: System MUST perform Phase 7 – Contract Validation by checking all pipeline outputs against the JSON‑Schema contracts (e.g., `contracts/simulation_output.schema.yaml`) before final reporting. *(See US-2)*

- **FR-017**: System MUST source a publicly available real‑world scale‑free network with geographic coordinates (e.g., the OpenFlights airline network with airport lat/long) and use it as the primary analysis graph. *(See US-1)*

### Key Entities

- **Network Graph**: A graph structure containing nodes (with optional 2D coordinates) and edges (with weights if available).

- **Simulation Run**: A single execution of the SIR model with specific parameters ($\beta_0, \lambda$, seed) producing a trajectory of infection states.

- **Epidemic Metric**: Aggregated outcomes including epidemic threshold (critical $\beta_0$), peak infection rate, and final outbreak size.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The absolute difference in epidemic threshold between the topology‑only model and the spatially constrained model must be **≥ 0.02** AND the associated p‑value (from the permutation test) must be **≤ 0.05** when compared against the null distribution. *(See US-2)*

- **SC-002**: The peak infection rate reduction under spatial constraints is measured against the baseline topology‑only peak rate to quantify the “barrier effect”. *(See US-1)*

- **SC-003**: The statistical significance of the observed effects is measured against a p‑value threshold of 0.05 using the permutation test defined in FR-014. *(See US-2)*

- **SC-004**: The range of epidemic thresholds across the sensitivity sweep of $\lambda \in \{0.05, 0.1, 0.2\}$ must be **≤ 0.05**. *(See US-3)*

- **SC-005**: The computational feasibility is measured by the successful completion of the full analysis pipeline (with the configured Monte Carlo and null‑run counts) within 6 hours on a 2‑core CPU runner (See US-3).

## Assumptions

- The selected dataset must be a publicly available **real‑world** scale‑free network that includes genuine geographic coordinates (e.g., the OpenFlights airline network, road‑network datasets from OpenStreetMap, or transportation contact networks). If no such dataset can be sourced, the project is out of scope.

- The “free CPU” constraint (2 cores, 7 GB RAM) is sufficient to run the specified Monte Carlo simulations (10 iterations) on networks up to **10 000** nodes; larger networks will be downsampled as per FR‑007.

- The transmission decay function $\beta_{ij} = \beta_0 \cdot e^{-\lambda d_{ij}}$ is a standard approximation for geographic constraints in epidemic modeling within this domain.

- The network assortativity and degree distribution of the selected real‑world datasets do not introduce extreme heterogeneity that prevents SIR model convergence within the simulation steps.

- The null model of randomizing coordinates (uniform sampling) preserves the topological properties of the network sufficiently to isolate the effect of geometry.

- Phase 7 – Contract Validation will be performed after the main analysis to ensure output compliance with the defined JSON‑Schema contracts.
