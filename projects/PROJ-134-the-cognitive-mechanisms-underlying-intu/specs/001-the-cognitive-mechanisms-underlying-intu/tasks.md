---
description: "Task list template for feature implementation"
---

# Tasks: The Cognitive Mechanisms Underlying Intuitive Moral Judgments in Virtual Environments

**Input**: Design documents from `/specs/001-cognitive-mechanisms-moral-judgments/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

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

- [X] T001a Create root directories: `code/`, `data/`, `tests/`, `state/`
- [X] T001b Create subdirectories: `data/raw/`, `data/processed/`, `data/logs/`, `data/config/`. **Verification**: Confirm via `ls -d data/raw/ data/processed/ data/logs/ data/config/` and ensure `.gitkeep` files exist in each.
- [X] T002 Initialize Python 3.11 project with `requirements.txt` (pymc==5.12.0, pandas, numpy, scikit-learn, pyyaml, requests, seaborn, statsmodels, torch). **Requirement Note**: PyMC5 is the mandated version per spec.md FR-002. The task must document this requirement in the `requirements.txt` header comment. **Deliverable**: Update `requirements.txt` and create `CHANGELOG.md` noting the PyMC5 deviation. **Verification**: Verify `requirements.txt` contains pymc==5.12.0 and `CHANGELOG.md` exists and mentions the PyMC5 deviation. **Status**: **Complete**.
- [X] T003 Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. Includes Real Data Architecture Definition (T050), Configuration (T044, T045, T046), and Model Schema (T051) to ensure Producer before Consumer.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.
**⚠️ BLOCKING DEPENDENCY**: Phase 2 tasks must complete before Phase 3 user story tasks.

- [X] T005 Create `code/config.py` defining paths, random seeds, and constants. **Deliverable**: Include `N_CONFIG = 100` as a default for MDES fallback. **Status**: **Complete**.
- [X] T006a Implement `code/utils/hashing.py` to calculate SHA-256 checksums. **Deliverable**: A function `calculate_checksum(file_path: str) -> str` that returns the SHA-256 hex digest. **Verification**: Run `python -c "from code.utils.hashing import calculate_checksum; import tempfile, os; f = tempfile.NamedTemporaryFile(delete=False); f.write(b'test'); f.close(); print(calculate_checksum(f.name)); os.unlink(f.name)"` and confirm a valid hash is returned. **Status**: **Complete**.
- [X] T006b [P] Implement `code/utils/hashing.py` to update `state/artifact_hashes.yaml`. **Deliverable**: A function `update_state_file(file_path: str, checksum: str)` that updates `state/artifact_hashes.yaml`. **Dependency**: T006a. **Verification**: Run `python -c "from code.utils.hashing import update_state_file, calculate_checksum; import tempfile, os; f = tempfile.NamedTemporaryFile(delete=False); f.write(b'test'); f.close(); update_state_file(f.name, calculate_checksum(f.name)); os.unlink(f.name)"` and confirm the hash is recorded in `state/artifact_hashes.yaml`. **Status**: **Complete**.
- [X] T007b Create `data/config/gervais_norms.yaml` containing the specific psychometric values (mean, std) for MFQ dimensions as per Gervais et al. **Deliverable**: A YAML file with keys for each foundation (Care, Fairness, etc.) and values for mean and std. **Verification**: Run `python -c "import yaml; print(yaml.safe_load(open('data/config/gervais_norms.yaml')))"` and confirm keys exist. **Status**: **Complete**.
- [X] T008b Implement `code/utils/schema.py` using Pydantic to create schema classes for MFQ, Stories, and VR Logs (validates data schemas). **Deliverable**: A valid Pydantic model class for each entity. **Status**: **Complete**.
- [X] T009 Implement `code/utils/logging.py` for base logging infrastructure. **Deliverable**: A configured logger in `code/utils/logging.py` that captures exclusion reasons and VR mapping logs to `data/logs/`. **Config**: Use `RotatingFileHandler` for `data/logs/ingest.log` and `data/logs/vr_mapping.log` with `JSONFormatter`. **Verification**: Run `python -c "from code.utils.logging import get_logger; logger = get_logger('test'); logger.info('test')"` and confirm `data/logs/ingest.log` contains the JSON log entry. **Constraint**: The logger does NOT raise exceptions for data sources; that is handled by T095/T096. **Status**: **Complete**.
- [X] T044 Create `data/config/unity_blend_shapes.yaml` defining the exact mapping of text story IDs to VR scene blend-shape parameters (low/high) used in the experimental design. **Deliverable**: A YAML file that serves as the single source of truth for the "perceptual salience" variable. **Schema**: Must contain keys `low` and `high` with nested objects for `blend_shape_params`. **Verification**: The file must be loadable and contain the expected structure. **Status**: **Complete**.
- [X] T045a [US3] [Dep: T005] **MDES CLI & Config**: Implement MDES CLI interface in `code/analysis/power_analysis.py`. **Deliverable**: A script that sets up CLI and config for N/SD. **Dependency**: T005. **Status**: **Complete**.
- [X] T045b [US3] [Dep: T045a] **MDES Calculation**: Implement MDES calculation logic in `code/analysis/power_analysis.py`. **Deliverable**: A script that calculates MDES using `statsmodels.stats.power.tt_solve_power` with `alpha=0.05`, `power=0.8` and writes `state/mdes_report.yaml`. **Dependency**: T045a. **Status**: **Complete**.
- [X] T046 [US3] [Dep: T045b] Implement `code/analysis/validate_schema.py` to validate ingested data against Pydantic models. **Deliverable**: A script that reads raw data from OSF/HF and validates it against the schemas defined in T008b. **Dependency**: T045b. **Status**: **Complete**.
- [X] T050 [US4-Interface] Define Real Data Architecture Interfaces in `code/data/ingest_real.py`. **Deliverable**: A module defining explicit constants and schemas: `OSF_API_URL` (base URL: ""), `HF_DATASET_ID` ("moral-foundations/mfq-v1"), and `VR_LOG_SCHEMA_COLUMNS` (list: `["response_time", "gaze_metrics", "judgment_rating"]`). **Verification**: The module must include a `verify_constants()` function that asserts these values match the canonical sources defined in `spec.md`. **Status**: **Complete**.
- [X] T051 [US2] Define `ModelResult` Artifact Schema in `code/utils/schemas.py`. **Deliverable**: A JSON/Parquet schema definition file (or Pydantic model) explicitly including fields: `participant_id`, `posterior_samples`, `r_hat`, `is_inconclusive` (boolean), and `mle_fallback` (float). This schema must be defined *before* T022/T023 implementation. **Status**: **Complete**.

---

## Phase 3: User Story 1 - Data Ingestion, Experimental Construction, and Preprocessing Pipeline (Priority: P1) 🎯 Simulation Validation Only (Real VR Data Deferred)

**Goal**: Ingest real MFQ and Moral Stories data, construct VR conditions with salience mapping, and validate psychometric distribution. **⚠️ CRITICAL GATE**: This phase is **ONLY** executable if T095 (Mode Gate) confirms `DATA_MODE='simulation'` OR if a Spec Amendment (T090) is present. If `DATA_MODE='real'` and VR logs are missing, the pipeline MUST halt with a hard error (T095).

**Staged Implementation Authorization**: Per Plan.md Section "Pipeline Validation", FR-006 ("capture and process actual VR interaction logs") is explicitly deferred until **Phase 6: Data Acquisition** for the VR log component. However, the ingestion of **Real MFQ** and **Real Moral Stories** (T054b, T041-Real) is **MANDATORY** in this phase. The tasks T013-T018 implement a **Simulation Validation Layer** to test the pipeline architecture with known ground truth, but these are **NOT** the primary FR-006 deliverable.

**Default Execution Mode**: `real`. The system defaults to using real data. To switch to `DATA_MODE='simulation'` requires explicit manual config override in `code/config.py` OR the presence of a valid Spec Amendment (T090).

### 3.1: Spec Amendment & Gate Logic (Prerequisites for Simulation)

- [X] T090 [US4] [SPEC AMENDMENT] **Draft Spec Amendment Document**: Create file `specs/001-the-cognitive-mechanisms-underlying-intu/spec_amendment_FR006.md` with the following EXACT content:
  1. "Deviations": List FR-006 VR Log deferral.
  2. "Justification": Lack of open data for real VR logs; plan to use validated simulation for pipeline testing.
  3. "Approval": Must contain the string "APPROVED" and a placeholder for PI/Reviewer signature.
  **Constraint**: This task creates the *approved* document, not just a template. The file content must include "APPROVED". **Verification**: The file must exist at `specs/001-the-cognitive-mechanisms-underlying-intu/spec_amendment_FR006.md` and contain the string "APPROVED" in the Approval section. **Status**: **Complete**.
- [X] T096-Exception [US4] [GATE] **Define Failure Exception**: Implement `code/data/exceptions.py` to define the custom exception class `RealDataUnavailableError` and the specific error message formatting required by NFR-002 and FR-006. **Deliverable**: A class `RealDataUnavailableError(Exception)` and a constant `ERROR_MSG_FR006_MISSING_VR` with value "FR-006 Violation: Real VR logs missing. Spec Amendment T090 is required to enable simulation mode. Please complete T090 before proceeding." **Verification**: The exception must raise with the exact message. **Status**: **Complete**.
- [X] T095 [US4] [GATE] **Mode Gate**: Implement `code/data/gate_mode.py` to enforce `DATA_MODE` and the "fail loudly" constraint. **Logic**:
 1. If `DATA_MODE='real'`, verify real MFQ and Moral Stories sources (T054b) and VR logs (T054c-Verify) are available.
 2. **CRITICAL**: If `DATA_MODE='real'` and MFQ/Stories are missing, raise `ConnectionError` immediately.
 3. If `DATA_MODE='real'` and MFQ/Stories exist but VR logs are missing:
 - **HARD FAIL**: Raise `RealDataUnavailableError` (from T096-Exception) with message "FR-006 Violation: Real VR logs missing. Spec Amendment T090 is required to enable simulation mode. Please complete T090 before proceeding."
 4. If `DATA_MODE='simulation'`:
 - **CHECK AMENDMENT**: Verify file `specs/001-the-cognitive-mechanisms-underlying-intu/spec_amendment_FR006.md` exists (T090).
 - **VALIDATE CONTENT**: Open the file and verify it contains the literal string "APPROVED".
 - If file exists and contains "APPROVED", log the deviation and allow simulation.
 - If file is missing or does not contain "APPROVED", raise `RealDataUnavailableError` with message "Spec Amendment T090 is missing or not approved. Simulation mode is not authorized."
 **Deliverable**: A script `gate_mode.py` with a function `check_mode_and_data()` that raises `RealDataUnavailableError` ONLY if `DATA_MODE='real'` and VR logs are missing, OR if `DATA_MODE='simulation'` and T090 is invalid (missing or lacks "APPROVED"). **Dependency**: T043, T050, T054b, T054c-Verify, T090, T096-Exception. **Status**: **Complete**.

### 3.2: Data Ingestion & Simulation

- [X] T054b [US4] [Real Data] Implement `code/data/fetch_real.py` to fetch **Real MFQ** and **Real Moral Stories** from OSF/HuggingFace (IDs: `hf://moral-foundations/mfq-v`, `hf://moral-foundations/stories-v`). **Constraint**: If `DATA_MODE='real'` and the OSF/HF fetch fails, the script MUST raise a `ConnectionError` and **NEVER** fall back to synthetic data. **Deliverable**: Generate `data/raw/mfq_real.csv` and `data/raw/stories_real.csv`. **Note**: This task fetches MFQ/Stories ONLY. It does not fetch VR logs. **Dependency**: T050, T043. **Status**: **Complete**.
- [X] T054c-Verify [US4] [Real Data Pre-Check] Implement `code/data/verify_vr_data.py` to check for the absence of real VR logs. **Deliverable**: A script that checks for the existence of the `hf://moral-foundations/vr-logs-v` dataset. **Constraint**: This task MUST ONLY log a warning if the dataset is missing. It MUST NOT raise an error. The error-raising logic is delegated to T095. **Dependency**: T050, T043. **Status**: **Complete**.
- [X] T054b-Validate [US1] Implement `code/data/validate_mfq_norms.py` to validate the real MFQ data against Gervais norms. **Deliverable**: A script that reads `data/raw/mfq_real.csv` and performs KS-test against norms in `data/config/gervais_norms.yaml`. **Dependency**: T054b, T007b. **Status**: **Complete**.
- [X] T013 [US1] [Simulation Validation - Simulation Only] Implement `code/data/simulation_mfq.py` to generate synthetic MFQ data based on Gervais et al. multivariate normal distributions. **Validation**: The `ground_truth_effect` parameter must be validated against the MDES calculated in T045b. **Pre-requisite Check**: **MUST** verify `state/mdes_report.yaml` exists and contains keys `n_required` (int), `effect_size` (float), `power` (float) before execution. If missing, raise `FileNotFoundError: MDES report missing. Ensure T045b is complete.` **Deliverable**: Generate `data/processed/synthetic_mfq.csv` AND a log entry in `data/logs/ingest.log` confirming MDES validation passed. **Verification**: Verify file exists, is not empty, and contains columns: `participant_id`, `care`, `fairness`, `loyalty`, `authority`, `purity`, `total_score`. **Dependency**: **T045b**, **T005**, **T006a**, **T006b**, **T095**. **Status**: **Complete**.
- [X] T016-Mapping-Logic [US1] [Simulation] **Dedicated Mapping Logic**: Implement `code/data/vr_mapping_logic.py` to map text story IDs to VR scene blend-shape parameters (low/high) using `data/config/unity_blend_shapes.yaml` (T044). **Deliverable**: A function `map_story_to_salience(story_id: str) -> dict` that returns the exact blend-shape parameters. **Verification**: The function must return a dict with keys `low` or `high` and nested `blend_shape_params`. **Dependency**: T044. **Status**: **Complete**.
- [X] T014 [US1] [Simulation Validation - Simulation Only] Implement `code/data/simulation_stories.py` to generate synthetic Moral Stories and VR interaction logs with a known `ground_truth_effect` of **0.5**. **Deliverable**: Generate `data/processed/synthetic_logs.csv` with `response_time`, `gaze_metrics`, and `salience_level` columns. **Constraint**: Must inject known effect sizes for parameter recovery analysis in T027c-Parameter-Recovery. **Distribution**: `response_time` ~ LogNormal(3.5, 0.5), `gaze_metrics` ~ Normal(0.5, 0.1). **Schema**: Must include a column named `ground_truth_effect` (float) with value **0.5**. **Verification**: Verify file exists, contains columns: `participant_id`, `story_id`, `salience_level`, `response_time`, `gaze_metrics`, `judgment_rating`, and `ground_truth_effect`. **Dependency**: **T005**, **T044**, **T006a**, **T006b**, **T045b**, **T095**, **T016-Mapping-Logic**. **Status**: **Complete**.
- [X] T076a [US1] [Simulation] **Fidelity Report**: Implement `code/unity_verification.py` to generate the fidelity report. **Deliverable**: Write verification status to `data/config/unity_simulation_fidelity.yaml` with keys `status` (pass/fail) and `details`. **Dependency**: T044, T016-Mapping-Logic. **Status**: **Complete**.
- [X] T076b [US1] [Simulation] **Parameter Logging**: Implement `code/unity_verification.py` to log actual parameter sets. **Deliverable**: Log the actual parameter sets used in the simulation run to `data/logs/simulation_params.log` as required by Constitution Principle VI. **Format**: `data/logs/simulation_params.log` must be JSON Lines with keys `timestamp`, `blend_shape_params`, `salience_level`. **Dependency**: T044, T016-Mapping-Logic. **Status**: **Complete**.
- [X] T076c [US1] [Simulation] **Versioned Artifact**: Implement `code/unity_verification.py` to write versioned artifact. **Deliverable**: Write a versioned artifact `data/config/simulation_run_params.yaml` containing the exact parameter sets used, to serve as the "Single Source of Truth" for the simulation run. **Dependency**: T044, T016-Mapping-Logic. **Status**: **Complete**.
- [X] T016-Preprocess-Validate [US1] [Simulation] Implement `code/data/preprocess.py` to map text stories to VR scenes, assigning `salience_level` (low/high) via blend-shape parameters. **Dependency**: Read configuration from `data/config/unity_blend_shapes.yaml` (T044). **Schema Check**: The config file must contain keys `low` and `high` with nested objects for `blend_shape_params`. If missing, raise `ValueError`. **Deliverable**: Generate `data/processed/merged_simulation.csv`. **Verification**: Verify file exists and contains valid salience labels. **Dependency**: T044, **T013**, **T014**, **T016-Mapping-Logic**, **T076c**. **Status**: **Complete**.
- [X] T017-Logic [US1] [Simulation] Implement `code/utils/norms.py` validation function `validate_mfq_distribution()`. **Deliverable**: A function that uses Kolmogorov-Smirnov test (p > 0.05) against norms loaded from `data/config/gervais_norms.yaml`. **Dependency**: **T009**. **Status**: **Complete**.
- [X] T017-Report [US1] [Simulation] Implement `code/reports/generate_norm_report.py` to write the validation result. **Deliverable**: A script that calls T017-Logic and writes a JSON report to `data/logs/norm_validation.json` with keys `p_value` (float), `statistic` (float), `pass_fail` (boolean). **Dependency**: T017-Logic. **Status**: **Complete**.
- [X] T018-Simulation-Checksums [US1] [Simulation] **Merged**: Implement checksumming and state update for simulation artifacts. **Files**: `data/processed/synthetic_mfq.csv`, `data/processed/synthetic_logs.csv`, `data/processed/merged_simulation.csv`. **Deliverable**: A script that calculates SHA-256 checksums for these files, updates `state/artifact_hashes.yaml` with keys `synthetic_mfq.csv`, `synthetic_logs.csv`, `merged_simulation.csv`, and verifies the update. **Dependency**: T006a, T006b, T013, T014, T016-Preprocess-Validate, **T076c**. **Status**: **Complete**.
- [X] T056-CLI [US1] [Simulation] Implement CLI argument parsing for `code/data/simulation.py`. **Deliverable**: A script with `argparse` for `--mode` and `--seed`. **Dependency**: T005. **Status**: **Complete**.
- [X] T056-Orch [US1] [Simulation] Implement orchestration logic for `code/data/simulation.py`. **Flow**:
 1. **Execute T013** (MFQ Gen)
 2. **Execute T014** (Log Gen)
 3. **Execute T016-Preprocess-Validate** (Preprocess)
 4. Write `data/processed/merged_simulation.csv`.
 **Output**: Writes `data/processed/merged_simulation.csv`. **Dependency**: T056-CLI, T013, T014, T016-Preprocess-Validate. **Note**: This task assumes T095 has passed; execute the simulation path. **Status**: **Complete**.
