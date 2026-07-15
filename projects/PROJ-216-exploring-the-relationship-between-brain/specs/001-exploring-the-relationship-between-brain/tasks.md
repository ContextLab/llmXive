# Tasks: Exploring the Relationship Between Brain Network Dynamics and Musical Creativity

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

- [ ] T001b Create `data/` subdirectories: `raw`, `interim`, `processed`
- [ ] T001c Create `code/` subdirectories: `__init__.py`, `tests/`
- [ ] T001d Create `tests/unit/` and `tests/integration/` directories
- [ ] T001e Create `reports/` directory for final outputs
- [ ] T002 Initialize Python 3.11 project with dependencies (`requirements.txt`: `nibabel`, `nilearn`, `networkx`, `scikit-learn`, `pandas`, `numpy`, `openneuro-py`, `dipy`)
- [ ] T003 [P] Configure linting and formatting tools (ruff, black)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [~] T005 [P] Implement system-level dependency check script for FSL/AFNI availability
- [ ] T006 [P] Setup logging and error handling infrastructure (`code/utils.py`)
- [X] T007 [Dep: None] Create class `Subject` and `BehavioralScore` in `code/models.py` with attributes for ID, age, gender, file paths, score_value, source_type based on `data-model.md`; verify with `pytest tests/unit/test_models.py`
- [~] T008 Configure environment configuration management for dataset IDs (ds000224, ds000230) and sample limits (N=10 for CI, deviation from Spec SC-001 N=50)
- [ ] T009 [P] Implement `ResourceMonitor` class in `code/utils.py` that logs RAM usage per subject to stderr and writes to `data/processed/resource_profile.json`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download resting-state fMRI data from OpenNeuro ds000224 and ds000230, validate for Fluid Intelligence scores (fallback per Plan), and preprocess to generate clean BOLD time series.

- [X] T010 [P] [US1] Unit test for OpenNeuro download retry logic in `tests/unit/test_download_retry.py`
- [X] T011 [P] [US1] Unit test for behavioral data validation (Fluid Intelligence check) in `tests/unit/test_download_validation.py`
- [X] T012 [P] [US1] Integration test for full preprocessing pipeline on 1 subject in `tests/integration/test_pipeline.py`
- [~] T013 [US1] Implement `download.py` to fetch ds000224 first, then ds000230; prioritize ds000224 for Fluid Intelligence; handle ds000230 absence gracefully; enforce N=10 sample limit for CI (Overrides Spec SC-001 N=50 target per Plan N=10 constraint)
- [~] T014 [US1] Implement validation logic in `download.py` to confirm presence of Fluid Intelligence scores (fallback per Plan); Aggregate valid subjects from ds000224 and ds000230; halt with critical error ONLY if total N=0 (Overrides Spec FR-001 per Plan pivot)
- [ ] T015 [US1] Implement preprocessing pipeline in `code/preprocess.py` using FSL/AFNI for motion correction, spatial normalization, and bandpass filtering (0.01-0.1 Hz) as a single executable script
- [ ] T016 [US1] Add motion artifact detection and subject exclusion logic (>3mm translation) in `preprocess.py`; halt with critical error if effective N becomes 0 after exclusion
- [ ] T017 [US1] Generate `data/processed/preprocessing_stats.json` with keys: `total_subjects`, `successful_subjects`, `success_rate_percentage`
- [ ] T018 [US1] Add resource monitoring to `preprocess.py` to log RAM usage per subject (consumes `ResourceMonitor` from T009)

---

## Phase 4: User Story 2 - Graph Metric Computation (Priority: P2)

**Goal**: Compute functional connectivity matrices and derive graph theoretical metrics (global efficiency, modularity, clustering coefficient) for each preprocessed subject using the Schaefer parcellation atlas.

