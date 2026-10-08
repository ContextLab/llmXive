# Feature Specification: Quantifying the Impact of Network Proximity on Epidemic Spreading in Scale-Free Networks

**Feature Branch**: `001-gene-regulation`  
**Created**: 2026-08-10  
**Status**: Draft  
**Input**: User description: "Quantifying the Impact of Network Proximity on Epidemic Spreading in Scale-Free Networks"

## User Scenarios & Testing

### User Story 1 - Reproducible Baseline and Spatial SIR Simulation (Priority: P1)

As a computational physicist, I need to run a standard SIR simulation on a real-world scale-free network with and without geographic constraints so that I can establish the baseline epidemic threshold and compare it against the spatially constrained model.

**Why this priority**: This is the core scientific engine of the project. Without a working simulation that correctly implements the topology-only and spatially-modified transmission probabilities, no data can be generated to answer the research question.

**Independent Test**: The system can be tested by executing the simulation script on a small, fixed test network (e.g., 100 nodes) and verifying that the output CSV contains the expected columns (`simulation_id`, `beta`, `peak_infection`, `final_size`, `threshold_hit`) and that the spatial model produces different results than the topology-only model for the same $\beta$ when $\lambda > 0$.

**Acceptance Scenarios**:

1. **Given** a loaded scale-free network with node coordinates, **When** the simulation runs with $\lambda=0$ (topology-only), **Then** the transmission probability $\beta_{ij}$ is uniform across all edges, and the output records the peak infection rate.
2. **Given** the same network with $\lambda=0.5$, **When** the simulation runs, **Then** the transmission probability $\beta_{ij}$ is scaled by $e^{-0.5 \cdot d_{ij}}$, resulting in a lower peak infection rate compared to the $\lambda=0$ run for the same base $\beta_0$.
3. **Given** a configuration where $\beta_0$ is below the theoretical epidemic threshold, **When** 50 Monte Carlo runs are executed, **Then** at least 95% of runs result in no epidemic outbreak (peak infection < 1% of nodes).

---

### User Story 2 - Statistical Significance and Null Model Generation (Priority: P2)

As a researcher, I need to generate a null distribution by randomizing node coordinates and perform paired t-tests so that I can statistically validate that the observed differences in epidemic thresholds are due to the specific empirical spatial arrangement and not random chance.

**Why this priority**: The research question explicitly asks to isolate the effect of *empirical* proximity. Without the null model (randomized coordinates) and statistical testing, the results are merely descriptive observations rather than a quantified scientific finding.

**Independent Test**: The system can be tested by running the analysis pipeline on a static dataset and verifying that the output includes a p-value < 0.05 (or appropriate alpha) for the difference between the empirical spatial model and the randomized coordinate baseline, and that the Cohen's d effect size is calculated.

**Acceptance Scenarios**:

1. **Given** the results from the empirical spatial simulation, **When** the null model generation runs 100 coordinate randomizations, **Then** the distribution of peak infection rates from the null model is distinct from the empirical model distribution.
2. **Given** paired results from the topology-only and spatial models across 50 simulations, **When** a paired t-test is performed, **Then** the output includes the t-statistic, p-value, and Cohen's d effect size.
3. **Given** a p-value > 0.05, **When** the results are reported, **Then** the system explicitly flags the finding as "not statistically significant" rather than claiming a difference.

---

### User Story 3 - Resource-Constrained Execution and Sensitivity Analysis (Priority: P3)

As a CI/CD engineer, I need the analysis to complete within 6 hours on a 2-core, 7GB RAM runner without GPU usage, while performing a sensitivity analysis on the spatial decay parameter $\lambda$, so that the project remains feasible and the results are robust to parameter choice.

**Why this priority**: The project must pass the compute feasibility gate. If the simulation exceeds memory or time limits, the project cannot reach `research_complete`. Additionally, the methodology panel requires sensitivity analysis for any introduced thresholds or parameters.

**Independent Test**: The system can be tested by running the full pipeline on the GitHub Actions free-tier runner and verifying the job completes successfully (exit code 0) within 6 hours, with memory usage reported under 7GB.

**Acceptance Scenarios**:

