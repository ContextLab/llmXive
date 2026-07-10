# Tasks: The Impact of Emotional Expression in AI Avatars on User Trust

**Input**: Design documents from `/specs/001-emotional-synchrony-trust/`
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

- [ ] T001 Create project structure per implementation plan in `projects/PROJ-344-the-impact-of-emotional-expression-in-ai/` by executing `mkdir -p data/raw data/processed data/features code tests/contract tests/unit tests/integration outputs state` <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested -->
- [X] T002 Initialize Python project with pinned dependencies by generating `code/requirements.txt` containing pinned versions for openface, librosa, scikit-learn, statsmodels, pandas, matplotlib, seaborn, synthpop
- [X] T003 [P] Configure linting and formatting tools by creating `.black` and `.flake8` config files in root

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create static schema definitions in `specs/001-emotional-synchrony-trust/contracts/dataset_schema.yaml` and `contracts/feature_extraction_schema.yaml` based on FR-001 schema requirements
- [X] T005 Implement data validation logic in `code/config.py` and `code/validators.py` to enforce FR-001 (schema check, metadata presence)
- [X] T006 Setup deterministic logging and state tracking by creating `state/` directory and `code/logging_config.py` with specific logging format
- [X] T007 Implement error handling framework by creating `code/utils.py` with a `handle_corrupted_file()` function that logs to logger and returns None for specific error conditions (corrupted media, missing metadata)
- [X] T012c [P] [US1] Implement Controlled Data Collection Protocol by creating `code/data_collection.py` (survey interface, consent capture, anonymization pipeline) and `code/consent_form_template.md` as version-controlled artifacts per Constitution Principle VII and FR-001 fallback

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Core Intra-Modal Consistency Extraction and Correlation (Priority: P1) 🎯 MVP

**Goal**: Download/generate dataset, extract facial/vocal features, compute consistency metric, and calculate Spearman correlation.

**Independent Test**: Run extraction and correlation on a sample; verify output CSV contains interaction IDs, consistency scores, trust scores, and a correlation coefficient with a confidence interval.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Contract test for dataset schema validation in `tests/contract/test_dataset_schema.py` against `contracts/dataset_schema.yaml`
- [ ] T011 [P] [US1] Unit test for cross-correlation logic with mocked time-series from `tests/fixtures/mock_timeseries.npy` in `tests/unit/test_compute_metrics.py`

### Implementation for User Story 1

- [ ] T012 [US1] Implement dataset fetcher in `code/data_loader.py` to download real NAB/UCI data OR generate synthetic time-series via `synthpop` if no real data exists (adhering to FR-001 fallback), calling validator from T005
- [ ] T012b [US1] Implement 'trigger controlled data collection' pathway in `code/data_collection_trigger.py` as a placeholder script that logs a warning and halts execution if real data is required, directing the user to manual IRB steps (do NOT automate IRB logic)
- [~] T013 [P] [US1] Implement facial feature extraction in `code/extract_facial.py` using OpenFace (CPU binary) for video frames
- [~] T014 [P] [US1] Implement vocal prosody extraction in `code/extract_vocal.py` using librosa for pitch, energy, tempo from audio tracks
- [~] T015 [US1] Implement intra-modal consistency metric calculation in `code/compute_metrics.py` (max abs cross-correlation within ±2s lag, normalized) per FR-004, consuming `data/processed/features.csv` produced by T013/T014 (WAIT FOR T013/T014 COMPLETION)
- [~] T016 [US1] Implement Spearman correlation analysis in `code/analyze.py` to compute coefficient and 95% CI per FR-005, reading consistency scores from T015 output
- [~] T017 [US1] Add logic to frame results as associational only (non-causal) in all outputs per SC-004

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Robustness Check with Control Variables (Priority: P2)

**Goal**: Run ordinal regression with control variables (avatar type, duration, difficulty) to verify robustness.

