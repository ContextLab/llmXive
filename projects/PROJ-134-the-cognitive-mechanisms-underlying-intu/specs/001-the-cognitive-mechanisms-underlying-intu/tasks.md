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

- **Single project**: `code/`, `data/`, `tests/`, `state/` at repository root
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
- [X] T002 [P] Initialize Python 3.11 project with `requirements.txt` (pymc>=5.0.0, pandas, numpy, scikit-learn, pyyaml, requests, seaborn, statsmodels). **Deviation Note**: This task implements PyMC5 as a **Deviation from FR-002 (PyMC3)** per Plan.md "Spec Deviation & Resolution". The task must document this deviation in the `requirements.txt` header comment.
- [X] T002a [P] Update `spec.md` FR-002 to explicitly state "PyMC5 (successor to PyMC3)" to formally resolve the specification contradiction. **Deliverable**: Updated FR-002 in `spec.md`.
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. Includes Real Data Architecture Definition (T050), Configuration (T044, T045, T046), and Model Schema (T051) to ensure Producer before Consumer.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.
**⚠️ BLOCKING DEPENDENCY**: T045, T046, T051, T053, T050, T055, T043, T044 MUST be completed before T013, T014, T015, T022, T023, T041.
**⚠️ SEQUENTIAL ENFORCEMENT**: T005 -> T006; T045 -> T046; T055 depends on T050 and T008b completion.

### Removed Tasks
- [X] T053 [P] [US1/US4] **REMOVED**. This task was merged into T056 to resolve the run-book vs implementation mismatch. The `code/data/simulation.py` entry point is now defined and implemented in T056.

