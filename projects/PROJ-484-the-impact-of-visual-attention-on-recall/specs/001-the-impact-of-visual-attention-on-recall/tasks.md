---
description: "Task list template for feature implementation"
---

# Tasks: The Impact of Visual Attention on Recall of Emotional Stimuli in Rapid Visual Sequences

**Input**: Design documents from `/specs/001-visual-attention-recall/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 [P] Create project directory structure per implementation plan (`projects/PROJ-484-the-impact-of-visual-attention-on-recall/`). Execute: `mkdir -p data/raw data/processed artifacts/figures artifacts/logs code tests`. **Verification**: Execute `ls data/raw data/processed artifacts/figures artifacts/logs code tests` and `test -d` for each directory; fail if any directory is missing.
- [X] T001b [P] [US0] [FR-000] Initialize project root files (`projects/PROJ-484-the-impact-of-visual-attention-on-recall/.gitignore`, `projects/PROJ-484-the-impact-of-visual-attention-on-recall/README.md`). Create a `.gitignore` excluding `data/`, `artifacts/`, `__pycache__/`, and `.env`. Initialize a minimal `README.md` with project title, branch reference, and reproducibility statement.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002 [P] Generate `requirements.txt` (`projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/requirements.txt`). Pin versions where possible.
- [X] T002b [P] Initialize Python virtual environment (`projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/venv`). Execute: `python3.11 -m venv code/venv`. **Deliverable**: `code/venv/pyvenv.cfg`. Verify activation by checking that `code/venv/bin/python` reports version 3.11.x.
- [X] T003 [P] Configure linting and formatting tools (`pyproject.toml`). Create `pyproject.toml` with sections `[tool.black]`, `[tool.flake8]`, and `[tool.isort]` configured with project-specific settings (line length consistent with style guidelines, skip gitignore).
- [X] T004 [P] Create data directory structure (`data/raw/`, `data/processed/`, `artifacts/figures/`, `artifacts/logs/`).
- [X] T005 [P] Implement logging infrastructure (`code/__init__.py`, `code/logging_config.py`). Create a logging configuration that sets up a rotating file handler to `artifacts/logs/app.log` with DEBUG level and JSON formatting (fields: `timestamp`, `level`, `message`, `module`).
- [X] T006 [P] Create dataset schema validation contract (`specs/001-visual-attention-recall/contracts/dataset.schema.yaml`). Define YAML schema for the analysis-ready CSV based on Key Entities (Participant, Stimulus, Trial) in spec.md.
- [X] T006a [P] Generate data-model artifact (`specs/001-visual-attention-recall/data-model.md`). Create the data-model document defining the schema for Participant, Stimulus, and Trial entities.
- [X] T006b [P] [US1] Create model output schema validation contract (`specs/001-visual-attention-recall/contracts/model_output.schema.yaml`). Define YAML schema for model results JSON and power analysis output. **Fields**: `model_convergence`, `chi_squared_stat`, `p_value`, `power_estimate`. **DEPENDS ON**: T006a.
- [X] T007 [P] Setup environment configuration management (`.env.example`, `code/config.py`). Define variables: DATA_PATH, RANDOM_SEED, and structure `code/config.py` to load them.
- [X] T011a [P] [US1] Implement Dataset Manifest Check in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/download_data.py`. Verify the dataset source against the 'Verified datasets' block and Constitution Principle I. Fetch ONLY the BIDS manifest (JSON/YAML sidecars) to verify variable presence. **CRITICAL**: If no verified source is found, halt with `ERROR: No verified data source found`. **Exception**: Allow local mock data for *testing* pipeline logic only. **DEPENDS ON**: T006a (for schema reference).
- [X] T050 [P] [US1] Refactor `download_data.py` to remove ALL generic `try/except` blocks that fallback to synthetic/mock data. Ensure any network failure raises a specific `DataFetchError` with a clear message. **Constraint**: No synthetic data generation code allowed in this file. **Clarification**: This task reinforces T011a's "Fail Loud" logic by ensuring error handling is explicit and robust, not by removing the halt condition. **DEPENDS ON**: T011a.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: Data Verification & Geometry Calibration (Critical Prerequisite)

