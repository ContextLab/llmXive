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

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. This phase includes mandatory edge-case handling to prevent downstream failures.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002 Initialize Python project with dependencies (`pandas`, `statsmodels`, `scikit-learn`, `pyyaml`, `requests`, `numpy`) in `code/requirements.txt`
- [X] T003b [P] Create `pyproject.toml` in `code/` with `[tool.black]` section, `line-length = 88`, and `target-version = ['py311']` (Supports **Code Quality Standards**)
- [X] T004 [P] Create configuration module `code/config.py` defining paths, random seeds (`SEED = 42`), constants (including `MISSINGNESS_THRESHOLD`, `BOOTSTRAP_ITERATIONS = 1000`), and the specific OSF DOI string for the dataset
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
 - `diagnostic_tests`: object, required (keys: shapiro_wilk_p_value, breusch_pagan_p_value)
 - `validation`: object, required (keys: lopo_average_rmse, lopo_sign_consistency_pct)
 - `sensitivity`: object, required (keys: weekdays_only_sign_consistent, weekdays_only_pvalue, weekdays_only_pvalue_consistent, active_minutes_sign_consistent, single_rating_bootstrap_consistency, single_rating_bootstrap_pass)
- [X] T005c [P] Create schema definition `preprocess_stats.schema.yaml` in `specs/001-physical-activity-levels-and-mood-variab/contracts/` with the following structure:
 - `excluded_days_count`: integer, required
 - `reason`: string, required (e.g., "n_mood_ratings < 2")
 **Action**: Validate the generated JSON against this schema before writing to ensure FR-002 compliance.
- [X] T006 [P] Create base test utilities in `tests/conftest.py` for schema validation and fixture data
- [X] T007 [P] Create `code/ingest.py` to download StudentLife dataset from OSF DOI specified in `code/config.py`. **Critical Integrity Steps**: 1) Compute a cryptographic SHA‑256 checksum immediately upon download completion (before any write). 2) Convert the downloaded zip to `data/raw/bronze.parquet`. 3) Atomically update `state/projects/PROJ-715-physical-activity-levels-and-mood-variab.yaml` under the exact key `artifact_hashes: { data_raw_bronze: "<sha256_hex_string>" }` using a helper function `update_state_artifact_hash(state_path, key, value)` that reads the YAML, updates the dict, and writes it back atomically. This ensures Constitution Principle III (Data Hygiene) compliance and defines the exact output filename for downstream tasks.
- [X] T007b [Depends: T007] **Artifact Verification**: Explicitly verify that `data/raw/bronze.parquet` exists and is readable. **Output**: Writes `data/raw/bronze.parquet` to disk as a verifiable artifact. **Dependency**: This file is the required input for T011.
- [X] T052 [US1] [Depends: T007] **Fail Loudly on Corruption**: Modify `code/ingest.py` to remove any `try/except` blocks that might silently fallback to synthetic data generation. **Action**: If the OSF download fails or the file is corrupted (checksum mismatch), the script must raise a `RuntimeError` with a clear message listing the missing files or network error, ensuring the pipeline fails loudly rather than fabricating data.
- [X] T051 [US1] [Depends: T007] **Corrupted Data Check**: Implement a validation step in `code/ingest.py` or a new `code/validate_raw.py` to verify the integrity of `data/raw/bronze.parquet` against the recorded checksum. If the file is missing or corrupted, raise a `RuntimeError` with a clear message. This ensures FR-001 compliance.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Download StudentLife dataset, parse raw step logs, align EMA mood timestamps, and compute daily aggregates (`total_steps`, `mean_mood`, `mood_std`) per participant‑day.

**Independent Test**: Verify that `data/processed/daily_aggregates.csv` contains one row per participant per day with non‑null `total_steps`, `mean_mood`, `mood_std`, and row count matches valid participant‑days.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T009 [P] [US1] Contract test for `daily_aggregates.csv` schema in `tests/contract/test_daily_aggregates.py`
- [X] T010 [P] [US1] Unit test for aggregation logic (handling missing ratings, zero steps) in `tests/unit/test_preprocess_aggregation.py` with specific test function `test_aggregate_handles_zero_steps` asserting that days with no recorded steps are retained rather than dropped.

### Implementation for User Story 1

