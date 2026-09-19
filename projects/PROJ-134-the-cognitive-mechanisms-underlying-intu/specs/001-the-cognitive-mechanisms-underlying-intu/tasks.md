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
- [X] T001b [P] Create subdirectories: `data/raw/`, `data/processed/`, `data/logs/`, `data/config/`, `reports/`. **Verification**: Confirm via `ls -d data/raw/ data/processed/ data/logs/ data/config/` and ensure `.gitkeep` files exist in each.
- [X] T002 [P] Initialize Python 3.11 project with `requirements.txt` (pymc==5.12.0, pandas, numpy, scikit-learn, pyyaml, requests, seaborn, statsmodels, torch). **Requirement Note**: PyMC5 is the mandated version per spec.md FR-002. The task must document this requirement in the `requirements.txt` header comment. **Deliverable**: Update `requirements.txt` and create `CHANGELOG.md` noting the PyMC5 deviation. **Constraint**: Do NOT modify `spec.md` in this task. **Verification**: Verify `requirements.txt` contains pymc==5.12.0 and `CHANGELOG.md` exists and mentions the PyMC5 deviation.
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. Includes Real Data Architecture Definition (T050), Configuration (T044, T045, T046), and Model Schema (T051) to ensure Producer before Consumer.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.
**⚠️ BLOCKING DEPENDENCY**: T045, T046, T051, T053, T050, T055, T043, T044 MUST be completed before T013, T014, T015, T022, T023, T041.
**⚠️ SEQUENTIAL ENFORCEMENT**: T005 -> T045 -> T013/T014; T045 -> T046; T055 depends on T050 and T008b completion.

### Removed Tasks
- [X] T053 [P] [US1/US4] **REMOVED**. This task was merged into T056 to resolve the run-book vs implementation mismatch. The `code/data/simulation.py` entry point is now defined and implemented in T056.

