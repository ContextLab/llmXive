# Feature Specification: The Impact of Simulated Social Exclusion on Subsequent Prosocial Behavior

**Feature Branch**: `001-social-exclusion-prosociality`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Does experimentally induced social exclusion reduce subsequent willingness to engage in prosocial behavior (e.g., monetary donation) among adults? Aggregating open behavioral datasets from OSF containing exclusion tasks and outcome measures to quantify the effect size."

## User Scenarios & Testing

### User Story 1 - Data Ingestion, Schema Validation, and Standardization (Priority: P1)

The research pipeline MUST locate, download, and validate raw data from public OSF repositories. The system MUST verify that each dataset contains the required columns (`condition`, `prosocial_amount`, `randomized`) before ingestion. If a dataset lacks these columns or contains fewer than 3 valid datasets overall, the system MUST halt and report the error. The system MUST then standardize data, mapping various prosocial outcome names to `prosocial_amount` and handling missing values (NaN) via median imputation (if <5% missing per dataset) or row exclusion (if >=5%). Structural zeros (value = 0) MUST NOT be imputed; they are reserved for the Zero-Inflated model.

**Why this priority**: Without a unified, clean, and *valid* dataset, no statistical analysis can be performed. Schema validation prevents the pipeline from running on irrelevant data (e.g., Iris dataset), and the halt condition ensures the research question is only answered with sufficient evidence.

**Independent Test**: Can be fully tested by running the ingestion script against a configuration containing one valid OSF URL and one invalid URL (missing columns). The system must successfully ingest the valid one, reject the invalid one with a logged error, and report the total count of valid datasets. If the total valid count is <3, the system must halt.

**Acceptance Scenarios**:

1. **Given** a list of OSF dataset URLs, **When** the ingestion script executes, **Then** it validates each URL's schema for required columns (`condition`, `prosocial_amount`, `randomized`). If any are missing, it logs an error and skips that dataset. If fewer than 3 valid datasets remain, the system halts with an "Insufficient Data" error.
2. **Given** a dataset with missing values (NaN) in the `prosocial_amount` column, **When** the preprocessing step runs, **Then** it calculates the missingness percentage *per dataset*: if missingness is <5%, it applies median imputation; if missingness is >=5%, it excludes the rows and logs the count. **Crucially, structural zeros (value=0) are NOT imputed and are passed as 0 to the statistical model.**
3. **Given** a dataset where the exclusion condition is labeled with non-standard strings (e.g., "ignored", "excluded", "ostracized"), **When** the script runs, **Then** it maps all variants to a binary `condition` variable (0=Included, 1=Excluded).
4. **Given** a dataset where the prosocial outcome is named differently (e.g., "allocation", "transfer"), **When** the script runs, **Then** it maps these columns to the unified `prosocial_amount` variable.

---

### User Story 2 - Statistical Analysis and Effect Size Estimation (Priority: P2)

The system MUST perform a **Zero-Inflated Gamma (ZIG)** or **Hurdle** model for continuous outcomes to handle the zero-inflated nature of donation data. If the outcome is binary (0/1), it MUST switch to Logistic Regression. The analysis MUST be split into two pools:
1. **Causal Pool**: Only datasets where the `randomized` flag is explicitly `true`.
2. **Associational Pool**: Datasets where `randomized` is `false` or `unknown`.
The system MUST report separate effect sizes and confidence intervals for each pool. The meta-analysis MUST aggregate two distinct effect sizes: (1) the log-odds coefficient for the zero-inflation component (probability of donating) and (2) the log-scale coefficient for the positive component (amount donated conditional on donating). For binary outcomes, the meta-analysis MUST aggregate the log-odds ratio.

**Why this priority**: Standard Gamma models fail on zeros; ZIG/Hurdle models are mathematically sound for this data. Separating causal and associational pools ensures the research question ("reduces behavior") is only answered with RCT data, preventing causal overreach on observational data. Defining the meta-analytic unit ensures construct validity.

