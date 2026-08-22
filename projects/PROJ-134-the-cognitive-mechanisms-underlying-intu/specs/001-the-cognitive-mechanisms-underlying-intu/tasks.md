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
**⚠️ SEQUENTIAL ENFORCEMENT**: T045 and T046 are the **BLOCKING TASKS** for Phase 3. They MUST complete successfully before T013 (Phase 3) can execute. These are NOT parallelizable with Phase 3 tasks. Note: T045 -> T046; T055 depends on T050 and T008b completion.

- [X] T045 [US3] Implement `code/analysis/power_analysis.py` to calculate the minimum detectable effect size (MDES) for a mixed-effects model with **N=200** participants and 50 vignettes, assuming a standard deviation of **1.0**, alpha=0.05, and **power=0.80**. **Deliverable**: A report stating the MDES and writing the calculated value to `state/mdes_report.yaml` under the key `mdes_value`. **Note**: Use N=200 and SD=1.0 as defined in `plan.md` Section "Success Criteria". **Constraint**: The calculated MDES must be strictly less than the `ground_truth_effect` used in the simulation to ensure statistical power; if not, the script must raise a `ValueError`. **Output**: `state/mdes_report.yaml` with key `mdes_value`. **Priority**: This task MUST be executed first in Phase 2 to ensure downstream tasks (T013) have valid MDES data. **Dependency**: T005 (config.py) must complete first. **Enforcement**: A pre-commit hook MUST be configured to verify T045 completion before T013 execution.
- [X] T046 [US3] [Dep: T045] Implement `code/analysis/validation.py` to validate that the simulated dataset size (N) matches the MDES assumption (N=200) calculated in T045. **Deliverable**: A validation script that reads `state/mdes_report.yaml` and asserts `N_simulated == 200`. If mismatch, raise `ValueError`. **Dependency**: T045 must complete first. **Note**: Ensures statistical power constraint is not silently violated.
- [X] T005 [P] Create `code/config.py` defining paths, random seeds, and constants
- [X] T006 [P] Implement `code/utils/hashing.py` to calculate SHA-256 checksums and update `state/artifact_hashes.yaml` (Constitution Principle V). **Deliverable**: A function `calculate_checksum(file_path: str) -> str` that returns the SHA-256 hex digest and a function `update_state_file(file_path: str, checksum: str)` that updates `state/artifact_hashes.yaml`. **Verification**: Run `python -c "from code.utils.hashing import calculate_checksum, update_state_file; update_state_file('data/processed/test.csv', calculate_checksum('data/processed/test.csv'))"` and confirm the hash is recorded in `state/artifact_hashes.yaml` under the key `test.csv`. **Constraint**: This task is NOT marked [P] and must complete before any artifact generation tasks.
- [X] T007b [P] Create `data/config/gervais_norms.yaml` containing the specific psychometric values (mean, std) for MFQ dimensions as per Gervais et al. (2011). **Deliverable**: A YAML file with keys for each foundation (Care, Fairness, etc.) and values for mean and std. **Verification**: Run `python -c "import yaml; print(yaml.safe_load(open('data/config/gervais_norms.yaml')))"` and confirm keys exist.
- [X] T007 [P] [Dep: T007b] Implement `code/utils/norms.py` to load and reference Gervais et al. psychometric norms. **Deliverable**: A function `load_norms() -> dict` that returns the norms.
- [X] T008b [P] Implement `code/utils/schema.py` using Pydantic to create schema classes for MFQ, Stories, and VR Logs (validates data schemas). **Deliverable**: A valid Pydantic model class for each entity.
- [X] T009 [P] Implement `code/utils/logging.py` for base logging infrastructure. **Deliverable**: A configured logger in `code/utils/logging.py` that captures exclusion reasons and VR mapping logs to `data/logs/`. **Config**: Use `RotatingFileHandler` for `data/logs/ingest.log` and `data/logs/vr_mapping.log` with `JSONFormatter`. **Verification**: Run `python -c "from code.utils.logging import get_logger; logger = get_logger('test'); logger.info('test')"` and confirm `data/logs/ingest.log` contains the JSON log entry.
- [X] T050 [P] [US4-Interface] Define Real Data Architecture Interfaces in `code/data/ingest_real.py`. **Deliverable**: A module defining explicit constants and schemas: `OSF_API_URL` (base URL: "https://api.osf.io/v2/"), `HF_DATASET_ID` ("moral-stories-v1"), and `VR_LOG_SCHEMA_COLUMNS` (list: `["response_time", "gaze_metrics", "judgment_rating"]`). **Verification**: The module must include a `verify_constants()` function that asserts these values match the canonical sources defined in `spec.md`. **Note**: This task defines the *interface* for Phase 4; the *implementation* (fetch logic) is deferred to Phase 6.
- [X] T051 [P] [US2] Define `ModelResult` Artifact Schema in `code/utils/schemas.py`. **Deliverable**: A JSON/Parquet schema definition file (or Pydantic model) explicitly including fields: `participant_id`, `posterior_samples`, `r_hat`, `is_inconclusive` (boolean), and `mle_fallback` (float). This schema must be defined *before* T022/T023 implementation.
- [X] T044 [P] [US1] Create `data/config/unity_blend_shapes.yaml` defining the exact mapping of text story IDs to VR blend-shape parameters (low/high salience) used in the simulation. **Deliverable**: A YAML file that serves as the single source of truth for the "perceptual salience" variable, replacing the assumption of a runtime Unity environment.
- [X] T043 [P] [US1/US4] Update `code/config.py` to add a `DATA_MODE` flag (`'simulation'` | `'real'`). **Default**: `'real'`. Ensure `code/data/ingest.py` routes to `ingest_real.py` when `DATA_MODE='real'` and to `simulation.py` when `DATA_MODE='simulation'`, with a hard assertion that `DATA_MODE` cannot be 'real' without a verified source. **Deliverable**: Config-driven routing that enforces the "Real Data Only" constraint when requested. **Trigger**: Only execute if `DATA_MODE='real'`. **Dependency**: T005 (config.py creation) must complete first.
- [X] T055 [P] [US1/US4] Implement `code/utils/schema_equivalence.py` to verify that the simulation data schema (generated by T014) is structurally identical to the Real Data Interface schema (defined in T050). **Deliverable**: A script that compares the Pydantic models from T008b (Simulation) and T050 (Real) and raises an error if any field mismatch is found. **Dependency**: T050 and T008b must complete first. **Note**: This task ensures FR-006's data capture requirements are met structurally even if data is simulated.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion, Experimental Construction, and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest real MFQ and Moral Stories data, construct VR conditions with salience mapping, and validate psychometric distribution. **FR-006 (Real VR Logs) is satisfied by the implementation of T050 (Interface), T060 (Streaming), and T016/T016b (Mapping) in this phase.** T013-T018 are explicitly labeled as 'Simulation-Only' for local unit testing, while the *capability* to capture real logs is implemented in Phase 3 via T054b/T041/T060.

