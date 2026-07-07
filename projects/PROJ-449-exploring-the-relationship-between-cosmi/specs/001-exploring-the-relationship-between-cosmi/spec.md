# Feature Specification: Exploring the Relationship Between Cosmic Ray Composition and Solar Activity Cycles

**Feature Branch**: `001-cosmic-ray-composition-solar-cycle`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Exploring the Relationship Between Cosmic Ray Composition and Solar Activity Cycles"

## User Scenarios & Testing

### User Story 1 - Retrieve and Preprocess Multi-Species Cosmic Ray Flux Data (Priority: P1)

The researcher MUST be able to download daily averaged flux data for protons, helium, and heavier nuclei (CNO/Fe) from the AMS-02 public repository for the period 2011–2024, and automatically align this data with concurrent solar activity indices (sunspot numbers) to create a unified time-series dataset.

**Why this priority**: This is the foundational data layer. Without a correctly aligned, multi-species dataset covering at least one full solar cycle, no correlation or modulation analysis can be performed. It is the prerequisite for all subsequent analysis.

**Independent Test**: A script can be run that downloads the specified AMS-02 and NOAA/SWPC data, performs the time-alignment, and outputs a single CSV file containing columns for date, proton flux, helium flux, heavy flux, and sunspot number. The test passes if the file exists, contains no missing dates in the 2011-2024 range (or explicitly flags gaps), and the row count matches the expected daily resolution.

**Acceptance Scenarios**:

1. **Given** the AMS-02 public data API is accessible, **When** the retrieval script runs for the date range 2011-01-01 to 2024-12-31, **Then** the system downloads and parses fluxes for protons, helium, and CNO/Fe nuclei into a structured format.
2. **Given** the AMS-02 data and NOAA sunspot data are retrieved, **When** the alignment process runs, **Then** the system outputs a unified dataset where every row contains a timestamp and corresponding values for all required variables (fluxes and sunspot number), handling missing data points by either interpolation (if < 5 days) or flagging as null.

---

### User Story 2 - Compute Composition Ratios and Correlation with Solar Activity (Priority: P2)

The researcher MUST be able to compute composition ratios (He/p, Fe/p) from the unified dataset and perform time-lagged Pearson/Spearman correlation analyses against sunspot numbers (±12 months lag) to identify phase relationships.

**Why this priority**: This implements the core scientific hypothesis testing. It moves from raw data to the primary statistical evidence required to answer the research question regarding differential modulation patterns.

**Independent Test**: The system generates a correlation matrix and a set of time-lag plots. The test passes if the output includes correlation coefficients for lags ranging from -12 to +12 months for both He/p and Fe/p ratios against sunspot numbers, and if the statistical significance (p-value) is calculated for each.

**Acceptance Scenarios**:

1. **Given** a unified dataset with fluxes and sunspot numbers, **When** the correlation analysis runs, **Then** the system calculates and reports the Pearson correlation coefficient and p-value for the He/p ratio against sunspot numbers for all lags between -12 and +12 months.
2. **Given** the same dataset, **When** the analysis runs for heavy nuclei, **Then** the system calculates and reports the Spearman correlation coefficient and p-value for the Fe/p ratio against sunspot numbers for the same lag range, distinguishing between linear and monotonic relationships.

---

### User Story 3 - Validate Results via Bootstrap Resampling and Model Fitting (Priority: P3)

The researcher MUST be able to validate the statistical robustness of the observed correlations using bootstrap resampling (n=1000) and fit a rigidity-dependent diffusion model to the observed modulation amplitudes to compare against theoretical transport mechanisms.

**Why this priority**: This adds scientific rigor and methodological soundness. It addresses the "multiplicity & power" and "measurement validity" concerns by ensuring the observed patterns are not statistical artifacts and provides a quantitative comparison to physical models.

**Independent Test**: The system outputs confidence intervals (95%) for the correlation coefficients derived from 1000 bootstrap iterations and generates a fitted curve for the diffusion model. The test passes if the confidence intervals are narrower than the initial point estimates (indicating stability) and the model fitting converges within the 6-hour compute limit.

**Acceptance Scenarios**:

1. **Given** the correlation results from User Story 2, **When** the bootstrap resampling process runs (n=1000), **Then** the system outputs the 95% confidence interval for the maximum correlation coefficient found in User Story 2, ensuring the interval does not include zero if the original p-value was < 0.01.
2. **Given** the modulation amplitudes derived from the time-series, **When** the least-squares optimization for the rigidity-dependent diffusion model runs, **Then** the system outputs the fitted parameters and the residual error, confirming the model explains a statistically significant portion of the variance (R² > 0.5).

---

### Edge Cases

