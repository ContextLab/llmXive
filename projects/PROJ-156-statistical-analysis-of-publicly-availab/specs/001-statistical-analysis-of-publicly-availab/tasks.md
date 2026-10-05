# Tasks: Statistical Analysis of Speedrun Data

**Input**: Design documents from `/specs/001-speedrun-statistics/`
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
 - Delivered as a MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 [P] Initialize project directory structure: Create `data/raw`, `data/processed`, `data/checkpoints`, `code/scripts`, `code/tests`, `contracts`, `paper`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Create `contracts/run_record.schema.yaml` defining RunRecord entity (run_time_seconds, runner_id, attempt_number, category, submission_date, game_id)
 - **Action**: Create file `contracts/run_record.schema.yaml` with the following JSON schema content:
 ```yaml
 $schema: http://json-schema.org/draft-07/schema#
 type: object
 properties:
   run_time_seconds: { type: number, minimum: 0 }
   runner_id: { type: string, pattern: "^[a-f-64]{64}$" } # Salted SHA-256
   attempt_number: { type: integer, minimum: 1 }
   category: { type: string }
   submission_date: { type: string, format: date-time }
   game_id: { type: string }
   total_prior_runs: { type: integer, minimum: 0 }
   time_since_first_run_days: { type: number, minimum: 0 }
   lagged_competitive_pressure: { type: integer, minimum: 0 }
 required: [run_time_seconds, runner_id, attempt_number, category, submission_date, game_id]
 ```
 - **Verification**: Assert that `contracts/run_record.schema.yaml` exists and is valid YAML/JSON Schema.

- [X] T005 [P] Create `contracts/distribution_fit.schema.yaml` defining DistributionFit entity (game_id, distribution_family, parameters, KS_D, KS_pvalue, AIC)
 - **Action**: Create file `contracts/distribution_fit.schema.yaml` with the following JSON schema content:
 ```yaml
 $schema: http://json-schema.org/draft-07/schema#
 type: object
 properties:
   game_id: { type: string }
   distribution_family: { type: string, enum: ["log-normal", "Weibull", "Gamma", "descriptive"] }
   parameters: { type: object, additionalProperties: { type: number } }
   KS_D: { type: ["number", "null"] }
   KS_pvalue: { type: ["number", "null"] }
   AIC: { type: ["number", "null"] }
   ad_statistic: { type: ["number", "null"] }
 required: [game_id, distribution_family, parameters]
 ```
 - **Verification**: Assert that `contracts/distribution_fit.schema.yaml` exists and is valid YAML/JSON Schema.

- [X] T006a [P] Define schema for configuration keys in `code/config.yaml`:
 - **Action**: Define the schema and expected keys for `code/config.yaml` (e.g., `games`, `min_sample_size`, `salt`, `effect_size_assumptions`, `lagged_pressure_window_days`). **Note**: This task defines the schema only; file creation is deferred to T006b.
 - **Schema**: Explicitly state expected YAML structure:
 ```yaml
 games: [string]
 min_sample_size: int
 salt: string
 effect_size_assumptions: float
 lagged_pressure_window_days: int
 ```
 - **Verification**: Assert that the keys are documented and ready for file creation in T006b.

- [X] T006b Create `code/config.yaml` file:
 - **Action**: Create file `code/config.yaml` with the following YAML content based on T006a keys. **Requirement**: `effect_size_assumptions` MUST be a numeric value (e.g., 0.5), not a placeholder string, to enable power analysis calculations.
 - **Content**:
 ```yaml
 games:
 - "super-mario-64"
 - "zelda-oot"
 # Add more games as needed
 min_sample_size:
 salt: "speedrun-statistics-project-salt-2025"
 effect_size_assumptions: a moderate effect size
 lagged_pressure_window_days:
 ```
 - **Verification**: Assert that `code/config.yaml` exists, is valid YAML, and contains numeric values for `effect_size_assumptions`.

