# Feature Specification: The Influence of Emotional Contagion on Collective Decision-Making in Online Forums

**Feature Branch**: `001-emotional-contagion-decisions`  
**Created**: 2026-01-15  
**Status**: Draft  
**Input**: User description: "Does the emotional tone of early contributions in online forums bias subsequent participants and thereby affect the quality and efficiency of collective decisions?"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Collection and Thread Extraction (Priority: P1)

The research team MUST be able to download Reddit comment archives and Stack Exchange data dumps, then identify discussion threads with clearly defined decision points (e.g., questions asking for recommendations, polls, or problem-solving requests). From each selected thread, the system MUST extract the first N=3 top-level posts as seed posts for sentiment analysis.

**Why this priority**: This is the foundational data pipeline without which no analysis can proceed. All downstream measurements depend on correctly identifying and extracting the relevant thread data.

**Independent Test**: Can be fully tested by running the data extraction script against a sample of threads from r/AskScience and verifying that each thread has exactly 3 seed posts extracted with valid timestamps and author IDs.

**Acceptance Scenarios**:

1. **Given** a subreddit with decision-making threads (e.g., r/AskScience), **When** the data extraction script runs, **Then** ≥95% of threads contain exactly 3 seed posts with complete metadata (timestamp, author, comment ID)
2. **Given** a thread with fewer than 3 top-level posts, **When** the extraction script runs, **Then** the thread is flagged for exclusion and logged with reason code

---

### User Story 2 - Sentiment Analysis and Contagion Index Computation (Priority: P2)

The system MUST apply VADER sentiment analysis (NLTK) to compute a compound sentiment score for each post. It MUST compute an emotional contagion index as the Pearson correlation between seed-post sentiment and the sentiment trajectory of subsequent replies over the first 20 comments.

**Why this priority**: This implements the core predictor variable (emotional contagion) that tests the research hypothesis. Without accurate sentiment measurement, the association analysis cannot proceed.

**Independent Test**: Can be fully tested by running sentiment analysis on a fixed test corpus of a sample of Reddit comments and verifying that VADER compound scores fall within [-1.0, 1.0] and the contagion index computation returns a valid correlation coefficient for threads with ≥5 replies.

**Acceptance Scenarios**:

1. **Given** a thread with ≥5 replies after seed posts, **When** sentiment analysis runs, **Then** the contagion index is computed and stored with Pearson correlation value in [-1.0, 1.0]
2. **Given** a thread with <5 replies, **When** sentiment analysis runs, **Then** the thread is flagged as insufficient for contagion analysis and excluded from the primary analysis set

---

### User Story 3 - Decision Quality Metrics and Statistical Modeling (Priority: P3)

The system MUST compute decision-quality metrics (agreement proportion, Shannon entropy for diversity, predictive accuracy against ground truth where available) and fit mixed-effects linear models with thread-level random intercepts. The system MUST test significance of contagion coefficients using Wald tests (α=0.05) and apply multiple-comparison correction when >1 hypothesis test is run.

**Why this priority**: This produces the final research outputs (hypothesis tests, effect sizes) that answer the research question. Lower priority because it depends on P1 and P2 completing successfully.

**Independent Test**: Can be fully tested by running the statistical modeling pipeline on a sample dataset of threads and verifying that mixed-effects models converge, p-values are computed, and multiple-comparison correction (e.g., Bonferroni or FDR) is applied when ≥3 tests are run.

**Acceptance Scenarios**:

1. **Given** a dataset of ≥30 threads with complete sentiment and decision-quality metrics, **When** mixed-effects modeling runs, **Then** ≥90% of models converge and output coefficient estimates with standard errors
2. **Given** ≥3 hypothesis tests are run, **When** the statistical pipeline completes, **Then** multiple-comparison correction is applied and corrected p-values are reported

---

### Edge Cases

