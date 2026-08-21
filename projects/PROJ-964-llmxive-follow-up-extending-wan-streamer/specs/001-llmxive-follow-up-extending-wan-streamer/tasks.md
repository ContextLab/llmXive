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

- [X] T002 [P] **Initialize Project Directory Structure**: Create all required directories (`code/`, `data/`, `state/`, `docs/`, `contracts/`, `tests/`) and subdirectories (`data/raw`, `data/processed`, `code/data`, `code/models`, etc.). **Verification**: Run a script `tests/unit/test_setup_verification.py` that asserts `os.path.isdir` for all required paths. (Consolidated from T002a-T002h).
- [X] T005a [P] Create `code/requirements.txt` with CPU-only dependencies (`torch`, `scikit-learn`, `pandas`, `numpy`, `datasets`, `scipy`, `pyyaml`, `videomae`). **Verification**: Run `os.path.exists('code/requirements.txt')` and assert True.
- [X] T005b [P] Implement `code/config.py` to pin the exact HuggingFace dataset revision for VoxCeleb2 (FR-019, Constitution Principle I). **Verification**: Run `os.path.exists('code/config.py')` and assert True.
- [X] T005d [P] Create `pyproject.toml` with black formatting configuration. **Verification**: Run `os.path.exists('pyproject.toml')` and assert True.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

- [X] T007a [P] **Implement Seed Pinning**: Implement `code/utils/config.py` function `set_seed(seed=42)` that sets `torch.manual_seed`, `numpy.random.seed`, and `random.seed`. **Verification**: Run script that asserts all seeds are set to 42. (FR-001, Constitution Principle I).
- [X] T007b [P] **Implement Path Configuration**: Implement `code/utils/config.py` constants `RAW_DATA_PATH`, `PROCESSED_DATA_PATH`, `MODEL_PATH`, `STATE_PATH`. **Verification**: Run script that asserts constants are defined and point to correct relative paths. (FR-001).
- [X] T008 [P] **Implement State Updater**: Implement `code/utils/update_state_yaml.py` function `update_state(artifact_path, key)` that reads `state.yaml`, computes MD5 hash of `artifact_path`, updates `artifact_hashes[key]`, and writes back. **Verification**: Run script that creates a dummy file, calls function, and asserts hash is recorded in `state.yaml`. (Constitution Principle V, FR-020).
- [X] T009 [P] **Implement Data Source Check**: Implement `code/data/validate_logs.py` to check for Wan-Streamer v0.1 logs first; if missing, fetch the canonical VoxCeleb2 dataset. **Logic**: 1. Check `os.path.exists('data/raw/wan-streamer-logs')`. If True, register checksum and set `data_source='wan-streamer'`. 2. If False, check `os.path.exists('data/raw/voxceleb2')`. If True, register checksum and set `data_source='voxceleb2'`. 3. If both missing, fetch `voxceleb2` via `datasets.load_dataset`, register checksum, set `data_source='voxceleb2'`. **Crucially, this task MUST explicitly call the `update_state()` function from T008 with the path and MD5 hash of the downloaded dataset to write the checksum to `state.yaml` before returning.** (FR-019, FR-022, Assumption about dataset availability).
- [X] T010 [P] **Implement Validators**: Implement `code/utils/validators.py` function `validate_schema(df, schema_path)` that loads schema from `contracts/dataset.schema.yaml` and validates `df` using `pandera`. **Dependency**: T009 must complete successfully before T010 runs. T010 reads the `data_source` flag set by T009. (FR-001, FR-010).
- [X] T053 [P] **Implement Sample Size Reduction Module**: Implement `code/tasks/reduce_sample_size.py` that calculates a *deferred* reduction amount based on the current sample size, the minimum required size from power analysis (`MIN_SAMPLE_SIZE` defined in `code/config.py`), and the memory budget (≤ 7 GB). If reduction would bring size below `MIN_SAMPLE_SIZE`, raise a `PowerLimitationError`. Expose `reduce_sample_size(current_size) -> new_size`. (FR-014, FR-023). **Dependency**: None (standalone utility).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Extraction and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Extract time-series latent vectors and turn‑taking labels from real Wan‑Streamer v0.1 logs (or VoxCeleb2 fallback) to create a CPU‑tractable dataset.

