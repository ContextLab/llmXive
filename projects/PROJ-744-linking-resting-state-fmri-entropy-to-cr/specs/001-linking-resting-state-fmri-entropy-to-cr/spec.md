# Feature Specification: Linking Resting‑State fMRI Entropy to Creative Problem Solving

**Feature Branch**: `001-linking-resting-state-fmri-entropy`  
**Created**: 2026-06-20  
**Status**: Draft  
**Input**: User description: "Linking Resting‑State fMRI Entropy to Creative Problem Solving"

## User Scenarios & Testing

### User Story 1 - Compute Global and Network-Specific Entropy Metrics (Priority: P1)

The research pipeline MUST successfully ingest pre-processed HCP resting-state fMRI 4-D volumes and compute Multiscale Sample Entropy (MSE) for the whole brain and specific canonical networks (DMN, FPN, CON). This is the foundational data generation step; without accurate entropy values, no statistical analysis can occur.

**Why this priority**: This is the core computational task that transforms raw neuroimaging data into the predictor variables required for the study. It is the prerequisite for all subsequent modeling and validation steps.

**Independent Test**: The system can be tested by running the entropy computation module on a subset of subjects, verifying that the output CSV contains non-null MSE values for all HCP atlas parcels and that the aggregated global mean and network averages are calculated correctly against a manual spot-check of one subject's data.

**Acceptance Scenarios**:

1. **Given** a valid 4-D fMRI NIfTI file and the HCP 360-parcel atlas, **When** the entropy module processes the file, **Then** it outputs a CSV row containing the global mean entropy and 7 network-specific average entropy values.
2. **Given** a time series with excessive motion artifacts (mean framewise displacement > 0.2 mm) OR insufficient frames (< 100 frames remaining after motion scrubbing), **When** the module processes the data, **Then**:
   - If > 100 frames remain: It computes entropy on the remaining contiguous time series and flags the subject for exclusion from the primary model in `motion_exclusions.log` (for robustness logging only).
   - If ≤ 100 frames remain: It excludes the subject entirely (no entropy computed) and logs the exclusion ID and reason in `missing_data.log`.
3. **Given** the default template length (m=2) and tolerance (r=0.2*SD), **When** the module runs, **Then** it completes the calculation for all 360 parcels.

---

### User Story 2 - Fit Linear Regression Models with Covariates (Priority: P2)

The system MUST fit a Linear Regression (Ordinary Least Squares) model with robust standard errors to test the association between entropy metrics (predictor) and Alternative Uses Test scores (outcome), controlling for age, sex, and head motion. This step translates the computed metrics into statistical evidence regarding the research question.

**Why this priority**: This implements the primary hypothesis testing mechanism. It is the analytical core that answers the research question, distinguishing the project from a mere data processing script. Note: A Linear Mixed-Effects model with a random intercept is statistically invalid for cross-sectional data (1 observation per subject); OLS with robust SEs is the correct approach.

**Independent Test**: The system can be tested by running the modeling script on a synthetic dataset with known coefficients, verifying that the fitted model recovers the input coefficients within an acceptable margin of error and correctly reports p-values for the fixed effects.

**Acceptance Scenarios**:

1. **Given** a dataset of entropy metrics and behavioral scores, **When** the modeling script executes, **Then** it outputs a summary table containing the fixed effect coefficient, standard error, t-statistic, and p-value for the global entropy predictor.
2. **Given** a model specification including age, sex, and framewise displacement, **When** the model is fitted, **Then** these variables are included as fixed effects in the output.
3. **Given** a dataset where the entropy predictor has no relationship with the outcome, **When** the model is fitted, **Then** the p-value for the entropy coefficient is > 0.05, correctly indicating a null finding.

---

### User Story 3 - Apply Multiple-Comparison Correction and Sensitivity Analysis (Priority: P3)

The system MUST apply Benjamini-Hochberg FDR correction to the set of network-specific hypothesis tests and perform a sensitivity analysis sweeping the entropy tolerance parameter (r) over a defined range for BOTH global and network-specific metrics. This ensures the robustness of findings and controls for false positives inherent in testing multiple networks.

**Why this priority**: This addresses methodological rigor. Without correction for multiple comparisons, the risk of false positives is high; without sensitivity analysis, the results may be artifacts of arbitrary parameter choices.

**Independent Test**: The system can be tested by running the correction module on a set of p-values (one per network) and verifying the adjusted p-values match the Benjamini-Hochberg calculation manually. The sensitivity analysis can be tested by verifying that the output includes results for r ∈ {, 0.20, 0.25}.

**Acceptance Scenarios**:

1. **Given** a list of 7 unadjusted p-values from network-specific models, **When** the FDR correction module runs, **Then** it outputs 7 adjusted p-values where the false discovery rate is controlled at q < 0.05.
2. **Given** a baseline tolerance parameter of r=0.2*SD, **When** the sensitivity analysis runs, **Then** it re-computes global and network-specific entropy and model statistics for r values of 0.15*SD, 0.20*SD, and 0.25*SD, and reports the variation in the headline p-value.
3. **Given** a model result where the p-value is significant at r=0.2 but not at r=0.15, **When** the analysis completes, **Then** the output report explicitly flags this sensitivity and indicates the result is not robust across the tested range.

---

### Edge Cases

- **What happens when** the HCP dataset contains a subject with missing behavioral scores (Alternative Uses Test)?
  - **System handles**: The pipeline automatically excludes the subject from the statistical modeling phase but logs the exclusion ID and reason in a `missing_data.log` file.
