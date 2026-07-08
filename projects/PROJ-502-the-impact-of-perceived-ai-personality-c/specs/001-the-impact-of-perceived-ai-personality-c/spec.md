# Feature Specification: The Impact of Perceived AI Personality Consistency on User Trust

**Feature Branch**: `001-ai-personality-consistency-trust`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Research on whether perceived personality consistency in AI chatbots predicts user trust levels across multiple interaction sessions using public datasets and CPU-tractable NLP metrics."

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Session Extraction (Priority: P1)

The system MUST successfully download the specified public dataset (DailyDialog), filter for valid conversation sessions containing at least 3 turns, and persist the raw text data for analysis.

**Why this priority**: Without a clean, filtered dataset, no subsequent analysis of consistency or trust can occur. This is the foundational step.

**Independent Test**: Can be fully tested by running the data loader script on a small, hardcoded subset of 10 sessions. The test verifies that:
1. All sessions with <3 turns are excluded.
2. All sessions with ≥3 turns are included.
3. No null values exist in the text fields of the output.
4. The output file structure matches the expected JSON/CSV schema.

**Acceptance Scenarios**:

1. **Given** the DailyDialog dataset is available via HuggingFace, **When** the ingestion script runs, **Then** a local data file is created containing exactly the subset of sessions with ≥3 turns and no missing text fields.
2. **Given** a corrupted or incomplete download, **When** the ingestion script runs, **Then** the system retries up to 3 times and fails gracefully with a clear error message if the data integrity check (row count > 0) fails.

---

### User Story 2 - Consistency and Trust Metric Computation (Priority: P2)

The system MUST compute a "Personality Consistency Score" (variance of sentiment + variance of lexical diversity) and "Trust Indicators" (interaction length, session frequency, and user ratings) for every user session identified in User Story 1.

**Why this priority**: This is the core analytical engine. It transforms raw text into the quantitative variables required to test the research hypothesis.

**Independent Test**: Can be fully tested by running the computation module on a hardcoded reference dataset of 10 conversations where the Type-Token Ratio (TTR) and sentiment variance are pre-calculated using the exact specified formulas. The test verifies that the output metrics match the reference values within an acceptable tolerance.

**Acceptance Scenarios**:

1. **Given** a session with 3 distinct AI responses, **When** the metric engine runs, **Then** it outputs a sentiment variance score and a lexical diversity score (type-token ratio) for that session.
2. **Given** a user with multiple sessions over time, **When** the metric engine runs, **Then** it calculates the session frequency (days between sessions), total interaction length (cumulative word count), and average user rating (if available).
3. **Given** a response that triggers a sentiment model error, **When** the engine runs, **Then** it skips the specific response, logs the error, and proceeds without crashing the entire batch.

---

### User Story 3 - Statistical Analysis and Reporting (Priority: P3)

The system MUST perform Generalized Linear Models (GLM) with Poisson/Negative Binomial distributions for count data and Survival Analysis for time-to-event data, controlling for interaction count and duration, and generate visualizations.

**Why this priority**: This delivers the final research answer and visual evidence required to validate or refute the hypothesis using statistically appropriate methods for the data types.

**Independent Test**: Can be fully tested by running the analysis script on a synthetic mock dataset generated with a known correlation coefficient (r=0.5) and a fixed sample size (n=1000). The test verifies that the output regression coefficients and p-values match the expected theoretical results (calculated via standard statistical tables for n=1000, r=0.5) within a 5% margin of error.

**Acceptance Scenarios**:

1. **Given** a dataset of computed metrics, **When** the analysis script runs, **Then** it outputs a correlation coefficient (r) and p-value for the relationship between consistency and trust.
2. **Given** multiple predictor variables, **When** the regression model runs, **Then** it produces a summary table including coefficients, standard errors, and p-values for all predictors.
3. **Given** the analysis completes, **When** the visualization step runs, **Then** it generates a scatter plot with a regression line and a histogram of consistency scores, saving them as PNG files in the output directory.

### Edge Cases

- **What happens when** a user has exactly 3 turns but the sentiment model returns identical scores for all? (System must handle zero variance correctly without division-by-zero errors).
- **How does the system handle** a dataset where no sessions meet the ≥3 turn threshold? (System must report a "No valid data found" error and exit with code 1).
- **What happens when** the CPU memory limit is approached during batch processing? (System must dynamically calculate batch size to stay within available RAM, defaulting to 7GB).

## Requirements

### Functional Requirements