- [X] T007a [P] Create `code/scripts/hash_artifacts.py`:
 - **Action**: Implement script to compute SHA-256 checksums for all `data/` files (Constitution Principle V).
 - **Output**: Module file `code/scripts/hash_artifacts.py`.
 - **Verification**: Assert that the script file exists and is executable. **Critical Execution Order**: Although marked [P] for parallel creation, this script file MUST be committed and available before Phase 3 begins (specifically before T013b runs), as it is a runtime dependency for T013b and T036.
 - **Note**: This script file must be committed and available before Phase 3 begins, as it is a runtime dependency for T013b.

- [X] T007b [P] Run `hash_artifacts.py` to initialize state:
 - **Action**: Execute `python code/scripts/hash_artifacts.py` to generate initial checksums.

- [X] T008a [P] Create `code/scripts/utils/checkpoint.py`:
 - **Action**: Implement utility module to save/load intermediate state (JSON) for resumption on CI timeout.
 - **Output**: Module file `code/scripts/utils/checkpoint.py`.

- [X] T008b [P] Create `code/scripts/utils/bonferroni.py`:
 - **Action**: Implement utility module to apply Bonferroni correction to a list of p-values with a configurable total test count.
 - **Output**: Module file `code/scripts/utils/bonferroni.py`.

- [X] T009 [P] Setup `code/tests/conftest.py` with fixtures for mock speedrun.com API responses and sample data

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel
**Note**: T004 and T005 now include full schema content, resolving "missing schema" risk.

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Download, clean, and engineer features for speedrun data to ensure ≥95% completeness and compute runner experience metrics.

**Independent Test**: Verify script outputs a CSV with run times, runner IDs, attempt numbers, categories, and dates; duplicates removed; ≥95% record retention; per-runner metrics computed.

### Implementation for User Story 1

- [X] T012 [US1] Implement `code/scripts/fetch_data.py` to download raw JSON from speedrun.com API for multiple games (FR-001)
 - *Note*: Must handle pagination and save raw JSON to `data/raw/`

- [X] T013a [US1] Implement `code/scripts/preprocess.py` to:
 - Remove duplicates and filter incomplete runs (FR-002)
 - Compute `total_prior_runs` and `time_since_first_run_days` for every record (FR-003)
 - Validate output against `contracts/run_record.schema.yaml`
 - Save to `data/processed/run_records.csv`

- [X] T013b [US1] Implement runner_id anonymization in `code/scripts/preprocess.py` using SHA-256 with project-specific salt (from `code/config.yaml` created in T006b) to satisfy Constitution Principle III while preserving unique grouping for mixed-effects models (FR-006)
 - *Dependency*: **MUST** run after T006b (config creation) AND T007a (hash script creation).
 - *Note*: The salted hash must be deterministic to allow grouping by `RunnerID` in T027. T007a creates the script file which must be committed before this task runs.
 - *Verification*: Assert that `runner_id` in `run_records.csv` matches the salted hash of the original ID and is not the original ID.
 - *Constraint*: Read raw runner IDs from `data/raw`, compute salted hash, write hashed ID to `data/processed`, and DO NOT modify `data/raw` (Constitution Principle III).
 - *Output*: `runner_id` column in `run_records.csv` contains the salted hash.
 - *Critical Execution Order*: T007a (hash script creation) MUST be committed and available before T013b executes to prevent race conditions.

- [X] T013c [US1] Generate `RunnerProfile` entity:
 - **Action**: Implement logic in `code/scripts/preprocess.py` to aggregate per-runner statistics: `total_prior_runs`, `time_since_first_run_days`, `games_played_count`.
 - **Schema**: Columns: `runner_id` (hashed), `total_prior_runs` (count of all runs), `time_since_first_run_days` (max date - min date), `games_played_count` (unique game_ids).
 - **Aggregation Logic**: Group by `runner_id`, then aggregate: `total_prior_runs` = count of rows, `time_since_first_run_days` = (max(submission_date) - min(submission_date)).days, `games_played_count` = nunique(game_id).
 - **Output**: Create file `data/processed/runner_profiles.csv` (Key Entities: RunnerProfile).

