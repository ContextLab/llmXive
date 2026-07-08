# Feature Specification: Statistical Analysis of Early Universe CMB Fluctuations and Topological Defects

**Feature Branch**: `001-cmb-defect-analysis`  
**Created**: 2025-01-15  
**Status**: Draft  
**Input**: User description: "Statistical Analysis of Early Universe CMB Fluctuations and Topological Defects"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1)

As a researcher, I need to download and preprocess the Planck 2015/2018 SMICA CMB temperature maps with appropriate masking so that I have clean input data for statistical analysis.

**Why this priority**: This is the foundational data pipeline without which no analysis can proceed. It delivers immediate value by establishing reproducible data access.

**Independent Test**: Can be fully tested by downloading a single Planck map, applying the Galactic mask, and verifying pixel counts and coverage.

**Acceptance Scenarios**:

1. **Given** access to the Planck Legacy Archive, **When** the pipeline requests the SMICA temperature map at Nside=128, **Then** the file downloads successfully and validates against expected checksums
2. **Given** a downloaded CMB map, **When** the Galactic mask is applied, **Then** ≥95% sky coverage is preserved and the masked map contains ≥2.5 million valid pixels
3. **Given** the masked map, **When** basic statistics are computed, **Then** mean temperature and standard deviation are within physically plausible ranges

---

### User Story 2 - Minkowski Functional Computation (Priority: P2)

As a researcher, I need to compute all three Minkowski Functionals (area, perimeter, genus) on the masked CMB map so that I can quantify non-Gaussian topological signatures.

**Why this priority**: This is the core analytical capability that addresses the research question. Without Minkowski Functional computation, the project cannot measure defect signatures.

**Independent Test**: Can be tested by computing Minkowski Functionals on a single masked map and verifying the three functional values are returned with physically consistent ranges.

**Acceptance Scenarios**:

1. **Given** a masked CMB map with ≥2.5 million valid pixels, **When** Minkowski Functional computation is executed using a custom implementation or pyMinkowski library with mask-corrected estimators, **Then** all three functionals (area, perimeter, genus) are returned at thresholds {±0.5σ, ±1σ, 0σ} with numerical precision ≥6 decimal places
2. **Given** the computed functionals, **When** the computation is repeated on the same input, **Then** results are reproducible within ±0.001% numerical tolerance

---

### User Story 3 - Gaussian Simulation and Statistical Comparison (Priority: P3)

As a researcher, I need to generate [deferred] Gaussian random field realizations (including beam smoothing and instrumental noise) based on the theoretical LCDM power spectrum and perform a multivariate statistical comparison of observed Minkowski Functionals against the Gaussian null hypothesis so that I can assess statistical significance of any deviations and constrain cosmic string tension.

**Why this priority**: This provides the statistical validation framework. While essential for interpretation, it depends on User Stories 1 and 2 being functional.

**Independent Test**: Can be tested by generating 1,000 Gaussian simulations to verify the pipeline method; the production requirement is 1,000 simulations for statistical power.

**Acceptance Scenarios**:

1. **Given** the theoretical LCDM power spectrum (Planck 2018 TT, TE, EE), **When** [deferred] Gaussian random field realizations are generated using `healpy` with beam smoothing (FWHM = 5.0 arcmin) and noise (σ² = 1.1 μK²), **Then** the simulated maps preserve the input power spectrum within ≤2% RMS deviation across multipoles ℓ=2 to ℓ=200
2. **Given** observed and simulated Minkowski Functional distributions, **When** a likelihood ratio test comparing a Gaussian + Cosmic String model against the pure Gaussian model is performed, **Then** p-values and Gμ upper bounds are computed and stored with ≥6 decimal precision in JSON format
3. **Given** the covariance structure of the three Minkowski Functionals, **When** statistical significance is assessed, **Then** the joint test accounts for correlation between functionals via the sample covariance matrix to maintain α ≤ 0.05 overall

---

### Edge Cases

