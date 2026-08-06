# Feature Specification: Investigating the Impact of Network Structure on Energy Dissipation in Driven Oscillators

**Feature Branch**: `001-investigate-network-dissipation`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Investigating the Impact of Network Structure on Energy Dissipation in Driven Oscillators"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate Topological Networks and Compute Metrics (Priority: P1)

The researcher needs to generate a diverse set of synthetic oscillator network topologies (random, scale-free, small-world) with a fixed node count (N=100-200) and compute their static structural metrics (clustering coefficient, average path length, degree distribution) to serve as the independent variables for the study.

**Why this priority**: This is the foundational data generation step. Without a controlled, reproducible set of topologies with known metrics, no simulation of physics or correlation analysis can occur. It is the prerequisite for all subsequent steps.

**Independent Test**: Can be fully tested by running the network generation script and verifying that the output CSV contains exactly the requested number of network realizations, that each row contains valid graph metrics (e.g., clustering coefficient between 0 and 1), and that the topological classes are correctly labeled.

**Acceptance Scenarios**:

1. **Given** the user requests 50 random graphs with N=100 nodes, **When** the generation script executes, **Then** the output file contains 50 rows, each with a unique graph ID, a label "random", and computed metrics (average degree, clustering coefficient) that match theoretical expectations for Erdős-Rényi graphs within a 5% tolerance.
2. **Given** the user requests scale-free networks, **When** the script executes, **Then** the generated adjacency matrices exhibit a power-law degree distribution with a scaling exponent between 2.0 and 3.0, and the "average path length" metric is recorded for each instance.
3. **Given** the user requests small-world networks, **When** the script executes, **Then** the generated graphs exhibit a high clustering coefficient (significantly higher than random graphs of same density) and a short average path length comparable to random graphs.

---

### User Story 2 - Simulate Driven Damped Oscillator Dynamics and Extract Decay Rates (Priority: P2)

The researcher needs to numerically integrate the equations of motion for a coupled harmonic oscillator system on each generated topology, applying external driving forces and damping terms, to calculate the steady-state energy dissipation rate for each network configuration.

**Why this priority**: This implements the core physical model. It transforms the static graph structures into dynamic energy profiles. The accuracy of the decay rate extraction determines the validity of the final correlation analysis.

**Independent Test**: Can be fully tested by running the simulation on a single, known topology (e.g., a ring graph) with fixed parameters, verifying that the total system energy decays exponentially over time, and that the computed decay rate matches the analytical solution for a simple damped harmonic oscillator within a 1% numerical error margin.

**Acceptance Scenarios**:

1. **Given** a network topology and a set of physical parameters (mass, spring constant, damping coefficient, driving frequency), **When** the `solve_ivp` integration runs for a duration of T=100 time units, **Then** the system energy time-series shows a clear exponential decay phase after the initial transient, and the fitted decay rate is output with a goodness-of-fit (R²) ≥ 0.95.
2. **Given** a specific network with high damping, **When** the simulation runs, **Then** the energy decay rate is numerically higher than that of the same network with low damping, confirming the simulation responds correctly to parameter changes.
3. **Given** the simulation is run on a CPU-only environment, **When** the integration completes, **Then** the process consumes ≤ 7 GB of RAM and finishes within 30 minutes for a batch of 10 networks, ensuring feasibility within the 6-hour CI budget.

---

### User Story 3 - Perform Statistical Correlation Analysis and Sensitivity Testing (Priority: P3)

The researcher needs to perform multiple linear regression to correlate topological metrics with dissipation rates, apply corrections for multiple comparisons, and conduct a sensitivity analysis on the regression thresholds to validate the robustness of the findings.

**Why this priority**: This synthesizes the data to answer the research question. It moves from raw numbers to scientific inference, ensuring the results are statistically sound and not artifacts of arbitrary threshold choices.

**Independent Test**: Can be fully tested by feeding a pre-generated dataset of metrics and decay rates into the analysis module, verifying that the regression output includes p-values, confidence intervals, and a Bonferroni-corrected significance table, and that the sensitivity analysis produces a report showing how the significance of top predictors changes across a defined threshold sweep.

**Acceptance Scenarios**:

1. **Given** a dataset of 50+ network realizations with topological metrics and decay rates, **When** the regression analysis runs, **Then** the output includes a table of coefficients, standard errors, and p-values for each metric, with p-values corrected for family-wise error rate (e.g., Bonferroni or Holm-Bonferroni method).
2. **Given** a specific threshold for "significant correlation" (e.g., p < 0.05), **When** the sensitivity analysis runs, **Then** the system sweeps the threshold across {0.01, 0.05, 0.1} and outputs a summary showing the variation in the number of significant predictors and the stability of the coefficient signs.
3. **Given** the analysis detects high collinearity between two metrics (e.g., degree and clustering), **When** the diagnostic runs, **Then** the system flags the collinearity (VIF > 5) and reports the joint relationship descriptively rather than claiming independent predictive effects for both.

