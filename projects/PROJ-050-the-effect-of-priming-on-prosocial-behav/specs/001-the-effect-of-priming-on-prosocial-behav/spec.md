# Feature Specification: The Effect of Priming on Prosocial Behavior in Online Communities

**Feature Branch**: `001-the-effect-of-priming-on-prosocial-behav`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "To what extent does the presence of prosocial cues (e.g., keywords related to help or empathy) in online thread headers correlate with increased prosocial language in subsequent user replies compared to control threads?"

## User Scenarios & Testing

### User Story 1 - Data Ingestion, Classification, and Anonymization (Priority: P1)

The system MUST retrieve a subset of Reddit comments, filter them by a specific timeframe and selected subreddits, classify threads into "Prime" (containing keywords like "help", "support", "charity" in the title, excluding negations) and "Control" groups, and anonymize all PII (hashing usernames, stripping timestamps) before storage. This is the foundational step; without valid data separation and privacy compliance, no analysis can occur.

**Why this priority**: This is the critical path dependency. If data cannot be fetched, classified, or anonymized, the entire study fails and violates ethical constraints. It establishes the independent variable (thread type) required for all subsequent analysis.

**Independent Test**: Execute the data pipeline script against a small, known test subset of the dataset and verify that the resulting DataFrame contains exactly two distinct groups with the expected keyword presence flags, totaling at least 4,000 comments per group, and that no plaintext usernames or timestamps exist in the output.

**Acceptance Scenarios**:

1. **Given** a valid HuggingFace dataset subset or pushshift mirror and a list of 5 target subreddits (r/AskReddit, r/relationships, r/socialscience, r/psychology, r/dataisbeautiful), **When** the ingestion script runs with a limit of `TARGET_N` ([deferred]) comments, **Then** the output file contains a `thread_type` column correctly labeling threads as "Prime" or "Control" based on title keyword presence (excluding negations) and a `thread_id` column.
2. **Given** the ingestion script completes, **When** the user inspects the summary statistics, **Then** the dataset contains at least 4,000 comments in each group (Prime and Control) if the dataset allows; if the dataset is exhausted before `TARGET_N` total or the split is uneven (e.g., [deferred] total, [deferred] Prime, [deferred] Control), the system MUST log a warning and proceed with the available data. The study is considered successful if the analysis runs on the available data.
3. **Given** the raw data is retrieved, **When** the anonymization step runs, **Then** the output file contains hashed user IDs (SHA-256) and no plaintext timestamps or usernames.

---

### User Story 2 - Prosocial Action Scoring and Validation (Priority: P2)

The system MUST process every comment in the dataset using a validated prosocial action lexicon to compute a `prosocial_action_count` (count of action verbs like "offer", "give", "assist") and a `neg_score` (VADER negative sentiment component) on a CPU-only environment. This transforms raw text into the dependent variables required for the hypothesis test. The system MUST also validate the VADER sentiment tool and the prosocial action lexicon on a stratified sample of comments against human annotations.

**Why this priority**: This implements the core measurement mechanism. Without converting text to numerical scores and validating the tools against human ground truth, the correlation between priming and behavior cannot be quantified or trusted.

**Independent Test**: Run the scoring module on a sample of pre-labeled comments with known prosocial intent and verify that the computed `prosocial_action_count` matches the human annotations with a Cohen's Kappa ≥ 0.7.

**Acceptance Scenarios**:

1. **Given** a DataFrame of comments, **When** the scoring function is applied, **Then** every row is augmented with a `prosocial_action_count` (integer ≥ 0) and a `neg_score` (float) without raising memory errors or exceeding 4 hours of runtime on a standard GitHub Actions ubuntu-latest runner.
2. **Given** the validation step, **When** the system processes a stratified sample of comments, **Then** the system outputs a validation report confirming Cohen's Kappa ≥ 0.7 for both the VADER sentiment and the prosocial action lexicon against human annotations.

---

### User Story 3 - Statistical Analysis and Reporting (Priority: P3)

The system MUST perform a Linear Mixed-Effects Model (LMM) to compare mean `prosocial_action_count` between Prime and Control groups, controlling for `thread_age`, `comment_count`, and random effects for `thread_id` and `user_id`. It must also run a sensitivity analysis and generate a boxplot visualization of the results. This delivers the final scientific conclusion.

**Why this priority**: This synthesizes the data and measurements into the answer to the research question. It is the final value-delivery step for the researcher.

**Independent Test**: Execute the analysis script on the full dataset and verify that the output JSON report contains a p-value for the LMM fixed effect of "Prime" and a confidence interval, alongside a generated PNG plot file.

