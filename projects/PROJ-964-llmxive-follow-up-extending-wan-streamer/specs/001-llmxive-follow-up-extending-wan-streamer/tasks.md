---
description: "Task list template for feature implementation"
---

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
- [X] T009 [P] **Implement Data Source Check**: Implement `code/data/validate_logs.py` to check for Wan-Streamer v0.1 logs first; if missing, fetch the canonical VoxCeleb2 dataset. **Logic**: 1. Check `os.path.exists('data/raw/wan-streamer-logs')`. If True, register checksum and set `data_source='wan-streamer'`. 2. If False, check `os.path.exists('data/raw/voxceleb2')`. If True, register checksum and set `data_source='voxceleb2'`. 3. If both missing, fetch `voxceleb2` via `datasets.load_dataset`. **Crucially**: Before fetching, load `code/config.py` to get the pinned `DATASET_REVISION`. After fetching, verify the loaded dataset's `default` or `split` revision matches the pinned revision. If mismatch, raise an error. **Then**, call `update_state()` from T008 with the path and MD5 hash of the downloaded dataset to write the checksum to `state.yaml` before returning. Register the checksum and set `state.dataset.source` to either "wan-streamer" or "voxceleb2". **Verification**: Run script that simulates missing logs, fetches VoxCeleb2, asserts the revision matches `config.py`, and asserts `state.yaml` contains the correct hash and source.
- [X] T010 **Implement Validators**: Implement `code/utils/validators.py` function `validate_schema(df, schema_path)` that loads schema from `contracts/dataset.schema.yaml` and validates `df` using `pandera`. **Dependency**: T009 must complete successfully before T010 runs.
- [X] T053 [P] **Implement Sample Size Reduction Module**: Implement `code/tasks/reduce_sample_size.py` that calculates a *deferred* reduction amount based on the current sample size, the minimum required size from power analysis (`MIN_SAMPLE_SIZE` defined in `code/config.py`), and the memory budget (≤ 7 GB). If reduction would bring size below `MIN_SAMPLE_SIZE`, raise a `PowerLimitationError`. Expose `reduce_sample_size(current_size) -> new_size`. **Verification**: Run script that reduces sample size and asserts correct behavior. (FR-014, FR-023). **Dependency**: None (standalone utility).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Extraction and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Extract time-series latent vectors and turn‑taking labels from real Wan‑Streamer v0.1 logs (or VoxCeleb2 fallback) to create a CPU‑tractable dataset.

### Tests (optional)

- [X] T011 [P] [US1] Contract test for dataset schema in `tests/contract/test_dataset_schema.py`
- [X] T012 [P] [US1] Integration test for data extraction pipeline in `tests/integration/test_data_extraction.py` (US‑1, FR‑001)

### Implementation