**Goal**: Resolve the critical gap regarding unverified data sources and missing geometry metadata before any data processing begins. Uses BIDS standard for metadata extraction. If metadata is missing, the system MUST FAIL (unless `--allow-hypothetical` is set in Phase 10).

**Independent Test**: Execute the verification script against the target dataset manifest and confirm all required variables and geometry parameters are present (or the system fails with a specific error).

**⚠️ BLOCKING**: Phase 4 (User Story 1) cannot begin until Phase 3 succeeds.

### Implementation for Phase 3

- [X] T037 [US1] Implement OpenNeuro Dataset Verification and Variable Validation in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/verify_data.py`. Target dataset: **a publicly available neuroimaging repository**.

Parse the BIDS manifest (JSON/YAML sidecars) to verify the presence of ALL four required variables: Eye-tracking (x,y,timestamp), Valence, Recall, STAI. **CRITICAL**: DO NOT proceed to download full data. **References T006a** for schema. **DEPENDS ON**: T011a (Manifest Check) completion. **HALT** if ds001435 is not found or variables are missing.
- [X] T038 [US1] Implement Geometry Calibration and I-VT Threshold Calculation in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/verify_data.py`. Extract screen width, viewing distance, and sampling rate from `participants.tsv` or `dataset_description.json`. **CRITICAL**: If metadata is missing, the system MUST FAIL with "ERROR: Cannot calibrate I-VT threshold without screen geometry." No fallback to literature defaults permitted. Calculate the pixel-threshold for the I-VT algorithm: `threshold_pixels_per_frame = (deg/s) * (pixels_per_degree) / (sampling_rate_hz)`.
- [X] T039 [US1] Implement Temporal-Load Check in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/verify_data.py`. Verify `stimulus_duration_ms` in `events.tsv` or `task-*.json`. If missing, attempt to infer from `frame_count * (1000/fps)`. **CRITICAL**: If only `ISI` is available and `ISI != duration`, **FAIL** with "ERROR: Cannot verify Temporal-Load constraint; ISI does not equal duration." UNLESS a documented ratio exists in metadata, in which case log a warning and proceed with adjusted calculation. **Deliverable**: `artifacts/logs/temporal_load_check.log`. **DEPENDS ON**: T011a.
- [X] T040 [US1] Generate Data Verification Report in `artifacts/logs/data_verification_report.json`. Output a summary of success/failure for data verification, variable presence, and geometry calibration. **Format**: JSON with fields `success`, `variable_presence`, `geometry_status`. If successful, this report serves as the prerequisite for T011b. **DEPENDS ON**: T011a, T037-T039.

**Checkpoint**: Data verification complete - User Story 1 implementation can now proceed safely

---

## Phase 4: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download raw RSVP dataset, extract gaze fixation metrics, and map stimuli to generate a clean analysis-ready CSV.

**Independent Test**: Run preprocessing on a small sample subset of participants. and verify output CSV contains non-null fixation durations, valid valence labels, and matches expected schema without crashing.

### Implementation for User Story 1

- [X] T011b [US1] Implement dataset download script with checksum verification in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/download_data.py` (FR-001). **CONSTRAINT**: Use `huggingface_hub` or `wget` with a verified URL (ds001435). **DEPENDS ON**: T040 (Verification Report success), T011a (Manifest Check).
- [X] T011c [P] [US1] Implement Disk Space Check in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/download_data.py` (FR-001). Verify available disk space is sufficient for the full dataset before download begins. **CRITICAL**: If insufficient space, halt with `ERROR: Insufficient disk space`. **DEPENDS ON**: T011a.
- [X] T013 [US1] Implement I-VT velocity-threshold algorithm for fixation extraction in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/preprocess.py` (FR-002). **MANDATORY**: Implement the I-VT algorithm (velocity threshold + minimum duration) as defined in FR-002. Use a configurable threshold derived from T038. **MANDATORY**: Implement a command-line argument parser (e.g., `argparse`) and config loading to allow the threshold and minimum fixation window to be set dynamically. **Default minimum fixation window: a standard duration consistent with established gaze-contingent paradigms.** (configurable via `config.yaml: ivt_min_duration_ms`).
- [X] T014 [US1] Implement stimulus ID to valence mapping (IAPS/NimStim) in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/preprocess.py` (FR-003). Reject unmapped IDs.
- [X] T015 [US1] Implement STAI score merging and participant filtering in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/preprocess.py`. Exclude participants missing STAI scores and log/report reduced sample size in `artifacts/logs/preprocessing.log`.
- [X] T016 [US1] Implement trial filtering logic (missing data, excessive blinks) with strict exclusion rules in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/preprocess.py`. Exclude trials with >50% missing frames. For blinks, exclude trials where blink duration exceeds a configurable threshold or a proportion of stimulus duration. No imputation permitted.
- [X] T017 [US1] Generate final analysis-ready CSV (`data/processed/analysis.csv`) with schema validation in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/preprocess.py`. **Verification**: Assert output CSV matches `dataset.schema.yaml` and row count > 0. **Default: Full Load**. The dataset is expected to fit comfortably in memory; standard `pandas` load is sufficient. **DEPENDS ON**: T013, T014, T015, T016.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