**Acceptance Scenarios**:

1. **Given** the scored dataset, **When** the LMM is executed, **Then** the system outputs a p-value and a confidence interval, explicitly stating if the difference is statistically significant at the p < 0.05 level (two-tailed).
2. **Given** the regression model is fit, **When** the results are printed, **Then** the output includes the coefficient for the "Prime" indicator variable and the control variables (thread age, comment count), indicating the isolated effect of the priming cue.
3. **Given** the analysis script runs, **When** the sensitivity analysis is performed, **Then** the output includes p-values for conventional significance thresholds to demonstrate robustness.

### Edge Cases

- **What happens when** a thread title contains a keyword but in a negated context (e.g., "No help needed")? The system MUST exclude such titles from the Prime group (as per FR-002) and log them as "Negation Exclusions". The system MUST NOT rely on regression controls to mitigate this bias.
- **How does the system handle** a subreddit with a limited number of matching threads in the timeframe? The system MUST exclude that subreddit from the final analysis or log a warning, ensuring the `TARGET_N` comment target is not skewed by a single outlier source.
- **What happens when** the dataset is exhausted before reaching `TARGET_N` ([deferred]) comments? The system MUST proceed with the available data and log a warning indicating the final sample size and group distribution.

## Requirements

### Functional Requirements

- **FR-001**: System MUST retrieve comments from the 5 specified subreddits (r/AskReddit, r/relationships, r/socialscience, r/psychology, r/dataisbeautiful) until either a substantial corpus of comments (TARGET_N = 10,000) is collected OR the dataset is exhausted. If the `TARGET_N` target is met but the split is <4,000 per group, the system MUST log a warning and proceed with available data. (See US-1)
- **FR-001a**: System MUST validate that the target dataset contains the 5 specified subreddits and the required schema fields (`title`, `body`, `author`, `created_utc`, `subreddit`) before retrieval begins. If the primary source (e.g., 'derek-thomas/dataset-creator-askreddit') lacks these, the system MUST switch to a verified multi-subreddit source (e.g., 'pushshift/reddit') or abort with an error. (See US-1)
- **FR-002**: System MUST classify threads into "Prime" or "Control" groups based on the presence of specific keywords ("help", "support", "charity") in the thread title, excluding titles where a negation word (no, not, never, without) appears within 3 tokens before a keyword, using the NLTK word tokenizer. (See US-1)
- **FR-002a**: System MUST exclude titles with negation errors from the Prime group and log them as "Negation Exclusions". (See US-1)
- **FR-003**: System MUST compute VADER sentiment scores (`compound`, `pos`, `neu`, `neg`) and a `prosocial_action_count` for every comment in the dataset. The output DataFrame MUST include columns: `comment_id`, `thread_id`, `compound`, `pos`, `neu`, `neg`, `neg_score` (defined strictly as the `neg` component, a float 0-1, NOT an aggression proxy), `prosocial_action_count`. (See US-2)
- **FR-003b**: System MUST compute `prosocial_action_count` using a secondary lexicon of action verbs (e.g., "offer", "give", "assist", "contribute") that explicitly EXCLUDES the prime keywords ("help", "support", "charity") and their semantic equivalents (e.g., "donate") to avoid tautology. This design choice measures *responsive* prosociality (generic action) rather than lexical repetition, acknowledging the trade-off that specific responsive phrases (e.g., "I can help") may be undercounted. (See US-2)
- **FR-004**: System MUST perform a Linear Mixed-Effects Model (LMM) comparing `prosocial_action_count` between Prime and Control groups, with a fixed effect for `thread_type` and random intercepts for `thread_id` and `user_id`, using a significance threshold of p < 0.05 (two-tailed). (See US-3)
- **FR-005**: System MUST execute a Linear Mixed-Effects Model (LMM) predicting `prosocial_action_count` using `thread_type` as the primary predictor, controlling for `thread_age` and `comment_count`, with random intercepts for `thread_id` and `user_id`. (See US-3)
- **FR-005a**: System MUST include a sensitivity analysis in the final report that reports p-values for thresholds of 0.01, 0.05, and 0.10 to demonstrate robustness. (See US-3)
- **FR-006**: System MUST generate a boxplot visualization comparing `prosocial_action_count` distributions across Prime and Control groups and save it as a PNG file. (See US-3)
- **FR-009**: System MUST anonymize all PII by hashing usernames (SHA-256) and stripping timestamps before storing data in `data/`. The SHA-256 hash of the username MUST be used as the persistent `user_id` for the random intercept in the LMM. (See US-1)
- **FR-010**: System MUST validate the VADER sentiment tool and the prosocial action lexicon on a stratified random sample of comments. Stratification MUST be by `thread_type` and `subreddit`, with a minimum of 50 samples per stratum. If a stratum has < 50 samples, aggregate with similar strata until the minimum is met, up to a total of a sufficient number of samples. Report Cohen's Kappa ≥ 0.7 against human annotations. (See US-2)
- **FR-011**: System MUST implement a Human Annotation Protocol to generate ground truth labels for validation. This protocol MUST: (1) Recruit at least 3 independent raters; (2) Provide a defined codebook for "prosocial action" and "negative sentiment"; (3) Calculate Cohen's Kappa between raters and the system output. Heuristic baselines or simulated data are strictly prohibited for this validation. (See US-2)
- **FR-012**: System MUST enforce a performance constraint where the full scoring module (processing `TARGET_N` = 10,000 comments) completes within 4 hours on a standard GitHub Actions ubuntu-latest runner. (See US-2)

