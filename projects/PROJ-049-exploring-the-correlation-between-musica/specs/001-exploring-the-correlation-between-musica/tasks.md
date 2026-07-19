# Tasks: Exploring the Correlation Between Musical Preference and Personality Traits

**Input**: Design documents from `/specs/001-music-personality-correlation/`
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

- [X] T001a [P] Create directory structure: `data/raw/`, `data/processed/`, `code/`, `tests/`, `results/`, `logs/`. **Note**: The `contracts/` directory is created in Phase 2 (T007a) as it is a foundational artifact, not a generic setup directory.
- [X] T001b [P] Create empty `__init__.py` files in `code/` and `tests/`
- [X] T001c [P] Initialize `requirements.txt` with placeholder dependencies
- [X] T002 [P] Initialize Python project with dependencies in `requirements.txt`. **Content**: Pin exact versions for `pandas`, `scikit-learn`, `scipy`, `matplotlib`, `seaborn`, `numpy`, `openml`, `requests`, `pytest`, `statsmodels`. **Verification**: Run `pip install -r requirements.txt` successfully; ensure all versions are pinned (e.g., `pandas==2.0.0`).
- [X] T003a [P] Create `.ruff.toml` configuration file for linting. **Content**: Set `line-length = 88`, `target-version = "py311"`, and enable specific rules (E, F, W).
- [X] T003b [P] Create `pyproject.toml` with `[tool.black]` configuration for formatting. **Content**: Set `line-length = 88`, `target-version = ['py311']`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005a [P] Implement `setup_logging()` function in `code/utils.py` returning a logger configured with file rotation to `logs/app.log`.
- [X] T006b [P] Create `.env.example` file listing expected environment variable names (e.g., `RANDOM_SEED`, `DATA_PATH`) with placeholder values.
- [X] T006a Implement `load_config()` function in `code/utils.py` returning a dict of environment variables (Depends on T006b to ensure variables are defined).
- [X] T007a [P] Create `contracts/` directory if it does not exist. **Verification**: `ls contracts/` must succeed.
- [X] T007b [P] Define schema fields in `contracts/dataset.schema.yaml` (fields: `user_id`, `openness`, `conscientiousness`, `extraversion`, `agreeableness`, `neuroticism`, `age`, `gender`, `country`) and `contracts/analysis_output.schema.yaml` (fields: `trait`, `genre`, `rho`, `p_value`, `adjusted_p_value`, `is_significant`). **Verification**: Validate a sample CSV against the schema.
- [X] T008 [P] Implement `code/synthetic_data.py`: Generate a deterministic synthetic dataset with a fixed random seed, 1000 rows, specific column names matching `contracts/dataset.schema.yaml`, and realistic distributions (e.g., age 18-65, uniform genre distribution). Save to `data/processed/synthetic_data.csv`. **Verification**: Validate output against `contracts/dataset.schema.yaml`.
- [X] T009 [P] Setup error handling wrappers in `code/utils.py` for HTTP timeouts and 404s.
- [X] T035 [P] Implement `code/ingest.py` data source validation logic: Check `plan.md` for "NO verified source" flag. If present, log `VALIDATION_MODE: NO_REAL_DATA` and skip network requests. (Ref: Plan "Validation Mode" section).
- [X] T036 [P] Implement `code/ingest.py` fallback logic: If "NO verified source" is detected, invoke `code/synthetic_data.py` (T008). If a verified source is listed but fetch fails (HTTP 404/Timeout), raise `DataUnavailableError` with message "Real data fetch failed; verified source unavailable". (Ref: Rule "The loader must FAIL LOUDLY" for real sources, but graceful fallback for Validation Mode).
- [X] T037 [P] Add `--force-synthetic` CLI flag to `code/pipeline.py` that explicitly overrides the default behavior and forces the use of `code/synthetic_data.py` even if real data is available, for reproducible validation runs.
- [X] T038 [P] Update `tests/test_analysis.py` to include a test case that verifies the statistical output is identical when run with `--force-synthetic` vs. a pre-generated synthetic file, ensuring the synthetic generator is deterministic.
- [X] T039 [P] Update `results/results_report.csv` generation to include a metadata column `data_source` that explicitly states either "REAL_DATA" or "SYNTHETIC_VALIDATION_MODE" to prevent misinterpretation of results.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Ingest BFI-2 and Last.fm data (or synthetic fallback), clean, map genres, and merge into a unified dataframe.