- **FR-001**: System MUST download the DailyDialog dataset from HuggingFace and filter for sessions containing ≥3 turns (See US-1).
- **FR-002**: System MUST compute the variance of sentiment scores across AI responses within a session using a CPU-tractable sentiment model (default: `distilbert-base-uncased@v1.2.0` with SHA-256 checksum validation). If the default model fails validation or is unavailable, the system MUST automatically switch to a configured fallback model (See US-2).
- **FR-003**: System MUST compute lexical diversity (Type-Token Ratio) for each AI response and aggregate variance across the session (See US-2).
- **FR-004**: System MUST calculate trust indicators including total interaction length (word count), session frequency (days between sessions), and average user rating (if available) (See US-2).
- **FR-005**: System MUST perform Generalized Linear Models (GLM) with Poisson or Negative Binomial distributions for count data (interaction length) and Survival Analysis for time-to-event data (session frequency), controlling for total interaction count and session duration (See US-3).
- **FR-006**: System MUST generate a scatter plot with regression line and a histogram of consistency scores as PNG files (See US-3).
- **FR-007**: System MUST implement a dynamic batch processing loop that calculates the maximum batch size to ensure memory usage stays within the available RAM limit (defaulting to 7GB) (See US-2, US-3).
- **FR-008**: System MUST handle missing sentiment scores by skipping the specific response and logging the error without terminating the job (See US-2).
- **FR-009**: System MUST implement a 'Lagged Trust Indicator' calculation where the trust metric for session N is derived from turns 1 to N-1, while the consistency score for session N is derived from turns 2 to N, to break mechanical dependency between predictor and outcome (See US-2).
- **FR-010**: System MUST perform a 'Proxy Validity Analysis' comparing the sentiment distribution of the DailyDialog dataset against a small reference sample of known AI-human dialogues to quantify the validity gap before proceeding with the main hypothesis test (See US-1).
- **FR-011**: System MUST report the results of the Proxy Validity Analysis and the Lagged Trust Indicator check in the final output, flagging any significant validity gaps (See US-3).
- **FR-012**: System MUST allow configuration of the fallback sentiment model via an environment variable or config file, ensuring substitution is possible without code changes (See US-2).

### Key Entities

- **Conversation Session**: A single interaction instance containing a sequence of user and AI turns, identified by a unique session ID.
- **User Profile**: An aggregation of all sessions belonging to a single user, used to calculate session frequency and total interaction length.
- **Consistency Metric**: A composite score derived from the variance of sentiment and lexical diversity across a user's sessions (derived from turns 2 to N).
- **Trust Indicator**: A quantitative measure of user trust, operationalized as interaction length, session frequency, and user ratings (derived from turns 1 to N-1).
- **Proxy Validity Score**: A metric quantifying the distributional difference between the proxy dataset and the target AI-human domain.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The correlation coefficient (r) between consistency scores and trust indicators is measured against the null hypothesis of no correlation (r=0) (See US-3).
- **SC-002**: The variance explained (R²) by the GLM/Survival model is measured against the baseline of a null model (See US-3).
- **SC-003**: Runtime must be ≤ 6 hours on the GitHub Actions free-tier runner (See US-2, US-3).
- **SC-004**: Memory footprint must not exceed the available RAM limit during batch processing (See US-2).
- **SC-005**: The data validity rate (percentage of sessions with ≥3 turns and valid sentiment scores) is measured against the total downloaded dataset size (See US-1).
- **SC-006**: The Proxy Validity Analysis must show a distributional difference (KS test p-value) of > 0.05 between the proxy dataset and the reference AI-human sample, or the study must be flagged as invalid (See FR-010).

## Assumptions

- **Assumption about dataset**: The DailyDialog dataset on HuggingFace contains sufficient session data with human-human dialogue that can be reasonably approximated as a proxy for AI-chatbot interactions for the purpose of this exploratory study, subject to the Proxy Validity Analysis (FR-010).
- **Assumption about methodology**: The study is observational; therefore, all findings will be framed as associational, not causal, to avoid overclaiming given the lack of random assignment.
- **Assumption about model**: The `distilbert-base-uncased` model is sufficiently accurate for sentiment analysis in this context and can run on CPU without quantization. If this model fails validation or proves insufficient for the 'personality' nuance, a substitute CPU-tractable model (e.g., a quantized variant) will be used as per FR-012.
- **Assumption about metrics**: Variance of sentiment and lexical diversity are valid proxies for "personality consistency" in the absence of a ground-truth personality label.
- **Assumption about power**: The sample size available from the public dataset is presumed sufficient to detect a moderate effect size (r ≥ 0.3) with power ≥ 0.8, subject to post-hoc power verification.
- **Assumption about compute**: The 6-hour time limit on the free-tier runner is sufficient to process the entire dataset in dynamically calculated batches.