**Staged Implementation Authorization**: Per Plan.md Section "Pipeline Validation", FR-006 ("capture and process actual VR interaction logs") and the scientific hypothesis validation (SC-002) are explicitly deferred to Phase 4. The tasks in this phase (T013-T018) are authorized to use **Simulation-Only** data with a known `ground_truth_effect` to validate the pipeline architecture and statistical engine. **Real data ingestion (T054b, T041) is defined in Phase 2 (Interface) and implemented in Phase 6.**

**Default Execution Mode**: `real`. The system defaults to using real data. To switch to `simulation` mode, `code/config.py` must be explicitly set to `DATA_MODE='simulation'`. If `DATA_MODE='real'`, the system MUST execute Phase 6 tasks; if Phase 6 fails, the run MUST halt with `DataFetchError` (no synthetic fallback).

**Independent Test**: The pipeline can be tested by running the ingestion and construction scripts against the synthetic data (via `--mode=simulation`) and verifying that the output CSV contains correctly merged rows, valid salience labels, and matches Gervais et al. norms. **Schema Requirement**: The output CSV MUST contain `gaze_metrics` (as a JSON string or structured column), `response_time`, `salience_level`, etc., matching spec.md US-1 Acceptance Scenario 1.

**⚠️ BLOCKING DEPENDENCY**: Phase 2 (T045, T046, T050, T055) must complete successfully before any Phase 3 task can execute.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation. These tasks define the interface for T013-T018 based on the schema defined in T014a-3.