- What happens when a thread contains <3 seed posts? → Thread is excluded and logged with reason code `SEED_INSUFFICIENT`
- What happens when ground truth is unavailable for predictive accuracy? → Predictive accuracy metric is set to `null` and thread is excluded from that specific analysis (but retained for agreement/diversity analysis)
- What happens when sentiment analysis fails on a comment (e.g., empty text)? → Comment is skipped and the contagion index is computed on available comments; if <3 comments remain, thread is excluded
- How does system handle threads with <20 replies for contagion trajectory? → Contagion index is computed on available replies; threads with <5 replies are excluded from primary analysis

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download Reddit comment archives via Pushshift API for ≥2 subreddits with clear decision-making outcomes (e.g., r/AskScience, r/ProductReviews) and Stack Exchange data dumps for ≥1 site (e.g., Politics.SE, Seasoned Advice) (See US-1)
- **FR-002**: System MUST identify and extract the first N=3 top-level posts from each thread as seed posts, excluding threads with <3 top-level posts (See US-1)
- **FR-003**: System MUST apply VADER sentiment analysis (NLTK) to compute a compound sentiment score in [-1.0, 1.0] for each post (See US-2)
- **FR-004**: System MUST compute an emotional contagion index as the Pearson correlation between seed-post sentiment and sentiment trajectory of subsequent replies over the first 20 comments (See US-2)
- **FR-005**: System MUST compute decision-quality metrics including: (a) agreement proportion, (b) Shannon entropy for diversity, (c) predictive accuracy against external ground truth where available (See US-3)
- **FR-006**: System MUST fit mixed-effects linear models with thread-level random intercepts and test significance of contagion coefficients using Wald tests (α=0.05) (See US-3)
- **FR-007**: System MUST apply multiple-comparison correction (e.g., Bonferroni or Benjamini-Hochberg FDR) when ≥3 hypothesis tests are run (See US-3)
- **FR-008**: System MUST perform a sensitivity analysis that sweeps the decision-quality threshold over {0.01, 0.05, 0.1} and reports how false-positive/false-negative rates vary (See US-3)

*Example of marking unclear requirements:*

- **FR-009**: System MUST obtain ground truth labels for [NEEDS CLARIFICATION: which subreddits/sites provide verifiable ground truth for decision outcomes?]

### Key Entities *(include if feature involves data)*

- **Thread**: A Reddit/Stack Exchange discussion thread with decision point; key attributes: thread ID, subreddit, creation timestamp, seed posts (up to 3), reply count
- **SeedPost**: The first 3 top-level posts in a thread; key attributes: post ID, author, timestamp, VADER compound sentiment score
- **ContagionMetric**: Computed measure of emotional contagion; key attributes: thread ID, Pearson correlation value, number of replies used in computation
- **DecisionQuality**: Computed measure of decision outcomes; key attributes: thread ID, agreement proportion, Shannon entropy, predictive accuracy (or null if ground truth unavailable)

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Dataset-variable fit is measured against the Pushshift/Stack Exchange data schema to verify all required variables (sentiment, decision outcomes, covariates) are present (See US-1)
- **SC-002**: Inference framing is measured against the study design documentation to verify all findings are framed as associational (not causal) when no random assignment is used (See US-3)
- **SC-003**: Multiple-comparison correction is measured against the number of hypothesis tests run; ≥1 correction method MUST be applied when ≥3 tests are executed (See US-3)
- **SC-004**: Threshold sensitivity analysis is measured against the swept threshold set {0.01, 0.05, 0.1}; ≥1 sensitivity analysis MUST be reported showing how false-positive/false-negative rates vary (See US-3)
- **SC-005**: Compute feasibility is measured against GitHub Actions free-tier constraints (2 CPU, 7 GB RAM, 14 GB disk, ≤6 h); the full analysis MUST complete within these bounds (See US-3)

## Assumptions

- **Assumption 1**: Reddit comment archives are accessible via Pushshift API (or alternative archival source if Pushshift is unavailable); [NEEDS CLARIFICATION: confirm current API availability or identify backup source]
- **Assumption 2**: Ground truth for predictive accuracy is available for ≥50% of selected threads; threads without ground truth are excluded from predictive accuracy analysis but retained for agreement/diversity analysis
- **Assumption 3**: VADER sentiment analysis is sufficient for the research question; TextBlob and BERT-based models are used only for robustness checks (not primary analysis) to maintain CPU feasibility
- **Assumption 4**: The study is observational (no random assignment); therefore, all findings MUST be framed as associational relationships, not causal claims
- **Assumption 5**: Sample size/power is [deferred] pending initial data exploration; an explicit acknowledgement of power limitation MUST be included in the final report if n < 100 threads
- **Assumption 6**: All analysis runs on CPU-only GitHub Actions free-tier runner; no GPU/CUDA/mixed-precision methods are used; data is sampled/subset if needed to fit ~7 GB RAM / ~14 GB disk
- **Assumption 7**: Predictor collinearity diagnostics (e.g., variance inflation factor) MUST be computed when ≥2 predictors are correlated (e.g., sentiment and topic keywords); joint relationships are framed descriptively rather than as independent effects
