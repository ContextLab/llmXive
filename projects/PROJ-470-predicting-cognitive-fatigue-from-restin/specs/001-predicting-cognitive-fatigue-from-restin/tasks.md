---
description: "Task list template for feature implementation"
---

# Tasks: Predicting Cognitive Fatigue from Resting-State EEG Complexity

**Input**: Design documents from `/specs/001-cognitive-fatigue-from-restin/`
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
 - Delivered as a MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project directory structure: `projects/PROJ-470-predicting-cognitive-fatigue-from-restin/`, `data/raw/`, `data/processed/`, `code/`, `tests/unit/`, `tests/integration/`, `docs/`. **Verification**: Run `mkdir -p` to create directories, then run `find projects/PROJ-470-predicting-cognitive-fatigue-from-restin -type d` and assert that the following directories exist: `data/raw`, `data/processed`, `code`, `tests/unit`, `tests/integration`, `docs`. Fail if any are missing. <!-- FAILED: unspecified -->
- [X] T002 Create skeleton files: `code/config.yaml`, `code/download.py`, `code/preprocess.py`, `code/features.py`, `code/analysis.py`, `code/report.py`, `code/models/__init__.py`, `docs/README.md`. **Verification**: Run `ls -l` on the `code/` directory and assert that all listed files exist.
- [X] T003 [P] Initialize Python 3.11 virtual environment and create `code/requirements.txt` with pinned dependencies: `mne`, `scikit-learn`, `numpy`, `pandas`, `lempel-ziv-complexity`, `scipy`, `pyyaml`, `pytest`. **Verification**: Run `pip list` in the venv and assert all dependencies are installed with pinned versions.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create `code/config.yaml` with pipeline parameters. **Verification**: Parse `code/config.yaml` and assert it contains the following keys: `filter_low` (value 1), `filter_high` (value 40), `artifact_threshold` (value 100), and `random_seed` (integer).
- [X] T005 [P] Implement logging infrastructure in `code/utils/logging.py` to track participant exclusion and artifact rejection reasons. **Verification**: Run a mock script that triggers a log entry and assert `logs/exclusion_log.csv` is created with the correct format.
- [ ] T006 [P] Create base data models for `EEGSegment` and `ComplexityMetric` in `code/models/`. **Verification**: Import models in a test script and assert classes are defined with expected attributes.
- [X] T029 [P] Run `quickstart.md` validation to ensure pipeline executes on CPU‑only CI. **Verification**: Execute the commands in `docs/quickstart.md` on a local environment or CI runner and assert all steps complete successfully without errors. (Note: This task is moved here from Phase 6 to validate documentation early).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Retrieval and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Retrieve clean EEG data from public sources and preprocess to remove artifacts/line noise

**Independent Test**: Run preprocessing on a single sample file; verify 50Hz line noise peak is attenuated by >20dB in output spectrum.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T007 [P] [US1] Unit test for bandpass filter attenuation in `tests/unit/test_preprocess.py`. **Verification**: Run `pytest tests/unit/test_preprocess.py::test_bandpass_attenuation` and assert it fails initially, then passes after implementation.
- [X] T008 [P] [US1] Integration test for data download and checksum verification in `tests/integration/test_download.py`. **Verification**: Run `pytest tests/integration/test_download.py` and assert it fails initially, then passes after implementation. <!-- FAILED: unspecified -->
- [ ] T027 [P] [US1] Unit tests for edge cases (missing data, analysis mode failures) in `tests/unit/`. Specifically implement:
 - `tests/unit/test_preprocess.py::test_missing_data` – verifies that the preprocessing script raises a clear error when a required EEG file is absent.
 - `tests/unit/test_analysis.py::test_analysis_mode_failure` – verifies that `code/analysis.py` exits with an informative error when neither paired nor baseline data are available.
 **Verification**: Run `pytest tests/unit/` and assert that both new tests execute and pass (i.e., the error‑handling paths are exercised and succeed).

