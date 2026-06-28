# Feature Specification: Investigating the Impact of Early Life Stress on Hippocampal Subfield Volumes

**Feature Branch**: `001-gene-regulation`  
**Created**: 2025-01-15  
**Status**: Draft  
**Input**: User description: "Investigating the Impact of Early Life Stress on Hippocampal Subfield Volumes"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Acquisition and Pre-processing Pipeline (Priority: P1)

The system MUST acquire the ABCD Study Release 4.0 phenotypic and imaging data, then pre-process it to prepare for statistical analysis. This is foundational work without which no analysis can proceed.

**Why this priority**: Without properly acquired and cleaned data, no statistical modeling is possible. This is the prerequisite for all downstream analysis.

**Independent Test**: Can be fully tested by verifying that the pipeline successfully downloads the required CSV files, filters out participants with missing ACE scores or poor MRI quality flags, and outputs a pre-processed dataset file with normalized subfield volumes.

**Acceptance Scenarios**:

1. **Given** the ABCD Study Release 4.0 data is available at the specified URLs, **When** the data acquisition script runs, **Then** it downloads the phenotypic CSV and subcorticalSegmentationStats files within 30 minutes and stores them in the project's data directory.
2. **Given** the raw data contains participants with missing ACE scores or poor MRI quality flags, **When** the pre-processing script runs, **Then** it excludes these participants and outputs a filtered dataset with at least 80% of the original sample size.
3. **Given** subfield volumes (CA3, DG, subiculum) and intracranial volume (ICV) are available, **When** normalization runs, **Then** each subfield volume is divided by ICV and the normalized values are stored with a precision of ≥ 4 decimal places.

---

### User Story 2 - Statistical Modeling and Association Testing (Priority: P2)

The system MUST fit linear mixed-effects models for each hippocampal subfield to test associations between ACE scores and normalized subfield volumes, controlling for covariates.

**Why this priority**: This is the core research question - establishing the statistical relationship between early life stress and hippocampal subfield volumes.

**Independent Test**: Can be fully tested by running the modeling script on the pre-processed dataset and verifying that three separate model outputs (one per subfield) contain standardized β coefficients, 95% confidence intervals, and p-values.

**Acceptance Scenarios**:

1. **Given** a pre-processed dataset with ACE scores and normalized subfield volumes, **When** the statistical modeling script runs, **Then** it fits three separate linear mixed-effects models with the formula `subfield_vol ~ ACE_score + age + sex + scanner_site + (1|family_id)` and completes within 45 minutes.
2. **Given** three subfield models are fit, **When** p-values are extracted, **Then** both corrected p-values (Bonferroni-adjusted with threshold p < 0.05/3 = 0.0167) and uncorrected p-values are reported for each subfield.
3. **Given** the CA3 and DG subfield volumes, **When** the volume ratio is computed, **Then** the CA3:DG ratio is calculated as a continuous variable and tested for association with ACE scores using the same covariate set, with results stored separately from the individual subfield models.

---

### User Story 3 - Robustness Validation and Sensitivity Analysis (Priority: P3)

The system MUST perform robustness checks including non-parametric permutation tests and sensitivity analyses to verify that findings are not dependent on specific threshold choices or model assumptions.

**Why this priority**: While the primary analysis provides the main results, robustness checks validate the reliability of findings and address methodological concerns about threshold sensitivity.

**Independent Test**: Can be fully tested by running the robustness check script and verifying that permutation test results (5,000 permutations) and sensitivity analysis outputs are generated and stored separately from primary results.

**Acceptance Scenarios**:

1. **Given** the primary linear mixed-effects model results, **When** the permutation test runs with 5,000 permutations, **Then** it completes within 3 hours and outputs empirical p-values that agree with parametric p-values within ±0.02.
2. **Given** the CA3:DG ratio analysis, **When** sensitivity analysis runs, **Then** it sweeps the inconsistency tolerance threshold over {0.01, 0.05, 0.1} and reports how the false-positive rate varies across these thresholds in a summary table.
3. **Given** the full sample, **When** the restricted analysis runs, **Then** it repeats the primary analysis on participants with ICV within 1 standard deviation of the sample mean and outputs comparison statistics showing effect size changes ≤ 15%.

---

### Edge Cases

