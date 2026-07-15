# Tasks: Neural Oscillations as a Biomarker for Predicting Response to Transcranial Direct Current Stimulation

**Input**: Design documents from `/specs/001-neural-oscillations-tDCS-biomarker/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[D]**: Dependent (must wait for specific upstream task)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001a [P] Create project structure. Execute the following command to establish the directory tree: `mkdir -p code/ code/utils/ tests/ data/raw data/processed data/synthetic models/ docs/ docs/contracts/ state/projects/`. **[FR-001]**
- [ ] T001b [P] Set restricted write permissions on `data/raw`. Execute: `chmod 555 data/raw` (read‑execute only). **[FR-001]** *(depends on T001a)*
- [ ] T002 [P] Initialize Python 3.11 project with `requirements.txt`. Execute: `echo -e "mne==1.7.0\nscikit-learn==1.4.0\nnumpy==1.26.0\npandas==2.1.0\nscipy==1.12.0\nstatsmodels==0.14.1\npyyaml==6.0.1\npytest==7.4.0" > requirements.txt`. Then execute `pip install -r requirements.txt` to install dependencies. Verify file content matches exactly. **[FR-001]**
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools with `pyproject.toml`. Define `target-version = "py311"` and exclude `data/`, `models/`, `state/`. **[FR-001]**

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Setup configuration management in `code/utils/config.py` for paths, seeds, and thresholds (p=0.05, R2_expected=0.1). Include constants for `BANDS = ['delta', 'theta', 'alpha', 'beta', 'gamma']` and `LOWER_FREQ_HZ = 1.0`. **[FR-004][US-4]**
- [ ] T005 [P] Implement I/O helpers in `code/utils/io_helpers.py` for CSV/Parquet loading, checksumming (SHA-256), and artifact hashing. Ensure `verify_checksum` function returns boolean and logs mismatches. **Mandatory**: Include a function `write_checksum_to_state` that writes successful checksums to `state/projects/PROJ-164-neural-oscillations-as-a-biomarker-for-p.yaml` as required by FR-005 and Constitution Principle III. **[FR-005]**
- [~] T006 [P] Create base data schema definitions in `specs/contracts/dataset.schema.yaml`. Define fields strictly matching spec data model: `subject_id`, `channel`, `time`, `voltage`, `condition`. Remove any fields not explicitly defined in spec.md (e.g., `mode_flag`). **[FR-006]**
- [~] T007 [P] Create output schema definitions in `specs/contracts/output.schema.yaml`. Define fields for `feature_matrix`, `model_metrics` strictly matching plan.md output artifacts. Remove any fields not explicitly defined (e.g., `sensitivity_table`). **[FR-007]**
- [~] T008 [P] Setup logging infrastructure to capture warnings, mode switches, and resource usage (stdout + `logs/pipeline.log`). Configure log rotation to prevent disk overflow. **[FR-008]**

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Verify existence of a single‑source paired EEG + tDCS dataset, then ingest and preprocess it. If no such dataset exists, terminate pipeline in **Data Insufficient Mode** (no synthetic data for inference).

### Source Verification (must run before any download or power analysis)

- [~] T011 [P] **Source Verification Task**: Search OpenNeuro, PhysioNet, Kaggle with query "EEG AND tDCS AND motor". Produce `verified_source_manifest.json` listing any single‑source paired dataset found (FR‑001, FR‑012, FR‑013). **Mandatory**: Explicitly populate the manifest with the search scope (OpenNeuro, PhysioNet, Kaggle) and the query string ("EEG AND tDCS AND motor") as required by FR-018. If none found, log "Data Insufficient: No single‑source paired dataset found" and set mode flag to **Data Insufficient**. **[FR-001][FR-012][FR-013][FR-018]**
- [~] T012 [D] **Mode Check Task**: Read `verified_source_manifest.json`. If mode flag is **Data Insufficient**, terminate pipeline gracefully (exit code 0) after writing the manifest. No further tasks are executed. **[FR-001]** *(depends on T011)*

### Power Analysis & Pre-Registration (Conditional on Data Existence)

- [~] T009 [D] Perform prospective power analysis *after* T011 confirms data existence. Compute minimum sample size required to detect an expected R² = 0.1 with 80 % power at α = 0.05 (FR‑007, FR‑008, US‑4). **Mandatory**: Generate `pre-registration.json` artifact containing the analysis plan hash, timestamp, and parameters (R² target, power, α, predictor count) **BEFORE** any data ingestion. If `N_actual < N_min`, set mode flag to **Underpowered** and skip downstream statistical inference. Output `power_analysis_report.json`. **[FR-007][FR-008][US-4][FR-016]** *(depends on T011)*

### Implementation (executed only if Primary Mode)

- [ ] T013 [US1] Implement data download for the verified paired dataset identified by T011 (if any) in `code/01_ingest_preprocess.py`. <!-- FAILED: unspecified -->
 - **URL**: derived from manifest entry.
 - **Output**: Save to `data/raw/` with pattern `sub-{subject_id}_run-{run_id}.edf`.
 - **Constraint**: Monitor RAM/CPU; log metrics to `logs/pipeline.log`. **[FR-012][FR-013]**
- [~] T015 [US1] **Data Alignment Check**: Verify subject overlap between EEG and tDCS within the single source (FR‑011). **Mandatory**: Run immediately after download (T013). If mismatch, set mode flag to **Data Insufficient** and terminate. **[FR-011]** *(depends on T013)*
- [ ] T014 [US1] Implement SHA‑256 checksum verification for all files in `data/raw/` and log results to `state/projects/PROJ-164-neural-oscillations-as-a-biomarker-for-p.yaml`. **Mandatory**: Use `write_checksum_to_state` helper to write successful checksums to the state file. Set files read‑only on success. **[FR-005]** *(depends on T013)*
- [ ] T016 [US1] **Dataset Representativeness Check**: Analyze dataset metadata to flag if the dataset is small (<50 subjects) or from a single population (e.g., healthy young adults). **Mandatory**: Implement the flagging logic and record this flag explicitly in the final output (e.g., `results.json` and `docs/research_results.md`) as required by FR-021. **[FR-021]** *(depends on T013)*
- [ ] T017 [US1] Implement band‑pass filtering (1–45 Hz) and common‑average referencing in `code/01_ingest_preprocess.py`. Write filtered epochs to `data/processed/`. **[FR-002][FR-006]**
- [ ] T018 [US1] Implement epoching (fixed‑duration windows) and automated bad‑channel detection (z‑score > 5). Output `data/processed/epochs.fif`. **[FR‑002][FR‑006]**

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (only in Primary Mode).

### Tests for User Story 1 (OPTIONAL)

- [ ] T010 [P] [US1] Write unit test code for checksum verification in `tests/test_preprocess.py`. Test case: Verify SHA‑256 match/mismatch handling.
- [ ] T011a [P] [US1] Write unit test code for mode detection logic (Primary vs. Data Insufficient) in `tests/test_preprocess.py`. Test case: Verify termination when no paired dataset is found.

- [ ] T045 [US1] **Run** all unit tests (T010‑T011a). **Pass Criteria**: All tests pass. If fail, halt pipeline.

---

## Phase 4: User Story 2 - Feature Extraction and Statistical Modeling (Priority: P2)

**Goal**: Compute spectral power and connectivity metrics, then fit a ridge regression model (or Rank‑Ridge if non‑normal). Executes only in Primary Mode.

- [ ] T023 [P] Implement spectral power density extraction (Delta, Theta, Alpha, Beta, Gamma) using Welch's method in `code/02_feature_extraction.py`. Output `data/processed/spectral_power.csv`. **[FR-003]**
- [ ] T024 [P] Implement connectivity metric extraction (PLV, wPLI) for ROI pairs (C3‑C4, C3‑Cz, C4‑Cz) in `code/02_feature_extraction.py`. Append results to `spectral_power.csv`. **[FR-004]**
- [ ] T025 [P] Assemble final feature matrix with subject IDs in `code/02_feature_extraction.py`. Output `data/processed/feature_matrix.csv`. **[FR-005]**
- [ ] T027 [P] **Mode‑Gate Before Modeling**: Read mode flag; if not **Primary**, skip modeling tasks and log "Modeling Skipped: Data Insufficient". **[FR-001][FR-004]**
- [ ] T028 [D] **Normality Check**: Perform Shapiro‑Wilk on tDCS response (FR‑009). **Mandatory**: If non-normal (p < 0.05), switch to **Rank-Ridge regression** (non-parametric) and explicitly execute the Rank-Ridge model fitting as the replacement for standard Ridge. Log the change and the model type used. **[FR‑009]** *(depends on T025)*
- [ ] T026 [D] Implement **nested cross‑validation** for Ridge/Rank-Ridge Regression:
 - **Inner loop**: 5‑fold CV to select α from a logarithmically spaced range spanning multiple orders of magnitude.
 - **Outer loop**: 5‑fold CV to evaluate model performance (R², coefficients).
 - **Logic**: If T028 determined data is non-normal, execute Rank-Ridge; otherwise, execute standard Ridge.
 - Save best model to `models/ridge_model.pkl` (or `rank_ridge_model.pkl`) and CV history to `data/processed/model_cv_results.json`. **[FR-004]** *(depends on T028)*

**Checkpoint**: User Stories 1 & 2 should now work independently.

### Tests for User Story 2 (OPTIONAL)

- [ ] T020 [P] [US2] Write unit test code for spectral power calculation (Welch) in `tests/test_feature_extraction.py`.
- [ ] T021 [P] [US2] Write unit test code for connectivity metrics (PLV, wPLI) in `tests/test_feature_extraction.py`.
- [ ] T022 [P] [US2] Write integration test ensuring modeling is skipped when mode flag is **Data Insufficient**.

---

## Phase 5: User Story 3 - Validation, Sensitivity Analysis, and Reporting (Priority: P3)

**Goal**: Validate model with permutation testing, apply FDR correction, perform sensitivity analysis, and generate final report.

- [ ] T033 [D] Implement permutation testing: shuffle target labels, refit model, collect null R² distribution (≥ 1000 permutations if N ≥ 30, else log skip). Compute p‑value and **also compute Kolmogorov‑Smirnov statistic and p-value** to assess uniformity of the null distribution. Output `data/processed/perm_null_distribution.csv` and `data/processed/ks_test.json`. **[FR‑019]** *(depends on T026)*
- [ ] T034 [P] Implement Benjamini‑Hochberg FDR correction for feature‑level p-values. Output `data/processed/fdr_corrected_pvalues.csv`. **[FR-014]**
- [ ] T035 [P] Implement sensitivity analysis: sweep significance thresholds {0.01, 0.05, 0.1} and configurable R² thresholds. Output `data/processed/sensitivity_table.csv`. **[FR-006]**
- [ ] T036 [P] Calculate stability variance from `sensitivity_table.csv`. **Mandatory**: Output the calculated variance value to `data/processed/stability_variance.json`. Log a warning if variance > 0.05. **[SC‑004]**
- [ ] T037 [P] Ensure batch processing or down‑sampling during permutation testing to stay within 7 GB RAM (NFR-001). **[NFR-001]**
- [ ] T038 [P] Generate final research report `docs/research_results.md` with mandatory sections (Introduction, Methods, Results, Discussion, Appendix). **Mandatory**: Include KS statistic/p-value by parsing `data/processed/ks_test.json` (if it exists). Include FDR-adjusted p-values. Include sensitivity table. **Mandatory**: Read `data/processed/stability_variance.json` and include the stability variance value in the report. Include explicit mode flags. **[SC‑001][FR‑018][FR‑019][SC‑004]**
- [ ] T039b [P] Implement runtime monitor in `code/main.py`. Abort if total runtime exceeds 6 h, log runtime metrics to the report. **[NFR-001][SC‑003]**

### Independent Test

- [ ] T032 [P] Write unit test for KS test implementation in `tests/test_validation.py`.
- [ ] T033a [P] Write integration test confirming that when `N < 30` permutation testing is skipped with appropriate log entry.

---

## Phase 6: Independent Dataset Evaluation (Constitution VII)

**Goal**: Evaluate the trained biomarker on a *real* independent public dataset (e.g., Kaggle EEG Motor Imagery) if available.

- [ ] T050 [D] Search Kaggle (or other public repo) for a dataset containing BOTH raw EEG and paired tDCS motor scores. **Mandatory**: If found, download, run the full pipeline (Phases 3‑5) on this dataset, and record comparative metrics. **Mandatory**: If not found, log "Skipped: No independent dataset found", flag the generalizability check as "Skipped" in the final report, and **continue** the pipeline without halting. **[FR‑020][Principle VII]** *(depends on T038)*

---

## Phase N: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T040a [P] Update `docs/quickstart.md` with installation steps, environment setup, and run commands. **[SC‑004]**
- [ ] T041 [P] Create `docs/research.md` containing detailed narrative (Introduction, Methods, Results, Discussion, Appendix). **[SC‑002][FR‑018]**
- [ ] T040c [P] Update `docs/README.md` with project overview, architecture diagram, and contribution guidelines. **[SC‑001]**
- [ ] T042a [P] Profile code for performance bottlenecks (ingestion, feature extraction, modeling). Generate `logs/profile_report.txt`. **[NFR-001]**
- [ ] T042b [P] Vectorize identified bottlenecks; verify runtime reduction. **[NFR-001]**
- [ ] T043 [P] Add additional unit tests for edge cases (missing metadata, empty epochs) in `tests/unit/`. **[SC‑005]**
- [ ] T044 [P] Run quickstart validation to ensure all commands execute successfully. **[SC‑003]**

---

## Dependencies & Execution Order

### Phase Dependencies
- **Setup (Phase 1)** → **Foundational (Phase 2)** → **User Stories (Phase 3‑5)** → **Independent Dataset (Phase 6)** → **Polish (Phase N)**
- All tasks marked **[P]** can run in parallel when their preceding phase is complete.

### User Story Dependencies
- **US 1** must complete (including mode flag) before **US 2** and **US 3** can start.
- **US 2** requires outputs from **US 1** (preprocessed epochs).
- **US 3** requires model outputs from **US 2**.
- **Phase 6** runs after **US 3** (or after **US 2** if primary mode was never entered).

### Parallel Opportunities
- Setup and Foundational tasks are fully parallel.
- Test‑code authoring tasks can run alongside implementation within each user story.

---

*All tasks are designed to run on CPU‑only CI with ≤ 7 GB RAM, ≤ 6 h runtime, and no GPU or large‑model dependencies.*