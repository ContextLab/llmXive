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

 Tasks MUST be organized by user story so each story can be independently completable and testable.
 - Delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Pre-Phase 0: Design Artifacts

**Purpose**: Create foundational design artifacts required as inputs for the main implementation phases.

- [ ] T008 [P] Create `specs/001-comparative-analysis-of-molecular-fingerprints/data-model.md` defining Compound, Fingerprint, Model, and PerformanceMetric entities with schema. This task must be completed before Phase 1 and serves as a prerequisite for T011/T012.

**Checkpoint**: Design artifacts ready - main implementation can now begin

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure. **Gate**: Pre-Phase 0 (T008) must be complete.

- [ ] T001 Create project directory structure: `projects/PROJ-678-comparative-analysis-of-molecular-finger/` with subdirs `data/raw/`, `data/processed/`, `code/`, `tests/`. Note: `specs/` is a sibling to `projects/`, not nested inside.
- [X] T002 Initialize Python project files: `requirements.txt` (pinning rdkit, scikit-learn, pandas, numpy, requests, pytest), `pyproject.toml` (linting config), `README.md`
- [X] T003 [P] Configure linting (flake8/black) and formatting tools in `pyproject.toml`
- [X] T004 [P] Create `data/raw/` and `data/processed/` directories with `.gitkeep`. Verify with: `ls -d data/raw data/processed && test -f data/raw/.gitkeep && test -f data/processed/.gitkeep`.
- [X] T005 [P] Implement `code/utils.py` with logging configuration, random seed initialization (seed=42), and environment variable loading
- [X] T006 [P] Create `code/constants.py` with exact variable definitions: `SMARTS_PATTERN = "[P](=O)([O,SC])[O,SC]" [UNRESOLVED-CLAIM: c_913a59d2 — status=not_enough_info]` (str), `TANIMOTO_THRESHOLD = 0.85 [UNRESOLVED-CLAIM: c_786db302 — status=not_enough_info]` (float), `MORGAN_RADIUS = 2 [UNRESOLVED-CLAIM: c_53f1a499 — status=not_enough_info]` (int), `MORGAN_BITS = 2048 [UNRESOLVED-CLAIM: c_826b935c — status=not_enough_info]` (int), `MACCS_BITS = 166 [UNRESOLVED-CLAIM: c_53ae5ad1 — status=not_enough_info]` (int), `N_FOLDS = 5 [UNRESOLVED-CLAIM: c_59834747 — status=not_enough_info]` (int). **MUST**: Ensure `code/filter.py` imports and applies this exact constant from `code/constants.py`; hardcoding the pattern in `code/filter.py` is strictly forbidden.
- [X] T007 [P] Setup `tests/` directory structure (`unit/`, `integration/`)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 2: User Story 1 - Data Acquisition and Organophosphate Filtering (Priority: P1) 🎯 MVP

**Goal**: Download Tox21 dataset, filter for organophosphates using SMARTS, and validate labels.

**Independent Test**: Verify `data/processed/organophosphates_filtered.csv` exists, contains only compounds matching the SMARTS pattern, and has non-zero rows for at least one toxicity endpoint.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T009 [P] [US1] Unit test in `tests/unit/test_filter.py::test_smarts_filter_returns_empty_on_no_match`. Implement a pytest function that asserts the filtered dataframe is empty when the SMARTS pattern matches no compounds in a mock dataset.
- [X] T010 [P] [US1] Integration test in `tests/integration/test_download.py::test_download_and_checksum_tox21` to verify dataset download and checksum validation.

### Implementation for User Story 1

