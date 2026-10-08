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
- [X] T005a [P] [General] Implement `code/utils/logging_config.py`: Define a `LoggingContext` class with methods `add_exclusion(type, count)` and `write_report(path)`. **Verify** by instantiating the class and asserting methods exist. **Dependency**: None. This is a foundational setup task. **Schema**: The `write_report` method must initialize `results/quality_report.csv` with columns `exclusion_type, count`.

---

## Phase 2: Foundational (Blocking Prerequisites & Data Verification)

**Purpose**: Core infrastructure, configuration, and the mandatory Data Verification Hard Gate that MUST run before any user story.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. The Data Verification tasks (T002c) act as a hard gate.

### Environment Setup (Must precede Data Verification)

- [X] T002a [P] Create `code/requirements.txt` with **pinned versions**: `pandas==2.0.3`, `numpy==1.24.3`, `scipy==1.10.1`, `statsmodels==0.14.1`, `scikit-learn==1.2.2`, `mne==1.5.0`, `pyyaml==6.0.1`, `tqdm==4.65.0`, `opencv-python-headless==4.8.0.74`, `requests==2.31.0`, `datasets==2.14.0`, `python-dotenv==1.0.0`, `radon==5.1.0`, `memory_profiler==0.61.0`. **Verify** by running `pip install -r code/requirements.txt` and ensuring exit code 0.
- [X] T002b [P] [US1] Setup a Python virtual environment in `code/` and install dependencies. **Verify** by running `code/.venv/bin/python --version` and asserting output contains '3.11' using `grep -q '3.11'`. **Dependency**: Depends on T002a (requirements.txt must exist).

### Data Verification Hard Gate (MUST precede all other Foundational tasks)

- [X] T002c [General] Implement `code/verify_data_availability.py`: Parse the `# Verified datasets` block in `plan.md`.
 - **Logic**: Check if the block contains datasets.
 - **Dynamic Validation**: Use the `datasets` library (`datasets.get_dataset` or `openneuro-cli` metadata API) to fetch dataset metadata and validate the dataset type (eye-tracking vs fMRI). **Do NOT** hard-code ID rejection.
 - **Hard Gate**: If the dataset type is NOT eye-tracking (e., fMRI), **HALT** with Exit Code 1 and message: "ERROR: Dataset {id} is not an eye-tracking dataset. Pipeline cannot proceed."
 - **Hard Gate**: If the block is empty or contains no valid eye-tracking dataset IDs, **HALT** with Exit Code 1 and message: "ERROR: No verified eye-tracking dataset found. Pipeline cannot proceed."
 - **Logic**: If a valid eye-tracking dataset is found (type validated), download it to `data/raw/`.
 - **Constraint**: Do NOT trust the block blindly. The task MUST validate against the dataset type metadata. If type is invalid, halt.
 - **Error Handling**: If the API is unreachable, halt with "ERROR: Metadata API unreachable. Cannot verify dataset type."
 - **Dependency**: Depends on T002a/T002b (Python environment must exist).

### Logging Infrastructure (Must follow Data Verification)

- [X] T005b [P] [US1] Implement `code/utils/logging_config.py` (CSV Initialization): Initialize `results/quality_report.csv` with headers `[exclusion_type, count]` upon first call to `LoggingContext.write_report`. **Verify** by calling `write_report` and asserting the file exists with correct headers. **Dependency**: Depends on T005a.
- [X] T005c [P] [US1] Implement `tests/test_logging.py`: Verify that calling `LoggingContext.add_exclusion` appends to the CSV correctly and that `results/quality_report.csv` exists with the correct schema. **Dependency**: Depends on T005b.