### Tests (optional)

- [X] T011 [P] [US1] Contract test for dataset schema in `tests/contract/test_dataset_schema.py`
- [X] T012 [P] [US1] Integration test for data extraction pipeline in `tests/integration/test_data_extraction.py` (US‑1, FR‑001)

### Implementation

- [X] T012a [P] [US1] **Define Threshold Algorithm**: Create `code/config/detection_thresholds.yaml` to define the algorithm and default parameters for classifying 'interruption' and 'pause' events (e.g., `audio_energy_threshold: 20` dB). **Note**: Thresholds are chosen to maximize the number of detected events; verification of the resulting count occurs in T012b. (FR‑018, US‑1).
- [X] T013 [US1] [FR‑001] **Extract Latents**: Implement `code/data/extract_latents.py` to parse Wan‑Streamer v0.1 logs (or fetched VoxCeleb2) using thresholds from `code/config/detection_thresholds.yaml` and output `data/processed/raw_extract.parquet`. **Verification**: Assert file exists and schema validation passes. (FR‑001, US‑1).
- [X] T012b [US1] **Validate Thresholds & Event Count**: Load `data/processed/raw_extract.parquet` (produced by T013), apply thresholds from `code/config/detection_thresholds.yaml`, compute the total event count, interruption event count, and pause event count. Write `data/logs/threshold_validation.log` containing the lines `Total Events: <number>`, `Interruption Events: <number>`, `Pause Events: <number>`. **If interruption count < 500 OR pause count < 500**, log an error message `WARNING: insufficient events (<count>)` and continue (do not abort). **Verification**: Assert the log file exists, contains the exact count lines for all three event types, and that the task exits with code 0 regardless of count (logging the warning). (FR‑018, US‑1, AS‑2).
- [X] T014d [US1] **Data Filtering**: Implement `code/data/preprocess.py` function `filter_events(df)` that retains only rows where `semantic_feature` is not null and not an empty string. **Ensure `audio_energy` is extracted and added to the dataframe here** if not present. Output intermediate `data/processed/filtered.parquet`. **Verification**: File exists and row count matches filter criteria. (FR‑001, US‑1).
- [X] T014e [US1] **Event Labeling**: Extend `code/data/preprocess.py` with `assign_priority(df)` that adds a boolean column `high_priority` set to `True` if `latent_delta_magnitude > 0.5` OR `uncertainty > 0.8` (using thresholds from `code/config/detection_thresholds.yaml` if defined, otherwise defaults). Log counts of high vs. low priority events to `data/logs/priority_counts.log` in the format `High Priority: <count>, Low Priority: <count>`. **Verification**: Log file exists and contains both counts in the specified format. (FR‑001, US‑1).
- [X] T014f [US1] **Log Event Count**: Implement a lightweight script `code/data/log_event_counts.py` that reads `data/processed/filtered.parquet` and writes the total number of events to `data/logs/event_counts.log` as a single line containing only the integer count. **Verification**: Log file exists and contains an integer line. (FR‑001, US‑1).
- [X] T015b [US1] **Generate Theoretical Defaults**: Implement `code/data/generate_defaults.py` to create `data/metrics/theoretical_defaults.json` with hardcoded defaults (`variance:`, `effect_size: a small magnitude`) if the file does not exist. **Verification**: File exists and contains valid JSON. (FR‑016, SC‑008).
- [X] T016 [US1] **Critical Statistical Prep (Initial Power Analysis)**: Implement `code/data/power_analysis_initial.py` that reads `data/processed/filtered.parquet`. If the file exists, compute empirical variance of `latent_delta_magnitude`; otherwise load defaults from `data/metrics/theoretical_defaults.json` (generated by T015b). **Crucially, if `data/metrics/theoretical_defaults.json` does not exist, this script MUST generate it with hardcoded defaults before proceeding.** Output `data/metrics/power_analysis_initial.json` with fields `recommended_sample_size`, `expected_variance`, `effect_size`, `variance_source`. (FR‑016, SC‑008). **Dependency**: T015b.
- [X] T014g [US1] **Determine Sample Size**: Implement `code/data/decide_sample_size.py` that reads `power_analysis_initial.json`; if `recommended_sample_size` is present, use it, else fall back to `config.DEFAULT_SAMPLE_SIZE` (defined in `code/config.py` as a substantial default value). Write the chosen size to `data/metrics/selected_sample_size.txt`. **Verification**: File exists and contains an integer. (FR‑015, US‑1).
- [X] T014b [US1] **Stratified Sampling**: Implement `code/data/preprocess.py` function `stratified_sample(df, size)` that performs stratified sampling based on `turn_label` using `sklearn.model_selection.StratifiedShuffleSplit` with `random_state=42` and `size` from `selected_sample_size.txt`. Output `data/processed/sampled_dataset.parquet`. **Dependency**: T014g. **Verification**: File exists and row count equals the selected size (or the dataset size if smaller). (FR‑015, US‑1).
- [X] T014h [US1] **Data Validation**: Implement `code/data/validate_processed.py` to verify that all required columns (`timestamp`, `semantic_feature`, `prosodic_feature`, `latent_delta_magnitude`, `turn_label`, `audio_energy`) are non‑null and correctly typed in `sampled_dataset.parquet`. `timestamp` must be ISO 8601 datetime, others numeric. Write a validation report `data/logs/validation_report.txt`. **Verification**: Report file exists and contains `PASS`. (FR‑001, US‑1).
- [X] T015 [US1] **Validate Sampling Distribution**: Implement `code/data/validate_sampling_distribution.py` that compares the distribution of `turn_label` in the original filtered data vs. the sampled data, logs KL divergence to `data/logs/sampling_distribution.log` using `scipy.stats.entropy` with `base=2`. **Dependency**: T014b. **Verification**: Log file exists and contains a numeric divergence value. (FR‑015).
- [X] T017 [US1] **Final Power Analysis**: Re‑run `power_analysis_initial.py` using `sampled_dataset.parquet` as input (pass `--input sampled_dataset.parquet --output data/metrics/power_analysis_final.json` flag). Output `data/metrics/power_analysis_final.json`. This confirms that the final sample size satisfies power requirements. (FR‑016, SC‑008). **Dependency**: T014b.

