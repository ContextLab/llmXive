# Specification: The Impact of Perceived Social Support on Resilience to Online Harassment

## 1. Overview

This project investigates the moderating role of perceived social support on the relationship between online harassment exposure and mental health outcomes (depression, anxiety, PTSD).

**Methodological Note**: This specification adopts a **single-dataset approach** using the Cyberbullying Survey 2021. The General Social Survey (GSS) 2022 is explicitly excluded from this analysis due to methodological incompatibility for interaction terms (confounding dataset source with harassment/support levels) and lack of verified PCL-5 items.

## 2. Functional Requirements (Single-Dataset Approach)

### FR-001-Single: Data Source
The analysis shall use the **Cyberbullying Survey 2021** dataset as the sole source of data.
- The dataset must contain measures for:
 - Harassment exposure (binary and continuous severity).
 - Perceived social support.
 - Mental health outcomes: Depression (CES-D), Anxiety (GAD-7), and PTSD (PCL-5).
 - Covariates: Age, Gender, Education, Income, Platform.
- **Exclusion**: The GSS 2022 dataset is excluded. No dual-dataset merging or comparison is performed.

### FR-002-Single: Variable Harmonization
All variables must be harmonized to a common schema within the single dataset context.
- Scale scoring must follow `config/scales.yaml`.
- Missing data must be handled via listwise deletion (>5% missing) followed by MICE imputation.
- No external data imputation or synthetic generation is permitted.

### FR-003: Interaction Analysis
The primary analysis must test the interaction between `SocialSupport` and `HarassmentExposure` on mental health outcomes using OLS regression with heteroskedasticity-consistent (HC3) standard errors.

### FR-004: Robustness Checks
Sensitivity analyses must be performed using:
- Continuous harassment severity instead of binary exposure.
- Stratification by platform (top 3 platforms).

## 3. User Stories (Single-Dataset)

### US-1-Single: Single-Dataset Cohort Construction
**As a** researcher,
**I want** to ingest and clean the Cyberbullying Survey 2021 dataset,
**So that** I have a validated analysis cohort with no missing critical variables and correct scale scores.

**Acceptance Criteria**:
1. Ingestion script successfully loads Cyberbullying Survey 2021.
2. GSS 2022 is not loaded or referenced.
3. Scale scoring (CES-D, GAD-7, PCL-5) is applied correctly.
4. Missingness is handled per protocol (listwise deletion + MICE).
5. A validation report confirms variance and multicollinearity checks pass.
6. Final artifact: `data/results/analysis_cohort.csv`.

### US-2: Interaction Modeling
**As a** researcher,
**I want** to fit OLS models with interaction terms and bootstrap confidence intervals,
**So that** I can quantify the buffering effect of social support.

**Acceptance Criteria**:
1. Models fit for Depression, Anxiety, and PTSD.
2. Interaction term `SocialSupport:HarassmentExposure` is included.
3. BCa bootstrap CIs are computed.
4. FDR correction is applied to p-values.

### US-3: Sensitivity Analysis
**As a** researcher,
**I want** to re-run models with alternative definitions,
**So that** I can confirm the robustness of the findings.

## 4. Success Criteria (Revised)

### SC-001-Single: Single-Dataset Validation
The analysis cohort derived from the Cyberbullying Survey 2021 must pass:
1. **Variance Check**: Standard deviation of `harassment_exposure` > 0.2 and N > 30 in the exposed group.
2. **Support Variance**: Standard deviation of `social_support` > 0.5.
3. **Multicollinearity**: VIF < 5 for the full model matrix including interaction.
4. **Completeness**: No synthetic data or GSS data is present in the final cohort.

## 5. Data Dictionary (Excerpt)

| Variable | Source | Type | Description |
|:--- |:--- |:--- |:--- |
| `age` | Cyberbullying Survey 2021 | Numeric | Age in years |
| `gender` | Cyberbullying Survey 2021 | Categorical | Gender identity |
| `harassment_severity` | Cyberbullying Survey 2021 | Numeric | Sum of severity items |
| `harassment_exposure` | Derived | Binary | 1 if severity > 0, else 0 |
| `social_support` | Cyberbullying Survey 2021 | Numeric | Sum of support items |
| `depression` | CES-D | Numeric | Total CES-D score |
| `anxiety` | GAD-7 | Numeric | Total GAD-7 score |
| `ptsd` | PCL-5 | Numeric | Total PCL-5 score |

## 6. Exclusions

- **GSS 2022**: Explicitly excluded.
- **Dual-Dataset Interaction**: Not performed.
- **Synthetic Data**: Not permitted for final analysis.