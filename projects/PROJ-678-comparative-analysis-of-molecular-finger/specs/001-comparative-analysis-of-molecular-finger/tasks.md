---
description: "Task list template for feature implementation"
---

# Tasks: Comparative Analysis of Molecular Fingerprints for Pesticide Toxicity Prediction

**Input**: Design documents from `/specs/001-comparative-analysis-of-molecular-fingerprints/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this belongs to (e.g., US1, US2, US3)
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

**Purpose**: Create foundational design artifacts required as inputs for the main implementation phases. **Gate**: This phase must be completed before Phase 1.

- [ ] T008 Create `specs/001-comparative-analysis-of-molecular-fingerprints/data-model.md` defining Compound, Fingerprint, Model, and PerformanceMetric entities with schema. This task is a hard gate for Phase 1 and serves as a prerequisite for T011/T012. **Note**: Although it may be done early, it is NOT parallel with the pipeline start; T011/T012 depend on its completion.

**Checkpoint**: Design artifacts ready - main implementation can now begin

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure. **Gate**: Pre-Phase 0 (T008) must be complete.

- [ ] T001 Create project directory structure: `projects/PROJ-678-comparative-analysis-of-molecular-fingerprints/`. Execute: `mkdir -p data/raw data/processed code tests`. Note: `specs/` is a sibling to `projects/`, not nested inside.
- [X] T002 Initialize Python project files: `requirements.txt` (pinning rdkit, scikit-learn, pandas, numpy, requests, pytest), `pyproject.toml` (linting config), `README.md`
- [X] T003 [P] Configure linting (flake8/black) and formatting tools in `pyproject.toml`
- [X] T004 [P] Create `data/raw/` and `data/processed/` directories with `.gitkeep`. Verify with: `ls -d data/raw data/processed && test -f data/raw/.gitkeep && test -f data/processed/.gitkeep`.
- [X] T005 [P] Implement `code/utils.py` with logging configuration, random seed initialization (seed=42), and environment variable loading
- [X] T006 [US1] Create `code/constants.py` with exact variable definitions: `SMARTS_PATTERN = "[P](=O)([O,SC])[O,SC]"` (str), `TANIMOTO_THRESHOLD = 0.85` (float), `MORGAN_RADIUS = 2` (int), `MORGAN_BITS = 2048` (int), `MACCS_BITS = 166` (int), `N_FOLDS = 5` (int). **MUST**: Ensure `code/filter.py` imports and applies this exact constant from `code/constants.py`; hardcoding the pattern in `code/filter.py` is strictly forbidden. **Dependency**: T011 and T012 depend on T006 completion.
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

- [X] T011 [US1] Implement `code/download.py` to fetch Tox dataset from HuggingFace `datasets.load_dataset("deepchem/tox")`, including checksum verification. **Depends on T008 (Data Model) and T006 (Constants)**.
- [ ] T012 [US1] Implement `code/filter.py` to apply SMARTS pattern `[P](=O)([O,SC])[O,SC]` to filter compounds and save to `data/processed/organophosphates_filtered.csv`. **Depends on T004 (Directory Creation), T008 (Data Model), and T006 (Constants)**.
- [X] T013a [US1] Implement validation logic in `code/filter.py` to count rows per toxicity endpoint. **CRITICAL**:
 - If total sample size < 50, write the exact string "WARNING: Low Sample Size (n < 50)" to `data/processed/filter_log.txt`.
 - If total sample size >= 50, write "status: OK" to `data/processed/filter_log.txt`.
 **Verification**: After execution, `grep "WARNING: Low Sample Size (n < 50)" data/processed/filter_log.txt` must succeed if n < 50. **Deliverable**: File `data/processed/filter_log.txt` must exist and contain either the warning string or "status: OK". **Depends on T012**.
- [ ] T013b [US1] Implement logic in `code/filter.py` to write `data/processed/sample_size_status.json` with `{"status": "SKIP_STATS"}` if sample size < 50, or `{"status": "OK"}` otherwise. **CRITICAL**: This file is the trigger for downstream statistical tasks. **Verification**: `cat data/processed/sample_size_status.json` must return valid JSON. **Depends on T013a**. <!-- FAILED: unspecified -->
- [ ] T014 [US1] Add logging for dataset download size, filter counts, and endpoint distribution to `data/processed/filter_log.txt`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 3: User Story 2 - Fingerprint Generation and Model Training (Priority: P2)

**Goal**: Generate Morgan and MACCS fingerprints. Perform a **Single Greedy Maximal Dissimilarity Split** (Tanimoto < 0.85) for the held-out test set (FR-004), AND perform **K-Fold Cross-Validation on the Full Dataset** for the statistical test (FR-005).

**Independent Test**: Execute training script on a sample subset to verify memory safety, artifact generation, and completion within 60 minutes on 2-core CPU.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T015 [P] [US2] Unit test in `tests/unit/test_fingerprints.py::test_morgan_fingerprint_generation` to verify Morgan fingerprint generation parameters.
- [X] T016 [P] [US2] Unit test in `tests/unit/test_split.py::test_greedy_split_tanimoto_threshold` to verify the greedy split logic maintains Tanimoto < 0.85.

### Implementation for User Story 2

- [X] T017 [US2] Implement `code/fingerprints.py` to generate Morgan (radius=2, 2048 bits) and MACCS (bits) fingerprints for all compounds in filtered CSV; implement chunked processing (batch=500) if memory > 7GB.
- [X] T018a [US2] Implement `code/split.py` to execute a **Single Greedy Maximal Dissimilarity Split** (Tanimoto < 0.85) on the **full filtered dataset** to create a held-out test set (FR-004).
 **Algorithm**:
 1. Initialize test set with the compound furthest from the mean of all compounds.
 2. Iterate through remaining compounds, selecting the one with max min-distance to current test set.
 3. Add to test set if distance > threshold and test set size < 20% of total.
 4. **Verification Logic**:
 - Verify test set size >= 20.
 - Verify NO compound in test set has Tanimoto similarity >= 0.85 to ANY compound in training set.
 - If both pass, set `status: VALID`. Else, set `status: INVALID`.
 **Deliverable**: Write `data/processed/split_indices.json` with schema `{"status": "VALID|INVALID", "test_indices": [int], "train_indices": [int], "tanimoto_min": float, "tanimoto_max": float}`.
 **Dependency**: T017.
- [ ] T018b [US2] Implement `code/split.py` (or a verification script) to read `data/processed/split_indices.json` and verify its content. If status is "INVALID", log "Split Verification Failed: Status is INVALID". **Depends on T018a**.
- [ ] T018c [US2] **Invalid Path Handler**: If `data/processed/split_indices.json` status is "INVALID", write `data/processed/invalid_split_report.md` stating "Statistical comparison is invalid due to insufficient structural diversity." AND write `data/processed/research_results.md` with header "## STATISTICAL COMPARISON INVALID" and the same message. **THEN** exit with code 0 (success) to allow the pipeline to complete. **CRITICAL**: The final `research_results.md` MUST be generated before exit. **CRITICAL**: This task acts as a hard gate; if executed, it terminates the valid path flow for T019/T029a. **Depends on T018b**.
- [ ] T019 [US2] Implement `code/train.py` to train Random Forest models (100 trees, max_depth=15) using **K-Fold Cross-Validation** on the **full filtered dataset** (NOT the split training set) for the statistical test (FR-005).
 **Rationale**: This implements the Corrected Resampled t-test (FR-005/Constitution VII) which requires repeated samples. T018a handles the single split for the descriptive report (FR-004).
 **MUST**: Check `data/processed/split_indices.json` at startup; if status is "INVALID", exit immediately with code 0 (no training).
 **Deliverable**: Write `data/processed/kfold_scores.json` with schema `{"morgan": {"roc_auc": [float,...]}, "maccs": {"roc_auc": [float,...]}}`. These scores are used for the Corrected Resampled t-test.
 **Dependency**: T018a (Success Path).
- [ ] T020 [US2] Implement `code/train.py` to also train a **Final Model** on the **Training Set** (from T018a) and evaluate on the **Test Set** (from T018a) for the descriptive report.
 **Deliverable**: Write `data/processed/final_test_metrics.json` with schema `{"morgan": {"roc_auc": float, "pr_auc": float}, "maccs": {"roc_auc": float, "pr_auc": float}}`.
 **Dependency**: T018a (Success Path).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 4: User Story 3 - Comparative Evaluation and Statistical Validation (Priority: P3)

**Goal**: Evaluate models on the **Single Held-Out Test Set** for the report, perform a Corrected Resampled t-test on the **K-Fold Scores**, generate bootstrap confidence intervals, and map feature importance to phosphorus center.

**Independent Test**: Verify final report contains ROC-AUC for both models on the test set, p-value from paired t-test on **K-Fold ROC-AUC scores**, confidence interval, and SC-003 feature importance analysis.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T022 [P] [US3] Unit test in `tests/unit/test_stats.py::test_paired_ttest_cv_scores` to verify paired t-test logic on **K-Fold scores**.
- [X] T023 [P] [US3] Unit test in `tests/unit/test_stats.py::test_bootstrap_confidence_interval` to verify bootstrap CI calculation.

### Implementation for User Story 3

- [ ] T024 [US3] Implement `code/evaluate.py` to read `data/processed/final_test_metrics.json`.
 **Task**:
 - Calculate ROC-AUC and PR-AUC for the **Single Held-Out Test Set** (descriptive only).
 - Write `data/processed/test_set_descriptive.json` with schema `{"morgan": {"roc_auc": float, "pr_auc": float}, "maccs": {"roc_auc": float, "pr_auc": float}}`.
 **CRITICAL**: PR-AUC is calculated for descriptive purposes ONLY and is **NOT** used for the statistical test.
 **Dependency**: T020.
- [ ] T025a [US3] Implement `code/evaluate.py` to perform the **Corrected Resampled t-test (Nadeau & Bengio)** on the **K-Fold ROC-AUC scores** from `data/processed/kfold_scores.json`.
 **Prerequisite**: Read `data/processed/sample_size_status.json`; if status is "SKIP_STATS", skip execution and log "Statistical test skipped due to low sample size".
 **CRITICAL**: Only ROC-AUC scores are used for this test. PR-AUC is excluded.
 **Dependency**: T019, T013b.
- [ ] T025b [US3] Implement `code/evaluate.py` to generate confidence intervals via **bootstrap resamples** of the **difference** in performance (Morgan - MACCS) for **ROC-AUC** using the **K-Fold scores**.
 **Dependency**: T025a.
- [ ] T025c1 [US3] Implement `code/evaluate.py` to identify the phosphorus atom in the filtered compounds (from T012) and use RDKit `GetBitInfo` to find Morgan bits within radius=2 of the phosphorus atom.
 **Dependencies**: T012 (Filtered Data), T017 (Fingerprints), T019 (Train).
- [ ] T025c2 [US3] Implement `code/evaluate.py` to sum the Gini importance for the identified Morgan bits and calculate the **total Gini importance** for both Morgan and MACCS models (from T019).
 **Dependency**: T025c1.
- [ ] T025c3 [US3] Implement `code/evaluate.py` to compare the Morgan sum to the MACCS sum.
 **CRITICAL**:
 - Calculate **Absolute Sum** of Gini importance for Morgan and MACCS.
 - Calculate `difference_pct = (morgan_sum - maccs_sum) / maccs_sum * 100`.
 - Determine `threshold_met` if `difference_pct >= 15`.
 - **Mean Gini Importance** (normalized by bit count) is **NOT** to be calculated or reported for SC-003 validation.
 - **Deliverable**: Write `data/processed/sc003_analysis.json` with schema `{"morgan_absolute_sum": float, "maccs_absolute_sum": float, "difference_pct": float, "threshold_met": bool}`.
 **Dependency**: T025c2.
- [ ] T029a1 [US3] **Valid Path Gate**: Implement `code/evaluate.py` to read `data/processed/split_indices.json` and `data/processed/sample_size_status.json`.
 **Gate Condition**:
 - If `split_indices.json` status is "INVALID", skip execution (T018c handles this).
 - If `sample_size_status.json` status is "SKIP_STATS", skip statistical tests but generate descriptive report.
 - If both are valid, proceed to generate metrics.
 **Dependency**: T013b, T018a, T024, T025a, T025b, T025c3.
- [ ] T029a2 [US3] **Valid Path**: Generate metrics table with exact Markdown syntax:
 ```markdown
 | Metric | Morgan | MACCS | P-Value | 95% CI |
 |:--- |:---: |:---: |:---: |:---: |
 | ROC-AUC |... |... |... |... |
 ```
 **CRITICAL**: Do NOT include PR-AUC in the table or statistical columns. PR-AUC is only in the descriptive section. Do NOT calculate p-values for PR-AUC. The table columns are for ROC-AUC only.
 **Dependency**: T029a1.
- [ ] T029a3 [US3] **Valid Path**: Write final report `data/processed/research_results.md` containing:
 1. **Descriptive Metrics** (ROC-AUC and PR-AUC on Test Set).
 2. **Statistical Test Results** (p-values for ROC-AUC only).
 3. **SC-003 Analysis** (Gini sums and threshold verification).
 **Condition**: ONLY run if `data/processed/split_indices.json` indicates "VALID" and sample size is sufficient.
 **Dependency**: T029a2.

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
 3. Reiterate that the **statistical methodology** (Corrected Resampled t-test) accounts for the variance in the learning process, while the study remains **purely observational and correlational** as per Spec Assumptions.
 4. **Explicitly state that the study makes NO causal claims** and align the language with the Spec's cautious tone.
 **Note**: Do not generate new methodological notes or data. Strictly document the existing assumptions from the Spec. **Depends on T029a3 (Valid Path) or T018c (Invalid Path)**.

**Checkpoint**: Reviewer concerns fully addressed with transparent documentation and methodological justification.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Pre-Phase 0**: No dependencies - can start immediately. **Must complete before Phase 1**.
- **Setup (Phase 1)**: Depends on Pre-Phase 0 completion (T008 required). **Gate**: T008 must be complete before T001-T007.
- **User Stories (Phase 2+)**: All depend on Foundational phase completion (Phase 1)
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 5)**: Depends on all desired user stories being complete
- **Revision (Phase 6)**: Depends on Phase 5 (T029a) to have generated the initial results report to be updated.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 1) - No dependencies on other stories. **Depends on T008 (Data Model) and T006 (Constants)**.
- **User Story 2 (P2)**: Depends on US1 completion (requires filtered data). **Depends on T004 (Directory Creation) and T006 (Constants)**.
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

- All Setup tasks marked [P] can run in parallel (except T006 which is now sequential).
- All Pre-Phase 0 tasks marked [P] can run in parallel.
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows).
- All tests for a user story marked [P] can run in parallel.
- Models within a story marked [P] can run in parallel.
- Different user stories can be worked on in parallel by different team members.

### Critical Sequential Dependencies (Non-Parallel)

- **US1**: T011 (Download) -> T012 (Filter) -> T013a (Validate) -> T013b (Write Status).
 - T012 depends on T004 (Directory creation), T008 (Data Model), and **T006 (Constants)**.
 - T006 must complete before T012.
- **US2**: T017 (Fingerprints) -> T018a (Single Split) -> T018b (Verify) -> T018c (Invalid Path Halt) OR T019 (K-Fold Train) + T020 (Final Train).
 - T018b strictly depends on T018a (requires split status).
 - T018c strictly depends on T018b (requires verification).
 - T019/T020 strictly depend on T018a (Success Path). If T018c halts, T019/T020 are skipped by runner logic.
 - **T018c is a hard gate**: If T018c halts, T019/T020 and T029a are skipped; T018c generates the final report.
- **US3**: T024 (Test Set Descriptive) -> T025a (t-test on K-Fold) -> T025b (Bootstrap) -> T025c1/2/3 (Feature Importance) -> T029a (Report).
 - T025a/T025b strictly depend on T013b (Sample Size Status) to skip if needed.
 - T025c1 strictly depends on T012 (Filtered Data) and T017 (Fingerprints).
 - T029a1 strictly depends on T013b (Sample Size Status) and T018a (Split) to handle the valid path.
 - **T029a1 is a conditional gate**: It checks T013b for "SKIP_STATS" and T018a for "VALID" before proceeding.
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
- **Statistical Rigor**: Corrected Resampled t-test (Nadeau & Bengio) on **K-Fold ROC-AUC scores** (Full Dataset) MUST apply to ROC-AUC only. **NO PR-AUC** for the t-test.
- **Success Criteria**: SC-003 ([deferred] Gini improvement) MUST be explicitly verified using **Absolute Sum** of Gini Importance (not normalized mean).
- **Edge Cases**: Handle n < 50 with warning/skip (T013a/T013b); handle insufficient diversity with **HALT** (T018c) and invalid report generation (T018c).
- **Reviewer Compliance**: T039 addresses the `marie-curie-simulated` review by confirming the Spec Assumptions are sufficient and no new justification is needed. Tasks T031, T035, T036 have been removed to avoid gold-plating.
- **Revision Compliance**: T018 now strictly enforces the "halt execution" constraint with verification (T018b) before halting (T018c). T018c now generates the final `research_results.md` for the invalid path to ensure the report exists. T029a/T029b logic updated to reflect **K-Fold CV for t-test** and **Single Split for Report**.
- **Methodology**: The project implements a **Single Held-Out Test Set** (FR-004) for the final report and a **K-Fold Cross-Validation** (Full Dataset) for the statistical test (FR-005). This satisfies both the structural constraint and the statistical validity requirement.