- [X] T045 [US3] [Dep: T005] **Merged Task**: Implement MDES Pipeline in `code/analysis/power_analysis.py`. **Deliverable**: A single script that: (1) Sets up CLI and config for N/SD, (2) Calculates MDES, (3) Writes `state/mdes_report.yaml`. **Constraint**: For Phase 3 (Simulation), `N` MUST be read from `code/config.py` (static value) to avoid circular dependency on data loading. **Dependency**: T005.
- [X] T046 [US3] [Dep: T045] Implement `code/analysis/validation.py` to validate that the simulated dataset size (N) matches the MDES assumption. **Deliverable**: A validation script that reads `state/mdes_report.yaml` and `code/config.py` (for `N_CONFIG`). It asserts `N_simulated == N_CONFIG`. If mismatch, raise `ValueError`. **Dependency**: T045. **Note**: Ensures statistical power constraint is not silently violated. Supports both simulation and real data paths by reading N from config.
- [X] T005 [P] Create `code/config.py` defining paths, random seeds, and constants
- [X] T006 [Dep: T005] Implement `code/utils/hashing.py` to calculate SHA-256 checksums and update `state/artifact_hashes.yaml` (Constitution Principle V). **Deliverable**: A function `calculate_checksum(file_path: str) -> str` that returns the SHA-256 hex digest and a function `update_state_file(file_path: str, checksum: str)` that updates `state/artifact_hashes.yaml`. **Verification**: Run `python -c "from code.utils.hashing import calculate_checksum, update_state_file; update_state_file('data/processed/test.csv', calculate_checksum('data/processed/test.csv'))"` and confirm the hash is recorded in `state/artifact_hashes.yaml`. **Constraint**: This task is NOT marked [P] and must complete before any artifact generation tasks. **Status**: Pending verification of functionality.
- [X] T007b [P] Create `data/config/gervais_norms.yaml` containing the specific psychometric values (mean, std) for MFQ dimensions as per Gervais et al. **Deliverable**: A YAML file with keys for each foundation (Care, Fairness, etc.) and values for mean and std. **Verification**: Run `python -c "import yaml; print(yaml.safe_load(open('data/config/gervais_norms.yaml')))"` and confirm keys exist.
- [X] T007 [P] Implement `code/utils/norms.py` to load and reference Gervais et al. psychometric norms. **Deliverable**: A function `load_norms() -> dict` that returns the norms.
- [X] T008b [P] Implement `code/utils/schema.py` using Pydantic to create schema classes for MFQ, Stories, and VR Logs (validates data schemas). **Deliverable**: A valid Pydantic model class for each entity.
- [X] T009 [P] [US1] Implement `code/utils/logging.py` for base logging infrastructure. **Deliverable**: A configured logger in `code/utils/logging.py` that captures exclusion reasons and VR mapping logs to `data/logs/`. **Config**: Use `RotatingFileHandler` for `data/logs/ingest.log` and `data/logs/vr_mapping.log` with `JSONFormatter`. **Verification**: Run `python -c "from code.utils.logging import get_logger; logger = get_logger('test'); logger.info('test')"` and confirm `data/logs/ingest.log` contains the JSON log entry. **Status**: Pending verification of log file creation. **Retry Logic**: If verification fails, the task must be re-attempted with a retry mechanism to ensure log files are created before marking complete.
- [X] T050 [P] [US4-Interface] Define Real Data Architecture Interfaces in `code/data/ingest_real.py`. **Deliverable**: A module defining explicit constants and schemas: `OSF_API_URL` (base URL: ""), `HF_DATASET_ID` ("moral-stories-v1"), and `VR_LOG_SCHEMA_COLUMNS` (list: `["response_time", "gaze_metrics", "judgment_rating"]`). **Verification**: The module must include a `verify_constants()` function that asserts these values match the canonical sources defined in `spec.md`. **Note**: This task defines the *interface* for Phase 6; the *implementation* (fetch logic) is deferred to Phase 6.
- [X] T051 [P] [US2] Define `ModelResult` Artifact Schema in `code/utils/schemas.py`. **Deliverable**: A JSON/Parquet schema definition file (or Pydantic model) explicitly including fields: `participant_id`, `posterior_samples`, `r_hat`, `is_inconclusive` (boolean), and `mle_fallback` (float). This schema must be defined *before* T022/T023 implementation.
- [X] T044 [P] [US1] Create `data/config/unity_blend_shapes.yaml` defining the exact mapping of text story IDs to VR scene blend-shape parameters (low/high) used in the experimental design. **Deliverable**: A YAML file that serves as the single source of truth for the "perceptual salience" variable, replacing the assumption of a runtime Unity environment. **Schema**: Must contain keys `low` and `high` with nested objects for `blend_shape_params`. **Verification**: The file must be loadable and contain the expected structure.
- [X] T043 [P] [US1/US4] Update `code/config.py` to add a `DATA_MODE` flag (`'simulation'` | `'real'`). **Default**: `'simulation'`. Ensure `code/data/ingest.py` routes to `code/data/fetch_real.py` (Phase 6) and `code/data/parse_real_logs.py` (Phase 6) when `DATA_MODE='real'` and to `simulation.py` when `DATA_MODE='simulation'`, with a hard assertion that `DATA_MODE` cannot be 'real' without a verified source. **Deliverable**: Config-driven routing that enforces the "Real Data Only" constraint. **Dependency**: T005 must complete first.
- [ ] T055 [US1/US4] [Dep: T050, T008b] Implement `code/utils/schema_equivalence.py` to verify that the simulation data schema (generated by T014) is structurally identical to the Real Data Interface schema (defined in T050). **Deliverable**: A script that compares the Pydantic models from T008b (Simulation) and T050 (Real) and raises an error if any field mismatch is found. **Dependency**: T050 and T008b must complete first. **Note**: Removed [P] tag to enforce strict sequential ordering after dependencies.

---

## Phase 3: User Story 1 - Data Ingestion, Experimental Construction, and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest real MFQ and Moral Stories data, construct VR conditions with salience mapping, and validate psychometric distribution. **⚠️ FORMAL DEVIATION**: FR-006 (Real VR Logs) is **NOT satisfied** in this phase. The system uses a **Simulation Layer** to generate synthetic VR interaction logs. Real data ingestion is deferred to Phase 6.

**Staged Implementation Authorization**: Per Plan.md Section "Pipeline Validation", FR-006 ("capture and process actual VR interaction logs") and the scientific hypothesis validation (US-4) are explicitly deferred until **Phase 4: Data Acquisition**. The tasks in this phase (T013-T018) are authorized to use **Simulation-Only** data with a known `ground_truth_effect` to validate the pipeline architecture and statistical engine.

**Default Execution Mode**: `simulation`. The system defaults to using simulation data. To switch to `DATA_MODE='real'` requires manual config override in `code/config.py` and completion of Phase 6 tasks.

