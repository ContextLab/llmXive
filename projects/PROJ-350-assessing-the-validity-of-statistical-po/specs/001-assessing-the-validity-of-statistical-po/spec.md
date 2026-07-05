# Feature Specification: Assessing the Validity of Statistical Power in Publicly Available Pre-Registered Studies

**Feature Branch**: `001-assessing-statistical-power-validity`  
**Created**: 2024-05-22  
**Status**: Draft  
**Input**: User description: "Assessing the Validity of Statistical Power in Publicly Available Pre-Registered Studies"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Ingestion and Metadata Extraction (Priority: P1)

The system must successfully connect to the Open Science Framework (OSF) public API, retrieve a batch of pre-registered study records, and extract the specific planned power estimates, target sample sizes, and effect size assumptions defined in the pre-registration documents.

**Why this priority**: Without accurate extraction of the "planned" variables, the core comparison (planned vs. sensitivity) cannot occur. This is the foundational data layer; if this fails, the entire research question is unanswerable.

**Independent Test**: The system can be tested by running the extraction pipeline against a known, small subset of OSF studies (e.g., 5 studies) and verifying that the extracted JSON contains the exact planned power values, target_n, and effect_size_assumption as manually read from the source documents.

**Acceptance Scenarios**:

1. **Given** a list of 5 valid OSF study IDs, **When** the extraction script runs, **Then** the output file contains a record for each study with the `planned_power`, `target_n`, and `effect_size_assumption` fields populated.
2. **Given** a study record where the pre-registration text is missing the planned power estimate, **When** the extraction script runs, **Then** the record is flagged with a `missing_planned_data` status rather than causing the script to crash.
3. **Given** a study with multiple pre-registration documents, **When** the extraction script runs, **Then** it prioritizes the document labeled "Primary Pre-registration" or the earliest date to extract the planned variables.

---

### User Story 2 - Sensitivity Power Calculation and Power Gap Analysis (Priority: P2)

The system must retrieve the actual sample sizes and observed effect sizes from the study's published results or linked data repository. Crucially, it must calculate the **Sensitivity Power** (the power to detect the *assumed* effect size given the *actual* sample size) and compute the **Power Gap** (Planned Power - Sensitivity Power). This avoids the circularity of using observed effect sizes to validate planned power.

**Why this priority**: This step generates the primary dependent variable (Power Gap). By using the *assumed* effect size for the sensitivity calculation, we validate the planning process independently of the "Winner's Curse" bias inherent in observed effect sizes.

**Independent Test**: The system can be tested by feeding it a CSV with known `n`, `assumed_effect_size`, and `alpha` values, and verifying the calculated `sensitivity_power` matches a manual calculation using the `statsmodels` library.

**Acceptance Scenarios**:

1. **Given** a study with `n=50`, `assumed_effect_size=0.5`, and `alpha=0.05`, **When** the calculation module runs, **Then** the `sensitivity_power` is calculated and the `power_gap` (planned - sensitivity) is recorded.
2. **Given** a study where the assumed effect size cannot be determined from the text, **When** the calculation module runs, **Then** the study is excluded from the power gap analysis but retained in a "missing_assumption" log for audit.
3. **Given** a study where the sensitivity power calculation results in a value > 1.0 (due to error) or < 0.0, **When** the calculation module runs, **Then** the value is clamped to the [0.0, 1.0] range and a warning is logged.

---

### User Story 3 - Regression Modeling and Predictor Identification (Priority: P3)

The system must perform a multiple linear regression analysis to identify which study design features (e.g., field of study, sample size category, effect size domain) systematically predict the **Power Gap** between planned and sensitivity power.

**Why this priority**: This addresses the "what factors predict" part of the research question. It moves beyond descriptive statistics to explanatory modeling, providing the actionable insights for the "Motivation" section.

**Independent Test**: The system can be tested by running the regression on a synthetic dataset where the relationship between a predictor (e.g., "Field") and the outcome (Power Gap) is known, verifying that the model recovers the correct direction and significance of the coefficient.

**Acceptance Scenarios**:

1. **Given** a dataset of 50+ studies with calculated Power Gaps and predictor variables, **When** the regression model runs, **Then** it outputs coefficients, p-values, and R-squared values for each predictor.
2. **Given** a dataset where the predictors exhibit high collinearity (VIF > 5), **When** the regression model runs, **Then** it flags the collinearity and reports the joint relationship descriptively rather than claiming independent effects.
3. **Given** the regression output, **When** the report generator runs, **Then** it produces a diagnostic plot showing the distribution of residuals and the relationship between the primary predictor and the Power Gap.