- [X] T011 [US1] Implement `code/download.py` to fetch Tox dataset from HuggingFace `datasets.load_dataset("deepchem/tox")`, including checksum verification. **Depends on T008 (Data Model)**.
- [ ] T012 [US1] Implement `code/filter.py` to apply SMARTS pattern `[P](=O)([O,SC])[O,SC]` to filter compounds and save to `data/processed/organophosphates_filtered.csv`. **Depends on T004 (Directory Creation) and T008 (Data Model)**.
- [ ] T013a [US1] Implement validation logic in `code/filter.py` to count rows per toxicity endpoint. **CRITICAL**: If total sample size < 50, write the exact string "WARNING: Low Sample Size (n < 50)" to `data/processed/filter_log.txt`. **Verification**: After execution, `grep "WARNING: Low Sample Size (n < 50)" data/processed/filter_log.txt` must succeed if n < 50. **Deliverable**: File `data/processed/filter_log.txt` must contain the exact warning string if n < 50. **Depends on T012**. <!-- FAILED: unspecified -->
- [ ] T013b [US1] Implement logic in `code/filter.py` to write `data/processed/sample_size_status.json` with `{"status": "SKIP_STATS"}` if sample size < 50, or `{"status": "OK"}` otherwise. **CRITICAL**: This file is the trigger for downstream statistical tasks. **Verification**: `cat data/processed/sample_size_status.json` must return valid JSON. **Depends on T013a**. <!-- FAILED: unspecified -->
- [ ] T014 [US1] Add logging for dataset download size, filter counts, and endpoint distribution to `data/processed/filter_log.txt`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 3: User Story 2 - Fingerprint Generation and Model Training (Priority: P2)

**Goal**: Generate Morgan and MACCS fingerprints, perform a **5-Fold Greedy Maximal Dissimilarity Split** (Tanimoto < 0.85) per fold, and train Random Forest models on CPU.

**Independent Test**: Execute training script on a sample subset to verify memory safety, artifact generation, and completion within 60 minutes on 2-core CPU.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T015 [P] [US2] Unit test in `tests/unit/test_fingerprints.py::test_morgan_fingerprint_generation` to verify Morgan fingerprint generation parameters.
- [X] T016 [P] [US2] Unit test in `tests/unit/test_split.py::test_greedy_split_tanimoto_threshold` to verify the greedy split logic maintains Tanimoto < 0.85.

### Implementation for User Story 2

- [X] T017 [US2] Implement `code/fingerprints.py` to generate Morgan (radius=2, 2048 bits) and MACCS (bits) fingerprints for all compounds in filtered CSV; implement chunked processing (batch=500) if memory > 7GB.
- [X] T018a [US2] Implement `code/split.py` to execute **5-Fold Greedy Maximal Dissimilarity Split** (Tanimoto < 0.85): Loop 5 times (fold=0..4). In each iteration: 1) Initialize test set with the compound furthest from the mean of remaining compounds; 2) Iterate through remaining compounds, selecting the one with max min-distance to current test set; 3) Add to test set if distance > threshold; 4) Verify test set size >= 20. Write `data/processed/split_fold_{fold}.json` with schema `{"fold": int, "status": "VALID|INVALID", "test_indices": [int], "train_indices": [int]}`. After the loop, aggregate results into `data/processed/split_summary.json` with schema `{"total_folds": 5, "valid_folds": int, "invalid_folds": int, "status": "VALID|INVALID"}`. If ANY fold fails (status="INVALID"), set `split_summary.json` status to "INVALID". **Depends on T017**.
- [X] T018b [US2] Implement `code/split.py` (or a verification script) to read `data/processed/split_summary.json` and verify its content. If status is "INVALID", log "Split Verification Failed: Status is INVALID". **Depends on T018a**.
- [X] T018c [US2] **Invalid Path Handler**: If `data/processed/split_summary.json` status is "INVALID", write `data/processed/invalid_split_report.md` stating "Statistical comparison is invalid due to insufficient structural diversity." AND write `data/processed/research_results.md` with header "## STATISTICAL COMPARISON INVALID" and the same message. **THEN** exit with code 0 (success) to allow the pipeline to complete. **CRITICAL**: The final `research_results.md` MUST be generated before exit. **Depends on T018b**.
- [X] T019 [US2] Implement `code/train.py` to train two Random Forest models (100 trees, max_depth=15) for **EACH** of the 5 folds defined by T018a. **MUST**: Check `data/processed/split_summary.json` at startup; if status is "INVALID", exit immediately with code 0 (no training). **Depends on T018a** (Success Path).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 4: User Story 3 - Comparative Evaluation and Statistical Validation (Priority: P3)

**Goal**: Evaluate models on the **5-fold CV** results, perform a Corrected Resampled t-test on the k-fold scores, generate bootstrap confidence intervals, and map feature importance to phosphorus center.

**Independent Test**: Verify final report contains ROC-AUC and PR-AUC for both models, p-value from paired t-test on **5-fold scores**, 95% CI, and SC-003 feature importance analysis.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T022 [P] [US3] Unit test in `tests/unit/test_stats.py::test_paired_ttest_cv_scores` to verify paired t-test logic on **5-fold scores**.
- [X] T023 [P] [US3] Unit test in `tests/unit/test_stats.py::test_bootstrap_confidence_interval` to verify bootstrap CI calculation.

