# Feature Specification: Can Publicly Available Data Reveal Subtle Violations of Time-Reversal Symmetry in Beta Decay?

**Feature Branch**: `001-t-violation-beta-decay`  
**Created**: 2026-07-14  
**Status**: Draft  
**Input**: User description: "Can Publicly Available Data Reveal Subtle Violations of Time-Reversal Symmetry in Beta Decay? (Physics)"

## User Scenarios & Testing

### User Story 1 - Archival Raw Data Retrieval and Validation (Priority: P1)

The researcher MUST be able to retrieve raw or semi-raw momentum spectra and polarization asymmetry coefficients for specific nuclei (e.g., 6He, 19Ne) from the NNDC ENSDF database and validate that the data format supports cross-modal covariance analysis.

**Why this priority**: This is the foundational step; without retrieving the fundamental observables required for the proposed fusion method, no analysis can occur. This step also validates the feasibility of the novel approach.

**Independent Test**: Can be fully tested by executing the data extraction script against the ENSDF API/website and verifying the output contains raw/semi-raw spectra or asymmetry coefficients (not just pre-calculated D-coefficients) for a target nucleus.

**Acceptance Scenarios**:

1. **Given** a target nucleus (e.g., 6He) exists in ENSDF with raw momentum/polarization data, **When** the extraction script queries the database, **Then** the script retrieves the momentum spectrum and polarization asymmetry values with their uncertainties.
2. **Given** multiple published measurements for the same nucleus, **When** the validation process runs, **Then** the system confirms each dataset contains the necessary modalities (momentum AND polarization) to perform the fusion.
3. **Given** a target nucleus where only pre-calculated D-coefficients are available (no raw data), **When** the script processes it, **Then** the script flags the nucleus as "fusion impossible" and excludes it from the fusion analysis, reporting the limitation explicitly.

---

### User Story 2 - Cross-Modal Data Fusion and Permutation Testing (Priority: P2)

The system MUST perform a cross-modal data fusion by computing the covariance matrix between momentum distribution and polarization coefficients for each nucleus, and use permutation testing (minimum 10,000 shuffles) to establish the null distribution and calculate a 95% confidence interval upper bound on the D-coefficient.

**Why this priority**: This is the core scientific analysis. It directly addresses the research question by testing the hypothesis that archival data can reveal T-violation via the proposed novel fusion method.

**Independent Test**: Can be fully tested by running the statistical analysis module on a mock dataset with known injected correlations, verifying the permutation p-value is stable (variance < 0.01) when the number of shuffles is doubled from [deferred] to [deferred].

**Acceptance Scenarios**:

1. **Given** a harmonized dataset of momentum spectra and polarization asymmetries for a single nucleus, **When** the fusion algorithm runs, **Then** the system calculates the cross-modal covariance matrix and derives the D-coefficient estimate.
2. **Given** the derived D-coefficient, **When** the permutation test runs (10,000 shuffles), **Then** the system generates a null distribution and calculates a p-value.
3. **Given** the p-value and D-estimate, **When** the bound calculation runs, **Then** the system outputs a 95% confidence interval upper bound (e.g., |D| < X) based on the 95th percentile of the null distribution.

---

### User Story 3 - Sensitivity Validation and PDG Comparison (Priority: P3)

The system MUST calculate the sensitivity limit of the derived bound for each nucleus and compare it against the best single-experiment sensitivity and the 2024 Particle Data Group (PDG) review limits to validate the results.

**Why this priority**: This ensures the scientific rigor of the results by quantifying the precision of the fusion method and benchmarking it against established constraints.

**Independent Test**: Can be fully tested by running the validation module on the processed data and verifying the generation of a sensitivity limit (per nucleus) and a comparison table against the 2024 PDG Review.

**Acceptance Scenarios**:

1. **Given** the derived D-coefficient bound for a nucleus, **When** the sensitivity analysis runs, **Then** the system calculates the sensitivity limit as the standard error of the weighted mean of measurements for *that specific nucleus*.
2. **Given** the derived upper bound, **When** the validation step runs, **Then** the system cross-references the result with the 2024 PDG review and flags if the new bound is looser than the current world average.
3. **Given** the derived sensitivity limit, **When** the benchmarking runs, **Then** the system compares the fusion sensitivity against the best single-experiment sensitivity in the set.

---

### Edge Cases

