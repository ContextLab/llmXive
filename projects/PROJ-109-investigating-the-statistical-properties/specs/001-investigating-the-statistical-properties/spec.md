# Feature Specification: Investigating Statistical Properties of Simulated Dark Matter Halos

**Feature Branch**: `[001-dark-matter-halo-statistics]`  
**Created**: 2025-01-15  
**Status**: Draft  
**Input**: User description: "Investigate statistical properties of simulated dark matter halos from IllustrisTNG and Millennium, testing deviations from NFW framework predictions across mass and environment bins"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Acquisition and Pre-processing (Priority: P1)

Download and filter public cosmological simulation catalogs (IllustrisTNG TNG100-1 and Millennium) to produce a validated halo dataset ready for structural analysis. This includes downloading the full particle catalog for neighbor counting.

**Why this priority**: Without access to validated halo data and full particle positions for environment calculation, no structural metrics or statistical comparisons can be computed. This is the foundational step that enables all downstream analysis.

**Independent Test**: Can be fully tested by successfully downloading both catalogs (including particle data), filtering for halos with ≥300 particles, and producing a consolidated dataset file that contains all required columns (mass, position, velocity, particle counts).

**Acceptance Scenarios**:

1. **Given** the IllustrisTNG and Millennium public data release URLs are accessible via the official API, **When** the download scripts execute, **Then** both halo catalogs and necessary particle data are saved locally in HDF5/pandas-compatible format within 30 minutes
2. **Given** the raw halo catalogs contain variable particle counts, **When** the filtering routine executes, **Then** only halos with ≥300 particles are retained and a count of filtered vs. total halos is logged

---

### User Story 2 - Structural Metric Computation (Priority: P2)

Compute shape (s=c/a), spin parameter (λ), and concentration index (c) for each halo using validated physical formulas.

**Why this priority**: These three metrics are the core research variables; without accurate computation, hypothesis testing cannot proceed. P2 because it depends on US-1 data availability.

**Independent Test**: Can be fully tested by running the metric computation on a sample of 100 halos and verifying that output distributions match expected physical ranges (shape s ∈ [0,1], spin λ ∈ [0,1], concentration c > 0).

**Acceptance Scenarios**:

1. **Given** a halo with ≥300 particles and valid velocity/position data, **When** the inertia tensor calculation executes, **Then** the shape parameter s=c/a is computed with s ∈ [,1]
2. **Given** a halo with valid angular momentum (J), energy (E), mass (M), and gravitational constant (G), **When** the spin parameter formula executes, **Then** λ=J|E|^(1/2)/(GM^(5/2)) is computed with λ ∈ [0,1]
3. **Given** a radial density profile for a halo, **When** the NFW profile fit executes via scipy.optimize.curve_fit, **Then** concentration c=R_(200)/r_s is returned with algorithmic convergence achieved (success flag is True) and reduced chi-squared ≈ 1 (p-value > 0.05)

---

### User Story 3 - Statistical Hypothesis Testing (Priority: P3)

Perform Kolmogorov-Smirnov tests and Spearman correlations to assess deviations from NFW/ΛCDM predictions across mass and environment bins.

**Why this priority**: This delivers the research answer but depends on US-1 and US-2 being complete. P3 because it is the final analytical layer.

**Independent Test**: Can be fully tested by running the full statistical pipeline on the processed dataset and producing a results summary with p-values, effect sizes, and visualizations saved as PNG/PDF.

**Acceptance Scenarios**:

1. **Given** halo metrics binned by mass (10^10-10^11, 10^11-10^12 M⊙ h⁻¹) and by environment (low vs. high overdensity), **When** two-sample KS tests execute between the low and high bins, **Then** p-values and effect sizes are recorded for each metric-environment combination
2. **Given** the mass-concentration relationship data, **When** Spearman's ρ correlation executes, **Then** correlation coefficient and p-value are computed against the null hypothesis of zero correlation
3. **Given** multiple hypothesis tests (≥9 KS tests across 3 metrics × 3 bins), **When** the multiplicity correction executes, **Then** a family-wise error correction (e.g., Bonferroni or Benjamini-Hochberg) is applied and adjusted p-values are reported
4. **Given** the measured mass-concentration relation data, **When** the comparison against the Bullock et al. (2001) analytic fit executes, **Then** the deviation statistics (mean difference, RMSE) are computed and reported

---

### Edge Cases

