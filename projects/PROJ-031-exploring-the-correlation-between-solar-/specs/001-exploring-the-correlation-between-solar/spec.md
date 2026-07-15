# Feature Specification: Exploring the Correlation Between Solar Flare Characteristics and Geomagnetic Storm Intensities

**Feature Branch**: `001-solar-flare-storm-correlation`  
**Created**: 2024-01-15  
**Status**: Draft  
**Input**: User description: "To what extent do solar flare X-ray peak flux and associated coronal mass ejection (CME) speeds correlate with the minimum Dst index of subsequent geomagnetic storms, and can this relationship define a predictive threshold for severe space weather events?"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Ingestion and Event Alignment (Priority: P1)

The research pipeline MUST download solar eruption data (GOES X-ray flares, SOHO/LASCO CMEs) and geomagnetic storm indices (NOAA Dst), then align them to create a unified dataset where **all** Dst minima (storms) are identified first, and then matched to preceding solar activity within a ≤3-day window. Events with missing solar predictors MUST be included in the dataset with missing data flags, not excluded. **Matching** explicitly includes the case of "no match found" (resulting in a null flag for the solar predictor) rather than requiring a match to exist.

**Why this priority**: Without aligned event data, no statistical analysis can proceed. This is the foundational data layer that all subsequent analysis depends on. Crucially, identifying storms independently of solar activity prevents circular selection bias.

**Independent Test**: Can be fully tested by verifying that the pipeline successfully downloads all available historical events, produces a CSV with aligned timestamps for flare class, CME speed, and Dst minimum values, and correctly flags events with missing predictors without excluding them from the primary dataset.

**Acceptance Scenarios**:

1. **Given** the NOAA SWPC FTP server and CDAWeb are accessible, **When** the pipeline executes, **Then** all available flare/CME/dst data from the past 10 years are downloaded and stored locally
2. **Given** a Dst minimum exists, **When** the pipeline filters for preceding flares and CMEs within ≤3 days, **Then** the output dataset includes the storm event regardless of whether a matching solar event is found, flagging missing predictors appropriately

---

### User Story 2 - Statistical Correlation Analysis (Priority: P2)

The system MUST compute Spearman rank correlation coefficients between (a) X-ray flare class (log10-transformed to W/m²) and Dst minimum, and (b) CME speed and Dst minimum, along with linear regression modeling to estimate variance explained (R²) as a first-order approximation. The system MUST also calculate the Variance Inflation Factor (VIF) to assess collinearity between predictors. If VIF > 5, the system MUST switch to separate univariate models or Ridge regression. The system MUST also perform a post-hoc power analysis using a pre-specified effect size of r=0.30 (based on Zhang et al., 2020, Space Weather, 18, e2019SW002345) to estimate the minimum detectable effect size; if the effective sample size (N) is <30, the system MUST log a power limitation warning and defer definitive threshold claims.

**Why this priority**: This directly answers the research question about which predictor (flare class vs. CME speed) has stronger correlation with geomagnetic intensity. This is the core analytical output.

**Independent Test**: Can be fully tested by running the correlation analysis on a known subset of events and verifying that correlation coefficients, p-values, R² values, and VIF scores are computed and output correctly, regardless of the statistical significance of the results.

**Acceptance Scenarios**:

1. **Given** the aligned event dataset exists, **When** Spearman correlation is computed, **Then** correlation coefficients and p-values are output for both predictor-outcome pairs (flare→Dst, CME→Dst)
2. **Given** multiple hypothesis tests are performed, **When** the analysis completes, **Then** a multiple-comparison correction (e.g., Bonferroni or Benjamini-Hochberg) is applied to control family-wise error rate at α≤0.05
3. **Given** linear regression is run, **When** the model completes, **Then** the system outputs R² and VIF values, explicitly labeling the model as a first-order approximation and applying fallback logic if VIF > 5

---

### User Story 3 - Threshold Identification and Sensitivity Analysis (Priority: P3)

