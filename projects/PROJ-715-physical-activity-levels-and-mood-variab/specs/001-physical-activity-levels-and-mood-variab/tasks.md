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

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. This phase includes mandatory edge-case handling to prevent downstream failures and robust modeling utilities.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002 Initialize Python project with dependencies (`pandas`, `statsmodels`, `scikit-learn`, `pyyaml`, `requests`, `numpy`) in `code/requirements.txt`
- [X] T003b [P] Create `pyproject.toml` in `code/` with `[tool.black]` section, `line-length = 88`, and `target-version = ['py3']` (Supports **Code Quality Standards**)
- [ ] T004 [P] Create configuration module `code/config.py` defining paths, random seeds (`SEED = 42`), constants (including `MISSINGNESS_THRESHOLD`, `BOOTSTRAP_ITERATIONS = 1000`, `CHUNK_SIZE = 100000`), and the specific OSF DOI string for the dataset
- [X] T005a [P] Create schema definition `daily_aggregates.schema.yaml` in `specs/001-physical-activity-levels-and-mood-variab/contracts/` with the following structure:
 - `participant_id`: string, required
 - `date`: date, required
 - `total_steps`: integer, required, min=0
 - `mean_mood`: float, required
 - `mood_std`: float, required, min=0 (raw standard deviation, NO transformation applied here)
 - `n_mood_ratings`: integer, required, min=1 (Updated to allow single-rating days for sensitivity analysis)
 - `sleep_duration`: float, nullable
 - `baseline_affect`: float, nullable
 - `day_of_week`: integer, required (0=Monday)
- [X] T005b [P] Create schema definition `model_results.schema.yaml` in `specs/001-physical-activity-levels-and-mood-variab/contracts/` with the following structure:
 - `model_type`: string, required (e.g., "LMM_mood_variability")
 - `fixed_effects`: object, required (keys: predictor name, values: {estimate, std_err, p_value, ci_lower, ci_upper})
 - `random_effects`: object, required (keys: variance components)
 - `model_fit`: object, required (keys: aic, bic, log_likelihood)
 - `diagnostic_tests`: object, required (keys: shapiro_wilk_p_value, breusch_pagan_p_value)
 - `convergence_diagnosis`: object, required (keys: status, reason, fallback_model_type)
 - `validation`: object, required (keys: lopo_average_rmse, lopo_sign_consistency_pct)
 - `sensitivity`: object, required (keys: weekdays_only_sign_consistent, weekdays_only_pvalue, weekdays_only_pvalue_consistent, active_minutes_sign_consistent, single_rating_bootstrap_consistency, single_rating_bootstrap_pass)
- [ ] T005c [P] Create schema definition `preprocess_stats.schema.yaml` in `specs/001-physical-activity-levels-and-mood-variab/contracts/` with the following structure:
```yaml
type: object
properties:
  excluded_days_count:
    type: integer
    description: Number of days excluded due to n_mood_ratings < 2
  reason:
    type: string
    description: Reason for exclusion (e.g., "n_mood_ratings < 2")
  data_source_url:
    type: string
    description: URL of the source dataset (OSF or HF)
required:
  - excluded_days_count
  - reason
  - data_source_url
additionalProperties: false
```
 **Action**: Validate the generated JSON against this schema before writing to ensure FR-002 compliance.
- [X] T006 [P] Create base test utilities in `tests/conftest.py` for schema validation and fixture data
- [ ] T007 [P] [US1] **Implement Robust Dataset Download and State Update**: Create `code/ingest.py` to download StudentLife dataset from OSF DOI specified in `code/config.py`. **Critical Integrity Steps**:
 1. Download the zip file to a temporary location.
 2. Compute a cryptographic SHA‑256 checksum of the downloaded file.
 3. Convert the downloaded zip to `data/raw/bronze.parquet`.
 4. Implement a helper function `update_state_artifact_hash(state_path, key, value)` that reads `state/projects/PROJ-715-physical-activity-levels-and-mood-variab.yaml`, updates the `artifact_hashes` dict with `key: value`, and writes it back atomically.
 5. Call `update_state_artifact_hash` to record the checksum under `data_raw_bronze`.
 6. If OSF download fails or checksum is invalid, raise a `RuntimeError` with a clear message. **Do NOT** fallback to synthetic data or a guessed hash for a mirror.
 **Output**: `data/raw/bronze.parquet` and updated state file.
