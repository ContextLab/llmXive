# Tasks: Neural Correlates of Predictive Error Signals During Tactile Discrimination Learning

**Input**: Design documents from `/specs/001-neural-correlates-of-predictive-error-si/`
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

## Phase 0: Dataset Validation & Variable Fit (SC-004 Gate)

**Purpose**: Verify dataset metadata and determine analysis path (Error-Signal vs Stimulus-Driven).

- [X] T001 [P] [US1] Implement dataset metadata fetcher in `src/data/ingest.py` to search for "tactile", "somatosensory", "odd-ball" datasets (FR-001)
- [X] T002 [P] [US1] Implement variable check in `src/data/ingest.py` to verify presence of `stimulus_type` and `response_correctness` in metadata (FR-011, FR-012)
- [ ] T003 [US1] Generate `data/validation_report.json` with `analysis_mode` ("error_signal" or "stimulus_driven") based on variable availability (FR-011, FR-012). **Logic**:
 1. If `response_correctness` exists -> set `analysis_mode` to "error_signal". **Power Check**: Apply strict Constitution Principle VII (≥20 subjects, ≥500 trials/condition) to ALL modes. If failed, flag as `underpowered_primary` and exclude from primary analysis.
 2. If only `stimulus_type` exists -> set `analysis_mode` to "stimulus_driven". **Power Check**: Apply strict Constitution Principle VII. If failed, flag as `underpowered_fallback` but **DO NOT SKIP**. Run in fallback mode with warnings. **No relaxed thresholds allowed.**
 3. If neither exists -> log error and skip dataset. **Exclusion Requirement**: Explicitly apply Constitution Principle VII to **primary hypothesis tests** only. The fallback mode must remain operational for smaller cohorts with appropriate warnings, but underpowered subjects are excluded from the primary GLMM. **Verification**: Confirm file exists, contains valid JSON, `analysis_mode` key is present, and `power_status` is recorded for both modes.
