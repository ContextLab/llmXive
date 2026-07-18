# Tasks: The Cognitive Mechanisms Underlying Intuitive Moral Judgments in Virtual Environments

**Input**: Design documents from `/specs/001-cognitive-mechanisms-moral-judgments/`
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

- [X] T001a [P] Create root directories: `code/`, `data/`, `tests/`, `state/`
- [X] T001b [P] Create subdirectories: `data/raw/`, `data/processed/`, `data/logs/`, `reports/`. **Verification**: Confirm via `ls -d data/raw/ data/processed/ data/logs/` and ensure `.gitkeep` files exist in each.
- [X] T002 Initialize Python 3.11 project with `requirements.txt` (pymc>=5.0.0, pandas, numpy, scikit-learn, pyyaml, requests, seaborn, statsmodels)
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools
- [X] T004 [P] Initialize `.gitignore` and CI configuration (GitHub Actions) for CPU-only environment

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. Includes Real Data Architecture Definition (T050), Configuration (T044, T045), and Model Schema (T051) to ensure Producer before Consumer.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Create `code/config.py` defining paths, random seeds, and constants
- [X] T006 Implement `code/utils/hashing.py` to calculate SHA-256 checksums and update `state/...yaml` (Constitution Principle V)
- [X] T007 Create `code/utils/norms.py` to load and reference Gervais et al. psychometric norms <!-- FAILED: unspecified -->
- [X] T008b [P] Implement `code/utils/schema.py` using Pydantic to create schema classes for MFQ, Stories, and VR Logs (validates data schemas). **Deliverable**: A valid Pydantic model class for each entity.
- [X] T009 [P] Implement `code/utils/logging.py` for base logging infrastructure. **Deliverable**: A configured logger in `code/utils/logging.py` that captures exclusion reasons and VR mapping logs to `data/logs/`.
- [X] T050 [P] [US4-Interface] Define Real Data Architecture Interfaces in `code/data/ingest_real.py`. **Deliverable**: A module defining explicit constants and schemas: `OSF_API_URL` (base URL), `HF_DATASET_ID`, and `VR_LOG_SCHEMA_COLUMNS` (response_time, gaze_x, gaze_y, judgment_rating). These must be defined as constants, not just `raise NotImplementedError`, to ensure the interface is populated. **Note**: This task defines the *interface* for Phase 4; the *implementation* (fetch logic) is deferred.
- [X] T051 [P] [US2] Define `ModelResult` Artifact Schema in `code/utils/schemas.py`. **Deliverable**: A JSON/Parquet schema definition file (or Pydantic model) explicitly including fields: `participant_id`, `posterior_samples`, `r_hat`, `is_inconclusive` (boolean), and `mle_fallback` (float). This schema must be defined *before* T022/T023 implementation.
- [X] T044 [P] [US1] Create `data/config/unity_blend_shapes.yaml` defining the exact mapping of text story IDs to VR blend-shape parameters (low/high salience) used in the simulation. **Deliverable**: A YAML file that serves as the single source of truth for the "perceptual salience" variable, replacing the assumption of a runtime Unity environment.
- [X] T045 [P] [US3] Implement `code/analysis/power_analysis.py` to calculate the minimum detectable effect size (MDES) for a mixed-effects model with N=200 participants and 50 vignettes, assuming a standard deviation of 1.0 and alpha=0.05. **Deliverable**: A report stating the MDES and confirming that the `ground_truth_effect` in the simulation is above this threshold, ensuring the validation is statistically meaningful. **Note**: Use N=200 and SD=1.0 as defined in `plan.md` Section "Success Criteria".
- [X] T038 [P] [US1] Implement `code/data/unity_verification.py` to verify the simulation's fidelity to the actual Unity environment by validating blend-shape parameters against a reference configuration file. **Authorization**: This task replaces the Spec's assumption of a runnable Unity environment with a mock configuration, explicitly citing the "Staged Implementation Authorization" in `plan.md` as the authority for this substitution. **Deliverable**: A script that validates the `data/config/unity_blend_shapes.yaml` against the simulation logic, ensuring the mock configuration is reproducible.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion, Experimental Construction, and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest synthetic MFQ and Moral Stories data, construct VR conditions with salience mapping, and validate psychometric distribution.