- [X] T010 [P] [US1] Unit test for synthetic MFQ generator in `code/tests/test_ingest_mfq.py`. **Deliverable**: Function `test_mfq_distribution_matches_norms` that asserts `assert abs(mean - expected_mean) < 0.05` using values explicitly loaded from `data/config/gervais_norms.yaml`. **Verification**: Run `pytest code/tests/test_ingest_mfq.py::test_mfq_distribution_matches_norms`. **Dependency**: T007b must complete first.
- [X] T011 [P] [US1] Unit test for salience mapping logic in `code/tests/test_schema.py`. **Deliverable**: Function `test_salience_mapping_valid` that asserts `assert salience_level in ['low', 'high']` given mock story IDs.
- [X] T012 [US1] Unit test for psychometric norm validation in `code/tests/test_ingest_stories.py`. **Deliverable**: Function `test_psychometric_validity` using Kolmogorov-Smirnov test with p > 0.05 threshold against Gervais et al. norms. **Verification**: Run `pytest code/tests/test_ingest_stories.py::test_psychometric_validity` and confirm p-value > 0.05.

### Implementation for User Story 1 (Real Data First, Simulation for Testing)

**Note**: These tasks implement **Real Data Ingestion** as the default. The 'Simulation' path is a separate, opt-in configuration for local unit testing only, explicitly labeled as such. FR-001 and FR-006 (Real Data Ingestion) are implemented in this phase via T054b/T041.