- [ ] T004 [P] [US1] Implement graceful degradation in `src/data/ingest.py`: Log warnings for missing metadata or failed fetches and skip affected datasets rather than crashing (FR-011). **Requirement**: If a real dataset fetch (OpenNeuro/HF) fails, log the error, skip the dataset, and continue processing other datasets. Do NOT terminate the pipeline.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T005c [P] Initialize Git repository at the **repository root** (not in `src/`). **Commands**: `git init` executed at the root level. **Constraint**: Must be executed before any other git operations.
- [X] T005d [US1] Generate initial `state/projects/PROJ-500-neural-correlates-of-predictive-error-si.yaml` with content hashes for `./requirements.txt` and `./pyproject.toml` to satisfy Constitution Principle V. **Dependency**: T005c (Git Init). **Implementation Detail**: Use **SHA-256** hashing algorithm. Hash the full content of `./requirements.txt` and `./pyproject.toml` and write them to the state file. **Verification**: Confirm file exists, contains valid YAML, and includes `artifact_hashes` map with SHA-256 values for both files. **Note**: Sequential execution required to ensure directory structure is ready.
- [X] T005a [P] Create project directory structure (`src/`, `tests/`, `contracts/`, `data/`, `analysis/`)
- [X] T005b [P] Initialize Python 3.11 project with `pyproject.toml` and `requirements.txt` (dependencies: `mne`, `pandas`, `numpy`, `statsmodels`, `scikit-learn`, `pyyaml`, `requests`, `datasets`, `joblib`)
- [~] T006 [P] Configure linting (`ruff`) and formatting (`black`) tools (Create `ruff.toml` and `pyproject.toml` [tool.black] sections)
- [~] T009c [P] [US1] Implement **Verified Source Injection Hook** in `src/data/ingest.py`. **Logic**: Check for `VERIFIED_REAL_DATA_SOURCE` env var (JSON). If present, use the provided `package_name` and `access_recipe` as the **single** source of truth. **Constraint**: Do NOT allow hand-rolled guesses to coexist. **Output**: Generate `state/projects/PROJ-500...yaml` `artifact_hashes` entry for the verified source. **Verification**: Unit test simulates injection and asserts exclusive use.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [~] T009a [P] Create base data schema `contracts/aligned_data.schema.yaml`. **Format**: YAML (JSON Schema Draft 7). **Library**: `jsonschema`. **Fields**: `subject_id`, `block_id`, `mmn_amplitude`, `source_window_start_trial`, `analysis_mode`, `learning_phase`. **Deliverable**: Write the **complete, valid JSON Schema** content to `contracts/aligned_data.schema.yaml`. **Verification**: Validate the file against JSON Schema Draft 7 syntax and ensure all required fields are present.
- [~] T009b [P] Create base data schema `contracts/model_output.schema.yaml`. **Format**: YAML (JSON Schema Draft 7). **Library**: `jsonschema`. **Fields**: `coefficients`, `p_values`, `fdr_p_values`, `permutation_p_value`. **Deliverable**: Write the **complete, valid JSON Schema** content to `contracts/model_output.schema.yaml`. **Verification**: Validate the file against JSON Schema Draft 7 syntax and ensure all required fields are present.
- [~] T010 [P] Configure environment variable validation and error handling infrastructure (Create `src/utils/config.py` to check `DATA_DIR`, `SEED`, `RAM_LIMIT`)
- [~] T007 [P] Configure configuration management (`src/utils/config.py`) for paths, seeds, and parameters. **Defaults**: Low-frequency filter -40 Hz, `EPOCH_WINDOW` (default -250ms to 500ms to match Plan Constraints), `ACCURACY_BLOCK_SIZE`. **Verification**: Confirm `config.py` contains these specific defaults and they are used by downstream modules.
- [~] T008 [P] Implement structured logging (`src/utils/logging.py`) with JSON output for pipeline traceability
- [~] T011 [P] Implement checksum utility (`src/utils/checksum.py`) for data hygiene (FR-009, Constitution III)
- [~] T012 [P] Contract test for data schema validation in `tests/contract/test_schemas.py`. **Dependency**: T009a/b completion. **Logic**: Load schemas from `contracts/` and validate sample data against them. **Note**: Sequential execution required after T009a/b.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download raw EEG data from OpenNeuro/HF, preprocess (filter, ICA, interpolate), and epoch data with ≥95% success rate for valid datasets.

**Independent Test**: Can be fully tested by executing the data ingestion script on a sample dataset and verifying the output contains correctly labeled epochs, filtered signals, and interpolated channels without manual intervention.

- [~] T013 [P] [US1] Contract test for underpowered exclusion in `tests/contract/test_schemas.py`. **Dependency**: T009a (Base Schema), T007 (Config), T016 (Logic). **Logic**: Load a mock dataset with <20 subjects or <500 trials/condition, run the exclusion logic (T016), and assert that the resulting schema-compliant output contains these subjects with a `power_status: "underpowered"` flag rather than being removed. **Mock Data Generation**: Create a DataFrame within the test using: `import pandas as pd; mock = pd.DataFrame({'subject_id': ['S1', 'S2'], 'trial_count': [100, 100]})`. **Verification**: Confirm `excluded_subjects.csv` is NOT generated for primary exclusion, but a `power_report.csv` is generated with flags. **Note**: This test validates the *schema and logic contract* for power flagging, not removal.
- [~] T014 [US1] Implement streaming data downloader in `src/data/ingest.py` (chunked buffering, delete raw files post-processing, FR-001, FR-009)
- [~] T015 [US1] Implement preprocessing module in `src/data/preprocess.py` (Bandpass filter **1–40 Hz** as per Plan Phase 1, ICA artifact removal, bad channel interpolation) (FR-002, Constitution VI). **Note**: Explicitly use 1–40 Hz to resolve Spec ambiguity.
- [~] T016 [US1] Implement artifact rejection logic (trial count loss ≤ 5%) and **generate exclusion report** in `src/data/preprocess.py`. **Logic**: Apply **strict thresholds** based on Constitution Principle VII:
 - If subject has <20 subjects or <500 trials/condition -> Add to `data/power_report.csv` with `reason: "underpowered"`. **Do not exclude** from raw data files, but mark in metadata.
 - Generate a warning message in the processing log if a subject is flagged. Write `data/power_report.csv` with columns: `subject_id`, `reason`, `power_status` (values: "powered", "underpowered_primary").
 - **Deliverable**: `data/power_report.csv` containing subject_ids and their power status.
 - **Verification**: Confirm `power_report.csv` exists and contains entries for underpowered subjects.
