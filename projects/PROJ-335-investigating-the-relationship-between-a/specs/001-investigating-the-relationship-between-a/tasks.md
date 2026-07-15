# Tasks: Alpha Oscillations and Working Memory Capacity

**Input**: Design documents from `/specs/001-alpha-oscillations-wm-capacity/`
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

- [X] T001 Create project structure per implementation plan by executing `mkdir -p code data/raw data/processed data/metrics data/results tests/unit tests/integration tests/contract docs` <!-- ATOMIZE: requested -->
- [X] T002 Initialize Python project with pinned dependencies by installing `mne`, `numpy`, `scipy`, `pandas`, `scikit-learn`, `statsmodels`, `pyyaml` and running `pip freeze > code/requirements.txt`
- [X] T003 [P] Configure linting and formatting tools (ruff/black) and pre-commit hooks in `code/.pre-commit-config.yaml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create `code/config.yaml` defining MNE parameters (filter bandpass range, alpha band range), random seeds, and dataset IDs (ds000248)
- [X] T005 [P] Implement base data validation utility in `code/utils/validation.py` to check for required columns (EEG channels, k-scores/d') and halt with specific error codes (FR-006)
- [X] T006 [P] Setup BIDS-compliant directory structure in `data/raw` and metadata handling for OpenNeuro downloads
- [X] T007a [P] Create base data model for `EEG Dataset`, `Alpha Power Metric`, and `PLV Metric` in `code/models/eeg_dataset.py`, `code/models/alpha_power.py`, `code/models/plv_metric.py`
- [X] T007b [P] Create base data model for `Working Memory Capacity` in `code/models/wm_capacity.py` (Key Entity from Spec)
- [ ] T008 Configure logging infrastructure to output structured logs to `data/results/` and console

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Download and Preprocess EEG Datasets (Priority: P1) 🎯 MVP

**Goal**: Download publicly available EEG datasets (ds000248) and preprocess them using MNE-Python (bandpass filter, ICA, epoching) with strict validation.

**Independent Test**: Verify that (1) ds000248 downloads successfully, (2) data is bandpass-filtered (1-40 Hz), (3) ICA artifacts are removed, and (4) epochs are segmented with behavioral scores extracted.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Unit test for dataset validation logic in `tests/unit/test_validation.py` (tests validation utility from T005 for missing behavioral measures)
- [ ] T011 [US1] Integration test for full download and preprocessing pipeline in `tests/integration/test_download_preprocess.py` (Depends on T012-T018 completion) <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested -->

### Implementation for User Story 1

- [ ] T012 [P] [US1] Implement `code/01_download_preprocess.py` to fetch ds000248 from OpenNeuro and save to `data/raw/`
- [ ] T013 [US1] Implement bandpass filtering (1-40 Hz) and re-reference to average mastoids in `code/01_download_preprocess.py`
- [ ] T014 [US1] Implement ICA artifact removal in `code/01_download_preprocess.py` using MNE-Python
- [X] T015 [US1] Implement trial epoching aligned to task events and extraction of behavioral performance scores (k-scores/d') in `code/01_download_preprocess.py`
- [~] T016 [US1] Add validation logic to exit with a failure code if required variables (channels, k-scores) are missing, invoking the utility from T005, and logging 'ERROR: Missing behavioral measures...'
- [~] T017 [US1] Add power analysis check to `code/01_download_preprocess.py`: if N < 30, halt with 'INSUFFICIENT POWER' message; if N=30-52, log warning, write `data/results/power_status.json` with keys `n_count` and `status` set to 'LIMITED', and continue; otherwise proceed.
- [~] T018 [US1] Save preprocessed epochs to `data/processed/` in HDF5/npz format

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Extract Alpha Power and PLV Metrics (Priority: P2)

**Goal**: Compute alpha-band power from frontal/parietal electrodes and pairwise phase-locking values (PLV) between frontal-parietal sites during delay periods.

**Independent Test**: Verify that () alpha power is extracted from F3, F4, Fz, P3, P4, Pz, (2) PLV is computed via Hilbert transform for frontal-parietal pairs, and (3) metrics are stored per participant.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [P] [US2] Unit test for alpha power extraction logic in `tests/unit/test_metrics.py`
- [X] T020 [P] [US2] Unit test for PLV calculation and electrode pair validation in `tests/unit/test_plv.py`

### Implementation for User Story 2

- [X] T021 [P] [US2] Implement alpha-band power extraction from frontal and parietal electrodes, including Fz, Pz, and bilateral homologs. in `code/02_extract_metrics.py`
- [X] T022 [US2] Implement Hilbert transform-based PLV calculation for frontal-parietal electrode pairs in `code/02_extract_metrics.py`
- [~] T023 [US2] Add validation to exit with code 1 if required electrodes (e.g., Pz) are missing, logging 'CRITICAL: Missing required electrode data...'
- [~] T024 [US2] Store alpha power metrics per participant in `data/metrics/alpha_power.csv`
- [~] T025 [US2] Store PLV metrics per participant in `data/metrics/plv.csv` with electrode pair identifiers

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Correlation Analysis and Robustness (Priority: P3)

**Goal**: Perform partial correlations, FDR correction, cross-validation (LOSO), and split-half reliability to validate alpha-WM capacity relationships.

**Independent Test**: Verify that (1) partial correlations are computed, (2) FDR correction is applied, (3) LOSO cross-validation is run, and (4) split-half reliability is reported.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T026 [P] [US3] Unit test for VIF calculation and collinearity handling in `tests/unit/test_collinearity.py`
- [X] T027 [P] [US3] Unit test for FDR correction and correlation thresholding in `tests/unit/test_statistics.py`
- [X] T028 [P] [US3] Integration test for full analysis pipeline in `tests/integration/test_analysis.py`

### Implementation for User Story 3

- [X] T029 [P] [US3] Implement Variance Inflation Factor (VIF) calculation in `code/03_correlation_analysis.py`; if VIF > 5, flag collinearity and prepare PCA components
- [~] T030 [US3] Implement correlation logic: IF VIF > 5, implement PCA components and report joint variance (descriptive only, do NOT claim independent effects); IF VIF <= 5, implement Partial Correlation (controlling for other metric) to disentangle shared variance.
- [X] T031 [US3] Implement FDR (Benjamini-Hochberg) correction for multiple tests (electrodes × metrics) in `code/03_correlation_analysis.py`; include a comment referencing `plan.md` Complexity Tracking section which explicitly rejects Cluster-Based Permutation Testing for discrete electrode-metric pairs.
- [X] T031a [US3] Verify Cluster-Based Permutation is NOT implemented by checking for absence of specific libraries/functions in `code/03_correlation_analysis.py` and ensuring the code comment from T031 is present.
- [X] T032 [US3] Implement Leave-One-Subject-Out (LOSO) cross-validation (Subject-Level only, replacing trial-level per Plan) for correlation model in `code/03_correlation_analysis.py` [FR-008]; note that split-half reliability is handled in T033.
- [ ] T033 [US3] Implement split-half reliability analysis and output robustness metrics in `code/03_correlation_analysis.py`
- [ ] T034 [US3] Compare correlation coefficients to |r| ≥ 0.3 threshold and reliability to ≥0.7 threshold; output JSON to `data/results/threshold_results.json` with keys `threshold_status` (PASS/FAIL), `reliability_status` (PASS/LOW), `r_value`, and `reliability_coeff`.
- [ ] T035 [US3] Generate final report in `data/results/analysis_report.md` summarizing findings, limitations, and associational nature

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T036a [P] Documentation updates: Create `docs/quickstart.md` with run instructions
- [ ] T036b [P] Documentation updates: Create `docs/api.md` with script parameter descriptions
- [ ] T037 Run linter (ruff) and fix all violations in `code/` scripts to ensure clean code state
- [ ] T038 [P] Additional unit tests for edge cases (e.g., N < 30, missing electrodes) in `tests/unit/`
- [ ] T039 [P] Run `quickstart.md` validation to ensure full pipeline executes on GitHub Actions free tier

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
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 metric output

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
Task: "Unit test for dataset validation logic in tests/unit/test_validation.py"
Task: "Integration test for full download and preprocessing pipeline in tests/integration/test_download_preprocess.py" (Note: T011 depends on implementation)

# Launch all models for User Story 1 together:
Task: "Implement dataset fetching in code/01_download_preprocess.py"
Task: "Implement validation utility in code/utils/validation.py"
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