- [X] T045-MDES-Calc [US3] [Dep: T005] **Merged Task**: Implement MDES Calculation in `code/analysis/power_analysis.py`. **Deliverable**: A single script that: (1) Sets up CLI and config for N/SD, (2) Calculates MDES using `statsmodels.stats.power.tt_solve_power` with `alpha=0.05`, `power=0.8`, (3) Writes `state/mdes_report.yaml` with keys `n_required`, `effect_size`, `power`. **Constraint**: If `state/mdes_report.yaml` does not exist, the script MUST use a hardcoded default `N=100` from `code/config.py` to break the circular dependency and log "Using default N=100". **Dependency**: T005. **Status**: **Pending** - Must complete T005 before starting. **Pre-requisite**: T005 must be marked 'Complete' before T045-MDES-Calc can be executed.
- [X] T045-Sensitivity-Link [US3] [Dep: T045-MDES-Calc] Implement linkage of MDES results to sensitivity analysis in `code/analysis/power_analysis.py`. **Deliverable**: A script that reads `state/mdes_report.yaml` and explicitly includes a `sensitivity_implication` field in the report, linking the calculated power to the sensitivity analysis required by FR-005. **Dependency**: T045-MDES-Calc. **Note**: Ensures statistical power constraint is not silently violated. Supports both simulation and real data paths by reading N from config.
- [X] T046 [US3] [Dep: T045-Sensitivity-Link] Implement `code/analysis/validation.py` to validate that the simulated dataset size (N) matches the MDES assumption. **Deliverable**: A validation script that reads `state/mdes_report.yaml` and `code/config.py` (for `N_CONFIG`). It asserts `N_simulated == N_CONFIG`. If mismatch, raise `ValueError`. **Dependency**: T045-Sensitivity-Link. **Note**: Ensures statistical power constraint is not silently violated. Supports both simulation and real data paths by reading N from config.
- [X] T005 [P] Create `code/config.py` defining paths, random seeds, and constants. **Deliverable**: Include `N_CONFIG = 100` as a default for MDES fallback.
- [X] T006a [P] [US1] Implement `code/utils/hashing.py` to calculate SHA-256 checksums. **Deliverable**: A function `calculate_checksum(file_path: str) -> str` that returns the SHA-256 hex digest. **Verification**: Run `python -c "from code.utils.hashing import calculate_checksum; import tempfile, os; f = tempfile.NamedTemporaryFile(delete=False); f.write(b'test'); f.close(); print(calculate_checksum(f.name)); os.unlink(f.name)"` and confirm a valid hash is returned. **Constraint**: This task is NOT marked [P] and must complete before any artifact generation tasks. **Status**: **Active** - Must complete before T013/T014.
- [X] T006b [US1] [Dep: T006a] Implement `code/utils/hashing.py` to update `state/artifact_hashes.yaml`. **Deliverable**: A function `update_state_file(file_path: str, checksum: str)` that updates `state/artifact_hashes.yaml`. **Dependency**: T006a. **Verification**: Run `python -c "from code.utils.hashing import update_state_file, calculate_checksum; import tempfile, os; f = tempfile.NamedTemporaryFile(delete=False); f.write(b'test'); f.close(); update_state_file(f.name, calculate_checksum(f.name)); os.unlink(f.name)"` and confirm the hash is recorded in `state/artifact_hashes.yaml`.
- [X] T007b [P] Create `data/config/gervais_norms.yaml` containing the specific psychometric values (mean, std) for MFQ dimensions as per Gervais et al. **Deliverable**: A YAML file with keys for each foundation (Care, Fairness, etc.) and values for mean and std. **Verification**: Run `python -c "import yaml; print(yaml.safe_load(open('data/config/gervais_norms.yaml')))"` and confirm keys exist.
- [X] T007 [P] Implement `code/utils/norms.py` to load and reference Gervais et al. psychometric norms. **Deliverable**: A function `load_norms() -> dict` that returns the norms.
- [X] T008b [P] Implement `code/utils/schema.py` using Pydantic to create schema classes for MFQ, Stories, and VR Logs (validates data schemas). **Deliverable**: A valid Pydantic model class for each entity.
- [X] T009 [P] [US1] Implement `code/utils/logging.py` for base logging infrastructure. **Deliverable**: A configured logger in `code/utils/logging.py` that captures exclusion reasons and VR mapping logs to `data/logs/`. **Config**: Use `RotatingFileHandler` for `data/logs/ingest.log` and `data/logs/vr_mapping.log` with `JSONFormatter`. **Verification**: Run `python -c "from code.utils.logging import get_logger; logger = get_logger('test'); logger.info('test')"` and confirm `data/logs/ingest.log` contains the JSON log entry. **Implementation Detail**: Implement a retry decorator with `max_attempts=3` and `backoff_factor=1` for file I/O operations. **Constraint**: The logger MUST raise an exception (e.g., `ConnectionError`) if a real data source is unreachable, ensuring "fail loudly" behavior is captured and propagated. **Verification Step**: Include a unit test that mocks a missing data source and asserts `ConnectionError` is raised. **Status**: Pending verification of log file creation.
- [X] T050 [P] [US4-Interface] Define Real Data Architecture Interfaces in `code/data/ingest_real.py`. **Deliverable**: A module defining explicit constants and schemas: `OSF_API_URL` (base URL: ""), `HF_DATASET_ID` ("moral-foundations/mfq-v1"), and `VR_LOG_SCHEMA_COLUMNS` (list: `["response_time", "gaze_metrics", "judgment_rating"]`). **Verification**: The module must include a `verify_constants()` function that asserts these values match the canonical sources defined in `spec.md`. **Note**: This task defines the *interface* for Phase 6; the *implementation* (fetch logic) is deferred to Phase 6.
- [X] T050-Validate [US1] [Dep: T050, T008b] Implement `code/data/validate_schema.py` to validate ingested data against Pydantic models. **Deliverable**: A script that reads raw data from OSF/HF and validates it against the schemas defined in T008b. **Dependency**: T050, T008b. **Status**: **Active**.
- [X] T051 [P] [US2] Define `ModelResult` Artifact Schema in `code/utils/schemas.py`. **Deliverable**: A JSON/Parquet schema definition file (or Pydantic model) explicitly including fields: `participant_id`, `posterior_samples`, `r_hat`, `is_inconclusive` (boolean), and `mle_fallback` (float). This schema must be defined *before* T022/T023 implementation.
- [X] T044 [P] [US1] Create `data/config/unity_blend_shapes.yaml` defining the exact mapping of text story IDs to VR scene blend-shape parameters (low/high) used in the experimental design. **Deliverable**: A YAML file that serves as the single source of truth for the "perceptual salience" variable, replacing the assumption of a runtime Unity environment. **Schema**: Must contain keys `low` and `high` with nested objects for `blend_shape_params`. **Verification**: The file must be loadable and contain the expected structure.
- [X] T043 [US1/US4] [Dep: T005] Update `code/config.py` to add a `DATA_MODE` flag (`'real'` | `'simulation'`). **Default**: `'real'`. **Constraint**: If `DATA_MODE='real'` and real data is unavailable, the system MUST raise a `ConnectionError` and NEVER fall back to simulation. To run simulation, the user MUST explicitly set `DATA_MODE='simulation'` in the CLI or config. **Deliverable**: Config-driven routing that enforces the "Real Data Only" constraint. **Dependency**: T005 must complete first. **Note**: When `DATA_MODE='simulation'`, the system logs a warning and uses synthetic data.
- [X] T043-Verify [US4] [Verification] Implement unit test for T043 'fail loudly' behavior in `code/tests/test_config.py`. **Deliverable**: A test case `test_real_mode_missing_data_raises_error` that mocks a missing data source and asserts `ConnectionError` is raised when `DATA_MODE='real'`. **Dependency**: T043. **Status**: **Active**.
- [X] T019 [US3] [Dep: T005, T045-Sensitivity-Link] **VALIDATION**: Implement `code/analysis/validate_simulation_params.py` to perform sensitivity analysis on simulation parameters (e.g., range of low to high values) as required by literature. **Deliverable**: A script that sweeps thresholds [low, 10, 20] and calculates stability metrics, validating against literature cited in `research.md` (Gervais et al.). **Constraint**: Must raise `ValueError` if parameters are arbitrary or unsupported. **Dependency**: T005, T045-Sensitivity-Link. **Status**: **Active**.
- [X] T019-Model-Sensitivity [US3] [Dep: T005, T045-Sensitivity-Link] **VALIDATION**: Implement `code/analysis/validate_model_thresholds.py` to perform sensitivity analysis on *model* thresholds (e.g., {2, 10, 20}) as required by FR-005. **Deliverable**: A script that sweeps model thresholds [10, 20] and calculates stability metrics for the Bayesian model results. **Dependency**: T005, T045-Sensitivity-Link. **Note**: This task is distinct from T019 (simulation parameters) and focuses on model robustness. **Status**: **Active**.

