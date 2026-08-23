# Tasks: Physical Activity Levels and Mood Variability in Daily Life

**Input**: Design documents from `/specs/001-physical-activity-levels-and-mood-variab/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `android/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

<!--
 ============================================================================
 IMPORTANT: The tasks below are SAMPLE TASKS for illustration purposes only.

 The /speckit-tasks command MUST replace these with actual tasks based on:
 - User stories from spec.md (with their priorities P1, P2, P3...)
 - Feature requirements from plan.md
 - Entities from data-model.md
 - Endpoints from contracts/

 Tasks MUST be organized by user story so that:
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
- [ ] T003a Create `.flake8` configuration file in `code/` with `[flake8]` section, `max-line-length = 88`, and `ignore = E203, E266, W503` (Provides code‑style linting for the project)
- [X] T003b [P] Create `pyproject.toml` in `code/` with `[tool.black]` section, `line-length = 88`, and `target-version = ['py']` (Supports **Code Quality Standards**)
- [X] T004 [P] Create configuration module `code/config.py` defining paths, random seeds (`SEED = 42`), constants (including `MISSINGNESS_THRESHOLD` and `BOOTSTRAP_ITERATIONS`), and the specific OSF DOI string for the dataset
- [X] T005a [P] Create schema definition `daily_aggregates.schema.yaml` in `specs/001-physical-activity-levels-and-mood-variab/contracts/` with the following structure:
 - `participant_id`: string, required
 - `date`: date, required
 - `total_steps`: integer, required, min=0
 - `mean_mood`: float, required
 - `mood_std`: float, required, min=0 (raw standard deviation, NO transformation applied here)
 - `n_mood_ratings`: integer, required, min=2
 - `sleep_duration`: float, nullable
 - `baseline_affect`: float, nullable
 - `day_of_week`: integer, required (0=Monday)
- [X] T005b [P] Create schema definition `model_results.schema.yaml` in `specs/001-physical-activity-levels-and-mood-variab/contracts/` with the following structure:
 - `model_type`: string, required (e.g., "LMM_mood_variability")
 - `fixed_effects`: object, required (keys: predictor name, values: {estimate, std_err, p_value, ci_lower, ci_upper})
 - `random_effects`: object, required (keys: variance components)
 - `model_fit`: object, required (keys: aic, bic, log_likelihood)
 - `validation`: object, required (keys: lopo_average_rmse, lopo_sign_consistency_pct)
 - `sensitivity`: object, required (keys: weekdays_only_sign_consistent, weekdays_only_pvalue_consistent, active_minutes_sign_consistent, single_rating_bootstrap_consistency, single_rating_bootstrap_pass)
- [X] T005c [P] Create schema definition `preprocess_stats.schema.yaml` in `specs/001-physical-activity-levels-and-mood-variab/contracts/` with the following structure:
 - `excluded_days_count`: integer, required
 - `reason`: string, required (e.g., "n_mood_ratings < 2")
- [X] T006 [P] Create base test utilities in `tests/conftest.py` for schema validation and fixture data
- [X] T007 [P] Create `code/ingest.py` to download StudentLife dataset from OSF DOI specified in `code/config.py`. **Critical Integrity Steps**: 1) Compute a cryptographic SHA‑256 checksum immediately upon download completion (before any write). 2) Convert the downloaded zip to `data/raw/bronze.parquet`. 3) Atomically update `state/projects/PROJ-715-physical-activity-levels-and-mood-variab.yaml` under the exact key `artifact_hashes: { data_raw_bronze: "<sha256_hex_string>" }`. This ensures Constitution Principle III (Data Hygiene) compliance and defines the exact output filename for downstream tasks.
- **Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Download StudentLife dataset, parse raw step logs, align EMA mood timestamps, and compute daily aggregates (`total_steps`, `mean_mood`, `mood_std`) per participant‑day.

