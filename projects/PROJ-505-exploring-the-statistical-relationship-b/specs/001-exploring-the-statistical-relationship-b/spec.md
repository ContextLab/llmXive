# Feature Specification: Exploring the Statistical Relationship Between Solar Wind Composition and Geomagnetic Indices

**Feature Branch**: `001-solar-wind-composition-geomagnetic`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Does solar wind elemental composition (specifically O/Fe and He/H ion ratios) independently predict geomagnetic storm intensity (Dst, Kp indices) beyond what is explained by solar wind velocity and interplanetary magnetic field strength?"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Temporal Alignment (Priority: P1)

The system MUST download, parse, and align time-series data from the ACE/WIND solar wind composition archives and the NOAA geomagnetic indices database into a unified, hourly-resolution dataset ready for analysis.

**Why this priority**: Without a clean, temporally aligned dataset containing both the predictor variables (composition ratios, bulk parameters) and outcome variables (Dst, Kp), no statistical analysis can be performed. This is the foundational block for the entire research pipeline.

**Independent Test**: Can be fully tested by executing the data ingestion script and verifying that the output CSV/Parquet file contains exactly one row per hour for the defined period (2000-2020), with no missing values in the core index columns (Dst, Kp) and that the timestamps are monotonically increasing.

**Acceptance Scenarios**:

1. **Given** the ACE SWICS and WIND composition data are available on CDAWeb, **When** the ingestion script runs, **Then** it must successfully retrieve the O/Fe, He/H, and C/O ion flux ratios and merge them with the hourly Dst and Kp indices.
2. **Given** the source data has varying resolutions (e.g., 64s vs 1-hour), **When** the resampling logic executes, **Then** all variables must be aligned to a 1-hour resolution using the hourly median aggregation method, ensuring a maximum temporal offset of ≤ 30 minutes for any single data point.

---

### User Story 2 - Multivariate Regression and Predictive Power Assessment (Priority: P2)

The system MUST perform a multivariate linear regression analysis where geomagnetic indices (Dst, Kp) are predicted by physically relevant coupling functions (derived from bulk solar wind parameters) first, and then by adding composition ratios (O/Fe, He/H) to measure the incremental explanatory power (ΔR²).

**Why this priority**: This directly addresses the core research question: "Do composition ratios provide independent predictive power?" It distinguishes this project from existing bulk-parameter-only studies.

**Independent Test**: Can be fully tested by running the regression module on the aligned dataset and verifying that the output includes a coefficient table, p-values, and a specific metric for the change in R-squared (ΔR²) between the baseline model (coupling functions only) and the full model (coupling functions + composition).

**Acceptance Scenarios**:

1. **Given** the aligned dataset, **When** the regression model is fitted, **Then** it must report the coefficient, standard error, and p-value for each composition ratio (O/Fe, He/H, C/O) while controlling for coupling functions (e.g., Akasofu epsilon).
2. **Given** a 5-fold cross-validation setup, **When** the models are evaluated, **Then** the system must output the out-of-sample R² for both the baseline and full models, calculating the difference (ΔR²) to quantify the independent contribution of composition.

---

### User Story 3 - Statistical Significance and Sensitivity Analysis (Priority: P3)

The system MUST validate the statistical significance of composition coefficients using block permutation tests and perform a sensitivity analysis on any decision thresholds (e.g., significance cutoffs) to ensure robustness against multiple comparisons.

**Why this priority**: To be methodologically sound, the findings must distinguish between random noise and true signal, especially when testing multiple hypotheses (multiple ratios, multiple indices). This prevents false positives.

**Independent Test**: Can be fully tested by running the significance module and verifying that the block permutation test generates a null distribution of coefficients and that the sensitivity analysis reports how the number of significant predictors changes across a swept range of thresholds.

**Acceptance Scenarios**:

1. **Given** the fitted regression coefficients, **When** the block permutation test runs (shuffling composition data in blocks of 24 hours for ≥ 1,000 iterations), **Then** the observed coefficient must fall outside the 95% confidence interval of the null distribution to be flagged as significant.
2. **Given** a significance threshold (e.g., p < 0.05), **When** the sensitivity analysis sweeps the threshold over {0.01, 0.05, 0.10}, **Then** the system must report the corresponding change in the number of significant predictors and the stability of the ΔR² metric.

---

### Edge Cases