**Independent Test**: Run regression script on extracted features; verify output includes coefficients, p-values, and pseudo R-squared.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [~] T018 [P] [US2] Unit test for ordinal regression model fitting with synthetic metadata in `tests/unit/test_analyze.py`

### Implementation for User Story 2

- [~] T019 [US2] Implement ordinal regression (proportional odds model) in `code/analyze.py` including control variables per FR-006 <!-- ATOMIZE: requested -->
- [~] T020 [US2] Add logic to extract and report p-values and model fit statistics (pseudo R-squared) for consistency and controls
- [~] T021 [US2] Integrate regression results with US1 consistency scores to produce a unified analysis report

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualization and Reporting (Priority: P3)

**Goal**: Generate scatter plot with regression line and 95% CI, ensuring WCAG 2.1 AA contrast.

**Independent Test**: Run plotting script; verify output is a valid PNG with labeled axes, legend, title, and readable font sizes.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [~] T022 [P] [US3] Visual regression test to check file generation and basic structure in `tests/integration/test_visualize.py`

### Implementation for User Story 3

- [~] T023 [US3] Implement scatter plot generation in `code/visualize.py` with consistency on X, trust on Y, regression line, and 95% CI bands per FR-007, including embedded logic to verify WCAG 2.1 AA contrast (≥4.5:1) and minimum font sizes before export per SC-003
- [~] T025 [US3] Export final figure to `outputs/` with proper labeling (title indicating correlation coefficient)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Integration & End-to-End Verification

**Purpose**: Verify the full pipeline runs within constraints and produces valid results.

- [~] T026b [US1] Create `code/benchmark.py` to profile memory/time on N=50 sample and verify constraints before full run (Proactive SC-005 check)
- [~] T026c [US1] Implement resource monitoring and optimization logic in `code/monitor_resources.py` to ensure analysis completes within 6 hours and <7GB RAM based on benchmark results
- [~] T026a [US1] Create `code/run_pipeline.py` to orchestrate the full pipeline execution
- [~] T026 [US1] Execute `code/run_pipeline.py` with N=500 sample and verify outputs exist in `outputs/` (after T026b/T026c pass) <!-- ATOMIZE: requested -->
- [~] T027 [US1] Verify memory usage stays within acceptable peak limits by creating `code/monitor_resources.py` that logs peak RAM usage to `state/memory_log.csv` and asserts <7GB
- [~] T028 [US1] Validate all output artifacts (CSV, JSON, PNG) against their respective schemas and success criteria

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
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
Task: "Contract test for dataset schema validation in tests/contract/test_dataset_schema.py"
Task: "Unit test for cross-correlation logic with mocked time-series in tests/unit/test_compute_metrics.py"

# Launch all extraction tasks for User Story 1 together:
# Note: T013 and T014 are now in separate files (extract_facial.py, extract_vocal.py) producing data artifacts.
Task: "Implement facial feature extraction in code/extract_facial.py using OpenFace (CPU binary)"
Task: "Implement vocal prosody extraction in code/extract_vocal.py using librosa"

# T015 consumes the data artifacts (data/processed/features.csv) produced by T013/T014.
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
 - Developer A: User Story 1 (Extraction & Correlation)
 - Developer B: User Story 2 (Regression)
 - Developer C: User Story 3 (Visualization)
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
- **Critical Constraint**: All data processing must use CPU-only models (OpenFace CPU binary, librosa). No GPU, no 8-bit/4-bit quantization, no deep learning training.
- **Data Integrity**: Do not fabricate input data. Use real datasets (NAB/UCI) or deterministic synthetic generation via `synthpop` only as a fallback per FR-001. If synthetic is insufficient, trigger controlled data collection (T012b) using the protocol defined in T012c.
- **Constitution Compliance**: T012c implements the actual Data Collection Protocol (consent forms, anonymization) as version-controlled artifacts. T012b is a placeholder trigger only; do not automate IRB logic.