# Feature Specification: Exploring the Correlation Between Solar Flare Characteristics and Geomagnetic Storm Intensities

**Feature Branch**: `001-solar-flare-storm-correlation`  
**Created**: 2024-01-15  
**Status**: Draft  
**Input**: User description: "To what extent do solar flare X-ray peak flux and associated coronal mass ejection (CME) speeds correlate with the minimum Dst index of subsequent geomagnetic storms, and can this relationship define a predictive threshold for severe space weather events?"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Ingestion and Event Alignment (Priority: P1)

The research pipeline MUST download and align solar eruption data (GOES X-ray flares, SOHO/LASCO CMEs) with geomagnetic storm indices (NOAA Dst) to create a unified event dataset where flares and CMEs precede storms by ≤3 days.

**Why this priority**: Without aligned event data, no statistical analysis can proceed. This is the foundational data layer that all subsequent analysis depends on.

**Independent Test**: Can be fully tested by verifying that the pipeline successfully downloads ≥100 historical events and produces a CSV with aligned timestamps for flare class, CME speed, and Dst minimum values.

**Acceptance Scenarios**:

1. **Given** the NOAA SWPC FTP server is accessible, **When** the pipeline executes, **Then** at least 100 flare-CME-storm events from the past 10 years are downloaded and stored locally
2. **Given** a flare timestamp exists, **When** the pipeline filters for CMEs and storms within ≤3 days, **Then** the output dataset contains only events meeting this temporal constraint

---

### User Story 2 - Statistical Correlation Analysis (Priority: P2)

The system MUST compute Spearman rank correlation coefficients between (a) X-ray flare class and Dst minimum, and (b) CME speed and Dst minimum, along with linear regression modeling to estimate predictive variance.

**Why this priority**: This directly answers the research question about which predictor (flare class vs. CME speed) has stronger correlation with geomagnetic intensity. This is the core analytical output.

**Independent Test**: Can be fully tested by running the correlation analysis on a known subset of events and verifying that correlation coefficients are computed with p-values ≤0.05 for statistically significant relationships.

**Acceptance Scenarios**:

1. **Given** the aligned event dataset exists, **When** Spearman correlation is computed, **Then** correlation coefficients and p-values are output for both predictor-outcome pairs (flare→Dst, CME→Dst)
2. **Given** multiple hypothesis tests are performed, **When** the analysis completes, **Then** a multiple-comparison correction (e.g., Bonferroni or Benjamini-Hochberg) is applied to control family-wise error rate at α≤0.05

---

### User Story 3 - Threshold Identification and Sensitivity Analysis (Priority: P3)

The system MUST identify predictive thresholds (e.g., CME speed > 1000 km/s) where severe storm probability increases, and perform a sensitivity analysis sweeping the cutoff over {900, 1000, 1100} km/s to report how detection rates vary.

**Why this priority**: This provides the practical predictive value for space weather forecasting. The sensitivity analysis ensures the threshold is not arbitrarily chosen and demonstrates robustness.

**Independent Test**: Can be fully tested by verifying that threshold detection rates (true positive/false positive) are computed for at least 3 different cutoff values and reported in the output.

**Acceptance Scenarios**:

1. **Given** the correlation analysis identifies a candidate threshold, **When** the sensitivity sweep executes, **Then** detection rates are computed for cutoffs in {900, 1000, 1100} km/s and variation is documented
2. **Given** a threshold is proposed, **When** justification is required, **Then** the threshold cites a community-standard basis (e.g., "severe storm" definition from NOAA SWPC Dst≤-100 nT)

---

### Edge Cases

