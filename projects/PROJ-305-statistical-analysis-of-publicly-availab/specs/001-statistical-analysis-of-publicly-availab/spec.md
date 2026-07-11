# Feature Specification: Statistical Analysis of Publicly Available COVID-19 Vaccine Adverse Event Reports

**Feature Branch**: `001-covid-vaccine-signal-detection`  
**Created**: 2026-07-05  
**Status**: Draft  
**Input**: User description: "Statistical Analysis of Publicly Available COVID-19 Vaccine Adverse Event Reports"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1)

The system MUST download, clean, and merge VAERS datasets for both COVID-19 and non-COVID vaccines across recent reporting years., mapping raw MedDRA codes to System Organ Classes (SOCs) to create a unified analysis-ready dataset.

**Why this priority**: Without a clean, merged, and categorized dataset, no statistical analysis can be performed. This is the foundational data layer required for all subsequent signal detection.

**Independent Test**: The pipeline can be fully tested by running the ingestion script on a small, synthetic subset of VAERS data and verifying that the output CSV contains correctly mapped SOCs, distinct vaccine type flags, and no duplicate or malformed records.

**Acceptance Scenarios**:

1. **Given** raw VAERS CSV files for 2020-2023, **When** the ingestion script runs, **Then** the output file contains a unified table with columns for `VAX_TYPE`, `SOC_CODE`, `SOC_NAME`, and `REPORT_DATE`, filtering out records with missing critical fields.
2. **Given** a raw MedDRA code (e.g., 10007541), **When** the mapping logic executes, **Then** the record is correctly assigned to the corresponding System Organ Class (e.g., "Cardiac disorders") based on the provided MedDRA hierarchy.
3. **Given** a dataset exceeding 7GB in raw size, **When** the processing runs on a 7GB RAM environment, **Then** the script processes the data in chunks or streams to prevent memory overflow, completing within 6 hours.

---

### User Story 2 - Disproportionality Signal Detection (Priority: P2)

The system MUST calculate Reporting Odds Ratio (ROR), Proportional Reporting Ratio (PRR), and Information Component (IC) for every System Organ Class comparing COVID-19 vaccines against non-COVID vaccines, applying Benjamini-Hochberg correction for multiple comparisons.

**Why this priority**: This is the core statistical engine of the project. It directly addresses the research question by quantifying the association between vaccine types and adverse event frequencies.

**Independent Test**: The analysis can be tested by running the calculation module on a static, pre-computed contingency table and verifying that the output ROR, PRR, and IC values match manual calculations or known benchmarks within an acceptable tolerance.

**Acceptance Scenarios**:

1. **Given** a contingency table of COVID-19 vs. Non-COVID reports for a specific SOC, **When** the ROR function executes, **Then** the output includes the point estimate, 95% confidence interval, and a flag indicating if the lower bound > 1.0.
2. **Given** a list of 20+ SOCs tested simultaneously, **When** the Benjamini-Hochberg correction is applied, **Then** the adjusted p-values are calculated correctly to control the False Discovery Rate at α=0.05.
3. **Given** a specific SOC with zero events in the control group, **When** the PRR calculation runs, **Then** the system handles the division-by-zero edge case by returning a defined infinity value or skipping the metric with a logged warning, rather than crashing.

---

### User Story 3 - Temporal Clustering and Visualization (Priority: P3)

The system MUST perform time-series analysis on the top candidate SOCs using Poisson regression to detect temporal clustering within the first 14-30 days post-vaccination and generate forest plots visualizing the results. The system MUST compare observed rates to background rates *only if* such rates are available in reference literature; otherwise, it MUST rely on the internal non-COVID baseline.

**Why this priority**: While the disproportionality metrics identify *what* is associated, the temporal analysis determines *when* the signals occur, distinguishing acute reactions from background noise. Visualization is required for human interpretation.

**Independent Test**: The visualization module can be tested by feeding it a static set of ROR values and confidence intervals and verifying that the generated PDF/PNG forest plot correctly displays the point estimates and error bars for a representative subset of SOCs.

**Acceptance Scenarios**:

1. **Given** weekly reporting counts for a candidate SOC, **When** the Poisson regression model runs, **Then** the output includes a p-value for the temporal trend and identifies if significant clustering (p < 0.05) occurs within the 14-30 day window, without requiring a specific 'peak' location.
2. **Given** a set of validated signals (consistent across ≥2 metrics), **When** the forest plot is generated, **Then** the plot displays the ROR point estimate with 95% CI for each signal, clearly distinguishing those with lower bounds > 1.0.
3. **Given** a comparison against background incidence rates (if available), **When** the contextualization step runs, **Then** the output report includes a table comparing the observed VAERS rate to the established background rate for each signal. If no background rate is available, the system MUST mark the comparison as 'N/A' and proceed with internal baseline analysis only.

### Edge Cases