**Independent Test**: The pipeline can be tested by running the ingestion and construction scripts against the synthetic data (via `--mode=simulation`) and verifying that the output CSV contains correctly merged rows, valid salience labels, and matches Gervais et al. norms. **Schema Requirement**: The output CSV MUST contain `gaze_metrics` (as a JSON string or structured column), `response_time`, `salience_level`, etc., matching spec.md US-1 Acceptance Scenario 1.

**⚠️ BLOCKING DEPENDENCY**: Phase 2 (T045, T046, T006) must complete successfully before any Phase 3 task can execute.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T010 [P] [US1] Unit test for **Simulation** MFQ generator in `code/tests/test_ingest_mfq.py`. **Deliverable**: Function `test_mfq_distribution_matches_norms` that asserts `assert abs(mean - expected_mean) < 0.05` using values explicitly loaded from `data/config/gervais_norms.yaml`. **Note**: This test validates the **simulation fallback** path, not the primary real-data ingestion path defined in FR-001.
- [X] T011 [P] [US1] Unit test for salience mapping logic in `code/tests/test_schema.py`. **Deliverable**: Function `test_salience_mapping_valid` that asserts `assert salience_level in ['low', 'high']` given mock story IDs.
- [X] T012 [US1] Unit test for psychometric norm validation in `code/tests/test_ingest_stories.py`. **Deliverable**: Function `test_psychometric_validity` using Kolmogorov-Smirnov test with p > 0.05 threshold against Gervais et al. norms.

### Implementation for User Story 1 (Real Data First, Simulation for Testing)

- [ ] T019 [P] [US1] [Simulation] Implement `code/data/validate_simulation_params.py` to validate simulation parameters against literature cited in `research.md`. **Deliverable**: A script that reads `research.md` for cited effect sizes and asserts that the `ground_truth_effect` injected in T013/T014 is within a reasonable range of these citations. **Constraint**: Must raise `ValueError` if parameters are arbitrary or unsupported by literature. **Dependency**: T005, T045.
- [ ] T054b-Sim [US1] [Simulation] Implement `code/data/fetch_simulation.py` to generate synthetic MFQ and Moral Stories data with known `ground_truth_effect`. **Deliverable**: A script that generates `data/processed/synthetic_mfq.csv` and `data/processed/synthetic_stories.csv` with deterministic seeds. **Constraint**: Must inject `ground_truth_effect` into the data generation process for later parameter recovery validation. **Dependency**: T019.
- [ ] T013 [US1] [Simulation] Implement `code/data/simulation_mfq.py` to generate synthetic MFQ data based on Gervais et al. multivariate normal distributions. **Validation**: The `ground_truth_effect` parameter must be validated against the MDES calculated in T045. **Pre-requisite Check**: **MUST** verify `state/mdes_report.yaml` exists and contains key `mdes_value` before execution. If missing, raise `FileNotFoundError: MDES report missing. Ensure T045 is complete.` **Deliverable**: Generate `data/processed/synthetic_mfq.csv`. **Verification**: Verify file exists, is not empty, and contains columns: `participant_id`, `care`, `fairness`, `loyalty`, `authority`, `purity`, `total_score`. **Dependency**: **T054b-Sim**, **T045**, **T006**. **Status**: Pending Implementation. **Note**: `ground_truth_effect` source is defined in `code/config.py`.
- [ ] T014 [US1] [Simulation] Implement `code/data/simulation_stories.py` to generate synthetic Moral Stories and VR interaction logs with a known `ground_truth_effect`. **Deliverable**: Generate `data/processed/synthetic_logs.csv` with `response_time`, `gaze_metrics`, and `salience_level` columns. **Constraint**: Must inject known effect sizes for parameter recovery analysis in T027c. **Distribution**: `response_time` ~ LogNormal(3.5, 0.5), `gaze_metrics` ~ Normal(0.5, 0.1). **Verification**: Verify file exists and contains columns: `participant_id`, `story_id`, `salience_level`, `response_time`, `gaze_metrics`, `judgment_rating`. **Dependency**: **T054b-Sim**, **T006**. **Status**: Pending Implementation.
- [ ] T015-Sim [US1] [Simulation] Implement `code/data/ingest.py` to load and merge **synthetic** MFQ and Moral Stories datasets. **Routing**: If `DATA_MODE='simulation'`, call `code/data/fetch_simulation.py` and `code/data/simulation_stories.py`; otherwise, use real data. **Constraint**: Must include a hard assertion that `DATA_MODE` is defined in `code/config.py`. **Dependency**: **T013**, **T014**. **Gating**: If `DATA_MODE='real'` and real data is not available, this task MUST raise a `ConnectionError` and **NEVER** fall back to synthetic data.
- [ ] T016-Sim [US1] [Simulation] Implement `code/data/preprocess.py` to map text stories to VR scenes, assigning `salience_level` (low/high) via blend-shape parameters. **Dependency**: Read configuration from `data/config/unity_blend_shapes.yaml` (T044). **Schema Check**: The config file must contain keys `low` and `high`, each with a nested `blend_shape_params` object. If missing, raise `ValueError`. **Dependency**: T044.
- [ ] T017 [US1] Add validation logic to existing `code/utils/norms.py` to compare synthetic MFQ distribution against published norms (must be within 1 SD).
- [ ] T018 [US1] [Simulation] Implement `code/utils/hashing.py` integration to checksum **simulation-derived** CSVs and update `state/artifact_hashes.yaml`. **Dependency**: T006, T013, T014. **Verification**: Must verify `state/artifact_hashes.yaml` is updated correctly before marking complete. **Status**: Pending Implementation.
- [ ] T038 [US1] [Simulation] Implement `code/unity_verification.py` to verify the simulation's fidelity to the actual Unity environment by validating blend-shape parameters against a reference configuration file (`data/config/unity_blend_shapes.yaml`). **Validation Logic**: Check that simulated blend-shape values match reference values within a tolerance of 0.05. **Dependency**: T044. **Status**: Pending Implementation.
- [ ] T056 [US1] Implement `code/data/simulation.py` as the orchestration entry point for the simulation pipeline. **Dependency**: T013, T014, T016-Sim.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (Simulation Mode Only)