**Staged Implementation Authorization**: Per Plan.md Section "Pipeline Validation", FR-006 ("capture and process actual VR interaction data") and the scientific hypothesis validation (SC-002) are explicitly deferred to Phase 4. The tasks in this phase (T013-T018) are authorized to use **Simulation-Only** data with a known `ground_truth_effect` to validate the pipeline architecture and statistical engine. Real data ingestion (T041-T043) is defined in Phase 2 (Interface) and implemented in Phase 4.

**Default Execution Mode**: `simulation`. The system defaults to using synthetic data. To switch to `real` mode, `code/config.py` must be explicitly set to `DATA_MODE='real'`. If `DATA_MODE='real'`, the system MUST execute Phase 4 tasks; if Phase 4 fails, the run MUST halt with `DataFetchError` (no synthetic fallback).

**Independent Test**: The pipeline can be tested by running the ingestion and construction scripts against the synthetic data and verifying that the output CSV contains correctly merged rows, valid salience labels, and matches Gervais et al. norms.

### Real Data Architecture Definition (Staged Implementation)

**Purpose**: Define the architecture for real data ingestion (FR-001, FR-006) to ensure simulation schema compatibility. **Note**: T050 defines the *interface*; T041 (Phase 4) implements the *logic*.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation. These tasks define the interface for T013-T018 based on the schema defined in T014a-3.

- [X] T010 [P] [US1] Unit test for synthetic MFQ generator in `code/tests/test_ingest_mfq.py`. **Deliverable**: Function `test_mfq_distribution_matches_norms` that asserts `assert mean within 1 SD of Gervais et al.` using values explicitly loaded from `data/config/gervais_norms.yaml`.
- [X] T011 [P] [US1] Unit test for salience mapping logic in `code/tests/test_schema.py`. **Deliverable**: Function `test_salience_mapping_valid` that asserts `assert salience_level in ['low', 'high']` given mock story IDs.
- [X] T012 [US1] Unit test for psychometric norm validation in `code/tests/test_ingest_stories.py`. **Deliverable**: Function `test_psychometric_validity` using Kolmogorov-Smirnov test with p > 0.05 threshold against Gervais et al. norms.

### Implementation for User Story 1 (Simulation-Only)

**Note**: These tasks implement **Simulation-Only** data generation, authorized by the "Staged Implementation Authorization" block above. FR-001 and FR-006 (Real Data Ingestion) are deferred to Phase 4. The simulation mimics the real data schema defined in T050.

- [X] T013 [US1] Implement `code/data/simulation_mfq.py` to generate synthetic MFQ data based on Gervais et al. (year) multivariate normal distributions. **Validation**: The `ground_truth_effect` parameter must be validated against the MDES calculated in T045 by reading the value from `state/mdes_report.yaml`. **Dependency**: Phase 2 (T045) must complete first to provide MDES values. **[Simulation-Only, Authorized by Phase 3 Staged Implementation]** <!-- FAILED: unspecified -->
- [X] T014 [US1] Implement `code/data/simulation_stories.py` to generate **Validation-Only** simulated Moral Stories and VR interaction logs (response times, gaze, judgment) with a known `ground_truth_effect` to proxy FR-006 requirements. **Note**: Simulation-only implementation; FR-006 (Real Data) deferred to Phase 4. This task uses constants from T050 (OSF_API_URL, HF_DATASET_ID) for schema alignment but does not fetch real data. **[Simulation-Only, Authorized by Phase 3 Staged Implementation]** <!-- FAILED: unspecified -->
- [X] T014a [US1] Verify OSF API URL constant. **Deliverable**: A script or test in `code/tests/test_real_interfaces.py` that imports `OSF_API_URL` from `code/data/ingest_real.py` (defined in T050) and asserts it matches the expected canonical OSF base URL. **Dependency**: T050 must be complete.
- [X] T014b [US1] Verify HuggingFace Dataset ID constant. **Deliverable**: A script or test in `code/tests/test_real_interfaces.py` that imports `HF_DATASET_ID` from `code/data/ingest_real.py` (defined in T050) and asserts it matches the expected canonical HF dataset ID. **Dependency**: T050 must be complete.
- [X] T014c [US1] Verify VR Log Schema columns. **Deliverable**: A script or test in `code/tests/test_real_interfaces.py` that imports `VR_LOG_SCHEMA_COLUMNS` from `code/data/ingest_real.py` (defined in T050) and asserts it contains the required columns (response_time, gaze_x, gaze_y, judgment_rating). **Dependency**: T050 must be complete.
- [X] T015 [US1] Implement `code/data/ingest.py` to load and merge synthetic MFQ and Moral Stories datasets, handling ID mismatches. **Routing**: If `DATA_MODE='real'`, explicitly call `code/data/ingest_real.py` (Phase 4) to fetch real data; otherwise, use simulation. **Constraint**: Must include a hard assertion that `DATA_MODE` is defined in `code/config.py`. If `DATA_MODE='real'` and Phase 4 tasks are incomplete, raise `NotImplementedError` immediately. **Note**: Simulation-Only (FR-006 Deferred to Phase 4).
- [X] T015a [US1] Implement logging logic in `code/data/ingest.py` to capture exclusion reasons for mismatched IDs to `data/logs/exclusion.log`. **[Simulation-Only]**
- [X] T016 [US1] Implement `code/data/preprocess.py` to map text stories to VR scenes, assigning `salience_level` (low/high) via blend-shape parameters. **Dependency**: Read configuration from `data/config/unity_blend_shapes.yaml` (T044). **Note**: Simulation-Only (FR-006 Deferred to Phase 4). **Sub-task**: Implement logging of VR mapping logs (story ID -> salience level) to `data/logs/vr_mapping.log` within this task. **Log Format**: CSV with columns `story_id`, `salience_level`, `blend_shape_params` (JSON string). **Dependency**: Phase 2 (T044) must complete first. **Constraint**: T016 cannot start until Phase 2 is fully complete.
- [X] T017 [US1] Add validation logic to existing `code/utils/norms.py` to compare synthetic MFQ distribution against published norms (must be within 1 SD). **Dependency**: Must validate output of T013. <!-- FAILED: unspecified -->
- [X] T018 [US1] Implement `code/utils/hashing.py` integration to checksum **simulation-derived** CSVs and update `state/...yaml` <!-- FAILED: unspecified -->

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Bayesian Model Execution and Comparison (Priority: P2)