- [X] T013 [US1] Implement `code/data/simulation_mfq.py` to generate synthetic MFQ data based on Gervais et al. multivariate normal distributions. **Validation**: The `ground_truth_effect` parameter must be validated against the MDES calculated in T045. **Pre-requisite Check**: **MUST** verify `state/mdes_report.yaml` exists and contains key `mdes_value` before execution. If missing, raise `FileNotFoundError: MDES report missing. Ensure T045 is complete.` **Dependency**: **Phase 2 (T045, T046) must complete first.** T045 is a blocking task and must finish before T013 starts. **[Simulation-Only, for Unit Tests]** **Config**: Use `GROUND_TRUTH_EFFECT` from `code/config.py` (loaded from `state/mdes_report.yaml`). **Validation Logic**: Assert `MDES < ground_truth_effect`. **Constraint**: If this assertion fails, the script MUST raise a `ValueError` and halt execution to ensure statistical rigor. **N Check**: Assert `N_simulated == 200`. **Verification**: Run script and confirm MDES check and N check pass.
- [X] T014 [US1] Implement `code/data/simulation_stories.py` to generate **Mock Data for Unit Tests Only** (not the main pipeline) Moral Stories and VR interaction logs (response times, `gaze_metrics`, judgment) with a known `ground_truth_effect` to proxy FR-006 requirements. **Constraint**: Must explicitly generate columns `response_time`, `gaze_metrics` (JSON string), `judgment_rating`. **Note**: This task generates **Mock/Simulation** data that mimics the real data schema; it is NOT real data and is NOT used in the main pipeline. **[Simulation-Only, for Unit Tests]** **Config**: Use `GROUND_TRUTH_EFFECT` from `code/config.py`. **Authorization**: This task is explicitly authorized by the "Staged Implementation Authorization" block in Plan.md. **Distribution**: Use Gaussian distribution for numeric columns. **Missingness**: Introduce a controlled proportion of intentional missing values in `gaze_metrics` and `response_time` using a fixed random seed for reproducibility. **Verification**: Run `df.isnull.sum` and confirm [deferred] missingness in critical columns.
- [X] T015 [US1] Implement `code/data/ingest.py` to load and merge real MFQ and Moral Stories datasets, handling ID mismatches and missing data. **Routing**: If `DATA_MODE='real'`, explicitly call `code/data/fetch_real.py` (Phase 6) and `code/data/parse_real_logs.py` (Phase 6) to fetch real data; otherwise, use simulation. **Constraint**: Must include a hard assertion that `DATA_MODE` is defined in `code/config.py`. If `DATA_MODE='real'` and Phase 6 tasks are incomplete, raise `NotImplementedError` immediately. **Note**: Real Data First (FR-006). **Deliverable**: Function `fetch_real_data() -> DataFrame` and error handling `raise DataFetchError`. **Dependency**: T013, T014 must complete first. **Verification**: Run `df.isnull().sum()` on the *final* merged CSV and assert 0 nulls in critical columns.
- [X] T016 [US1] Implement `code/data/preprocess.py` to map text stories to VR scenes, assigning `salience_level` (low/high) via blend-shape parameters. **Dependency**: Read configuration from `data/config/unity_blend_shapes.yaml` (T044) and use T016b for mapping logic. **Note**: Real Data First. **Sub-task**: Implement logging of VR mapping logs (story ID -> salience level) to `data/logs/vr_mapping.log` within this task. **Log Format**: CSV with columns `story_id`, `salience_level`, `blend_shape_params` (JSON string). **Delimiter**: Comma. **Constraint**: This log format MUST be invariant across simulation and real modes to preserve acceptance criteria. **Dependency**: Phase 2 (T044) must complete first. **Dependency**: T015 must complete first. **Deliverable**: `data/logs/vr_mapping.log` must be generated and non-empty. **Verification**: Ensure the output CSV contains the `salience_level` column with valid values ('low' or 'high').
- [X] T016b [US1] Implement `code/data/vr_mapping_logic.py` to implement the text-to-VR mapping logic using `data/config/unity_blend_shapes.yaml` as the verified source. **Deliverable**: A function `map_story_to_vr(story_id: str) -> dict` that returns the salience level and blend-shape parameters. **Authorization**: This task explicitly implements the mapping logic required by FR-006, distinguishing it from the static config file (T044). **Dependency**: T044 must complete first. **Verification**: Run unit tests to confirm correct mapping for all story IDs.
- [X] T017 [US1] Add validation logic to existing `code/utils/norms.py` to compare synthetic MFQ distribution against published norms (must be within 1 SD). **Dependency**: Must validate output of T013. **Statistical Test**: Use Kolmogorov-Smirnov test with a p-value threshold of > 0.05 to validate the distribution.
- [X] T018 [US1] Implement `code/utils/hashing.py` integration to checksum **simulation-derived** CSVs and update `state/artifact_hashes.yaml`. **Dependency**: T006 must complete first. **Constraint**: Hashing must be performed on the final, processed CSV files (e.g., `data/processed/simulated_data.csv`) immediately after generation, before any further processing. **Verification**: Confirm `state/artifact_hashes.yaml` contains the checksums for all generated CSVs.
- [X] T053 [P] [US1] **COMPLETED/MERGED**: This task's responsibilities have been merged into T056 to resolve the run-book vs implementation mismatch. The `code/data/simulation.py` entry point is now defined and implemented in T056.
- [X] T038 [P] [US1] Implement `code/data/unity_verification.py` to verify the simulation's fidelity to the actual Unity environment by validating blend-shape parameters against a reference configuration file. **Authorization**: This task replaces the Spec's assumption of a runnable Unity environment with a mock configuration, explicitly citing the "Staged Implementation Authorization" in `plan.md` as the authority for this substitution. **Deliverable**: A script that validates the `data/config/unity_blend_shapes.yaml` against the simulation logic, ensuring the mock configuration is reproducible.
- [X] T056 [US1] Implement `code/data/simulation.py` as the orchestration entry point for the simulation pipeline. **Deliverable**: A script that imports and executes `code/data/simulation_mfq.py`, `code/data/simulation_stories.py`, and `code/data/preprocess.py` in the correct order. **Verification**: Run `python code/data/simulation.py --mode=simulation` and confirm `data/processed/simulated_data.csv` is generated and non-empty. **Dependency**: T013, T014, T016 must complete first. **Note**: This task resolves the execution feedback error regarding the missing script and ensures US-1 is independently testable.
- [X] T060 [US1/US4] Implement `code/data/streaming_loader.py` to support **streaming** of large real datasets from HuggingFace or OSF if the full dataset exceeds memory limits, ensuring no synthetic fallback is used. **Deliverable**: A generator-based loader that processes data in chunks, accumulating statistics online, and explicitly documents the chunking strategy and sample size limits in the module's docstring if full streaming is not feasible. **Constraint**: Must raise `DataFetchError` if the real source is unreachable, never falling back to synthetic data. **Authorization**: This task addresses the "Large real datasets: STREAM the real data" rule, ensuring the pipeline can handle large datasets without fabrication. **Dependency**: T054b must complete first. **Note**: This task is critical for Phase 4 when real data is large and cannot fit in memory.
- [X] T061 [US1/US4] Implement `code/data/vr_mapping_logic.py` to implement the text-to-VR mapping logic using `data/config/unity_blend_shapes.yaml` as the verified source. **Deliverable**: A function `map_story_to_vr(story_id: str) -> dict` that returns the salience level and blend-shape parameters. **Authorization**: This task explicitly implements the mapping logic required by FR-006, distinguishing it from the static config file (T044). **Dependency**: T044 must complete first. **Verification**: Run unit tests to confirm correct mapping for all story IDs.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Bayesian Model Execution and Comparison (Priority: P2)

**Goal**: Execute a Bayesian decision model on the preprocessed data to estimate the effect of visual salience, validating parameter recovery and scientific evidence.