- **Data Gap Handling**: What happens if AMS-02 data is missing for a continuous period > 30 days (e.g., instrument maintenance)? The system must flag this as a "Data Gap" and exclude the affected period from the correlation analysis rather than interpolating, to avoid biasing the solar cycle phase.
- **Solar Cycle Transition**: How does the system handle the ambiguous boundary between Solar Cycle 24 and 25? The analysis must treat the transition period (2019-2020) as a distinct phase with its own lag analysis or explicitly note the potential for reduced statistical power in this specific window.
- **Zero Flux Events**: How does the system handle days with zero reported flux for heavy nuclei (rare but possible in specific energy bins)? The system must log these as "Below Detection Limit" and exclude them from the ratio calculation to prevent division-by-zero or skewing the mean.

## Requirements

### Functional Requirements

- **FR-001**: System MUST retrieve daily averaged flux data for protons, helium, and CNO/Fe nuclei from the AMS-02 public repository for the period 2011-01-01 to 2024-12-31 (See US-1).
- **FR-002**: System MUST download and align concurrent sunspot number data from NOAA/SWPC with the cosmic ray flux data at a daily resolution (See US-1).
- **FR-003**: System MUST compute composition ratios (He/p and Fe/p) from the aligned flux data, excluding any data points where the denominator flux is zero or missing (See US-2).
- **FR-004**: System MUST perform Pearson and Spearman correlation analyses between the composition ratios and sunspot numbers across a time-lag window of ±12 months (See US-2).
- **FR-005**: System MUST execute bootstrap resampling with n=1000 iterations to estimate 95% confidence intervals for the calculated correlation coefficients (See US-3).
- **FR-006**: System MUST fit a rigidity-dependent diffusion model to the observed modulation amplitudes using least-squares optimization and report the R² value (See US-3).
- **FR-007**: System MUST explicitly flag any data gaps > 30 days in the source datasets and exclude them from the primary statistical analysis to prevent bias (See Edge Cases).

### Key Entities

- **CosmicRayFlux**: Represents the daily averaged flux for a specific particle species (proton, helium, heavy) at a specific rigidity, containing attributes for date, species, flux value, and uncertainty.
- **SolarActivityIndex**: Represents the daily sunspot number and solar wind parameters, containing attributes for date, sunspot_number, and solar_wind_speed.
- **CompositionRatio**: Represents the derived ratio between two species (e.g., He/p), containing attributes for date, numerator_species, denominator_species, ratio_value, and lag_analysis_results.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The percentage of days with valid data coverage in the 2011-2024 period is measured against the requirement of ≥ 90% continuous coverage for the analysis to be considered statistically robust (See FR-001, FR-002).
- **SC-002**: The p-value of the maximum correlation coefficient found between composition ratios and sunspot numbers is measured against the threshold of p < 0.01 to determine statistical significance of the modulation pattern (See FR-004).
- **SC-003**: The width of the 95% confidence interval derived from bootstrap resampling is measured against the stability of the correlation coefficient; a width < 0.1 indicates robust statistical inference (See FR-005).
- **SC-004**: The R² value of the fitted rigidity-dependent diffusion model is measured against the observed variance to confirm the model explains ≥ 50% of the modulation amplitude (See FR-006).
- **SC-005**: The total compute time for the full analysis pipeline (retrieval, alignment, correlation, bootstrap, fitting) is measured against the 6-hour limit of the GitHub Actions free-tier runner (See Assumptions).

## Assumptions

- **Data Availability**: The AMS-02 public data repository contains continuous daily averaged flux data for protons, helium, and CNO/Fe nuclei from 2011 to 2024. If specific energy bins are missing, the analysis will default to the most populated rigidity bin available for each species.
- **Computational Constraints**: The entire analysis pipeline, including 1000 bootstrap iterations and least-squares fitting, will complete within the 6-hour time limit and 7 GB RAM constraint of a GitHub Actions free-tier runner using CPU-only methods (no GPU acceleration).
- **Methodological Framing**: Since the study is observational (no random assignment), all findings regarding the relationship between solar activity and cosmic ray composition will be framed as **associational** correlations, not causal effects, unless the data reveals a specific identification strategy (e.g., natural experiment) which is not currently assumed.
- **Variable Fit**: The AMS-02 dataset is assumed to contain all necessary variables (fluxes for specific species) and the NOAA/SWPC dataset contains the necessary solar activity indices. If a specific variable required for a refined analysis is missing, a `[NEEDS CLARIFICATION]` marker will be generated.
- **Threshold Justification**: The time-lag window of ±12 months is selected based on the approximate duration of a solar cycle phase transition and is justified as sufficient to capture the delayed response of cosmic rays to solar wind changes; a sensitivity analysis will sweep lags in {6, 9, 12, 15} months to ensure robustness.
- **Collinearity**: Since He/p and Fe/p ratios share the proton flux as a denominator, they are definitionally related; the analysis will not claim independent predictive effects for both simultaneously but will treat them as distinct indicators of modulation magnitude, requiring a collinearity diagnostic (VIF) if used in a joint model.
