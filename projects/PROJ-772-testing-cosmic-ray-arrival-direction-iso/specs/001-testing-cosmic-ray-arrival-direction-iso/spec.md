# Feature Specification: Testing Cosmic Ray Arrival Direction Isotropy with Public Ultra‑High‑Energy Data

**Feature Branch**: `001-testing-cosmic-ray-arrival-direction-iso`  
**Created**: 2026-06-24  
**Status**: Draft  
**Input**: User description: "Do the arrival directions of ultra‑high‑energy cosmic rays (E > 50 EeV) exhibit statistically significant large‑scale anisotropies—detectable via the angular power spectrum up to ℓ = 5—relative to the expectation from an isotropic sky?"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Pre-processing (Priority: P1)

The researcher must be able to download the public UHECR event catalogs from the Pierre Auger Observatory and Telescope Array, apply the energy cut (E > 50 EeV), and convert the Right Ascension (RA) and Declination (Dec) coordinates into a HEALPix sky map (Nside=64) ready for analysis.

**Why this priority**: This is the foundational step. Without a clean, correctly formatted dataset, no statistical analysis can occur. It validates the data availability and the correctness of the coordinate transformation pipeline.

**Independent Test**: This can be fully tested by executing the data ingestion script on a local machine or CI runner and verifying the existence of a valid HEALPix map file containing exactly the number of events predicted by the energy cut, with no NaN values in the coordinates.

**Acceptance Scenarios**:

1. **Given** the public repositories are accessible, **When** the script downloads the Auger and TA event tables, **Then** the combined dataset contains only events with energy > 50 EeV and valid RA/Dec coordinates.
2. **Given** a combined event list, **When** the script converts coordinates to HEALPix format with Nside=64, **Then** the output map covers the visible sky of the respective detectors without coordinate wrap-around errors or pixel overflow.

---

### User Story 2 - Angular Power Spectrum Computation and Exposure Correction (Priority: P2)

The researcher must be able to compute the angular power spectrum ($C_\ell$) for multipoles $\ell=1$ to $5$ from the HEALPix map, using the detector exposure map to generate an expected isotropic distribution and analyzing the residuals (observed minus expected) to correct for non-uniform sky coverage.

**Why this priority**: This implements the core scientific method. It transforms the raw sky map into the statistical metric ($C_\ell$) required to test the isotropy hypothesis. Correctly modeling the expected distribution is critical to avoid false positives caused by detector geometry.

**Independent Test**: This can be tested by running the computation on a synthetic dataset with a known, injected dipole anisotropy of amplitude 0.01. The system must recover the $C_\ell$ values within a root-mean-square (RMS) relative error of [deferred] compared to the theoretical injection.

**Acceptance Scenarios**:

1. **Given** an exposure-corrected HEALPix map, **When** the script calculates spherical-harmonic coefficients $a_{\ell m}$ from the residuals (Observed - Expected), **Then** the resulting power spectrum $C_\ell$ is computed for $\ell \in [1, 5]$ without numerical instability or division-by-zero errors in low-exposure regions.
2. **Given** the raw event distribution and the detector exposure map, **When** the system generates the Expected Isotropic Map by normalizing the exposure to the total event count, **Then** the residuals reflect the deviation from the exposure pattern as described in arXiv:astro-ph/0507510 ("Anisotropy of the arrival directions of ultra-high-energy cosmic rays").

---

### User Story 3 - Statistical Significance Testing and Multiple-Comparison Correction (Priority: P3)

The researcher must be able to generate a substantial volume of isotropic Monte Carlo simulations, compute their power spectra, and compare the maximum observed $C_\ell$ (across $\ell=1..5$) against the maximum distribution from the null simulations to derive a global p-value, ensuring the false discovery rate is controlled at $\alpha=0.05$.

**Why this priority**: This provides the final scientific conclusion. It determines whether the observed anisotropy is statistically distinguishable from random noise, accounting for the correlation between multipoles via a global test statistic rather than correcting individual p-values.

**Independent Test**: This can be tested by running the pipeline on a purely random isotropic dataset; the system must report that the global p-value is > 0.05 in at least 95% of repeated trials (i.e., the false positive rate is controlled at [deferred]).