**Independent Test**: The model execution can be tested by running the PyMC3 script on the synthetic data and verifying that the model recovers the `ground_truth_effect` within the 95% credible interval and converges (R-hat < 1.05).

### Simulation Validation (US2)

- [X] T020 [P] [US2] Unit test for model convergence check in `code/tests/test_model_convergence.py`. **Deliverable**: Function `test_convergence_check` that asserts `assert r_hat < 1.05 ` given mock posterior samples.
- [X] T021 [US2] Unit test for parameter recovery validation in `code/tests/test_model_recovery.py`. **Deliverable**: Function `test_parameter_recovery` injecting `ground_truth_effect=0.5` and asserting recovery within 95% CI. **Verification**: Run `pytest code/tests/test_model_recovery.py::test_parameter_recovery` and confirm 0.5 is within the 95% CI.
- [X] T022 [US2] Implement `code/models/bayesian.py` defining the **Base PyMC Model Structure**: Gaussian likelihood, Normal priors for coefficients, foundation scores as covariates, salience as fixed-effect predictor. **Scope**: This task is strictly for the model definition (likelihood, priors, observed data). It does NOT include execution logic, convergence handling, or MLE fallback. **Dependency**: T051 (ModelResult Schema).
- [X] T023 [US2] Implement `code/models/bayesian.py` logic for **Schema Integration & Execution Flow**: Integrate the base model (T022) with `ModelResult` schema (T051), handle convergence checks, and implement the logic to flag inconclusive runs and calculate MLE fallback. **Deliverable**: The execution wrapper that calls the base model, checks R-hat, calculates MLE if needed, and prepares the `ModelResult` artifact. **Dependency**: T051 (ModelResult Schema) and T022 (Model Definition). **Prerequisite**: Phase 2 must be fully completed (including T051) before Phase 4 implementation tasks can begin. **Verification**: Ensure `code/utils/schemas.py` is importable and contains the `ModelResult` definition before execution. **Sub-task 1**: Integrate schema. **Sub-task 2**: Handle convergence. **Sub-task 3**: Calculate MLE if inconclusive. **Verification**: Run model with forced failure and assert `ModelResult` artifact contains `is_inconclusive=True` and `mle_fallback` value.
- [X] T026 [US2] Implement `code/analysis/validation.py` to verify **Parameter Recovery**: check if `ground_truth_effect` is within the credible interval of the posterior (Primary Validation Metric)

### Model Comparison (US2)

- [X] T024 [US2] Implement `code/analysis/model_comparison.py` to calculate AIC and WAIC for the salience-augmented model vs. baseline (no salience)
- [X] T025 [US2] Implement `code/analysis/model_comparison.py` to perform Posterior Predictive Checks (PPC): generate synthetic data from the posterior, compare distributions to observed data, and produce a visual plot (histogram/KDE) of observed vs. generated data. **Deliverable**: A plot and a quantitative metric (e.g., KS-test p-value) for the PPC.
- [X] T027a [US2] Implement `code/analysis/model_comparison.py` to explicitly calculate and report ΔAIC and ΔWAIC metrics. **Requirement**: Always calculate and report ΔAIC. **Log Format**: `LOG: Metric Calculation: ΔAIC={val}, ΔWAIC={val}`. **Dependency**: T024 must complete first. **Note**: This task ensures the metric is calculated regardless of mode; claim logic is handled in T027b.
- [X] T027b [US2] Implement `code/analysis/model_comparison.py` logic to evaluate the ΔAIC > 10 threshold and report a definitive Pass/Fail/Inconclusive outcome for SC-002. **Requirement**: If `DATA_MODE='simulation'`, log `LOG: Scientific Metric: Calculated (ΔAIC={val}) - Report Outcome: Inconclusive (Simulation Mode)`. If `DATA_MODE='real'`, flag 'strong evidence' if ΔAIC > 10 and report 'Pass'. **Deliverable**: A report explicitly stating 'Condition Met: True/False/Inconclusive' for SC-002 (ΔAIC > 10) in both modes. **Verification**: Run `pytest code/tests/test_model_comparison.py::test_delta_aic_threshold_logic` to verify the capability. **Dependency**: T027a must complete first.
- [X] T027b-test [US2] Unit test for ΔAIC threshold logic in `code/tests/test_model_comparison.py`. **Deliverable**: Function `test_delta_aic_threshold_logic` that mocks a 'real' data scenario with ΔAIC > 10 and asserts that the system correctly flags 'strong evidence' and does not defer the claim. **Verification**: Run `pytest code/tests/test_model_comparison.py::test_delta_aic_threshold_logic`. **Dependency**: T027b must complete first.

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
- [X] T031 [US3] Implement `code/analysis/validation.py` to apply Bonferroni correction to interaction term p-values. **Verification**: Compare corrected p-values against manual calculation and assert match.
- [X] T032 [US3] Implement `code/analysis/validation.py` to conduct sensitivity analysis sweeping decision thresholds over a range of values and report model selection stability matrix. **Constraint**: Must explicitly use {2, 10, 20} as per FR-005. **Output**: Stability matrix CSV. **Verification**: Run script and confirm CSV is generated with correct structure containing these specific thresholds. **Note**: This task explicitly implements the sensitivity analysis required by FR-005.
- [X] T033 [US3] Implement `code/reports/generate_report.py` to generate the final report summarizing findings (Pipeline Validation: PASSED/FAILED)
- [X] T034 [US3] Ensure `code/reports/generate_report.py` explicitly states "Pipeline Validation Only" while including a clear statement of findings regarding the hypothesis (as per US-3), deferring final scientific claims to Phase 4 by noting **"Evidence strength (ΔAIC) calculated but claim deferred per Phase 3 Staged Implementation."**

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: User Story 4 - Real Data Integration (Priority: P4 - Active Implementation of Pipeline)

