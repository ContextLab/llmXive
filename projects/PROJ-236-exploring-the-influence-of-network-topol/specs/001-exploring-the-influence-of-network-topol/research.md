# Research: Exploring the Influence of Network Topology on Heat Transport in Disordered Materials

## Research Questions

1. How do Small-World, Scale-Free, and Random network topologies correlate with effective thermal conductivity in disordered atomic ensembles?
2. Which specific topological metrics (clustering coefficient, spectral gap, degree variance) are most predictive of anomalous heat transport?
3. Are observed correlations robust to variations in the distance-based cutoff used to define atomic connectivity?

## Methodology Sketch

### Phase 0: Power Analysis
- **Goal**: Determine sample size (N) to detect a moderate effect size (r=0.3) with [deferred] power.
- **Method**: G*Power or analytical calculation for Pearson correlation.
- **Output**: Target N per ensemble type.

### Phase 1: Network Generation (US-1)
- **Algorithm**: 
  - *Small-World*: Watts-Strogatz (rewiring probability $p$, nearest-neighbor $k$).
  - *Scale-Free*: Barabási-Albert (preferential attachment $m=2$).
  - *Random*: Erdős-Rényi (probability $p$ matched to mean degree).
- **Input**: **Synthetic atomic coordinates (randomly perturbed lattice) with N ≤ 100 atoms** and random chemical composition (e.g., equimolar Si and Ge).
- **Constraint**: Distance cutoff $d_c = \alpha \times d_{nn}$ (default $\alpha=1.5$). Retry up to $2.0\times$ if disconnected.
- **Validation**: Check connectedness (>95%), degree distribution fit.
- **Note**: Topology is an **abstract overlay** on the physical structure, generated algorithmically to isolate topological effects. It does not naturally emerge from the distance cutoff. The physical atomic structure is constrained to produce the desired topological metrics by assigning atomic properties to nodes in the generated graph.

### Phase 1.5: Cutoff Sensitivity (FR-008)
- **Task**: Sweep cutoff factors across a range from a baseline multiplier to an elevated multiplier in uniform increments.
- **Goal**: Verify that the topology-transport correlation is robust to cutoff variations.

### Phase 2: Transport Simulation (US-2)
- **Method**: **Debye-Grüneisen Approximation** (CPU-tractable).
- **Rationale**: Anharmonic Lattice Dynamics (ALD) via `phonopy` is computationally infeasible on 2-core/7GB RAM for N > 100. The Debye-Grüneisen model captures essential scattering effects via a Grüneisen parameter approximation, which models anharmonic phonon-phonon scattering without requiring full higher-order force constants.
- **Force Constants**: Derived via a bond-stiffness model where $k_{ij} \propto \frac{1}{r_{ij}^n} \times \gamma$, scaled by atomic properties (mass, bond length). **Crucially, mass is assigned based on chemical composition (Si/Ge), not node degree.**
- **Mass Assignment**: Atomic masses are assigned based on random chemical composition (Si/Ge), **independent** of node degree. This avoids the tautological loop where topology dictates mass.
- **Solver**: Custom CPU-only implementation (no `phono3py`).
- **Output**: Thermal conductivity $\kappa$ (W/mK).

### Phase 3: Statistical Analysis (US-3)
- **Regression**: Linear/Power-law fit between metrics (independent) and $\kappa$ (dependent).
- **Control**: **Include geometric descriptors (mean coordination number) as covariates** to ensure correlations are not trivial geometric artifacts.
- **Resampling**: Bootstrap for 95% CI.
- **Correction**: Bonferroni or FDR for multiple metrics.
- **Disorder Parameter**: Compute 'NetworkDisorderParameter' as a composite of degree variance and mass variance. Fit power-law between this parameter and $\kappa$ to calculate R² (SC-005). **Also fit individual components.**
- **Framing**: Strictly associational (FR-007).

## Dataset Strategy

**Verified datasets**: 
*Note: No specific verified dataset URL was provided in the prompt's "# Verified datasets" block for "disordered alloy atomic connectivity".*

- **Strategy**: 
  1. **Synthetic Generation**: Primary data will be generated synthetically using `pymatgen` to create disordered alloy structures (random substitution of Si/Ge in a lattice) to ensure full control over topology and properties.
  2. **Methodology Citations**: All methodology references (e.g., Watts-Strogatz, Debye-Grüneisen) will be verified against primary literature sources.
  3. **No Fabrication**: No raw URLs will be invented. If a dataset is needed but not verified, the plan will explicitly state "Data to be generated synthetically" rather than guessing a source.

## Decision Rationale

- **CPU-Only Constraint**: The plan uses a Debye-Grüneisen approximation and simplified bond-stiffness model to ensure runtime on a 2-core CPU runner (≤6h total). Full DFT-based FC calculation or `phono3py` is excluded as it violates the compute constraint.
- **Synthetic Data**: Given the lack of a verified public dataset containing *both* explicit atomic coordinates and *pre-computed* topological metrics for disordered materials, synthetic generation is the only reproducible path that satisfies FR-001 and FR-002.
- **Statistical Rigor**: Bootstrap resampling and multiple-comparison corrections are mandatory to address FR-004 and FR-005, ensuring the results are not artifacts of random noise.
- **Scientific Validity**: Mass assignment is decoupled from node degree to avoid circular validation. Topology influences transport via connectivity, not by dictating atomic mass. The study design treats topology as an independent variable imposed on the system.
- **Feasibility**: Reducing system size to N ≤ 100 atoms ensures the O(N^2) complexity of the Debye-Grüneisen model fits within the 7GB RAM and 45-minute per-realization constraints.

## Risk Assessment

- **Risk**: Convergence failure in solver.
  - *Mitigation*: Retry logic (multiple attempts) with adjusted solver parameters; exclude failed runs and log rate (target <5%).
- **Risk**: Disconnected graphs at low cutoffs.
  - *Mitigation*: Automatic cutoff sweep (from a baseline to an elevated multiplier) and exclusion of invalid realizations.
- **Risk**: Collinearity in metrics (e.g., degree variance vs. spectral gap).
  - *Mitigation*: Report descriptive statistics and acknowledge collinearity; do not claim independent causal effects.
- **Risk**: Spec Contradictions.
  - *Mitigation*: The plan explicitly flags contradictions with FR-006, FR-009, and Assumptions in the spec.md. The implemented methodology (Debye-Grüneisen, composition-based mass) is scientifically valid and feasible, while the spec requirements are not. The spec requires amendment.