- [ ] T019 [P] [US2] Unit test for correlation matrix generation symmetry in `tests/unit/test_graph_metrics.py`
- [ ] T020 [P] [US2] Unit test for Louvain algorithm fallback (resolution sweep) in `tests/unit/test_graph_metrics.py`
- [ ] T021 [P] [US2] Integration test for graph metric aggregation in `tests/integration/test_pipeline.py`
- [ ] T022 [US2] Implement connectivity matrix generation using `nilearn` and a Schaefer atlas with a variable number of ROIs in `code/graph_metrics.py`; read preprocessed NIfTI files from `data/processed/` (output of T015)
- [ ] T023 [US2] Implement global efficiency and clustering coefficient calculation using `networkx` in `code/graph_metrics.py`
- [ ] T024 [US2] Implement modularity calculation (Louvain) with resolution parameter sweep fallback in `code/graph_metrics.py`
- [ ] T025 [US2] Aggregate results into `data/processed/graph_metrics.csv` with subject ID, metric name, and value
- [ ] T026 [US2] Validate numerical ranges (e.g., efficiency 0-1) and write anomalies to `data/processed/graph_metric_validation.log` with format: `[SUBJECT_ID] [METRIC] [VALUE] [REASON]`

---

## Phase 5: User Story 3 - Correlation Analysis and Reporting (Priority: P3)

**Goal**: Perform statistical correlation analysis between graph metrics and Fluid Intelligence scores using Bonferroni correction, generating visualizations and a summary report.

- [ ] T027 [P] [US3] Unit test for Bonferroni correction logic in `tests/unit/test_stats.py`
- [ ] T028 [P] [US3] Unit test for Cohen's d and 95% CI calculation in `tests/unit/test_stats.py`
- [ ] T029 [P] [US3] Integration test for full analysis report generation in `tests/integration/test_pipeline.py`
- [ ] T030 [US3] Implement multiple linear regression analysis (controlling for age/gender) and Pearson/Spearman correlation between graph metrics and Fluid Intelligence scores in `code/stats.py`; requires `data/processed/graph_metrics.csv` (T025) and validated behavioral data (T014)
- [ ] T031 [US3] Implement Bonferroni correction for multiple comparisons (Overrides Spec FR-005 per Constitution Principle VII) in `code/stats.py`
- [ ] T032 [US3] Calculate effect sizes (Cohen's d) and 95% confidence intervals; append columns `cohens_d`, `ci_95_lower`, `ci_95_upper` to `data/processed/graph_metrics.csv`
- [ ] T033 [US3] Generate scatter plots with regression lines and confidence intervals using `matplotlib`/`seaborn`
- [ ] T034 [US3] Generate `reports/summary.pdf` containing scatter plots, regression lines, correlation coefficients, p-values, effect sizes (Cohen's d), and 95% CIs for all significant correlations
- [ ] T035 [US3] Generate `data/processed/analysis_resource_profile.json` with peak RAM and total runtime for SC-005 verification

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T036 [P] Documentation updates in `README.md` and `quickstart.md`
- [ ] T037 Code cleanup and refactoring for memory efficiency (sequential processing)
- [ ] T038 Performance optimization for large matrix operations within RAM limits
- [ ] T039 [P] Additional unit tests for edge cases (missing metadata, convergence failures)
- [ ] T040 Run quickstart.md validation to ensure end-to-end reproducibility

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 output (preprocessed data)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 output (graph metrics)

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
Task: "Unit test for OpenNeuro download retry logic in tests/unit/test_download_retry.py"
Task: "Unit test for behavioral data validation (Fluid Intelligence check) in tests/unit/test_download_validation.py"

# Launch all models for User Story 1 together:
Task: "Create class Subject and BehavioralScore in code/models.py"
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
 - Developer A: User Story 1 (Data/Preprocessing)
 - Developer B: User Story 2 (Graph Metrics)
 - Developer C: User Story 3 (Stats/Reporting)
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
- **Feasibility**: All tasks designed for N=10 subjects on CPU-only CI (2 cores, 7GB RAM, 6h limit).
- **Data Integrity**: No synthetic data generation; all analysis uses real OpenNeuro data.
- **Statistical Compliance**: Bonferroni correction used per Constitution (replacing FDR from spec).
- **Spec Conflict Note**: FR-005 (FDR) and FR-001 (Creativity Halt) are overridden by Constitution/Plan; tasks implement Bonferroni and Fluid Intelligence fallback.