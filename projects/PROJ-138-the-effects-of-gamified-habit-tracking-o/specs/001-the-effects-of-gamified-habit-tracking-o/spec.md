# Feature Specification: The Effects of Gamified Habit Tracking on Long-Term Behavioral Change

**Feature Branch**: `001-gamification-effects`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Research question: Does the inclusion of game‑like elements (points, badges, leaderboards) in habit‑tracking applications produce higher long‑term adherence to self‑defined behavioral goals than non‑gamified habit‑tracking, and how is this effect moderated by individual personality traits such as conscientiousness and need for achievement?"

## Data Source Rejection Log
> **Rejection of MyPersonality Dataset**: The initial hypothesis proposed using the MyPersonality dataset. This was rejected because MyPersonality is a cross-sectional survey (one-time snapshot) containing Facebook usage data and Big Five traits, but lacks the required longitudinal habit-tracking logs (weekly adherence, time-to-event data). A mixed-effects model or survival analysis requires repeated measures per user (N>1), which this dataset cannot provide.
> **Pivot to Verified Source**: The pipeline now targets the **Habitica API** (or equivalent verified longitudinal mobile health dataset) which provides event-based logs of user activity, allowing for the construction of weekly adherence metrics and valid time-to-event analysis.

## User Scenarios & Testing

### User Story 1 - Data Acquisition, Validation, and Aggregation (Priority: P1)

The research pipeline MUST ingest data from a verified longitudinal source (e.g., Habitica API), validate the existence of required fields, and aggregate daily event logs into weekly bins to produce a unified analysis-ready dataset. The system MUST define "gamified" users as those with activity logs in apps tagged with gamification features and "non-gamified" users as those with no such activity or activity in non-gamified tools.

**Why this priority**: Without a valid, unified dataset containing both behavioral adherence metrics and personality predictors from a longitudinal source, no statistical analysis can be performed. This is the foundational step for the entire study.

**Independent Test**: The pipeline can be tested by running the data ingestion script on a sample of the Habitica API and verifying that the output CSV contains unique user IDs with non-null values for gamification status, weekly adherence counts, and personality scores (if linked or simulated for the test).

**Acceptance Scenarios**:
1. **Given** the longitudinal dataset is available in the designated input directory (or API endpoint), **When** the ingestion script is executed, **Then** a single merged CSV file is generated containing all available valid user records with no missing values in the primary predictor (gamification status) or outcome (weekly adherence count) columns. The target is to maximize sample size, with a minimum viability threshold of ≥ 100 valid user records.
2. **Given** a user record exists in the dataset, **When** the data cleaning logic is applied, **Then** the record is flagged as "gamified" if the user has activity logs in gamified apps, "non-gamified" if they have logs in non-gamified tools or no logs, or excluded if the habit tracking data is missing.
3. **Given** the raw daily logs, **When** the aggregation logic is executed, **Then** the system generates a `week_number` column (sequential integers starting at 1) and a `weekly_adherence_flag` (binary: 1 if ≥ 1 activity event in the week, 0 otherwise) for each user, ensuring the time-series structure is valid for longitudinal modeling.

---

### User Story 2 - Statistical Modeling and Interaction Analysis (Priority: P2)

The system MUST fit a mixed-effects logistic regression model to predict weekly adherence, including fixed effects for gamification, personality traits (Conscientiousness, and "need for achievement" if available), and their interaction, along with random intercepts for users. The system MUST define "dropout" as 3 consecutive weeks of non-adherence to distinguish from temporary lapses.

**Why this priority**: This is the core analytical engine that directly addresses the research question regarding the moderation effect of personality on gamification efficacy.

**Independent Test**: The modeling script can be tested by running it against a synthetic longitudinal dataset with known interaction coefficients and verifying that the model recovers the interaction term within an acceptable margin of error (coefficient variance < 0.01).