---

## Phase 4: User Story 2 - Bayesian Model Execution and Comparison (Priority: P2)

**Goal**: Execute the Bayesian model on the preprocessed data (simulation or real) and compare against baseline.

**Interface Contract**:
- **T022** outputs a `model` object adhering to the `ModelResult` schema (T051).
- **T023** takes the `model` object from T022 as input and outputs comparison metrics.

- [X] T022a [US2] [Dep: T051] Define Pydantic schema for `ModelResult` in `code/utils/schemas.py`. **Deliverable**: Pydantic model class. **Dependency**: T051.
- [X] T022b [US2] [Dep: T022a] Implement PyMC5 model definition in `code/models/bayesian_model.py`. **Deviation Note**: This task implements PyMC5 as a **Deviation from FR-002 (PyMC3)** per Plan.md. **Deliverable**: A function `build_model(data)` returning a PyMC model. **Dependency**: T022a.
- [X] T022c [US2] [Dep: T022b] Implement wrapper to ensure schema compliance in `code/models/bayesian_model.py`. **Deliverable**: A function `run_model(data)` that returns a `ModelResult` object. **Dependency**: T022b.
- [ ] T022d [US2] [Dep: T022c] Implement **PyMC5 Convergence Check** in `code/tests/test_migration.py`. **Deliverable**: A script that verifies R-hat < 1.05 and effective sample size > 200 for all parameters. **Constraint**: Does NOT compare against PyMC3. **Dependency**: T022c. **Status**: Pending Implementation.
- [ ] T023a [US2] [Dep: T022c] Implement MCMC sampling execution in `code/models/run_bayesian.py`. **Deliverable**: A function `sample_model(model)` that returns samples. **Dependency**: T022c.
- [ ] T023b [US2] [Dep: T023a] Implement AIC/WAIC calculation in `code/models/run_bayesian.py`. **Deliverable**: A function `calculate_metrics(samples)` that returns AIC/WAIC values. **Dependency**: T023a.
- [ ] T023c [US2] [Dep: T023b] Implement result serialization in `code/models/run_bayesian.py`. **Deliverable**: A function `serialize_results(model, metrics)` that returns `ModelResult` objects. **Dependency**: T023b.
- [ ] T024 [US2] Implement `code/analysis/model_comparison.py` to calculate AIC/WAIC and compare against a **Frequentist Linear Mixed Model (LMM)** baseline using `statsmodels`. **Dependency**: T023c. **Status**: Pending Implementation.
- [ ] T025 [US2] Implement `code/analysis/model_comparison.py` to perform Posterior Predictive Checks (PPC). **Dependency**: T023c. **Status**: Pending Implementation.
- [ ] T027a [US2] [Dep: T024] Implement `code/analysis/model_comparison.py` to calculate ΔAIC. **Dependency**: T024.
- [ ] T027b [US2] [Dep: T027a] Implement `code/analysis/model_comparison.py` to report ΔAIC > 10 (Real Data Path). **Dependency**: T027a.
- [ ] T027b-Sim [US2] [Simulation] Implement `code/analysis/model_comparison.py` to report ΔAIC > 10 (Simulation Path). **Deliverable**: A script that calculates and reports ΔAIC for the synthetic data run to validate the primary success criterion. **Dependency**: T027a.
- [ ] T027c [US2] [Simulation] Implement `code/analysis/parameter_recovery.py` to calculate **Parameter Recovery** metrics. **Deliverable**: A script that compares estimated posterior means against the `ground_truth_effect` injected in T013/T014. **Metrics**: Calculate bias (mean - truth) and coverage (proportion of truth within 95% CI). **Output**: `data/results/parameter_recovery.json`. **Format**: JSON with keys: `bias`, `coverage_95ci`, `n_samples`. **Dependency**: T023c, T014.
- [ ] T027d [US2] [Simulation] **Distinct Task**: Implement `code/analysis/synthetic_delta_aic_validation.py` to explicitly calculate and report the ΔAIC threshold check for the **synthetic** data run. **Deliverable**: A script that calculates ΔAIC on synthetic data and asserts `ΔAIC > 10` as the primary success criterion. **Verification**: Log pass/fail status and write result to `data/results/synthetic_delta_aic.json`. **Dependency**: T027a.
- [ ] T027b-test [US2] Unit test for ΔAIC threshold logic. **Dependency**: T027b.

