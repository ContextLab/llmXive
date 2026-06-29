# Feature Specification: The Impact of Perceived Agency in AI‑Driven Cognitive Behavioral Therapy on Treatment Adherence

**Feature Branch**: `PROJ-547-perceived-agency`  
**Created**: 2026‑06‑24  
**Status**: Draft  
**Input**: User description: "Investigate how linguistic markers of perceived user agency in AI‑CBT conversations predict treatment adherence metrics (session completion, usage frequency, self‑reported engagement) using publicly available chatbot datasets."

## User Scenarios & Testing *(mandatory)*

### User Story 1 – Compute Agency Scores from Conversation Transcripts (Priority: P1)

A researcher needs to transform raw AI‑CBT conversation logs into a numeric "agency score" for each therapy session.

**Why this priority**: Without a reliable, reproducible agency metric the entire research question cannot be addressed; it is the core data product.

**Independent Test**: Run the agency‑score pipeline on a sample transcript file and verify that a numeric score (float) is output for each session.

**Acceptance Scenarios**:

1. **Given** a CSV file containing session‑id and ordered utterances, **When** the pipeline is executed with default feature weighting, **Then** a new CSV is produced with columns `session_id, agency_score` where each score is a float in the range [0, 1].
2. **Given** a transcript that contains no agency‑related linguistic markers, **When** the pipeline runs, **Then** the resulting `agency_score` equals 0.0.

---

### User Story 2 – Extract Adherence Metrics from Usage Metadata (Priority: P2)

A researcher must derive objective adherence indicators (completion rate, inter‑session interval, total engagement time, usage frequency) **and** self‑reported engagement scores from the platform's usage logs.

**Why this priority**: The dependent variable for the regression analysis must be accurately measured; this story isolates that capability.

**Independent Test**: Feed a mock usage‑log JSON file to the adherence‑extraction script and confirm that the five metrics are computed per user.

**Acceptance Scenarios**:

1. **Given** a JSON file with `user_id`, `session_start`, `session_end`, `session_completed` flags, **When** the extraction tool runs, **Then** a CSV is emitted with columns `user_id, completion_rate, avg_inter_session_days, total_minutes, self_reported_engagement, sessions_per_week` where:
   - `completion_rate` is the proportion of sessions marked completed (0 ≤ ≤ 1),
   - `avg_inter_session_days` is the mean gap in days between consecutive sessions,
   - `total_minutes` is the sum of session durations,
   - `self_reported_engagement` is the average of any Likert‑scale engagement scores supplied by the user (0 ≤ ≤ 5),
   - `sessions_per_week` is the count of sessions divided by the total weeks of observation (≥ 0).
2. **Given** a dataset with incomplete session timestamps, **When** the extraction tool runs, **Then** it logs a warning and excludes affected users from the `sessions_per_week` metric while computing other metrics.

---

### User Story 3 – Perform Correlational Regression Analysis (Priority: P3)

A researcher wants to test whether higher agency scores are associated with better adherence outcomes while controlling for confounders.

**Why this priority**: This story delivers the hypothesis test that answers the research question; it can be executed once Stories 1 & 2 are satisfied.

**Independent Test**: Run the analysis script on the merged dataset and verify that regression coefficients, p‑values, and confidence intervals are reported.

**Acceptance Scenarios**:

1. **Given** a merged CSV containing `agency_score` and the five adherence metrics plus optional covariates, **When** the script executes a multiple regression (agency → each adherence metric), **Then** a results file is produced showing:
   - Regression coefficient for `agency_score`,
   - Two‑tailed p‑value with Benjamini‑Hochberg FDR correction (adjusted p < 0.05 or a flag indicating non‑significance),
   - confidence interval,
   - R² statistic.

---

### User Story 4 – Validate Agency‑Score Metric (Priority: P2)

A researcher must assess the reliability and convergent validity of the computed agency scores against an established perceived agency/autonomy scale.

**Why this priority**: Psychometric validation (FR‑009) is required before the agency metric can be interpreted; it ensures the score measures the intended construct.

