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
- [X] T002 [P] Initialize Python 3.11 project with `requirements.txt` (pymc>=5.0.0, pandas, numpy, scikit-learn, pyyaml, requests, seaborn, statsmodels). **Deviation Note**: This task implements PyMC5 as a **Deviation from FR-002 (PyMC3)** per Plan.md "Spec Deviation & Resolution". The task must document this deviation in the `requirements.txt` header comment. **Verification**: Update `spec.md` FR-002 to explicitly state "PyMC5 (successor to PyMC3)" as part of this task's deliverable.
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. Includes Real Data Architecture Definition (T050), Configuration (T044, T045, T046), and Model Schema (T051) to ensure Producer before Consumer.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.
**⚠️ BLOCKING DEPENDENCY**: T045, T046, T051, T053, T050, T055, T043, T044 MUST be completed before T013, T014, T015, T022, T023, T041.
**⚠️ SEQUENTIAL ENFORCEMENT**: T005 -> T006; T045 -> T046; T055 depends on T050 and T008b completion.

### Removed Tasks
- [X] T053 [P] [US1/US4] **REMOVED**. This task was merged into T056 to resolve the run-book vs implementation mismatch. The `code/data/simulation.py` entry point is now defined and implemented in T056.

- [X] T045 [US3] [Dep: T005] **Merged Task**: Implement MDES Pipeline in `code/analysis/power_analysis.py`. **Deliverable**: A single script that: (1) Sets up CLI and config for N/SD, (2) Calculates MDES using `statsmodels.stats.power.tt_solve_power` with `alpha=0.05`, `power=0.8`, (3) Writes `state/mdes_report.yaml` with keys `n_required`, `effect_size`, `power`. **Constraint**: For Phase 3 (Simulation), `N` MUST be read from `code/config.py` (static value) to avoid circular dependency on data loading. **Dependency**: T005. **Status**: **Active** - Must complete before T013, T014.
- [X] T046 [US3] [Dep: T045] Implement `code/analysis/validation.py` to validate that the simulated dataset size (N) matches the MDES assumption. **Deliverable**: A validation script that reads `state/mdes_report.yaml` and `code/config.py` (for `N_CONFIG`). It asserts `N_simulated == N_CONFIG`. If mismatch, raise `ValueError`. **Dependency**: T045. **Note**: Ensures statistical power constraint is not silently violated. Supports both simulation and real data paths by reading N from config.
- [X] T005 [P] Create `code/config.py` defining paths, random seeds, and constants
- [X] T006 [Dep: T005] Implement `code/utils/hashing.py` to calculate SHA-256 checksums and update `state/artifact_hashes.yaml` (Constitution Principle V). **Deliverable**: A function `calculate_checksum(file_path: str) -> str` that returns the SHA-256 hex digest and a function `update_state_file(file_path: str, checksum: str)` that updates `state/artifact_hashes.yaml`. **Verification**: Run `python -c "from code.utils.hashing import calculate_checksum, update_state_file; update_state_file('data/processed/test.csv', calculate_checksum('data/processed/test.csv'))"` and confirm the hash is recorded in `state/artifact_hashes.yaml`. **Constraint**: This task is NOT marked [P] and must complete before any artifact generation tasks. **Status**: **Active** - Must complete before T013/T014.
- [X] T007b [P] Create `data/config/gervais_norms.yaml` containing the specific psychometric values (mean, std) for MFQ dimensions as per Gervais et al. **Deliverable**: A YAML file with keys for each foundation (Care, Fairness, etc.) and values for mean and std. **Verification**: Run `python -c "import yaml; print(yaml.safe_load(open('data/config/gervais_norms.yaml')))"` and confirm keys exist.
- [X] T007 [P] Implement `code/utils/norms.py` to load and reference Gervais et al. psychometric norms. **Deliverable**: A function `load_norms() -> dict` that returns the norms.
- [X] T008b [P] Implement `code/utils/schema.py` using Pydantic to create schema classes for MFQ, Stories, and VR Logs (validates data schemas). **Deliverable**: A valid Pydantic model class for each entity.
- [X] T009 [P] [US1] Implement `code/utils/logging.py` for base logging infrastructure. **Deliverable**: A configured logger in `code/utils/logging.py` that captures exclusion reasons and VR mapping logs to `data/logs/`. **Config**: Use `RotatingFileHandler` for `data/logs/ingest.log` and `data/logs/vr_mapping.log` with `JSONFormatter`. **Verification**: Run `python -c "from code.utils.logging import get_logger; logger = get_logger('test'); logger.info('test')"` and confirm `data/logs/ingest.log` contains the JSON log entry. **Implementation Detail**: Implement a retry decorator with `max_attempts=3` and `backoff_factor=1` for file I/O operations. **Status**: Pending verification of log file creation. **Retry Logic**: If verification fails, the task must be re-attempted with a retry mechanism to ensure log files are created before marking complete.
- [X] T050 [P] [US4-Interface] Define Real Data Architecture Interfaces in `code/data/ingest_real.py`. **Deliverable**: A module defining explicit constants and schemas: `OSF_API_URL` (base URL: ""), `HF_DATASET_ID` ("moral-stories-v1"), and `VR_LOG_SCHEMA_COLUMNS` (list: `["response_time", "gaze_metrics", "judgment_rating"]`). **Verification**: The module must include a `verify_constants()` function that asserts these values match the canonical sources defined in `spec.md`. **Note**: This task defines the *interface* for Phase 6; the *implementation* (fetch logic) is deferred to Phase 6.
- [X] T051 [P] [US2] Define `ModelResult` Artifact Schema in `code/utils/schemas.py`. **Deliverable**: A JSON/Parquet schema definition file (or Pydantic model) explicitly including fields: `participant_id`, `posterior_samples`, `r_hat`, `is_inconclusive` (boolean), and `mle_fallback` (float). This schema must be defined *before* T022/T023 implementation.
- [X] T044 [P] [US1] Create `data/config/unity_blend_shapes.yaml` defining the exact mapping of text story IDs to VR scene blend-shape parameters (low/high) used in the experimental design. **Deliverable**: A YAML file that serves as the single source of truth for the "perceptual salience" variable, replacing the assumption of a runtime Unity environment. **Schema**: Must contain keys `low` and `high` with nested objects for `blend_shape_params`. **Verification**: The file must be loadable and contain the expected structure.
- [X] T043 [P] [US1/US4] Update `code/config.py` to add a `DATA_MODE` flag (`'real'` | `'simulation'`). **Default**: `'real'`. **Constraint**: If `DATA_MODE='real'` and real data is unavailable, the system MUST raise a `ConnectionError` and NEVER fall back to simulation. To run simulation, the user MUST explicitly set `DATA_MODE='simulation'` in the CLI or config. **Deliverable**: Config-driven routing that enforces the "Real Data Only" constraint. **Dependency**: T005 must complete first.
- [X] T043-Verify [US4] [Verification] Implement unit test for T043 'fail loudly' behavior in `code/tests/test_config.py`. **Deliverable**: A test case `test_real_mode_missing_data_raises_error` that mocks a missing data source and asserts `ConnectionError` is raised when `DATA_MODE='real'`. **Dependency**: T043. **Status**: **Active**.
- [X] T019 [US3] [Dep: T005, T045] **VALIDATION**: Implement `code/analysis/validate_simulation_params.py` to validate simulation parameters against literature. **Deliverable**: A script that reads `code/config.py` for `ground_truth_effect` and asserts it is within the range [0.2, 0.8] as cited in Gervais et al. (2014). **Constraint**: Must raise `ValueError` if parameters are arbitrary or unsupported. **Dependency**: T005, T045. **Status**: **Active**.

