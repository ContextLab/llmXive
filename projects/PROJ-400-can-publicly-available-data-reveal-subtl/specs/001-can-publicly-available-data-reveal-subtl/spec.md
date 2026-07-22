# Feature Specification: Can Publicly Available Data Reveal Subtle Violations of Time-Reversal Symmetry in Beta Decay?

**Feature Branch**: `001-t-violation-beta-decay`  
**Created**: 2026-07-22  
**Status**: Draft  
**Input**: User description: "Can Publicly Available Data Reveal Subtle Violations of Time-Reversal Symmetry in Beta Decay? (Physics)"

## User Scenarios & Testing

### User Story 1 - Archival Data Retrieval and Validation (Priority: P1)

The researcher MUST be able to retrieve *published* T-violation D-coefficients, their uncertainties, and experimental conditions for specific nuclei (e.g., $^{6}$He, $^{19}$Ne) from the 2024 Particle Data Group (PDG) Review and primary literature, and validate that the data format supports meta-analysis.

**Why this priority**: This is the foundational step; without retrieving the fundamental observables (D-coefficients) required for the proposed meta-analysis, no analysis can occur. This step also validates the feasibility of the approach by confirming the existence of sufficient published data.

**Independent Test**: Can be fully tested by executing the data extraction script against the 2024 PDG Review and primary literature sources and verifying the output contains D-coefficients with uncertainties for a target nucleus.

**Acceptance Scenarios**:

1. **Given** a target nucleus (e.g., $^{6}$He) exists in the 2024 PDG Review with D-coefficient data, **When** the extraction script queries the database, **Then** the script retrieves the D-coefficient value and its standard error.
2. **Given** multiple published measurements for the same nucleus, **When** the validation process runs, **Then** the system confirms each dataset contains the necessary metadata (value, uncertainty, source reference) to perform the meta-analysis.
3. **Given** a target nucleus where no D-coefficient is reported in the 2024 PDG Review or primary literature, **When** the script processes it, **Then** the script flags the nucleus as "insufficient data" and excludes it from the analysis, reporting the limitation explicitly.

---

### User Story 2 - Cross-Study Meta-Analysis (Priority: P2)