**Checkpoint**: User Story 1 is now fully functional and independently testable.

---

## Phase 4: User Story 2 - Lightweight Estimator Training (Priority: P2)

**Goal**: Train a lightweight GRU model on CPU to predict latent delta magnitude and uncertainty scores.

### Tests (optional)

- [X] T021 [P] [US2] Contract test for model output schema in `tests/contract/test_model_output_schema.py`
- [X] T022 [P] [US2] Integration test for training loop and memory constraints in `tests/integration/test_training_constraints.py`

### Implementation

- [X] T019a1 [US2] **Define GRU Architecture**: Implement `code/models/gru_estimator.py` defining a shallow GRU with a moderate number of hidden layers, activation function `tanh`, input size matching the feature vector and two output heads (delta magnitude, uncertainty). Read hyperparameters from `code/config.py`. **Verification**: Class can be instantiated without error. (FR‑002).
- [X] T019a2 [US2] **Implement Trainer Script**: Implement `code/models/trainer.py` containing a CPU‑optimized training loop that respects the 7 GB RAM budget, logs progress, and writes a checkpoint to `data/models/estimator_checkpoint_pending.pt` with metadata `pending_validation: True`. Use `nn.MSELoss`, `torch.optim.Adam` with `lr=0.001`, `weight_decay=1e-5`, and `batch_size=64`. **Verification**: Script exists and runs without exceeding memory limits on a small test subset. (FR‑002, FR‑014).
- [X] T019b [US2] **Execute Training Loop with Retry**: Run `python code/models/trainer.py` using data from `data/processed/sampled_dataset.parquet`. If training exceeds the 6-hour wall‑clock limit or memory budget, invoke `code/tasks/reduce_sample_size.py` (T053) with the current size and `max_retries=3` to compute a reduced size, truncate the dataset accordingly, and retry. Perform a limited number of attempts; after the designated maximum number of failures, log `Power Limitation` and exit with code 1. Upon successful training, also run a counterfactual full‑solver evaluation on a random [deferred] subset to produce `data/metrics/counterfactual_fid.json`. **Verification**: Checkpoint file exists with `pending_validation: True` and counterfactual FID file exists; on failure, appropriate log and non-zero exit code. (FR‑002, FR‑014, FR‑008).
- [X] T024c [US2] **Implement Baseline Comparison Logic**: Implement `code/metrics/baseline_comparison.py` that loads the trained estimator's predictions and compares them against a naive baseline (predicting zero delta) on the validation set. Calculate the MSE for both and assert the estimator's MSE is at least 10% lower. Write results to `data/metrics/baseline_comparison.json`. **Verification**: JSON exists and contains `passed: true`. (US‑2 AS‑2). **Dependency**: T019b.
- [X] T024a [US2] **Compute Uncertainty Correlation**: Implement `code/metrics/uncertainty_calibration.py` that loads `estimator_checkpoint_pending.pt` and the validation split ([deferred], `random_state=42`) of `sampled_dataset.parquet`, computes Pearson correlation `r` between `uncertainty_score` and `abs(prediction_error - ground_truth_delta)` using `scipy.stats.pearsonr`, asserts `r >= 0.7`. Write `data/metrics/uncertainty_correlation.json` with fields `correlation` and `passed`. **Verification**: File exists and `passed` is true only if `r >= 0.7`. (SC‑006).
- [X] T024d [US2] **Implement Memory Profile Verification**: Implement `code/tests/unit/test_memory_profile.py` to verify that the training script (T019a2) does not exceed the 7 GB RAM limit by profiling memory usage during the training loop. **Verification**: Test passes if peak RAM < 7 GB. (US‑2 AS‑3, FR‑002). **Dependency**: T019a2.
- [X] T024b [US2] **Finalize Checkpoint**: Read `data/metrics/uncertainty_correlation.json` key `correlation`. If `correlation >= 0.7`, rename `estimator_checkpoint_pending.pt` to `estimator_checkpoint_final.pt`, update `state.yaml` key `state.calibration.status` to `'passed'`. Otherwise, write `data/logs/uncertainty_calibration_failed.log` and set `state.calibration.status` to `'failed'` in `state.yaml`. **Verification**: Final checkpoint exists only when calibration passes; state reflects status. (FR‑002, SC‑006, Constitution Principle VI).
- [X] T051 [US2] **Verify Final Checkpoint**: Assert that `data/models/estimator_checkpoint_final.pt` exists (or fail if calibration failed). Update `state.yaml` key `state.artifacts.estimator.ready` to `true` when the file is present. **Verification**: Simple existence check and state update. (FR‑002).

