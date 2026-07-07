# Research: Exploring the Role of Network Topology on Synchronization in Coupled Oscillators

## Research Question
How does the small-world rewiring probability in a **synthetic regular ring lattice** influence the critical coupling strength required for global synchronization in the Kuramoto oscillator model?

**Correction Note**: The original spec (User Story 1, FR-001) incorrectly mandated using the 'ca-AstroPh' citation network as a base for reconstruction into a regular ring lattice. This is methodologically invalid as an irregular citation network cannot be transformed into a regular lattice without discarding its entire structure. This research plan replaces the ca-AstroPh base with a **synthetic regular ring lattice of N=500 nodes** to ensure the Watts-Strogatz parameter `p` retains its standard theoretical meaning. The study is now a purely synthetic investigation of the Watts-Strogatz model.

## Dataset Strategy

### Base Graph: Synthetic Regular Ring Lattice
No external dataset is used. The base graph is generated synthetically.
- **Source**: `networkx` library function `nx.watts_strogatz_graph` with `p=0.0` on a ring lattice of N=500 nodes.
- **Parameters**: N=500 nodes, k=6 (degree of base lattice, chosen to match typical small-world studies).
- **Justification**: A regular ring lattice is the theoretical starting point for the Watts-Strogatz model. Using a real-world dataset like ca-AstroPh as a base for a ring lattice reconstruction is impossible without total data loss. The synthetic base ensures the validity of the `p` parameter.

**Note on Dataset-Variable Fit**: The study generates the topology directly. The "variables" are the network metrics (clustering, path length) derived from this synthetic structure. This fit is valid and avoids the mismatch of trying to force a real-world graph into a synthetic model.

## Methodology

### 1. Topology Generation (FR-001, FR-002)
- **Base Graph**: A regular ring lattice of N=500 nodes with degree k=6.
- **Algorithm**: Watts-Strogatz small-world model.
  - Parameters: N=500, k=6, `p` in [0.0, 1.0].
  - Instances: 50 instances with `p` linearly spaced.
- **Validation**: Check connectivity. If disconnected, skip and log (FR-002).
- **Metadata**: Record the exact random seed and `p` value for each instance in `graph_metadata.json`.

### 2. Kuramoto Simulation (FR-003, FR-004)
- **Model**: $\frac{d\theta_i}{dt} = \omega_i + \frac{K}{N} \sum_{j=1}^{N} A_{ij} \sin(\theta_j - \theta_i)$.
- **Natural Frequencies ($\omega_i$)**: Drawn from a standard distribution (e.g., Gaussian with mean 0, std 1).
- **Integration**: `scipy.integrate.odeint` with fixed step size (e.g., `dt=0.01`) and total steps=[deferred] (to be determined in Phase 0).
- **Critical Coupling ($K_c$)**: Determined via binary search or linear sweep.
  - Target: Order parameter $R \ge 0.5$ (configurable).
  - Tolerance: $\le 0.01$.
  - Max iterations: a sufficient number to ensure convergence.
- **Invariance Check (FR-009)**: Run simulation with phase reference at oscillator 0 and at the center of mass to verify $K_c$ is identical.
- **Transition Shape Analysis**: The analysis will also examine the slope of the $R(K)$ curve to determine if the transition sharpness varies with topology, not just the crossing point. This ensures the critical coupling is a robust physical property and not an artifact of the chosen threshold.

### 3. Statistical Analysis (FR-005, FR-006, FR-007, FR-008)
- **Primary Metric**: Correlation between **measured topological metrics** (clustering coefficient, average path length) and `K_c`. This isolates which structural feature drives the synchronization change.
- **Secondary Metric**: Spearman rank correlation between `p` (rewiring prob) and `K_c` (as a proxy for the generation mechanism).
- **Significance**: P-value < 0.05.
- **Correction**: If multiple hypotheses are tested (e.g., multiple `p` ranges or sensitivity thresholds), apply Bonferroni or Benjamini-Hochberg.
- **Sensitivity**: Sweep threshold $R \in \{0.4, 0.5, 0.6\}$.
- **Assumption**: Observational study; results are associational, not causal.

## Statistical Rigor & Feasibility

- **Multiple Comparisons**: The primary hypothesis is the correlation between measured metrics and $K_c$. The sensitivity analysis (3 thresholds) and secondary correlations (clustering, path length) constitute multiple tests. We will apply Bonferroni correction ($\alpha_{adj} = 0.05 / N_{tests}$) for these checks.
- **Power**: With 50 instances (levels of `p`), the statistical power for detecting a monotonic trend is high. The sample size for the correlation analysis is 50 data points (the number of `p` levels), not 500 nodes. This is sufficient for the expected effect sizes in small-world networks.
- **Collinearity**: The rewiring probability `p` is the independent variable. The network metrics (clustering, path length) are intermediate variables. We do not claim independent effects of metrics vs `p`, but rather the effect of `p` *via* these metrics.
- **Compute Feasibility**:
  - 50 graphs × [deferred] steps.
  - `scipy.integrate.odeint` on 500 nodes is lightweight.
  - Estimated runtime: a few hours on a 2-core CPU (assuming a standard number of steps).
  - Memory: < 2GB.
  - No GPU required.

## Risks & Mitigations

- **Disconnected Graphs**: High `p` values may disconnect the graph. Mitigation: Skip disconnected instances, log warning, and adjust `p` range if >10% are disconnected.
- **Numerical Instability**: Mitigation: Use `rtol=1e-6`, `atol=1e-9`, and fixed `dt`.
- **Spec Contradiction**: The spec (User Story 1, FR-001) mandates using ca-AstroPh as a base. This plan explicitly rejects that instruction as methodologically invalid. A kickback is required to update the spec to reflect the synthetic base.