---

## Phase 3: User Story 1 - Data Ingestion, Experimental Construction, and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest real MFQ and Moral Stories data, construct VR conditions with salience mapping, and validate psychometric distribution. **⚠️ FORMAL DEVIATION**: FR-006 (Real VR Logs) and US4 (Real Data Acquisition) are **PARTIALLY DEFERRED** for the *VR Log* component due to lack of open data. The system MUST fetch **Real MFQ** and **Real Moral Stories** (T054b, T041-Real) and fail loudly if missing. Synthetic VR logs (T013/T014) are **Simulation Validation Only** and must be explicitly labeled as such, not as the primary FR-006 deliverable.

**Staged Implementation Authorization**: Per Plan.md Section "Pipeline Validation", FR-006 ("capture and process actual VR interaction logs") is explicitly deferred until **Phase 6: Data Acquisition** for the VR log component. However, the ingestion of **Real MFQ** and **Real Moral Stories** (FR-001) is **MANDATORY** in this phase. The tasks T054b and T041-Real implement this. The tasks T013-T018 implement a **Simulation Validation Layer** to test the pipeline architecture with known ground truth, but these are **NOT** the primary FR-006 deliverable.

**Default Execution Mode**: `real`. The system defaults to using real data. To switch to `DATA_MODE='simulation'` requires explicit manual config override in `code/config.py` or CLI flag.

**Independent Test**: The pipeline can be tested by running the ingestion and construction scripts against the real data (via `--mode=real`) and verifying that the output CSV contains correctly merged rows, valid salience labels, and matches Gervais et al. norms. **Schema Requirement**: The output CSV MUST contain `gaze_metrics` (as a JSON string or structured column), `response_time`, `salience_level`, etc., matching spec.md US-1 Acceptance Scenario 1.

**⚠️ BLOCKING DEPENDENCY**: Phase 2 (T045, T046, T006) must complete successfully before any Phase 3 task can execute.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T010 [P] [US1] Unit test for **Simulation** MFQ generator in `code/tests/test_ingest_mfq.py`. **Deliverable**: Function `test_mfq_distribution_matches_norms` that asserts `assert abs(mean - expected_mean) < 0.05` using values explicitly loaded from `data/config/gervais_norms.yaml`. **Note**: This test validates the **simulation fallback** path, not the primary real-data ingestion path defined in FR-001.
- [X] T011 [P] [US1] Unit test for salience mapping logic in `code/tests/test_schema.py`. **Deliverable**: Function `test_salience_mapping_valid` that asserts `assert salience_level in ['low', 'high']` given mock story IDs.
- [X] T012 [US1] Unit test for psychometric norm validation in `code/tests/test_ingest_stories.py`. **Deliverable**: Function `test_psychometric_validity` using Kolmogorov-Smirnov test with p > 0.05 threshold against Gervais et al. norms.

### Implementation for User Story 1 (Real Data & Simulation Validation)

- [ ] T054b [US4] [Real Data] Implement `code/data/fetch_real.py` to fetch **Real MFQ** and **Real Moral Stories** from OSF/HuggingFace (IDs: `hf://moral-foundations/mfq-v1`, `hf://moral-foundations/stories-v1`). **Constraint**: If `DATA_MODE='real'` and the OSF/HF fetch fails, the script MUST raise a `ConnectionError` and **NEVER** fall back to synthetic data. **Deliverable**: Generate `data/raw/mfq_real.csv` and `data/raw/stories_real.csv`. **Note**: This task fetches MFQ/Stories ONLY. It does not fetch VR logs. **Dependency**: T050, T043. **Status**: **Active** - Primary FR-001/FR-006 implementation (MFQ/Stories).

- [ ] T054c [US4] [Real Data] Implement `code/data/fetch_real_vr.py` to fetch **Real VR Logs** from OSF/HuggingFace (ID: `hf://moral-foundations/vr-logs-v1` or similar verified source). **Constraint**: If `DATA_MODE='real'` and the VR log fetch fails, the script MUST raise a `ConnectionError` and **NEVER** fall back to synthetic data. **Deliverable**: Generate `data/raw/vr_logs_real.csv`. **Note**: This task fetches VR logs ONLY. If `DATA_MODE='simulation'`, this task is skipped. **Dependency**: T050, T043. **Status**: **Active** - Primary FR-006 implementation (VR Logs).

