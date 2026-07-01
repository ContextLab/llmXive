# Feature Specification: Assessing the Validity of the Cosmological Principle with Public CMB Data

**Feature Branch**: `001-assess-cosmological-principle`  
**Created**: 2025-01-15  
**Status**: Draft  
**Input**: User description: "Assessing the Validity of the Cosmological Principle with Public CMB Data"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Acquire and preprocess public Planck CMB data (Priority: P1)

As a researcher, I need to download the Planck 2018 SMICA CMB temperature map and apply appropriate masking and resolution reduction so that I can process the data within the compute constraints of the CI environment.

**Why this priority**: This is the foundational data ingestion step without which no analysis can proceed. All downstream computations depend on correctly acquired and preprocessed input data.

**Independent Test**: Can be fully tested by verifying the downloaded map file exists with correct Nside=2048 resolution, applying the Galactic Commander mask, and confirming the downgraded Nside=128 map fits within 7 GB RAM and completes within 60 minutes on CPU.

**Acceptance Scenarios**:

1. **Given** the Planck 2018 SMICA map is available at the ESA archive URL, **When** the download script executes, **Then** the file is saved locally with checksum validation and a size ≤ 14 GB
2. **Given** the full-resolution map is loaded, **When** the Galactic Commander mask is applied, **Then** ≥ 95% of masked pixels are excluded and the remaining unmasked region is ≥ 95% of the sky
3. **Given** the masked map is loaded, **When** it is downgraded to Nside=128, **Then** the resulting array occupies ≤ 100 MB RAM and the downgraded map passes a visual sanity check (no NaN/inf values)

---

### User Story 2 - Compute spherical harmonic decomposition and angular power spectrum (Priority: P1)

As a researcher, I need to compute the spherical harmonic coefficients (a_lm) and derive the angular power spectrum (C_l) for the full sky and split hemispheres so that I can quantify temperature variance as a function of multipole moment.

**Why this priority**: This is the core scientific computation that generates the primary observables (C_l spectra) needed to test isotropy. Without this, no statistical comparison is possible.

**Independent Test**: Can be fully tested by computing C_l from a known isotropic Gaussian random field simulation and verifying the recovered spectrum matches the input power law within numerical precision (relative error ≤ 1% for l ≤ 128).

**Acceptance Scenarios**:

1. **Given** the downgraded and masked CMB map is loaded, **When** healpy's `map2alm` function is called, **Then** the a_lm coefficients are computed for multipoles l ∈ [2, 128] with no NaN/inf values
2. **Given** the a_lm coefficients are computed, **When** the angular power spectrum C_l is calculated, **Then** the output array has length 127 (one value per multipole l=2 to l=128) and all values are positive real numbers
3. **Given** the full-sky C_l is computed, **When** hemispherical splits (North/South and East/West) are analyzed, **Then** each hemisphere produces an independent C_l estimate with ≥ 95% sky coverage after masking

---

### User Story 3 - Generate Monte Carlo null distribution and perform statistical test (Priority: P2)

As a researcher, I need to generate isotropic Gaussian random field simulations and compare observed hemispherical variance against the null distribution so that I can derive a p-value for isotropy rejection at the 95% confidence level.

**Why this priority**: This provides the statistical validation framework that determines whether observed anomalies are significant or consistent with random fluctuations under the Cosmological Principle.

**Independent Test**: Can be fully tested by running the analysis on simulated isotropic data and verifying that the resulting p-value is uniformly distributed (≥ 90% of 100 runs yield p ∈ [0.05, 0.95]) when the null hypothesis is true, AND by injecting anisotropy to verify the method correctly rejects the null (power validation).

**Acceptance Scenarios**:

1. **Given** the observed C_l spectrum is available, **When** Monte Carlo simulations of isotropic Gaussian random fields are generated at Nside=128 using the theoretical ΛCDM power spectrum, **Then** each simulation completes within 30 seconds on CPU and the total runtime is ≤ 60 minutes
2. **Given** the Monte Carlo simulations are complete, **When** hemispherical variance statistics are computed for each, **Then** the null distribution contains a sufficient number of values with no NaN/inf and a finite standard deviation
3. **Given** the null distribution is constructed, **When** the observed variance is compared to it after applying multiple-comparison correction, **Then** a two-tailed p-value is reported with p < 0.05 indicating a statistical anomaly (not a definitive rejection) of isotropy at 95% confidence
4. **Given** anisotropy is injected into a simulation, **When** the analysis is run, **Then** the method correctly identifies the anomaly with p < 0.05 in ≥ 80% of trials (power validation)

---

### User Story 4 - Document reproducibility and sensitivity analysis (Priority: P3)

As a researcher, I need to document all code, parameters, and perform sensitivity analysis on decision thresholds so that the results are reproducible and robust to parameter choices.

**Why this priority**: Reproducibility is essential for scientific validity, and sensitivity analysis ensures that conclusions are not artifacts of arbitrary threshold choices.

**Independent Test**: Can be fully tested by running the analysis pipeline with three different threshold values {2.5σ, 3.0σ, 3.5σ} and verifying that the reported p-value changes are documented, with results in a reproducible repository.

**Acceptance Scenarios**:

1. **Given** the analysis pipeline is complete, **When** all code and parameters are committed to a public repository, **Then** a README documents the exact versions of healpy, numpy, and scipy used
2. **Given** the primary significance threshold is set at 3σ, **When** a sensitivity analysis sweeps the threshold over {2.5σ, 3.0σ, 3.5σ}, **Then** the variation in rejection rates is documented and reported
3. **Given** the hemispherical power asymmetry is measured, **When** multiple comparison correction is applied (Benjamini-Hochberg), **Then** the adjusted p-value is reported alongside the uncorrected value