- [X] T013d [US1] Attach experience metrics to run records (FR-003):
 - **Action**: Merge `total_prior_runs` and `time_since_first_run_days` from `runner_profiles.csv` into `run_records.csv` on `runner_id`.
 - **Verification**: Assert that `run_records.csv` contains the `total_prior_runs` and `time_since_first_run_days` columns populated for every record.
 - **Output**: `data/processed/run_records.csv` with attached metrics.

- [X] T013e [US1] Create audit trail for anonymization (Constitution Principle I):
 - **Action**: Save the salted hash mapping (original_id -> hashed_id) to `data/checkpoints/anonymization_audit.json` before hashing.
 - **Verification**: Assert that `anonymization_audit.json` exists and contains the mapping for all processed runners.
 - **Rationale**: Ensures ability to audit 'active_runners_count' calculation against raw API data. This artifact MUST be used for manual verification of the 'active_runners_count' proxy against raw API data.

- [X] T013f [US1] Pre-evaluate power constraints (FR-009, F001):
 - **Action**: Calculate the total number of runs per game in the raw dataset and compare against `min_sample_size` (a predefined minimum threshold). Generate a preliminary power assessment report indicating which games are likely to be excluded from parametric fitting due to low sample size.
 - **Output Artifact**: `data/processed/power_pre_evaluation.json`.
 - **Schema**: `[ { "game_id": string, "run_count": int, "excluded_from_parametric": boolean } ]`.
 - **Rationale**: Addresses F001 by acknowledging power limitations BEFORE the exclusion decision in T021a. This task MUST run before any parametric fitting to ensure constraints are evaluated early.

- [X] T014 [US1] Implement lagged `competitive_pressure` calculation in `code/scripts/preprocess.py` (Plan: Phase 0 Step 3, FR-006)
 - *Dependency*: **MUST** run after T013c (RunnerProfile aggregation) and T013b (anonymization) to ensure valid -day rolling windows and grouping by final `runner_id`.
 - *Algorithm*: Calculate `active_runners_count` in a configurable window prior to run date. For each run, filter all runs in the dataset where `submission_date` is within `[run_date - lagged_pressure_window_days days, run_date - 1 day]` and count unique `runner_id`s. The `lagged_pressure_window_days` value is read from `code/config.yaml` (T006b), NOT hard-coded.
 - *Output*: Add column `lagged_competitive_pressure` to `data/processed/run_records.csv`.
 - *Constraint*: T014 must complete before T027 (US3) can run.

- [X] T015a [US1] Integrate checkpoint mechanism into `fetch_data.py` (FR-012, Plan: Phase 0 Step 5)
 - *Dependency*: Requires `code/scripts/utils/checkpoint.py` (T008a) to be created.
 - *Note*: Must handle a time limit.
 - *Verification*: Implement logic in `fetch_data.py` to save state after each game. **Verify** by injecting a mock timeout/signal (e.g., raising `KeyboardInterrupt` after the first game) and asserting that: (1) a checkpoint JSON file is saved to `data/checkpoints/fetch_checkpoint.json` containing the list of completed game IDs and partial metrics, and (2) a subsequent run successfully resumes from this checkpoint, fetching only the remaining games.
 - *Artifact Schema*: `fetch_checkpoint.json` must contain `{ "completed_games": [string], "last_timestamp": string, "partial_results": object }`.

- [X] T015b [US1] Integrate checkpoint mechanism into `preprocess.py` (FR-012, Plan: Phase 0 Step 5)
 - *Dependency*: Requires `code/scripts/utils/checkpoint.py` (T008a) to be created.
 - *Note*: Must handle time-constrained scenarios.
 - *Verification*: Implement logic in `preprocess.py` to save state after each game. **Verify** by injecting a mock timeout/signal after processing the first game's data and asserting that: (1) a checkpoint JSON file is saved to `data/checkpoints/preprocess_checkpoint.json` containing the current game index and partial processed data, and (2) a subsequent run successfully resumes, loading the checkpoint and continuing from the interrupted game without re-processing completed games.
 - *Artifact Schema*: `preprocess_checkpoint.json` must contain `{ "current_game_index": int, "processed_rows": int, "partial_data_path": string }`.