**Independent Test**: Verify that `data/processed/daily_aggregates.csv` contains one row per participant per day with non‑null `total_steps`, `mean_mood`, `mood_std`, and row count matches valid participant‑days.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T009 [P] [US1] Contract test for `daily_aggregates.csv` schema in `tests/contract/test_daily_aggregates.py`
- [X] T010 [P] [US1] Unit test for aggregation logic (handling missing ratings, zero steps) in `tests/unit/test_preprocess_aggregation.py` with specific test function `test_aggregate_handles_zero_steps` asserting that days with zero steps are recorded as 0 and not dropped.

### Implementation for User Story 1

- [ ] T011 [US1] [Depends: T007] Implement `code/preprocess.py` function `parse_step_logs()` to load `data/raw/bronze.parquet` (produced by T007) and parse raw step logs into daily totals. **Input columns**: `participant_id`, `timestamp`, `step_count`. **Output**: DataFrame with `participant_id`, `date`, `total_steps`. Handle missing `step_count` by treating as 0.
- [X] T012 [US1] [Depends: T011] Implement `code/preprocess.py` function `derive_covariates()` to derive `sleep_duration` and `baseline_affect` from raw data if missing, using `config.MISSINGNESS_THRESHOLD` to decide between derivation and proceeding without them (per spec Assumptions); ensure derived columns are written to the output CSV.
- [X] T013 [US1] [Depends: T011] Implement `code/preprocess.py` function `align_ema_timestamps()` to align EMA mood timestamps and exclude records with missing critical values. **Logic**: Join step logs and EMA data on `participant_id` and `date`. **Exclusion**: Drop any EMA entry where `mood` is null. **Tolerance**: Align timestamps within 24 h window.
- [X] T014 [US1] [Depends: T012, T013] Implement `code/preprocess.py` function `compute_daily_aggregates()` to:
 1. **Filter out days with 0 mood ratings FIRST** (drop entirely to avoid division-by-zero).
 2. **Then filter out days with fewer than 2 valid mood ratings** (to satisfy FR‑002 and Constitution Principle VI).
 3. Compute daily aggregates: `mean_mood` and **raw** `mood_std` (standard deviation, recording `0.0` for days with identical ratings). **Do NOT** apply log‑transformation here.
 4. **Log the count of excluded days** to `data/processed/preprocess_stats.json` with the schema defined in `preprocess_stats.schema.yaml`: `{"excluded_days_count": int, "reason": "n_mood_ratings < 2 or count == 0"}`.
 5. Ensure `total_steps` is recorded as 0 for days with zero steps.
- [ ] T015 [US1] [Depends: T014] Write the final output to `data/processed/daily_aggregates.csv` and validate against `daily_aggregates.schema.yaml`. **Assert** that no NaN/Inf values exist in the `mood_std` column before writing using `assert not df['mood_std'].isna().any()`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Modeling and Association Testing (Priority: P2)

**Goal**: Fit linear mixed‑effects models to test association between `total_steps` and (a) `mood_std` (log‑transformed) and (b) `mean_mood`, controlling for sleep, day‑of‑week, and baseline affect.

**Independent Test**: Run model fitting script and verify output report contains fixed‑effect coefficient for `total_steps` (with p‑value and 95 % CI) for both models, and model converges successfully.

### Tests for User Story 2

- [X] T017 [P] [US2] Contract test for `model_results.json` schema in `tests/contract/test_model_results.py`
- [X] T018 [P] [US2] Unit test for model convergence and coefficient extraction in `tests/unit/test_analysis_modeling.py` with specific test function `test_model_convergence_flag` asserting `model.converged == True`.

### Implementation for User Story 2