**Acceptance Scenarios**:
1. **Given** the merged longitudinal dataset, **When** the mixed-effects model is fitted, **Then** the output includes a coefficient estimate and p-value for the interaction term between `Gamified_Binary` and `Conscientiousness_Score`. If "need for achievement" is available, the interaction term for this trait is also included.
2. **Given** the fitted model, **When** the analysis is executed, **Then** the output includes a hazard ratio or derived metric comparing time-to-dropout (defined as 3 consecutive weeks of non-adherence) for high-conscientiousness users in gamified vs. non-gamified conditions.
3. **Given** the model convergence, **When** the leave-one-user-out cross-validation is performed, **Then** the average AUC across folds is reported, and the variance across folds remains within acceptable bounds (variance < 0.05).

---

### User Story 3 - Robustness Validation and Reporting (Priority: P3)

The system MUST execute internal robustness checks (bootstrapping) to validate findings and generate a final report containing visualizations of usage trajectories and survival curves. If a compatible external dataset is available, the system MAY re-run the analysis, but this is not mandatory.

**Why this priority**: Internal validation ensures the findings are not artifacts of the specific sample, and visualizations are required for the final research output.

**Independent Test**: The validation script can be tested by running the analysis pipeline on a bootstrapped sample and verifying that the generated report includes a section comparing effect sizes across bootstrap iterations.

**Acceptance Scenarios**:
1. **Given** the merged dataset, **When** the bootstrapping procedure is executed, **Then** a comparison table is generated showing the distribution of the gamification effect size across 1,000 bootstrap samples.
2. **Given** the final model results, **When** the report generation script is executed, **Then** a PDF/HTML report is produced containing a Kaplan-Meier survival curve (based on the 3-week dropout definition) stratified by personality quartiles and a line plot of weekly adherence trajectories.
3. **Given** the full analysis, **When** the sensitivity analysis for the adherence threshold is run, **Then** the report includes a table showing the stability of the effect size (coefficient variance) across a range of thresholds for the primary outcome definition.

---

### Edge Cases

- **What happens when** the data ingestion yields fewer than 100 valid user records?
  - **System handles**: The pipeline logs a critical warning, halts the main analysis, and outputs a "Data Insufficiency" report recommending the study cannot proceed with statistical validity.
- **How does system handle** users with zero adherence weeks (complete dropouts) in the survival analysis?
  - **System handles**: These users are censored at their last known active timestamp (or at week 0 if they never started); the survival curve explicitly marks the censoring time to avoid bias in the hazard ratio calculation.
- **What happens when** the mixed-effects model fails to converge due to collinearity between personality traits?
  - **System handles**: The system automatically detects the Variance Inflation Factor (VIF) > 5, removes one of the collinear traits (prioritizing Conscientiousness as the primary moderator), re-runs the model, and logs the removal in the methodology section of the report.
- **What happens when** the number of observed dropout events is < 10 per group?
  - **System handles**: The system halts the survival analysis, logs a "Insufficient Events" warning, and outputs a descriptive statistics report instead of p-values, noting the exploratory nature of the findings.

## Requirements

### Functional Requirements

