# Feature Specification: The Impact of Perceived Agency in AI‑Driven Cognitive Behavioral Therapy on Treatment Adherence

**Feature Branch**: `PROJ-547-perceived-agency`  
**Created**: 2026‑06‑24  
**Status**: Draft  
**Input**: User description: “Investigate how linguistic markers of perceived user agency in AI‑CBT conversations predict treatment adherence metrics (session completion, usage frequency, self‑reported engagement) using publicly available chatbot datasets.”

## User Scenarios & Testing *(mandatory)*

### User Story 1 – Compute Agency Scores from Conversation Transcripts (Priority: P1)

A researcher needs to transform raw AI‑CBT conversation logs into a numeric “agency score” for each therapy session.

**Why this priority**: Without a reliable, reproducible agency metric the entire research question cannot be addressed; it is the core data product.

**Independent Test**: Run the agency‑score pipeline on a sample transcript file and verify that a numeric score (float) is output for each session.

**Acceptance Scenarios**:

1. **Given** a CSV file containing session‑id and ordered utterances, **When** the pipeline is executed with default feature weighting, **Then** a new CSV is produced with columns `session_id, agency_score` where each score is a float in the range [0, 1].
2. **Given** a transcript that contains no agency‑related linguistic markers, **When** the pipeline runs, **Then** the resulting `agency_score` equals 0.0.

---

### User Story 2 – Extract Adherence Metrics from Usage Metadata (Priority: P2)

A researcher must derive objective adherence indicators (completion rate, inter‑session interval, total engagement time) from the platform’s usage logs.

**Why this priority**: The dependent variable for the regression analysis must be accurately measured; this story isolates that capability.

**Independent Test**: Feed a mock usage‑log JSON file to the adherence‑extraction script and confirm that the three metrics are computed per user.

**Acceptance Scenarios**:

1. **Given** a JSON file with `user_id`, `session_start`, `session_end`, and `session_completed` flags, **When** the extraction tool runs, **Then** a CSV is emitted with columns `user_id, completion_rate, avg_inter_session_days, total_minutes` where:
   - `completion_rate` is the proportion of sessions marked completed (0 ≤ ≤ 1),
   - `avg_inter_session_days` is the mean gap in days between consecutive sessions,
   - `total_minutes` is the sum of session durations.

---

### User Story 3 – Perform Correlational Regression Analysis (Priority: P3)

A researcher wants to test whether higher agency scores are associated with better adherence outcomes while controlling for confounders.

**Why this priority**: This story delivers the hypothesis test that answers the research question; it can be executed once Stories 1 & 2 are satisfied.

**Independent Test**: Run the analysis script on the merged dataset and verify that regression coefficients, p‑values, and confidence intervals are reported.

**Acceptance Scenarios**:

1. **Given** a merged CSV containing `agency_score` and the three adherence metrics plus optional covariates, **When** the script executes a multiple linear regression (agency → each adherence metric), **Then** a results file is produced showing:
   - Regression coefficient for `agency_score`,
   - Two‑tailed p‑value < 0.05 (or a flag indicating non‑significance),
 - [deferred] confidence interval,
   - R² statistic.

---

### Edge Cases

- What happens when a session transcript is empty or unreadable?  
  *The pipeline should log a warning and assign an `agency_score` of 0.0 for that session.*

- How does the system handle missing adherence metadata for a user (e.g., no usage logs)?  
  *The user is excluded from the regression dataset with a logged note; the overall sample size is reported.*

- What if all sessions have identical agency scores (zero variance)?  
  *The regression step aborts with an explicit error indicating insufficient variance for modeling.*

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST ingest conversation transcript files in CSV or JSON format and parse utterances in chronological order.  
- **FR-002**: System MUST detect agency‑related linguistic markers (modal verbs, choice constructions, collaborative phrasing, open‑ended questions) using spaCy or NLTK tokenizers.  
- **FR-003**: System MUST aggregate turn‑level markers into a per‑session agency score using a weighted sum; default weights are defined in `config/agency_weights.yaml`.  
- **FR-004**: System MUST ingest usage‑metadata files and compute the three adherence metrics defined in User Story 2.  
- **FR-005**: System MUST merge agency scores with adherence metrics on a common session/user identifier and execute multiple linear regression with optional covariates.  
- **FR-006**: System MUST output a human‑readable results summary (CSV + PNG regression plots) in a configurable `output/` directory.  
- **FR-007**: System MUST enforce computational limits of ≤ 7 GB RAM and ≤ 2 CPU cores; if limits are exceeded, the process aborts with an informative error.  
- **FR-008**: System MUST log all processing steps, warnings, and errors to `logs/run_<timestamp>.log`.  

**Clarifications Needed**  

- **FR-003**: *[NEEDS CLARIFICATION: exact weighting scheme for agency markers – equal weights vs. empirically derived coefficients?]*  
- **FR-005**: *[NEEDS CLARIFICATION: which statistical library to use for regression – statsmodels or scikit‑learn?]*  
- **FR-006**: *[NEEDS CLARIFICATION: desired confidence level for intervals – [deferred] (default) or configurable?]*

### Key Entities

- **ConversationSession**: Represents one therapy session; attributes include `session_id`, `utterances` (ordered list of strings), `agency_score` (float).  
- **UserEngagement**: Represents a user’s usage record; attributes include `user_id`, `completion_rate` (float), `avg_inter_session_days` (float), `total_minutes` (float).  
- **RegressionResult**: Contains `dependent_metric`, `beta_agency`, `p_value`, `ci_lower`, `ci_upper`, `r_squared`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Agency‑score pipeline processes ≥ 95 % of input sessions without failure on a benchmark dataset of 1 000 sessions.  
- **SC-002**: Adherence‑extraction module yields correct metric values (within ± 0.01) when validated against a hand‑crafted ground‑truth subset of 200 users.  
- **SC-003**: Regression analysis completes within 30 minutes on the full dataset (≤ 6 GB RAM, 2 CPU) and produces a non‑empty results file.  

## Assumptions

- Publicly available mental‑health chatbot datasets contain both conversation transcripts and usage metadata; if missing, the researcher will supplement with synthetic placeholders.  
- The linguistic markers listed (modal verbs, choice phrasing, collaborative language, open‑ended questions) are sufficient proxies for “perceived agency” as established in human‑computer interaction literature.  
- Researchers have access to a Python 3.11 environment with spaCy ≥ 3.6, NLTK ≥ 3.8, pandas ≥ 2.0, and either statsmodels ≥ 0.14 or scikit‑learn ≥ 1.3 installed.  
- No GPU acceleration is required; all computations run on CPU only.  
- Ethical review and data‑privacy compliance are handled externally; the feature does not store personally identifiable information beyond what is present in the source datasets.