- [X] T012a [P] [US1] **Define Threshold Algorithm**: Create `code/config/detection_thresholds.yaml` to define the algorithm and default parameters for classifying 'interruption' and 'pause' events (e.g., audio energy > X dB overlapping with agent speech) to ensure the minimum event count is verifiable (see FR-018). **Verification**: Assert file exists, is valid YAML, and contains the required keys: `audio_energy_threshold`, `pause_threshold`, `interruption_overlap_duration`. (FR-018).
- [X] T013 [P] [US1] **Extract Latents**: Implement `code/data/extract_latents.py` to parse Wan‑Streamer v0.1 logs (or fetched VoxCeleb2) using thresholds from `code/config/detection_thresholds.yaml` and output `data/processed/raw_extract.parquet`. **Verification**: Assert file exists and schema validation passes.
- [X] T012b [P] [US1] **Validate Thresholds & Event Count**: Load `data/processed/raw_extract.parquet` (produced by T013), apply thresholds from `code/config/detection_thresholds.yaml`, compute the total event count, interruption event count, and pause event count. Write `data/logs/threshold_validation.log` containing the lines `Total Events: <number>`, `Interruption Events: <number>`, `Pause Events: <number>`. **If interruption count < 500 OR pause count < 500, abort execution with a non-zero exit code.** Log an error message if insufficient events are found. (FR‑018, US‑1).
- [X] T014d [P] [US1] **Data Filtering**: Implement `code/data/preprocess.py` function `filter_events(df)` that retains only rows where `semantic_feature` is not null and not an empty string. Ensure `audio_energy` is extracted and added to the dataframe here if not present. Output intermediate `data/processed/filtered.parquet`. **Verification**: File exists and row count matches filter criteria.
- [X] T014e [P] [US1] **Event Labeling**: Extend `code/data/preprocess.py` with `assign_priority(df)` that adds a boolean column `high_priority` set to `True` if `latent_delta_magnitude > 0.5` OR `uncertainty > 0.8` (using thresholds from `code/config/detection_thresholds.yaml` if defined, otherwise defaults). Log counts of high vs. low priority events to `data/logs/priority_counts.log`.
- [X] T014f [P] [US1] **Log Event Count**: Implement a lightweight script `code/data/log_event_counts.py` that reads `data/processed/filtered.parquet` and writes the total number of events to `data/logs/event_counts.log` as a single line containing only the integer count, followed *exactly* by a newline character. **Verification**: Log file exists and contains an integer line ending with a newline.
- [X] T015b [US1] **Generate Theoretical Defaults**: Implement `code/data/generate_defaults.py` to create `data/metrics/theoretical_defaults.json` with hardcoded defaults (`variance:`, `effect_size: a small magnitude`) if the file does not exist. **Verification**: File exists and contains valid JSON.
- [X] T016 [US1] **Critical Statistical Prep (Initial Power Analysis)**: Implement `code/data/power_analysis_initial.py` that reads `data/processed/filtered.parquet`. If the file exists, compute empirical variance of `latent_delta_magnitude`; otherwise load defaults from `data/metrics/theoretical_defaults.json`. Output `data/metrics/power_analysis_initial.json` with fields `recommended_sample_size`, `expected_variance`, `effect_size`, `variance_source`. **Verification**: JSON exists and contains all required keys.
- [X] T014g [US1] **Determine Sample Size**: Implement `code/data/decide_sample_size.py` that reads `power_analysis_initial.json`; if `recommended_sample_size` is present, use it, else fall back to `config.DEFAULT_SAMPLE_SIZE`. Write the chosen size to `data/metrics/selected_sample_size.txt`. **Verification**: File exists and contains an integer.
- [X] T014b [US1] **Stratified Sampling**: Implement `code/data/preprocess.py` function `stratified_sample(df, size)` that performs stratified sampling based on `turn_label` using `sklearn.model_selection.StratifiedShuffleSplit` with `random_state=42` and `size` from `selected_sample_size.txt`. **Verification**: File exists and row count equals the selected size (or the dataset size if smaller). Implement a KL divergence check to verify that the distribution of 'turn_label' is preserved after sampling, logging the result for verification.
- [X] T014h [US1] **Data Validation**: Implement `code/data/validate_processed.py` to verify that all required columns (`timestamp`, `semantic_feature`, `prosodic_feature`, `latent_delta_magnitude`, `turn_label`, `audio_energy`) are non‑null and correctly typed in `sampled_dataset.parquet`.
- [X] T015 [US1] **Validate Sampling Distribution**: Implement `code/data/validate_sampling_distribution.py` to compare the distribution of `turn_label` in the original filtered data vs. the sampled data, logs KL divergence to `data/logs/sampling_distribution.log` using `scipy.stats.entropy`.
- [X] T017 [US1] **Final Power Analysis**: Re‑run `power_analysis_initial.py` using `sampled_dataset.parquet` as input and output the results to `data/metrics/power_analysis_final.json`, containing  `recommended_sample_size`, `expected_variance`, `effect_size`.

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
- [X] T019b [US2] **Execute Training Loop with Retry**: Run `python code/models/trainer.py` using data from `data/processed/sampled_dataset.parquet`. If training exceeds the 6-hour wall‑clock limit or memory budget, invoke `code/tasks/reduce_sample_size.py` and retry.
- [X] T024c [US2] **Implement Baseline Comparison Logic**: Implement `code/metrics/baseline_comparison.py` that loads the trained estimator's predictions and compares them against a naive baseline (predicting zero delta).
- [X] T024a [US2] **Compute Uncertainty Correlation**: Implement `code/metrics/uncertainty_calibration.py` that computes Pearson correlation between uncertainty score and prediction error.
- [X] T024d [US2] **Implement Memory Profile Verification**: Implement `code/tests/unit/test_memory_profile.py` to verify memory usage during the training loop.
- [X] T024b [US2] **Finalize Checkpoint**: Read correlation value and rename checkpoint if calibration passes.
- [X] T051 [US2] **Verify Final Checkpoint**: Assert that `data/models/estimator_checkpoint_final.pt` exists.

**Checkpoint**: User Stories 1 & 2 are now independently functional.

---

## Phase 5: User Story 3 - Hybrid Inference Simulation and Quality‑Latency Trade-off (Priority: P3)

**Goal**: Simulate hybrid inference, compute FID/proxy MOS, and validate latency reduction via statistical tests.

