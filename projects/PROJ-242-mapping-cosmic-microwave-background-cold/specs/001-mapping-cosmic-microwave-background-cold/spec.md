# Feature Specification: Mapping Cosmic Microwave Background Cold Spots to Large-Scale Structure

**Feature Branch**: `001-mapping-cmb-cold-spots`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Mapping CMB Cold Spots to Large-Scale Structure to test the supervoid hypothesis via Integrated Sachs-Wolfe effect."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Ingestion and Preprocessing (Priority: P1)

The researcher MUST be able to download, parse, and preprocess the Planck 2018 CMB temperature maps and the SDSS/DES galaxy density catalogs into a unified, memory-efficient format suitable for CPU-only analysis.

**Why this priority**: Without clean, aligned data, no statistical analysis can occur. This is the foundational step for the entire project.

**Independent Test**: The system can be tested by running the data pipeline on a small subset (e.g., [deferred] of the sky) and verifying that the output HEALPix maps (nside=64) contain valid temperature and density values without NaNs or memory errors on a 7GB RAM limit.

**Acceptance Scenarios**:

1. **Given** the Planck Legacy Archive and SDSS DR16 URLs, **When** the ingestion script executes, **Then** the system downloads the commander/smica CMB maps and the galaxy catalog subset, converts them to HEALPix nside=64, and saves them as compressed FITS files within 30 minutes.
2. **Given** the raw galaxy catalog, **When** the redshift binning process runs for z=0.2–1.0, **Then** the system produces three distinct density maps (z-bins) with no more than 5% pixel loss due to missing redshift data, and the total memory usage remains below 4 GB.

---

### User Story 2 - Cold Spot Identification and Cross-Correlation (Priority: P2)

The researcher MUST be able to identify cold spot candidates using a top-hat filter and compute the cross-correlation function $\xi(\theta)$ between these spots and the underdense regions in the galaxy maps.

**Why this priority**: This implements the core physics hypothesis (alignment of CMB anomalies with supervoids). It is the primary analytical engine of the feature.

**Independent Test**: The system can be tested by applying the pipeline to a synthetic Gaussian random field where the correlation is known to be zero, verifying that the computed $\xi(\theta)$ is statistically indistinguishable from zero.

**Acceptance Scenarios**:

1. **Given** the preprocessed CMB map, **When** the top-hat filter (radius 5°) is applied, **Then** the system identifies all pixels with temperature $< -2\sigma$ from the mean and outputs a list of 10–50 candidate cold spot coordinates.
2. **Given** the cold spot coordinates and the galaxy density maps, **When** the cross-correlation function is computed, **Then** the system outputs a correlation curve $\xi(\theta)$ for angular separations $\theta \in [0°, 10°]$ with a resolution of 0.1°, completing the calculation in [deferred].

---

### User Story 3 - Statistical Significance and Sensitivity Analysis (Priority: P3)

The researcher MUST be able to generate 1000 ΛCDM Gaussian random realizations to establish a null distribution, perform a Kolmogorov-Smirnov (KS) test, and run a sensitivity analysis on the cold spot threshold.

**Why this priority**: This provides the statistical rigor required to claim a discovery or a null result, addressing the "multiplicity" and "threshold justification" methodological requirements.

**Independent Test**: The system can be tested by running the simulation suite on a CPU-only runner; the KS test must return a p-value, and the sensitivity sweep must show how the p-value changes with threshold adjustments.

**Acceptance Scenarios**:

1. **Given** the observed correlation amplitude, **When** the simulation module generates 1000 ΛCDM realizations using CAMB/CLASS, **Then** the system computes the null distribution and performs a KS test, returning a p-value within 60 seconds of simulation completion.
2. **Given** the baseline threshold of $-2\sigma$, **When** the sensitivity analysis runs, **Then** the system sweeps the threshold over $\{-2.0\sigma, -2.05\sigma, -2.1\sigma\}$ and outputs a table showing the variation in the KS p-value and the number of detected cold spots for each threshold.

