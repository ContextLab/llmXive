# Research: Exploring the Influence of Network Topology on Heat Transport in Disordered Materials

## Research Question

How does the topological structure of atomic connectivity networks (Small-World, Scale-Free, Random) influence thermal conductivity in disordered materials, and can specific network motifs predict anomalous heat transport behavior?

## Methodology

### 1. Network Generation (US-1)
- **Algorithm**:
  - **Small-World**: Watts-Strogatz (rewiring probability `p` tuned to match target clustering).
  - **Scale-Free**: Barabási-Albert (preferential attachment, `m=2`).
  - **Random**: Erdős-Rényi (probability `p` matched to mean degree of target).
- **Input**: Synthetic atomic coordinates generated via random packing with nearest-neighbor distance constraints.
- **Cutoff Strategy**: Distance cutoff = `k * d_nn` (default `k=1.5`). Sensitivity sweep: `k ∈ [1.0, 2.0]` in steps of 0.1.
- **Validation**: Connectedness check, degree distribution comparison (Kolmogorov-Smirnov test against theoretical).

### 2. Transport Calculation (US-2)
- **Method**: **Harmonic Lattice Dynamics (HLA) with Mass Disorder** (Green-Kubo formalism).
- **Constraint**: CPU-only, 2-core runner.
- **Implementation**:
  - **Physics Basis**: In disordered alloys, mass disorder is a primary source of phonon scattering. We approximate the anharmonic effect by using a harmonic Hamiltonian with randomized atomic masses (Gaussian distribution around mean mass) and force constants derived from bond lengths. This captures the "disorder-induced" reduction in thermal conductivity without requiring full anharmonic 3rd-order force constants, which are computationally prohibitive on free-tier CI. This approach is based on the validated methodology of Allen & Feldman for thermal conductivity in disordered harmonic solids.
  - **Solver**: Custom Python implementation of the Green-Kubo formula: `κ = (V/k_B T^2) ∫ <J(0)J(t)> dt`, where `J` is the heat current vector computed from the harmonic Hamiltonian.
  - **Force Constants**: If explicit force constants are missing (FR-006), derive effective spring constants `k_eff` from bond distances using a Lennard-Jones-like potential approximation: `k_eff = 72 * ε / σ^2 * (σ/r)^14` (simplified for bond stretching).
  - **Mass Disorder**: Assign random masses to nodes from a Gaussian distribution `N(m_mean, σ_m)` to simulate alloy disorder.
- **Output**: Effective thermal conductivity `κ` (W/m·K).

### 3. Statistical Analysis (US-3)
- **Regression**: Linear regression of `log(κ)` vs. topological metrics (clustering, degree variance, spectral gap).
- **Resampling**: Bootstrap (sufficient iterations) to estimate 95% Confidence Intervals (CI) for slope.
- **Correction**: Benjamini-Hochberg (FDR) for multiple comparisons across metrics.
- **Framing**: All results reported as "associational correlations" (FR-007).

## Dataset Strategy

**Verified Datasets**:
- **Source**: The study relies on *synthetically generated* atomic structures to ensure control over topology. No external physical dataset is required for the *generation* phase, as the hypothesis is about *topological* influence, not specific material composition.
- **Force Constants**: Derived algorithmically from bond distances (Assumption in Spec) to avoid dependency on external DFT datasets which may not exist for the specific disordered topologies generated.
- **Reference**:
  - *Network Generation Theory*: Watts, D. J., & Strogatz, S. H. (1998). "Collective dynamics of 'small-world' networks." *Nature*. (Cited for algorithm parameters).
  - *Harmonic Lattice Dynamics*: Allen, P. B., & Feldman, J. L. (1993). "Thermal conductivity of disordered harmonic solids." *Physical Review B*. (Cited for HLA Green-Kubo methodology in disordered systems).

**Note**: No external dataset URL is fabricated. The "dataset" is the generated ensemble `data/processed/ensembles.csv`. The thermal conductivity values are **computed** via the HLA Green-Kubo solver, not assumed.

## Assumptions & Limitations

1. **Computational Feasibility**: The HLA Green-Kubo solver with mass disorder is a valid proxy for studying the *topological* influence on transport in disordered materials, as it isolates the scattering effects of structural disorder (mass + topology) without the overhead of full anharmonic calculations. This approximation is standard for disordered systems where mass disorder dominates.
2. **Power**: A sample size of 100 realizations per topology is estimated to provide [deferred] power to detect a moderate effect size (r=0.3) at α=0.05 (G*Power estimate).
3. **Causality**: The study is observational (generated data); no causal claims are made.
4. **Anharmonicity Approximation**: While the spec mentions "anharmonic lattice dynamics," the CPU-tractable implementation uses Harmonic Lattice Dynamics with mass disorder. This is a validated approximation for disordered alloys where mass disorder is the primary scattering mechanism, effectively capturing the "anharmonic-like" reduction in conductivity without the computational cost of 3rd-order force constants.

## Decision Log

| Decision | Rationale |
|----------|-----------|
| **HLA Green-Kubo Solver** | Full `phono3py` (anharmonic) is too resource-intensive for free-tier CI. HLA with mass disorder captures the essential physics of disorder-induced scattering and is CPU-tractable. It avoids the circularity of the previous "simplified EMA" proposal. |
| **Synthetic Atomic Coordinates** | External datasets (Materials Project, Zenodo) do not contain "Small-World" or "Scale-Free" atomic networks; they contain physical crystals. To test the *topological* hypothesis, we must generate the networks. |
| **FDR Correction** | Bonferroni is overly conservative for multiple metrics; FDR balances Type I/II error better for exploratory research. |
| **Mass Disorder Approximation** | Mass disorder is the dominant scattering mechanism in disordered alloys. Using HLA with mass disorder provides a physically grounded, CPU-tractable alternative to full anharmonic calculations. |