- [X] T003 [P] Create `code/.flake8` and `code/pyproject.toml` with linting rules (max-line-length=88, etc.); verify by running `black --check code/` and ensuring exit code 0
- [X] T004 [P] Create `code/config.yaml` with keys: `seeds` (int), `thresholds` (dict, default {0.40, 0.50, 0.60}), `paths` (dict), `aggregation` (bool, default true), `gabor` (dict, default {wavelength: 1.0, sigma: 1.0, gamma: 0.5, orientations: multiple, scales: [2]}); verify by parsing in a test script `tests/test_config.py`
- [X] T006 [P] Create `code/data_model.py` defining classes: `Dataset(subject_id, trial_id, timestamp, pupil_diameter, x, y, search_time, target_salience, fixation_count)` and `ModelResult(coefficients, std_errors, p_values, log_likelihood)`. **Constraint**: These classes must be serializable to `data/processed/features.csv` and `results/model_summary.csv` respectively (e.g., inherit from `pandas.DataFrame` or provide a `.to_csv()` method). **Dependency**: None.
- [X] T007 [P] Implement `code/utils/provenance.py` with functions `hash_file(path)` and `write_meta(path, meta_dict)`; verify by generating `data/raw/*_meta.json` with keys `[hash, timestamp, source]`
- [X] T008 [P] Configure environment variables: Create `code/.env.example` with keys: `DATA_PATH`, `OPENNEURO_API_KEY`, `LOG_LEVEL`; update `code/main.py` (created in T018) to load these keys via `python-dotenv`; verify script fails gracefully with error message if keys are missing.
- [X] T002d [P] Create `generate_synthetic_test_data.py` ONLY for unit tests (flagged `--test-mode`); ensure it is NEVER called by the main pipeline and its output is hashed in `state/test_artifacts.yaml` only.

**Checkpoint**: Foundation ready + Data Verification passed - user story implementation can now begin

---

## Phase 3: User Story 1 - Compute Trial‑wise Pupil‑Load Correlations (Priority: P1) 🎯 MVP

**Goal**: Load raw eye-tracking data, preprocess signals, extract load proxies (including on-the-fly salience if needed), and compute correlations.

**Independent Test**: Run the pipeline on a single dataset and verify output CSV contains required columns and Pearson-r values.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these test files first (TDD), but **execution** of integration tests (T012) depends on implementation (T013/T014).

- [X] T010 [P] [US1] Unit test for data loader validation in `tests/test_data_loader.py`: Implement `test_load_edf_raises_on_missing_file` (asserts FileNotFoundError), `test_load_csv_invalid_columns` (asserts ValueError), and `test_load_edf_valid_file` (asserts output schema). **Dependency**: None (Writing only; Execution depends on T013).
- [X] T011 [P] [US1] Unit test for blink interpolation logic in `tests/test_preprocess.py`: Implement `test_interpolate_short_gaps` (asserts gaps < 200ms are interpolated), `test_exclude_long_gaps` (asserts gaps > 200ms are excluded), and `test_blink_detection` (asserts blink events are detected). **Dependency**: None (Writing only; Execution depends on T014).
- [X] T012 [P] [US1] Integration test for full preprocessing pipeline in `tests/test_pipeline_us1.py`: Implement `test_full_pipeline_produces_csv` (asserts `data/processed/raw_converted.csv` exists with correct schema), `test_blink_interpolation_applied` (asserts interpolated values exist), and `test_timestamp_validation` (asserts non-monotonic trials are excluded). **Dependency**: **Writing** depends on None; **Execution** depends on T013 and T014.

### Implementation for User Story 1

- [X] T038 [P] [US1] Implement `code/preprocessing/stream_loader.py` to support streaming large datasets from HuggingFace/OpenNeuro.
 - **Logic**: Use `datasets.load_dataset(name, split=..., streaming=True)` to iterate chunks.
 - **Constraint**: Do NOT load the full dataset into RAM. Accumulate statistics online (mean, variance, counts) to avoid memory overflow.
 - **Constraint**: If a specific chunk fails to download, log the error and continue to the next chunk; do NOT halt the entire pipeline unless the source is completely unreachable.
 - **Output**: A unified `data/processed/streamed_features.csv` or a set of chunked files that are merged into the final features file.
 - **Dependency**: Depends on T002c (verified source).

- [X] T039 [P] [US1] Update `code/preprocessing/load_data.py` to explicitly call `stream_loader.py` when the dataset size (estimated from metadata) exceeds 2GB.
 - **Logic**: Check `config.yaml` for `force_streaming` flag or dataset size metadata. If > 2GB, route to streaming path.
 - **Constraint**: Ensure the output schema of the streaming path matches the non-streaming path exactly to maintain SSoT.
 - **Dependency**: Depends on T038.

