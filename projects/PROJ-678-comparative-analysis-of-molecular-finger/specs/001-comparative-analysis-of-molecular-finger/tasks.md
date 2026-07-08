# Tasks: Comparative Analysis of Molecular Fingerprints for Pesticide Toxicity Prediction

**Input**: Design documents from `/specs/001-comparative-analysis-of-molecular-fingerprints/`
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

## Pre-Phase 0: Design Artifacts

**Purpose**: Create foundational design artifacts required as inputs for the main implementation phases.

- [ ] T008 [P] Create `specs/001-comparative-analysis-of-molecular-fingerprints/data-model.md` defining Compound, Fingerprint, Model, and PerformanceMetric entities with schema. This task must be completed before Phase 1.

**Checkpoint**: Design artifacts ready - main implementation can now begin

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project directory structure: `projects/PROJ-678-comparative-analysis-of-molecular-fingerprints/` with subdirs `data/raw/`, `data/processed/`, `code/`, `tests/`. Note: `specs/` is a sibling to `projects/`, not nested inside.
- [ ] T002 Initialize Python project files: `requirements.txt` (pinning rdkit, scikit-learn, pandas, numpy, requests, pytest), `pyproject.toml` (linting config), `README.md`
- [ ] T003 [P] Configure linting (flake8/black) and formatting tools in `pyproject.toml`
- [ ] T004 [P] Create `data/raw/` and `data/processed/` directories with `.gitkeep`
- [X] T005 [P] Implement `code/utils.py` with logging configuration, random seed initialization (seed=42), and environment variable loading
- [~] T006 [P] Create `code/constants.py` with exact variable definitions: `SMARTS_PATTERN = "[P](=O)([O,SC])[O,SC]"` (str), `TANIMOTO_THRESHOLD = 0.85` (float), `MORGAN_RADIUS = 2` (int), `MORGAN_BITS = 2048` (int), `MACCS_BITS = 166` (int), `N_FOLDS = 5` (int). Ensure `code/filter.py` imports and applies this exact constant.
- [~] T007 Setup `tests/` directory structure (`unit/`, `integration/`)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 2: User Story 1 - Data Acquisition and Organophosphate Filtering (Priority: P1) 🎯 MVP

**Goal**: Download Tox21 dataset, filter for organophosphates using SMARTS, and validate labels.

