# Feature Specification: Exploring the Role of Network Topology on Synchronization in Coupled Oscillators

**Feature Branch**: `001-explore-network-topology-synchronization`  
**Created**: 2026-06-25  
**Status**: Draft  
**Input**: User description: "Exploring the Role of Network Topology on Synchronization in Coupled Oscillators"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate Rewired Network Instances (Priority: P1)

The researcher needs to generate a sequence of network graphs with varying small-world rewiring probabilities to serve as the structural basis for simulation. This is the foundational step; without valid topologies, no dynamics can be simulated. The base graph is the 'ca-AstroPh' citation network from SNAP, which is first reconstructed as a regular ring lattice to ensure the Watts-Strogatz rewiring parameter retains its standard theoretical meaning.

**Why this priority**: This is the primary data generation step. If the network generation fails or produces invalid graphs (e.g., disconnected components where synchronization is impossible), the entire experiment halts.

**Independent Test**: The system can be tested by generating multiple network instances with rewiring probabilities ranging from 0.0 to 1.0 and verifying that each graph is connected, has the correct number of nodes (N=500), and preserves the average degree of the reconstructed lattice before any simulation runs.

**Acceptance Scenarios**:

1. **Given** a base citation network graph (ca-AstroPh from SNAP) reconstructed as a regular ring lattice with N=500 nodes, **When** the system applies the Watts-Strogatz algorithm with a rewiring probability of 0.0, **Then** the output graph is topologically identical to the base lattice structure.
2. **Given** a base citation network graph reconstructed as a regular ring lattice, **When** the system applies the algorithm with a rewiring probability of 0.5, **Then** the output graph exhibits a mix of local clustering and short path lengths characteristic of small-world networks.
3. **Given** a base citation network graph reconstructed as a regular ring lattice, **When** the system applies the algorithm with a rewiring probability of 1.0, **Then** the output graph is a random graph with minimal local clustering.

---

### User Story 2 - Simulate Kuramoto Dynamics and Detect Synchronization (Priority: P2)

The researcher needs to simulate the Kuramoto oscillator dynamics on each generated network and determine the critical coupling strength where global synchronization emerges. This transforms static topology into dynamic behavior.

**Why this priority**: This is the core scientific engine. It translates the structural input (topology) into the observable output (synchronization state).

**Independent Test**: 
1. The system can be tested by running the simulation on a known topology (e.g., a fully connected graph) with a high coupling strength and verifying that the Kuramoto order parameter converges to a value indicating global synchronization.
2. The system can be tested by running the binary search algorithm on a synthetic dataset with a known critical coupling strength and verifying that the detected value is within an acceptable tolerance of the true value.

**Acceptance Scenarios**:

1. **Given** a network with a specific coupling strength, **When** the simulation runs for 10,000 time steps, **Then** the system computes the Kuramoto order parameter $R$ at the final time step.
2. **Given** a network and a coupling strength below the critical threshold, **When** the simulation completes, **Then** the order parameter $R$ remains near 0.0 (incoherent state).
3. **Given** a network and a configurable coupling threshold, **When** the simulation completes, **Then** the system correctly identifies the critical coupling strength based on the configured threshold or the maximum of dR/dK.

---

### User Story 3 - Quantify Topological Influence via Statistical Correlation (Priority: P3)

The researcher needs to analyze the relationship between the rewiring probability (topology) and the critical coupling strength (dynamics) to quantify the effect of small-world structures. This provides the final scientific insight.

**Why this priority**: This is the analysis and reporting layer. It synthesizes the results from the previous steps to answer the research question.

**Independent Test**: The system can be tested by generating synthetic data with a known non-linear relationship between rewiring probability and critical coupling strength and verifying that the Spearman correlation coefficient calculated by the system matches the expected value within an acceptable margin.

**Acceptance Scenarios**:

1. **Given** a dataset of (rewiring probability, critical coupling strength) pairs from multiple simulation runs, **When** the analysis script executes, **Then** it calculates the Spearman correlation coefficient and its p-value.
2. **Given** the calculated p-value, **When** it is less than 0.05, **Then** the system flags the correlation as statistically significant.
3. **Given** the results, **When** the system generates the summary plot, **Then** the plot displays critical coupling strength on the y-axis and rewiring probability on the x-axis with a trend line.

---

### Edge Cases

