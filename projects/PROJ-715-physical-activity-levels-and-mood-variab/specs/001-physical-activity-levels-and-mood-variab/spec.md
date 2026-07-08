# Feature Specification: Physical Activity Levels and Mood Variability in Daily Life

**Feature Branch**: `001-physical-activity-mood-variability`  
**Created**: 2026-06-17  
**Status**: Draft  
**Input**: User description: "Analyze the relationship between daily step counts and intra-day mood variability using the StudentLife dataset."

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Preprocessing (Priority: P1)

The system MUST successfully download the StudentLife dataset, parse raw step logs into daily totals, align EMA mood timestamps, and compute daily aggregates (mean mood, mood variability) for each participant-day, excluding any records with missing critical values.

**Why this priority**: Without clean, aligned data, no statistical analysis can occur. This is the foundational data engineering step required to transform raw sensor logs into an analyzable table.

**Independent Test**: Verify that the generated `daily_aggregates.csv` contains one row per participant per day, with non-null values for `total_steps`, `mean_mood`, and `mood_std`, and that the row count matches the expected number of valid participant-days after filtering.

**Acceptance Scenarios**:

1. **Given** the raw StudentLife zip file is downloaded, **When** the preprocessing script executes, **Then** the output table contains exactly one record per participant per calendar day with computed `total_steps`, `mean_mood`, and `mood_std` columns.
2. **Given** an EMA entry with a missing mood rating, **When** the alignment step runs, **Then** that specific entry is excluded from the daily average calculation, and the day is only included if a sufficient number of valid ratings remain (≥ 2).
3. **Given** a day with zero recorded steps, **When** the aggregation runs, **Then** the `total_steps` field is recorded as 0 (not null), preserving the day for analysis.

---

### User Story 2 - Statistical Modeling and Association Testing (Priority: P2)

The system MUST fit linear mixed-effects models to test the association between daily step counts and (a) intra-day mood variability and (b) average mood, controlling for sleep duration, day-of-week, and baseline affect, while explicitly framing results as associational due to the observational nature of the data.

**Why this priority**: This is the core research question. The model output provides the evidence needed to answer whether activity levels relate to mood stability.

**Independent Test**: Run the model fitting script and verify that the output report contains the fixed-effect coefficient for `total_steps` for both the variability and mean mood models, along with p-values and 95% confidence intervals. The model must converge successfully.

**Acceptance Scenarios**:

1. **Given** the cleaned `daily_aggregates.csv`, **When** the mixed-effects model is fitted, **Then** the output includes the coefficient estimate, standard error, and p-value for the `total_steps` predictor in the `mood_variability` model.
2. **Given** the observational design, **When** the results are summarized, **Then** the report explicitly states that findings represent associations, not causal effects, and avoids language implying causation (e.g., "exercise causes").
3. **Given** multiple covariates (sleep, day-of-week), **When** the model is fitted, **Then** the output includes the coefficients for these covariates to demonstrate control for potential confounders.

---

### User Story 3 - Validation and Sensitivity Analysis (Priority: P3)

The system MUST perform a leave-one-participant-out cross-validation to test the generalizability of the association (coefficient stability) and execute a sensitivity analysis by re-running the primary model with alternative activity metrics (e.g., active minutes) and excluding weekends to ensure robustness.

**Why this priority**: These checks confirm that the observed association is not an artifact of a single outlier participant or specific data subsets, increasing the reliability of the findings.

**Independent Test**: Verify that the final report contains a section detailing the cross-validation performance (coefficient consistency across folds) and the results of the sensitivity checks (e.g., "Coefficient remained significant when weekends excluded").

**Acceptance Scenarios**:

1. **Given** the full dataset, **When** the leave-one-participant-out loop executes, **Then** the model is retrained N times (where N is the number of participants), and the consistency of the `total_steps` coefficient is reported.
2. **Given** the primary model results, **When** the sensitivity analysis runs, **Then** the report compares the `total_steps` coefficient from the primary model against the model run on "weekdays only" data.
3. **Given** the primary model results, **When** the alternative metric test runs, **Then** the report compares the primary model (using step counts) against a model using "active minutes" to verify consistency of the direction of effect.

### Edge Cases

