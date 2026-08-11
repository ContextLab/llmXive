# Tasks: Assessing Dataset Imbalance Effects on Materials Property Predictions

**Input**: Design documents from `/specs/001-assess-dataset-imbalance-effects/`
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

- [X] T001 [P] Create project directory structure: `projects/PROJ-756-assessing-dataset-imbalance-effects-on-m/` including `data/`, `code/`, `tests/`, `artifacts/`, `results/`, `state/`, `logs/`, `logs/archive/`. **MUST create placeholder files**: `__init__.py` in all directories, `.gitkeep` in data subdirs, `requirements.txt` in `code/`, and a `run.sh` entry point script in the root to ensure the project is immediately runnable per Constitution Principle I.
- [X] T001b [P] Implement `code/main.py` entry point with CLI arguments `--full-pipeline`, `--include-mp`, `--fallback-mode`. **Must parse arguments and orchestrate the full pipeline flow.** (FR-001, FR-008).
- [X] T002 Initialize Python 3.11 project with pinned dependencies in `code/requirements.txt` (pandas, scikit-learn, shap, magpie, datasets, numpy, scipy, pyyaml, cvxpy)
- [X] T003 [P] Configure linting (ruff/black) and formatting tools in root `pyproject.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. **Foundation is READY ONLY AFTER T006b-DataFetch, T006d-DataFetch-MP, T007, T007b, T008a, T008b, T006c, T004a, T004b, T004c, T006a are complete.**

- [ ] T004a-Backoff [P] Implement `code/ingestion.py` logic for **API ingestion with exponential backoff** for OQMD, AFLOW, and Materials Project APIs. **Parameters**: base_delay=1s, max_delay=60s, multiplier=2.0, max_retries=5. **Log all API errors as JSON lines to `logs/api_errors.log`** with schema `{"timestamp":..., "endpoint":..., "error":..., "retry_count":...}`. (FR-007, FR-008). **Depends on T006a for MP availability flag.**
- [ ] T004a-LogSchema [P] Implement `code/ingestion.py` logic for **logging API errors** with the specific JSON schema defined in T004a-Backoff. **Ensure JSON lines format is strictly followed.** (FR-007). **Depends on T004a-Backoff.**
- [X] T004b [P] Implement `code/ingestion.py` logic for **size-based log rotation** (create new file if > 100MB) without deletion to preserve raw trace. **Depends on T004a-Backoff.**
- [X] T004c [P] Implement `code/ingestion.py` logic for **Fail Loudly**: raise `DataFetchError` on persistent failure for OQMD/AFLOW; for Materials Project, if persistent failure occurs after retries, log a warning and switch to fallback mode (OQMD/AFLOW only) as per FR-008, ensuring no synthetic fallback. **Depends on T004a-Backoff.**
- [X] T004 [X] **DEPRECATED**: Split into T004a-Backoff, T004a-LogSchema, T004b, T004c.
- [ ] T006a-MP-Availability-Check [P] Implement `code/ingestion.py` logic to **detect Materials Project API availability** by attempting a lightweight probe request using the configured API key. **If the key is missing or the probe fails (403/timeout), set a global flag `MP_AVAILABLE = False` and log a warning.** **This task ensures FR-008 fallback logic is triggered before ingestion begins.** (FR-008). **Must be completed BEFORE T004a-Backoff.**
- [ ] T006b-DataFetch [P] Implement `code/downloaders.py` to download OQMD dataset **to `data/raw/oqmd.parquet`** using the **official OQMD REST API** with exponential backoff. **Do NOT use Hugging Face datasets library for this specific API.** Ensure directory exists: `mkdir -p data/raw`. (FR-001, FR-007, FR-008). **Depends on T004a-Backoff (interface) and T004c (error handling).**
- [ ] T006d-DataFetch-MP [P] Implement `code/downloaders.py` to download Materials Project dataset **to `data/raw/mp.parquet`** if `MP_AVAILABLE` is True. **Use the official Materials Project REST API** with exponential backoff. **If `MP_AVAILABLE` is False, skip this task and log a warning.** (FR-001, FR-008). **Depends on T004a-Backoff (interface), T004c (error handling), and T006a.**
- [ ] T006c-Checksums [P] Implement checksum verification in `code/downloaders.py` using **SHA‑256 algorithm**, generating checksum files **`data/raw/oqmd.parquet.sha256`, `data/raw/aflow.parquet.sha256`, and `data/raw/mp.parquet.sha256` (if MP exists)** in `sha256sum` format (`<hash> <filename>`). **Update `state/projects/PROJ-756-assessing-dataset-imbalance-effects-on-m.yaml` with the generated checksums in the `artifact_hashes` map. Verify the YAML structure explicitly matches the `artifact_hashes` map format; raise ValueError if key missing or structure mismatch.** (Constitution Principle III). **Sequential to T006b-DataFetch and T006d-DataFetch-MP; parallel to other Phase 2 tasks.**
- [X] T007 [P] Implement `code/descriptors.py` to compute all Magpie compositional descriptors (L‑normalized) and save to `data/processed/descriptors.parquet` (FR‑002).
- [ ] T007b-Schema-Extraction [P] Implement `code/descriptors.py` to **extract the schema (column names, count)** from `data/processed/descriptors.parquet` and save it as `data/processed/descriptor_schema.json`. **This artifact is required for T036 to generate the synthetic ground truth.** (FR-014). **Depends on T007.**
- [ ] T008a [P] Implement `code/imbalance.py` to calculate **Target Imbalance Score** (Gini coefficient of target property values for properties with >= 100 samples, handling negative values via absolute transformation or offset). Skip properties with < 100 samples. Output to `results/target_imbalance_scores.csv` (FR‑011). **Depends on T006b-DataFetch, T006d-DataFetch-MP, T007.**
- [ ] T008b [P] Implement `code/imbalance.py` to calculate **Compositional Imbalance Score** (Gini coefficient of the **cluster assignment counts** derived from K-Means clustering with k=50 on compositional features). **Step 1: Perform K-Means clustering (k=50) on compositional features to project data into 50-dimensional cluster space. Step 2: Calculate Gini coefficient of the frequency of samples assigned to each cluster (cluster assignment counts) to quantify feature space diversity.** **Load feature matrix from `data/processed/descriptors.parquet`.** Output to `results/compositional_imbalance_score.csv` (FR‑002). **Note: This task implements Spec FR-002, which supersedes the Plan's "Convex Hull" rejection.** **Depends on T006b-DataFetch, T006d-DataFetch-MP, T007.**
- [X] T010 [P] Create unit tests for ingestion retry logic and API failure handling in `tests/unit/test_ingestion.py`.
- [X] T011 [P] Create unit tests for Magpie descriptor computation in `tests/unit/test_descriptors.py`.
- [X] T010b [P] Generate `contracts/dataset.schema.yaml` defining the schema for `data/processed/` (columns: composition, target properties, descriptors, imbalance scores) (FR‑001).
- [X] T010c [P] Generate `contracts/resampling.schema.yaml` defining the schema for resampled datasets (columns: bin_id, sample_count, CV, real_data_flag, synthetic_flag) (FR‑003). **Must be completed before T020.**
- [X] T012 [US1] Contract test for data schema validation in `tests/contract/test_dataset_schema.py` (validates `data/processed/` against `contracts/dataset.schema.yaml`). *Depends on T010b.*
- [X] T013 [P] Integration test for baseline pipeline in `tests/integration/test_baseline_pipeline.py` (runs ingestion → descriptors → baseline training → report).
- [X] T014 [US2] Contract test for resampling schema validation in `tests/contract/test_resampling_schema.py` (validates CV constraints against `contracts/resampling.schema.yaml`). *Depends on T010c.*
- [X] T015 [P] Integration test for statistical significance in `tests/integration/test_statistical_significance.py` (validates power analysis and p‑value calculation).
- [X] T049 Implement strict error handling in `code/downloaders.py` and `code/ingestion.py`: **raise a specific `DataFetchError` exception on any persistent fetch failure for OQMD/AFLOW after retries**, ensuring no synthetic fallback code paths exist (Constitution Principle II, "Fail Loudly" rule). **Preserve exponential backoff and retry logic. For MP, implement fallback logic as per FR-008.** **Depends on T004a-Backoff, T004c, T006b-DataFetch, T006d-DataFetch-MP.**
- [X] T050 [P] [US1/US2] Add a verification script `code/verify_no_synthetic_fallback.py` that scans `code/downloaders.py`, `code/resampling.py`, and `code/ingestion.py` for patterns indicating synthetic fallback (e.g., `if not data: return mock_data`, `except: return synthetic`) and fails the build if found. **Depends on T004a-Backoff, T004c, T006b-DataFetch, T006d-DataFetch-MP.**
- [X] T051 [P] [US2] Implement explicit logging in `code/resampling.py` when SMOTE is triggered as a fallback, logging the **exact percentage of synthetic data added** and the **resulting CV** to `results/resampling_log.json` to ensure compliance with FR-013 (Synthetic data ≤ 30%) and FR-003 (Combined CV ≤ 0.30). **Verify that the hard validation gate in T023 raises a ValidationException if the synthetic portion exceeds 30%.** **Depends on T023.**

### Checkpoint
**Foundation ready ONLY after T006b-DataFetch, T006d-DataFetch-MP, T007, T007b, T008a, T008b, T006c, T004a-Backoff, T004a-LogSchema, T004b, T004c, T006a are complete** – user story implementation can now begin in parallel.

---

## Phase 3: User Story 1 - Quantify Imbalance and Generate Baseline Predictions (Priority: P1) 🎯 MVP

**Goal**: Download datasets, compute descriptors, train baseline RF/GB models on skewed data, and generate baseline performance report.

**Independent Test**: Can be fully tested by running `code/ingestion.py`, `code/descriptors.py`, and `code/training.py` (baseline mode) to produce a CSV report with MAE, RMSE, R² for skewed data.

### Tests for User Story 1 (Contract & Integration) ⚠️

- [X] T012 [US1] Contract test for data schema validation (already defined above).
- [X] T013 [US1] Integration test for baseline pipeline (already defined above).

### Implementation for User Story 1

- [X] T014 [US1] Implement `code/training.py` to train Random Forest and Gradient Boosting regressors on skewed data (FR‑004).
- [X] T015 [US1] Implement `code/training.py` to evaluate models on a stratified test set preserving original imbalance (FR‑004).
- [X] T016 [US1] Implement `code/evaluation.py` to generate **baseline performance report** saved as `results/baseline_report.csv` with columns: `property, model_type, MAE, RMAE, R2` (FR-004).
- [X] T019 [US1] Verify that contract tests T012 and integration test T013 **pass before** baseline report generation (requires T012/T013 completion prior to T016). **Scheduling constraint: MUST be executed only after T012 and T013 are marked complete.**

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently.

---

## Phase 4: User Story 2 - Apply Resampling and Measure Performance Degradation (Priority: P2)

**Goal**: Apply stratified resampling (or fallback), retrain models, and statistically compare performance on the minority subset.

**Independent Test**: Can be fully tested by running the resampling pipeline, producing a comparison table and statistical test results (paired t‑test/Wilcoxon) showing performance difference on the bottom [MINORITY_QUANTILE] subset.

### Tests for User Story 2 (Contract & Integration) ⚠️

- [X] T020 [US2] Define Contract test for resampling logic in `tests/contract/test_resampling_logic.py` (validates CV constraints against `contracts/resampling.schema.yaml`). **Validates output of T023.** **Depends on T010c (schema generation) and T023 (implementation).**
- [X] T021 [US2] Define Integration test for statistical significance in `tests/integration/test_statistical_significance_logic.py` (validates power analysis and p‑value calculation). **Depends on T029.**

### Implementation for User Story 2

- [X] T023 [US2] Implement `code/resampling.py` with stratified undersampling/oversampling using **equal‑frequency binning into 20 bins** (default) and ensure **real‑data CV ≤ 0.10**. **Fallback Logic**: If >20% data loss or empty bins occur, **first switch to cost-sensitive learning (class_weight='balanced')**. If that fails to meet CV ≤ 0.10, **then switch to SMOTE for regression**. Enforce **combined CV ≤ 0.30** while still keeping real‑data CV ≤ 0.10. **Implement hard validation gate raising `ValidationException` if synthetic data > 30% (FR-013).** **Note: This task implements Spec FR-003 (SMOTE as fallback), which supersedes Plan.md initial 'SMOTE excluded' note.** (FR-003, US-2 Edge Cases). **Depends on T008a, T008b.**
- [X] T024 [US2] Enforce the CV constraints described above (real ≤ 0.10, combined ≤ 0.30) within the resampling implementation.
- [X] T025 [US2] Implement `code/training.py` to retrain RF and GB models on the balanced dataset with identical hyperparameters (FR‑004).
- [X] T026-MinoritySubset [US2] Implement `code/evaluation.py` to **isolate the bottom [deferred] (MINORITY_QUANTILE) of each target property** using **Jenks Natural Breaks (k=5) with seed=42** derived from the **FULL dataset** distribution (FR‑010) and calculate per‑bin MAE for this subset. **Document the justification for the chosen threshold in `results/minority_threshold_justification.md`.** (FR-010). **Depends on T008a.**
- [X] T027 [US2] Implement `code/evaluation.py` to calculate **performance degradation**: `MAE_skewed_minority - MAE_balanced_minority` and write to `results/performance_degradation.csv`.
- [X] T028 [US2] Implement power analysis in `code/evaluation.py` to determine the minimum number of random seeds required for **paired t-test**, Cohen's d = 0.5, power ≥ 0.8, α = 0.05; output seed count to `results/power_analysis.json`.
- [X] T029 [US2] Implement paired statistical tests (paired t‑test or Wilcoxon) across the seed count from T028 (**Read seed_count from results/power_analysis.json**), saving results to `results/statistical_test_results.csv` with columns `test_type, p_value, effect_size, seed_count` (FR‑005). **Sequential dependency: T029 MUST run after T028 completes.**
- [X] T030 [US2] Compute Pearson correlation between **Compositional Imbalance Score** (from T008b) and **performance degradation** (from T027); output to `results/correlation_analysis.csv` with columns `property, score_type, r, p_value` (FR‑012).
- [X] T031 [US2] Compute Pearson correlation between **Target Imbalance Score** (from T008a) and **performance degradation**; append results to the same `results/correlation_analysis.csv` (FR‑012).
- [X] T032 [US2] Generate comparison report `results/comparison_report.csv` with columns `property, metric, skewed_value, balanced_value, delta_pct, p_value, effect_size` (US‑2).
- [X] T033 [US2] Verify that contract test T020 and integration test T021 pass after resampling implementation.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently.

---

## Phase 5: User Story 3 - Analyze Feature Importance Distortion via SHAP (Priority: P3)

**Goal**: Generate SHAP values, compare top-ranked feature rankings, and validate against a synthetic ground‑truth baseline.

**Independent Test**: Can be fully tested by running the SHAP analysis script on trained models and synthetic data, producing a ranked list and visualization of rank shifts.

### Tests for User Story 3 (Contract & Integration) ⚠️

- [X] T034 [US3] Define Contract test for SHAP output schema in `tests/contract/test_shap_schema.py` (validates rank‑shift CSV schema). **Validates output of T036.** **Depends on T036 (Synthetic Ground Truth generation completed).**
- [X] T035 [US3] Define Integration test for synthetic ground truth validation in `tests/integration/test_shap_validation.py`. **Validates output of T036.** **Depends on T036 (Synthetic Ground Truth generation completed).**

### Implementation for User Story 3

- [X] T036 [US3] Implement `code/shap_analysis.py` to generate a **synthetic dataset** with known non‑linear feature weights (algorithm: Gaussian noise with fixed seed). **Load the descriptor schema from T007b (`data/processed/descriptor_schema.json`) to determine feature count and names.** Dynamically generate the `known_weights` vector based on a physics-inspired function: `w_i = mean_atomic_number / scaling_factor` for the **`mean_atomic_number`** feature column, and a negligible or null value otherwise. Target calculated as `target = sum(w_i * x_i) + alpha * sum(x_i^2) + beta * sum(x_i * x_{i+1})` where alpha and beta represent tunable weighting coefficients., saved as `data/synthetic/ground_truth.parquet` (columns: Magpie descriptors, `target`, `known_weights`) (FR-014). *Ensure `known_weights` are validated against descriptor count before use.* **Depends on T007b.**
- [X] T037 [US3] Compute SHAP values for both skewed and balanced models, saving to `results/shap_analysis/shap_skewed.npy` and `results/shap_analysis/shap_balanced.npy`.
- [X] T038 [US3] Rank top features for each model, calculate **mean rank shift** (ties broken by average rank), and write `results/shap_analysis/rank_shift.csv` containing `feature, rank_skewed, rank_balanced, rank_shift`.
- [X] T039 [US3] Validate SHAP rankings against the synthetic ground truth (load `data/synthetic/ground_truth.parquet` column `known_weights`), compare `rank_shift.csv` with `known_weights`, output validation summary to `results/shap_analysis/shap_validation.json`.
- [X] T040 [US3] Visualize significant rank changes: create `results/shap_analysis/rank_shift_plot.png` (bar plot of rank shift) and `results/shap_analysis/feature_importance_bar.png` (side‑by‑side importance bars) using matplotlib.
- [X] T041 [US3] Assemble SHAP comparison report in `results/shap_analysis/shap_report.md` linking to CSVs and PNGs.
- [X] T042 [US3] Verify contract test T034 and integration test T035 pass after SHAP implementation.

**Checkpoint**: All user stories should now be independently functional.

---

## Phase 6: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T043a [P] Update `README.md` with setup instructions, directory layout, and quick‑start command examples.
- [X] T043b [P] Update `docs/quickstart.md` with step‑by‑step execution guide and expected output files.
- [ ] T044a [P] Run `ruff check` on all Python files in `code/` and fix errors.
- [ ] T044b [P] Run `black` on all Python files in `code/` and format code.
- [ ] T045 [P] Add memory profiling to `code/training.py` and `code/shap_analysis.py`; log peak usage to `results/memory_profile.csv` with columns `timestamp, peak_memory_mb, function_name` (verify Constraint‑002).
- [ ] T046 [P] Add additional unit tests for edge cases (e.g., < 100 samples property, API rate limits) in `tests/unit/`.
- [ ] T047a [P] [US1/US2/US3] Execute the full pipeline using command `python code/main.py --full-pipeline --include-mp --streaming`, ensuring total runtime ≤ 6 hours by **streaming the full merged dataset (OQMD/AFLOW/MP shards via `datasets.load_dataset(..., streaming=True)`)**, and save execution log to `results/validation_log_mp.txt` containing runtime, exit code, and pass/fail flag (verify Constraint‑001). **Task must check `MP_AVAILABLE` flag; if MP is unavailable, skip MP shards and log a warning, but still verify runtime on OQMD/AFLOW.** *Prerequisite: T016, T027, T030, T036, T037, T038, T039, T040, T041, T001b must be complete and artifacts generated.*
- [ ] T047b [P] [US1/US2/US3] Execute the full pipeline using command `python code/main.py --full-pipeline --fallback-mode --streaming`, ensuring total runtime ≤ 6 hours by **streaming the OQMD/AFLOW dataset only (MP unavailable scenario)**, and save execution log to `results/validation_log_fallback.txt` containing runtime, exit code, and pass/fail flag (verify Constraint‑001 for fallback). *Prerequisite: T016, T027, T030, T036, T037, T038, T039, T040, T041, T001b must be complete and artifacts generated.* **T047a and T047b must be run sequentially.**
- [ ] T048 [P] Final review of `state/projects/PROJ-756-assessing-dataset-imbalance-effects-on-m.yaml` for versioning completeness and artifact hashes.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies – can start immediately.
- **Foundational (Phase 2)**: Depends on Setup completion – **BLOCKS** all user stories.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion.
 - User stories can proceed in parallel (if staffed) or sequentially in priority order (P1 → P2 → P3).
- **Polish (Final Phase)**: Depends on all desired user stories being complete.
- **Data Integrity (Phase 2)**: Implemented in Phase 2 to ensure foundational logic is in place before user stories.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) – no dependencies on other stories.
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) – **requires baseline models** from US1 for comparison.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) – **requires trained models** from US1 and US2 for SHAP analysis.

### Within Each User Story

- Tests (if included) **MUST** be written and FAIL before implementation.
- Models before services.
- Services before endpoints.
- Core implementation before integration.
- Story complete before moving to next priority.

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel.
- All Foundational tasks marked [P] can run in parallel (within Phase 2), **except T010b/T010c which must complete before T012/T014/T020**.
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows).
- All tests for a user story marked [P] can run in parallel.
- Models within a story marked [P] can run in parallel.
- Different user stories can be worked on in parallel by different team members.

### Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for data schema validation in tests/contract/test_dataset_schema.py"
Task: "Integration test for baseline pipeline in tests/integration/test_baseline_pipeline.py"

# Launch all models for User Story 1 together:
Task: "Implement code/ingestion.py with exponential backoff"
Task: "Implement code/descriptors.py to compute Magpie descriptors"
```