- [ ] T075-Validate [US1] [Real Data] Implement `code/data/validate_mfq_norms.py` to validate the real MFQ data against Gervais norms. **Deliverable**: A script that reads `data/raw/mfq_real.csv` and performs KS-test against norms in `data/config/gervais_norms.yaml`. **Dependency**: T054b, T007b. **Status**: **Active**.

- [ ] T015-Gate-Mode [US1] [Gate] Implement `code/data/gate_mode.py` to enforce `DATA_MODE` and the "fail loudly" constraint. **Logic**:
 1. If `DATA_MODE='real'`, verify real MFQ and Moral Stories sources (T054b) and VR logs (T054c) are available.
 2. **CRITICAL**: If `DATA_MODE='real'` and MFQ/Stories are missing, raise `ConnectionError` immediately.
 3. If `DATA_MODE='real'` and MFQ/Stories exist but VR logs are missing:
    - If `config.FORMAL_DEVIATION_VR_LOGS` is False, raise `ConnectionError` with message "FR-006 Violation: Real VR logs missing. Switch DATA_MODE to 'simulation' manually."
    - If `config.FORMAL_DEVIATION_VR_LOGS` is True, log a warning and proceed to simulation mode.
 4. If `DATA_MODE='simulation'`, log the deviation and allow simulation.
 **Deliverable**: A script `gate_mode.py` with a function `check_mode_and_data()` that raises `ConnectionError` ONLY if MFQ/Stories are missing in 'real' mode OR if VR logs are missing in 'real' mode (unless deviation flag is set). **Dependency**: T043, T050, T054b, T054c. **Status**: **Active** - Must run before T013/T014.

- [ ] T013 [US1] [Simulation Validation - Simulation Only] Implement `code/data/simulation_mfq.py` to generate synthetic MFQ data based on Gervais et al. multivariate normal distributions. **Validation**: The `ground_truth_effect` parameter must be validated against the MDES calculated in T045-MDES-Calc. **Pre-requisite Check**: **MUST** verify `state/mdes_report.yaml` exists and contains keys `n_required`, `effect_size`, `power` before execution. If missing, raise `FileNotFoundError: MDES report missing. Ensure T045-MDES-Calc is complete.` **Deliverable**: Generate `data/processed/synthetic_mfq.csv`. **Verification**: Verify file exists, is not empty, and contains columns: `participant_id`, `care`, `fairness`, `loyalty`, `authority`, `purity`, `total_score`. **Dependency**: **T045-MDES-Calc**, **T005**, **T006a**, **T006b**, **T015-Gate-Mode**. **Status**: **Pending** - Simulation Validation Only. **Note**: T045-MDES-Calc must be marked 'Complete' before T013 can be executed.

- [ ] T014 [US1] [Simulation Validation - Simulation Only] Implement `code/data/simulation_stories.py` to generate synthetic Moral Stories and VR interaction logs with a known `ground_truth_effect`. **Deliverable**: Generate `data/processed/synthetic_logs.csv` with `response_time`, `gaze_metrics`, and `salience_level` columns. **Constraint**: Must inject known effect sizes for parameter recovery analysis in T027c-Parameter-Recovery. **Distribution**: `response_time` ~ LogNormal(3.5, 0.5), `gaze_metrics` ~ Normal(0.5, 0.1). **Verification**: Verify file exists and contains columns: `participant_id`, `story_id`, `salience_level`, `response_time`, `gaze_metrics`, `judgment_rating`. **Dependency**: **T005**, **T044**, **T006a**, **T006b**, **T045-MDES-Calc**, **T015-Gate-Mode**. **Status**: **Pending** - Simulation Validation Only. **Note**: T045-MDES-Calc must be marked 'Complete' before T014 can be executed.

- [ ] T016-Sim [US1] [Simulation] Implement `code/data/preprocess.py` to map text stories to VR scenes, assigning `salience_level` (low/high) via blend-shape parameters. **Dependency**: Read configuration from `data/config/unity_blend_shapes.yaml` (T044). **Schema Check**: The config file must contain keys `low` and `high`, each with a nested `blend_shape_params` object. If missing, raise `ValueError`. **Dependency**: T044, **T013**, **T014**. **Status**: **Pending**.

- [ ] T016-Validate [US1] [Simulation] Implement `code/data/validate_salience_conditions.py` to validate the resulting salience conditions against the psychometric distribution. **Deliverable**: A script that checks the distribution of `salience_level` in the processed data against expected distributions. **Dependency**: T016-Sim, T017-Logic. **Status**: **Pending**.

- [ ] T017-Logic [US1] [Simulation] Implement `code/utils/norms.py` validation function `validate_mfq_distribution()`. **Deliverable**: A function that uses Kolmogorov-Smirnov test (p > 0.05) against norms loaded from `data/config/gervais_norms.yaml`. **Dependency**: T013, **T009**. **Status**: **Pending**.

