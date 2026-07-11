# Feature Specification: Statistical Analysis of Publicly Available COVID-19 Vaccine Adverse Event Reports

**Feature Branch**: `001-statistical-analysis-covid-vaers`  
**Created**: 2026-07-05  
**Status**: Draft  
**Input**: User description: "Statistical Analysis of Publicly Available COVID-19 Vaccine Adverse Event Reports"

## User Scenarios & Testing

### User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1)

The system must successfully download, clean, and merge the VAERS 2020-2023 datasets (COVID-19 and non-COVID) and filter them by vaccine type to prepare for analysis.

**Why this priority**: This is the foundational step; without clean, filtered data, no statistical analysis can be performed. It represents the Minimum Viable Product (MVP) for data readiness.

**Independent Test**: The pipeline can be run end-to-end on a CPU-only environment, outputting a consolidated CSV file containing only valid records with `VAX_TYPE` classified as "COVID-19" or "Non-COVID" and valid MedDRA-coded adverse events.

**Acceptance Scenarios**:

1. **Given** the VAERS 2020-2023 raw data files are available at the specified URL, **When** the download and extraction script runs, **Then** the local storage contains the extracted CSV files with no corruption.
2. **Given** the raw data files, **When** the cleaning script filters for `VAX_TYPE` and removes records with missing MedDRA codes, **Then** the output dataset contains only records with a valid `VAX_TYPE` classification and a non-empty `SOC` field.
3. **Given** the merged dataset, **When** the script validates the output, **Then** the output file is a valid CSV with a row count > 0 and all required columns (`VAX_TYPE`, `SOC`, `REPT_DATE`) are populated.

---

### User Story 2 - Disproportionality Signal Detection (Priority: P2)

The system must calculate Reporting Odds Ratio (ROR), Proportional Reporting Ratio (PRR), and Information Component (IC) for each System Organ Class (SOC) comparing COVID-19 vaccines to non-COVID vaccines, and perform a sensitivity analysis against a Flu-only baseline.

**Why this priority**: This is the core analytical engine. It directly addresses the research question by identifying potential safety signals. It is independent of the temporal analysis.

**Independent Test**: The analysis script produces a table of metrics (ROR, PRR, IC) and 95% confidence intervals for every SOC, where the calculation logic is verifiable against the 2x2 contingency tables derived from the preprocessed data.

**Acceptance Scenarios**:

1. **Given** the preprocessed dataset with COVID-19 and non-COVID groups, **When** the ROR calculation runs, **Then** the output includes an ROR value and a lower 95% confidence bound for every SOC with at least 5 reported events in the COVID-19 group.
2. **Given** the same dataset, **When** the PRR and IC metrics are computed, **Then** the output table contains finite, non-NaN, non-Infinity positive numbers for all three metrics for every SOC with ≥ 5 total reports.
3. **Given** the computed metrics, **When** the system identifies signals, **Then** a signal is flagged if it meets the threshold criteria (ROR > 2.0, lower 95% CI > 1.0; PRR > 1.5, lower 95% CI > 1.0; IC > 0, lower 95% CI > 0) in at least two of the three metrics.
4. **Given** the computed metrics for the 'Non-COVID' baseline, **When** the sensitivity analysis runs against a 'Flu-only' baseline, **Then** the system outputs a comparison table showing the delta in ROR/PRR/IC values for the top 5 candidate signals to assess robustness against confounding.

---

### User Story 3 - Descriptive Temporal Profile (Priority: P3)

The system must generate a descriptive weekly reporting profile for top candidate SOCs to identify reporting spikes, acknowledging the limitation that vaccination dates are unavailable.

**Why this priority**: This adds a layer of descriptive context to the signal detection by checking for temporal patterns in reporting, refining the initial P1/P2 findings. It is explicitly non-causal due to data limitations.

**Independent Test**: The script generates a time-series plot for top SOCs showing weekly counts relative to the median report date of the cohort.

**Acceptance Scenarios**:

1. **Given** the top 5 candidate SOCs identified in User Story 2, **When** the temporal profile analysis runs, **Then** the output includes a weekly count plot relative to the group median report date, explicitly labeled as 'Reporting Time' and not 'Post-Vaccination Time'.
2. **Given** the list of all tested SOCs, **When** the Benjamini-Hochberg correction is applied to the cross-sectional metrics, **Then** the final output list contains only SOCs with an adjusted p-value < 0.05.
3. **Given** the ROR, PRR, and IC results, **When** the consistency check runs, **Then** a signal is included in the final report only if it meets the threshold criteria in at least two of the three metrics.

### Edge Cases