---

### Edge Cases

- What happens if the numerical integration fails to converge for a specific stiff network topology (e.g., a scale-free network with extreme degree disparity)? The system must detect non-convergence, log the specific graph ID, and exclude it from the final analysis rather than crashing.
- How does the system handle a network where the driving frequency matches a natural mode, causing resonance instead of decay? The system must identify the energy growth (negative decay rate) and flag these instances as "resonant" rather than "dissipative" to avoid skewing the regression.
- What happens if the dataset size is insufficient for the multiple linear regression (e.g., fewer than 10 samples per predictor)? The system must halt and report a power limitation warning rather than producing spurious statistical results.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST generate synthetic network topologies (random, scale-free, small-world) with a fixed node count N ∈ [100, 200] and compute static metrics (clustering coefficient, average path length, degree distribution) for each instance (See US-1).
- **FR-002**: System MUST numerically integrate the coupled harmonic oscillator equations of motion using `scipy.integrate.solve_ivp` on CPU, applying external driving forces and damping terms, and output the total system energy time-series (See US-2).
- **FR-003**: System MUST extract the energy decay rate from the time-series data by fitting an exponential decay model and validating the fit quality (R² ≥ 0.95) before accepting the value (See US-2).
- **FR-004**: System MUST perform multiple linear regression to identify correlations between topological metrics and decay rates, and apply a multiple-comparison correction method (e.g., Bonferroni) to the resulting p-values (See US-3).
- **FR-005**: System MUST execute a sensitivity analysis on the significance threshold (sweeping p ∈ {0.01, 0.05, 0.1}) and report how the count of significant predictors varies across the sweep (See US-3).
- **FR-006**: System MUST detect and flag instances of high predictor collinearity (Variance Inflation Factor > 5) and frame the results descriptively rather than claiming independent causal effects (See US-3).
- **FR-007**: System MUST ensure the entire simulation and analysis pipeline for 50+ network realizations completes within 6 hours on a standard CPU-only environment with ≤ 7 GB RAM (See US-2).

### Key Entities

- **NetworkTopology**: A graph structure representing the oscillator network, defined by an adjacency matrix and a set of static metrics (clustering, path length, degree distribution).
- **EnergyTimeSeries**: A time-ordered sequence of total system energy values generated by the numerical integration of the equations of motion.
- **DecayRate**: A scalar value representing the rate of energy dissipation, derived from the exponential fit of the EnergyTimeSeries.
- **RegressionResult**: A statistical object containing coefficients, standard errors, p-values (corrected), and confidence intervals linking topological metrics to decay rates.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The number of successfully generated network topologies is measured against the target of 50+ realizations across 5 topological classes (See FR-001).
- **SC-002**: The goodness-of-fit (R²) of the exponential decay model is measured against the threshold of 0.95 for accepted decay rates (See FR-003).
- **SC-003**: The statistical significance of topological predictors is measured against the family-wise error corrected p-value threshold (e.g., p < 0.05) to determine if a correlation exists (See FR-004).
- **SC-004**: The stability of the regression results is measured by the variance in the number of significant predictors across the sensitivity threshold sweep (p ∈ {0.01, 0.05, 0.1}) (See FR-005).
- **SC-005**: The computational efficiency is measured by the total wall-clock time required to process the full dataset, ensuring it remains ≤ 6 hours (See FR-007).

## Assumptions

- The dataset variable fit is valid: The synthetic network generation (NetworkX) and the coupled oscillator model (scipy) provide all necessary variables (topological metrics, energy, time) without missing data; no external empirical dataset is required for this simulation study.
- The inference framing is associational: Since the study uses synthetic data and no random assignment to "real-world" conditions, findings regarding topology and dissipation will be framed as statistical associations, not causal claims.
- The power analysis is deferred: While 50+ samples are targeted, the exact power calculation for the specific effect size is deferred to the analysis phase; the sample size is chosen to be computationally feasible within the 6-hour CI budget.
- The threshold justification is community-standard: The p < 0.05 significance threshold is used based on standard statistical practice; the sensitivity analysis will sweep this value to test robustness.
- The measurement validity is ensured by simulation: Since the "measurements" are derived from deterministic differential equations, the validity of the dissipation rate depends on the numerical stability of the solver, not on instrument calibration.
- The predictor collinearity is handled: The assumption is that topological metrics may be correlated; the analysis will explicitly check for this and adjust the interpretation accordingly.
- The compute feasibility is guaranteed: The simulation uses CPU-only methods (scipy) and moderate data sizes (N=200 nodes) that are known to fit within the 7 GB RAM and 6-hour time limits of the free-tier GitHub Actions runner.
