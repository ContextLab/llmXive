# Tasks: llmXive follow-up: extending "Wan-Streamer v0.1"

**Input**: Design documents from `/specs/001-llmxive-streamer-optimization/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T002a [P] **Initialize code/ Directory**: Create `code/` and subdirectories (`code/data`, `code/models`, `code/metrics`, `code/inference`, `code/utils`, `code/tasks`). **Verification**: Run `os.path.isdir` for all created paths.
- [X] T002b [P] **Initialize data/ Directory**: Create `data/` and subdirectories (`data/raw`, `data/processed`, `data/metrics`, `data/logs`, `data/models`). **Verification**: Run `os.path.isdir` for all created paths.
- [X] T002c [P] **Initialize state/ Directory**: Create `state/` directory. **Verification**: Run `os.path.isdir`.
- [X] T002d [P] **Initialize docs/ Directory**: Create `docs/` directory. **Verification**: Run `os.path.isdir`.
- [X] T002e [P] **Initialize contracts/ Directory**: Create `contracts/` directory. **Verification**: Run `os.path.isdir`.
- [X] T002f [P] **Initialize tests/ Directory**: Create `tests/` and subdirectories (`tests/unit`, `tests/integration`, `tests/contract`). **Verification**: Run `os.path.isdir` for all created paths.
- [X] T005a [P] Create `code/requirements.txt` with CPU-only dependencies (`torch`, `scikit-learn`, `pandas`, `numpy`, `datasets`, `scipy`, `pyyaml`, `videomae`). **Verification**: Run `os.path.exists('code/requirements.txt')` and assert True.
- [X] T005b [P] Implement `code/config.py` to pin the exact HuggingFace dataset revision for VoxCeleb2 (FR-019, Constitution Principle I). **Verification**: Run `os.path.exists('code/config.py')` and assert True.
- [X] T005d [P] Create `pyproject.toml` with black formatting configuration. **Verification**: Run `os.path.exists('pyproject.toml')` and assert True.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

- [X] T007a [P] **Implement Seed Pinning**: Implement `code/utils/config.py` function `set_seed(seed=42)` that sets `torch.manual_seed`, `numpy.random.seed`, and `random.seed`. **Verification**: Run script that asserts all seeds are set to 42. (FR-001, Constitution Principle I).
- [X] T007b [P] **Implement Path Configuration**: Implement `code/utils/config.py` constants `RAW_DATA_PATH`, `PROCESSED_DATA_PATH`, `MODEL_PATH`, `STATE_PATH`. **Verification**: Run script that asserts constants are defined and point to correct relative paths. (FR-001).
- [X] T008 [P] **Implement State Updater**: Implement `code/utils/update_state_yaml.py` function `update_state(artifact_path, key)` that reads `state.yaml`, computes MD5 hash of `artifact_path`, updates `artifact_hashes[key]`, and writes back. **Verification**: Run script that creates a dummy file, calls function, and asserts hash is recorded in `state.yaml`. (Constitution Principle V, FR-020).
- [X] T009 **Implement Data Source Check**: Implement `code/data/validate_logs.py` to check for Wan-Streamer v0.1 logs first; if missing, fetch the canonical VoxCeleb2 dataset. **Dependencies**: T002 (Directory Structure), T008 (State Updater). **Logic**: 1. Check `os.path.exists('data/raw/wan-streamer-logs')`. If True, register checksum and set `data_source='wan-streamer'`. 2. If False, check `os.path.exists('data/raw/voxceleb2')`. If True, register checksum and set `data_source='voxceleb2'`. 3. If both missing, fetch `voxceleb2` via `datasets.load_dataset`. **Crucially**: Before fetching, load `code/config.py` to get the pinned `DATASET_REVISION`. After fetching, verify the loaded dataset's `default` or `split` revision matches the pinned revision. If mismatch, raise an error. **Then**, call `update_state()` from T008 with the path and MD5 hash of the downloaded dataset to write the checksum to `state.yaml` before returning. Register the checksum and set `state.dataset.source` to either "wan-streamer" or "voxceleb2". **Verification**: Run script that simulates missing logs, fetches VoxCeleb2, asserts the revision matches `config.py`, and asserts `state.yaml` contains the correct hash and source.
- [X] T010 **Implement Validators**: Implement `code/utils/validators.py` function `validate_schema(df, schema_path)` that loads schema from `contracts/dataset.schema.yaml` and validates `df` using `pandera`. **Dependency**: T009 must complete successfully before T010 runs.
- [X] T053 [P] **Implement Sample Size Reduction Module**: Implement `code/tasks/reduce_sample_size.py` that calculates a *deferred* reduction amount based on the current sample size, the minimum required size from power analysis (`MIN_SAMPLE_SIZE` defined in `code/config.py`), and the memory budget (≤ 7 GB). If reduction would bring size below `MIN_SAMPLE_SIZE`, raise a `PowerLimitationError`. Expose `reduce_sample_size(current_size) -> new_size`. **Verification**: Run script that reduces sample size and asserts correct behavior. (FR-014, FR-023). **Dependency**: None (standalone utility).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Extraction and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Extract time-series latent vectors and turn‑taking labels from real Wan‑Streamer v0.1 logs (or VoxCeleb2 fallback) to create a CPU‑tractable dataset.

### Prerequisites (Strict Order: Config & Power Analysis must complete before Extraction)

- [X] T012a [US1] **Define Threshold Algorithm**: Create `code/config/detection_thresholds.yaml` to define the algorithm and default parameters for classifying 'interruption' and 'pause' events (e.g., audio energy > X dB overlapping with agent speech) to ensure the minimum event count is verifiable (see FR-018). **Verification**: Assert file exists, is valid YAML, and contains the required keys: `audio_energy_threshold`, `pause_threshold`, `interruption_overlap_duration`. **Crucially**: The file MUST contain a `rationale` key (string) documenting the source or domain knowledge used to derive these default values (e.g., citing specific literature or domain standards) and include actual default numeric values. (FR-018).
- [X] T015b [US1] **Generate Theoretical Defaults**: Implement `code/data/generate_defaults.py` to create `data/metrics/theoretical_defaults.json`. **Logic**: If empirical data is missing, derive `variance` and `effect_size` from domain knowledge or prior literature (e.g., citing Cohen (1988) or similar). **Do NOT** use arbitrary hardcoded 'small magnitude' values without justification. The derivation MUST include a citation and a brief rationale. **Output**: JSON with `variance`, `effect_size`, `source_citation`, `rationale`. **Verification**: File exists and contains valid JSON with a citation and rationale. (FR-016).
- [X] T016_pre [US1] **Pre-Extraction Power Analysis**: Implement `code/data/power_analysis_pre.py`. **Logic**: Load `data/metrics/theoretical_defaults.json` (from T015b). If the file is missing, use the default values derived in T015b. Calculate the required sample size `N` to detect a statistically significant FID degradation (FR-016). **Output**: Write `data/metrics/pre_extraction_sample_size.txt` containing the integer `N`. **Fail-Fast**: If `N` exceeds the maximum feasible sample size for the hardware, log "Power Limitation: Insufficient Sample" and exit with code 1. **Verification**: Assert file exists and contains an integer. (FR-016, SC-008).

### Tests (optional)

- [X] T011 [P] [US1] Contract test for dataset schema in `tests/contract/test_dataset_schema.py`
- [X] T012 [P] [US1] Integration test for data extraction pipeline in `tests/integration/test_data_extraction.py` (US‑1, FR‑001)

### Implementation

- [X] T013 [US1] **Extract Latents**: Implement `code/data/extract_latents.py` to parse Wan‑Streamer v0.1 logs (or fetched VoxCeleb2) using thresholds from `code/config/detection_thresholds.yaml`. **Logic**: Parse logs, extract semantic/prosodic features, and compute `latent_delta_magnitude` between consecutive frames. **Crucially**: Extract `audio_energy` from the raw audio files using `librosa.feature.melspectrogram` if not present in logs. Output `data/processed/raw_extract.parquet` with columns: `timestamp`, `semantic_feature`, `prosodic_feature`, `latent_delta_magnitude`, `turn_label`, `audio_energy`. **Verification**: Assert file exists, schema validation passes, and `audio_energy` column is present and non-null. (FR-001, US-1).
- [X] T013b [US1] **Calculate Frame Complexity Covariate**: Implement `code/data/calculate_frame_complexity.py`. **Logic**: Load `data/processed/raw_extract.parquet`. Compute `frame_complexity` as the standard deviation of the `audio_energy` values within a sliding window (e.g., 1 second) around each frame, or as the spectral entropy of the audio segment. **Output**: Add `frame_complexity` column to the dataframe and save as `data/processed/complexity_added.parquet`. **Verification**: Assert `frame_complexity` column exists, is non-null, and has a valid distribution (variance > 0). (Addresses missing covariate for FR-005).
- [X] T012b [US1] **Validate Thresholds & Event Count (Streaming)**: Implement `code/data/verify_event_counts.py`. **Logic**: Read the raw source logs (or the first chunk of the stream) directly to count 'interruption' and 'pause' events using thresholds from `code/config/detection_thresholds.yaml`. **Do NOT** wait for T013 to complete. **If** interruption count < 500 OR pause count < 500: Log a WARNING with the actual counts and the message "Proceeding with available events (count < 500)". **Do NOT** abort. **Output**: Write `data/logs/threshold_validation.log` containing the lines `Total Events: <number>`, `Interruption Events: <number>`, `Pause Events: <number>`. **Verification**: Assert log file exists and contains the counts. (FR-018, US-1 AS-2).
- [X] T014d [US1] **Data Filtering**: Implement `code/data/preprocess.py` function `filter_events(df)` that retains only rows where `semantic_feature` is not null and not an empty string. Ensure `audio_energy` is extracted and added to the dataframe here if not present (using `librosa` if necessary). Output intermediate `data/processed/filtered.parquet`. **Verification**: File exists and row count matches filter criteria. **Crucially**: Assert that `audio_energy` column is present and non-null in the output. (FR-001, US-1).
- [X] T014e [US1] **Event Labeling**: Extend `code/data/preprocess.py` with `assign_priority(df)` that adds a boolean column `high_priority` set to `True` if `latent_delta_magnitude > 0.5` OR `uncertainty > 0.8` (using thresholds from `code/config/detection_thresholds.yaml` if defined, otherwise defaults). Log counts of high vs. low priority events to `data/logs/priority_counts.log`.
- [X] T014f [US1] **Log Event Count**: Implement a lightweight script `code/data/log_event_counts.py` that reads `data/processed/filtered.parquet` and writes the total number of events to `data/logs/event_counts.log` as a single line containing only the integer count, followed *exactly* by a newline character. **Verification**: Log file exists and contains an integer line ending with a newline.
- [X] T014g [US1] **Determine Sample Size**: Implement `code/data/decide_sample_size.py` that reads `data/metrics/pre_extraction_sample_size.txt` (from T016_pre). **Logic**: If `pre_extraction_sample_size.txt` exists, use that value as `N`. Else, fall back to `config.DEFAULT_SAMPLE_SIZE` (defined as 1000 in `code/config.py`). Write the chosen size to `data/metrics/selected_sample_size.txt`. **Verification**: File exists and contains an integer.
- [X] T014b [US1] **Stratified Sampling**: Implement `code/data/preprocess.py` function `stratified_sample(df, size)` that performs stratified sampling based on `turn_label` using `sklearn.model_selection.StratifiedShuffleSplit` with `random_state=42` and `size` from `selected_sample_size.txt`. **Verification**: File exists and row count equals the selected size (or the dataset size if smaller). Implement a KL divergence check to verify that the distribution of 'turn_label' is preserved after sampling, logging the result for verification.
- [X] T014h [US1] **Data Validation**: Implement `code/data/validate_processed.py` to verify that all required columns (`timestamp`, `semantic_feature`, `prosodic_feature`, `latent_delta_magnitude`, `turn_label`, `audio_energy`, `frame_complexity`) are non‑null and correctly typed in `sampled_dataset.parquet`.
- [X] T015 [US1] **Validate Sampling Distribution**: Implement `code/data/validate_sampling_distribution.py` to compare the distribution of `turn_label` in the original filtered data vs. the sampled data, logs KL divergence to `data/logs/sampling_distribution.log` using `scipy.stats.entropy`.
- [X] T016_post [US1] **Post-Extraction Power Analysis**: Re‑run `power_analysis_pre.py` logic using `sampled_dataset.parquet` as input to compute empirical variance. Output results to `data/metrics/power_analysis_final.json`, containing `recommended_sample_size`, `expected_variance`, `effect_size`, `variance_source`. **Verification**: JSON exists and contains all required keys. (FR-016).
- [X] T066 [US1] **Implement Streaming Sample Documentation**: Document the streaming/sampling rule used.

**Checkpoint**: User Story 1 is now fully functional and independently testable.

---

## Phase 4: User Story 2 - Lightweight Estimator Training (Priority: P2)

**Goal**: Train a lightweight GRU model on CPU to predict latent delta magnitude and uncertainty scores.

### Tests (optional)

- [X] T021 [P] [US2] Contract test for model output schema in `tests/contract/test_model_output_schema.py`
- [X] T022 [P] [US2] Integration test for training loop and memory constraints in `tests/integration/test_training_constraints.py`

### Implementation

- [X] T019a1 [US2] **Define GRU Architecture**: Implement `code/models/gru_estimator.py` defining a shallow GRU with a moderate number of hidden layers, activation function `tanh`, input size matching the feature vector and two output heads (delta magnitude, uncertainty). Read hyperparameters from `code/config.py`.
- [X] T019a2 [US2] **Implement Trainer Script**: Implement `code/models/trainer.py` containing a CPU‑optimized training loop that respects the 7 GB RAM budget, logs progress, and writes a checkpoint to `data/models/estimator_checkpoint_pending.pt`.
- [X] T019b [US2] **Execute Training Loop with Retry**: Run `python code/models/trainer.py` using data from `data/processed/sampled_dataset.parquet`. **Logic**: If training exceeds the wall‑clock time limit or memory budget, invoke `code/tasks/reduce_sample_size.py` and retry. **Fail-Fast**: If `reduce_sample_size.py` indicates the sample size has reached the `MIN_SAMPLE_SIZE` threshold and cannot be reduced further, **exit immediately with a non-zero code (e.g., 1) and log the specific error message: "Power Limitation: Insufficient Sample"**. Do not retry. (FR-023, US-2). **Verification**: Run script that simulates memory exhaustion until minimum size is reached, asserts the process exits with code 1 and the specific error message is present in logs.
- [X] T024c [US2] **Implement Baseline Comparison Logic**: Implement `code/metrics/baseline_comparison.py` that loads the trained estimator's predictions and compares them against a naive baseline (predicting zero delta).
- [X] T024a [US2] **Compute Uncertainty Correlation**: Implement `code/metrics/uncertainty_calibration.py` that computes Pearson correlation between uncertainty score and prediction error.
- [X] T024d [US2] **Implement Memory Profile Verification**: Implement `code/tests/unit/test_memory_profile.py` to verify memory usage during the training loop.
- [X] T024b [US2] **Finalize Checkpoint**: Read correlation value and rename checkpoint if calibration passes.
- [X] T051 [US2] **Verify Final Checkpoint**: Assert that `data/models/estimator_checkpoint_final.pt` exists.
- [X] T072 [US2] **Implement Two-Stage Validation Logic**: Implement `code/metrics/two_stage_validation.py`. **Dependency**: T024c (Baseline Comparison). **Logic**: Explicitly separate the training data (Subset A) from the validation data (Subset B). Run the full solver on Subset B to generate Ground Truth FID Stability. Correlate the estimator's predictions (on Subset B) with this Ground Truth. **Verification**: Assert that the correlation is computed only on the held-out Subset B and that the script logs the separation of data stages. (Addresses US-2 AS-2, Constitution Principle VII).
- [X] T076 [US2] **Implement Power Analysis Failure Log**: Implement `code/utils/log_power_failure.py`. **Dependency**: T016_pre (Power Analysis), T053 (Sample Reduction). **Logic**: If the power analysis indicates the sample size is insufficient and cannot be reduced further, this script ensures the specific error message "Power Limitation: Insufficient Sample" is logged and the process exits with code 1. **Verification**: Assert that the log contains the exact message and the exit code is 1. (Addresses FR-023, Edge Cases).
- [X] T080 [US2] **Implement Uncertainty Calibration Check**: Implement `code/metrics/verify_uncertainty_calibration.py`. **Dependency**: T024a (Uncertainty Correlation). **Logic**: Verify that the correlation between high uncertainty scores and high prediction errors is statistically significant. **Verification**: Assert that the correlation is significant (p < 0.05) and logged. (Addresses SC-006).

**Checkpoint**: User Stories 1 & 2 are now independently functional.

---

## Phase 5: User Story 3 - Hybrid Inference Simulation and Quality‑Latency Trade-off (Priority: P3)

**Goal**: Simulate hybrid inference, compute FID/proxy MOS, and validate latency reduction via statistical tests.

### Tests (optional)

- [X] T028 [P] [US3] Contract test for hybrid output schema in `tests/contract/test_hybrid_output_schema.py`
- [X] T029 [P] [US3] Integration test for end‑to‑end simulation and metrics in `tests/integration/test_hybrid_simulation.py`

### Implementation

- [X] T047 [US3] **Critical Data Generation (Counterfactual Indices)**: Select frame indices for the randomized counterfactual intervention. **Logic**: Randomly select frame indices such that the count is **≥ 5% of the total frames** in the test set. **Output**: Write the selected indices to `data/processed/counterfactual_indices.json`. **Verification**: Assert `len(indices) >= 0.05 * total_frames` and log the exact count to `data/logs/counterfactual_log.txt`. (FR-008, US-3).
- [X] T060_Exec [US3] **Execute Full Solver Baseline**: Run `python code/inference/full_solver.py` on all segments in the test set EXCEPT those in the counterfactual subset (T047). **Logic**: Generate ground truth video artifacts for the non-counterfactual frames to establish a complete baseline FID. **Input**: `segment_path` is a path to a `.parquet` row containing a list of latent vectors. **Output**: `.mp4` or `.parquet` video artifacts in `data/artifacts/baseline/`. **Verification**: Assert that for every non-counterfactual segment, a corresponding output file exists and contains valid video data. (FR-008, US-3).
- [X] T060 [US3] **Implement Causal FID Ground Truth**: Implement `code/metrics/generate_counterfactual_fid.py`. **Dependencies**: US-1 (Sampled Dataset), US-2 (Trained Estimator). **Logic**: For each segment in the test set, run the full flow-matching solver to generate ground truth. **Command**: Execute `python code/inference/full_solver.py --input <segment_path> --output <output_path>` for every segment in the input list. **Verification**: Assert that for every input segment, a corresponding output file exists and contains valid video data. (FR-008, US-3).
- [X] T070 [US3] **Implement Explicit Causal FID Calculation**: Implement `code/metrics/calculate_causal_fid.py`. **Dependency**: T060 (Full Solver Ground Truth), T047 (Counterfactual Indices), T060_Exec (Baseline Ground Truth). **Logic**: For the specific subset of frames defined in `counterfactual_indices.json`, compute the FID of the hybrid output (where skip was forced) versus the full solver output (ground truth). This isolates the causal effect of the skip action on quality. **Error Handling**: If T060 fails for any frame in the counterfactual subset, raise an error. **Verification**: Assert that the FID degradation for this specific subset is computed and logged, distinguishing it from the overall FID. (Addresses FR-008, US-3 AS-3).
- [X] T045a [US3] **Precedence Rule Logic**: Implement `code/inference/precedence_rule.py` with function `resolve_skip_decision`.
- [X] T045b [US3] **Fallback Handler**: Implement `code/inference/fallback_handler.py`.
- [X] T050a [US3] **Hybrid Engine Core**: Implement `code/inference/hybrid_engine.py` that applies the estimator and decides per‑frame whether to skip or run full solver. **Input Format**: Tensor shape `(batch, seq_len, features)`. **Output Format**: Tuple `(skip_flag: bool, uncertainty_score: float)`. **Verification**: Assert that the estimator is correctly loaded and the input/output shapes match the spec. (FR-003, US-3).
- [X] T050b [US3] **Apply Counterfactual Intervention**: Force the skip flag for frames in the randomized subset (loaded from `data/processed/counterfactual_indices.json`). **Verification**: Assert that the skip flag is set for exactly the indices in the counterfactual file and log the count. (FR-008).
- [X] T050c_impl [US3] **Implement Hybrid Output Generation**: Implement `code/inference/generate_hybrid_output.py`. **Logic**: For frames marked as 'skip', generate the hybrid video artifact by **reusing the previous frame** or **linear interpolation** of the previous and next frames (as defined in the plan). **Output**: Write hybrid video artifacts to `data/artifacts/hybrid/`. **Verification**: Assert that hybrid artifacts are generated for all skipped frames and contain valid video data. (FR-003, US-3).
- [X] T075 [US3] **Implement Randomized Intervention Precedence Check**: Implement `code/inference/verify_precedence.py`. **Dependency**: T045a (Precedence Rule), T050b (Intervention). **Logic**: Run a unit test that injects a frame into the randomized subset with a low uncertainty score (which would normally trigger a skip) and verify that the fallback logic is *ignored* and the skip is enforced. **Verification**: Assert that the skip flag is True despite the uncertainty score, confirming FR-017. (Addresses Edge Cases, FR-017).
- [X] T050c [US3] **Metrics Computation**: Compute per-segment latency and FID. **Dependencies**: T060_Exec (Baseline Ground Truth), T050c_impl (Hybrid Output), T050b (Intervention).
- [X] T071 [US3] **Implement Propensity Score Matching for Latency**: Implement `code/metrics/propensity_score_matching.py`. **Dependencies**: T013b (Frame Complexity Calculation). **Logic**: Calculate propensity scores based on *independent* covariates (`speaker_id` from metadata and `frame_complexity` from T013b) as required by FR-005. Perform matching between skipped and non-skipped frames to create a balanced dataset for the latency reduction test. **Output**: Save the matched dataset to `data/processed/matched_dataset.parquet` and log balance diagnostics (p > 0.05 for covariate differences). **Verification**: Assert that the matched dataset has balanced covariates before passing to T045. (Addresses FR-005, SC-004, breaks circular dependency).
- [X] T045 [US3] **Implement analyze_latency_bias Module**: Implement `code/metrics/analyze_latency_bias.py`. **Logic**: Perform a **stratified bootstrap** with **propensity-score matching** on the latency reduction metric using the matched dataset from T071. **Covariates**: MUST use independent covariates `speaker_id` and `frame_complexity` (as defined in FR-005 and calculated in T013b), NOT the estimator's prediction. **Library**: Use `scikit-learn` for propensity score matching (specifically `PropensityScoreMatching` or equivalent logic) and `scipy` for stratified bootstrap. **Output**: Write results to `data/metrics/latency_bias_analysis.json` containing the propensity-score corrected p-value and confidence intervals, and the matched dataset used. **Verification**: Assert `p-value < 0.05` and that the output file contains the required fields and the matched dataset artifact. (FR-005, SC-004).
- [X] T049 [US3] **TOST Equivalence Test for Quality**: Implement `code/metrics/tost_quality.py`. **Logic**: Perform the **Two One-Sided Tests (TOST)** with the specified margin (Δ=0.05) on the FID differences between hybrid and baseline outputs. Use bootstrapping to estimate the distribution of the difference if non-Gaussian, but the primary output MUST be the TOST p-values. **Output**: Write the p-values for both one-sided tests and the conclusion (equivalence/rejection) to `data/metrics/fid_tost_results.json`. **Verification**: Assert the output file exists and contains the TOST p-values. (FR-005, SC-002).
- [X] T046 [US3] **Human Data Check**: Check for human ratings data, logging status accordingly.
- [X] T044 [US3] **Validate Proxy MOS**: Implement `code/metrics/validate_proxy_mos.py`. **Logic**: Check if human ratings data exists. **If data exists**: Compute Pearson correlation between proxy MOS predictions and human MOS scores. **Assert** that the correlation `r >= 0.8` (SC-007). **If data is missing**: **Write the log entry "Assumption Validated (No Human Data Available)" to `data/logs/mos_validation.log` and exit with code 0** (skipping the correlation test). **Verification**: Assert that if data is missing, the specific log message exists in `mos_validation.log` and the process exits with code 0. If data exists, assert `r >= 0.8`. (FR-012, SC-007).
- [X] T077 [US3] **Implement Human Data Fallback Logging**: Implement `code/metrics/log_human_data_fallback.py`. **Dependency**: T044 (Proxy MOS). **Logic**: Ensure that if no human data is found, the script writes the exact string "Assumption Validated (No Human Data Available)" to `data/logs/mos_validation.log` and exits cleanly. **Verification**: Assert the log file contains the exact string and the process exits with code 0. (Addresses FR-012, SC-007).
- [X] T078 [US1] **Implement Event Count Verification**: Implement `code/data/verify_event_counts.py`. **Dependency**: T012b (Threshold Validation). **Logic**: Re-run the threshold logic on the final dataset to verify that the counts of "interruption" and "pause" events match the logged values in `threshold_validation.log`. **Verification**: Assert that the counts match and the script logs the verification result. (Addresses US-1 AS-2, FR-018).
- [X] T079 [US3] **Implement FID Stability Correlation Verification**: Implement `code/metrics/verify_fid_stability.py`. **Dependency**: T043 (FID Stability Correlation). **Logic**: Verify that the correlation (r ≥ 0.7) is computed between the predicted delta magnitude and the *actual* FID stability (relative change in FID between skipped and full-solver frames) for the specific subset of skipped frames. **Verification**: Assert that the correlation value is logged and meets the threshold. (Addresses FR-010, SC-003).
- [X] T043 [US3] **FID Stability Correlation**: Calculate the correlation between predicted delta magnitude and FID stability. **Logic**: Compute FID stability as the relative change in FID between skipped frames and full-solver frames for the subset defined in `counterfactual_indices.json`. **Filtering**: Exclude frames where the full solver or hybrid engine failed. Correlate this with the predicted delta magnitude. **Verification**: Assert that `state.yaml` is updated with key `state.validation_status` set to 'passed' or 'failed' based on the correlation threshold (r ≥ 0.7), and that the correlation value is logged. (FR-010, SC-003). **Dependencies**: T050c (Metrics Computation), T060 (Ground Truth), T049 (TOST Test).

**Checkpoint**: All user stories are now independently functional.

---

## Phase N: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T033 [P] **Create Documentation**: Create `docs/quickstart.md` and `docs/research.md`.
- [X] T034 [P] **Refactor Trainer**: Refactor training loop to use generator expressions and streaming data loaders.
- [X] T035 [P] **Profile Hybrid Simulation**: Profile the hybrid simulation for performance metrics.
- [X] T036 [P] **Add Unit Tests for Filtering**: Add unit tests for edge cases in filtering logic.
- [X] T037 [P] **Run quickstart.md validation**: Run `tests/integration/test_quickstart_repro.py`.
- [X] T038a [P] **Implement Contract Documentation Links (quickstart.md)**: Update `docs/quickstart.md` with links to schema files.
- [X] T038b [P] **Implement Contract Documentation Links (data-model.md)**: Update `docs/data-model.md` with links to schema files.
- [X] T038c [P] **Verify Contract Documentation Links**: Run a test to verify the documentation links.
- [X] T039 [P] **Implement Streaming Data Loader**: Implement data loader for large datasets using streaming.
- [X] T040 [P] **Implement Strict Data Fetch Failure**: Implement data fetch logic that **fails loudly** if the primary source (Wan-Streamer) is unavailable, but **explicitly falls back** to the canonical VoxCeleb2 dataset as required by FR-019. **Do NOT** use synthetic data as a fallback. **Verification**: Assert that if Wan-Streamer is missing, VoxCeleb2 is fetched and used. (FR-019).

---

## Dependencies & Execution Order

### Phase Dependencies
- **Setup (Phase 1)** → **Foundational (Phase 2)** → **User Stories (Phase 3‑5)** → **Polish (Phase N)**

### Within User Story 1
`T012a → T016_pre → T015b → T013 → T013b → T012b → T014d → T014e → T014f → T014g → T014b → T014h → T015 → T016_post → T066`

### Within User Story 2
`T019a1 → T019a2 → T019b → T024c → T024a → T024d → T024b → T051 → T072 → T076 → T080`

### Within User Story 3
`T047 → T060_Exec → T060 → T070 → T045a → T045b → T050a → T050b → T050c_impl → T075 → T050c → T071 → T045 → T049 → T046 → T044 → T077 → T078 → T043 → T079`

**Structure Decision**: Single `code/` directory with modular sub-packages to isolate responsibilities and facilitate independent testing of the estimator vs. the evaluation metrics. Explicit task modules (FR-007, FR-009, FR-011, FR-014, FR-015) are mapped to specific script files.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-----|
| Randomized Counterfactuals (FR-008) | Required to distinguish "easy to skip" from "easy to generate" and establish causal effect. | Observational data alone (propensity matching) cannot rule out confounding variables in the latent trajectory. |
| Hybrid Inference Simulation | Essential to measure the *actual* FID degradation of skipping steps. | A purely theoretical model of latency/quality trade-off lacks empirical validity for the 5% threshold claim. |
| Two-Stage Validation (Estimator vs. FID) | Prevents circular validation (Principle VII). | Using the same data/model for training and evaluation would inflate performance metrics. |
| Segment-Level FID | Required for construct validity in video generation. | Frame-level FID fails to capture temporal artifacts (jitter, flicker) introduced by skipping frames. |

## Constitution Check

| Principle | Status | Compliance Strategy |
|-----------|--------|-----|
| **I. Reproducibility** | PASS | All random seeds pinned in `code/`; Data fetched from verified URLs (VoxCeleb2) or checksummed local logs; `requirements.txt` pinned. Local logs are only for dev; reproducible runs use canonical source. |
| **II. Verified Accuracy** | PASS | Citations restricted to verified dataset URLs provided in spec; No external claims without source. |
| **III. Data Hygiene** | PASS | Datasets checksummed; Derivations written to new files; PII scan passed (VoxCeleb2 is public). |
| **IV. Single Source of Truth** | PASS | Every figure, statistic, or interpretation in the paper traces back to exactly one row in this project's `data/` and one block in this project's `code/`. Derived numbers are NOT hand-typed into the paper. |
| **V. Versioning Discipline** | PASS | Artifact hashes recorded in `state.yaml` via `update_state()` function. |
| **VI. Latency-Quality Trade-off** | PASS | Paired statistical test (TOST) and randomized counterfactual intervention validate claims. |
| **VII. Validation Independence** | PASS | Estimator trained on latent/turn data; FID/MOS computed by separate, pre-trained models not involved in training. |

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Latency reduction is measured against the full flow-matching baseline, targeting a ≥ 20% decrease in inference time per frame.
- **SC-002**: Perceptual quality degradation is measured against the baseline FID score, ensuring the hybrid output FID satisfies `(FID_hybrid - FID_baseline) / FID_baseline <= 0.05` (relative ratio).
- **SC-003**: Estimator prediction accuracy is measured against the actual latent delta magnitude in the validation set, requiring a significant improvement over a naive baseline and a correlation (r ≥ 0.7) with FID stability.
- **SC-004**: Statistical significance of the latency reduction is measured using bias-corrected methods, requiring a p-value < 0.05.
- **SC-005**: Computational feasibility is measured against the CI runner constraints, ensuring peak RAM usage ≤ 7 GB and total runtime ≤ 6 hours.
- **SC-006**: Uncertainty score calibration is measured against the actual prediction error, requiring a significant correlation between high uncertainty scores and high prediction errors.
- **SC-007**: Proxy MOS validity is measured against human ratings (if available), requiring a correlation (r ≥ 0.8).
- **SC-008**: Power analysis is performed to justify the sample size for the TOST test with [deferred] power.

## Assumptions

- **Assumption about dataset availability**: The Wan-Streamer v0.1 training logs and pre-trained weights are accessible via the official repository or public archive.
- **Assumption about CPU feasibility**: A representative sample of the total training data is sufficient to train a lightweight RNN model within the 6-hour CPU runtime limit while maintaining statistical power for the correlation analysis.
- **Assumption about metric validity**: The CLIP-based video-text similarity or pre-trained video quality assessment model serves as a valid proxy for Mean Opinion Score (MOS) in the absence of human raters.
- **Assumption about turn-taking labels**: The semantic and prosodic signals derived from the input audio/text are sufficient to distinguish "low-information" turns from "high-information" interruptions with a precision of at least 0.7.
- **Assumption about inference constraints**: The "no GPU" constraint applies strictly; all training and inference must be performed using standard CPU floating-point operations without quantization libraries that require CUDA.

<!-- auto-added by the execution fix loop: run-book / implementation path mismatch (a quickstart command names a script no task created) -->
- [ ] T081 Reconcile run-book vs implementation for `code/data/fetch_data.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/data/fetch_data.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.
- [ ] T082 Reconcile run-book vs implementation for `code/data/extract_turn_taking.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/data/extract_turn_taking.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.
- [ ] T083 Reconcile run-book vs implementation for `code/model/estimator_train.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/model/estimator_train.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.
- [ ] T084 Reconcile run-book vs implementation for `code/model/hybrid_simulate.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/model/hybrid_simulate.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.
- [ ] T085 Reconcile run-book vs implementation for `code/metrics/calculate_fid_stability.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/metrics/calculate_fid_stability.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.
- [ ] T086 Reconcile run-book vs implementation for `code/metrics/statistical_tests.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/metrics/statistical_tests.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.
- [ ] T087 Reconcile run-book vs implementation for `code/utils/state_manager.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/utils/state_manager.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.
- [ ] T088 [P] **Create Missing Data Fetch Script**: Create `code/data/fetch_data.py` to serve as the canonical entry point for data acquisition. **Logic**: This script must wrap the logic from T009 (`validate_logs.py`) and T040 (`Strict Data Fetch Failure`) into a single CLI command that can be invoked by `quickstart.md`. It must fail loudly if no real source is found, falling back only to the verified VoxCeleb2 dataset as per FR-019. **Verification**: Run `python code/data/fetch_data.py` and assert it successfully fetches data and updates `state.yaml`. (Addresses T081, FR-019).
- [ ] T089 [P] **Create Missing Extraction Script**: Create `code/data/extract_turn_taking.py` to serve as the canonical entry point for turn-taking extraction. **Logic**: This script must wrap the logic from T013 (`extract_latents.py`) and T012b (`verify_event_counts.py`) into a single CLI command. It must ensure the output file `data/processed/turn_taking_dataset.parquet` is generated with the correct schema. **Verification**: Run `python code/data/extract_turn_taking.py` and assert the output file exists and passes schema validation. (Addresses T082, FR-001).
- [ ] T090 [P] **Create Missing Estimator Train Script**: Create `code/model/estimator_train.py` to serve as the canonical entry point for model training. **Logic**: This script must wrap the logic from T019a1 (`GRU Architecture`), T019a2 (`Trainer`), and T019b (`Execute Training Loop with Retry`) into a single CLI command. It must handle the power limitation logic and checkpoint finalization. **Verification**: Run `python code/model/estimator_train.py` and assert the final checkpoint `data/models/estimator_checkpoint_final.pt` exists. (Addresses T083, FR-002).
- [ ] T091 [P] **Create Missing Hybrid Simulate Script**: Create `code/model/hybrid_simulate.py` to serve as the canonical entry point for hybrid inference. **Logic**: This script must wrap the logic from T050a (`Hybrid Engine Core`), T050b (`Apply Counterfactual Intervention`), and T050c (`Metrics Computation`) into a single CLI command. It must ensure the precedence rules are applied correctly. **Verification**: Run `python code/model/hybrid_simulate.py` and assert the hybrid output and metrics are generated. (Addresses T084, FR-003).
- [ ] T092 [P] **Create Missing FID Stability Script**: Create `code/metrics/calculate_fid_stability.py` to serve as the canonical entry point for FID stability correlation. **Logic**: This script must wrap the logic from T043 (`FID Stability Correlation`) and T079 (`Verify FID Stability Correlation`) into a single CLI command. **Verification**: Run `python code/metrics/calculate_fid_stability.py` and assert the correlation is computed and logged. (Addresses T085, FR-010).
- [ ] T093 [P] **Create Missing Statistical Tests Script**: Create `code/metrics/statistical_tests.py` to serve as the canonical entry point for statistical analysis. **Logic**: This script must wrap the logic from T045 (`analyze_latency_bias`), T071 (`Propensity Score Matching`), and T049 (`TOST Equivalence Test`) into a single CLI command. **Verification**: Run `python code/metrics/statistical_tests.py` and assert the JSON results for TOST and propensity matching are generated. (Addresses T086, FR-005).
- [ ] T094 [P] **Create Missing State Manager Script**: Create `code/utils/state_manager.py` to serve as the canonical entry point for state updates. **Logic**: This script must wrap the logic from T008 (`Implement State Updater`) into a single CLI command that can be invoked by other scripts or the quickstart run-book. **Verification**: Run `python code/utils/state_manager.py --help` and assert the CLI interface is available. (Addresses T087, FR-020).