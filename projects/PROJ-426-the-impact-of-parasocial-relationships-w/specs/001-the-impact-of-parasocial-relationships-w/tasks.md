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
- [X] T006 [P] Implement `src/utils/config.py`:
 - Define configuration management for API keys and data paths.
 - Create `config/env_config.yaml` with placeholders for `ZENODO_API_KEY`, `PUSHSHIFT_API_URL`.
 - **Output Artifact**: `src/utils/config.py` and `config/env_config.yaml`
- [X] T007 [P] Implement `src/utils/data_validation.py`:
 - Implement schema validation functions using `jsonschema`.
 - Create checksum utility to record file hashes in `state/artifact_hashes.yaml`.
 - **Output Artifact**: `src/utils/data_validation.py`
- [X] T008 [P] Implement `src/utils/retry_policy.py`:
 - Define exponential backoff strategy (max retries = 3, base delay = 1 second, max delay 60s).
 - Create configuration object for retry logic.
 - **Output Artifact**: `src/utils/retry_policy.py`
- [X] T009 [P] Implement `src/utils/rate_limit_handler.py`:
 - Implement logic to handle 429 responses from Pushshift API.
 - Integrate with `retry_policy.py` for backoff.
 - Verify error handling by simulating rate limit responses in unit tests.
 - **Output Artifact**: `src/utils/rate_limit_handler.py`
- [X] T025.5 [P] Implement `src/modeling/config_model_structure.py`:
 - **Purpose**: Satisfy Constitution Principle VI (Pre-specification) and FR-005
 - Define the random effect structure (Intercepts for User, random slopes for UsageFrequency by User) in `config/model_structure.yaml`.
 - Define fixed effects and lagged structure in the same config.
 - **CONSTRAINT**: This script must NOT read any data files from `data/` or perform any data exploration. It must rely solely on hardcoded specifications from the plan.
 - **Output Artifact**: `config/model_structure.yaml`

---

## Phase 3: User Story 1 - Data Ingestion and User Matching (Priority: P1) 🎯 MVP

**Goal**: Ingest the Reddit Loneliness Longitudinal Dataset and Pushshift logs, match users via hashed usernames, and produce a unified analysis-ready dataset.

**Independent Test**: Execute the data pipeline on a sample subset and verify the output table contains matched records with non-null values for both loneliness scores and usage metrics.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Contract test for unified dataset schema in `tests/contract/test_unified_schema.py`
- [X] T011 [P] [US1] Integration test for end-to-end data ingestion on sample data in `tests/integration/test_full_pipeline.py`:
 - **Logic**: Fetch first 100 users from the Zenodo dataset.
 - **Action**: Run `download_loneliness.py`, `fetch_pushshift.py`, and `user_match.py`.
 - **Verification**: Assert that `data/processed/matched_users.parquet` exists, contains >= 100 rows, and has no null values in `loneliness_score` or `usage_frequency`.
 - **Expected Failure**: Initially, the pipeline will fail due to missing implementation in T012, T013, T014.

### Implementation for User Story 1

- [X] T012 [US1] Implement `src/ingest/download_loneliness.py`:
 - Fetch *Reddit Loneliness Longitudinal Dataset* from Zenodo DOI.
 - **Mandatory Validation**: Validate presence of `username` or `username_hash` AND **verify that each user has at least 6 distinct calendar months of non-null loneliness scores**.
 - **Halt Condition**: If any user lacks 6 distinct months or linkable IDs are missing, halt with "Data Linkage Impossible" or "Insufficient Longitudinal Data" error.
 - Log ingestion stats (total rows, unique users, date range, validation pass/fail) to `data/logs/ingest.log`.
 - **Output Artifact**: `data/raw/loneliness_dataset.parquet`
- [X] T013 [US1] Implement `src/ingest/fetch_pushshift.py`:
 - **Depends on**: T012 (Must read `data/raw/loneliness_dataset.parquet` to determine date range).
 - **Date Range Logic**: Retrieve AI interaction logs for `r/Replika`, `r/characterAI`, `r/AICompanions` strictly for the **exact calendar window defined by the earliest and latest survey timestamps in the MATCHED user set** (not the entire dataset).
 - Implement exponential backoff (max retries = 3, 60s timeout) using `src/utils/retry_policy.py` and `src/utils/rate_limit_handler.py`.
 - Log fetch stats (total logs retrieved, API calls made, date range used) to `data/logs/ingest.log`.
 - **Output Artifact**: `data/raw/pushshift_logs.parquet`