**Goal**: Execute a Bayesian decision model on the preprocessed data to estimate the effect of visual salience, validating parameter recovery and scientific evidence.

**Independent Test**: The model execution can be tested by running the PyMC3 script on the synthetic data and verifying that the model recovers the `ground_truth_effect` within the 95% credible interval and converges (R-hat < 1.05).

### Simulation Validation (US2)

- [X] T020 [P] [US2] Unit test for model convergence check in `code/tests/test_model_convergence.py`. **Deliverable**: Function `test_convergence_check` that asserts `assert r_hat < 1.05 ` given mock posterior samples.
- [X] T021 [US2] Unit test for parameter recovery validation in `code/tests/test_model_recovery.py`. **Deliverable**: Function `test_parameter_recovery` injecting `ground_truth_effect=0.5` and asserting recovery within 95% CI.
- [X] T022 [US2] Implement `code/models/bayesian.py` defining the PyMC3 model structure: Gaussian likelihood, Normal priors, foundation scores as covariates, salience as fixed-effect predictor <!-- FAILED: unspecified -->
- [X] T023 [US2] Implement `code/models/bayesian.py` logic to handle convergence failures: log failure, **report the maximum likelihood estimate (MLE) value** in the output artifact, and **flag the run as 'inconclusive'** for that participant. **Deliverable**: The `ModelResult` artifact (JSON/Parquet) MUST include a boolean field `is_inconclusive` and a field `mle_fallback` containing the MLE value when convergence fails. **Dependency**: T051 (ModelResult Schema). **Prerequisite**: Phase 2 must be fully completed (including T051) before Phase 4 implementation tasks can begin. **Verification**: Ensure `code/utils/schemas.py` is importable and contains the `ModelResult` definition before execution.
- [X] T026 [US2] Implement `code/analysis/validation.py` to verify **Parameter Recovery**: check if `ground_truth_effect` is within the credible interval of the posterior (Primary Validation Metric)

### Model Comparison (US2)

- [X] T024 [US2] Implement `code/analysis/model_comparison.py` to calculate AIC and WAIC for the salience-augmented model vs. baseline (no salience)
- [X] T025 [US2] Implement `code/analysis/model_comparison.py` to perform Posterior Predictive Checks (PPC): generate synthetic data from the posterior, compare distributions to observed data, and produce a visual plot (histogram/KDE) of observed vs. generated data. **Deliverable**: A plot and a quantitative metric (e.g., KS-test p-value) for the PPC.
- [X] T027 [US2] Implement `code/analysis/model_comparison.py` to explicitly check and report metrics: Detect `RUN_MODE` from `config.py`. **Requirement**: Always calculate and report ΔAIC. If 'simulation', log `LOG: Scientific Metric: Calculated (ΔAIC={val}) - Claim Deferred per Phase 3 Staged Implementation` and prioritize "Parameter Recovery"; if 'real', flag 'strong evidence' (ΔAIC > 10) as required by SC-002. **Authorization**: This override of SC-002 is authorized by the Phase 3 Staged Implementation plan.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Validation and Reporting (Priority: P3)