- **What happens when the Planck Legacy Archive is temporarily unavailable?** The system retries download up to 3 times with exponential backoff (1s, 2s, 4s) before failing gracefully with an error message.
- **How does the system handle corrupted mask files?** If mask file integrity check fails (checksum mismatch), the system aborts with a clear error and does not proceed with analysis.
- **What happens when memory usage approaches the 7GB limit?** The system monitors RAM usage and if it exceeds 6.5GB, it MUST abort the pipeline with a "Resource Limit Exceeded" error and halt downstream analysis to preserve statistical validity.
- **How does the system handle edge effects near the Galactic mask boundary?** Minkowski Functional computation uses a 2-pixel buffer zone around mask edges and applies Monte Carlo mask-corrected estimators to account for the mask's own topology.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download the Planck 2015/2018 SMICA CMB temperature map at Nside=128 resolution from the Planck Legacy Archive and validate file integrity via checksum comparison (See US-1)
- **FR-002**: System MUST apply a Galactic mask that preserves ≥95% sky coverage and produces a masked map containing ≥2.5 million valid pixels (See US-1)
- **FR-003**: System MUST compute all three Minkowski Functionals (area, perimeter, genus) on the masked CMB map using a custom implementation or pyMinkowski library with mask-corrected estimators at thresholds {±0.5σ, ±1σ, 0σ} with numerical precision ≥6 decimal places (See US-2)
- **FR-004**: System MUST generate [deferred] Gaussian random field realizations matching the theoretical LCDM power spectrum (Planck 2018 TT, TE, EE), including beam smoothing (FWHM = 5.0 arcmin) and instrumental noise (σ² = 1.1 μK²), for null hypothesis comparison (See US-3)
- **FR-005**: System MUST perform a likelihood ratio test comparing observed Minkowski Functional distributions against a Gaussian + Cosmic String template model, accounting for covariance between functionals via sample covariance matrix, with p-values and Gμ upper bounds computed to ≥6 decimal precision and output in JSON format (See US-3)
- **FR-006**: System MUST compute the sample covariance matrix of the three Minkowski Functionals across N simulations (where N=1,000) to enable the multivariate test (See US-3)
- **FR-007**: System MUST complete the full analysis pipeline (download, mask, compute, simulate, test) for Nside=128 and N=1,000 simulations within ≤6 hours on GitHub Actions free-tier runners (2 CPU, 7GB RAM) (See US-1, US-2, US-3)

### Key Entities

- **CMB Map**: Represents the Planck SMICA temperature anisotropy map; key attributes include Nside resolution, pixel count, and masked pixel count
- **Minkowski Functionals**: Represents the three topological statistics (area, perimeter, genus) computed on the CMB map; key attributes include functional values and threshold levels
- **Gaussian Realization**: Represents a single simulated CMB map generated from the theoretical LCDM power spectrum with beam and noise; key attributes include simulation ID and power spectrum fidelity
- **Statistical Test Result**: Represents the output of the likelihood ratio test; key attributes include p-value, Gμ upper bound, and degrees of freedom

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Data pipeline reliability is measured by the percentage of successful downloads and checksum validations within 3 retries (Target: ≥99%) (See US-1)
- **SC-002**: Minkowski Functional computation accuracy is measured by the RMS deviation of computed functionals from the theoretical genus curve for a Gaussian field with the Planck 2015 power spectrum (Target: ≤1% RMS deviation) (See US-2)
- **SC-003**: Statistical comparison output is measured by the system's ability to produce a p-value for the likelihood ratio test and a derived upper bound on the cosmic string tension Gμ with 95% confidence intervals via template matching (See US-3)
- **SC-004**: Compute resource adherence is measured against the GitHub Actions free-tier specification (2 CPU, 7GB RAM, ≤6h) for Nside=128 and N=1,000 simulations (See US-1, US-2, US-3)

---

## Assumptions

- The Planck 2015/2018 SMICA CMB temperature maps at Nside=128 contain sufficient information to constrain non-Gaussian signatures consistent with topological defects.
- The Galactic mask provided by the Planck Legacy Archive removes foreground contamination while preserving ≥95% of the cosmological signal.
- Minkowski Functionals computed on temperature anisotropies are sensitive to the non-Gaussian signatures predicted by cosmic string and domain wall models.
- The analysis is observational (no random assignment); therefore all findings regarding defect constraints must be framed as ASSOCIATIONAL rather than causal.
- A sample size of 1,000 Gaussian simulations follows standard practice in cosmological simulation studies (N=500-2,000) to achieve adequate statistical power for null hypothesis testing of CMB statistics.
- Family-wise error correction is not required for the likelihood ratio test as it inherently accounts for the correlation between the three Minkowski Functionals via the covariance matrix.
- The theoretical LCDM power spectrum data required to generate Gaussian realizations is available and compatible with the `healpy` library version used in the analysis.
- All statistical instruments (likelihood ratio test, Minkowski Functional computation) are validated methods with citable validation in the cosmological literature.
- The Planck SMICA map at Nside=128 resolution is sufficient to resolve topological scales > 2 arcminutes. According to Planck 2015 constraints, cosmic strings with tension Gμ ≤ 10⁻⁷ produce non-Gaussian signatures at angular scales corresponding to Nside ≥ 64. The Nside=128 resolution (pixel size ~2.9 arcmin) preserves the relevant topological scales for constraint analysis while maintaining computational feasibility. See Planck 2015 results XXIV: Constraints on primordial non-Gaussianity.
- The Gaussian simulations explicitly model beam smoothing and instrumental noise characteristics in addition to power spectrum matching. Planck 2015 analysis requires convolution with the Planck beam transfer function (FWHM ≈ 5 arcmin for 143 GHz channel) and addition of Gaussian noise with variance σ² = 1.1 μK² to match the SMICA map properties. These covariates are essential for producing realistic null hypothesis realizations that account for observational effects. See: Planck 2015 results I: Overview and the Planck mission, Section 4.3 on beam and noise modeling.