- What happens when the NNDC ENSDF database is temporarily unavailable or returns a 404 error for a specific nucleus? (System must retry a limited number of times with exponential backoff, then log the failure and proceed with available nuclei).
- How does the system handle nuclei where the raw data is reported as a range rather than a point estimate? (System must use the midpoint for calculation and propagate the range width as the uncertainty, or exclude if the range is too wide).
- What happens if the permutation test results in a p-value exactly equal to 0 or 1 due to floating-point precision limits? (System must clamp values to [e-10, 1-1e-10] and log a warning).
- How does the system handle a nucleus with only a single published measurement? (System must skip the permutation consistency check and report the single measurement's result and uncertainty directly, noting the lack of statistical power).
- What happens if the archival data is strictly binned aggregates with no event-level covariance information? (System must flag the dataset as "invalid for fusion" and exclude it, preventing the generation of a statistical artifact).

## Requirements

### Functional Requirements

- **FR-001**: System MUST retrieve raw or semi-raw beta decay energy/momentum spectra and polarization asymmetry coefficients for specified nuclei (e.g., 6He, 19Ne) from the NNDC ENSDF database, ensuring data is aligned by nuclear state and source experiment. (See US-1)
- **FR-002**: System MUST compute the cross-modal covariance matrix between the retrieved momentum distributions and polarization coefficients to derive the D-coefficient for each nucleus individually. (See US-2)
- **FR-003**: System MUST perform permutation testing with a minimum of 10,000 shuffles to generate the null distribution for the D-coefficient and calculate a 95% confidence interval upper bound. (See US-2)
- **FR-004**: System MUST validate the feasibility of the fusion by checking for the presence of event-level or sufficiently granular covariance information; if only binned aggregates are available, the system MUST flag the dataset as "invalid for fusion" and exclude it from the analysis. (See US-1)
- **FR-005**: System MUST calculate the sensitivity limit of the derived bound for each nucleus individually as the standard error of the weighted mean of measurements for that specific nucleus. (See US-3)
- **FR-006**: System MUST validate the derived upper bounds by cross-referencing them with the 2024 Particle Data Group (PDG) Review limits and flag any results that are looser than the current world average. (See US-3)

### Key Entities

- **Nucleus**: Represents a specific atomic nucleus (e.g., 6He) with attributes: `name`, `mass_number`, `experimental_conditions`.
- **RawObservable**: Represents a raw/semi-raw measurement (momentum spectrum or polarization asymmetry), with attributes: `value`, `uncertainty`, `modality_type`, `source_experiment`, `reference_id`.
- **FusionResult**: Represents the statistical output of the data fusion analysis, with attributes: `nucleus_id`, `d_coefficient_estimate`, `p_value_null`, `d_upper_bound_95`, `sensitivity_limit`.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The derived D-coefficient upper bound for each nucleus is measured against the constraints reported in the 2024 Particle Data Group (PDG) Review for the same nucleus. (See US-3)
- **SC-002**: The p-value from the permutation test is measured against the standard significance threshold of 0.05 to determine if the derived D-coefficient is statistically significant. (See US-2)
- **SC-003**: The sensitivity limit of the fusion method is measured against the best single-experiment sensitivity in the set to verify if the fusion improves precision. (See US-3)
- **SC-004**: The permutation test stability is measured by doubling the shuffles from [deferred] to [deferred] and verifying the p-value variance is < 0.01. (See US-2)
- **SC-005**: The data retrieval coverage is measured against the total number of requested nuclei in the target list {6He, 19Ne}, requiring [deferred] retrieval of all available raw/semi-raw datasets (flagging those where only aggregates exist). (See US-1)

## Assumptions

- The NNDC ENSDF database is accessible via its public interface or API for the duration of the analysis, and the data format remains stable.
- The archival data for the selected nuclei (6He, 19Ne) contains sufficient raw or semi-raw momentum and polarization data to attempt the cross-modal fusion.
- The published measurements of the raw observables are independent and their uncertainties are correctly reported.
- The cross-modal covariance method is theoretically capable of deriving the D-coefficient if the necessary event-level or granular data is available.
- The Standard Model prediction for the T-violation D-coefficient is effectively zero, serving as the null hypothesis baseline.
- If archival data is strictly binned aggregates, the fusion method is physically invalid for that dataset, and the system will correctly identify and flag this limitation.
- The permutation testing approach (10,000 shuffles) is computationally feasible within the allocated runtime for the dataset size.