**Independent Test**: Can be fully tested by feeding a synthetic dataset with known zeros and a known negative correlation. The system must fit a ZIG model (not standard Gamma) and report the two distinct coefficients. It must also correctly split the data into two pools based on the `randomized` flag and report separate results.

**Acceptance Scenarios**:

1. **Given** a cleaned dataset with `condition`, `prosocial_amount`, and `randomized` flag, **When** the regression model runs, **Then** it outputs two regression coefficients (log-odds for zero-inflation, log-scale for positive amounts) with standard errors, p-values, and 95% confidence intervals using a Zero-Inflated Gamma or Hurdle model for continuous outcomes, or a single log-odds ratio for binary outcomes.
2. **Given** a dataset where the null hypothesis is true (no effect), **When** the model runs, **Then** the p-value is ≥ 0.05 (assuming significance level $\alpha = 0.05$).
3. **Given** multiple independent datasets, **When** the system aggregates results, **Then** it performs a Random-Effects meta-analysis separately for the **Causal Pool** (RCTs only) and the **Associational Pool**. If fewer than 3 valid datasets exist in the Causal Pool, it reports "Insufficient Causal Data" for that pool but continues with the Associational Pool.
4. **Given** a continuous outcome with zeros, **When** the model runs, **Then** it uses the Zero-Inflated component to model the probability of zero donation and the Gamma component for positive amounts, without imputing zeros.

---

### User Story 3 - Sensitivity Analysis, Robustness Check, and Data Quality Filtering (Priority: P3)

The system MUST perform a sensitivity analysis on the *model assumptions* (e.g., link function, distributional assumption) to verify the stability of the results, AND MUST filter out underpowered datasets (n < 5 in exclusion group) to ensure the validity of the meta-analysis pool. The system MUST also perform a formal meta-analytic power assessment to estimate the power to detect a pooled effect size given the number of studies and observed heterogeneity.

**Why this priority**: Empirical research requires demonstrating that findings are not artifacts of specific parameter choices. The sensitivity analysis must test the robustness of the coefficient to changes in model assumptions (link function, distribution), not the significance threshold. Additionally, including underpowered datasets (n < 5) in a meta-analysis can distort effect size estimates, and a formal power assessment is required to avoid Type II errors.

**Independent Test**: Can be fully tested by running the analysis on the same data with a modified link function (e.g., logit vs. probit) and verifying the system reports the change in the effect size estimate.

**Acceptance Scenarios**:

1. **Given** the primary regression results, **When** the sensitivity analysis runs, **Then** it re-calculates the effect size using a sweep of link functions (logit vs. probit vs. cloglog) and distributional assumptions (Gamma vs. Log-Normal) and reports whether the *effect size coefficient* remains stable (variance < 10%) across this range.
2. **Given** a dataset with outliers (prosocial amounts > 3 standard deviations from the mean), **When** the robustness check runs, **Then** it re-runs the regression excluding these outliers and reports the difference in the effect size ($\Delta\beta$).
3. **Given** multiple independent datasets, **When** the system aggregates results, **Then** it performs a Random-Effects meta-analysis to calculate a pooled effect size and heterogeneity statistic ($I^2$). If fewer than 3 valid datasets remain after filtering, the system reports an "Insufficient Data" status.
4. **Given** a dataset where the exclusion group sample size is < 5, **When** the data quality filter runs, **Then** it excludes the dataset from the primary meta-analysis pool and logs the exclusion reason.
5. **Given** the final set of included studies, **When** the power assessment runs, **Then** it calculates the statistical power to detect a small-to-medium effect size (e.g., Cohen's d = 0.3) given the observed heterogeneity and number of studies, reporting the result.

### Edge Cases

- **What happens when** an OSF dataset is inaccessible or the download times out? The system MUST skip the dataset, log the error, and continue with remaining datasets, ensuring the pipeline does not crash.
- **How does system handle** a dataset where the `prosocial_amount` is recorded as a binary (0/1) rather than a continuous currency value? The system MUST detect this and switch the analysis model to Logistic Regression (as authorized in FR-003), and the `AnalysisResult` entity MUST adapt to report odds ratios instead of linear coefficients. The `Participant` entity MUST support a polymorphic `outcome_type` flag to track this.
- **What happens when** the sample size for the "Excluded" group is < 5? The system MUST flag this dataset as "Underpowered", exclude it from the primary meta-analysis pool, and log the exclusion reason.
- **What happens when** fewer than 3 valid datasets are found after schema validation? The system MUST halt execution, log "Insufficient Data: <3 valid datasets found", and exit with a non-zero status code.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download raw data from OSF URLs specified in the configuration and merge them into a single standardized dataframe, mapping various prosocial outcome names (donation, allocation, transfer) to `prosocial_amount` (See US-1).
- **FR-001.5**: System MUST validate the schema of every downloaded dataset to ensure it contains the required columns: `condition`, `prosocial_amount`, and `randomized`. If any are missing, the dataset MUST be rejected and logged. If the predefined list of URLs yields no valid datasets, the system MUST perform a keyword-based search on OSF for "social exclusion" AND "prosocial" OR "donation" to locate additional candidate datasets (See US-1).
- **FR-002**: System MUST impute missing values (NaN) in the `prosocial_amount` column using *median* imputation for datasets with <5% missingness (calculated per-dataset), or exclude rows if missingness >=5%. **Structural zeros (value=0) MUST NOT be imputed** (See US-1).
- **FR-003**: System MUST execute a **Zero-Inflated Gamma (ZIG)** or **Hurdle** model for continuous outcomes (handling zeros natively), or Logistic Regression for binary outcomes. For ZIG/Hurdle, the model MUST output two coefficients: (1) log-odds for the zero-inflation process and (2) log-scale for the positive component. For Logistic Regression, it MUST output the log-odds ratio. The model MUST use `prosocial_amount` as the dependent variable and `condition` (binary) as the independent variable (See US-2).
- **FR-004**: System MUST calculate and report the 95% confidence interval for both the zero-inflation coefficient and the positive amount coefficient for both the Causal (RCT) and Associational pools (See US-2).
- **FR-005**: System MUST perform a sensitivity analysis by re-running the regression with a sweep of **link functions** (logit, probit, cloglog) and **distributional assumptions** (Gamma, Log-Normal) and report the stability of the *effect size coefficients* (variance < 10%) across this range (See US-3).
- **FR-006**: System MUST detect and exclude datasets where the exclusion group sample size (rows where `condition` == 1, after string normalization per FR-001) is < 5 participants from the primary meta-analysis pool to prevent underpowered distortion of the effect size estimate (See US-3).
- **FR-007**: System MUST filter datasets based on the `randomized` flag. The primary causal analysis MUST only include datasets where `randomized` == true. A secondary associational analysis MUST include datasets where `randomized` is false or unknown (See US-2).
- **FR-008**: System MUST halt execution and report an error if fewer than 3 valid datasets (passing FR-001.5) are found *overall* after ingestion. If >=3 valid datasets exist but <3 are in the Causal Pool, the system MUST proceed with the Associational Pool and flag the Causal Pool as "Insufficient Causal Data" (See US-1, US-2).
- **FR-009**: System MUST perform a formal meta-analytic power assessment using the observed number of studies and heterogeneity ($I^2$) to estimate the power to detect a pooled effect size (e.g., Cohen's d = 0.3) and report the result (See US-3).

### Key Entities

- **Dataset**: Represents a single OSF study containing exclusion manipulation and prosocial outcome data.
- **Participant**: Represents a single row in the consolidated data. Contains `condition` status, `prosocial_amount` (continuous or binary), `randomized` (boolean flag), and `outcome_type` (string: "continuous" or "binary").
- **AnalysisResult**: Represents the output of the regression. For continuous outcomes, it contains `zero_inflation_coeff`, `positive_amount_coeff`, `p_value_zi`, `p_value_pos`, `ci_zi_lower`, `ci_zi_upper`, `ci_pos_lower`, `ci_pos_upper`, `sample_size`, `model_type` (e.g., "ZIG", "Hurdle"), and `pool_type` (e.g., "Causal", "Associational"). For binary outcomes, it contains `log_odds_ratio`, `p_value`, `ci_lower`, `ci_upper`, `sample_size`, `model_type` ("Logistic"), and `pool_type`.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The count of successfully merged datasets is measured against the count of valid URLs in the configuration (Target: [deferred] of valid URLs processed).
- **SC-002**: The effect size (regression coefficient) of exclusion on prosocial behavior is measured against the null hypothesis ($\beta = 0$) to determine statistical significance at $\alpha = 0.05$ for the **Causal Pool** (See FR-003, FR-007).
- **SC-003**: The stability of the effect size estimate is measured across the link function and distributional assumption sweeps; the result is considered robust if the coefficient variance is < 10% across this range (See FR-005).
- **SC-004**: The computational resource usage (RAM and CPU time) is measured against the GitHub Actions free-tier limits (Sufficient RAM, 6 hours) to ensure the analysis completes without resource exhaustion (See FR-001, FR-003).
- **SC-005**: The count and percentage of datasets excluded due to insufficient sample size (n < 5) is measured and reported to ensure the final meta-analysis pool is statistically valid. Additionally, the statistical power to detect a pooled effect size is measured and reported (See FR-006, FR-009).
- **SC-006**: The number of datasets included in the **Causal Pool** vs. the **Associational Pool** is reported to verify the separation of RCT and observational data (See FR-007).
- **SC-007**: The stability of the effect size estimate across the sensitivity analysis (link function/distribution sweeps) is measured and reported as a binary pass/fail (variance < 10%) (See FR-005).

## Assumptions

- **Assumption about data source**: The Open Science Framework contains at least 3 public datasets with raw CSV/JSON data linking Cyberball (or equivalent) exclusion tasks to prosocial outcome measures (monetary donation, resource allocation, or dictator game transfers). **Note**: The current 'Verified Datasets' list may not contain these specific columns; if so, the system will perform a keyword-based search on OSF to locate suitable datasets. **If this assumption fails (fewer than 3 valid datasets found after search), the pipeline halts.**
- **Assumption about data quality**: The downloaded datasets contain at least one column clearly indicating the experimental condition (exclusion vs. inclusion), one column indicating the prosocial outcome, and a metadata flag or column indicating whether the study used random assignment (`randomized`).
- **Assumption about variable fit**: The datasets contain the necessary variables for the primary analysis; specifically, if the idea requires controlling for baseline empathy, it is assumed that at least some datasets include a validated empathy scale (e.g., IRI) or that the primary analysis will be conducted without this covariate if data is missing.
- **Assumption about compute environment**: The analysis can be performed using standard Python libraries (pandas, statsmodels, scipy, metafor-equivalent) on a CPU-only environment without requiring GPU acceleration or large model inference.
- **Assumption about statistical framing**: The primary causal claim ("reduces behavior") is only supported by the **Causal Pool** (RCTs). The **Associational Pool** results are reported as correlational.
- **Assumption about threshold justification**: The significance threshold $\alpha = 0.05$ is used as the community standard default for psychological research; sensitivity analysis will sweep model link functions and distributional assumptions.
- **Assumption about measurement validity**: The prosocial amounts in the datasets (whether called donation, allocation, or transfer) represent valid proxies for prosocial behavior as defined in the original studies.
- **Assumption about data distribution**: Donation/allocation data is typically zero-inflated and right-skewed; therefore, the system defaults to Zero-Inflated Gamma (ZIG) or Hurdle models rather than standard OLS or Gamma GLM to ensure statistical validity.
- **Assumption about input artifacts**: The `research.md` and `data-model.md` files exist as input artifacts for this specification phase, defining the research context and data model constraints.