# Tasks: Physical Activity Levels and Mood Variability in Daily Life

**Input**: Design documents from `/specs/001-physical-activity-levels-and-mood-variability/`
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

- [X] T001a Create `code/__init__.py`
- [X] T001b Create `data/raw/.gitkeep`, `data/processed/.gitkeep`, and `data/interim/.gitkeep`
- [X] T001c Create `tests/unit/.gitkeep` and `tests/contract/.gitkeep`

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002 Initialize Python project with dependencies (`pandas`, `statsmodels`, `scikit-learn`, `pyyaml`, `requests`, `numpy`) in `code/requirements.txt`
- [ ] T003a [P] Create `.flake8` configuration file in `code/` with `[flake8]` section, `max-line-length = 88`, and `ignore = E203, E266, W503` (Supports Constitution Principle I: Reproducibility)
- [X] T003b [P] Create `pyproject.toml` in `code/` with `[tool.black]` section, `line-length = 88`, and `target-version = ['py311']` (Supports Constitution Principle I: Reproducibility)
- [X] T004 [P] Create configuration module `code/config.py` defining paths, random seeds (a fixed value), constants (including `MISSINGNESS_THRESHOLD`), and the specific OSF DOI string for the dataset
- [X] T005a [P] Create schema definition `daily_aggregates.schema.yaml` in `specs/001-physical-activity-levels-and-mood-variability/contracts/` with the following structure:
 - `participant_id`: string, required
 - `date`: date, required
 - `total_steps`: integer, required, min=0
 - `mean_mood`: float, required
 - `mood_std`: float, required, min=0 (raw standard deviation, NO transformation applied here)
 - `n_mood_ratings`: integer, required, min=2
 - `sleep_duration`: float, nullable
 - `baseline_affect`: float, nullable
 - `day_of_week`: integer, required (0=Monday)
- [X] T005b [P] Create schema definition `model_results.schema.yaml` in `specs/001-physical-activity-levels-and-mood-variability/contracts/` with the following structure:
 - `model_type`: string, required (e.g., "LMM_mood_variability")
 - `fixed_effects`: object, required (keys: predictor name, values: {estimate, std_err, p_value, ci_lower, ci_upper})
 - `random_effects`: object, required (keys: variance components)
 - `model_fit`: object, required (keys: aic, bic, log_likelihood)
 - `validation`: object, required (keys: lopo_average_rmse, lopo_sign_consistency_pct)
 - `sensitivity`: object, required (keys: weekdays_only_sign_consistent, active_minutes_sign_consistent, single_rating_bootstrap_consistency, single_rating_bootstrap_pass)
- [X] T006 [P] Create base test utilities in `tests/conftest.py` for schema validation and fixture data
- [X] T007 [P] Implement `code/ingest.py` to download StudentLife dataset from OSF DOI specified in `code/config.py`, verify cryptographic checksum (SHA-256), **and write the resulting hash to `state/projects/PROJ-715-physical-activity-levels-and-mood-variab.yaml` under the key `artifact_hashes.data_raw_bronze_parquet`** to satisfy Constitution Principle III: Data Hygiene.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Download StudentLife dataset, parse raw step logs, align EMA mood timestamps, and compute daily aggregates (`total_steps`, `mean_mood`, `mood_std`) per participant-day.

**Independent Test**: Verify that `data/processed/daily_aggregates.csv` contains one row per participant per day with non-null `total_steps`, `mean_mood`, `mood_std`, and row count matches valid participant-days.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T009 [P] [US1] Contract test for `daily_aggregates.csv` schema in `tests/contract/test_daily_aggregates.py`
- [X] T010 [P] [US1] Unit test for aggregation logic (handling missing ratings, zero steps) in `tests/unit/test_preprocess_aggregation.py` <!-- FAILED: unspecified -->

### Implementation for User Story 1

- [ ] T011 [US1] [P] Implement `code/preprocess.py` function `parse_step_logs()` to load `data/raw/bronze.parquet` and parse raw step logs into daily totals <!-- FAILED: unspecified -->
- [X] T012 [US1] [P] [Depends: T011] Implement `code/preprocess.py` function `derive_covariates()` to derive `sleep_duration` and `baseline_affect` from raw data if missing, using `config.MISSINGNESS_THRESHOLD` to decide between derivation and proceeding without them (per spec Assumptions); ensure derived columns are written to the output CSV
- [X] T013 [US1] [P] [Depends: T011] Implement `code/preprocess.py` function `align_ema_timestamps()` to align EMA mood timestamps and exclude records with missing critical values <!-- FAILED: unspecified -->
- [X] T014 [US1] [Depends: T012, T013] Implement `code/preprocess.py` function `compute_daily_aggregates()` to:
 1. **Filter out days with an insufficient number of valid mood ratings FIRST** (before any variance calculation) to satisfy FR-002 and Constitution Principle VI.
 2. Compute daily aggregates: `mean_mood` and `mood_std` (raw standard deviation).
 3. **Handle days with exactly 0 mood variability** (all ratings identical) by recording `mood_std` as `0.0` (not NaN).
 4. **Log the count of excluded days** (due to <2 ratings) to `data/processed/preprocess_stats.json` with the schema: `{"excluded_days_count": int, "reason": "n_mood_ratings < 2"}`.
 5. Ensure `total_steps` is recorded as 0 for days with zero steps.