**Independent Test**: The pipeline can be tested by executing the data loading script and verifying the output dataframe contains non-null values for all 5 personality traits and at least 10 standardized genre categories (plus 'Other') for a sample of at least 100 users, with no missing demographic covariates.

### Implementation for User Story 1

- [X] T014 [US1] Implement `code/mapping.py`: Load lookup table from `contracts/genre_lookup.yaml` and map raw genre tags to standard categories + 'Other'. **Verification**: Test with inputs `['alt', 'rock']` expecting `['Rock', 'Rock']`.
- [X] T015 [US1] Implement `code/ingest.py`: Merge personality and listening data on `user_id`; exclude users with zero listening minutes.
- [X] T016 [US1] Implement `code/ingest.py`: Handle missing demographic data (impute numeric with median, categorical with mode) or exclude; log counts. **Verification**: Log "Excluded X rows" or "Imputed Y rows using median/mode".
- [X] T010 [US1] Define test cases in `tests/test_mapping.py`: `test_map_raw_tags_to_standard` using inputs `['alt', 'rock']` and expected output from `contracts/genre_lookup.yaml`. (Depends on T014 implementation).
- [X] T011 [US1] Define test cases in `tests/test_ingest.py`: `test_missing_data_imputation` verifying strategy and logging. (Depends on T016 implementation).
- [X] T012 [US1] Implement `code/ingest.py`: **Download/Fallback Logic**: 
    1. Check for "NO verified source" in `plan.md` (T035). If present, log `VALIDATION_MODE` and immediately invoke `code/synthetic_data.py` (T008).
    2. If verified source exists, attempt download with a configurable timeout.
    3. If HTTP 404/Timeout occurs, log `FALLBACK: SYNTHETIC` and invoke `code/synthetic_data.py` (T008).
    4. Call mapping (T014), merge (T015), and missing data handler (T016).
    5. Save final merged dataset to `data/processed/merged_data.csv` and compute/store checksum.
    **Verification**: Log file exists and contains correct columns.
- [X] T017 [US1] Verify `data/processed/merged_data.csv` schema integrity (non-empty, correct columns) and log checksum.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Correlation and Regression Analysis (Priority: P2)

**Goal**: Compute Spearman correlations and multiple linear regressions with demographic controls, applying FDR correction.

**Independent Test**: The analysis can be tested by running the script on a known synthetic dataset with pre-calculated correlation values and verifying the output matches the expected coefficients within an acceptable tolerance.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Unit test for Spearman correlation calculation in `tests/test_analysis.py` (verify against synthetic ground truth with a strict numerical tolerance).
- [X] T019 [P] [US2] Unit test for Benjamini-Hochberg FDR correction in `tests/test_analysis.py` (verify p-value adjustment logic).

### Implementation for User Story 2

- [X] T020 [US2] Implement `code/analysis.py`: 
    1. Log-transform `listening_minutes`.
    2. Compute Spearman rho and p-values for all trait-genre pairs.
    3. Write intermediate results to `data/processed/correlation_results.csv` with columns: `trait`, `genre`, `rho`, `p_value`.
    4. Calculate boolean flag for `r > 0.3` (SC-001).
    **Verification**: Verify file exists, contains correct columns, and numerical values match synthetic ground truth within 0.001 tolerance.
- [X] T021 [US2] Implement `code/analysis.py`: Run multiple linear regression for each trait with age, gender, and country (one-hot encoded) as covariates.
- [X] T022 [FR-004] [US2] Implement `code/analysis.py`: Detect collinear predictors using VIF (statsmodels) with a standard threshold. If dropped, log the specific predictor name, update the regression model, and output a `model_definition` column in results as a JSON string listing the *actual* covariates used.
- [X] T023 [US2] Implement `code/analysis.py`: Apply Benjamini-Hochberg FDR correction (q < 0.05) to all p-values based on the dynamic count of tests. **Note**: This implements Spec FR-005, which supersedes Constitution Principle VI (Bonferroni) for this project per the Spec's explicit override.
- [X] T024 [US2] Save final analysis results (rho, p-value, adjusted p-value, is_significant, beta coefficients, model_definition) to `data/processed/analysis_results.csv`. (Depends on T020, T021, T022, T023).
- [X] T034 [US2] Implement `code/analysis.py`: Calculate the delta in regression coefficients for personality traits between models with covariates and models without covariates to satisfy SC-003 (validity of demographic controls). **Verification**: Log the delta, compare against a threshold (e.g., >10% change), and explicitly flag as "VALIDITY_CONFIRMED" or "VALIDITY_FAILED" in the log and a new column `validity_status` in `data/processed/coefficient_deltas.csv`.