### Edge Cases

- What happens when the galaxy catalog has a gap in redshift coverage (e.g., $z \approx 0.5$)? The system must interpolate or mask the gap without crashing, and log a warning.
- How does the system handle a scenario where no cold spots meet the $-2\sigma$ threshold? The system must gracefully handle an empty list of candidates and report a p-value of 1.0 (no correlation) rather than failing with a division-by-zero error.
- What if the HEALPix map generation fails due to memory constraints on the 7GB limit? The system must automatically downsample to nside=32 and log the resolution change.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download Planck 2018 CMB maps (commander/smica) and SDSS/DES galaxy catalogs, converting them to HEALPix nside=64 format, serving US-1 (See US-1).
- **FR-002**: System MUST identify cold spot candidates by applying a top-hat filter (radius 5°) and thresholding at $-2\sigma$ from the mean temperature, serving US-2 (See US-2).
- **FR-003**: System MUST compute the cross-correlation function $\xi(\theta)$ between identified cold spots and underdense regions in redshift bins $z \in [0.2, 1.0]$, serving US-2 (See US-2).
- **FR-004**: System MUST generate 1000 ΛCDM Gaussian random realizations and perform a Kolmogorov-Smirnov test to compare observed vs. simulated correlation amplitudes, serving US-3 (See US-3).
- **FR-005**: System MUST execute a sensitivity analysis sweeping the cold spot threshold over $\{-2.0\sigma, -2.05\sigma, -2.1\sigma\}$ and report the resulting variation in p-values, serving US-3 (See US-3).
- **FR-006**: System MUST ensure all computations (data loading, correlation, simulation) complete within 6 hours on a 2-core, 7GB RAM CPU-only environment, serving US-1 (See US-1).

### Key Entities

- **CMB Map**: A HEALPix pixelized representation of the CMB temperature anisotropy (nside=64), derived from Planck 2018 data.
- **Galaxy Density Map**: A HEALPix pixelized representation of galaxy number density in specific redshift shells, derived from SDSS/DES catalogs.
- **Cold Spot Candidate**: A coordinate (RA, Dec) and temperature deviation value identified as an underdense region in the CMB map.
- **Correlation Amplitude**: The scalar value representing the strength of the alignment between cold spots and underdensities at a specific angular scale.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The observed cross-correlation amplitude is measured against the null distribution generated from 1000 ΛCDM realizations to determine statistical significance (See US-3).
- **SC-002**: The sensitivity of the detection (p-value stability) is measured against the variation in the cold spot threshold ($\{-2.0\sigma, -2.05\sigma, -2.1\sigma\}$) to validate threshold robustness (See US-3).
- **SC-003**: The computational feasibility is measured against the 6-hour runtime limit and 7GB RAM constraint on the GitHub Actions free-tier runner (See US-1).
- **SC-004**: The alignment strength is measured against the theoretical prediction of the Integrated Sachs-Wolfe effect for supervoids to assess physical consistency (See US-2).

## Assumptions

- The Planck 2018 CMB maps and SDSS/DES galaxy catalogs are publicly available and accessible via the provided URLs without requiring authentication or complex proxy configurations.
- The "cold spot" definition using a $-2\sigma$ threshold and 5° radius is sufficient for initial detection; more complex topological definitions are out of scope for this MVP.
- The galaxy photometric redshifts in the SDSS/DES catalogs are accurate enough to bin galaxies into $z=0.2–1.0$ shells with minimal catastrophic outlier contamination.
- The integrated Sachs-Wolfe (ISW) effect is the primary physical mechanism linking CMB cold spots to large-scale structure underdensities in this redshift range.
- The dataset fits within the 7GB RAM limit after HEALPix downsampling to nside=64; if the full-resolution data is required, the analysis will be restricted to a [deferred] sky fraction.
- The "multiplicity" issue of testing multiple redshift bins is addressed by the global KS test across the combined correlation signal, rather than individual bin tests requiring Bonferroni correction.