- [X] T013 [US1] Implement `code/preprocessing/load_data.py` to ingest raw eye-tracking files (`.edf`, `.csv`) from verified eye-tracking sources (configured via `config.yaml` or `verify_data_availability.py` output).
 - **Logic**: Parse raw files and convert to a uniform CSV schema.
 - **Output**: `data/processed/raw_converted.csv` with columns: `timestamp` (float, ms), `x` (float), `y` (float), `pupil_diameter` (float, mm).
 - **Constraint**: The task MUST handle both `.edf` (using `mne` or `edfread`) and `.csv` formats.
 - **Constraint**: The task MUST fail loudly if the real dataset fetch fails; no synthetic fallbacks are permitted.
 - **Dependency**: Depends on T002c (valid dataset must be downloaded) and T038/T039 (streaming logic).

- [X] T014 [US1] Implement `code/preprocessing/filter.py` with blink interpolation and low-pass filter (≤4 Hz) handling missing samples (>30% exclusion). **Constraint**: Must use a **Butterworth 4th order** low-pass filter with a **cutoff frequency ≤ 4 Hz**. **Verify** by applying to a synthetic signal and checking frequency response. **Dependency**: Depends on T013.

- [X] T015a [US1] Implement `code/preprocessing/features.py` (Part 1: Metadata) to extract load proxies from metadata: `search_time` and `fixation_count`. **Logic**: Read from trial metadata. If missing, log warning and set to `null`. **Output**: Append columns `search_time`, `fixation_count` to `data/processed/features.csv`. **Dependency**: Depends on T014.

- [X] T015b [US1] Implement `code/preprocessing/features.py` (Part 2: Metadata Handling) to handle missing `target_salience` in metadata. **Logic**: If metadata is missing, check for valid stimulus image data in `data/external/stimuli/`. **Output**: Flag `target_salience` as `NEEDS_COMPUTATION` in `data/processed/features.csv`. **Dependency**: Depends on T015a.

- [X] T015c [US1] Implement `code/preprocessing/features.py` (Part 3: On-the-Fly Salience) to compute `target_salience` from stimulus images using Gabor filter bank **ONLY IF** `target_salience` is flagged as `NEEDS_COMPUTATION` and valid image data exists. **Read Gabor parameters (wavelength=1.0, sigma=1.0, gamma=0.5, orientations=4, scales=2) from `config.yaml` (default values if missing)**. **Image Mapping**: Assume images are located at `data/external/stimuli/{subject_id}/{trial_id}.png` (or .jpg). **IF** neither metadata nor valid image data exists, log warning "Target salience missing; skipping proxy" and skip that proxy while still completing the others (do NOT mark as UNFULFILLABLE or halt). **Output**: Append column `target_salience` to `data/processed/features.csv` with computed values or `null` if skipped. **Dependency**: Depends on T015b and T004.

- [X] T016a [US1] Implement `code/analysis/metrics.py` to extract pupil metrics (peak, mean, temporally quantized distribution) from preprocessed time-series data. **Logic**: Compute `pupil_peak`, `pupil_mean`, and quantile values (e.g., 25th, 50th, 75th percentiles) for each trial. **Output**: Append columns `pupil_peak`, `pupil_mean`, `pupil_q25`, `pupil_q50`, `pupil_q75` to `data/processed/features.csv`. **Dependency**: Depends on T014.

- [X] T016b [US1] Implement `code/analysis/correlations.py` (Part 1: Raw Correlations) to calculate Pearson correlations (peak/mean/quantized vs. proxies) for valid data. **Input**: `data/processed/features.csv`. **Output**: Write raw correlations to `results/correlations.csv` with columns: `metric`, `proxy`, `pearson_r`, `raw_p`, `method`. **Constraint**: This task produces intermediate data; the final artifact MUST be the FDR-corrected version from T016c. **State Hand-off**: Output file `results/correlations.csv` is consumed by T016c. **Dependency**: Depends on T016a.

- [X] T016c [US1] Implement `code/analysis/correlations.py` (Part 2: FDR Correction) to apply Benjamini-Hochberg FDR correction to the results from T016b. **Input**: `results/correlations.csv` (column `raw_p`). **Output**: Add column `adj_p` to `results/correlations.csv`. **Constraint**: `adj_p` MUST replace `raw_p` as the primary reported p-value in the final artifact. **Dependency**: Depends on T016b.

