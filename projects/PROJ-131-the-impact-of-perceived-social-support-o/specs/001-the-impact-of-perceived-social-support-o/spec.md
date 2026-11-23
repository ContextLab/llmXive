# Specification: The Impact of Perceived Social Support on Resilience to Online Harassment

## 1. Introduction
This project investigates the buffering effect of perceived social support on the relationship between online harassment and mental health outcomes.

## 2. Objectives
- Quantify the interaction between social support and harassment severity.
- Validate the single-dataset approach as methodologically superior to dual-dataset matching.

## 3. Data Dictionary
| Variable | Description | Source |
|:--- |:--- |:--- |
| social_support | Perceived social support score | Cyberbullying Survey 2021 (Sole Source) |
| harassment_severity | Continuous harassment severity score | Cyberbullying Survey 2021 (Sole Source) |
| harassment_exposure | Binary indicator (severity > 0) | Derived |
| depression | CES-D score | Cyberbullying Survey 2021 (Sole Source) |
| anxiety | GAD-7 score | Cyberbullying Survey 2021 (Sole Source) |
| ptsd | PCL-5 score | Cyberbullying Survey 2021 (Sole Source) |
| platform | Social media platform used | Cyberbullying Survey 2021 (Sole Source) |
| age | Age in years | Cyberbullying Survey 2021 (Sole Source) |
| gender | Gender identity | Cyberbullying Survey 2021 (Sole Source) |
| education | Education level | Cyberbullying Survey 2021 (Sole Source) |
| income | Income level | Cyberbullying Survey 2021 (Sole Source) |

## 4. Functional Requirements
- FR-001: [REMOVED - Methodologically Invalid] Dual-dataset matching (Synthetic Cohort) is excluded.
- FR-002: [REMOVED - Methodologically Invalid] GSS 2022 dataset is excluded.
- FR-003: Ingest Cyberbullying Survey 2021.
- FR-004: Apply MICE imputation for predictors.
- FR-005: Stratify by platform if N >= 30.
- FR-006: Score scales (CES-D, GAD-7, PCL-5).
- FR-007: Bootstrap with BCa CI.
- FR-008: Apply FDR correction.

## 5. Methodological Notes
### Revised Approach
This project strictly follows a **Single-Dataset Approach** using the Cyberbullying Survey 2021. The dual-dataset matching approach (Synthetic Cohort) was rejected as methodologically invalid due to confounding by dataset source. All variables are derived from this sole source to ensure the interaction term estimates a genuine psychological buffering effect.

### Rejection of Dual-Dataset Matching
The initial proposal for a "Synthetic Cohort" (matching Cyberbullying Survey data with GSS 2022) has been **REMOVED** and **DEPRECATED**. This approach is methodologically invalid because it confounds the effect of social support with the dataset source. The "Synthetic Cohort" is therefore **excluded** from this implementation.

### Data Integrity
No synthetic data generation is permitted. All analysis must be performed on real, observed data from the Cyberbullying Survey 2021.

## 6. Technical Context
- Python 3.9+
- pandas, numpy, statsmodels, scikit-learn
- Reproducible via `config/seeds.yaml`
