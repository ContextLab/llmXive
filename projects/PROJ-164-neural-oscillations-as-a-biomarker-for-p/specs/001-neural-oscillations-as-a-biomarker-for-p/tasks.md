# Tasks: Neural Oscillations as a Biomarker for Predicting Response to Transcranial Direct Current Stimulation

**Input**: Design documents from `/specs/001-neural-oscillations-tDCS-biomarker/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root
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

- [ ] T001 [P] Create project structure. Execute the following command to establish the directory tree: `mkdir -p code/ code/utils/ tests/ data/raw data/processed data/synthetic models/ docs/ docs/contracts/ state/projects/`. Ensure `data/raw` is created with restricted write permissions after initial ingestion.
- [ ] T002 [P] Initialize Python 3.11 project with `requirements.txt`. Execute: `echo -e "mne==1.7.0\nscikit-learn==1.4.0\nnumpy==1.26.0\npandas==2.1.0\nscipy==1.12.0\nstatsmodels==0.14.1\npyyaml==6.0.1\npytest==7.4.0" > requirements.txt`. Then execute `pip install -r requirements.txt` to install dependencies. Verify file content matches exactly.
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools with `pyproject.toml`. Define `target-version = "py311"` and exclude `data/`, `models/`, `state/`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Setup configuration management in `code/utils/config.py` for paths, seeds (42), and thresholds (p=0.05, R2=0.0). Include constants for `BANDS = ['delta', 'theta', 'alpha', 'beta', 'gamma']`.
- [ ] T005 [P] Implement I/O helpers in `code/utils/io_helpers.py` for CSV/Parquet loading, checksumming (SHA-256), and artifact hashing. Ensure `verify_checksum` function returns boolean and logs mismatches.
- [ ] T006 Create base data schema definitions in `specs/contracts/dataset.schema.yaml`. Define fields: `subject_id`, `channel`, `time`, `voltage`, `condition`, `mode_flag`.
- [ ] T007 Create output schema definitions in `specs/contracts/output.schema.yaml`. Define fields for `feature_matrix`, `model_metrics`, `sensitivity_table`.
- [ ] T008 Setup logging infrastructure to capture warnings, mode switches, and resource usage (stdout + `logs/pipeline.log`). Configure log rotation to prevent disk overflow.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest raw EEG data, verify pairing, and generate synthetic targets if paired data is missing (Fallback/Positive Control Mode).

**Independent Test**: Can be fully tested by running the preprocessing script on a subset of the PhysioNet EEG Motor Movement/Imagery Dataset and verifying the output file structure matches the schema defined in `specs/contracts/dataset.schema.yaml` without crashing.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: These tasks represent **Writing Test Code**. Execution of these tests occurs in T045.

- [ ] T010 [P] [US1] Write unit test code for checksum verification in `tests/test_preprocess.py`. Test case: Verify SHA-256 match/mismatch handling.
- [ ] T011 [P] [US1] Write unit test code for mode detection logic (Primary vs. Fallback vs. Positive Control) in `tests/test_preprocess.py`. Test case: Verify mode switch on missing pairing.
- [ ] T012 [P] [US1] Write unit test code for synthetic target generation (decoupled vs. injected) in `tests/test_preprocess.py`. Test case: Verify signal injection formula and noise decoupling.

### Implementation for User Story 1

- [ ] T013 [US1] Implement data download for PhysioNet EEG Motor Movement/Imagery Dataset in `code/01_ingest_preprocess.py`. 
    - **URL**: `https://physionet.org/files/eegmmidb/1.0.0/`. 
    - **Output**: Save to `data/raw/` with exact filename pattern `sub-{subject_id}_run-{run_id}.edf`. 
    - **Logic**: If file exists, compute SHA-256. If match, skip download. If mismatch, halt with error. If missing, download with retry logic (catch `requests.exceptions.RequestException`, exponential backoff, max 3 retries). 
    - **Constraint**: Monitor RAM/CPU usage during download and extraction. Log metrics to `logs/pipeline.log`.