- [X] T017 [US1] Implement quality report generation in `code/preprocessing/filter.py` using the `LoggingContext` interface defined in T005a. The script must call `LoggingContext.add_exclusion` during preprocessing and `LoggingContext.write_report` at the end to append counts to `results/quality_report.csv` (headers initialized in T005b) with columns `[exclusion_type, count]`. **Verify** that the file contains non-zero counts for at least one exclusion type if exclusions occurred. **Dependency**: Depends on T005b.

- [X] T018 [US1] Create `code/main.py` orchestrator for US1 pipeline execution

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Fit Linear Mixed‑Effects Model (Priority: P2)

**Goal**: Fit LME model predicting pupil metrics from load proxies with subject random intercepts.

**Independent Test**: Execute LME script and verify model summary includes coefficients, SEs, p-values, and likelihood-ratio test.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [P] [US2] Unit test for VIF calculation and collinearity check in `tests/test_analysis.py`: Implement `test_vif_drops_predictor_when_above_5` (asserts highest VIF predictor is dropped), `test_vif_no_drop_when_below_5` (asserts no drop if all VIF < 5), and `test_vif_reduced_model` (asserts reduced model is fitted). **Dependency**: None.
- [X] T020 [P] [US2] Unit test for LME model fitting with missing predictor handling in `tests/test_analysis.py`: Implement `test_lme_fits_with_missing_salience` (asserts reduced model is fitted if salience missing), `test_lme_fits_with_dropped_predictor` (asserts reduced model is fitted if predictor dropped), and `test_lme_output_schema` (asserts output schema is correct). **Dependency**: None.

### Implementation for User Story 2

- [X] T024 [US2] Implement `code/analysis/trial_validation.py` (Part 1: Trial Count Validation): Validate sufficient trials per subject (<20 triggers behavior based on `config.yaml`). **Logic**: Check `config.yaml` for `aggregation` key. If `aggregation` is `true` OR if the key is **missing** (default to `true` per Spec Edge Cases), **aggregate across subjects** (concatenate rows from all subjects into a single dataset without subject-level grouping). If `aggregation` is `false` and any subject has < 20 trials, **abort** with error "Subject {id} has < 20 trials". **Input**: `data/processed/features.csv`. **Output**: Log validation status to `results/trial_validation.log`. **Dependency**: Depends on T015a/T015b/T016a (US1 completion) to ensure data integrity.

- [X] T021a [US2] Implement `code/analysis/vif_check.py` (Part 1: VIF & Selection): Calculate Variance Inflation Factor (VIF) for *each* predictor. **Input**: `data/processed/features.csv`. **Logic**: If any VIF > 5, identify the predictor with the highest VIF. **Output**: Log the selected predictor for removal to `results/vif_report.log` with schema: `predictor_name, vif_score`. **State Hand-off**: Output log file `results/vif_report.log` is consumed by T021b. **Dependency**: Depends on T024, T015a, T015b, T016a.

- [X] T021b [US2] Implement `code/analysis/lme_fit.py` (Part 2: Model Fitting): Fit the LME model `pupil_metric ~ search_time + target_salience + fixation_count + (1|subject)`. **Input**: `data/processed/features.csv` and `results/vif_report.log`. **Logic**: If target salience is missing (null), fit a reduced model excluding that predictor and log the reduction. If a predictor was selected for removal in T021a, fit the reduced model excluding that predictor. **State Hand-off**: Output fitted model object is passed to T021c. **Dependency**: Depends on T021a and T024.

- [X] T021c [US2] Implement `code/analysis/lrt_test.py` (Part 3: LRT & Output): Perform the Likelihood-Ratio Test (LRT) comparing the nested models (full vs. reduced) using the model object from T021b. **Output**: Output fixed-effect estimates, SEs, p-values, and likelihood-ratio test statistic to `results/model_summary.csv`. **Schema**: Include column `dropped_predictor` (string or null) to indicate which predictor was removed. **Dependency**: Depends on T021b.

- [X] T025 [US2] Output fixed-effect estimates, SEs, p-values to `results/model_summary.csv`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Simulated Real‑Time Load Classification Prototype (Priority: P3)