- What happens when the ACE or WIND instruments have data gaps exceeding 6 hours? (System must interpolate or flag the row as missing, not crash).
- How does the system handle periods where solar wind velocity is near zero or IMF is near zero (division by zero risks in ratio calculations)? (System must apply a small epsilon floor or exclude these specific rows).
- How does the system handle the transition between different instrument versions (e.g., ACE SWICS vs. SWICS-2)? (System must apply documented calibration offsets or treat them as separate cohorts).

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and parse solar wind composition data (O/Fe, He/H, C/O) from ACE/WIND archives for the period 2000-2020. (See US-1)
- **FR-002**: System MUST download and parse NOAA Dst and Kp geomagnetic indices for the same 2000-2020 period. (See US-1)
- **FR-003**: System MUST align all time series to a 1-hour resolution using hourly median aggregation, ensuring a maximum temporal offset of ≤ 30 minutes. (See US-1)
- **FR-004**: System MUST fit a baseline multivariate linear regression model predicting Dst/Kp using physically relevant coupling functions (e.g., Akasofu epsilon, Newell function) derived from bulk parameters. (See US-2)
- **FR-005**: System MUST fit a full multivariate linear regression model predicting Dst/Kp using coupling functions plus composition ratios (O/Fe, He/H, C/O). (See US-2)
- **FR-006**: System MUST calculate the incremental R-squared (ΔR²) between the baseline and full models to quantify independent predictive power. (See US-2)
- **FR-007**: System MUST perform a 5-fold cross-validation to assess out-of-sample predictive gain from composition. (See US-2)
- **FR-008**: System MUST execute a block permutation test (minimum 1,000 iterations, continuing until p-value standard error < 0.001 or max [deferred] iterations) using a block size of 24 hours to validate the statistical significance of composition coefficients. (See US-3)
- **FR-009**: System MUST perform a sensitivity analysis sweeping the significance threshold over {0.01, 0.05, 0.10} and report the variation in the number of significant predictors. (See US-3)
- **FR-010**: System MUST apply Benjamini-Hochberg False Discovery Rate (FDR) correction for multiple hypothesis testing across the three composition ratios and two indices. (See US-3)
- **FR-011**: System MUST calculate and report the Variance Inflation Factor (VIF) for all predictors to detect multicollinearity, flagging any VIF ≥ 5. (See US-2)

### Key Entities

- **SolarWindSample**: Represents a single time-point observation containing bulk plasma parameters (velocity, density), magnetic field (IMF), and compositional ratios (O/Fe, He/H, C/O).
- **GeomagneticIndex**: Represents a single time-point observation of the Dst or Kp index.
- **RegressionModel**: Represents a fitted statistical model containing coefficients, p-values, R-squared, and cross-validation metrics.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation/research phase.

- **SC-001**: The system MUST reject the null hypothesis of no improvement if the permutation-derived p-value < 0.05. If rejected, the system MUST report ΔR² and its 95% confidence interval. If ΔR² > 0.05, the system claims 'statistically significant and practically meaningful improvement'; if ΔR² ≤ 0.05, the system reports 'statistically significant but below practical threshold'. (See US-2)
- **SC-002**: A coefficient is considered significant if its observed value falls outside the [deferred] percentile range of the null distribution generated by the block permutation test. (See US-3)
- **SC-003**: The stability of the significance findings is measured against the swept thresholds {0.01, 0.05, 0.10} to assess sensitivity to the choice of cutoff. (See US-3)
- **SC-004**: The model performance (out-of-sample R²) is measured against the 5-fold cross-validation split to ensure the predictive gain is not due to overfitting. (See US-2)

## Assumptions

- The ACE SWICS and WIND composition datasets contain the necessary ion flux measurements to calculate O/Fe, He/H, and C/O ratios for the entire 2000-2020 period.
- The NOAA Dst and Kp indices are available at an hourly resolution or can be reliably interpolated to hourly without introducing significant bias.
- The relationship between solar wind parameters and geomagnetic indices is non-linear, requiring the use of coupling functions (e.g., Akasofu epsilon) rather than raw linear sums.
- The analysis will be conducted on a standard CPU-only environment (GitHub Actions free tier: 2 CPU, 7GB RAM), requiring data to be subsampled or processed in chunks if the full 20-year dataset exceeds memory limits.
- The data sources (CDAWeb, NOAA) are accessible via standard HTTP GET requests without requiring complex authentication or proprietary keys.
- Any missing data points in the source archives are handled via hourly median aggregation or exclusion, assuming gaps are random and not systematic.
- The "bulk parameters" (velocity, density, IMF) are sufficient to capture the primary variance in geomagnetic activity via coupling functions, allowing composition to be tested as an additive factor.
- The study is observational; therefore, all findings will be framed as associational relationships, not causal effects.