**Independent Test**: Run the validation script on a subset of sessions that have both agency scores, the underlying marker‑level scores, and perceived agency scale scores; verify that split‑half reliability ≥ 0.80 and Pearson r ≥ 0.30 with p < 0.05.

**Acceptance Scenarios**:

1. **Given** a validation CSV containing `session_id, agency_score, marker_item_1, …, marker_item_N, agency_scale_score`, **When** the script computes split‑half reliability across the marker items, **Then** it reports a reliability coefficient ≥ 0.80.
2. **Given** the same CSV, **When** the script computes convergent validity, **Then** it reports Pearson r ≥ 0.30 and p < 0.05.
3. **Given** a failure to meet either threshold, **When** the script completes, **Then** it logs a warning and aborts further analysis, prompting the researcher to revise the marker set.

---

### User Story 5 – Comprehensive Logging (Priority: P2)

A researcher needs a complete audit trail of all processing steps, warnings, and errors for reproducibility and debugging.

**Why this priority**: FR‑008 requires logging; without a dedicated story the requirement is orphaned.

**Independent Test**: Execute the full pipeline on a sample dataset and inspect `logs/run_<timestamp>.log` for entries covering ingestion, scoring, metric extraction, regression, and validation.

**Acceptance Scenarios**:

1. **Given** a successful run, **When** the pipeline finishes, **Then** the log file contains timestamped entries for each major step and a final "run completed successfully" message.
2. **Given** any error (e.g., dataset checksum mismatch), **When** the pipeline aborts, **Then** the log records the error with a clear description and exit code.

---

### Edge Cases

- **Empty or unreadable transcript** – The pipeline logs a warning and assigns an `agency_score` of 0.0 for that session, as defined in **FR-003**.  
- **Missing adherence metadata for a user** – The user is excluded from the regression dataset with a logged note; the overall sample size is reported.  
- **All sessions have identical agency scores (zero variance)** – The regression step aborts with an explicit error indicating insufficient variance for modeling.  
- **Dataset exceeds computational limits** – The system detects RAM or CPU usage above the thresholds in **FR-007**, aborts processing, and logs an informative error message.  
- **Psychometric validation fails** – The validation script logs a failure message and halts downstream analysis, ensuring only validated agency scores are used.  
- **Dataset download checksum verification fails** – The acquisition step aborts, logs the mismatch, and prompts the researcher to provide a correct source or checksum.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST ingest conversation transcript files in CSV or JSON format and parse utterances in chronological order.  
- **FR-002**: System MUST detect agency‑related linguistic markers (modal verbs, choice constructions, collaborative phrasing, open‑ended questions) using spaCy or NLTK tokenizers.  
- **FR-003**: System MUST aggregate turn‑level markers into a per‑session agency score using a weighted sum; default weights are defined in `config/agency_weights.yaml`. The pipeline MUST assign a score of 0.0 when no markers are detected or the transcript is empty/unreadable.  
- **FR-004**: System MUST ingest usage‑metadata files and compute the four adherence metrics defined in User Story 2 (completion_rate, avg_inter_session_days, total_minutes, sessions_per_week), plus the self‑reported engagement metric. Self‑reported engagement MUST be collected ≥ 7 days after the conversation period to mitigate common‑method bias, or the analysis MUST include statistical control for common‑method variance.  
- **FR-005**: System MUST merge agency scores with adherence metrics on a common session/user identifier and execute appropriate regression models:  
  - Logistic regression for binary/compositional outcomes (e.g., completion_rate),  
  - Beta regression for proportion outcomes (e.g., completion_rate when treated as continuous bounded variable),  
  - Ordinary Least Squares for continuous outcomes (e.g., total_minutes, self_reported_engagement, sessions_per_week),  
  controlling for specified confounders (see FR-010). All p‑values from the four regression tests MUST undergo Benjamini‑Hochberg FDR correction (adjusted p < 0.05 or a flag indicating non‑significance).  