The system MUST perform a meta-analysis by treating extracted D-coefficients from independent experiments as samples of an underlying parameter, calculating a weighted mean estimator (inverse-variance weighting), and performing heterogeneity assessment (Cochran's $Q$ and $I^2$) to determine if the datasets are consistent with a null hypothesis ($D=0$).

**Why this priority**: This is the core scientific analysis. It directly addresses the research question by testing the hypothesis that archival data reveals T-violation via the proposed meta-analysis method, while correctly framing findings as associational limits derived from independent measurements.

**Independent Test**: Can be fully tested by running the statistical analysis module on a mock dataset with known injected means and variances, verifying that the weighted mean calculation matches the analytical expectation and that the heterogeneity statistics ($Q, I^2$) are computed correctly for the input variance structure.

**Acceptance Scenarios**:

1. **Given** a harmonized dataset of D-coefficients for a single nucleus from multiple experiments, **When** the meta-analysis algorithm runs, **Then** the system calculates the inverse-variance weighted mean of the coefficients and reports the value with its standard error.
2. **Given** the set of independent measurements, **When** the heterogeneity assessment runs, **Then** the system calculates Cochran's $Q$ statistic and the $I^2$ index, reporting whether the variation is consistent with statistical noise or indicates unmodeled systematics.
3. **Given** the weighted mean and its standard error, **When** the upper bound calculation runs (assuming the null is not rejected), **Then** the system outputs a 95% confidence interval upper bound on $|D|$ derived strictly from the profile likelihood of the combined dataset.

---

### User Story 3 - Sensitivity Validation and PDG Comparison (Priority: P3)

The system MUST calculate the sensitivity limit of the derived bound for each nucleus and compare it against the best single-experiment sensitivity and the 2024 Particle Data Group (PDG) review limits to validate the results.

**Why this priority**: This ensures the scientific rigor of the results by quantifying the precision of the meta-analysis method and benchmarking it against established constraints.

**Independent Test**: Can be fully tested by running the validation module on the processed data and verifying the generation of a sensitivity limit (per nucleus) and a comparison table against the 2024 PDG Review.

**Acceptance Scenarios**:

1. **Given** the derived upper bound for a nucleus, **When** the sensitivity analysis runs, **Then** the system calculates the sensitivity limit as the standard error of the weighted mean of measurements for *that specific nucleus*.
2. **Given** the derived upper bound, **When** the validation step runs, **Then** the system cross-references the result with the 2024 PDG review and flags if the new bound is looser than the current world average.
3. **Given** the derived sensitivity limit, **When** the benchmarking runs, **Then** the system compares the meta-analysis sensitivity against the best single-experiment sensitivity in the set.

---

### Edge Cases

- What happens when the NNDC ENSDF database or 2024 PDG Review is temporarily unavailable or returns a 404 error for a specific nucleus? (System must retry a limited number of times with exponential backoff, then log the failure and proceed with available nuclei).
- How does the system handle nuclei where the D-coefficient is reported as a range rather than a point estimate? (System must use the midpoint for calculation and propagate the range width as the uncertainty, or exclude if the range is too wide).
- What happens if the meta-analysis results in a p-value exactly equal to 0 or 1 due to floating-point precision limits? (System must clamp values to [1e-10, 1-1e-10] and log a warning. If the clamped p-value is used for the final conclusion, the system MUST report the bound but flag the result as "inconclusive due to numerical precision" and exclude it from the final meta-analysis average).
- How does the system handle a nucleus with only a single published measurement? (System must skip the heterogeneity check and report the single measurement's result and uncertainty directly, noting the lack of statistical power for fusion).
- What happens if the archival data is strictly binned aggregates with no event-level covariance information? (System must flag the dataset as "invalid for meta-analysis" and exclude it, preventing the generation of a statistical artifact).

## Requirements

### Functional Requirements

- **FR-001**: System MUST retrieve *published* T-violation D-coefficients, their uncertainties, and experimental conditions for specified nuclei (e.g., $^{6}$He, $^{19}$Ne) from the 2024 Particle Data Group (PDG) Review and primary literature, ensuring data is aligned by nuclear state and source experiment. (See US-1)
- **FR-002**: System MUST compute an inverse-variance weighted mean estimator for the extracted D-coefficients to serve as the primary meta-analysis statistic, explicitly treating the input measurements as independent samples of an underlying physical parameter. (See US-2)
- **FR-003**: System MUST calculate Cochran's $Q$ statistic and the $I^2$ index to quantify heterogeneity across the independent datasets, determining if the variation is consistent with a single null hypothesis ($D=0$). (See US-2)
- **FR-004**: System MUST validate the feasibility of the meta-analysis by checking for the presence of D-coefficients with uncertainties; if only raw spectra without derived D-coefficients are available, the system MUST flag the dataset as "invalid for meta-analysis" and exclude it from the analysis. (See US-1)
- **FR-005**: System MUST calculate the 95% confidence interval upper bound on $|D|$ using the profile likelihood method on the combined dataset (Gaussian likelihood on the weighted mean, parameterized by central value D and uncertainty sigma) if the null hypothesis is not rejected. (See US-2)
- **FR-006**: System MUST validate the derived upper bounds by cross-referencing them with the 2024 Particle Data Group (PDG) Review limits and flag any results that are looser than the current world average. (See US-3)
- **FR-007**: System MUST perform a leave-one-out cross-validation to determine the influence of individual experiments on the final bound, where influence is defined as the absolute change in the 95% CI upper bound magnitude when an experiment is excluded. A change >10% triggers a 'high influence' flag. (See US-2)
- **FR-008**: System MUST extract D-coefficients, uncertainties, and experimental conditions from the text/tables of published papers (via the extraction script) as the primary input, ensuring no derivation from raw spectra is attempted. (See US-1)

### Key Entities

- **Nucleus**: Represents a specific atomic nucleus (e.g., $^{6}$He) with attributes: `name`, `mass_number`, `experimental_conditions`.
- **PublishedDValue**: Represents a published D-coefficient measurement, with attributes: `value`, `uncertainty`, `source_experiment`, `reference_id`, `publication_year`.
- **MetaAnalysisResult**: Represents the statistical output of the data fusion analysis, with attributes: `nucleus_id`, `weighted_mean_estimate`, `combined_standard_error`, `cochran_Q`, `I_squared`, `upper_bound_95_CI`, `sensitivity_limit`.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The derived 95% confidence interval upper bound on $|D|$ for each nucleus is measured against the constraints reported in the 2024 Particle Data Group (PDG) Review for the same nucleus. (See US-3)
- **SC-002**: The heterogeneity statistics ($Q, I^2$) are measured against the degrees of freedom (number of experiments minus one) to determine if the assumption of a single underlying parameter is statistically valid. The assumption is valid ONLY if p-value(Cochran's Q) ≥ 0.05 AND I² ≤ 50%. (See US-2)
- **SC-003**: The sensitivity limit of the meta-analysis method is measured against the best single-experiment sensitivity in the set to verify if the meta-analysis improves precision. (See US-3)
- **SC-004**: The influence of individual experiments is measured by comparing the full meta-analysis bound against the bound derived after excluding each experiment individually (leave-one-out). Influence is quantified as the absolute change in the 95% CI upper bound magnitude. (See US-2)
- **SC-005**: The data retrieval coverage is measured against the total number of requested nuclei in the target list {6He, 19Ne}, requiring retrieval of all available D-coefficients (flagging those where data is missing). (See US-1)

## Assumptions

- The 2024 Particle Data Group (PDG) Review and primary literature are accessible via public interfaces for the duration of the analysis, and the data format remains stable.
- The archival data for the selected nuclei ($^{6}$He, $^{19}$Ne) contains sufficient *published* D-coefficients with uncertainties to attempt the meta-analysis.
- The published measurements of the D-coefficients are independent and their uncertainties are correctly reported.
- The D-coefficient is a specific triple-correlation term ($\vec{\sigma} \cdot (\vec{p}_e \times \vec{p}_\nu)$) that cannot be derived from raw momentum spectra and polarization asymmetries alone without the neutrino momentum vector. Therefore, the system relies exclusively on *published* D-coefficients derived from triple-correlation analyses in the source papers.
- The Standard Model prediction for the T-violation D-coefficient is effectively zero, serving as the null hypothesis baseline.
- If no D-coefficient is reported for a nucleus in the 2024 PDG Review or primary literature, the meta-analysis method is invalid for that dataset, and the system will correctly identify and flag this limitation.
- The meta-analysis approach (inverse-variance weighting) is computationally feasible within the allocated runtime for the dataset size.
- All results are derived exclusively from real *published* D-coefficients retrieved from the 2024 PDG Review or primary literature; no simulated, hardcoded, or placeholder values are used in the final analysis. If data retrieval fails, the result is flagged as "insufficient data" rather than imputed.
- The analysis assumes no significant systematic bias common to all archival experiments for a given nucleus, as this cannot be corrected without raw event-level data.