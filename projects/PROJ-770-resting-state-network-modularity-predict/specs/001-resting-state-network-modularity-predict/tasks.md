# Tasks: Resting-State Network Modularity Predicts Social Network Size

**Input**: Design documents from `/specs/001-gene-regulation/`
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
  
  Tasks MUST be organized by user story so each story can be:
  - Implemented independently
  - Tested independently
  - Delivered as an MVP increment
  
  DO NOT keep these sample tasks in the generated tasks.md file.
  ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan (`code/`, `data/`, `tests/`)
- [ ] T002 Initialize Python 3.11 project with `requirements.txt` (pinning `nilearn`, `scikit-learn`, `python-louvain`, `statsmodels`, `nibabel`)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Implement `code/utils.py` with global random seed setting (numpy, random, python) and memory profiling helpers
- [ ] T005 [P] Create `code/config.py` to manage paths (`data/raw`, `data/processed`, `data/results`) and hyperparameters (thresholds, sensitivity analysis increments)
- [ ] T006 [P] Implement `code/download_data.py` with full HCP S3/HuggingFace verification logic: fetch metadata, verify NIfTI existence for a random subset of subjects, and HALT execution if data is unavailable (Phase 0 critical path)
- [ ] T007 Setup `tests/test_utils.py` to verify seed reproducibility and memory constraints
- [ ] T008 Setup CI workflow (`.github/workflows/research.yml`) targeting CPU-only runner with 7GB RAM limit

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Retrieve, filter, and preprocess HCP resting-state fMRI and behavioral data to produce a clean subject-level dataset.

**Independent Test**: The pipeline executes end-to-end on a CPU-only runner, outputting a single CSV with subject IDs, preprocessed modularity Q values (placeholder for now), and behavioral metrics, with no GPU errors or memory overflows.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T009 [P] [US1] Unit test for data filtering logic in `tests/test_download_data.py`
- [ ] T010 [P] [US1] Unit test for band-pass filter frequency response in `tests/test_preprocess_fmri.py`

### Implementation for User Story 1

- [ ] T011 [P] [US1] Implement `code/download_data.py` to fetch a representative sample of subjects' fMRI NIfTI and behavioral CSVs from HCP verified sources (S3/HuggingFace) using `seed=42` and `random.sample`, verifying column existence for "Number of close friends" and "Number of acquaintances"; output `data/processed/behavioral_clean.csv` (schema: subject_id, age, sex, friends, acquaintances) with median imputation applied if missingness <20%, otherwise exclude subject and log exclusion count
- [ ] T012 [P] [US1] Implement `code/preprocess_fmri.py` to apply band-pass filter (–0.1 Hz), regress motion parameters and global signal, and extract region-wise time series using the Schaefer atlas
- [ ] T013 [US1] Implement `code/preprocess_fmri.py` logic to compute Fisher-z transformed correlation matrices for each subject, handling motion artifact exclusion (FD > 0.5mm) and missing data via **median imputation (if <20% missing) or subject exclusion (if >20% missing)** with mandatory logging/exclusion count documentation
- [ ] T014 [US1] Add validation logic in `code/preprocess_fmri.py` to ensure no NaN values or dimension mismatches in output matrices

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Graph Construction and Modularity Calculation (Priority: P2)

**Goal**: Construct sparse functional connectivity graphs and compute the Louvain modularity quality index (Q) for each subject.

**Independent Test**: The system computes Q for a cohort of subjects using the specified thresholding method and outputs a CSV of Q values, verifying that values fall within the theoretical range (0.0–1.0).

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T016 [P] [US2] Unit test for adjacency matrix thresholding logic in `tests/test_build_graphs.py`
- [ ] T017 [P] [US2] Unit test for Louvain algorithm convergence and seed stability in `tests/test_build_graphs.py`

### Implementation for User Story 2