### Implementation for User Story 1

- [X] T009 [US1] Implement `code/download.py` to fetch a public EEG dataset. **CRITICAL**: Before proceeding, the script MUST validate the presence of both resting-state EEG and paired pre/post fatigue ratings per FR-001. The script MUST specifically look for columns named `pre_fatigue` (or similar standard naming) and `post_fatigue` in the metadata. If the dataset lacks the required variables or yields N < 30, the script MUST halt with exit code 1 and log `validation_report.json` with schema: `{ "status": "fail", "available_variables": [...], "participant_count": 0, "message": "Required variables missing" }`. Log specific error: "ERROR: No valid dataset found with required variables."
- [ ] T010 [US1] Implement `code/preprocess.py` to apply a 1–40 Hz bandpass filter and a 50 Hz notch filter to remove line noise using MNE-Python per FR-002. Output preprocessed data to `data/processed/cleaned_eeg.fif`. **Verification**: Run `mne.io.read_raw_fif('data/processed/cleaned_eeg.fif')` and assert file exists. Then, compute the power spectral density and assert the peak at 50Hz is attenuated by >20dB compared to the raw signal. Assert file contains data for ≥30 participants.
- [X] T011 [US1] Implement artifact rejection logic in `code/preprocess.py` to exclude epochs >±100µV and segments <120 seconds per FR-002 and Edge Cases. Log exclusion counts and reasons to `logs/exclusion_log.csv`. **Verification**: Assert `logs/exclusion_log.csv` exists and contains columns `[participant_id, reason, timestamp]`. Additionally, assert that the `reason` column contains valid rejection reasons (e.g., 'amplitude > 100uV', 'segment < 120s').

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Complexity Feature Extraction (Priority: P2)

**Goal**: Calculate Lempel-Ziv complexity and permutation entropy for resting-state segments, ensuring reproducibility and correct artifact generation.

**Independent Test**: Run complexity calculation on a synthetic signal with known properties; verify output values fall within expected ranges.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T012 [P] [US2] Unit test for LZC calculation on known signal in `tests/unit/test_features.py`.
- [X] T013 [P] [US2] Unit test for permutation entropy on known signal in `tests/unit/test_features.py`.

### Implementation for User Story 2

- [ ] T014 [P] [US2] Implement `code/features.py` to calculate Lempel‑Ziv complexity per channel per FR-003. Output to `data/processed/lzc_metrics.csv`. **Schema**: `participant_id` (str), `channel` (str), `lzc_value` (float64, 4 decimal places). **Verification**: Assert `data/processed/lzc_metrics.csv` exists, is non‑empty, and contains the three columns in the specified order. Additionally, run the calculation on a synthetic signal with known LZC properties and assert the output value falls within the expected range. <!-- FAILED: unspecified -->
- [ ] T015 [P] [US2] Implement `code/features.py` to calculate Permutation Entropy per channel per FR-003. Output to `data/processed/pe_metrics.csv`. **Schema**: `participant_id` (str), `channel` (str), `pe_value` (float64, 4 decimal places). **Verification**: Assert `data/processed/pe_metrics.csv` exists, is non‑empty, and contains the three columns in the specified order. Additionally, run the calculation on a synthetic signal with known PE properties and assert the output value falls within the expected range.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Correlation Analysis and Reporting (Priority: P3)

**Goal**: Correlate complexity metrics with fatigue scores, apply corrections, and generate report

**Independent Test**: Run analysis on mock dataset with known correlation values; verify reported p‑values and coefficients match mock truth.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T016 [P] [US3] Unit test for Benjamini‑Hochberg correction implementation in `tests/unit/test_analysis.py`.
- [X] T017 [P] [US3] Integration test for full analysis pipeline on mock data in `tests/integration/test_analysis.py`. <!-- ATOMIZE: requested -->

