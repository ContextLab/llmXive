# Methodology: Exploring the Role of Network Topology on Synchronization in Coupled Oscillators

This document outlines the theoretical basis, implementation details, and interpretation of results for the study of Kuramoto oscillator synchronization on Watts-Strogatz small-world networks.

## 1. Theoretical Background

### 1.1 The Kuramoto Model
The Kuramoto model describes the dynamics of a population of coupled phase oscillators. The phase $\theta_i$ of the $i$-th oscillator evolves according to:

$$ \frac{d\theta_i}{dt} = \omega_i + \frac{K}{N} \sum_{j=1}^{N} A_{ij} \sin(\theta_j - \theta_i) $$

where:
- $\omega_i$ is the natural frequency of oscillator $i$ (drawn from a distribution $g(\omega)$).
- $K$ is the global coupling strength.
- $A_{ij}$ is the adjacency matrix of the underlying network topology.
- $N$ is the total number of oscillators.

### 1.2 Order Parameter and Synchronization
Synchronization is quantified by the complex order parameter $re^{i\psi}$:
$$ re^{i\psi} = \frac{1}{N} \sum_{j=1}^{N} e^{i\theta_j} $$
The magnitude $r \in [0, 1]$ measures the phase coherence of the population. $r \approx 0$ indicates incoherence, while $r \approx 1$ indicates full synchronization. The critical coupling strength $K_c$ is the threshold above which a macroscopic fraction of oscillators synchronizes.

## 2. Network Topology: Watts-Strogatz Small-World Model

### 2.1 Construction
We generate network instances using the Watts-Strogatz (WS) model, starting from a regular ring lattice of $N=500$ nodes with degree $k=2$. Each edge is rewired with probability $p \in [0, 1]$.
- **$p=0$**: Regular ring lattice (high clustering, long path length).
- **$p=1$**: Random graph (low clustering, short path length).
- **$0 < p < 1$**: Small-world networks (high clustering, short path length).

### 2.2 Physical Interpretation of $p$ and $K_c$
A critical aspect of this study is the physical interpretation of the parameters involved, particularly in response to concerns regarding observer independence (EPR criterion).

**The Rewiring Probability ($p$):**
The parameter $p$ is a **topological invariant** of the graph structure. It defines the statistical ensemble from which a specific network instance is drawn. Once a graph is generated and fixed, its structural properties (degree distribution, clustering coefficient, path length) are intrinsic to the graph and do not depend on the state of the oscillators or the observer's coordinate system. $p$ represents the "disorder" in the connectivity pattern, which directly influences the ease with which information (phase synchronization) propagates through the network.

**The Critical Coupling Strength ($K_c$):**
The critical coupling $K_c$ is the **dynamical threshold** required to overcome the dispersion in natural frequencies ($\omega_i$) and establish global phase coherence. It is a property of the interaction between the network topology and the oscillator dynamics.
- **Dependence on Topology:** $K_c$ is determined by the spectral properties of the adjacency matrix $A$ (specifically, the eigenvalue gap or the algebraic connectivity). A more connected network (lower $p$, higher clustering) typically requires a different $K_c$ compared to a more random network (higher $p$).
- **Independence from Observer:** Crucially, $K_c$ must be an **observer-invariant** quantity. The physical phenomenon of synchronization—where a macroscopic fraction of oscillators locks to a common frequency—occurs regardless of the phase reference frame chosen by an observer. Whether one measures phases relative to a single oscillator, the center-of-mass of the population, or an arbitrary rotating frame, the *threshold* $K$ at which the transition from incoherence to synchronization occurs must remain the same. If $K_c$ varied with the reference frame, it would be a coordinate artifact rather than a physical element of reality.

This study explicitly verifies this invariance (see Section 3) to ensure that the observed relationship between $p$ and $K_c$ reflects a genuine physical law of the system, not a mathematical artifact of the coordinate system.

## 3. Rotational Invariance Verification (FR-009)

To address the requirement that physical quantities correspond to elements of reality independent of the observer, we perform a rigorous invariance check on the critical coupling strength $K_c$.

### 3.1 Reference Frames
We evaluate $K_c$ using three distinct phase reference frames:
1. **Single Oscillator Frame:** Phases are measured relative to a fixed oscillator $\theta_0(t)$. Relative phase: $\phi_i(t) = \theta_i(t) - \theta_0(t)$.
2. **Center-of-Mass (COM) Frame:** Phases are measured relative to the average phase of the population $\bar{\theta}(t)$. Relative phase: $\phi_i(t) = \theta_i(t) - \bar{\theta}(t)$.
3. **Perturbed Frames:** To ensure robustness against specific choices, we generate $N_{perturb}=5$ random reference frames constructed as weighted averages of the phases.

### 3.2 Methodology
For each valid topology generated in User Story 1:
1. Run the Kuramoto simulation with the binary search algorithm to determine $K_c$ in the Single Oscillator Frame.
2. Repeat the determination of $K_c$ in the COM Frame.
3. Repeat for the Perturbed Frames.
4. Repeat the entire process over multiple seeds (as defined in `config.json`) to account for stochasticity in natural frequencies.

### 3.3 Success Criteria
A topology is considered to exhibit **Physical Invariance** if:
- The variance of $K_c$ estimates across seeds within a specific frame is below a numerical threshold (indicating stability).
- The absolute difference between the mean $K_c$ of the Single Oscillator frame and the COM frame is negligible (within numerical tolerance).
- The maximum deviation of $K_c$ in any Perturbed frame from the mean is sufficiently small.

If these conditions are met, we conclude that $K_c$ is a robust, observer-independent property of the system, satisfying the EPR criterion.

## 4. Stability and Sensitivity Analysis

### 4.1 Stability (SC-001)
We verify that the simulation results are stable across multiple runs with different random seeds for natural frequencies. A high variance in the order parameter $R$ or the estimated $K_c$ would indicate numerical instability or insufficient averaging. The pipeline enforces a minimum `run_count` of 10 to ensure statistical validity.

### 4.2 Sensitivity Analysis (FR-007)
We perform a threshold sweep to ensure that the correlation between rewiring probability $p$ and critical coupling $K_c$ is robust to the specific definition of the synchronization threshold used in the binary search. The correlation coefficient (Spearman) and p-value are calculated for a range of thresholds, and the variation in these metrics is reported.

## 5. Statistical Model

The primary statistical analysis employs the **Spearman rank correlation** to assess the monotonic relationship between the topological parameter $p$ and the dynamical threshold $K_c$.
- **Model Type:** Single regression (non-parametric).
- **Correction:** Bonferroni correction is applied if multiple independent tests are performed (e.g., across different threshold definitions), as defined in `analysis_config.yaml`.
- **Justification:** The relationship between network structure and synchronization threshold is expected to be monotonic but not necessarily linear, making Spearman correlation appropriate.

## 6. Computational Constraints and Scope

The experiment is constrained by the available compute budget (6 hours on a 2-core CPU). A feasibility study (T009) determines the maximum number of time steps and topologies. If the feasible scope is below the target, a contingency plan is enacted, and the resulting sparsity in $p$-space is documented. The final report explicitly states the scope reduction factor and its potential impact on statistical power.

## 7. Conclusion

This methodology ensures that the observed dependence of synchronization on network topology is not only statistically significant but also physically robust. By explicitly verifying the rotational invariance of $K_c$, we establish that the critical coupling is a genuine element of physical reality, independent of the observer's coordinate choice, and intrinsically linked to the topological invariant $p$.