- What happens when the ABCD Study data download fails or returns an incomplete file?
- How does the system handle participants with extreme outlier ACE scores (>3 standard deviations from the mean)?
- What if the Freesurfer subfield segmentation fails for certain participants (missing volume data)?
- How does the system handle multicollinearity between covariates (e.g., age and scanner site correlation)?
- What if the permutation test exceeds the 6-hour runtime limit on GitHub Actions?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download the ABCD Study Release 4.0 phenotypic CSV and subcorticalSegmentationStats files from the official ABCD Study data portal and verify file integrity using MD5 checksums (See US-1)
- **FR-002**: System MUST exclude participants with missing ACE scores or poor MRI quality flags, retaining at least 80% of the original sample size after filtering (See US-1)
- **FR-003**: System MUST normalize each hippocampal subfield volume (CA3, DG, subiculum) by dividing by intracranial volume (ICV) to control for head size, storing results with ≥4 decimal precision (See US-1)
- **FR-004**: System MUST fit three separate linear mixed-effects models using the formula `subfield_vol ~ ACE_score + age + sex + scanner_site + (1|family_id)` for CA3, DG, and subiculum, completing within 45 minutes (See US-2)
- **FR-005**: System MUST apply Bonferroni correction for the three subfield tests with corrected significance threshold p < 0.0167 (0.05/3), reporting both corrected and uncorrected p-values (See US-2)
- **FR-006**: System MUST compute the CA3:DG volume ratio as a continuous variable and test its association with ACE scores using the same covariate set as individual subfield models (See US-2)
- **FR-007**: System MUST perform non-parametric permutation tests with exactly 5,000 permutations to verify linear model assumptions, completing within 3 hours (See US-3)
- **FR-008**: System MUST conduct sensitivity analysis sweeping the threshold over {0.01, 0.05, 0.1} and report how false-positive rates vary across these values (See US-3)
- **FR-009**: System MUST repeat the primary analysis on participants with ICV within 1 standard deviation of the sample mean and output comparison statistics (See US-3)
- **FR-010**: System MUST frame all findings as ASSOCIATIONAL rather than causal in all output reports and documentation (See US-2)

### Key Entities

- **Participant**: Represents an individual in the ABCD Study cohort with attributes including family_id, age, sex, scanner_site, ACE_score, and quality flags
- **HippocampalSubfield**: Represents a subfield (CA3, DG, subiculum) with attributes including raw_volume, normalized_volume, and ICV
- **StatisticalModel**: Represents a fitted linear mixed-effects model with attributes including β_coefficient, confidence_interval, p_value, and corrected_p_value
- **AnalysisResult**: Represents the output of a statistical test with attributes including effect_size, standard_error, p_value, and permutation_p_value

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The number of participants retained after filtering is measured against the original ABCD Study Release 4.0 cohort size to verify ≥80% retention (See US-1)
- **SC-002**: The runtime of the primary statistical modeling pipeline is measured against the 45-minute target to verify CPU-tractability on GitHub Actions free tier (See US-2)
- **SC-003**: The agreement between parametric and permutation test p-values is measured against a ±0.02 tolerance to verify linear model assumptions hold (See US-3)
- **SC-004**: The effect size stability across the ICV-restricted sensitivity analysis is measured against a ≤15% change threshold to verify robustness (See US-3)
- **SC-005**: The variation in false-positive rates across the threshold sensitivity sweep {0.01, 0.05, 0.1} is measured to quantify threshold dependency (See US-3)
- **SC-006**: The total runtime of the complete analysis pipeline (data acquisition through robustness checks) is measured against the 6-hour GitHub Actions job limit (See US-1, US-2, US-3)

## Assumptions

- The ABCD Study Release 4.0 data portal provides downloadable phenotypic CSV and subcorticalSegmentationStats files containing ACE scores, hippocampal subfield volumes (CA3, DG, subiculum), intracranial volume, age, sex, scanner site, and family_id for all participants
- The Freesurfer-derived hippocampal subfield segmentation has been validated for the ABCD Study cohort and provides reliable volume estimates (see Related work citation)
- Parent-reported ACE questionnaire scores have been validated in the ABCD Study population and represent a reliable measure of adverse childhood experiences
- The linear mixed-effects model approach is appropriate for the hierarchical structure of the ABCD Study data (family clustering)
- The ABCD Study data files fit within the 7 GB RAM and 14 GB disk constraints of the GitHub Actions free-tier runner when properly sampled or streamed
- The ACE score distribution will require log-transformation if skewness exceeds 1.0 (absolute value)
- The Bonferroni correction threshold of p < 0.0167 (0.05/3) follows community-standard practice for three simultaneous hypothesis tests
- No GPU acceleration is available or required; all statistical methods are CPU-tractable using Python's statsmodels library
- The total number of participants after filtering will be sufficient for statistical power (N ≥ 500) for detecting modest effect sizes (β ≈ 0.1) at α = 0.0167
