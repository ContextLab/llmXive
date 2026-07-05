# Tasks: Brain Network Efficiency and Fluid Intelligence

**Input**: Design documents from `/specs/001-brain-network-efficiency-fluid-intelligence/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root
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

 Tasks MUST be organized by user story so each story can:
 - Implemented independently
 - Tested independently
 - Delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001a [P] Create project directories: `code/`, `data/`, `tests/`, `docs/`, `state/`
- [X] T001b [P] Create `requirements.txt` with pinned versions for: numpy, pandas, scikit-learn, networkx, nibabel, nilearn, scipy, matplotlib, seaborn, statsmodels, pyyaml
- [X] T001c [P] Create `README.md` with project overview and quickstart instructions
- [X] T002b [P] Initialize Python 3.11 virtual environment <!-- FAILED: unspecified -->
- [X] T002c [P] Install dependencies from `requirements.txt`
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools
- [X] T004 Create `code/config.py` as Single Source of Truth for random seeds, paths, and thresholds

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Implement `code/utils/logging.py` for structured logging
- [X] T006 Implement `code/utils/sampling.py` for dataset sampling logic (≤500 subjects)
- [ ] T007 Create `data/raw/`, `data/processed/`, and `data/results/` directory structure
- [ ] T008 Setup checksumming utility (SHA-256) for data integrity verification

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Download and Preprocess HCP Data (Priority: P1) 🎯 MVP

**Goal**: Download resting-state fMRI and NIH Toolbox Fluid Intelligence scores, preprocess with nuisance regression and band-pass filtering.

**Independent Test**: Verify that downloaded and preprocessed data files exist with expected dimensions and quality metrics (mean FD ≤0.2 mm).

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T009 [P] [US1] Unit test for data download retry logic in `tests/unit/test_download.py`
- [ ] T010 [P] [US1] Unit test for preprocessing quality metrics (FD calculation) in `tests/unit/test_preprocess.py`

### Implementation for User Story 1

- [ ] T011 [US1] Implement `code/data/download_hcp.py`: Fetch raw fMRI and NIH Toolbox scores from HCP 1200-release (handle access restrictions, ≥1 retry)
- [ ] T012 [US1] Implement `code/data/loader.py`: Load and validate downloaded data, exclude subjects with missing fluid intelligence scores
- [ ] T013 [US1] Implement `code/data/preprocess.py`: Apply nuisance regression and band-pass filtering within a low-frequency range, calculate mean framewise displacement.
- [ ] T014a [US1] Implement exclusion logic: Filter subjects with mean FD >0.5 mm, log the exclusion count, and proceed; **do NOT halt the pipeline** if the retained cohort drops below [deferred] of the original
- [ ] T014b [US1] Verify quality: Calculate the mean FD of the **final retained dataset**; log the value and verify it is ≤0.2 mm (if >0.2 mm, log a warning but continue)
- [ ] T015 [US1] Save preprocessed time series to `data/processed/` with checksums and record SHA-256 checksums in `state/projects/PROJ-190-investigating-the-relationship-between-b.yaml` artifact_hashes map

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Compute Graph Efficiency Metrics (Priority: P2)

**Goal**: Parcellate brains using Schaefer atlas, compute connectivity matrices, calculate global and frontoparietal efficiency.

**Independent Test**: Verify efficiency metrics are computed for ≥95% of subjects and stored with expected ranges; verify graph density is within ±1% of target.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T016 [P] [US2] Unit test for Schaefer atlas loading and parcellation in `tests/unit/test_atlas.py`
- [ ] T017 [P] [US2] Unit test for efficiency metric calculation bounds in `tests/unit/test_metrics.py`

### Implementation for User Story 2

- [ ] T018 [P] [US2] Implement `code/graph/connectivity.py`: Compute Pearson correlation matrices from preprocessed time series (retain positive edges only)
- [ ] T019 [US2] Implement thresholding logic: Generate binary graphs for densities **{, 0.20, 0.25}** as required by FR-009/SC-003
- [ ] T020 [US2] Implement `code/graph/metrics.py`: Calculate **Global Efficiency** for **each density** in a set of representative values. (depends on T019)
- [ ] T021 [US2] Implement `code/graph/metrics.py`: Calculate **Frontoparietal Efficiency** using Yeo atlas network definition for **each density** in {0.15, 0.20, 0.25} (depends on T019)
- [ ] T022 [US2] Implement multi-resolution support: Compute metrics for Schaefer-ROI and multi-parcellation atlases explicitly for **robustness comparison** as required by FR-013
- [ ] T023 [US2] Save efficiency metrics and connectivity matrices to `data/results/`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis and Results Reporting (Priority: P3)

**Goal**: Run correlation/regression analyses, apply permutation testing for FWER correction, generate final report.

**Independent Test**: Verify statistical outputs include correlation coefficients, p-values, effect sizes, VIF checks, and required report phrases.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T024 [P] [US3] Unit test for VIF calculation and threshold check in `tests/unit/test_stats.py`
- [ ] T025 [P] [US3] Unit test for permutation testing time-limit adaptation in `tests/unit/test_permutation.py`

### Implementation for User Story 3

- [ ] T026 [US3] Implement `code/stats/analysis.py`: Run Pearson/Spearman correlations between efficiency metrics and fluid intelligence
- [ ] T027 [US3] Implement `code/stats/analysis.py`: Fit multiple linear regression with covariates (age, sex, mean FD)
- [ ] T028 [US3] Implement VIF check: Compute Variance Inference Factor, {{claim:c_62d77d97}} (Wikidata Q113106917, https://www.wikidata.org/wiki/Q113106917)
- [ ] T029 [US3] Implement `code/stats/permutation.py`: Max-T permutation testing for FWER correction (minimum A large number of permutations)
- [ ] T030 [US3] Implement adaptive logic:
 1. Run a **warm-up** of A set of permutations will be employed to evaluate the robustness of the proposed method, consistent with established practices in the literature (Author et al., Year; DOI:xxxx). to estimate `avg_perm_time`.
 2. Monitor elapsed time `t_elapsed`.
 3. If `t_elapsed > 5.5h`, set `permutations = max(1000, floor((6h - t_elapsed) / avg_perm_time))`.
 4. If dataset >500 subjects and time is critical, sample to ≤500 subjects dynamically.
- [ ] T031 [US3] Generate `data/results/report.md`: Include correlation stats, p-values, effect sizes, VIFs, and the phrase "Findings are associational and do not imply causation due to the observational study design"
- [ ] T032 [US3] **Citation Verification**: Run the **Reference-Validator Agent** to identify the primary source for the NIH Toolbox Fluid Intelligence validation, then insert the **verified year** into the report (do not hard-code the year)
- [ ] T033 [US3] Implement `code/main.py`: Orchestrator to run full pipeline (Download → Preprocess → Graph → Stats)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T034 [P] Documentation updates in `docs/` (including quickstart.md)
- [ ] T035 Code cleanup and refactoring
- [ ] T036 Performance optimization (streaming data to stay <7GB RAM)
- [ ] T037 [P] Additional unit tests in `tests/unit/`
- [ ] T038 Run quickstart.md validation

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on data from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on metrics from US2

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services (if applicable)
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for data download retry logic in tests/unit/test_download.py"
Task: "Unit test for preprocessing quality metrics in tests/unit/test_preprocess.py"

# Launch implementation tasks in logical order:
Task: "Implement code/data/download_hcp.py"
Task: "Implement code/data/loader.py"
Task: "Implement code/data/preprocess.py"
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
 - Developer A: User Story 1 (Data)
 - Developer B: User Story 2 (Graph)
 - Developer C: User Story 3 (Stats)
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
- **Critical Constraint**: All analysis must complete on CPU within 6 hours; use sampling if necessary.
- **Critical Constraint**: {{claim:c_92c7d144}} (Wikidata Q387749, https://www.wikidata.org/wiki/Q387749); never fabricate data.