- [X] T016a [US1] Implement script to fetch/load game difficulty labels (T006c moved):
 - **Action**: Implement script to fetch/load game difficulty labels from external sources (Machin et al.) and save to `data/processed/game_metadata.csv`.
 - **Source**: Fetch from "Machin et al. (2021) - Speedrun Difficulty Rankings " (GitHub repo or dataset) or document manual fetch if no API exists.
 - **Output**: `data/processed/game_metadata.csv` with columns: `game_id`, `game_name`, `difficulty_label`, `active_runners_count`.
 - **Dependency**: This task is now part of US1 (Data Acquisition) to ensure semantic consistency.

- [X] T016b [US1] Implement strict real-data loader with "fail loud" policy (T039 moved):
 - **Action**: Refactor `fetch_data.py` to remove any `try/except` blocks that fall back to `generate_synthetic_*()` or mock data. If the real speedrun.com API fetch fails, the script MUST raise a `RuntimeError` with a clear message and exit.
 - **Verification**: Verify that the script raises an exception when the API endpoint is unreachable and does NOT produce a CSV with synthetic data.
 - **Rationale**: Addresses the "Loader must fail loudly" rule to prevent silent fabrication of data.

- [X] T016c [US1] Implement streaming data processing for large datasets (T040 moved):
 - **Action**: Refactor `preprocess.py` to use `datasets.load_dataset(..., streaming=True)` or chunked CSV reading if the raw dataset exceeds available RAM capacity. Accumulate statistics online (running mean, count, etc.) without loading the full dataset into memory.
 - **Verification**: Verify that the script processes a simulated large dataset without exceeding available memory limits., using `memory_profiler`.
 - **Rationale**: Addresses the "Large real datasets: STREAM" rule to ensure feasibility on free-tier runners without fabricating toy datasets.

- [X] T016d [US1] Pre-check difficulty label availability (T006c verification):
 - **Action**: Implement logic to verify that the loaded difficulty labels from `data/processed/game_metadata.csv` are present for the specific games listed in `code/config.yaml` (T006b) BEFORE the pipeline proceeds to modeling.
 - **Verification**: Assert that the script exits with an error if any game in `config.yaml` is missing a difficulty label, or logs a warning and excludes that game from the difficulty analysis.
 - **Rationale**: Addresses the risk of silent failure or exclusion of all games at runtime.

- [X] T016 [US1] Implement robust data fetching with retry, caching, and logging in `code/scripts/fetch_data.py` (Plan: Risks & Mitigations, SC-005)
 - *Note*: Consolidates retry, caching, and logging logic into a single atomic implementation.

- [X] T017 [US1] Add logging for data acquisition and preprocessing steps in `code/scripts/fetch_data.py` and `preprocess.py` (Plan: Risks & Mitigations, SC-005)
 - *Note*: Must ensure data acquisition completes within 6-hour limit.

### Tests for User Story 1 (Mandatory per Spec) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation. Note: Tests must run AFTER implementation tasks.

- [X] T010 [US1] Contract test for `run_record.schema.yaml` validation in `code/tests/test_preprocess.py`
 - *Dependency*: **MUST** run after T004 (schema creation) and T012/T013 (data).
 - *Note*: Asserts that `contracts/run_record.schema.yaml` exists, then implements `assert jsonschema.validate(run_records, schema)`.
 - *Verification*: Verify that `contracts/run_record.schema.yaml` exists before running validation logic.
 - *Specific Path*: `code/tests/test_preprocess.py::test_run_record_schema`.

- [X] T011 [US1] Integration test for data completeness (≥95% retention) and duplicate removal in `code/tests/test_fetch.py`
 - *Dependency*: **MUST** run after T012 (fetch) and T013 (preprocess).
 - *Note*: Asserts that `len(processed) / len(raw) >= 0.95`.

- [X] T011b [US1] Explicit verification task for SC-003 in `code/tests/test_preprocess.py`
 - *Note*: Asserts that the retention calculation logic in `preprocess.py` correctly filters incomplete runs and counts retained records.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Distribution Fitting and Goodness-of-Fit Testing (Priority: P2)

