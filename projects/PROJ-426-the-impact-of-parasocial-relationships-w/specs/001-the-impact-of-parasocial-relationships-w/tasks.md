# Tasks: The Impact of Parasocial Relationships with AI Companions on Loneliness

**Input**: Design documents from `/specs/001-ai-companion-loneliness-impact/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

<!--
 ============================================================================
 IMPORTANT: The tasks below are SAMPLE TASKS for illustration purposes only.

 The /speckit-tasks command MUST replace these with actual tasks based on:
 - User stories from spec.md (with their priorities P1, P2, P3...)
 - Feature requirements from plan.md
 - Entities from data-model.md
 - Endpoints from contracts/

 Tasks MUST be organized by user story so each story can be:
 - Implemented independently
 - Tested independently
 - Delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001a [P] Create project root directory structure: `src/`, `tests/`, `data/`, `data/raw/`, `data/processed/`, `data/results/`, `docs/`, `contracts/`, `config/`
- [X] T001b [P] Create initialization files: `src/__init__.py`, `tests/__init__.py`, `tests/conftest.py`, `data/.gitkeep`, `docs/.gitkeep`, `config/.gitkeep`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Create `contracts/unified_dataset.schema.yaml` defining the schema for matched user data (user_id, loneliness_score, usage_frequency, session_duration, attachment scores, age)
- [X] T005 [P] Implement `src/utils/logging.py` for structured logging and progress tracking
- [ ] T006 [P] Setup environment configuration management for API keys and data paths
- [ ] T007 Create `src/utils/data_validation.py` for schema validation and checksum recording
- [ ] T008 [P] Implement `src/utils/retry_policy.py`:
 - Define exponential backoff strategy (max retries = 3, base delay = 1 second, max delay 60s)
 - Create configuration object for retry logic
 - **Output Artifact**: `src/utils/retry_policy.py`
- [X] T009 [P] Implement `src/utils/rate_limit_handler.py`:
 - Implement logic to handle 429 responses from Pushshift API
 - Integrate with `retry_policy.py` for backoff
 - Verify error handling by simulating rate limit responses in unit tests
 - **Output Artifact**: `src/utils/rate_limit_handler.py`
- [ ] T025.5 Implement `src/modeling/config_model_structure.py`:
 - **Purpose**: Satisfy Constitution Principle VI (Pre-specification) and FR-005
 - Define the random effect structure (Intercepts for User, Slopes for UsageFrequency by User) in `config/model_structure.yaml`
 - Define fixed effects and lagged structure in the same config
 - **CONSTRAINT**: This script must NOT read any data files from `data/` or perform any data exploration. It must rely solely on hardcoded specifications from the plan.
 - **Output Artifact**: `config/model_structure.yaml`

---

## Phase 3: User Story 1 - Data Ingestion and User Matching (Priority: P1) 🎯 MVP

**Goal**: Ingest the Reddit Loneliness Longitudinal Dataset and Pushshift logs, match users via hashed usernames, and produce a unified analysis-ready dataset.

**Independent Test**: Execute the data pipeline on a sample subset and verify the output table contains matched records with non-null values for both loneliness scores and usage metrics.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Contract test for unified dataset schema in `tests/contract/test_unified_schema.py`
- [X] T011 [P] [US1] Integration test for end-to-end data ingestion on sample data in `tests/integration/test_full_pipeline.py` <!-- FAILED: unspecified -->

### Implementation for User Story 1

- [X] T012 [US1] Implement `src/ingest/download_loneliness.py`:
 - Fetch *Reddit Loneliness Longitudinal Dataset* from Zenodo DOI.
 - Validate presence of `username` or `username_hash` and Extended periods of non-null scores.
 - Halt with "Data Linkage Impossible" if linkable IDs are missing.
 - **Output Artifact**: `data/raw/loneliness_dataset.parquet`
- [ ] T014 [US1] Implement `src/match/user_match.py`:
 - **Depends on**: T012 (Must read `data/raw/loneliness_dataset.parquet`)
 - Hash raw usernames using a cryptographic hash function (UTF-8 encoded string, no salt) to produce deterministic IDs.
 - Join datasets on hashed ID (Note: Pushshift data is fetched AFTER matching in T013).
 - Drop unmatched rows (users with no Pushshift logs).
 - Output `data/processed/matched_users.parquet` with anonymized IDs.
- [ ] T012.6 [US1] Implement `src/ingest/calculate_matched_window.py`:
 - **Depends on**: T014 (Must read `data/processed/matched_users.parquet`)
 - Load the *matched* user dataset.
 - Recalculate the earliest and latest survey timestamps *only* for the matched users.
 - Persist the corrected boundary timestamps to `data/processed/survey_window_final.json` with keys `start_date` and `end_date`.
 - **Output Artifact**: `data/processed/survey_window_final.json`
- [ ] T013 [US1] Implement `src/ingest/fetch_pushshift.py`:
 - **Depends on**: T014 (Must read `data/processed/matched_users.parquet`) AND T012.6 (Must read `data/processed/survey_window_final.json`)
 - Retrieve AI interaction logs for `r/Replika`, `r/characterAI`, `r/AICompanions`.
 - **Strict Constraint**: Fetch logs ONLY for the exact calendar window defined by `start_date` and `end_date` in `data/processed/survey_window_final.json`.
 - Implement exponential backoff (max retries = 3, 60s timeout) using `src/utils/retry_policy.py` and `src/utils/rate_limit_handler.py`.
 - **Output Artifact**: `data/processed/pushshift_logs_refined.parquet`
- [ ] T015 [US1] Implement `src/validation/validate_match.py`:
 - **Depends on**: T014 (Must read `data/processed/matched_users.parquet`)
 - Calculate match rate (matched count / total loneliness users).
 - Validate N >= 500. [UNRESOLVED-CLAIM: c_45d630cb — status=not_enough_info]
 - **Mandatory**: If match rate < 80% OR N < 500, halt execution with "Power Insufficient" error.
 - Generate `data/validation/match_report.yaml` containing `match_rate`, `total_users`, `matched_users`, `status` (pass/fail).
 - **Output Artifact**: `data/validation/match_report.yaml`
- [ ] T016 [US1] Add logging for ingestion stats and match failures

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Feature Engineering and Attachment Proxy Extraction (Priority: P2)

**Goal**: Compute weekly usage metrics and extract attachment-style proxies using the ECAR Lexicon.

**Independent Test**: Run the feature engineering script on a fixed set of known user posts. and verify calculated attachment scores match manual calculations.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Unit test for attachment score calculation in `tests/unit/test_features.py`
- [ ] T019 [P] [US2] Integration test for feature aggregation in `tests/integration/test_features.py`

### Implementation for User Story 2

- [ ] T021.0 [US2] Implement `src/ingest/download_ecar_lexicon.py`:
 - Download *ECAR Lexicon (Emotion and Coping in AI Relationships)* from Zenodo DOI: `` (Source must be verified in spec).
 - Validate schema: columns `keyword`, `anxiety_weight`, `avoidance_weight`.
 - Save to `data/lexicons/ecar_lexicon.csv`.
 - **Output Artifact**: `data/lexicons/ecar_lexicon.csv`
- [ ] T021.1 [US2] Implement `src/features/define_baseline_window.py`:
 - **Purpose**: Define the temporal window for baseline post identification.
 - Create `config/baseline_window_config.yaml` with key `baseline_days_preceding` set to `30`.
 - **Output Artifact**: `config/baseline_window_config.yaml`
- [ ] T020 [P] [US2] Implement `src/features/usage_metrics.py`:
 - **Depends on**: T014 (Must read `data/processed/matched_users.parquet`)
 - Aggregate weekly usage frequency per user.
 - Calculate `session_duration` as the time difference between the first and last timestamp of consecutive activities in a 7-day window (NO cap).
 - Handle edge cases: multiple activities, missing data.
 - **Input**: `data/processed/matched_users.parquet` (Strict dependency).
 - **Output**: `data/processed/usage_metrics.parquet`
- [ ] T021 [US2] Implement `src/features/attachment_proxy.py`:
 - **Depends on**: T014 (Must consume `data/processed/matched_users.parquet`), T021.0 (Must consume `data/lexicons/ecar_lexicon.csv`), AND T021.1 (Must consume `config/baseline_window_config.yaml`).
 - Load *ECAR Lexicon* from `data/lexicons/ecar_lexicon.csv`.
 - Load baseline window config from `config/baseline_window_config.yaml`.
 - **Baseline Post Identification**: Identify baseline posts by filtering Pushshift logs for posts within the defined 30-day window preceding the user's first survey timestamp in the matched dataset.
 - Scan baseline posts for anxiety/avoidance keywords.
 - Compute normalized `attachment_anxiety_score` and `attachment_avoidance_score`.
 - Assign default 0.0 and set `missing_attachment_flag` for users with no baseline posts.
 - **Input**: `data/processed/matched_users.parquet`, `data/processed/pushshift_logs_refined.parquet` (from T013), `data/lexicons/ecar_lexicon.csv`, `config/baseline_window_config.yaml`.
 - **Output**: `data/processed/attachment_scores.parquet`
- [ ] T022 [US2] Implement `src/features/integrate_features.py`:
 - Merge usage metrics and attachment scores into the unified dataset.
 - **Input**: `data/processed/matched_users.parquet`, `data/processed/usage_metrics.parquet`, `data/processed/attachment_scores.parquet`.
 - **Output**: `data/processed/unified_dataset.parquet`.
 - Validate output columns against `contracts/unified_dataset.schema.yaml`.
- [ ] T023 [US2] Validate output columns against `contracts/unified_dataset.schema.yaml`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Mixed-Effects Modeling and Robustness Validation (Priority: P3)

**Goal**: Fit a linear mixed-effects model with lagged predictors and bootstrap resampling for robust confidence intervals.

**Independent Test**: Run the model on a synthetic dataset with known coefficients and verify estimated coefficients fall within the confidence interval of true values.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T024 [P] [US3] Unit test for MixedLM fitting in `tests/unit/test_modeling.py`
- [ ] T025 [P] [US3] Integration test for bootstrap resampling in `tests/integration/test_bootstrap.py`

### Implementation for User Story 3

- [ ] T026 [US3] Implement `src/modeling/mixed_effects.py`:
 - **Depends on**: T022 (Must consume `data/processed/unified_dataset.parquet`) AND T025.5 (Must consume `config/model_structure.yaml`).
 - **Input**: `data/processed/unified_dataset.parquet`, `config/model_structure.yaml`.
 - **Mandatory**: Load random effect structure (Intercepts + Slopes for UsageFrequency) from `config/model_structure.yaml`.
 - **CONSTRAINT**: If `config/model_structure.yaml` is missing or invalid, the script MUST FAIL LOUDLY with an error message stating: "Pre-specified model structure missing. Expected: random intercepts for User, random slopes for UsageFrequency by User." (Do NOT fallback to hardcoded values).
 - **Mandatory**: Implement lagged predictor structure (Usage T → Loneliness T+1) by:
 1. Sorting data by `user_id` and `timestamp`.
 2. **Shifting** the `loneliness_score` column by +1 time step (creating `loneliness_T_plus_1`).
 3. Aligning `usage_frequency` (T) with `loneliness_T_plus_1` (T+1).
 - Fit Linear Mixed-Effects Model (statsmodels MixedLM) using the pre-specified random effects.
 - Controls: Baseline attachment scores.
 - **Output**: `data/results/model_fit_summary.json`.
- [ ] T027 [US3] Implement `src/modeling/bootstrap_ci.py`:
 - Perform cluster bootstrap resampling with **1000 iterations** (seed=42) at User level.
 - Generate confidence intervals.
 - Run diagnostics (normality, homoscedasticity); switch to bootstrap CIs if violated.
 - **Output**: `data/results/bootstrap_ci.json`.
- [ ] T028 [US3] Implement `src/modeling/subgroup_analysis.py`:
 - **Depends on**: T022.
 - **Input**: `data/processed/unified_dataset.parquet`.
 - Filter unified dataset where `age >= 60` **AND** `age is not null` (exclude missing ages).
 - Re-fit model and compare effect sizes against full population.
 - **Output**: `data/results/subgroup_analysis_60plus.json`.
- [ ] T029 [US3] Implement `src/validation/validate_success.py`:
 - Compute success metrics: Marginal R² gain (SC-002, threshold = 0.05), CI stability (SC-003), Runtime (SC-004).
 - **Mandatory Check**: Compare Marginal R² gain against threshold = 0.05 (from SC-002).
 - **Do NOT halt execution** if R² gain < 0.05. Instead, set the `passed` flag to `false` in the report.
 - If Runtime >= 6 hours (per Plan Phase 7), set `passed` flag to `false`.
 - Generate `data/results/robustness_report.csv` with the following schema:
 - `metric_name` (e.g., "marginal_r2_gain", "ci_stability", "runtime_hours")
 - `value` (float/string)
 - `threshold` (float/string, e.g., "0.05" or "6.0")
 - `passed` (boolean)
 - `timestamp`
 - **Output Artifact**: `data/results/robustness_report.csv`.
- [ ] T030 [US3] Export `model_results.csv` and generate concise HTML report

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T031 [P] Documentation updates: Update `docs/README.md`, `docs/quickstart.md`, and `src/README.md` with new endpoints and installation steps
- [ ] T032a [P] Refactor `src/modeling/mixed_effects.py` to reduce cyclomatic complexity to < 10
- [ ] T032b [P] Refactor `src/modeling/bootstrap_ci.py` to reduce cyclomatic complexity to < 10
- [ ] T033a [P] Optimize `src/modeling/bootstrap_ci.py` to reduce runtime to < 4 hours on 2-CPU runner
- [ ] T033b [P] Optimize memory usage in `src/features/integrate_features.py` for large datasets
- [ ] T034 [P] Additional unit tests for edge cases in `tests/unit/`
- [ ] T035 Security hardening (ensure no PII leakage in logs or outputs)
- [ ] T036 Run `quickstart.md` validation to ensure end-to-end reproducibility

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output (specifically `matched_users.parquet`)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 feature output (specifically `unified_dataset.parquet`)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Ingestion (T012) before Matching (T014)
- Matching (T014) before Window Calculation (T012.6) and Pushshift Fetch (T013)
- Pushshift Fetch (T013) before Feature Engineering (T020, T021)
- Feature Engineering (T020, T021) before Modeling (T026)
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2) EXCEPT T025.5
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for unified dataset schema in tests/contract/test_unified_schema.py"
Task: "Integration test for end-to-end data ingestion on sample data in tests/integration/test_full_pipeline.py"

# Launch ingestion scripts in parallel (they fetch different data sources):
Task: "Implement src/ingest/download_loneliness.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (verify match rate and data integrity)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Data Ingestion)
 - Developer B: User Story 2 (Feature Engineering)
 - Developer C: User Story 3 (Modeling)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical**: Ensure all data sources (Zenodo, Pushshift) are real and accessible before execution. Do not fabricate data.