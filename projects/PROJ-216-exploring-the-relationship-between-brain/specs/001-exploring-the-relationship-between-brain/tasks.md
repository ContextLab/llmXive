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

- [ ] T001b Create directory `data/raw`
- [ ] T001c Create directory `data/interim`
- [ ] T001d Create directory `data/processed`
- [ ] T001e Create directory `code` and file `code/__init__.py`
- [ ] T001f Create directories `tests/unit` and `tests/integration`
- [ ] T001g Create directory `reports`
- [X] T002 Initialize Python project with dependencies

Research Question: [Not provided in original text]
Method: [Not provided in original text]
References: [Not provided in original text] (`requirements.txt`: `nibabel`, `nilearn`, `networkx`, `scikit-learn`, `pandas`, `numpy`, `openneuro-py`, `dipy`)
- [ ] T003 [P] Configure linting and formatting tools (ruff, black)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your plan):

- [ ] T005 [P] Implement system-level dependency check script for FSL/AFNI availability
- [X] T006 [P] Setup logging and error handling infrastructure (`code/utils.py`)
- [X] T007 [Dep: None] Create class `Subject` and `BehavioralScore` in `code/models.py` with attributes for ID, age, gender, file paths, score_value, source_type based on `data-model.md`; verify with `pytest tests/unit/test_models.py`
- [ ] T008a [P] Generate Spec Amendment artifact updating SC-001 to reflect N=10 CI feasibility study and pivot to Fluid Intelligence
- [ ] T008b [P] Create `config.yaml` with dataset IDs (ds000224 as primary, ds000230 as fallback_only) and N=10 sample limit
- [ ] T009 [P] Implement `ResourceMonitor` class in `code/utils.py` that logs RAM usage per subject to stderr and writes to `data/processed/resource_profile.json`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download resting-state fMRI data from OpenNeuro ds000224 (primary for Fluid Intelligence), validate data, and preprocess to generate clean BOLD time series.

- [X] T010 [P] [US1] Unit test for OpenNeuro download retry logic in `tests/unit/test_download_retry.py`
- [X] T011 [P] [US1] Unit test for behavioral data validation (Fluid Intelligence check) in `tests/unit/test_download_validation.py`
- [X] T012 [P] [US1] Integration test for full preprocessing pipeline on 1 subject in `tests/integration/test_pipeline.py`
- [ ] T013a [US1] Implement OpenNeuro fetch for ds000224 in `code/download.py`; enforce N=10 sample limit for CI
- [ ] T013b [US1] Implement fallback logic for ds000230 (only if ds000224 fails or lacks data)
- [ ] T013c [US1] Implement N=10 sample limit enforcement logic in `code/download.py`
- [ ] T014a [US1] Validate presence of Fluid Intelligence scores in aggregated subjects
- [ ] T014b [US1] Validate absence of Musical Creativity proxies (TTCT/AUT) to trigger pivot logic
- [ ] T014c [US1] Implement halt logic if valid subject count is 0 after validation, raising critical error: "No valid data found in specified datasets"
- [X] T015 [US1] Implement preprocessing pipeline in `code/preprocess.py` using FSL/AFNI for motion correction, spatial normalization, and bandpass filtering (low-frequency range) as a single executable script
- [ ] T016a [US1] Implement motion artifact detection (>3mm translation) in `preprocess.py`
- [ ] T016b [US1] Implement halt logic if effective N becomes 0 after motion exclusion
- [ ] T017a [US1] Generate `data/processed/preprocessing_stats.json` with keys: `total_subjects`, `successful_subjects`, `success_rate_percentage`
- [ ] T017b [US1] Calculate preprocessing success rate as (successful_subjects / total_downloaded_subjects) and write to `preprocessing_stats.json`
- [ ] T018 [US1] Add resource monitoring to `preprocess.py` to log RAM usage per subject (consumes `ResourceMonitor` from T009)

---

## Phase 4: User Story 2 - Graph Metric Computation (Priority: P2)

**Goal**: Compute functional connectivity matrices and derive graph theoretical metrics (global efficiency, modularity, clustering coefficient) for each preprocessed subject using the Schaefer parcellation atlas.

