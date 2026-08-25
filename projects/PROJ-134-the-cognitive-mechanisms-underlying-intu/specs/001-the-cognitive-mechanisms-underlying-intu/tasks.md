---
description: "Task list template for feature implementation"
---

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

 Tasks MUST be organized by user story so each story can:
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

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. Includes Real Data Architecture Definition (T050), Configuration (T044, T045, T046), and Model Schema (T051) to ensure Producer before Consumer.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.
**⚠️ BLOCKING DEPENDENCY**: T045, T046, T051, T053, T050, T055, T043, T044 MUST be completed before T013, T015, T016, T022, T023, T041.
**⚠️ SEQUENTIAL ENFORCEMENT**: T045 and T046 are the **BLOCKING TASKS** for Phase 3. They MUST complete successfully before T013 can execute. These are NOT parallelizable with Phase 3 tasks. Note: T045 -> T046; T055 depends on T050 and T008b completion.

- [ ] T045 [US3] Implement `code/analysis/power_analysis.py` to calculate the minimum detectable effect size (MDES) for a mixed-effects model with **N=200** participants and 50 vignettes, assuming a standard deviation of **1.0**, alpha=0.05, and **power=0.80**. **Deliverable**: A report stating the MDES and writing the calculated value to `state/mdes_report.yaml` under the key `mdes_value`. **Note**: Use N=200 and SD=1.0 as defined in `plan.md` Section "Success Criteria". **Constraint**: The calculated MDES must be strictly less than the `ground_truth_effect` used in the simulation to ensure statistical power; if not, the script must raise a `ValueError`. **Output**: `state/mdes_report.yaml` with key `mdes_value`. **Priority**: This task MUST be executed first in Phase 2 to ensure downstream tasks (T013) have valid MDES data. **Dependency**: T005 (config.py) must complete first. **Enforcement**: A pre-commit hook MUST be configured to verify T045 completion before T013 execution.
- [ ] T046 [US3] [Dep: T045] Implement `code/analysis/validation.py` to validate that the simulated dataset size (N) matches the MDES assumption (N=200). **Deliverable**: A validation script that reads `state/mdes_report.yaml` and asserts `N_simulated == 200`. If mismatch, raise `ValueError`. **Dependency**: T045 must complete first. **Note**: Ensures statistical power constraint is not silently violated.
- [X] T005 [P] Create `code/config.py` defining paths, random seeds, and constants
- [X] T006 [P] Implement `code/utils/hashing.py` to calculate SHA-256 checksums and update `state/artifact_hashes.yaml` (Constitution Principle V). **Deliverable**: A function `calculate_checksum(file_path: str) -> str` that returns the SHA-256 hex digest and a function `update_state_file(file_path: str, checksum: str)` that updates `state/artifact_hashes.yaml`. **Verification**: Run `python -c "from code.utils.hashing import calculate_checksum, update_state_file; update_state_file('data/processed/test.csv', calculate_checksum('data/processed/test.csv'))"` and confirm the hash is recorded in `state/artifact_hashes.yaml`. **Constraint**: This task is NOT marked [P] and must complete before any artifact generation tasks.
- [X] T007b [P] Create `data/config/gervais_norms.yaml` containing the specific psychometric values (mean, std) for MFQ dimensions as per Gervais et al. **Deliverable**: A YAML file with keys for each foundation (Care, Fairness, etc.) and values for mean and std. **Verification**: Run `python -c "import yaml; print(yaml.safe_load(open('data/config/gervais_norms.yaml')))"` and confirm keys exist.
- [X] T007 [P] Implement `code/utils/norms.py` to load and reference Gervais et al. psychometric norms. **Deliverable**: A function `load_norms() -> dict` that returns the norms.
- [X] T008b [P] Implement `code/utils/schema.py` using Pydantic to create schema classes for MFQ, Stories, and VR Logs (validates data schemas). **Deliverable**: A valid Pydantic model class for each entity.
- [ ] T009 [P] Implement `code/utils/logging.py` for base logging infrastructure. **Deliverable**: A configured logger in `code/utils/logging.py` that captures exclusion reasons and VR mapping logs to `data/logs/`. **Config**: Use `RotatingFileHandler` for `data/logs/ingest.log` and `data/logs/vr_mapping.log` with `JSONFormatter`. **Verification**: Run `python -c "from code.utils.logging import get_logger; logger = get_logger('test'); logger.info('test')"` and confirm `data/logs/ingest.log` contains the JSON log entry.
- [X] T050 [P] [US4-Interface] Define Real Data Architecture Interfaces in `code/data/ingest_real.py`. **Deliverable**: A module defining explicit constants and schemas: `OSF_API_URL` (base URL: "https://api.osf.io/v2/"), `HF_DATASET_ID` ("moral-stories-v1"), and `VR_LOG_SCHEMA_COLUMNS` (list: `["response_time", "gaze_metrics", "judgment_rating"]`). **Verification**: The module must include a `verify_constants()` function that asserts these values match the canonical sources defined in `spec.md`. **Note**: This task defines the *interface* for Phase 4; the *implementation* (fetch logic) is deferred to Phase 6.
- [X] T051 [P] [US2] Define `ModelResult` Artifact Schema in `code/utils/schemas.py`. **Deliverable**: A JSON/Parquet schema definition file (or Pydantic model) explicitly including fields: `participant_id`, `posterior_samples`, `r_hat`, `is_inconclusive` (boolean), and `mle_fallback` (float). This schema must be defined *before* T022/T023 implementation.
- [ ] T044 [P] [US1] Create `data/config/unity_blend_shapes.yaml` defining the exact mapping of text story IDs to VR scene blend-shape parameters (low/high) used in the experimental design. **Deliverable**: A YAML file that serves as the single source of truth for the "perceptual salience" variable, replacing the assumption of a runtime Unity environment. **Schema**: Must contain keys `low` and `high` with nested objects for `blend_shape_params`. **Verification**: The file must be loadable and contain the expected structure.
- [ ] T043 [P] [US1/US4] Update `code/config.py` to add a `DATA_MODE` flag (`'simulation'` | `'real'`). **Default**: `'simulation'`. Ensure `code/data/ingest.py` routes to `code/data/fetch_real.py` (Phase 6) and `code/data/parse_real_logs.py` (Phase 6) when `DATA_MODE='real'` and to `simulation.py` when `DATA_MODE='simulation'`, with a hard assertion that `DATA_MODE` cannot be 'real' without a verified source. **Deliverable**: Config-driven routing that enforces the "Real Data Only" constraint. **Dependency**: T005 must complete first.
- [ ] T053 [P] [US1/US4] This task is merged into T056, to resolve the run-book vs implementation mismatch. The `code/data/simulation.py` entry point is now defined and implemented in T056.
- [ ] T055 [P] [US1/US4] Implement `code/utils/schema_equivalence.py` to verify that the simulation data schema (generated by T014) is structurally identical to the Real Data Interface schema (defined in T050). **Deliverable**: A script that compares the Pydantic models from T008b (Simulation) and T050 (Real) and raises an error if any field mismatch is found. **Dependency**: T050 and T008b must complete first.

