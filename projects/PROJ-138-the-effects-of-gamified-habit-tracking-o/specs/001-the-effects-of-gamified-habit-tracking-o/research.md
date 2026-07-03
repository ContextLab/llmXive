# Research: The Effects of Gamified Habit Tracking on Long-Term Behavioral Change

## Research Question
Does the inclusion of game-like elements (points, badges, leaderboards) in habit-tracking applications produce higher long-term adherence to self-defined behavioral goals than non-gamified habit-tracking, and how is this effect moderated by individual personality traits such as conscientiousness and need for achievement?

## Dataset Strategy

### Primary Dataset Status: No Verified Public Source
**Critical Finding**: There is **no verified public longitudinal dataset** currently available that contains the triad of required variables: (1) detailed habit-tracking event logs, (2) explicit gamification status (or app tags), and (3) personality trait scores (Big Five).
- **MyPersonality**: Rejected (cross-sectional, no logs).
- **Habitica API**: Not a verified public dataset for research; requires authentication and does not provide personality data.
- **Action**: The pipeline defaults to a **Synthetic Data Generator** for the `code/` pipeline to ensure the statistical logic is correct and reproducible. This run is strictly a **Methodological Validation**. It does not claim to answer the research question with empirical evidence.

### Synthetic Data Generative Model
To ensure the pipeline is not validating a tautology, the synthetic data is generated with a known "ground truth":
1.  **User Traits**: `conscientiousness` and `achievement` are drawn from a standard normal distribution.
2.  **Gamification**: `gamification_status` is assigned (50/50 split) to ensure independence from initial traits.
3.  **Adherence Process**: `weekly_adherence` is generated via a logistic function:
    `logit(p) = β0 + β1*Gamified + β2*Conscientiousness + β3*(Gamified*Conscientiousness) + ε`
    where `β3` (interaction) is set to a fixed value (e.g., 0.2) to simulate a moderate effect.
4.  **Dropout Logic**: Dropout is simulated as a hazard function where `h(t) = h0(t) * exp(γ1*Gamified + γ2*Conscientiousness)`.
    - **Crucial Distinction**: The generator produces "gaps" (missing weeks) and "dropouts" (permanent cessation) separately. A user may have a 3-week gap but resume activity later; this is **not** a dropout. Only permanent cessation (no activity for remaining weeks) is a dropout event. This prevents the circular logic of "0 events = dropout".

### Variable Mapping
| Variable | Source/Generation | Type | Role |
| :--- | :--- | :--- | :--- |
| `user_id` | Synthetic / API | ID | Primary Key |
| `gamification_status` | Derived from `app_id` tags or simulation | Binary (0/1) | Independent Variable |
| `conscientiousness_score` | Synthetic (Normal dist) or API | Continuous | Moderator |
| `achievement_score` | Synthetic (Normal dist) or API | Continuous | Moderator (if available) |
| `event_date` | Synthetic / API | Date | Time Index |
| `last_active_date` | Derived | Date | Censoring/Event Time |
| `weekly_adherence_flag` | Aggregated from `event_date` | Binary | Dependent Variable |
| `dropout_event` | Derived (3 weeks non-adherence, no resumption) | Binary | Survival Outcome |

## Methodological Rationale

### 1. Data Aggregation Strategy
Daily logs will be binned into weeks (`week_number` 1..N).
- **Missing vs. Dropout**: A week with no events is `weekly_adherence_flag=0`.
    - If the user has activity in a later week, the gap is treated as **Missing at Random (MAR)** or a temporary lapse, not a dropout.
    - If the user has **no activity** from week `t` to the end of the observation window (and `t` is >= 3 consecutive zeros), it is a **Dropout Event**.
    - **Censoring**: Users who complete the study or are lost to follow-up (no activity but study ends) are censored at `last_active_date` or `study_end`.

### 2. Statistical Modeling: Mixed-Effects Logistic Regression
**Model**: `logit(P(adherence)) = β0 + β1*Gamified + β2*Conscientiousness + β3*(Gamified*Conscientiousness) + u_user + ε`
- **Fixed Effects**: Gamification status, Personality traits, Interaction terms.
- **Random Effects**: Random intercepts for `user_id`.
- **Multiple Comparison Correction (FR-007)**: If multiple traits (e.g., Conscientiousness, Achievement, Extraversion) are tested, the Benjamini-Hochberg (FDR) procedure will be applied to the interaction p-values.
- **Limitation**: The binary outcome reduces rich data. As a robustness check, the pipeline will also compute event counts per week to assess if a Zero-Inflated Poisson (ZIP) model is more appropriate (though not the primary model).

### 3. Survival Analysis: Time-to-Dropout
**Definition of Dropout**: 3 consecutive weeks of `weekly_adherence_flag` == 0 **AND** no subsequent activity in the observation window.
**Method**: Kaplan-Meier estimator and Cox Proportional Hazards model.
- **Stratification**: By Conscientiousness quartiles.
- **Event Count Check (FR-009)**: Before running Cox models, the system counts dropout events per group. If < 10 events in any group, the survival analysis is halted, and only descriptive statistics (Kaplan-Meier curves without p-values) are reported.
- **Censoring**: Users who do not drop out by the end of the study are censored at `study_end`.

### 4. Robustness & Validation
- **Bootstrapping**: A sufficient number of iterations to generate a confidence interval for the gamification effect size.
- **Cross-Validation**: Leave-One-User-Out (LOUO) to assess predictive stability.
- **Sensitivity Analysis**: Varying the adherence threshold (e.g., 1 vs 2 events/week) to test stability of results.

### 5. Power & Sample Size Limitation
- **Acknowledgement**: N=100 is statistically **underpowered** to detect moderate interaction effects (Gamification × Conscientiousness) in mixed-effects models with random intercepts.
- **Implication**: The study is **exploratory**. If real data is obtained, non-significant results cannot rule out the hypothesis. The synthetic data run validates the *pipeline's ability to recover known parameters*, not the empirical truth of the hypothesis.

## Decision Log & Assumptions

| Decision | Rationale |
| :--- | :--- |
| **Use Synthetic Data for Default Run** | No verified longitudinal dataset URL is available. The synthetic generator is tuned to a known effect size to validate the pipeline logic. |
| **Dropout Definition = 3 Weeks + No Resumption** | Distinguishes temporary lapses from true dropout. Prevents circular logic where "0 events" automatically equals "dropout". |
| **Non-Gamified Group Definition** | Defined as users with `gamification_status=0` (self-reported or tag-based). If the dataset is from a single gamified platform, the "control" is "low usage" or "non-gamified features", acknowledging potential endogeneity. |
| **Construct Validity Limitation** | Personality traits are assumed stable. This ignores regression to the mean or state-dependent error. This is explicitly noted as a limitation in the final report. |
| **CPU-Only Implementation** | GitHub Actions free tier has no GPU. `statsmodels` and `lifelines` are CPU-optimized. |

## Ethical & Legal Considerations
- **Consent**: The pipeline enforces `FR-010` by checking for `data/consent/` artifacts.
- **Anonymization**: All `user_id` values are hashed or synthetic. No PII is stored.
- **Psychometrics**: Cronbach's α will be calculated if real scale data is used; for synthetic data, the theoretical value is logged to demonstrate the metric's existence.