---

### Edge Cases

- What happens when the Planck archive URL is unavailable or the file checksum fails validation?
- How does the system handle cases where the Galactic mask excludes > 5% of the sky (insufficient data for reliable statistics)?
- What if the Monte Carlo simulations produce a null distribution with extreme outliers (e.g., variance > 5 standard deviations from the mean)?
- How does the system handle numerical instability in spherical harmonic transforms at low multipoles (l < 5)?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download the Planck 2018 SMICA CMB temperature map from the ESA Planck archive at Nside=2048 and validate the file integrity using checksum verification (See US-1)
- **FR-002**: System MUST apply the Commander Galactic mask to exclude foreground-contaminated regions, retaining ≥ 95% of the sky in the unmasked region (See US-1)
- **FR-003**: System MUST downgrade the masked CMB map to Nside=128 to ensure the analysis fits within 7 GB RAM and completes within 60 minutes on CPU-only hardware (See US-1)
- **FR-004**: System MUST compute spherical harmonic coefficients (a_lm) for multipoles l ∈ [2, 128] using the healpy Python library in default CPU precision (See US-2)
- **FR-005**: System MUST calculate the angular power spectrum (C_l) for the full sky and for hemispherical splits (North/South, East/West) independently using a pseudo-C_l estimator (MASTER algorithm) to correct for mode coupling (See US-2)
- **FR-006**: System MUST generate a sufficient number of Monte Carlo simulations of isotropic Gaussian random fields using the theoretical ΛCDM power spectrum (Planck 2018 best-fit) as the source (See US-3)
- **FR-007**: System MUST compute hemispherical variance statistics of the angular power spectrum (C_l) for each simulation to construct a null distribution for hypothesis testing (See US-3)
- **FR-008**: System MUST compare the observed variance to the null distribution and report a two-tailed p-value for a statistical anomaly (not a definitive rejection) at the 95% confidence level (See US-3)
- **FR-009**: System MUST apply the Benjamini-Hochberg multiple-comparison correction when testing >1 hypothesis (e.g., N/S and E/W splits) to control false discovery rate (See US-3)
- **FR-010**: System MUST perform a sensitivity analysis sweeping the significance threshold over {2.5σ, 3.0σ, 3.5σ} and report how the rejection rate varies across the sweep (See US-4)

### Key Entities

- **CMB Temperature Map**: Represents the observed cosmic microwave background temperature field in HEALPix format with Nside resolution parameter and pixel values in µK units
- **Angular Power Spectrum (C_l)**: Represents the variance of temperature fluctuations as a function of multipole moment l, computed from spherical harmonic coefficients
- **Monte Carlo Simulation**: Represents a synthetic isotropic Gaussian random field generated with the theoretical ΛCDM power spectrum for null hypothesis testing
- **Hemispherical Variance**: Represents the power asymmetry statistic computed separately for split sky regions (North/South, East/West)

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Hemispherical power asymmetry is measured against the null distribution generated from multiple isotropic Monte Carlo simulations (See US-3)
- **SC-002**: Statistical significance of anisotropy detection is measured against the 95% confidence threshold (p < 0.05) with Benjamini-Hochberg correction applied (See US-3)
- **SC-003**: Reproducibility is measured against the documented code repository and parameter set, with all versions pinned and accessible (See US-4)
- **SC-004**: Sensitivity to threshold choice is measured by sweeping the significance cutoff over {2.5σ, 3.0σ, 3.5σ} and quantifying the variation in rejection rates (See US-4)
- **SC-005**: Computational feasibility is measured against the CI constraints: ≤ 7 GB RAM, ≤ 14 GB disk, ≤ 60 minutes runtime on 2 CPU cores with no GPU (See US-1)

## Assumptions

- The Planck 2018 SMICA CMB map is available at the ESA Planck archive URL and remains publicly accessible throughout the project lifecycle
- The Commander Galactic mask adequately excludes foreground-contaminated regions, with ≥ 95% of the sky remaining unmasked after application
- The dataset-variable fit is valid: the Planck 2018 SMICA map contains the temperature measurements required to compute hemispherical variance statistics (no missing variables)
- The analysis is observational (no random assignment); therefore, findings must be framed as ASSOCIATIONAL, not causal, per the inference framing requirement
- The Nside=128 downgrade preserves sufficient angular resolution (≈ 57 arcminutes) to test large-scale isotropy at low multipoles (l ≤ 128)
- A sufficient number of Monte Carlo simulations provide adequate statistical power for p-value estimation.; if power limitations arise, this will be documented as a constraint
- The spherical harmonic transform using healpy on CPU with default precision is numerically stable for l ≤ 128
- The 2.5σ–3.5σ threshold sweep is justified by the look-elsewhere effect and the need to validate robustness against the chosen significance threshold; sensitivity analysis will be documented in the final report
- No GPU/CUDA accelerators are available; all computations must complete on CPU-only hardware within the designated CI job limit
- The analysis assumes the CMB temperature field follows a Gaussian random field under the null hypothesis (isotropic Cosmological Principle)
- The theoretical ΛCDM power spectrum (Planck 2018 best-fit) is a valid and independent source for generating the null distribution, avoiding circular validation with observed anomalies
- The MASTER algorithm is used to correct for mode coupling in partial-sky power spectrum estimation