---

## Phase 3: User Story 1 - Data Ingestion, Experimental Construction, and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest real MFQ and Moral Stories data, construct VR conditions with salience mapping, and validate psychometric distribution. **FR-006 (Real VR Logs) is satisfied by the implementation of T050 (Interface), T041 (parse_real_logs.py), and T016/T018 in this phase.** T013-T018 are explicitly labeled as 'Simulation-Only' for local unit testing, while the *capability* to capture real logs is implemented in Phase 6.

**Staged Implementation Authorization**: Per Plan.md Section "Pipeline Validation", FR-006 ("capture and process actual VR interaction logs") and the scientific hypothesis validation (US-4) are explicitly deferred until **Phase 4: Data Acquisition**. The tasks in this phase (T013-T018) are authorized to use **Simulation-Only** data with a known `ground_truth_effect` to validate the pipeline architecture and statistical engine.

**Default Execution Mode**: `simulation`. The system defaults to using simulation data. To switch to `DATA_MODE='real'` requires manual config override in `code/config.py`.

**Independent Test**: The pipeline can be tested by running the ingestion and construction scripts against the synthetic data (via `--mode=simulation`) and verifying that the output CSV contains correctly merged rows, valid salience labels, and matches Gervais et al. norms. **Schema Requirement**: The output CSV MUST contain `gaze_metrics` (as a JSON string or structured column), `response_time`, `salience_level`, etc., matching spec.md US-1 Acceptance Scenario 1.

