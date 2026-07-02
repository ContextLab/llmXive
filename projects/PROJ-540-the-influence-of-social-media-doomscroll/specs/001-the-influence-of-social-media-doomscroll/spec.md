# Feature Specification: The Influence of Social Media "Doomscrolling" on Anticipatory Anxiety

**Feature Branch**: `001-doomscrolling-anxiety`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Does frequency of negative news consumption on social media predict elevated anticipatory anxiety scores, independent of baseline anxiety and demographic factors?"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Variable Extraction (Priority: P1)

The system MUST download a specified public survey dataset (e.g., General Social Survey, Pew Research, or YouGov) that contains the required variables and extract the specific variables needed for the analysis: negative news consumption frequency, anxiety scores (anticipatory or general), baseline anxiety, and demographic covariates.

**Why this priority**: Without successfully ingesting and correctly mapping the raw data to the required analytical variables, no statistical modeling or hypothesis testing can occur. This is the foundational step for the entire research pipeline.

**Independent Test**: The pipeline can be tested by verifying that the output CSV/JSON contains the exact columns defined in the schema with no null values for the primary predictor and outcome variables after cleaning.

**Acceptance Scenarios**:

1. **Given** a valid URL to a public dataset (e.g., GSS, Pew) containing the required schema, **When** the ingestion script runs, **Then** the output file contains columns for `news_exposure_freq`, `anxiety_score`, `baseline_anxiety`, `age`, and `gender` with >90% non-null values.
2. **Given** a dataset with missing values in the `news_exposure_freq` column, **When** the cleaning step executes, **Then** the system performs listwise deletion (if resulting N ≥ 30) and logs the count of removed rows, ensuring the final analysis dataset has no missing values in key predictors.

---

### User Story 2 - Statistical Modeling and Association Estimation (Priority: P2)

The system MUST fit a multiple linear regression model to estimate the association between negative news exposure and anxiety scores, controlling for baseline anxiety and demographics, and calculate the correlation coefficient. The system MUST ensure that baseline and outcome anxiety measures are distinct constructs (e.g., trait vs. state or pre-test vs. post-test) to avoid mathematical coupling.

**Why this priority**: This is the core research activity. It directly answers the research question by quantifying the relationship while controlling for confounders.

**Independent Test**: The model can be tested by running the regression on a synthetic dataset with known coefficients and verifying that the estimated coefficients match the expected values within a small tolerance.

**Acceptance Scenarios**:

1. **Given** a cleaned dataset with valid numeric variables, **When** the regression model is fitted, **Then** the output includes the coefficient, standard error, and p-value for the `news_exposure_freq` predictor.
2. **Given** a fitted model, **When** the assumption checks run, **Then** the system outputs diagnostic plots (residuals vs. fitted, Q-Q plot) and a pass/fail status for linearity, homoscedasticity, and normality assumptions.

---

### User Story 3 - Robustness Check and Visualization (Priority: P3)

The system MUST generate a scatter plot with a regression line and confidence interval, and perform a robustness check by re-running the analysis on a subset of users with high social media engagement (top 25th percentile), provided engagement correlates with news exposure (r > 0.3).

**Why this priority**: Visualization provides immediate interpretability for stakeholders, while the robustness check ensures the findings are not driven by a specific segment of the population, adding scientific rigor.

**Independent Test**: The visualization can be tested by generating a plot file and verifying the regression line passes through the centroid of the data points. The robustness check is tested by comparing the coefficient sign and significance between the full sample and the high-engagement subset.

**Acceptance Scenarios**:

1. **Given** the regression results, **When** the plotting module executes, **Then** a PNG/SVG file is generated showing the scatter of `news_exposure_freq` vs. `anxiety_score` with a fitted regression line and 95% confidence interval shaded.
2. **Given** a subset of users with `social_media_engagement` > 75th percentile, **When** the robustness regression runs (if correlation with predictor > 0.3), **Then** the system reports the new coefficient and p-value, and flags if the sign of the association flips or loses significance.

---

### Edge Cases