**Goal**: Fit parametric distributions (log-normal, Weibull, gamma) to speedrun times and evaluate them with KS tests and AIC.

**Independent Test**: Verify script outputs max-likelihood estimates, KS statistics, and AIC; flags rejected distributions; selects best fit by AIC.

### Implementation for User Story 2

- [X] T020 [US2] Implement `code/scripts/fit_distributions.py` to:
 - Fit log-normal, Weibull, and gamma distributions using MLE (FR-004)
 - Perform KS tests and calculate AIC for each (FR-004)
 - Flag distributions with p < 0.05 and recommend next-best (FR-005)
 - Filter out games with <100 runs (Edge Case: Low-sample)
 - Read `min_sample_size` from `code/config.yaml` (T006)
 - Save results to `data/processed/distribution_fits.csv`
 - **Output Schema**: `game_id`, `distribution_family`, `mu`, `sigma` (or params), `KS_D`, `KS_pvalue`, `AIC`, `ad_statistic`.

- [X] T021a [US2] Implement logic to filter games with n < 100 from parametric fitting (Spec: Edge Cases)
 - *Trigger*: If `n < 100`, exclude from primary parametric fitting rows.
 - *Action*: Filter `distribution_fits.csv` to exclude games with n < 100 from the "parametric" rows.
 - *Dependency*: Uses pre-evaluation from T013f to confirm exclusion criteria.
 - *Deliverable*: Verify that `distribution_fits.csv` does not contain parametric fit rows for games with n < 100.

- [X] T021b [US2] Run Anderson-Darling test on low-sample games (Spec: Edge Cases)
 - *Trigger*: For games filtered in T021a (n < 100).
 - *Action*: Implement logic in `code/scripts/fit_distributions.py` to run the Anderson-Darling test on the run times of these specific games.
 - *Output*: Calculate and store the `ad_statistic` value for each low-sample game.
 - *Deliverable*: Verify that `data/processed/distribution_fits.csv` contains the `ad_statistic` column populated for low-sample games.

- [X] T021c [US2] Implement logic to add 'descriptive' rows for excluded games (Spec: Edge Cases)
 - *Trigger*: If `n < 100`, add a separate row for each excluded game to `data/processed/distribution_fits.csv`.
 - *Action*: For each game with n < 100, add a row with `distribution_family='descriptive'`, `KS_D=null`, `KS_pvalue=null`, `AIC=null`, and `ad_statistic=<value>` (from T021b).
 - *Deliverable*: Verify that `distribution_fits.csv` contains the 'descriptive' flag for excluded games and explicitly sets null values for KS statistics.

- [X] T021d [US2] Generate human-readable flag for low-sample games (Constraint Preservation):
 - **Action**: Implement logic in `generate_report.py` (or a dedicated task) to create a summary section in `paper/draft.md` listing games excluded from parametric fitting due to low sample size (<100 runs) and the reason (insufficient data for KS test reliability).
 - **Verification**: Verify that `paper/draft.md` contains a section explicitly listing excluded games and the reason for exclusion.
 - **Rationale**: Addresses the requirement for a human-readable flag in the final report, not just a null row in CSV. This ensures SC-001 measurability for excluded games.

- [X] T023 [US2] Validate `distribution_fits.csv` against `contracts/distribution_fit.schema.yaml`
 - *Dependency*: **MUST** run after T005 (schema creation).
 - *Verification*: Add a pytest assertion in `code/tests/test_models.py` that loads `data/processed/distribution_fits.csv` and asserts it passes `jsonschema.validate` against `contracts/distribution_fit.schema.yaml`.
 - *Verification*: Verify that `contracts/distribution_fit.schema.yaml` exists before running validation logic.
 - *Specific Path*: `code/tests/test_models.py::test_distribution_fit_schema`.

- [X] T024 [US2] Add checkpointing after each game's distribution fitting (Plan: Phase 1 Step 5)
 - *Dependency*: Requires `code/scripts/utils/checkpoint.py` (T008a) to be created.