- **How does system handle** a runtime error during entropy computation for a specific parcel due to NaN values in the time series?
  - **System handles**: The module catches the error, sets the specific parcel's entropy to `NaN`, continues processing the remaining parcels, and aggregates the result only from valid parcels, flagging the subject for manual review if >10% of parcels are invalid.
- **What happens when** the sample size is too small to support the regression model (N < 30)?
  - **System handles**: The script detects the low sample size, halts the primary analysis, and logs a critical warning that the sample size is insufficient for reliable inference, preventing the generation of a potentially misleading p-value.

## Requirements

### Functional Requirements

- **FR-001**: System MUST compute Multiscale Sample Entropy (MSE) for each of the HCP atlas parcels from pre-processed 4-D fMRI volumes using a vectorized Python implementation. (See US-1)
- **FR-002**: System MUST aggregate parcel-level entropy into a global mean and network-specific averages for the DMN, FPN, CON, and other canonical networks defined by the HCP atlas. (See US-1)
- **FR-003**: System MUST fit a Linear Regression (OLS) model with robust standard errors, using entropy metrics as predictors, age/sex/motion as covariates, and creativity scores as the outcome. (See US-2)
- **FR-004**: System MUST apply Benjamini-Hochberg FDR correction to the set of p-values generated from the network-specific model tests. (See US-3)
- **FR-005**: System MUST execute a sensitivity analysis that sweeps the entropy tolerance parameter `r` over the set {0.15*SD, 0.20*SD, 0.25*SD} and reports the stability of the primary association for both global and network metrics. (See US-3)
- **FR-006**: System MUST exclude participants with mean framewise displacement > 0.2 mm from the primary analysis and log the exclusion ID, reason, and FD value to `motion_exclusions.log`. (See US-1)
- **FR-007**: System MUST output a final results table containing coefficients, standard errors, unadjusted p-values, and FDR-adjusted p-values for all tested models. (See US-2)
- **FR-008**: System MUST validate that all input fMRI volumes and the phenotype file `Creative_Problem_Solving.csv` exist in the directory specified by the `PHENOTYPE_PATH` environment variable (default `./data/phenotypes/`) before starting computation. (See US-1)
- **FR-009**: System MUST compute Multiscale Sample Entropy across multiple scales and aggregate the result as the Area Under the Curve (AUC) of the entropy-vs-scale profile. (See US-1)

### Key Entities

- **Subject**: Represents an individual participant in the HCP dataset, containing attributes: `subject_id`, `age`, `sex`, `mean_framewise_displacement`, `alternative_uses_score`.
- **EntropyMetric**: Represents the computed complexity measure, containing attributes: `subject_id`, `parcel_id`, `network_name`, `global_mean_entropy`, `network_avg_entropy`, `entropy_parameters` (m, r, scale_range, AUC).
- **ModelResult**: Represents the output of the statistical test, containing attributes: `network_name`, `coefficient`, `std_error`, `t_stat`, `p_value`, `p_value_fdr`, `covariate_effects`.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The association between global resting-state entropy and divergent-thinking performance is measured against the null hypothesis (p > 0.05) using the FDR-corrected p-value from the OLS regression model. (See US-2)
- **SC-002**: The robustness of the primary finding is measured against the sensitivity analysis sweep, specifically the variation in the p-value across the tolerance parameter set {0.15, 0.20, 0.25} *SD for both global and network metrics. (See US-3)
- **SC-003**: The validity of the entropy measure is measured against the requirement that the computation completes without memory errors and reports peak RAM usage and runtime for the full dataset. (See US-1)
- **SC-004**: The control for multiple comparisons is measured against the Benjamini-Hochberg procedure, ensuring the false discovery rate is maintained at q < 0.05 across all network tests. (See US-3)
- **SC-005**: The data quality control is measured by the system reporting the final valid N and flagging if N < 30, ensuring the sample size is sufficient for the regression model. (See US-2)

## Assumptions

- **Dataset-variable fit**: It is assumed that the pre-processed HCP resting-state fMRI data and the associated behavioral phenotype file (`Creative_Problem_Solving.csv`) are available and linked by subject ID in the `PHENOTYPE_PATH` directory. If the public HCP release lacks this specific file, the pipeline MUST halt with a clear error suggesting manual data injection.
- **Inference framing**: The study design is observational; therefore, all findings regarding the relationship between entropy and creativity will be framed as associational, not causal, in the final report.
- **Compute feasibility**: The analysis assumes that the vectorized Python implementation of Multiscale Sample Entropy for a set of parcels across a large cohort of subjects fits within the available RAM limit of the GitHub Actions free-tier runner and completes within the 6-hour job limit on a 2-core CPU.
- **Threshold justification**: The tolerance parameter `r` for Sample Entropy is set to 0.2 * SD as a community standard default; the sensitivity analysis (FR-005) is required to validate this choice rather than asserting it as fixed.
- **Measurement validity**: The Alternative Uses Test scores in the HCP dataset are assumed to be a valid measure of divergent thinking, consistent with standard psychometric definitions.
- **Predictor collinearity**: Age, sex, and head motion are assumed to be distinct from the entropy metric; however, a collinearity diagnostic (VIF) will be run, and if VIF > 5, the model will be re-specified to avoid inflated standard errors.
- **Multiplicity & power**: The sample size of the HCP dataset is assumed to provide sufficient power for the OLS models, though the power calculation is deferred to the analysis phase.