### Tests for User Story 1

- [X] T008 [P] [US1] Unit test for I-VT algorithm logic in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/tests/test_preprocess.py`. Implement `test_ivt_fixation_extraction`: asserts list of fixations with duration >= 100ms is returned.
- [X] T009 [P] [US1] Unit test for stimulus mapping in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/tests/test_preprocess.py`. Implement `test_stimulus_valence_mapping`: asserts unmapped IDs raise KeyError.
- [X] T010 [P] [US1] Integration test for full pipeline on sample data in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/tests/test_integration.py`. Implement `test_full_preprocessing_pipeline`: asserts output CSV has non-null fixation durations and valid valence labels.

---

## Phase 5: User Story 2 - Mixed-Effects Model Execution and Interaction Testing (Priority: P2)

**Goal**: Fit mixed-effects logistic regression and perform likelihood-ratio testing to determine interaction significance.

**Independent Test**: Run model fitting on a simulated dataset with known parameters and verify the likelihood-ratio test correctly identifies the interaction term as significant.

### Implementation for User Story 2

- [X] T020 [US2] Implement mixed-effects logistic regression model fitting (`recall ~ fixation_duration * valence * trait_anxiety + (1|participant) + (1|stimulus_id)`) in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/model_fit.py` (FR-004). Use 'logit' link, 'bobyqa' optimizer, max_iter=10000, tol=1e-6. **Constraint**: Ensure the model runs on CPU. If convergence fails due to complexity, simplify random effects as per T021b. **DEPENDS ON**: T017.
- [X] T021a [US2] Implement Convergence Failure Detection in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/model_fit.py`. Check for convergence status and log warning if model fails to converge. **Deliverable**: Log status of convergence. **DEPENDS ON**: T020.
- [X] T021b [US2] Implement Random Effects Simplification Fallback in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/model_fit.py`. If convergence fails (T021a), retry with formula: `... + (1|participant)` only. Log warning. **DEPENDS ON**: T021a.
- [X] T022a [US2] Implement Likelihood-Ratio Test Statistic Calculation in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/model_fit.py`. Calculate chi-squared statistic and p-value for model comparison. **DEPENDS ON**: T020.
- [X] T022b [US2] Execute Model Comparison in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/model_fit.py`. Compare full vs. reduced model and report significance. **DEPENDS ON**: T022a.
- [X] T023a [US2] Implement Residual Diagnostics in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/model_fit.py`. Calculate residuals and report convergence status. **DEPENDS ON**: T020.
- [X] T023b [US2] Compute Overdispersion Metric in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/model_fit.py`. Check if the dispersion parameter exceeds a threshold indicative of overdispersion and flag if overdispersion is detected. **DEPENDS ON**: T023a.
- [X] T023c [US2] Implement Bootstrap Convergence Verification Loop in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/model_fit.py`. **MANDATORY**: Run bootstrap simulation on the ACTUAL dataset (resampling rows with replacement) to empirically verify the high convergence rate (SC-002). **CRITICAL**: If the actual dataset is missing or invalid, verify convergence on the FULL dataset (mock or real) and log the method used. **FALLBACK**: If bootstrap fails due to missing data, verify convergence on the FULL dataset and log the method used. **DEPENDS ON**: T020.
- [X] T023d [US2] Calculate Convergence Metric in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/model_fit.py`. Compute and report convergence percentage from bootstrap samples. **DEPENDS ON**: T023c.
- [X] T024 [US2] Implement Monte Carlo Power Analysis in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/model_fit.py` (SC-003). Extract variance components from the fitted model (T023). **Fallback**: If the model fails to converge and variance components are unavailable, use conservative literature estimates (f2=0.15) and sample size. Execute the simulation with iterations=1000, alpha=0.05. Calculate achieved power and report to `artifacts/logs/power_analysis.json`. **Deliverable**: `artifacts/logs/power_analysis.json`. **DEPENDS ON**: T020.
- [X] T025 [US2] Export model results and diagnostics to JSON (`artifacts/logs/model_results.json`, `artifacts/logs/power_analysis.json`) in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/model_fit.py`. **DEPENDS ON**: T020, T022b, T023b, T023d, T024.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

