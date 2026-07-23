# Tasks: Predicting Personal Sleep Quality from Resting‑State fMRI Connectivity

**Input**: Design documents from `/specs/001-predict-sleep-quality/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root
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

- [X] T001a [P] Create directory structure: `code/`, `tests/`, `data/`, `docs/`, `data/raw/`, `data/processed/`, `data/results/`, `code/data/`, `code/modeling/`, `code/utils/`
- [X] T001b [P] Create `code/__init__.py`, `code/data/__init__.py`, `code/modeling/__init__.py`, `code/utils/__init__.py`, `tests/__init__.py`
- [X] T001c [P] Create `requirements.txt` with pinned versions: nilearn, scikit-learn, pandas, numpy, nibabel, networkx, pytest, psutil, seaborn, matplotlib

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin. Includes critical error handling and robustness checks.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002 Implement `code/config.py` with seeds, paths, and hyperparameters (variance_threshold set to a low default, PCA retention defaults, subset size). **MUST**: Define `PERMUTATION_COUNT=1000`, `PERMUTATION_SUBSET_SIZE=100`, `SENSITIVITY_TIMEOUT_HOURS=3`, `GLOBAL_TIMEOUT_HOURS=5`, `EXPECTED_R2_EFFECT_SIZE=0.05`, `POWER_THRESHOLD=0.8`, `ALPHA_LEVEL=0.05`.
- [X] T003 [P] Implement `code/utils/logging.py` for structured JSON logging (FR-010)
- [X] T004 [P] Create `code/utils/metrics.py` for Pearson r, R², and p-value calculation utilities
- [ ] T005 [P] Implement `code/data/download_hcp.py` to fetch HCP minimally preprocessed CIFTI files and `hcp_behavioral_data.csv` using the `hcp_data` package (verified real source). **MUST**: (1) Verify SHA256 checksums of all downloaded files, (2) Record checksums in `data/raw/manifest.json` (Constitution Principle III), (3) Save behavioral data to `data/raw/behavioral/hcp1200_behavioral_data.csv`. **Output**: Verified raw data files and manifest.
- [X] T006 [P] Implement `code/data/preprocess.py` for Schaefer parcellation, nuisance regression, and -0.1 Hz band-pass filtering (FR-001). **MUST**: Accept a list of subject IDs as an argument to process only specific subjects (enables filtering).
- [X] T007 [P] Implement `code/data/feature_engineering.py` for pairwise Pearson correlation, Fisher-z transformation, and upper-triangular vector extraction (FR-002)
- [X] T007b [P] [US1] Implement `code/data/filter.py` to identify subjects with valid Sleep Scores and exclude those with >0.3mm framewise displacement (US1 Acceptance 2). **MUST**: Read `data/raw/behavioral/hcp1200_behavioral_data.csv` and output a list of valid subject IDs to `data/processed/valid_subjects.txt`. **Dependency**: Must run after T005.
- [X] T040 [US1] **MOVED TO PHASE 2**: Implement explicit handling for missing Sleep Scores in `code/data/filter.py`: Explicitly check for `NaN`, `null`, or "N/A" strings in the Sleep Score column and exclude those subjects with a specific log entry. **Rationale**: Addresses the "Edge Case" regarding missing values to ensure SC-001 accuracy. **Dependency**: T007b.
- [X] T041 [US2] **MOVED TO PHASE 2**: Implement "All-Edges-Dropped" guard in `code/modeling/pipeline_factory.py`: Detect if variance thresholding results in zero features and raise a descriptive `RuntimeError` with a suggested threshold adjustment, rather than crashing downstream. **Rationale**: Addresses the edge case where variance < 0.01 removes all edges. **Dependency**: T020a (code structure).
- [X] T039 [US2] **MOVED TO PHASE 2**: Implement strict "Fit-Within-Loop" validation in `code/modeling/pipeline_factory.py`: Add an assertion that fails if `VarianceThreshold` or `PCA` objects are instantiated outside the `train_test_split` loop. **Rationale**: Prevents accidental data leakage if the pipeline is refactored, ensuring FR-003 compliance. **Dependency**: T020a (code structure).
- [X] T043 [US1] **MOVED TO PHASE 2**: Add checksum verification for intermediate `.npy` files: Extend `code/main.py` to compute and log SHA256 hashes for all generated connectivity vectors in `data/processed/` to ensure data integrity across pipeline stages. **Rationale**: Strengthens Constitution Principle III (Data Hygiene) for intermediate artifacts.
- [X] T010 Create `tests/contract/` directory and schema definitions (`dataset.schema.yaml`, `result.schema.yaml`)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - End‑to‑end Data Pipeline (Priority: P1) 🎯 MVP

**Goal**: Obtain preprocessed whole‑brain functional connectivity vectors for every HCP participant with Sleep questionnaire data.

**Independent Test**: Run the data‑pipeline script on the HCP -subject release (restricted to subjects with Sleep questionnaire data) and verify that the expected `.npy` files are produced.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T011 [P] [US1] Contract test for data schema in `tests/contract/test_dataset_schema.py`
- [X] T012 [P] [US1] Integration test for pipeline execution on a single subject in `tests/integration/test_single_subject_pipeline.py`

### Implementation for User Story 1

- [ ] T014 [US1] Implement `code/main.py` orchestration to: (1) download raw data (T005), (2) filter subjects (T007b, T040), (3) preprocess time series (T006) with the filtered list, (4) compute connectivity vectors (T007), and (5) save `.npy` files to `data/processed/`. **MUST**: Include structured JSON logging (seeds, hyperparameters, data hashes) to `data/logs/pipeline_run.json` (FR-010, SC-006) using the utility from T003.
- [X] T016 [US1] Implement error handling to log excluded subjects and abort if success rate <80% (SC-001)
- [X] T017 [P] [US1] Create unit tests for Fisher-z transformation and variance calculations in `tests/unit/test_feature_engineering.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Predictive Modeling & Statistical Validation (Priority: P2)

