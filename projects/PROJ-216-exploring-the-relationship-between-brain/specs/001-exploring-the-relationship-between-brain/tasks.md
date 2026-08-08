# Tasks: Exploring the Relationship Between Brain Network Dynamics and Fluid Intelligence

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

## Phase 1: Setup (Shared Infrastructure & Formal Amendments)

**Purpose**: Project initialization, formal amendment of conflicting specs, and creation of foundational artifacts required by the Plan.

- [ ] T001 [P] **Initialize Data Directory Structure**: Create directories `data/raw`, `data/interim`, `data/processed`, `tests/unit`, `tests/integration`, and `reports`. **Verification**: Generate a log file `data/.verify_structure.log` containing a list of created paths and their timestamps. Verify `data/.verify_structure.log` exists and contains entries for all required directories.
- [X] T002 Initialize Python project with dependencies

Research Question: [Not provided in original text]
Method: [Not provided in original text]
References: [Not provided in original text] (`requirements.txt`: `nibabel`, `nilearn`, `networkx`, `scikit-learn`, `pandas`, `numpy`, `openneuro-py`, `dipy`)
- [ ] T003 [P] Configure linting and formatting tools (ruff, black)
- [ ] T008a [P] **Generate Spec Amendment Artifact**: Create `specs/amendment-template.md` if it does not exist. Then, create `specs/amendment-001-fluid-intelligence-n10.md` using the template. **Content Requirement**: The artifact MUST explicitly state: (1) FR-001 is amended to pivot to Fluid Intelligence and remove the hard halt for missing Musical Creativity; (2) SC-001 and SC-005 are amended to reflect N=10 CI feasibility baseline; (3) FR-005 and SC-004 are amended to mandate Bonferroni correction per Constitution Principle VII. **Verification**: Verify file exists and contains all three specific amendment clauses.
- [ ] T008b [P] **Generate Success Criteria Amendment**: Create `specs/amendment-002-sc-n10-baseline.md`. **Content Requirement**: Explicitly redefine SC-001 success rate baseline to N=10 and SC-005 runtime constraint to N=10. **Verification**: Verify file exists and contains the revised N=10 baseline definitions.
- [ ] T008c [P] **Generate Conflict Resolution Report**: Create `reports/conflict_resolution.json` documenting the Bonferroni override of Spec FR-005 (FDR) per Constitution Principle VII. **Schema**: `{"conflict": "FR-005 FDR vs Constitution Bonferroni", "resolution": "Bonferroni implemented", "rationale": "Constitution Principle VII mandates Bonferroni"}`. **Verification**: Verify JSON exists and contains all required keys and the specific rationale string.
- [ ] T009 [P] **Implement ResourceMonitor Class**: Implement `ResourceMonitor` class in `code/utils.py` that logs RAM usage per subject to stderr and writes to `data/processed/resource_profile.json`. **Verification**: Write a unit test in `tests/unit/test_resource_monitor.py` that mocks the process to generate a sample `resource_profile.json` and verify the file is created with the correct schema. This ensures the artifact exists before integration.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented.
**⚠️ CRITICAL**: No user story work can begin until this phase is complete.
**Note**: T008a must complete before T013a as it defines the configuration and amendment record required for execution.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T010 [P] **Configure Dataset IDs**: Create `config.yaml` with dataset IDs (ds000224 as primary, ds000230 as fallback_only) and N=10 sample limit. **Verification**: Verify YAML syntax and presence of keys.
- [ ] T011 [P] **Implement Resource Monitoring Integration**: Modify `code/preprocess.py` to import and invoke `ResourceMonitor` (from T009) during processing. **Dependency**: Must be implemented and integrated BEFORE T015 (Preprocessing execution) to ensure RAM logging occurs during the process. **Verification**: Verify `preprocess.py` contains the import and invocation of `ResourceMonitor`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download resting-state fMRI data from OpenNeuro ds000224 (primary for Fluid Intelligence), validate data, and preprocess to generate clean BOLD time series.
**Amended Requirement (FR-001)**: System MUST attempt to download resting-state fMRI data from OpenNeuro datasets. It MUST validate the presence of at least one valid **Fluid Intelligence** score. If fewer than 10 subjects with valid data are found, the system MUST use all available subjects (N ≥ 1) for analysis. If NO subjects with valid data are found, the system MUST halt execution with a critical error stating 'No valid Fluid Intelligence data found in specified datasets'. (Note: Original FR-001 requirement for Musical Creativity is amended per Plan).

