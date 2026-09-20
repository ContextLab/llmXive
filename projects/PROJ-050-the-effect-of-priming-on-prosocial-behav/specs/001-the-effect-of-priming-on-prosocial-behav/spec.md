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
 - Validation performed against dual-blind human annotations (N=200 random sample); Cohen's Kappa value reported (no pass/fail threshold enforced in spec).

### US3: Statistical Analysis (See FR-003, SC-003)
As a researcher, I want to run LMMs on the scored data so that I can test the hypothesis regarding priming effects.
- **Acceptance Criteria**:
 - LMM formula: `prosocial_keyword_count ~ thread_type + thread_length + user_tenure + (1|subreddit) + (1|user_id)`.
 - Sensitivity analysis performed on model convergence.
 - Model MUST converge (convergence status == 'converged') AND the p-value for the `thread_type` fixed effect MUST be < 0.05 for the analysis to be considered successful.
 - Results exported to JSON and PNG.

## Functional Requirements

- **FR-001**: System MUST fetch Reddit comments from pushshift for specified subreddits and time windows, anonymize user IDs via SHA-256 hashing, and classify threads as 'Prime' or 'Control' based on title regex matching `/(thank|help|support|care)/i`.
- **FR-002**: System MUST compute VADER sentiment scores and prosocial keyword counts for each comment, and generate a validation report comparing automated scores against a dual-blind human annotation sample of N=200.
- **FR-003**: System MUST fit a Linear Mixed Model with the formula `prosocial_keyword_count ~ thread_type + thread_length + user_tenure + (1|subreddit) + (1|user_id)`, verify convergence, and output the p-value for the `thread_type` fixed effect.

## Key Entities

- **Thread**: Represents a Reddit post; attributes include `thread_id`, `title`, `subreddit`, `thread_type` (Prime/Control).
- **Comment**: Represents a user reply; attributes include `comment_id`, `user_id` (hashed), `thread_id`, `prosocia_keyword_count`, `vader_score`.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Total number of comments fetched and successfully processed is measured against the raw API response count.
- **SC-002**: Cohen's Kappa score for prosocial keyword classification is measured against the dual-blind human annotation sample.
- **SC-003**: Model fit success is measured against the LMM convergence status (must be 'converged') and the p-value for the `thread_type` fixed effect (must be < 0.05).

## Assumptions

- Users have stable internet connectivity to access the pushshift API.
- The pushshift API provides complete historical data for the specified subreddits and date range.
- The chosen regex pattern `/(thank|help|support|care)/i` adequately captures the 'Prime' condition for thread titles.
- User tenure is calculated based on the account creation date found in the user profile API.