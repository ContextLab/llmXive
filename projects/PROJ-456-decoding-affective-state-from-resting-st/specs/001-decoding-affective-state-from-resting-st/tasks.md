# Tasks: Decoding Affective State from Resting-State EEG Microstates

**Input**: Design documents from `/specs/001-decoding-affective-state/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

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

- [X] T001 Create project structure matching the directory tree defined in `plan.md` Project Structure section: `projects/PROJ-456-decoding-affective-state-from-resting-st/` containing `code/`, `data/`, `tests/`, `docs/`, `state/` subdirectories.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented.
**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T004 [P] Implement data loading utilities in `code/utils.py` to fetch OpenNeuro datasets (ds, ds004137) and verify dataset-variable fit (EEG + Questionnaire). **Note**: Corrects spec typo "ds" to "ds003501". **Output**: `data/raw/dataset_manifest.json` containing verification status and file paths.
- [X] T005 Implement checksum verification logic in `code/utils.py` to record SHA-256 hashes in `state/checksums.json` (schema: `{file_path: hash}`). **Dependency**: T004 (manifest must exist).
- [X] T006 [P] Create configuration file `code/preprocessing.yaml` with keys: `bandpass: {low: 1, high: upper limit}`, `ica`, `reference`. **Deliverable**: The YAML file itself.
- [ ] T007 [P] Implement logging infrastructure in `code/utils.py` to track exclusion logs. **Output**: `data/logs/exclusion.log`.
- [X] T008 [P] Define data classes/entities in `code/entities.py` for `EEGRecording`, `MicrostateSegmentation`, `MicrostateFeatures`, `AffectiveScores`, `CorrelationResult`. **Verification**: Ensure imports succeed in a test script.
- [ ] T023A [US2] Implement `verify_dataset_variable_fit()` in `code/analysis.py` to check for presence of both EEG and Affective scores (PANAS/SAM) AND ≥80% questionnaire response rate per subject (FR-012). **Note**: Includes verification of validated instruments (PANAS/SAM) with citable validation literature. **Output**: `state/dataset_fit_status.json` with `status: 'ready'` or `status: 'skipped'`. **Dependency**: T004.
- [ ] T023A-1 [US2] Implement `verify_affective_instruments()` in `code/analysis.py` to explicitly check for the presence of specific affective instruments (PANAS/SAM) in dataset metadata before proceeding. **Output**: Update `state/dataset_fit_status.json` with instrument verification status. **Dependency**: T004.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - EEG Data Acquisition and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download resting-state EEG, preprocess (filter, ICA, re-reference), and segment into 4 canonical microstates using a pre-defined template to prevent data leakage.

**Independent Test**: Can be fully tested by running the preprocessing pipeline on a single OpenNeuro dataset and verifying output files exist and contain valid numeric data for ≥10 subjects.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T009 [P] [US1] Unit test for bandpass filter design (1-40Hz) in `tests/unit/test_preprocessing.py`
- [X] T010 [P] [US1] Unit test for ICA artifact removal variance retention (≥85%) in `tests/unit/test_preprocessing.py`
- [X] T011 [P] [US1] Unit test for microstate template application (GEV ≥75%) in `tests/unit/test_microstate.py`

### Implementation for User Story 1

- [X] T012 [US1] Implement `download_eeg()` in `code/preprocessing.py` to fetch ds/ds004137 from OpenNeuro with CPU-only streaming
- [X] T013 [US1] Implement `apply_bandpass_filter()` in `code/preprocessing.py` (1-40 Hz) with verification of passband
- [X] T014 [US1] Implement `run_ica_artifact_removal()` in `code/preprocessing.py` using ADJUST/MARA (CPU-compatible) to remove ocular/muscle components <!-- ATOMIZE: requested -->
- [X] T015 [US1] Implement `apply_average_rereference()` in `code/preprocessing.py`
- [ ] T016A-1 [US1] Implement `download_microstate_template()` in `code/microstate.py` to download the pre-defined literature template (Lehmann et al.) from a canonical source (e.g., HuggingFace) to `data/templates/microstate_template.npy`. **Constraint**: No clustering on current data. **Output**: Template array.
- [ ] T016A [US1] [P] Implement `load_microstate_template()` in `code/microstate.py` to load the pre-defined literature template from `data/templates/microstate_template.npy`. **Constraint**: No clustering on current data. **Output**: Template array. **Dependency**: T016A-1.
- [ ] T016B [US1] Implement `apply_microstate_template()` in `code/microstate.py` to apply the loaded template to preprocessed EEG data to assign canonical class labels. **Constraint**: No K-means clustering on current data; use template matching only. **Note**: This is a CPU-tractable alternative to K-means clustering on the full dataset to satisfy FR-003's segmentation intent within hardware constraints. **Verification**: Ensure GEV ≥75% is reported in output metadata. **Dependency**: T016A.
- [X] T017 [US1] Implement `verify_preprocessing_quality()` in `code/preprocessing.py` to check variance retention and GEV thresholds
- [~] T018 [US1] Save preprocessed data and microstate labels to `data/processed/` with metadata flags. **Note**: Includes `analysis_type: associational` flag.
- [ ] T018-1 [US1] Implement `add_associational_flag()` in `code/microstate.py` to explicitly add the `analysis_type: associational` metadata flag to all microstate feature files generated in T018. **Dependency**: T018.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Affective Correlation Analysis (Priority: P2)

**Goal**: Extract temporal features, collect questionnaire scores, compute correlations with Bonferroni correction (switching to Holm/FDR only if VIF > 5).

**Independent Test**: Can be fully tested by running correlation analysis on extracted features and questionnaire scores from ≥10 subjects, verifying that correlation coefficients, p-values, and corrected significance flags are produced.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T019 [P] [US2] Unit test for feature extraction matrix shape (multiple classes × multiple features × N subjects) in `tests/unit/test_analysis.py`
- [ ] T020 [P] [US2] Unit test for Bonferroni and Holm/FDR correction logic in `tests/unit/test_analysis.py`
- [ ] T021 [P] [US2] Unit test for VIF collinearity diagnostics in `tests/unit/test_analysis.py`

### Implementation for User Story 2

- [ ] T022 [P] [US2] Implement `extract_microstate_features()` in `code/microstate.py` (mean duration, occurrence, coverage, transition prob)
- [ ] T023B [US2] Implement `load_affective_scores()` in `code/analysis.py`. **Logic**: Check `state/dataset_fit_status.json` (from T023A). If `status: 'skipped'`, write `state/correlation_status.json` with `status: 'skipped'`, `reason: 'no_linked_data'`, and halt pipeline. **Dependency**: T023A.
- [ ] T024 [US2] Implement `compute_collinearity_diagnostics()` in `code/analysis.py` (VIF calculation) to validate independence assumptions
- [ ] T024-1 [US2] Implement `save_correlation_matrix()` in `code/analysis.py` to explicitly generate and save the correlation matrix as an alternative diagnostic artifact, satisfying FR-013's requirement for collinearity diagnostics beyond just VIF. **Output**: `data/outputs/correlation_matrix.csv`. **Dependency**: T024.
- [ ] T025 [US2] Implement `run_correlation_analysis()` in `code/analysis.py` for Pearson/Spearman (multiple tests across classes, features, and dimensions)
- [ ] T026 [US2] Implement `apply_multiple_comparison_correction()` in `code/analysis.py`. **Logic**: Primary method is Holm-Bonferroni (per Plan.md override of Spec). Secondary is FDR. **Note**: FR-015's 'switch to Holm/FDR if VIF > 5' is now a re-affirmation of the primary method (Holm-Bonferroni) as per Plan.md, ensuring consistent p-value threshold application. **Dependency**: T024.
- [ ] T027 [US2] Implement `compute_effect_sizes()` in `code/analysis.py` (Cohen's d, 95% CI) for significant correlations
- [ ] T028 [US2] Implement `save_correlation_results()` in `code/analysis.py` with `analysis_type: associational` metadata flag

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Validation and Robustness (Priority: P3)

**Goal**: Bootstrap resampling for stability, effect size confidence intervals, and sensitivity analysis.

**Independent Test**: Can be fully tested by running bootstrap resampling on ≥10 subjects and verifying that correlation confidence intervals are computed with variance reported.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T030 [P] [US3] Unit test for bootstrap resampling loop and CI calculation in `tests/unit/test_analysis.py`
- [ ] T031 [P] [US3] Unit test for sensitivity analysis threshold sweep in `tests/unit/test_analysis.py`

### Implementation for User Story 3

- [ ] T032-0 [US3] Implement `check_power_limitation()` in `code/analysis.py` to check if N < 10 subjects. **Logic**: If N < 10, skip bootstrap (T032) and generate a 'power limitation' documentation/log. **Dependency**: T004/T023A. **Output**: `data/outputs/power_limitation_report.json` if N < 10.
- [ ] T032 [US3] Implement `run_bootstrap_resampling()` in `code/analysis.py` (A sufficient number of iterations to ensure convergence.) with N<20 stability warning flag. **Output**: Write `stability_warning: 'N < 20'` to `data/outputs/bootstrap_report.json` if N < 20. **Dependency**: T032-0 (if N >= 10).
- [ ] T032-2 [US3] Implement `add_associational_flag_to_bootstrap()` in `code/analysis.py` to explicitly add the `analysis_type: associational` metadata flag to all bootstrap report files generated in T032. **Dependency**: T032.
- [ ] T033 [US3] Implement `compute_replication_statistics()` in `code/analysis.py` (I² or Q-test) if multiple datasets are available
- [ ] T034 [US3] Implement `run_sensitivity_analysis()` in `code/analysis.py` to sweep thresholds across a range of values. **Requirement**: Report **correlation coefficient stability metrics (mean, std, range)** across the sweep in `data/outputs/sensitivity_report.csv`.
- [ ] T035 [US3] Implement `generate_robustness_report()` in `code/analysis.py` aggregating bootstrap CI, heterogeneity, and sensitivity metrics
- [ ] T036 [US3] Save all validation artifacts to `data/outputs/` with content hashes. **Files**: `data/outputs/bootstrap_results.json`, `data/outputs/sensitivity_report.csv`, `data/outputs/replication_stats.json`. **Note**: Includes `analysis_type: associational` flag.
- [ ] T036-1 [US3] Implement `add_associational_flag_to_sensitivity()` in `code/analysis.py` to explicitly add the `analysis_type: associational` metadata flag to all sensitivity analysis report files generated in T034/T036. **Dependency**: T034.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [ ] T037 [P] [P3] Run integration test for full pipeline (Download → Preprocess → Analyze) in `tests/integration/test_pipeline.py`
- [ ] T038A [P] Update `README.md` with "Prerequisites" section listing Python, mne, and CPU-only constraints.
- [ ] T038B [P] Update `README.md` with "Execution" section detailing pipeline steps and runtime limits.
- [ ] T039 [P] Update `code/requirements.txt` to ensure all dependencies are CPU-only and pinned
- [ ] T040 [P] Run `pytest` suite and ensure [deferred] pass rate on unit and integration tests
- [ ] T041 [P] Verify `data/processed` and `data/outputs` contain valid JSON/CSV with correct schemas
- [ ] T042 [P] Update `state/projects/PROJ-456-decoding-affective-state-from-resting-st.yaml` with `updated_at` and artifact hashes

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data (preprocessed EEG) and T023A (Dataset Fit)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 data (correlation results)

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
Task: "Unit test for bandpass filter design (1-40Hz) in tests/unit/test_preprocessing.py"
Task: "Unit test for ICA artifact removal variance retention (≥85%) in tests/unit/test_preprocessing.py"

# Launch all models for User Story 1 together:
Task: "Implement download_eeg() in code/preprocessing.py"
Task: "Implement apply_bandpass_filter() in code/preprocessing.py"
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