- [ ] T012 [P] [US1] Unit test for OpenNeuro download retry logic in `tests/unit/test_download_retry.py`; validates requirements defined in T013a (retry 3x, exponential backoff).
- [ ] T013 [P] [US1] Unit test for behavioral data validation (Fluid Intelligence check) in `tests/unit/test_download_validation.py`; validates requirements defined in T014a (presence of Fluid Intelligence scores).
- [ ] T014 [P] [US1] Integration test for full preprocessing pipeline on 1 subject in `tests/integration/test_pipeline.py`
- [ ] T015a [US1] Implement OpenNeuro fetch for ds000224 in `code/download.py`; enforce N=10 sample limit for CI
- [ ] T015b [US1] **Implement Fallback for ds000230**: Implement function `fetch_fallback_dataset()` in `code/download.py` that triggers when ds000224 returns 404 or yields no valid subjects. Downloads ds000230 and writes to `data/raw/ds000230/`. **Verification**: Verify function exists and logs the fallback trigger event.
- [ ] T015c [US1] Implement N=10 sample limit enforcement logic in `code/download.py`
- [ ] T016a [US1] **Validate Presence of Fluid Intelligence**: Implement logic to scan downloaded subjects for valid Fluid Intelligence scores. Output: `data/processed/valid_subjects.json` with schema `{"subjects": [{"id": "str", "score": "float"},...], "count": int}`. **Verification**: Verify file exists and contains at least 1 subject. If count is 0, trigger T016c.
- [ ] T016c [US1] **Halt on Zero Valid Subjects**: Implement critical halt logic in `download.py` if `valid_subjects.json` count is 0. **Error Message**: "No valid Fluid Intelligence data found in specified datasets". **Verification**: Verify `pytest` raises `ValueError` with exact message. Log event to `data/processed/validation_errors.log` with prefix `[VALIDATION_ERROR]`. **Dependency**: T008a.
- [ ] T017 [US1] Implement preprocessing pipeline in `code/preprocess.py` using FSL/AFNI for motion correction, spatial normalization, and bandpass filtering (low-frequency range) as a single executable script. **Dependency**: Consumes the list of valid subjects from T016a (not the halt logic of T016c). Requires ResourceMonitor integration (from T011).
- [ ] T018a [US1] **Implement Motion Artifact Detection**: Implement logic to detect excessive motion (Translation > 3mm OR Rotation > 2mm) on preprocessed data. Output: `data/processed/motion_exclusion_log.csv` with columns `subject_id, translation_mm, rotation_mm, excluded (bool)`. **Verification**: Verify CSV exists and contains correct columns and calculated boolean flags. **Dependency**: T017.
- [ ] T018b [US1] **Halt on Zero Effective Subjects**: Implement halt logic in `preprocess.py` if effective N becomes 0 after motion exclusion. **Error Message**: "No valid subjects remaining after motion exclusion". **Verification**: Verify `pytest` raises `ValueError` with exact message. Log event to `data/processed/motion_exclusion.log` with prefix `[MOTION_EXCLUSION_ERROR]`. **Dependency**: T018a.
- [ ] T019a [US1] Generate `data/processed/preprocessing_stats.json` with keys: `total_subjects`, `successful_subjects`, `success_rate_percentage`. **Verification**: Verify JSON exists and keys match schema.
- [ ] T019b [US1] Calculate preprocessing success rate as (successful_subjects / total_downloaded_subjects) and write to `preprocessing_stats.json`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 4: User Story 2 - Graph Metric Computation (Priority: P2)

**Goal**: Compute functional connectivity matrices and derive graph theoretical metrics (global efficiency, modularity, clustering coefficient) for each preprocessed subject using the Schaefer parcellation atlas.

- [ ] T020 [P] [US2] Unit test for correlation matrix generation symmetry in `tests/unit/test_graph_metrics.py`
- [ ] T021 [P] [US2] Unit test for Louvain algorithm fallback (resolution sweep) in `tests/unit/test_graph_metrics.py`
- [ ] T022 [P] [US2] Integration test for graph metric aggregation in `tests/integration/test_pipeline.py`
- [ ] T023 [US2] Implement connectivity matrix generation using `nilearn` and a Schaefer atlas with a variable number of ROIs in `code/graph_metrics.py`; read preprocessed NIfTI files from `data/processed/` (output of T017)
- [ ] T024 [US2] Implement global efficiency and clustering coefficient calculation using `networkx` in `code/graph_metrics.py`
- [ ] T025 [US2] Implement modularity calculation (Louvain) with resolution parameter sweep fallback in `code/graph_metrics.py`
- [ ] T026 [US2] Aggregate results into `data/processed/graph_metrics.csv` with columns: subject_id, metric_name, value
- [ ] T027 [US2] Validate numerical ranges (e.g., efficiency -1) and write anomalies to `data/processed/graph_metric_validation.log` with format: `[SUBJECT_ID] [METRIC] [VALUE] [REASON]`

---

## Phase 5: User Story 3 - Correlation Analysis and Reporting (Priority: P3)