- [ ] T017-Report [US1] [Simulation] Implement `code/reports/generate_norm_report.py` to write the validation result. **Deliverable**: A script that calls T017-Logic and writes a JSON report to `data/logs/norm_validation.json` with keys `p_value` (float), `statistic` (float), `pass_fail` (boolean). **Dependency**: T017-Logic. **Status**: **Pending**.

- [ ] T018-Checksum [US1] [Simulation] Implement `code/utils/hashing.py` integration to calculate checksums for **simulation-derived** CSVs. **Files**: `data/processed/synthetic_mfq.csv`, `data/processed/synthetic_logs.csv`. **Dependency**: T006a, T013, T014. **Status**: **Pending**.

- [ ] T018-Update [US1] [Simulation] Implement `code/utils/hashing.py` update logic to update `state/artifact_hashes.yaml`. **Files**: `data/processed/synthetic_mfq.csv`, `data/processed/synthetic_logs.csv`. **Schema**: Update `state/artifact_hashes.yaml` with keys `synthetic_mfq.csv` and `synthetic_logs.csv` containing their SHA-256 hashes. **Dependency**: T018-Checksum. **Status**: **Pending**.

- [ ] T018-Verify [US1] [Simulation] Verify that `state/artifact_hashes.yaml` contains checksums for `data/processed/synthetic_mfq.csv` and `data/processed/synthetic_logs.csv`. **Deliverable**: A script that asserts the existence of these keys in the YAML file. **Dependency**: T018-Update. **Status**: **Pending**.

- [ ] T076 [US1] [Simulation] Implement `code/unity_verification.py` to verify the simulation's fidelity to the actual Unity environment by validating blend-shape parameters against a reference configuration file (`data/config/unity_blend_shapes.yaml`). **Validation Logic**: Check that simulated blend-shape values match reference values within an acceptable tolerance. **Deliverable**: Write verification status to `data/config/unity_simulation_fidelity.yaml` with keys `status` (pass/fail) and `details`. **CRITICAL**: MUST ALSO log the actual parameter sets used in the simulation run to `data/logs/simulation_params.log` as required by Constitution Principle VI. **Dependency**: T044. **Constraint**: Must checksum `data/config/unity_simulation_fidelity.yaml` and `data/logs/simulation_params.log` and update `state/artifact_hashes.yaml` as per Constitution Principle V. **Requirement**: The script MUST log the actual parameter sets used in the simulation run to `data/logs/simulation_params.log` for reproducibility. **Status**: **Pending**.

- [ ] T056-CLI [US1] [Simulation] Implement CLI argument parsing for `code/data/simulation.py`. **Deliverable**: A script with `argparse` for `--mode` and `--seed`. **Dependency**: T005. **Status**: **Pending**.

- [ ] T056-Orch [US1] [Simulation] Implement orchestration logic for `code/data/simulation.py`. **Flow**:
 1. **Execute T013** (MFQ Gen)
 2. **Execute T014** (Log Gen)
 3. **Execute T016-Sim** (Preprocess)
 4. Write `data/processed/merged_simulation.csv`.
 **Output**: Writes `data/processed/merged_simulation.csv`. **Dependency**: T056-CLI, T013, T014, T016-Sim. **Note**: This task assumes T015-Gate-Mode has passed; execute the simulation path. **Status**: **Pending**.

- [ ] T056-Output [US1] [Simulation] Implement output serialization for `code/data/simulation.py`. **Deliverable**: A script that writes a summary JSON to `data/results/simulation_summary.json`. **Dependency**: T056-Orch. **Status**: **Pending**.

- [ ] T069 [US1] [Real Data Mode Gate] **REMOVED**. Logic moved to T054b/T041-Real.
- [ ] T075 [US4] [Real Data Gate] **REMOVED**. Merged into T054b/T041-Real.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (Real Data Mode). Simulation Mode is available for validation only.

---

## Phase 4: User Story 2 - Bayesian Model Execution and Comparison (Priority: P2)

**Goal**: Execute the Bayesian model on the preprocessed data (simulation or real) and compare against baseline.

**Interface Contract**:
- **T022** outputs a `model` object adhering to the `ModelResult` schema (T051).
- **T023** takes the `model` object from T022 as input and outputs comparison metrics.

