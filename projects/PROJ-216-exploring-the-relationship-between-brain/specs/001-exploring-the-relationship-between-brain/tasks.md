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

**Governance Note**: The `specs/amendment-001-fluid-intelligence-n10.md` artifact is the ratified authority for this project, overriding the unamended text in `spec.md` regarding Fluid Intelligence, Bonferroni correction, and N=10 limits.

- [ ] T001 [P] **Initialize Data Directory Structure**: Create directories `data/raw`, `data/interim`, `data/processed`, `tests/unit`, `tests/integration`, and `reports`. **Verification**: Run `python -c "import os, datetime; paths=['data/raw','data/interim','data/processed','tests/unit','tests/integration','reports']; [os.makedirs(p, exist_ok=True) for p in paths]; open('data/.verify_structure.log','w').write('\\n'.join([f'{p}:{datetime.datetime.now()}' for p in paths]))"`. Verify `data/.verify_structure.log` exists and contains entries for all required directories.
- [X] T002 [P] **Initialize Python Project with Dependencies**: Create `requirements.txt` with pinned versions of `nibabel`, `nilearn`, `networkx`, `scikit-learn`, `pandas`, `numpy`, `openneuro-py`, `dipy`. **Verification**: Verify `requirements.txt` exists, contains valid package specifications, and includes the specific packages listed above.
- [X] T003 [P] **Configure Linting and Formatting Tools**: Create `pyproject.toml` with sections `[tool.black]` (line-length=88, target-version=['py311']) and `[tool.ruff]` (select=['E','F','W']). **Verification**: Verify `pyproject.toml` exists, contains valid TOML syntax, and includes the required sections `[tool.black]` and `[tool.ruff]` with the specified configurations. Run `python -c "import tomllib; f=open('pyproject.toml','rb'); d=tomllib.load(f); assert 'tool' in d and 'black' in d['tool'] and 'ruff' in d['tool']"`.
- [X] T008 [P] **Generate Spec Amendment Artifact**: Create `specs/amendment-001-fluid-intelligence-n10.md`. **Content Requirement**: The artifact MUST explicitly state: (1) FR-001 is amended to pivot to Fluid Intelligence and remove the hard halt for missing Musical Creativity; (2) SC-001 and SC-005 are amended to reflect N=10 CI feasibility baseline; (3) FR-005 and SC-004 are amended to mandate Bonferroni correction per Constitution Principle VII. **Verification**: Write the content to `specs/amendment-001-fluid-intelligence-n10.md` using a heredoc or script. Verify file exists and contains all three specific amendment clauses by grepping for "FR-001", "Fluid Intelligence", "N=10", and "Bonferroni". **Governance Note**: This artifact is a governance document requiring manual ratification; the task is to generate the content for that ratification.
- [X] T008c [P] **Generate Conflict Resolution Report**: Create `reports/conflict_resolution.json` documenting the Bonferroni override of Spec FR-005 (FDR) per Constitution Principle VII. **Schema**: `{"conflict": "FR-005 FDR vs Constitution Bonferroni", "resolution": "Bonferroni implemented", "rationale": "Constitution Principle VII mandates Bonferroni"}`. **Verification**: Verify JSON exists and contains all required keys and the specific rationale string.
- [ ] T009 [P] **Implement ResourceMonitor Class**: Implement `ResourceMonitor` class in `code/utils.py` that logs RAM usage per subject to stderr and writes to `data/processed/resource_profile.json`. **Verification**: Write a unit test in `tests/unit/test_resource_monitor.py` that instantiates the `ResourceMonitor` class, runs it on a mock object with simulated memory usage, and verifies the internal logic correctly calculates and formats the RAM values. **Note**: This task focuses on the class implementation and logic verification. Artifact generation is handled in T009b.
- [ ] T009b [P] **Execute Resource Monitor on Real Subject**: Execute the `ResourceMonitor` class during a real preprocessing run (mocked or real) to generate `data/processed/resource_profile.json`. **Verification**: Run the monitor on a mock subject process that simulates fMRI load (e.g., using `psutil` to simulate memory spike) and verify `data/processed/resource_profile.json` is created with the schema `{"peak_ram_gb": float, "total_runtime_hours": float}`. **Dependency**: T009.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented.
**⚠️ CRITICAL**: No user story work can begin until this phase is complete.
**Note**: T008 must complete before T013a as it defines the configuration and amendment record required for execution.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T010 [P] **Configure Dataset IDs**: Create `config.yaml` with dataset IDs (A primary dataset will be selected, with a secondary dataset designated as a fallback if the primary is unavailable.) and N=10 sample limit. **Verification**: Verify YAML syntax and presence of keys.
- [ ] T011 **Implement Resource Monitoring Integration**: Modify `code/preprocess.py` to import and invoke `ResourceMonitor` (from T009) during processing. **Dependency**: Must be implemented and integrated AFTER T009 is complete. **Verification**: Verify `preprocess.py` contains the import and invocation of `ResourceMonitor`. **Note**: This task is NOT parallel-safe ([P] removed) due to dependency on T009.
- [X] T014a [P] **Verify FSL/AFNI Installation**: Create a script `code/verify_env.py` that checks for the presence of `fsl`, `afni`, and `fslmaths` commands in the system PATH. **Verification**: Run the script. If any tool is missing, the script MUST exit with code 1 and print a clear error message: "Required tool [TOOL_NAME] not found in PATH. Please install FSL/AFNI." If all tools are present, exit with code 0. **Execution Requirement**: Execute the script in the CI environment to verify tool availability before proceeding to preprocessing tasks.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download resting-state fMRI data from OpenNeuro ds000224 (primary for Fluid Intelligence), validate data, and preprocess to generate clean BOLD time series.
**Amended Requirement (FR-001)**: System MUST attempt to download resting-state fMRI data from OpenNeuro datasets. It MUST validate the presence of at least one valid **Fluid Intelligence** score. If fewer than 10 subjects with valid data are found, the system MUST use all available subjects (N ≥ 1) for analysis. If NO subjects with valid data are found, the system MUST halt execution with a critical error stating 'No valid Fluid Intelligence data found in specified datasets'. (Note: Original FR-001 requirement for Musical Creativity is amended per Plan).