The system MUST attempt to identify predictive thresholds (e.g., CME speed > 1000 km/s) where severe storm probability increases, using a hold-out validation set to prevent overfitting. The hold-out set MUST be strictly the last two years of data (e.g., the most recent available period) to ensure the threshold was not derived from the validation period. It MUST perform a sensitivity analysis sweeping the cutoff over a range of high-velocity thresholds (step size 100 km/s) and report how detection rates (True Positive Rate) vary on the validation set.

**Why this priority**: This provides the practical predictive value for space weather forecasting. The sensitivity analysis ensures the threshold is not arbitrarily chosen and demonstrates robustness. The hold-out set ensures validation metrics are not training artifacts.

**Independent Test**: Can be fully tested by verifying that the system attempts to identify thresholds, reports if none meet significance criteria, and computes detection rates for cutoffs in {900, 1000, 1100} km/s on a separate validation subset (last 2 years).

**Acceptance Scenarios**:

1. **Given** the correlation analysis, **When** the system attempts to identify thresholds, **Then** it reports a candidate threshold with justification OR explicitly states no significant threshold was found
2. **Given** a threshold is proposed, **When** the sensitivity sweep executes, **Then** detection rates (True Positive Rate) are computed for cutoffs in {900, 1000, 1100} km/s on the hold-out set and variation is documented
3. **Given** a threshold is proposed, **When** justification is required, **Then** the threshold cites a community-standard basis (e.g., "severe storm" definition from NOAA SWPC Dst≤-100 nT) with a specific citation to the NOAA SWPC definition document

---

### Edge Cases

- What happens when a flare has no associated CME (or vice versa)? → Events are included in the dataset; the missing predictor is flagged as missing data and excluded only from the specific paired calculation, not the overall analysis.
- How does the system handle missing data (e.g., CME speed unavailable for fast events)? → Missing values trigger a data-quality flag; the event is retained in the dataset with a null value for the missing field.
- What if the 3-day temporal window yields too few events for statistical power? → Pipeline logs power limitation and defers to larger dataset or extended window, documenting the limitation in the output.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download GOES X-ray flare lists from NOAA SWPC FTP (`ftp://ftp.swpc.noaa.gov/pub/lists/`) covering ≥10 years of historical data (See US-1)
- **FR-002**: System MUST retrieve CME catalog data (speed, width, direction) from CDAWeb SOHO/LASCO database (See US-1)
- **FR-003**: System MUST download geomagnetic storm indices (Dst, Kp) from NOAA SWPC for temporal alignment with flare/CME events (See US-1)
- **FR-004**: System MUST compute Spearman rank correlation coefficients between flare class (log10-transformed to W/m²)→Dst and CME speed→Dst with p-values for statistical significance (See US-2)
- **FR-005**: System MUST apply multiple-comparison correction (Bonferroni or Benjamini-Hochberg) to control family-wise error rate at α≤0.05 across all hypothesis tests (See US-2)
- **FR-006**: System MUST perform linear regression modeling to estimate variance explained (R²) by CME speed versus flare intensity (transformed to log10(W/m²)) as separate predictors, explicitly framing the model as a first-order approximation and calculating the Variance Inflation Factor (VIF) to assess collinearity. **If VIF > 5, the system MUST switch to separate univariate models or Ridge regression.** (See US-2)
- **FR-007**: System MUST identify candidate predictive thresholds for severe storms (Dst≤ nT) with explicit justification citing the specific NOAA SWPC definition document (See US-3)
- **FR-008**: System MUST sweep identified thresholds over 900, 1000, and 1100 km/s (step size 100 km/s) and report variation in detection rates (True Positive Rate) (See US-3)
- **FR-009**: System MUST frame all findings as ASSOCIATIONAL (not causal) in output documentation, specifically in `results/metrics.json`, `README.md`, and any generated reports (See US-2)
- **FR-010**: System MUST run on CPU-only hardware without GPU/CUDA requirements, fitting within ≤7 GB RAM and ≤6 h execution time (See US-1, US-2, US-3)
- **FR-011**: System MUST implement a hold-out validation strategy using a **time-series split (train on events from 2010-2020, test on events from 2021-2023)** to separate threshold discovery from validation, ensuring detection rates are computed on unseen data (See US-3)
- **FR-012**: System MUST measure and report execution time and peak RAM usage to `results/metrics.json` to verify FR-010 constraints (See US-1, US-2, US-3)
- **FR-013**: System MUST validate aligned events against `contracts/aligned_event.schema.yaml` and metrics against `contracts/metrics.schema.yaml` (See US-1, US-3)
- **FR-014**: If the linear regression R² is < 0.1, the system MUST test a non-linear (piecewise) model and report the improvement in fit (See US-2)