### Tests for User Story 2

- [X] T018 [P] [US2] Unit test for model convergence diagnostics in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/tests/test_model.py`. Implement `test_model_convergence_check`: asserts convergence status is correctly identified.
- [X] T019 [P] [US2] Unit test for likelihood-ratio test logic in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/tests/test_model.py`. Implement `test_likelihood_ratio_test`: asserts p-value calculation is correct for known parameters.

---

## Phase 6: User Story 3 - Visualization of Marginal Effects (Priority: P3)

**Goal**: Generate marginal effect plots showing the slope of fixation duration on recall probability for high vs. low anxiety groups.

**Independent Test**: Generate the plot file (PNG) and verify it contains two distinct regression lines with shaded CIs and a legend, running headlessly.

### Implementation for User Story 3

- [X] T028 [US3] Implement marginal effects calculation for high/low anxiety groups in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/visualize.py`. Calculate slopes and CIs from model coefficients. **Deliverable**: `artifacts/logs/marginal_effects_data.json`. **DEPENDS ON**: T025.
- [X] T030 [US3] Implement marginal effects plot generation in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/visualize.py`. Set matplotlib backend to 'Agg' (headless). Generate the plot with two distinct regression lines and shaded confidence interval regions for both high and low anxiety groups. **Deliverable**: `artifacts/figures/marginal_effects.png` and `artifacts/logs/render_config.log`. Log total disk usage for informational purposes. **Verification**: Assert PNG contains two lines, shaded CI regions, and legend. **DEPENDS ON**: T028.

**Checkpoint**: All user stories should now be independently functional

### Tests for User Story 3

