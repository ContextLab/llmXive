# Feature Specification: Reconstructing Early Universe Phase Transitions from CMB B-Mode Polarization

**Feature Branch**: `001-reconstructing-early-universe-phase-transitions`  
**Created**: 2026-06-26  
**Status**: Draft  
**Input**: User description: "Do causal, non-inflationary phase transitions in the early universe produce distinct, detectable signatures in CMB B-mode polarization that can be statistically distinguished from inflationary gravitational wave signals using existing Planck and BICEP/Keck data?"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1)

As a cosmologist, I want to download, mask, and prepare Planck 2015 and BICEP/Keck B-mode polarization maps so that I can compute clean angular power spectra free from Galactic foreground contamination.

**Why this priority**: Without clean, preprocessed data, no subsequent analysis (fitting, model comparison) is possible. This is the foundational step that enables all downstream scientific inquiry.

**Independent Test**: The pipeline can be fully tested by running it on a subset of the sky (e.g., a single HEALPix patch) and verifying that the output power spectrum matches known theoretical expectations for lens-only B-modes in that region.

**Acceptance Scenarios**:

1. **Given** the Planck 2015 SMICA B-mode maps and BICEP/Keck 2018 power spectra are available via public URLs, **When** the pipeline executes the download and masking steps, **Then** the output consists of masked maps covering at least 70% of the sky with Galactic foregrounds removed.
2. **Given** a masked B-mode map, **When** the angular power spectrum is computed using pyHEALPix, **Then** the resulting $C_\ell^{BB}$ spectrum for $\ell > 100$ matches the expected lensing-dominated shape within 5% statistical uncertainty.

---

### User Story 2 - Theoretical Model Generation and Fitting (Priority: P2)

As a researcher, I want to generate theoretical B-mode power spectra for inflationary, phase transition, and null models, and fit them to observed data using MCMC so that I can estimate posterior distributions for key parameters like the tensor-to-scalar ratio $r$ and phase transition energy scale.

**Why this priority**: This step directly addresses the research question by quantifying how well each physical model explains the observed data. It is the core analytical engine of the project.

**Independent Test**: The fitting routine can be tested independently by generating synthetic data from a known model (e.g., $r=0.01$ inflation) and verifying that the MCMC sampler recovers the input parameters within 1$\sigma$ confidence intervals.

**Acceptance Scenarios**:

1. **Given** a set of observed $C_\ell^{BB}$ data points with covariance matrices, **When** The MCMC sampler (emcee) runs for a sufficient number of steps on a CPU., **Then** the posterior distribution for the tensor-to-scalar ratio $r$ is centered within 10% of the true value used to generate synthetic test data.
2. **Given** three competing models (inflation, phase transition, null), **When** the $\chi^2$ minimization is performed, **Then** the best-fit model has a statistically acceptable fit to the data.

---

### User Story 3 - Model Comparison and Statistical Validation (Priority: P3)

As a scientist, I want to compute Bayes factors and perform null tests using independent sky patches so that I can rigorously distinguish between phase transition and inflationary signals and validate the robustness of my findings.

**Why this priority**: While fitting provides parameter estimates, model comparison determines which physical scenario is most favored by the data. Null tests ensure the results are not artifacts of systematic errors or specific sky regions.

**Independent Test**: The validation suite can be tested by splitting synthetic data into two halves, running the full analysis on each, and verifying that the Bayes factors and parameter estimates are consistent within statistical fluctuations.

**Acceptance Scenarios**:

1. **Given** posterior samples for the inflation and phase transition models, **When** the Savage-Dickey density ratio is computed, **Then** the Bayes factor $K$ is reported with a precision of at least 2 decimal places, allowing a clear decision (e.g., $K > 10$ for strong evidence).
2. **Given** the full-sky data split into two independent patches (e.g., Northern and Southern hemispheres), **When** the analysis is run separately on each, **Then** the difference in best-fit $r$ values between patches is negligible, indicating consistency.

---

### Edge Cases

