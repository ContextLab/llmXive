# Feature Specification: Testing the Isotropy of Cosmic Expansion with Type Ia Supernova Data

**Feature Branch**: `001-testing-isotropy-cosmic-expansion`  
**Created**: 2026-06-22  
**Status**: Draft  
**Input**: User description: "Testing the Isotropy of Cosmic Expansion with Type Ia Supernova Data"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Residual Calculation (Priority: P1)

The system MUST ingest the Pantheon+ Type Ia Supernova dataset, apply the standard flat ΛCDM cosmological model to calculate distance-modulus residuals, and map each supernova to its celestial coordinates (RA, Dec).

**Why this priority**: This is the foundational data layer. Without accurate residuals and sky positions, no subsequent anisotropy analysis can occur. It delivers the primary dataset required for the hypothesis test.

**Independent Test**: This can be tested by running the ingestion script on the Pantheon+ release and verifying that the output CSV contains the exact number of rows defined in the official Pantheon+ release v1.0 metadata (specifically the row count of the 'full' sample), valid RA/Dec coordinates, and calculated residuals that match a manual calculation for a known subset of supernovae.

**Acceptance Scenarios**:

1. **Given** the Pantheon+ release file is available, **When** the ingestion script executes, **Then** the output file contains all supernovae with calculated residuals relative to the flat ΛCDM model and valid sky coordinates.
2. **Given** a subset of 10 supernovae with known published residuals, **When** the system calculates residuals, **Then** the computed values match the published values within a tolerance of the reported uncertainty or a negligible magnitude..

---

### User Story 2 - Spherical Harmonic Decomposition and Dipole/Quadrupole Extraction (Priority: P2)

The system MUST project the residuals onto a HEALPix grid (Nside=32), compute spherical harmonic coefficients up to ℓ=3 using a mask-aware method, and extract the amplitudes of the dipole (ℓ=1) and quadrupole (ℓ=2) terms.

**Why this priority**: This implements the core scientific method for detecting anisotropy. It transforms raw spatial data into the specific statistical metrics (dipole/quadrupole amplitudes) required to test the Cosmological Principle.

**Independent Test**: This can be tested by generating a synthetic dataset with a known injected dipole signal, running the decomposition, and verifying that the extracted dipole amplitude matches the injected signal within statistical error bounds.

**Acceptance Scenarios**:

1. **Given** a set of residuals mapped to a HEALPix grid, **When** the spherical harmonic analysis runs, **Then** the system outputs the coefficients $a_{\ell m}$ for $\ell \in \{1, 2, 3\}$.
2. **Given** the calculated coefficients, **When** the amplitude extraction logic runs, **Then** the system outputs a dipole amplitude and a quadrupole amplitude with units of magnitudes.

---

### User Story 3 - Null Distribution Simulation and Significance Assessment (Priority: P3)

The system MUST generate a statistically sufficient set of isotropic mock catalogs by applying random 3D rotation matrices to the celestial coordinates relative to a fixed survey mask while preserving the original redshift and uncertainty distributions, compute their dipole/quadrupole amplitudes, and compare the observed values against this null distribution to derive p-values.

**Why this priority**: This establishes the statistical significance of any detected signal. Without the null distribution, observed amplitudes are meaningless. It provides the final "pass/fail" metric for the research question.

**Independent Test**: This can be tested by running the simulation with a dataset known to be isotropic (e.g., randomized data) and verifying that the observed dipole falls within the 95% confidence interval of the null distribution (p-value > 0.05).

**Acceptance Scenarios**:

1. **Given** the observed dipole amplitude, **When** the system compares it against a large set of simulated isotropic amplitudes, **Then** the system outputs a p-value representing the fraction of simulations exceeding the observed value.
2. **Given** a p-value < 0.05, **When** the system generates the final report, **Then** the report flags the result as "statistically significant anisotropy" with a 95% confidence level.

---

### Edge Cases

