# Feature Specification: Exploring the Statistical Significance of Fine‑Structure Constant Variations

**Feature Branch**: `001-fine-structure-constant-variations`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Exploring the Statistical Significance of Fine‑Structure Constant Variations"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Reproducible Data Ingestion and Preprocessing Pipeline (Priority: P1)

As a researcher, I want to automatically download publicly available quasar absorption-line spectra (e.g., from ESO UVES) and extract metal-absorption line lists (Fe II, Mg II, Si IV) with their measured wavelengths, so that I have a clean, standardized dataset ready for statistical analysis without manual data wrangling.

**Why this priority**: Without reliable data ingestion and line extraction, no subsequent statistical modeling or hypothesis testing is possible. This is the foundational step that enables the entire research workflow.

**Independent Test**: Can be fully tested by running the data pipeline script against a small subset of public spectra and verifying that the output CSV contains correctly identified absorption lines with wavelengths within expected error margins compared to manual inspection.

**Acceptance Scenarios**:

1. **Given** a list of quasar IDs from the ESO archive, **When** the pipeline executes, **Then** it downloads the corresponding FITS files and extracts at least 95% of known strong absorption lines (Fe II, Mg II) with wavelengths matching catalog values within 0.05 Å.
2. **Given** a corrupted or incomplete FITS file, **When** the pipeline attempts processing, **Then** it logs the error, skips the file, and continues processing remaining files without crashing.
3. **Given** a spectrum with low signal-to-noise ratio, **When** the pipeline runs, **Then** it flags lines with S/N < 5 for potential exclusion in downstream analysis.

---

### User Story 2 - Hierarchical Bayesian Inference for Δα/α Estimation (Priority: P2)

As a physicist, I want to run a hierarchical Bayesian model that estimates the fractional change in the fine-structure constant (Δα/α) for each absorber while accounting for systematic errors (wavelength calibration drift, intra-order distortions) as nuisance parameters, so that I obtain robust posterior distributions for potential variations.

**Why this priority**: This is the core scientific analysis that directly addresses the research question. It transforms raw measurements into statistically meaningful estimates of α variation while properly propagating uncertainties.

**Independent Test**: Can be fully tested by running the PyMC model on simulated data with known Δα/α values and systematic errors, then verifying that the posterior distributions correctly recover the injected parameters within 95% credible intervals. To validate frequentist coverage, the test MUST run 10+ independent seeds with 4 chains each (2000 warmup, 4000 draws) and confirm that the 95% CI contains the true value in ≥95% of the 10+ runs.

**Acceptance Scenarios**:

1. **Given** a dataset of 50 absorbers with injected systematic errors, **When** the hierarchical model runs with 4 chains (2000 warmup, 4000 draws each), **Then** the posterior mean for Δα/α is within 0.1σ of the true injected value for at least 90% of absorbers.
2. **Given** a null hypothesis scenario (no true variation), **When** the model is applied, **Then** the 95% credible interval for the global trend parameter includes zero in at least 95% of repeated simulations (verified via the 10+ seed coverage test).
3. **Given** varying prior widths on systematic error parameters, **When** the model is re-run, **Then** the posterior estimates for Δα/α remain stable (change < 0.05σ) across the sensitivity sweep.

---

### User Story 3 - Model Comparison and Spatial/Temporal Trend Validation (Priority: P3)

As a researcher, I want to compute Bayes factors comparing null models (no variation) against alternative models (spatial dipole, temporal trend) and correlate Δα/α estimates with large-scale structure data, so that I can quantify the evidence for new physics and assess potential spatial alignments.

**Why this priority**: This provides the final interpretive layer that determines whether observed variations are statistically significant and physically meaningful, completing the scientific inquiry.

**Independent Test**: Can be fully tested by running the model comparison on synthetic datasets with known ground truth (null vs. dipole) and verifying that Bayes factors correctly favor the true model in >90% of cases.

**Acceptance Scenarios**:

1. **Given** a dataset where a true dipole pattern exists, **When** Bayes factors are computed between null and dipole models, **Then** the dipole model is favored with ln(BF) > 5 in at least 85% of simulation trials.
2. **Given** Δα/α posterior estimates and celestial coordinates (RA, Dec), **When** a spatial dipole fit is computed, **Then** the dipole amplitude and direction are reported with 95% credible intervals.
3. **Given** a sensitivity analysis where prior widths are varied by ±20%, **When** model comparison is re-run, **Then** the qualitative conclusion (null vs. alternative favored) remains unchanged in at least 90% of cases.

---

### Edge Cases