**Checkpoint**: At this point, All user stories should now be independently functional

---

## Phase 5: User Story 3 - Visualization and Reporting (Priority: P3)

**Goal**: Generate correlation heatmap, regression coefficient plots, and a summary report with effect sizes.

**Independent Test**: The reporting module can be tested by executing the script and verifying the existence of a `results_report.csv` and a `correlation_heatmap.png` file, ensuring the heatmap correctly displays the sign and magnitude of correlations.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T025 [P] [US3] Integration test for report generation in `tests/test_reporting.py` (verify file existence and content schema).

### Implementation for User Story 3

- [X] T026 [US3] Implement `code/analysis.py`: Read `data/processed/analysis_results.csv` (T024 output). Generate `results/correlation_heatmap.png` (800x600, 150dpi) using seaborn with a **diverging colormap** ('coolwarm'). **Axis Labels**: "Personality Trait" (y), "Genre" (x). **Title**: "Spearman Correlation: Personality vs. Music Genre". **Verification**: Verify output file exists and color intensity maps to signed rho values.
- [X] T027 [US3] Implement `code/analysis.py`: Calculate **Pearson's r** effect sizes and **Fisher's z** confidence intervals for significant results as mandated by FR-006/US-3. **Clarification**: This is a secondary calculation performed on the Spearman correlation results to report effect size magnitude, not a replacement for the primary Spearman analysis.
- [X] T028 [US3] Implement `code/analysis.py`: Generate `results/results_report.csv` containing effect sizes, CIs, and explicit "Non-significant" labels for multiple traits across multiple genres. **Verification**: Fill nulls with string "Non-significant" and ensure schema matches FR-006. (Depends on T027).
- [X] T029 [P] [US3] Add `tests/test_report.py::test_report_completeness` to verify `results_report.csv` includes all relevant traits across a diverse set of genres.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T030 [P] Documentation updates in `README.md` with execution instructions and synthetic data explanation.
- [X] T031 Code cleanup and refactoring in `code/` (Only after T020, T026, T028 are verified complete).
- [X] T032a [P] Add `tests/test_edge_cases.py::test_empty_dataset` for empty dataset handling.
- [X] T032b [P] Add `tests/test_edge_cases.py::test_all_missing_demographics` for missing demographic handling.
- [X] T033 [P] [US1-US3] Implement `code/pipeline.py` end-to-end orchestration script that sequentially executes ingestion, analysis, and reporting; add timing logic to record execution time in `logs/timing.log` and fail the run if total time exceeds **6 hours** (as defined by SC-004).

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires merged data from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires analysis results from US2

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2, except T006a which depends on T006b)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for genre mapping logic in tests/test_mapping.py"
Task: "Unit test for missing data imputation in tests/test_ingest.py"

# Launch all implementation tasks for User Story 1 together:
Task: "Implement code/mapping.py: Load lookup table..."
Task: "Implement code/ingest.py: Merge personality and listening data..."
Task: "Implement code/ingest.py: Orchestration (Download/Fallback)... (Depends on T014/T015/T016)"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
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
 - Developer A: User Story 1
 - Developer B: User Story 2
 - Developer C: User Story 3
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
- **Critical**: Ensure synthetic data generator uses a fixed seed for reproducibility on CI.
- **Critical**: Ensure all statistical tests run on CPU only (no GPU dependencies).
- **Critical**: T012 implements the download attempt (FR-001) with explicit fallback logic for Validation Mode.
- **Critical**: T020, T026, T028 are now marked complete and include verification steps for numerical accuracy and schema compliance.
- **Critical**: Phase O has been merged into Phase 2 to ensure data source validation runs before ingestion.
- **Critical**: `contracts/` directory creation is now exclusively handled in Phase 2 (T007a) to avoid confusion.