---

## Phase 3: User Story 1 - Data Ingestion, Experimental Construction, and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest real MFQ and Moral Stories data, construct VR conditions with salience mapping, and validate psychometric distribution. **⚠️ FORMAL DEVIATION**: FR-006 (Real VR Logs) and US4 (Real Data Acquisition) are **PARTIALLY DEFERRED** for the *VR Log* component due to lack of open data. The system MUST fetch **Real MFQ** and **Real Moral Stories** (T075-Real, T041-Real) and fail loudly if missing. Synthetic VR logs (T013/T014) are **Simulation Validation Only** and must be explicitly labeled as such, not as the primary FR-006 deliverable.

**Staged Implementation Authorization**: Per Plan.md Section "Pipeline Validation", FR-006 ("capture and process actual VR interaction logs") is explicitly deferred until **Phase 6: Data Acquisition** for the VR log component. However, the ingestion of **Real MFQ** and **Real Moral Stories** (FR-001) is **MANDATORY** in this phase. The tasks T075-Real and T041-Real implement this. The tasks T013-T018 implement a **Simulation Validation Layer** to test the pipeline architecture with known ground truth, but these are **NOT** the primary FR-006 deliverable.

**Default Execution Mode**: `real`. The system defaults to using real data. To switch to `DATA_MODE='simulation'` requires explicit manual config override in `code/config.py` or CLI flag.