- [ ] T015 [US1] [Depends: T014] Write final output to `data/processed/daily_aggregates.csv` and validate against `daily_aggregates.schema.yaml`. **Assert that no NaN/Inf values exist in the `mood_std` column before writing.** <!-- FAILED: unspecified -->

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Modeling and Association Testing (Priority: P2)

**Goal**: Fit linear mixed-effects models to test association between `total_steps` and (a) `mood_std` (log-transformed) and (b) `mean_mood`, controlling for sleep, day-of-week, and baseline affect.

**Independent Test**: Run model fitting script and verify output report contains fixed-effect coefficient for `total_steps` (with p-value and 95% CI) for both models, and model converges successfully.

### Tests for User Story 2

- [X] T017 [P] [US2] Contract test for `model_results.json` schema in `tests/contract/test_model_results.py`
- [X] T018 [P] [US2] Unit test for model convergence and coefficient extraction in `tests/unit/test_analysis_modeling.py` <!-- FAILED: unspecified -->

### Implementation for User Story 2

- [X] T019a [US2] [Depends: T015] Implement `code/analysis.py` function `validate_raw_mood_std()` to load `daily_aggregates.csv` and **verify that the `mood_std` column contains no negative values or NaNs** (ensuring T014 executed correctly). **This task depends on T015 (data production), not T019a (model fitting), to validate input before modeling.**
- [ ] T019b [US2] [P] [Depends: T019a] **Explicitly verify and document** that the raw `mood_std` column in `daily_aggregates.csv` remains unmodified and available for other analyses, ensuring compliance with FR-003's requirement to preserve the raw metric. <!-- FAILED: unspecified -->
- [X] T019c [US2] [P] Implement `code/analysis.py` function `enforce_transform_constraint()` as a **decorator or wrapper** that enforces the global constraint: "No code path may use `mood_std` directly in a log calculation without the epsilon offset of a small magnitude." This function must be **called by** `fit_lmm_variability` and `fit_lmm_mean` to ensure the transformation `np.log(mood_std + 0.01)` is applied correctly.
- [X] T020 [US2] [Depends: T019c] Implement `code/analysis.py` function `fit_lmm_variability()` to fit the primary LMM with `log(mood_std + 0.01)` as the outcome and `total_steps` as the primary predictor (random intercepts for participant), **invoking `enforce_transform_constraint()` to apply the transformation**. <!-- ATOMIZE: requested -->
- [X] T021 [US2] [Depends: T019c] Implement `code/analysis.py` function `fit_lmm_mean()` to fit the secondary LMM with `mean_mood` as the outcome and `total_steps` as the predictor, ensuring the results are included in the final report (hierarchy to be enforced in T032).
- [X] T022 [US2] [Depends: T020, T021] Implement `code/analysis.py` function `extract_model_coefficients()` to extract fixed-effect coefficients, standard errors, p-values, and 95% CIs for `total_steps` and covariates (sleep, day-of-week, baseline_affect) from both models.
- [X] T023 [US2] [Depends: T020, T021] Implement `code/analysis.py` function `run_model_diagnostics()` to perform model diagnostics (Shapiro-Wilk, Breusch-Pagan) and generate residual plots (specifically 'residuals vs. fitted').
- [X] T024a [US2] [P] Implement `code/analysis.py` to ensure all results are explicitly labeled as "associational" in internal data structures.
- [ ] T024b [US2] [P] [Depends: T022, T023, T028b, T030, T031c] **Generate and aggregate** the `model_results.json` artifact by consolidating all fixed effects, random effects, diagnostics, LOPO results, and sensitivity analysis results into a single JSON file. <!-- ATOMIZE: requested -->
- [ ] T025 [US2] [Depends: T024b] Save model results to `data/processed/model_results.json` and validate against `model_results.schema.yaml`. Ensure the file includes all required fields from the schema. <!-- FAILED: unspecified -->

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Validation and Sensitivity Analysis (Priority: P3)

**Goal**: Perform leave-one-participant-out (LOPO) cross-validation and sensitivity analyses (weekdays-only, alternative metrics, single-rating handling) to ensure robustness.