- [ ] T052 [US1] [Depends: T007] **Fail Loudly on Corruption**: Modify `code/ingest.py` to remove any `try/except` blocks that might silently fallback to synthetic data generation. **Action**: If the OSF download fails or the file is corrupted (checksum mismatch), the script must raise a `RuntimeError` with a clear message listing the missing files or network error, ensuring the pipeline fails loudly rather than fabricating data.
- [ ] T051 [US1] [Depends: T007] **Corrupted Data Check**: Implement a validation step in `code/ingest.py` or a new `code/validate_raw.py` to verify the integrity of `data/raw/bronze.parquet` against the recorded checksum. If the file is missing or corrupted, raise a `RuntimeError` with a clear message. This ensures FR-001 compliance.
- [ ] T064 [US1] [P] **Log Source Fidelity**: Create `code/preprocess.py` function `init_preprocess_stats()` that writes the initial `data/processed/preprocess_stats.json` file containing the `data_source_url` (OSF URL used) and initializes `excluded_days_count` to 0. **Action**: This task MUST run before T014b to ensure the source URL is recorded in the stats file before any exclusion counts are added. **Output**: Writes `data/processed/preprocess_stats.json` with `{"data_source_url": "<url>", "excluded_days_count": 0, "reason": "initial"}`. **Constraint**: This file is the single source of truth for data provenance. **Verification**: Explicitly verify the file is written and non-empty before returning.
- [ ] T074 [P] **Implement Robust Convergence Handling**: Create `code/analysis.py` function `fit_lmm_robust()` which attempts to fit a Linear Mixed-Effects Model. If the model fails to converge after max iterations, it MUST attempt a fallback to a Fixed-Effects GLS model (`statsmodels.GLS`) with the same predictors but without random effects, logging a warning. **Constraint**: The fallback model MUST be explicitly labeled as "GLS_Fallback" in the results to distinguish it from the primary LMM. **CRITICAL**: If the fallback is used, the function MUST set `convergence_diagnosis.status` to "non-significant" and `convergence_diagnosis.reason` to "Model failed to converge; GLS fallback used" to satisfy FR-003. This task is moved to Phase 2 to ensure the modeling logic is robust during the primary fitting phase and available to all US2/US3 tasks.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Download StudentLife dataset, parse raw step logs, align EMA mood timestamps, and compute daily aggregates (`total_steps`, `mean_mood`, `mood_std`) per participant‑day.

**Independent Test**: Verify that `data/processed/daily_aggregates.csv` contains one row per participant per day with non‑null `total_steps`, `mean_mood`, `mood_std`, and row count matches valid participant‑days.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T009 [P] [US1] Contract test for `daily_aggregates.csv` schema in `tests/contract/test_daily_aggregates.py`
- [ ] T010 [P] [US1] Unit test for aggregation logic (handling missing ratings, zero steps) in `tests/unit/test_preprocess_aggregation.py` with specific test function `test_aggregate_handles_zero_steps` asserting that days with no recorded steps are retained rather than dropped.

### Implementation for User Story 1