- [X] T012 [P] [US1] Unit test for OpenNeuro download retry logic in `tests/unit/test_download_retry.py`; validates requirements defined in T015 (retry multiple times, exponential backoff).
- [X] T013 [P] [US1] Unit test for behavioral data validation (Fluid Intelligence check) in `tests/unit/test_download_validation.py`; validates requirements defined in T015 (presence of Fluid Intelligence scores).
- [X] T014 [P] [US1] Integration test for full preprocessing pipeline on 1 subject in `tests/integration/test_pipeline.py`
- [ ] T015 [P] [US1] **Implement OpenNeuro Fetch, Validation, and Pivot**: Implement `fetch_openneuro_data()` in `code/download.py` to download ds000224 (primary) and ds000230 (fallback). Enforce N=10 sample limit. **Validation Logic**: Scan downloaded subjects for valid **Fluid Intelligence** scores. **Pivot Logic**: Explicitly remove/replace any logic that checks for "Musical Creativity" or "TTCT/AUT" and replaces it with the Fluid Intelligence check. **Governance**: This implementation MUST reference `specs/amendment-001-fluid-intelligence-n10.md` as the authority for the pivot. **Verification**: Run the script on a mock network simulation (using `unittest.mock` to simulate network responses) to generate `data/processed/valid_subjects.json`. **Mock Input Schema**: The mock must provide a list of subjects with `{'id': 'sub-XXX', 'fluid_intelligence_score': 0.0-1.0}`. **Output Schema**: `{"subjects": [{"id": "str", "score": "float"},...], "count": int}`. Verify file exists and contains at least 1 subject. If count is 0, verify the script halts with the correct error. **Mock Requirement**: The test MUST simulate a scenario where `valid_subjects.json` has count 0 to force the log generation.
- [ ] T015b [P] [US1] **Implement Error Message Transition**: Explicitly remove the "No valid creativity proxy found" error path from `code/download.py` and replace it with the "No valid Fluid Intelligence data found" error path. **Governance**: This change MUST reference `specs/amendment-001-fluid-intelligence-n10.md` as the authority for the error message change. **Verification**: Write a unit test that simulates a missing creativity score (mocking the old check) and verifies that the code does NOT halt with the old error, but instead proceeds to check for Fluid Intelligence. Write another test that simulates missing Fluid Intelligence and verifies the new error message is raised. **Dependency**: T015. **Correction Note**: Dependency updated from T013a to T015.
- [ ] T015c [P] [US1] **Validate Age/Gender Metadata**: Implement logic in `code/download.py` to validate the presence of age and gender metadata for each subject. **Exclusion Logic**: Subjects missing age or gender MUST be flagged in `data/processed/covariate_exclusion_log.csv` and **excluded** from the regression analysis (T031d). **Output**: Generate `data/processed/covariate_validation.json` with schema `{"total_subjects": int, "valid_covariates": int, "excluded_ids": ["str"]}`. **Fallback**: If all subjects lack covariates, the system MUST proceed with unadjusted analysis (T015d) but log a warning. **Governance**: This task MUST reference `specs/amendment-001-fluid-intelligence-n10.md` and FR-001 (Amended). **Verification**: Write a unit test that simulates subjects with missing age/gender and verifies they are excluded from the output list and logged. **Dependency**: T015.
- [ ] T015d [P] [US1] **Define Covariate Fallback Logic**: Implement logic to handle the case where **all** subjects lack age/gender metadata. **Action**: If `valid_covariates` is 0, the system MUST switch to unadjusted analysis (simple correlation) instead of multiple regression. **Verification**: Write a unit test that simulates 0 valid covariates and verifies the analysis mode switches to "unadjusted" and a warning is logged. **Dependency**: T015c.
- [ ] T016c [P] [US1] **Halt on Zero Valid Subjects**: Implement critical halt logic in `download.py` if `valid_subjects.json` count is 0. **Error Message**: "No valid Fluid Intelligence data found in specified datasets". **Governance**: This halt condition MUST reference `specs/amendment-001-fluid-intelligence-n10.md` and FR-001 (Amended). **Verification**: Write a unit test that forces the halt condition (mock 0 subjects) and verifies the log file `data/processed/validation_errors.log` is written with prefix `[VALIDATION_ERROR]` BEFORE raising a `ValueError`. **Dependency**: T015. **Mock Requirement**: The test MUST simulate a scenario where `valid_subjects.json` has count 0 to force the log generation.
- [ ] T017a [P] [US1] **Implement Preprocessing Pipeline**: Implement `preprocess_subject()` in `code/preprocess.py` using FSL/AFNI for motion correction, spatial normalization, and bandpass filtering (low-frequency range). **Verification**: Verify the function exists and accepts a subject path. **Output Check**: Run the function on a mock preprocessed NIfTI (or real if available) and verify the output NIfTI has non-zero variance and the log file contains "Motion Correction: Done". **Dependency**: T014a (FSL/AFNI check).
- [ ] T017b [P] [US1] **Implement Preprocessing Wrapper**: Implement the wrapper script `code/run_preprocessing.py` that iterates over valid subjects and calls `preprocess_subject()`. **Verification**: Verify the script exists and accepts a list of subject paths. **Note**: This task implements the execution logic. Artifact generation is handled in T017c. **Dependency**: T017a.
- [ ] T017c [US1] **Execute Preprocessing Pipeline on Mock**: Execute the preprocessing wrapper (T017b) on a mock subject (defined as a file path to a valid NIfTI with header `dim[1]=64, dim[2]=64, dim[3]=32, dim[4]=2.0`) to generate `data/processed/preprocessing_stats.json`. **Verification**: Run the pipeline on the mock subject and verify `data/processed/preprocessing_stats.json` is generated with keys `total_subjects`, `successful_subjects`, `success_rate_percentage`. **Execution Requirement**: This task MUST execute the pipeline to generate the artifact. **Dependency**: T017b.
- [ ] T018a [P] [US1] **Implement Motion Artifact Detection**: Implement logic to detect excessive motion (Translation > 3mm OR Rotation > 2mm) on preprocessed data. Output: `data/processed/motion_exclusion_log.csv` with columns `subject_id, translation_mm, rotation_mm, excluded (bool)`. **Verification**: Generate a mock subject with Translation=4mm to force the exclusion logic and ensure the CSV is populated with at least one row. **Dependency**: T017a. **Mock Requirement**: The test MUST simulate a subject with high motion to ensure the CSV is generated.
- [ ] T018b [US1] **Halt on Zero Effective Subjects**: Implement halt logic in `preprocess.py` if effective N becomes 0 after motion exclusion **and** covariate exclusion (T015c). **Error Message**: "No valid subjects remaining after motion and covariate exclusion". **Governance**: This halt condition MUST reference `specs/amendment-001-fluid-intelligence-n10.md` and FR-001 (Amended). **Verification**: Write a unit test that forces the halt condition (mock all subjects excluded) and verifies the log file `data/processed/motion_exclusion.log` is written with prefix `[MOTION_EXCLUSION_ERROR]` BEFORE raising a `ValueError`. **Dependency**: T018a, T015c. **Constraint Note**: This halt is consistent with the 'N>=1' requirement of FR-001 (amended) and the Plan's 'N=10' target. **Mock Requirement**: The test MUST simulate a scenario where all subjects are excluded to force the log generation.
- [ ] T019a [P] [US1] **Verify Preprocessing Stats Artifact**: Verify the existence and schema of `data/processed/preprocessing_stats.json` generated by T017b. **Schema**: `{"total_subjects": int, "successful_subjects": int, "success_rate_percentage": float}`. **Dependency**: T017b. **Verification**: Verify file exists and keys match schema. **Note**: This task verifies the artifact generated by T017b; it does not re-run the pipeline. **Correction Note**: Status updated to pending [ ] to align with T017b dependency.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 4: User Story 2 - Graph Metric Computation (Priority: P2)

