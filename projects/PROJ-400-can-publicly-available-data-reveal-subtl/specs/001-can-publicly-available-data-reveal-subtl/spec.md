# Feature Specification: Can Publicly Available Data Reveal Subtle Violations of Time-Reversal Symmetry in Beta Decay?

**Feature Branch**: `001-t-violation-beta-decay`  
**Created**: 2026-07-14  
**Status**: Draft  
**Input**: User description: "Can Publicly Available Data Reveal Subtle Violations of Time-Reversal Symmetry in Beta Decay? (Physics)"

## User Scenarios & Testing

### User Story 1 - Archival Data Retrieval and Harmonization (Priority: P1)

The researcher MUST be able to retrieve published T-violation correlation coefficients (specifically the D-coefficient) and their associated uncertainties for specific nuclei (e.g., 6He, 19Ne) from the NNDC ENSDF database and harmonize them into a single dataset for meta-analysis.

**Why this priority**: This is the foundational step; without retrieving the existing published limits on T-violation, no meta-analysis or comparison can occur. It represents the minimum viable data pipeline.

**Independent Test**: Can be fully tested by executing the data extraction script against the ENSDF API/website and verifying the output CSV contains rows with D-coefficient values and uncertainties for a target nucleus, with no missing critical identifiers.

**Acceptance Scenarios**:

1. **Given** a target nucleus (e.g., 6He) exists in ENSDF with published D-coefficient data, **When** the extraction script queries the database, **Then** the script retrieves the D-coefficient value, its uncertainty, and the source experiment reference.
2. **Given** multiple published measurements for the same nucleus, **When** the harmonization process runs, **Then** the resulting dataset lists each measurement separately with its source, preserving the independence of the results.
3. **Given** a target nucleus with no published D-coefficient data, **When** the script processes it, **Then** the script flags the nucleus as "insufficient data" and excludes it from the meta-analysis without crashing.

---

### User Story 2 - Meta-Analysis and Upper Bound Calculation (Priority: P2)

The system MUST perform a weighted meta-analysis of the retrieved D-coefficients to calculate a combined upper bound on T-violation, properly propagating uncertainties and checking for consistency among the measurements.

**Why this priority**: This is the core scientific analysis. It directly addresses the research question by synthesizing independent measurements to determine if the combined data reveals a non-zero T-violation or establishes a tighter upper bound than individual experiments.

**Independent Test**: Can be fully tested by running the statistical analysis module on a mock dataset with known injected D-coefficients and uncertainties, verifying the calculated weighted average and combined uncertainty match the theoretical expectation within a defined tolerance.

**Acceptance Scenarios**:

1. **Given** a harmonized dataset of D-coefficients, **When** the meta-analysis runs, **Then** the system calculates the weighted average of the D-coefficients using inverse-variance weighting.
2. **Given** the combined D-coefficient and its uncertainty, **When** the upper bound calculation runs, **Then** the system outputs a 95% confidence interval upper bound (e.g., |D| < X) based on the combined result.
3. **Given** a dataset where the weighted average is statistically indistinguishable from zero, **When** the bound calculation runs, **Then** the system reports a null result with a quantified sensitivity limit (e.g., "Combined data limits D to < Y at [deferred] CL").

---

### User Story 3 - Consistency Testing and Sensitivity Validation (Priority: P3)

