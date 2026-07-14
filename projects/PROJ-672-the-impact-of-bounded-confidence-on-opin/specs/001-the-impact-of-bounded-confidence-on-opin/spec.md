# Feature Specification: The Impact of Bounded Confidence on Opinion Polarization Speed

**Feature Branch**: `001-gene-regulation`  
**Created**: 2026-07-13  
**Status**: Draft  
**Input**: User description: "To what extent do specific network topologies (e.g., scale-free vs. small-world) disrupt the universal power-law scaling of convergence time in bounded confidence models, and what structural features of the network determine the divergence of the scaling exponent $\gamma$?"

## User Scenarios & Testing

### User Story 1 - Generate Synthetic Network Ensembles (Priority: P1)

The system must generate reproducible ensembles of synthetic networks (Erdős-Rényi, Barabási-Albert, Watts-Strogatz) with exactly $N=500$ nodes to serve as the structural substrate for opinion dynamics. This is the foundational step; without valid, distinct topologies, no simulation can occur.

**Why this priority**: This is the prerequisite for all downstream analysis. If the network generation is non-reproducible or exceeds memory limits, the entire study fails. It is the most critical dependency.

**Independent Test**: Can be tested by generating a single instance of each topology type, calculating its structural metrics (degree distribution, clustering coefficient), and verifying they match the theoretical expectations for $N=500$ within a 5% tolerance, without running any agent simulations.

**Acceptance Scenarios**:

1. **Given** a request to generate a Barabási-Albert network with $N=500$, **When** the generation script executes, **Then** the resulting network must have a power-law degree distribution with a characteristic exponent and an average degree matching the specified parameter $m$.
2. **Given** a request to generate 50 independent instances of a Watts-Strogatz graph with varying rewiring probabilities $p \in \{0.05, 0.1, 0.2\}$, **When** the generation completes, **Then** each instance must have a unique random seed and reproducible structural metrics (average path length, clustering) within the expected range for the specified rewiring probability.
3. **Given** the memory constraints of the runner, **When** 50 networks of $N=500$ are held in memory simultaneously, **Then** the total RAM usage must remain within 7 GB to prevent OOM errors during the batch generation phase.

---

### User Story 2 - Execute Bounded Confidence Simulations (Priority: P2)

The system must execute discrete-time Hegselmann-Krause agent-based simulations on the generated networks, sweeping the confidence threshold $\epsilon$ across a range of values in uniform increments, and measuring the convergence time for each configuration.

**Why this priority**: This is the core experimental engine. It produces the raw data (convergence times) required to test the scaling hypothesis. It is complex and computationally intensive, making it the second most critical component.

**Independent Test**: Can be tested by running a single simulation on a small network ($N=50$) with a fixed $\epsilon$ and verifying that the agents' opinions converge to a stable state (max change $< 10^{-4}$) within a reasonable iteration count, confirming the logic of the update rule.

**Acceptance Scenarios**:

1. **Given** a network of $N=500$ and a confidence threshold $\epsilon=0.2$, **When** the simulation executes for 50 independent seeds, **Then** the system must record the iteration count at which the maximum opinion change across all agents drops below $10^{-4}$ for each seed.
2. **Given** the full sweep of $\epsilon \in [0.05, 0.50]$ with step 0.05, **When** the batch execution completes, **Then** the system must output a dataset containing at least 10 configurations $\times$ 50 seeds = 500 convergence time records per topology type.
3. **Given** a fixed runtime limit of 6 hours, **When** the full simulation suite (3 topologies $\times$ 10 $\epsilon$ values $\times$ 50 seeds) is executed, **Then** the total wall-clock time must not exceed 5 hours to allow for data processing and plotting.

---

### User Story 3 - Analyze Scaling Laws and Structural Correlations (Priority: P3)

The system must fit a power-law model to the convergence time data for each topology within the critical regime and perform a multiple linear regression to determine if the extracted scaling exponent $\gamma$ correlates with structural metrics (assortativity, path length), while accounting for variance in the critical point $\epsilon_c$.

**Why this priority**: This is the analytical phase that answers the research question. It relies entirely on the outputs of US-1 and US-2. While essential for the final result, it is logically downstream of data generation.

**Independent Test**: Can be tested by providing a synthetic dataset of convergence times and structural metrics, verifying that the regression model correctly identifies a known correlation (e.g., $\gamma \propto$ assortativity) and that the power-law fit $R^$ exceeds 0.8.

**Acceptance Scenarios**:

1. **Given** the convergence time data for a specific topology, **When** the power-law fitting algorithm runs on the critical regime ($\epsilon \in [\epsilon_c + 0.05, 0.50]$), **Then** it must output the scaling exponent $\gamma$, the critical threshold $\epsilon_c$, and a standard error estimate (calculated via bootstrapping with 1000 resamples) where the standard error must be < 0.1 for the fit to be considered valid.
2. **Given** the set of $\gamma$ values, corresponding network metrics, and $\epsilon_c$ estimates from 50 network instances per topology, **When** the multiple linear regression is performed with topology type as a categorical variable, **Then** the model must output the coefficients for path length and assortativity, along with the p-values for statistical significance.
3. **Given** the results, **When** the visualization module runs, **Then** it must generate a scatter plot of $\gamma$ vs. assortativity with a fitted regression line and a plot of convergence time vs. $\epsilon$ on a log-log scale restricted to the critical regime.