### Tests for User Story 2 (Mandatory per Spec) ⚠️

- [X] T018 [P] [US2] Contract test for `distribution_fit.schema.yaml` validation in `code/tests/test_models.py`
 - *Dependency*: **MUST** run after T005 (schema creation).

- [X] T019 [P] [US2] Integration test for distribution fitting on a single game (KS p ≥ 0.05 check) in `code/tests/test_models.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Learning-Curve Modeling with Mixed-Effects Regression (Priority: P3)

**Goal**: Fit hierarchical mixed-effects models to quantify how experience and external factors modulate performance improvement.

**Independent Test**: Verify model convergence, interpretable coefficients, p-values, VIF checks, and associational framing.

### Implementation for User Story 3

- [X] T027 [US3] Implement `code/scripts/fit_mixed_effects.py` to:
 - **Dependency**: **MUST** run after T014 (lagged pressure), T016a (game metadata), and T013b (anonymization).
 - **Note**: The dependency of T027 on T014 is a necessary cross-story dependency for data flow; US3 cannot be independently shipped without the output of US1's T014.
 - **Note**: T016a (game metadata) is now correctly placed in US1 (Phase 3) as a data acquisition step.
 - **Note**: The dependency on T014 is on the *artifact* (`data/processed/run_records.csv` with `lagged_competitive_pressure`), not the task execution order. US3 is independent of the *task* T014, but dependent on the *data* it produces.
 - Fit `log(Time) ~ log(Attempt Number) + Game Difficulty + Lagged Pressure + log(Attempt Number):Lagged Pressure + (1 | RunnerID)` (FR-006, Plan: Complexity Tracking)
 - *Note*: Exclude `total_prior_runs` from fixed effects to avoid collinearity (Plan: Complexity Tracking)
 - Compute VIFs and flag if > 5 (FR-011)
 - **Verification**: Confirm the interaction coefficient for `log(Attempt Number):Lagged Pressure` is computed and reported.
 - **Verification**: Explicitly check model convergence and the statistical significance of the interaction term before proceeding to avoid spurious coefficients.
 - Save results to `data/processed/model_results.csv`
 - **Output Schema**: `predictor_name`, `coefficient`, `standard_error`, `p_value`, `vif`, `random_effect_variance`.

- [X] T027b [US3] Perform likelihood-ratio tests for nested models (FR-007):
 - **Action**: Construct nested models (e.g., `~ log(Attempt) + (1|RunnerID)` vs `~ log(Attempt) + Difficulty + (1|RunnerID)`; `~ log(Attempt) + Lagged Pressure + (1|RunnerID)` vs `~ log(Attempt) + Lagged Pressure + Difficulty + (1|RunnerID)`) and perform likelihood-ratio tests.
 - **Verification**: Assert that the script reports χ² statistics and p-values for each comparison.
 - **Output**: Append results to `data/processed/model_results.csv` or a separate `model_comparison.csv`.

- [X] T028b [US3] Implement power analysis check and append to report:
 - *Method*: Use G*Power parameters with effect size assumptions from `code/config.yaml` (T006).
 - *Input*: Model coefficients and sample sizes from `data/processed/model_results.csv`.
 - *Action*: Programmatically calculate power limits from model coefficients and sample sizes.
 - **Content Requirement**: Must include a specific statement acknowledging power limitations for small games (e.g., "Power analysis indicates limited ability to detect effects for games with <100 runs").
 - *Format*: Append section 'Power Analysis' to `paper/draft.md` with fields: `sample_size`, `power_limit`, `method`, `effect_size_assumptions`.
 - **Output Artifact**: `paper/draft.md` with appended 'Power Analysis' section.
 - **Parsing Logic**: Read `effect_size_assumptions` (numeric) from `code/config.yaml` and `sample_size` from `data/processed/power_pre_evaluation.json` to generate the specific text block: "Power analysis indicates limited ability to detect effects for games with <100 runs (effect size: a moderate magnitude, alpha: a standard significance threshold).".
 - **Dependency**: Must explicitly reference the output of T013f (power pre-evaluation) to ensure the statement is based on the pre-exclusion analysis.

- [X] T029b [US3] Implement `code/scripts/generate_report.py` to:
 - Aggregate results from all phases
 - Enforce associational language framing (FR-010, SC-006)
 - Invoke Reference-Validator Agent for citations (Plan: Phase 2 Step 5)
 - **Agent Interface**: Run `python -m code.scripts.reference_validator --input paper/draft.md --log code/logs/reference_validator.log`. The agent MUST exit with code 0 if all citations are verified, and code 1 if any fail. The log file MUST contain a JSON object `{"status": "VERIFIED"}` or `{"status": "FAILED", "errors": [...]}`.
 - **Verification**: Verify that `paper/draft.md` is generated and contains no causal verbs OR nouns by running a regex check against the following prohibited terms: `causes`, `affects`, `impacts`, `determines`, `leads to`, `results in`, `effect`, `impact`, `cause`, `consequence`. (Note: Context-aware exceptions allowed for non-causal usage, e.g., 'impact parameter'). **AND** verify that `code/logs/reference_validator.log` contains `{"status": "VERIFIED"}` by running `grep -q '"status": "VERIFIED"' code/logs/reference_validator.log`. If the grep fails, the task is considered failed.
 - **FR-009 Check**: Verify that `paper/draft.md` contains the specific "Power Analysis" section with the required statement acknowledging power limitations for small games.
 - Generate `paper/draft.md`

- [X] T030 [US3] Add logic to exclude games without external difficulty labels from difficulty-modulation analysis (Edge Case: Missing labels)
 - *Source*: Check `data/processed/game_metadata.csv` (T006c) for difficulty labels.
 - *Output*: Log excluded games to `data/processed/excluded_games.log`.

- [X] T031 [US3] Add checkpointing after model fitting for resumption (Plan: Phase 2 Step 5)
 - *Dependency*: Requires `code/scripts/utils/checkpoint.py` (T008a) to be created.

### Tests for User Story 3 (Mandatory per Spec) ⚠️

- [X] T025 [P] [US3] Contract test for model output structure in `code/tests/test_models.py`

- [X] T026 [P] [US3] Integration test for model convergence and VIF < 5 check in `code/tests/test_models.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T032 [P] Documentation updates: Add `quickstart.md` with data fetching and analysis instructions