**Independent Test**: Verify `data/processed/organophosphates_filtered.csv` exists, contains only compounds matching the SMARTS pattern, and has non-zero rows for at least one toxicity endpoint.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [~] T009 [P] [US1] Unit test in `tests/unit/test_filter.py::test_smarts_filter_returns_empty_on_no_match` to verify empty list when no compounds match SMARTS. <!-- SKIPPED: YAML+regex parse failed (expected '<document start>', but found '<scalar>'
 in "<unicode string>", line 2, column 3:
 """Unit tests for the SMARTS-based...
 ^) -->
- [~] T010 [P] [US1] Integration test in `tests/integration/test_download.py::test_download_and_checksum_tox21` to verify dataset download and checksum validation.

### Implementation for User Story 1

- [~] T011 [US1] Implement `code/download.py` to fetch Tox21 dataset from HuggingFace `datasets.load_dataset("deepchem/tox21")`, including checksum verification
- [~] T012 [US1] Implement `code/filter.py` to apply SMARTS pattern `[P](=O)([O,SC])[O,SC]` to filter compounds and save to `data/processed/organophosphates_filtered.csv`
- [~] T013 [US1] Implement validation logic in `code/filter.py` to count rows per toxicity endpoint; if sample size < 50, log a "Low Sample Size" warning and skip statistical tests (do not raise error), recording this limitation in `data/processed/filter_log.txt`
- [~] T014 [US1] Add logging for dataset download size, filter counts, and endpoint distribution to `data/processed/filter_log.txt`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 3: User Story 2 - Fingerprint Generation and Model Training (Priority: P2)

**Goal**: Generate Morgan and MACCS fingerprints, perform 5-Fold Greedy Maximal Dissimilarity Split (Tanimoto < 0.85), and train Random Forest models on CPU.

**Independent Test**: Execute training script on a sample subset to verify memory safety, artifact generation, and completion within 60 minutes on 2-core CPU.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [~] T015 [P] [US2] Unit test in `tests/unit/test_fingerprints.py::test_morgan_fingerprint_generation` to verify Morgan fingerprint generation parameters.
- [~] T016 [P] [US2] Unit test in `tests/unit/test_split.py::test_greedy_split_tanimoto_threshold` to verify the greedy split logic maintains Tanimoto < 0.85.

### Implementation for User Story 2

- [~] T017 [US2] Implement `code/fingerprints.py` to generate Morgan (radius=2, 2048 bits) and MACCS (166 bits) fingerprints for all compounds in filtered CSV; implement chunked processing (batch=500) if memory > 7GB
- [~] T018 [US2] Implement `code/split.py` to execute Greedy Maximal Dissimilarity Split (Tanimoto < 0.85) for each of 5 folds: 1) Initialize test set with the compound furthest from the mean; 2) Iterate through remaining compounds, selecting the one with max min-distance to current test set; 3) Add to test set if distance > threshold; 4) Verify test set size >= 20; 5) Halt execution if split cannot achieve 20 samples with Tanimoto < 0.85.
- [ ] T019 [US2] Implement `code/train.py` to train two Random Forest models (100 trees, max_depth=15) per fold (Morgan vs MACCS) using CPU-only constraints (no CUDA)
- [ ] T020 [US2] Save model artifacts and split indices to `data/processed/models/` and `data/processed/splits/`
- [ ] T021 [US2] Add error handling in `code/split.py` to halt execution, log "Insufficient Structural Diversity: Cannot achieve valid split," and output `data/processed/invalid_split_report.md` if the 20-sample threshold with Tanimoto < 0.85 cannot be met.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 4: User Story 3 - Comparative Evaluation and Statistical Validation (Priority: P3)

**Goal**: Evaluate models, perform paired t-test on CV scores, bootstrap confidence intervals, and map feature importance to phosphorus center.

**Independent Test**: Verify final report contains ROC-AUC and PR-AUC for both models, p-value from paired t-test on CV scores, 95% CI, and SC-003 feature importance analysis.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T022 [P] [US3] Unit test in `tests/unit/test_stats.py::test_paired_ttest_cv_scores` to verify paired t-test logic on CV scores.
- [ ] T023 [P] [US3] Unit test in `tests/unit/test_stats.py::test_bootstrap_confidence_interval` to verify bootstrap CI calculation.

### Implementation for User Story 3

- [ ] T024 [US3] Implement `code/evaluate.py` to calculate ROC-AUC, Precision-Recall AUC, and Balanced Accuracy for all 5 folds
- [ ] T025 [US3] Implement `code/evaluate.py` to perform a Paired t-test on the 5-fold CV scores for BOTH ROC-AUC and Precision-Recall AUC differences to determine statistical significance (p < 0.05).
- [ ] T026 [US3] Implement `code/evaluate.py` to generate confidence intervals via bootstrap resampling of the performance difference for BOTH ROC-AUC and Precision-Recall AUC
- [ ] T027 [US3] Implement `code/evaluate.py` to map Morgan fingerprint bits to phosphorus-centered substructures: 1) Identify phosphorus atom (atomic number characteristic of the element) in the molecule; 2) Use RDKit `GetBitInfo` to find bits within a defined radius of the phosphorus atom; 3) Sum the Gini importance for these specific bits; 4) Compare this sum to the total Gini importance.
- [ ] T028 [US3] Implement `code/evaluate.py` to verify SC-003: explicitly check if the sum of Gini importance for Morgan bits (radius 2) exceeds the sum for MACCS keys by ≥ 15%; record result in report.
- [ ] T029 [US3] Generate final report `data/processed/research_results.md` containing: (1) Metrics table (ROC-AUC, PR-AUC, Balanced Accuracy per fold), (2) Statistical Test Results (p-values for ROC-AUC and PR-AUC), (3) SC-003 Analysis (Gini sums and threshold verification)
- [ ] T030 [US3] Add logic to handle "Low Sample Size" warning: if n < 50, skip t-test and report descriptive stats only in `data/processed/research_results.md`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 5: Polish & Cross-Cutting Concerns (Addressing Reviewer Concerns)

**Purpose**: Address specific research-stage reviews regarding measurement uncertainty and calibration (by documenting their exclusion per spec).

- [ ] T031 [US3] Update `specs/001-comparative-analysis-of-molecular-fingerprints/research.md` to explicitly document that measurement uncertainty was not recalculated and no external calibration was performed, citing the spec's 'Assumptions' section as the reason.
- [ ] T032 [P] Documentation updates in `specs/001-comparative-analysis-of-molecular-fingerprints/` including a detailed "Methodology and Constraints" section confirming adherence to the specified training SLA duration and 5-Fold CV
- [ ] T033 Code cleanup and refactoring to ensure all random seeds are reproducible
- [ ] T034 Run `quickstart.md` validation to ensure full pipeline execution within 60 minutes on CI
- [ ] T035 [US3] Implement `code/evaluate.py` to append a section titled "Measurement Uncertainty & Calibration" to `research_results.md` with the exact text: "Measurement uncertainty was not recalculated; toxicity labels treated as ground truth per Spec Assumptions. RDKit fingerprint generation is the industry-standard calibration method." Cite spec.md:Assumptions.

**Checkpoint**: All documentation and reporting requirements met

---

## Dependencies & Execution Order

### Phase Dependencies

- **Pre-Phase 0**: No dependencies - can start immediately
- **Setup (Phase 1)**: Depends on Pre-Phase 0 completion (data-model.md required)
- **User Stories (Phase 2+)**: All depend on Foundational phase completion (Phase 1)
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 5)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 1) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on US1 completion (requires filtered data)
- **User Story 3 (P3)**: Depends on US2 completion (requires trained models and splits)
- **Phase 5 (Review)**: Depends on US3 completion (requires results to analyze)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Pre-Phase 0 tasks marked [P] can run in parallel
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

### Critical Sequential Dependencies (Non-Parallel)

- **US1**: T011 (Download) -> T012 (Filter) -> T013 (Validate)
- **US2**: T017 (Fingerprints) -> T018 (Split) -> T019 (Train)
 - T018 strictly depends on T017 (requires fingerprint vectors for Tanimoto calculation)
 - T019 strictly depends on T018 (requires split indices)
- **US3**: T024 (Metrics) -> T025 (t-test) -> T026 (Bootstrap) -> T027/T028 (Feature Importance) -> T029 (Report)
 - T027/T028 strictly depend on T019 (Train) for Gini importance data
- **Phase 5**: T031/T035 strictly depend on T029 (Report) for content verification

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test in tests/unit/test_filter.py::test_smarts_filter_returns_empty_on_no_match"
Task: "Integration test in tests/integration/test_download.py::test_download_and_checksum_tox21"

# Launch all models for User Story 1 together:
Task: "Implement code/download.py to fetch Tox21 dataset"
Task: "Implement code/filter.py to apply SMARTS pattern"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Pre-Phase 0: Design Artifacts
2. Complete Phase 1: Setup
3. Complete Phase 2: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Pre-Phase 0 -> Setup -> Foundation ready
2. Add User Story 1 -> Test independently -> Deploy/Demo (MVP!)
3. Add User Story 2 -> Test independently -> Deploy/Demo
4. Add User Story 3 -> Test independently -> Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Pre-Phase 0 and Setup together
2. Once Setup is done:
 - Developer A: User Story 1
 - Developer B: User Story 2 (can start after US1 data is ready)
 - Developer C: User Story 3 (can start after US2 models are ready)
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
- **Critical Constraint**: All tasks must run on CPU-only CI (cores, limited RAM, no GPU). Do not use 8-bit quantization or CUDA.
- **Data Integrity**: All data must be real. No synthetic data generation tasks are allowed.
- **Statistical Rigor**: Paired t-test on CV scores MUST apply to both ROC-AUC and Precision-Recall AUC.
- **Success Criteria**: SC-003 ([deferred] Gini improvement) MUST be explicitly verified.
- **Edge Cases**: Handle n < 50 with warning/skip; handle insufficient diversity with halt/invalid report.
- **Reviewer Compliance**: T031 and T035 explicitly document the exclusion of uncertainty analysis per Spec Assumptions.