### Implementation for User Story 3

- [X] T018 [US3] Implement `code/analysis.py` validation: Check for columns `[pre_fatigue, post_fatigue, pre_eeg_id, post_eeg_id]` in the metadata dataframe. If paired data exists, proceed to paired analysis (delta vs delta) using Pearson/Spearman correlation per FR-004. If paired data is missing but baseline fatigue exists, pivot to cross‑sectional analysis (Baseline Complexity vs. Baseline Fatigue) per plan.md Summary. If neither condition is met, write `validation_report.json` with error details and exit with code 1.
- [X] T019 [P] [US3] Implement `code/analysis.py` for Pearson/Spearman correlation between complexity changes (delta) and fatigue delta scores (paired mode) OR baseline complexity vs baseline fatigue (cross‑sectional mode) per FR-004. <!-- FAILED: unspecified -->
- [ ] T020 [US3] Implement Benjamini‑Hochberg correction for multiple comparisons across electrodes per FR-005.
- [X] T021 [US3] Implement sensitivity analysis at p≤0.05 and p≤0.01 thresholds with result table per FR-006. Output table to `data/analysis/sensitivity_table.csv`. **Schema Requirement**: The CSV MUST contain columns: `threshold` (float), `count_significant` (int), `total_electrodes` (int). **Verification**: Assert `data/analysis/sensitivity_table.csv` exists and contains the three specified columns with correct counts.
- [ ] T022 [US3] Generate final report with statistical significance, Pearson/Spearman coefficients, p-values, 95% confidence intervals, and the sensitivity analysis table per US‑3 and FR-004. The report must strictly discuss correlation coefficients, p‑values, and confidence intervals. Output to `docs/final_report.md`. **Verification**: Assert `docs/final_report.md` exists and contains sections for "Correlation Analysis", "Statistical Significance", "Confidence Intervals", and "Sensitivity Analysis".
- [ ] T023 [US3] Add collinearity diagnostics (VIF < 5) check if metrics are combined per SC‑004.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T024 [P] Documentation updates in `docs/` covering pipeline parameters, data sources, and statistical interpretation guidelines.
- [ ] T025 [P] Performance profiling of `code/preprocess.py` and `code/features.py` to identify memory bottlenecks.
- [ ] T026 [P] Implement streaming data loading in `code/preprocess.py` to ensure peak memory usage < 6 GB (targeting DC‑001). **Implementation Detail**: Use MNE-Python's `preload=False` for raw data loading and implement a generator-based iteration pattern to process epochs in chunks, avoiding full dataset loading into RAM.
- [ ] T028 [P] Security hardening for data handling (PII scan implementation).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed) or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on cleaned data from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on features from US2

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
- **Critical**: All tasks must run on CPU‑only CI (limited cores, constrained RAM, no GPU)
- **Critical**: No synthetic/fake data allowed; must use real datasets from verified sources
- **Critical**: T009 implements the mandatory validation logic for paired pre/post fatigue ratings as defined in FR-001.
- **Critical**: T010 specifies the 1–40 Hz bandpass filter and 50 Hz notch filter as required by FR-002 and Constitution Principle VI.
- **Critical**: T018 implements the conditional fallback logic (paired vs. cross‑sectional) as defined in the plan, using Pearson/Spearman correlation as mandated by FR-004.
- **Critical**: T022, T023, T024, etc. respect the spec‑defined deliverables.
- **Critical**: T021 now explicitly defines the schema for the sensitivity analysis table to meet FR-006.
- **Critical**: T026 specifies the use of `preload=False` and generator iteration for streaming.
- **Critical**: T029 has been moved to Phase 2 to resolve the circular dependency with `quickstart.md`.
- **Critical**: Tasks T030, T031, and T032 (Topological attractor analysis) have been removed to strictly adhere to the spec's authorized features (FR-003: LZC and PE only) and eliminate unapproved scope creep.