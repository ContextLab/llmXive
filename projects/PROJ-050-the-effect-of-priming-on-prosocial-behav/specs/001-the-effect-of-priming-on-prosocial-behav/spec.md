# Specification: The Effect of Priming on Prosocial Behavior

## User Stories

### US1: Data Ingestion and Anonymization (See FR-001, SC-001)
As a researcher, I want to fetch and anonymize Reddit comments so that I can analyze them without violating privacy policies.
- **Acceptance Criteria**:
 - Data fetched from `pushshift/reddit` for subreddits r/AskReddit, r/science, r/relationships between 2020-01-01 and 2023-12-31.
 - Classification rule: Prime if thread title contains regex `/(thank|help|support|care)/i`; else Control.
 - User IDs hashed; raw timestamps removed.
 - Target N >= 4,000 comments per group; if data yields < 4,000, proceed with all available data and report N explicitly.

### US2: Prosocial Scoring and Validation (See FR-002, SC-002)
As an analyst, I want to score comments for prosocial actions and negative sentiment so that I can quantify the dependent variable.
- **Acceptance Criteria**:
 - VADER sentiment scores computed.
 - Prosocial keyword counts derived from a specific lexicon.
 - Validation performed against dual‑blind human annotations (N=200 random sample); Cohen's Kappa value reported (no pass/fail threshold enforced in spec).

### US3: Statistical Analysis (See FR-003, SC-003)
As a researcher, I want to run LMMs on the scored data so that I can test the hypothesis regarding priming effects.
- **Acceptance Criteria**:
 - LMM formula: `prosocial_keyword_count ~ thread_type + thread_length + user_tenure + (1|subreddit) + (1|user_id)`.
 - Model MUST converge (convergence status == 'converged').
 - p‑value for the `thread_type` fixed effect MUST be reported (significance not a success condition).
 - Sensitivity analysis performed on model convergence by varying optimizer tolerance (1e‑4, 1e‑5, 1e‑6) and reporting resulting p‑values and convergence flags.
 - Results exported to JSON and PNG files.

## Functional Requirements

- **FR-001**: System MUST fetch Reddit comments from pushshift for the specified subreddits and time windows, anonymize user IDs via SHA‑256 hashing, classify threads as 'Prime' or 'Control' based on title regex matching `/(thank|help|support|care)/i`, ensure at least 4,000 comments per group (Prime and Control); if fewer are available, process all available comments and report the actual N for each group in the output summary.
- **FR-002**: System MUST compute VADER sentiment scores and prosocial keyword counts for each comment, generate a validation report comparing automated scores against a dual‑blind human annotation sample of N=200, and **report the Cohen’s Kappa statistic** for the prosocial keyword classification.
- **FR-003**: System MUST fit a Linear Mixed Model with the formula `prosocial_keyword_count ~ thread_type + thread_length + user_tenure + (1|subreddit) + (1|user_id)`, verify convergence, **perform a sensitivity analysis on model convergence** by running the model with optimizer tolerances of 1e‑4, 1e‑5, and 1e‑6, **export all model results, convergence diagnostics, and sensitivity analysis outcomes to JSON and PNG**, and report the p‑value for the `thread_type` fixed effect.
- **FR-002c**: System MUST conduct a CPU feasibility analysis for the sentiment‑analysis and keyword‑count pipelines, documenting expected runtime and memory usage; if feasibility fails, the requirement is deferred with a “FR‑002c Deferred” note.
- **FR-004**: System MUST validate the VADER sentiment scores against the same 200‑sample human annotation set, compute Pearson correlation *r*, and report this correlation coefficient.
  
## Key Entities

- **Thread**: Represents a Reddit post; attributes include `thread_id`, `title`, `subreddit`, `thread_type` (Prime/Control).
- **Comment**: Represents a user reply; attributes include `comment_id`, `user_id` (hashed), `thread_id`, `prosocial_keyword_count`, `vader_score`.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Total number of comments fetched and successfully processed is measured against the raw API response count.
- **SC-002**: Cohen's Kappa score for prosocial keyword classification is measured against the dual‑blind human annotation sample.
- **SC-003**: Model fit success is measured by convergence status = 'converged' and the p‑value for `thread_type` is reported; sensitivity analysis must report p‑values and convergence flags for optimizer tolerances 1e‑4, 1e‑5, 1e‑6 in the exported JSON.
- **SC-004**: Pearson correlation *r* for VADER sentiment scores against human annotations is measured; the requirement is satisfied when *r* ≥ 0.7.
- **SC-005**: Exported result files (JSON and PNG) are present and correctly formatted.

## Assumptions

- Users have stable internet connectivity to access the pushshift API.
- The pushshift API provides complete historical data for the specified subreddits and date range.
- The chosen regex pattern `/(thank|help|support|care)/i` adequately captures the 'Prime' condition for thread titles.
- User tenure is calculated based on the account creation date found in the user profile API.

*All generic Spec Template placeholder sections have been removed to maintain internal consistency.*