- **What happens when** the dataset lacks a critical predictor variable (e.g., `news_exposure_freq` is missing)? The system MUST log an error and halt, preventing the assumption of variable interchangeability.
- **What happens when** the dataset lacks the specific 'anticipatory_anxiety' variable but contains 'general_anxiety'? The system MUST adjust to use 'general_anxiety' as a proxy, flag the construct validity limitation, and proceed.
- **How does the system handle** perfect multicollinearity (e.g., if `baseline_anxiety` is mathematically derived from `anxiety_score`)? The system MUST detect the Variance Inflation Factor (VIF) > 10 and flag the model as unstable, preventing the reporting of independent effects.
- **What happens when** the sample size is too small for regression?
    - If N < 30: The system MUST stop and report a power limitation warning (Hard Stop).
    - If 30 ≤ N < 100: The system MUST proceed but emit a 'Low Power' warning (post-hoc power < 0.8) and flag results as preliminary.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download a public survey dataset from a specified URL (e.g., GSS, Pew) and parse it into a structured dataframe format, ensuring the schema matches required variables. (See US-1)
- **FR-002**: System MUST perform listwise deletion on rows with missing values in the predictor (`news_exposure_freq`) or outcome (`anxiety_score`) variables ONLY IF the resulting sample size is ≥ 30. If resulting N < 30, the system MUST halt and report a power limitation warning. (See US-1)
- **FR-003**: System MUST fit a multiple linear regression model where `anxiety_score` is the dependent variable and `news_exposure_freq`, `baseline_anxiety`, `age`, and `gender` are independent variables. The system MUST verify that `baseline_anxiety` and `anxiety_score` are measured via distinct instruments or time points to avoid mathematical coupling. (See US-2)
- **FR-004**: System MUST calculate and report the Pearson or Spearman correlation coefficient between `news_exposure_freq` and `anxiety_score`. (See US-2)
- **FR-005**: System MUST generate a scatter plot with a regression line and 95% confidence interval visualization. (See US-3)
- **FR-006**: System MUST perform a robustness check by re-fitting the model on a subset of users with high social media engagement (top 25th percentile), provided the correlation between `social_media_engagement` and `news_exposure_freq` is > 0.3. If correlation ≤ 0.3, the system MUST skip the check and log a warning. (See US-3)
- **FR-007**: System MUST verify model assumptions (linearity, homoscedasticity, normality of residuals) and output diagnostic metrics. (See US-2)
- **FR-008**: System MUST flag the analysis results if 'general_anxiety' was used as a proxy for 'anticipatory_anxiety', explicitly noting the construct validity limitation. (See US-2)

### Key Entities

- **SurveyResponse**: Represents a single participant record containing fields for news consumption frequency, anxiety scores, and demographics.
- **RegressionModel**: Represents the fitted statistical model containing coefficients, p-values, and diagnostic metrics.
- **Visualization**: Represents the generated plot artifact showing the relationship between variables.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The association between negative news exposure and anxiety is measured against the null hypothesis (p < 0.05) to determine statistical significance. (See US-2)
- **SC-002**: The model's explanatory power is measured against the R-squared value to assess the proportion of variance in anxiety explained by news exposure and covariates. (See US-2)
- **SC-003**: The robustness of the findings is measured against the consistency of the coefficient sign and significance between the full sample and the high-engagement subset. (See US-3)
- **SC-004**: The validity of the statistical inference is measured against the results of assumption checks (e.g., Shapiro-Wilk test p-value > 0.05 for residuals). (See US-2)
- **SC-005**: The computational feasibility is measured against the execution time (≤ 60 seconds per [deferred] records) on a standard CPU environment. (See US-1)

## Assumptions

- The analysis accepts any public dataset (e.g., GSS, Pew, YouGov) that contains the required variables: `news_exposure_freq`, `anxiety_score`, `baseline_anxiety`, and demographics. The system does not assume GSS specifically, but requires the schema.
- If the dataset lacks a specific 'anticipatory_anxiety' scale (common in general surveys like GSS), the system will use 'general_anxiety' as a proxy, provided the limitation is explicitly flagged in the output (see FR-008).
- The relationship between news exposure and anxiety is linear enough to be modeled via linear regression; non-linear relationships will be noted as a limitation if residual plots suggest curvature.
- The dataset sample size must be ≥ 30 to proceed. If 30 ≤ N < 100, results are considered preliminary with low power.
- The analysis runs entirely on CPU without GPU acceleration, utilizing standard Python libraries (pandas, statsmodels, scikit-learn) which are compatible with the GitHub Actions free-tier environment.
- Since the data is observational, all findings will be framed as associational, not causal, regardless of the statistical significance of the results.
- Listwise deletion is the primary method for missing data. If the resulting N < 30, the analysis halts. No imputation methods are applied to preserve simplicity for CPU constraints.
- 'Social media engagement' is used as a proxy for 'doomscrolling frequency' in the robustness check, valid only if correlated with news consumption (r > 0.3).