- [ ] T022b [US2] [Dep: T051] Implement PyMC5 model definition in `code/models/bayesian_model.py`. **Deviation Note**: This task implements PyMC5 as mandated by spec.md FR-002. **Deliverable**: A function `build_model(data)` returning a PyMC model. **Dependency**: T051.
- [ ] T022c [US2] [Dep: T022b] Implement wrapper to ensure schema compliance in `code/models/bayesian_model.py`. **Deliverable**: A function `run_model(data)` that returns a `ModelResult` object. **Dependency**: T022b.
- [ ] T022d [US2] [Dep: T022c] Implement **PyMC5 Convergence Check** in `code/tests/test_migration.py`. **Deliverable**: A script that verifies R-hat < 1.05 and effective sample size > 200 for all parameters. **Constraint**: Does NOT compare against PyMC3. **Dependency**: T022c. **Status**: **Pending**.
- [ ] T023-Sampling [US2] [Dep: T022c] Implement MCMC sampling execution in `code/models/run_bayesian.py`. **Deliverable**: A function `sample_model(model)` using `pm.sample(chains=4, draws=2000, target_accept=0.9)` that returns samples AND explicitly outputs the posterior distributions as a distinct artifact. **Dependency**: T022c. **Status**: **Active** - Must complete before T024-Comparison. **Verification**: Verify that the output artifact contains posterior samples and is not empty.
- [ ] T024-Baseline-LMM [US2] [Dep: T023-Sampling] Implement `code/analysis/model_comparison.py` to fit a **Frequentist Linear Mixed Model (LMM)** baseline using `statsmodels`. **Deliverable**: A function `fit_baseline(data)` using `statsmodels.MixedLM` with formula `judgment_rating ~ salience_level + (|participant_id)`. **Constraint**: Must raise `ValueError` if model fails to converge. **Dependency**: T023-Sampling. **Status**: **Pending**.
- [ ] T024-PPC [US2] [Dep: T023-Sampling] Implement `code/analysis/model_comparison.py` to perform Posterior Predictive Checks (PPC). **Deliverable**: A function `run_ppc(model)` that generates posterior predictive samples using `pm.sample_posterior_predictive`, compares distribution of simulated data vs observed data using KS-test, and writes p-value to `data/results/ppc.json`. **Constraint**: Must fail if p-value < 0.05 (indicates poor fit). **Dependency**: T023-Sampling. **Status**: **Pending**.
- [ ] T024-Report [US2] [Dep: T024-Baseline-LMM, T024-PPC] Implement `code/analysis/model_comparison.py` to calculate AIC/WAIC and write the unified comparison report. **Deliverable**: A script that calculates `delta_aic`, `waic`, `ppc_p_value`, and writes a unified JSON report `data/results/model_comparison.json` containing these metrics and a `comparison_summary` field that explicitly links the PPC results to the LMM comparison. **Dependency**: T024-Baseline-LMM, T024-PPC. **Note**: This task is data-agnostic and can run on both real and simulated data. **Status**: **Pending**.
- [ ] T027a [US2] [Dep: T024-Report] Implement `code/analysis/model_comparison.py` to calculate ΔAIC. **Dependency**: T024-Report. **Status**: **Pending**.
- [ ] T027b [US2] [Dep: T027a] Implement `code/analysis/model_comparison.py` to report ΔAIC > 10 (Real Data Path). **Dependency**: T027a. **Status**: **Pending**.
- [ ] T027b-Sim-Read [US2] [Simulation] **DELTA AIC REPORTING**: Implement `code/analysis/simulation_delta_aic.py` to read baseline and bayesian AIC JSON files. **Deliverable**: A script that reads `data/results/baseline_aic.json` (from T024-Report) and `data/results/bayesian_aic.json` (from T023-Sampling). **Dependency**: T023-Sampling, T024-Report. **Status**: **Pending**.
- [ ] T027b-Sim-Calc [US2] [Simulation] Implement `code/analysis/simulation_delta_aic.py` to calculate **Delta AIC**. **Deliverable**: A function that computes `delta_aic = baseline_aic - bayesian_aic`. **Constraint**: Does NOT raise an error if `delta_aic <= 10`. Instead, it reports the value and sets a `status` field in the output JSON. **Dependency**: T027b-Sim-Read. **Status**: **Pending**.
- [ ] T027b-Sim-Write [US2] [Simulation] Implement `code/analysis/simulation_delta_aic.py` to write the report. **Deliverable**: A script that writes `data/results/simulation_delta_aic.json` with keys `delta_aic` (float), `threshold` (int, default 10), `threshold_check` (boolean), `status` (string: "PASS" or "FAIL" or "INCONCLUSIVE"). **Dependency**: T027b-Sim-Calc. **Status**: **Pending**.
- [ ] T027c-Parameter-Recovery [US2] [Dep: T023-Sampling, T014, T027b-Sim-Write] Implement `code/analysis/parameter_recovery.py` to calculate **Parameter Recovery** metrics. **Deliverable**: A script that compares estimated posterior means against the `ground_truth_effect` injected in T014. **Metrics**: Calculate bias (mean - truth) and coverage (proportion of truth within 95% CI). **Output**: `data/results/parameter_recovery.json`. **Format**: JSON with keys: `bias`, `coverage_95ci`, `n_samples`. **Dependency**: T023-Sampling, T014, T027b-Sim-Write. **Verification**: Must verify syntax and generate `data/results/parameter_recovery.json`. **Status**: **Pending**.
- [ ] T027c-Sensitivity-Analysis [US2] [Dep: T027c-Parameter-Recovery] Implement `code/analysis/parameter_recovery.py` to perform sensitivity analysis on model thresholds (e.g., {2, 10, 20}) as required by FR-005. **Deliverable**: A script that sweeps thresholds [low, 10, 20] and calculates stability metrics. **Output**: Append `sensitivity_analysis` (list of threshold results) to `data/results/parameter_recovery.json`. **Dependency**: T027c-Parameter-Recovery. **Verification**: Must verify syntax and generate `data/results/parameter_recovery.json` with sensitivity data. **Status**: **Pending**.
- [ ] T027b-test [US2] Unit test for ΔAIC threshold logic. **Dependency**: T027b.

