# Tasks: Investigating the Relationship Between Pupil Dilation and Cognitive Load During Visual Search

**Input**: Design documents from `/specs/001-pupil-dilation-cognitive-load/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root (per `plan.md` structure)
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

- [X] T001a [P] Create project directories: `code/`, `tests/`, `data/raw/`, `data/processed/`, `results/`, `state/`
- [X] T001b [P] Create `.gitignore` to exclude `data/`, `__pycache__/`, `*.pyc`, `results/`, and `state/`
- [X] T001c [P] Implement `scripts/verify_structure.py` to check directory layout against `plan.md` and generate `state/structure_check.yaml` with status "PASS" or "FAIL"

---

## Phase 2: Foundational (Blocking Prerequisites & Data Verification)

**Purpose**: Core infrastructure, configuration, and the mandatory Data Verification Hard Gate that MUST run before any user story.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. The Data Verification tasks (T002c) act as a hard gate.

### Data Verification Hard Gate (MUST precede all other Foundational tasks)

- [X] T002c [US1] Implement `code/verify_data_availability.py`: Parse the `# Verified datasets` block in `plan.md` and **perform internal validation** of dataset types.
 - **Logic**: Check if the block contains datasets.
 - **Hard Gate**: If the block contains **only** datasets that are NOT eye-tracking (e.,g., fMRI, EEG), **HALT** with Exit Code 1 and message: "ERROR: Spec cites invalid dataset types. Pipeline cannot proceed. Spec requires correction."
 - **Hard Gate**: If the block is empty, **HALT** with Exit Code 1 and message: "ERROR: No verified eye-tracking dataset found. Pipeline cannot proceed."
 - **Logic**: If a valid eye-tracking dataset is found, download it to `data/raw/`.
 - **Constraint**: Do NOT trust the block blindly. The task MUST validate dataset types against known types. If a contradiction exists between the block content and the known invalid types (e. g., fMRI datasets listed as eye-tracking), the pipeline MUST halt (Exit 1).
 - **Dependency**: None. This is the first task in Phase 2.

### Logging Infrastructure (Must follow Data Verification)

- [X] T005 [US1] Setup logging infrastructure: Initialize `code/logging_config.py` to define a `LoggingContext` class with methods `add_exclusion(type, count)` and `write_report(path)`. Initialize `results/quality_report.csv` with headers `[exclusion_type, count]` upon first call. **Verify** by asserting that calling `LoggingContext.add_exclusion` appends to the CSV correctly and that `results/quality_report.csv` exists with the correct schema. **Note: This task MUST follow T002c. Depends on T002c.**

### Configuration & Environment

- [X] T002a [P] Create `code/requirements.txt` with pinned versions: `pandas`, `numpy`, `scipy`, `statsmodels`, `scikit-learn`, `mne`, `pyyaml`, `tqdm`, `opencv-python-headless`, `requests`, `datasets`, `python-dotenv`, `radon`
- [ ] T002b [US1] Setup Python 3.11 virtual environment in `code/` and install dependencies. **Verify** by running `code/.venv/bin/python --version` and asserting output contains '3.11' using `grep -q '3.11'`. **Dependency**: Depends on T002a (requirements.txt must exist).
- [X] T003 [P] Create `code/.flake8` and `code/pyproject.toml` with linting rules (max-line-length=88, etc.); verify by running `black --check code/` and ensuring exit code 0
- [X] T004 [P] Create `code/config.yaml` with keys: `seeds` (int), `thresholds` (dict, default {0.40, 0.50, 0.60}), `paths` (dict), `aggregation` (bool, default false); verify by parsing in a test script `tests/test_config.py`
- [X] T006 [P] Create `code/data_model.py` defining classes: `Dataset(subject_id, trial_id, timestamp, pupil_diameter, x, y, search_time, target_salience, fixation_count)` and `ModelResult(coefficients, std_errors, p_values, log_likelihood)`
- [X] T007 [P] Implement `code/utils/provenance.py` with functions `hash_file(path)` and `write_meta(path, meta_dict)`; verify by generating `data/raw/*_meta.json` with keys `[hash, timestamp, source]`
- [X] T008 [P] Configure environment variables: Create `code/.env.example` with keys: `DATA_PATH`, `OPENNEURO_API_KEY`, `LOG_LEVEL`; update `code/main.py` (created in T018) to load these keys via `python-dotenv`; verify script fails gracefully with error message if keys are missing.
- [X] T002d [P] Create `generate_synthetic_test_data.py` ONLY for unit tests (flagged `--test-mode`); ensure it is NEVER called by the main pipeline and its output is hashed in `state/test_artifacts.yaml` only.