The system MUST perform a consistency test (Cochran's Q test) to check for heterogeneity among the published D-coefficients and calculate the sensitivity limit (experimental noise floor) of the combined dataset, validating results against known constraints from the Particle Data Group (PDG).

**Why this priority**: This ensures the scientific rigor of the results by verifying that the combined measurements are consistent (i.e., no hidden systematic errors or conflicting results) and quantifying the precision of the final bound.

**Independent Test**: Can be fully tested by running the validation module on the processed data and verifying the generation of a heterogeneity p-value (Cochran's Q), a sensitivity limit, and a comparison table against external PDG constraints.

**Acceptance Scenarios**:

1. **Given** multiple D-coefficient measurements, **When** the consistency test runs, **Then** the system calculates Cochran's Q statistic and the associated p-value to determine if the measurements are consistent (p > 0.05).
2. **Given** the combined dataset, **When** the sensitivity analysis runs, **Then** the system calculates the sensitivity limit as the inverse-variance weighted average of the individual uncertainties.
3. **Given** the derived upper bound, **When** the validation step runs, **Then** the system cross-references the result with the Particle Data Group (PDG) review and flags if the new bound is looser than the current world average.

---

### Edge Cases

- What happens when the NNDC ENSDF database is temporarily unavailable or returns a 404 error for a specific nucleus? (System must retry 3 times with exponential backoff, then log the failure and proceed with available nuclei).
- How does the system handle nuclei where the D-coefficient is reported as a range rather than a point estimate? (System must use the midpoint for calculation and propagate the range width as the uncertainty, or exclude if the range is too wide).
- What happens if the consistency test results in a p-value exactly equal to 0 or 1 due to floating-point precision limits? (System must clamp values to [1e-10, 1-1e-10] and log a warning).
- How does the system handle a nucleus with only a single published measurement? (System must skip the consistency test and report the single measurement's result and uncertainty directly).

## Requirements

### Functional Requirements

- **FR-001**: System MUST retrieve published T-violation D-coefficients and their uncertainties for specified nuclei (e.g., 6He, 19Ne) from the NNDC ENSDF database, ensuring data is aligned by nuclear state and source experiment. (See US-1)
- **FR-002**: System MUST perform a weighted meta-analysis of the retrieved D-coefficients using inverse-variance weighting to calculate a combined central value and uncertainty. (See US-2)
- **FR-003**: System MUST convert the combined D-coefficient result into a 95% confidence interval upper bound, reporting the result with explicit numerical limits. (See US-2)
- **FR-004**: System MUST perform a consistency test using Cochran's Q statistic with [deferred] shuffles (for p-value estimation if analytic solution is unavailable) to check for heterogeneity among the measurements. (See US-3)
- **FR-005**: System MUST calculate the sensitivity limit of the combined dataset as the inverse-variance weighted average of the individual uncertainties, representing the experimental noise floor. (See US-3)
- **FR-006**: System MUST validate the derived upper bounds by cross-referencing them with the Particle Data Group (PDG) review limits and flag any results that are looser than the current world average. (See US-3)

### Key Entities

- **Nucleus**: Represents a specific atomic nucleus (e.g., 6He) with attributes: `name`, `mass_number`, `experimental_conditions`.
- **DMeasurement**: Represents a published measurement of the D-coefficient, with attributes: `value`, `uncertainty`, `source_experiment`, `reference_id`.
- **MetaAnalysisResult**: Represents the statistical output of the fusion analysis, with attributes: `weighted_average`, `combined_uncertainty`, `p_value_heterogeneity`, `d_upper_bound`.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The combined D-coefficient upper bound is measured against the constraints reported in the Particle Data Group (PDG) review for the same nucleus. (See US-3)
- **SC-002**: The p-value from the Cochran's Q consistency test is measured against the standard significance threshold of 0.05 to determine if measurements are consistent. (See US-3)
- **SC-003**: The sensitivity limit (experimental noise floor) is measured against the weighted average of the individual measurement uncertainties to verify precision. (See US-3)
- **SC-004**: The meta-analysis accuracy is measured against a mock dataset with a known injected D-coefficient and uncertainties, verifying the result is within 1% relative error of the injected value. (See US-2)
- **SC-005**: The data retrieval success rate is measured against the total number of requested nuclei in the target list {6He, 19Ne}, targeting ≥ 90% successful retrievals for nuclei with available data. (See US-1)

## Assumptions

- The NNDC ENSDF database is accessible via its public interface or API for the duration of the analysis, and the data format remains stable.
- The archival data for the selected nuclei (6He, 19Ne) contains published D-coefficients or sufficient angular correlation parameters to derive them.
- The published measurements of the D-coefficient are independent and their uncertainties are correctly reported.
- The meta-analysis approach (inverse-variance weighting) is appropriate for combining these independent experimental results.
- The Standard Model prediction for the T-violation D-coefficient is effectively zero, serving as the null hypothesis baseline.
- The "data fusion" is a meta-analysis of published results, not a statistical correlation of raw spectra from different experiments.