- [ ] T014 [US1] Implement SHA-256 checksum verification for all files in `data/raw/` and log to `state/projects/PROJ-164-neural-oscillations-as-a-biomarker-for-p.yaml`. **Constraint**: Verify raw files are **read-only** and unchanged after verification. Set permissions to `chmod 444` on successful verification.
- [ ] T015 [US1] Implement pairing check logic: detect missing tDCS outcomes. **Logic**: If missing, switch to **Fallback Mode** (decoupled data) or **Positive Control Mode** (injected signal) based on `config.py` flag. Log the mode switch explicitly.
- [ ] T016 [US1] **Generate Synthetic Target Data** (Executed immediately after T015 if in synthetic mode). 
    - **Fallback Mode**: Generate target using `np.random.normal(0, 1)` scaled by literature-derived aggregate effect size (decoupled from EEG).
    - **Positive Control Mode**: Generate target with **known injected signal** using a weighted sum of ALL bands (delta, theta, alpha, beta, gamma) across the global feature vector: `target = 0.5 * (sum_of_all_band_powers) + np.random.normal(0, 0.1)`. 
    - **Output**: Save to `data/synthetic/tDCS_response.csv` with columns `subject_id`, `response_pct`, `mode_flag`.
- [ ] T017 [US1] Implement band-pass filtering (1–45 Hz) and common average referencing in `code/01_ingest_preprocess.py`. 
    - **Constraint**: **Read-only** access to `data/raw/`. All filtered outputs written to `data/processed/`. **Do not** modify raw files.
    - **Constraint**: Monitor RAM/CPU usage during filtering. Log metrics to `logs/pipeline.log`.
- [ ] T018 [US1] Implement epoch alignment (2s windows) and bad channel logging (z-score > 5) in `code/01_ingest_preprocess.py`. Output: `data/processed/epochs.fif`.
    - **Constraint**: Monitor RAM/CPU usage during epoching. If memory exceeds a predefined threshold, trigger downsampling logic. Log metrics to `logs/pipeline.log`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

### Test Execution for User Story 1

- [ ] T045 [US1] **Run** all unit tests (T010-T012) for User Story 1. **Pass Criteria**: All tests pass. If fail, halt pipeline.

---

## Phase 4: User Story 2 - Feature Extraction and Statistical Modeling (Priority: P2)

**Goal**: Compute spectral power and connectivity metrics, then fit a Ridge Regression model (Positive Control Mode).