- [X] T019a [US2] Implement `code/analysis.py` function `validate_raw_mood_std()` to load `daily_aggregates.csv` and **verify that the `mood_std` column contains no negative values or NaNs**. **Depends:** T015.
- [X] T019c [US2] Implement `code/analysis.py` function `apply_log_transform(mood_std: np.ndarray) -> np.ndarray` that returns `np.log(mood_std + epsilon)`. **This is the SINGLE authorized mechanism** for the log transformation used by all models.
- [X] T020a [US2] [Depends: T019c] Implement `code/analysis.py` function `fit_lmm_variability()` to fit the primary LMM with `apply_log_transform(mood_std)` as the outcome and `total_steps` as the primary predictor (random intercepts for participant).
- [X] T020b [US2] [Depends: T019c] Implement `code/analysis.py` function `fit_lmm_mean()` to fit the secondary LMM with `mean_mood` as the outcome and `total_steps` as the predictor.
- [X] T022 [US2] [Depends: T020a, T020b] Implement `code/analysis.py` function `extract_model_coefficients()` to extract fixed‑effect coefficients, standard errors, p‑values, and 95 % CIs for `total_steps` and covariates (sleep, day‑of‑week, baseline_affect) from both models.
- [X] T023 [US2] [Depends: T020a, T020b] Implement `code/analysis.py` function `run_model_diagnostics()` to perform model diagnostics (Shapiro‑Wilk, Breusch‑Pagan) and generate residual plots (specifically "residuals vs. fitted").
- [X] T024a [US2] [P] Implement `code/analysis.py` to ensure all results are explicitly labeled as "associational" in internal data structures.
- [ ] T024b [US2] [Depends: T020a, T020b, T022, T023] Compute and return a dictionary containing **all** base model results (fixed effects, random effects, diagnostics) matching `model_results.schema.yaml`. **No file is written here**; results are kept in memory for later merging.
- [X] T025 [US2] [Depends: T024b] Verify that the base model results dictionary is valid and conforms to the partial `model_results.schema.yaml` (excluding sensitivity/validation sections).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (base models ready, but full results pending US3)

---

## Phase 5: User Story 3 - Validation and Sensitivity Analysis (Priority: P3)

**Goal**: Perform leave‑one‑participant‑out (LOPO) cross‑validation and sensitivity analyses (weekdays‑only, alternative metrics, single‑rating handling) to ensure robustness.

**Independent Test**: Verify final report contains LOPO coefficient consistency (≥ 90 % sign stability), sensitivity check results, and bootstrap consistency for single‑rating handling (≥ 80 %).

### Tests for User Story 3

- [X] T026 [P] [US3] Unit test for LOPO loop logic and coefficient aggregation in `tests/unit/test_analysis_validation.py`
- [X] T027 [P] [US3] Unit test for sensitivity analysis logic (weekdays filter, metric swap) in `tests/unit/test_analysis_sensitivity.py`

### Implementation for User Story 3

- [X] T028a [US3] Implement `code/analysis.py` function `run_lopo_cv()` to retrain the primary model N times (N = number of participants), track `total_steps` coefficient sign stability, and calculate the **average RMSE** across all LOPO folds.
- [X] T028b [US3] [Depends: T024b] Compute the percentage of folds where the `total_steps` coefficient sign matches the full‑data sign; **if sign consistency < 90 %** flag the result (but do **not** raise an error). Return both the average RMSE and the sign‑consistency percentage for consumption by T024c.
- [X] T029 [US3] [Depends: T024b] Implement `code/analysis.py` function `run_sensitivity_weekdays()` to re‑run the primary model on "weekdays only" data and compare coefficients. **Result**: Return a dictionary containing the `total_steps` coefficient, p-value, and boolean flags for `sign_consistent` and `pvalue_consistent` (p < 0.05 status matches primary model) for merging.
- [X] T030 [US3] [Depends: T024b] Implement `code/analysis.py` function `run_sensitivity_active_minutes()` to re‑run the model using "active minutes" instead of step counts and compare direction of effect. Return a result dictionary for merging.
- [X] T031a [US3] Implement logic to exclude single‑rating days from the dataset for the primary sensitivity branch.
- [X] T031b [US3] Implement logic to impute single‑rating days using the participant's median mood value for the secondary sensitivity branch.
- [X] T031c [US3] [Depends: T024b] Implement `code/analysis.py` function `run_sensitivity_single_rating_bootstrap()` to execute a **bootstrap sampling loop** with `config.BOOTSTRAP_ITERATIONS` iterations, utilizing a sufficiently large default to ensure robust estimation of sampling variability.. For each iteration:
   1. Set `np.random.seed(config.SEED)` (seed 42 defined in T004).
   2. Fit the exclusion model (using T031a logic) and the imputation model (using T031b logic).
   3. Compare the sign of the `total_steps` coefficient from both models (`np.sign(coef_excl) == np.sign(coef_imp)`).
   4. Record whether the direction remains consistent.
 After the loop, calculate the **consistency percentage**. **Calculate a boolean `pass` flag** (True if percentage >= 80%, False otherwise). **Do NOT assert or fail the build** if the percentage is < 80%; simply return the percentage and the `pass` flag for merging into the final results. Return both the percentage and the `pass` flag for merging.