- **Zero-Count Events**: What happens when a specific SOC has zero reports in the non-COVID group? The system must apply a standard continuity correction (e.g., adding a small constant) to the contingency table to allow ROR calculation without division by zero.
- **Missing Background Rates**: How does the system handle SOCs where no published background incidence rate exists? The system must flag these SOCs as "Background Rate Unknown" in the final report. This is a known limitation of the VAERS dataset which lacks denominator data; the analysis is strictly limited to 'Reporting Disproportionality' and cannot calculate 'Incidence Rates'.
- **Sparse Data**: How does the system handle SOCs with very few total reports (e.g., < 5)? The system must exclude these SOCs from the disproportionality analysis to prevent statistical noise from generating false positives.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and parse VAERS 2020-2023 datasets, filtering records by `VAX_TYPE` to separate COVID-19 and non-COVID groups, ensuring all MedDRA codes are mapped to System Organ Classes (SOC) (See US-1).
- **FR-002**: System MUST calculate the Reporting Odds Ratio (ROR), Proportional Reporting Ratio (PRR), and Information Component (IC) for each SOC with ≥ 5 total reports using 2x2 contingency tables derived from the filtered data (See US-2).
- **FR-003**: System MUST apply the Benjamini-Hochberg procedure to control the false discovery rate (FDR) across all SOC tests for the cross-sectional ROR/PRR/IC metrics, outputting adjusted p-values for every metric (See US-3).
- **FR-004**: System MUST generate a descriptive weekly reporting profile for the top 5 candidate SOCs, aggregating counts relative to the median report date of the cohort, and explicitly label this analysis as 'Reporting Time' (not 'Post-Vaccination Time') to acknowledge the absence of `VACCINATION_DATE` data (See US-3).
- **FR-005**: System MUST validate a safety signal only if it meets the threshold criteria (ROR > 2.0, lower 95% CI > 1.0; PRR > 1.5, lower 95% CI > 1.0; IC > 0, lower 95% CI > 0) in at least two of the three disproportionality metrics (ROR, PRR, IC) (See US-2).
- **FR-006**: System MUST execute the entire analysis pipeline on a CPU-only environment with memory usage optimized to remain under 7 GB RAM, avoiding any GPU-dependent libraries (See US-1).
- **FR-007**: System MUST perform a sensitivity analysis comparing the 'Non-COVID' baseline (all other vaccines) against a 'Flu-only' baseline (VAX_TYPE contains 'Influenza') for the top 5 candidate signals, outputting the delta in metrics to assess robustness against confounding (See US-2).

### Key Entities

- **Report**: A single adverse event entry containing `VAX_TYPE`, `SOC`, `REPT_DATE`, and `AGE`.
- **Signal**: A specific SOC identified as having a statistically significant disproportionality, characterized by ROR, PRR, IC values, and an adjusted p-value.
- **Contingency Table**: A 2x2 matrix representing the counts of (Event/No Event) vs. (COVID-19/Non-COVID) for a specific SOC.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The proportion of SOCs with valid ROR, PRR, and IC calculations (finite, non-NaN, non-Infinity) must be ≥ 95% of the total number of unique SOCs that meet the minimum sample size (≥ 5 reports) (See US-2).
- **SC-002**: The implementation of the Benjamini-Hochberg correction MUST produce monotonically increasing adjusted p-values when sorted by raw p-value, verifying algorithmic correctness (See US-3).
- **SC-003**: The temporal profile analysis MUST successfully generate weekly count plots for the top 5 candidate signals relative to the group median report date (See US-3).
- **SC-004**: The memory footprint of the data processing pipeline is measured against the 7 GB RAM constraint of the target CI environment (See US-1).
- **SC-005**: [deferred] of reported signals MUST satisfy the 2-out-of-3 metrics validation rule defined in FR-005 (See US-2).

## Assumptions

- The VAERS 2020-2023 datasets are publicly available and downloadable via `wget` without authentication or rate-limiting that exceeds the 6-hour CI job limit.
- The MedDRA coding system in the VAERS data is consistent enough to allow aggregation into System Organ Classes (SOC) without requiring manual curation of every code.
- The background incidence rates for adverse events, if required for context, are available in the cited literature or CDC resources and can be hard-coded or fetched as static values rather than dynamic API calls.
- The relationship between vaccine type and adverse event reporting is observational; therefore, all findings will be framed as associational signals rather than causal evidence.
- The dataset size (after filtering for 2020-2023) will fit within the ~7 GB RAM constraint of the free-tier GitHub Actions runner without requiring complex chunking strategies.
- The "non-COVID" comparison group will include all other vaccine types reported in VAERS during the same period, assuming this provides a sufficient baseline for disproportionality analysis.
- **Flu-only Baseline**: The 'Flu-only' baseline for sensitivity analysis (FR-007) is defined as any record where `VAX_TYPE` contains the string "Influenza".
- **Temporal Limitation**: The dataset lacks `VACCINATION_DATE` for the vast majority of records; therefore, temporal analysis is limited to 'Reporting Time' relative to the median report date and cannot establish biological causality or post-vaccination clustering.