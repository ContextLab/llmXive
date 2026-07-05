# Feature Specification: Assessing the Validity of Modified Newtonian Dynamics with Galaxy Rotation Curves

**Feature Branch**: `[001-assess-mond-validity]`  
**Created**: 2026-06-12  
**Status**: Draft  
**Input**: User description: "Assessing the Validity of Modified Newtonian Dynamics (MOND) with Galaxy Rotation Curves"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1)

As a researcher, I want to download and preprocess galaxy rotation curve data from the SPARC database so that I have a clean, filtered dataset ready for model fitting.

**Why this priority**: This is the foundational step without which no analysis can proceed. The entire downstream methodology depends on obtaining valid, well-filtered observational data.

**Independent Test**: Can be fully tested by executing the data download and preprocessing script and verifying that the output contains ≥15 data points per galaxy with inclination uncertainties <10°.

**Acceptance Scenarios**:

1. **Given** the SPARC database URL is accessible, **When** the download script executes, **Then** all rotation curve files are saved locally with verification checksums
2. **Given** raw rotation curve data with inclination uncertainties, **When** the preprocessing filter runs, **Then** galaxies with inclination uncertainty ≥10° are excluded from the analysis sample
3. **Given** a parsed galaxy rotation curve file, **When** the point-count filter executes, **Then** galaxies with <15 radial data points are excluded

---

### User Story 2 - Dual-Model Fitting and Goodness-of-Fit Computation (Priority: P2)

As a researcher, I want to fit both MOND and NFW dark matter halo models to each galaxy's rotation curve and compute goodness-of-fit metrics so that I can quantitatively compare their predictive accuracy.

**Why this priority**: This delivers the core scientific comparison that answers the research question. Without dual-model fitting, no comparative assessment is possible.

**Independent Test**: Can be fully tested by running the fitting pipeline on a subset of galaxies and verifying that reduced chi-squared, AIC, and BIC values are computed and match the analytical definitions provided in FR-004 and FR-005.

**Acceptance Scenarios**:

1. **Given** a filtered galaxy rotation curve with radial distances and velocities, **When** both MOND and NFW models are fitted, **Then** velocity uncertainty-weighted least-squares optimization completes within 30 seconds per galaxy
2. **Given** fitted model parameters for a galaxy, **When** goodness-of-fit metrics are computed, **Then** reduced chi-squared, AIC, and BIC are calculated with documented degrees of freedom
3. **Given** the full sample of fitted galaxies, **When** model comparison metrics are aggregated, **Then** the system reports the distribution of reduced chi-squared values for both models

---

### User Story 3 - Residual Analysis and Statistical Comparison (Priority: P3)

As a researcher, I want to analyze residual distributions between observed and predicted velocities and perform statistical tests comparing the two models so that I can assess systematic deviations and model validity.

**Why this priority**: This provides deeper diagnostic insight beyond point estimates, revealing whether model failures are random or systematic.

**Independent Test**: Can be fully tested by running the residual analysis module on the fitted sample and verifying that block-bootstrap permutation test statistics and p-values are produced.

**Acceptance Scenarios**:

1. **Given** observed velocities and model-predicted velocities for each galaxy, **When** residuals are computed, **Then** residual distributions are stored with mean, median, and standard deviation per model
2. **Given** residual distributions for MOND and NFW models, **When** the block-bootstrap permutation test executes, **Then** test statistic and p-value are computed to assess distribution differences while accounting for galaxy-level clustering
3. **Given** multiple hypothesis tests across the sample, **When** family-wise error correction is applied, **Then** Holm-Bonferroni adjusted p-values are reported

---

### Edge Cases

