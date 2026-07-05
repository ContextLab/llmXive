# Feature Specification: Investigating the Correlation Between Muon Flux and Atmospheric Temperature Profiles

**Feature Branch**: `001-muon-temp-correlation`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Investigating the Correlation Between Muon Flux and Atmospheric Temperature Profiles"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Ingestion and Temporal Alignment (Priority: P1)

The researcher MUST be able to ingest IceCube muon flux time series and ERA5 atmospheric reanalysis profiles, align them to a common temporal resolution (daily bins), and verify data completeness before analysis begins.

**Why this priority**: Without aligned, complete datasets, no correlation or regression analysis can be performed. This is the foundational step; if data cannot be merged due to missing timestamps or incompatible resolutions, the entire study fails.

**Independent Test**: The system can be tested by running the ingestion script on a sample subset of historical data (e.g., 1 week) and verifying that the output is a single CSV with matching dates, non-null muon counts, and non-null temperature metrics.

**Acceptance Scenarios**:

1. **Given** a valid IceCube muon flux CSV and an ERA5 temperature CSV covering overlapping date ranges, **When** the ingestion script runs with a daily aggregation bin, **Then** the output file contains exactly one row per day where both datasets have valid data, and rows with missing data in either source are excluded.
2. **Given** a dataset where ERA5 data is missing for 3 consecutive days in the middle of the range, **When** the script processes the data, **Then** the resulting aligned dataset contains gaps for those 3 days (or excludes them) and logs a warning count of 3 missing entries.
3. **Given** a request to align data with a weekly resolution, **When** the script executes, **Then** muon counts are summed and temperature metrics are averaged over 7-day windows, and the output date column represents the start of each week.

---

### User Story 2 - Statistical Correlation and Regression Analysis (Priority: P2)

The researcher MUST be able to compute Pearson and Spearman correlation coefficients between muon flux and the Effective Temperature (T_eff) metric, and fit a linear regression model to quantify the temperature coefficient.

**Why this priority**: This is the core analytical step that answers the research question. It transforms aligned data into quantitative evidence regarding the relationship between atmospheric temperature and muon flux using the physically correct proxy (T_eff).

**Independent Test**: The system can be tested by running the analysis module on the aligned dataset and verifying that the output includes correlation coefficients (r-values), p-values, and regression slope/intercept values with confidence intervals.

**Acceptance Scenarios**:

1. **Given** a clean, aligned dataset of 30 days of muon flux and Effective Temperature, **When** the correlation analysis runs, **Then** the output includes a Pearson correlation coefficient and a p-value, and if p < 0.01, the result is flagged as statistically significant.
2. **Given** a dataset with non-linear trends, **When** the Spearman correlation is computed, **Then** the output provides a rank-based correlation coefficient that differs from the Pearson coefficient if the relationship is non-linear.
3. **Given** the aligned dataset, **When** the linear regression model is fitted, **Then** the output includes the slope (muon flux change per degree Celsius), the intercept, and the R-squared value, all calculated using standard ordinary least squares (OLS) on CPU.

---

### User Story 3 - Sensitivity Analysis and Seasonal Stratification (Priority: P3)

The researcher MUST be able to validate the robustness of the findings by performing sensitivity analysis on the T_eff calculation parameters and stratifying results by season (summer vs. winter).

**Why this priority**: This ensures the results are not artifacts of a specific data window or arbitrary parameter choice. It addresses the "threshold justification" and "methodological soundness" requirements by demonstrating stability across conditions.

**Independent Test**: The system can be tested by running the analysis with modified parameters (e.g., different weighting functions) and verifying that the output generates a comparison table showing how the correlation coefficient and slope vary.

**Acceptance Scenarios**:

1. **Given** a baseline correlation result, **When** the sensitivity analysis sweeps the pressure weighting function parameters, **Then** the output table lists the correlation coefficient and slope for each variation, showing the sensitivity of the result to the T_eff calculation method.
2. **Given** a full-year dataset, **When** the analysis is stratified by season (June-August vs. December-February), **Then** the output provides separate correlation coefficients and regression slopes for each season, allowing comparison of the relationship strength.
3. **Given** a dataset with potential outliers, **When** the analysis is re-run after applying a standard deviation filter (e.g., removing points > 3σ), **Then** the output compares the filtered results to the unfiltered baseline, reporting the change in the correlation coefficient.

### Edge Cases