1. **Given** a network with >10,000 nodes, **When** the simulation starts, **Then** the system automatically downsamples the network to a size that fits within 7GB RAM (e.g., via subgraph extraction) and logs this action.
2. **Given** the default spatial decay $\lambda=0.1$, **When** the sensitivity analysis runs, **Then** the system sweeps $\lambda$ over the set $\{0.05, 0.1, 0.2\}$ and records how the epidemic threshold shifts for each value.
3. **Given** a total runtime exceeding 5 hours, **When** the job is still running, **Then** the system reduces the number of Monte Carlo iterations (e.g., from 50 to 20) to ensure completion before the 6-hour limit, logging the reduction.

---

### Edge Cases

- What happens when the input dataset lacks node coordinates? The system MUST assign 2D positions using Multidimensional Scaling (MDS) on the adjacency matrix and log this as a synthetic coordinate generation.
- How does the system handle a network where the graph is disconnected? The system MUST simulate on the largest connected component only and record the size of the discarded components.
- What happens if the epidemic threshold is not reached in any of the 50 Monte Carlo runs? The system MUST report the threshold as "undefined" or "> max tested beta" rather than returning a null value that crashes the statistical analysis.

## Requirements

### Functional Requirements

- **FR-001**: System MUST load a real-world scale-free network dataset and parse node coordinates, defaulting to MDS-generated coordinates if missing (See US-1).
- **FR-002**: System MUST implement a discrete-time SIR model where transmission probability $\beta_{ij}$ is modulated by Euclidean distance $d_{ij}$ via $\beta_{ij} = \beta_0 \cdot e^{-\lambda d_{ij}}$ (See US-1).
- **FR-003**: System MUST execute 50 independent Monte Carlo simulations per configuration ($\beta_0$, $\lambda$) to generate robust outcome distributions (See US-2).
- **FR-004**: System MUST generate a null distribution by randomizing node coordinates 100 times while preserving network topology (See US-2).
- **FR-005**: System MUST perform paired t-tests and calculate Cohen's d effect sizes to compare empirical spatial results against topology-only and null baselines (See US-2).
- **FR-006**: System MUST perform a sensitivity analysis on the spatial decay parameter $\lambda$ over the set $\{0.05, 0.1, 0.2\}$ to verify result stability (See US-3).
- **FR-007**: System MUST enforce a hard runtime limit of 6 hours and memory limit of 7GB by dynamically adjusting simulation count or network size if necessary (See US-3).

### Key Entities

- **Network Graph**: A graph structure containing nodes (with optional 2D coordinates) and edges (with weights if available).
- **Simulation Run**: A single execution of the SIR model with specific parameters ($\beta_0, \lambda$, seed) producing a trajectory of infection states.
- **Epidemic Metric**: Aggregated outcomes including epidemic threshold (critical $\beta$), peak infection rate, and final outbreak size.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The difference in epidemic threshold between the topology-only model and the spatially constrained model is measured against the null distribution generated by randomized coordinates (See US-2).
- **SC-002**: The peak infection rate reduction under spatial constraints is measured against the baseline topology-only peak rate to quantify the "barrier effect" (See US-1).
- **SC-003**: The statistical significance of the observed effects is measured against a p-value threshold of 0.05 using paired t-tests (See US-2).
- **SC-004**: The robustness of the findings is measured by the variation in the epidemic threshold across the sensitivity sweep of $\lambda \in \{0.05, 0.1, 0.2\}$ (See US-3).
- **SC-005**: The computational feasibility is measured by the successful completion of the full analysis pipeline (including 50 simulations + 100 null runs) within 6 hours on a 2-core CPU runner (See US-3).

## Assumptions

- The OpenML or HuggingFace datasets selected for this study contain sufficient node metadata to either provide coordinates or allow for geocoding; if not, MDS is assumed to be a valid proxy for spatial embedding.
- The "free CPU" constraint (2 cores, 7GB RAM) is sufficient to run the specified Monte Carlo simulations (50 iterations) on networks up to [deferred] nodes; larger networks will be downsampled.
- The transmission decay function $\beta_{ij} = \beta_0 \cdot e^{-\lambda d_{ij}}$ is a valid and standard approximation for geographic constraints in epidemic modeling within this domain.
- The network assortativity and degree distribution of the selected real-world datasets do not introduce such extreme heterogeneity that the SIR model fails to converge within the simulation steps.
- The null model of randomizing coordinates preserves the topological properties of the network sufficiently to isolate the effect of geometry.