**⚠️ BLOCKING DEPENDENCY**: Phase 2 (T045, T046, T050, T055) must complete successfully before any Phase 3 task can execute.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [ ] T010 [P] [US1] Unit test for synthetic MFQ generator in `code/tests/test_ingest_mfq.py`. **Deliverable**: Function `test_mfq_distribution_matches_norms` that asserts `assert abs(mean - expected_mean) < 0.05` using values explicitly loaded from `data/config/gervais_norms.yaml`.
- [X] T011 [P] [US1] Unit test for salience mapping logic in `code/tests/test_schema.py`. **Deliverable**: Function `test_salience_mapping_valid` that asserts `assert salience_level in ['low', 'high']` given mock story IDs.
- [ ] T012 [US1] Unit test for psychometric norm validation in `code/tests/test_ingest_stories.py`. **Deliverable**: Function `test_psychometric_validity` using Kolmogorov-Smirnov test with p > 0.05 threshold against Gervais et al. norms.

### Implementation for User Story 1 (Real Data First, Simulation for Testing)

- [ ] T013 [US1] [Simulation] Implement `code/data/simulation_mfq.py` to generate synthetic MFQ data based on Gervais et al. multivariate normal distributions. **Validation**: The `ground_truth_effect` parameter must be validated against the MDES calculated in T045. **Pre-requisite Check**: **MUST** verify `state/mdes_report.yaml` exists and contains key `mdes_value` before execution. If missing, raise `FileNotFoundError: MDES report missing. Ensure T045 is complete.` **Dependency**: **Phase 2 (T045, T046) must complete first.**
- [ ] T014 [US1] [Simulation] Implement `code/data/simulation_stories.py` to generate synthetic Moral Stories and VR interaction logs with a known `ground_truth_effect`.
- [ ] T015 [US1] [Real] Implement `code/data/ingest.py` to load and merge real MFQ and Moral Stories datasets, handling ID mismatches and missing data. **Routing**: If `DATA_MODE='real'`, explicitly call `code/data/fetch_real.py` and `code/data/parse_real_logs.py`; otherwise, use simulation. **Constraint**: Must include a hard assertion that `DATA_MODE` is defined in `code/config.py`. **Dependency**: T054b, T041 (Real Interface tasks). **Note**: This task is distinct from T013/T014 and does not depend on them.
- [ ] T016 [US1] Implement `code/data/preprocess.py` to map text stories to VR scenes, assigning `salience_level` (low/high) via blend-shape parameters. **Dependency**: Read configuration from `data/config/unity_blend_shapes.yaml`. **Schema Check**: The config file must contain keys `low` and `high`, each with a nested `blend_shape_params` object. If missing, raise `ValueError`.
- [ ] T016b [US1] Implement `code/data/vr_mapping_logic.py` to implement the text-to-VR mapping logic using `data/config/unity_blend_shapes.yaml`. **Dependency**: T044.
- [ ] T017 [US1] Add validation logic to existing `code/utils/norms.py` to compare synthetic MFQ distribution against published norms (must be within 1 SD).
- [ ] T018 [US1] Implement `code/utils/hashing.py` integration to checksum **simulation-derived** CSVs and update `state/artifact_hashes.yaml`.
- [ ] T053 [US1] This task's responsibilities have been merged into T056.
- [ ] T038 [US1] Implement `code/unity_verification.py` to verify the simulation's fidelity to the actual Unity environment by validating blend-shape parameters against a reference configuration file.
- [ ] T056 [US1] Implement `code/data/simulation.py` as the orchestration entry point for the simulation pipeline. **Dependency**: T013, T014, T016.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Bayesian Model Execution and Comparison (Priority: P2)