**Goal**: Train an elastic‑net regression model on connectivity features, evaluate out‑of‑sample performance, and assess statistical significance.

**Independent Test**: Execute the modeling script on the feature matrix produced by US‑1 and confirm that the script returns performance metrics, permutation‑test p‑value, and bootstrap confidence intervals.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Contract test for result schema in `tests/contract/test_result_schema.py`
- [X] T019 [P] [US2] Integration test for nested CV loop on a small synthetic dataset in `tests/integration/test_nested_cv.py`

### Implementation for User Story 2

- [X] T020a [US2] Implement `code/modeling/pipeline_factory.py` to encapsulate the nested CV logic. **MUST**: (1) Accept an optional `data_subset` parameter, (2) **Implement a wrapper class/function that instantiates VarianceThreshold and PCA objects strictly inside the cross-validation training loop** (never outside) to prevent data leakage (Plan: Critical Methodological Correction). **Implementation Pattern**: The wrapper must wrap the `cross_val_predict` or manual loop, ensuring `fit` is called only on training folds. **Dependency**: T039 (Fit-Within-Loop validation).
- [ ] T020 [US2] Implement `code/modeling/train.py` to **invoke T020a** on the full dataset, tune ElasticNetCV, and output `data/processed/predictions.npy` containing outer-fold predictions (shape: [n_subjects, 1]) for T023 (FR-004, FR-005). **MUST**: Explicitly call T020a and save the trained model object to `data/processed/model.pkl`.
- [X] T021 [P] [US2] Implement `code/modeling/select_subset.py` to select a stratified random subset of subjects from the valid list (based on Sleep Score distribution). **Output**: `data/processed/perm_subset_ids.txt`.
- [ ] T037a [US2] **MOVED TO PHASE 4**: Perform a pilot power analysis to validate the 100-subject subset. **MUST**: Use expected effect size `R²=0.05`, alpha level `0.05`, and power threshold `>0.8` (defined in `config.py`) with a theoretical F-test for linear regression to confirm power > 0.8. **Output**: `data/results/power_analysis.json`. **Dependency**: T020a (logic structure).
- [ ] T022a [US2] **NEW**: Update `spec.md` to amend FR-006. **MUST**: (1) Add a section explicitly stating that FR-006 is amended to run 1,000 permutations on a stratified subset of 100 subjects due to compute constraints, (2) Reference the validation from T037a, (3) Ensure the text matches the implementation plan. **Dependency**: T037a.
- [X] T022 [US2] Implement `code/modeling/evaluate.py` to perform **1,000** label permutations on the stratified subset (N=100). **MUST**: (1) Invoke T020a with the subset parameter, (2) Include the entire nested CV pipeline (inner-loop tuning and variance-thresholding) re-run for each permutation, (3) Output null distribution to `data/results/null_distribution.npy`, (4) Reference the spec amendment in **Task T022a** and the **Plan: Critical Methodological Correction** section, (5) Register a signal handler to flush partial results on abort. **Deliverable**: Empirical p-value (validated by T037a and FR-006 Amendment). **Dependency**: T037a, T022a.
- [ ] T023 [US2] Implement `code/modeling/evaluate.py` to perform bootstrap resamples of **aggregated out-of-sample predictions** (loaded from `data/processed/predictions.npy`) to compute a confidence interval for R² (FR-007). **MUST**: Aggregate predictions across all folds before bootstrapping. **Dependency**: T020 (explicitly depends on `predictions.npy` artifact). **Output**: `data/results/bootstrap_ci.json`.
- [ ] T024 [US2] Implement sensitivity analysis in `code/modeling/evaluate.py` to iterate variance thresholds across a range of small values and PCA retention (high variance thresholds). **MUST**: (1) Use the pipeline logic from T020a with full dataset, (2) Enforce a cumulative **3-hour** time budget (defined in `config.py` as `SENSITIVITY_TIMEOUT_HOURS`), (3) **Retry mechanism**: If a grid point fails or times out, re-run only that specific combination, (4) If the grid remains incomplete after retries, explicitly set `status: 'partial'` and list `missing_combinations` in the output, (5) Save partial results to `data/results/sensitivity_partial.json` if aborted, (6) Log `incomplete: true` only if retries are exhausted. **Deliverable**: Full or partial R² grid with explicit state flagging.
- [X] T025 [US2] Implement `code/modeling/evaluate.py` to enforce CPU-only execution, monitor RAM usage (≤6 GB) using `psutil`, and abort if wall-clock time exceeds **5 hours** (defined in `config.py` as `GLOBAL_TIMEOUT_HOURS`) using `signal` module (FR-009). **MUST**: Integrate signal handler logic from T022/T024 to ensure partial results are flushed.
- [ ] T026 [US2] Generate `data/results/ResultReport.json` containing all metrics, p-values, CIs, and sensitivity analysis results (SC-002). **MUST**: (1) Depend on T022, T023, and T024, (2) Handle 'incomplete' state from T024 by merging partial results into the report and setting `status: 'partial'`, (3) Reference the spec amendment from T022a regarding the permutation test. **Dependency**: T022, T023, T024.
- [ ] T026c [US2] Explicitly document in `ResultReport.json` that the permutation-test p-value is an **Override of FR-006** (subset N=100) and reference the validation from T037a and the spec amendment from T022a. **Dependency**: T026 (sub-task).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Interpretation & Visualization (Priority: P3)