- What happens when the ERA5 data has missing vertical profiles for a specific date? (System should skip that date or interpolate if a fallback is defined, but default is to exclude).
- How does the system handle dates where IceCube data is flagged as "calibration mode" or "maintenance"? (System should exclude these dates automatically based on metadata flags).
- What if the correlation p-value is exactly 0.05? (System should report the exact value and not auto-flag as significant unless p < 0.05).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download and parse IceCube muon flux data from the IceCube Public Data Portal (https://icecube.wisc.edu/science/data) and ERA Reanalysis data from the CDS API (https://cds.climate.copernicus.eu), ensuring all files are cached locally for reproducibility. (See US-1)
- **FR-002**: System MUST align temporal resolution by aggregating muon counts to daily bins and matching them with ERA5 temperature metrics (pressure levels 1000hPa to 10hPa), excluding any dates where either source lacks valid data. (See US-1)
- **FR-003**: System MUST compute both Pearson and Spearman correlation coefficients between muon flux and the Effective Temperature (T_eff), outputting the correlation coefficient (r) and p-value for each pair. (See US-2)
- **FR-004**: System MUST perform linear regression to quantify the temperature coefficient (slope), including the calculation of confidence intervals for the slope and intercept. (See US-2)
- **FR-005**: System MUST execute a sensitivity analysis that varies the T_eff calculation weighting parameters and reports the variation in correlation coefficients and slopes across this sweep. (See US-3)
- **FR-006**: System MUST stratify the analysis by season (Summer: June-August, Winter: December-February) and output separate correlation and regression results for each season. (See US-3)
- **FR-007**: System MUST log all data exclusion events (e.g., missing ERA5 profiles, IceCube maintenance flags) with a count and date range to ensure transparency in the dataset used. (See US-1, Edge Cases)
- **FR-008**: System MUST calculate the Effective Temperature (T_eff) using the standard weighted integral formulation (T_eff = ∫ T(z) * W(z) dz / ∫ W(z) dz) where W(z) is the muon production/decay probability weight function, rather than using a single-point temperature proxy. (See US-2)

### Key Entities

- **MuonTimeSeries**: Represents daily aggregated muon counts from IceCube, with attributes: `date`, `count`, `uncertainty`, `quality_flag`.
- **AtmosphericProfile**: Represents daily temperature metrics from ERA5, with attributes: `date`, `pressure_levels` (map of hPa to temp), `mean_temp`, `vertical_gradient`, `pressure`.
- **EffectiveTemperature**: Represents the calculated Effective Temperature, with attributes: `date`, `t_eff_value`, `weight_function_version`, `uncertainty`.
- **AlignedDataset**: Represents the merged dataset ready for analysis, with attributes: `date`, `muon_count`, `t_eff_value`, `season_flag`, `exclusion_reason`.
- **SensitivityAnalysisResult**: Represents the outcome of the sensitivity sweep, with attributes: `parameter_set`, `correlation_coefficient`, `slope`, `p_value`.
- **CorrelationResult**: Represents the outcome of a statistical test, with attributes: `metric_pair` (e.g., "flux_vs_t_eff"), `correlation_type` (Pearson/Spearman), `r_value`, `p_value`, `sample_size`.
- **RegressionModel**: Represents the linear fit, with attributes: `slope`, `intercept`, `r_squared`, `slope_ci_lower`, `slope_ci_upper`, `season` (optional).

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The correlation coefficient magnitude and p-value are measured against the hypothesis that a positive relationship exists (r > 0, p < 0.01) using the Effective Temperature (T_eff) metric. (See US-2)
- **SC-002**: The stability of the temperature coefficient is measured by comparing the slope variations across the sensitivity sweep against the combined statistical uncertainty (95% CI) of the individual fits, and by performing an ANOVA test to confirm no significant difference (p > 0.05) in slopes across parameter sets. (See US-3)
- **SC-003**: The seasonal variation is measured by comparing the correlation coefficients between Summer and Winter subsets, quantifying the magnitude of the difference (|r_summer - r_winter|) and the statistical significance via Fisher's r-to-z transformation (p < 0.05), regardless of whether a difference is found. (See US-3)
- **SC-004**: The computational feasibility is measured by the total runtime of the analysis pipeline on a CPU-only environment (2 vCPU, 7GB RAM, Intel Xeon equivalent), which must complete within 6 hours. (See Assumptions)

## Assumptions

- The IceCube muon flux data (https://icecube.wisc.edu/science/data) and ERA5 Reanalysis data (https://cds.climate.copernicus.eu) are publicly accessible and do not require authentication credentials to download (or require a free CDS API key).
- The Effective Temperature (T_eff) calculated via the weighted integral of the vertical temperature profile is a valid proxy for the muon production region density, as per standard atmospheric physics models (Grieder,).
- The analysis will use a standard CPU-only environment (a modest vCPU count, 7GB RAM, Intel Xeon equivalent) and will not require GPU acceleration; all statistical methods (Pearson, Spearman, OLS) are computationally light and will run within the 6-hour limit.
- The dataset size (historical muon flux and ERA profiles) will fit within the available disk space after downloading and processing.
- No randomization is involved in the data collection; therefore, all findings will be framed as associational correlations, not causal effects.
- The "sensitivity analysis" will vary the T_eff calculation parameters (e.g., weighting function variants) to assess robustness, rather than a continuous sweep, to maintain computational efficiency.
- If the ERA5 data lacks a specific pressure level for a given day, the system will interpolate linearly; this method is assumed to be sufficient for the proxy variable.