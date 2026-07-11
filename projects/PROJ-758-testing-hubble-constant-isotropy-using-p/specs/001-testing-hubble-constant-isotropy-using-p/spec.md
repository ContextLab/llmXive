# Feature Specification: Testing Hubble Constant Isotropy Using Pantheon Supernova Sample

**Feature Branch**: `001-testing-hubble-constant-isotropy`  
**Created**: 2026-06-23  
**Status**: Draft  
**Input**: User description: "Does the locally measured Hubble constant (H₀) show statistically significant directional variation across the sky when estimated from the Pantheon+ Type Ia supernova compilation?"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Sky Partitioning (Priority: P1)

The research pipeline must successfully ingest the Pantheon+ dataset, apply standard quality cuts (redshift < 0.15, valid flags), and map every supernova to a unique HEALPix pixel on the celestial sphere. This forms the foundational data structure for all subsequent regional analysis.

**Why this priority**: Without a clean, spatially indexed dataset, no regional H₀ estimates can be generated. This is the prerequisite for the entire study.

**Independent Test**: Can be fully tested by running the data loader and verifying that the output DataFrame contains exactly the expected number of rows (after cuts) and that every row has a valid `healpix_index` corresponding to the input `ra`/`dec`.

**Acceptance Scenarios**:

1. **Given** the raw Pantheon+ CSV file, **When** the pipeline applies the redshift cut (z < 0.15) and quality flag filter, **Then** the resulting dataset contains only valid low-redshift supernovae and the row count matches the expected subset size.
2. **Given** a supernova with valid celestial coordinates (RA, Dec), **When** the HEALPix assignment function is called with Nside=4 and NESTED ordering, **Then** the output is a valid integer pixel index between 0 and 191, and the inverse projection recovers the original coordinates within floating-point tolerance.

---

### User Story 2 - Local and Global H₀ Estimation (Priority: P2)

The system must calculate a global H₀ from the full sample and independent local H₀ estimates for each HEALPix pixel containing sufficient data. The estimation must use a fit of the luminosity distance model d_L(z) = c/H₀ ∫ dz'/E(z') to the Hubble diagram (distance modulus μ vs. redshift z) to extract H₀ from the intercept/normalization, correcting for local bulk flows.

**Why this priority**: This is the core analytical step that generates the primary variable of interest (regional H₀ deviations). It directly addresses the research question.

**Independent Test**: Can be tested by running the regression module on a synthetic dataset with a known H₀ and verifying that the estimated H₀ matches the ground truth within a defined tolerance (e.g., ±1 km/s/Mpc).

**Acceptance Scenarios**:

1. **Given** a subset of supernovae in a single HEALPix pixel with N ≥ 30, **When** the cosmological model fit is performed on distance modulus vs. redshift (with peculiar velocity correction applied), **Then** the slope yields a local H₀ estimate with an associated standard error.
2. **Given** the full Pantheon+ dataset, **When** the global regression is performed, **Then** the resulting H₀ estimate is consistent with the literature value (approx. 73 km/s/Mpc) within the expected statistical uncertainty of the sample.

---

### User Story 3 - Anisotropy Quantification and Statistical Significance (Priority: P3)

The pipeline must compute the dipole and quadrupole moments of the H₀ deviation map, perform Monte Carlo simulations to determine if observed anisotropies exceed random fluctuations, and apply a False Discovery Rate correction to the joint test of these modes.

**Why this priority**: This step transforms raw regional estimates into a scientific conclusion (isotropy vs. anisotropy) and addresses the "Specific objection" regarding bulk flows and selection effects by establishing a statistical baseline.

**Independent Test**: Can be tested by generating a synthetic isotropic dataset (constant H₀ + noise), running the anisotropy analysis, and verifying that the resulting p-value for dipole/quadrupole power is > 0.05 in the majority of trials.

**Acceptance Scenarios**:

1. **Given** the map of local H₀ deviations, **When** the spherical harmonic decomposition is performed, **Then** the dipole (ℓ=1) and quadrupole (ℓ=2) amplitudes are computed and stored.
2. **Given** 1,000 Monte Carlo realizations where the underlying cosmology is isotropic (constant H₀) and noise is added, **When** the anisotropy metrics are recalculated, **Then** the distribution of simulated dipole amplitudes allows for the calculation of a p-value for the observed amplitude.
3. **Given** the observed dipole amplitude and the null distribution from Monte Carlo randomization, **When** the p-value is calculated and adjusted for multiple comparisons (dipole and quadrupole), **Then** it is reported alongside a binary decision flag (Significant if p < 0.05, Insignificant otherwise).

### Edge Cases