**Goal**: Implement the ingestion of real VR interaction logs and a verified "Moral Stories" dataset when available. **Active Implementation**: The tasks in this phase (T054b, T041, T042, T054d) are actively implemented to build the *capability* for real data ingestion. The *scientific hypothesis validation* (US-4) is deferred until real data is available.

- [X] T054b [US1/US4] Implement `code/data/fetch_real.py` with strict "Fail Loudly" logic: attempt to fetch real MFQ data from OSF and real Moral Stories from HuggingFace; if fetch fails, raise a `DataFetchError` immediately without falling back to synthetic generators. **Deliverable**: A robust fetcher that halts execution on network/source failure, ensuring no synthetic data is used when real data is expected. **Implementation Detail**: Use `OSF_API_URL` from T050 and explicitly implement the OSF endpoint path (`/v2/nodes/{node_id}/files/osfstorage`) with required query parameters and response schema validation. **Trigger**: Only execute if `DATA_MODE='real'`. **Authorization**: This task implements the 'Fail Loudly' path required by FR-006 when `DATA_MODE='real'`, ensuring no fabrication occurs. **Dependency**: T050 must complete first. **Note**: This task is the *Fetcher* only. Parsing is handled by T041 in Phase 6. **Phase**: Moved from Phase 3 to Phase 6 to align with Real Data Integration.
- [X] T041 [US4-Real] Implement `code/data/parse_real_logs.py` to parse real VR interaction logs from a specified CSV/JSON source and validate against the schema defined in T050. **Deliverable**: A parser that validates real data structure and raises `SchemaError` if real data is malformed, preventing silent data corruption. **Implementation Detail**: Explicitly implement the logic to extract response times, gaze metrics, and judgment ratings from the raw VR log format into the structured schema. **Trigger**: Only execute if `DATA_MODE='real'`. **Note**: This task handles missing data gracefully by excluding affected participants, as per Spec Edge Cases. **Dependency**: T054b (Real Data Fetcher) must complete first. **File Ownership**: This task owns `code/data/parse_real_logs.py` (distinct from T054b's `fetch_real.py`). **Verification**: Run on sample real data and assert schema compliance.
- [X] T042 [US4-Real] Implement end-to-end execution of the Real Data Pipeline. **Deliverable**: A script `code/run_real_data_pipeline.py` that orchestrates T054b (fetch), T041 (parse), T016 (preprocess), and T018 (hashing) when `DATA_MODE='real'`. **Verification**: Run `python code/run_real_data_pipeline.py --mode=real` and verify `data/processed/real_data.csv` is generated with correct schema and no nulls. **Dependency**: T054b, T041, T016 must complete first. **Authorization**: This task ensures FR-006 is not just defined but actively tested and executed.
- [X] T054c [US1/US4] Verify VR mapping with real data: Run `code/data/preprocess.py` (T016) with real data (from T041) and verify that `data/logs/vr_mapping.log` is generated with the correct CSV format (columns: `story_id`, `salience_level`, `blend_shape_params`). **Deliverable**: A verification script or pytest test that asserts the log file exists and contains the expected columns. **Dependency**: T016 and T041 must complete first. **Verification**: Run `pytest code/tests/test_real_data_mapping.py` (to be created as part of this task) which asserts `assert 'story_id' in df.columns` and `assert 'salience_level' in df.columns`.
- [X] T054d [US1/US4] End-to-End Real Data Integration Test: Implement and run an integration test that fetches real data (T054b), parses it (T041), preprocesses it (T016), and validates the output against the spec's acceptance criteria (US-1, Scenario 1). **Deliverable**: A pytest test `test_real_data_pipeline_end_to_end` that asserts the pipeline produces a valid CSV with no nulls and correct salience labels. **Dependency**: T054b, T041, T016 must complete first. **Authorization**: This task ensures FR-006 is not just defined but actively tested.

**Checkpoint**: Real data path is fully implemented and verified

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T004a [P] Create `.gitignore` with specific patterns: `data/raw/*`, `data/processed/*`, `*.pyc`, `__cache__/`, `state/*.yaml`. **Verification**: Run `git status` and confirm no untracked data files are listed.
- [X] T004b [P] Create `.github/workflows/ci.yml` with specific steps: install dependencies, run tests, run linting. **Verification**: Run `act` locally and confirm the workflow executes successfully.
- [X] T035 [P] Documentation updates: Add installation instructions, update usage examples, and add data schema reference in `README.md` and `docs/`
- [X] T036a [P] Code cleanup: Remove unused imports from all Python files in `code/`. **Verification**: Run `ruff check code/` and ensure no unused import warnings.
- [X] T036b [P] Code cleanup: Enforce black formatting on all Python files in `code/`. **Verification**: Run `black --check code/` and ensure no formatting errors.
- [X] T037 [P] Implement CPU-only performance profiling in `code/analysis/profile_pipeline.py` to guarantee full pipeline execution completes within the CI limit on the free-tier runner (limited cores, constrained RAM). **Success Criterion**: Record pipeline runtime in `state/perf_metrics.yaml` and validate against the established time threshold.
- [X] T039 [P] Additional unit tests for edge cases: Implement specific tests for (1) missing data handling in ingestion (`test_missing_data_handling`), (2) convergence failure in Bayesian model (`test_convergence_failure`), and (3) invalid schema in preprocessing (`test_invalid_schema`). **Deliverable**: `code/tests/test_edge_cases.py` with passing tests for each scenario, including specific input fixtures and expected exceptions.
- [X] T040 [P] Run `quickstart.md` validation and verify all artifacts are checksummed. **Execution**: Execute `python -m code.quickstart` and verify `state/artifact_hashes.yaml` contains non-empty `artifact_hashes`. **Verification**: Run command and confirm hash map is non-empty.
- [X] T060 [P] [US1/US4] Implement `code/data/streaming_loader.py` to support **streaming** of large real datasets from HuggingFace or OSF if the full dataset exceeds memory limits, ensuring no synthetic fallback is used. **Deliverable**: A generator-based loader that processes data in chunks, accumulating statistics online, and explicitly documents the chunking strategy and sample size limits in the module's docstring if full streaming is not feasible. **Constraint**: Must raise `DataFetchError` if the real source is unreachable, never falling back to synthetic data. **Authorization**: This task addresses the "Large real datasets: STREAM the real data" rule, ensuring the pipeline can handle large datasets without fabrication. **Dependency**: T054b must complete first. **Note**: This task is critical for Phase 4 when real data is large and cannot fit in memory.

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
- All Foundational tasks marked [P] can run in parallel (within Phase 2, excluding T045/T046/T055 which are sequential)
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
3. Complete Phase 3: User Story 1 (Real Data Ingestion & Validation)
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
- **Critical Constraint**: All modeling must run on CPU-only CI (no CUDA, no 8-bit quantization). Use default precision (floating-point).
- **Data Integrity**: Synthetic data must have a known `ground_truth_effect` to validate the pipeline; real data ingestion (T041) is deferred to Phase 6 and gated by `DATA_MODE`.
- **Performance Constraint**: T037 must ensure the full pipeline (ingestion → modeling → reporting) completes within 6 hours on the free-tier CPU runner.
- **Simulation-Only Override**: T013-T018 are explicitly marked "Simulation-Only" as FR-006 (Real VR Logs) is deferred to Phase 6, authorized by the "Staged Implementation Authorization" block in Phase 3.
- **Revision Concern**: The current plan relies on a "Simulated" Moral Stories dataset and OSF MFQ fetch stubs. While valid for pipeline validation, the spec requires a **Real Data** ingestion path (FR-001, FR-006) that does not fall back to synthetic data. T054b (moved to Phase 6) defines the interface and implements the **Real Data Fetcher** with strict "Fail Loudly" semantics, ensuring that if real data is unavailable, the pipeline halts rather than substituting fake data, satisfying the "No Fabrication" rule. T041 (Phase 6) implements the **Parser** for real data, resolving the file ownership conflict.
- **Revision Concern**: The spec assumes Unity VR scene accessibility for blend-shape mapping. T044 addresses the gap by creating a **Mock Unity Configuration** task that defines the exact JSON schema for blend-shape parameters, ensuring the simulation logic (T016) is grounded in a defined, reproducible configuration rather than an assumed runtime environment.
- **Revision Concern**: The sensitivity analysis (T032) currently sweeps thresholds but lacks a formal **Power Analysis** task to justify the sample size (N=200) for the planned mixed-effects regression. T045 adds a task to compute the minimum detectable effect size for N=200, ensuring the simulation is statistically powered to recover the `ground_truth_effect`.
- **Revision Concern**: T025 contained a placeholder. Replaced with concrete PPC implementation steps.
- **Revision Concern**: T016a was marked rejected. Updated to be an active task for logging VR mapping logs (merged into T016).
- **Revision Concern**: T051 added to define `ModelResult` schema before implementation.
- **Revision Concern**: T052 removed to eliminate redundant scope documentation (plan.md already defines the override).
- **Revision Concern**: T004 was rejected. Replaced with T004a/T004b with specific deliverables and verification steps.
- **Revision Concern**: T043 was misplaced. Moved to Phase 2 to ensure configuration is available before routing logic.
- **Revision Concern**: T053 was a decision task. Converted to an implementation task to create the missing `code/data/simulation.py` script. **Moved from Phase 2 to Phase 3** to resolve dependency ordering. **Status**: Completed/Merged into T056.
- **Revision Concern**: T041 was marked [P]. Removed [P] flag and added explicit dependency on T043 and T050.
- **Revision Concern**: T013 relied on runtime check. Added structural dependency (T045 first) and explicit pre-requisite check.
- **Revision Concern**: T015a/T016 were truncated. Updated with full logging logic and schema. **Merged T015a into T015**.
- **Revision Concern**: T023 was split into T023 and T023b to isolate MLE logic for atomic execution.
- **Revision Concern**: T022 and T023 scopes clarified to avoid redundancy. T022 is base model definition; T023 is execution and schema integration.
- **Revision Concern**: T055 added to Phase 2 to explicitly verify schema equivalence between simulation and real data paths, ensuring FR-006 is structurally satisfied.
- **Revision Concern**: T046 added to Phase 2 to validate simulated N matches MDES assumption.
- **Revision Concern**: T054/T041 file conflict resolved by splitting into `fetch_real.py` (T054b) and `parse_real_logs.py` (T041). Added T054d for end-to-end testing.
- **Revision Concern**: T027 updated to include explicit verification of ΔAIC > 10 capability via T027b.
- **Revision Concern**: T027 split into T027a (calculation) and T027b (threshold logic) to ensure metric is always computed.
- **Revision Concern**: T042 added to Phase 6 to orchestrate the full real-data pipeline, ensuring the real path is actively tested.
- **Revision Concern**: T056 added to Phase 3 to explicitly create the missing `code/data/simulation.py` script referenced in the quickstart run-book, resolving the execution feedback error regarding the missing script.
- [X] T060 [US1/US4] **New Task**: Implement `code/data/streaming_loader.py` to support **streaming** of large real datasets from HuggingFace or OSF if the full dataset exceeds memory limits, ensuring no synthetic fallback is used. **Deliverable**: A generator-based loader that processes data in chunks, accumulating statistics online, and explicitly documents the chunking strategy and sample size limits in the module's docstring if full streaming is not feasible. **Constraint**: Must raise `DataFetchError` if the real source is unreachable, never falling back to synthetic data. **Authorization**: This task addresses the "Large real datasets: STREAM the real data" rule, ensuring the pipeline can handle large datasets without fabrication. **Dependency**: T054b must complete first. **Note**: This task is critical for Phase 4 when real data is large and cannot fit in memory.

<!-- auto-added by the execution fix loop: run-book / implementation path mismatch (a quickstart command names a script no task created) -->
<!-- RESOLVED: T053 merged into T056. T056 updated with explicit verification command. -->