- **FR-001**: System MUST ingest data from a verified longitudinal source (e.g., Habitica API), ensuring every record contains a unique User_ID and non-null values for Gamified status (derived from app tags) and Adherence metrics (See US-1).
- **FR-001a**: System MUST validate the existence of `gamified_app_usage` or equivalent tags in the source data; if missing, the system MUST halt and report "Data Schema Mismatch" (See US-1).
- **FR-001b**: System MUST aggregate daily event logs into weekly bins, generating a `week_number` column (sequential integers ≥ 1) and a `weekly_adherence_flag` (binary) for each user, ensuring the data structure supports longitudinal modeling (See US-1).
- **FR-002**: System MUST fit a mixed-effects logistic regression model predicting weekly adherence with fixed effects for gamification, conscientiousness, and the interaction terms. If "need for achievement" is available in the dataset, it MUST be included as a fixed effect; otherwise, the system MUST log the omission and proceed with Conscientiousness only (See US-2).
- **FR-003**: System MUST perform survival analysis (Kaplan-Meier and Cox proportional hazards) to compare time-to-dropout (defined as 3 consecutive weeks of non-adherence) between gamified and non-gamified groups, stratified by Conscientiousness quartiles (and "need for achievement" quartiles if available) (See US-2).
- **FR-004**: System MUST perform leave-one-user-out cross-validation on the predictive models and execute a bootstrapping procedure (1,000 iterations) to validate robustness. External validation on a compatible dataset is OPTIONAL (See US-3).
- **FR-005**: System MUST generate a final report containing visualizations of usage trajectories, survival curves (based on the 3-week dropout definition), and a sensitivity analysis table for the adherence decision threshold (See US-3).
- **FR-006**: System MUST frame all reported findings as associational rather than causal, explicitly noting the observational nature of the data in the final output (See US-2).
- **FR-007**: System MUST implement a multiple-comparison correction (e.g., Bonferroni or FDR) for all hypothesis tests involving multiple personality traits or interaction terms. Correction MUST NOT be applied to time points (weeks) as they are modeled as repeated measures within the hierarchical framework (See US-2).
- **FR-008**: System MUST explicitly define the "non-gamified" control group as users who self-reported using non-gamified habit tracking methods or no tracking at all, and ensure the group size is ≥ 30 users (See US-2).
- **FR-009**: System MUST validate that the number of observed dropout events is ≥ 10 per group before performing survival analysis; if events < 10, the system MUST report descriptive statistics and halt p-value calculation (See US-2).
- **FR-010**: System MUST verify the presence of original consent documentation in the `data/consent/` directory before ingesting any user data, and halt if artifacts are missing (Constitution Principle VI) (See US-1).
- **FR-011**: System MUST calculate and report Cronbach's α for the personality scales used in the study to document psychometric validity (Constitution Principle VII) (See US-2).

### Key Entities

- **User Profile**: Represents an anonymized individual, containing attributes: `user_id`, `gamification_status` (binary, derived from app tags), `conscientiousness_score`, `achievement_score`.
- **Behavioral Log**: Represents a daily record of user activity, containing attributes: `user_id`, `date`, `event_type`, `app_id`.
- **Weekly Aggregation**: Represents a weekly summary, containing attributes: `user_id`, `week_number`, `adherence_flag` (binary), `streak_length`.
- **Analysis Result**: Represents the output of a statistical test, containing attributes: `test_type`, `coefficient`, `p_value`, `confidence_interval`, `sample_size`.

## Success Criteria

- **SC-001**: The merged dataset MUST contain a minimum of 100 valid user records with non-null values for all primary variables, measured against the input dataset sizes (See US-1).
- **SC-002**: The system MUST calculate and report the p-value for the interaction term between gamification and conscientiousness, measured against the null hypothesis of no interaction (See US-2).
- **SC-003**: The system MUST perform the Log-rank test comparing time-to-dropout between high-conscientiousness users in gamified vs. non-gamified conditions and report the test statistic and p-value, provided there are ≥ 10 events per group (See US-2).
- **SC-004**: The bootstrapping procedure MUST generate a sufficient number of resamples. and report the 95% confidence interval for the gamification effect size, with a coefficient variance < 0.01 across samples (See US-3).
- **SC-005**: The sensitivity analysis MUST report the stability of the effect size (coefficient variance) across a set of representative thresholds, measured against the baseline effect size at the standard threshold (See US-3).

## Assumptions

- The dataset used is a verified longitudinal source (e.g., Habitica API) containing event-based logs, NOT the cross-sectional MyPersonality dataset.
- The "gamified" status is a binary attribute derived from app tags or self-report in the longitudinal dataset and does not require manual labeling of individual user interfaces.
- The adherence metric (weekly activity flag) is a valid proxy for long-term behavioral change, as validated by the community standards in the related work literature.
- The analysis will be performed on a CPU-only environment; therefore, any heavy machine learning models (e.g., deep neural networks) are out of scope, and the study relies on classical statistical methods (mixed-effects regression, survival analysis).
- The personality trait scores (Big Five) are stable over the observation period and do not require longitudinal measurement updates.
- The "need for achievement" score is available as a distinct variable in the dataset; if only the Big Five is present, the analysis will use Conscientiousness as the primary moderator and treat "need for achievement" as a secondary or derived metric (logged as per FR-002).
- The "non-gamified" control group consists of users who reported using non-gamified tracking methods or no tracking, ensuring a valid comparison within the same population.
- "Dropout" is strictly defined as 3 consecutive weeks of non-adherence to distinguish from temporary lapses.