### Tests (optional)

- [X] T028 [P] [US3] Contract test for hybrid output schema in `tests/contract/test_hybrid_output_schema.py`
- [X] T029 [P] [US3] Integration test for end‑to‑end simulation and metrics in `tests/integration/test_hybrid_simulation.py`

### Implementation

- [X] T060 [US3] **Implement Causal FID Ground Truth**: Implement `code/metrics/generate_counterfactual_fid.py`. **Logic**: For each segment in the test set, run the full flow-matching solver to generate ground truth. **Command**: Execute `python code/inference/full_solver.py --input <segment_path> --output <output_path>` for every segment in the input list. **Verification**: Assert that for every input segment, a corresponding output file exists and contains valid video data. (FR-008, US-3).
- [X] T047 [US3] **Critical Data Generation (Counterfactual Indices)**: Select frame indices for the randomized counterfactual intervention, ensuring a minimum proportion of total frames and logging values.
- [X] T045a [US3] **Precedence Rule Logic**: Implement `code/inference/precedence_rule.py` with function `resolve_skip_decision`.
- [X] T045b [US3] **Fallback Handler**: Implement `code/inference/fallback_handler.py`.
- [X] T050a [US3] **Hybrid Engine Core**: Implement `code/inference/hybrid_engine.py` that applies the estimator and decides per‑frame whether to skip or run full solver.
- [X] T050b [US3] **Apply Counterfactual Intervention**: Force the skip flag for frames in the randomized subset.
- [X] T050c [US3] **Metrics Computation**: Compute per-segment latency and FID.
- [X] T045 [US3] **Implement analyze_latency_bias Module**: Perform stratified bootstrap with propensity-score matching.
- [X] T049 [US3] **Two One‑Sided Tests (TOST) for FID Degradation**: Run a paired TOST test to assess the equivalence of FID scores between hybrid and baseline outputs.
- [X] T046 [US3] **Human Data Check**: Check for human ratings data, logging status accordingly.
- [X] T044 [US3] **Validate Proxy MOS**: Compute Pearson correlation between proxy MOS predictions and human MOS scores (if available).
- [X] T043 [US3] **FID Stability Correlation**: Calculate the correlation between predicted delta magnitude and FID stability. **Verification**: Assert that `state.yaml` is updated with key `state.validation_status` set to 'passed' or 'failed' based on the correlation threshold, and that the correlation value is logged. (FR-010, SC-003).

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
- [X] T040 [P] **Implement Strict Data Fetch Failure**: Remove fallback data generation in extraction scripts.
- [X] T066 [US1] **Implement Streaming Sample Documentation**: Document the streaming/sampling rule used.

---

## Dependencies & Execution Order

### Phase Dependencies
- **Setup (Phase 1)** → **Foundational (Phase 2)** → **User Stories (Phase 3‑5)** → **Polish (Phase N)**

### Within User Story 1
`T012a → T013 → T012b → T014d → T014e → T014f → T015b → T016 → T014g → T014b → T014h → T015 → T017`

### Within User Story 2
`T019a1 → T019a2 → T019b → T024c → T024a → T024d → T024b → T051`

### Within User Story 3
`T047 → T060 → T045a → T045b → T050a → T050b → T050c → (T045, T045c, T049, T043, T046, T044)`

**Structure Decision**: Single `code/` directory with modular sub-packages to isolate responsibilities and facilitate independent testing of the estimator vs. the evaluation metrics.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Randomized Counterfactual (FR-008) | Required to distinguish "easy to skip" from "easy to generate" and establish causal effect (US-3, Edge Cases). | Observational propensity matching alone (FR-005) is insufficient for causal claims; it only adjusts for confounders, does not prove intervention efficacy. |
| Fallback Logic (FR-006) | Ensures quality safety when uncertainty is high; prevents degradation on non-smooth trajectories. | Blind skipping based on prediction alone risks >5% FID degradation on ambiguous frames. |
| Hybrid Simulation (FR-003) | Necessary to measure the *actual* trade-off of the proposed skipping strategy. | Running only the estimator does not measure the system-level latency/quality impact. |
| Segment-Level FID | FID is a batch metric; per-frame FID is mathematically invalid. | Using per-frame FID would yield degenerate results. We compute FID over segments (windows) to maintain validity while approximating frame-level granularity. |

## Constitution Check

| Principle | Status | Compliance Strategy |
|-----------|--------|---------------------|
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

# Project ID: PROJ-964-llmxive-follow-up-extending-wan-streamer | Field: computer science | Ratified: 2026-07-11