# Research: Exploring the Influence of Network Topology on Heat Transport in Disordered Materials

## Background & Motivation

Thermal transport in disordered materials is governed by phonon scattering, which is heavily influenced by the underlying atomic connectivity. While traditional models often assume random or periodic lattices, real disordered systems (e.g., amorphous solids, alloys) may exhibit specific topological features like small-world clustering or scale-free degree distributions. Understanding how these topological motifs correlate with thermal conductivity ($\kappa$) is crucial for designing materials with tailored thermal properties.

## Dataset Strategy

This study **generates its own data** to ensure full control over topological parameters and to avoid the "garbage-in, garbage-out" risk of finding external datasets that lack the specific topological annotations required.

| Data Source | Description | Access Method | Verification |
| :--- | :--- | :--- | :--- |
| **Synthetic Atomic Coordinates** | Disordered point clouds generated via Poisson Disk Sampling or Gaussian perturbation of a lattice. | `numpy` / `scipy` (Local generation) | N/A (Self-generated) |
| **Network Generators** | Watts-Strogatz (Small-World), Barabási-Albert (Scale-Free), Erdős-Rényi (Random). | `networkx` (Local library) | Unit-tested against theoretical distributions |
| **Force Constants** | Effective force constants derived from an **EAM-like empirical potential** based on atomic species and equilibrium bond lengths. **Crucially, these are calculated BEFORE graph topology is defined, ensuring independence.** | `code/02_compute_transport.py` (Local calculation) | Validated against analytical 1D chain |
| **Physics Model** | **Allen-Feldman Theory** (Allen & Feldman, Phys. Rev. Lett. 1989) for heat transport in disordered systems. | `code/02_compute_transport.py` (Local implementation) | Cited primary source |

**Note**: No external pre-computed thermal conductivity values are used. All $\kappa$ values are computed by the `02_compute_transport.py` script on the CI runner.

## Methodology

### Phase 1: Network Generation (FR-001, FR-008)
1.  **Input**: Number of nodes $N$ (e.g., 200), target topology type.
2.  **Procedure**:
    *   Generate random atomic coordinates in a box.
    *   **Step 1.1 (Force Constants)**: Derive effective force constants $K_{ij}$ from an EAM-like potential based on atomic species and equilibrium bond lengths. **This step is independent of the graph topology.**
    *   Apply distance-based cutoff ($1.5 \times$ nearest-neighbor distance) to define edges.
    *   For Small-World: Start with a ring lattice, rewire with probability $p$.
    *   For Scale-Free: Use Barabási-Albert growth with $m=2$.
    *   **Validation**: Check connectedness. If disconnected, retry with cutoff up to $2.0 \times$. Log exclusion reasons.
3.  **Output**: `data/processed/graphs/{type}_{id}.graphml`.

### Phase 1.5: Sensitivity Analysis (FR-008)
1. **Input**: A representative subset ([deferred]) of network realizations.
2.  **Procedure**: Systematically sweep distance cutoff values from $1.0\times$ to $2.0\times$ in $0.1\times$ increments.
3.  **Output**: `data/processed/sensitivity/cutoff_sweep_results.csv`.

### Phase 2: Transport Calculation (FR-002, FR-006, FR-009, FR-011)
1.  **Input**: Graph structure, atomic masses, pre-calculated force constants.
2.  **Procedure**:
    *   Construct dynamical matrix from $K_{ij}$.
    *   Compute thermal conductivity using **Allen-Feldman theory** (diffusivity of vibrational modes). This method is valid for disordered systems and does not require third-order force constants.
    *   **Regime Validation (FR-011)**: Calculate spectral gap and estimate mean free path. If ballistic regime is detected (high hubs, low clustering, mean free path > system size), switch to NEMD or flag as invalid.
    *   **Constraint**: Must run on CPU (2 cores, 7 GB RAM). System size limited to $N \le 500$.
3.  **Output**: `data/processed/transport/{type}_{id}.csv` (contains $\kappa$, convergence status, regime_detected).

### Phase 2.1: Finite-Size Scaling Pilot (FR-011)
1.  **Input**: Small ensembles at $N=100, 200, 300$.
2.  **Procedure**: Run transport calculations to verify that $\kappa$ converges (is size-independent) before proceeding to the main ensemble at $N=500$.
3.  **Output**: `data/processed/pilot/finite_size_results.csv`.

### Phase 3: Statistical Analysis (FR-003, FR-004, FR-005, FR-007, FR-010, SC-005)
1.  **Input**: Ensemble of graphs and $\kappa$ values.
2.  **Procedure**:
    *   Extract metrics: Clustering coeff, degree variance, spectral gap, betweenness.
    *   Perform Power Analysis (FR-010): Determine $N$ for power $\ge 0.80$ at $r \ge 0.3$.
    *   **Statistical Modeling**:
        *   **ANOVA/Mixed-Effects**: Treat 'Topology Type' as a categorical fixed effect and 'Metric Value' as a continuous covariate to separate discrete class effects from continuous variations.
        *   **Power-Law Fit**: Regress $\kappa$ against 'disorder parameter' (e.g., $1 - \text{clustering}$) to calculate $R^2$ and exponent (SC-005).
    *   Bootstrap: A sufficient number of iterations for confidence intervals.
    *   Correction: Bonferroni for multiple metrics.
3.  **Output**: `data/processed/analysis/correlation_results.json`.

## Statistical Rigor & Limitations

- **Multiple Comparisons**: Bonferroni correction applied for all metric tests (FR-005).
- **Power Analysis**: Formal calculation performed prior to full ensemble generation (FR-010).
- **Causal Framing**: All results framed as **associational** (FR-007). No claim of "causation" due to observational nature of generated ensembles.
- **Collinearity**: If degree variance and clustering are correlated, this is reported descriptively; independent effects are not claimed without orthogonalization.
- **Limitations**:
    - Allen-Feldman theory is an approximation for disordered systems; full anharmonicity may not be captured.
    - System size limited to $N \le 500$ due to CPU constraints; extrapolation to macroscopic scales is speculative.
    - Force constants are derived from an empirical potential, not DFT.

## Decision Log

- **Why Allen-Feldman?**: `phono3py` is infeasible on 2-core CPU for N=500. Allen-Feldman is the standard CPU-tractable method for disordered systems.
- **Why EAM Potential?**: Ensures force constants are independent of graph topology, preventing circular validation (FR-009).
- **Why ANOVA?**: Separates the effect of discrete topology types from continuous metric variations (Methodology concern).
- **Why Subset Sensitivity?**: Performing sensitivity analysis on [deferred] of realizations balances FR-008 requirements with the 6-hour runtime budget.