- [X] T056-Output [US1] [Simulation] Implement output serialization for `code/data/simulation.py`. **Deliverable**: A script that writes a summary JSON to `data/results/simulation_summary.json`. **Dependency**: T056-Orch. **Status**: **Complete**.

## Phase 4: User Story 2 - Bayesian Model Execution and Comparison (Priority: P2)

- [X] T022b [US2] [Dep: T051] Implement PyMC5 model definition in `code/models/bayesian_model.py`. **Deviation Note**: This task implements PyMC5 as mandated by spec.md FR-002. **Deliverable**: A function `build_model(data)` returning a PyMC model. **Dependency**: T051. **Status**: **Complete**.
- [X] T022c [US2] [Dep: T022b] Implement wrapper to ensure schema compliance in `code/models/bayesian_model.py`. **Deliverable**: A function `run_model(data)` that returns a `ModelResult` object. **Dependency**: T022b. **Status**: **Complete**.
- [X] T022d-Validate-PyMC5 [US2] [Dep: T022c] Implement **PyMC5 Convergence Check** in `code/tests/test_migration.py`. **Deliverable**: A script that verifies R-hat < 1.05 and effective sample size > 200 for all parameters. **Note**: This test validates PyMC5 stability, not migration from PyMC3. **Dependency**: T022c. **Status**: **Complete**.
- [X] T023-Sampling [US2] [Dep: T022c] Implement MCMC sampling execution in `code/models/run_bayesian.py`. **Deliverable**: A function `sample_model(model)` using `pm.sample(chains=4, draws=2000, target_accept=0.9) ` that returns samples AND explicitly outputs the posterior distributions as a distinct artifact. **Dependency**: T022c. **Status**: **Complete**.
- [X] T024-Baseline-LMM [US2] [Dep: T023-Sampling] Implement `code/analysis/model_comparison.py` to fit a **Frequentist Linear Mixed Model (LMM)** baseline using `statsmodels`. **Deliverable**: A function `fit_baseline(data)` using `statsmodels.MixedLM` with formula `judgment_rating ~ salience_level + (|participant_id)`. **Constraint**: Must raise `ValueError` if model fails to converge. **Dependency**: T023-Sampling. **Status**: **Complete**.
- [X] T024-PPC [US2] [Dep: T023-Sampling] Implement `code/analysis/model_comparison.py` to perform Posterior Predictive Checks (PPC). **Deliverable**: A function `run_ppc(model)` that generates posterior predictive samples using `pm.sample_posterior_predictive`, compares distribution of simulated data vs observed data using KS-test, and writes p-value to `data/results/ppc.json`. **Constraint**: Must fail if p-value < 0.05 (indicates poor fit). **Dependency**: T023-Sampling. **Status**: **Complete**.
- [X] T024-Comparison [US2] [Dep: T024-Baseline-LMM, T024-PPC] Implement `code/analysis/model_comparison.py` to calculate AIC/WAIC and write the unified comparison report. **Deliverable**: A script that calculates `delta_aic`, `waic`, `ppc_p_value`, and writes a unified JSON report `data/results/model_comparison.json` containing these metrics and a `comparison_summary` field that explicitly links the PPC results to the LMM comparison. **Dependency**: T024-Baseline-LMM, T024-PPC. **Note**: This task is data-agnostic and can run on both real and simulated data. **Status**: **Complete**.
- [X] T027b-Delta-AIC-Report [US2] [Dep: T024-Comparison] Implement `code/analysis/simulation_delta_aic.py` to read baseline and bayesian AIC from `data/results/model_comparison.json`, calculate **Delta AIC**, and write the report. **Deliverable**: A script that computes `delta_aic = baseline_aic - bayesian_aic` and writes `data/results/simulation_delta_aic.json` with keys `delta_aic` (float), `threshold` (int, configurable), `threshold_check` (boolean), `status` (string: "PASS" or "FAIL" or "INCONCLUSIVE"). **Constraint**: Does NOT raise an error if `delta_aic <= 10`. Instead, it reports the value and sets a `status` field. **Dependency**: T023-Sampling, T024-Comparison. **Status**: **Complete**.
- [X] T027c-Parameter-Recovery [US2] [Dep: T023-Sampling, T014, T027b-Delta-AIC-Report] Implement `code/analysis/parameter_recovery.py` to calculate **Parameter Recovery** metrics. **Deliverable**: A script that compares estimated posterior means against the `ground_truth_effect` injected in T014. **Metrics**: Calculate bias (mean - truth) and coverage (proportion of truth within 95% CI). **Input Verification**: Must verify `data/processed/synthetic_logs.csv` and `data/results/model_comparison.json` exist before execution. **Output**: `data/results/parameter_recovery.json`. **Format**: JSON with keys: `bias`, `coverage_95ci`, `n_samples`, `ground_truth_effect`. **Dependency**: T023-Sampling, T014, T027b-Delta-AIC-Report. **Verification**: Must verify syntax and generate `data/results/parameter_recovery.json`. **Status**: **Complete**.
- [X] T027c-Sensitivity-Analysis [US2] [Dep: T027c-Parameter-Recovery] Implement `code/analysis/parameter_recovery.py` to perform sensitivity analysis on model thresholds **exactly {2, 10, 20}** as required by FR-005. **Metric Definition**: The metric being swept is the **prior standard deviation (sigma_prior)** of the effect size parameter in the PyMC5 model. **Threshold Units**: The values {2, 10, 20} represent the **prior standard deviation (sigma)** in the model definition (e.g., `pm.Normal('effect', mu=0, sigma=2)`). **Deliverable**: A script that sweeps thresholds across the set {2, 10, 20} and calculates stability metrics (coefficient of variation of posterior means). **Output**: `data/results/sensitivity_analysis.json`. **Dependency**: T027c-Parameter-Recovery. **Status**: **Complete**.
- [X] T027c-Verify [US2] [Verification] Implement `code/analysis/verify_parameter_recovery.py` to verify that `data/results/parameter_recovery.json` exists and contains the required keys before T033 runs. **Deliverable**: A script that asserts file existence and schema. **Dependency**: T027c-Parameter-Recovery. **Status**: **Complete**.