- **Disconnected Graphs**: What happens if the rewiring process (especially at high probabilities or specific base graphs) results in a disconnected network? The system must detect this and either skip the simulation for that instance or assign an infinite critical coupling strength, logging the event.
- **Numerical Instability**: How does the system handle numerical integration errors in `scipy.integrate.odeint` if the time step is too large or the coupling strength is extreme? The system must implement a maximum iteration limit or adaptive step size to prevent infinite loops.
- **Zero Variance**: In the case where the order parameter variance is zero across runs (unlikely but possible for extreme cases), the statistical significance test must handle division-by-zero errors gracefully.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST generate multiple network instances using the Watts-Strogatz algorithm with rewiring probabilities linearly spaced between 0.0 and 1.0, starting from a regular ring lattice reconstruction of the ca-AstroPh dataset (See US-1).
- **FR-002**: System MUST validate that every generated network instance is connected before proceeding to simulation, skipping disconnected instances and logging a warning (See US-1).
- **FR-003**: System MUST simulate Kuramoto oscillator dynamics for N=500 nodes for [deferred] time steps using `scipy.integrate.odeint` in double precision (See US-2).
- **FR-004**: System MUST determine the critical coupling strength for each topology by performing a binary search or linear sweep of the coupling parameter until the order parameter $R$ exceeds a configurable threshold (default 0.5) OR the maximum of dR/dK is detected, with a tolerance of ≤ 0.01 and a maximum of 100 iterations (See US-2).
- **FR-005**: System MUST compute the Spearman rank correlation coefficient and p-value between the rewiring probability and the critical coupling strength across all valid simulation runs, with Pearson correlation as a secondary check (See US-3).
- **FR-006**: System MUST apply a multiple-comparison correction (e.g., Bonferroni or Benjamini-Hochberg) if multiple statistical hypotheses are tested simultaneously, or explicitly state the correction method used based on the statistical model (See US-3).
- **FR-007**: System MUST perform a sensitivity analysis by sweeping the order parameter threshold over a representative range of values. and report the variation in the headline correlation rate (See US-3).
- **FR-008**: System MUST explicitly define the statistical model (single regression vs. multiple tests) used for the analysis and justify the choice of multiple-comparison correction accordingly (See US-3).
- **FR-009**: System MUST verify the rotational invariance of the critical coupling strength by testing against different phase reference frames (e.g., single oscillator vs. center-of-mass) and confirm the results are identical within a negligible tolerance (See Assumptions).

### Key Entities

- **Network Instance**: A graph object defined by its node count (N=500), edge list, and specific rewiring probability parameter, derived from a regular ring lattice reconstruction of the ca-AstroPh dataset.
- **Simulation Run**: A specific execution of the Kuramoto model on a Network Instance with a defined coupling strength, resulting in a time series of phases and a final order parameter.
- **Critical Coupling Point**: The specific coupling strength value identified as the transition point from incoherence to synchronization for a given Network Instance, determined via configurable threshold or dR/dK maximization.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The sample variance of the final Kuramoto order parameter $R$ values across 1000 simulation runs per topology is measured against the threshold of 0.01 to ensure statistical stability (See US-2).
- **SC-002**: The Spearman correlation between rewiring probability and critical coupling strength is measured against the significance level of p < 0.05 to confirm the relationship (See US-3).
- **SC-003**: The computational runtime for the full suite of simulations (50 topologies × 10,000 steps) is measured against the constraint of ≤ 6 hours on a github.com actions runner type ubuntu-latest (2-core CPU, 7GB RAM), as defined in 'Assumption about Compute Feasibility' (See Assumptions).
- **SC-004**: The sensitivity of the critical coupling threshold to the order parameter cutoff is measured by sweeping the cutoff over the set {0.4, 0.5, 0.6} (as defined in 'Assumption about Threshold Justification') and verifying that the variation in the headline correlation rate is ≤ 5% (See Assumptions).

## Assumptions

- **Assumption about Dataset-Variable Fit**: The base citation network from SNAP (ca-AstroPh) is first reconstructed as a regular ring lattice to ensure the Watts-Strogatz rewiring parameter retains its standard theoretical meaning; if the base graph is already too random, the rewiring range may be adjusted to [0.0, 0.2] to preserve the "small-world" regime, but this will be recorded as a scope limitation.
- **Assumption about Inference Framing**: Since the study involves observational analysis of network properties without random assignment of nodes to specific roles, all findings regarding the relationship between topology and synchronization are framed as **associational**, not causal.
- **Assumption about Compute Feasibility**: The simulation of N=500 nodes for 10,000 steps using `scipy` in double precision on a 2-core CPU runner will complete within the 6-hour limit; If the runtime exceeds a reasonable threshold during a dry run, the time steps may be reduced as a fallback optimization., but this must be logged and reported as a contingency, and the primary success criteria (SC-003) remains defined for the [deferred]-step run.
- **Assumption about Threshold Justification**: The order parameter threshold of 0.5 for defining "synchronization" is based on community standards in the Kuramoto literature; a sensitivity analysis sweeping the threshold over {0.4, 0.5, 0.6} is required to ensure the headline correlation is not an artifact of this specific cutoff.
- **Assumption about Measurement Validity**: The Kuramoto model parameters (natural frequencies, coupling strength) are treated as abstract variables; no specific real-world units (e.g., Hz) are required, but the relative scaling must be consistent across all runs.
- **Assumption about Observer Invariance**: The critical coupling strength is assumed to be invariant to the choice of phase reference frame (single oscillator vs. center-of-mass), as the order parameter $R$ is a rotationally invariant metric; this invariance is explicitly verified by FR-009.