- What happens when a HEALPix pixel contains fewer than the minimum required supernovae (e.g., < 30) to perform a stable regression? The system must skip the pixel for bootstrap analysis and instead apply a hierarchical Bayesian estimation that borrows strength from neighboring pixels, logging a warning.
- How does the system handle supernovae with missing or invalid redshift/coordinate data? These entries must be filtered out during the initial ingestion step with a clear audit trail of the count removed.
- What occurs if the Monte Carlo simulation fails to converge or produces a degenerate distribution? The system must detect this condition and flag the specific pixel as "unreliable" rather than propagating erroneous statistics.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST ingest the Pantheon+ dataset, apply a redshift cut of z < 0.15, and filter by quality flags to create a clean analysis sample (See US-1).
- **FR-002**: The system MUST assign every valid supernova to a HEALPix pixel using Nside=4 and NESTED ordering, ensuring full-sky coverage without overlap (See US-1).
- **FR-003**: The system MUST apply a peculiar velocity correction using the CosmicFlows-3 model to the redshifts, then fit the luminosity distance model d_L(z) = c/H₀ ∫ dz'/E(z') to the Hubble diagram (μ vs. z) to estimate H₀ for both the global sample and each individual HEALPix pixel with N ≥ 30 (See US-2).
- **FR-004**: The system MUST generate a sufficient number of Monte Carlo realizations (≥ 1,000) where the underlying cosmology is isotropic (constant H₀) and noise is added, to quantify the uncertainty of the local H₀ estimates (See US-3).
- **FR-005**: The system MUST compute the dipole (ℓ=1) and quadrupole (ℓ=2) spherical harmonic coefficients of the H₀ deviation map and compare them against a null distribution generated by randomizing supernova positions within the observed Pantheon+ selection function (survey mask) (See US-3).
- **FR-006**: The system MUST implement the Benjamini-Hochberg False Discovery Rate (FDR) correction at q=0.05 when evaluating the joint significance of the dipole and quadrupole modes to control the family-wise error rate (See US-3).
- **FR-007**: The system MUST perform a sensitivity analysis by varying the redshift cut threshold (e.g., z < 0.10, z < 0.15, z < 0.20) and reporting the stability of the anisotropy metrics across these thresholds (See US-3).

### Key Entities

- **Supernova Record**: Represents a single Type Ia supernova, containing attributes for RA, Dec, redshift (z), distance modulus (μ), and quality flags.
- **HEALPix Pixel**: A spatial partition of the sky, identified by an integer index (NESTED), containing a list of associated Supernova Records.
- **H₀ Estimate**: A derived metric representing the expansion rate, containing the central value, standard error, and the subset of data (Pixel or Global) used for its calculation.
- **Anisotropy Metric**: A composite result containing dipole/quadrupole amplitudes, p-values, and the method used for statistical validation (Monte Carlo).

## Success Criteria

### Measurable Outcomes

- **SC-001**: The proportion of HEALPix pixels with valid H₀ estimates (N ≥ 30 supernovae) is measured against the total number of pixels (192) to ensure sufficient sky coverage for the dipole analysis (See US-1, US-2).
- **SC-002**: The standard deviation of the global H₀ estimate is measured against the theoretical uncertainty calculated via the Cramér-Rao bound for the given Pantheon+ sample size to validate the regression implementation (See US-2).
- **SC-003**: The p-value for the observed dipole amplitude is measured against the null distribution generated by Monte Carlo simulations to determine statistical significance. (See US-3).
- **SC-004**: The variation in the dipole amplitude across three distinct redshift cuts (z < 0.10, 0.15, 0.20) is measured to assess the robustness of the result against sample selection (See FR-007).
- **SC-005**: The family-wise error rate for the joint test of dipole and quadrupole modes is measured against the nominal alpha level (0.05) in a null simulation, verifying that the observed false positive rate is ≤ 0.05 + 0.01 (See FR-006).

## Assumptions

- The Pantheon+ dataset provided via the Zenodo repository contains all necessary variables (RA, Dec, redshift, distance modulus, and quality flags) required for the analysis; if any variable is missing, the pipeline will halt with a `The Pantheon+ dataset (Scolnic et al., Zenodo) is missing required variables: [list of missing variables]` error.
- The analysis is observational; therefore, any detected anisotropy will be framed as an **associational** relationship between sky position and H₀, not a causal effect, unless the user explicitly specifies a randomization strategy (which is not present in the current design).
- The GitHub Actions free-tier runner (multi-core CPU, several GB RAM) is sufficient for processing the ~200 MB Pantheon+ dataset and running a statistically significant number of Monte Carlo iterations (≥ 1,000), provided that memory-intensive operations (like large matrix inversions) are avoided or optimized.
- The standard HEALPix Nside=4 resolution (192 pixels) provides an optimal balance between spatial resolution and the number of supernovae per pixel for this specific sample size; lower resolutions (Nside=2) are used only for robustness checks.
- The "local bulk flows" and "selection effects" mentioned in the reviewer's objection are treated as potential sources of systematic error; the statistical significance test (Monte Carlo randomization within the selection function) is designed to distinguish these from true anisotropy by establishing a null distribution of random fluctuations.
- The redshift cut of z < 0.15 is a community-standard default for "local" H₀ measurements using supernovae; if the dataset is sparse below this threshold, the cutoff will be adjusted to z < 0.10 or z < 0.20 as part of the sensitivity analysis (FR-007).