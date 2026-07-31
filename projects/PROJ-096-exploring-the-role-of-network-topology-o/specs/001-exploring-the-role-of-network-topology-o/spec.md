# Specification: Exploring the Role of Network Topology on Synchronization in Coupled Oscillators

**Project ID**: PROJ-096-exploring-the-role-of-network-topology-o
**Status**: Draft
**Version**: 1.0.0

## 1. Introduction

This project investigates the relationship between network topology and the synchronization threshold (critical coupling strength, $K_c$) in a system of coupled phase oscillators. Specifically, we analyze how the small-world rewiring probability ($p$) in a Watts-Strogatz network affects the onset of synchronization in the Kuramoto model.

## 2. Objectives

- To generate a series of network topologies starting from a regular ring lattice and applying Watts-Strogatz rewiring with varying probabilities.
- To simulate Kuramoto dynamics on these topologies to determine $K_c$.
- To quantify the correlation between rewiring probability and $K_c$.
- To verify the rotational invariance of $K_c$ across different reference frames.

## 3. Functional Requirements

### FR-001: Network Generation
The system MUST generate a set of network topologies based on a **synthetic regular ring lattice of N=500 nodes**.
- **Base Graph**: The base graph MUST be a synthetic regular ring lattice with $N=500$ nodes and nearest-neighbor connectivity $k=2$.
- **Rewiring**: The system MUST apply the Watts-Strogatz algorithm with rewiring probabilities $p$ ranging from 0.0 to 1.0.
- **Constraint**: The original requirement to use the 'ca-AstroPh' dataset has been formally amended. The 'ca-AstroPh' dataset is irregular and cannot be reconstructed into a regular ring lattice without destroying its inherent topological properties, making it methodologically invalid as a base for the Watts-Strogatz parameter $p$. The synthetic ring lattice is used to ensure the theoretical validity of the $p$ parameter.
- **Output**: Generated graphs MUST be saved as `.gpickle` files with metadata including $N$, $k$, $p$, and the random seed used.

### FR-002: Connectivity Validation
The system MUST validate that each generated graph is connected. Disconnected graphs MUST be logged and excluded from the simulation batch.

### FR-003: Kuramoto Simulation
The system MUST simulate Kuramoto dynamics on each valid topology.
- **ODE Solver**: Use `scipy.integrate.odeint` or `solve_ivp`.
- **Parameters**: Natural frequencies $\omega_i$ drawn from a Gaussian distribution with mean 0 and standard deviation 1.

### FR-004: Critical Coupling Detection
The system MUST determine the critical coupling strength $K_c$ for each topology using a binary search algorithm with a fallback linear sweep.
- **Threshold**: Synchronization is defined as the order parameter $R$ exceeding a threshold (configurable, default 0.5) for the final 10% of the simulation time.

### FR-005: Data Persistence
All simulation results MUST be saved to `data/processed/simulation_results.csv`.

### FR-006: Statistical Analysis
The system MUST calculate the Spearman correlation coefficient and p-value between rewiring probability and $K_c$.

### FR-007: Sensitivity Analysis
The system MUST perform a sensitivity analysis by sweeping the synchronization threshold over a representative set of values.

### FR-008: Statistical Model Definition
The statistical model (e.g., single regression, multiple comparison correction) MUST be defined in `data/processed/analysis_config.yaml` before analysis begins.

### FR-009: Rotational Invariance Verification
The system MUST verify that $K_c$ is invariant under a change of reference frame.
- **Method**: Re-calculate $K_c$ using two reference frames:
 1. Single oscillator frame (phase of oscillator 0).
 2. Center-of-mass frame (average phase of all oscillators).
- **Success Criterion**: The difference between $K_c$ values in both frames must be negligible (within numerical tolerance).

## 4. Non-Functional Requirements

### SC-001: Stability
The simulation results for $K_c$ must be stable across multiple runs with different random seeds for natural frequencies.

### SC-002: Reproducibility
All random number generation MUST use a documented seed. All artifacts MUST be checksummed.

### SC-003: Runtime
The full experiment (generation, simulation, analysis) MUST complete within 6 hours on a standard 2-core CPU runner. If this is not feasible, a contingency plan MUST be executed to reduce scope (time steps or number of topologies) while logging the reduction.

## 5. Data Models

### Graph Metadata
- `node_count`: int
- `avg_degree`: float
- `p`: float (rewiring probability)
- `seed`: int
- `checksum`: string

### Simulation Results
- `topology_id`: string
- `p`: float
- `kc_binary`: float
- `kc_linear`: float (if binary failed)
- `status`: string (success/failure)

## 6. References

- Watts, D. J., & Strogatz, S. H. (n.d.). Collective dynamics of 'small-world' networks. Nature.
- Kuramoto, Y. Chemical Oscillations, Waves, and Turbulence. Springer. 