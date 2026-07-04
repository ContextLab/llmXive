# Feature Specification: Testing Lorentz Violation with Publicly Available CMB Data

**Feature Branch**: `001-testing-lorentz-violation`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Do publicly available CMB temperature and polarization maps exhibit directional anomalies—such as power‑spectrum asymmetries or non‑Gaussian signatures—that would be consistent with a violation of Lorentz invariance?"

## User Scenarios & Testing

### User Story 1 - Data Acquisition and Pre-processing Pipeline (Priority: P1)

The system MUST download Planck 2018 PR3 temperature (SMICA) and polarization (EE, TE) maps, apply confidence masks, and deconvolve beam/pixel window functions to produce a clean, analysis-ready dataset.

**Why this priority**: Without valid, pre-processed input data, no statistical analysis or model comparison can occur. This is the foundational dependency for all subsequent scientific calculations.

**Independent Test**: This can be fully tested by executing the data ingestion script and verifying that the output files (masked, deconvolved maps) exist, have the correct `healpix` resolution (Nside=2048), and contain no NaN values within the masked region.

**Acceptance Scenarios**:

1. **Given** the ESA Legacy Archive is accessible, **When** the system requests the SMICA, EE, and TE maps, **Then** the system downloads the files and saves them to the local workspace with checksums verified.
2. **Given** the raw maps and confidence masks, **When** the system applies the masks and deconvolves the beam functions, **Then** the output maps have zero values in masked regions and the beam transfer function is correctly applied to the power spectra.
3. **Given** a corrupted or incomplete download, **When** the system attempts to process the file, **Then** the system halts and reports a specific error code indicating file integrity failure.

---

### User Story 2 - Anisotropy Diagnostics and Power Spectrum Estimation (Priority: P2)

The system MUST compute angular power spectra (TT, EE, TE) and perform dipole-modulation and Bipolar Spherical Harmonic (BipoSH) analyses to quantify hemispherical power asymmetry and directional dependence.

**Why this priority**: This constitutes the core scientific engine of the project. It transforms raw data into the specific metrics (asymmetry, BipoSH coefficients) required to test the Lorentz-violation hypothesis.

**Independent Test**: This can be tested by running the diagnostics on a set of known isotropic Gaussian simulations (returning p-value > 0.05) AND on a set of simulations with a known injected Lorentz-violating signal (recovering the injected SME coefficient within 95% credible interval) to validate both false-positive control and sensitivity.

**Acceptance Scenarios**:

1. **Given** the pre-processed CMB maps, **When** the system computes the angular power spectra using `healpy.anafast` over multipoles ℓ = 2–2000, **Then** the resulting TT, EE, and TE spectra match the Planck Legacy Release Table 5 reference values within a 1% tolerance.
2. **Given** the masked maps, **When** the system calculates the dipole modulation amplitude and phase, **Then** the output includes a statistical significance (sigma) value and a p-value derived from the null distribution.
3. **Given** the global limits defined in SC-004 and SC-005, **When** the system runs the BipoSH coefficient calculation on the standard ubuntu-latest GitHub Actions runner, **Then** it completes within 6 hours without exceeding 7 GB of RAM.

---

### User Story 3 - Model Comparison and Statistical Inference (Priority: P3)

The system MUST perform a likelihood-ratio test comparing the isotropic ΛCDM model against a Lorentz-violating anisotropic model, utilizing MCMC sampling to derive posterior constraints on SME coefficients.

**Why this priority**: This is the final interpretive step that answers the research question. It synthesizes the diagnostics into a formal statistical conclusion (null result vs. detection) with quantified uncertainty.

**Independent Test**: This can be tested by running the MCMC sampler on a synthetic dataset where the true SME coefficient is known to be zero; the system must recover a posterior distribution centered at zero with the correct credible interval width.

**Acceptance Scenarios**:

1. **Given** the anisotropy diagnostics and isotropic simulations, **When** the system runs the MCMC chain (≤ 10,000 samples), **Then** it outputs the posterior distribution for the SME coefficient \(k_{(V)00}^{(5)}\) and the likelihood-ratio statistic.
2. **Given** a 95% confidence threshold, **When** the system calculates the corrected p-value from the simulation-based null distribution, **Then** it correctly classifies the result as "consistent with isotropy" or "anomalous" based on whether the corrected p-value is < 0.05, AND reports the continuous sigma value for nuance.
3. **Given** the computational constraints, **When** the MCMC chain fails to converge within the time limit, **Then** the system reports the convergence status and provides the best-effort posterior constraints with a warning flag.

---

### Edge Cases