- **What happens when** a specific MedDRA code is missing from the current hierarchy version? The system MUST log a warning and exclude that record from SOC aggregation rather than failing the entire pipeline.
- **How does the system handle** a scenario where the non-COVID control group has zero reports for a specific rare SOC? The system MUST flag this as "insufficient data" for that specific metric and exclude it from the primary signal list, preventing false positives from division by zero.
- **What happens when** the background incidence rate for a specific event is unavailable in the reference literature? The system MUST mark that specific comparison as 'N/A' in the output report and proceed with the internal ROR/PRR analysis only, ensuring the Poisson regression (which relies on internal counts) continues unaffected.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and parse VAERS datasets (2020-2023) from the official source, filtering for `VAX_TYPE` to separate COVID-19 and non-COVID reports (See US-1).
- **FR-002**: System MUST map raw MedDRA codes to System Organ Classes (SOCs) using the official MedDRA hierarchy to reduce dimensionality (See US-1).
- **FR-003**: System MUST calculate Reporting Odds Ratio (ROR) with 95% confidence intervals for every SOC comparing COVID-19 vs. non-COVID vaccines (See US-2).
- **FR-004**: System MUST calculate Proportional Reporting Ratio (PRR) and Information Component (IC) as alternative estimators for all SOCs to support robustness checks (See US-2).
- **FR-005**: System MUST apply Benjamini-Hochberg correction to all calculated p-values to control the False Discovery Rate across multiple SOC tests (See US-2).
- **FR-006**: System MUST identify signals as "positive" only if the ROR lower 95% CI bound > 1.0 AND the signal is consistent across at least two of the three metrics (ROR, PRR, IC), where PRR requires a lower 95% CI > 1.0 and IC requires a lower 95% CI > 0. This multi-metric consistency is required per FDA/EMA pharmacovigilance conventions to ensure robustness against metric-specific anomalies (See US-3).
- **FR-007**: System MUST perform Poisson regression on weekly reporting counts for top candidate SOCs to detect temporal clustering within 14-30 days post-vaccination (See US-3).
- **FR-008**: System MUST generate a forest plot visualization of the top 20 candidate signals with 95% confidence intervals. If background incidence rates are available in reference literature, the system SHOULD include them in the visualization; otherwise, it MUST omit the comparison (See US-3).
- **FR-009**: System MUST execute all data processing and statistical modeling within a peak memory limit of ≤ 7GB and a total runtime of ≤ 6 hours on a CPU-only environment (See US-1, US-2, US-3).
- **FR-010**: System MUST perform a control-group time-series comparison (comparing COVID-19 reporting trends against non-COVID reporting trends over the same time window) to distinguish biological signals from general reporting artifacts (See US-3).

### Key Entities

- **VAERS_Report**: Represents a single adverse event report, containing attributes for vaccine type, date, and MedDRA codes.
- **SOC_Cluster**: Represents a System Organ Class aggregation, containing the count of reports for COVID-19 and non-COVID vaccines, and calculated statistical metrics.
- **Signal_Candidate**: Represents a validated statistical signal, containing the SOC name, ROR/PRR/IC values, p-values, and temporal cluster status.

## Success Criteria

### Measurable Outcomes

- **SC-001**: At least ≥ 95% of SOCs present in the merged dataset must have valid ROR calculations (non-zero denominator) (See US-2).
- **SC-002**: The system MUST correctly implement the Benjamini-Hochberg procedure such that the theoretical False Discovery Rate is controlled at ≤ 0.05 for the set of identified signals (See US-2).
- **SC-003**: The system MUST correctly calculate temporal clustering significance (p-values) such that when tested against synthetic data with known clusters, it identifies the cluster with p < 0.05 (See US-3).
- **SC-004**: The memory usage peak during the full pipeline execution is measured against the 7GB RAM constraint to ensure feasibility on free-tier CI (See US-1).
- **SC-005**: The total runtime of the end-to-end analysis is measured against the 6-hour limit to ensure compatibility with GitHub Actions free-tier jobs (See US-1).

## Assumptions

- **Assumption about data availability**: The VAERS public datasets for 2020-2023 contain sufficient granularity (VAX_TYPE and MedDRA codes) to perform the required separation and mapping. If specific years lack required fields, the analysis will be restricted to the available years.
- **Assumption about background rates**: Published background incidence rates for the specific System Organ Classes of interest are available in the referenced CDC/NCIRD literature or peer-reviewed sources. If a specific SOC lacks a background rate, the analysis will rely solely on the internal non-COVID vaccine baseline.
- **Assumption about computational load**: The aggregated dataset, after grouping by SOC and filtering for the 2020-2023 window, will fit within 7GB of RAM. If the raw data exceeds this, the system assumes chunked processing or sampling will be sufficient without biasing the ROR/PRR calculations.
- **Assumption about methodological framing**: The analysis is strictly observational; all findings regarding associations between vaccine types and adverse events will be framed as associational (disproportionality) rather than causal, consistent with the limitations of spontaneous reporting systems.
- **Assumption about threshold justification**: The ROR lower bound threshold of > 1.0 and the requirement for consistency across ≥2 metrics are based on standard pharmacovigilance practices (e.g., FDA/EMA guidelines) to balance sensitivity and specificity.
- **Assumption about multiple testing**: The number of System Organ Classes is small enough that the Benjamini-Hochberg correction will effectively control the FDR without overly penalizing statistical power.