- [~] T017 [US1] Implement epoching logic in `src/data/preprocess.py`. **Requirement**: Read `EPOCH_WINDOW` from `src/utils/config.py` (default: -250ms to 500ms) and apply it. **Note**: The default value is a time window matching Plan Constraints. (FR-003). **Verification**: Confirm epoching window matches the configured value in `config.py`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - MMN Amplitude and Behavioral Alignment (Priority: P2)

**Goal**: Compute MMN amplitude (early-latency window) at CP3, CP4, C3, C4, align with behavioral accuracy using Lagged Alignment, and handle missing logs via "Stimulus-Driven" fallback.

**Independent Test**: Can be fully tested by running the alignment module on a pre-processed dataset and verifying the output CSV contains a time-series of MMN amplitudes and corresponding accuracy percentages for each block, with no missing values for valid blocks.

- [~] T018 [P] [US2] Contract test for aligned_data schema in `tests/contract/test_schemas.py`. **Dependency**: T009a (Base Schema), T022b (Learning_Phase extension). **Logic**: Validate that the final `aligned_data.csv` contains all required fields including `learning_phase`.
- [~] T019 [P] [US2] Integration test for lagged alignment logic in `tests/integration/test_alignment.py`. **Verification**: Must validate that `data/interim_lagged_mmns.csv` is generated with the exact schema: `subject_id`, `block_id`, `mmn_amplitude`, `source_window_start_trial`, and that the lagged logic (-trial source window -> subsequent accuracy block) is correctly applied. **Deliverable**: `tests/integration/test_alignment.py::test_lagged_alignment_no_overlap`.

### Implementation for User Story 2

