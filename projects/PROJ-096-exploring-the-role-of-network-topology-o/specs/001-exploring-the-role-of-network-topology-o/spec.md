# Specification: Exploring the Role of Network Topology on Synchronization in Coupled Oscillators

## 1. Introduction

This project investigates the relationship between network topology and the synchronization properties of coupled oscillators, specifically focusing on the Kuramoto model. The primary goal is to determine how the small-world rewiring probability ($p$) affects the critical coupling strength ($K_c$) required for synchronization.

## 2. Research Question

What is the quantitative relationship between the small-world rewiring probability ($p$) and the critical coupling strength ($K_c$) in a network of $N=500$ coupled oscillators?

## 3. Functional Requirements

### FR-001: Base Graph Generation
The system MUST generate a synthetic regular ring lattice of N=500 nodes as the base topology. This base graph is then subjected to the Watts-Strogatz rewiring process with varying probabilities $p \in [0.0, 1.0]$.

**Note**: The original requirement to use the 'ca-AstroPh' dataset has been formally amended. As documented in `docs/constitutional_amendment.md` and `specs/001-exploring-the-role-of-network-topology-o/constitution.md`, the use of a real-world citation network as a base for a regular lattice reconstruction is methodologically incoherent. The base graph MUST be a synthetic regular ring lattice generated with $N=500$ and degree $k=2$.

### FR-002: Connectivity Validation
The system MUST validate that every generated network instance is connected. Disconnected graphs MUST be logged and excluded from the simulation batch.

### FR-003: Kuramoto Simulation
The system MUST simulate the Kuramoto model dynamics on each valid topology. The simulation must support configurable time steps and coupling strengths.

### FR-004: Critical Coupling Detection
The system MUST determine the critical coupling strength ($K_c$) for each topology using a binary search algorithm, with a fallback to a linear sweep if convergence fails.

### FR-005: Order Parameter Calculation
The system MUST calculate the complex order parameter $R(t)$ and its time-averaged magnitude $\langle R \rangle$ to quantify the level of synchronization.

### FR-006: Statistical Analysis
The system MUST compute the Spearman correlation coefficient and p-value between the rewiring probability $p$ and the detected $K_c$ values.

### FR-007: Sensitivity Analysis
The system MUST perform a sensitivity analysis by sweeping the synchronization threshold over the set $\{0.4, 0.5, 0.6\}$ to verify the robustness of the correlation results.

### FR-008: Statistical Model Documentation
The system MUST explicitly document the statistical model used (e.g., single regression vs. multiple tests) and any multiple-comparison corrections applied in the final report.

### FR-009: Rotational Invariance Verification
The system MUST verify that the calculated $K_c$ is invariant under a change of phase reference frame. This involves comparing $K_c$ values derived using a "single oscillator" reference frame versus a "center-of-mass" reference frame.

## 4. Non-Functional Requirements

### SC-001: Stability
The simulation results must be stable across multiple runs with different random seeds for initial phases. The variance of the order parameter must remain below a defined threshold.

### SC-002: Reproducibility
All random number generators must be seeded with documented values. All generated graphs and simulation results must be saved with metadata including the seed and parameters used.

### SC-003: Runtime Constraint
The full experiment (generation, simulation, and analysis) must complete within 6 hours on a standard 2-core CPU runner. If this is not feasible, a contingency plan must be logged, and the scope reduced accordingly.

## 5. Data Model

- **Graph**: A NetworkX graph object representing the network topology.
- **Metadata**: JSON file containing node count, average degree, rewiring probability $p$, and random seed.
- **Simulation Results**: CSV file containing topology ID, $p$, $K_c$, and stability metrics.
- **Analysis Results**: JSON file containing correlation coefficients, p-values, and sensitivity analysis data.

## 6. Deliverables

1. `data/processed/graph_p*.gpickle`: Generated network topologies.
2. `data/processed/simulation_results.csv`: Critical coupling strengths for all topologies.
3. `data/processed/correlation_results.json`: Statistical analysis results.
4. `data/processed/analysis_report.md`: Final report summarizing findings.
5. `docs/constitutional_amendment.md`: Documentation of the deviation from the original 'ca-AstroPh' requirement.