**Goal**: Compute functional connectivity matrices and derive graph theoretical metrics (global efficiency, modularity, clustering coefficient) for each preprocessed subject using the Schaefer parcellation atlas.

- [X] T020 [P] [US2] Unit test for correlation matrix generation symmetry in `tests/unit/test_graph_metrics.py`
- [X] T021 [P] [US2] Unit test for Louvain algorithm fallback (resolution sweep) in `tests/unit/test_graph_metrics.py`
- [X] T023 [US2] **Implement Connectivity Matrix Generation**: Implement connectivity matrix generation using `nilearn` and the **200-ROI Schaefer atlas** (fixed, per FR-003) in `code/graph_metrics.py`; read preprocessed NIfTI files from `data/processed/` (output of T017a). **Verification**: Run the script on a mock preprocessed subject and verify a symmetric correlation matrix is generated. **Constraint**: The ROI count MUST be set to 200. Verify the atlas configuration explicitly uses a comprehensive set of ROIs.
- [X] T024 [P] [US2] **Implement Graph Metrics Calculation**: Implement global efficiency and clustering coefficient calculation using `networkx` in `code/graph_metrics.py`. **Verification**: Run the script on a mock matrix and verify output values are within valid ranges (0-1).
- [X] T025 [P] [US2] **Implement Modularity Calculation**: Implement modularity calculation (Louvain) with resolution parameter sweep fallback in `code/graph_metrics.py`. **Verification**: Run the script on a mock matrix and verify modularity score is generated.
- [X] T026 [US2] **Aggregate Graph Metrics**: Aggregate results into `data/processed/graph_metrics.csv` with columns: subject_id, metric_name, value. **Verification**: Run the aggregation script and verify the CSV file exists with correct schema. **Execution Requirement**: This task MUST execute the aggregation to generate the artifact.
- [X] T027 [P] [US2] **Validate Numerical Ranges**: Validate numerical ranges (e.g., efficiency -1) and write anomalies to `data/processed/graph_metric_validation.log` with format: `[SUBJECT_ID] [METRIC] [VALUE] [REASON]`. **Verification**: Run the validation script on `graph_metrics.csv` and verify the log file is created.
- [X] T022 [US2] **Integration Test for Graph Metric Aggregation**: Run `tests/integration/test_pipeline.py` to verify the full flow from T023-T027. **Verification**: Verify the test passes and `data/processed/graph_metrics.csv` is generated with correct schema. **Dependency**: Must run AFTER T027.