- [X] T011 [US1] [Depends: T007b] Implement `code/preprocess.py` function `parse_step_logs()` to load `data/raw/bronze.parquet` (produced and verified by T007b) and parse raw step logs into daily totals. **Input columns**: `participant_id`, `timestamp`, `step_count`. **Output**: DataFrame with `participant_id`, `date`, `total_steps`. Handle missing `step_count` by treating as 0.
- [X] T012 [US1] [Depends: T011] Implement `code/preprocess.py` function `derive_covariates()` to derive `sleep_duration` and `baseline_affect` from raw data if missing, using `config.MISSINGNESS_THRESHOLD` to decide between derivation and proceeding without them (per spec Assumptions); ensure derived columns are written to the output CSV.
- [X] T013 [US1] [Depends: T011] Implement `code/preprocess.py` function `align_ema_timestamps()` to align EMA mood timestamps and exclude records with missing critical values. **Logic**: Join step logs and EMA data on `participant_id` and `date`. **Exclusion**: Drop any EMA entry where `mood` is null. **Tolerance**: Align timestamps within 24 h window.
- [X] T050 [US1] [Depends: T014] Implement `code/preprocess.py` function `handle_sparse_participants()` to identify participants with < 3 valid days. **Action**: Log a warning and exclude these participants from the random-effects model fitting (fallback to fixed-effects or exclusion) to prevent LMM convergence failures, as per Edge Case "Participant has data for only 1 or 2 days". **Output**: Returns a filtered dataset and a list of excluded participant IDs. **Constraint**: This must run AFTER T014 (compute_daily_aggregates) because it requires the 'valid days' metric.
- [X] T014 [US1] [Depends: T012, T013] Implement `code/preprocess.py` function `compute_daily_aggregates()` to:
 1. **Filter out days with 0 mood ratings FIRST** (drop entirely to avoid division-by-zero).
 2. **Then filter out days with fewer than a minimal number of valid mood ratings** (to satisfy FR‑002 and Constitution Principle VI).
 3. Compute daily aggregates: `mean_mood` and **raw** `mood_std` (standard deviation, recording `0.0` for days with identical ratings). **Do NOT** apply log‑transformation here. (Note: 0.0 values are handled by applying epsilon offset in T019c).
 4. **Log the count of excluded days** to `data/processed/preprocess_stats.json` using function `write_preprocess_stats()`. **Output**: Writes a JSON file matching `preprocess_stats.schema.yaml` with `{"excluded_days_count": int, "reason": "n_mood_ratings < 2 or count == 0"}`. **Validate** the output against `preprocess_stats.schema.yaml` before writing.
 5. Ensure `total_steps` is recorded as 0 for days with zero steps.
