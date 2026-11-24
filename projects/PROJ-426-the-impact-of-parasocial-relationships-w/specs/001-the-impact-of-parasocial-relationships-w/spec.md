# Feature Specification: The Impact of Parasocial Relationships with AI Companions on Loneliness

**Feature Branch**: `001-ai-companion-loneliness-impact`  
**Created**: 2026-06-24  
**Status**: Draft  
**Input**: User description: "The Impact of Parasocial Relationships with AI Companions on Loneliness"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Ingestion and User Matching (Priority: P1)

The system MUST successfully ingest the *Reddit Loneliness Longitudinal Dataset* and the *Pushshift Reddit* interaction logs, then match users across both sources using hashed Reddit usernames to create a unified analysis-ready dataset.

**Why this priority**: Without a unified dataset linking behavioral logs to self-reported loneliness scores, no statistical analysis can be performed. This is the foundational data layer for the entire study.

**Independent Test**: Can be fully tested by executing the data pipeline on a sample subset (e.g., first 100 users) and verifying that the output table contains matched records with non-null values for both loneliness scores and usage metrics.

**Acceptance Scenarios**:

1. **Given** the raw Zenodo dataset and Pushshift archive are accessible, **When** the ingestion script runs, **Then** the output CSV contains at least **600** matched user records (justified by the required sample size for adequate statistical power) with columns for `user_id`, `loneliness_score`, `usage_frequency`, and `session_duration`.
2. **Given** a user exists in the loneliness dataset but has no corresponding Pushshift logs, **When** the matching process runs, **Then** that user is excluded from the final analysis dataset to prevent null-value errors in the mixed-effects model.
3. **Given** the input datasets contain sensitive PII, **When** the matching process runs, **Then** only hashed usernames are used, and the original usernames are never written to the output file or logs.

---

### User Story 2 - Feature Engineering and Attachment Proxy Extraction (Priority: P2)

The system MUST compute per-user weekly metrics (usage frequency, session duration) and extract an attachment‑style proxy using the **ECAR Lexicon (Emotion and Coping in AI Relationships)** from baseline posts to serve as control variables.

**Why this priority**: The research hypothesis explicitly requires controlling for attachment style. Without this feature, the model cannot distinguish between the effect of AI usage and pre‑existing attachment dispositions.

**Independent Test**: Can be fully tested by running the feature engineering script on a fixed set of 10 known user posts and verifying that the calculated attachment scores match manual calculations based on the lexicon.

**Acceptance Scenarios**:

1. **Given** a user's baseline posts are available, **When** the lexicon scan runs, **Then** the system outputs a numeric `attachment_anxiety_score` and `attachment_avoidance_score` derived from the frequency of specific terms (e.g., "fear," "avoid," "trust").
2. **Given** a user has multiple AI‑related activities within a 7‑day window, **When** the aggregation runs, **Then** the system calculates the `session_duration` as the time difference between the first and last timestamp of consecutive activities, capped at a fixed duration per session.
3. **Given** a user has no baseline posts, **When** the feature extraction runs, **Then** the system excludes the user from the analysis dataset (rather than imputing a neutral score) to prevent invalid statistical controls.

---

### User Story 3 - Mixed-Effects Modeling and Robustness Validation (Priority: P3)

The system MUST fit a linear mixed-effects model predicting loneliness changes from usage metrics and attachment style (using a lagged structure), and perform bootstrap resampling to generate robust confidence intervals.

**Why this priority**: This is the core analytical engine that produces the research findings. It must handle the longitudinal nature of the data and provide statistically valid inferences.

**Independent Test**: Can be fully tested by running the model on a synthetic dataset with known coefficients and verifying that the estimated coefficients fall within the 95% confidence interval of the true values.

**Acceptance Scenarios**:

1. **Given** the unified dataset with ≥600 user‑observations, **When** the model fits, **Then** the output includes fixed effect estimates for `UsageFrequency` and `SessionDuration` and their corresponding p‑values.
2. **Given** the model assumptions (normality, homoscedasticity) are violated, **When** the diagnostic checks run, **Then** the system triggers the bootstrap resampling to generate corrected confidence intervals.
3. **Given** the analysis completes, **When** the robustness check for age moderation runs, **Then** the system produces a separate model summary for users aged ≥ 60, comparing the effect sizes against the full population model.

---

### Edge Cases