- [~] T020 [P] [US2] Implement MMN amplitude calculator in `src/data/align.py`. **Requirement**: Calculate mean difference wave (Deviant - Standard) **explicitly at electrodes CP3, CP4, C3, and C4** within the 150–250ms window (FR-004). **Deliverable**: Output must be a DataFrame with distinct columns/rows for each of the four electrodes. **Verification**: Verify output file contains columns/rows for CP3, CP4, C3, C4. Do NOT calculate a single global average.
- [~] T021 [US2] Implement behavioral binning logic in `src/data/align.py`. **Logic**: Read `ACCURACY_BLOCK_SIZE` from `src/utils/config.py` (defined in T007) and calculate accuracy over a **configurable multi-trial block** (t to t+n) defined in `src/utils/config.py` (FR-005, Plan Phase 2). **Schema**: `subject_id` (str), `block_id` (int), `trial_start` (int), `trial_end` (int), `accuracy` (float). **Output**: `data/accuracy_blocks.csv`. **Verification**: Confirm file exists and contains valid accuracy values for the configured window size.
- [~] T023 [US2] Filter data based on exclusion criteria from `data/power_report.csv` and generate `data/filtered_aligned_for_glmm.csv`. **Requirement**: The filtered dataset must **exclude** subjects listed in `data/power_report.csv` with `power_status: "underpowered_primary"`. **Logic**: Read `data/power_report.csv`, filter `data/interim_lagged_mmns.csv` (T022) and `data/accuracy_blocks.csv` (T021) to remove these subjects, and merge. **Verification**: Confirm `filtered_aligned_for_glmm.csv` does not contain any subject_ids from the exclusion list.
- [~] T022 [P] [US2] Implement **Lagged Alignment** logic in `src/data/align.py**. **Dependency**: T021 (Binning), T020 (MMN Calc). **Logic**: Calculate MMN over a preceding fixed-length trial window (t-N to t-M) and align to the **subsequent accuracy block** (t to t+n) generated by T021. **Deliverable**: Write intermediate artifact to `data/interim_lagged_mmns.csv` with columns: `subject_id`, `block_id`, `mmn_amplitude`, `source_window_start_trial`. The source window spans `range(t-50, t-10)` (40 trials, matching Plan Phase 2). (Python exclusive end). **Note**: The span from t-50 to t-10 covers 40 trials. **Verification**: Confirm the source window size is 40 trials and that data is aligned correctly.
- [~] T022b [P] [US2] Implement **Learning_Phase** feature generation in `src/data/align.py`. **Dependency**: T023 (Filtering). **Logic**: Bin trial blocks into discrete phases based on `block_id`. **Algorithm**: Calculate the median `block_id` of the **filtered dataset** (`data/filtered_aligned_for_glmm.csv` from T023). Assign 'Early' if `block_id < median`, 'Late' if `block_id >= median`. **Output**: Add `learning_phase` column to `data/filtered_aligned_for_glmm.csv`. **Verification**: Confirm `learning_phase` column exists and contains valid categorical values ('Early', 'Late').
- [ ] T024 [US2] Finalize and Write Aligned Dataset: **Dependency**: Explicitly consume `data/filtered_aligned_for_glmm.csv` from T023, filtered data from T023, and `learning_phase` from T022b **BEFORE** merging. **Logic**: Merge filtered `data/filtered_aligned_for_glmm.csv` with filtered `data/accuracy_blocks.csv` on keys `['subject_id', 'block_id']`. **Output**: `data/aligned_data.csv` (FR-011, FR-012). **Verification**: Ensure `aligned_data.csv` matches the schema and includes `power_status` column. <!-- FAILED-IN-EXECUTION: code/src/data/finalize_aligned.py exit=1 -->

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Modeling and Validation (Priority: P3)

**Goal**: Fit Gaussian LME (`MMN ~ Accuracy + (1|Subject)`), apply multiple-comparison correction, run permutation test (n=1000), and perform sensitivity analysis.

**Independent Test**: Can be fully tested by executing the analysis script on the aligned dataset and verifying the output includes the model coefficients, p-values (corrected), and a permutation test p-value, all generated within 6 hours on CPU-only hardware.

- [~] T025 [P] [US3] Contract test for model_output schema in `tests/contract/test_schemas.py`
- [~] T026 [P] [US3] Unit test for permutation test implementation in `tests/unit/test_model.py`. **Verification**: Must verify that the permutation test runs a sufficient number of shuffles and reports the resulting p-value..

### Implementation for User Story 3

- [~] T027 [US3] Implement Gaussian LME fitting in `src/analysis/model.py` (`MMN_Amplitude ~ Accuracy + Learning_Phase + (1|Subject)`) consuming `data/aligned_data.csv` (Plan Correction, Spec FR-006 Updated). **Note**: Assumes Spec v1.1 is the SSoT. **Library**: `statsmodels.formula.api.mixedlm`. **Encoding**: `Learning_Phase` must be encoded as categorical. **Deliverable**: Write model output to `analysis/results/model_output.json`. **Distribution**: Gaussian, **Link Function**: Identity. **Constraint**: The model runs ONLY on the filtered dataset from T023 (underpowered subjects already excluded). **Verification**: Confirm `model_output.json` contains coefficients and p-values.
- [~] T028 [P] [US3] Implement multiple-comparison correction using **FDR (Benjamini-Hochberg)** for electrodes in `src/analysis/model.py` (FR-008). **Dependency**: Requires T027 output.
- [~] T029 [US3] Implement permutation test in `src/analysis/model.py`. **Logic**: Run a permutation test with **adaptive n**. Start at n=1000. Check p-value stability (variance < 0.01 OR coefficient of variation < 5%). If unstable, increase n by a moderate increment (up to a defined maximum). If stable, report n used. **Deliverable**: Write `analysis/results/permutation_stability_log.json` containing the final n used and the final p-value. **Verification**: Confirm log file exists and shows adaptive logic was applied. (FR-007).
- [ ] T030 [US3] Implement sensitivity analysis in `src/analysis/robustness.py` (sweep time windows ±10ms: 140–240ms, 160–260ms) (FR-010)
- [~] T031 [US3] Generate `analysis/results/model_output.json` with coefficients, p-values, and robustness metrics. **Traceability**: Output must be derived from and traceable to Functional Requirements FR-006, FR-007, and FR-010. **Verification**: Ensure JSON contains all required fields and matches the schema from T009b. **Dependency**: T027, T028.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [~] T032 [P] Documentation updates in `docs/` and `README.md` including `quickstart.md`
- [~] T033a [P] Refactor `src/data/ingest.py` to use streaming buffers ensuring peak RAM ≤ 7 GB. **Verification**: Run pipeline with memory profiling using `memory_profiler` (command: `python -m memory_profiler src/main.py`) and log peak usage < 7GB. (FR-009)
- [~] T033b [P] Refactor `src/analysis/model.py` to process subjects in batches ensuring peak RAM ≤ 7 GB. **Verification**: Run pipeline with memory profiling using `memory_profiler` (command: `python -m memory_profiler src/main.py`) and log peak usage < 7GB. (FR-009)
- [~] T034 [P] Run `quickstart.md` validation to ensure end-to-end reproducibility
- [~] T035 [P] Additional unit tests for edge cases (missing metadata, handling zero accuracy values to prevent division errors) in `tests/unit/`
- [~] T036 [P] Verify full pipeline runtime ≤6 hours on **GitHub Actions free-tier runner (2-core, 7GB RAM)**. **Verification**: Run full pipeline on sample dataset, log runtime to `analysis/runtime.log`, and confirm ≤6 hours. **Note**: This is a **Performance Goal** (per Plan); minor variations due to hardware are acceptable if reproducibility is maintained. (FR-009, SC-005)

---

## Phase 7: Execution Verification & Robustness (Revision Concerns)

**Purpose**: Address specific reviewer concerns regarding data source verification, streaming integrity, and rigorous power analysis enforcement.

- [~] T038 [P] [US1] Implement **Streaming Chunk Verification** in `src/data/ingest.py`. **Logic**: When using `datasets.load_dataset(..., streaming=True)`, implement an iterator wrapper that logs the count of processed chunks and verifies the total row count matches the expected dataset size (or logs a specific sampling fraction if subsampling is intentional). **Deliverable**: Add `data/streaming_log.json` recording chunks processed and total rows seen.
- [~] T040 [P] [US2] Implement **Lagged Window Sanity Check** in `src/data/align.py`. **Logic**: Before writing `data/aligned_data.csv`, assert that the "source window" (t-N to t-M) and "target block" (t to t+n) do not overlap and that the source window contains at least 10 valid trials. If not, drop the block and log `WARNING: Block {block_id} excluded: insufficient trials or overlap`. **Verification**: Confirm no overlapping windows exist in the output CSV.
- [~] T042 [US2] Implement **Strict Data Fetcher** in `src/data/ingest.py`. **Logic**: If a real dataset fetch fails, log a warning message and skip the dataset. Do **NOT** raise an exception or terminate the pipeline. **Correction**: This task now aligns with FR-011 by ensuring graceful degradation rather than halting.
- [~] T043 [US2] Implement **Verified Source Injection Hook** in `src/data/ingest.py`. **Logic**: If the execution environment provides a `VERIFIED_REAL_DATA_SOURCE` configuration (JSON format with required keys: `package_name`: str, `access_recipe`: str), the loader MUST adopt this as the **single** source of truth. **Constraint**: Do NOT allow hand-rolled `load_dataset("<guessed-id>")` or raw URL guesses to coexist with the verified source. **Verification**: Unit test simulates an injected verified source and asserts that the loader uses the injected recipe exclusively.
- [~] T044 [US2] Implement **Real Data Stream Validator** in `src/data/align.py`. **Logic**: Before computing MMN or Accuracy, verify that the input data was derived from a real stream (check `streaming_log.json` or data headers). If the data source is flagged as synthetic or mock, log a warning and skip the analysis.
- [~] T045 [US2] Implement **Result Provenance Check** in `src/analysis/model.py`. **Logic**: Ensure that the `model_output.json` includes a `data_source_hash` field derived from the **SHA-256 hash of the content** of the input `aligned_data.csv`. **Verification**: Confirm that the output JSON contains the hash and matches the input data checksum.
- [~] T046 [US2] Implement **Explicit Sampling Documentation** in `src/data/ingest.py`. **Requirement**: If a dataset is too large and must be sampled (streaming limit), the code MUST explicitly log and record the sampling rule (e.g., "First 500 rows of split 'train'") in `data/streaming_log.json`. **Constraint**: Do NOT use random sampling unless explicitly configured with a fixed seed and documented. **Verification**: Confirm `streaming_log.json` contains the exact sampling rule used.

---

## Phase 8: Critical Data Integrity & Anti-Fabrication (Revision Concerns)

**Purpose**: Enforce strict data integrity rules to prevent silent fallbacks to synthetic data and ensure real data provenance.

- [~] T047 [P] [US1] Implement **Fail-Loud Data Loader** in `src/data/ingest.py`. **Logic**:
 1. **Fetch Errors**: If a real data fetch (OpenNeuro/HF/Verified Source) fails due to network issues, log a warning and skip the dataset (FR-011).
 2. **Synthetic Detection**: If data is flagged as synthetic or mock (e.g., `source_type: "synthetic"`), raise a `DataIntegrityError` **for that specific dataset only**, log the error, and skip the dataset. Do NOT terminate the entire pipeline.
 **Constraint**: No silent substitution of fake data is permitted. **Verification**: Unit test must assert that a simulated network failure skips the dataset, while a simulated synthetic data input raises an exception for that dataset but allows the pipeline to continue with others.
- [~] T048 [US2] Implement **Synthetic Data Rejection** in `src/data/align.py`. **Logic**: Before any statistical calculation, verify the input DataFrame contains a `source_type` column marked as "real_stream" or "verified_source". If the column is missing or marked "synthetic", raise a `DataIntegrityError` **for that specific dataset**, log the error, and skip the dataset. **Verification**: Integration test confirms that a pipeline fed with mock data skips that dataset and continues with valid ones (or exits cleanly if no valid data remains).
- [~] T049 [US1] Implement **Real Data Source Fingerprinting** in `src/data/ingest.py`. **Logic**: Upon successful fetch, generate a unique fingerprint (SHA-256 of file content or manifest) and store it in `state/projects/PROJ-500...yaml` under `artifact_hashes`. **Constraint**: This fingerprint must be used to validate data integrity in downstream tasks. **Dependency**: T009c (Verified Source Injection). **Verification**: Confirm the state file is updated with the new hash after a successful fetch.
- [~] T050 [US2] Implement **Streaming Integrity Monitor** in `src/data/ingest.py`. **Logic**: While streaming a large dataset, track the cumulative byte count and row count. If the stream terminates unexpectedly (e.g., partial file) before the expected size or row count is reached, raise an error **for that dataset** and skip it. **Verification**: Simulate a truncated stream in a unit test and verify the process skips the dataset and logs an error.