---

### Edge Cases

- **Non-convergence**: What happens if the simulation does not converge within the maximum iteration limit ([deferred] iterations) for a specific $\epsilon$? The system must flag this as "non-convergent" and exclude it from the power-law fit, rather than crashing or returning an arbitrary large number.
- **Threshold boundary**: How does the system handle $\epsilon$ values very close to the critical threshold $\epsilon_c$ where convergence time diverges? The system must implement a robust outlier detection mechanism to identify and handle these divergent points without skewing the regression.
- **Memory overflow**: How does the system handle the scenario where a specific network topology (e.g., highly dense random graph) causes the agent state matrix to exceed available RAM? The system must detect this and switch to a disk-backed or chunked processing mode, or fail gracefully with a clear error message.

## Requirements

### Functional Requirements

- **FR-001**: System MUST generate synthetic networks (Erdős-Rényi, Barabási-Albert, Watts-Strogatz) with exactly $N=500$ nodes and reproducible random seeds (See US-1).
- **FR-002**: System MUST implement the discrete-time Hegselmann-Krause update rule where agents only adjust opinions if $|x_i - x_j| \le \epsilon$ (See US-2).
- **FR-003**: System MUST sweep the confidence threshold $\epsilon$ across a range of values $\epsilon \in [0.05, 0.50]$ with step 0.05 and execute 50 independent simulation runs per configuration (See US-2).
- **FR-004**: System MUST measure convergence time as the number of iterations until the maximum opinion change across all agents falls below $10^{-4}$ (See US-2).
- **FR-005**: System MUST detect the critical threshold $\epsilon_c$ and fit a power-law model $T = A(\epsilon - \epsilon_c)^{-\gamma}$ to the convergence time data only within the critical regime $\epsilon \in [\epsilon_c + 0.05, 0.50]$ for each topology and extract $\gamma$ (See US-3).
- **FR-006**: System MUST perform multiple linear regression to test the correlation between $\gamma$ and structural metrics (assortativity, average path length), including $\epsilon_c$ as a covariate and modeling topology type as a categorical variable (See US-3).
- **FR-007**: System MUST enforce a maximum iteration limit per simulation run to prevent infinite loops (See Edge Cases).
- **FR-008**: System MUST implement a sensitivity analysis for the convergence threshold $10^{-4}$ by sweeping it over a range of $10^{-3}$ to $10^{-5}$ and reporting the variation in $\gamma$ to isolate topological effects from numerical noise (See Methodological Soundness: Threshold Justification).

### Key Entities

- **NetworkInstance**: Represents a generated graph with attributes: topology_type, node_count, edge_count, assortativity, average_path_length, clustering_coefficient, rewiring_probability (if applicable).
- **SimulationRun**: Represents a single execution of the opinion dynamics model with attributes: seed, epsilon, convergence_time, final_opinion_clusters, status (converged/non-converged).
- **ScalingResult**: Represents the fitted parameters for a topology with attributes: topology_type, gamma, epsilon_c, r_squared, standard_error.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The power-law fit $R^2$ for the convergence time vs. $\epsilon$ relationship is measured against a threshold of $\ge 0.8$ for at least two of the three topology types (See US-3, FR-005).
- **SC-002**: The multiple linear regression model identifies at least one structural metric (assortativity or path length) with a p-value $< 0.05$ as a significant predictor of $\gamma$ (See US-3, FR-006).
- **SC-003**: The total wall-clock time for the full simulation suite (3 topologies $\times$ 10 $\epsilon$ values $\times$ 50 seeds) is measured against the 6-hour limit, ensuring completion within 5 hours (See US-2, FR-002).
- **SC-004**: The sensitivity analysis of the convergence threshold (sweeping $10^{-3}$ to $10^{-5}$) shows that the variation in $\gamma$ is < 5% across the sweep, confirming robustness (See US-3, FR-008).
- **SC-005**: The memory usage during the generation of 50 networks and simultaneous simulation runs is measured against the 7 GB RAM limit, ensuring no OOM errors occur (See US-1, FR-001).

## Assumptions

- The synthetic network generation using NetworkX with $N=500$ nodes will fit within the 7 GB RAM limit of the GitHub Actions runner.
- The Hegselmann-Krause model implementation in Python will execute efficiently enough on a CPU-only environment to complete 1,500 simulation runs within 5 hours.
- The power-law scaling relationship $T \propto (\epsilon - \epsilon_c)^{-\gamma}$ is theoretically valid for the bounded confidence model in the critical regime of interest, allowing for meaningful regression analysis.
- The structural metrics (assortativity, path length) calculated by NetworkX are sufficient to capture the relevant topological features influencing opinion dynamics.
- The random number generator in Python's `random` module provides sufficient entropy for generating 50 independent simulation seeds per configuration.
- The convergence threshold is a standard and appropriate criterion for determining stability in bounded confidence models, as supported by the literature.
- The GitHub Actions free-tier runner will not be preempted or throttled to the point of exceeding the 6-hour runtime limit.