**Independent Test**: Can be fully tested by executing the feature extraction and regression module on the synthetic dataset and verifying the model outputs coefficients, R², and p-values without requiring external network access.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T020 [P] [US2] Write unit test code for spectral power calculation (Welch's method) in `tests/test_feature_extraction.py`
- [ ] T021 [P] [US2] Write unit test code for connectivity metrics (PLV, wPLI) in `tests/test_feature_extraction.py`
- [ ] T022 [P] [US2] Write integration test code for Positive Control signal detection in `tests/test_positive_control.py`

### Implementation for User Story 2

- [ ] T023 [P] [US2] Implement spectral power density extraction (Delta, Theta, Alpha, Beta, Gamma) using Welch's method in `code/02_feature_extraction.py`. **Output**: `data/processed/spectral_power.csv`.
- [ ] T024 [P] [US2] Implement connectivity metric extraction (PLV, wPLI) for ROI pairs (C3-C4, C3-Cz, C4-Cz) and Global Mean in `code/02_feature_extraction.py`. **Output**: Append to `data/processed/spectral_power.csv`.
- [ ] T025 [US2] Assemble final feature matrix with subject IDs and conditions in `code/02_feature_extraction.py`. **Output**: `data/processed/feature_matrix.csv`.
- [ ] T026 [US2] Implement Ridge Regression with L2 regularization, 5-fold CV, and nested hyperparameter tuning in `code/03_modeling.py`. 
    - **Search Space**: `alpha = np.logspace(-3, 3, 10)`. 
    - **Scoring**: `neg_mean_squared_error`.
    - **Output**: Save best model to `models/ridge_model.pkl` and **full CV history** to `data/processed/model_cv_results.json` (schema: `best_alpha`, `best_score`, `cv_scores`, `feature_importance`).
- [ ] T027 [US2] Implement logic to flag outputs as 'Structural Validation Only' when in Fallback/Positive Control Mode (FR-002). **Dependency**: Must execute before T028.
- [ ] T028 [US2] **Verify Model Sensitivity** (Positive Control Mode only). 
    - **Logic**: If `mode_flag == 'Positive Control'`, verify `R² > 0` and `p < 0.05` for the injected signal. 
    - **Constraint**: Also verify `R² < 0.9` to prevent overfitting. 
    - **Action**: If check fails, log error and set `pipeline_status = 'broken'`.
    - **Dependency**: Requires T027 to have flagged the mode.
- [ ] T029 [US2] Add CPU-only execution constraints (no CUDA, no 8-bit quantization) to all modeling steps (NFR-001).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Validation, Sensitivity Analysis, and Reporting (Priority: P3)

**Goal**: Validate model with permutation testing, apply FDR correction, and perform sensitivity analysis.

**Independent Test**: Can be fully tested by running the validation module and verifying the output report contains a sensitivity sweep table and a corrected p-value.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T030 [P] [US3] Write unit test code for permutation test logic in `tests/test_validation.py`
- [ ] T031 [P] [US3] Write unit test code for FDR correction implementation in `tests/test_validation.py`
- [ ] T032 [P] [US3] Write integration test code for sensitivity analysis sweep in `tests/test_validation.py`

### Implementation for User Story 3

- [ ] T033 [US3] Implement permutation testing (with a default number of permutations, configurable). 
    - **Logic**: Shuffle target labels, re-fit model, store `null_r2`. 
    - **Convergence Check**: If `std(null_r2)` > 0.01, increase permutations until stable.
    - **Output**: `data/processed/perm_null_distribution.csv` with columns `permutation_id`, `null_r2`, `observed_r2`.
    - **P-Value Formula**: `p = (count(null_r2 >= observed_r2) + 1) / (total_permutations + 1)`.
- [ ] T034 [US3] Implement False Discovery Rate (FDR) correction for multiple EEG features in `code/04_validation.py`. **Output**: `data/processed/fdr_corrected_pvalues.csv`.
- [ ] T035 [US3] Implement sensitivity analysis: sweep p across a range of low values and R² across a range of moderate values. **Output**: `data/processed/sensitivity_table.csv`.
- [ ] T036 [US3] Calculate `stability_variance` from sensitivity table. **Success Criteria**: `variance ≤ 0.05`. **Action**: If `variance > 0.05`, **exit with code 1** (build failure).
- [ ] T037 [US3] Implement batch processing or epoch downsample logic to prevent memory overflow during permutation testing (NFR-001).
- [ ] T038 [US3] Generate final report in `docs/research_results.md` (Markdown). **Mandatory Sections**: 
    1. Introduction 
    2. Methods (pipeline config, seeds) 
    3. Results (R², p-values, sensitivity table, mode flags) 
    4. Discussion (limitations, Constitution VII blocker) 
    5. Appendix (raw data hashes).
- [ ] T039 [US3] Log runtime and peak RAM usage to verify NFR-001 (≤6h, ≤7GB) in `docs/research_results.md` (SC-003).

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T040a [P] Update `docs/quickstart.md` with installation steps, environment setup, and run commands.
- [ ] T040b [P] Create `docs/research.md` with the following required sections: 
    1. Introduction 
    2. Methods (pipeline config, seeds) 
    3. Results (R², p-values, sensitivity table, mode flags) 
    4. Discussion (limitations, Constitution VII blocker) 
    5. Appendix (raw data hashes).
- [ ] T040c [P] Update `docs/README.md` with project overview, architecture diagram, and contribution guidelines.
- [ ] T042a [P] Profile code for performance bottlenecks. Focus on: `01_ingest_preprocess.py` (epoching loops), `02_feature_extraction.py` (Welch's method loops), `03_modeling.py` (CV loops). Generate `logs/profile_report.txt`.
- [ ] T042b [P] Vectorize identified bottlenecks from T042a. Replace explicit loops with numpy/scipy vectorized operations. Verify runtime reduction.
- [ ] T043 [P] Add additional unit tests for edge cases (missing metadata, empty epochs) in `tests/unit/`.
- [ ] T044 Run quickstart.md validation to ensure all commands execute successfully.
- [ ] T045 [P] **Constitution VII Blocker Note**: Add explicit note in `docs/research_results.md` and `plan.md` that **Constitution Principle VII (Independent Dataset Validation)** is **BLOCKED** due to lack of public paired data. This is a **publication blocker** until a second dataset is identified.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 output (preprocessed data)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 output (model/feature matrix)

### Within Each User Story

- **Writing Tests** (T010-T012, T020-T022, T030-T032): Can be parallel to implementation.
- **Running Tests** (T045 and equivalents): MUST be after Implementation (T013-T018, etc.)
- Data download/checksum (T013-T014) before **Mode Detection** (T015)
- **Mode Detection** (T015) before **Synthetic Generation** (T016)
- **Synthetic Generation** (T016) before **Filtering** (T017) - *Critical for Positive Control Mode*
- Filtering (T017) before feature extraction (T023-T024)
- Feature extraction (T023-T024) before modeling (T026)
- Modeling (T026) before validation (T033)
- **Cross-Phase Dependency**: T028 (Verify Model) depends on T027 (Flag Mode) which depends on T016 (Synthetic Target). Explicitly: T016 -> T027 -> T028. T028 cannot run until T027 has flagged the mode.

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All **Writing Test Code** tasks for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all test code writing for User Story 1 together:
Task: "Write unit test code for checksum verification in tests/test_preprocess.py"
Task: "Write unit test code for mode detection logic in tests/test_preprocess.py"
Task: "Write unit test code for synthetic target generation in tests/test_preprocess.py"

# Launch all data ingestion tasks together:
Task: "Implement data download for PhysioNet EEG Motor Movement/Imagery Dataset in code/01_ingest_preprocess.py"
Task: "Implement SHA-256 checksum verification in code/01_ingest_preprocess.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Ingestion + Preprocessing + Synthetic Data)
4. **STOP and VALIDATE**: Test that data is ingested, checksummed, and synthetic targets are generated correctly.
5. Deploy/demo if ready.

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
   - Developer A: User Story 1 (Data Ingestion)
   - Developer B: User Story 2 (Feature Extraction & Modeling)
   - Developer C: User Story 3 (Validation & Reporting)
3. Stories complete and integrate independently.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing (TDD workflow)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Constraint**: All tasks must run on CPU-only CI (limited cores, 7GB RAM). No GPU, no 8-bit models, no large LLMs.
- **Critical Constraint**: Synthetic data in **Positive Control Mode** must have a known injected signal (coefficient 0.5 applied to sum of all band powers) across **ALL bands** (delta, theta, alpha, beta, gamma). Synthetic data in **Fallback Mode** must be decoupled (random noise).
- **Constitution VII Blocker**: The lack of an independent public dataset is a known blocker for final publication. This must be resolved before the project transitions to `research_accepted`.
- **Raw Data Preservation**: Raw files in `data/raw` MUST NEVER be modified after successful checksum verification. T013 handles download logic: if file exists and checksum matches, skip; if mismatch, halt. T014 sets permissions to read-only after T013 completes to ensure immutability for subsequent runs.