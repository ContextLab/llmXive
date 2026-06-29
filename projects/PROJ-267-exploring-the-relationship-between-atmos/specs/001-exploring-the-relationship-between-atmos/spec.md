# Feature Specification: Atmospheric River Gravity Correlation

**Feature Branch**: `001-atmospheric-river-gravity`  
**Created**: 2024-05-22  
**Status**: Draft  
**Input**: User description: "Research: Atmospheric River Intensity vs Regional Gravity Variations"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Ingestion & Preprocessing (Priority: P1)

The system MUST retrieve GRACE-FO processed mascon data and NOAA CPC Atmospheric River Catalog data, then align them to a common monthly temporal resolution for the West Coast North America region (35°N-50°N, 120°W-125°W).

**Why this priority**: This is the foundational step; without clean, aligned datasets, no statistical analysis can occur.

**Independent Test**: Can be fully tested by executing the data pipeline script and verifying the output contains a merged CSV with ≥ 90% of expected monthly rows and no NaN values in the primary columns.

**Acceptance Scenarios**:

1. **Given** the NOAA and GRACE-FO public APIs are accessible, **When** the pipeline runs, **Then** it downloads the latest available mascon solutions and AR catalog entries.
2. **Given** raw GRACE-FO data contains degree-1 and C20 coefficients, **When** preprocessing runs, **Then** the output data reflects low-degree correction, C20 replacement, and 300 km Gaussian smoothing.

---

### User Story 2 - Statistical Correlation Analysis (Priority: P1)

The system MUST compute Pearson correlation coefficients between AR intensity metrics and regional gravity anomalies across varying lag windows., applying multiple-comparison correction to the resulting p-values. The system MUST apply bootstrap resampling (1000 iterations, seed=42) to estimate confidence intervals on correlation coefficients. The system MUST validate signal against control regions (areas without significant AR activity).

**Why this priority**: This directly addresses the research question and produces the core scientific result.

**Independent Test**: Can be fully tested by running the analysis module on a mock dataset and verifying the output includes correlation coefficients, p-values, corrected significance flags, bootstrap confidence intervals, and control region comparison results.

**Acceptance Scenarios**:

1. **Given** aligned time-series data exists, **When** the analysis runs, **Then** it calculates correlation for lags 0, 1, 2, and 3 months.
2. **Given** multiple lag tests are performed, **When** significance is reported, **Then** p-values are corrected using Bonferroni or FDR methods.
3. **Given** correlation coefficients are computed, **When** bootstrap runs, **Then** Multiple resampled iterations produce 95% confidence intervals on each coefficient.
4. **Given** control regions are defined, **When** validation runs, **Then** correlation in control regions is compared to target region to distinguish signal from noise.

---

### User Story 3 - Diagnostic Visualization & Sensitivity Reporting (Priority: P2)

The system MUST generate time-series overlays, scatter plots with regression lines, spatial anomaly maps, and a sensitivity report sweeping correlation thresholds to demonstrate robustness.

**Why this priority**: Visualizations validate the data quality, and sensitivity analysis ensures the findings are not artifacts of arbitrary cutoffs.

**Independent Test**: Can be fully tested by verifying that plot files are generated in the output directory and the sensitivity report contains results for the specified threshold set.

**Acceptance Scenarios**:

1. **Given** analysis results are available, **When** the reporting module runs, **Then** it produces a PNG time-series overlay, scatter plot, and spatial anomaly map.
2. **Given** a correlation threshold is defined, **When** sensitivity analysis runs, **Then** it reports correlation stability and confidence interval overlap for thresholds ∈ {0.4, 0.5, 0.6}.

---

### Edge Cases