---

### Edge Cases

- What happens when the OSF API rate limits the requests? (System must implement exponential backoff and resume capability).
- How does the system handle studies where the "observed effect size" is reported as a confidence interval rather than a point estimate? (System must extract the midpoint or flag for manual review).
- What if a pre-registration document mentions "power analysis" but provides no numerical value? (System must record as `missing_planned_data` and exclude from Power Gap calculation).
- How does the system handle studies where the actual sample size is zero or negative due to data extraction errors? (System must validate `n > 0` before calculation).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST extract `planned_power`, `target_n`, and `effect_size_assumption` from OSF pre-registration documents using NLP parsing first, falling back to regex for specific patterns, explicitly citing the source document section as `page_number:paragraph_id` or `json_path`. (See US-1)
- **FR-002**: System MUST retrieve `actual_sample_size` and `observed_effect_size` from linked data repositories or published result sections, handling cases where data is missing by flagging the record. (See US-2)
- **FR-003**: System MUST calculate `sensitivity_power` using the `statsmodels` Python library with `alpha=0.05` as the fixed significance level, ensuring the method is CPU-tractable. (See US-2)
- **FR-004**: System MUST compute the `power_gap` metric as `planned_power - sensitivity_power` for every study where both values are available. (See US-2)
- **FR-005**: System MUST perform a multiple linear regression to model `power_gap` as a function of study characteristics (field mapped to broad categories like Social/Natural; sample size category binned as Small: n<30, Medium: 30-100, Large: >100) and output coefficients with p-values. (See US-3)
- **FR-006**: System MUST include a collinearity diagnostic (e.g., Variance Inflation Factor) for predictors in the regression model and suppress independent effect claims if VIF > 5. (See US-3)
- **FR-007**: System MUST frame all regression findings as ASSOCIATIONAL, explicitly stating that observational design precludes causal claims regarding predictor effects. (See US-3)

### Key Entities

- **StudyRecord**: Represents a single pre-registered study, containing `osf_id`, `field`, `planned_power`, `target_n`, `actual_sample_size`, `observed_effect_size`, `sensitivity_power`, `power_gap`.
- **PredictorVariable**: Represents a study characteristic used in regression (e.g., `field_of_study`, `sample_size_category`, `effect_size_domain`).
- **RegressionResult**: Contains the statistical output of the Power Gap model, including coefficients, standard errors, p-values, and VIF diagnostics.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The Power Gap distribution (Planned - Sensitivity) is measured against a null hypothesis of zero mean using a one-sample t-test (or Wilcoxon signed-rank test if non-normal) to determine if systematic overestimation exists. (See US-2)
- **SC-002**: The regression model's predictive power (R-squared) is measured against a baseline model containing only an intercept to determine if study characteristics explain variance in Power Gap. (See US-3)
- **SC-003**: The collinearity diagnostic (VIF) is measured against the threshold of 5.0 to determine if predictors can be interpreted independently or must be treated jointly. (See US-3)
- **SC-004**: The sample size of the final analysis is measured against the requirement of ≥ 30 studies with valid power calculations to ensure the regression model has sufficient degrees of freedom for the number of predictors used. (See US-3)
- **SC-005**: The sensitivity power calculation method is measured against the `statsmodels` documentation to ensure the implementation matches the standard statistical definition for the specified test type. (See US-2)

## Assumptions

- The Open Science Framework (OSF) public API provides stable access to pre-registration metadata and document text for the selected study cohort.
- The `statsmodels` Python library is available on the GitHub Actions runner and can perform power calculations within the available memory constraints.
- Pre-registration documents contain machine-readable text or structured fields for planned power and sample size; manual extraction is not required for >90% of the sample.
- Observed effect sizes are reported as point estimates in the linked data or results; if only confidence intervals are provided, the midpoint will be used as a proxy.
- The analysis will be performed on a sample of studies, which is sufficient for the regression analysis and fits within the allocated GitHub Actions job time limit.
- The study fields are categorical and can be encoded as dummy variables for the regression model without introducing excessive collinearity.
- The "observed effect size" is defined consistently across studies (e.g., Cohen's d for t-tests, Pearson's r for correlations) or is normalized to a common scale.
- No GPU acceleration is required; all statistical computations are CPU-tractable.