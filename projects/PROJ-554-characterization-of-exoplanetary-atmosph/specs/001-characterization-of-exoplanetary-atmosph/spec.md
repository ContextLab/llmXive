# Feature Specification: Characterization of Exoplanetary Atmospheres through Advanced Spectroscopic Techniques

**Feature Branch**: `001-characterization-of-exoplanetary-atmosph`  
**Created**: 2026-06-08  
**Status**: Draft  
**Input**: User description: "Characterization of Exoplanetary Atmospheres through Advanced Spectroscopic Techniques"

## User Scenarios & Testing

### User Story 1 - Data Acquisition and Pre-processing (Priority: P1)

The system MUST download publicly available transmission spectra from the NASA Exoplanet Archive for a defined sample of hot Jupiters and temperate super-Earths, extracting equilibrium temperatures and host star metallicities for each. The system must aim for a target sample size of 20–30 hot Jupiters and 10–15 super-Earths, but MUST download ALL available spectra matching these planet type criteria to avoid selection bias.

**Why this priority**: Without a curated, reproducible dataset, no statistical analysis can occur. This is the foundational step that defines the scope and validity of the entire study.

**Independent Test**: The system can be tested by verifying that the output directory contains a metadata CSV with non-null values for temperature, metallicity, and planet category, and that the total count of unique planets falls within the range of 30 to 45 (sum of the target ranges).

**Acceptance Scenarios**:

1. **Given** the NASA Exoplanet Archive API is accessible, **When** the download script executes with the specified query filters (Hot Jupiters and Super-Earths), **Then** the system saves all available spectrum files to the local working directory.
2. **Given** a downloaded spectrum file, **When** the metadata extraction runs, **Then** the system outputs a CSV row containing the planet name, equilibrium temperature (in Kelvin), and host star metallicity ([Fe/H]).

---

### User Story 2 - Atmospheric Retrieval and Water Abundance Derivation (Priority: P2)

The system MUST run the `petitRADTRANS` retrieval pipeline in CPU-optimized mode on each spectrum to derive water vapor mixing ratios with associated uncertainty estimates. For spectra with low signal-to-noise, the system MUST derive an upper limit (censored value) rather than discarding the data point.

**Why this priority**: This step transforms raw observational data into the specific scientific variable (water abundance) required to answer the research question. It is the core analytical engine.

**Independent Test**: The system can be tested by running the retrieval on a single, known test spectrum and verifying that the output includes a water mixing ratio value (or an upper limit flag) and a 1-sigma uncertainty interval.

**Acceptance Scenarios**:

1. **Given** a valid transmission spectrum file and the `petitRADTRANS` configuration, **When** the retrieval job completes, **Then** the output file contains a water vapor mixing ratio (log10 scale) and a standard deviation, OR a flag indicating an upper limit.
2. **Given** a spectrum with low signal-to-noise, **When** the retrieval runs, **Then** the system reports a high uncertainty (≥ 1.0 dex) or flags the result as an upper limit rather than producing a false precision.

---

### User Story 3 - Statistical Correlation and Regression Analysis (Priority: P3)

The system MUST compute Kendall's tau correlation coefficients for censored data between water abundance and equilibrium temperature for each planet category, perform 1000-iteration bootstrap resampling for confidence intervals, and fit a Tobit regression model (or equivalent censored-data model) controlling for mass and metallicity.

**Why this priority**: This step directly addresses the research question by quantifying relationships and testing for confounding variables using methods valid for censored data, providing the final scientific conclusions.

**Independent Test**: The system can be tested by running the analysis on a mock dataset with known censored values and verifying that the calculated Kendall's tau matches the expected value within the bootstrap confidence interval.

**Acceptance Scenarios**:

1. **Given** a dataset of water abundances (including upper limits) and temperatures, **When** the correlation analysis runs, **Then** the system outputs a Kendall's tau coefficient and a 95% confidence interval derived from 1000 bootstrap iterations.
2. **Given** the full dataset including mass and metallicity, **When** the regression model fits, **Then** the system outputs p-values for each predictor (temperature, mass, metallicity) and a model fit statistic appropriate for censored data.