- [ ] T011 [US1] [Depends: T007] Implement `code/preprocess.py` function `parse_step_logs()` to load `data/raw/bronze.parquet` (produced and verified by T007) and parse raw step logs into daily totals. **Input columns**: `participant_id`, `timestamp`, `step_count`. **Output**: DataFrame with `participant_id`, `date`, `total_steps`. Handle missing `step_count` by treating as 0.
- [ ] T012 [US1] [Depends: T011] **Derive Covariates**: Implement `code/preprocess.py` function `derive_covariates()` to derive `sleep_duration` and `baseline_affect` from raw data if missing, using `config.MISSINGNESS_THRESHOLD` to decide between derivation and proceeding without them (per spec Assumptions); ensure derived columns are written to the output CSV. **Dependency Note**: This task explicitly depends on T011 for the parsed step logs.
- [ ] T013 [US1] [Depends: T011] Implement `code/preprocess.py` function `align_ema_timestamps()` to align EMA mood timestamps and exclude records with missing critical values. **Logic**: Join step logs and EMA data on `participant_id` and `date`. **Exclusion**: Drop any EMA entry where `mood` is null. **Tolerance**: Align timestamps within 24 h window.
- [ ] T014a [US1] [Depends: T011, T012, T013] **Compute Daily Aggregates**: Implement `code/preprocess.py` function `compute_daily_aggregates()` to:
 1. **Filter out days with 0 mood ratings FIRST** (drop entirely to avoid division-by-zero).
 2. **Compute daily aggregates**: `mean_mood` and **raw** `mood_std` (standard deviation, recording `0.0` for days with identical ratings). **Do NOT** apply log‑transformation here.
 3. **Retain** days with `n_mood_ratings == 1` in the output DataFrame (do NOT filter them out yet).
 4. **Count Exclusions**: Calculate and return the count of days excluded due to having < 2 valid mood ratings (to be used by T014b).
 5. **Return** the aggregated DataFrame (raw) and the exclusion count.
 6. Ensure `total_steps` is recorded as 0 for days with zero steps.
 **Constraint**: This task returns the **raw** dataset including single-rating days for downstream sensitivity analysis. **Note**: This task does NOT depend on T064; it operates purely on data.
- [ ] T014b [US1] [Depends: T014a, T005c, T064] **Validate and Write Preprocess Stats**: Implement `code/preprocess.py` function `write_preprocess_stats()` to update `data/processed/preprocess_stats.json` (created by T064) with the `excluded_days_count` and `reason`. **Action**: **Consume** the exclusion count returned by T014a (specifically for the FR-002 filter) to populate the stats file. **Validate** the output JSON against `preprocess_stats.schema.yaml` (defined in T005c) BEFORE writing to disk. **Constraint**: If validation fails, raise `RuntimeError`. **Output**: Writes `data/processed/preprocess_stats.json` with `{"excluded_days_count": int, "reason": "n_mood_ratings < 2", "data_source_url": "<url>"}`. **Note**: Depends on T064 for the initial file write and T014a for the data counts.
- [ ] T014c [US1] [Depends: T014a] **Write Raw Aggregates**: Implement `code/preprocess.py` function `write_raw_daily_aggregates()` to write the **unfiltered** dataset (including single-rating days) to `data/processed/raw_daily_aggregates.csv`. **Action**: **Validate** the output against `daily_aggregates.schema.yaml` (which now allows `n_mood_ratings >= 1`). **Constraint**: This file is the input for T031a (Sensitivity Analysis).
- [ ] T050a [US1] [Depends: T014a] **Handle Sparse Participants**: Implement `code/preprocess.py` function `handle_sparse_participants()` to identify participants with < 3 valid days. **Action**: Log a warning and **exclude** these participants from the dataset returned to downstream tasks (T020a) to prevent LMM convergence failures, as per Edge Case "Participant has data for only 1 or 2 days". **Output**: Returns a filtered dataset and a list of excluded participant IDs. **Constraint**: This must run AFTER T014a (compute_daily_aggregates) because it requires the 'valid days' metric.
- [ ] T015 [US1] [Depends: T014a] **Write Final Aggregates**: Implement `code/preprocess.py` function `write_daily_aggregates()` to write the **filtered** dataset (excluding days with n_mood_ratings < 2 and sparse participants) to `data/processed/daily_aggregates.csv`. **Action**: **Validate** the output against `daily_aggregates.schema.yaml`. **Assert** that no NaN/Inf values exist in the `mood_std` column before writing using `assert (df['mood_std'] >= 0).all() and np.isfinite(df['mood_std']).all()`. **Constraint**: This task writes the final, filtered dataset used by all downstream analysis tasks (US2).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Modeling and Association Testing (Priority: P2)

**Goal**: Fit linear mixed‑effects models to test association between `total_steps` and (a) `mood_std` (log‑transformed) and (b) `mean_mood`, controlling for sleep, day‑of‑week, and baseline affect.