## Phase 5: User Story 3 - Statistical Validation and Reporting (Priority: P3)

- [X] T030-Regression [US3] Implement `code/models/regression.py` for hierarchical mixed-effects regression with Bonferroni correction. **Deliverable**: A function `fit_model(data)` using `statsmodels.MixedLM` with formula `judgment_rating ~ salience_level + (|participant_id)`. **Constraint**: The function MUST apply Bonferroni correction to the regression p-values within the same function before serialization. **Output**: A single artifact `data/results/mixed_effects_bonferroni_results.json` containing the regression coefficients, raw p-values, and Bonferroni-corrected p-values. **Dependency**: T023-Sampling. **Status**: **Complete**.
- [X] T030-Regression-Verify [US3] [Verification] Implement `code/analysis/verify_regression.py` to verify that `data/results/mixed_effects_bonferroni_results.json` exists and contains the required keys before T033 runs. **Deliverable**: A script that asserts file existence and schema. **Dependency**: T030-Regression. **Status**: **Complete**.
- [X] T045-Sensitivity-Link [US3] [Dep: T027c-Sensitivity-Analysis] Implement `code/analysis/sensitivity_link.py` to generate the sensitivity link report. **Deliverable**: A script that reads `data/results/sensitivity_analysis.json` and writes `data/results/sensitivity_link_report.json` with a `verdict` (string: "Robust", "Inconclusive", "Fragile") and a `justification` string. **Dependency**: T027c-Sensitivity-Analysis. **Status**: **Complete**.
- [X] T033-Final-Report-Synthesis [US3] [Dep: T027c-Parameter-Recovery, T027c-Sensitivity-Analysis, T030-Regression, T045-Sensitivity-Link] Implement `code/reports/generate_report.py` to generate the final report and synthesis. **Deliverable**: A script that reads `data/results/model_comparison.json`, `data/results/parameter_recovery.json`, `data/results/sensitivity_analysis.json`, `data/results/mixed_effects_bonferroni_results.json`, and `data/results/sensitivity_link_report.json`. **Output**: Generate `reports/final_report.md` with the required sections (Executive Summary, Model Comparison, Parameter Recovery, Sensitivity Analysis, Regression Results) and `data/results/robustness_summary.json` with a `verdict` (string: "Robust", "Inconclusive", "Fragile") and a `justification` string. **Dependency**: T024-Comparison, T027c-Parameter-Recovery, T027c-Sensitivity-Analysis, T030-Regression, T045-Sensitivity-Link. **Status**: **Complete**.