---

### Edge Cases

- **What happens when** a spectrum has a signal-to-noise ratio below the detection threshold for water? The system must derive an upper limit (censored value) for the water mixing ratio rather than flagging it as "non-detection" and excluding it.
- **How does the system handle** missing host star metallicity data for a specific planet? The system must exclude that planet from the multiple regression analysis but retain it for the bivariate correlation if temperature is available.
- **What happens when** `petitRADTRANS` fails to converge on a solution for a specific spectrum? The system must log the failure, attempt to derive an upper limit, and proceed without halting the entire pipeline.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST download transmission spectra for ALL available hot Jupiters and temperate super-Earths from the NASA Exoplanet Archive, aiming for a target sample size of 20–30 hot Jupiters and 10–15 super-Earths, ensuring the total count is between 30 and 45. (See US-1)
- **FR-002**: The system MUST execute `petitRADTRANS` in CPU-optimized mode to derive water vapor mixing ratios and uncertainties, ensuring the output contains a finite log10 mixing ratio and a positive standard deviation, or a valid upper limit flag. (See US-2)
- **FR-003**: The system MUST compute Kendall's tau correlation coefficients for censored data between water abundance and equilibrium temperature separately for hot Jupiters and super-Earths. (See US-3)
- **FR-004**: The system MUST perform bootstrap resampling with exactly 1000 iterations to estimate 95% confidence intervals for all correlation coefficients. (See US-3)
- **FR-005**: The system MUST fit a Tobit regression model (or equivalent censored-data model) with water abundance as the dependent variable and equilibrium temperature, planet mass, and host star metallicity as independent predictors. (See US-3)
- **FR-006**: The system MUST generate diagnostic plots including water abundance vs. temperature with error bars/limits, residual plots, and a correlation matrix. (See US-3)

### Key Entities

- **Exoplanet Spectrum**: A data structure containing wavelength, flux, and flux uncertainty arrays derived from HST or Spitzer observations.
- **Retrieval Result**: A record containing the derived water vapor mixing ratio, uncertainty, and model fit statistics for a specific planet, including a flag for upper limits.
- **Correlation Metric**: A statistical object holding the Kendall's tau coefficient, p-value, and bootstrap confidence intervals for a specific planet category.
- **Planet Category**: A classification label assigned to an exoplanet, specifically "Hot Jupiter" or "Temperate Super-Earth", used to stratify statistical analysis.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The correlation between water abundance and equilibrium temperature is measured against the null hypothesis (no correlation) using bootstrap-derived p-values, validating US-3 Acceptance Scenario 1. (See US-3)
- **SC-002**: The significance of the regression model predictors is measured against the standard alpha threshold of 0.05 to determine statistical relevance, validating US-3 Acceptance Scenario 2. (See US-3)
- **SC-003**: The robustness of the correlation is measured against the stability of the confidence intervals, defined as the 95% CI width for the water mixing ratio distribution being ≤ 0.2 dex, validating US-3 Acceptance Scenario 1. (See US-3)
- **SC-004**: The statistical power of the correlation test is measured against a minimum threshold of 0.8 for detecting a moderate correlation (|tau| ≥ 0.3), validating the study's ability to answer the research question. (See US-3)

## Assumptions

- The NASA Exoplanet Archive contains sufficient high-quality transmission spectra for the specified target sample size (aiming for 30–45 total) of hot Jupiters and super-Earths.
- The `petitRADTRANS` package can be installed and executed on a CPU-only environment (2 cores, 7 GB RAM) without requiring GPU acceleration or 8-bit quantization.
- The spectral resolution and signal-to-noise ratios of the downloaded HST/Spitzer spectra are sufficient to detect water vapor features or establish meaningful upper limits, as confirmed by the initial literature search.
- The equilibrium temperatures and host star metallicities provided in the Exoplanet Archive catalog are accurate and consistent across the dataset.
- The analysis will treat the correlation as associational, not causal, due to the lack of random assignment in the observational data.
- The sample size is sufficient to achieve statistical power (≥ 0.8) for detecting moderate correlations using the planned 1000 bootstrap iterations.