- [ ] T018 [P] [US2] Implement `code/build_graphs.py` to threshold Fisher-z correlation matrices at the top percentage of strongest positive edges as defined in `code/config.py` to ensure comparable density
- [ ] T019 [US2] Implement `code/build_graphs.py` to apply the Louvain algorithm (via `python-louvain`) with retry logic (seeds) for convergence, recording modularity Q and community assignments
- [ ] T020 [US2] Add sanity check in `code/build_graphs.py` to flag and log subjects with Q > 1.0 or Q < 0.0
- [ ] T021 [US2] Generate `data/processed/subject_modularity.csv` containing subject IDs and computed Q values
- [ ] T022 [US2] Implement `code/build_graphs.py` to calculate "total connectivity strength" (sum of absolute edge weights) for each subject to serve as a covariate controlling for global signal intensity (Addressing FR-006)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Modeling and Association Testing (Priority: P3)

**Goal**: Fit a standard linear regression model to test the association between modularity Q and social network size, controlling for covariates and performing sensitivity analysis.

**Independent Test**: The system executes a regression model and outputs a summary table with coefficients, p-values, and confidence intervals, confirming the procedure correctly calculates the association against the null hypothesis.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T023 [P] [US3] Unit test for Benjamini-Hochberg correction logic in `tests/test_analyze_stats.py`
- [ ] T024 [P] [US3] Unit test for VIF calculation and covariate removal logic in `tests/test_analyze_stats.py`

### Implementation for User Story 3

- [ ] T025 [P] [US3] Implement `code/analyze_stats.py` to merge `data/processed/subject_modularity.csv` (Q values) with `data/processed/behavioral_clean.csv` (from T011) on `subject_id`, handling missing values, to produce the final single CSV containing subject IDs, Q values, and behavioral metrics (Single Source of Truth)
- [ ] T026 [US3] Implement `code/analyze_stats.py` to fit a linear regression model (Q as fixed effect) with covariates: age, sex, mean FD, and total connectivity strength (to control for global signal intensity)
- [ ] T027 [US3] Implement `code/analyze_stats.py` to perform Variance Inflation Factor (VIF) check; if VIF > 5 for connectivity strength, re-run model without it and log as exploratory (Addressing FR-006)
- [ ] T028 [US3] Implement `code/analyze_stats.py` to apply Benjamini-Hochberg procedure for multiple comparisons if separate models are run for "friends" vs "acquaintances"
- [ ] T029 [US3] Implement `code/analyze_stats.py` to perform sensitivity analysis by varying graph threshold from a low percentage to a higher percentage in increments defined in `code/config.py` (e.g., [deferred]) and recording coefficient stability
- [ ] T030 [US3] Generate `data/results/primary_analysis.csv` and `data/results/sensitivity_analysis.csv` with coefficients, p-values, and confidence intervals

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [ ] T031 [P] Update `README.md` with execution instructions and data sources
- [ ] T032 Code cleanup and refactoring for memory efficiency (streaming large matrices if needed)
- [ ] T033 Run full pipeline on GitHub Actions to verify ≤6h runtime and ~7GB RAM peak usage (Addressing SC-004)
- [ ] T034 [P] Run quickstart.md validation
- [ ] T035 Generate final `research.md` update with power analysis and methodological rationale

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output (correlation matrices)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 and US2 data output

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
Task: "Unit test for data filtering logic in tests/test_download_data.py"
Task: "Unit test for band-pass filter frequency response in tests/test_preprocess_fmri.py"

# Launch all models for User Story 1 together:
Task: "Implement code/download_data.py to fetch 200 random subjects..."
Task: "Implement code/preprocess_fmri.py to apply band-pass filter..."
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
- **CPU Constraint**: All tasks must run on vCPU, 7GB RAM. No GPU, no 8-bit quantization, no large model training.
- **Data Constraint**: All data must be real. No synthetic data generation for input or results.
- **Reviewer Addressed**: Task T022, T027 explicitly address the "total connectivity strength" covariate requirement (FR-006) to control for global signal intensity, without unauthorized metabolic modeling.
- **Critical Path**: T006 must successfully verify data availability before T011 proceeds.
- **Determinism**: Subject selection uses `seed=42`.
- **Imputation**: Missing behavioral data uses **median imputation if <20% missing, otherwise exclude** with logging.
- **Sensitivity Analysis**: Graph threshold varies in increments defined in `code/config.py`.