**Checkpoint**: Foundation ready + Data Verification passed - user story implementation can now begin

---

## Phase 3: User Story 1 - Compute Trial‑wise Pupil‑Load Correlations (Priority: P1) 🎯 MVP

**Goal**: Load raw eye-tracking data, preprocess signals, extract load proxies (including on-the-fly salience if needed), and compute correlations.

**Independent Test**: Run the pipeline on a single dataset and verify output CSV contains required columns and Pearson-r values.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Unit test for data loader validation in `tests/test_data_loader.py`
- [X] T011 [P] [US1] Unit test for blink interpolation logic in `tests/test_preprocess.py`
- [X] T012 [P] [US1] Integration test for full preprocessing pipeline in `tests/test_pipeline_us1.py`

### Implementation for User Story 1

- [ ] T013 [US1] Implement `code/preprocessing/load_data.py` to ingest raw files from verified eye-tracking sources (configured via `config.yaml` or `verify_data_availability.py` output) and convert to uniform CSV (`timestamp`, `x`, `y`, `pupil_diameter`)
- [X] T014 [US1] Implement `code/preprocessing/filter.py` with blink interpolation and low-pass filter (≤4 Hz) handling missing samples (>30% exclusion)
- [X] T015a [US1] Implement `code/preprocessing/features.py` (Part 1: Metadata) to extract load proxies from metadata: `search_time` and `fixation_count`. **Logic**: Read from trial metadata. If missing, log warning and set to `null`. **Output**: Append columns `search_time`, `fixation_count` to `data/processed/features.csv`.
- [X] T015b [US1] Implement `code/preprocessing/features.py` (Part 2: Salience) to compute `target_salience` on-the-fly from stimulus images using Gabor filter bank **ONLY IF** metadata is missing AND valid stimulus image data exists in `data/external/stimuli/`. **Read Gabor parameters (wavelength, sigma, gamma, orientations, scales) from `config.yaml`**. **IF** neither metadata nor valid image data exists, mark proxy as `UNFULFILLABLE` in output artifact `data/processed/features.csv`, log specific exclusion reason, and set `status` column to "UNFULFILLABLE" (do NOT skip silently or crash).
- [X] T016a [US1] Implement `code/analysis/metrics.py` to extract pupil metrics (peak, mean, temporally quantized distribution) from preprocessed time-series data. **Logic**: Compute `pupil_peak`, `pupil_mean`, and quantile values (e.g., 25th, 50th, 75th percentiles) for each trial. **Output**: Append columns `pupil_peak`, `pupil_mean`, `pupil_q25`, `pupil_q50`, `pupil_q75` to `data/processed/features.csv`.
- [ ] T016b [US1] Implement `code/analysis/correlations.py` (Part 1: Raw Correlations) to calculate Pearson correlations (peak/mean/quantized vs. proxies) for valid data. **Input**: `data/processed/features.csv`. **Output**: Write raw correlations to `results/correlations.csv` with columns: `metric`, `proxy`, `pearson_r`, `raw_p`, `method`. **Constraint**: This task produces intermediate data; the final artifact MUST be the FDR-corrected version from T016c. **State Hand-off**: Output file `results/correlations.csv` is consumed by T016c.
- [X] T016c [US1] Implement `code/analysis/correlations.py` (Part 2: FDR Correction) to apply Benjamini-Hochberg FDR correction to the results from T016b. **Input**: `results/correlations.csv` (column `raw_p`). **Output**: Add column `adj_p` to `results/correlations.csv`. **Constraint**: `adj_p` MUST replace `raw_p` as the primary reported p-value in the final artifact. **Dependency**: Depends on T016b.
- [X] T017 [US1] Implement quality report generation in `code/preprocessing/filter.py` using the `LoggingContext` interface defined in T005. The script must call `LoggingContext.add_exclusion` during preprocessing and `LoggingContext.write_report` at the end to append counts to `results/quality_report.csv` (headers initialized in T005) with columns `[exclusion_type, count]`. **Verify** that the file contains non-zero counts for at least one exclusion type if exclusions occurred.
- [X] T018 [US1] Create `code/main.py` orchestrator for US1 pipeline execution

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Fit Linear Mixed‑Effects Model (Priority: P2)

