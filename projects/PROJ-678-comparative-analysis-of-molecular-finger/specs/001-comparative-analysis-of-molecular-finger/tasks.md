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

- [ ] T001 Create project directory structure: `projects/PROJ-678-comparative-analysis-of-molecular-fingerprints/` with subdirs `data/raw/`, `data/processed/`, `code/`, `tests/`. Note: `specs/` is a sibling to `projects/`, not nested inside.
- [X] T002 Initialize Python project files: `requirements.txt` (pinning rdkit, scikit-learn, pandas, numpy, requests, pytest), `pyproject.toml` (linting config), `README.md` [UNRESOLVED-CLAIM: c_ce5dbbdd — status=not_enough_info]
- [X] T003 [P] Configure linting (flake8/black) and formatting tools in `pyproject.toml` [UNRESOLVED-CLAIM: c_4c370b2e — status=not_enough_info]
- [X] T004 [P] Create `data/raw/` and `data/processed/` directories with `.gitkeep`. Verify with: `ls -d data/raw data/processed && test -f data/raw/.gitkeep && test -f data/processed/.gitkeep`.
- [X] T005 [P] Implement `code/utils.py` with logging configuration, random seed initialization (seed=42), and environment variable loading
- [X] T006 [P] Create `code/constants.py` with exact variable definitions: `SMARTS_PATTERN = "[P](=O)([O,SC])[O,SC]"` (str), `TANIMOTO_THRESHOLD = 0.85` (float), `MORGAN_RADIUS = 2` (int), `MORGAN_BITS = 2048` (int), `MACCS_BITS = 166` (int), `N_FOLDS = 5` (int). **MUST**: Ensure `code/filter.py` imports and applies this exact constant from `code/constants.py`; hardcoding the pattern in `code/filter.py` is strictly forbidden.
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

- [X] T011 [US1] Implement `code/download.py` to fetch Tox dataset from HuggingFace `datasets.load_dataset("deepchem/tox21")`, including checksum verification. [UNRESOLVED-CLAIM: c_9f9a71d6 — status=not_enough_info] **Depends on T008 (Data Model)**.
- [ ] T012 [US1] Implement `code/filter.py` to apply SMARTS pattern `[P](=O)([O,SC])[O,SC]` to filter compounds and save to `data/processed/organophosphates_filtered.csv`. [UNRESOLVED-CLAIM: c_8053dd5e — status=not_enough_info] **Depends on T004 (Directory Creation) and T008 (Data Model)**.
- [ ] T013 [US1] Implement validation logic in `code/filter.py` to count rows per toxicity endpoint; if sample size < 50, log a "Low Sample Size" warning and skip statistical tests (do not raise error), recording this limitation in `data/processed/filter_log.txt`. <!-- FAILED: unspecified -->
- [ ] T014 [US1] Add logging for dataset download size, filter counts, and endpoint distribution to `data/processed/filter_log.txt`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 3: User Story 2 - Fingerprint Generation and Model Training (Priority: P2)

**Goal**: Generate Morgan and MACCS fingerprints, perform 5-Fold Greedy Maximal Dissimilarity Split (Tanimoto < 0.85), and train Random Forest models on CPU.

**Independent Test**: Execute training script on a sample subset to verify memory safety, artifact generation, and completion within 60 minutes on 2-core CPU. [UNRESOLVED-CLAIM: c_3ec400e8 — status=not_enough_info]

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T015 [P] [US2] Unit test in `tests/unit/test_fingerprints.py::test_morgan_fingerprint_generation` to verify Morgan fingerprint generation parameters.
- [X] T016 [P] [US2] Unit test in `tests/unit/test_split.py::test_greedy_split_tanimoto_threshold` to verify the greedy split logic maintains Tanimoto < 0.85.

### Implementation for User Story 2

- [X] T017 [US2] Implement `code/fingerprints.py` to generate Morgan (radius=2, 2048 bits) and MACCS (166 bits) fingerprints for all compounds in filtered CSV; implement chunked processing (batch=500) if memory > 7GB. [UNRESOLVED-CLAIM: c_19b5f778 — status=not_enough_info]
- [ ] T018 [US2] Implement `code/split.py` to execute Greedy Maximal Dissimilarity Split (Tanimoto < 0.85) for each of 5 folds: 1) Initialize test set with the compound furthest from the mean; 2) Iterate through remaining compounds, selecting the one with max min-distance to current test set; 3) Add to test set if distance > threshold; 4) Verify test set size >= 20. **CRITICAL**: If split fails (size < 20 or threshold not met), the script MUST: (a) Log "Insufficient Structural Diversity: Cannot achieve valid split", (b) Write a file `data/processed/invalid_split_report.md` stating that statistical comparison is invalid, (c) Write a status file `data/processed/split_status.json` with `{"status": "INVALID"}`, and (d) **HALT EXECUTION** (exit with code 1). **DO NOT** allow the pipeline to continue to T029a. **Depends on T017**.
- [X] T019 [US2] Implement `code/train.py` to train two Random Forest models (100 trees, max_depth=15) per fold (Morgan vs MACCS) using CPU-only constraints (no CUDA). [UNRESOLVED-CLAIM: c_e943d3db — status=not_enough_info] **Depends on T018 (Success Path)**.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 4: User Story 3 - Comparative Evaluation and Statistical Validation (Priority: P3)

