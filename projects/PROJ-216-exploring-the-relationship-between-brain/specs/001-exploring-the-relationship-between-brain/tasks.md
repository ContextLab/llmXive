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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 [P] Initialize project directory structure (`data/raw`, `data/interim`, `data/processed`, `code`, `tests/unit`, `tests/integration`, `reports`) and create `__init__.py` files. Verification: Run `ls -R data/ code/ tests/ reports/ && find . -name __init__.py -print | wc -l`.
- [X] T002 [P] Initialize Python project with dependencies. Artifact: `requirements.txt` with pinned versions for `nibabel`, `nilearn`, `networkx`, `scikit-learn`, `pandas`, `numpy`, `openneuro-py`, `dipy`. Verification: Run `pip install -r requirements.txt && pip check`.
- [X] T003 [P] Configure linting and formatting tools (ruff, black). Verification: Run `ruff check .` and `black --check .` successfully.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented.
**⚠️ CRITICAL**: No user story work can begin until this phase is complete.
**Note**: T008a must complete before T013a as it defines the configuration and amendment record required for execution.

- [X] T005 [P] Implement system-level dependency check script for FSL/AFNI availability. Artifact: `scripts/check_deps.sh`. Verification: Run `bash scripts/check_deps.sh` and assert exit code 0.
- [X] T006 [P] Setup logging and error handling infrastructure. Artifact: `code/utils.py` containing `setup_logger()` function returning a configured logger instance. Verification: See T006b.
- [X] T006b [P] [US0] Unit test for logging infrastructure. Artifact: `tests/unit/test_utils.py` containing function `test_setup_logger`. Verification: Run `pytest tests/unit/test_utils.py::test_setup_logger` and assert it checks log output format and file rotation.
- [X] T007 [Dep: None] Create class `Subject` and `BehavioralScore` in `code/models.py` with attributes for ID, age, gender, file paths, score_value, source_type based on `data-model.md`; verify with `pytest tests/unit/test_models.py`
- [ ] T008a [P] Generate Spec Amendment Artifact and Conflict Resolution Report. Logic: Create `reports/spec_amendment_record.json` documenting the N=10 limit and Fluid Intelligence pivot, and `reports/conflict_resolution_report.md` detailing the Bonferroni vs. FDR conflict resolution per Constitution Principle VII. Verification: Assert `reports/spec_amendment_record.json` and `reports/conflict_resolution_report.md` exist and contain the required keys.
- [ ] T009 [P] Implement `ResourceMonitor` class in `code/utils.py` that logs RAM usage per subject to stderr and writes to `data/processed/resource_profile.json`. Verification: Unit test `tests/unit/test_resource_monitor.py` must assert JSON schema and that RAM is logged.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download resting-state fMRI data from OpenNeuro ds (primary for Fluid Intelligence), validate data, and preprocess to generate clean BOLD time series.

**Validation Note**: T010-T012 are written as **failing** tests to drive implementation. T013a implements the logic. T014a validates the implementation. Only after T013a and T014a pass are T010-T012 considered "passed".

- [ ] T010 [P] [US1] Unit test for OpenNeuro download retry logic. Artifact: `tests/unit/test_download_retry.py` containing function `test_download_retry_logic`. Verification: Run `pytest tests/unit/test_download_retry.py::test_download_retry_logic` and assert it fails initially then passes after T013a.
- [ ] T011 [P] [US1] Unit test for behavioral data validation (Fluid Intelligence check). Artifact: `tests/unit/test_download_validation.py` containing function `test_fluid_intelligence_validation`. Verification: Run `pytest tests/unit/test_download_validation.py::test_fluid_intelligence_validation` and assert it fails initially then passes after T013a.
- [ ] T012 [P] [US1] Integration test for full preprocessing pipeline on 1 subject. Artifact: `tests/integration/test_pipeline.py` containing function `test_full_pipeline_one_subject`. Verification: Run `pytest tests/integration/test_pipeline.py::test_full_pipeline_one_subject` and assert it fails initially then passes after T013a/T015.
- [ ] T013a [Dep: T008a] Implement OpenNeuro fetch for ds000224 (primary) and ds000230 (fallback) in `code/download.py`. Logic: 
  1. Attempt to download ds000224. 
  2. If ds000224 yields valid Fluid Intelligence data, use it (capped at N=10; if <10 available, use all). 
  3. If ds000224 has NO valid Fluid Intelligence data, attempt ds000230. 
  4. If ds000230 yields valid Fluid Intelligence data, use it (capped at N=10; if <10 available, use all). 
  5. If neither dataset yields valid Fluid Intelligence data, halt with critical error: "No valid Fluid Intelligence data found in specified datasets". 
  Verification: Unit tests `tests/unit/test_download.py::test_download_ds000224` and `tests/unit/test_download.py::test_download_fallback_ds000230` pass, and `data/processed/validation_report.json` is generated with N=10 limit applied.