**Independent Test**: The pipeline can be tested by running the ingestion and construction scripts against the real data (via `--mode=real`) and verifying that the output CSV contains correctly merged rows, valid salience labels, and matches Gervais et al. norms. **Schema Requirement**: The output CSV MUST contain `gaze_metrics` (as a JSON string or structured column), `response_time`, `salience_level`, etc., matching spec.md US-1 Acceptance Scenario 1.

**⚠️ BLOCKING DEPENDENCY**: Phase 2 (T045, T046, T006) must complete successfully before any Phase 3 task can execute.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T010 [P] [US1] Unit test for **Simulation** MFQ generator in `code/tests/test_ingest_mfq.py`. **Deliverable**: Function `test_mfq_distribution_matches_norms` that asserts `assert abs(mean - expected_mean) < 0.05` using values explicitly loaded from `data/config/gervais_norms.yaml`. **Note**: This test validates the **simulation fallback** path, not the primary real-data ingestion path defined in FR-001.
- [X] T011 [P] [US1] Unit test for salience mapping logic in `code/tests/test_schema.py`. **Deliverable**: Function `test_salience_mapping_valid` that asserts `assert salience_level in ['low', 'high']` given mock story IDs.
- [X] T012 [US1] Unit test for psychometric norm validation in `code/tests/test_ingest_stories.py`. **Deliverable**: Function `test_psychometric_validity` using Kolmogorov-Smirnov test with p > 0.05 threshold against Gervais et al. norms.

### Implementation for User Story 1 (Real Data & Simulation Validation)

- [ ] T015-Gate-Mode [US1] [Gate] Implement `code/data/gate_mode.py` to enforce `DATA_MODE` and the "fail loudly" constraint. **Logic**: If `DATA_MODE='real'`, verify real data sources (T075-Real) are available. If missing, raise `ConnectionError`. If `DATA_MODE='simulation'`, log the formal deviation for FR-006 and allow simulation tasks to proceed. **Deliverable**: A script `gate_mode.py` with a function `check_mode_and_data()` that raises `ConnectionError` if real mode is active and data is missing. **Dependency**: T043, T050. **Status**: **Active** - Must run before T013/T014.

- [ ] T075-Real [US4] [Real Data] Implement `code/data/fetch_real.py` to fetch **Real MFQ** and **Real Moral Stories** from OSF/HuggingFace. **Constraint**: If `DATA_MODE='real'` and the OSF/HF fetch fails, the script MUST raise a `ConnectionError` and **NEVER** fall back to synthetic data. **Deliverable**: Generate `data/raw/mfq_real.csv` and `data/raw/stories_real.csv`. **Dependency**: T050, T043. **Status**: **Active** - Primary FR-001/FR-006 implementation.

