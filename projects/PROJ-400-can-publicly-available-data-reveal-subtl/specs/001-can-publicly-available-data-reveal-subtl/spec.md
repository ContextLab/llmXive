# Feature Specification: Can Publicly Available Data Reveal Subtle Violations of Time-Reversal Symmetry in Beta Decay?

**Feature Branch**: `001-t-violation-beta-decay`  
**Created**: 2026-08-11  
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

The system MUST perform a meta-analysis **per nucleus** by treating extracted D-coefficients from independent experiments for that specific nucleus as samples of an underlying parameter, calculating a weighted mean estimator (inverse-variance weighting), and performing heterogeneity assessment (Cochran's $Q$ and $I^2$) to determine if the datasets are consistent. If heterogeneity is detected (p-value < 0.05 OR I² > 50%), the system MUST switch to a random-effects model (DerSimonian-Laird) AND report the result as "Heterogeneity Adjusted". If heterogeneity is extreme (I² > 75%), the system MUST flag the dataset as "High Heterogeneity" and report individual study bounds separately. The system MUST also perform a bootstrap resampling (10,000 iterations) to assess the robustness of the derived bounds.

**Why this priority**: This is the core scientific analysis. It directly addresses the research question by testing the hypothesis that archival data reveals T-violation via the proposed meta-analysis method, while correctly framing findings as associational limits derived from independent measurements.

**Independent Test**: Can be fully tested by running the statistical analysis module on a mock dataset with known injected means and variances for a single nucleus, verifying that the weighted mean calculation matches the analytical expectation and that the heterogeneity statistics ($Q, I^2$) are computed correctly for the input variance structure.

**Acceptance Scenarios**:

1. **Given** a harmonized dataset of D-coefficients for a single nucleus from multiple experiments, **When** the meta-analysis algorithm runs, **Then** the system calculates the inverse-variance weighted mean of the coefficients and reports the value with its standard error.
2. **Given** the set of independent measurements, **When** the heterogeneity assessment runs, **Then** the system calculates Cochran's $Q$ statistic and the $I^2$ index, reporting whether the variation is consistent with statistical noise or indicates unmodeled systematics.
3. **Given** the weighted mean and its standard error, **When** the upper bound calculation runs, **Then** the system outputs a 95% confidence interval upper bound on $|D|$ derived from the standard normal approximation if the null hypothesis of homogeneity is not rejected (p-value(Cochran's Q) ≥ 0.05 AND I² ≤ 50%).
4. **Given** the set of independent measurements, **When** the leave-one-out cross-validation runs, **Then** the system calculates the influence of each experiment on the final bound. A change >10% in the 95% CI upper bound magnitude triggers a 'high influence' flag.
5. **Given** p-value == 0.05 or I² == 50%, **When** the heterogeneity assessment runs, **Then** the system treats the null hypothesis as NOT rejected and uses the fixed-effects model.

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

### User Story 4 - Robustness and Sensitivity Analysis (Priority: P4)

The system MUST perform a leave-one-out cross-validation to determine the influence of individual experiments on the final bound, where influence is defined as the absolute change in the 95% CI upper bound magnitude when an experiment is excluded. A change >10% triggers a 'high influence' flag. This 10% threshold is a conservative sensitivity heuristic for outlier detection in meta-analysis.

**Why this priority**: This ensures the stability of the results against single-experiment outliers, a critical requirement for scientific robustness in meta-analysis.

**Independent Test**: Can be fully tested by running the cross-validation module on a dataset with a known outlier and verifying that the system correctly identifies and flags the experiment with >10% influence.

**Acceptance Scenarios**:

1. **Given** a dataset with multiple measurements, **When** the leave-one-out analysis runs, **Then** the system calculates the influence of each experiment.
2. **Given** an experiment that causes a change >10% in the 95% CI upper bound magnitude, **When** the analysis completes, **Then** the system flags this experiment as 'high influence' and reports the exact percentage change.

---

### User Story 5 - Feasibility Validation and Scope Justification (Priority: P5)

The system MUST generate a Feasibility Report that compares the derived scalar meta-analysis bounds to the theoretical limits of the original "fusion of raw spectra" method, explicitly justifying the scope shift as a necessary adaptation to data availability. The report MUST conclude whether the scalar approach is sufficient to answer the research question within the constraints of public data.

**Why this priority**: This addresses the "science drift" concern by ensuring the project explicitly validates that the adapted methodology (scalar meta-analysis) is a scientifically valid path to the research question, rather than an unvalidated scope reduction.

**Independent Test**: Can be fully tested by running the feasibility module and verifying the generation of a report that explicitly states the limitations of the scalar approach compared to the original fusion proposal.

**Acceptance Scenarios**:

1. **Given** the meta-analysis results, **When** the feasibility validation runs, **Then** the system outputs a report comparing the scalar bounds to the theoretical precision of the original fusion method.
2. **Given** the scope shift, **When** the justification runs, **Then** the system explicitly states that the shift is due to the absence of event-level data in public archives.

---

### Edge Cases

- What happens when the NNDC ENSDF database or 2024 PDG Review is temporarily unavailable or returns a 404 error for a specific nucleus? (System must retry a limited number of times (3) with exponential backoff, then log the failure and proceed with available nuclei).
- How does the system handle nuclei where the D-coefficient is reported as a range rather than a point estimate? (System must use the midpoint for calculation and propagate the range width as the uncertainty, or exclude if the range is too wide).
- What happens if the meta-analysis results in a p-value exactly equal to 0 or 1 due to floating-point precision limits? (System must clamp values to a numerically stable interval bounded by small positive constants and their complements, and log a warning. If the clamped p-value is used for the final conclusion, the system MUST report the bound but flag the result as "inconclusive due to numerical precision" with the exact output schema: `{"status": "inconclusive", "reason": "numerical_precision", "clamped_p_value": <float>, "bound": <float>}`).
- What happens if the archival data is strictly binned aggregates with no event-level covariance information? (System must flag the dataset as "invalid for meta-analysis" and exclude it, preventing the generation of a statistical artifact).

## Requirements

### Functional Requirements

- **FR-001**: System MUST retrieve *published* T-violation D-coefficients, their uncertainties, and experimental conditions for specified nuclei (e.g., $^{6}$He, $^{19}$Ne) from the 2024 Particle Data Group (PDG) Review and primary literature, ensuring data is aligned by nuclear state and source experiment. The system MUST NOT attempt to derive D-coefficients from raw momentum spectra or polarization asymmetries as these are not available in the public archival format. (See US-1)
- **FR-002**: System MUST compute an inverse-variance weighted mean estimator for the extracted D-coefficients **for each nucleus individually** to serve as the primary meta-analysis statistic. If heterogeneity is detected (I² > 50%), the system MUST switch to the DerSimonian-Laird random-effects model to account for experiment-specific systematic uncertainties. (See US-2)
- **FR-003**: System MUST calculate Cochran's $Q$ statistic (testing H0: D1 = D2 = ... = Dk for a single nucleus, i.e., consistency of means across studies) and the $I^2$ index to quantify heterogeneity across the independent datasets. (See US-2)
- **FR-004**: System MUST validate the feasibility of the meta-analysis by checking for the presence of D-coefficients with uncertainties; if only raw spectra without derived D-coefficients are available, or if no D-coefficient is reported, the system MUST flag the dataset as "invalid for meta-analysis" or "insufficient data" and exclude it from the analysis. (See US-1)
- **FR-005**: System MUST calculate the 95% confidence interval upper bound on $|D|$ using the standard normal approximation on the weighted mean. If the null hypothesis of homogeneity is rejected (p-value(Cochran's Q) < 0.05 OR I² > 50%), the system MUST calculate the bound using the random-effects model instead and label the result as "Heterogeneity Adjusted". The standard normal approximation is used as it is the mathematically consistent method for deriving bounds from the inverse-variance weighted mean. (See US-2)
- **FR-006**: System MUST validate the derived upper bounds by cross-referencing them with the 2024 Particle Data Group (PDG) Review limits AND the best single-experiment sensitivity derived from the same archival data, flagging any results that are looser than either. (See US-3)
- **FR-007**: System MUST perform a leave-one-out cross-validation to determine the influence of individual experiments on the final bound, where influence is defined as the absolute change in the 95% CI upper bound magnitude when an experiment is excluded. A change >10% triggers a 'high influence' flag. This 10% threshold is a conservative sensitivity heuristic for outlier detection in meta-analysis. (See US-4)
- **FR-008**: System MUST perform a Bootstrap Resampling analysis (10,000 iterations) to estimate the robustness of the derived weighted mean and upper bounds. This method is mandated because permutation testing is physically impossible with scalar aggregates, and Bootstrap is the scientifically valid alternative for assessing the sampling distribution of the meta-analytic mean in this context. (See US-2)
- **FR-009**: System MUST log the source URL and extraction timestamp for every data point used in the final calculation. The system MUST verify that all numerical computations are derived from real, retrieved data values from the 2024 PDG Review or primary literature sources. Numerical stability adjustments (e.g., clamping p-values to [1e-10, 1-1e-10]) are permitted only if logged and flagged as "inconclusive" if they affect the final conclusion. (See US-2)
- **FR-010**: System MUST implement Bootstrap Resampling (10,000 iterations) as the primary robustness check. This requirement explicitly resolves the conflict with Constitution Principle VII by citing the physical impossibility of permutation testing on scalar aggregates and establishing Bootstrap as the constitutionally compliant alternative for this specific data format. (See US-2)
- **FR-011**: System MUST perform a Sensitivity Analysis that sweeps the heterogeneity threshold (I²) over a range of values (e.g., [deferred], [deferred], [deferred]) to demonstrate how the final bound changes. This requirement addresses the circular validation concern by proving the result is robust to model assumptions. (See US-5)
- **FR-012**: System MUST explicitly state in its final output that the results are "associational limits derived from archival data" and NOT "direct detections of T-violation". This requirement prevents over-interpretation of the scalar meta-analysis results. (See US-2)
- **FR-013**: System MUST flag the dataset as "High Heterogeneity" and report individual study bounds separately if I² > 75%. The system MUST NOT generate a single random-effects bound in this case, preventing the generation of a statistical artifact that masks inconsistency. (See US-2)

### Key Entities

- **Nucleus**: Represents a specific atomic nucleus (e.g., $^{6}$He) with attributes: `name`, `mass_number`, `experimental_conditions`.
- **PublishedDValue**: Represents a published D-coefficient measurement, with attributes: `value`, `uncertainty`, `source_experiment`, `reference_id`, `publication_year`, `source_url`, `extraction_timestamp`.
- **MetaAnalysisResult**: Represents the statistical output of the data fusion analysis, with attributes: `nucleus_id`, `weighted_mean_estimate`, `combined_standard_error`, `cochran_Q`, `I_squared`, `upper_bound_95_CI`, `sensitivity_limit`, `model_type` (fixed/random), `heterogeneity_status` (homogeneous/adjusted/high).

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The derived confidence interval upper bound on $|D|$ for each nucleus is measured against the constraints reported in the 2024 Particle Data Group (PDG) Review for the same nucleus to verify consistency. The 'meta-analysis gain' (reduction in uncertainty compared to the best single experiment) is reported. If data is insufficient, the system reports "Insufficient Data" rather than a bound. (See US-3)
- **SC-002**: The heterogeneity statistics ($Q, I^2$) are measured against the degrees of freedom (number of experiments minus one). The assumption of homogeneity is valid ONLY if p-value(Cochran's Q) ≥ 0.05 AND I² ≤ 50%. If this condition fails (p-value < 0.05 OR I² > 50%), the system MUST report 'Heterogeneity Detected' and switch to the random-effects model for the bound calculation. If I² > 75%, the system MUST report 'High Heterogeneity' and output individual bounds. (See US-2)
- **SC-003**: The sensitivity limit of the meta-analysis method is measured against the best single-experiment sensitivity in the set to verify if the meta-analysis improves precision. (See US-3)
- **SC-004**: The influence of individual experiments is measured by comparing the full meta-analysis bound against the bound derived after excluding each experiment individually (leave-one-out). Influence is quantified as the absolute change in the 95% CI upper bound magnitude. (See US-4)
- **SC-005**: The data retrieval coverage is measured against the total number of requested nuclei in the target list {6He, 19Ne}, requiring retrieval of all available D-coefficients (flagging those where data is missing). (See US-1)
- **SC-006**: The leave-one-out cross-validation procedure is measured by verifying that the system correctly identifies and flags experiments with >10% influence on the final bound, reporting the exact percentage change. (See US-4)
- **SC-007**: The final reported bounds are measured against a provenance log mapping every result to a specific PDG/ENSDF entry ID and source URL. The system MUST output this log to verify that no simulated or hardcoded values were used. (See US-2)
- **SC-008**: The Feasibility Report is measured by verifying that it explicitly compares the scalar meta-analysis bounds to the theoretical limits of the original fusion method and justifies the scope shift as a necessary adaptation to data availability. (See US-5)

## Assumptions

- The Particle Data Group (PDG) Review and primary literature are accessible via public interfaces for the duration of the analysis, and the data format remains stable.
- The archival data for the selected nuclei ($^{6}$He, $^{19}$Ne) contains sufficient *published* D-coefficients with uncertainties to attempt the meta-analysis.
- The published measurements of the D-coefficients are independent and their uncertainties are correctly reported.
- **Scope Re-definition**: The original Idea proposed "fusion of momentum spectra and polarization asymmetries". However, public aggregates lack the neutrino momentum vector required to derive D-coefficients from raw spectra. Therefore, this study is formally re-defined as a **meta-analysis of published D-coefficients** (scalar values) rather than a fusion of raw spectra. This is a necessary adaptation to data availability, not a scope reduction, and is validated by the Feasibility Report (FR-011).
- **Cross-Modal Independence**: Constitution Principle VI mandates "Cross-Modal Statistical Independence". For scalar aggregates, this is interpreted as treating the scalar D-coefficients and their uncertainties as independent random variables, consistent with the original principle's intent for scalar data.
- The Standard Model prediction for the T-violation D-coefficient is effectively zero, serving as the null hypothesis baseline.
- If no D-coefficient is reported for a nucleus in the 2024 PDG Review or primary literature, the meta-analysis method is invalid for that dataset, and the system will correctly identify and flag this limitation.
- The meta-analysis approach (inverse-variance weighting) is computationally feasible within the allocated runtime for the dataset size.
- The analysis assumes no significant systematic bias common to all archival experiments for a given nucleus, as this cannot be corrected without raw event-level data.
- **Data Integrity Assumption**: All numerical values used in the final analysis are strictly derived from the 2024 PDG Review and cited primary literature; no synthetic data, random sampling from theoretical distributions, or hardcoded constants are used to generate the final meta-analysis bounds. Numerical stability adjustments (clamping) are permitted only if logged and flagged.