- [ ] T014a [Dep: T013a] Validate presence of Fluid Intelligence scores in aggregated subjects. Artifact: `data/processed/validation_report.json`. Verification: Assert `data/processed/validation_report.json` exists, status is PASS, and that T013a execution caused T010-T012 tests to pass.
- [ ] T014b [Dep: T014a] Validate presence of age/gender metadata for subjects with Fluid Intelligence scores. Artifact: Append validation status to `data/processed/validation_report.json`. Verification: See T014d.
- [ ] T014d [P] [US1] Unit test for age/gender validation logic. Artifact: `tests/unit/test_validation_report.py` containing function `test_age_gender_valid`. Verification: Run `pytest tests/unit/test_validation_report.py::test_age_gender_valid` and assert it checks the validation report for age/gender presence.
- [ ] T014c [Dep: T014a] Implement halt logic if valid subject count is 0 after validation (specifically if no Fluid Intelligence scores found), raising critical error: "No valid Fluid Intelligence data found in specified datasets". Verification: Unit test `tests/unit/test_download.py::test_halt_on_missing_fluid_intel` passes.
- [ ] T015 [Dep: T014a] Implement preprocessing pipeline in `code/preprocess.py` using FSL/AFNI for motion correction, spatial normalization, and bandpass filtering (low-frequency range) as a single executable script. Dependency: T014a (Validation) must pass.
- [ ] T016a [Dep: T015] Implement motion artifact detection (>3mm translation) in `preprocess.py`. Artifact: `data/processed/motion_exclusions.csv`. Verification: Assert `data/processed/motion_exclusions.csv` exists and contains excluded subject IDs.
- [ ] T016b [Dep: T016a] Implement halt logic if effective N becomes 0 after motion exclusion. Verification: Unit test `tests/unit/test_preprocess.py::test_halt_on_zero_subjects_after_motion` passes.
- [ ] T017 [Dep: T016b] Generate `data/processed/preprocessing_stats.json` with keys: `total_subjects`, `successful_subjects`, `success_rate_percentage` (calculated as successful/total, where total is the N=10 limit or actual downloaded count)
- [ ] T018 [Dep: T015, T009] Add resource monitoring to `preprocess.py` to log RAM usage per subject (consumes `ResourceMonitor` from T009). Verification: Run `preprocess.py` on N=10 and assert `data/processed/resource_profile.json` is updated.

---

## Phase 4: User Story 2 - Graph Metric Computation (Priority: P2)

**Goal**: Compute functional connectivity matrices and derive graph theoretical metrics (global efficiency, modularity, clustering coefficient) for each preprocessed subject using the Schaefer parcellation atlas.

- [ ] T019 [P] [US2] Unit test for correlation matrix generation symmetry. Artifact: `tests/unit/test_graph_metrics.py` containing function `test_correlation_matrix_symmetry`. Verification: Run `pytest tests/unit/test_graph_metrics.py::test_correlation_matrix_symmetry` and assert it fails initially then passes after T022.
- [ ] T020 [P] [US2] Unit test for Louvain algorithm fallback (resolution sweep). Artifact: `tests/unit/test_graph_metrics.py` containing function `test_louvain_resolution_sweep`. Verification: Run `pytest tests/unit/test_graph_metrics.py::test_louvain_resolution_sweep` and assert it fails initially then passes after T024.
- [ ] T021 [P] [US2] Integration test for graph metric aggregation. Artifact: `tests/integration/test_pipeline.py` containing class `TestUS2Pipeline` and function `test_graph_metric_aggregation`. Verification: Run `pytest tests/integration/test_pipeline.py::TestUS2Pipeline::test_graph_metric_aggregation` and assert it fails initially then passes after T025.
- [ ] T022 [Dep: T017] Implement connectivity matrix generation using `nilearn` and a **fixed Schaefer atlas with a 200-ROI parcellation scheme** in `code/graph_metrics.py`; read preprocessed NIfTI files from `data/interim/sub-*_preprocessed.nii.gz`. Verification: Assert generated matrices are symmetric and match the 200-ROI dimension.
- [ ] T023 [Dep: T022] Implement global efficiency and clustering coefficient calculation using `networkx` in `code/graph_metrics.py`.
- [ ] T024 [Dep: T023] Implement modularity calculation (Louvain) with resolution parameter sweep fallback in `code/graph_metrics.py`.
- [ ] T025 [Dep: T024] Aggregate results into `data/processed/graph_metrics.csv` with columns: subject_id, metric_name, value
- [ ] T026 [Dep: T025] Validate numerical ranges (e.g., efficiency -1) and write anomalies to `data/processed/graph_metric_validation.log` with format: `[SUBJECT_ID] [METRIC] [VALUE] [REASON]`

---

## Phase 5: User Story 3 - Correlation Analysis and Reporting (Priority: P3)

**Goal**: Perform statistical correlation analysis between graph metrics and Fluid Intelligence scores using Bonferroni correction, generating visualizations and a summary report.