**Independent Test**: Verify final report contains LOPO coefficient consistency (≥90% sign stability), sensitivity check results, and bootstrap consistency for single-rating handling (≥80%).

### Tests for User Story 3

- [X] T026 [P] [US3] Unit test for LOPO loop logic and coefficient aggregation in `tests/unit/test_analysis_validation.py`
- [X] T027 [P] [US3] Unit test for sensitivity analysis logic (weekdays filter, metric swap) in `tests/unit/test_analysis_sensitivity.py`

### Implementation for User Story 3

- [X] T028a [US3] [P] Implement `code/analysis.py` function `run_lopo_cv()` to retrain model N times (N=participants), track `total_steps` coefficient sign stability, and calculate the **average RMSE** across all LOPO folds.
- [X] T028b [US3] [Depends: T028a] Implement `code/analysis.py` logic to calculate the percentage of folds where the `total_steps` coefficient sign matches, flag the result in `model_results.json` if sign consistency <90%, and **continue execution** (do not raise an error) to allow report generation. **Record average RMSE under key `validation.lopo_average_rmse`** in `model_results.json`.
- [X] T029 [US3] [P] Implement `code/analysis.py` function `run_sensitivity_weekdays()` to re-run primary model on "weekdays only" dataset and compare coefficients.
- [X] T030 [US3] [P] Implement `code/analysis.py` function `run_sensitivity_active_minutes()` to re-run model using "active minutes" instead of step counts and compare direction of effect.
- [X] T031a [US3] [Internal Step for T031c] Implement logic to exclude single-rating days from the dataset for the primary sensitivity branch.
- [X] T031b [US3] [Internal Step for T031c] Implement logic to impute single-rating days using the participant's median mood value for the secondary sensitivity branch.
- [X] T031c [US3] [Depends: T031a, T031b, T025] Implement `code/analysis.py` function `run_sensitivity_single_rating_bootstrap()` to execute a **bootstrap sampling loop with exactly 1000 iterations** (seed 42): for each iteration, fit the exclusion model (T031a logic) and the imputation model (T031b logic), **compare the coefficients of the two models within the iteration**, record whether the direction remains consistent, and calculate the final consistency percentage. **Write a boolean `pass` (true if consistency ≥ 80%) and the calculated percentage to `model_results.json` under key `sensitivity.single_rating_bootstrap_consistency` and `sensitivity.single_rating_bootstrap_pass` respectively.** Explicitly report whether the ≥80% threshold is met.
- [X] T032 [US3] [Depends: T025, T028b, T030, T031c] Implement `code/report.py` to generate PDF/HTML report containing effect sizes, CIs, diagnostic plots (including 'residuals vs. fitted' from T023), LOPO results, and sensitivity analysis summaries. **Use `jinja2` for templating and `weasyprint` for PDF generation.** Prioritize the `mood_variability` model results as the primary finding and ensure the `mean_mood` model is presented as secondary. **Explicitly inject the 'associational' disclaimer text required by FR-004 into the report header and conclusion sections.** **Include a validation step that programmatically checks the generated report content for the presence of the 'associational' disclaimer string before saving the file.** Verify that the report contains no causal language. **This task includes the final verification previously assigned to T033.**
- [X] T037 [P] Additional unit tests for edge cases (single participant days, zero mood entries) in `tests/unit/`. **Specifically test: 1) dropping days with zero mood entries, 2) handling single participant days (fixed-effects fallback), 3) zero mood variability calculation.** **These tests must be written, executed, and passing before marking this task complete.**

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T034a-1 [P] Update `README.md` with specific section: Installation (include pip install command `pip install -r code/requirements.txt`)
- [ ] T034a-2 [P] Update `README.md` with specific section: Usage (include CLI example `python code/main.py --input data/processed/daily_aggregates.csv`)
- [ ] T034b [P] Update `docs/` with specific content: API documentation for `analysis.py` and Data Dictionary for `daily_aggregates.csv`
- [X] T036 [P] Run full pipeline integration test in `tests/integration/test_full_pipeline.py` to verify end-to-end execution within 6 hours
- [ ] T038 [P] [Depends: T034a-1, T034a-2] **Create a shell script `scripts/validate_quickstart.sh`** that executes the steps in `quickstart.md` and captures the exit code. **Run this script** and generate a validation log file `docs/quickstart_validation.log` confirming success. This mechanism ensures the documentation is runnable end-to-end.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on data output from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on model output from US2

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for daily_aggregates.csv schema in tests/contract/test_daily_aggregates.py"
Task: "Unit test for aggregation logic in tests/unit/test_preprocess_aggregation.py"

# Launch all models for User Story 1 together:
Task: "Implement code/preprocess.py to load data and parse step logs"
Task: "Implement code/preprocess.py logic to align EMA timestamps"
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