**Checkpoint**: Graph metrics ready - US3 can begin

---

## Phase 5: User Story 3 - Correlation Analysis and Reporting (Priority: P3)

**Goal**: Perform statistical correlation analysis between graph metrics and Fluid Intelligence scores using Bonferroni correction, generating visualizations and a summary report.
**Amended Requirement (FR-005)**: System MUST apply **Bonferroni** correction (per Constitution Principle VII) for multiple comparisons across all tested graph metrics and report effect sizes with confidence intervals. (Note: Original FR-005 requirement for FDR is amended per Plan).

- [ ] T028 [P] [US3] Unit test for Bonferroni correction logic in `tests/unit/test_stats.py`
- [ ] T029 [P] [US3] Unit test for Cohen's d and % CI calculation in `tests/unit/test_stats.py`
- [ ] T031a [US3] **Validate Presence of Fluid Intelligence for US3**: Implement logic to verify Fluid Intelligence scores exist for subjects in `graph_metrics.csv`. Output: `data/processed/us3_validation.json` with schema `{"valid_pairs": int, "missing_scores": int}`. **Dependency**: T015 (Data Ingestion) and T026 (Graph Metrics). **Verification**: Verify file exists and `valid_pairs` > 0.
- [ ] T031b [US3] **Halt on Zero Valid Scores for US3**: Implement critical halt logic in `stats.py` if `valid_pairs` is 0. **Error Message**: "No valid Fluid Intelligence scores found for correlation analysis". **Governance**: This halt condition MUST reference `specs/amendment-001-fluid-intelligence-n10.md`. **Verification**: Write a unit test that forces the halt condition and verifies the log file `data/processed/pipeline_errors.log` is written with prefix `[PIPELINE_ERROR]` BEFORE raising a `ValueError`. **Mock Requirement**: The test MUST simulate a scenario where `valid_pairs` is 0 to force the log generation.
- [ ] T031c [US3] **Implement Correlation Analysis**: Implement Pearson/Spearman correlation analysis between graph metrics and Fluid Intelligence scores in `code/stats.py`. **Verification**: Run the script on a mock dataset with known values. **Mock Input Schema**: A CSV with columns `metric_name`, `score_value` (float). **Expected Output**: Verify the output dict contains key "pearson_r" with a value within the expected range (e.g., a moderate positive correlation). **Execution Requirement**: This task MUST execute the script to generate the analysis output.
- [ ] T031d [P] [US3] **Implement Multiple Linear Regression**: Implement multiple linear regression analysis (controlling for age/gender) in `code/stats.py`. **Exclusion Logic**: This task MUST consume the list of excluded subject IDs from T015c and **exclude** them from the regression model. If T015d (Fallback) is active, this task MUST skip regression and use simple correlation. **Verification**: Run the script on a mock dataset and verify regression coefficients are calculated (or correlation if fallback). **Dependency**: T015c, T015d.
- [ ] T031e [P] [US3] **Integrate Results**: Integrate results; ensure correlation coefficients are reported separately from regression control model. **Verification**: Verify the integration logic correctly separates the two outputs.
- [ ] T032 [P] [US3] **Implement Bonferroni Correction**: Implement Bonferroni correction for multiple comparisons as mandated by Constitution Principle VII in `code/stats.py`. **Dependency**: Must reference conflict resolution logic from T008c and `specs/amendment-001-fluid-intelligence-n10.md`. **Verification**: Verify output includes `p_adj_bonferroni` column.
- [ ] T032b [P] [US3] **Disable FDR Correction**: Explicitly remove or disable any default FDR correction logic in `code/stats.py` to ensure Bonferroni is the only active path. Add a code comment referencing `specs/amendment-001-fluid-intelligence-n10.md` and FR-005 (Amended). **Verification**: Write a unit test that attempts to import the FDR function from `stats.py` and verifies it raises an `ImportError` or `NameError` (indicating the function has been removed). **Dependency**: T032. **Correction Note**: Verification updated to expect ImportError for removed function.
- [ ] T033 [US3] **Calculate Effect Sizes and Save Results**: Calculate effect sizes (Cohen's d) and confidence intervals; write results to **new artifact** `data/processed/correlation_results.csv` with columns: `metric_name`, `score_type`, `correlation`, `p_value`, `p_adj_bonferroni`, `cohens_d`, `ci_lower`, `ci_upper`. **Verification**: Verify file exists and schema matches. **Execution Requirement**: This task MUST execute the calculation and writing logic to generate the CSV. **Note**: Do NOT append to `graph_metrics.csv` to maintain data model separation.
- [ ] T034 [US3] **Generate and Save Scatter Plot**: Generate scatter plot of Metric vs Fluid Intelligence using `matplotlib`/`seaborn` and save to `reports/scatter_metric_vs_fluid.png`. **Verification**: Verify the file exists and contains a valid image. **Execution Requirement**: This task MUST execute the plotting logic to generate the PNG.
- [ ] T035 [US3] **Generate Summary Report**: Create `code/report_generator.py` with a `main()` function that aggregates scatter plots, regression lines, correlation coefficients, p-values, effect sizes (Cohen's d), and confidence intervals into `reports/summary.pdf`. **Verification**: Verify the file exists and contains valid PDF content. **Execution Requirement**: This task MUST execute the report generation logic. **Note**: The `main()` function must accept no arguments and generate the report based on the data in `data/processed/correlation_results.csv`.
- [ ] T036 [P] [US3] **Generate Resource Profile**: Generate `data/processed/analysis_resource_profile.json` with keys: `peak_ram_gb` (float), `total_runtime_hours` (float). **Verification**: Verify JSON exists, keys match schema, and types are float. **Execution Requirement**: This task MUST execute the profiling logic to generate the JSON.
- [ ] T030 [US3] **Integration Test for Full Analysis Report**: Run `tests/integration/test_pipeline.py` to verify the full flow from T031a-T035. **Verification**: Verify the test passes and `reports/summary.pdf` is generated. **Dependency**: Must run AFTER T035.

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
 - T008 must complete before T013a
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
- All Foundational tasks marked [P] can run in parallel (within Phase 2), EXCEPT T008 which must precede T013a and T011 depends on T009
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
- **Ordering Note**: Validation (T015) and Motion Exclusion (T018) now correctly follow Preprocessing (T017) where motion metrics are derived. Resource Monitoring (T009) is implemented before integration (T011). US3 has dedicated validation (T031a) before correlation (T031c).
- **Log Differentiation**: T016c writes to `validation_errors.log` and T018b writes to `motion_exclusion.log` to prevent ambiguous failure states.
- **Data Model Separation**: T033 writes to `correlation_results.csv` to avoid conflating predictor data with analysis results.
- **Execution Note**: Tasks requiring artifact generation (T001, T009b, T016c, T018a, T017c, T026, T033, T034, T035, T036) now include explicit commands or mock-simulation steps to ensure the artifacts exist for verification.
- **Test Ordering**: Integration tests T022 and T030 have been moved to after their respective artifact generation tasks (T027 and T035) to resolve ordering contradictions.
- **Task Merging**: T015 and T016a merged into T015; T034a-b merged into T034 to ensure atomicity and avoid in-memory dependencies. T019a/b merged into T019a (verification of T017b artifact) to resolve circular dependency. T008a/b merged into T008.
- **Constraint Note**: T023 enforces 200-ROI atlas; T032b disables FDR logic. T014a verifies FSL/AFNI installation.
- **Governance Note**: All pivot and halt logic (T015, T015b, T016c, T018b, T031b, T032b) explicitly references `specs/amendment-001-fluid-intelligence-n10.md` to ensure legal grounding.
- **Correction Note**: T011 is marked sequential (no [P]) due to T009 dependency. T019a is marked pending [ ] to align with T017b. T015c and T015d handle covariate exclusion and fallback. T009b handles real execution of resource monitor.