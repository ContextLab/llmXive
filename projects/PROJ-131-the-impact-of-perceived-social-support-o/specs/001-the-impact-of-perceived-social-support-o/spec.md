# Specification: The Impact of Perceived Social Support on Resilience to Online Harassment

## 1. Introduction
This project investigates the relationship between perceived social support and resilience to online harassment, specifically examining whether social support buffers the negative mental health impacts of harassment.

## 2. User Stories
- **US1**: As a researcher, I want to ingest and prepare the Cyberbullying Survey 2021 dataset so that I can analyze the relationship between social support and mental health outcomes.
- **US2**: As a researcher, I want to fit regression models with interaction terms and bootstrap confidence intervals to test the buffering hypothesis.
- **US3**: As a researcher, I want to perform sensitivity analyses (continuous severity, platform stratification) to ensure robustness of findings.

## 3. Functional Requirements
- **FR-001**: [REMOVED per Plan's Critical Methodological Pivot] The dual-dataset matching approach was found to introduce confounding and is methodologically invalid for interaction analysis.
- **FR-002**: [REMOVED per Plan's Critical Methodological Pivot] The synthetic cohort construction is excluded.
- **FR-003**: Ingest the Cyberbullying Survey 2021 dataset.
- **FR-004**: Apply MICE imputation for predictor variables and handle outcome missingness via listwise deletion.
- **FR-005**: Stratify analyses by platform for groups with N >= 30.
- **FR-006**: Score standard psychological scales (CES-D, GAD-7, PCL-5).
- **FR-007**: Use BCa bootstrap with 1,000 resamples.
- **FR-008**: Apply Benjamini-Hochberg FDR correction.

## 4. Data Dictionary
| Variable | Description | Source |
|:--- |:--- |:--- |
| `social_support` | Perceived social support score | Cyberbullying Survey 2021 (Sole Source) |
| `harassment_severity` | Continuous harassment severity score | Cyberbullying Survey 2021 (Sole Source) |
| `harassment_exposure` | Binary indicator (severity > 0) | Derived from Cyberbullying Survey 2021 |
| `depression` | CES-D total score | Cyberbullying Survey 2021 (Sole Source) |
| `anxiety` | GAD-7 total score | Cyberbullying Survey 2021 (Sole Source) |
| `ptsd` | PCL-5 total score (if available) | Cyberbullying Survey 2021 (Sole Source) |
| `platform` | Social media platform used | Cyberbullying Survey 2021 (Sole Source) |
| `age`, `gender`, `education`, `income` | Demographic covariates | Cyberbullying Survey 2021 (Sole Source) |

## 5. Methodological Notes

### The Revised Approach (Single-Dataset)
The project strictly uses the **Cyberbullying Survey 2021** alone as the data source for all analyses.

**Rejection of Dual-Dataset Matching**: The dual-dataset matching approach (previously proposed to construct a "Synthetic Cohort" by matching Cyberbullying Survey respondents with GSS 2022 participants) was **rejected as methodologically invalid**.

**Reasoning**: Matching on observed covariates while leaving unobserved confounders (such as dataset-specific survey administration effects, sampling frames, and temporal context) creates a situation where **Harassment Exposure is perfectly confounded with Dataset Source**. In such a design, any observed interaction effect between social support and harassment could be driven by unmeasured differences between the two datasets rather than a genuine psychological buffering mechanism.

**Implementation**: Consequently, the analysis pipeline ingests only the Cyberbullying Survey 2021. All statistical models (OLS with interaction terms, bootstrap CIs, FDR correction) are fit on this single, internally consistent dataset. This ensures that the interaction term estimates a genuine psychological buffering effect within the population sampled by the Cyberbullying Survey, free from confounding by dataset source.

### Validation Criteria (Revised SC-001)
- **Variance Check**: The analysis cohort must exhibit sufficient variance in Harassment Exposure (SD > 0.5, N > 30).
- **Collinearity Check**: Variance Inflation Factor (VIF) for model predictors must be < 5.
- **Note**: The Standardized Mean Difference (SMD) check for synthetic cohort balance is **inapplicable** and removed from the validation criteria.