**Checkpoint**: User Stories 1 & 2 are now independently functional.

---

## Phase 5: User Story 3 - Hybrid Inference Simulation and Quality‑Latency Trade‑off (Priority: P3)

**Goal**: Simulate hybrid inference, compute FID/proxy MOS, and validate latency reduction via statistical tests.

### Tests (optional)

- [X] T028 [P] [US3] Contract test for hybrid output schema in `tests/contract/test_hybrid_output_schema.py`
- [X] T029 [P] [US3] Integration test for end‑to‑end simulation and metrics in `tests/integration/test_hybrid_simulation.py`

### Implementation

- [X] T060 [US3] **Implement Causal FID Ground Truth**: **MUST RUN BEFORE T050a.** Implement `code/metrics/generate_counterfactual_fid.py` to execute the FULL flow-matching solver on a specific subset of frames (defined in T047) to generate the ground-truth video frames. Compute FID for these specific frames against the real data ground truth and write `data/metrics/counterfactual_fid_ground_truth.json`. **Rationale**: FR-008 and US-3 AS-2 require a counterfactual measurement procedure where the full solver is run on the same frames to establish ground truth FID. **Verification**: File exists and contains FID scores. (FR‑008, US‑3). **Dependency**: T047.
- [X] T047 [US3] **Critical Data Generation (Counterfactual Indices)**: Using a seeded random number generator, select frame indices representing a **representative proportion** of total frames **and** meeting the minimum required size from `power_analysis_final.json` (field `recommended_sample_size`). Calculate size as `max([deferred] of total frames, N_min)` where `N_min` is from `power_analysis_final.json`. Write `data/processed/counterfactual_indices.parquet` with schema `frame_id` (int64). Log the actual proportion and any size adjustments. **Verification**: File exists, proportion ≥ 5 %, and size ≥ minimum required; log contains these details. (FR‑008, SC‑008). **Dependency**: T017 (Phase 3).
- [X] T045a [US3] **Precedence Rule Logic**: Implement `code/inference/precedence_rule.py` with function `resolve_skip_decision(frame_id, uncertainty, randomized_flag)` where `randomized_flag` is a boolean derived from checking if `frame_id` is in `counterfactual_indices.parquet` (load this file at module load time or pass as argument). If `randomized_flag` is True, return True (skip); else return uncertainty > threshold. **Verification**: Unit test ensures precedence behavior. (FR‑017, FR‑009). **Dependency**: T047.
- [X] T045b [US3] **Fallback Handler**: Implement `code/inference/fallback_handler.py` that triggers the full solver when `uncertainty > 0.8` (from config) or `delta magnitude` > 0.5 (from config), respecting the precedence rule from T045a by calling `precedence_rule.resolve_skip_decision`. **Verification**: Module can be imported and decision function returns correct boolean. (FR‑006, FR‑009, FR‑017). **Dependency**: T047, T045a.
- [X] T050a [US3] **Hybrid Engine Core**: Implement `code/inference/hybrid_engine.py` that loads the trained estimator, reads `sampled_dataset.parquet`, applies the estimator to obtain predictions, and decides per‑frame whether to skip or run full solver based on `uncertainty` (from estimator output) and the precedence rule (skip if uncertainty < threshold and not randomized_flag). Output intermediate `data/processed/hybrid_predictions.parquet`. **Verification**: File exists and contains columns `frame_id`, `predicted_delta`, `uncertainty`, `skip_flag_preliminary`. (FR‑003, US‑3). **Dependency**: T045a, T045b, T060.
- [X] T050b [US3] **Apply Counterfactual Intervention**: Extend the hybrid engine (or a thin wrapper) to force `skip_flag = True` for all frames listed in `counterfactual_indices.parquet` (schema: `frame_id` int64) by performing a left join on `frame_id` and overwriting the `skip_flag` column. Write final `data/processed/hybrid_output.parquet` with schema `frame_id`, `latency`, `fid_score`, `skip_flag`. **Verification**: File exists; rows matching counterfactual indices have `skip_flag == True`. (FR‑008, FR‑017). **Dependency**: T060, T050a.
- [X] T050c [US3] **Metrics Computation**: Implement `code/evaluation/metrics.py` that computes per-segment latency and FID (using `torchmetrics.FID` with `feature_extractor='resnet50'` and `num_features=2048` on generated **segments/windows**, NOT per-frame) and stores results in `hybrid_output.parquet`. Handles two data source modes (`wan-streamer` vs `voxceleb2`) as described in the plan. **Verification**: Output file contains numeric latency and FID columns. (FR‑004, FR‑010, FR‑011). **Dependency**: T050b.
- [X] T045 [US3] **Implement analyze_latency_bias Module**: Implement `code/metrics/latency_bias.py` that performs stratified bootstrap with propensity‑score matching. **First, verify that covariates `timestamp` and `audio_energy` are independent of the estimator's prediction** (assert correlation < 0.1; if `audio_energy` column is missing, fail loudly). Fit `LogisticRegression` on covariates `timestamp` and `audio_energy` to predict treatment (skip), compute propensity scores, and match treated/untreated frames. **Output** `data/metrics/latency_bootstrap_results.csv` with bias estimate, confidence interval, and intermediate p-value. **Verification**: CSV exists and contains numeric columns. (FR‑005, FR‑007, SC‑004). **Dependency**: T050c, T014d (for `audio_energy`).
- [X] T045c [US3] **Aggregate Latency Significance**: Implement `code/metrics/aggregate_latency_significance.py` that reads `data/metrics/latency_bootstrap_results.csv` (from T045), extracts the final p-value, asserts it is < 0.05, and writes `data/metrics/latency_significance_final.json` with the conclusion. **Verification**: JSON exists and contains `passed: true` if p-value < 0.05. (FR‑005, SC‑004). **Dependency**: T045.
- [X] T049 [US3] **Two One‑Sided Tests (TOST) for FID Degradation**: Implement `code/metrics/tost_fid.py` that computes the relative FID degradation `(FID_hybrid - FID_baseline) / FID_baseline` for each **segment** (using segment-level FID scores from T050c), then runs a paired TOST with equivalence margin Δ = 0.05 using `statsmodels.stats.weightstats.ttost_paired`. Assert p‑value < 0.05. Write results to `data/metrics/tost_results.csv`. **Verification**: CSV exists and contains `p_value` < 0.05. (SC‑002, FR‑005). **Dependency**: T050c.
- [X] T049b [US3] **Implement TOST Equivalence Margin Validation**: Implement `code/metrics/validate_tost_margin.py` to verify that the equivalence margin (Δ=0.05) is correctly applied in the TOST test and that the resulting p-values are interpreted correctly for both one-sided tests. **Verification**: Test passes if margin is correctly applied. (US‑3 AS‑3, FR‑005). **Dependency**: T049.
- [X] T049c [US3] **Implement FID Degradation Threshold Validation**: Implement `code/metrics/validate_fid_threshold.py` to verify that the FID degradation is within the predefined threshold. as defined in SC-002 and FR-004. **Verification**: Test passes if threshold is met. (US‑3 AS‑2, SC‑002). **Dependency**: T049.
- [X] T046 [US3] **Human Data Check**: Implement `code/data/check_human_ratings.py` that looks for `data/raw/human_ratings.json`. Write `data/metrics/human_data_status.json` with `status` (`present`/`missing`) and, if missing, log `Assumption Validated (No Human Data Available)` to `data/logs/mos_assumption_validated.log` and update `state.yaml` with `mos_validation: 'assumption_validated'`. **Verification**: Status file exists and log/message is correct. (FR‑012, FR‑013, SC‑007).
- [X] T044 [US3] **Validate Proxy MOS**: Implement `code/metrics/proxy_mos_validation.py` that, if human data is present, computes Pearson correlation using `scipy.stats.pearsonr` between proxy MOS predictions and human MOS scores, asserts `r >= 0.8`, writes `data/metrics/mos_validation_status.json` (`passed`/`failed`), and updates `state.yaml` accordingly. If human data is missing, write `status: skipped` with reason and **log exactly** `Assumption Validated (No Human Data Available)`. **Verification**: JSON file and state reflect correct status; log message present when skipped. (FR‑012, FR‑013, SC‑007). **Dependency**: T046.
- [X] T044b [US3] **Implement Proxy MOS Correlation Fallback**: Implement `code/metrics/fallback_mos_validation.py` to handle the scenario where human data is missing by logging the exact message "Assumption Validated (No Human Data Available)" and skipping the correlation test, as per FR-012 and US-3 AS-4. **Verification**: Log message present. (FR‑012, US‑3 AS‑4). **Dependency**: T046.
- [X] T043 [US3] **FID Stability Correlation**: Implement `code/metrics/fid_stability_corr.py` that calculates Pearson correlation between predicted `latent_delta_magnitude` and the relative change in FID between skipped and full‑solver frames. Write `data/metrics/fid_stability_corr.json` with `correlation` and `passed` (true if r ≥ 0.7). Update `state.yaml` key `validation_status` to `validated` or `reported_negative_result` accordingly, and log a message when r < 0.7. **Verification**: JSON exists; state and log reflect outcome. (FR‑010, FR‑011, SC‑003). **Dependency**: T050c.