- What happens if the Planck 2015 data release URL is unavailable or the file is corrupted? The system must retry the download up to 3 times with exponential backoff, then fail gracefully with a clear error message indicating the missing dataset.
- How does the system handle a case where the MCMC sampler fails to converge (e.g., autocorrelation time exceeds the sample limit)? The system must detect non-convergence, log a warning, and either extend the chain or report a "convergence failed" status rather than returning unreliable parameter estimates.
- What if the phase transition model parameters (e.g., energy scale) push the theoretical spectrum into a regime where the approximation breaks down (e.g., $\ell < 2$)? The system must clamp the model prediction to the valid range and flag any extrapolated points in the diagnostic plots.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download Planck 2015 SMICA B-mode maps and BICEP/Keck 2018 power spectra from their respective public repositories and store them locally with checksums for integrity verification (See US-1).
- **FR-002**: System MUST apply the Planck 2015 Common Mask to all B-mode maps to remove Galactic foregrounds and ensure consistent sky coverage across datasets (See US-1).
- **FR-003**: System MUST compute angular power spectra $C_\ell^{BB}$ from masked maps using the pyHEALPix library in CPU-only mode, covering a range of low to intermediate multipoles. (See US-1).
- **FR-004**: System MUST generate theoretical B-mode power spectra as a grid across the following parameter ranges: (a) inflation with $r$ spanning a broad range of theoretically motivated values, (b) causality-limited phase transition with energy scale $E_{\text{PT}}$ in the grand unification regime, and (c) null (lens-only) (See US-2).
- **FR-005**: System MUST perform $\chi^2$ minimization and MCMC sampling (emcee, a sufficient number of steps) to estimate posterior distributions for $r$ and phase transition energy scale (See US-2).
- **FR-006**: System MUST compute Bayes factors using thermodynamic integration to compare phase transition vs. inflation vs. null hypotheses (See US-3).
- **FR-007**: System MUST split the sky into at least two independent patches and verify consistency of signal detection across them by ensuring the absolute difference in best-fit $r$ values is negligible (See US-3).

### Key Entities

- **B-mode Map**: Represents the observed CMB B-mode polarization on the celestial sphere, characterized by HEALPix resolution parameter $N_{\text{side}}$ and a sky mask.
- **Power Spectrum**: A sequence of angular power values $C_\ell^{BB}$ indexed by multipole $\ell$, representing the variance of B-mode fluctuations at different angular scales.
- **Theoretical Model**: A parametric description of B-mode power spectra, defined by physical parameters such as $r$ (tensor-to-scalar ratio) or energy scale $E_{\text{PT}}$ (phase transition energy).
- **Posterior Distribution**: A probability distribution over model parameters derived from MCMC sampling, representing the updated belief after observing the data.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The percentage of sky retained after masking is measured against the target of [deferred] defined by the Planck 2015 Common Mask (See US-1).
- **SC-002**: The Bayes factor $K$ between the phase transition and inflation models is measured against the decision threshold $K > 10$ for strong evidence, with specific focus on the low-$\ell$ regime ($\ell < 100$) where models diverge (See US-2).
- **SC-003**: The Bayes factor $K$ between the phase transition and inflation models is measured against the decision threshold $K > 10$ for strong evidence (See US-3).
- **SC-004**: The consistency of best-fit $r$ values across independent sky patches is measured against an absolute tolerance of 0.005 (See US-3).
- **SC-005**: The coverage of the standard credible intervals for $r$ is measured against the true value in synthetic data tests (See US-2).

## Assumptions

- The Planck 2015 SMICA B-mode maps and BICEP/Keck 2018 power spectra are publicly available and accessible via the provided URLs without authentication.
- The pyHEALPix and emcee libraries are compatible with CPU-only execution and can run within the time limit of the GitHub Actions free-tier runner.
- The causality-limited phase transition model is theoretically well-defined and computable across the energy scale range $[10^{14}, 10^{16}]$ GeV without requiring GPU-accelerated computation.
- The Planck 2015 Common Mask is sufficient to remove Galactic foreground contamination for the purpose of this analysis, and no additional foreground cleaning is required.
- The sample size (full-sky CMB data) provides sufficient statistical power to distinguish between inflationary and phase transition models at a statistically significant confidence level, assuming such a distinction exists in the data.
- Thermodynamic integration is an appropriate method for computing Bayes factors in this context, given the non-nested nature of the models being compared, and the CPU-only constraint is sufficient for the defined parameter grid.