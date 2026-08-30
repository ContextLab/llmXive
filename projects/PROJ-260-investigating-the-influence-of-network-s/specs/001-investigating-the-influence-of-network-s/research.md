# Research: Investigating the Influence of Network Structure on Heat Conduction in Amorphous Solids

## Objective

To determine the statistical correlation between network topological features (coordination number, bond angle variance, bottleneck density) and thermal conductivity in amorphous silicon, using molecular dynamics (MD) trajectory data and vibrational density of states (VDOS) analysis. The study design ensures statistical validity by analyzing **multiple independent disorder realizations** (N≥30) per system size, rather than relying on a small N=3 sample of system sizes.

## Methodology

### 1. Data Ingestion and Network Topology Extraction (FR-001, FR-002)

**Input**: MD trajectory files (LAMMPS dump or XYZ format) containing atomic positions and velocities.
**Process**:
1. **Parsing**: Use `ase` (Atomic Simulation Environment) to parse atomic coordinates (FR-001).
2. **RDF Calculation**: Compute the Radial Distribution Function $g(r)$ for each dataset.
3. **Cutoff Determination**: Identify the first local minimum of $g(r)$ to define the bond cutoff distance $r_c$. This ensures dataset-specific consistency (Constitution Principle VII).
4. **Network Construction**: Construct a graph where nodes are atoms and edges exist if $r_{ij} < r_c$.
5. **Metric Calculation**:
 * **Coordination Number ($CN_i$)**: Degree of node $i$.
 * **Bond Angle Variance**: Variance of angles formed by triplets of bonded atoms.
 * **Bottleneck Identification**: Flag atoms with $CN_i < 3$ as "under-coordinated". Calculate bottleneck density as the ratio of under-coordinated atoms to total atoms.
 * **Sensitivity Analysis (US-2)**: Perform a threshold sweep of the under-coordination definition (±0.5) to report the stability of the bottleneck density metric (coefficient of variation < 0.1).

**Output**: A CSV file per system containing atomic IDs, $CN$, bond angle variance, and a global bottleneck density metric.

### 2. Vibrational Mode Analysis and Scattering Mechanisms (FR-003, FR-004)

**Input**: Velocity trajectory data and the constructed bond network.
**Process**:
1. **Velocity Autocorrelation Function (VACF)**: Compute the VACF from velocity time series.
2. **VDOS Calculation**: Perform Fourier Transform of the VACF to obtain the Vibrational Density of States (VDOS).
3. **Participation Ratio (PR)**: Calculate the PR to quantify the localization of vibrational modes.
 * $PR = \frac{(\sum_i |e_i|^2)^2}{N \sum_i |e_i|^4}$, where $e_i$ is the eigenvector component.
4. **Phonon Scattering Analysis**: Calculate the spectral thermal conductivity or mean free path estimates to explicitly link topology to scattering mechanisms (addressing scientific soundness concern).
5. **Localized Mode Density**: Integrate the VDOS weighted by low PR values in the high-frequency range to estimate the density of localized modes.

**Output**: VDOS spectrum (frequency vs. density), participation ratio, mean free path estimates, and a scalar "density of localized modes" per simulation box.

### 3. Reference Generation & Independence Verification (FR-008)

**Input**: The same topological structures used for predictor metrics.
**Process**:
1. **Independence Check**: Verify that the thermal conductivity source is independent. The system will **programmatically generate** reference $\kappa$ values using a distinct physical model (Cahill-Pohl limit) or a separate Green-Kubo calculation on a *disjoint* subset of the trajectory (different time window or different realization).
2. **Verification**: The `reference_generator.py` service will log the source of the $\kappa$ value, compare trajectory IDs, and confirm it is not derived from the *exact same* atomic configuration used for the topological metrics.
3. **Error Handling**: If the independence check fails (e.g., user attempts to supply $\kappa$ derived from the same trajectory), the system halts with a specific error code (FR-008).

**Output**: A `data/derived/reference/thermal_conductivity.csv` file with programmatic $\kappa$ values and source metadata.

### 4. Statistical Correlation and Robustness (FR-005, FR-006, FR-007)

**Input**: Topological metrics, localized mode densities, and programmatic thermal conductivity values ($\kappa$).
**Process**:
1. **Data Aggregation**: Combine metrics across **multiple independent snapshots** (N≥30) for each system size (N=1000, 2000, 4000). This provides sufficient degrees of freedom for valid correlation analysis.
2. **Decoupling Finite-Size Effects**: Perform correlation analysis *within* each system size group to isolate topological effects from size effects. If necessary, perform a partial correlation controlling for system size.
3. **Correlation Analysis**:
 * Compute **Spearman** and **Pearson** correlation coefficients between topological metrics and $\kappa$ across the N≥30 snapshots.
 * **Bootstrap Resampling**: Perform a sufficient number of bootstrap iterations to estimate the confidence interval for correlation coefficients.