- What happens when the Pushshift API rate limits are hit during log retrieval? (System must implement exponential backoff with multiple retries and a 30‑second timeout per request).
- How does the system handle users with missing attachment style proxies? (They are excluded from the analysis dataset to prevent invalid statistical controls).
- What if the number of matched users is insufficient for the mixed‑effects model (e.g., < 600 users)? (The system must halt execution and report a **"Power Insufficient"** error, preventing a false negative result).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST collect a **Reddit Loneliness Survey Dataset** by recruiting participants from the target subreddits, administering the UCLA Loneliness Scale (Version 3) and collecting baseline post text; the resulting dataset must be deposited in Zenodo () and contain at least **600 participants** with **≥ 6 distinct calendar months** of non‑null loneliness scores per user (See US-1). *Justification*: a self‑reported, validated loneliness measure is essential to answer the research question (methodology scope concern). Required columns: `UCLA_Loneliness_Score`, `timestamp`, `username_hash`, `baseline_text`, `baseline_mental_health_score`, `ses_index`.
- **FR-002**: System MUST retrieve AI interaction logs from the Pushshift API endpoint `https://api.pushshift.io/reddit/search/submission/?subreddit={subreddit}&size=500&before={timestamp}&after={timestamp}` for subreddits `r/Replika`, `r/characterAI`, and `r/AICompanions`, ensuring logs cover the exact calendar window defined by the earliest and latest survey timestamps in the matched user set, specifically the period strictly preceding the survey dates to support the lagged structure (See US-1).
- **FR-003**: System MUST match users across datasets using SHA‑256 hashed usernames to preserve anonymity while enabling longitudinal linking (See US-1).
- **FR-004**: System MUST compute weekly usage metrics (frequency and session duration) and extract attachment‑style proxies using the **ECAR Lexicon (Emotion and Coping in AI Relationships)** on baseline posts, scoring via normalized term frequency, **only if** the raw text of baseline posts is present in the dataset (See US-2).
- **FR-004b**: System MUST exclude any user from the final analysis dataset if the lexicon extraction fails for that user (e.g., due to missing baseline text or processing error), ensuring no imputed neutral scores are used as control variables (See US-2). *Note*: If the ECAR Lexicon file itself is missing, FR-008 governs the response.
- **FR-005**: System MUST fit a linear mixed‑effects model with random intercepts for `User` and random slopes for `UsageFrequency` by `User`, controlling for attachment style, using a lagged predictor structure (usage at T predicts loneliness at T+1) where T is strictly prior to T+1 (See US-3).
- **FR-006**: System MUST perform bootstrap resampling with a sufficiently large number of iterations (e.g., on the order of thousands) and a fixed random seed (seed = 42) to generate robust 95% confidence intervals for all model coefficients (See US-3).
- **FR-007**: System MUST execute a subgroup analysis for users aged ≥ 60 (derived from the demographics table; users with missing age are excluded from this specific subgroup analysis) to test for age moderation effects (See US-3).
- **FR-008**: System MUST detect if the **ECAR Lexicon** is missing or invalid and immediately halt execution with a "Lexicon Missing" error, preventing the use of a fallback keyword‑based proxy that lacks validation (See US-2).
- **FR-009**: System MUST validate that the **Reddit Loneliness Survey Dataset** contains the raw text of baseline posts required for the lexicon scan; if the text is missing, the system MUST exclude those users from the analysis (See US-2).

### Key Entities

- **UserProfile**: Represents a matched individual with a hashed ID, attachment style scores, and age.
- **LongitudinalRecord**: Represents a single time‑point observation for a user, containing loneliness score, usage frequency, and session duration.
- **ModelResult**: Represents the output of the statistical analysis, containing fixed effects, p‑values, and confidence intervals.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation phase.

- **SC-001**: The proportion of users successfully matched between the loneliness dataset and Pushshift logs is measured against the total number of unique users in the loneliness dataset; success is defined as a match rate ≥ 80% (See US-1).
- **SC-002**: The variance explained (marginal R²) by the mixed‑effects model is measured against a baseline intercept‑only model; success is defined as an increase in marginal R² ≥ 0.05 (See US-3).
- **SC-003**: The stability of the model coefficients is measured against the bootstrap confidence intervals; if the interval includes zero, the effect is deemed non‑significant (See US-3).
- **SC-004**: The computational runtime of the bootstrap resampling is measured against the GitHub Actions free‑tier constraint (≤ 6 hours execution time); success is defined as completion within this limit without resource exhaustion (See US-3).
- **SC-005**: Attachment‑style proxy extraction accuracy is measured against a manually annotated validation set of 20 users; success is defined as ≥ 90% agreement (Cohen’s κ ≥ 0.8) between automated scores and human annotations (See US-2).
- **SC-006**: The collected Reddit Loneliness Survey Dataset must contain ≥ 600 participants and ≥ 6 months of longitudinal loneliness scores per user; success is defined as meeting both thresholds (See US-1). (See US-1)

## Assumptions

- The **Reddit Loneliness Survey Dataset** will be collected as described in FR‑001 and will contain the variables `UCLA_Loneliness_Score`, `timestamp`, `username_hash`, and **raw text of baseline posts**. If any of these fields are missing for a user, that user will be excluded from the analysis dataset (see FR‑009).
- The **ECAR Lexicon** is a validated, citable instrument available in the project repository; if not, the analysis will halt with a "Lexicon Missing" error (see FR‑008).
- The Pushshift API endpoint ` remains accessible and rate‑limited to a maximum of 100 requests/minute without requiring authentication.
- The analysis is observational; therefore, all findings regarding the relationship between AI usage and loneliness are framed as **associational**, not causal, to avoid inference framing violations.
- The sample size of the matched dataset is sufficient (n ≥ 600) to achieve statistical power for a mixed‑effects model with the expected effect size (Cohen's d ≥ 0.5); if the sample is smaller, the study will report a power limitation and halt.
- The linear mixed‑effects model and bootstrap resampling can be executed within the GitHub Actions free‑tier constraints (CPU cores, ~7 GB RAM, ≤ 6 hours) without GPU acceleration.