# Tasks: Investigating the Influence of Network Topology on Spontaneous Brain Activity Patterns

**Input**: Design documents from `/specs/001-gene-regulation/`
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

- [ ] T001 Create project directory structure (`code/`, `data/`, `contracts/`, `tests/`) as per implementation plan.
- [ ] T002 Create `requirements.txt` pinning all dependencies (nilearn, networkx, scikit-learn, pandas, numpy, statsmodels, scipy, pyyaml).
- [ ] T003 [P] Configure linting (flake8/pylint) and formatting (black) tools in `pyproject.toml` or `.pre-commit-config.yaml`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement `code/config.py` for paths, seeds, and baseline parameters (30 TR window, 20 TR sensitivity, k=5).
- [X] T005 [P] Implement `code/config.py` hyperparameters section for density thresholds and statistical alpha levels.
- [ ] T006 [P] Create `code/preprocess/__init__.py` and data loading utilities for HCP OpenNeuro data (dMRI/fMRI).
- [X] T007 [P] Implement `code/preprocess/structural.py` skeleton with placeholder for graph metric calculation.
- [X] T008 [P] Implement `code/preprocess/functional.py` skeleton for sliding-window and state extraction.
- [X] T009 [P] Create `code/analysis/correlation.py` skeleton for statistical testing.
- [X] T010 [P] Create `code/reports/generate_report.py` skeleton for final output.
- [ ] T011 [P] Setup `data/` directory structure (raw, processed, logs) and `contracts/` schema files (`dataset.schema.yaml`, `output.schema.yaml`).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Compute Structural and Dynamic Graph Metrics (Priority: P1) 🎯 MVP

**Goal**: Derive quantitative topological metrics (global efficiency, average clustering, modularity) from dMRI and dynamic functional states (dwell time, visited states) from fMRI for a cohort.

**Independent Test**: Run pipeline on a single subject's preprocessed HCP data; verify output JSON contains non-null values for structural global efficiency, clustering, modularity, and dynamic state dwell times.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [~] T012 [P] [US1] Unit test for `code/preprocess/structural.py` graph metric calculation in `tests/unit/test_structural.py`.
- [X] T013 [P] [US1] Unit test for `code/preprocess/functional.py` k-means state extraction in `tests/unit/test_functional.py`.
- [X] T014 [P] [US1] Integration test for single-subject pipeline in `tests/integration/test_single_subject.py`.

### Implementation for User Story 1

- [X] T015 [US1] Implement structural graph metric calculation (global efficiency, clustering, modularity) in `code/preprocess/structural.py` using NetworkX. Handle sparsity >90% exclusion.
- [X] T016 [US1] Implement sliding-window correlation in `code/preprocess/functional.py` with **strict parameters**: 30 TR window, 1 TR step, and **concatenating these windowed matrices across all subjects** before k-means clustering.
- [X] T017 [US1] Implement **Leave-One-Out (LOO) K-Means (k=5)** clustering for dynamic states in `code/preprocess/functional.py`. **Algorithm**: For each subject `i`, centroids must be calculated by clustering the windowed matrices of **all subjects j != i** (excluding the target subject) to derive centroids, then assign subject `i`'s windows to these centroids. **Must run sequentially** to ensure strict subject isolation during centroid derivation and prevent circular correlation (Constitution Principle VI).
- [X] T018 [US1] Implement per-subject dynamic metric calculation (number of visited states, mean dwell time) in `code/preprocess/functional.py`.
- [~] T019 [US1] Implement batch processing logic in `code/main.py` to aggregate metrics into `data/processed/structural_metrics.csv` and `data/processed/dynamic_metrics.csv`. **Dependency**: This task relies on the schema defined in `contracts/output.schema.yaml` (set up in Task T011 in Phase 2) to ensure correct CSV structure.
- [ ] T020 [US1] Implement subject exclusion logging (convergence failure, sparsity) to `data/logs/exclusion_log.json`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Perform Structure-Function Correlation Analysis (Priority: P2)

