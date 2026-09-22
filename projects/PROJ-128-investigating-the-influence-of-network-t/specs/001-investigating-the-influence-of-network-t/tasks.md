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
- [X] T002 Create `requirements.txt` pinning all dependencies (nilearn, networkx, scikit-learn, pandas, numpy, statsmodels, scipy, pyyaml>=6.0).
- [X] T003 [P] Configure linting (flake8/pylint) and formatting (black) tools in `pyproject.toml` or `.pre-commit-config.yaml`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004a [P] Create `code/config.py` structure for paths and seeds.
- [X] T004b [P] Define hyperparameters in `code/config.py`: `WINDOW_LENGTH_BASELINE = 30` (in TRs), `WINDOW_LENGTH_VALIDATION = 20` (in TRs), `WINDOW_STEP = 1` (in TRs), `K_MEANS_K = 5`, `DENSITY_THRESHOLD_BASELINE = 0.15` (15% density), `DENSITY_THRESHOLD_VARIATIONS = [0.10, 0.15, 0.20]`, `TRACTOGRAPHY_CONFIDENCE_MIN = 0.0`, `TRACTOGRAPHY_CONFIDENCE_MAX = 1.0`, `TRACTOGRAPHY_CONFIDENCE_STEPS = 5`.
- [X] T005 [P] Create `code/preprocess/__init__.py` and data loading utilities for HCP OpenNeuro data (dMRI/fMRI).
- [X] T006 [P] Implement `code/preprocess/structural.py` skeleton with placeholder for graph metric calculation.
- [X] T007 [P] Implement `code/preprocess/functional.py` skeleton for sliding-window and state extraction.
- [X] T008 [P] Create `code/analysis/correlation.py` skeleton for statistical testing.
- [X] T009 [P] Create `code/reports/generate_report.py` skeleton for final output.
- [X] T009a [P] **Create Documentation**: Write `docs/quickstart.md` with instructions to run the full pipeline end-to-end, including environment setup and data fetching.
- [X] T009b [P] [P] Create `docs/quickstart.md` with instructions to run the full pipeline end-to-end.
- [ ] T010 [P] Setup `data/` directory structure (raw, processed, logs) and `contracts/` schema files (`dataset.schema.yaml`, `output.schema.yaml`).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Compute Structural and Dynamic Graph Metrics (Priority: P1) 🎯 MVP

**Goal**: Derive quantitative topological metrics (global efficiency, average clustering, modularity) from dMRI and dynamic functional states (dwell time, visited states) from fMRI for a cohort using Leave-One-Out (LOO) K-Means to ensure independence.

**Independent Test**: Run pipeline on a single subject's preprocessed HCP data; verify output JSON contains non-null values for structural global efficiency, clustering, modularity, and dynamic state dwell times.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T012 [P] [US1] Unit test for `code/preprocess/structural.py` graph metric calculation in `tests/unit/test_structural.py`.
- [X] T013 [P] [US1] Unit test for `code/preprocess/functional.py` LOO k-means state extraction in `tests/unit/test_functional.py`.
- [X] T013b [P] [US1] **CRITICAL**: Unit test for LOO Independence Constraint in `tests/unit/test_functional.py`. Verify that for any subject `i`, the generated centroids are computed *exclusively* from the data of subjects `j != i`. Assert that subject `i`'s data is never included in the centroid generation step.
- [X] T014 [P] [US1] Integration test for single-subject pipeline in `tests/integration/test_single_subject.py`.

*Note on [P] tags: Tests T012-T014 are marked [P] meaning they can run in parallel once the code skeletons (T006, T007) exist. They must be written to FAIL first (TDD) before implementation tasks T015+ are run.*

### Implementation for User Story 1

- [X] T015a [US1] Implement structural graph metric calculation (global efficiency, clustering, modularity) in `code/preprocess/structural.py` using NetworkX. **Constraint**: MUST consume `DENSITY_THRESHOLD_BASELINE` from `code/config.py` (defined in T004b).
- [ ] T015b [US1] **Mandatory Sensitivity Analysis (Graph Density)**: Extend `code/preprocess/structural.py` to perform the FR-008 mandated sensitivity analysis on **proportional density**. Iterate through `DENSITY_THRESHOLD_VARIATIONS` (e.g., 10%, [deferred], 20%) by applying these thresholds to the adjacency matrix. **Output**: Save results to `data/processed/structural_density_sensitivity.csv` containing metrics for each density level.
- [X] T016 [US1] Implement **Leave-One-Out (LOO) K-Means Centroid Generation** in `code/preprocess/functional.py`. **Logic**: For each subject `i` in the cohort:
 1. Compute sliding-window correlations (window_length=30 TR, step=1 TR) for all OTHER subjects (N-1).
 2. Concatenate these matrices and apply k-means (k=5) to generate **Subject-Specific LOO Centroids**.
 3. **Output**: Save a structured file `data/processed/loo_centroids_all_subjects.npz` where keys are subject IDs (e.g., `subject_001_centroids`) and values are the `(5, 200)` centroid arrays derived *only* from `j != i`.
 4. **Constraint**: Must strictly enforce independence (subject `i` is never used to generate centroids for subject `i`).