- What happens when the Planck archive is temporarily unreachable or the specific map files are missing? (System must retry a limited number of times with exponential backoff, then fail gracefully with a clear error message).
- How does the system handle non-Gaussian noise artifacts in the masked regions that might mimic anisotropy? (System must apply a secondary non-Gaussianity check using Minkowski functionals to flag potential false positives).
- How does the system behave if the MCMC chain exhibits poor mixing or gets stuck in a local mode? (System must detect low effective sample size (ESS < 200) and output a warning, providing the trace plot for manual review).

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and verify the integrity of Planck 2018 PR3 SMICA, EE, and TE maps and corresponding masks from the ESA Legacy Archive (See US-1).
- **FR-002**: System MUST apply confidence masks and deconvolve beam/pixel window functions using `healpy` utilities to produce analysis-ready maps (See US-1).
- **FR-003**: System MUST compute angular power spectra (TT, EE, TE) and generate isotropic ΛCDM simulations to establish a null distribution, completing the simulation phase within the global runtime limit (See US-2).
- **FR-004**: System MUST implement the Hanson & Lewis estimator for dipole modulation and calculate Bipolar Spherical Harmonic (BipoSH) coefficients to quantify directional dependence (See US-2).
- **FR-005**: System MUST perform a likelihood-ratio test and MCMC sampling (≤ 10,000 samples) to constrain the SME coefficient \(k_{(V)00}^{(5)}\), utilizing the forward-model defined in FR-008 for likelihood generation (See US-3).
- **FR-006**: System MUST explicitly frame all findings as associational and report p-values derived from Monte-Carlo simulations, avoiding causal claims for observational data (See US-3).
- **FR-007**: System MUST apply a multiple-comparison correction (e.g., Bonferroni or False Discovery Rate) when evaluating >1 hypothesis test to control family-wise error (See US-3).
- **FR-008**: System MUST implement a forward-model simulation that injects specific SME parameters into CMB maps to generate the likelihood function required for FR-005, establishing the physical mapping between SME coefficients and BipoSH coefficients (See US-3).

### Key Entities

- **CMBMap**: Represents a processed temperature or polarization map; attributes include Nside resolution, pixel mask, and beam transfer function.
- **PowerSpectrum**: Represents the angular power spectrum data; attributes include multipole moment (l), power (Cl), and variance (Cll).
- **AnisotropyMetric**: Represents a diagnostic result; attributes include type (dipole/BipoSH), amplitude, phase, and statistical significance (sigma).
- **SMEConstraint**: Represents the final statistical inference; attributes include coefficient name, posterior mean, 95% credible interval, and likelihood-ratio statistic.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The likelihood-ratio statistic between the isotropic and Lorentz-violating models is measured against the null distribution generated from isotropic simulations (See FR-005, FR-006).
- **SC-002**: The effective sample size (ESS) of the MCMC chain is measured against a predefined threshold to ensure adequate convergence. to ensure convergence and reliable posterior estimation (See FR-005).
- **SC-003**: The false-positive rate of the anisotropy detection is measured against the nominal significance level (α = 0.05) after applying multiple-comparison correction (See FR-007).
- **SC-004**: The total runtime of the end-to-end analysis is measured against the standard time limit of the ubuntu-latest GitHub Actions runner. (See FR-004, FR-005).
- **SC-005**: The memory usage peak is measured against the RAM limit of the standard ubuntu-latest GitHub Actions runner, OR successful degradation via sub-sampling if the limit is exceeded (See FR-004, FR-005).

## Assumptions

- The Planck 2018 PR3 data products (SMICA maps, masks, beam functions) are publicly available and accessible via the ESA Legacy Archive without authentication barriers.
- The `healpy`, `numpy`, `scipy`, and `emcee` libraries are compatible with the Python 3.9+ environment and can be installed within the GitHub Actions runner constraints.
- The dataset size (full-resolution Planck maps) fits within the GB RAM limit after masking and sub-sampling if necessary; if not, the analysis will proceed on a subset of multipoles (ℓ < 2000) as a CPU-tractable approximation.
- The SME coefficient \(k_{(V)00}^{(5)}\) is the primary parameter of interest for the photon sector Lorentz violation; other coefficients are out of scope for this specific iteration.
- The isotropic ΛCDM simulations generated for the null hypothesis MUST include realistic Planck noise properties and beam asymmetries to accurately represent the null distribution.
- The analysis does not require GPU acceleration; all computations (MCMC, power spectrum estimation) are performed using standard CPU-based floating-point arithmetic.
- A default target of a sufficient number of simulations is used for the null distribution generation unless a power analysis justifies a different count during implementation.
- The The performance target for the BipoSH calculation is a feasible duration on a multi-core CPU., which is a subset of the global -hour limit defined in SC-004.