# Research: Investigating Statistical Properties of Simulated Dark Matter Halos

## Dataset Strategy

The project relies on two major cosmological simulations. However, a critical data availability constraint exists for the primary dataset.

| Dataset | Source / URL | Availability Status | Notes |
| :--- | :--- | :--- | :--- |
| **IllustrisTNG (TNG100-1)** | **NO verified source found** | **Unavailable for direct download** | The spec assumes API access, but the "Verified datasets" block explicitly states no verified source exists. The plan implements a **Data Gap Mitigation** workflow: attempt real download, then fallback to **Synthetic Generator** with **Controlled Deviations**. |
| **Millennium Simulation** | **NO verified source found** | **Unavailable for direct download** | Similar to TNG100-1, no verified URL is provided. The pipeline will use a synthetic generator mimicking Millennium properties for code validation. |

> **Critical Decision**: Since no verified URLs exist for the required full catalogs, the implementation will **simulate** the data generation step using `numpy` to create synthetic halo catalogs with the statistical properties described in the spec (NFW profiles, mass ranges, particle counts), **but with injected deviations** to test the pipeline's sensitivity. This allows the *statistical pipeline* (FR-003 to FR-012) to be fully tested and validated. The `research.md` explicitly states that the *real data acquisition* is blocked until a verified source is found, but the *analysis methodology* is validated on synthetic data with known ground-truth deviations.

### Synthetic Data Generation Strategy (for Pipeline Validation)
To satisfy FR-001 and FR-002 (Download/Filter) in the absence of real data, the `code/data/download.py` will be implemented to:
1. **Generate Sparse Particle Stream**: Create a `particle_table` that is written to disk in chunks and accessed via memory-mapped arrays (mmap). This provides the necessary particle positions for FR-003 (overdensity calculation) without exceeding 7 GB RAM.
2. **Mass-Stratified Sampling**: Generate halos across the mass range (^ to 10^14 M⊙ h⁻¹) with a distribution matching the expected mass function, ensuring rare high-mass halos are included.
3. **Controlled Deviations**:
   - **Concentration**: Sample `c` from a distribution with a tunable offset from the Bullock et al. (2001) relation (e.g., `c = c_Bullock * (1 + noise + offset)`). This allows the pipeline to be tested for its ability to detect deviations.
   - **Environment**: Embed halos in a **synthetic large-scale structure field** (e.g., a Gaussian random field) to ensure local overdensity (Δ) varies naturally and is *independent* of the halo's internal virial radius (R_200). This prevents the tautology where Δ is definitionally 200.
4. **Spin Generation**: Generate particle positions/velocities such that the **Subsampled Plummer-Softened Potential** yields a physically plausible spin distribution, rather than a deterministic function of mass.

## Methodology & Statistical Rigor

### 1. Structural Metric Computation (FR-003 to FR-006)
- **Shape (s=c/a)**: Computed from the inertia tensor of particle positions. Eigenvalues $\lambda_1 \ge \lambda_2 \ge \lambda_3$ yield axes $a, b, c$. $s = c/a$.
- **Spin ($\lambda$)**: $\lambda = J|E|^{1/2} / (GM^{5/2})$.
  - **J**: Total angular momentum (sum of $r \times v$).
  - **E**: Total energy (Kinetic + Potential).
 - **Potential Energy (U)**: Computed via **Subsampled Plummer-Softened Potential** over a random subsample of **N=500 particles** per halo. This is O(N) and CPU-tractable, while preserving the physical definition of spin (unlike the flawed uniform sphere approximation). The Plummer softening length is set to [deferred] of the halo's virial radius.
  - *Note*: This method avoids the circular dependency where spin becomes a deterministic function of mass/radius.
- **Concentration (c)**: Fit radial density profile to NFW $\rho(r) = \rho_s / [(r/r_s)(1+r/r_s)^2]$ using `scipy.optimize.curve_fit`. $c = R_{200}/r_s$.
  - *Failure Handling*: If `curve_fit` does not converge (`success=False`), the halo is excluded from concentration analysis (FR-006). The **Convergence Rate** is tracked as a key metric (SC-004).

### 2. Environment Calculation (FR-003)
- **Local Overdensity ($\Delta$)**: Spherical top-hat of 5 Mpc $h^{-1}$.
- **Periodic Boundaries**: Coordinates wrapped using simulation box size $L_{box}$.
- **Neighbor Counting**: `scipy.spatial.cKDTree` for efficient neighbor search on the **memory-mapped particle stream**. The tree is built on a subsample of particles or incrementally to fit memory constraints.
- **Definition**: $\Delta = \rho_{local} / \rho_{critical}$.
- **Binning**: Low ($\Delta < 200$) vs. High ($\Delta \ge 200$).
- **Non-Triviality**: The synthetic generator creates a **background density field** (e.g., a Gaussian random field) where the local overdensity (calculated over 5 Mpc) is independent of the halo's internal virial radius. This ensures the environment classification is not a tautology of the halo's definition.

### 3. Hypothesis Testing (FR-008 to FR-011)
- **KS Tests**: Two-sample KS test between Low/High environment bins for Shape, Spin, Concentration.
  - *Multiple Testing*: 3 metrics × 3 mass bins = 9 tests.
  - *Correction*: Benjamini-Hochberg (FDR) or Bonferroni. *Decision*: Benjamini-Hochberg (less conservative, suitable for exploratory).
- **Spearman Correlation**: Mass vs. each metric. Null hypothesis: $\rho = 0$.
- **Bullock et al. (2001) Comparison**: Fit measured mass-concentration to analytic form $c(M) \propto M^{-0.1}$. Compute RMSE and mean difference. The synthetic data will have known deviations to verify the pipeline's ability to detect them.

## Statistical Rigor Checklist
- **Multiple Comparisons**: Benjamini-Hochberg applied to multiple KS tests.
- **Power**: Acknowledged limitation: Synthetic data allows code validation, but statistical power depends on real sample size (deferred).
- **Causal Claims**: None. All claims are associational (observational simulation data).
- **Measurement Validity**: NFW fit validity checked via reduced $\chi^2$ and p-value > 0.05. Spin validity ensured via Plummer-softened summation.
- **Collinearity**: Mass and Concentration are inversely related by definition; Spearman test used to quantify, not claim independence.

## Assumptions & Risks
- **Assumption**: Synthetic data with controlled deviations can mimic the statistical properties of real simulations sufficiently for pipeline stress-testing.
- **Risk**: Real data is unavailable (no verified URL). The project will be marked as "Pipeline Validated" but "Data Acquisition Pending" until a verified source is found.
- **Risk**: $O(N^2)$ potential calculation for spin is too slow. Mitigation: Use **Subsampled Plummer-Softened Summation over N=500 particles** (CPU-tractable, physically sound).
- **Risk**: Memory overflow. Mitigation: **Chunked Streaming** (10k halos/chunk) and **Memory-Mapped Particle Streams** for FR-003.