# Tasks: Predicting Cognitive Fatigue from Resting-State EEG Complexity

**Input**: Design documents from `/specs/001-cognitive-fatigue-eeg-complexity/`
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

- [ ] T001 Create project structure per implementation plan
- [ ] T002 Initialize Python 3.11 project with pinned dependencies in `code/requirements.txt`
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Create `code/config.yaml` with pipeline parameters (filter cutoffs 1-40Hz, artifact threshold ±100µV, random seeds)
- [ ] T005 [P] Create skeleton file `code/download.py` (empty or with docstrings only)
- [ ] T006 [P] Create skeleton file `code/preprocess.py` (empty or with docstrings only)
- [ ] T007 [P] Create skeleton file `code/features.py` (empty or with docstrings only)
- [ ] T008 [P] Create skeleton file `code/analysis.py` (empty or with docstrings only)
- [ ] T009 [P] Create base data models for `EEGSegment` and `ComplexityMetric` in `code/models/`
- [ ] T010 [P] Setup logging infrastructure to track participant exclusion and artifact rejection reasons

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Retrieval and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Retrieve clean EEG data from public sources and preprocess to remove artifacts/line noise

**Independent Test**: Run preprocessing on a single sample file; verify 50Hz line noise peak is attenuated by >20dB in output spectrum.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T011 [P] [US1] Unit test for bandpass filter attenuation in `tests/unit/test_preprocess.py`
- [ ] T012 [P] [US1] Integration test for data download and checksum verification in `tests/integration/test_download.py`

### Implementation for User Story 1

- [ ] T013 [US1] Implement `code/download.py` to fetch 'EEG Motor Movement/Imagery Dataset' (PhysioNet ID: `eegmmidb`, URL: `). Validate presence of both resting-state EEG and paired pre/post fatigue ratings per FR-001. Halt with exit code 1 and log `validation_report.json` if variables missing.
- [ ] T014 [US1] Implement `code/preprocess.py` to apply a 1-40 Hz bandpass filter using MNE-Python per FR-002.
- [ ] T015 [US1] Implement artifact rejection logic in `code/preprocess.py` to exclude epochs >±100µV and segments <120 seconds per FR-002 and Edge Cases. Log exclusion counts and reasons.
- [ ] T016 [US1] Add error handling for missing fatigue variables with clear error messages listing available variables (integrated into T013).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Complexity Feature Extraction (Priority: P2)

**Goal**: Calculate Lempel-Ziv complexity and permutation entropy for resting-state segments

**Independent Test**: Run complexity calculation on a synthetic signal with known properties; verify output values fall within expected ranges.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T017 [P] [US2] Unit test for LZC calculation on known signal in `tests/unit/test_features.py`
- [ ] T018 [P] [US2] Unit test for permutation entropy on known signal in `tests/unit/test_features.py`

### Implementation for User Story 2

- [ ] T019 [P] [US2] Implement `code/features.py` to calculate Lempel-Ziv complexity per channel per FR-003. Output to `data/processed/lzc_metrics.csv`.
- [ ] T020 [P] [US2] Implement `code/features.py` to calculate Permutation Entropy per channel per FR-003. Output to `data/processed/pe_metrics.csv`.
- [ ] T021 [US2] Implement segment extraction logic in `code/features.py` to ensure only segments ≥120 seconds (pre-filtered in T015) are processed. Log rejected segments.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Correlation Analysis and Reporting (Priority: P3)

**Goal**: Correlate complexity metrics with fatigue scores, apply corrections, and generate report

**Independent Test**: Run analysis on mock dataset with known correlation values; verify reported p-values and coefficients match mock truth.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T022 [P] [US3] Unit test for Benjamini-Hochberg correction implementation in `tests/unit/test_analysis.py`
- [ ] T023 [P] [US3] Integration test for full analysis pipeline on mock data in `tests/integration/test_analysis.py`

### Implementation for User Story 3

- [ ] T024 [US3] Implement `code/analysis.py` validation: Check for columns [pre_fatigue, post_fatigue, pre_eeg_id, post_eeg_id] in the metadata dataframe. If missing, write `validation_report.json` with error details and exit with code 1 (per FR-004 hard requirement). No fallback mode.
- [ ] T025 [P] [US3] Implement `code/analysis.py` for Pearson/Spearman correlation between complexity changes (delta) and fatigue delta scores per FR-004.
- [ ] T026 [US3] Implement Benjamini-Hochberg correction for multiple comparisons across electrodes per FR-005.
- [ ] T027 [US3] Implement sensitivity analysis at p≤0.05 and p≤0.01 thresholds with result table per FR-006. Output table to `data/analysis/sensitivity_table.csv`.
- [ ] T028 [US3] Generate final report with statistical significance, effect sizes, and limitations per US-3.
- [ ] T029 [US3] Add collinearity diagnostics (VIF < 5) check if metrics are combined per SC-004.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T030 [P] Documentation updates in `docs/` covering pipeline parameters and data sources
- [ ] T031 Code cleanup and refactoring for CPU efficiency (memory ≤7GB, runtime ≤6h)
- [ ] T032 Performance optimization for large EEG datasets
- [ ] T033 [P] Additional unit tests for edge cases (missing data, artifact rejection) in `tests/unit/`
- [ ] T034 Security hardening for data handling (PII scan implementation)
- [ ] T035 Run `quickstart.md` validation to ensure pipeline executes on CPU-only CI

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

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for bandpass filter attenuation in tests/unit/test_preprocess.py"
Task: "Integration test for data download and checksum verification in tests/integration/test_download.py"

# Launch all models for User Story 1 together:
Task: "Implement code/download.py to fetch real dataset"
Task: "Implement code/preprocess.py to apply 1-40Hz bandpass filter"
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
- **Critical**: All tasks must run on CPU-only CI (limited cores, constrained RAM, no GPU)
- **Critical**: No synthetic/fake data allowed; must use real datasets from verified sources
- **Critical**: Specific dataset 'EEG Motor Movement/Imagery Dataset' (PhysioNet) is mandated for T013.
- **Critical**: No fallback to cross-sectional analysis; system must halt if paired data is missing (T024).