**Goal**: Evaluate models, perform paired t-test on CV scores, bootstrap confidence intervals, and map feature importance to phosphorus center.

**Independent Test**: Verify final report contains ROC-AUC and PR-AUC for both models, p-value from paired t-test on CV scores, 95% CI, and SC-003 feature importance analysis.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T022 [P] [US3] Unit test in `tests/unit/test_stats.py::test_paired_ttest_cv_scores` to verify paired t-test logic on CV scores.
- [X] T023 [P] [US3] Unit test in `tests/unit/test_stats.py::test_bootstrap_confidence_interval` to verify bootstrap CI calculation.

### Implementation for User Story 3

- [X] T024 [US3] Implement `code/evaluate.py` to calculate ROC-AUC, Precision-Recall AUC, and Balanced Accuracy for all 5 folds. <!-- FAILED: unspecified -->
- [X] T025a [US3] Implement `code/evaluate.py` to perform the **Corrected Resampled t-test (Nadeau & Bengio)**. **Prerequisite**: Explicitly collect the ROC-AUC and Precision-Recall AUC scores from ALL 5 folds into two numpy arrays (`morgan_scores`, `maccs_scores`). Perform the t-test on these paired arrays to determine statistical significance (p < 0.05). **Depends on T019**.
- [X] T025b [US3] Implement `code/evaluate.py` to generate confidence intervals via bootstrap resampling of the performance difference for BOTH ROC-AUC and Precision-Recall AUC using the collected test set predictions. **MUST use exactly 1,000 bootstrap resamples** to match Spec precision requirements. <!-- FAILED: unspecified -->
- [ ] T025c [US3] Implement `code/evaluate.py` to perform the SC-003 analysis: 1) Identify phosphorus atom; 2) Use RDKit `GetBitInfo` to find Morgan bits within radius=2; 3) Sum the Gini importance for these bits; 4) Calculate the **total Gini importance** for both Morgan and MACCS models; 5) Compare the Morgan sum to the MACCS sum to verify if the Morgan sum exceeds the MACCS sum by ≥15%. **Write the result (sums, comparison, threshold check) to `data/processed/sc003_analysis.json`**. <!-- ATOMIZE: requested -->
- [X] T029a [US3] **Valid Path**: Generate final report `data/processed/research_results.md` containing:
 1. **Metrics table** with exact Markdown syntax:
 ```markdown
 | Metric | Morgan | MACCS | P-Value | 95% CI |
 |:--- |:---: |:---: |:---: |:---: |
 | ROC-AUC |... |... |... |... |
 | PR-AUC |... |... |... |... |
 ```
 2. **Statistical Test Results** (p-values for ROC-AUC and PR-AUC).
 3. **SC-003 Analysis** (Gini sums and threshold verification).
 **Condition**: ONLY run if `data/processed/split_status.json` indicates "VALID". **Depends on T025a, T025b, T025c**.
- [ ] T029b [US3] **Invalid Path**: If `data/processed/split_status.json` indicates "INVALID" (from T018), generate a report `data/processed/research_results.md` that **DOES NOT** contain statistical tables or p-values. The report must contain a prominent header "## STATISTICAL COMPARISON INVALID" and state: "The Greedy Maximal Dissimilarity Split failed to achieve a Tanimoto threshold < 0.85. Statistical comparison is invalid. See `data/processed/invalid_split_report.md` for details." **Depends on T018 (Failure Path)**.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 5: Polish & Cross-Cutting Concerns (Addressing Reviewer Concerns)

**Purpose**: Address specific research-stage reviews regarding measurement uncertainty and calibration (by documenting their exclusion per spec).