- **What happens when** a participant has data for only 1 or 2 days? (The model may fail to estimate random effects; these participants should be excluded or handled via a fixed-effects-only fallback).
- **How does system handle** days with zero mood entries? (These days must be dropped entirely from the daily aggregation to avoid division-by-zero errors in calculating standard deviation).
- **What happens when** the StudentLife dataset is incomplete or corrupted? (The pipeline must fail gracefully with a clear error message listing missing files rather than crashing silently).
- **How does system handle** days with exactly 0 mood variability (all ratings identical)? (The system MUST apply a log-transformation with an epsilon offset of 0.01 to avoid undefined log(0) values).

## Requirements

### Functional Requirements

- **FR-001**: System MUST download the StudentLife dataset from the specified OSF DOI and verify file integrity before processing (See US-1).
- **FR-002**: System MUST compute daily `mood_std` (standard deviation) for each participant-day, excluding days with fewer than 2 valid mood ratings to ensure variance calculation validity (See US-1).
- **FR-003**: System MUST fit a linear mixed-effects model with `log(mood_std + 0.01)` as the outcome and `total_steps` as the primary predictor, including random intercepts for participant. The model MUST converge, and the primary predictor coefficient must be reported with a p-value < 0.05 or explicitly flagged as non-significant (See US-2).
- **FR-004**: System MUST explicitly label all statistical findings as "associational" in the generated report to reflect the observational study design (See US-2).
- **FR-005**: System MUST perform a leave-one-participant-out cross-validation to assess the generalizability of the step-mood association. The system MUST report the average RMSE and verify that the `total_steps` coefficient sign remains consistent across ≥ 90% of the folds (See US-3).
- **FR-006**: System MUST execute a sensitivity analysis restricting the dataset to "weekdays only" and re-running the primary model. The requirement is met if the `total_steps` coefficient sign remains consistent and the p-value remains < 0.05 (or remains non-significant) compared to the primary model (See US-3).
- **FR-007**: System MUST generate a PDF/HTML report containing effect sizes, 95% confidence intervals, and diagnostic plots (residuals vs. fitted) (See US-2).
- **FR-008**: System MUST perform a sensitivity analysis for single-rating days by comparing the primary model (excluding single-rating days) against a model that imputes single-rating days using the participant's median mood value. The system MUST report whether the coefficient direction remains consistent in ≥ 80% of bootstrap samples (See US-3).

### Key Entities

- **ParticipantDay**: A unique record representing one participant on one calendar day, containing aggregated step counts, mean mood, mood variability, and covariates.
- **ModelOutput**: The statistical results object containing fixed effects, random effects variance, and model fit statistics (AIC/BIC).
- **SensitivityResult**: A comparative record storing the primary model coefficients alongside coefficients from robustness checks (e.g., weekdays-only).

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The association between `total_steps` and `mood_variability` is measured against the null hypothesis (coefficient = 0) via the p-value from the mixed-effects model (See US-2).
- **SC-002**: The generalizability of the model is measured against the consistency of the `total_steps` coefficient sign across leave-one-participant-out folds (See US-3).
- **SC-003**: The robustness of the findings is measured against the stability of the `total_steps` coefficient sign and significance when the dataset is restricted to "weekdays only" (See US-3).
- **SC-004**: The validity of the variance estimates is measured against the residual normality and homoscedasticity diagnostics from the model fit (See US-2).
- **SC-005**: The robustness of the single-rating handling is measured against the consistency of the coefficient direction in ≥ 80% of bootstrap samples comparing exclusion vs. imputation (See US-3).

## Assumptions

- The StudentLife dataset contains valid, parseable step count logs and EMA mood entries for the majority of the participants over the ~-month period.
- The `mood` variable in the EMA data is recorded on a consistent numeric scale allowing for standard deviation calculation.
- The GitHub Actions free-tier runner (standard CPU and RAM allocation) is sufficient to process the participant dataset and run the mixed-effects models within the 6-hour job limit without GPU acceleration.
- The `statsmodels` Python library provides robust mixed-effects modeling capabilities suitable for this sample size.
- The relationship between physical activity and mood is linear within the observed range of step counts for this population.
- Sleep duration and baseline affect data are available in the provided dataset covariates; if missing, the model will proceed without them or with imputation (to be clarified if missingness > 5%).