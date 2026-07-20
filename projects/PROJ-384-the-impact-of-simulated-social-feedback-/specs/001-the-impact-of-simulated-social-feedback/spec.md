# Feature Specification: The Impact of Simulated Social Feedback on Self-Esteem Fluctuations

**Feature Branch**: `001-the-impact-of-simulated-social-feedback-on-self-esteem-fluctuations`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "The Impact of Simulated Social Feedback on Self-Esteem Fluctuations - How does the rate of change in social feedback valence affect self-esteem fluctuations compared to the overall valence of social feedback in online social environments?"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Valence Sequencing (Priority: P1)

As a researcher, I need to download the LOST dataset and compute a time-series of feedback valence for each user session so that I can analyze the temporal dynamics of social interaction.

**Why this priority**: This is the foundational step. Without successfully ingesting the data and converting raw text interactions into a structured sequence of sentiment scores, no volatility metrics or regression analysis can be performed. It delivers the primary dataset required for the entire study.

**Independent Test**: Can be fully tested by running the data pipeline on a small subset (e.g., 100 posts) and verifying that a CSV output is generated containing `user_id`, `timestamp`, `post_text`, `reply_text`, and `calculated_valence` columns with no nulls in the valence column (except where the sentinel -999.0 is used for missing replies).

**Acceptance Scenarios**:

1. **Given** the LOST dataset is available in the project directory, **When** the ingestion script executes, **Then** the system outputs a processed CSV where every post has an associated list of reply sentiments derived via a pre-trained RoBERTa-based model.
2. **Given** a post with no replies, **When** the valence calculation runs, **Then** the system records a sentinel value of -999.0 in the `calculated_valence` column for that entry, preventing calculation errors while marking the data as missing.

---

### User Story 2 - Volatility Metric Calculation (Priority: P2)

As a researcher, I need to calculate specific metrics representing feedback volatility (e.g., standard deviation of rolling window valence, frequency of sign changes) for each user, so that I can quantify the "rate of change" in social feedback.

**Why this priority**: This directly addresses the core research gap (temporal dynamics vs. static valence). It transforms raw sentiment data into the specific independent variable required to test the hypothesis.

**Independent Test**: Can be tested by feeding a synthetic, known time-series of sentiments (e.g., `[1.0, -1.0, 1.0, -1.0]`) into the calculation module and verifying the output volatility score matches the expected mathematical derivation (high volatility) compared to a stable series (e.g., `[0.1, 0.1, 0.1]`).

**Acceptance Scenarios**:

1. **Given** a sequence of 10 consecutive replies with alternating positive/negative sentiment, **When** the volatility metric is computed, **Then** the resulting score is strictly higher than the score for a sequence of 10 identical positive sentiments.
2. **Given** a user with only one interaction, **When** the metric is computed, **Then** the system returns the sentinel value -999.0 and logs a warning, ensuring the regression model does not crash on low-data points.

---

### User Story 3 - Regression Analysis and Significance Testing (Priority: P3)

As a researcher, I need to run a multiple linear regression model controlling for overall valence to determine if feedback volatility significantly predicts self-esteem scores, so that I can validate the hypothesis that volatility drives instability.

**Why this priority**: This is the final analytical step that produces the research answer. It integrates the previous data and metrics into a statistical conclusion, fulfilling the project's primary scientific goal.

**Independent Test**: Can be tested by running the analysis script on a pre-generated synthetic dataset with known coefficients and verifying that the output includes the correct p-values, R² values, and coefficient estimates within a 1% margin of error.

**Acceptance Scenarios**:

1. **Given** the processed dataset with volatility and self-esteem scores, **When** the regression model is fitted, **Then** the output report includes a p-value for the volatility coefficient and an R² change metric indicating the variance explained by volatility beyond overall valence.
2. **Given** a model fit that fails to converge or has perfect collinearity, **When** the script executes, **Then** the system outputs a diagnostic error message and halts gracefully rather than producing silent incorrect results.

---

### Edge Cases