**Goal**: Deploy sliding-window logistic regression classifier and evaluate on held-out data.

**Independent Test**: Run classifier on test set and verify confusion matrix, accuracy, and ROC-AUC are reported.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T026 [P] [US3] Unit test for sliding window data slicing in `tests/test_classifier.py`: Implement `test_sliding_window_handles_gap` (asserts gap > 200ms triggers reset and interpolation), `test_sliding_window_feature_extraction` (asserts features are extracted correctly), and `test_sliding_window_output` (asserts output shape is correct). **Dependency**: None.
- [X] T027 [P] [US3] Unit test for sensitivity analysis logic in `tests/test_classifier.py`: Implement `test_sensitivity_analysis_sweep` (asserts thresholds are swept), `test_sensitivity_analysis_stability` (asserts stability metric is calculated), and `test_sensitivity_analysis_output` (asserts output schema is correct). **Dependency**: None.

### Implementation for User Story 3

- [X] T028a [US3] Initialize `results/classification_metrics.csv` with the correct schema: `threshold`, `accuracy`, `precision`, `recall`, `auc`, `ground_truth_source`. **Logic**: Create the file with headers if it does not exist. **Dependency**: None (prerequisite for T029).
- [X] T028 [US3] Implement `code/classification/classifier.py` with sliding-window logistic regression: use a **fixed-duration lookback window** for feature extraction, but update the classifier every **200ms**; use L2 regularization
- [X] T029 [US3] Implement ground-truth labeling logic and documentation.
 - **Logic**: If independent measure absent, label by median split of search time (strictly greater than median; exclude trials where search_time == median to handle ties).
 - **Constraint**: If 'search_time' from Ta is 'null', log exclusion and continue with other available proxies, do NOT halt.
 - **Documentation**: Write `results/limitations.md` with content: "This project uses search-time as a proxy for cognitive load. Independent ground truth was not available. Output is labeled as 'Search-Time Estimation'."
 - **Schema Update**: Update `results/classification_metrics.csv` headers to include `ground_truth_source` with value "Search-Time Estimation" if independent truth is missing. **Explicit Value**: If independent truth is missing, the `ground_truth_source` column in data rows MUST be set to the string "Search-Time Estimation".
 - **Dependency**: Depends on T028a, T015a, and T028.
- [X] T030 [US3] Implement `code/classification/evaluate.py` to compute accuracy, precision, recall, ROC-AUC on held-out set
- [X] T031 [US3] Implement sensitivity analysis sweeping thresholds across values defined in `config.yaml` (defaulting to a range of moderate thresholds) as defined in SC-004; output full metric tables AND calculate/report **relative decrease** or **stability** metrics to `results/sensitivity_analysis.csv`. **Definition**: 'Stability' is defined as AUC drop < 5% across the threshold sweep. Report this pass/fail condition. **Logic**: If 'thresholds' key is missing in `config.yaml`, use defaults. If `config.yaml` is missing, create it with defaults. **Output**: `results/sensitivity_analysis.csv` with columns `threshold`, `accuracy`, `auc`, `stability_status`. **Dependency**: Depends on T029, T028, and T030.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T033 [P] Documentation updates: Create `docs/pipeline.md` and update `README.md` with CLI usage and limitations. **Include**: The final report generation logic that consumes limitation notes from T029.
- [X] T034 [P] Refactor high-complexity functions: Use `radon cc` to identify functions in `code/preprocessing/` and `code/analysis/` with cyclomatic complexity > 15. Refactor identified functions to reduce complexity to < 15. Output list of refactored functions and new complexity scores to `results/complexity_report.txt`. **Note**: This is an optional internal metric, not a mandatory SSoT artifact.
- [X] T035 [US3] Create and execute memory profiling script: Create `scripts/profile_memory.py` that imports `preprocessing` modules and logs peak RAM usage to `results/memory_profile.csv` using the `memory_profiler` library. Execute the script against the **full real dataset** (the verified source found in T002c) using streaming to ensure SC-005 (Whole Pipeline) is verified. Log the dataset size used for the test. **Verify** the pipeline completes within **5 hours** AND ≤ 6 GB RAM as per SC-005. **Output**: `results/memory_profile.csv` with columns `step`, `peak_ram_gb`, `duration_hours`, `timestamp`. **Constraint**: If no valid real dataset is found (e.g., T002c passed but no data available), log "SKIPPED: No valid real dataset available" and do not halt. **Dependency**: Depends on T002c (valid dataset must be found).
- [X] T036 [P] Additional unit tests for edge cases: Implement tests for corrupted timestamps, missing metadata, and excessive blink loss in `tests/test_edge_cases.py`.
- [X] T037 [P] Run `docs/quickstart.sh` validation: Execute `bash docs/quickstart.sh` and verify exit code 0 and presence of `results/correlations.csv`.