- [X] T033c [P] Verify core scripts exist:
 - **Action**: Check that `code/scripts/fetch_data.py` and `code/scripts/preprocess.py` exist and are non-empty.
 - **Verification**: Assert that both files exist and have a line count > 0. If not, fail the task.
 - *Note*: This task MUST pass before T033a and T033b can proceed.

- [X] T033a [P] Code cleanup and refactoring: Refactor pagination logic in `fetch_data.py` for readability <!-- ATOMIZE: requested -->
 - *Dependency*: **MUST** run after T033c (Verify core scripts exist).
 - *Action*: Extract the pagination loop logic from `fetch_data.py` into a new function `fetch_paginated_data` in `code/scripts/utils/pagination.py`.
 - *Verification*: (See T033a-verify).

- [X] T033a-verify [P] Verify pagination refactoring:
 - *Action*: Run `pytest code/tests/test_pagination.py::test_pagination_readability` which asserts that the cyclomatic complexity of the main function in `fetch_data.py` has decreased by at least 2 and the line count of the main function has decreased by at least 10 lines.

- [X] T033b [P] Code cleanup and refactoring: Extract function `calculate_lagged_pressure` from `preprocess.py`
 - *Dependency*: **MUST** run after T033c (Verify core scripts exist).
 - *Action*: Extract the `calculate_lagged_pressure` logic from `preprocess.py` into a new function in `code/scripts/utils/pressure.py`.
 - *Verification*: (See T033b-verify).

- [X] T033b-verify [P] Verify lagged pressure extraction:
 - *Action*: Run `pytest code/tests/test_pressure.py::test_lagged_calc` which asserts that the function `calculate_lagged_pressure` exists, has the correct signature, and produces the expected output for a mock dataset.