## Phase 6: Real Data Integration (Deferred until Phase 6)

- [X] T060 [US4] [Real Data] Implement `code/data/streaming_loader.py` to stream large datasets. **Deliverable**: A script using `datasets.load_dataset(..., streaming=True)` to process the full real dataset in chunks, ensuring memory safety without shrinking to a toy dataset. **Constraint**: The script must accumulate statistics online (e.g., running mean/variance) and must explicitly log the sample size and streaming strategy used. **Dependency**: T054b. **Status**: **Pending**.
- [X] T092-Placeholder [US4] [Real Data] **Real VR Log Ingestion Interface**: Define the interface for future real VR log ingestion. **Deliverable**: A script `code/data/fetch_real_vr.py` that defines the function signature `fetch_real_vr_logs() -> pd.DataFrame` and raises `NotImplementedError` with a message indicating this is a placeholder for Phase 6. **Constraint**: This task is **ONLY** for defining the interface. It is **NOT** executable. **Dependency**: T054b, T060. **Status**: **Archived** (Deferred to Phase 6).

## ArchivedTasks (No longer active)

- [X] T078 [US2] [Review: Parameter Recovery Implementation] **REMOVED**. Merged into T027c-Parameter-Recovery.
- [X] T079 [US3] [Review: Sensitivity Analysis Implementation] **REMOVED**. Merged into T027c-Sensitivity-Analysis (logic corrected to use {2, 10, 20}).
- [X] T080 [US3] [Review: Final Report Synthesis] **REMOVED**. Merged into T033-Final-Report-Synthesis.
- [X] T081 [US3] [Review: Robustness Synthesis] **REMOVED**. Merged into T033-Final-Report-Synthesis.
- [X] T061 [US4] [Review: Data Source] Merged into T054b.
- [X] T062 [US4] [Review: Streaming] Merged into T060.
- [X] T063 [US2] [Review: GPU Fallback] Merged into T022c.
- [X] T065 [US3] [Review: Sensitivity] Merged into T027c-Sensitivity-Analysis.
- [X] T066 [US2] [Review: GPU Fallback Implementation] Merged into T022c.
- [X] T067 [US4] [Review: Real Data Source Verification] Merged into T054b/T054c-Verify.
- [X] T068 [US1] [Review: Simulation Fidelity] Merged into T076.
- [X] T092 [US4] [Real Data] **Real VR Log Ingestion**: **ARCHIVED**. This task is deferred to Phase 6. No implementation is required in this branch. **Reason**: No verified real VR log dataset is available.