**Explicit Dependency Notes**:
- T010b/T010c MUST complete before T012/T014/T020 can even begin (schema generation prerequisite).
- T012 and T014 depend on T010b/T010c.
- T029 depends on T028 (reads seed count from `results/power_analysis.json`).
- T030 and T031 depend on T027, T008a, T008b, and T007.
- T033 depends on T020 and T021.
- T042 depends on T034 and T035.
- T047a and T047b depend on completion of T016, T027, T030, T036, T037, T038, T039, T040, T041, T001b (All marked [ ] in this revision).
- T019 depends on T012 and T013.
- T006b-DataFetch must complete before T006c-Checksums.
- T006d-DataFetch-MP must complete before T006c-Checksums.
- T008a and T008b depend on T006b-DataFetch, T006d-DataFetch-MP, T007.
- **T049, T050, T051** must be implemented and verified before T047a/T047b (Full Pipeline Execution) to ensure data integrity and prevent fabrication.
- **T049 and T050 depend on T004a-Backoff, T004c, T006b-DataFetch, T006d-DataFetch-MP** (cannot run in parallel with them).
- **T028 and T029 are strictly sequential; T029 MUST wait for T028 to complete.**
- **T006b-DataFetch, T006d-DataFetch-MP, T049, T050 are sequential to T004a-Backoff and cannot be marked [P] for parallel execution with T004a-Backoff.**
- **T006c-Checksums is sequential to T006b-DataFetch/T006d-DataFetch-MP but parallel to other Phase 2 tasks.**
- T036 depends on T007b-Schema-Extraction.
- **T006b-DataFetch and T006d-DataFetch-MP are sequential to T004a-Backoff (Implementation of ingestion logic) and cannot be marked [P] for parallel execution with T004a-Backoff.**
- T006a-MP-Availability-Check is sequential to T004a-Backoff (must run before T004a-Backoff to set the flag).
- **T023 depends on T008a and T008b.**
- **T020 depends on T023 (validation of output).**
- **T034 and T035 depend on T036 (validation of output).**
- **T047a and T047b must be run sequentially.**

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL – blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → foundation ready
2. Add User Story 1 → test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → test independently → Deploy/Demo
4. Add User Story 3 → test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Ingestion, Descriptors, Baseline)
 - Developer B: User Story 2 (Resampling, Statistics)
 - Developer C: User Story 3 (SHAP, Synthetic Ground Truth)
 - Developer D: Phase 2 (Data Integrity & Safety Checks)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies (except where explicitly noted in Dependencies section).
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross‑story dependencies that break independence.
- **Data Constraint**: All data loaders **MUST** fail loudly on fetch errors; NO synthetic fallback allowed (T049).
- **Compute Constraint**: Pipeline must run on CPU‑only runner; if GPU is required for a method, it must be explicitly scaled down or offloaded, not faked.
- **SMOTE Constraint Resolution**: FR-003 mandates SMOTE as a fallback; Plan.md 'Constraints' section updated to reflect this (SMOTE allowed as fallback).
- **Task Consolidation**: T009a and T009b were removed as they were duplicates of T008. T008 now covers both Target and Compositional Imbalance Score calculations (split into T008a/T008b).
- **Imbalance Score Metric**: T008a/T008b implement K-Means/Gini for compositional diversity (per FR-002) and Gini for target imbalance (per FR-011). **Removed density-weighting step.**
- **Bottom [deferred]**: T026 uses **Jenks Natural Breaks (k=5) with seed=42** for minority subset determination.
- **Log Rotation**: T004b uses size-based rotation (create new file if > 100MB) without deletion to preserve raw trace. T004b-Test was removed as it verified implementation details not in spec.
- **Subset Strategy**: T047a uses streaming of the **full merged dataset** (up to 5GB) for MP scenario; T047b uses streaming of **OQMD/AFLOW dataset only** for fallback scenario to ensure 6-hour constraint verification is valid for both MP and fallback scenarios.
- **Revision Concerns**: Phase 2 tasks (T049-T051) address the "Fail Loudly" data loading rule and prevent synthetic data fabrication in edge cases, ensuring compliance with the Constitution.
- **Data Source**: All data fetches now use official OQMD and Materials Project REST APIs, aligning with spec FR-001 and FR-007.
- **Entry Point**: T001b implements `code/main.py` with required CLI flags.