---

## Phase 5: User Story 3 - Statistical Validation and Reporting (Priority: P3)

**Goal**: Perform mixed-effects regression, Bonferroni correction, and sensitivity analysis.

- [ ] T030 [US3] Implement `code/models/regression.py` for hierarchical mixed-effects regression. **Dependency**: T023c.
- [ ] T031 [US3] Implement `code/analysis/validation.py` for Bonferroni correction. **Dependency**: T030.
- [ ] T032 [US3] Implement `code/analysis/validation.py` for sensitivity analysis (thresholds {2, 10, 20}). **Deliverable**: A script that sweeps thresholds {2, 10, 20} and reports stability. **Verification**: Verify that the output JSON contains three distinct entries for thresholds 2, 10, and 20 with stability metrics. **Output**: `data/results/sensitivity_analysis.json`. **Dependency**: T030.
- [ ] T032a [US3] [Dep: T032] Write sensitivity analysis report to `data/results/sensitivity_analysis.json`. **Deliverable**: JSON file with stability metrics. **Dependency**: T032.
- [ ] T033 [US3] Implement `code/reports/generate_report.py` to generate the final report. **Deliverable**: A script that generates `reports/final_report.md`. **Content Structure**: Must include sections: Executive Summary, Model Comparison (ΔAIC), Parameter Recovery, Sensitivity Analysis, and Conclusion. **Dependency**: T030, T031, T032a.

---

## Phase 6: Real Data Integration (Deferred until Phase 4)

**Goal**: Implement the real data pipeline when verified data sources are available.