- What happens when the ESO archive is temporarily unavailable or returns rate-limited responses?
- How does the system handle spectra with overlapping absorption lines from multiple redshifts?
- What occurs if the NIST database lacks laboratory reference frequencies for a detected transition?
- How are outliers in Δα/α estimates (e.g., >5σ from mean) handled in the hierarchical model?
- What happens if the NUTS sampler fails to converge (R-hat > 1.01) for certain chains?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download UVES quasar spectra from the ESO Science Archive and parse FITS headers to extract observation metadata (redshift, exposure time, instrument setup) (See US-1)
- **FR-002**: System MUST identify and extract absorption line wavelengths for at least 5 common metal species (Fe II, Mg II, Si IV, C IV, Al III) using `specutils` with automated line-list matching (See US-1)
- **FR-003**: System MUST implement a hierarchical Bayesian model in PyMC v5 with Level 1 (individual absorbers) and Level 2 (global trend/dipole) structure, including nuisance parameters for systematic errors (See US-2)
- **FR-004**: System MUST derive wavelength-calibration drift and intra-order distortion parameters from per-spectrum calibration residuals (ThAr lamp lines or laser frequency comb data) found in FITS headers or linked logs. If such data is unavailable, the system MUST model these as a hyper-parameter with a broad Half-Cauchy prior (scale=0.1 Å) rather than a fixed constant (See US-2)
- **FR-005**: System MUST compute Bayes factors between null and alternative models using bridge sampling, with ln(BF) > 3 considered moderate evidence and ln(BF) > 5 strong evidence (See US-3)
- **FR-006**: System MUST fit a spatial dipole model (Δα/α = A cos(θ) + B) to the celestial coordinates (RA, Dec) of the absorbers. "Sightline groups" are defined as spatial clusters of absorbers within 10 degrees angular separation or redshift bins of Δz < 0.1. The system MUST apply Bonferroni correction if the number of such defined groups exceeds a threshold to control the family-wise error rate (See US-3)
- **FR-007**: System MUST run NUTS sampling with a minimum of 4 chains, 2000 warmup steps, and 4000 posterior draws per chain for production runs. The system MUST use the `arviz.rhat` function with a standard convergence threshold to verify convergence, and report the maximum R-hat value in the output log (See US-2)
- **FR-008**: System MUST generate corner plots and summary tables using `arviz` showing posterior distributions for Δα/α, trend slope, and dipole amplitude (See US-3)

### Key Entities *(include if feature involves data)*

- **Absorber**: Represents a single quasar absorption system with attributes: redshift, measured wavelengths for each transition, signal-to-noise ratio, and associated systematic error estimates.
- **Δα/α Estimate**: The fractional change in the fine-structure constant for an absorber, represented as a posterior distribution with mean, standard deviation, and 95% credible interval.
- **Global Trend Model**: Represents the redshift-dependent variation hypothesis with parameters: slope (temporal trend), dipole amplitude, and intrinsic scatter.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Posterior recovery accuracy is measured against simulated datasets with known ground-truth Δα/α values, where 95% credible intervals should contain the true value in ≥95% of cases (See US-2)
- **SC-002**: Model comparison performance is measured against synthetic data with known null/alternative ground truth, where Bayes factors should correctly identify the true model in ≥90% of trials (See US-3)
- **SC-003**: Computational efficiency is measured against the GitHub Actions free-tier constraint (a limited number of CPU cores, 7 GB RAM, 6-hour limit). For the benchmark dataset (20 simulated absorbers), the full analysis (4 chains, 2000 warmup, 4000 draws) MUST complete within 4 hours with ≤5 GB memory usage. For production runs (≥30 absorbers), the system MUST complete before resource exhaustion (memory > 7 GB or time > 6 hours) (See US-2)
- **SC-004**: Systematic error propagation is measured by comparing the posterior variance of Δα/α in the 'with-systematics' model against the 'without-systematics' model. Success is defined as the variance in the 'with-systematics' model being greater than or equal to the variance in the 'without-systematics' model (monotonicity check), ensuring systematics are not ignored (See US-2)
- **SC-005**: Sensitivity analysis coverage is measured by the number of prior-width variations tested (minimum 3 values: nominal, ±20%), with stable conclusions across all variations indicating robustness (See US-3)

## Assumptions

- The ESO Science Archive provides programmatic access to UVES Large Programme spectra without requiring manual authentication beyond API key configuration.
- Laboratory transition frequencies from the NIST Atomic Spectra Database are accurate to within 0.001 cm⁻¹ for all relevant metal transitions (Fe II, Mg II, Si IV, etc.).
- The GitHub Actions free-tier runner has sufficient disk space to store downloaded spectra, intermediate data files, and model outputs without requiring external storage.
- PyMC v5 and related packages (arviz, specutils, astropy) are compatible with the Python version available on the GitHub Actions runner and can be installed via pip without compilation issues.
- Systematic errors in high-resolution spectroscopy are typically characterized per observation using calibration lamps (ThAr) or laser combs; if such data is unavailable, broad hyper-priors are used as a fallback.
- The SDSS DR galaxy density catalog is publicly accessible and provides sufficient spatial coverage to correlate with the quasar sightlines in the analysis (for auxiliary checks, though the primary test is the dipole fit).
- The sample of available quasar spectra contains at least 30 absorbers with sufficient signal-to-noise ratio to enable meaningful hierarchical Bayesian inference.
- The NUTS sampler will converge (R-hat < 1.01) for all model parameters when run with the specified chain configuration (4 chains, 2000 warmup, 4000 draws) on the GitHub Actions hardware.