- [X] T014 [US1] Implement `src/match/user_match.py`:
 - **Depends on**: T012 (Must read `data/raw/loneliness_dataset.parquet`) AND T013 (Must read `data/raw/pushshift_logs.parquet`).
 - **PII Constraint**: Raw usernames MUST be hashed in memory and NEVER logged or written to disk. Only the SHA-256 hash is persisted.
 - Hash raw usernames using SHA-256 (UTF-8 encoded, no salt) to produce deterministic IDs.
 - Join datasets on hashed ID.
 - Drop unmatched rows (users with no Pushshift logs).
 - Output `data/processed/matched_users.parquet` with anonymized IDs.
 - Log match stats (total matched, match rate) to `data/logs/ingest.log`.
 - **Output Artifact**: `data/processed/matched_users.parquet`
- [X] T015 [US1] Implement `src/validation/validate_match.py`:
 - **Depends on**: T014 (Must read `data/processed/matched_users.parquet`).
 - Calculate match rate (matched count / total loneliness users).
 - Validate N >= 500.
 - **Mandatory**: If match rate < 80% OR N < 500, halt execution with "Power Insufficient" error.
 - Generate `data/validation/match_report.yaml` containing `match_rate`, `total_users`, `matched_users`, `status` (pass/fail).
 - **Output Artifact**: `data/validation/match_report.yaml`