- What happens when a galaxy rotation curve file is malformed or missing required columns (radial distance, velocity, velocity uncertainty)?
- How does the system handle convergence failures during scipy.optimize.curve_fit (e.g., when NFW parameters produce non-physical scale radii)?
- What happens when the SPARC database is temporarily unavailable or returns HTTP errors during download?
- How does the system handle galaxies where MOND acceleration scale a0 produces degenerate fits (flat rotation curves indistinguishable from NFW)?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download SPARC rotation curve data files using wget/curl with retry logic of at most 3 failed attempts before flagging as unavailable (See US-1)
- **FR-002**: System MUST parse rotation curve files to extract radial distances, rotational velocities, and velocity uncertainties for each galaxy (See US-1)
- **FR-003**: System MUST filter galaxies to include only those with inclination uncertainties <10° and ≥15 radial data points (See US-1)
- **FR-004**: System MUST implement the MOND 'simple' interpolating function using the explicit analytical form: a = a_N/2 + sqrt((a_N/2)^2 + a_N*a_0) with a0 = 1.2×10^(-10) m/s². This formula is the specific scientific target for this study (See US-2)
- **FR-005**: System MUST implement the NFW dark matter halo profile with concentration and scale radius as parameters, applying a Gaussian prior on concentration based on the baryonic Tully-Fisher relation (c ~ M_baryon^()) with a standard deviation of dex (See US-2)
- **FR-006**: System MUST fit both models to each galaxy using scipy.optimize.curve_fit with velocity uncertainty weighting and the priors defined in FR-005 (See US-2)
- **FR-007**: System MUST compute reduced chi-squared, AIC, and BIC for each galaxy-model combination (See US-2)
- **FR-008**: System MUST calculate residual distributions (observed − predicted velocities) across the full sample (See US-3)
- **FR-009**: System MUST perform a block-bootstrap permutation test on residual distributions to compare MOND and NFW models, resampling at the galaxy level to account for spatial correlations (See US-3)
- **FR-010**: System MUST apply Holm-Bonferroni correction when >1 hypothesis test is executed (See US-3)
- **FR-011**: System MUST document that all findings are framed as ASSOCIATIONAL rather than causal, given the observational nature of the data (See US-2)
- **FR-012**: System MUST perform sensitivity analysis on the reduced chi-squared threshold by sweeping values across a range of magnitudes and report the distribution of pass rates for each model (See US-2)

### Key Entities

- **GalaxyRotationCurve**: Represents a single galaxy's kinematic data with attributes: galaxy_id, radial_distances, rotational_velocities, velocity_uncertainties, inclination, inclination_uncertainty, baryonic_mass_distribution
- **ModelFit**: Represents a fitted model result with attributes: galaxy_id, model_type (MOND or NFW), fitted_parameters, reduced_chi_squared, AIC, BIC, residual_statistics
- **GoodnessOfFitMetric**: Represents computed fit quality with attributes: metric_name, metric_value, degrees_of_freedom, reference_value (e.g., threshold for pass/fail)

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Reduced chi-squared values are measured to assess model adequacy (See US-2)
- **SC-002**: The proportion of galaxies with χ² < 1.5 is measured for both models and compared to assess relative performance (See US-2)
- **SC-003**: AIC difference between MOND and NFW models is measured against the evidence threshold of |ΔAIC| > 10 for strong preference (See US-2)
- **SC-004**: Block-bootstrap permutation test p-values are measured against α = 0.05 to assess residual distribution differences (See US-3)
- **SC-005**: Multiple-comparison corrected p-values are measured against the family-wise error rate of ≤0.05 (See US-3)
- **SC-006**: Sensitivity analysis sweep results are measured across the threshold set ∈ {1.0, 1.25, 1.5, 1.75} to quantify threshold dependence (See US-2)

## Assumptions

- The SPARC database remains accessible at https://astroweb.cwru.edu/SPARC/ for the duration of data download
- The standard MOND acceleration scale a0 = 1.2×10^(-10) m/s² is used as the community-standard default (Milgrom 1983 basis)
- All SPARC galaxies in the sample have publicly available baryonic mass distribution data (stellar + gas) required for MOND predictions
- The analysis runs on CPU-only hardware with 2 cores, ~7 GB RAM, A moderate amount of disk space (e.g., several gigabytes) is anticipated., and completes within 6 hours total
- No GPU acceleration, CUDA, or mixed-precision training is required or permitted for this analysis
- The scipy.optimize.curve_fit optimizer converges within 1000 iterations for all galaxies in the filtered sample
- Velocity uncertainties in SPARC data are treated as Gaussian and independent across radial points
- The NFW profile parameters (concentration, scale radius) are physically bounded to prevent non-physical fits (scale radius > 0, concentration ∈ [low, moderate])
- The block-bootstrap permutation test is appropriate for comparing residual distributions given the sample sizes available and the clustering structure
- All cited references in Related work are valid arXiv preprints that remain accessible at the provided URLs