**Checkpoint**: All user stories are now independently functional.

---

## Phase N: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T033 [P] **Create Documentation**: Create `docs/quickstart.md` and `docs/research.md` with initial content. `quickstart.md` must include sections: Prerequisites, Installation, Data Preparation, Running the Pipeline, and Reproducibility (must include command `python tests/integration/test_quickstart_repro.py` and expected output file `data/logs/quickstart_validation_report.json`). **Verification**: Files exist.
- [X] T034 [P] **Refactor Trainer**: Refactor `code/models/trainer.py` to use generator expressions and streaming data loaders specifically in the `data_loader` loop to reduce peak RAM usage. **Verification**: Peak RAM < 7 GB on a sample run.
- [X] T035 [P] **Profile Hybrid Simulation**: Profile `code/inference/hybrid_engine.py` (or the orchestrator) using `cProfile` and log `max_memory` and `total_time` to `data/logs/profile_report.txt`; assert latency reduction ≥ 20% and memory ≤ 7 GB. **Verification**: Log contains required metrics.
- [X] T036 [P] **Add Unit Tests for Filtering**: Add unit tests for edge cases in `code/data/preprocess.py` (empty input, threshold extremes). **Verification**: All new tests pass.
- [X] T037 [P] **Run quickstart.md validation**: Run `tests/integration/test_quickstart_repro.py` to ensure end‑to‑end reproducibility. **Verification**: Assert `data/logs/quickstart_validation_report.json` exists and contains `status: PASS`.
- [X] T038a [P] **Implement Contract Documentation Links (quickstart.md)**: Update `docs/quickstart.md` to include explicit references to all schema files under `contracts/` (e.g., `dataset.schema.yaml`, `estimator_predictions.schema.yaml`, `evaluation_metrics.schema.yaml`). **Verification**: Files contain the required links.
- [X] T038c [P] **Implement Contract Documentation Links (data-model.md)**: Update `docs/data-model.md` to include explicit references to all schema files under `contracts/` (e.g., `dataset.schema.yaml`, `estimator_predictions.schema.yaml`, `evaluation_metrics.schema.yaml`). **Verification**: Files contain the required links. (FR‑021).
- [X] T038b [P] **Verify Contract Documentation Links**: Run `tests/unit/test_doc_links.py` to verify that the links added in T038a and T038c are correct and functional. The script must write `data/logs/link_verification_report.txt` containing a list of verified links or a `PASS` status. **Verification**: Assert `data/logs/link_verification_report.txt` exists and contains `PASS`.
- [X] T039 [P] **Implement Streaming Data Loader**: Implement `code/data/streaming_loader.py` to handle datasets exceeding RAM limits by processing `data/raw` shards in chunks of a fixed size using `datasets.load_dataset(..., streaming=True)` and updating running mean/variance for statistics accumulation using Welford's online algorithm. **Verification**: Script runs on a large subset without memory error and accumulates statistics correctly. (Constitution Principle I, Assumption about dataset availability).
- [X] T040 [US1] **Implement Strict Data Fetch Failure**: Refactor `code/data/extract_latents.py` to remove any `try/except` blocks that fall back to synthetic/mock data generation. Ensure that if the real data fetch fails (network error, missing file), the script raises a `DataFetchError` and exits with a non-zero code. **Retain** the fallback to the canonical VoxCeleb2 dataset as defined in FR-019. **Verification**: Unit test confirms that a simulated network failure raises an exception rather than generating mock data. (Constitution Principle I, Data Hygiene).
- [X] T066 [US1] **Implement Streaming Data Sample Documentation**: Implement `code/data/streaming_sample_doc.py` to document the exact streaming/sampling rule used (which split, chunking, how many rows) in `data/metrics/sampling_methodology.md`. **Verification**: File exists and contains methodology. (Rules). **Dependency**: T014b.

---

## Dependencies & Execution Order

### Phase Dependencies
- **Setup (Phase 1)** → **Foundational (Phase 2)** → **User Stories (Phase 3‑5)** → **Polish (Phase N)**

### Within User Story 1
`T012a → T013 → T012b → T014d → T014e → T014f → T015b → T016 → T014g → T014b → T014h → T015 → T017`

### Within User Story 2
`T019a1 → T019a2 → T019b → T024c → T024a → T024d → T024b → T051`

### Within User Story 3
`T047 → T060 → T045a → T045b → T050a → T050b → T050c → (T045, T045c, T049, T043, T046, T044, T044b, T049b, T049c)`
Human‑data path: `T046 → T044`.
**Dependencies**: T047 depends on T017. T060 depends on T047. T045a depends on T047. T045 depends on T050c and T014d. T045c depends on T045. T049 depends on T050c.

All dependencies are now explicitly sequential where required; parallel‑safe tasks are marked `[P]` only when they truly have no data dependencies.