- [ ] T041-Real [US4] [Real Data] Implement `code/data/parse_real_logs.py` to fetch **Real VR Logs** if available, or raise `FileNotFoundError` if missing. **Constraint**: If `DATA_MODE='real'` and the VR log fetch fails, the script MUST raise a `FileNotFoundError` and **NEVER** fall back to synthetic data. **Deliverable**: Generate `data/raw/vr_logs_real.csv` (if available) or raise error. **Dependency**: T075-Real. **Status**: **Active** - Primary FR-006 implementation (VR Logs).

- [ ] T013 [US1] [Simulation Validation - PRIMARY DELIVERABLE] Implement `code/data/simulation_mfq.py` to generate synthetic MFQ data based on Gervais et al. multivariate normal distributions. **Validation**: The `ground_truth_effect` parameter must be validated against the MDES calculated in T045. **Pre-requisite Check**: **MUST** verify `state/mdes_report.yaml` exists and contains keys `n_required`, `effect_size`, `power` before execution. If missing, raise `FileNotFoundError: MDES report missing. Ensure T045 is complete.` **Deliverable**: Generate `data/processed/synthetic_mfq.csv`. **Verification**: Verify file exists, is not empty, and contains columns: `participant_id`, `care`, `fairness`, `loyalty`, `authority`, `purity`, `total_score`. **Dependency**: **T045**, **T005**, **T006**, **T015-Gate-Mode**. **Status**: **Pending** - Simulation Validation Only.

- [ ] T014 [US1] [Simulation Validation - PRIMARY DELIVERABLE] Implement `code/data/simulation_stories.py` to generate synthetic Moral Stories and VR interaction logs with a known `ground_truth_effect`. **Deliverable**: Generate `data/processed/synthetic_logs.csv` with `response_time`, `gaze_metrics`, and `salience_level` columns. **Constraint**: Must inject known effect sizes for parameter recovery analysis in T027c. **Distribution**: `response_time` ~ LogNormal(3.5, 0.5), `gaze_metrics` ~ Normal(0.5, 0.1). **Verification**: Verify file exists and contains columns: `participant_id`, `story_id`, `salience_level`, `response_time`, `gaze_metrics`, `judgment_rating`. **Dependency**: **T005**, **T044**, **T006**, **T045**, **T015-Gate-Mode**. **Status**: **Pending** - Simulation Validation Only.

- [ ] T016-Sim [US1] [Simulation] Implement `code/data/preprocess.py` to map text stories to VR scenes, assigning `salience_level` (low/high) via blend-shape parameters. **Dependency**: Read configuration from `data/config/unity_blend_shapes.yaml` (T044). **Schema Check**: The config file must contain keys `low` and `high`, each with a nested `blend_shape_params` object. If missing, raise `ValueError`. **Dependency**: T044.

- [ ] T017-Logic [US1] [Simulation] Implement `code/utils/norms.py` validation function `validate_mfq_distribution()`. **Deliverable**: A function that uses Kolmogorov-Smirnov test (p > 0.05) against norms loaded from `data/config/gervais_norms.yaml`. **Dependency**: T013, **T009**. **Status**: **Pending**.

- [ ] T017-Report [US1] [Simulation] Implement `code/reports/generate_norm_report.py` to write the validation result. **Deliverable**: A script that calls T017-Logic and writes a JSON report to `data/logs/norm_validation.json` with keys `p_value` (float), `statistic` (float), `pass_fail` (boolean). **Dependency**: T017-Logic. **Status**: **Pending**.

- [ ] T018-Checksum [US1] [Simulation] Implement `code/utils/hashing.py` integration to calculate checksums for **simulation-derived** CSVs. **Files**: `data/processed/synthetic_mfq.csv`, `data/processed/synthetic_logs.csv`. **Dependency**: T006, T013, T014. **Status**: **Pending**.

- [ ] T018-Update [US1] [Simulation] Implement `code/utils/hashing.py` update logic to update `state/artifact_hashes.yaml`. **Files**: `data/processed/synthetic_mfq.csv`, `data/processed/synthetic_logs.csv`. **Schema**: Update `state/artifact_hashes.yaml` with keys `synthetic_mfq.csv` and `synthetic_logs.csv` containing their SHA-256 hashes. **Dependency**: T018-Checksum. **Status**: **Pending**.