- [ ] T054b [US4] Implement `code/data/fetch_real.py` to fetch MFQ from OSF. **Constraint**: If `DATA_MODE='real'` and the OSF fetch fails, the script MUST raise a `ConnectionError` and **NEVER** fall back to synthetic data. **Dependency**: T050.
- [ ] T041 [US4] Implement `code/data/parse_real_logs.py` to parse VR logs. **Constraint**: If `DATA_MODE='real'` and the VR log fetch fails, the script MUST raise a `FileNotFoundError` and **NEVER** fall back to synthetic data. **Dependency**: T054b.
- [ ] T060 [US4] Implement `code/data/streaming_loader.py` to stream large datasets. **Dependency**: T054b. **Note**: Moved from Phase 3 to Phase 6.
- [ ] T016-Real [US4] [Real Data] Implement `code/data/preprocess_real.py` to map text stories to VR scenes using real VR logs. **Deliverable**: A script that maps text to salience levels using real blend-shape parameters. **Dependency**: T054b, T041.
- [ ] T054c [US4] [Deferred] Implement `code/data/verify_vr_mapping.py` to verify VR mapping with real data. **Dependency**: T016-Real, T041. **Note**: Deferred.
- [ ] T054d [US4] [Deferred] Implement `code/tests/test_e2e_real.py` for real data integration tests. **Dependency**: T054b, T041, T016-Real. **Note**: Deferred.
- [ ] T015-REAL [US4] [Deferred] Implement `code/data/ingest_real.py` to load and merge **real** MFQ and Moral Stories datasets. **Constraint**: If `DATA_MODE='real'` and real data is not available, this task MUST raise a `ConnectionError` and **NEVER** fall back to synthetic data. **Dependency**: T054b, T041. **Status**: Deferred until Phase 6.

---

## Deferred Tasks (Not Executable in Current Phase)

- [ ] T042 [US4] [Deferred] End-to-End Real Data Pipeline.
- [ ] T054c [US4] [Deferred] Verify VR mapping with real data.
- [ ] T054d [US4] [Deferred] End-to-End real data tests.
- [ ] T016b [US1] [REMOVED] Merged into T016-Sim/T016-Real.
- [ ] T015-REAL [US1] [BLOCKED] Real Data Ingestion. **Status**: Blocked until Phase 6.

---

## Rejected / Failed Tasks (Requires Re-queuing)

- [ ] T024 [US2] [FAILED] Implement `code/analysis/model_comparison.py` to calculate AIC/WAIC and compare against a **Frequentist Linear Mixed Model (LMM)** baseline using `statsmodels`. **Reason**: Baseline model definition was ambiguous. **Action**: Re-queue with explicit baseline definition.
- [ ] T025 [US2] [FAILED] Implement `code/analysis/model_comparison.py` to perform Posterior Predictive Checks (PPC). **Reason**: Implementation details were unspecified. **Action**: Re-queue with explicit PPC logic.

---

## Phase N: Validation and Cleanup

- [X] T039 [P] [US1/US2/US3] Implement edge case tests for data ingestion, model convergence, and VR rendering failures. **Dependency**: T013, T023c, T016-Sim.
- [X] T040 [P] [US1/US2/US3] Implement quickstart validation script to ensure the pipeline runs end-to-end. **Dependency**: T006, T018, T056. **Note**: Cannot be marked complete until T018 and T056 are complete.

---

## Revision Tasks (Addressing Review Concerns)

- [X] T061 [US4] [Review: Data Source] Implement `code/data/fetch_real.py` with **strict failure-on-missing** logic. **Constraint**: If `DATA_MODE='real'` and the OSF or HuggingFace fetch fails, the script MUST raise a `ConnectionError` or `FileNotFoundError` and **NEVER** fall back to synthetic data. If `DATA_MODE='simulation'`, skip real fetch validation. This resolves the "silent synthetic fallback" fabrication risk. **Dependency**: T050.
- [X] T062 [US4] [Review: Streaming] Implement `code/data/streaming_loader.py` using `datasets.load_dataset(..., streaming=True)` to process the full real dataset in chunks, ensuring memory safety without shrinking to a toy dataset. **Constraint**: The script must accumulate statistics online (e.g., running mean/variance) and must explicitly log the sample size and streaming strategy used. **Dependency**: T054b.
- [X] T063 [US2] [Review: GPU Fallback] Update `code/models/bayesian.py` to detect CUDA availability. **Logic**: If `torch.cuda.is_available()` is True, set `device="cuda"`; otherwise, run on CPU. **Constraint**: If the task requires GPU (e.g., large model) and CPU fails convergence, the execution stage must re-run on Kaggle GPU; do NOT task a degenerate CPU imitation of a GPU method. **Dependency**: T022c.
- [X] T065 [US3] [Review: Sensitivity] Ensure `code/analysis/validation.py` (T032) explicitly sweeps a range of thresholds including low values and writes the stability report to `data/results/sensitivity_analysis.json` as required by FR-005. **Dependency**: T030.