### Implementation for User Story 3

- [ ] T024 [US3] Implement `code/evaluate.py` to calculate ROC-AUC, Precision-Recall AUC, and Balanced Accuracy for **each of the 5 folds**. **Deliverable**: Write `data/processed/cv_scores.json` with schema `{"morgan": {"roc_auc": [float,...], "pr_auc": [float,...], "balanced_acc": [float,...]}, "maccs": {...}}`. **Depends on T019**. <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->
- [ ] T025a [US3] Implement `code/evaluate.py` to perform the **Corrected Resampled t-test (Nadeau & Bengio)** on the **5-fold ROC-AUC and PR-AUC scores** from `data/processed/cv_scores.json`. **Prerequisite**: Read `data/processed/sample_size_status.json`; if status is "SKIP_STATS", skip execution and log "Statistical test skipped due to low sample size". **Depends on T024**. <!-- FAILED: unspecified -->
- [X] T025b [US3] Implement `code/evaluate.py` to generate confidence intervals via **1,000 (Wikipedia: Bootstrapping (statistics), https://en.wikipedia.org/wiki/Bootstrapping_(statistics))** bootstrap resamples of the **difference** in performance (Morgan - MACCS) for BOTH ROC-AUC and Precision-Recall AUC using the **5-fold scores**. **Depends on T025a**. <!-- FAILED: unspecified -->
- [ ] T025c1 [US3] Implement `code/evaluate.py` to identify the phosphorus atom in the filtered compounds and use RDKit `GetBitInfo` to find Morgan bits within radius=2 of the phosphorus atom. **Depends on T019**.
- [ ] T025c2 [US3] Implement `code/evaluate.py` to sum the Gini importance for the identified Morgan bits and calculate the **total Gini importance** for both Morgan and MACCS models. **Depends on T025c1**.
- [ ] T025c3 [US3] Implement `code/evaluate.py` to compare the Morgan sum to the MACCS sum. **CRITICAL**: Must calculate **Mean Gini Importance** (Sum / Total Bits: a standard fixed-length vector for Morgan, a standard fixed-length vector for MACCS.) before comparing. Verify if the Morgan Mean exceeds the MACCS Mean by ≥15%. Write the result (sums, means, comparison, threshold check) to `data/processed/sc003_analysis.json`. **Depends on T025c2**.
- [ ] T029a1 [US3] **Valid Path**: Implement `code/evaluate.py` to read `data/processed/split_summary.json`. If status is "VALID", proceed to generate metrics. **Depends on T025a, T025b, T025c3**.
- [ ] T029a2 [US3] **Valid Path**: Generate metrics table with exact Markdown syntax:
 ```markdown
 | Metric | Morgan | MACCS | P-Value | 95% CI |
 |:--- |:---: |:---: |:---: |:---: |
 | ROC-AUC |... |... |... |... |
 | PR-AUC |... |... |... |... |
 ```
 **Depends on T029a1**.
- [ ] T029a3 [US3] **Valid Path**: Write final report `data/processed/research_results.md` containing:
 1. **Metrics table** (from T029a2).
 2. **Statistical Test Results** (p-values for ROC-AUC and PR-AUC).
 3. **SC-003 Analysis** (Gini means and threshold verification).
 **Condition**: ONLY run if `data/processed/split_summary.json` indicates "VALID". **Depends on T029a2**.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 5: Polish & Cross-Cutting Concerns (Addressing Reviewer Concerns)

**Purpose**: Address specific research-stage reviews regarding measurement uncertainty and calibration (by documenting their exclusion per spec).

- [X] T033 Code cleanup and refactoring to ensure all random seeds are reproducible
- [X] T034 Run `quickstart.md` validation to ensure full pipeline execution within 60 minutes on CI

**Checkpoint**: All documentation and reporting requirements met

---

## Phase 6: Revision & Review Response (Addressing `marie-curie-simulated` Concerns)

**Purpose**: Explicitly address the reviewer's request for measurement uncertainty and calibration details by documenting the methodological constraints and standard practices used, ensuring transparency without fabricating data.

- [ ] T039 [P] [US3] Update `specs/001-comparative-analysis-of-molecular-fingerprints/research.md` to include a "Response to Reviewer" subsection. This subsection must:
 1. Acknowledge the reviewer's concern regarding "measurement uncertainty" and "calibration".
 2. State that the Spec Assumptions ("Instrument Precision" and "Algorithm Calibration") explicitly define the methodology: toxicity labels are treated as ground truth (binary, no SD), and RDKit defaults constitute the standard calibration. No additional justification or fabricated methodological notes are required.
 3. Reiterate that the statistical rigor of the study is ensured by the **Corrected Resampled t-test** (Nadeau & Bengio) on the *model predictions*, which accounts for the variance in the learning process.
 **Note**: Do not generate new methodological notes or data. Strictly document the existing assumptions from the Spec. **Depends on T029a3 (Valid Path) or T018c (Invalid Path)**.

**Checkpoint**: Reviewer concerns fully addressed with transparent documentation and methodological justification.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Pre-Phase 0**: No dependencies - can start immediately
- **Setup (Phase 1)**: Depends on Pre-Phase 0 completion (T008 required). **Gate**: T008 must be complete before T001-T007.
- **User Stories (Phase 2+)**: All depend on Foundational phase completion (Phase 1)
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 5)**: Depends on all desired user stories being complete
- **Revision (Phase 6)**: Depends on Phase 5 (T029a) to have generated the initial results report to be updated.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 1) - No dependencies on other stories. **Depends on T008 (Data Model)**.
- **User Story 2 (P2)**: Depends on US1 completion (requires filtered data). **Depends on T004 (Directory Creation)**.
- **User Story 3 (P3)**: Depends on US2 completion (requires trained models and splits). **Depends on T018 (Split)**.
- **Phase 5 (Review)**: Depends on US3 completion (requires results to analyze). **Depends on T029a (Report)**.
- **Phase 6 (Revision)**: Depends on Phase 5 completion.

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