- [ ] T018-Verify [US1] [Simulation] Verify that `state/artifact_hashes.yaml` contains checksums for `data/processed/synthetic_mfq.csv` and `data/processed/synthetic_logs.csv`. **Deliverable**: A script that asserts the existence of these keys in the YAML file. **Dependency**: T018-Update. **Status**: **Pending**.

- [ ] T076 [US1] [Simulation] Implement `code/unity_verification.py` to verify the simulation's fidelity to the actual Unity environment by validating blend-shape parameters against a reference configuration file (`data/config/unity_blend_shapes.yaml`). **Validation Logic**: Check that simulated blend-shape values match reference values within an acceptable tolerance. **Deliverable**: Write verification status to `state/unity_fidelity.json` with keys `status` (pass/fail) and `details`. **Dependency**: T044. **Constraint**: Must checksum `state/unity_fidelity.json` and update `state/artifact_hashes.yaml` as per Constitution Principle V. **Status**: **Pending**.

- [ ] T056-CLI [US1] [Simulation] Implement CLI argument parsing for `code/data/simulation.py`. **Deliverable**: A script with `argparse` for `--mode` and `--seed`. **Dependency**: T005. **Status**: **Pending**.

- [ ] T056-Orch [US1] [Simulation] Implement orchestration logic for `code/data/simulation.py`. **Flow**: Calls T013 (MFQ Gen) -> T014 (Log Gen) -> T016-Sim (Preprocess). **Output**: Writes `data/processed/merged_simulation.csv`. **Dependency**: T056-CLI, T013, T014, T016-Sim. **Note**: This task is the **End of Phase 3 Gate**. No Phase 4 tasks can begin until T056-Orch is complete. **Status**: **Pending**.

- [ ] T056-Output [US1] [Simulation] Implement output serialization for `code/data/simulation.py`. **Deliverable**: A script that writes a summary JSON to `data/results/simulation_summary.json`. **Dependency**: T056-Orch. **Status**: **Pending**.

- [ ] T069 [US1] [Real Data Mode Gate] **REMOVED**. Logic moved to T075-Real/T041-Real.
- [ ] T075 [US4] [Real Data Gate] **REMOVED**. Merged into T075-Real/T041-Real.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (Real Data Mode). Simulation Mode is available for validation only.

---

## Phase 4: User Story 2 - Bayesian Model Execution and Comparison (Priority: P2)

**Goal**: Execute the Bayesian model on the preprocessed data (simulation or real) and compare against baseline.

**Interface Contract**:
- **T022** outputs a `model` object adhering to the `ModelResult` schema (T051).
- **T023** takes the `model` object from T022 as input and outputs comparison metrics.