4. **Multiple Comparison Correction**: Apply Bonferroni or False Discovery Rate (FDR) correction if multiple hypotheses are tested (e.g., testing both CN and Bond Angle Variance).
5. **Power Analysis**: Calculate statistical power for the observed effect size. If Power < 0.8, flag as "Low Power" (SC-002).
6. **Runtime Validation**: Measure the total pipeline runtime for a 4000-atom system and assert it is ≤ 30 minutes (SC-005).

**Output**: Summary table with correlation coefficients, p-values (corrected), 95% CIs, power estimates, and runtime metrics.

## Dataset Strategy

The study requires MD trajectories of amorphous silicon with velocity data. Thermal conductivity values will be generated programmatically to ensure independence and reproducibility.

| Dataset Name | Description | Source / URL | Status |
|:--- |:--- |:--- |:--- |
| **THZ-Alencar** | Amorphous silicon trajectories (velocity dump) for VDOS calculation. | ` | **Verified** (Available) |
| **THZ-Alencar021** | Additional amorphous silicon trajectories for system size variation. | ` | **Verified** (Available) |
| **Reference Generator** | Programmatic generation of $\kappa$ values using Cahill-Pohl model or separate MD subset. | *Internal Service* | **Verified** (Reproducible) |

**Gap Analysis & Mitigation**:
* **Thermal Conductivity Source**: The spec assumes "pre-recorded thermal conductivity values from an independent source." No verified external source exists for the specific trajectories.
 * *Mitigation*: The `reference_generator.py` service will compute $\kappa$ estimates using a validated physical model (Cahill-Pohl limit) or a separate Green-Kubo run on a disjoint trajectory subset. This ensures independence (FR-008) and reproducibility (Constitution Principle I) without manual CSV entry.
* **VDOS-Ref**: No verified source for reference VDOS.
 * *Mitigation*: The pipeline will generate VDOS from the downloaded trajectories and compare the *shape* (e.g., peak location 10-15 THz) against known literature values for amorphous silicon (cited in `research.md` as a general reference).

## Statistical Rigor & Feasibility

### Statistical Rigor
* **Sample Size**: The design uses N≥30 independent snapshots per system size, providing sufficient degrees of freedom for valid correlation and bootstrap analysis (addressing methodology-80495c6c).
* **Multiple Comparisons**: FR-007 mandates correction. The plan will apply Bonferroni correction for the number of topological metrics tested.
* **Power Analysis**: SC-002 requires power calculation. With N≥30, power is expected to be adequate for moderate effects. The plan will explicitly report the calculated power.
* **Causal Framing**: The study is observational. All claims will be framed as "associational" (Constitution Principle II).
* **Collinearity**: Coordination number and bond angle variance are likely correlated. The plan will report the Variance Inflation Factor (VIF) if a multivariate model is attempted.
* **Finite-Size Effects**: By analyzing within system size groups, we decouple system size from topological disorder (methodology-c292547a).

### Compute Feasibility (CPU-First)
* **Memory**: The pipeline processes trajectories frame-by-frame or in chunks. VDOS calculation is $O(N \cdot T)$ but can be streamed. With $N \le 4000$, memory usage will be well under 7 GB.
* **Runtime**:
 * RDF and Bond Network: Optimized via neighbor lists.
 * VDOS: FFT of VACF is $O(T \log T)$.
 * Bootstrap: 1000 iterations on N≥30 is trivial.
* **Conclusion**: The entire pipeline is CPU-tractable and fits within the GitHub Actions limit. No GPU escape hatch is required.

## Risk Assessment

1. **Data Availability Risk**: Mitigated by programmatic reference generation.
2. **Numerical Instability**: Mitigated by windowing functions and `float64` precision.
3. **Ambiguous RDF Minimum**: Mitigated by fallback to user-specified override (logged).
4. **Circular Validation Risk**: Mitigated by strict independence checks in `reference_generator.py`.
5. **Low Power Risk**: Mitigated by N≥30 design; flagged if power < 0.8.

## References
* *Amorphous Silicon VDOS characteristics*: General knowledge of Si phonon spectra (10-15 THz peak).
* *Wooten-Winer-Weaire (WWW) Model*: Standard for defect identification in tetrahedral networks.
* *Bootstrap Methods*: Efron, B. (1979). "Bootstrap Methods: Another Look at the Jackknife".
* *Cahill-Pohl Limit*: Cahill, D. G., et al. (1992). "Thermal conductivity of amorphous solids above the plateau".