**Goal**: Perform hierarchical mixed-effects regression with Bonferroni correction and generate the final validation report.

**Independent Test**: The validation step can be tested by running the regression and verifying that the interaction term (salience × foundation) is reported with a Bonferroni-corrected p-value and the report includes the sensitivity analysis.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T028 [P] [US3] Unit test for Bonferroni correction logic in `code/tests/test_model.py`. **Deliverable**: Function `test_bonferroni_correction` using input p-values (list of values), number of tests (corresponding count), and asserting expected corrected p-values.
- [X] T029 [P] [US3] Unit test for sensitivity analysis thresholds in `code/tests/test_model.py`. **Deliverable**: Function `test_sensitivity_thresholds` using threshold set {2, 10, 20} and asserting expected output format (stability matrix).

### Implementation for User Story 3

- [X] T030 [US3] Implement `code/models/regression.py` for hierarchical mixed-effects regression testing the salience × foundation interaction
- [X] T031 [US3] Implement `code/analysis/validation.py` to apply Bonferroni correction to interaction term p-values
- [X] T032 [US3] Implement `code/analysis/validation.py` to conduct sensitivity analysis sweeping decision thresholds over the specific set **{2, 10, 20}** and report model selection stability matrix
- [X] T033 [US3] Implement `code/reports/generate_report.py` to generate the final report summarizing findings (Pipeline Validation: PASSED/FAILED) <!-- FAILED: unspecified -->
- [X] T034 [US3] Ensure `code/reports/generate_report.py` explicitly states "Pipeline Validation Only" while including a clear statement of findings regarding the hypothesis (as per US-3), deferring final scientific claims to Phase 4 by noting **"Evidence strength (ΔAIC) calculated but claim deferred per Phase 3 Staged Implementation."**

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: User Story 4 - Real Data Integration (Priority: P4 - Deferred)

**Goal**: Implement the ingestion of real VR interaction logs and a verified "Moral Stories" dataset when available.

**Status**: **DEFERRED**. These tasks are only active when `DATA_MODE='real'` and `PHASE=4`.

- [X] T041 [P] [US4-Real] Implement `code/data/ingest_real.py` with strict "Fail Loudly" logic: attempt to fetch real MFQ data from OSF and real Moral Stories from HuggingFace; if fetch fails, raise a `DataFetchError` immediately without falling back to synthetic generators. **Deliverable**: A robust fetcher that halts execution on network/source failure, ensuring no synthetic data is used when real data is expected. **Implementation Detail**: Use `OSF_API_URL` from T050 and explicitly implement the OSF endpoint path (`/v2/nodes/{node_id}/files/osfstorage`) with required query parameters and response schema validation. **Trigger**: Only execute if `DATA_MODE='real'`.
- [X] T042 [P] [US4-Real] Implement `code/data/ingest_real.py` to parse real VR interaction logs from a specified CSV/JSON source and validate against the schema defined in T050. **Deliverable**: A parser that validates real data structure and raises `SchemaError` if real data is malformed, preventing silent data corruption. **Trigger**: Only execute if `DATA_MODE='real'`.
- [X] T043 [US4-Real] Update `code/config.py` to add a `DATA_MODE` flag (`'simulation'` | `'real'`). **Default**: `'simulation'`. Ensure `code/data/ingest.py` routes to `ingest_real.py` when `DATA_MODE='real'` and to `simulation.py` when `DATA_MODE='simulation'`, with a hard assertion that `DATA_MODE` cannot be 'real' without a verified source. **Deliverable**: Config-driven routing that enforces the "Real Data Only" constraint when requested. **Trigger**: Only execute if `DATA_MODE='real'`.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T035 [P] Documentation updates: Add installation instructions, update usage examples, and add data schema reference in `README.md` and `docs/`
- [X] T036a [P] Code cleanup: Remove unused imports from all Python files in `code/`. **Verification**: Run `ruff check code/` and ensure no unused import warnings.
- [X] T036b [P] Code cleanup: Enforce black formatting on all Python files in `code/`. **Verification**: Run `black --check code/` and ensure no formatting errors.
- [X] T037 [P] Implement CPU-only performance profiling in `code/analysis/profile_pipeline.py` to guarantee full pipeline execution completes within the CI limit on the free-tier runner (limited cores, constrained RAM). **Success Criterion**: Record pipeline runtime in `state/perf_metrics.yaml` and validate against the established time threshold.
- [X] T039 [P] Additional unit tests for edge cases: Implement specific tests for (1) missing data handling in ingestion (`test_missing_data_handling`), (2) convergence failure in Bayesian model (`test_convergence_failure`), and (3) invalid schema in preprocessing (`test_invalid_schema`). **Deliverable**: `code/tests/test_edge_cases.py` with passing tests for each scenario, including specific input fixtures and expected exceptions.
- [X] T040 [P] Run `quickstart.md` validation and verify all artifacts are checksummed. **Execution**: Execute `python -m code.quickstart` and verify `state/...yaml` contains non-empty `artifact_hashes`.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 model output
- **User Story 4 (P4)**: Depends on US1-US3 completion and explicit `DATA_MODE='real'` trigger

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Simulation/Ingestion before Preprocessing
- Model Definition before Execution
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
Task: "Unit test for synthetic MFQ generator in code/tests/test_ingest_mfq.py"
Task: "Unit test for salience mapping logic in code/tests/test_schema.py"
# T012 is not marked [P] to avoid file conflicts if shared fixtures are used.

