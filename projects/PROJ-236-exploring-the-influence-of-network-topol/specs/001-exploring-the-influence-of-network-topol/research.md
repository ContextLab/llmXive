# Research: Exploring the Influence of Network Topology on Heat Transport in Disordered Materials

## 1. Scientific Background & Hypothesis

### 1.1 Background
Thermal transport in disordered materials is governed by phonon scattering. While traditional models focus on mass disorder or point defects, the topological arrangement of atomic bonds (the connectivity network) may significantly influence phonon mean free paths. This study investigates whether specific network motifs (e.g., small-world clustering, scale-free hubs) correlate with anomalous heat transport behavior.

### 1.2 Hypothesis
*H0*: Network topology metrics (clustering coefficient, degree variance, spectral gap) are not associated with effective thermal conductivity in disordered materials, after controlling for mass disorder.
*H1*: Specific topological features (e.g., high clustering in small-world networks) are negatively associated with thermal conductivity due to enhanced phonon scattering, while scale-free hubs may facilitate ballistic transport channels.

## 2. Dataset Strategy

### 2.1 Data Generation Pipeline
The study generates synthetic disordered atomic structures that are physically realizable for the target topologies.
*   **Source**: `pymatgen` for base lattice generation.
*   **Method**: **Physics-First Generation with EAM Relaxation**.
    1.  Generate a random disordered atomic configuration (e.g., random alloy).
    2.  Relax the structure using EAM potentials (via `lammps` CPU mode) to ensure physical validity (no overlaps, valid bond lengths).
    3.  Derive the connectivity graph from the relaxed coordinates using a distance cutoff.
    4.  Classify the resulting graph into topological bins (Small-World, Scale-Free, Random) based on its metrics.
*   **Force Constants**: Derived via **Embedded Atom Method (EAM)** potentials based on atomic species and relaxed positions. This ensures force constants depend on local geometry and species, satisfying FR-009 and avoiding circular validation with the abstract graph topology.
*   **Regime Validation**: Before transport calculation, the system checks for high-degree hubs or low clustering indicative of ballistic transport. If detected, the realization is **flagged** (not excluded) and the regime is recorded for stratified analysis (FR-011).

### 2.2 Force Constant Derivation
*   **Method**: EAM potentials (CPU-only) via `lammps`.
*   **Justification**: EAM captures many-body interactions and anharmonicity essential for disordered materials, unlike simple harmonic or bond-stiffness models. It depends on atomic positions, not the abstract graph, ensuring independence from the topology metric being tested.

### 2.3 Data Availability Note
The plan explicitly rejects using the 'Materials Project (Disordered Alloys)' dataset in favor of synthetic generation because the input block provided **NO verified Zenodo URL** for a specific disordered alloy dataset with force constants. The synthetic generation approach (Physics-First with EAM) is scientifically valid and avoids the risk of fabricating a dataset URL.

## 3. Methodology

### 3.1 Phase 0: Power Analysis (FR-010)
*   **Action**: Calculate required sample size N for r≥0.3, power≥0.80.
*   **Critical Nuance**: The power analysis will not use total variance. Instead, it will use a **pilot run** to estimate the **residual variance** of thermal conductivity after regressing out mass disorder effects (e.g., atomic mass variance, composition). The sample size N is calculated to detect the *topological signal* (r ≥ 0.3) against this residual noise, ensuring the study is not underpowered to distinguish topological effects from trivial mass-disorder correlations.
*   **Output**: Set N in `simulation_config.yaml` before generation.

### 3.2 Phase 1: Network Generation & Sensitivity (FR-001, FR-008)
*   **Algorithms**: Watts-Strogatz (Small-World), Barabási-Albert (Scale-Free), Erdős-Rényi (Random) are used for **classification** or **targeting** via iterative relaxation, not for direct coordinate constraint.
*   **Validation**: Ensure connectedness (>95% realizations) and degree distribution match theoretical expectations.
*   **Sensitivity Sweep**: Iterate distance cutoff factors from x to 2.0x to verify robustness of correlations.
*   **Edge Cases**: If disconnected, retry with larger cutoff. Flag failures.

### 3.3 Phase 2: Transport Calculation (FR-002, FR-009, FR-011)
*   **Method**: Anharmonic Lattice Dynamics (ALD) via Green-Kubo formalism.
*   **Constraint**: CPU-only.
*   **Solver**: `phono3py` (CPU mode) with EAM force constants.
*   **Fallback**: If `phono3py` fails or exceeds time limits, switch to a simplified `scipy`-based harmonic/anharmonic solver.
*   **Regime Check**: If ballistic transport is detected, **flag** the realization with `regime_flag: Ballistic` but **do not exclude**. The analysis will stratify by regime.

### 3.4 Phase 3: Statistical Analysis (FR-004, FR-005, SC-004, SC-005)
*   **Metrics**: Clustering, Degree Variance, Spectral Gap, Betweenness.
*   **Regression**: Linear regression of Metric vs. Conductivity.
*   **Power-Law Fit**: Calculate R² for power-law fit between disorder parameters and conductivity reduction (SC-005).
*   **Resampling**: Bootstrap (sufficient iterations) for confidence intervals

The research question and method remain as specified in the planning document, with references preserved verbatim..
*   **CI Validation**: Calculate CI width. If width > 0.2, flag result or retry with increased iterations/N (SC-004).
*   **Correction**: Bonferroni or FDR for multiple metrics (FR-005).
*   **Stratification**: Perform analysis stratified by `regime_flag` to test topology-transport relationships across diffusive and ballistic regimes.
*   **Framing**: All results reported as **associational** (FR-007).

## 4. Computational Feasibility

*   **Hardware**: GitHub Actions Free Tier (limited vCPU, constrained RAM).
*   **Memory**: Data subsets to < 6 GB.
*   **Runtime**: Total ensemble < 6 hours.
*   **Mitigation**:
    *   Use small system sizes (N_atoms ~) to ensure feasibility.
    *   EAM relaxation and transport calculations are CPU-tractable for these sizes.
    *   No CUDA/8-bit quantization.

## 5. Risks & Mitigations

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| **Dataset Unreachability** | High | Use synthetic generation with `pymatgen` + EAM relaxation (verified approach) instead of external Zenodo links. |
| **Solver Convergence Failure** | Medium | Implement retry logic and fallback to simplified scipy solver. Exclude outliers with logging only if convergence fails completely. |
| **Runtime Exceeds 6h** | High | Limit ensemble size based on power analysis (FR-010) to minimum required N. |
| **Circular Validation** | High | Force constants derived from EAM (species/position), not topology (FR-009). |
| **Ballistic Transport Bias** | Medium | Stratify analysis by regime rather than excluding ballistic cases. |
| **Underpowered Topological Signal** | High | Phase 0 explicitly targets residual variance after controlling for mass disorder to ensure N is sufficient for the specific topological effect. |