**Goal**: Perform statistical correlation analysis between graph metrics and Fluid Intelligence scores using Bonferroni correction, generating visualizations and a summary report.
**Amended Requirement (FR-005)**: System MUST apply **Bonferroni** correction (per Constitution Principle VII) for multiple comparisons across all tested graph metrics and report effect sizes with confidence intervals. (Note: Original FR-005 requirement for FDR is amended per Plan).

- [ ] T028 [P] [US3] Unit test for Bonferroni correction logic in `tests/unit/test_stats.py`
- [ ] T029 [P] [US3] Unit test for Cohen's d and 95% CI calculation in `tests/unit/test_stats.py`
- [ ] T030 [P] [US3] Integration test for full analysis report generation in `tests/integration/test_pipeline.py`
- [ ] T031a [US3] **Validate Presence of Fluid Intelligence for US3**: Implement logic to verify Fluid Intelligence scores exist for subjects in `graph_metrics.csv`. Output: `data/processed/us3_validation.json` with schema `{"valid_pairs": int, "missing_scores": int}`. **Verification**: Verify file exists and `valid_pairs` > 0.
- [ ] T031b [US3] **Halt on Zero Valid Scores for US3**: Implement critical halt logic in `stats.py` if `valid_pairs` is 0. **Error Message**: "No valid Fluid Intelligence scores found for correlation analysis". **Verification**: Verify `pytest` raises `ValueError` with exact message. Log event to `data/processed/pipeline_errors.log`.
- [ ] T031c [US3] Implement Pearson/Spearman correlation analysis between graph metrics and Fluid Intelligence scores in `code/stats.py`
- [ ] T031d [US3] Implement multiple linear regression analysis (controlling for age/gender) in `code/stats.py`
- [ ] T031e [US3] Integrate results; ensure correlation coefficients are reported separately from regression control model
- [ ] T032 [US3] **Implement Bonferroni Correction**: Implement Bonferroni correction for multiple comparisons as mandated by Constitution Principle VII in `code/stats.py`. **Dependency**: Must reference conflict resolution logic from T008c. **Verification**: Verify output includes `p_adj_bonferroni` column.
- [ ] T033 [US3] Calculate effect sizes (Cohen's d) and confidence intervals; write results to **new artifact** `data/processed/correlation_results.csv` with columns: `metric_name`, `score_type`, `correlation`, `p_value`, `p_adj_bonferroni`, `cohens_d`, `ci_lower`, `ci_upper`. **Verification**: Verify file exists and schema matches. **Note**: Do NOT append to `graph_metrics.csv` to maintain data model separation.
- [ ] T034a [US3] Generate scatter plot of Metric vs Fluid Intelligence using `matplotlib`/`seaborn`
- [ ] T034b [US3] Save scatter plot to `reports/scatter_metric_vs_fluid.png`
- [ ] T035 [US3] Generate `reports/summary.pdf` containing scatter plots, regression lines, correlation coefficients, p-values, effect sizes (Cohen's d), and confidence intervals for all significant correlations
- [ ] T036 [US3] **Generate Resource Profile**: Generate `data/processed/analysis_resource_profile.json` with keys: `peak_ram_gb` (float), `total_runtime_hours` (float). **Verification**: Verify JSON exists, keys match schema, and types are float.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T037 [P] Documentation updates in `README.md` and `quickstart.md`
- [ ] T038a [P] Refactor `preprocess.py` for sequential processing
- [ ] T038b [P] Verify RAM usage < 7GB on N=10
- [ ] T039a [P] Optimize matrix operations in `graph_metrics.py`
- [ ] T039b [P] Verify runtime < 6h for N=10
- [ ] T040 [P] Additional unit tests for edge cases (missing metadata, convergence failures)
- [ ] T041 [P] Run quickstart.md validation to ensure end-to-end reproducibility

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
 - T008a must complete before T013a
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
- All Foundational tasks marked [P] can run in parallel (within Phase 2), EXCEPT T008a which must precede T013a
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
- **Feasibility**: All tasks designed for N=10 subjects on CPU-only CI (A small number of cores, 7GB RAM, 6h limit).
- **Data Integrity**: No synthetic data generation; all analysis uses real OpenNeuro data.
- **Statistical Compliance**: Bonferroni correction used per Constitution (replacing FDR from spec).
- **Spec Conflict Note**: FR-001 (Creativity Halt) and FR-005 (FDR) are amended in this artifact to reflect the Plan (Fluid Intelligence, N=10, Bonferroni).
- **Ordering Note**: Validation (T016) and Motion Exclusion (T018) now correctly follow Preprocessing (T017) where motion metrics are derived. Resource Monitoring (T009) is implemented before integration (T011). US3 has dedicated validation (T031a) before correlation (T031c).
- **Log Differentiation**: T016c writes to `validation_errors.log` and T018b writes to `motion_exclusion.log` to prevent ambiguous failure states.
- **Data Model Separation**: T033 writes to `correlation_results.csv` to avoid conflating predictor data with analysis results.