**Goal**: Execute the Bayesian model on the preprocessed data (simulation or real) and compare against baseline.

- [ ] T022 [US2] Implement `code/models/bayesian.py` to define the PyMC3 model with Gaussian likelihood and Normal priors. **Dependency**: T051 (Schema).
- [ ] T023 [US2] Implement `code/models/bayesian.py` execution logic to fit the model. **Dependency**: T022, T015/T014 (Data).
- [ ] T024 [US2] Implement `code/analysis/model_comparison.py` to calculate AIC/WAIC. **Dependency**: T022, T023.
- [ ] T025 [US2] Implement `code/analysis/model_comparison.py` to perform Posterior Predictive Checks (PPC). **Dependency**: T022, T023.
- [ ] T027a [US2] Implement `code/analysis/model_comparison.py` to calculate ΔAIC. **Dependency**: T024.
- [ ] T027b [US2] Implement `code/analysis/model_comparison.py` to report ΔAIC > 10 (or Parameter Recovery in simulation). **Dependency**: T027a.
- [ ] T027b-test [US2] Unit test for ΔAIC threshold logic. **Dependency**: T027b.

---

## Phase 5: User Story 3 - Statistical Validation and Reporting (Priority: P3)

**Goal**: Perform mixed-effects regression, Bonferroni correction, and sensitivity analysis.

- [ ] T030 [US3] Implement `code/models/regression.py` for hierarchical mixed-effects regression. **Dependency**: T022, T023.
- [ ] T031 [US3] Implement `code/analysis/validation.py` for Bonferroni correction. **Dependency**: T030.
- [ ] T032 [US3] Implement `code/analysis/validation.py` for sensitivity analysis (thresholds {2, 10, 20}). **Dependency**: T030.
- [ ] T033 [US3] Implement `code/reports/generate_report.py` to generate the final report. **Dependency**: T030, T031, T032.
- [ ] T034 [US3] Implement report logic to include specific statistical metrics. **Dependency**: T033.

---

## Phase 6: Real Data Integration (Deferred until Phase 4)

**Goal**: Implement the real data pipeline when verified data sources are available.

- [ ] T054b [US4] Implement `code/data/fetch_real.py` to fetch MFQ from OSF. **Dependency**: T050.
- [ ] T041 [US4] Implement `code/data/parse_real_logs.py` to parse VR logs. **Dependency**: T054b.
- [ ] T060 [US4] Implement `code/data/streaming_loader.py` to stream large datasets. **Dependency**: T054b. **Note**: Moved from Phase 3 to Phase 6.
- [ ] T042 [US4] [Deferred] Implement `code/data/e2e_real.py` for End-to-End Real Data Pipeline. **Dependency**: T054b, T041, T016. **Note**: This task is deferred until Phase 4. It is not executable in the current Simulation-Only phase.
- [ ] T054c [US4] [Deferred] Implement `code/data/verify_vr_mapping.py` to verify VR mapping with real data. **Dependency**: T016, T041. **Note**: Deferred.
- [ ] T054d [US4] [Deferred] Implement `code/tests/test_e2e_real.py` for real data integration tests. **Dependency**: T054b, T041, T016. **Note**: Deferred.

---

## Deferred Tasks (Not Executable in Current Phase)

- [ ] T042 [US4] [Deferred] End-to-End Real Data Pipeline.
- [ ] T054c [US4] [Deferred] Verify VR mapping with real data.
- [ ] T054d [US4] [Deferred] End-to-End real data tests.

---

## Phase N: Validation and Cleanup

- [ ] T039 [P] [US1/US2/US3] Implement edge case tests for data ingestion, model convergence, and VR rendering failures. **Dependency**: T013, T022, T016.
- [ ] [ ] T040 [P] [US1/US2/US3] Implement quickstart validation script to ensure the pipeline runs end-to-end. **Dependency**: T006, T018, T056. **Note**: Cannot be marked complete until T018 and T056 are complete.