# Specification: The Impact of Perceived Social Support on Resilience to Online Harassment

## 1. Introduction

This project investigates the moderating role of perceived social support in the relationship between online harassment and mental health outcomes (depression, anxiety, PTSD). The analysis strictly follows a **Single-Dataset Approach** using the Cyberbullying Survey 2021 to ensure methodological validity and avoid confounding by dataset source.

## 2. Background

Online harassment is a significant public health concern. While prior research suggests social support acts as a buffer, methodological challenges in isolating this effect have led to conflicting results. This project addresses these challenges through a rigorous, single-source analysis.

## 3. Research Questions

1. Does perceived social support moderate the relationship between online harassment and depression?
2. Does perceived social support moderate the relationship between online harassment and anxiety?
3. Does perceived social support moderate the relationship between online harassment and PTSD?

## 4. Data Sources

### 4.1 Primary Source: Cyberbullying Survey 2021
- **Dataset ID**: `cyberbullying_survey_2021` (Verified via `code/config/data_sources.yaml`)
- **Access Method**: `datasets.load_dataset("path/to/verified_id")` or direct CSV fetch from verified URL.
- **Rationale**: This dataset contains all necessary variables (harassment severity, social support, mental health scales) within a single cohort, eliminating the confounding variable of dataset source that invalidated the dual-dataset approach.

### 4.2 Excluded Sources
- **GSS 2022**: Explicitly excluded. The dual-dataset matching approach (Synthetic Cohort) using GSS 2022 as a reference was rejected as methodologically invalid due to unresolvable confounding by dataset source.

## 5. Methodological Notes

### 5.1 Revised Approach: Single-Dataset Analysis
The project strictly adheres to the **Single-Dataset Approach** as mandated by the project Plan. This approach utilizes the Cyberbullying Survey 2021 as the sole data source for all variables.

**Rationale for Rejection of Dual-Dataset Matching:**
Previous proposals to construct a "Synthetic Cohort" by matching the Cyberbullying Survey 2021 with the General Social Survey (GSS) 2022 were found to be methodologically invalid. The fundamental issue is **confounding by dataset source**. Any observed interaction effect in a dual-dataset design would be impossible to distinguish from artifacts arising from differences in:
1. Sampling frames and demographic distributions.
2. Question wording and measurement instruments.
3. Cultural and temporal contexts of data collection.

Consequently, the "Synthetic Cohort" approach is **rejected**. The interaction term estimates a genuine psychological buffering effect only when derived from within a single, consistent measurement context.

### 5.2 Analysis Strategy
1. **Ingestion**: Load Cyberbullying Survey 2021.
2. **Preprocessing**: Harmonize variables, apply MICE imputation for predictors, and handle outcome missingness via listwise deletion.
3. **Modeling**: Fit OLS models with heteroskedasticity-consistent (HC3) standard errors, including the interaction term `SocialSupport:HarassmentExposure`.
4. **Robustness**: Apply bootstrap confidence intervals and Benjamini-Hochberg FDR correction.

### 5.3 Ethical Considerations
All analysis is conducted on anonymized survey data. No personally identifiable information is used.

## 6. Data Dictionary

The following variables are derived exclusively from the **Cyberbullying Survey 2021 (Sole Source)**:

| Variable Name | Description | Source | Type |
|:--- |:--- |:--- |:--- |
| `social_support` | Perceived social support score (PSS) | Cyberbullying Survey 2021 (Sole Source) | Continuous |
| `harassment_severity` | Continuous measure of harassment severity | Cyberbullying Survey 2021 (Sole Source) | Continuous |
| `harassment_exposure` | Binary indicator (1 if severity > 0) | Derived from `harassment_severity` | Binary |
| `depression` | CES-D aggregate score | Cyberbullying Survey 2021 (Sole Source) | Continuous |
| `anxiety` | GAD-7 aggregate score | Cyberbullying Survey 2021 (Sole Source) | Continuous |
| `ptsd` | PCL-5 aggregate score (if available) | Cyberbullying Survey 2021 (Sole Source) | Continuous |
| `age` | Age of respondent | Cyberbullying Survey 2021 (Sole Source) | Continuous |
| `gender` | Gender identity | Cyberbullying Survey 2021 (Sole Source) | Categorical |
| `education` | Education level | Cyberbullying Survey 2021 (Sole Source) | Ordinal |
| `income` | Household income bracket | Cyberbullying Survey 2021 (Sole Source) | Ordinal |
| `platform` | Primary platform of harassment experience | Cyberbullying Survey 2021 (Sole Source) | Categorical |

## 7. User Stories

### US1: Data Ingestion & Cohort Preparation
As a researcher, I want to ingest the Cyberbullying Survey 2021, clean the data, and prepare a valid analysis cohort so that I can proceed to modeling.
- **Acceptance Criteria**:
 - Real data source verified.
 - MICE imputation applied to predictors.
 - Analysis cohort saved to `data/results/analysis_cohort.csv`.
 - Validation checks (variance, VIF) passed.

### US2: Interaction Analysis & Hypothesis Testing
As a researcher, I want to fit OLS models with interaction terms and compute bootstrapped confidence intervals so that I can test the buffering hypothesis.
- **Acceptance Criteria**:
 - OLS models fitted with HC3 SEs.
 - Bootstrap CIs computed.
 - FDR correction applied.
 - Results saved to `data/results/regression_results.csv`.

### US3: Sensitivity Analysis & Robustness Checks
As a researcher, I want to run sensitivity analyses (continuous severity, platform stratification) to ensure robustness.
- **Acceptance Criteria**:
 - Continuous severity model fitted.
 - Platform stratification performed (if data allows).
 - Sensitivity summary saved to `data/results/sensitivity_analysis.csv`.

## 8. Appendices

### 8.1 References
- Radloff, L. S. (n.d.). The CES-D Scale.
- Spitzer, R. L., et al. (2006). GAD-7.
- Weathers, F. W., et al. (2013). PCL-5.