**Goal**: Fit LME model predicting pupil metrics from load proxies with subject random intercepts.

**Independent Test**: Execute LME script and verify model summary includes coefficients, SEs, p-values, and likelihood-ratio test.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [P] [US2] Unit test for VIF calculation and collinearity check in `tests/test_analysis.py`
- [X] T020 [P] [US2] Unit test for LME model fitting with missing predictor handling in `tests/test_analysis.py`

### Implementation for User Story 2

- [ ] T021a [US2] Implement `code/analysis/lme_model.py` (Part 1: VIF & Selection): Calculate Variance Inflation Factor (VIF) for *each* predictor. **Input**: `data/processed/features.csv`. **Logic**: If any VIF > 5, identify the predictor with the highest VIF. **Output**: Log the selected predictor for removal to `results/vif_report.log` and update `data/processed/features.csv` with a `dropped_predictor` flag if applicable. **State Hand-off**: Output log file `results/vif_report.log` is consumed by T021b.
- [ ] T024 [US2] Add validation for sufficient trials per subject (<20 triggers RuntimeError with message "Subject {id} has < 20 trials" UNLESS `config.yaml` aggregation flag is true, in which case **aggregate across subjects**). **Logic**: First, verify `config.yaml` exists. If the `aggregation` key is missing, default to `false` and issue a warning. If `false`, abort with error. If `true`, aggregate. **Constraint**: This task must run after T021a to ensure data integrity. **Dependency**: Depends on T021a.
- [ ] T021b [US2] Implement `code/analysis/lme_model.py` (Part 2: Model Fitting): Fit the LME model `pupil_metric ~ search_time + target_salience + fixation_count + (1|subject)`. **Input**: `data/processed/features.csv` and `results/vif_report.log`. **Logic**: If target salience is missing (UNFULFILLABLE), fit a reduced model excluding that predictor and log the reduction. If a predictor was selected for removal in T021a, fit the reduced model excluding that predictor. **State Hand-off**: Output fitted model object is passed to T021c. **Dependency**: Depends on T021a and T024.
- [ ] T021c [US2] Implement `code/analysis/lme_model.py` (Part 3: LRT & Output): Perform the Likelihood-Ratio Test (LRT) comparing the nested models (full vs. reduced) using the model object from T021b. **Output**: Output fixed-effect estimates, SEs, p-values, and likelihood-ratio test statistic to `results/model_summary.csv`. **Schema**: Include column `dropped_predictor` (string or null) to indicate which predictor was removed. **Dependency**: Depends on T021b.
- [X] T025 [US2] Output fixed-effect estimates, SEs, p-values to `results/model_summary.csv`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Simulated Real‑Time Load Classification Prototype (Priority: P3)

**Goal**: Deploy sliding-window logistic regression classifier and evaluate on held-out data.

**Independent Test**: Run classifier on test set and verify confusion matrix, accuracy, and ROC-AUC are reported.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T026 [P] [US3] Unit test for sliding window data slicing in `tests/test_classifier.py`
- [X] T027 [P] [US3] Unit test for sensitivity analysis logic in `tests/test_classifier.py`

### Implementation for User Story 3