### Key Entities

- **Thread**: A conversation unit identified by a unique `thread_id`, containing a title, timestamp, and a list of associated comments.
- **Comment**: A text response within a thread, containing an anonymized `comment_id`, `thread_id`, author hash, and text body.
- **SentimentScore**: A numerical record derived from a comment, containing `comment_id`, `thread_id`, VADER `compound` score, `neg` score, and `prosocial_action_count`.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The statistical significance of the priming effect is measured against the null hypothesis (p < 0.05, two-tailed) using a Linear Mixed-Effects Model to determine if Prime threads exhibit higher `prosocial_action_count` (See US-3).
- **SC-002**: The robustness of the findings is measured against the assumption of no confounding by thread age or popularity by verifying the regression coefficient for `thread_type` remains significant after controlling for `thread_age` and `comment_count` in the LMM (See US-3).
- **SC-003**: The p-value for the primary LMM fixed effect is measured against the 0.05 threshold (two-tailed) to determine significance (See US-3).
- **SC-004**: The computational feasibility is measured against the constraint of a GitHub Actions ubuntu-latest runner (cores, 7 GB RAM) by verifying the full pipeline (processing [deferred] comments) completes within 4 hours (See US-2).
- **SC-005**: The anonymization compliance is measured against a PII scan of the stored data, confirming zero instances of plaintext usernames or timestamps (See US-1).
- **SC-006**: The methodological validity is measured against the requirement for validation by confirming Cohen's Kappa ≥ 0.7 on the 200-comment stratified validation sample against human annotations (See US-2).
- **SC-007**: The validation ground truth is measured against the Human Annotation Protocol (FR-011) to confirm that ground truth was generated by human raters, not heuristics (See US-2).
- **SC-008**: The `neg_score` metric is measured against the VADER standard to confirm it represents the `neg` component (float 0-1) and is NOT claimed to be an aggression proxy (See US-2).

## Assumptions

- **Assumption about data source**: The selected HuggingFace Reddit dataset (or verified multi-subreddit alternative) contains the necessary fields (`title`, `body`, `created_utc`, `subreddit`) and covers the 5 target subreddits with sufficient density of the target keywords.
- **Assumption about variable fit**: The `prosocial_action_count` (based on action verbs excluding prime keywords and semantic equivalents) is a valid proxy for "prosocial behavior" in this specific context, distinct from general sentiment polarity.
- **Assumption about observational framing**: Since this is an observational study of existing data (no random assignment of titles by the researchers), all findings are framed as associational (correlation), not causal. The regression controls and random effects (including `user_id`) are assumed to sufficiently mitigate confounding variables like user self-selection and thread-level clustering, though they do not eliminate them entirely.
- **Assumption about compute limits**: A sample of `TARGET_N` ([deferred]) comments fits within 7 GB RAM on a standard GitHub Actions ubuntu-latest runner when loaded entirely into a pandas DataFrame with VADER processing overhead (verified by pilot).
- **Assumption about threshold justification**: The p < 0.05 threshold is adopted as the community standard for statistical significance in social psychology; the sensitivity analysis (FR-005a) demonstrates robustness.
- **Assumption about measurement validity**: The use of VADER and the action lexicon is accepted as a lightweight, CPU-tractable approximation, with the understanding that validation (FR-010) confirms their suitability for this domain.
- **Assumption about power**: A sample size of `TARGET_N` ([deferred]) (approx. [deferred]/group) provides >80% power to detect a small effect size (d=0.15) at α=0.05, assuming an even split and accounting for intra-class correlation via the Mixed-Effects Model. Power is calculated based on the *actual* achieved N if the dataset is exhausted before `TARGET_N`.