- **What happens when** the Pantheon+ dataset contains supernovae with missing redshift or uncertainty values? The system must filter these entries and log the count of excluded supernovae to ensure the sample size is accurate.
- **How does the system handle** regions of the sky with extremely low supernova density? The HEALPix projection must handle empty pixels gracefully without crashing, and the analysis must treat them as zero-contribution rather than missing data errors.
- **What happens when** the calculated dipole amplitude is exactly on the boundary of the 95% confidence interval? The system must report the exact p-value to three decimal places rather than a binary pass/fail, allowing for nuanced interpretation.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and parse the Pantheon+ supernova dataset, filtering for entries with valid RA, Dec, redshift, and distance modulus values (See US-1).
- **FR-002**: System MUST calculate distance-modulus residuals by subtracting the theoretical distance modulus (derived from the flat ΛCDM model) from the observed values. The cosmological parameters ($H_, \Omega_m, \Omega_\Lambda$) MUST be extracted from the Pantheon+ dataset metadata. If metadata is missing, the system MUST default to the release's stated values (e.g., $H_0$) as recorded in the official Pantheon+ release paper. The theoretical distance modulus MUST be calculated via numerical integration of the inverse Hubble parameter $/E(z)$ over redshift with a stringent tolerance., using the formula $\mu_{th} = 5 \log_{10}(d_L(z)) + 25$, where $d_L(z) = (1+z) \int_0^z \frac{c}{H_0 E(z')} dz'$ (See US-1).
- **FR-003**: System MUST project the residuals onto a HEALPix grid with Nside=32, ensuring each supernova is assigned to the correct pixel based on its RA and Dec (See US-2).
- **FR-004**: System MUST compute spherical harmonic coefficients $a_{\ell m}$ for $\ell \le 3$ using the pseudo-C_l method with MASTER correction to account for the survey mask, and extract the scalar amplitudes for the dipole ($\ell=1$) and quadrupole ($\ell=2$) components (See US-2).
- **FR-005**: System MUST generate [deferred] isotropic mock catalogs by applying random 3D rotation matrices to the celestial coordinates relative to a fixed survey mask while preserving the original redshift and uncertainty distribution, then compute their dipole/quadrupole amplitudes to form a null distribution. The randomization MUST use a fixed seed (seed=42) for reproducibility (See US-3).
- **FR-006**: System MUST flag the result as "statistically significant anisotropy" if the calculated p-value is strictly less than 0.05 (95% confidence level) (See US-3).

### Key Entities

- **Supernova Record**: Represents a single Type Ia supernova with attributes: ID, RA, Dec, Redshift, Distance Modulus, Uncertainty, and Calculated Residual.
- **Healpix Pixel**: Represents a spatial bin on the celestial sphere with attributes: Pixel Index, Nside, and Aggregated Residual Mean.
- **Harmonic Coefficient**: Represents a term in the spherical harmonic expansion with attributes: $\ell$, $m$, Real Part, Imaginary Part.
- **Null Simulation**: Represents one iteration of the isotropic mock catalog with attributes: Run ID, Dipole Amplitude, Quadrupole Amplitude.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The fraction of supernovae successfully mapped to the HEALPix grid is measured against the total valid supernovae in the Pantheon+ release (See US-1).
- **SC-002**: The reproducibility of the dipole amplitude is measured against the output of a canonical implementation using HEALPix, Astropy, and the pseudo-C_l method with MASTER correction on a subset of supernovae. (See US-2).
- **SC-003**: The stability of the null distribution is measured by the standard deviation of the simulated dipole amplitudes., ensuring convergence defined as the running mean changing by < 0.001 mag over the last 1,000 simulations (See US-3).
- **SC-004**: The computational runtime of the full analysis (including a large-scale set of simulations) is measured against the GitHub Actions free-tier limit (See US-3).

## Assumptions

- The Pantheon+ dataset provided by the official repository contains all necessary variables (RA, Dec, Redshift, Distance Modulus, Uncertainty) required for the analysis; if any variable is missing for a subset of supernovae, those entries are excluded from the analysis.
- The flat ΛCDM model parameters ($H_0, \Omega_m$) used for residual calculation are derived from the dataset's metadata to ensure consistency with the dataset's native calibration.
- The analysis is observational; therefore, any detected anisotropy will be framed as an associational signal rather than a causal mechanism, consistent with the lack of random assignment in the data.
- The computational environment (GitHub Actions free tier) provides sufficient CPU and RAM to process 10,000 simulations on the ~1500 supernova dataset within 6 hours; if memory constraints arise, the simulation count may be reduced to a manageable level with a corresponding note on reduced statistical power.
- The HEALPix library (e.g., `healpy` in Python) is available and compatible with the CPU-only environment for spherical harmonic decomposition.
- The redshift distribution of the Pantheon+ sample is representative of the cosmic expansion history for the purpose of this isotropy test, and selection biases are mitigated by the rotation-aware null simulation strategy.