- **FR-006**: System MUST output a human‑readable results summary (CSV + PNG regression plots) in a configurable `output/` directory.  
- **FR-007**: System MUST enforce computational limits of ≤ 6 GB RAM and ≤ 2 CPU cores; if limits are exceeded, the process aborts with an informative error (see Edge Case above) (see US-3).  
- **FR-008**: System MUST log all processing steps, warnings, and errors to `logs/run_<timestamp>.log`.  
- **FR-009**: System MUST perform psychometric validation of the agency‑score metric by (a) computing split‑half reliability (Spearman‑Brown) across the set of linguistic marker items for each session (target ≥ 0.80) and (b) correlating the aggregated agency score with an established perceived agency/autonomy scale (target Pearson r ≥ 0.30, p < 0.05). Documentation of the validation procedure and results shall be saved in `validation/report.pdf`.  
- **FR-010**: System MUST include a predefined set of confounding variables in the regression analysis: user age, gender, baseline symptom severity, and prior therapy exposure. These variables shall be extracted from a supplied demographics file. If unavailable, the system MUST apply multiple imputation (m=5) for missing confounder values, or perform complete‑case analysis with a bias assessment report documenting potential selection effects.  
- **FR-011**: System MUST extract self‑reported engagement scores (e.g., Likert‑scale questionnaire responses) from usage metadata or a separate survey file and incorporate them as a continuous adherence metric. Self‑reported engagement MUST be collected ≥ 7 days after the conversation period to mitigate common‑method bias, or the analysis MUST include statistical control for common‑method variance. (See US-2)  
- **FR-012**: System MUST acquire public chatbot datasets by downloading from URLs listed in a `datasets/sources.yaml` file, verify each file's SHA‑256 checksum, and record source, version, license, and checksum in `datasets/metadata.yaml`. Failure to verify aborts the acquisition step with a logged error. (See US-1)  
- **FR-013**: System MUST compute a usage‑frequency metric (sessions_per_week) from session timestamps. sessions_per_week is calculated as total_session_count divided by observation_weeks (where observation_weeks = (last_session_date − first_session_date + 1) / 7). This metric MUST be included in the adherence dataset and used in regression analysis per FR-005. (See US-2)

### Key Entities

- **ConversationSession**: Represents one therapy session; attributes include `session_id`, `utterances` (ordered list of strings), `agency_score` (float).  
- **UserEngagement**: Represents a user's usage record; attributes include `user_id`, `completion_rate` (float), `avg_inter_session_days` (float), `total_minutes` (float), `self_reported_engagement` (float), `sessions_per_week` (float).  
- **RegressionResult**: Contains `dependent_metric`, `beta_agency`, `p_value`, `adjusted_p_value`, `ci_lower`, `ci_upper`, `r_squared`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Agency‑score pipeline processes ≥ 95 % of input sessions without failure on a benchmark dataset of ≥ 100 sessions.  
- **SC-002**: Adherence‑extraction module yields correct metric values (within ± 0.01) when validated against a hand‑crafted ground‑truth subset of ≥ 50 users.  
- **SC-003**: Regression analysis completes within 30 minutes on the full dataset (≤ 6 GB RAM, 2 CPU) and produces a non‑empty results file.  
- **SC-004**: Psychometric validation (FR-009) demonstrates split‑half reliability ≥ 0.80 and convergent validity (Pearson r ≥ 0.30, p < 0.05) on the validation subset.  
- **SC-005**: Logging completeness: ≥ 95 % of pipeline steps produce timestamped log entries (measured as logged_steps / total_expected_steps).

## Assumptions

- Publicly available mental‑health chatbot datasets contain both conversation transcripts and usage metadata; if missing, the researcher will supplement with synthetic placeholders.  
- The linguistic markers listed (modal verbs, choice phrasing, collaborative language, open‑ended questions) are sufficient proxies for "perceived agency" as established in human‑computer interaction literature.  
- Researchers have access to a Python 3.11 environment with spaCy ≥ 3.6, NLTK ≥ 3.8, pandas ≥ 2.0, and either statsmodels ≥ 0.14 or scikit‑learn ≥ 1.3 installed.  
- No GPU acceleration is required; all computations run on CPU only.  
- Ethical review and data‑privacy compliance are handled externally; the feature does not store personally identifiable information beyond what is present in the source datasets.  
- Dataset acquisition, verification, and citation (FR‑012) are performed before any analysis to satisfy reproducibility standards.