- **US1**: T011 (Download) -> T012 (Filter) -> T013a (Validate) -> T013b (Write Status).
 - T012 depends on T004 (Directory creation) and T008 (Data Model).
- **US2**: T017 (Fingerprints) -> T018a (5-Fold Split) -> T018b (Verify) -> T018c (Invalid Path Halt) OR T019 (Train).
 - T018b strictly depends on T018a (requires split status).
 - T018c strictly depends on T018b (requires verification).
 - T019 strictly depends on T018a (Success Path). If T018c halts, T019 is skipped by runner logic.
 - **T018c is a hard gate**: If T018c halts, T019 and T029a are skipped; T018c generates the final report.
- **US3**: T024 (Metrics) -> T025a (t-test) -> T025b (Bootstrap) -> T025c1/2/3 (Feature Importance) -> T029a (Report).
 - T025a/T025b strictly depend on T013b (Sample Size Status) to skip if needed.
 - T025c1 strictly depends on T019 (Train) for Gini importance data.
 - T029a strictly depends on T018 (Split) to handle the valid path.
- **Phase 5**: T033/T034 strictly depend on T029a (Report) for content verification.
- **Phase 6**: T039 strictly depends on Phase 5 completion.

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
- **Critical Constraint**: All tasks must run on CPU-only CI (cores, limited RAM, no GPU). Do not use low-bit quantization or CUDA.
- **Data Integrity**: All data must be real. No synthetic data generation tasks are allowed.
- **Statistical Rigor**: Corrected Resampled t-test (Nadeau & Bengio) on **5-fold CV scores** MUST apply to both ROC-AUC and Precision-Recall AUC. **NO Single Split** for the t-test.
- **Success Criteria**: SC-003 ([deferred] Gini improvement) MUST be explicitly verified using **Mean** Gini Importance (normalized by bit count).
- **Edge Cases**: Handle n < 50 with warning/skip (T013a/T013b); handle insufficient diversity with **HALT** (T018c) and invalid report generation (T018c).
- **Reviewer Compliance**: T039 addresses the `marie-curie-simulated` review by confirming the Spec Assumptions are sufficient and no new justification is needed. Tasks T031, T035, T036 have been removed to avoid gold-plating.
- **Revision Compliance**: T018 now strictly enforces the "halt execution" constraint with verification (T018b) before halting (T018c). T018c now generates the final `research_results.md` for the invalid path to ensure the report exists. T029a/T029b logic updated to reflect 5-Fold CV.