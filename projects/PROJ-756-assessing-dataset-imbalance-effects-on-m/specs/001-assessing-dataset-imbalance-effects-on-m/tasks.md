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

- [X] T001 [P] Create project directory structure: `projects/PROJ-756-assessing-dataset-imbalance-effects-on-m/` including `data/`, `code/`, `tests/`, `artifacts/`, `results/`, `state/`, `logs/`, `logs/archive/`.
- [X] T002 Initialize Python 3.11 project with pinned dependencies in `code/requirements.txt` (pandas, scikit-learn, shap, magpie, datasets, numpy, scipy, pyyaml, cvxpy)
- [X] T003 [P] Configure linting (ruff/black) and formatting tools in root `pyproject.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. **Foundation is READY ONLY AFTER T006b, T006c, T006d, T006e, T007, T009, T008 are complete.**

- [X] T004a [P] Implement `code/ingestion.py` logic for **OQMD and AFLOW** APIs: exponential backoff, JSON logging to `logs/api_errors.log`, size-based rotation (new file if >100MB, no deletion), and **Fail Loudly** (raise `DataFetchError` on persistent failure). (FR-007, FR-008, Constitution Principle III).
- [X] T004b [P] Implement `code/ingestion.py` logic for **Materials Project** API: lightweight probe using `MP_API_KEY` env var, fallback to `MP_AVAILABLE = False` if missing/timeout, no synthetic fallback. (FR-008).
- [X] T004c [P] Implement `code/ingestion.py` log rotation logic: ensure size-based rotation (create new file if >100MB) without deletion, preserving raw trace. (FR-007, Constitution Principle III).
- [ ] T006b [P] Implement `code/downloaders.py` to download **OQMD** dataset using `load_dataset("oqmd/oqmd-dataset", split="train", streaming=True)` to `data/raw/oqmd.parquet`. **Ensure directory exists: `mkdir -p data/raw`.** (FR-001, FR-007, FR-008).
- [ ] T006c [P] Implement `code/downloaders.py` to download **AFLOW** dataset using `load_dataset("aflow/aflow-dataset", split="train", streaming=True)` to `data/raw/aflow.parquet`. **Ensure directory exists: `mkdir -p data/raw`.** (FR-001, FR-007, FR-008).
- [ ] T006d [P] Implement `code/downloaders.py` to download Materials Project dataset using `mp-api` library (if `MP_API_KEY` is present) to `data/raw/mp.parquet`. **If no key or fetch fails persistently, log warning and skip (do not raise error), allowing pipeline to proceed with OQMD/AFLOW only.** (FR-001, FR-008).
- [ ] T006e [P] Implement checksum verification in `code/downloaders.py` using **SHA‑256 algorithm**, generating checksum files **`data/raw/oqmd.parquet.sha256`, `data/raw/aflow.parquet.sha256`, and `data/raw/mp.parquet.sha256` (if MP exists)** in `sha256sum` format (`<hash> <filename>`). **If MP download (T006d) was skipped, do not generate `mp.parquet.sha256` and log `N/A` in state file.** **Update `state/projects/PROJ-756-assessing-dataset-imbalance-effects-on-m.yaml` with the generated checksums in the `artifact_hashes` map.** (Constitution Principle III). **Depends on T006b, T006c, T006d.**
- [ ] T007 [P] Implement `code/descriptors.py` to compute all Magpie compositional descriptors (L‑normalized) and save to `data/processed/descriptors.parquet`. **Store the exact column order in the parquet metadata for downstream alignment.** (FR‑002). **BLOCKED until T006b/T006c/T006d complete.**
- [ ] T009 [P] Implement `code/merge.py` to merge OQMD, AFLOW, and MP (if available) datasets into a single `data/processed/merged.parquet`. **Handle column alignment and missing values.** **BLOCKED until T006b, T006c, T006d, T007 complete.**
- [ ] T008 [P] Implement `code/imbalance.py` to calculate **Target Imbalance Score** (Gini coefficient of target property values for properties with >= 100 samples) AND **Compositional Imbalance Score**. **Step 1: Load merged data. Step 2: Run K-Means (k=50) on compositional descriptors. Step 3: Calculate Gini of the **cluster count distribution** (frequency of samples per cluster) as the ImbalanceScore proxy.** Skip properties with < 100 samples. Output to `results/target_imbalance_scores.csv` and `results/compositional_imbalance_score.csv` (FR‑002, FR‑011). **Depends on T006b, T006c, T006d, T007, T009. BLOCKED until T006b/c/d/T009 complete.**
- [X] T010 [P] Create unit tests for ingestion retry logic and API failure handling in `tests/unit/test_ingestion.py`.
- [X] T011 [P] Create unit tests for Magpie descriptor computation in `tests/unit/test_descriptors.py`.
- [X] T010b [P] Generate `contracts/dataset.schema.yaml` defining the schema for `data/processed/` (columns: composition, target properties, descriptors, imbalance scores) (FR‑001).
- [X] T010c [P] Generate `contracts/resampling.schema.yaml` defining the schema for resampled datasets (columns: bin_id, sample_count, CV, real_data_flag) (FR‑003).
- [X] T012 [US1] Contract test for data schema validation in `tests/contract/test_dataset_schema.py` (validates `data/processed/` against `contracts/dataset.schema.yaml`). *Depends on T010b.*
- [X] T013 [P] Integration test for baseline pipeline in `tests/integration/test_baseline_pipeline.py` (runs ingestion → descriptors → baseline training → report).
- [X] T014 [US2] Contract test for resampling schema validation in `tests/contract/test_resampling_schema.py` (validates CV constraints against `contracts/resampling.schema.yaml`). *Depends on T010c.*
- [X] T015 [P] Integration test for statistical significance in `tests/integration/test_statistical_significance.py` (validates power analysis and p‑value calculation).
- [ ] T049 [P] [US1/US2] Implement strict error handling in `code/downloaders.py` and `code/ingestion.py`: **raise a specific `DataFetchError` exception on any persistent fetch failure for OQMD/AFLOW after retries**, ensuring no synthetic fallback code paths exist (Constitution Principle II, "Fail Loudly" rule). **Preserve exponential backoff and retry logic. For MP, implement fallback logic as per FR-008.** **Depends on T004a, T004b, T006b, T006c, T006d. Run after T004a, T004b, T006b, T006c, T006d are complete.**
- [ ] T050 [P] [US1/US2] Add a verification script `code/verify_no_synthetic_fallback.py` that scans `code/downloaders.py`, `code/resampling.py`, and `code/ingestion.py` for patterns indicating synthetic fallback (e.g., `if not data: return mock_data`, `except: return synthetic`) and fails the build if found. **Depends on T004a, T004b, T006b, T006c, T006d. Run after T004a, T004b, T006b, T006c, T006d are complete.**
- [ ] T051 [P] [US2] Implement explicit logging in `code/resampling.py` when SMOTE is triggered as a fallback, logging the **exact percentage of synthetic data added** and the **resulting CV** to `results/resampling_log.json` to ensure compliance with FR-013 (Synthetic data ≤ 30%) and FR-003 (Combined CV ≤ 0.30).
- [ ] T052b [P] [US2] Implement **MiniBatchKMeans** strategy in `code/imbalance.py` for K-Means clustering (k=50) on large datasets to satisfy Constraint-002 (7GB RAM). **Use chunked processing to calculate Gini of cluster counts without loading full dataset into memory.** (Replaces T052).
- [ ] T053 [P] [US2] Implement a check in `code/evaluation.py` to verify that the **minority subset** (bottom [MINORITY_QUANTILE]) used for performance degradation calculation is derived from the **original, unmodified dataset** distribution, not a resampled one, to prevent circular validation (FR-010).

### Checkpoint
**Foundation ready ONLY after T006b, T006c, T006d, T006e, T007, T009, T008 are complete** – user story implementation can now begin in parallel.

---

## Phase 3: User Story 1 - Quantify Imbalance and Generate Baseline Predictions (Priority: P1) 🎯 MVP

**Goal**: Download datasets, compute descriptors, train baseline RF/GB models on skewed data, and generate baseline performance report.

**Independent Test**: Can be fully tested by running `code/ingestion.py`, `code/descriptors.py`, and `code/training.py` (baseline mode) to produce a CSV report with MAE, RMSE, R² for skewed data.

### Tests for User Story 1 (Contract & Integration) ⚠️

- [X] T012 [US1] Contract test for data schema validation (already defined above).
- [X] T013 [US1] Integration test for baseline pipeline (already defined above).

### Implementation for User Story 1

- [ ] T014 [US1] Implement `code/training.py` to train Random Forest and Gradient Boosting regressors on skewed data (FR‑004). **BLOCKED until T006b/c/d/T007/T009 complete.**
- [ ] T015 [US1] Implement `code/training.py` to evaluate models on a stratified test set preserving original imbalance (FR‑004). **BLOCKED until T014 complete.**
- [ ] T016 [US1] Implement `code/evaluation.py` to generate **baseline performance report** saved as `results/baseline_report.csv` with columns: `property, model_type, MAE, RMAE, R2` (FR-004). **BLOCKED until T015 complete.**
- [ ] T018a-Verify-Log-Rotation [P] Run `code/verify_log_rotation.py` to verify that log rotation **creates new files if >100MB without deleting old files**, matching T004 logic. (FR-007, Constitution Principle III).
- [X] T019 [US1] Verify that contract tests T012 and integration test T013 **pass before** baseline report generation. *Status: Complete (T012/T013 marked [X]).*

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently.

---

## Phase 4: User Story 2 - Apply Resampling and Measure Performance Degradation (Priority: P2)

**Goal**: Apply stratified resampling (or fallback), retrain models, and statistically compare performance on the minority subset.

**Independent Test**: Can be fully tested by running the resampling pipeline, producing a comparison table and statistical test results (paired t‑test/Wilcoxon) showing performance difference on the bottom [MINORITY_QUANTILE] subset.

### Tests for User Story 2 (Contract & Integration) ⚠️

- [ ] T020 [US2] Contract test for resampling logic (validates CV constraints against `contracts/resampling.schema.yaml`). **BLOCKED until T022 complete.**
- [ ] T021 [US2] Integration test for statistical significance (validates power analysis and p‑value calculation). **BLOCKED until T029 complete.**

### Implementation for User Story 2

- [ ] T022 [US2] Implement `code/resampling.py` with stratified undersampling/oversampling using **equal‑frequency binning into multiple bins** (default) and ensure **real‑data CV ≤ 0.10**. **BLOCKED until T008 complete.**
- [ ] T023 [US2] Implement fallback in `code/resampling.py`: if > 20% data loss or empty bins occur, **switch to SMOTE for regression immediately** (FR-003). Enforce **combined CV ≤ 0.30** while still keeping real‑data CV ≤ 0.10. (FR-003, US-2 Edge Cases).
- [ ] T024 [US2] Enforce the CV constraints described above (real ≤ 0.10, combined ≤ 0.30) within the resampling implementation.
- [ ] T025 [US2] Implement `code/training.py` to retrain RF and GB models on the balanced dataset with identical hyperparameters (FR‑004). **BLOCKED until T022/T023 complete.**
- [ ] T026 [US2] Implement `code/evaluation.py` to **isolate the bottom [MINORITY_QUANTILE] of each target property** using a quantile threshold **read from `config.yaml` (default small)** derived from the **FULL dataset** distribution (FR‑010) and calculate per‑bin MAE for this subset. *Rationale: Bottom [MINORITY_QUANTILE] represents the extreme tail where imbalance effects are most critical.*
- [ ] T027 [US2] Implement `code/evaluation.py` to calculate **performance degradation**: `MAE_skewed_minority - MAE_balanced_minority` and write to `results/performance_degradation.csv`. **BLOCKED until T025 complete.**
- [ ] T028 [US2] Implement power analysis in `code/evaluation.py` to determine the minimum number of random seeds required for **paired t-test**, Cohen's d = 0.5, power ≥ 0.8, α = 0.05; output seed count to `results/power_analysis.json`.
- [ ] T029 [US2] Implement paired statistical tests (paired t‑test or Wilcoxon) across the seed count from T028 (**Read seed_count from results/power_analysis.json**), saving results to `results/statistical_test_results.csv` with columns `test_type, p_value, effect_size, seed_count` (FR‑005). **BLOCKED until T028 complete.**
- [ ] T030 [US2] Compute Pearson correlation between **Compositional Imbalance Score** (from T008) and **performance degradation** (from T027); output to `results/correlation_analysis.csv` with columns `property, score_type, r, p_value` (FR‑012). **BLOCKED until T008/T027 complete.**
- [ ] T031 [US2] Compute Pearson correlation between **Target Imbalance Score** (from T008) and **performance degradation**; append results to the same `results/correlation_analysis.csv` (FR‑012). **BLOCKED until T008/T027 complete.**
- [ ] T032 [US2] Generate comparison report `results/comparison_report.csv` with columns `property, metric, skewed_value, balanced_value, delta_pct, p_value, effect_size` (US‑2).
- [ ] T033 [US2] Verify that contract test T020 and integration test T021 pass after resampling implementation.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently.

---

## Phase 5: User Story 3 - Analyze Feature Importance Distortion via SHAP (Priority: P3)

**Goal**: Generate SHAP values, compare top-ranked feature rankings
The research question is to identify the most influential variables, the method involves ranking features by their contribution scores, and the references include [Citation]., and validate against a synthetic ground‑truth baseline.

**Independent Test**: Can be fully tested by running the SHAP analysis script on trained models and synthetic data, producing a ranked list and visualization of rank shifts.

### Tests for User Story 3 (Contract & Integration) ⚠️

- [ ] T034 [US3] Contract test for SHAP output schema in `tests/contract/test_shap_schema.py` (validates rank‑shift CSV schema). **BLOCKED until T036 complete.**
- [ ] T035 [US3] Integration test for synthetic ground truth validation in `tests/integration/test_shap_validation.py`. **BLOCKED until T036 complete.**

### Implementation for User Story 3

- [ ] T036 [US3] Implement `code/shap_analysis.py` to generate a **synthetic dataset** with known non‑linear feature weights. **Algorithm: Load descriptor column order from `data/processed/descriptors.parquet` metadata; align a `known_weights` vector dynamically to this order. Target calculated as `sum(weight_i * x_i) + c * sum(x_i^) + 0.3 * sum(x_i * x_{i+1})`, where c represents a positive scaling coefficient., saved as `data/synthetic/ground_truth.parquet` (columns: Magpie descriptors, `target`, `known_weights`) (FR-014).** *Ensure `known_weights` length matches descriptor count and order is logged.*
- [ ] T037 [US3] Compute SHAP values for both skewed and balanced models, saving to `results/shap_analysis/shap_skewed.npy` and `results/shap_analysis/shap_balanced.npy`. **BLOCKED until T014/T025 complete.**
- [ ] T038 [US3] Rank top features for each model, calculate **mean rank shift** (ties broken by average rank), and write `results/shap_analysis/rank_shift.csv` containing `feature, rank_skewed, rank_balanced, rank_shift`.
- [ ] T039 [US3] Validate SHAP rankings against the synthetic ground truth (load `data/synthetic/ground_truth.parquet` column `known_weights`), compare `rank_shift.csv` with `known_weights`, output validation summary to `results/shap_analysis/shap_validation.json`.
- [ ] T040 [US3] Visualize significant rank changes: create `results/shap_analysis/rank_shift_plot.png` (bar plot of rank shift) and `results/shap_analysis/feature_importance_bar.png` (side‑by‑side importance bars) using matplotlib.
- [ ] T041 [US3] Assemble SHAP comparison report in `results/shap_analysis/shap_report.md` linking to CSVs and PNGs.
- [ ] T042 [US3] Verify contract test T034 and integration test T035 pass after SHAP implementation.

**Checkpoint**: All user stories should now be independently functional.

---

## Phase 6: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T043a [P] Update `README.md` with setup instructions, directory layout, and quick‑start command examples.
- [ ] T043b [P] Update `docs/quickstart.md` with step‑by‑step execution guide and expected output files.
- [ ] T044a [P] Run `ruff check` on all Python files in `code/` and fix errors.
- [ ] T044b [P] Run `black` on all Python files in `code/` and format code.
- [ ] T045 [P] Add memory profiling to `code/training.py` and `code/shap_analysis.py`; log peak usage to `results/memory_profile.csv` with columns `timestamp, peak_memory_mb, function_name` (verify Constraint‑002).
- [ ] T046 [P] Add additional unit tests for edge cases (e.g., < 100 samples property, API rate limits) in `tests/unit/`.
- [ ] T047 [P] Execute the full pipeline using command `python code/main.py --full-pipeline`, ensuring total runtime ≤ 6 hours by **using MiniBatchKMeans and chunked processing for large datasets**, and save execution log to `results/validation_log.txt` containing runtime, exit code, and pass/fail flag (verify Constraint‑001). **If prerequisites (T016, T027, T030) are missing, the script must exit with code 1 and log `PREREQUISITE_MISSING`.** *Prerequisite: T016, T027, T030 must be complete and artifacts generated (Status: T016=[ ], T027=[ ], T030=[ ]).*
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
- T030 and T031 depend on T027, T008, and T007.
- T033 depends on T020 and T021.
- T042 depends on T034 and T035.
- T047 depends on completion of T016, T027, and T030 (All marked [ ] in this revision).
- T019 depends on T012 and T013.
- T006b must complete before T006e.
- T006c must complete before T006e.
- T006d must complete before T006e.
- T008 depends on T006b, T006c, T006d, T007, T009.
- **T049, T050, T051, T052b, T053** must be implemented and verified before T047 (Full Pipeline Execution) to ensure data integrity and prevent fabrication.
- **T049 and T050 depend on T004a, T004b, T006b, T006c, and T006d** (cannot run in parallel with them).
- T036 depends on T007.
- **Foundation is BLOCKED until T006b, T006c, T006d, T006e, T007, T009, T008 are complete.**

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
- **Data Constraint**: All data loaders **MUST** fail loudly on fetch errors; NO synthetic fallback allowed (T049, T050).
- **Compute Constraint**: Pipeline must run on CPU‑only runner; if GPU is required for a method, it must be explicitly scaled down or offloaded, not faked.
- **SMOTE Constraint Resolution**: Although the initial plan draft mentioned 'SMOTE excluded', Functional Requirement FR-003 explicitly mandates implementing 'SMOTE for regression' as a fallback. FR-003 takes precedence over the plan's initial constraint assumption. T023 implements this fallback as required.
- **Task Consolidation**: T009a and T009b were removed as they were duplicates of T008. T008 now covers both Target and Compositional Imbalance Score calculations.
- **Imbalance Score Metric**: T008 implements K-Means/Gini for compositional diversity (per FR-002) and Gini for target imbalance (per FR-011).
- **Bottom [deferred]**: T026 uses `MINORITY_QUANTILE` read from `config.yaml` (default 0.05) to analyze the extreme tail.
- **Log Rotation**: T004 uses size-based rotation (create new file if > 100MB) without deletion to preserve raw trace.
- **Subset Strategy**: T047 uses MiniBatchKMeans and chunked processing for large datasets to ensure 6-hour constraint.
- **Revision Concerns**: Phase 2 tasks (T049-T053) address the "Fail Loudly" data loading rule and prevent synthetic data fabrication in edge cases, ensuring compliance with the Constitution.