- [X] T028a [US3] Initialize `results/classification_metrics.csv` with the correct schema: `threshold`, `accuracy`, `precision`, `recall`, `auc`, `ground_truth_source`. **Logic**: Create the file with headers if it does not exist. **Dependency**: None (prerequisite for T029).
- [X] T028 [US3] Implement `code/classification/classifier.py` with sliding-window logistic regression: use a **fixed-duration lookback window** for feature extraction, but update the classifier every **200ms**; use L2 regularization
- [ ] T029 [US3] Implement ground-truth labeling logic: if independent measure absent, label by median split of search time (strictly greater than median). **Constraint**: If 'search_time' from T015a is 'UNFULFILLABLE', log exclusion and continue with other available proxies, do NOT halt. **Documentation**: Explicitly write a `results/limitations.md` file documenting the "Search-Time Estimation" limitation and update `results/classification_metrics.csv` headers to include "Ground Truth: Search-Time Estimation". **Note**: This task must ensure the limitation is documented as per FR-011. **Dependency**: Depends on T028a.
- [X] T030 [US3] Implement `code/classification/evaluate.py` to compute accuracy, precision, recall, ROC-AUC on held-out set
- [ ] T031 [US3] Implement sensitivity analysis sweeping thresholds across values defined in `config.yaml` (defaulting to {0.40, 0.50, 0.60}) as defined in SC-004; output full metric tables AND calculate/report **relative decrease** or **stability** metrics to `results/sensitivity_analysis.csv`. **Definition**: 'Stability' is defined as AUC drop < 5% across the threshold sweep. Report this pass/fail condition. **Logic**: If 'thresholds' key is missing in `config.yaml`, use defaults {0.40, 0.50, 0.60}. **Output**: `results/sensitivity_analysis.csv` with columns `threshold`, `accuracy`, `auc`, `stability_status`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T033 [P] Documentation updates: Create `docs/pipeline.md` and update `README.md` with CLI usage and limitations. **Include**: The final report generation logic that consumes limitation notes from T029.
- [X] T034 [P] Refactor high-complexity functions: Use `radon cc` to identify functions in `code/preprocessing/` and `code/analysis/` with cyclomatic complexity > 15. Refactor identified functions to reduce complexity to < 15. Output list of refactored functions and new complexity scores to `results/complexity_report.txt`. **Note**: This is an optional internal metric, not a mandatory SSoT artifact.
- [ ] T035 [US3] Create and execute memory profiling script: Create `scripts/profile_memory.py` that imports `preprocessing` modules and logs peak RAM usage to `results/memory_profile.csv` using a memory profiler (e.g., `memory_profiler`). Execute the script against the **full real dataset** using streaming to ensure SC-005 (Whole Pipeline) is verified. Log the dataset size used for the test. **Verify** the pipeline completes within 5 hours and ≤ 6 GB RAM as per SC-005.
- [X] T036 [P] Additional unit tests for edge cases: Implement tests for corrupted timestamps, missing metadata, and excessive blink loss in `tests/test_edge_cases.py`.
- [X] T037 [P] Run `docs/quickstart.sh` validation: Execute `bash docs/quickstart.sh` and verify exit code 0 and presence of `results/correlations.csv`.
- [ ] T038 [P] Generate final quality report: Explicitly generate `results/quality_report.csv` as a distinct deliverable by consuming logs from T005/T017. **Verify** that the file exists and contains the correct schema `[exclusion_type, count]`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories (includes Data Verification Hard Gate)
 - **T002c** (Data Verification) MUST be the FIRST task in Phase 2.
 - **T005** (Logging) depends on T002c completion.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - **Depends on T015a/T015b/T016a (US1) completion** to determine data artifact state (target_salience column presence, pupil metrics). **Strict Order**: T015a/T015b must complete before T021a.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] (except T002c) can run in parallel
- Once Foundational phase completes, all user stories can start in parallel (if staffed)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for data loader validation in tests/test_data_loader.py"
Task: "Unit test for blink interpolation logic in tests/test_preprocess.py"

# Launch all models for User Story 1 together:
Task: "Implement data_loader.py to ingest raw files"
Task: "Implement preprocess.py with blink interpolation"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories, includes Data Verification)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

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
 - Developer A: User Story 1
 - Developer B: User Story 2
 - Developer C: User Story 3
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
- **Critical**: Do not proceed with US1/US2/US3 if T002c fails (invalid dataset detected)
- **Note on T021**: US2 depends on US1's data artifact state; ensure T015a/T015b/T016a completes before T021a runs. T021a, T021b, T021c are strictly sequential.
- **Note on T002c**: The task MUST validate dataset types (e.g., eye-tracking vs fMRI) and halt if the dataset type is invalid. Specific dataset IDs are not hard-coded; the check is based on dataset type metadata.