**Goal**: Identify which brain connections drive the prediction and visualise them on a cortical surface.

**Independent Test**: Run the feature‑importance script on the trained model from US‑2 and verify that a brain‑surface plot is generated without errors.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T027 [P] [US3] Contract test for visualization output in `tests/contract/test_viz_schema.py`
- [X] T028 [P] [US3] Integration test for plot generation in `tests/integration/test_visualization.py`

### Implementation for User Story 3

- [ ] T029 [US3] Implement `code/modeling/interpret.py` to extract non-zero elastic-net coefficients from the **trained model object** (output of T020) and map them back to brain edges using the Schaefer atlas (FR-008). **MUST**: Explicitly depend on the `model.pkl` artifact from T020.
- [X] T030 [US3] Implement logic to handle failed edge mappings (log warning, continue) (US3 Acceptance 2)
- [ ] T031 [US3] Generate brain-surface plot using Nilearn `plot_connectome` highlighting top N (configurable) predictive connections. **MUST**: Save to `data/results/plot_top_edges.png`. **Handle**: Case where <50 non-zero coefficients exist by plotting all available and logging a warning (SC-004).
- [ ] T032 [US3] Save visualization to `data/results/` as `.png` or `.svg` and log file path in `ResultReport.json`
- [ ] T033 [US3] Verify plot file exists and contains ≥50 edges: Use Python's built-in `xml.etree.ElementTree` to parse SVG and count both `<line>` and `<path>` elements. **MUST**: Log verification result (boolean flag) in `ResultReport.json` and raise error if <50 edges found (SC-004). **Do not use OpenCV.**
- [X] T044 [US3] **MOVED TO PHASE 5**: Implement robust edge-case plotting: Modify `code/modeling/interpret.py` to handle the scenario where the model coefficients are all zero (e.g., due to extreme regularization) by generating a placeholder "No Predictive Edges Found" visualization instead of crashing. **Rationale**: Addresses the edge case of failed mapping or zero coefficients for SC-004.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [X] T034 [P] Update `README.md` with quickstart instructions and environment setup
- [ ] T035 Run contract tests against `ResultReport.json` schema to ensure reproducibility (SC-006)
- [X] T036 Implement Docker containerization strategy (Dockerfile) to guarantee environment reproducibility (Plan: Constitution Check)
- [ ] T037 [US2] Run end-end integration test on `ubuntu-latest` runner to verify a multi-hour time limit and GB RAM constraint (FR-009, SC-005). **MUST**: Produce a GitHub Actions run log URL and a `data/results/runtime_metrics.json` file as proof.
- [ ] T038 Finalize `ResultReport.json` with all metrics and paths; verify no manual entry (Plan: Constitution Check)

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 model output

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
Task: "Contract test for data schema in tests/contract/test_dataset_schema.py"
Task: "Integration test for pipeline execution on a single subject in tests/integration/test_single_subject_pipeline.py"