---

## Phase 7: Revision & Compliance (Addressing Review Concerns)

**Purpose**: Improvements that affect multiple user stories (Streaming integration moved to Phase 2)

- [X] T040 [P] [US1] Refactor `code/preprocessing/features.py` to ensure `target_salience` computation (Gabor filters) is also streaming-compatible.
 - **Logic**: Process stimulus images in batches if the `data/external/stimuli/` directory is large.
 - **Constraint**: If image processing is required, use `opencv-python-headless` and process images one-by-one or in small batches to stay within RAM limits.
 - **Dependency**: Depends on T015c and T039.
- [X] T041 [P] [US3] Update `code/classification/evaluate.py` to explicitly log the dataset size and streaming method used during evaluation.
 - **Logic**: Record `dataset_size_gb`, `streaming_mode` (true/false), and `peak_ram_gb` in `results/classification_metrics.csv` or a dedicated `results/compute_log.csv`.
 - **Dependency**: Depends on T035 and T039.
- [X] T042 [P] [General] Add a "Compute Feasibility" check to `code/main.py` that runs before the full pipeline.
 - **Logic**: Estimate RAM usage based on dataset size and task complexity. If estimated RAM > 6GB, trigger the streaming path automatically or abort with a clear message suggesting the `--stream` flag.
 - **Dependency**: Depends on T039.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories (includes Data Verification Hard Gate)
 - **T002c** (Data Verification) MUST be the FIRST task in Phase 2 **after** T002a/T002b.
 - **T005a** (Logging Setup) depends on None (moved to Phase 1).
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 6)**: Depends on all desired user stories being complete
- **Revision (Phase 7)**: Depends on Phase 6 completion and specific reviewer feedback regarding data size and streaming.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - **Depends on T015a/T015b/T016a (US1) completion** to determine data artifact state (target_salience column presence, pupil metrics). **Strict Order**: T015a/T015b/T016a must complete before T021a.
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
- Revision tasks (T038-T042) can run in parallel with each other but depend on the core US1 implementation.

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

### Revision Strategy

Once the core pipeline is functional, the team should address the streaming and memory constraints (Phase 7) to ensure the pipeline can handle large real-world datasets without violating the 6GB RAM constraint.

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
- **Note on T002c**: The task MUST validate dataset type (e.g., eye-tracking vs fMRI) dynamically using metadata or API. If type is invalid, halt with error. If type is valid, proceed regardless of ID. **UPDATED**: The task now dynamically validates dataset type, removing hardcoded ID rejection.
- **Note on T013**: The data loader MUST fail loudly if the real dataset fetch fails; no synthetic fallbacks are permitted.
- **Note on T035**: Memory profiling must use streaming to handle datasets larger than RAM, verifying SC-005. If no valid dataset is found, log "SKIPPED" and do not halt.
- **Note on T015c**: The task MUST skip target salience with a warning if images are missing, aligning with US-1 Acceptance Scenario 2. **Note**: Plan.md contradiction flagged for kickback; tasks follow Spec.
- **Note on T024**: The task MUST default to 'aggregate' if aggregation key is missing, preserving spec's 'aggregate OR abort' logic.
- **Note on T029**: The task MUST exclude trials where search_time == median to handle ties.
- **Note on T004**: The task MUST include default values for Gabor parameters in config.yaml.
- **Note on T038-T042**: These tasks address the specific reviewer concern regarding large datasets and the need for streaming to stay within the 6GB RAM constraint. They ensure the pipeline is robust for real-world data sizes. **Updated**: T038/T039 moved to Phase 2.