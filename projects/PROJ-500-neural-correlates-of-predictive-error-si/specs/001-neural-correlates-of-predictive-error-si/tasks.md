# Tasks: Neural Correlates of Predictive Error Signals During Tactile Discrimination Learning

**Input**: Design documents from `/specs/001-neural-correlates-of-predictive-error-si/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]****: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

## Phase 0: Dataset Validation & Variable Fit (SC-004 Gate)

**Purpose**: Verify dataset metadata and determine analysis path (Error-Signal vs Stimulus-Driven).

- [X] T001 [P] [US1] Implement dataset metadata fetcher in `src/data/ingest.py` to search for "tactile", "somatosensory", "odd-ball" datasets (FR-001)
- [X] T002 [P] [US1] Implement variable check in `src/data/ingest.py` to verify presence of `stimulus_type` and `response_correctness` in metadata (FR-011, FR-012)
- [X] T003 [US1] Generate `data/validation_report.json` with `analysis_mode` ("error_signal" or "stimulus_driven") based on variable availability (FR-011, FR-012). **Logic**:
 1. If `response_correctness` exists -> set `analysis_mode` to "error_signal". **Power Check**: Apply Constitution Principle VII (≥20 subjects, ≥500 trials/condition). If failed, flag as `underpowered_primary` but **do not** exclude; mark as `analysis_mode: "error_signal"` with `power_status: "underpowered"`.
 2. If only `stimulus_type` exists -> set `analysis_mode` to "stimulus_driven". **Power Check**: Apply a relaxed threshold (e.g., ≥5 subjects, ≥50 trials/condition). If failed, flag as `underpowered_stimulus_driven` but **do not** exclude; mark as `analysis_mode: "stimulus_driven"` with `power_status: "underpowered"`.
 3. If neither exists -> log error and skip dataset. **Exclusion Requirement**: Explicitly apply Constitution Principle VII to **primary hypothesis tests** only. The fallback mode must remain operational for smaller cohorts with appropriate warnings. **Verification**: Confirm file exists, contains valid JSON, `analysis_mode` key is present, and `power_status` is recorded for both modes.
- [X] T004 [P] [US1] Implement graceful degradation in `src/data/ingest.py`: Log warnings for missing metadata or failed fetches and skip affected datasets rather than crashing (FR-011). **Requirement**: If a real dataset fetch (OpenNeuro/HF) fails, log the error, skip the dataset, and continue processing other datasets. Do NOT terminate the pipeline.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T005c [P] Initialize Git repository at the **repository root** (not in `src/`). **Commands**: `git init` executed at the root level. **Constraint**: Must be executed before any other git operations.
- [X] T005d [US1] Generate initial `state/projects/PROJ-500-neural-correlates-of-predictive-error-si.yaml` with content hashes for `./requirements.txt` and `./pyproject.toml` to satisfy Constitution Principle V. **Dependency**: T005c (Git Init). **Implementation Detail**: Use **SHA-256** hashing algorithm. Hash the full content of `./requirements.txt` and `./pyproject.toml`. **Verification**: Confirm file exists, contains valid YAML, and includes `artifact_hashes` map with SHA-256 values for both files. **Note**: Sequential execution required to ensure directory structure is ready.
- [X] T005e [P] Calculate SHA-256 hashes for `./requirements.txt` and `./pyproject.toml`. **Dependency**: T005c (Git Init).  **Implementation Detail**: Use **SHA-256** hashing algorithm. **Verification**: Confirm correct hashes are generated.
- [X] T005a [P] Create project directory structure (`src/`, `tests/`, `contracts/`, `data/`, `analysis/`)
- [X] T005b [P] Initialize Python 3.11 project with `pyproject.toml` and `requirements.txt` (dependencies: `mne`, `pandas`, `numpy`, `statsmodels`, `scikit-learn`, `pyyaml`, `requests`, `datasets`, `joblib`)
- [X] T006 [P] Configure linting (`ruff`) and formatting (`black`) tools (Create `ruff.toml` and `pyproject.toml` [tool.black] sections)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T009a [P] Create base data schema `contracts/aligned_data.schema.yaml`. **Format**: YAML (JSON Schema Draft 7). **Library**: `jsonschema`. **Fields**: `subject_id`, `block_id`, `mmn_amplitude`, `source_window_start_trial`, `analysis_mode`, `learning_phase`. **Deliverable**: Write the **complete, valid JSON Schema** content to `contracts/aligned_data.schema.yaml`. **Verification**: Validate the file against JSON Schema Draft 7 syntax and ensure all required fields are present.
- [X] T009b [P] Create base data schema `contracts/model_output.schema.yaml`. **Format**: YAML (JSON Schema Draft 7). **Library**: `jsonschema`. **Fields**: `coefficients`, `p_values`, `fdr_p_values`, `permutation_p_value`. **Deliverable**: Write the **complete, valid JSON Schema** content to `contracts/model_output.schema.yaml`. **Verification**: Validate the file against JSON Schema Draft 7 syntax and ensure all required fields are present.
- [X] T010 [P] Configure environment variable validation and error handling infrastructure (Create `src/utils/config.py` to check `DATA_DIR`, `SEED`, `RAM_LIMIT`)
- [X] T007 [P] Configure configuration management (`src/utils/config.py`) for paths, seeds, and parameters (Low-frequency filter in the range of a few hertz to the upper limit of the low-frequency band., `EPOCH_WINDOW` (default -250ms to 500ms), `ACCURACY_BLOCK_SIZE`)
- [X] T008 [P] Implement structured logging (`src/utils/logging.py`) with JSON output for pipeline traceability
- [X] T011 [P] Implement checksum utility (`src/utils/checksum.py`) for data hygiene (FR-009, Constitution III)
- [X] T012 [P] Contract test for data schema validation in `tests/contract/test_schemas.py`. **Dependency**: T009a/b completion. **Logic**: Load schemas from `contracts/` and validate sample data against them. **Note**: Sequential execution required after T009a/b.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download raw EEG data from OpenNeuro/HF, preprocess (filter, ICA, interpolate), and epoch data with ≥95% success rate for valid datasets.

**Independent Test**: Can be fully tested by executing the data ingestion script on a sample dataset and verifying the output contains correctly labeled epochs, filtered signals, and interpolated channels without manual intervention.

- [X] T013 [P] [US1] Contract test for underpowered exclusion in `tests/contract/test_schemas.py`. **Dependency**: T009a (Base Schema), T007 (Config). **Logic**: Load a mock dataset with <20 subjects or <500 trials/condition, run the exclusion logic (T016), and assert that the resulting schema-compliant output contains these subjects with a `power_status: "underpowered"` flag rather than being removed. **Mock Data Generation**: Create a DataFrame within the test using: `import pandas as pd; mock = pd.DataFrame({'subject_id': ['S1', 'S2'], 'trial_count': [100, 100]})`. **Verification**: Confirm `excluded_subjects.csv` is NOT generated for primary exclusion, but a `power_report.csv` is generated with flags. **Note**: This test validates the *schema and logic contract* for power flagging, not removal.
- [X] T014 [US1] Implement streaming data downloader in `src/data/ingest.py` (chunked buffering, delete raw files post-processing, FR-001, FR-009)
- [X] T015 [US1] Implement preprocessing module in `src/data/preprocess.py` (Bandpass filter **1–40 Hz** as per Plan Phase 1, ICA artifact removal, bad channel interpolation) (FR-002, Constitution VI). **Note**: Explicitly use 1–40 Hz to resolve Spec ambiguity.
- [X] T016 [US1] Implement artifact rejection logic (trial count loss ≤ 5%) and **flag** underpowered dataset flagging in `src/data/preprocess.py`. **Logic**: Apply **dynamic thresholds** based on `analysis_mode`:
  - If `analysis_mode == "error_signal"`: Flag subjects/datasets with <20 subjects or <500 trials/condition as `underpowered_primary`. **Do not exclude** from data files, but mark in metadata.
  - If `analysis_mode == "stimulus_driven"`: Flag subjects/datasets with <5 subjects or <50 trials/condition as `underpowered_stimulus_driven`.
  - Generate a warning message in the processing log if a subject or dataset is flagged. Write a `data/power_report.csv` with columns: `subject_id`, `reason`, `power_status` (values: "powered", "underpowered_primary", "underpowered_stimulus_driven"). **Verification**: Confirm `power_report.csv` exists and contains entries for both exclusion criteria with appropriate flags, ensuring no data is silently dropped.
- [X] T017 [US1] Implement epoching logic in `src/data/preprocess.py`. **Requirement**: Read `EPOCH_WINDOW` from `src/utils/config.py` (default: -200ms to 500ms) and apply it. **Note**: The default value is provisional pending spec confirmation; the code must support configuration changes without modification. (FR-003). **Verification**: Confirm epoching window matches the configured value in `config.py`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - MMN Amplitude and Behavioral Alignment (Priority: P2)

**Goal**: Compute MMN amplitude (early-latency window) at CP3, CP4, C3, C4, align with behavioral accuracy using Lagged Alignment, and handle missing logs via "Stimulus-Driven" fallback.

**Independent Test**: Can be fully tested by running the alignment module on a pre-processed dataset and verifying the output CSV contains a time-series of MMN amplitudes and corresponding accuracy percentages for each block, with no missing values for valid blocks.

- [X] T018 [P] [US2] Contract test for aligned_data schema in `tests/contract/test_schemas.py`. **Dependency**: T009a (Base Schema), T022b (Learning_Phase extension). **Logic**: Validate that the final `aligned_data.csv` contains all required fields including `learning_phase`.
- [X] T019 [P] [US2] Integration test for lagged alignment logic in `tests/integration/test_alignment.py`. **Verification**: Must validate that `data/interim_lagged_mmns.csv` is generated with the exact schema: `subject_id`, `block_id`, `mmn_amplitude`, `source_window_start_trial`, and that the lagged logic (-trial source window -> subsequent accuracy block) is correctly applied.

### Implementation for User Story 2

- [X] T020 [P] [US2] Implement MMN amplitude calculator in `src/data/align.py`. **Requirement**: Calculate mean difference wave (Deviant - Standard) **explicitly at electrodes CP3, CP4, C3, and C4** within the 150–250ms window (FR-004). **Deliverable**: Output must be a DataFrame with distinct columns/rows for each of the four electrodes. **Verification**: Verify output file contains columns/rows for CP3, CP4, C3, C4. Do NOT calculate a single global average.
- [X] T021 [US2] Implement behavioral binning logic in `src/data/align.py`. **Logic**: Read `ACCURACY_BLOCK_SIZE` from `src/utils/config.py` (defined in T007) and calculate accuracy over a **configurable multi-trial block** (t to t+n) defined in `src/utils/config.py` (FR-005, Plan Phase 2). **Output**: `data/accuracy_blocks.csv` (Schema: `subject_id`, `block_id`, `accuracy`, `trial_start`, `trial_end`). **Verification**: Confirm file exists and contains valid accuracy values for the configured window size.
- [X] T022 [US2] Implement **Lagged Alignment** logic in `src/data/align.py`. **Logic**: Calculate MMN over a preceding fixed-length trial window (t-N to t-M) and align to the **subsequent accuracy block** (t to t+n) generated by T021. **Deliverable**: Write intermediate artifact to `data/interim_lagged_mmns.csv` with columns: `subject_id`, `block_id`, `mmn_amplitude`, `source_window_start_trial`. The source window spans **50 trials** (t-50 to t-10). **Verification**: Confirm the source window size is 50 trials and that data is aligned correctly.
- [X] T022b [US2] Implement **Learning_Phase** feature generation in `src/data/align.py`. **Logic**: Bin trial blocks into discrete phases (e.g., "Early", "Late") based on `block_id` or cumulative trial count to create the `Learning_Phase` predictor required for the LME model (FR-006). **Output**: Add `learning_phase` column to `data/interim_lagged_mmns.csv` or create `data/learning_phases.csv`. **Verification**: Confirm `learning_phase` column exists and contains valid categorical values.
- [X] T023 [US2] Filter data based on exclusion criteria from `data/power_report.csv` and generate `data/filtered_aligned_for_glmm.csv`. **Requirement**: The filtered dataset must **exclude** subjects flagged as `underpowered_primary` ONLY if the `analysis_mode` is "error_signal". If `analysis_mode` is "stimulus_driven", include all subjects but retain the `power_status` flag. **Logic**: Apply conditional filtering based on the `analysis_mode` determined in T003.
- [X] T024 [US2] Finalize and Write Aligned Dataset: **Dependency**: Explicitly consume `data/filtered_aligned_for_glmm.csv` from T023, filtered data from T023, and `learning_phase` from T022b **BEFORE** merging. **Logic**: Merge filtered `data/filtered_aligned_for_glmm.csv` with filtered `data/accuracy_blocks.csv`, and generate final `data/aligned_data.csv` (FR-011, FR-012). **Verification**: Ensure `aligned_data.csv` matches the schema and includes `power_status` column.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Modeling and Validation (Priority: P3)

**Goal**: Fit Gaussian LME (`MMN ~ Accuracy + (1|Subject)`), apply multiple-comparison correction, run permutation test (n=1000), and perform sensitivity analysis.

**Independent Test**: Can be fully tested by executing the analysis script on the aligned dataset and verifying the output includes the model coefficients, p-values (corrected), and a permutation test p-value, all generated within 6 hours on CPU-only hardware.

- [X] T025 [P] [US3] Contract test for model_output schema in `tests/contract/test_schemas.py`
- [X] T026 [P] [US3] Unit test for permutation test implementation in `tests/unit/test_model.py`. **Verification**: Must verify that the permutation test runs exactly 1000 shuffles and reports the fixed p-value.

### Implementation for User Story 3

- [X] T027 [US3] Implement Gaussian LME fitting in `src/analysis/model.py` (`MMN_Amplitude ~ Accuracy + Learning_Phase + (1|Subject)`) consuming `data/aligned_data.csv` (Plan Correction, Spec FR-006 Updated). **Note**: Assumes Spec v1.1 is the SSoT. **Deliverable**: Write model output to `analysis/results/model_output.json`. **Distribution**: Gaussian, **Link Function**: Identity. **Constraint**: If `power_status` is "underpowered_primary", the model must still run but append a `warning: "Underpowered dataset"` to the output.
- [X] T028 [P] [US3] Implement multiple-comparison correction using **FDR (Benjamini-Hochberg)** for electrodes in `src/analysis/model.py` (FR-008). **Dependency**: Requires T027 output.
- [X] T029 [US3] Implement permutation test in `src/analysis/model.py`. **Logic**: Run a permutation test with **exactly n=1000 shuffles**. If the dataset size is < 500, reduce n to 200 to improve runtime. **Dynamic Stability Check**: If p-value variance > 0.05 across 3 runs, increase n by 500 until stable or max n=5000. Check for p-value stability. **Deliverable**: Write `analysis/results/permutation_stability_log.json` containing the final n used and the final p-value. **Verification**: Confirm log file exists and shows n used and stability status.
- [X] T030 [US3] Implement sensitivity analysis in `src/analysis/robustness.py` (sweep time windows ±10ms: 140–240ms, 160–260ms) (FR-010)
- [X] T031 [US3] Generate `analysis/results/model_output.json` with coefficients, p-values, and robustness metrics. **Traceability**: Output must be derived from and traceable to Functional Requirements FR-006, FR-007, and FR-010. **Verification**: Ensure JSON contains all required fields and matches the schema from T009b.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T032 [P] Documentation updates in `docs/` and `README.md` including `quickstart.md`
- [X] T033a [P] Refactor `src/data/ingest.py` to use streaming buffers ensuring peak RAM ≤ 7 GB. **Verification**: Run pipeline with memory profiling using `memory_profiler` (command: `python -m memory_profiler src/main.py`) and log peak usage < 7GB. (FR-009)
- [X] T033b [P] Refactor `src/analysis/model.py` to process subjects in batches ensuring peak RAM ≤ 7 GB. **Verification**: Run pipeline with memory profiling using `memory_profiler` (command: `python -m memory_profiler src/main.py`) and log peak usage < 7GB. (FR-009)
- [X] T034 [P] Run `quickstart.md` validation to ensure end-to-end reproducibility
- [X] T035 [P] Additional unit tests for edge cases (missing metadata, handling zero accuracy values to prevent division errors) in `tests/unit/`
- [X] T036 [P] Verify full pipeline runtime ≤6 hours on **GitHub Actions free-tier runner (2-core, 7GB RAM)**. **Verification**: Run full pipeline on sample dataset, log runtime to `analysis/runtime.log`, and confirm ≤6 hours. **Note**: This is a **Performance Goal** (per Plan); minor variations due to hardware are acceptable if reproducibility is maintained. (FR-009, SC-005)

---

## Phase 7: Execution Verification & Robustness (Revision Concerns)

**Purpose**: Address specific reviewer concerns regarding data source verification, streaming integrity, and rigorous power analysis enforcement.

- [X] T037 [P] **DELETED**: Replaced by T004 (Graceful Degradation).
- [X] T038 [P] [US1] Implement **Streaming Chunk Verification** in `src/data/ingest.py`. **Logic**: When using `datasets.load_dataset(..., streaming=True)`, implement an iterator wrapper that logs the count of processed chunks and verifies the total row count matches the expected dataset size (or logs a specific sampling fraction if subsampling is intentional). **Deliverable**: Add `data/streaming_log.json` recording chunks processed and total rows seen.
- [X] T039 [P] [US1] **DELETED**: Replaced by T016 (Static Thresholds).
- [X] T040 [P] [US2] Implement **Lagged Window Sanity Check** in `src/data/align.py`. **Logic**: Before writing `data/aligned_data.csv`, assert that the "source window" (t-N to t-M) and "target block" (t to t+n) do not overlap and that the source window contains at least 10 valid trials. If not, drop the block and log a warning. **Verification**: Confirm no overlapping windows exist in the output CSV.
- [X] T041 [US2] Implement **Learning_Phase** feature generation in `src/data/align.py`. **Logic**: Bin trial blocks into discrete phases (e.g., "Early", "Late") based on `block_id` or cumulative trial count to create the `Learning_Phase` predictor required for the LME model (FR-006). **Output**: Add `learning_phase` column to `data/interim_lagged_mmns.csv` or create `data/learning_phases.csv`. **Verification**: Confirm `learning_phase` column exists and contains valid categorical values.
- [X] T042 [US2] Implement **Strict Data Fetcher** in `src/data/ingest.py`. **Logic**: If a real dataset fetch fails, log a warning message and skip the dataset. Do **NOT** raise an exception or terminate the pipeline. **Correction**: This task now aligns with FR-011 by ensuring graceful degradation rather than halting.
- [X] T043 [US2] Implement **Verified Source Injection Hook** in `src/data/ingest.py`. **Logic**: If the execution environment provides a `VERIFIED_REAL_DATA_SOURCE` configuration (JSON format with required keys: `package_name`: str, `access_recipe`: str), the loader MUST adopt this as the **single** source of truth. **Constraint**: Do NOT allow hand-rolled `load_dataset("<guessed-id>")` or raw URL guesses to coexist with the verified source. **Verification**: Unit test simulates an injected verified source and asserts that the loader uses the injected recipe exclusively.
- [X] T044 [US2] Implement **Real Data Stream Validator** in `src/data/align.py`. **Logic**: Before computing MMN or Accuracy, verify that the input data was derived from a real stream (check `streaming_log.json` or data headers). If the data source is flagged as synthetic or mock, log a warning and skip the analysis.
- [X] T045 [US2] Implement **Result Provenance Check** in `src/analysis/model.py`. **Logic**: Ensure that the `model_output.json` includes a `data_source_hash` field derived from the checksum of the input `aligned_data.csv`. **Verification**: Confirm that the output JSON contains the hash and matches the input data checksum.
- [X] T046 [US2] Implement **Explicit Sampling Documentation** in `src/data/ingest.py`. **Requirement**: If a dataset is too large and must be sampled (streaming limit), the code MUST explicitly log and record the sampling rule (e.g., "First 500 rows of split 'train'") in `data/streaming_log.json`. **Constraint**: Do NOT use random sampling unless explicitly configured with a fixed seed and documented. **Verification**: Confirm `streaming_log.json` contains the exact sampling rule used.