- What happens when a flare has no associated CME (or vice versa)? → Events are excluded from paired analysis; unpaired events are flagged in diagnostics
- How does the system handle missing data (e.g., CME speed unavailable for fast events)? → Missing values trigger imputation flag or exclusion with count reported
- What if the 3-day temporal window yields too few events for statistical power? → Pipeline logs power limitation and defers to larger dataset or extended window

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download GOES X-ray flare lists from NOAA SWPC FTP (`ftp://ftp.swpc.noaa.gov/pub/lists/`) covering ≥10 years of historical data (See US-1)
- **FR-002**: System MUST download CME catalog data (speed, width, direction) from CDAWeb SOHO/LASCO database via wget (See US-1)
- **FR-003**: System MUST download geomagnetic storm indices (Dst, Kp) from NOAA SWPC for temporal alignment with flare/CME events (See US-1)
- **FR-004**: System MUST compute Spearman rank correlation coefficients between flare class→Dst and CME speed→Dst with p-values for statistical significance (See US-2)
- **FR-005**: System MUST apply multiple-comparison correction (Bonferroni or Benjamini-Hochberg) to control family-wise error rate at α≤0.05 across all hypothesis tests (See US-2)
- **FR-006**: System MUST perform linear regression modeling to estimate variance explained (R²) by CME speed versus flare intensity as separate predictors (See US-2)
- **FR-007**: System MUST identify candidate predictive thresholds for severe storms (Dst≤-100 nT) with explicit justification citing community-standard basis (See US-3)
- **FR-008**: System MUST sweep identified thresholds over {900, 1000, 1100} km/s (absolute diff ∈ {100}) and report variation in detection rates (See US-3)
- **FR-009**: System MUST frame all findings as ASSOCIATIONAL (not causal) in output documentation since the design is observational without randomization (See US-2)
- **FR-010**: System MUST run on CPU-only hardware without GPU/CUDA requirements, fitting within ≤7 GB RAM and ≤6 h execution time (See US-1, US-2, US-3)

### Key Entities *(include if feature involves data)*

- **SolarFlareEvent**: Represents a GOES X-ray flare with attributes (timestamp, X-ray peak flux class, location)
- **CMEEvent**: Represents a SOHO/LASCO coronal mass ejection with attributes (timestamp, speed km/s, width, direction)
- **GeomagneticStorm**: Represents a Dst-indexed storm event with attributes (timestamp, Dst minimum nT, Kp index)
- **AlignedEvent**: Composite entity linking flare, CME, and storm within ≤3-day temporal window

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Correlation strength between CME speed and Dst minimum is measured against the flare-class→Dst correlation to determine dominant predictor (See US-2)
- **SC-002**: Statistical significance (p-value) for each correlation coefficient is measured against α≤0.05 threshold with multiple-comparison correction applied (See US-2)
- **SC-003**: Threshold sensitivity is measured by detection rate variation across {900, 1000, 1100} km/s cutoffs to assess robustness (See US-3)
- **SC-004**: Computational feasibility is measured by total execution time ≤6 h on CPU-only GitHub Actions runner with ≤7 GB RAM (See US-1, US-2, US-3)

## Assumptions

- GOES X-ray flare lists, SOHO/LASCO CME catalog, and NOAA Dst indices are publicly accessible via the specified FTP/CDAWeb endpoints without authentication
- The dataset contains all required variables (X-ray peak flux, CME speed, Dst minimum) for the analysis; if any variable is missing from a source, the event is excluded rather than imputed
- Severe geomagnetic storm is defined by Dst≤-100 nT (NOAA SWPC community standard) for threshold analysis
- The 3-day temporal window for flare-CME-storm alignment is sufficient to capture causally relevant events; if event counts are too low, power limitation is documented
- All measurements use validated instruments (GOES satellites, SOHO/LASCO, ground magnetometers) with citable validation from the related work section
- Any collinearity between flare class and CME speed (e.g., more energetic flares tend to produce faster CMEs) is tested via variance inflation factor (VIF) and if present, joint relationships are framed descriptively rather than as independent predictive effects
- [NEEDS CLARIFICATION: Does the CDAWeb SOHO/LASCO catalog contain complete CME speed data for all events matching the GOES flare list, or will significant event exclusion be required?]
- [NEEDS CLARIFICATION: Should the analysis include only non-recurrent storms, or are recurrent geomagnetic activity periods acceptable for the correlation analysis?]
- [NEEDS CLARIFICATION: What is the minimum sample size required for adequate statistical power given the expected effect size, or is this to be determined post-hoc?]
