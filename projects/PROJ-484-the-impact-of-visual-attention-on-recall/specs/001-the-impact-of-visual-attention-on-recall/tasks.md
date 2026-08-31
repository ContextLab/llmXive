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

- [ ] T001 [P] Create project directory structure per implementation plan (`projects/PROJ-484-the-impact-of-visual-attention-on-recall/`). Execute: `mkdir -p data/raw data/processed artifacts/figures artifacts/logs code tests`.
- [ ] T001b [P] [US0] [FR-000] Initialize project root files (`projects/PROJ-484-the-impact-of-visual-attention-on-recall/.gitignore`, `projects/PROJ-484-the-impact-of-visual-attention-on-recall/README.md`). Create a `.gitignore` excluding `data/`, `artifacts/`, `__pycache__/`, and `.env`. Initialize a minimal `README.md` with project title, branch reference, and reproducibility statement.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T002 [P] Generate `requirements.txt` (`projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/requirements.txt`). {{claim:c_07d4954d}} (Wikidata Q6014791, https://www.wikidata.org/wiki/Q6014791) Pin versions where possible.
- [ ] T002b [P] Initialize Python virtual environment (`projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/venv`). Execute: `python3.11 -m venv code/venv`. [UNRESOLVED-CLAIM: c_41caf67b — status=not_enough_info] **Deliverable**: `code/venv/pyvenv.cfg`. Verify activation by checking that `code/venv/bin/python` reports version 3.11.x. [UNRESOLVED-CLAIM: c_fc5cbaad — status=not_enough_info]
- [X] T003 [P] Configure linting and formatting tools (`pyproject.toml`). Create `pyproject.toml` with sections `[tool.black]`, `[tool.flake8]`, and `[tool.isort]` configured with project-specific settings (line length consistent with style guidelines, skip gitignore).
- [ ] T004 [P] Create data directory structure (`data/raw/`, `data/processed/`, `artifacts/figures/`, `artifacts/logs/`).
- [X] T005 [P] Implement logging infrastructure (`code/__init__.py`, `code/logging_config.py`). Create a logging configuration that sets up a rotating file handler to `artifacts/logs/app.log` with DEBUG level and JSON formatting. [UNRESOLVED-CLAIM: c_fb5d94dd — status=not_enough_info]
- [ ] T006 [P] Create dataset schema validation contract (`specs/001-visual-attention-recall/contracts/dataset.schema.yaml`). Define YAML schema for the analysis-ready CSV based on Key Entities (Participant, Stimulus, Trial) in spec.md. [UNRESOLVED-CLAIM: c_8dbfee78 — status=not_enough_info]
- [ ] T006a [P] Generate data-model artifact (`specs/001-visual-attention-recall/data-model.md`). Create the data-model document defining the schema for Participant, Stimulus, and Trial entities.
- [ ] T006b [P] Create model output schema validation contract (`specs/001-visual-attention-recall/contracts/model_output.schema.yaml`). Define YAML schema for model results JSON and power analysis output. **Fields**: `model_convergence`, `chi_squared_stat`, `p_value`, `power_estimate`. [UNRESOLVED-CLAIM: c_eb62b26a — status=not_enough_info] (Depends on T006a)
- [X] T007 [P] Setup environment configuration management (`.env.example`, `code/config.py`). Define variables: DATA_PATH, RANDOM_SEED [UNRESOLVED-CLAIM: c_ebc56547 — status=not_enough_info], and structure `code/config.py` to load them.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: Data Verification & Geometry Calibration (Critical Prerequisite)

**Goal**: Resolve the critical gap regarding unverified data sources and missing geometry metadata before any data processing begins. Uses BIDS standard for metadata extraction and literature defaults if missing.

**Independent Test**: Execute the verification script against the target dataset manifest and confirm all required variables and geometry parameters are present (or defaults are applied).

**⚠️ BLOCKING**: Phase 3 (User Story 1) cannot begin until Phase 3 (Verification) succeeds.

### Implementation for Phase 3

- [X] T037 [P] [US1] Implement OpenNeuro Dataset Verification and Variable Validation in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/verify_data.py`. Target dataset: **ds001435**. [UNRESOLVED-CLAIM: c_164481f6 — status=not_enough_info] Parse the BIDS manifest (JSON/YAML sidecars) to verify the presence of ALL four required variables: Eye-tracking (x,y,timestamp), Valence, Recall, STAI. **CRITICAL**: {{claim:c_077633f3}} (Wikidata Q179550, https://www.wikidata.org/wiki/Q179550) DO NOT proceed to download. **References T006a** for schema.
- [X] T038 [US1] Implement Geometry Calibration and I-VT Threshold Calculation in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/verify_data.py`. Extract screen width, viewing distance, and sampling rate from `participants.tsv` or `dataset_description.json`. **Fallback**: {{claim:c_e066bdce}} (1110.0514, https://arxiv.org/abs/1110.0514) and log a warning. Calculate the pixel-threshold for the I-VT algorithm: `threshold_pixels_per_frame = (deg/s) * (pixels_per_degree) / (sampling_rate_hz)`. [UNRESOLVED-CLAIM: c_fd064309 — status=not_enough_info]
- [X] T039 [US1] Implement Temporal-Load Check in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/verify_data.py`. Verify `stimulus_duration_ms` in `events.tsv` or `task-*.json`. If missing, attempt to infer from `frame_count * (1000/fps)`. [UNRESOLVED-CLAIM: c_b3030667 — status=not_enough_info] **Fallback**: If only `ISI` is available and `ISI != duration`, use a default of 100ms and log a warning. **Deliverable**: `artifacts/logs/temporal_load_check.log`.
- [ ] T040 [US1] Generate Data Verification Report in `artifacts/logs/data_verification_report.json`. Output a summary of success/failure for data verification, variable presence, and geometry calibration. **Format**: JSON with fields `success`, `variable_presence`, `geometry_status`. If successful, this report serves as the prerequisite for T011b (Download).

**Checkpoint**: Data verification complete - User Story 1 implementation can now proceed safely

---

## Phase 4: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download raw RSVP dataset, extract gaze fixation metrics, and map stimuli to generate a clean analysis-ready CSV.

**Independent Test**: Run preprocessing on a small sample subset of participants. and verify output CSV contains non-null fixation durations, valid valence labels, and matches expected schema without crashing.

### Implementation for User Story 1

- [X] T011a [P] [US1] Implement Dataset Manifest Check in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/download_data.py`. Verify the dataset source against the 'Verified datasets' block and Constitution Principle I. **CRITICAL**: If no verified source is found, halt with `ERROR: No verified data source found`. **Exception**: Allow local mock data for *testing* pipeline logic only. **DEPENDS ON**: T037 success.
- [X] T011b [US1] Implement dataset download script with checksum verification in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/download_data.py` (FR-001). **CONSTRAINT**: Use `huggingface_hub` or `wget` with a verified URL (ds001435). **DEPENDS ON**: T011a success.
- [X] T013 [US1] Implement I-VT velocity-threshold algorithm for fixation extraction in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/preprocess.py` (FR-002). Use a configurable threshold derived from T038. **MANDATORY**: Implement a command-line argument parser (e.g., `argparse`) and config loading to allow the threshold and minimum fixation window to be set dynamically. Default minimum fixation window: a duration sufficient to distinguish stable gaze from saccadic transitions. (configurable).
- [X] T014 [US1] Implement stimulus ID to valence mapping (IAPS/NimStim) in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/preprocess.py` (FR-003). Reject unmapped IDs.
- [X] T015 [US1] Implement STAI score merging and participant filtering in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/preprocess.py`. Exclude participants missing STAI scores and log/report reduced sample size in `artifacts/logs/preprocessing.log`.
- [X] T016 [US1] Implement trial filtering logic (missing data, excessive blinks) with strict exclusion rules in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/preprocess.py`. Exclude trials with >50% missing frames. For blinks, exclude trials where blink duration exceeds a configurable threshold or a proportion of stimulus duration. No imputation permitted.
- [ ] T017 [US1] Generate final analysis-ready CSV (`data/processed/analysis.csv`) with schema validation in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/preprocess.py`. **Verification**: Assert output CSV matches `dataset.schema.yaml` and row count > 0.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

### Tests for User Story 1

- [X] T008 [P] [US1] Unit test for I-VT algorithm logic in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/tests/test_preprocess.py`. Implement `test_ivt_fixation_extraction`: asserts list of fixations with duration > 100ms is returned.
- [X] T009 [P] [US1] Unit test for stimulus mapping in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/tests/test_preprocess.py`. Implement `test_stimulus_valence_mapping`: asserts unmapped IDs raise KeyError.
- [X] T010 [P] [US1] Integration test for full pipeline on sample data in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/tests/test_integration.py`. Implement `test_full_preprocessing_pipeline`: asserts output CSV has non-null fixation durations and valid valence labels.

---

## Phase 5: User Story 2 - Mixed-Effects Model Execution and Interaction Testing (Priority: P2)

**Goal**: Fit mixed-effects logistic regression and perform likelihood-ratio testing to determine interaction significance.

**Independent Test**: Run model fitting on a simulated dataset with known parameters and verify the likelihood-ratio test correctly identifies the interaction term as significant.

### Implementation for User Story 2

- [X] T020 [US2] Implement mixed-effects logistic regression model fitting (`recall ~ fixation_duration * valence * trait_anxiety + (1|participant) + (1|stimulus_id)`) in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/model_fit.py` (FR-004). Use 'logit' link, 'bobyqa' optimizer, max_iter high, tolerance to a sufficiently small threshold. **Constraint**: Ensure the model runs on CPU. If convergence fails due to complexity, simplify random effects as per T021.
- [X] T021 [US2] Implement fallback logic for random effects structure if convergence fails in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/model_fit.py`. If design is not fully crossed or convergence fails, retry with formula: `... + (1|participant)` only. Log warning.
- [X] T022 [US2] Implement Likelihood-Ratio Test (LRT) comparing full vs. reduced model in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/model_fit.py` (FR-005). **Depends on T020 completion**.
- [X] T023 [US2] Implement residual diagnostics and overdispersion check in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/model_fit.py` (FR-007). Report "Convergence: OK" or flag overdispersion if dispersion > 1.2.
- [X] T023c [US2] Implement Bootstrap Convergence Verification in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/model_fit.py`. **MANDATORY**: ONLY run if the initial model (T020) fails to converge or if sample size is small. Run bootstrap simulation on the failed cases to empirically verify the high convergence rate (SC-002). Calculate convergence metric as the percentage of bootstrap samples where the model status is 'Convergence: OK'. Report convergence status and power metric (SC-002) to `artifacts/logs/bootstrap_convergence.log`.
- [ ] T024 [US2] Implement Monte Carlo Power Analysis in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/model_fit.py` (SC-003). Extract variance components from the fitted model (T023). **Fallback**: If the model fails to converge and variance components are unavailable, use conservative literature estimates (f2=0.15) and sample size. Execute the simulation with iterations=1000, alpha=0.05. Calculate achieved power and report to `artifacts/logs/power_analysis.json`.
- [ ] T025 [US2] Export model results and diagnostics to JSON (`artifacts/logs/model_results.json`, `artifacts/logs/power_analysis.json`) in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/model_fit.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

### Tests for User Story 2

- [X] T018 [P] [US2] Unit test for model convergence diagnostics in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/tests/test_model.py`. Implement `test_model_convergence_check`: asserts convergence status is correctly identified.
- [X] T019 [P] [US2] Unit test for likelihood-ratio test logic in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/tests/test_model.py`. Implement `test_likelihood_ratio_test`: asserts p-value calculation is correct for known parameters.

---

## Phase 6: User Story 3 - Visualization of Marginal Effects (Priority: P3)

**Goal**: Generate marginal effect plots showing the slope of fixation duration on recall probability for high vs. low anxiety groups.

**Independent Test**: Generate the plot file (PNG) and verify it contains two distinct regression lines with shaded CIs and a legend, running headlessly.

### Implementation for User Story 3

- [ ] T028 [US3] Implement marginal effects calculation for high/low anxiety groups in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/visualize.py`. Calculate slopes and CIs from model coefficients. **Deliverable**: `artifacts/logs/marginal_effects_data.json`.
- [ ] T030 [US3] Implement marginal effects plot generation in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/visualize.py`. Set matplotlib backend to 'Agg' (headless). Generate the plot with two distinct regression lines and shaded confidence interval regions for both high and low anxiety groups. **Deliverable**: `artifacts/figures/marginal_effects.png` and `artifacts/logs/render_config.log`. Log total disk usage for informational purposes.

**Checkpoint**: All user stories should now be independently functional

### Tests for User Story 3

- [ ] T026 [P] [US3] Unit test for confidence interval calculation in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/tests/test_visualize.py`. Implement `test_confidence_interval_calculation`: asserts CI bounds match standard errors.
- [ ] T027 [P] [US3] Integration test for plot generation in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/tests/test_visualize.py`. Implement `test_plot_generation`: asserts PNG file exists, has two lines, shaded regions, and legend.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T032 [P] Implement run_pipeline.py in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/run_pipeline.py`. Define pipeline steps: download -> verify -> preprocess -> model -> visualize. Implement error handling wrapper with try/except blocks and specific error logging. Execute steps sequentially, halting on the first error.
- [ ] T033 [P] Configure log rotation and test in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/logging_config.py` and `tests/test_logging.py`. Configure `RotatingFileHandler` with `maxBytes=10MB`, `backupCount=5`. Implement `test_log_rotation`: asserts backup files are created after exceeding maxBytes.
- [ ] T034 [P] Update documentation in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/README.md` and `docs/quickstart.md`. Add installation, usage, and pipeline description to README. Add step-by-step execution commands to quickstart.
- [ ] T035 [P] Execute full integration test suite and verify acceptance criteria in `projects/PROJ-484-the-impact-of-visual-attention-on-recall`. Execute `pytest -v`. Check that all acceptance criteria from spec.md are met (row counts, convergence, plot validity).
- [ ] T036 [P] Validate quickstart.md execution in `projects/PROJ-484-the-impact-of-visual-attention-on-recall`. Execute the commands in `docs/quickstart.md` in a fresh venv and capture exit code 0.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **Phase 3 (Data Verification)**: Depends on Foundational completion - BLOCKS User Story 1
- **User Stories (Phase 4+)**: All depend on Foundational phase completion AND Phase 3 success
 - User story 1 must complete before user stories 2 and 3.
 - User story 2 must complete before user story 3.
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, Phase 3 tasks can run in parallel.
- Once Phase 3 succeeds, User Stories can be implemented sequentially due to dependencies.
- All tests for a user story marked [P] can run in parallel
- Different models within a story marked [P] can run in parallel