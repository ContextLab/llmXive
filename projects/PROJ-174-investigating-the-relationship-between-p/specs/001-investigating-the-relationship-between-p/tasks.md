# Tasks: Investigating the Relationship Between Pupil Dilation and Cognitive Load During Visual Search

**Input**: Design documents from `/specs/001-pupil-dilation-cognitive-load/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root (per `plan.md` structure)
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

- [X] T001a [P] Create project directories: `code/`, `tests/`, `data/raw/`, `data/processed/`, `results/`, `state/`
- [X] T001b [P] Create `.gitignore` to exclude `data/`, `__pycache__/`, `*.pyc`, `results/`, and `state/`
- [X] T001c [P] Implement `scripts/verify_structure.py` to check directory layout against `plan.md` and generate `state/structure_check.yaml` with status "PASS" or "FAIL"

---

## Phase 2: Foundational (Blocking Prerequisites & Data Verification)

**Purpose**: Core infrastructure, configuration, and the mandatory Data Verification Hard Gate that MUST run before any user story.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. The Data Verification tasks (T002c) act as a hard gate.

### Configuration & Logging

- [X] T002a [P] Create `code/requirements.txt` with pinned versions: `pandas`, `numpy`, `scipy`, `statsmodels`, `scikit-learn`, `mne`, `pyyaml`, `tqdm`, `opencv-python-headless`, `requests`, `datasets`, `python-dotenv`, `radon`
- [X] T002b [P] Setup Python 3.11 virtual environment in `code/` and install dependencies
- [X] T003 [P] Create `code/.flake8` and `code/pyproject.toml` with linting rules (max-line-length=88, etc.); verify by running `black --check code/` and ensuring exit code 0
- [X] T004 [P] Create `code/config.yaml` with keys: `seeds` (int), `thresholds` (dict), `paths` (dict); verify by parsing in a test script `tests/test_config.py`
- [ ] T005 Setup logging infrastructure: Initialize `code/logging_config.py` to write to `code/logs/preprocess.log` and initialize `results/quality_report.csv` with headers `[exclusion_type, count]`; verify by asserting file creation and column presence. **Note: This task must complete before T002c and T017.**
- [ ] T006 [P] Create `code/data_model.py` defining classes: `Dataset(subject_id, trial_id, timestamp, pupil_diameter, x, y, search_time, target_salience, fixation_count)` and `ModelResult(coefficients, std_errors, p_values, log_likelihood)`
- [ ] T007 [P] Implement `code/utils/provenance.py` with functions `hash_file(path)` and `write_meta(path, meta_dict)`; verify by generating `data/raw/*_meta.json` with keys `[hash, timestamp, source]`
- [ ] T008 [P] Configure environment variables: Create `code/.env.example` with keys: `DATA_PATH`, `OPENNEURO_API_KEY`, `LOG_LEVEL`; update `code/main.py` (created in T018) to load these keys via `python-dotenv`; verify script fails gracefully with error message if keys are missing.

### Data Verification Hard Gate (MUST precede US1/US2/US3)

- [X] T002c [P] Implement `code/verify_data_availability.py`: Parse the `# Verified datasets` block in `plan.md`.
 - **Logic**: If the block is empty OR contains ONLY invalid sources (e.g., fMRI datasets like ds001734/2642 identified by content type in plan.md), HALT (Exit 1) with message "ERROR: No verified eye-tracking dataset found. Pipeline cannot proceed."
 - **Logic**: If valid eye-tracking datasets are found, download to `data/raw/`.
 - **Constraint**: Do NOT hardcode specific ID rejections; rely on the content of `plan.md`'s 'Verified datasets' block.
- [ ] T002d [P] Create `generate_synthetic_test_data.py` ONLY for unit tests (flagged `--test-mode`); ensure it is NEVER called by the main pipeline and its output is hashed in `state/test_artifacts.yaml` only.

**Checkpoint**: Foundation ready + Data Verification passed - user story implementation can now begin

---

## Phase 3: User Story 1 - Compute Trial‑wise Pupil‑Load Correlations (Priority: P1) 🎯 MVP

**Goal**: Load raw eye-tracking data, preprocess signals, extract load proxies (including on-the-fly salience if needed), and compute correlations.

**Independent Test**: Run the pipeline on a single dataset and verify output CSV contains required columns and Pearson-r values.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [~] T010 [P] [US1] Unit test for data loader validation in `tests/test_data_loader.py`
- [X] T011 [P] [US1] Unit test for blink interpolation logic in `tests/test_preprocess.py`
- [X] T012 [P] [US1] Integration test for full preprocessing pipeline in `tests/test_pipeline_us1.py`

### Implementation for User Story 1

- [ ] T013 [US1] Implement `code/preprocessing/load_data.py` to ingest raw files from verified eye-tracking sources (configured via `config.yaml` or `verify_data_availability.py` output) and convert to uniform CSV (`timestamp`, `x`, `y`, `pupil_diameter`)
- [X] T014 [US1] Implement `code/preprocessing/filter.py` with blink interpolation and low-pass filter (≤4 Hz) handling missing samples (>30% exclusion)
- [X] T015 [US1] Implement `code/preprocessing/features.py` to compute load proxies: search time, fixation count; **COMPUTE** target salience on-the-fly from stimulus images using Gabor filter bank (4 orientations, 2 scales) if metadata is missing; **IF** neither metadata nor valid image data exists, mark proxy as `UNFULFILLABLE` in output CSV, log specific exclusion reason, and set `status` column to "UNFULFILLABLE" (do NOT skip silently or crash)
- [~] T016 [US1] Implement `code/analysis/correlations.py` to calculate Pearson correlations (peak/mean/quantized vs. proxies) with **Benjamini-Hochberg FDR correction** (replacing Bonferroni) and output adjusted p-values to `results/correlations.csv`
- [~] T017 [US1] Implement quality report generation in `code/preprocessing/filter.py` writing exclusion counts to `results/quality_report.csv` (appending to headers initialized in T005) with columns `[exclusion_type, count]`
- [X] T018 [US1] Create `code/main.py` orchestrator for US1 pipeline execution

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Fit Linear Mixed‑Effects Model (Priority: P2)

**Goal**: Fit LME model predicting pupil metrics from load proxies with subject random intercepts.

**Independent Test**: Execute LME script and verify model summary includes coefficients, SEs, p-values, and likelihood-ratio test.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [P] [US2] Unit test for VIF calculation and collinearity check in `tests/test_analysis.py`
- [X] T020 [P] [US2] Unit test for LME model fitting with missing predictor handling in `tests/test_analysis.py`

### Implementation for User Story 2

- [X] T021 [US2] Extend `code/analysis/lme_model.py` to:
 1. Calculate Variance Inflation Factor (VIF) for *each* predictor.
 2. If any VIF > 5, drop the predictor with the highest VIF and refit.
 3. If target salience is missing (UNFULFILLABLE), fit a reduced model excluding that predictor and log the reduction.
 4. Output fixed-effect estimates, SEs, p-values, and likelihood-ratio test to `results/model_summary.csv`.
 *Note: This task depends on T015 completing feature extraction to determine column availability. US2 cannot start until T015 completes.*
- [X] T022 [US2] Implement collinearity mitigation (VIF > 5 triggers Reduced Model for remaining predictors only) in `code/analysis/lme_model.py`
- [~] T023 [US2] Implement likelihood-ratio test logic comparing nested models
- [ ] T024 [US2] Add validation for sufficient trials per subject (<20 triggers RuntimeError with message "Subject {id} has < 20 trials" unless `config.yaml` aggregation flag is true)
- [ ] T025 [US2] Output fixed-effect estimates, SEs, p-values to `results/model_summary.csv`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Simulated Real‑Time Load Classification Prototype (Priority: P3)

**Goal**: Deploy sliding-window logistic regression classifier and evaluate on held-out data.

**Independent Test**: Run classifier on test set and verify confusion matrix, accuracy, and ROC-AUC are reported.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T026 [P] [US3] Unit test for sliding window data slicing in `tests/test_classifier.py`
- [X] T027 [P] [US3] Unit test for sensitivity analysis logic in `tests/test_classifier.py`

### Implementation for User Story 3

- [X] T028 [US3] Implement `code/classification/classifier.py` with sliding-window logistic regression: use a **fixed-duration lookback window** for feature extraction, but update the classifier every **200ms**; use L2 regularization
- [~] T029 [US3] Implement ground-truth labeling logic: if independent measure absent, label by median split of search time; **REMOVE** "predictive validity" claims from ALL outputs (logs, CSVs); write explicit limitation note to `results/limitations.md` stating "Ground truth is derived from search-time median split; predictive validity claims removed" and label output as "Search-Time Estimation"; **SET** the `status` column in `results/classification_metrics.csv` to `UNVALIDATED` to prevent downstream misinterpretation.
- [X] T030 [US3] Implement `code/classification/evaluate.py` to compute accuracy, precision, recall, ROC-AUC on held-out set
- [ ] T031 [US3] Implement sensitivity analysis sweeping thresholds across the **specific values {0.40, 0.50, 0.60}** as defined in SC-004; output full metric tables AND calculate/report **relative decrease** or **stability** metrics to `results/sensitivity_analysis.csv` with caveat if ground truth is derived from median split
- [~] T032 [US3] Output continuous correlation between predicted probability and search time as auxiliary validation

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T033 [P] Documentation updates: Create `docs/pipeline.md` and update `README.md` with CLI usage and limitations
- [~] T034a [P] Refactor `code/` to reduce cyclomatic complexity of `preprocess.py` and `analysis.py` to < 15; verify by running `radon cc code/` and ensuring all functions score < 15
- [ ] T035a [P] Create `scripts/profile_memory.py` that runs `preprocess.py` and logs peak RAM to `results/memory_profile.csv`; verify script exists and runs successfully
- [~] T036 [P] Additional unit tests for edge cases (corrupted timestamps, missing metadata)
- [~] T037 [P] Run `docs/quickstart.sh` validation: execute `bash docs/quickstart.sh` and verify exit code 0 and presence of `results/correlations.csv`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories (includes Data Verification Hard Gate)
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - **Depends on T015 (US1) completion** to determine data artifact state (target_salience column presence)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

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
Task: "Unit test for data loader validation in tests/test_data_loader.py"
Task: "Unit test for blink interpolation logic in tests/test_preprocess.py"

# Launch all models for User Story 1 together:
Task: "Implement data_loader.py to ingest raw files"
Task: "Implement preprocess.py with blink interpolation"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories, includes Data Verification)
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
- **Critical**: Do not proceed with US1/US2/US3 if T002c fails (invalid dataset detected)
- **Note on T021**: US2 depends on US1's data artifact state; ensure T015 completes before T021 runs.