**Goal**: Statistically correlate structural topological metrics with dynamic functional metrics, applying FDR correction.

**Independent Test**: Run correlation script on aggregated CSV; verify output includes correlation matrix (r, p-values) and FDR-corrected flags.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T021 [P] [US2] Unit test for normality check (Shapiro-Wilk) and correlation selection in `tests/unit/test_correlation.py`.
- [X] T022 [P] [US2] Unit test for Benjamini-Hochberg FDR correction in `tests/unit/test_correlation.py`.
- [X] T023 [P] [US2] Integration test for end-to-end correlation analysis in `tests/integration/test_correlation.py`.

### Implementation for User Story 2

- [X] T024 [US2] Implement normality testing (Shapiro-Wilk, α=0.05) in `code/analysis/correlation.py` to select Pearson vs. Spearman.
- [X] T025 [US2] Implement correlation calculation between structural and dynamic metrics across the cohort in `code/analysis/correlation.py`.
- [X] T026 [US2] Implement Benjamini-Hochberg FDR correction (q=0.05) on all p-values in `code/analysis/correlation.py`.
- [ ] T027 [US2] Generate `data/processed/correlation_results.csv` containing r-values, raw p-values, and FDR-corrected p-values.
- [~] T028 [US2] Handle edge case: If FDR correction yields zero significant findings, ensure report explicitly states this rather than omitting results.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Generate Robustness and Methodological Reports (Priority: P3)

**Goal**: Verify robustness to parameter choices (window length, threshold density) and ensure "associational" framing.

**Independent Test**: Compare primary report with robustness report; verify "associational" labels and sensitivity tables are present.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T029 [P] [US3] Unit test for sensitivity analysis logic in `tests/unit/test_robustness.py`.
- [X] T030 [P] [US3] Integration test for full robustness report generation in `tests/integration/test_robustness.py`.

### Implementation for User Story 3

- [X] T031 [US3] Implement sensitivity analysis for window length in `code/analysis/robustness.py`. This must explicitly compare the **30 TR baseline** against a **20 TR sensitivity check** as mandated by FR-006 and SC-002.
- [ ] T032 [US3] Implement sensitivity analysis for structural threshold density (±5% variation) in `code/analysis/robustness.py`.
- [ ] T033 [US3] Implement resource usage monitoring (peak RAM, runtime) in `code/main.py` to verify CPU-only constraints (GB/h).
- [ ] T034 [US3] Generate final report in `code/reports/generate_report.py` with explicit "associational" framing (FR-007) and sensitivity tables. **Requirement**: The report MUST explicitly calculate and display the "absolute difference between 30 TR and 20 TR correlation coefficients" to satisfy SC-002.
- [ ] T035 [US3] Validate report against `contracts/output.schema.yaml` to ensure all required fields (r, p, FDR, sensitivity, absolute difference) are present.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T040 [P] Documentation updates in `docs/` and `README.md`.
- [ ] T041 Code cleanup and refactoring for CPU efficiency (ensure no GPU calls).
- [ ] T042 Run `quickstart.md` validation to ensure full pipeline reproducibility.
- [ ] T043 Final review of all reports for "associational" language compliance.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories and revisions being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 and US2 data output
- **Polish (Final Phase)**: Depends on all desired user stories and revisions being complete

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
Task: "Unit test for structural graph metric calculation"
Task: "Unit test for functional state extraction"

# Launch all models for User Story 1 together:
Task: "Implement structural graph metric calculation"
Task: "Implement sliding-window correlation"
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
- **Critical Constraint**: All tasks must run on CPU-only (a limited number of cores, GB RAM). No GPU, no 8-bit quantization, no large LLMs.
- **Data Integrity**: No fake data. All metrics must come from real HCP data fetched via OpenNeuro/URL.
- **Scope Constraint**: Only implement features explicitly mandated by FR-001 through FR-008. No unapproved sensitivity analyses (e.g., tractography confidence) are permitted.