- [X] T026 [P] [US3] Unit test for confidence interval calculation in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/tests/test_visualize.py`. Implement `test_confidence_interval_calculation`: asserts CI bounds match standard errors. **DEPENDS ON**: T028.
- [X] T027 [P] [US3] Integration test for plot generation in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/tests/test_visualize.py`. Implement `test_plot_generation`: asserts PNG file exists, has two lines, shaded regions, and legend. **DEPENDS ON**: T030.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T032 [P] Implement run_pipeline.py in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/run_pipeline.py`. Define pipeline steps: download -> verify -> preprocess -> model -> visualize. Implement error handling wrapper with try/except blocks and specific error logging. Execute steps sequentially, halting on the first error. **DEPENDS ON**: T011b, T017, T025, T030.
- [X] T033 [P] Configure log rotation and test in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/logging_config.py` and `tests/test_logging.py`. Configure `RotatingFileHandler` with `maxBytes=10MB`, `backupCount=5`. Implement `test_log_rotation`: asserts backup files are created after exceeding maxBytes. **DEPENDS ON**: T005.
- [X] T034 [P] Update documentation in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/README.md` and `docs/quickstart.md`. Add installation, usage, and pipeline description to README. Add step-by-step execution commands to quickstart.
- [X] T035 [P] Execute full integration test suite and verify acceptance criteria in `projects/PROJ-484-the-impact-of-visual-attention-on-recall`. Execute `pytest -v`. Check that all acceptance criteria from spec.md are met (row counts, convergence, plot validity).
- [X] T036 [P] Validate quickstart.md execution in `projects/PROJ-484-the-impact-of-visual-attention-on-recall`. Execute the commands in `docs/quickstart.md` in a fresh venv and capture exit code 0.

---

## Phase 9: Execution Feasibility & Resource Optimization (Revision: CPU-First Strategy)

**Goal**: Explicitly optimize the statistical modeling phase for the -core CPU constraint (GitHub Actions) while maintaining scientific validity. This phase ensures the mixed-effects model does not timeout and respects the "CPU-first" rule by using appropriate approximations if necessary.

**Independent Test**: Execute the model fitting script on the full dataset (or a representative large sample) on a 2-core CPU environment and verify it completes within 4 hours with convergence status "OK".

### Implementation for Execution Feasibility

- [X] T060a [P] [US2] Configure CPU-Optimized Model Fitting Parameters in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/model_fit.py`. Configure `statsmodels` or `lme4` (via `rpy2` if necessary, though Python-native preferred) to use 'bobyqa' optimizer, max_iter=10000, and convergence tolerance of 1e-6. **Constraint**: Do NOT arbitrarily reduce iterations to meet time limits; prioritize convergence accuracy. **References**: SC-004 (4-hour limit).
- [X] T060b [US2] Implement Random Effects Simplification Fallback in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/model_fit.py`. If the full crossed design `(1|participant) + (1|stimulus_id)` causes convergence timeouts, simplify to `(1|participant)` only. Log warning and proceed. **Constraint**: Do NOT downgrade to fixed-effects model. **DEPENDS ON**: T021a.
- [X] T061 [US2] Implement Early Stopping and Timeout Enforcement in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/model_fit.py`. Wrap the model fitting process in a `multiprocessing` wrapper (cross-platform compatible) to ensure the process terminates gracefully if it exceeds a predefined time limit (leaving buffer for LRT and plotting). **CRITICAL**: Ensure partial diagnostics are saved to `artifacts/logs/timeout_protection.log` before termination. **Deliverable**: `artifacts/logs/timeout_protection.log`. **DEPENDS ON**: T020.
- [X] T062 [P] [US2] Add Benchmark Test for CPU Runtime in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/tests/test_model.py`. Implement `test_cpu_runtime_limit`: Executes the model fitting on a known dataset subset and asserts that the process completes within A duration of approximately half an hour (scaled down from 4 hours for test speed) and logs the actual runtime.
- [X] T064 [P] [US2] Implement Global Pipeline Runtime Aggregation in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/run_pipeline.py`. Track cumulative runtime for download, preprocess, model, and visualize steps. Report total time to `artifacts/logs/pipeline_runtime.json`. **Verification**: Assert total time < 4 hours (SC-004). **DEPENDS ON**: T032.