**Independent Test**: Run model fitting script and verify output report contains fixed‑effect coefficient for `total_steps` (with p‑value and 95 % CI) for both models, and model converges successfully.

### Tests for User Story 2

- [ ] T017 [P] [US2] Contract test for `model_results.json` schema in `tests/contract/test_model_results.py`
- [ ] T018 [P] [US2] Unit test for model convergence and coefficient extraction in `tests/unit/test_analysis_modeling.py` with specific test function `test_model_convergence_flag` asserting `model.converged == True`.

### Implementation for User Story 2

- [ ] T019a [US2] [Depends: T015] Implement `code/analysis.py` function `validate_raw_mood_std()` to load `daily_aggregates.csv` and **verify that the `mood_std` column contains no negative values or NaNs**.
- [ ] T019c [US2] [Depends: T019a] Implement `code/analysis.py` function `apply_log_transform(mood_std: np.ndarray) -> np.ndarray` that returns `np.log(mood_std + epsilon)`. **This is the SINGLE authorized mechanism** for the log transformation used by all models.
- [ ] T020a [US2] [Depends: T019c, T050a, T074] Implement `code/analysis.py` function `fit_lmm_variability()` to fit the primary LMM with `apply_log_transform(mood_std)` as the outcome and `total_steps` as the primary predictor (random intercepts for participant). **Action**: Use `fit_lmm_robust()` (T074) to handle convergence failures. **Note**: T050a ensures sparse participants are excluded before this step.
- [ ] T020b [US2] [Depends: T019c, T050a, T074] Implement `code/analysis.py` function `fit_lmm_mean()` to fit the secondary LMM with `mean_mood` as the outcome and `total_steps` as the predictor. **Action**: Use `fit_lmm_robust()` (T074) to handle convergence failures.
- [ ] T022 [US2] [Depends: T020a, T020b] Implement `code/analysis.py` function `extract_model_coefficients()` to extract fixed‑effect coefficients, standard errors, p‑values, and 95 % CIs for `total_steps` and covariates (sleep, day-of-week, baseline_affect) from both models.
- [ ] T023 [US2] [Depends: T020a, T020b] Implement `code/analysis.py` function `run_model_diagnostics()` to perform model diagnostics (Shapiro‑Wilk, Breusch‑Pagan) and generate residual plots (specifically "residuals vs. fitted"). **Action**: **Write the statistical test results (p-values)** to `data/processed/diagnostics_temp.json` under the key `diagnostic_tests` with structure `{"shapiro_wilk_p_value": float, "breusch_pagan_p_value": float}`. **Return**: A dictionary containing these values for T041 to merge. **Constraint**: Ensure these values are persisted in the final artifact for SC-004 compliance.
- [ ] T024a [US2] [P] Implement `code/analysis.py` to ensure all results are explicitly labeled as "associational" in internal data structures.
- [X] T025 [US2] [Depends: T020a, T020b, T022] **Compute the base model results** dictionary. **Action**: Combine coefficients from T022 and model fit statistics. **Return**: A dictionary containing `fixed_effects`, `random_effects`, `model_fit`, `associational_label`, and `diagnostic_tests` (loaded from T023's temp file). **Do NOT write to disk yet**; this data will be merged by T041. This task replaces the previous "partial write" pattern by ensuring the base model is computed and returned as a complete object for merging.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (base models ready, but full results pending US3)

---

## Phase 5: User Story 3 - Validation and Sensitivity Analysis (Priority: P3)

**Goal**: Perform leave‑one‑participant‑out (LOPO) cross-validation and sensitivity analyses (weekdays‑only, alternative metrics, single‑rating handling) to ensure robustness.

**Independent Test**: Verify final report contains LOPO coefficient consistency (≥ 90% sign stability), sensitivity check results, and bootstrap consistency for single‑rating handling (≥ 80%).

### Tests for User Story 3

- [ ] T026 [P] [US3] Unit test for LOPO loop logic and coefficient aggregation in `tests/unit/test_analysis_validation.py` with specific test function `test_lopo_sign_consistency` asserting `sign_consistency >= 0.90`.
- [ ] T027 [P] [US3] Unit test for sensitivity analysis logic (weekdays filter, metric swap) in `tests/unit/test_analysis_sensitivity.py` with specific test function `test_sensitivity_weekdays_sign_consistent`.

### Implementation for User Story 3

- [ ] T028a [US3] [Depends: T025] Implement `code/analysis.py` function `run_lopo_cv()` to retrain the primary model N times (N = number of participants), track `total_steps` coefficient sign stability, and calculate the **average RMSE** across all LOPO folds. **Return**: A dictionary `{"average_rmse": float, "sign_consistency_pct": float, "coefficients": list}`.
- [ ] T028b [US3] [Depends: T025, T028a] Compute the percentage of folds where the `total_steps` coefficient sign matches the full‑data sign. **Action**: Return a dictionary containing `sign_consistency_pct` (float), `average_rmse` (float), and a boolean `pass` flag (True if consistency >= 90%, False otherwise). **Do NOT raise RuntimeError**. This ensures the pipeline completes and reports the metric as required by FR-005. **Return**: The exact metrics for consumption by T041.
- [ ] T029 [US3] [Depends: T025] Implement `code/analysis.py` function `run_sensitivity_weekdays()` to re‑run the primary model on "weekdays only" data and compare coefficients. **Result**: Return a dictionary containing the `total_steps` coefficient, the **actual p-value** (float), and boolean flags for `sign_consistent` and `pvalue_consistent` (p < 0.05 status matches primary model) for merging.
- [ ] T030 [US3] [Depends: T025] Implement `code/analysis.py` function `run_sensitivity_active_minutes()` to re‑run the model using "active minutes" instead of step counts and compare direction of effect. Return a result dictionary for merging.
- [ ] T031a [US3] [Depends: T014c] **Prepare Single-Rating Dataset**: Implement `code/analysis.py` function `prepare_single_rating_dataset()` that loads `data/processed/raw_daily_aggregates.csv` and filters to **include ONLY** days where `n_mood_ratings == 1`. **Output**: Returns a filtered DataFrame.
- [ ] T031b [US3] [Depends: T014c] **Prepare Imputation Logic**: Implement `code/analysis.py` function `impute_single_ratings()` that takes the dataset from T031a, imputes the missing mood rating using the participant's median mood value, and recalculates `mean_mood` and `mood_std` for these days. **Output**: Returns a DataFrame with imputed values.
- [ ] T031c [US3] [Depends: T014c, T031a, T031b, T025] **Implement Bootstrap Loop**: Implement `code/analysis.py` function `run_bootstrap_loop()` that executes a **bootstrap sampling loop** with `config.BOOTSTRAP_ITERATIONS` (1000) iterations. For each iteration `i`:
 1. Set `np.random.seed(42 + i)` (seed 42 defined in T004, incremented by iteration).
 2. **Derive the 'Exclusion Dataset'**: Filter the full dataset to exclude days where `n_mood_ratings == 1`.
 3. **Derive the 'Imputation Dataset'**: Start with the full dataset, impute missing ratings for days where `n_mood_ratings == 1` using T031b logic.
 4. **Resample the 'Exclusion Dataset'** with replacement to create the bootstrap sample for the **Exclusion Model**.
 5. **Resample the 'Imputation Dataset'** with replacement to create the bootstrap sample for the **Imputation Model**.
 6. Fit the **Exclusion Model** on the exclusion bootstrap sample and the **Imputation Model** on the imputation bootstrap sample.
 7. Compare the sign of the `total_steps` coefficient from both models (`np.sign(coef_excl) == np.sign(coef_imp)`).
 8. Record whether the direction remains consistent.
 **Return**: A list of booleans indicating consistency for each iteration.
- [ ] T031d [US3] [Depends: T031c] **Calculate Bootstrap Metrics**: Implement `code/analysis.py` function `calculate_bootstrap_metrics()` that takes the list of booleans from T031c. **Action**: Calculate the **consistency percentage**. **Calculate a boolean `pass` flag** (True if percentage >= 80%, False otherwise). **Return**: A dictionary containing `consistency_percentage` (float), `pass` (bool), and `bootstrap_samples` (list of booleans). **Action**: This result MUST be merged into `model_results.json` by T041 to satisfy FR-008 reporting requirements.

**Checkpoint**: All user stories should now be independently functional, with US3 completing the full analysis pipeline

---

## Phase 6: Result Merging & Reporting

**Purpose**: Merge all results into the final artifact and generate the report

- [ ] T041 [US2/US3 Merge] [Depends: T025, T028b, T029, T030, T031d, T023] **Write the final `model_results.json`**. **Action**: Load base results from T025. Update the `validation` section with LOPO results from T028b. Update the `sensitivity` section with results from T029, T030, and T031d. Update the `diagnostic_tests` section with results from T023 (loaded from `data/processed/diagnostics_temp.json`). Update the `convergence_diagnosis` section with the status from T074/T077. **Specifically verify** that if `convergence_diagnosis.status` is "non-significant" (from T074), the `sensitivity` or `model_fit` sections reflect this non-significance. **Validate** the final dictionary against `model_results.schema.yaml`. **Specifically verify** that `sensitivity.single_rating_bootstrap_pass` is present and valid. **Write** the complete JSON to `data/processed/model_results.json`. **Constraint**: This task is the **sole writer** of the final `model_results.json` to prevent race conditions or overwrites. **Input Schema Expectations**: T025 provides `fixed_effects`, `random_effects`, `model_fit`, `associational_label`; T028b provides `average_rmse`, `sign_consistency_pct`; T029/T030/T031d provide their respective dictionaries; T023 provides `shapiro_wilk_p_value`, `breusch_pagan_p_value`.

**Checkpoint**: All user stories should now be independently functional, with US3 completing the full analysis pipeline

---

## Phase 7: Entry Point & CLI

**Purpose**: Create the executable entry point for the pipeline

- [ ] T040 [P] Create `code/main.py` as the CLI entry point. **Logic**: Import and orchestrate `ingest.py`, `preprocess.py`, `analysis.py`, and `report.py` in sequence. Parse `--input` argument (optional, defaults to `data/processed/daily_aggregates.csv`). **Output**: Returns exit code 0 on success, non-zero on failure. **Dependency**: Required for T034a-2.

---

## Phase 8: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T034a-1 [P] Update `README.md` with specific section: Installation (include pip install command `pip install -r code/requirements.txt`)
- [ ] T034a-2 [P] Update `README.md` with specific section: Usage (include CLI example `python code/main.py --input data/processed/daily_aggregates.csv`). **Verification**: Run the command `python code/main.py --input data/processed/daily_aggregates.csv` and assert exit code == 0. **Dependency**: T040.
- [ ] T034b [P] Update `specs/001-physical-activity-levels-and-mood-variab/` (aligned with plan.md Project Structure) with specific content: API documentation for `analysis.py` and Data Dictionary for `daily_aggregates.csv`. **Note**: If a root‑level `docs/` directory exists from previous revisions, remove or deprecate it to prevent path conflicts.
- [X] T036 [P] Run full pipeline integration test in `tests/integration/test_full_pipeline.py` to verify end‑to‑end execution within 6 hours
- [ ] T038 [P] Create a shell script `scripts/validate_quickstart.sh` with the following exact content:
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

---

## Phase 9: Report Generation & Final Validation

**Purpose**: Generate the final human-readable report and perform final validation checks

- [ ] T066 [US2/US3] [Depends: T023] **Generate Diagnostic Plots**: Ensure `code/report.py` generates and embeds the residual diagnostic plots (Shapiro-Wilk QQ-plot, Breusch-Pagan residual plot) directly into the report. **Action**: Save plots to `data/processed/plots/` (e.g., `residuals_qq.png`, `residuals_vs_fitted.png`). **Verification**: Assert that the plot files exist in `data/processed/plots/`. **Note**: This task MUST run BEFORE T065 to ensure plot files exist for embedding.
- [ ] T065 [US2/US3] [Depends: T066, T041] **Implement Report Generation**: Implement `code/report.py` function `generate_report()` to create the final PDF/HTML report. **Action**: Read `data/processed/model_results.json` and `data/processed/daily_aggregates.csv`. **Library**: Use `reportlab` and `matplotlib`. **Output**: `data/processed/report.pdf`. **Content**: Include effect sizes, 95% confidence intervals, **diagnostic plots (residuals vs. fitted) by explicitly reading the pre-generated plot files from `data/processed/plots/` and embedding them into the document**, LOPO consistency metrics, and sensitivity analysis results. **Constraint**: The report MUST explicitly label all findings as "associational" (FR-004). **Explicit Check**: If `model_results.json` contains `convergence_diagnosis.status` == 'non-significant' (as set by T074), the report MUST explicitly insert the text: "Model failed to converge; result flagged as non-significant" (FR-003). **Verification**: Assert that the generated file exists and contains the string "associational" and the non-significant flag text if applicable.
- [ ] T067 [P] [US3] Final validation of `model_results.json` against `model_results.schema.yaml` to ensure all required fields (including sensitivity and validation metrics) are present and populated. **Action**: If validation fails, raise `RuntimeError` with specific field paths missing. **CRITICAL**: Explicitly verify that the `diagnostic_tests` object exists and contains `shapiro_wilk_p_value` and `breusch_pagan_p_value` to satisfy SC-004.
- [ ] T068 [P] [US3] Final validation of `daily_aggregates.csv` against `daily_aggregates.schema.yaml` to ensure data integrity before reporting.
- [ ] T069 [P] [US3] Create a summary text file `data/processed/analysis_summary.txt` containing the key findings: primary coefficient, p-value, LOPO consistency %, and sensitivity pass/fail status for quick reference.

**Checkpoint**: Final report generated and all artifacts validated.

---

## Phase 10: Review & Revision (Addressing Analysis Findings)

**Purpose**: Tasks added to address specific concerns raised by `/speckit.analyze` regarding data streaming, model convergence robustness, and edge-case handling.

- [ ] T075a [US1] **Memory Streaming Implementation**: Implement `code/preprocess.py` function `process_bronze_in_chunks()` to handle `data/raw/bronze.parquet` if it exceeds available memory (e.g., > 4GB). **Logic**: Use `dask.dataframe.read_parquet` to stream-read the **local, checksummed file** (`data/raw/bronze.parquet`) in segments (chunk size `config.CHUNK_SIZE = 100000`). Compute partial aggregates for each chunk and merge them in a streaming fashion to produce the final `daily_aggregates.csv` without loading the entire dataset into RAM. **Action**: This ensures the pipeline runs within a constrained memory environment of the GitHub Actions free-tier runner, satisfying Spec Assumptions and Plan Constraints. **Constraint**: This task operates ONLY on the local file created and checksummed by T007. It does NOT download or stream from remote APIs. **Do NOT** use `datasets.load_dataset` for remote streaming as it violates Constitution Principles I and III.
- [ ] T077 [US2] **Enhanced Convergence Diagnostics**: Implement `code/analysis.py` function `diagnose_convergence_failure()` to be called when `fit_lmm_robust()` falls back to GLS. **Logic**: Analyze the Hessian matrix, gradient norms, and iteration history to determine if the failure is due to perfect separation, near-zero variance components, or data sparsity. **Action**: Log specific warnings (e.g., "Variance component near zero; random intercept may be redundant") to `data/processed/diagnostics_temp.json` under a new `convergence_diagnosis` key. **Constraint**: This provides actionable feedback for FR-003 compliance, ensuring the fallback is not just a blind retry but a documented, reasoned alternative.
- [ ] T078 [US3] **Robustness Check for Single-Rating Imputation**: Implement `code/analysis.py` function `validate_imputation_plausibility()` before running the bootstrap loop in T031c. **Logic**: Compare the distribution of imputed mood values (participant medians) against the distribution of actual mood values for the same participant. **Action**: If the imputed values are statistically indistinguishable from the actual values (e.g., via KS-test p > 0.05), log a "Plausible" flag; otherwise, log a "Caution: Imputation may introduce bias" warning. **Constraint**: This addresses the edge case where a single rating is an outlier, ensuring the sensitivity analysis (FR-008) is robust to extreme imputation artifacts.