**Acceptance Scenarios**:

1. **Given** the observed $C_\ell$ values for $\ell \in [1, 5]$, **When** the script compares the maximum observed value to the distribution of maximum values from 10,000 Monte Carlo null simulations, **Then** it outputs a global empirical p-value.
2. **Given** the global p-value, **When** the system compares it against the significance threshold $\alpha=0.05$, **Then** the system outputs a binary decision indicating whether the null hypothesis of isotropy is rejected.

### Edge Cases

- What happens if the public data repositories are temporarily unavailable or return an empty file? (System must fail gracefully with a clear error message and not proceed to analysis).
- How does the system handle events with missing energy or coordinate data? (System must log and exclude these events prior to HEALPix conversion, reporting the exclusion count).
- What occurs if the Monte Carlo simulation fails to converge or produces a degenerate distribution (e.g., all $C_\ell$ identical)? (System must flag this as a critical failure and halt the pipeline).

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and merge public UHECR event tables from Pierre Auger and Telescope Array repositories, filtering for events with energy $E > 50$ EeV. (See US-1)
- **FR-002**: System MUST convert RA/Dec coordinates to HEALPix format (Nside=64), generate an Expected Isotropic Map based on the combined detector exposure, and compute residuals (Observed - Expected). (See US-2)
- **FR-003**: System MUST compute the angular power spectrum $C_\ell$ for multipoles $\ell = 1$ through $5$ using spherical-harmonic decomposition of the residuals. (See US-2)
- **FR-004**: System MUST generate 10,000 isotropic Monte Carlo event sets matching the real event count and exposure geometry to establish a null distribution of maximum $C_\ell$ values. (See US-3)
- **FR-005**: System MUST calculate a global empirical p-value by comparing the maximum observed $C_\ell$ against the null distribution of maximums, and reject isotropy if $p \le 0.05$. (See US-3)

### Key Entities

- **EventCatalog**: A dataset containing UHECR events with attributes: Energy (EeV), Right Ascension (degrees), Declination (degrees), and Source Detector.
- **ExposureMap**: A HEALPix map representing the relative sky coverage of the detectors, used to generate the expected isotropic distribution.
- **PowerSpectrum**: A data structure containing the computed power $C_\ell$ for each multipole $\ell$ and its associated statistical significance metrics.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The validity of the coordinate transformation is measured against the known sky coverage of the Auger and TA detectors (Reference: Detector documentation and arXiv:astro-ph/0507510).
- **SC-002**: The statistical robustness of the anisotropy detection is measured against the empirical null distribution generated from a large ensemble of isotropic simulations. (Reference: Monte Carlo null distribution).
- **SC-003**: The control of false discoveries is measured against the global p-value derived from the maximum $C_\ell$ statistic to ensure the false discovery rate is controlled at $\alpha=0.05$ (Reference: Statistical theory of global tests).
- **SC-004**: The computational feasibility is measured against the GitHub Actions free-tier constraints (≤ 6 hours runtime, ≤ 7 GB RAM, no GPU) to ensure the pipeline completes end-to-end (Reference: CI runner specifications).

## Assumptions

- The public repositories for Pierre Auger and Telescope Array provide downloadable event tables in a format compatible with standard CSV/ASCII parsing.
- The combined dataset of events with $E > 50$ EeV contains sufficient statistics (approx. 100+ events) to compute a meaningful angular power spectrum up to $\ell=5$, but not higher, due to Poisson noise dominance at higher multipoles.
- The exposure maps provided by the observatories are accurate and sufficient for correcting the non-uniform sky coverage without requiring additional instrumental calibration modeling.
- The analysis assumes an observational study design; therefore, all findings regarding correlations between arrival directions and sky structure are framed as associational, not causal.
- The "free CPU" constraint implies that the 10,000 Monte Carlo simulations will be parallelized across available cores but must complete within the 6-hour job limit.
- The global maximum statistic test is chosen over Benjamini-Hochberg to account for the correlation between adjacent multipoles in the angular power spectrum.