- [X] T015b [US1] Implement `src/validation/power_analysis.py`:
 - **Depends on**: T015 (Must read `data/validation/match_report.yaml`).
 - **Purpose**: Satisfy Plan Phase 1b (Power Analysis).
 - If N < 500, calculate the detectable effect size (Cohen's d) given the sample size and power (0.8).
 - If d > 0.8, log a "Power Limitation" warning but allow execution to proceed (as per Plan assumption), or halt if configured strictly.
 - **Output Artifact**: `data/validation/power_analysis_report.yaml`

---

## Phase 4: User Story 2 - Feature Engineering and Attachment Proxy Extraction (Priority: P2)

**Goal**: Compute weekly usage metrics and extract attachment-style proxies using the ECAR Lexicon.

**Independent Test**: Run the feature engineering script on a fixed set of known user posts. and verify calculated attachment scores match manual calculations.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Unit test for attachment score calculation in `tests/unit/test_features.py`
- [ ] T019 [P] [US2] Integration test for feature aggregation in `tests/integration/test_features.py`

### Implementation for User Story 2

- [X] T021.0 [P] [US2] Implement `src/ingest/download_ecar_lexicon.py`:
 - Download *ECAR Lexicon (Emotion and Coping in AI Relationships)* from Zenodo DOI.
 - Validate schema: columns `keyword`, `anxiety_weight`, `avoidance_weight`.
 - **Mandatory Halt**: If the lexicon is missing, invalid, or schema validation fails, **HALT execution immediately** with "Lexicon Missing" error (FR-008). Do not proceed.
 - Save to `data/lexicons/ecar_lexicon.csv`.
 - **Output Artifact**: `data/lexicons/ecar_lexicon.csv`
- [X] T021.1 [P] [US2] Implement `src/features/define_baseline_window.py`:
 - **Purpose**: Define the temporal window for baseline post identification.
 - Create `config/baseline_window_config.yaml` with key `baseline_days_preceding` set to `30`.
 - **Output Artifact**: `config/baseline_window_config.yaml`
- [X] T020 [P] [US2] Implement `src/features/usage_metrics.py`:
 - **Depends on**: T014 (Must read `data/processed/matched_users.parquet`) AND T013 (Must read `data/raw/pushshift_logs.parquet`) AND T015 (Success check).
 - Aggregate weekly usage frequency per user.
 - Calculate `session_duration` as the time difference between the first and last timestamp of consecutive activities in a 7-day window, **CAPPED at a fixed duration (e.g., 24 hours) per session** as per User Story 2.
 - Handle edge cases: multiple activities, missing data.
 - **Input**: `data/processed/matched_users.parquet`, `data/raw/pushshift_logs.parquet`.
 - **Output**: `data/processed/usage_metrics.parquet`
- [X] T021 [US2] Implement `src/features/attachment_proxy.py`:
 - **Depends on**: T014 (Must consume `data/processed/matched_users.parquet`), T013 (Must consume `data/raw/pushshift_logs.parquet`), T015 (Success check), T021.0 (Must consume `data/lexicons/ecar_lexicon.csv`), AND T021.1 (Must consume `config/baseline_window_config.yaml`).
 - Load *ECAR Lexicon* from `data/lexicons/ecar_lexicon.csv`.
 - Load baseline window config from `config/baseline_window_config.yaml`.
 - **Baseline Post Identification**: Identify baseline posts by filtering Pushshift logs for posts within the defined 30-day window preceding the user's first survey timestamp in the matched dataset.
 - Scan baseline posts for anxiety/avoidance keywords.
 - Compute normalized `attachment_anxiety_score` and `attachment_avoidance_score`.
 - **Mandatory Exclusion**: If a user has no baseline posts OR if the lexicon extraction fails for that user, **EXCLUDE the user from the analysis dataset**. Do NOT assign default 0.0 or set a flag for imputation (FR-004b).
 - **Input**: `data/processed/matched_users.parquet`, `data/raw/pushshift_logs.parquet`, `data/lexicons/ecar_lexicon.csv`, `config/baseline_window_config.yaml`.
 - **Output**: `data/processed/attachment_scores.parquet` (contains only users with valid scores)
- [X] T022 [US2] Implement `src/features/integrate_features.py`:
 - **Depends on**: T020, T021.
 - Merge usage metrics and attachment scores into the unified dataset.
 - **Input**: `data/processed/matched_users.parquet`, `data/processed/usage_metrics.parquet`, `data/processed/attachment_scores.parquet`.
 - **Output**: `data/processed/unified_dataset.parquet`.
 - Validate output columns against `contracts/unified_dataset.schema.yaml`.
- [X] T023 [US2] Validate output columns against `contracts/unified_dataset.schema.yaml`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Mixed-Effects Modeling and Robustness Validation (Priority: P3)

**Goal**: Fit a linear mixed-effects model with lagged predictors and bootstrap resampling for robust confidence intervals.

**Independent Test**: Run the model on a synthetic dataset with known coefficients and verify estimated coefficients fall within the confidence interval of true values.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T024 [P] [US3] Unit test for MixedLM fitting in `tests/unit/test_modeling.py`
- [ ] T025 [P] [US3] Integration test for bootstrap resampling in `tests/integration/test_bootstrap.py`

### Implementation for User Story 3

- [X] T026b [US3] Implement `src/modeling/baseline_model.py`:
 - **Depends on**: T022 (Must consume `data/processed/unified_dataset.parquet`).
 - **Purpose**: Fit the intercept-only baseline model required for SC-002 (Marginal R² calculation).
 - Fit Linear Mixed-Effects Model with only a random intercept for `User` and no fixed effects (except intercept).
 - **Output**: `data/results/baseline_model_summary.json` (contains logLik, AIC, BIC, variance components).
- [X] T026 [US3] Implement `src/modeling/mixed_effects.py`:
 - **Depends on**: T022 (Must consume `data/processed/unified_dataset.parquet`) AND T025.5 (Must consume `config/model_structure.yaml`).
 - **Input**: `data/processed/unified_dataset.parquet`, `config/model_structure.yaml`.
 - **Mandatory**: Load random effect structure (Intercepts + Slopes for UsageFrequency) from `config/model_structure.yaml`.
 - **CONSTRAINT**: If `config/model_structure.yaml` is missing or invalid, the script MUST FAIL LOUDLY with an error message stating: "Pre-specified model structure missing. Expected: random intercepts for User, random slopes for UsageFrequency by User." (Do NOT fallback to hardcoded values).
 - **Mandatory**: Implement lagged predictor structure (Usage T → Loneliness T+1) by:
 1. Sorting data by `user_id` and `timestamp`.
 2. **Shifting** the `loneliness_score` column by +1 time step (creating `loneliness_T_plus_1`).
 3. Aligning `usage_frequency` (T) and **`session_duration` (T)** with `loneliness_T_plus_1` (T+1).
 - Fit Linear Mixed-Effects Model (statsmodels MixedLM) using the pre-specified random effects.
 - **Fixed Effects**: `UsageFrequency`, **`SessionDuration`**, and attachment style controls.
 - **Random Effects**: Random intercepts for `User`, **random slopes for `UsageFrequency` and `SessionDuration` by `User`** (as per FR-005).
 - **Output**: `data/results/model_fit_summary.json`.
- [X] T026c [US3] Implement `src/modeling/export_results.py`:
 - **Depends on**: T026.
 - Convert `model_fit_summary.json` to CSV format for downstream reporting.
 - **Output**: `data/results/model_results.csv`.
 - **Schema**: `parameter`, `estimate`, `std_error`, `p_value`, `ci_lower`, `ci_upper`.
- [X] T027 [US3] Implement `src/modeling/bootstrap_ci.py`:
 - **Depends on**: T026.
 - Perform cluster bootstrap resampling with **1000 iterations** (seed=42) at User level.
 - Generate confidence intervals.
 - Run diagnostics (normality, homoscedasticity); switch to bootstrap CIs if violated.
 - **Output**: `data/results/bootstrap_ci.json`.
- [X] T028 [US3] Implement `src/modeling/subgroup_analysis.py`:
 - **Depends on**: T022 AND T026 (Primary Model).
 - **Input**: `data/processed/unified_dataset.parquet`, `data/results/model_fit_summary.json`.
 - Filter unified dataset where `age >= 60` **AND** `age is not null` (exclude missing ages).
 - Re-fit model and compare effect sizes against full population model (T026 output).
 - **Output**: `data/results/subgroup_analysis_60plus.json`.
- [X] T029 [US3] Implement `src/validation/validate_success.py`:
 - **Depends on**: T026b (Baseline Model), T026 (Primary Model), T027 (Bootstrap), T022.
 - Compute success metrics: Marginal R² gain (SC-002, threshold = 0.05), CI stability (SC-003), Runtime (SC-004).
 - **Mandatory Check 1 (Power Gate)**: If N < 500 OR match rate < 80%, HALT execution with "Power Insufficient" error.
 - **Mandatory Check 2 (Model Fit)**: If Marginal R² gain < 0.05, set `passed` flag to `false` in the report (do NOT halt).
 - **Mandatory Check 3 (Runtime)**: If **Runtime > 6.0 hours**, set `passed` flag to `false`. (Note: [deferred] is a PASS per SC-004).
 - Generate `data/results/robustness_report.csv` with the following schema:
 - `metric_name` (e.g., "marginal_r2_gain", "ci_stability", "runtime_hours")
 - `value` (float/string)
 - `threshold` (float/string, e.g., "0.05" or "6.0")
 - `passed` (boolean)
 - `timestamp`
 - **Output Artifact**: `data/results/robustness_report.csv`.
- [X] T030a [US3] Implement `src/validation/export_results.py`:
 - **Depends on**: T026c.
 - Ensure `model_results.csv` is available in `data/results/`.
 - **Output Artifact**: `data/results/model_results.csv`.
- [X] T030b [US3] Implement `src/validation/generate_report.py`:
 - **Depends on**: T030a, T029.
 - Generate `report.html` using `data/results/model_results.csv` and `data/results/robustness_report.csv`.
 - Use `jinja2` template for layout.
 - **Output Artifact**: `data/results/report.html`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T031a [P] Implement `docs/README.md`:
 - Add project overview, installation steps, and usage instructions.
 - **Output Artifact**: `docs/README.md`
- [X] T031b [P] Implement `docs/quickstart.md`:
 - Add API key setup instructions and a step-by-step guide to run the pipeline.
 - **Output Artifact**: `docs/quickstart.md`
- [X] T032 [P] Refactor `src/modeling/mixed_effects.py` to reduce cyclomatic complexity to < 10.
 - **Metric**: Use `radon` or similar tool to verify complexity.
 - **Output Artifact**: Updated `src/modeling/mixed_effects.py`.
- [X] T033 [P] Optimize `src/modeling/bootstrap_ci.py` to reduce runtime to < 4 hours on 2-CPU runner.
 - **Metric**: Profile execution time and optimize loops/parallelization.
 - **Output Artifact**: Updated `src/modeling/bootstrap_ci.py`.
- [X] T034 [P] Additional unit tests for edge cases in `tests/unit/`.
 - **Specific Cases**: `test_missing_age`, `test_null_text`, `test_empty_dataset`, `test_lexicon_validation_fail`.
- [X] T035 [P] Security hardening.
 - **Action**: Run `gitleaks` on all logs in `data/logs/` and `src/` to ensure zero PII matches.
 - **Pass Criteria**: Zero PII matches found.
- [X] T036 [P] Run `quickstart.md` validation to ensure end-to-end reproducibility.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output (specifically `matched_users.parquet` and `match_report.yaml` success)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 feature output (specifically `unified_dataset.parquet`)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Ingestion (T012) before Fetch Pushshift (T013)
- Fetch Pushshift (T013) before Matching (T014)
- Matching (T014) before Feature Engineering (T020, T021)
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