- [X] T019 [P] [US2] Unit test for correlation matrix generation symmetry in `tests/unit/test_graph_metrics.py`
- [X] T020 [P] [US2] Unit test for Louvain algorithm fallback (resolution sweep) in `tests/unit/test_graph_metrics.py`
- [X] T021 [P] [US2] Integration test for graph metric aggregation in `tests/integration/test_pipeline.py`
- [X] T022 [US2] Implement connectivity matrix generation using `nilearn` and a Schaefer atlas with a variable number of ROIs in `code/graph_metrics.py`; read preprocessed NIfTI files from `data/processed/` (output of T015)
- [X] T023 [US2] Implement global efficiency and clustering coefficient calculation using `networkx` in `code/graph_metrics.py`
- [X] T024 [US2] Implement modularity calculation (Louvain) with resolution parameter sweep fallback in `code/graph_metrics.py`
- [ ] T025 [US2] Aggregate results into `data/processed/graph_metrics.csv` with columns: subject_id, metric_name, value
- [X] T026 [US2] Validate numerical ranges (e.g., efficiency -1) and write anomalies to `data/processed/graph_metric_validation.log` with format: `[SUBJECT_ID] [METRIC] [VALUE] [REASON]`

---

## Phase 5: User Story 3 - Correlation Analysis and Reporting (Priority: P3)

**Goal**: Perform statistical correlation analysis between graph metrics and Fluid Intelligence scores using Bonferroni correction, generating visualizations and a summary report.

- [X] T027 [P] [US3] Unit test for Bonferroni correction logic in `tests/unit/test_stats.py`
- [X] T028 [P] [US3] Unit test for Cohen's d and 95% CI calculation in `tests/unit/test_stats.py`
- [X] T029 [P] [US3] Integration test for full analysis report generation in `tests/integration/test_pipeline.py`
- [ ] T031 [US3] Implement Bonferroni correction for multiple comparisons (Overrides Spec FR-005 per Constitution Principle VII) in `code/stats.py`
- [ ] T031a [US3] Generate Conflict Resolution Report in `reports/conflict_resolution.pdf` documenting Bonferroni override of Spec FR-005 (FDR) per Constitution Principle VII
- [ ] T030a [US3] Implement critical halt logic in `stats.py` if valid behavioral scores are empty after merge, raising error: "No valid creativity proxy scores exist in the dataset"
- [ ] T030b [US3] Implement Pearson/Spearman correlation analysis between graph metrics and Fluid Intelligence scores in `code/stats.py`
- [ ] T030c [US3] Implement multiple linear regression analysis (controlling for age/gender) in `code/stats.py`
- [ ] T030d [US3] Integrate results; ensure correlation coefficients are reported separately from regression control model
- [ ] T032 [US3] Calculate effect sizes (Cohen's d) and confidence intervals; append columns `cohens_d`, `ci_lower`, `ci_upper` to `data/processed/graph_metrics.csv`
- [ ] T033a [US3] Generate scatter plot of Metric vs Fluid Intelligence using `matplotlib`/`seaborn`
- [ ] T033b [US3] Save scatter plot to `reports/scatter_metric_vs_fluid.png`
- [ ] T034 [US3] Generate `reports/summary.pdf` containing scatter plots, regression lines, correlation coefficients, p-values, effect sizes (Cohen's d), and confidence intervals for all significant correlations
- [ ] T035 [US3] Generate `data/processed/analysis_resource_profile.json` with peak RAM and total runtime for SC-005 verification

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T036 [P] Documentation updates in `README.md` and `quickstart.md`
- [ ] T037a [P] Refactor `preprocess.py` for sequential processing
- [ ] T037b [P] Verify RAM usage < 7GB on N=10
- [ ] T038a [P] Optimize matrix operations in `graph_metrics.py`
- [ ] T038b [P] Verify runtime < 6h for N=10
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
- **Spec Conflict Note**: FR-005 (FDR) and FR-001 (Creativity Halt) are overridden by Constitution/Plan; tasks implement Bonferroni and Fluid Intelligence fallback with formal amendment tasks (T008a, T031a).