- What happens when GRACE-FO satellite maintenance causes missing months? (System skips missing months and logs a warning; analysis proceeds with available data).
- How does system handle zero AR events in a specific month? (System excludes months with zero intensity from the correlation calculation to avoid division by zero or bias).
- What happens if the signal is null (correlation < 0.1)? (System reports the null result with p-value and confidence intervals; does not force a positive finding).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST ingest GRACE-FO Level-2 mascon solutions covering the West Coast North America region (35°N-50°N, 120°W-125°W) with ≥ 90% data completeness (See US-1).
- **FR-002**: System MUST ingest NOAA CPC Atmospheric River Catalog data and aggregate Integrated Water Vapor Transport to monthly resolution (See US-1).
- **FR-003**: System MUST apply standard GRACE-FO preprocessing: low-degree coefficient correction, degree-2 C20 replacement, and appropriate spatial Gaussian smoothing (See US-1).
- **FR-004**: System MUST compute Pearson correlation coefficients between AR intensity and gravity anomalies across multiple time lags, apply bootstrap resampling (1000 iterations, seed=42) to estimate 95% confidence intervals, and report signal magnitude relative to GRACE-FO measurement noise floor (≥ 3σ threshold) (See US-2).
- **FR-005**: System MUST apply multiple-comparison correction (e.g., Bonferroni or FDR) to all lag-test p-values to control family-wise error rate (See US-2).
- **FR-006**: System MUST perform sensitivity analysis sweeping correlation thresholds across a range of values and report correlation coefficient stability and confidence interval overlap variations (See US-3).
- **FR-007**: System MUST frame all statistical findings as associational, explicitly avoiding causal language in output reports. Output reports must not contain the following keywords: causes, effect, impact, driven by, leads to, triggers (See US-2).
- **FR-008**: System MUST validate signal against control regions (geographic areas without significant AR activity) and report the difference in correlation coefficients between target and control regions (See US-2).
- **FR-009**: System MUST document temporal aggregation bias assessment and provide justification for monthly resolution choice versus sub-monthly alternatives (See US-2).

### Key Entities

- **AR Event**: Represents an atmospheric river occurrence with attributes for date, peak intensity (IWV transport), and geographic footprint (bounding box defined as lat/lon polygon coordinates).
- **Gravity Anomaly**: Represents monthly GRACE-FO mascon values for the study region with attributes for date, geoid height anomaly at satellite altitude (m), and uncertainty.
- **Correlation Result**: Represents the statistical output with attributes for lag, correlation coefficient, raw p-value, corrected p-value, bootstrap confidence interval (95%), and significance flag.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Data ingestion completeness is measured against the total available monthly mascons in the study period with ≥ 90% completeness threshold (See US-1).
- **SC-002**: Correlation is deemed statistically significant when p < 0.05 after multiple-testing correction (See US-2).
- **SC-003**: Sensitivity analysis coverage is measured against the defined threshold set {0.4, 0.5, 0.6} (See US-3).
- **SC-004**: Runtime is measured against GitHub Actions CI job limit of ≤ 6 hours on 2 CPU cores, 7 GB RAM (See US-1).

## Assumptions

- Public data APIs (NOAA CPC Atmospheric River Catalog, GRACE-FO CSR/JPL) remain accessible without authentication during the CI job.
- Analysis runtime completes within 6 hours on a GitHub Actions free-tier runner (2 CPU cores, ~7 GB RAM).
- GRACE-FO Level-2 mascon solutions are available at the specified regional resolution without requiring custom spherical harmonic processing beyond standard smoothing.
- Observational design precludes causal inference claims; all results are reported as associations. Causal language (causes, effect, impact, driven by, leads to, triggers) MUST NOT appear in any output reports.
- No GPU or CUDA accelerators are available; all statistical computations must use CPU-tractable methods (e.g., scipy, statsmodels).
- Gravity anomaly refers to geoid height anomaly at satellite altitude, not geoid height at Earth's surface or gravitational acceleration.
- Monthly temporal aggregation is justified for this study; any temporal aggregation bias will be documented per FR-009.

## Constitution

### Principle VII - Statistical Threshold Determination

Statistical significance thresholds (e.g., p < 0.05) and effect size thresholds (e.g., Pearson > 0.5) MUST NOT be pre-specified as success criteria before analysis. Thresholds must be determined by statistical power calculations appropriate to the sample size and expected effect size. Bootstrap resampling (1000 iterations, seed=42) MUST be applied to correlation coefficients to estimate confidence intervals. This prevents circular validation where 'success' is defined by achieving a specific effect size without power analysis.