- What happens when the LOST dataset contains posts with missing timestamps or malformed reply threads? (System must skip these rows and log a count).
- How does the system handle users with extremely long feedback histories that might skew the rolling window average? (System must normalize or cap the window size).
- How does the system handle the case where the sentiment analysis tool returns a value of exactly 0.0 for a clearly emotional post? (System must treat 0.0 as neutral but record the raw text for manual review if the threshold is critical).

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and parse the LOST dataset from the specified arXiv source, extracting post text, reply text, and timestamps, and output a structured intermediate format. (See US-1)
- **FR-002**: System MUST calculate a sentiment score for every post and its associated replies using a pre-trained RoBERTa-based model fine-tuned on social media text, ensuring all valid scores are normalized to the [-1.0, 1.0] range. For missing replies, the system MUST record a sentinel value of -999.0. (See US-1)
- **FR-003**: System MUST compute at least two distinct feedback volatility metrics for each user: (a) the standard deviation of a rolling window of valence scores (primary window size = 5 interactions) and (b) the frequency of sign changes (positive to negative or vice versa) within the interaction sequence. If a user has fewer than 5 interactions, the system MUST use all available data (minimum 2 interactions) to compute the metric; if fewer than 2 interactions exist, the system MUST return the sentinel value -999.0. (See US-2)
- **FR-004**: System MUST execute a multiple linear regression model where the dependent variable is the self-esteem indicator score (derived from the user's post text using a validated self-esteem lexicon, e.g., Rosenberg-derived word list) and independent variables include overall mean valence (derived from replies), the computed volatility metrics, and relevant covariates (e.g., post length, user activity level). (See US-3)
- **FR-005**: System MUST perform statistical significance testing (t-tests) on the regression coefficients and generate a diagnostic report including p-values, R² values, and residual plots to validate model assumptions. (See US-3)
- **FR-006**: System MUST perform a sensitivity analysis on the primary rolling window size by re-running the volatility calculation and regression for window sizes {3, 5, 7} and reporting the variance in the volatility coefficient's p-value and magnitude. (See US-2)

### Key Entities

- **InteractionSequence**: A chronological list of text-based interactions (post + replies) associated with a single user session, containing raw text and derived sentiment scores.
- **VolatilityMetric**: A numerical value representing the rate of change in sentiment within an InteractionSequence, derived via statistical aggregation.
- **SelfEsteemIndicator**: A numerical score derived from the user's post text using a validated self-esteem lexicon (e.g., Rosenberg-derived word list), serving as the outcome variable.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The data ingestion pipeline successfully processes ≥ 95% of the available records in the LOST dataset without crashing, measured against the total record count in the source file. (See US-1)
- **SC-002**: The volatility calculation module produces non-null, finite numerical values for ≥ 90% of users with ≥ 3 interactions, measured against the total number of eligible users in the dataset. (See US-2)
- **SC-003**: The regression analysis completes within 60 minutes on a standard CPU-only environment (2 cores, 7GB RAM), measured against the system execution time limit. (See US-3)
- **SC-004**: The final report explicitly states the p-value for the volatility coefficient (e.g., p=0.XX), allowing a binary determination of significance against the threshold of p < 0.05. (See US-3)
- **SC-005**: The model diagnostics confirm that multicollinearity (Variance Inflation Factor) is < 5.0 for all independent variables; if VIF >= 5.0, the system MUST halt and log a diagnostic error. (See US-3)

## Assumptions

- **Assumption about data availability**: The LOST dataset (arXiv:2306.05596v1) is accessible via direct download without authentication barriers or rate limits that would exceed the 6-hour CI job limit.
- **Assumption about NLP tooling**: The pre-trained RoBERTa-based model (fine-tuned on social media text) is sufficient for deriving valid sentiment scores from Reddit text in this context, and its CPU-only execution will complete within the allocated job time limit for the full dataset.
- **Assumption about proxy validity**: The LOST dataset contains sufficient text content to derive the "self-esteem indicator" via a validated self-esteem lexicon (e.g., Rosenberg-derived word list); however, this is acknowledged as a proxy with potential measurement error, and the sensitivity analysis (FR-006) is designed to assess robustness.
- **Assumption about statistical framing**: Since this is an observational study using existing social media data, the analysis will frame all findings as associational correlations rather than causal effects, acknowledging the lack of random assignment.
- **Assumption about compute resources**: The dataset size is small enough to fit entirely into the available RAM of the GitHub Actions free-tier runner, allowing for in-memory processing without chunking.