- [X] T034a [P] Create memory log file:
 - **Action**: Create `data/checkpoints/memory_log.txt` to store memory profiling results.

- [X] T034b [P] Performance optimization: Ensure memory usage < 7 GB and disk < 14 GB (SC-005)
 - *Dependency*: Requires `data/checkpoints/memory_log.txt` (T034a) to exist.
 - *Strategy*: If data exceeds limits, implement a strategy explicitly defined in the spec (e.g., excluding games with <100 runs) or fail with clear error. Do NOT use unauthorized downsampling.
 - *Verification*: Run the pipeline with a memory profiler using command `python -m memory_profiler code/scripts/main.py` and verify the peak memory usage recorded in `data/checkpoints/memory_log.txt` is < 7 GB. Peak memory is defined as the maximum value recorded in the log. If not, implement spec-defined exclusion logic.

- [X] T035 [P] Additional unit tests for edge cases (e.g., empty datasets, API rate limits)

- [X] T038 [P] Apply Global Bonferroni Correction:
 - *Dependency*: **MUST** run after T020 (US2) and T027 (US3) to aggregate all p-values.
 - **Role**: Finalization step required to complete the statistical rigor of US2 and US3. US2 and US3 produce intermediate results, but their final statistical outputs (corrected p-values) are only available after T038.
 - Aggregate total hypothesis test count from US2 (T020) and US3 (T027) and apply correction to all p-values using `utils/bonferroni.py` (T008b) (FR-008, SC-004)
 - **Filter Logic**: Filter `distribution_fits.csv` for rows where `KS_pvalue IS NOT NULL AND distribution_family != 'descriptive'` and `model_results.csv` for rows where `p_value IS NOT NULL`. **CRITICAL**: Include ALL hypothesis tests (including those with p < 0.05) in the divisor count to strictly control the family-wise error rate.
 - *Input*: All valid p-values from `data/processed/distribution_fits.csv` and `data/processed/model_results.csv`.
 - *Verification*: Verify that `paper/draft.md` and `data/processed/model_results.csv` contain p-values that are exactly equal to `min(unity, raw_p * total_test_count)` where `total_test_count` is the sum of ALL tests from US2 and US3 (including rejections).
 - *Output*: Updated p-values in final report (`paper/draft.md`) and corrected result files.

- [X] T036 Run `hash_artifacts.py` to finalize state and checksums (Constitution Principle V)

- [X] T037 Run quickstart.md validation to ensure all steps execute correctly on CI

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires clean data from US1 but independent of US2 results
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires clean data from US1; independent of US2 results
 - *Note*: US3 requires `data/processed/run_records.csv` (produced by US1)
 - *Note*: US3 requires `lagged_competitive_pressure` column from T014 (US1). **T014 is a hard prerequisite for T027.**
 - *Note*: US3 requires `data/processed/game_metadata.csv` (produced by T016a in US1).

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Contracts before Services/Scripts
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2) **EXCEPT T006b (config creation) which depends on T006a, and T016a (metadata) which depends on T006 (config content).**
- Once Foundational phase completes, US1 and US2 can start in parallel (if team capacity allows).
- **US3 (T027) CANNOT start until T014 (US1) is complete.**
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members (subject to dependencies).

---

## Parallel Example: User Story 1

```bash
# Launch all models for User Story 1 together:
Task: "Create run_record.schema.yaml in contracts/"
Task: "Create distribution_fit.schema.yaml in contracts/"

# Note: Tests T010 and T011 cannot run in parallel with T012 (fetch) due to dependencies.
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
 - Developer A: User Story 1 (Data)
 - Developer B: User Story 2 (Distribution)
 - Developer C: User Story 3 (Modeling) **BUT Developer C must wait for T014 (US1) to complete before starting T027.**
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
- **CRITICAL**: All statistical claims must be associational; no causal language (FR-010, SC-006).
- **CRITICAL**: Ensure all tasks are CPU-tractable (no GPU, no large models) per SC-005.
- **CRITICAL**: Bonferroni correction (FR-008) is applied globally in T038 after all tests are complete, including all tests in the divisor count.