# Launch all models for User Story 1 together:
Task: "Implement subject filtering logic in code/data/filter.py"
Task: "Implement main.py orchestration"
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
- **Critical**: Variance Thresholding and PCA MUST be fitted within the training fold of every CV iteration to prevent data leakage (Plan: Critical Methodological Correction). This is enforced by T039 and T020a.
- **Critical**: Permutation test runs on a stratified subset of 100 subjects (Amendment to FR-006 via T022a) to meet compute constraint. The resulting p-value is validated by T037a and formally documented in T022a.
- **Critical**: All tasks must run on CPU-only CI (limited vCPU, GB RAM) without GPU dependencies.
- **Critical**: Graceful shutdown logic is integrated into T022 and T024 to ensure partial results are saved if the 5-hour limit is hit.
- **Critical**: T024 enforces a 3-hour sub-budget for the sensitivity grid with retry logic for missing combinations to ensure SC-003 is satisfied with explicit partial-state reporting.
- **Critical**: T005 uses `hcp_data` package and records checksums in `data/raw/manifest.json` to satisfy Constitution Principle III.
- **Critical**: Robustness tasks (T039, T040, T041, T043, T044) have been moved to Phase 2 and Phase 5 to ensure the MVP pipeline handles edge cases immediately, not deferred to post-analysis.
- **Critical**: T022a is a mandatory prerequisite to T022 to ensure spec alignment before code execution.
- **Critical**: Power Analysis (T037a) is now a mandatory pre-requisite in Phase 4 before T022.