- [X] T024c [US2/US3 Merge] [Depends: T024b, T028b, T030, T031c, T005b] **Moved to Phase 5** to resolve dependency order. Merge base results from T024b with LOPO (T028b), active minutes (T030), and bootstrap (T031c) outputs into a **single complete dictionary** matching `model_results.schema.yaml`. Perform an **atomic write** to `data/processed/model_results.json`. Prior to merging, **verify that `model_results.schema.yaml` exists** (produced by T005b) and that the target file does not already exist or is overwritten safely. After writing, validate the JSON against the schema.
- [X] T025 [US2] [Depends: T024c] Verify that `data/processed/model_results.json` exists, is valid JSON, and conforms to the contract test `tests/contract/test_model_results.py`.
- [X] T032 [US3] [Depends: T024c] Implement `code/report.py` to generate PDF/HTML report containing effect sizes, CIs, diagnostic plots (including residuals vs. fitted from T023), LOPO results, and sensitivity analysis summaries. **Constraint**: Must wait for T024c to complete the final `model_results.json`. Use `jinja2` for templating and `weasyprint` for PDF generation. **Inject** the required "associational" disclaimer text into header and conclusion. **Verification**: Programmatically check that the generated report contains the disclaimer string and no causal language before saving.

**Checkpoint**: All user stories should now be independently functional, with US3 completing the full analysis pipeline

---

## Phase N: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T034a-1 [P] Update `README.md` with specific section: Installation (include pip install command `pip install -r code/requirements.txt`)
- [ ] T034a-2 [P] Update `README.md` with specific section: Usage (include CLI example `python code/main.py --input data/processed/daily_aggregates.csv`). **Verification**: Run the command `python code/main.py --input data/processed/daily_aggregates.csv` and assert exit code == 0.
- [ ] T034b [P] Update `specs/001-physical-activity-levels-and-mood-variab/` (aligned with plan.md Project Structure) with specific content: API documentation for `analysis.py` and Data Dictionary for `daily_aggregates.csv`. **Note**: If a root‑level `docs/` directory exists from previous revisions, remove or deprecate it to prevent path conflicts.
- [X] T036 [P] Run full pipeline integration test in `tests/integration/test_full_pipeline.py` to verify end‑to‑end execution within 6 hours
- [X] T038 [P] Create a shell script `scripts/validate_quickstart.sh` with the following exact content:
```bash
#!/usr/bin/env bash
set -euo pipefail
# Install dependencies
pip install -r code/requirements.txt
# Execute quickstart command
python code/main.py --input data/processed/daily_aggregates.csv
# Verify success
if [ $? -ne 0 ]; then
  echo "Quickstart validation failed"
  exit 1
fi
echo "Quickstart validation successful"
# Write validation log
echo "$(date --iso-8601=seconds) QUICKSTART SUCCESS" > docs/quickstart_validation.log
```
**Verification**: Execute the script and assert exit code 0; also assert that `docs/quickstart_validation.log` exists and contains the success string.

- [X] T036 [P] Run full pipeline integration test in `tests/integration/test_full_pipeline.py` to verify end‑to‑end execution within 6 hours
- [X] T038 [P] (as above) ensures documentation is runnable end‑to‑end.