---

## Phase 5: User Story 3 - Statistical Validation and Reporting (Priority: P3)

**Goal**: Perform mixed-effects regression, Bonferroni correction, and sensitivity analysis.

- [ ] T030-Regression [US3] Implement `code/models/regression.py` for hierarchical mixed-effects regression with Bonferroni correction. **Deliverable**: A function `fit_model(data)` using `statsmodels.MixedLM` with formula `judgment_rating ~ salience_level + (|participant_id)`. **Constraint**: The function MUST apply Bonferroni correction to the regression p-values within the same function before serialization. **Output**: A single artifact `data/results/mixed_effects_bonferroni_results.json` containing the regression coefficients, raw p-values, and Bonferroni-corrected p-values. **Dependency**: T023-Sampling. **Status**: **Pending**.
- [ ] T031 [US3] **REMOVED**. Merged into T030-Regression.
- [ ] T032-Logic [US3] [Dep: T030-Regression] Implement `code/analysis/validation.py` for sensitivity analysis (thresholds **[2, 10, 20]**). **Deliverable**: A script that sweeps thresholds [2, 10, 20] and calculates stability metrics. **Definition**: `stability_metric` is defined as the coefficient of variation of p-values across thresholds. **Dependency**: T030-Regression. **Status**: **Active** - Must complete before T032-Report. **Verification**: Ensure T030-Regression is complete before starting.
- [ ] T032-Report [US3] [Dep: T032-Logic] Implement `code/analysis/validation.py` to write the sensitivity report. **Deliverable**: A script that writes `data/results/sensitivity_analysis.json`. **Schema**: JSON list of objects: `{'threshold': int, 'stability_metric': float, 'p_value': float}`. **Dependency**: T032-Logic. **Status**: **Pending** - Must complete before T033-Report.
- [ ] T033-Report [US3] Implement `code/reports/generate_report.py` to generate the final report. **Deliverable**: A script that generates `reports/final_report.md`. **Content Structure**: Must include sections: Executive Summary, Model Comparison (ΔAIC), Parameter Recovery, Sensitivity Analysis, Mixed-Effects Regression Results with Bonferroni Correction, and Conclusion. **Dependency**: T030-Regression, T032-Logic, **T032-Report**. **Status**: **Pending** - Must complete after T032-Report.
- [ ] T033-Synthesis [US3] [Dep: T027c-Parameter-Recovery, T027c-Sensitivity-Analysis, T045-Sensitivity-Link] Implement `code/analysis/synthesis.py` to synthesize MDES, Parameter Recovery, and Sensitivity results into a single robustness claim. **Deliverable**: A script that reads the three artifacts and outputs `data/results/robustness_summary.json`. **Logic**: If Parameter Recovery coverage > 95% AND Sensitivity stability metric < 0.1, then the model is robust. **Dependency**: T027c-Parameter-Recovery, T027c-Sensitivity-Analysis, T045-Sensitivity-Link. **Status**: **Pending**. **Note**: T045-Sensitivity-Link must be marked 'Complete' before T033-Synthesis can be executed.

---

## Phase 6: Real Data Integration (Deferred until Phase 6)

**Goal**: Implement the real data pipeline when verified data sources are available. (Note: Core ingestion moved to Phase 3).

- [ ] T060 [US4] [Real Data] Implement `code/data/streaming_loader.py` to stream large datasets. **Deliverable**: A script using `datasets.load_dataset(..., streaming=True)` with `itertools.islice` to process a representative initial subset of rows. **Constraint**: Must accumulate statistics online (running mean/variance) and log the exact sample size and streaming rule used. **Dependency**: T054b. **Status**: **Active** (for Phase 6).
- [ ] T016-Real [US4] [Real Data] Implement `code/data/preprocess_real.py` to map text stories to VR scenes using real VR logs. **Deliverable**: A script that maps text to salience levels using real blend-shape parameters. **Dependency**: T054b, T041-Real. **Status**: **Deferred**.

---

## Deferred Tasks (Not Executable in Current Phase)