**Checkpoint**: Model fitting is guaranteed to complete within the 4-hour CPU constraint or fail gracefully with a clear diagnostic.

---

## Phase 10: Review Resolution & Final Validation (Revision: Addressing Analysis Findings)

**Goal**: Address specific reviewer concerns regarding the "Fail Loud" data strategy, the exactness of the I-VT calibration, and the robustness of the power analysis against sparse data.

**Independent Test**: Re-run the full pipeline with the new strict data checks and verify that the system halts immediately on missing metadata or data fetch failures, and that the power analysis correctly flags low power if sample size is insufficient.

### Implementation for Review Resolution

- [ ] T070a [US1] Generate `verified_sources_hypothetical.json` in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/`. Create a JSON file listing `ds001435` with status `hypothetical` and a mock data path. This file enables the pipeline to run in "hypothetical" mode without manual CLI flags. **DEPENDS ON**: T011a.
- [ ] T070 [US1] Refactor `download_data.py` to implement a strict "Verified Source" check before any network call. The script MUST query the `verified_sources_hypothetical.json` (created by T070a) or a local `verified_sources.json`. **CRITICAL**: If no verified source is found AND the config does not mark the dataset as 'hypothetical', the script MUST halt with `ERROR: No verified source found for ds001435`. If the config marks the dataset as 'hypothetical', proceed with mock data and log a `WARNING: Hypothetical mode enabled`. **Constraint**: Remove any logic that attempts to guess URLs or fallback to generic repositories. **Clarification**: This task supersedes the logic in T050. **DEPENDS ON**: T011a, T050, T070a.
- [ ] T071 [US1] Enhance `verify_data.py` to perform a strict "Geometry Calibration" check. The script MUST extract `screen_width_px`, `viewing_distance_mm`, and `sampling_rate_hz` from the BIDS manifest. If any of these are missing, the script MUST fail with `ERROR: Cannot calibrate I-VT threshold without screen geometry.` UNLESS the `verified_sources_hypothetical.json` config marks the dataset as 'hypothetical', in which case it loads default values from `config.yaml` and logs a warning. **Constraint**: No default values from literature are permitted in strict mode. **DEPENDS ON**: T038, T070a.
- [ ] T071b [US1] Implement "Hypothetical Geometry Fallback" in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/verify_data.py`. If `verified_sources_hypothetical.json` is present and marks the dataset as 'hypothetical', load default values from `config.yaml` (e.g., `default_screen_width_px`, `default_viewing_distance_mm`, `default_sampling_rate_hz`) and proceed. **DEPENDS ON**: T071.
- [ ] T072 [US2] Implement a "Sparse Data Power Warning" in `model_fit.py`. If the Monte Carlo simulation (T024) indicates achieved power < 0.80 for the three-way interaction, the script MUST log a `WARNING: Low statistical power detected` and output a `power_warning.json` file detailing the sample size and effect size constraints. **Constraint**: Do not suppress this warning or proceed as if the result is valid. **DEPENDS ON**: T024.
- [ ] T073 [P] [US2] Add a unit test for the "Sparse Data Power Warning" in `tests/test_model.py`. Implement `test_sparse_data_power_warning`: asserts that the warning is triggered and the `power_warning.json` file is created when simulated sample size is artificially reduced. **DEPENDS ON**: T072.
- [ ] T074 [P] [US1] Add a unit test for the "Strict Verified Source" check in `tests/test_download.py`. Implement `test_verified_source_check`: asserts that the script halts with the correct error message when a dataset is not in the verified list. **DEPENDS ON**: T070.
- [ ] T075 [P] [US1] Add a unit test for the "Geometry Calibration" failure in `tests/test_verify.py`. Implement `test_geometry_calibration_failure`: asserts that the script halts with the correct error message when required metadata is missing. **DEPENDS ON**: T071.

**Checkpoint**: All reviewer concerns regarding data integrity, calibration strictness, and power analysis transparency are addressed.