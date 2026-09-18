---
description: "Task list template for feature implementation"
---

# Tasks: Assessing the Sensitivity of Regression Coefficients to Dataset Subset Selection

**Input**: Design documents from `/specs/001-sensitivity-regression-coefficients/`  
**Prerequisites**: plan.md (required), spec.md (required for user stories), data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)  
- Include exact file paths in descriptions
- **[Dep: T###]**: Explicit dependency on another task ID

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root  
- **Web app**: `backend/src/`, `frontend/src/`  
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`  

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 [P] **Project Initialization & Configuration**: Create all required directories (`src/ingestion`, `src/resampling`, `src/analysis`, `src/utils`, `tests/unit`, `tests/integration`) and their `__init__.py` files. Create `requirements.txt` with pinned dependencies, `.ruff.toml`, `pyproject.toml` (black config), `.pre-commit-config.yaml`, and `.gitignore` with specific patterns for data/artifacts. **Deliverable**: All directories, config files, and init files exist and are tracked in git.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin.  
**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T002 [P] Create `.gitkeep` files to all newly created empty directories to ensure they are tracked.  
- [X] T003 [P] Implement utility module for checksumming (MD5) and validation in `src/utils/validation.py`.  
- [X] T004 [P] Setup environment configuration management (loading dataset lists, random seeds, sample size tiers) in `src/utils/config.py`. **Rule**: Sample size tiers must be read from config, not hardcoded, with the lowest tier representing a minimal cohort size. **Note**: The tier values must match the "Research Design Parameters" section of `spec.md`.  
- [X] T005 [P] Create base data models (Pydantic/TypedDict) for `DatasetProfile`, `StabilityResult`, `InteractionModel` in `src/models/data_models.py`.  
- [X] T006 [P] Configure error handling and logging infrastructure (structured logs to `artifacts/run.log`) in `src/utils/logger.py`.  
- [X] T007 [P] Implement checkpoint mechanism (save/load JSON state) in `src/utils/checkpoint.py` defining the **schema** for checkpoint state that T024 will consume to prevent schema drift. **Schema Fields**: Must include `dataset_id`, `tier`, `predictor`, `sd_value`, `subset_indices`, `tier_id`, `cond_num`, `bp_p_value`, `cooks_d`. **Constraint**: The schema must support a **list** of metrics (one per subset) for each tier, as T024 generates 200 subsets per tier. The fields `cond_num`, `bp_p_value`, and `cooks_d` are **per‑subset** values, not aggregate tier values. **Structure**: The checkpoint JSON must be a list of objects, where each object represents one subset: `[{"subset_id": 1, "cond_num": 12.5, "bp_p_value": 0.03, "cooks_d": 0.001, ...}, ...]`. **Deliverable**: Checkpoint schema definition and save/load functions.  
- [X] T008 [P] **Create `config.yaml`** containing:
  - Verified dataset identifiers (e.g., `UCI_Auto`, `HuggingFace_California_Housing`).
  - Random seed (pinned for reproducibility).
  - Sample size tier percentages: `[10, 25, 50, 75, 90]` (matching spec "Research Design Parameters").
  - Number of subsets per tier: `200`.
  - Convergence threshold: `0.05` (5%).
  - Other global parameters.  
  **Location**: `config.yaml` at repository root.  
- [X] T008a [P] **Populate `config.yaml` verified dataset list**: Explicitly add the specific dataset identifiers `UCI_Auto` and `HuggingFace_California_Housing` to the `verified_dataset_identifiers` list in `config.yaml` to ensure T012 has a valid source. **Rule**: Do not leave this list empty or with placeholders.  
- [X] T009 [P] **Validate `config.yaml` contents** in `src/utils/config.py`:
  - Ensure tier percentages are a list of five integers that sum to ≤ 100.
  - Verify that the list exactly matches the spec's "Research Design Parameters" `[10, 25, 50, 75, 90]`.
  - Raise a clear `ConfigValidationError` if mismatched.  
- [X] T039 [P] **Create `contracts/` directory and populate with required contract files** (e.g., `data_contract.yaml`, `model_contract.yaml`). Ensure contracts are version‑controlled and referenced from the documentation.  
- [X] T040 [P] **Author `quickstart.md`** documenting step‑by‑step pipeline execution, including environment setup, config usage, and expected artifacts. Place under `docs/quickstart.md`.  
- [X] T051 [P] **Unit test for checkpoint schema compliance**: Verify that a checkpoint saved via `src/utils/checkpoint.py` validates against the schema defined in T007, raising a `SchemaValidationError` on mismatch. This task tests the schema validator logic itself. **Dependency**: After T007.  
- [X] T067 [P] [US1] **Enforce "Fail Loudly" Data Loading**: Modify `src/ingestion/downloader.py` to remove any `try/except` blocks or `if download_failed` logic that falls back to `generate_synthetic_*()` or `mock_*()` functions. If `datasets.load_dataset` or the HTTP fetch fails, the script must raise `DataFetchError` immediately and terminate. **Rationale**: Prevents silent substitution of real data with synthetic data, which triggers the fabrication gate. **Dependency**: Before T012.  
- [X] T068 [P] [US1] **Implement Chunked Streaming for Large Datasets**: In `src/ingestion/profile.py`, ensure that for datasets > 7GB, the `profiler` processes data in chunks (e.g., A dataset of substantial scale comprising multiple rows.) using `datasets.load_dataset(..., streaming=True)` and iterates to accumulate `X'X` for Condition Number and sufficient statistics for Breusch-Pagan, rather than loading the full DataFrame. **Rationale**: Ensures compliance with the 7GB RAM constraint on the free runner. **Dependency**: Before T014.  
- [X] T069 [P] [US2] **Verify Subset-Specific Metric Calculation**: In `src/resampling/engine_metrics.py`, add a pre-flight assertion that `cond_num`, `bp_p_value`, and `cooks_d` are computed **only** from the subset data provided to the function, not from a global or full-dataset cache. **Rationale**: Prevents circular derivation where subset stability is predicted by full-dataset properties. **Dependency**: Before T054.

---

## Phase 3: User Story 1 - Data Ingestion and Violation Profiling (Priority: P1) 🎯 MVP

**Goal**: Ingest verified numerical datasets, profile OLS assumption violations (Breusch‑Pagan, Cook’s Distance, Condition Number), and ensure memory compliance.

**Independent Test**: Run ingestion script on a single known dataset (e.g., `Auto` from UCI) and verify output JSON contains valid, non‑null values for `breusch_pagan_stat`, `max_cooks_distance`, and `condition_number`.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T010 [P] [US1] Unit test for `DatasetProfile` schema validation in `tests/unit/test_profiler.py` implementing function `test_dataset_profile_rejects_null_bp_stat` with assertion that `ValidationError` is raised with message `'breusch_pagan_stat cannot be null'`. **Dependency**: After T005.  
- [X] T011 [P] [US1] Integration test for dataset download and checksum verification in `tests/integration/test_downloader.py` using the 'Auto' dataset from UCI. The test must compute the MD checksum of the downloaded file dynamically and assert it is a valid non‑empty hex string, rather than hardcoding a specific value. **Dependency**: After T005.  
- [X] T013 [P] [US1] Unit test for `profiler.py` ensuring that the computed condition number is finite and > 1 on a small real dataset (e.g., the first 200 rows of `Auto`). **Dependency**: After T014.

### Implementation for User Story 1

- [X] T012 [P] [US1] Implement `downloader.py` in `src/ingestion/` to fetch datasets from verified HuggingFace/UCI URLs using `datasets.load_dataset(..., streaming=True)`. **Rule**: Strictly use the verified dataset list from `config.yaml`. **Rule**: Fail loudly on fetch error; no synthetic fallback. **Constraint**: If dataset > 7 GB, implement a chunked iterator (A moderate number of rows per block) to accumulate statistics without loading full dataset. Raise a specific `DataFetchError` if download fails. **Dependency**: After T067.  
- [X] T014 [US1] Implement `profiler.py` in `src/ingestion/` to compute Condition Number, Breusch‑Pagan statistic, and Cook's Distance. **Constraint**: If streaming is used, implement a chunked iterator (10 k rows per block) to accumulate sums of squares for CondNum (via cross‑product matrix accumulation: `X'X += chunk.T @ chunk`) and BP test statistics (accumulate residuals and squared residuals per chunk) without loading full dataset. **Algorithm**: For streaming CondNum, accumulate `X'X` in chunks, then compute SVD on the final accumulated matrix. For BP, accumulate `residuals` and `residuals^2` to compute the auxiliary regression on the fly. **Deliverable**: `DatasetProfile` JSON artifact written to `artifacts/profiles/`. **Dependency**: After T068.  
- [X] T015 [US1] Implement logic in `src/ingestion/profiler.py` to classify violation severity (Low/Medium/High) based strictly on Breusch‑Pagan p‑values (Spec thresholds: Low > 0.10, Medium 0.05 – 0.10, High ≤ 0.05). **Rule**: Do NOT mix collinearity severity into this classification.  
- [X] T020 [P] [US1] Create `src/ingestion/__init__.py` to expose an `ingest_and_profile` pipeline that outputs a `DatasetProfile` JSON to `artifacts/profiles/`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently.

---

## Phase 4: User Story 2 - Subset Resampling and Stability Estimation (Priority: P2)

**Goal**: Generate random observation subsets across multiple sample size tiers, fit OLS models, and compute empirical standard deviation of coefficients.

**Independence Note**: This pipeline operates **independently** of the US1 profiling output; it does **not** consume `DatasetProfile` artifacts and derives all required metrics per subset.

**Independent Test**: Run resampling module on a small fixed dataset (N = 500) with a fixed seed, verify multiple subsets generated (distributed across tiers), OLS fits complete, and coefficient variance is a positive float.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T021 [P] [US2] Unit test for singularity detection (skip fit if condition number infinite) in `tests/unit/test_resampling.py` using input data with a fixed two‑dimensional shape and condition number > 1e15, expecting a specific `LinAlgError`.  
- [X] T022 [P] [US2] Integration test for resampling loop completion and artifact generation in `tests/integration/test_resampling.py` verifying that multiple subsets are generated per tier, OLS models fit successfully, and `coefficient_sd.json` contains positive float values for standard deviations.  
- [X] T025a [P] [US2] Unit test for config parsing: Verify `config.yaml` tier list is exactly `[10, 25, 50, 75, 90]`. **File**: `tests/unit/test_config.py`, **Function**: `test_tier_values_match_spec`.  
- [X] T025b [P] [US2] Unit test for config parsing: Verify `config.yaml` subsets per tier is `200`. **File**: `tests/unit/test_config.py`, **Function**: `test_subsets_per_tier_is_200`.  
- [X] T026 [P] [US2] Unit test for the bootstrap convergence loop confirming that, for a known small dataset, the computed SE of the SD is < 5 % of the SD. **File**: `tests/unit/test_bootstrap.py`, **Function**: `test_convergence_threshold_check`.

### Implementation for User Story 2

- [X] T023 [P] [US2] **Subset Generation**: Implement `generator.py` in `src/resampling/` to generate random subset index files per dataset across tiers. **Rule**: Read tier percentages **exclusively** from `config.yaml`. **Constraint**: No hard‑coded tier values. Save each subset's index list to `artifacts/stability/subsets_{dataset_id}_{tier}.json`.  
- [X] T054 [P] [US2] **Per‑Subset Metric Computation**: In `src/resampling/engine_metrics.py`, compute Condition Number, Breusch‑Pagan p‑value, and Cook's Distance for each generated subset and store them alongside subset identifiers. **Input**: Read subset indices from `artifacts/stability/subsets_*.json` generated by T023. **Output**: Return a list of dictionaries containing `subset_id`, `cond_num`, `bp_p_value`, `cooks_d`. **Dependency**: After T023, T069.  
- [X] T055 [P] [US2] **OLS Fitting Loop**: In `src/resampling/engine_fit.py`, fit OLS models on each subset, capture coefficient vectors, and handle singularity errors gracefully (log and skip). **Input**: Read subset indices from `artifacts/stability/subsets_*.json` generated by T023. **Dependency**: After T023.  
- [X] T056 [P] [US2] **Bootstrap Convergence Check**: In `src/resampling/bootstrap.py`, resample the 200 coefficient‑SD estimates per tier to compute the SE of the SD and verify it is < 5 % of the SD. Log results to `artifacts/convergence.log`.  
- [X] T057 [P] [US2] **Artifact Generation**: Consolidate results into:
  - `artifacts/stability/coefficient_sd.json` (schema: `dataset_id`, `tier`, `predictor`, `sd_value`)
  - `artifacts/stability/stability_result.json` (schema: `dataset_id`, `tier`, `subset_id`, `cond_num`, `bp_p_value`, `cooks_d`, `sd_value`) **CRITICAL**: Must include per-subset metrics computed in T054.
  - `artifacts/stability/convergence_analysis.json` (schema: `n_sd`, `m_sd`, `delta`)
  - `artifacts/stability/convergence_status.json` (schema: `{"dataset_id": "...", "tier": 10, "status": "PASS/FAIL", "se_value": 0.05, "n_subsets": 200}`)
  - **Checkpoint Integration**: Write the per-subset metrics (CondNum, BP, Cook's) into the checkpoint format defined in T007 for persistence.
  **Dependency**: After T054, T055, T056.  
- [X] T058 [P] [US2] **Convergence Verification Implementation**: Implement the logic in `src/resampling/convergence.py` to explicitly write `artifacts/stability/convergence_status.json`. If the SE of SD >= 5%, the script must raise a `ConvergenceError` to halt the pipeline. **Dependency**: After T056.  
- [X] T024 [P] **Resampling Orchestrator**: Create `src/resampling/__init__.py` exposing a `run_resampling_experiment` pipeline that sequentially calls T023, T054‑T058. The orchestrator does **not** require the full‑dataset `DatasetProfile`; it operates solely on subset‑specific data.  

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently.

---

## Phase 5: User Story 3 - Interaction Analysis and Sensitivity Visualization (Priority: P3)

**Goal**: Run multiple regression with interaction terms, visualize sensitivity effects, and frame findings associatively.

**Independent Test**: Run analysis script on aggregated results, verify regression model includes interaction term (Condition Number × Violation Severity), and plot is generated.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T029 [P] [US3] Unit test for interaction term calculation and p‑value extraction in `tests/unit/test_regression_analysis.py` implementing function `test_interaction_term_pvalue_extraction` with expected p‑value range within valid statistical bounds.  
- [X] T030 [P] [US3] Integration test for full meta‑analysis pipeline in `tests/integration/test_full_pipeline.py`.  
- [X] T058 [P] **Unit test for interaction term presence**: Verify that the fitted `InteractionModel` JSON contains the `severity:cond_num` interaction coefficient and that its p‑value is recorded.

### Implementation for User Story 3

- [X] T031 [US3] **Multiple Regression (HLM)**: Implement `meta_analysis.py` in `src/analysis/` to perform **Multiple Regression with interaction terms** (Spec FR‑005) with `sd_value` as outcome.
  - Formula: `sd_value ~ C(severity) * cond_num + bp_p_value + (1|dataset_id)`
  - `severity` derived from `bp_p_value` thresholds defined in T015 (Low > 0.10, Medium 0.05‑0.10, High ≤ 0.05).
  - **Non‑Circularity Guard**: Use **subset‑specific** `cond_num` and `bp_p_value` from `artifacts/stability/stability_result.json`. **FORBIDDEN**: Full‑dataset metrics as predictors.
  - **Library**: Use `statsmodels` `MixedLM` with `re_formula='(1|dataset_id)'`. Reference level for `severity` must be "Low".
  - Pre‑flight: Verify `artifacts/stability/convergence_status.json` exists and contains `'PASS'` for the target dataset/tier before running.
  **Dependency**: After T056, T057.
  **Deliverable**: `InteractionModel` JSON written to `artifacts/meta_analysis/interaction_model.json`.  
- [X] T032 [US3] **Visualization**: Implement visualization module in `src/visualization/curves.py` to generate plot `artifacts/meta_analysis/stability_curves.png` using `matplotlib`, plotting `coefficient_std_dev` vs `condition_number` for each `violation_severity` group, including confidence intervals derived from multiple subsets.  
- [X] T033 [US3] **Report Generator**: Implement report generator in `src/analysis/` to produce `artifacts/meta_analysis/final_report.md` containing a summary of the interaction‑term p‑value and an explicit statement that findings are associational. **Requirement**: Extract the specific p-value for the `severity:cond_num` interaction term from `InteractionModel` and format it into a sentence: "The interaction between violation severity and condition number was found to be [significant/not significant] (p = X.XXX), suggesting that coefficient stability is associatively linked to dataset quality."  
- [X] T034 [US3] Create `src/analysis/__init__.py` to expose a `run_meta_analysis` pipeline that outputs the `InteractionModel` JSON to `artifacts/meta_analysis/interaction_model.json` with schema validation.  
- [X] T043 [P] **Non‑Circular Derivation Audit**: Add a verification script `src/analysis/audit_non_circular.py` that scans `artifacts/meta_analysis/interaction_model.json` and ensures no predictor fields reference full‑dataset metrics. The script fails the pipeline if any such reference is found, satisfying Constitution Principle VII.  
- [X] T059 [P] **Verification Task for Non‑Circular Derivation**: Add a task that runs `src/analysis/audit_non_circular.py` after the meta‑analysis step and records the audit result in `artifacts/meta_analysis/audit_log.json`. This task explicitly enforces the constitution's non‑circular derivation requirement.  

**Checkpoint**: All user stories should now be independently functional and constitutionally compliant.

---

## Phase 6: Convergence Verification & Polish

**Purpose**: Final verification of success criteria and cross‑cutting improvements

- [X] T063 [P] Update `README.md` with CLI usage examples including `python -m src.cli --config test_config.yaml`.  
- [X] T064 [P] Update `docs/quickstart.md` with detailed pipeline execution steps.  
- [X] T065 [P] Verify `README.md` contains correct artifact paths for all outputs by comparing against generated artifacts.  
- [X] T066 [P] Refactor error handling in `src/ingestion/downloader.py` to use custom exception classes.  
- [X] T041 [P] Execute `python -m src.cli --config test_config.yaml` and verify completion time < 6 hours on a ‑core CPU runner.  
- [X] T042 [P] Run `scripts/verify_hashes.py` to ensure all files in `artifacts/` have corresponding entries in `state.yaml` with matching MD5 hashes.  
- [X] T070 [P] **Execute Data Integrity Audit**: Create a script `scripts/audit_data_integrity.py` that runs after T012 and T023 to verify that no `artifacts/` file contains synthetic data markers (e.g., `is_synthetic: true` or random seeds used for generation). **Rationale**: Proactive check before the execution gate runs. **Dependency**: After T042.

---

## Phase 7: Data Integrity & Execution Safety (Moved to Phases 2-6)

**Note**: Tasks T067-T070 have been moved to their respective prerequisite phases (2, 3, 4, 6) to ensure foundational tasks are implemented correctly from the start. This phase is now empty.