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

- [ ] T001 [P] Create project directory structure: `projects/PROJ-756-assessing-dataset-imbalance-effects-on-m/` including `data/`, `code/`, `tests/`, `artifacts/`, `results/`, `state/`, `logs/`, `logs/archive/`.
- [X] T002 Initialize Python 3.11 project with pinned dependencies in `code/requirements.txt` (pandas, scikit-learn, shap, magpie, datasets, numpy, scipy, pyyaml, cvxpy)
- [X] T003 [P] Configure linting (ruff/black) and formatting tools in root `pyproject.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `code/ingestion.py` with exponential backoff (multiple retries, 60s timeout) for OQMD, AFLOW, and Materials Project APIs, **log all API errors as JSON lines to `logs/api_errors.log` including the configurable retry count**, and merge data (FR‑007, FR‑008). **Implement size-based rotation (create new file if > 100MB) without deletion to preserve raw trace.** (FR‑007, Constitution Principle III).
- [X] T005 Implement fallback logic in `code/ingestion.py`: if Materials Project API fails (403/timeout), **dynamically switch to fallback mode using only OQMD and AFLOW**, log the scope change, and ensure the system can re-evaluate MP availability if credentials become available later (FR‑001, FR‑008).
- [ ] T006a [P] Create directory `projects/PROJ-756-assessing-dataset-imbalance-effects-on-m/data/raw/` for raw downloaded data.
- [ ] T006b [P] Implement `code/downloaders.py` to download OQMD and AFLOW datasets **to `data/raw/oqmd.parquet` and `data/raw/aflow.parquet`** respectively. **Use specific Hugging Face dataset IDs: `load_dataset("oqmd/oqmd-dataset", split="train")` and `load_dataset("aflow/aflow-dataset", split="train")` with fallback to raw URLs ` and ` if HF fails.** **Ensure directory exists: `mkdir -p data/raw`.** (FR-001, FR-007, FR-008). **Must complete before T007, T008.**
- [ ] T006c [P] Implement checksum verification in `code/downloaders.py` using **SHA‑256 algorithm**, generating checksum files **`data/raw/oqmd.parquet.sha256` and `data/raw/aflow.parquet.sha256`** in `sha256sum` format (`<hash> <filename>`). **Update `state/projects/PROJ-756-assessing-dataset-imbalance-effects-on-m.yaml` with the generated checksums in the `artifact_hashes` map.** (Constitution Principle III).
- [X] T007 Implement `code/descriptors.py` to compute all Magpie compositional descriptors (L‑normalized) and save to `data/processed/descriptors.parquet` (FR‑002).
- [ ] T008 [P] Implement `code/imbalance.py` to calculate **Target Imbalance Score** (Gini coefficient of target property values for properties with >= 100 samples, handling negative values via absolute transformation or offset) AND **Compositional Imbalance Score** (Convex Hull Coverage Score of compositional features). **Skip properties with < 100 samples.** Output to `results/target_imbalance_scores.csv` and `results/compositional_imbalance_score.csv` (FR‑002, FR‑011). *Note: Replaced K-Means/Gini with Convex Hull Coverage Score per plan.md Complexity Tracking.* **Depends on T006b, T007.**
- [X] T010 [P] Create unit tests for ingestion retry logic and API failure handling in `tests/unit/test_ingestion.py`.
- [X] T011 [P] Create unit tests for Magpie descriptor computation in `tests/unit/test_descriptors.py`.
- [ ] T010b Generate `contracts/dataset.schema.yaml` defining the schema for `data/processed/` (columns: composition, target properties, descriptors, imbalance scores) (FR‑001).
- [ ] T010c Generate `contracts/resampling.schema.yaml` defining the schema for resampled datasets (columns: bin_id, sample_count, CV, real_data_flag) (FR‑003).
- [X] T012 [US1] Contract test for data schema validation in `tests/contract/test_dataset_schema.py` (validates `data/processed/` against `contracts/dataset.schema.yaml`). *Depends on T010b.*
- [X] T013 [P] Integration test for baseline pipeline in `tests/integration/test_baseline_pipeline.py` (runs ingestion → descriptors → baseline training → report).
- [ ] T020 [US2] Contract test for resampling logic (validates CV constraints against `contracts/resampling.schema.yaml`). *Depends on T010c.*
- [X] T014 [P] Contract test for resampling schema validation in `tests/contract/test_resampling_schema.py` (validates CV constraints against `contracts/resampling.schema.yaml`). *Depends on T010c.*
- [X] T015 [P] Integration test for statistical significance in `tests/integration/test_statistical_significance.py` (validates power analysis and p‑value calculation).

### Checkpoint
Foundation ready – user story implementation can now begin in parallel.

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
- [ ] T018a [P] Run `code/verify_log_rotation.py` to verify the **absence of log rotation logic** and confirm that logs are appended without deletion (FR-007, Constitution Principle III). *Note: Log rotation logic removed, task verifies absence of rotation.*
- [X] T019 [US1] Verify that contract tests T012 and integration test T013 **pass before** baseline report generation (requires T012/T013 completion prior to T016).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently.

---

## Phase 4: User Story 2 - Apply Resampling and Measure Performance Degradation (Priority: P2)

**Goal**: Apply stratified resampling (or fallback), retrain models, and statistically compare performance on the minority subset.

**Independent Test**: Can be fully tested by running the resampling pipeline, producing a comparison table and statistical test results (paired t‑test/Wilcoxon) showing performance difference on the bottom [deferred] subset.

### Tests for User Story 2 (Contract & Integration) ⚠️

- [X] T020 [US2] Contract test for resampling logic (validates CV constraints against `contracts/resampling.schema.yaml`).
- [X] T021 [US2] Integration test for statistical significance (validates power analysis and p‑value calculation).

### Implementation for User Story 2

- [X] T022 [US2] Implement `code/resampling.py` with stratified undersampling/oversampling using **equal‑frequency binning into 20 bins** (default) and ensure **real‑data CV ≤ 0.10**.
- [X] T023 [US2] Implement fallback in `code/resampling.py`: if > 20% data loss or empty bins occur, **switch to cost-sensitive learning (class weights) FIRST; if that fails, THEN use SMOTE for regression**. Enforce **combined CV ≤ 0.30** while still keeping real‑data CV ≤ 0.10. **Note: If SMOTE is used, synthetic data must not exceed a modest proportion of the total training set.** (FR-003, US-2 Edge Cases). *Note: FR-003 mandates SMOTE fallback; this overrides the plan's initial 'SMOTE excluded' constraint assumption, but SMOTE is strictly a fallback.*
- [X] T024 [US2] Enforce the CV constraints described above (real ≤ 0.10, combined ≤ 0.30) within the resampling implementation.
- [X] T025 [US2] Implement `code/training.py` to retrain RF and GB models on the balanced dataset with identical hyperparameters (FR‑004).
- [X] T026 [US2] Implement `code/evaluation.py` to **isolate the bottom [deferred] of each target property** using a quantile threshold **MINORITY_QUANTILE = 0.05 (bottom [deferred])** derived from the **FULL dataset** distribution (FR‑010) and calculate per‑bin MAE for this subset. *Rationale: Bottom [deferred] represents the extreme tail where imbalance effects are most critical.*
- [X] T027 [US2] Implement `code/evaluation.py` to calculate **performance degradation**: `MAE_skewed_minority - MAE_balanced_minority` and write to `results/performance_degradation.csv`.
- [X] T028 [US2] Implement power analysis in `code/evaluation.py` to determine the minimum number of random seeds required for **paired t-test**, Cohen's d = 0.5, power ≥ 0.8, α = 0.05; output seed count to `results/power_analysis.json`.
- [X] T029 [US2] Implement paired statistical tests (paired t‑test or Wilcoxon) across the seed count from T028 (**Read seed_count from results/power_analysis.json**), saving results to `results/statistical_test_results.csv` with columns `test_type, p_value, effect_size, seed_count` (FR‑005).
- [X] T030 [US2] Compute Pearson correlation between **Compositional Imbalance Score** (from T008) and **performance degradation** (from T027); output to `results/correlation_analysis.csv` with columns `property, score_type, r, p_value` (FR‑012).
- [X] T031 [US2] Compute Pearson correlation between **Target Imbalance Score** (from T008) and **performance degradation**; append results to the same `results/correlation_analysis.csv` (FR‑012).
- [X] T032 [US2] Generate comparison report `results/comparison_report.csv` with columns `property, metric, skewed_value, balanced_value, delta_pct, p_value, effect_size` (US‑2).
- [X] T033 [US2] Verify that contract test T020 and integration test T021 pass after resampling implementation.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently.

---

## Phase 5: User Story 3 - Analyze Feature Importance Distortion via SHAP (Priority: P3)

**Goal**: Generate SHAP values, compare top-ranked feature rankings

The research question is to identify the most influential variables, the method involves ranking features by their contribution scores, and the references include [Citation]., and validate against a synthetic ground‑truth baseline.

**Independent Test**: Can be fully tested by running the SHAP analysis script on trained models and synthetic data, producing a ranked list and visualization of rank shifts.

### Tests for User Story 3 (Contract & Integration) ⚠️

- [ ] T034 [US3] Contract test for SHAP output schema in `tests/contract/test_shap_schema.py` (validates rank‑shift CSV schema).
- [ ] T035 [US3] Integration test for synthetic ground truth validation in `tests/integration/test_shap_validation.py`.

### Implementation for User Story 3

- [ ] T036 [US3] Implement `code/shap_analysis.py` to generate a **synthetic dataset** with known non‑linear feature weights (algorithm: Gaussian noise with fixed seed, `known_weights` vector **dynamically generated to match the length of Magpie descriptors from T007**), saved as `data/synthetic/ground_truth.parquet` (columns: Magpie descriptors, `target`, `known_weights`) (FR-014). *Ensure `known_weights` are validated against descriptor count before use.*
- [ ] T037 [US3] Compute SHAP values for both skewed and balanced models, saving to `results/shap_analysis/shap_skewed.npy` and `results/shap_analysis/shap_balanced.npy`.
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
- [ ] T047 [P] Execute the full pipeline using command `python code/main.py --full-pipeline --max-rows 10000`, ensuring total runtime ≤ 6 hours by **streaming first [deferred] rows** to guarantee compliance, and save execution log to `results/validation_log.txt` containing runtime, exit code, and pass/fail flag (verify Constraint‑001). *Prerequisite: T016, T027, T030 must be complete and artifacts generated (Status: T016=[X], T027=[X], T030=[X]).*
- [ ] T048 [P] Final review of `state/projects/PROJ-756-assessing-dataset-imbalance-effects-on-m.yaml` for versioning completeness and artifact hashes.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies – can start immediately.
- **Foundational (Phase 2)**: Depends on Setup completion – **BLOCKS** all user stories.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion.
 - User stories can proceed in parallel (if staffed) or sequentially in priority order (P1 → P2 → P3).
- **Polish (Final Phase)**: Depends on all desired user stories being complete.

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
- T020 depends on T010c.
- T029 depends on T028 (reads seed count from `results/power_analysis.json`).
- T030 and T031 depend on T027, T008a, and T008b.
- T033 depends on T020 and T021.
- T042 depends on T034 and T035.
- T047 depends on completion of T016, T027, and T030 (All marked [X] in this revision).
- T019 depends on T012 and T013.
- T006b must complete before T007 and T008.
- T008 depends on T006b and T007.

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
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies (except where explicitly noted in Dependencies section).
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross‑story dependencies that break independence.
- **Data Constraint**: All data loaders **MUST** fail loudly on fetch errors; NO synthetic fallback allowed.
- **Compute Constraint**: Pipeline must run on CPU‑only runner; if GPU is required for a method, it must be explicitly scaled down or offloaded, not faked.
- **SMOTE Constraint Resolution**: Although the initial plan draft mentioned 'SMOTE excluded', Functional Requirement FR-003 explicitly mandates implementing 'SMOTE for regression' as a fallback. FR-003 takes precedence over the plan's initial constraint assumption. T023 implements this fallback as required, but strictly as a second-tier fallback after cost-sensitive learning.
- **Task Consolidation**: T009a and T009b were removed as they were duplicates of T008. T008 now covers both Target and Compositional Imbalance Score calculations.
- **Imbalance Score Metric**: T008 implements Convex Hull Coverage Score for compositional diversity (per plan.md) and Gini for target imbalance (per FR-011).
- **Bottom [Deferred]**: T026 uses MINORITY_QUANTILE = 0.05 (bottom [deferred]) to analyze the extreme tail.
- **Log Rotation**: T004 uses size-based rotation (create new file if > 100MB) without deletion to preserve raw trace.
- **Subset Strategy**: T047 uses streaming of first 10k rows to ensure 6-hour constraint.