- [ ] T031 [US3] Update `specs/001-comparative-analysis-of-molecular-fingerprints/research.md` to explicitly document that measurement uncertainty was not recalculated and no external calibration was performed, citing `spec.md:Assumptions` sections "Instrument Precision" and "Algorithm Calibration".
- [X] T033 Code cleanup and refactoring to ensure all random seeds are reproducible
- [X] T034 Run `quickstart.md` validation to ensure full pipeline execution within 60 minutes on CI [UNRESOLVED-CLAIM: c_3170cf9f — status=not_enough_info]
- [ ] T035 [US3] Implement `code/evaluate.py` to append a section titled `## Measurement Uncertainty & Calibration` to `research_results.md` with the exact text: "Measurement uncertainty was not recalculated; toxicity labels treated as ground truth per Spec Assumptions. RDKit fingerprint generation is the industry-standard calibration method." Cite spec.md:Assumptions.
- [ ] T036 [US3] Add a "Limitations" section to `research_results.md` explicitly stating that the study does not provide standard deviations for toxicity measurements because the dataset provides binary labels (assay results) rather than continuous quantitative values, and that the "calibration" of fingerprints is inherent to the RDKit implementation standard, not a re-calibrated instrument.

**Checkpoint**: All documentation and reporting requirements met

---

## Phase 6: Revision & Review Response (Addressing `marie-curie-simulated` Concerns)

**Purpose**: Explicitly address the reviewer's request for measurement uncertainty and calibration details by documenting the methodological constraints and standard practices used, ensuring transparency without fabricating data.

- [ ] T039 [P] [US3] Update `specs/001-comparative-analysis-of-molecular-fingerprints/research.md` to include a "Response to Reviewer" subsection. This subsection must:
 1. Acknowledge the reviewer's concern regarding "measurement uncertainty" and "calibration".
 2. State that the Spec Assumptions ("Instrument Precision" and "Algorithm Calibration") explicitly define the methodology: toxicity labels are treated as ground truth (binary, no SD), and RDKit defaults constitute the standard calibration. No additional justification or fabricated methodological notes are required.
 3. Reiterate that the statistical rigor of the study is ensured by the **Corrected Resampled t-test** (Nadeau & Bengio) on the *model predictions*, which accounts for the variance in the learning process.
 **Note**: T037 and T038 (previously planned to generate detailed methodological notes) have been **DELETED** because the Spec Assumptions already provide the necessary directive; generating new justification tasks risks fabricating a methodological constraint where the Spec says none is needed.

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
- **Revision (Phase 6)**: Depends on Phase 5 (T029a/T029b) to have generated the initial results report to be updated.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 1) - No dependencies on other stories. **Depends on T008 (Data Model)**.
- **User Story 2 (P2)**: Depends on US1 completion (requires filtered data). **Depends on T004 (Directory Creation)**.
- **User Story 3 (P3)**: Depends on US2 completion (requires trained models and splits). **Depends on T018 (Split)**.
- **Phase 5 (Review)**: Depends on US3 completion (requires results to analyze). **Depends on T029a/T029b (Report)**.
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

- **US1**: T011 (Download) -> T012 (Filter) -> T013 (Validate)
 - T012 depends on T004 (Directory creation) and T008 (Data Model).
- **US2**: T017 (Fingerprints) -> T018 (Split) -> T019 (Train)
 - T018 strictly depends on T017 (requires fingerprint vectors for Tanimoto calculation)
 - T019 strictly depends on T018 (requires split indices)
 - **T018 is a hard gate**: If T018 fails, T019 and T029a are skipped; T029b is executed.
- **US3**: T024 (Metrics) -> T025a (t-test) -> T025b (Bootstrap) -> T025c (Feature Importance) -> T029a/T029b (Report)
 - T025c strictly depends on T019 (Train) for Gini importance data
 - T029a/T029b strictly depend on T018 (Split) to handle both success and failure paths.
- **Phase 5**: T031/T035/T036 strictly depend on T029a/T029b (Report) for content verification.
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
- **Critical Constraint**: All tasks must run on CPU-only CI (cores, limited RAM, no GPU). Do not use 8-bit quantization or CUDA.
- **Data Integrity**: All data must be real. No synthetic data generation tasks are allowed.
- **Statistical Rigor**: Corrected Resampled t-test (Nadeau & Bengio) on **test set predictions** MUST apply to both ROC-AUC and Precision-Recall AUC.
- **Success Criteria**: SC-003 ([deferred] Gini improvement) MUST be explicitly verified using radius=2.
- **Edge Cases**: Handle n < 50 with warning/skip; handle insufficient diversity with **HALT** and invalid report.
- **Reviewer Compliance**: T031, T035, and T036 explicitly document the exclusion of uncertainty analysis and the nature of "calibration" per Spec Assumptions. T039 addresses the `marie-curie-simulated` review by confirming the Spec Assumptions are sufficient and no new justification is needed.
- **Revision Compliance**: T018 now strictly enforces the "halt execution" constraint. T029a/T029b ensure valid/invalid paths are handled correctly without conflating reports.