- [ ] T022b [US2] [Dep: T051] Implement PyMC5 model definition in `code/models/bayesian_model.py`. **Deviation Note**: This task implements PyMC5 as a **Deviation from FR-002 (PyMC3)** per Plan.md. **Deliverable**: A function `build_model(data)` returning a PyMC model. **Dependency**: T051.
- [ ] T022c [US2] [Dep: T022b] Implement wrapper to ensure schema compliance in `code/models/bayesian_model.py`. **Deliverable**: A function `run_model(data)` that returns a `ModelResult` object. **Dependency**: T022b.
- [ ] T022d [US2] [Dep: T022c] Implement **PyMC5 Convergence Check** in `code/tests/test_migration.py`. **Deliverable**: A script that verifies R-hat < 1.05 and effective sample size > 200 for all parameters. **Constraint**: Does NOT compare against PyMC3. **Dependency**: T022c. **Status**: **Pending**.
- [ ] T023a [US2] [Dep: T022c] Implement MCMC sampling execution in `code/models/run_bayesian.py`. **Deliverable**: A function `sample_model(model)` using `pm.sample(chains=4, draws=2000, target_accept=0.9)` that returns samples. **Dependency**: T022c. **Status**: **Pending**.
- [ ] T023b [US2] [Dep: T023a] Implement AIC/WAIC calculation in `code/models/run_bayesian.py`. **Deliverable**: A function `calculate_metrics(samples)` that returns AIC/WAIC values. **Dependency**: T023a. **Status**: **Pending**.
- [ ] T023c [US2] [Dep: T023b] Implement result serialization in `code/models/run_bayesian.py`. **Deliverable**: A function `serialize_results(model, metrics)` that returns `ModelResult` objects with keys `participant_id`, `posterior_means`, `r_hat`, `is_inconclusive`. **Dependency**: T023b. **Status**: **Pending**.
- [ ] T024-LMM [US2] [Dep: T023c] Implement `code/analysis/model_comparison.py` to calculate AIC/WAIC and compare against a **Frequentist Linear Mixed Model (LMM)** baseline using `statsmodels`. **Deliverable**: A function `fit_baseline(data)` using `statsmodels.MixedLM` with formula `judgment_rating ~ salience_level + (|participant_id)`. **Constraint**: Must raise `ValueError` if model fails to converge. **Dependency**: T023c. **Note**: This task is data-agnostic and can run on both real and simulated data. **Status**: **Pending** - Baseline model definition is explicit.
- [ ] T025-PPC [US2] [Dep: T023c] Implement `code/analysis/model_comparison.py` to perform Posterior Predictive Checks (PPC). **Deliverable**: A function `run_ppc(model)` that generates posterior predictive samples using `pm.sample_posterior_predictive`, compares distribution of simulated data vs observed data using KS-test, and writes p-value to `data/results/ppc.json`. **Constraint**: Must fail if p-value < 0.05 (indicates poor fit). **Dependency**: T023c. **Status**: **Pending** - Explicit implementation details provided.
- [ ] T027a [US2] [Dep: T024-LMM] Implement `code/analysis/model_comparison.py` to calculate ΔAIC. **Dependency**: T024-LMM. **Status**: **Pending**.
- [ ] T027b [US2] [Dep: T027a] Implement `code/analysis/model_comparison.py` to report ΔAIC > 10 (Real Data Path). **Dependency**: T027a. **Status**: **Pending**.
- [ ] T027b-Sim-Read [US2] [Simulation] **DELTA AIC REPORTING**: Implement `code/analysis/simulation_delta_aic.py` to read baseline and bayesian AIC JSON files. **Deliverable**: A script that reads `data/results/baseline_aic.json` (from T024-LMM) and `data/results/bayesian_aic.json` (from T023c). **Dependency**: T023c, T024-LMM. **Status**: **Pending**.
- [ ] T027b-Sim-Calc [US2] [Simulation] Implement `code/analysis/simulation_delta_aic.py` to calculate **Delta AIC**. **Deliverable**: A function that computes `delta_aic = baseline_aic - bayesian_aic`. **Constraint**: Does NOT raise an error if `delta_aic <= 10`. Instead, it reports the value and sets a `status` field in the output JSON. **Dependency**: T027b-Sim-Read. **Status**: **Pending**.
- [ ] T027b-Sim-Write [US2] [Simulation] Implement `code/analysis/simulation_delta_aic.py` to write the report. **Deliverable**: A script that writes `data/results/simulation_delta_aic.json` with keys `delta_aic` (float), `threshold` (int, default 10), `threshold_check` (boolean), `status` (string: "PASS" or "FAIL" or "INCONCLUSIVE"). **Dependency**: T027b-Sim-Calc. **Status**: **Pending**.
- [ ] T027c [US2] [Simulation] Implement `code/analysis/parameter_recovery.py` to calculate **Parameter Recovery** metrics. **Deliverable**: A script that compares estimated posterior means against the `ground_truth_effect` injected in T013/T014. **Metrics**: Calculate bias (mean - truth) and coverage (proportion of truth within 95% CI). **Output**: `data/results/parameter_recovery.json`. **Format**: JSON with keys: `bias`, `coverage_95ci`, `n_samples`. **Dependency**: T023c, T014, T027b-Sim-Write. **Verification**: Must verify syntax and generate `data/results/parameter_recovery.json`. **Status**: **Pending**.
- [ ] T027b-test [US2] Unit test for ΔAIC threshold logic. **Dependency**: T027b.