- [ ] T017 [US1] Implement **LOO State Assignment** in `code/preprocess/functional.py`. **Logic**: Load `data/processed/loo_centroids_all_subjects.npz`. For each subject `i`:
 1. Retrieve the LOO Centroids generated specifically for subject `i` (from `j != i`).
 2. Assign windowed matrices of subject `i` to these centroids to determine state sequences.
 3. Calculate per-subject dynamic metrics: **Mean Dwell Time** and **Number of Visited States**.
 4. **Output**: Save per-subject state assignments and metrics to `data/processed/state_assignments.csv` and `data/processed/dynamic_metrics.csv`. **Schema for dynamic_metrics.csv**: Columns `[subject_id, state_id, mean_dwell_time, num_visits]`.
- [ ] T019 [US1] Implement subject exclusion logging *within* the per-subject loop. Log exclusions (convergence failure, sparsity >90%) to `data/logs/exclusion_log.json` immediately upon detection. **Schema**: `[{subject_id, reason, timestamp}]`.
- [ ] T018 [US1] Implement batch processing logic in `code/main.py` to aggregate metrics into `data/processed/structural_metrics.csv` and `data/processed/dynamic_metrics.csv`. **Dependency**: Requires `contracts/output.schema.yaml` (completed in T010) and completion of T015-T017. **Note**: Ensure T019 exclusion logic runs before aggregation so excluded subjects are omitted.
- [ ] T019b [US1] **Data Completeness Report**: Implement a script in `code/analysis/` to read `data/logs/exclusion_log.json` and `data/processed/structural_metrics.csv`. Calculate the percentage of processed subjects against the total cohort size and categorize exclusion reasons (count "convergence failure" vs "sparsity >90%"). **Output**: Save `data/processed/completeness_report.json` to satisfy SC-005.

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

- [ ] T024 [US2] Implement normality testing (Shapiro-Wilk, α=0.05) in `code/analysis/correlation.py` to select Pearson vs. Spearman.
- [ ] T025 [US2] Implement correlation calculation between structural and dynamic metrics across the cohort in `code/analysis/correlation.py`.
- [ ] T026 [US2] Implement Benjamini-Hochberg FDR correction (q=0.05) on all p-values in `code/analysis/correlation.py`.
- [ ] T027 [US2] Generate `data/processed/correlation_results.csv` containing r-values, raw p-values, and FDR-corrected p-values.
- [ ] T028 [US2] Handle edge case: If FDR correction yields zero significant findings, ensure report explicitly states this rather than omitting results.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Generate Robustness and Methodological Reports (Priority: P3)

**Goal**: Verify robustness to parameter choices (window length, threshold density) and ensure "associational" framing.

**Independent Test**: Compare primary report with robustness report; verify "associational" labels, sensitivity tables, and tractography noise analysis are present.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T029 [P] [US3] Unit test for sensitivity analysis logic in `tests/unit/test_robustness.py`.
- [ ] T030 [P] [US3] Integration test for full robustness report generation in `tests/integration/test_robustness.py`.

### Implementation for User Story 3

- [ ] T031 [US3] **Mandatory 20 TR Validation**: Implement a full re-run of the dynamic metric extraction (T016/T017) and correlation analysis (T025) using `WINDOW_LENGTH_VALIDATION = 20` TR. **Requirement**: This is a mandatory validation of metric stability (Constitution Principle VII). Compare these results against the 30 TR baseline. **Output**: Save `data/processed/sensitivity_comparison.csv` containing the absolute difference in correlation coefficients for all metric pairs between 30 TR and 20 TR.
- [ ] T032 [US3] Aggregate structural density sensitivity results (from T015b) and correlation stability to verify robustness to graph thresholding (FR-008).
- [ ] T033 [US3] Implement resource usage monitoring (peak RAM, runtime) in `code/main.py` to verify CPU-only constraints (GB/h).
- [ ] T034 [US3] Generate final report in `code/reports/generate_report.py` with explicit "associational" framing (FR-007) and sensitivity tables. **Requirement**: The report MUST explicitly calculate and display:
 1. The "absolute difference between 30 TR and 20 TR correlation coefficients" (from `data/processed/sensitivity_comparison.csv`).
 2. A table or plot showing how statistical power changes across the **graph density thresholds** (from `data/processed/structural_density_sensitivity.csv`).
- [ ] T035 [US3] Validate report against `contracts/output.schema.yaml` to ensure all required fields (r, p, FDR, sensitivity, absolute difference, density analysis) are present.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T050 [P] Documentation updates in `docs/` and `README.md`.
- [ ] T051 Code cleanup and refactoring for CPU efficiency (ensure no GPU calls).
- [ ] T052 Run `docs/quickstart.md` validation to ensure full pipeline reproducibility.
- [ ] T053 Final review of all reports for "associational" language compliance and scope adherence.

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
Task: "Unit test for LOO Independence Constraint"

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
- [Story] label maps task to traceability to specific user story
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Constraint**: All tasks must run on CPU-only (a limited number of cores, GB RAM). No GPU, no 8-bit quantization, no large LLMs.
- **Data Integrity**: No fake data. All metrics must come from real HCP data fetched via OpenNeuro/URL.
- **Scope Constraint**: Only implement features explicitly mandated by FR-001 through FR-008 AND the reviewer-mandated tractography sensitivity analysis. (Note: Tractography confidence sensitivity was removed as scope creep; only graph density sensitivity remains).
- **Methodological Note**: Tasks T016 and T017 implement the Plan-mandated "Leave-One-Out (LOO)" K-Means strategy to ensure statistical independence. T013b explicitly verifies this constraint.
- **Revision Note**: Phase 6 (Tractography Noise Sensitivity) has been removed as it was scope creep. The focus is now strictly on Graph Density Sensitivity (FR-008) and 20 TR Validation (Constitution Principle VII).