### Key Entities *(include if feature involves data)*

- **SolarFlareEvent**: Represents a GOES X-ray flare with attributes (timestamp, X-ray peak flux class, location, log10_flux)
- **CMEEvent**: Represents a SOHO/LASCO coronal mass ejection with attributes (timestamp, speed km/s, width, direction)
- **GeomagneticStorm**: Represents a Dst-indexed storm event with attributes (timestamp, Dst minimum nT, Kp index)
- **AlignedEvent**: Composite entity linking flare, CME, and storm within ≤3-day temporal window, including flags for missing data

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: System outputs a JSON object containing correlation coefficients for both predictors and a boolean flag indicating which predictor has the higher absolute coefficient value (See US-2)
- **SC-002**: Statistical significance (p-value) for each correlation coefficient is measured against α≤0.05 threshold with multiple-comparison correction applied (See US-2)
- **SC-003**: Threshold sensitivity is measured by detection rate variation (True Positive Rate) across 900, 1000, and 1100 km/s cutoffs on the hold-out set (last 2 years) to assess robustness (See US-3)
- **SC-004**: Computational feasibility is measured by total execution time ≤6 h on CPU-only GitHub Actions runner with ≤7 GB RAM, reported in `results/metrics.json` (See US-1, US-2, US-3)

## Assumptions

- GOES X-ray flare lists, SOHO/LASCO CME catalog, and NOAA Dst indices are publicly accessible via the specified FTP/CDAWeb endpoints without authentication. **HuggingFace 'Verified datasets' are explicitly identified as irrelevant for solar physics (containing NLP/legal text) and are NOT used; the pipeline relies on direct NOAA/CDAWeb ingestion as the primary strategy.**
- The dataset contains all required variables (X-ray peak flux, CME speed, Dst minimum) for the analysis; if any variable is missing from a source, the event is retained with a missing data flag rather than excluded.
- Severe geomagnetic storm is defined by a significant negative excursion in the Dst index (NOAA SWPC community standard) for threshold analysis, citing the specific NOAA SWPC definition document.
- The 3-day temporal window for flare-CME-storm alignment is sufficient to capture causally relevant events; if event counts are too low, power limitation is documented.
- All measurements use validated instruments (GOES satellites, SOHO/LASCO, ground magnetometers) with citable validation from the related work section.
- Any collinearity between flare class and CME speed (e.g., more energetic flares tend to produce faster CMEs) is tested via variance inflation factor (VIF) and if present (VIF > 5), joint relationships are framed descriptively or handled via univariate/Ridge regression.
- The CDAWeb SOHO/LASCO catalog contains high coverage of speed data for fast CMEs (>500 km/s) but may have gaps for slow events; the pipeline MUST include events with missing speed data and report the exclusion count as a data-quality metric (See US-1).
- The analysis MUST include only non-recurrent storms (defined as distinct minima separated by ≥24 hours of recovery) to ensure independence of samples; recurrent activity periods MUST be flagged and excluded from the primary correlation analysis (See US-2).
- The pipeline MUST perform a post-hoc power analysis (target power ≥0.8, α≤0.05) on the collected dataset to estimate the minimum detectable effect size using a **pre-specified effect size of r=0.30 (based on Zhang et al., 2020, Space Weather, 18, e2019SW002345)**; if the effective sample size (N) is <30, the system MUST log a power limitation warning and defer definitive threshold claims (See US-2).
- Standard network utilities (e.g., curl, wget) or HTTP libraries are available in the execution environment to support data retrieval (See FR-002).