---

## Phase 5: User Story 3 - Statistical Validation and Reporting (Priority: P3)

**Goal**: Perform mixed-effects regression, Bonferroni correction, and sensitivity analysis.

- [ ] T030 [US3] Implement `code/models/regression.py` for hierarchical mixed-effects regression. **Deliverable**: A function `fit_model(data)` using `statsmodels.MixedLM` with formula `judgment_rating ~ salience_level + (|participant_id)`. **Dependency**: T023c. **Status**: **Pending**.
- [ ] T031 [US3] Implement `code/analysis/validation.py` for Bonferroni correction. **Dependency**: T030. **Status**: **Pending**.
- [ ] T032-Logic [US3] [Dep: T030] Implement `code/analysis/validation.py` for sensitivity analysis (thresholds **{2, 10, 20}**). **Deliverable**: A script that sweeps thresholds and calculates stability metrics. **Dependency**: T030. **Status**: **Pending**.
- [ ] T032-Report [US3] [Dep: T032-Logic] Implement `code/analysis/validation.py` to write the sensitivity report. **Deliverable**: A script that writes `data/results/sensitivity_analysis.json`. **Schema**: JSON list of objects: `{'threshold': int, 'stability_metric': float, 'p_value': float}`. **Dependency**: T032-Logic. **Status**: **Pending**.
- [ ] T033 [US3] Implement `code/reports/generate_report.py` to generate the final report. **Deliverable**: A script that generates `reports/final_report.md`. **Content Structure**: Must include sections: Executive Summary, Model Comparison (ΔAIC), Parameter Recovery, Sensitivity Analysis, and Conclusion. **Dependency**: T030, T031, T032-Logic, T032-Report. **Status**: **Pending**.

---

## Phase 6: Real Data Integration (Deferred until Phase 6)

**Goal**: Implement the real data pipeline when verified data sources are available. (Note: Core ingestion moved to Phase 3).

- [ ] T060 [US4] [Real Data] Implement `code/data/streaming_loader.py` to stream large datasets. **Deliverable**: A script using `datasets.load_dataset(..., streaming=True)` with `itertools.islice` to process a representative initial subset of rows. **Constraint**: Must accumulate statistics online (running mean/variance) and log the exact sample size and streaming rule used. **Dependency**: T075-Real. **Status**: **Active** (for Phase 6).
- [ ] T016-Real [US4] [Real Data] Implement `code/data/preprocess_real.py` to map text stories to VR scenes using real VR logs. **Deliverable**: A script that maps text to salience levels using real blend-shape parameters. **Dependency**: T075-Real, T041-Real. **Status**: **Deferred**.

---

## Deferred Tasks (Not Executable in Current Phase)

- [ ] T042 [US4] [Deferred] End-to-End Real Data Pipeline.
- [ ] T054c [US4] [Deferred] Verify VR mapping with real data.
- [ ] T054d [US4] [Deferred] End-to-End real data tests.
- [ ] T016b [US1] [REMOVED] Merged into T016-Sim/T016-Real.
- [ ] T054b-Sim [US1] [REMOVED] Merged into T013/T014.
- [ ] T015-Real [US1] [REMOVED] Moved to Phase 3.
- [ ] T027d [US2] [REMOVED] Merged into T027c.

---

## Rejected / Failed Tasks (Requires Re-queuing)

- [X] T024 [US2] [REMOVED] Merged into T024-LMM.
- [X] T025 [US2] [REMOVED] Merged into T025-PPC.
- [X] T038 [US1] [REMOVED] Replaced by T076.
- [X] T032a [US3] [REMOVED] Merged into T032.
- [X] T022a [US2] [REMOVED] Duplicate of T051.