- [ ] T042 [US4] [Deferred] End-to-End Real Data Pipeline.
- [ ] T054c [US4] [Deferred] Verify VR mapping with real data.
- [ ] T054d [US4] [Deferred] End-to-End real data tests.
- [ ] T016b [US1] [REMOVED] Merged into T016-Sim/T016-Real.
- [ ] T054b-Sim [US1] [REMOVED] Merged into T013/T014.
- [ ] T015-Real [US1] [REMOVED] Moved to Phase 3.
- [ ] T027d [US2] [REMOVED] Merged into T027c.
- [ ] T041-Real [US4] [REMOVED] **REMOVED**. This task attempted to fetch non-existent VR logs, causing a logical contradiction with the plan. The "Real VR Logs" requirement is now fully deferred to Phase 6. T015-Gate-Mode no longer checks for T041-Real.

---

## Rejected / Failed Tasks (Requires Re-queuing)

- [X] T024 [US2] [REMOVED] Merged into T024-Report.
- [X] T025 [US2] [REMOVED] Merged into T024-PPC.
- [X] T038 [US1] [REMOVED] Replaced by T076.
- [X] T032a [US3] [REMOVED] Merged into T032.
- [X] T022a [US2] [REMOVED] Duplicate of T051.

---

## Phase N: Validation and Cleanup

- [ ] T039 [P] [US1/US2/US3] Implement edge case tests for data ingestion, model convergence, and VR rendering failures. **Dependency**: T013, T023-Sampling, T016-Sim.
- [ ] T040 [P] [US1/US2/US3] Implement quickstart validation script to ensure the pipeline runs end-to-end. **Dependency**: T006a, T006b, T018-Update, T056-Output. **Note**: Cannot be marked complete until T018-Update and T056-Output are complete.

---

## Revision Tasks (Addressing Review Concerns)

- [ ] T061 [US4] [Review: Data Source] Implement `code/data/fetch_real.py` with **strict failure-on-missing** logic. **Constraint**: If `DATA_MODE='real'` and the OSF or HuggingFace fetch fails, the script MUST raise a `ConnectionError` or `FileNotFoundError` and **NEVER** fall back to synthetic data. If `DATA_MODE='simulation'`, skip real fetch validation. This resolves the "silent synthetic fallback" fabrication risk. **Dependency**: T050.
- [ ] T062 [US4] [Review: Streaming] Implement `code/data/streaming_loader.py` using `datasets.load_dataset(..., streaming=True)` to process the full real dataset in chunks, ensuring memory safety without shrinking to a toy dataset. **Constraint**: The script must accumulate statistics online (e.g., running mean/variance) and must explicitly log the sample size and streaming strategy used. **Dependency**: T054b.
- [ ] T063 [US2] [Review: GPU Fallback] Update `code/models/bayesian.py` to detect CUDA availability. **Logic**: If `torch.cuda.is_available()` is True, set `device="cuda"`; otherwise, run on CPU. **Constraint**: If the task requires GPU (e.g., large model) and CPU fails convergence, the execution stage must re-run on Kaggle GPU; do NOT task a degenerate CPU imitation of a GPU method. **Dependency**: T022c.
- [ ] T065 [US3] [Review: Sensitivity] Ensure `code/analysis/validation.py` (T032) explicitly sweeps a range of thresholds including [2, 10, 20] and writes the stability report to `data/results/sensitivity_analysis.json` as required by FR-005. **Dependency**: T030.
- [ ] T066 [US2] [Review: GPU Fallback Implementation] Implement explicit GPU detection and offload logic in `code/models/bayesian_model.py`. **Deliverable**: Add `try: import torch; has_gpu = torch.cuda.is_available() except: has_gpu = False` check. If `has_gpu` is True, configure PyMC5 sampler with `target_accept=0.9` and `nuts_sampler="numpyro"` (if available) or standard `pm.sample` with `chains=4, cores=4`. **Constraint**: If CPU sampling fails to converge (R-hat > 1.05) within the **4-hour** limit, the script must raise a `RuntimeError` with a specific message: "Convergence failed on CPU. Re-run on GPU." to trigger the execution stage's auto-offload mechanism. **Implementation Detail**: Wrap `pm.sample` in a `time.time()` check loop that raises RuntimeError if `elapsed > 14400`. **Dependency**: T022c, T063. **Note**: This logic is for execution stage offload and does not contradict plan constraints.
- [ ] T067 [US4] [Review: Real Data Source Verification] Implement `code/data/verify_data_source.py` to validate that the real data source (OSF/HuggingFace) is reachable and returns valid schema before processing. **Deliverable**: A script that attempts to fetch a small sample (e.g., a representative subset of rows) from the real source. If the fetch fails or schema validation fails, raise `ConnectionError` immediately. **Constraint**: This task must run as a pre-check before T054b in `DATA_MODE='real'`. **Dependency**: T050, T061.
- [ ] T068 [US1] [Review: Simulation Fidelity] Implement `code/data/validate_simulation_fidelity.py` to ensure the synthetic VR logs generated in T014 match the statistical properties of the Gervais norms and literature-cited effect sizes. **Deliverable**: A script that compares the generated `response_time` and `gaze_metrics` distributions against the `research.md` citations. **Constraint**: Must raise `ValueError` if the synthetic data deviates significantly from the cited parameters. **Dependency**: T014, T019.