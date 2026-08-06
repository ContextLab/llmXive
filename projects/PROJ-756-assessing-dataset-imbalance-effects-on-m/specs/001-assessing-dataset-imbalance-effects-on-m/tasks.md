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

- [ ] T001a [P] Create directory `projects/PROJ-756-assessing-dataset-imbalance-effects-on-m/`
- [ ] T001b [P] Create directory `projects/PROJ-756-assessing-dataset-imbalance-effects-on-m/data/`
- [ ] T001c [P] Create directory `projects/PROJ-756-assessing-dataset-imbalance-effects-on-m/code/`
- [ ] T001d [P] Create directory `projects/PROJ-756-assessing-dataset-imbalance-effects-on-m/tests/`
- [ ] T001e [P] Create directory `projects/PROJ-756-assessing-dataset-imbalance-effects-on-m/artifacts/`
- [ ] T001f [P] Create directory `projects/PROJ-756-assessing-dataset-imbalance-effects-on-m/results/`
- [ ] T001g [P] Create directory `projects/PROJ-756-assessing-dataset-imbalance-effects-on-m/state/`
- [X] T002 Initialize Python 3.11 project with pinned dependencies in `code/requirements.txt` (pandas, scikit-learn, shap, magpie, datasets, numpy, scipy, pyyaml, cvxpy)
- [X] T003 [P] Configure linting (ruff/black) and formatting tools in root `pyproject.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `code/ingestion.py` with exponential backoff (a limited number of retries, 60 s timeout) for OQMD, AFLOW, and Materials Project APIs, **log all API errors as JSON lines to `logs/api_errors.log` including the configurable retry count**, and merge data (FR‑007, FR‑008). Also perform log rotation: archive logs older than days into `logs/archive/`. **Ensure directories exist: `mkdir -p logs logs/archive`**.
- [X] T005 Implement fallback logic in `code/ingestion.py`: if Materials Project API fails (403/timeout), **dynamically switch to fallback mode using only OQMD and AFLOW**, log the scope change, and ensure the system can re-evaluate MP availability if credentials become available later (FR‑001, FR‑008).
- [ ] T006a [P] Create directory `projects/PROJ-756-assessing-dataset-imbalance-effects-on-m/data/raw/` for raw downloaded data.
- [ ] T006b [P] Implement `code/downloaders.py` to download OQMD and AFLOW datasets **to `data/raw/oqmd.parquet` and `data/raw/aflow.parquet`** respectively. **Ensure directory exists: `mkdir -p data/raw`**.
- [ ] T006c [P] Implement checksum verification in `code/downloaders.py` using **SHA‑256 algorithm**, generating checksum files **`data/raw/oqmd.parquet.sha256` and `data/raw/aflow.parquet.sha256`** in `sha256sum` format (`<hash>  <filename>`).
- [X] T007 Implement `code/descriptors.py` to compute all Magpie compositional descriptors (L2‑normalized) and save to `data/processed/descriptors.parquet` (FR‑002).
- [X] T008 Implement `code/imbalance.py` to calculate **Target Imbalance Score** (Gini coefficient of each target property) and skip properties with < 100 samples (FR‑002, FR‑011). Output to `results/target_imbalance_scores.csv`.
- [X] T009a [P] Implement `code/imbalance.py` to calculate **Target Imbalance Score** (Gini of target values) for properties with >= 100 samples (FR-011). Output to `results/target_imbalance_scores.csv`.
- [X] T009b [P] Implement `code/imbalance.py` to calculate **Compositional Imbalance Score** using **Gini coefficient of K-Means cluster sizes (k=50, Euclidean distance)** on compositional features (FR‑002). Output to `results/compositional_imbalance_score.csv`.
- [X] T010 [P] Create unit tests for ingestion retry logic and API failure handling in `tests/unit/test_ingestion.py`.
- [X] T011 [P] Create unit tests for Magpie descriptor computation in `tests/unit/test_descriptors.py`.
- [ ] T010b [P] Generate `contracts/dataset.schema.yaml` and `contracts/resampling.schema.yaml` to define expected data structures for contract tests (FR‑001, FR‑003). These files are required for T012 and T020.
- [ ] T012 [P] [US1] Contract test for data schema validation in `tests/contract/test_dataset_schema.py` (validates `data/processed/` against `contracts/dataset.schema.yaml`). *Depends on T010b.*
- [X] T013 [P] Integration test for baseline pipeline in `tests/integration/test_baseline_pipeline.py` (runs ingestion → descriptors → baseline training → report).
- [ ] T020 [P] [US2] Contract test for resampling logic (validates CV constraints against `contracts/resampling.schema.yaml`). *Depends on T010b.*
- [X] T014 [P] Contract test for resampling schema validation in `tests/contract/test_resampling_schema.py` (validates CV constraints against `contracts/resampling.schema.yaml`). *Depends on T010b.*
- [X] T015 [P] Integration test for statistical significance in `tests/integration/test_statistical_significance.py` (validates power analysis and p‑value calculation).

### Checkpoint
Foundation ready – user story implementation can now begin in parallel.

---

## Phase 3: User Story 1 - Quantify Imbalance and Generate Baseline Predictions (Priority: P1) 🎯 MVP

**Goal**: Download datasets, compute descriptors, train baseline RF/GB models on skewed data, and generate baseline performance report.

**Independent Test**: Can be fully tested by running `code/ingestion.py`, `code/descriptors.py`, and `code/training.py` (baseline mode) to produce a CSV report with MAE, RMSE, R² for skewed data.

### Tests for User Story 1 (Contract & Integration) ⚠️

- [ ] T012 [P] [US1] Contract test for data schema validation (already defined above).
- [X] T013 [P] [US1] Integration test for baseline pipeline (already defined above).

### Implementation for User Story 1

- [ ] T014 [US1] Implement `code/training.py` to train Random Forest and Gradient Boosting regressors on skewed data (FR‑004).
- [ ] T015 [US1] Implement `code/training.py` to evaluate models on a stratified test set preserving original imbalance (FR‑004).
- [ ] T016 [US1] Implement `code/evaluation.py` to generate **baseline performance report** saved as `results/baseline_report.csv` with columns: `property, model_type, MAE, RMSE, R2` (FR-004). *Marked incomplete until implementation.*
- [X] T018a [P] Run `code/verify_log_rotation.py` to verify log rotation logic and archive creation (FR-007).
- [ ] T019 [P] Verify that contract tests T012 and integration test T013 **pass before** baseline report generation (requires T012/T013 completion prior to T016).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently.

---

## Phase 4: User Story 2 - Apply Resampling and Measure Performance Degradation (Priority: P2)

**Goal**: Apply stratified resampling (or fallback), retrain models, and statistically compare performance on the minority subset.

**Independent Test**: Can be fully tested by running the resampling pipeline, producing a comparison table and statistical test results (paired t‑test/Wilcoxon) showing performance difference on the bottom [deferred] subset.

### Tests for User Story 2 (Contract & Integration) ⚠️

- [ ] T020 [P] [US2] Contract test for resampling logic (validates CV constraints against `contracts/resampling.schema.yaml`).
- [X] T021 [P] [US2] Integration test for statistical significance (validates power analysis and p‑value calculation).

### Implementation for User Story 2

- [ ] T022 [US2] Implement `code/resampling.py` with stratified undersampling/oversampling using **dynamic equal‑frequency binning** (default a set of bins) and ensure **real‑data CV ≤ 0.10**.
- [ ] T023 [US2] Implement fallback in `code/resampling.py`: if > 20% data loss or empty bins occur, **switch to cost-sensitive learning (class weights) only**. Enforce **combined CV ≤ 0.30** while still keeping real‑data CV ≤ 0.10. **Note: SMOTE is excluded per plan.md constraints.**
- [ ] T024 [US2] Enforce the CV constraints described above (real ≤ 0.10, combined ≤ 0.30) within the resampling implementation.
- [ ] T025 [US2] Implement `code/training.py` to retrain RF and GB models on the balanced dataset with identical hyperparameters (FR‑004).
- [ ] T026 [US2] Implement `code/evaluation.py` to **isolate the bottom [deferred] of each target property** using quantile thresholds derived from the **FULL dataset** distribution (FR‑010) and calculate per‑bin MAE for this subset.
- [ ] T027 [US2] Implement `code/evaluation.py` to calculate **performance degradation**: `MAE_skewed_minority - MAE_balanced_minority` and write to `results/performance_degradation.csv`. *Marked incomplete until implementation.*
- [ ] T028 [US2] Implement power analysis in `code/evaluation.py` to determine the minimum number of random seeds required for Cohen's d = 0.5, power ≥ 0.8, α = 0.05; output seed count to `results/power_analysis.json`.
- [ ] T029 [US2] Implement paired statistical tests (paired t‑test or Wilcoxon) across the seed count from T028 (**Read seed_count from results/power_analysis.json**), saving results to `results/statistical_test_results.csv` with columns `test_type, p_value, effect_size, seed_count` (FR‑005).
- [ ] T030 [US2] Compute Pearson correlation between **Compositional Imbalance Score** (from T009b) and **performance degradation** (from T027); output to `results/correlation_analysis.csv` with columns `property, score_type, r, p_value` (FR‑012).
- [ ] T031 [US2] Compute Pearson correlation between **Target Imbalance Score** (from T009a) and **performance degradation**; append results to the same `results/correlation_analysis.csv` (FR‑012).
- [ ] T032 [US2] Generate comparison report `results/comparison_report.csv` with columns `property, metric, skewed_value, balanced_value, delta_pct, p_value, effect_size` (US‑2).
- [ ] T033 [P] Verify that contract test T020 and integration test T021 pass after resampling implementation.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently.

---

## Phase 5: User Story 3 - Analyze Feature Importance Distortion via SHAP (Priority: P3)

**Goal**: Generate SHAP values, compare top-ranked feature rankings

The research question is to identify the most influential variables, the method involves ranking features by their contribution scores, and the references include [Citation]., and validate against a synthetic ground‑truth baseline.

**Independent Test**: Can be fully tested by running the SHAP analysis script on trained models and synthetic data, producing a ranked list and visualization of rank shifts.

### Tests for User Story 3 (Contract & Integration) ⚠️

- [ ] T034 [P] [US3] Contract test for SHAP output schema in `tests/contract/test_shap_schema.py` (validates rank‑shift CSV schema).
- [ ] T035 [P] [US3] Integration test for synthetic ground truth validation in `tests/integration/test_shap_validation.py`.

### Implementation for User Story 3

- [ ] T036 [US3] Implement `code/shap_analysis.py` to generate a **synthetic dataset** with known non‑linear feature weights (algorithm: Gaussian noise with fixed seed, `known_weights` vector [0.1, 0.2, ...]), saved as `data/synthetic/ground_truth.parquet` (columns: Magpie descriptors, `target`, `known_weights`) (FR-014). *Ensure `known_weights` are used in T039 for validation.*
- [ ] T037 [US3] Compute SHAP values for both skewed and balanced models, saving to `results/shap_analysis/shap_skewed.npy` and `results/shap_analysis/shap_balanced.npy`.
- [ ] T038 [US3] Rank top‑10 features for each model, calculate **mean rank shift** (ties broken by average rank), and write `results/shap_analysis/rank_shift.csv` containing `feature, rank_skewed, rank_balanced, rank_shift`.
- [ ] T039 [US3] Validate SHAP rankings against the synthetic ground truth (load `data/synthetic/ground_truth.parquet` column `known_weights`), compare `rank_shift.csv` with `known_weights`, output validation summary to `results/shap_analysis/shap_validation.json`.
- [ ] T040 [US3] Visualize significant rank changes: create `results/shap_analysis/rank_shift_plot.png` (bar plot of rank shift) and `results/shap_analysis/feature_importance_bar.png` (side‑by‑side importance bars) using matplotlib.
- [ ] T041 [US3] Assemble SHAP comparison report in `results/shap_analysis/shap_report.md` linking to CSVs and PNGs.
- [ ] T042 [P] Verify contract test T034 and integration test T035 pass after SHAP implementation.

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
- [ ] T047 [P] Execute the full pipeline using command `python code/main.py --full-pipeline`, ensure total runtime ≤ 6 hours, and save execution log to `results/validation_log.txt` containing runtime, exit code, and pass/fail flag (verify Constraint‑001). *Prerequisite: T016, T027, T030 must be complete and artifacts generated.*
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
- All Foundational tasks marked [P] can run in parallel (within Phase 2), **except T010b which must complete before T012/T014/T020**.
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
- T010b must complete before T012, T014, and T020 can run (schema generation prerequisite).
- T012 and T014 depend on T010b.
- T020 depends on T010b.
- T029 depends on T028 (reads seed count from `results/power_analysis.json`).
- T047 depends on completion of T016, T027, and T030.

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