- [X] T015 [US1] [Depends: T014] Write the final output to `data/processed/daily_aggregates.csv` and validate against `daily_aggregates.schema.yaml`. **Assert** that no NaN/Inf values exist in the `mood_std` column before writing using `assert (df['mood_std'] >= 0).all() and np.isfinite(df['mood_std']).all()`.

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
- [X] T019c [US2] Implement `code/analysis.py` function `apply_log_transform(mood_std: np.ndarray) -> np.ndarray` that returns `np.log(mood_std + epsilon)`. **This is the SINGLE authorized mechanism** for the log transformation used by all models. **Depends**: T019a.
- [X] T020a [US2] [Depends: T019c, T050] Implement `code/analysis.py` function `fit_lmm_variability()` to fit the primary LMM with `apply_log_transform(mood_std)` as the outcome and `total_steps` as the primary predictor (random intercepts for participant). **Note**: T050 ensures sparse participants are excluded before this step.
- [X] T020b [US2] [Depends: T019c, T050] Implement `code/analysis.py` function `fit_lmm_mean()` to fit the secondary LMM with `mean_mood` as the outcome and `total_steps` as the predictor.
- [X] T022 [US2] [Depends: T020a, T020b] Implement `code/analysis.py` function `extract_model_coefficients()` to extract fixed‑effect coefficients, standard errors, p‑values, and 95 % CIs for `total_steps` and covariates (sleep, day-of-week, baseline_affect) from both models.
- [X] T023 [US2] [Depends: T020a, T020b] Implement `code/analysis.py` function `run_model_diagnostics()` to perform model diagnostics (Shapiro‑Wilk, Breusch‑Pagan) and generate residual plots (specifically "residuals vs. fitted"). **Action**: **Write the statistical test results (p-values)** to `data/processed/diagnostics_temp.json` under the key `diagnostic_tests` with structure `{"shapiro_wilk_p_value": float, "breusch_pagan_p_value": float}`. **Return**: A dictionary containing these values for T041 to merge. **Constraint**: Ensure these values are persisted in the final artifact for SC-004 compliance.
- [X] T024a [US2] [P] Implement `code/analysis.py` to ensure all results are explicitly labeled as "associational" in internal data structures.
- [X] T025 [US2] [Depends: T020a, T020b, T022] **Compute the base model results** dictionary. **Action**: Combine coefficients from T022 and model fit statistics. **Return**: A dictionary containing `fixed_effects`, `random_effects`, `model_fit`, `associational_label`, and `diagnostic_tests` (loaded from T023's temp file). **Do NOT write to disk yet**; this data will be merged by T041. This task replaces the previous "partial write" pattern by ensuring the base model is computed and returned as a complete object for merging.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (base models ready, but full results pending US3)

---

## Phase 5: User Story 3 - Validation and Sensitivity Analysis (Priority: P3)

**Goal**: Perform leave‑one‑participant‑out (LOPO) cross-validation and sensitivity analyses (weekdays‑only, alternative metrics, single‑rating handling) to ensure robustness.

**Independent Test**: Verify final report contains LOPO coefficient consistency (≥ 90% sign stability), sensitivity check results, and bootstrap consistency for single‑rating handling (≥ 80%).

### Tests for User Story 3

- [X] T026 [P] [US3] Unit test for LOPO loop logic and coefficient aggregation in `tests/unit/test_analysis_validation.py` with specific test function `test_lopo_sign_consistency` asserting `sign_consistency >= 0.90`.
- [X] T027 [P] [US3] Unit test for sensitivity analysis logic (weekdays filter, metric swap) in `tests/unit/test_analysis_sensitivity.py` with specific test function `test_sensitivity_weekdays_sign_consistent`.

### Implementation for User Story 3

- [X] T028a [US3] Implement `code/analysis.py` function `run_lopo_cv()` to retrain the primary model N times (N = number of participants), track `total_steps` coefficient sign stability, and calculate the **average RMSE** across all LOPO folds. **Return**: A dictionary `{"average_rmse": float, "sign_consistency_pct": float, "coefficients": list}`.
- [X] T028b [US3] [Depends: T025, T028a] Compute the percentage of folds where the `total_steps` coefficient sign matches the full‑data sign. **Action**: Return a dictionary containing `sign_consistency_pct` (float), `average_rmse` (float), and a boolean `pass` flag (True if consistency >= 90%, False otherwise). **Do NOT raise RuntimeError**. This ensures the pipeline completes and reports the metric as required by FR-005. **Return**: The exact metrics for consumption by T041.
- [X] T029 [US3] [Depends: T025] Implement `code/analysis.py` function `run_sensitivity_weekdays()` to re‑run the primary model on "weekdays only" data and compare coefficients. **Result**: Return a dictionary containing the `total_steps` coefficient, the **actual p-value** (float), and boolean flags for `sign_consistent` and `pvalue_consistent` (p < 0.05 status matches primary model) for merging.
- [X] T030 [US3] [Depends: T025] Implement `code/analysis.py` function `run_sensitivity_active_minutes()` to re‑run the model using "active minutes" instead of step counts and compare direction of effect. Return a result dictionary for merging.
- [X] T031a [US3] Implement logic to exclude single‑rating days from the dataset for the primary sensitivity branch.
- [X] T031b [US3] Implement logic to impute single‑rating days using the participant's median mood value for the secondary sensitivity branch.
- [X] T031c [US3] [Depends: T025] Implement `code/analysis.py` function `run_sensitivity_single_rating_bootstrap()` to execute a **bootstrap sampling loop** with `config.BOOTSTRAP_ITERATIONS` (1000) iterations. For each iteration `i`:
 1. Set `np.random.seed(42 + i)` (seed 42 defined in T004, incremented by iteration).
 2. Fit the exclusion model (using T031a logic) and the imputation model (using T031b logic).
 3. Compare the sign of the `total_steps` coefficient from both models (`np.sign(coef_excl) == np.sign(coef_imp)`).
 4. Record whether the direction remains consistent.
 After the loop, calculate the **consistency percentage**. **Calculate a boolean `pass` flag** (True if percentage >= 80%, False otherwise). **Return**: A dictionary containing `consistency_percentage` (float), `pass` (bool), and `bootstrap_samples` (list of booleans). **Action**: This result MUST be merged into `model_results.json` by T041 to satisfy FR-008 reporting requirements.
- [ ] T060 [US3] [Depends: T031c] **Detect CPU Timeout/Failure**: Implement a timeout wrapper in `code/analysis.py` around `run_sensitivity_single_rating_bootstrap()` that catches `TimeoutError` or `MemoryError`. If triggered, log a specific "GPU_REQUIRED" flag to `state/projects/PROJ-715-physical-activity-levels-and-mood-variab.yaml`.
- [ ] T061 [US3] [Depends: T060] **Generate GPU Offload Script**: Create `scripts/run_gpu_bootstrap.sh` that sets `CUDA_VISIBLE_DEVICES=0` and executes `python code/analysis.py --task run_sensitivity_single_rating_bootstrap --device cuda`. This script is designed to be picked up by the execution stage's auto-offload mechanism.
- [ ] T062 [US3] [Depends: T061] **Update State for GPU Retry**: Modify the state update logic to include `execution_context: { gpu_required: true, fallback_script: "scripts/run_gpu_bootstrap.sh" }` when T060 triggers, ensuring the execution stage knows to re-run on Kaggle GPU.
- [ ] T063 [US1] [Depends: T007] **Implement Verified Mirror Fallback**: In `code/ingest.py`, if the primary OSF DOI download fails (network error or 404), attempt to fetch from the verified HuggingFace mirror of the StudentLife dataset using `datasets.load_dataset("studentlife", split="train")`. **Constraint**: This fallback is ONLY permitted if the mirror is a verified, canonical copy of the OSF dataset (checksum must match). If the mirror also fails, raise `RuntimeError`. Do NOT generate synthetic data. OSF DOI remains the primary source.
- [ ] T064 [US1] [Depends: T063] **Log Source Fidelity**: Add a field `data_source_url` to `data/processed/preprocess_stats.json` recording exactly which URL or package was used to fetch the data (OSF or HF). This ensures traceability for SC-001.

**Checkpoint**: All user stories should now be independently functional, with US3 completing the full analysis pipeline

---

## Phase 6: Result Merging & Reporting

**Purpose**: Merge all results into the final artifact and generate the report

- [X] T041 [US2/US3 Merge] [Depends: T025, T028b, T029, T030, T031c, T023] **Write the final `model_results.json`**. **Action**: Load base results from T025. Update the `validation` section with LOPO results from T028b. Update the `sensitivity` section with results from T029, T030, and T031c. Update the `diagnostic_tests` section with results from T023 (loaded from `data/processed/diagnostics_temp.json`). **Validate** the final dictionary against `model_results.schema.yaml`. **Write** the complete JSON to `data/processed/model_results.json`. **Constraint**: This task is the **sole writer** of the final `model_results.json` to prevent race conditions or overwrites. **Input Schema Expectations**: T025 provides `fixed_effects`, `random_effects`, `model_fit`, `associational_label`; T028b provides `average_rmse`, `sign_consistency_pct`; T029/T030/T031c provide their respective dictionaries; T023 provides `shapiro_wilk_p_value`, `breusch_pagan_p_value`.

**Checkpoint**: All user stories should now be independently functional, with US3 completing the full analysis pipeline

---

## Phase 7: Entry Point & CLI

**Purpose**: Create the executable entry point for the pipeline

- [X] T040 [P] Create `code/main.py` as the CLI entry point. **Logic**: Import and orchestrate `ingest.py`, `preprocess.py`, `analysis.py`, and `report.py` in sequence. Parse `--input` argument (optional, defaults to `data/processed/daily_aggregates.csv`). **Output**: Returns exit code 0 on success, non-zero on failure. **Dependency**: Required for T034a-2.

---

## Phase 8: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T034a-1 [P] Update `README.md` with specific section: Installation (include pip install command `pip install -r code/requirements.txt`)
- [X] T034a-2 [P] Update `README.md` with specific section: Usage (include CLI example `python code/main.py --input data/processed/daily_aggregates.csv`). **Verification**: Run the command `python code/main.py --input data/processed/daily_aggregates.csv` and assert exit code == 0. **Dependency**: T040.
- [X] T034b [P] Update `specs/001-physical-activity-levels-and-mood-variab/` (aligned with plan.md Project Structure) with specific content: API documentation for `analysis.py` and Data Dictionary for `daily_aggregates.csv`. **Note**: If a root‑level `docs/` directory exists from previous revisions, remove or deprecate it to prevent path conflicts.
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