- [ ] T027 [P] [US3] Unit test for Bonferroni correction logic. Artifact: `tests/unit/test_stats.py` containing function `test_bonferroni_correction`. Verification: Run `pytest tests/unit/test_stats.py::test_bonferroni_correction` and assert it fails initially then passes after T031.
- [ ] T028 [P] [US3] Unit test for Cohen's d and 95% CI calculation. Artifact: `tests/unit/test_stats.py` containing function `test_cohens_d_ci`. Verification: Run `pytest tests/unit/test_stats.py::test_cohens_d_ci` and assert it fails initially then passes after T032.
- [ ] T029 [P] [US3] Integration test for full analysis report generation. Artifact: `tests/integration/test_pipeline.py` containing class `TestUS3Pipeline` and function `test_full_analysis_report`. Verification: Run `pytest tests/integration/test_pipeline.py::TestUS3Pipeline::test_full_analysis_report` and assert it fails initially then passes after T034.
- [ ] T031 [Dep: T025] Implement Bonferroni correction logic (p * k) for multiple comparisons in `code/stats.py`. Verification: Unit test `tests/unit/test_stats.py::test_bonferroni_correction` passes and `reports/conflict_resolution_report.md` (from T008a) documents the override of FR-005.
- [ ] T030a [Dep: T031] Implement critical halt logic in `stats.py` if valid Fluid Intelligence scores are empty after merge, raising error: "No valid Fluid Intelligence scores exist in the dataset". Verification: Unit test `tests/unit/test_stats.py::test_halt_on_empty_fluid_scores` passes.
- [ ] T030b [Dep: T030a] Implement Pearson/Spearman correlation analysis between graph metrics and Fluid Intelligence scores in `code/stats.py`.
- [ ] T030c [Dep: T030b] Implement multiple linear regression analysis (controlling for age/gender) in `code/stats.py`.
- [ ] T030d [Dep: T030c] Integrate results; ensure correlation coefficients are reported separately from regression control model.
- [ ] T032 [Dep: T030d] Calculate effect sizes (Cohen's d) and confidence intervals; append columns `cohens_d`, `ci_lower`, `ci_upper` to `data/processed/graph_metrics.csv`.
- [ ] T033a [Dep: T032] Generate and save scatter plot of Metric vs Fluid Intelligence using `matplotlib`/`seaborn` with regression line and 95% CI shading. Artifact: `reports/scatter_metric_vs_fluid.png`. Verification: Verify `reports/scatter_metric_vs_fluid.png` exists, is non-empty (file size > 0KB), and contains a regression line with 95% CI shading.
- [ ] T034 [Dep: T033a] Generate `reports/summary.pdf` containing scatter plots, regression lines, correlation coefficients, p-values, effect sizes (Cohen's d), and confidence intervals for all significant correlations. Verification: Verify `reports/summary.pdf` contains the string "Bonferroni" and at least one scatter plot image.
- [ ] T035 [Dep: T034] Generate `data/processed/analysis_resource_profile.json` with peak RAM and total runtime for SC-005 verification. Verification: Assert JSON keys `peak_ram_gb` and `total_runtime_hours` exist and are numeric.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T036 [P] Documentation updates in `README.md` and `quickstart.md`. Verification: Add "Usage" section to `README.md` with example CLI command and run `grep -q "Usage" README.md`.
- [ ] T037a [P] Refactor `preprocess.py` for sequential processing. Verification: Verify runtime < 6h for N=10 in `tests/integration/test_pipeline.py` and assert no parallel execution calls remain in `preprocess.py`.
- [ ] T037b [P] Verify RAM usage < 7GB on N=10. Verification: Run `code/utils.py` resource monitor on N=10 and assert `data/processed/resource_profile.json` peak_ram_gb < 7.0.
- [ ] T038a [P] Implement numpy vectorization for correlation matrix calculation in `code/graph_metrics.py` to replace nested loops. Verification: Run benchmark on N=10 and assert runtime reduced by >10% compared to non-vectorized version.
- [ ] T038b [P] Verify runtime < 6h for N=10. Verification: Run full pipeline on N=10 in CI and assert total runtime < 6h.
- [ ] T039 [P] Additional unit tests for edge cases (missing metadata, convergence failures). Verification: Add `tests/unit/test_graph_metrics.py::test_louvain_convergence_failure`, `tests/unit/test_stats.py::test_missing_metadata`.
- [ ] T040 Run quickstart.md validation to ensure end-to-end reproducibility. Verification: Execute `bash scripts/run_quickstart.sh` and assert exit code 0 and `reports/summary.pdf` exists.

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
- **Spec Conflict Resolution**: Spec amendments for N=10 and Fluid Intelligence pivot are assumed to be completed in the `plan` stage. The tasks now rely on the `plan.md` as the active guide for these deviations.
- **Task Order**: Validation (T014a) MUST precede Preprocessing (T015). Resource Monitoring (T009) MUST precede Preprocessing (T015). Scatter Plots (T033a) MUST precede Summary Report (T034).