# Launch all models for User Story 1 together:
Task: "Implement code/data/simulation_mfq.py to generate synthetic MFQ data"
Task: "Implement code/utils/norms.py validation logic"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Synthetic Data Ingestion & Validation)
4. **STOP and VALIDATE**: Test User Story 1 independently (verify psychometric norms and schema)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently (verify parameter recovery) → Deploy/Demo
4. Add User Story 3 → Test independently (verify reporting) → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Data Pipeline)
 - Developer B: User Story 2 (Bayesian Model)
 - Developer C: User Story 3 (Validation & Reporting)
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
- **Critical Constraint**: All modeling must run on CPU-only CI (no CUDA, no 8-bit quantization). Use default precision (float64).
- **Data Integrity**: Synthetic data must have a known `ground_truth_effect` to validate the pipeline; real data ingestion (T041-T043) is deferred to Phase 4 and gated by `DATA_MODE`.
- **Performance Constraint**: T037 must ensure the full pipeline (ingestion → modeling → reporting) completes within 6 hours on the free-tier CPU runner.
- **Simulation-Only Override**: T013-T018 are explicitly marked "Simulation-Only" as FR-006 (Real VR Logs) is deferred to Phase 4, authorized by the "Staged Implementation Authorization" block in Phase 3.
- **Revision Concern**: The current plan relies on a "Simulated" Moral Stories dataset and OSF MFQ fetch stubs. While valid for pipeline validation, the spec requires a **Real Data** ingestion path (FR-001, FR-006) that does not fall back to synthetic data. T050 defines the interface, and T041-T043 (Phase 4) implement the **Real Data Fetcher** with strict "Fail Loudly" semantics, ensuring that if real data is unavailable, the pipeline halts rather than substituting fake data, satisfying the "No Fabrication" rule.
- **Revision Concern**: The spec assumes Unity VR scene accessibility for blend-shape mapping. T044 addresses the gap by creating a **Mock Unity Configuration** task that defines the exact JSON schema for blend-shape parameters, ensuring the simulation logic (T016) is grounded in a defined, reproducible configuration rather than an assumed runtime environment.
- **Revision Concern**: The sensitivity analysis (T032) currently sweeps thresholds but lacks a formal **Power Analysis** task to justify the sample size (N=200) for the planned mixed-effects regression. T045 adds a task to compute the minimum detectable effect size for N=200, ensuring the simulation is statistically powered to recover the `ground_truth_effect`.
- **Revision Concern**: T025 contained a placeholder. Replaced with concrete PPC implementation steps.
- **Revision Concern**: T016a was marked rejected. Updated to be an active task for logging VR mapping logs (merged into T016).
- **Revision Concern**: T051 added to define `ModelResult` schema before implementation.
- **Revision Concern**: T052 removed to eliminate redundant scope documentation (plan.md already defines the override).

<!-- auto-added by the execution fix loop: run-book / implementation path mismatch (a quickstart command names a script no task created) -->
- [X] T053 Reconcile run-book vs implementation for `code/data/simulation.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/data/simulation.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.