- What happens when a halo has exactly 300 particles (boundary condition for filtering)? → Include in dataset; log particle count distribution to verify cutoff impact
- How does system handle halos where NFW profile fit fails to converge? → Exclude from concentration analysis; log count and percentage of failed fits
- What happens when the simulation catalog is missing a required column (e.g., velocities)? → Halt execution with explicit error message. The Millennium Simulation (and subsequent iterations) provides full 6D phase-space data (positions and velocities) for all particles and halos. The spin parameter λ will be computed using these velocity fields from the public `galaxy` or `subhalo` catalog tables (specifically `SubhaloVelocities`). (See US-2)
- How does system handle environments with insufficient halos for KDE estimation? → Skip KDE for that bin; use histogram with ≥30 samples minimum

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download IllustrisTNG TNG100-1 and Millennium halo catalogs and full particle catalogs from public data release URLs via the official API and save locally in HDF5/pandas format (See US-1)
- **FR-002**: System MUST filter halos to retain only those with ≥300 particles and log the filtered count (See US-1)
- **FR-003**: System MUST compute local overdensity for each halo using a spherical top-hat of 5 Mpc h⁻¹ radius via cKDTree neighbor counting, explicitly wrapping coordinates to account for periodic boundary conditions using the simulation box size, and defining overdensity as Δ = ρ_local / ρ_critical (See US-3)
- **FR-004**: System MUST calculate shape parameter s=c/a from the inertia tensor of particle positions with axis ratios a≥b≥c (See US-2)
- **FR-005**: System MUST compute dimensionless spin parameter λ=J|E|^(1/2)/(GM^(5/2)) using particle velocities and positions, where total energy E is estimated via direct summation approximation of potential energy (See US-2)
- **FR-006**: System MUST attempt to fit NFW profile to radial density profile via scipy.optimize.curve_fit and extract concentration c=R_(200)/r_s; halos where the fit fails to converge (success flag is False) MUST be excluded from concentration analysis (See US-2)
- **FR-007**: System MUST bin halos by mass (10^10-10^11, 10^11-10^12 M⊙ h⁻¹) and by environment (low vs. high overdensity threshold defined as Δ < 200 vs. Δ ≥ 200, relative to critical density) (See US-3)
- **FR-008**: System MUST perform two-sample Kolmogorov-Smirnov tests between the low and high environmental bins for shape, spin, and concentration metrics (See US-3)
- **FR-009**: System MUST apply family-wise error correction (Bonferroni or Benjamini-Hochberg) to adjust for multiple hypothesis testing across ≥9 KS tests (See US-3)
- **FR-010**: System MUST compute Spearman's ρ correlation between halo mass and each structural metric, testing against null hypothesis of zero correlation (See US-3)
- **FR-011**: System MUST compare measured mass-concentration relation to Bullock et al. () analytic fit and report deviation statistics (See US-3)
- **FR-012**: System MUST produce scatter plots, KDE curves, and heatmaps using matplotlib/seaborn and save as PNG/PDF (See US-3)

### Key Entities

- **Halo**: Represents a dark matter halo from simulation catalog; key attributes include mass, particle count, position (x,y,z), velocity (vx,vy,vz), shape parameter s, spin parameter λ, concentration c, local overdensity
- **MassBin**: Represents a halo mass range for stratification; key attributes include lower bound, upper bound, halo count, mean metrics
- **EnvironmentBin**: Represents a large-scale overdensity classification; key attributes include threshold value, bin label (low/high), halo count, mean metrics

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: KS test p-values for shape, spin, and concentration distributions between low and high environmental bins are measured against the null hypothesis of environmental independence (See US-3)
- **SC-002**: Spearman correlation coefficients for mass-concentration relationship are measured against the canonical inverse mass-concentration trend from literature (See US-3)
- **SC-003**: Family-wise error corrected p-values are measured against the significance threshold α=0.05 to determine statistical significance of deviations (See US-3)
- **SC-004**: NFW profile fit convergence rate is measured and reported as the percentage of halos with ≥300 particles achieving algorithmic convergence (See US-2)
- **SC-005**: Deviation statistics (RMSE, mean difference) between measured mass-concentration relation and Bullock et al. (2001) fit are measured and reported (See US-3)

## Assumptions

- IllustrisTNG TNG100-1 and Millennium Simulation halo catalogs contain all required variables: particle positions, velocities, mass, and particle counts for shape, spin, and concentration computation
- The Millennium Simulation FTP site remains accessible throughout the analysis window
- Halos with ≥300 particles provide sufficient statistical power for reliable structural measurements (shape, spin, concentration)
- A spherical top-hat for local overdensity computation is a defensible community-standard choice for large-scale environment classification.
- NFW profile fitting via scipy.optimize.curve_fit achieves convergence for a majority of halos with ≥300 particles; failed fits are excluded from concentration analysis
- The GitHub Actions free-tier runner (multiple CPU cores, sufficient RAM, sufficient disk) is sufficient for processing both catalogs with sampling/subsetting if needed to fit memory constraints
- No GPU/CUDA accelerators are required; all methods (KDE, KS tests, curve fitting, Spearman correlation) are CPU-tractable
- The Millennium Simulation (and Millennium-2) provides full 6D phase-space data (positions and velocities) for all particles and halos. The spin parameter λ will be computed using these velocity fields from the public `galaxy` or `subhalo` catalog tables (specifically `SubhaloVelocities`). (See US-2)
- The IllustrisTNG and Millennium catalogs provide particle positions but do not pre-compute local overdensity for every halo in the summary tables. FR-003 mandates computing local overdensity via a spherical top-hat of 5 Mpc h⁻¹ radius using cKDTree neighbor counting on the provided particle/subhalo positions. (See US-2)
- The system will use the official IllustrisTNG Data API to dynamically resolve the latest Snapshot URL for programmatic access, ensuring compatibility with future data releases. (See US-1)
- The Bullock et al. (2001) analytic fit for mass-concentration relationship is available for comparison without requiring additional data download
- Multiple comparison correction uses Benjamini-Hochberg procedure for false discovery rate control rather than Bonferroni, as it is less conservative for exploratory analysis
- Sensitivity analysis for environment overdensity threshold sweeps values over a range of Mpc h⁻¹ and reports how halo classification rates vary across this set
- The overdensity threshold Δ ≥ 200 is chosen based on the standard virial overdensity definition in cosmological simulations (Bryan & Norman 1998).