# Specification: The Effect of Priming on Prosocial Behavior

## User Stories

### US1: Data Ingestion and Anonymization
As a researcher, I want to fetch and anonymize Reddit comments so that I can analyze them without violating privacy policies.
- **Acceptance Criteria**:
 - Data fetched from `pushshift/reddit`.
 - Comments classified into "Prime" and "Control".
 - User IDs hashed; raw timestamps removed.
 - Minimum 4,000 comments per group.

### US2: Prosocial Scoring and Validation
As an analyst, I want to score comments for prosocial actions and negative sentiment so that I can quantify the dependent variable.
- **Acceptance Criteria**:
 - VADER sentiment scores computed.
 - Prosocial action counts derived from a specific lexicon.
 - Validation against human annotations (Cohen's Kappa >= 0.7).

### US3: Statistical Analysis
As a researcher, I want to run LMMs on the scored data so that I can test the hypothesis regarding priming effects.
- **Acceptance Criteria**:
 - LMM formula: `prosocial_action_count ~ thread_type +... + (1|user_id)`.
 - Sensitivity analysis performed.
 - Results exported to JSON and PNG.