---

## Phase N: Validation and Cleanup

- [ ] T039 [P] [US1/US2/US3] Implement edge case tests for data ingestion, model convergence, and VR rendering failures. **Dependency**: T013, T023c, T016-Sim.
- [ ] T040 [P] [US1/US2/US3] Implement quickstart validation script to ensure the pipeline runs end-to-end. **Dependency**: T006, T018-Update, T056-Output. **Note**: Cannot be marked complete until T018-Update and T056-Output are complete.

---

## Revision Tasks (Addressing Review Concerns)

- [ ] T061 [US4] [Review: Data Source] Implement `code/data/fetch_real.py` with **strict failure-on-missing** logic. **Constraint**: If `DATA_MODE='real'` and the OSF or HuggingFace fetch fails, the script MUST raise a `ConnectionError` or `FileNotFoundError` and **NEVER** fall back to synthetic data. If `DATA_MODE='simulation'`, skip real fetch validation. This resolves the "silent synthetic fallback" fabrication risk. **Dependency**: T050.
- [ ] T062 [US4] [Review: Streaming] Implement `code/data/streaming_loader.py` using `datasets.load_dataset(..., streaming=True)` to process the full real dataset in chunks, ensuring memory safety without shrinking to a toy dataset. **Constraint**: The script must accumulate statistics online (e.g., running mean/variance) and must explicitly log the sample size and streaming strategy used. **Dependency**: T054b.
- [ ] T063 [US2] [Review: GPU Fallback] Update `code/models/bayesian.py` to detect CUDA availability. **Logic**: If `torch.cuda.is_available()` is True, set `device="cuda"`; otherwise, run on CPU. **Constraint**: If the task requires GPU (e.g., large model) and CPU fails convergence, the execution stage must re-run on Kaggle GPU; do NOT task a degenerate CPU imitation of a GPU method. **Dependency**: T022c.
- [ ] T065 [US3] [Review: Sensitivity] Ensure `code/analysis/validation.py` (T032) explicitly sweeps a range of thresholds including low values and writes the stability report to `data/results/sensitivity_analysis.json` as required by FR-005. **Dependency**: T030.
- [ ] T066 [US2] [Review: GPU Fallback Implementation] Implement explicit GPU detection and offload logic in `code/models/bayesian_model.py`. **Deliverable**: Add `try: import torch; has_gpu = torch.cuda.is_available() except: has_gpu = False` check. If `has_gpu` is True, configure PyMC5 sampler with `target_accept=0.9` and `nuts_sampler="numpyro"` (if available) or standard `pm.sample` with `chains=4, cores=4`. **Constraint**: If CPU sampling fails to converge (R-hat > 1.05) within the **4-hour** limit, the script must raise a `RuntimeError` with a specific message: "Convergence failed on CPU. Re-run on GPU." to trigger the execution stage's auto-offload mechanism. **Dependency**: T022c, T063.
- [ ] T067 [US4] [Review: Real Data Source Verification] Implement `code/data/verify_data_source.py` to validate that the real data source (OSF/HuggingFace) is reachable and returns valid schema before processing. **Deliverable**: A script that attempts to fetch a small sample (e.g., a representative subset of rows) from the real source. If the fetch fails or schema validation fails, raise `ConnectionError` immediately. **Constraint**: This task must run as a pre-check before T075-Real in `DATA_MODE='real'`. **Dependency**: T050, T061.
- [ ] T068 [US1] [Review: Simulation Fidelity] Implement `code/data/validate_simulation_fidelity.py` to ensure the synthetic VR logs generated in T014 match the statistical properties of the Gervais norms and literature-cited effect sizes. **Deliverable**: A script that compares the generated `response_time` and `gaze_metrics` distributions against the `research.md` citations. **Constraint**: Must raise `ValueError` if the synthetic data deviates significantly from the cited parameters. **Dependency**: T014, T019.