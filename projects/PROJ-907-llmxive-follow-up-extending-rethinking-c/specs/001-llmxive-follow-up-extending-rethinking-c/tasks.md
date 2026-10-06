# Tasks: llmXive follow-up: extending "Rethinking Cross-Layer Information Routing in Diffusion Transformers"

**Input**: Design documents from `/specs/001-llmxive-static-routing/`
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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan by executing: `mkdir -p projects/PROJ-907-llmxive-follow-up-extending-rethinking-c/code/{src,tests,data/imagenet_trace,data/imagenet_benchmark,data/routing_cache,data/results,docs}`. **Note**: This creates all necessary directories including `src/` as defined in the plan.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin. This phase includes Data Integrity tasks (T035) to ensure safe data handling and verified loaders before any processing begins.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T002 Initialize Python project by creating `projects/PROJ-907-llmxive-follow-up-extending-rethinking-c/code/requirements.txt` containing pinned versions: `torch==2.3.0+cpu ` (install via `--index-url https://download.pytorch.org/whl/cpu`), `torchvision==0.18.0 `, `transformers`, `diffusers`, `scikit-learn`, `numpy`, `pandas`, `matplotlib`. **Note**: `bitsandbytes` removed as 8-bit quantization is not used; `torchmetrics` removed as FID is implemented manually via `torchvision`.
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools
- [X] T005 [P] Implement `projects/PROJ-907-llmxive-follow-up-extending-rethinking-c/code/src/model_loader.py`: Load canonical pre-trained SiT-XL model with DAR enabled. [UNRESOLVED-CLAIM: c_55a9979e — status=not_enough_info] **CRITICAL**: MUST use a low-precision format to ensure the model fits within the memory limit of the GitHub Actions runner., as per Spec Assumptions and SC-005. **Note**: `load_in_8bit` is explicitly NOT used per Spec Assumptions. **Verification**: Task is complete only when `src/model_loader.py` exists, can be imported without error, and successfully loads the model in float16 mode without OOM on a standard CPU runner.
- [X] T006 [P] Implement `projects/PROJ-907-llmxive-follow-up-extending-rethinking-c/code/src/metrics.py`: Implement FID calculation using a frozen, pre-trained Inception network **from `torchvision.models.inception_v3`** using **`Inception_V3_Weights.${FID_WEIGHTS_VERSION}`** (ensuring compatibility with pinned `torchvision==${TORCHVISION_VERSION}` and matching the canonical baseline). **Specific Function**: `calculate_fid(image_list_1, image_list_2)`. **Constraint**: MUST load the network in `inference-only` mode (`model.eval()`) and explicitly wrap all inference calls in `torch.no_grad()` to freeze weights and prevent gradient computation. **Preprocessing**: Inputs MUST be resized to 299x299 and center-cropped to match the canonical baseline. **Verification**: Verify `src/metrics.py` contains `calculate_fid` function that accepts two image lists, uses `model.eval()` and `torch.no_grad()`, applies correct resizing/cropping, loads `IMAGENET1K_V1` weights (or configured version), and returns a float.
- [X] T007 [P] Implement `projects/PROJ-907-llmxive-follow-up-extending-rethinking-c/code/src/utils.py`: Helper functions for batch processing, memory management, and error handling. **Specific Functions**:
 1. `batch_iterator(iterable, batch_size)`: Yields chunks of size `batch_size` from `iterable`.
 2. `memory_guard(threshold_gb)`: Returns `True` if current RAM usage < `threshold_gb`, else raises a `MemoryError` exception.
 **Verification**: Verify functions exist, have correct signatures, and `memory_guard` raises an exception when the threshold is exceeded.
- [X] T008 Configure environment variables by creating `.env` file at project root with exact keys and **default values**: `TRACE_SET_SIZE=100 ` (default), `BENCHMARK_SET_SIZE=100 ` (default, see T019 for specific count), `BENCHMARK_SET_START=100 ` (fixed integer), `RANDOM_SEED=42` (default), `NUM_TIMESTEPS=1000` (default), `FID_WEIGHTS_VERSION=IMAGENET1K_V1` (default), `TORCHVISION_VERSION=0.18.0` (default), `BENCHMARK_SEEDS=[, 456, 789, 1011, 2024]` (default), `SENSITIVITY_THRESHOLDS=[low, 0.05, 0.1]` (default), `SENSITIVITY_SET_SIZE=100` (default). **Note**: `BENCHMARK_SET_START=100` ensures disjointness from T011 (indices -99) as per T019 requirement. **Verification**: Verify `.env` exists, contains these keys with the specified default values, and the code validates that these values can be overridden via environment variables.
- [X] T035 [P] Implement `projects/PROJ-907-llmxive-follow-up-extending-rethinking-c/code/src/data_loader.py` to fetch ImageNet subsets using `datasets.load_dataset("imagenet1k", split="validation", streaming=True)`. **CRITICAL**: Remove any `try/except` blocks that fall back to synthetic/mock data; the loader MUST raise an exception if the real source is unreachable. **Verification**: Verify that a failed fetch raises an exception and no synthetic data is generated.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Trace Dynamic Routing and Identify Canonical Map (Priority: P1) 🎯 MVP

**Goal**: Execute pre-trained SiT-XL with DAR on a subset of validation images, record routing weight matrices at every timestep, and derive a canonical static routing map (or global average fallback).

**Independent Test**: Run tracing on a representative set of images; verify output contains complete routing tensors for every block/timestep; verify clustering logic outputs valid k and silhouette score; verify fallback logic triggers correctly on null results.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T009 [P] [US1] Write unit test file `projects/PROJ-907-llmxive-follow-up-extending-rethinking-c/code/tests/unit/test_clustering.py` with assertions for the expected fallback behavior (global average generation when k < 2 or silhouette < 0.25). **Verification**: Test must assert that the *expected system output* flags the null result condition.

### Implementation for User Story 1

- [ ] T011 [US1] Implement `projects/PROJ-907-llmxive-follow-up-extending-rethinking-c/code/src/tracing.py`: Load SiT-XL/2 with `torch.float16` (per Spec Assumptions and SC-005), iterate through `$TRACE_SET_SIZE` ImageNet validation images (streamed/batched to stay < 7GB RAM) with a **fixed timestep schedule (linear spacing from 0 to $NUM_TIMESTEPS, seed from `$RANDOM_SEED`)**, record routing weight matrices (softmax distributions) for every block and timestep. **File Naming**: Save a **single aggregated** `.npy` file containing ALL A set of images' routing tensors as `data/routing_cache/routing_aggregated.npy`. **Schema**: The `.npy` file MUST contain a 5D numpy array of shape `[num_images=$TRACE_SET_SIZE, num_timesteps=$NUM_TIMESTEPS, num_blocks, history_dim]` representing the routing weights for all images, timesteps, and blocks. **Sampling Strategy**: Use the first `$TRACE_SET_SIZE` images in the validation split to ensure reproducibility. `image_id` is defined as the 0-indexed position in the validation split (0 to `$TRACE_SET_SIZE-1`). **Memory Constraint**: Process strictly in **batches of small size** to guarantee < 7GB RAM usage. **Memory Guard Logic**: Invoke `memory_guard(7.0)` **per batch** before processing each batch. If RAM usage is < 7GB but > 6.5GB, log a warning to `data/results/memory_profile_raw.jsonl` and continue. If RAM usage >= 7GB, raise `MemoryError` and halt immediately. **Logging**: Log progress as JSON lines to `data/results/tracing_log.jsonl` with keys: `image_index`, `peak_memory_mb`, `routing_shape`. Log memory profiles to `data/results/memory_profile_raw.jsonl`.
 **Data Hygiene**:
 1. Query the HuggingFace `datasets` library for the exact `dataset_version` and `revision` of the loaded `imagenet1k` split.
 2. Save this metadata to `data/results/dataset_metadata.json` with keys: `dataset_name`, `split`, `revision`, `timestamp`, and `checksum` (cryptographic hash of the first shard).
 3. **CRITICAL**: Metadata MUST be saved **before** any routing files are generated.
 4. **Checksum Generation**: Generate a SHA checksum for the `routing_aggregated.npy` file immediately upon creation.
 5. **State Recording**: Record the checksum and derivation path in `state/projects/PROJ-907-llmxive-follow-up-extending-rethinking-c.yaml` under `artifact_hashes` before the file is considered complete.
 **Memory Profile Artifact**: At the end of execution, the script MUST parse `memory_profile_raw.jsonl` to compute peak memory usage and **generate** `data/results/memory_profile.json`. This artifact MUST contain a boolean field `within_limit` (true if peak < 7GB) and a string field `status` ("PASS" or "FAIL"). If a `MemoryError` was logged, `status` MUST be "FAIL".
 **Verification**:
 1. Verify `data/routing_cache/` contains a single valid `.npy` file named `routing_aggregated.npy`.
 2. Verify the `.npy` file loads as a 5D array with shape `[$TRACE_SET_SIZE, $NUM_TIMESTEPS, num_blocks, history_dim]` and dtype `float16` or `float32`.
 3. Verify `data/results/dataset_metadata.json` exists and was created **before** `routing_aggregated.npy` (check timestamps).
 4. Verify `data/results/memory_profile.json` exists and contains `within_limit` (boolean) and `status` (string "PASS"/"FAIL") fields with values consistent with the 7GB limit check.
 5. Verify `data/results/tracing_log.jsonl` exists and contains valid log entries for every image processed.
 6. Verify `state/projects/PROJ-907-llmxive-follow-up-extending-rethinking-c.yaml` contains the checksum for `routing_aggregated.npy`.

- [ ] T012 [US1] [FR-002] Dependency: T005, T011. Implement `projects/PROJ-907-llmxive-follow-up-extending-rethinking-c/code/src/clustering.py`: Load recorded routing tensors from `routing_aggregated.npy`. **Loading Logic**: Load the single aggregated file. **Clustering**: **For each block `b`** in `num_blocks` (derived dynamically from the model config loaded in T005), extract the routing vectors for all timesteps (shape `[num_timesteps, history_dim]`) from the aggregated tensor and apply k-means clustering **independently to these per-block vectors** to identify distinct phases. Compute the silhouette score for each block's clustering. **Null Hypothesis Handling**: If for any block the clustering identifies < 2 clusters or a silhouette score < 0.25, that block MUST default to a global average vector for that block (computed from the original `[num_timesteps, history_dim]` data). **Function**: Expose a pure function `compute_canonical_map(routing_tensor, distance_threshold=$DEFAULT_DISTANCE_THRESHOLD)` that performs the clustering and returns the map without file I/O. **Output**: Save cluster centers and silhouette scores to `data/routing_cache/cluster_centers.json` with a structure that preserves the block dimension (e.g., `{"block_0": {"centers": [...], "silhouette": 0.5, "null_hypothesis_triggered": false, "null_reason": null},...}`). **Verification**:
 1. Verify `cluster_centers.json` loads and has keys matching `num_blocks`.
 2. Verify for any block where `null_hypothesis_triggered` is `true`, the `centers` field contains the exact global average vector (recompute mean and assert equality).
 3. Verify the `compute_canonical_map` function exists and can be called in memory without re-loading files.
 4. **Deterministic Check**: Run `python -c "import json, sys; d=json.load(open('data/routing_cache/cluster_centers.json')); assert len(d)==NUM_BLOCKS, f'Expected {NUM_BLOCKS} blocks, got {len(d)}'"` where `NUM_BLOCKS` is derived from the model config loaded in T005.

- [ ] T013 [US1] Dependency: T012. Implement `projects/PROJ-907-llmxive-follow-up-extending-rethinking-c/code/src/canonical_map.py`: Derive the "Canonical Routing Map" (static weight vector per block) from the dominant cluster or global average for each block. **Output Schema**: Save to `data/routing_cache/canonical_map.json` as a JSON object with keys: `{"block_0": [float, float,...], "block_1": [float, float,...],...}` where each value is the static weight vector for that block. **Verification**: Verify `data/routing_cache/canonical_map.json` exists, contains the correct schema, and that the number of keys matches the number of blocks in the model.

- [ ] T039 [US1] Dependency: T011. Implement a script to parse memory logs and **generate** `docs/memory_report.md` containing a summary of peak memory usage statistics and OOM prevention efficacy, referencing the data in `data/results/memory_profile.json` (produced by T011). **Logic**: Read `data/results/memory_profile.json` and generate a human-readable report. **Verification**:
 1. Verify `docs/memory_report.md` exists and contains valid data.
 2. Verify the report correctly reflects the `status` field from `data/results/memory_profile.json`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Benchmark Static Approximation vs. Dynamic Baseline (Priority: P2)

**Goal**: Replace dynamic DAR module with static routing weights, benchmark inference latency and FID against the dynamic baseline on a disjoint image set.

**Independent Test**: Run static and dynamic models on a representative set of images.; verify latency reduction calculation; verify FID difference calculation; ensure results are logged to structured CSV/JSON.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T016 [P] [US2] Unit test for latency measurement logic in `projects/PROJ-907-llmxive-follow-up-extending-rethinking-c/code/tests/unit/test_benchmark.py` (verify timing accuracy)
- [X] T017 [P] [US2] Integration test for FID comparison in `projects/PROJ-907-llmxive-follow-up-extending-rethinking-c/code/tests/integration/test_fid_comparison.py` (verify FID calculation on dummy samples)

### Implementation for User Story 2

- [ ] T018 [US2] Dependency: T013. Implement `projects/PROJ-907-llmxive-follow-up-extending-rethinking-c/code/src/static_model.py`: Create a modified model class that injects the static routing map (from T013) and removes per-timestep softmax overhead. **Dependency**: Must load `data/routing_cache/canonical_map.json` (Artifact from T013). **Input Schema**: The input JSON MUST match the schema defined in T013: `{"block_0": [float...],...}`. **Verification**: Verify the model can be instantiated and runs without computing routing weights dynamically. Verify that `data/routing_cache/canonical_map.json` exists and contains valid per-block vectors before instantiation.
- [ ] T019 [US2] Dependency: T018. Implement `projects/PROJ-907-llmxive-follow-up-extending-rethinking-c/code/src/benchmark.py`: Run inference for both dynamic (original) and static models on a set of **$BENCHMARK_SET_SIZE** disjoint ImageNet validation images, starting from index **$BENCHMARK_SET_START** (to ensure disjointness from T011 which uses indices 0-99). **Logic**: Measure time-to-solution for a representative sequence of steps; generate samples. **Validation**: **Implement validation logic** to ensure the benchmark set (indices $BENCHMARK_SET_START to $BENCHMARK_SET_START+$BENCHMARK_SET_SIZE-1) is disjoint from the trace set (indices 0-99); raise an error if sets overlap. **Data Hygiene**: **CRITICAL**: Read dataset metadata from `data/results/dataset_metadata.json` (produced by T011) to satisfy data hygiene requirements; DO NOT re-fetch or re-log dataset version/checksums to avoid redundancy. **Error Handling**: Must report high FID degradation (> 0.5) as a valid negative result **by appending the result to `data/results/benchmark_results.csv` and `.json`** without halting. **Hypothesis Check**: The script MUST explicitly calculate `latency_reduction_percent` and `fid_difference` and set `hypothesis_status` to "PASS" if `latency_reduction_percent >= 40` AND `fid_difference < 0.1`, otherwise "FAIL". **Output Schema**: `data/results/benchmark_results.csv` and `data/results/benchmark_results.json` must contain columns/keys: `timestamp`, `model_type` (dynamic/static), `seed`, `latency_s`, `fid_score`, `fid_degradation`, `hypothesis_status` (PASS/FAIL based on SC-001/SC-002). **Image Saving**: **CRITICAL**: Save the generated raw image tensors for the benchmark set to `data/results/benchmark_images/` in `.npy` format to support downstream tasks (T025, T027) that require re-generating or re-using these specific images. **Note**: The benchmark set size is fixed at **$BENCHMARK_SET_SIZE** images for this initial baseline comparison (US2). For the statistical significance phase (T025), a larger set of $BENCHMARK_SEEDS images will be used. **Verification**:
 1. Verify `data/results/benchmark_results.csv` and `data/results/benchmark_results.json` are generated with the specified schema.
 2. Verify that running the script with overlapping configuration (e.g., `BENCHMARK_SET_START=50`) triggers a `ValueError` with a clear message.
 3. Verify no overlap errors occurred by checking logs for the absence of ValueError regarding set intersection, and confirm `benchmark_results.csv`/`.json` contain keys: timestamp, model_type, seed, latency_s, fid_score, fid_degradation, hypothesis_status.
 4. Verify `hypothesis_status` correctly reflects whether latency reduction ≥ 40% and FID difference < 0.1.
 5. Verify `data/results/benchmark_images/` contains the raw image tensors for the benchmark set.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Significance and Sensitivity Analysis (Priority: P3)

**Goal**: Perform statistical significance tests on FID scores across Multiple random seeds and sensitivity analysis on clustering thresholds.

**Independent Test**: Re-run benchmark 5 times with different seeds; verify mean/std reporting; sweep clustering thresholds; verify robustness reporting.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T023 [P] [US3] Unit test for bootstrap significance test in `projects/PROJ-907-llmxive-follow-up-extending-rethinking-c/code/tests/unit/test_stats.py` (verify non-parametric bootstrap implementation)
- [X] T024 [P] [US3] Unit test for sensitivity sweep logic in `projects/PROJ-907-llmxive-follow-up-extending-rethinking-c/code/tests/unit/test_sensitivity.py`

### Implementation for User Story 3

- [ ] T025 [US3] Dependency: T013, T018, T019. Implement `projects/PROJ-907-llmxive-follow-up-extending-rethinking-c/code/src/stats_analysis.py`: **Re-run the inference loop** (T019's generation step) **5 times** with different **pre-defined random seeds**: **$BENCHMARK_SEEDS**. **CRITICAL**: For each seed, the script MUST **re-initialize the static model (T018) using the SAME `canonical_map.json` derived in T013** (do NOT re-run clustering or data fetching). This ensures the static map is constant while the benchmark data (noise seeds) varies. **Note**: This task uses a benchmark set of **$BENCHMARK_SET_SIZE** images (indices $BENCHMARK_SET_START to $BENCHMARK_SET_START+$BENCHMARK_SET_SIZE-1) to ensure statistical power, distinct from the 100-image set in T019. Collect FID scores for **both** static and dynamic models; compute the **paired difference** (static - dynamic) for each seed; compute mean and standard deviation of these differences. **Verification**: Verify `data/results/statistical_analysis.json` exists and contains keys [mean, std, bootstrap_results].
 1. Verify `data/results/statistical_analysis.json` contains `statistical_limitations` string mentioning N=5.
 2. Verify `bootstrap_results` contains `n_resamples=1000 ` (if applicable).
 3. Confirm the file lists 5 distinct seeds and a `paired_differences` array.
 4. Verify that the benchmark set indices (disjoint from trace set) are maintained for each seed across multiple independent runs.
 5. **Dynamic Baseline**: The script MUST re-run the dynamic benchmark for each of the 5 seeds to collect FID scores for both static and dynamic models.

- [ ] T026 [US3] Implement non-parametric bootstrap in `src/stats_analysis.py` on the **paired differences** to test significance. **Parameters**: Use **n_resamples=1000 **, a **confidence interval** calculated using the **percentile method**. **Conditional Logic**: If the number of seeds (N) is less than 10, the researcher MUST document the statistical limitations of N=5 for parametric tests in the output artifact `data/results/statistical_analysis.json`. **However**, the researcher MUST still run the bootstrap test with N=5, acknowledging the low power. The task MUST support this choice. **Output**: Save p-values, bootstrap distribution (if run), and the limitation string to `data/results/statistical_analysis.json`. **Verification**: Verify `data/results/statistical_analysis.json` contains `n_resamples=1000` in the bootstrap results (if run) and the `statistical_limitations` string explicitly stating "Analysis based on N=5 seeds..." (if skipped or run with low power).

- [ ] T027 [US3] Dependency: T012, T018. Implement sensitivity analysis in `projects/PROJ-907-llmxive-follow-up-extending-rethinking-c/code/src/sensitivity.py`: **Sweep the `clustering.distance_threshold` parameter over the concrete set {$SENSITIVITY_THRESHOLDS}**. For each threshold in this set:
 1. **Call `compute_canonical_map` from `src/clustering.py` in memory** (passing the loaded routing tensor from T011) to compute a new canonical map using the specified threshold. This step **bypasses the static `canonical_map.json` artifact from T013** and re-executes the clustering logic with the new threshold. This must explicitly handle the case where the threshold triggers the fallback to a global average (null hypothesis).
 2. **Re-use the static model injection logic** from T018 (do NOT re-implement) by importing and using the class from `src/static_model.py`.
 3. **Load the existing benchmark images** generated in T019 (or T025's static artifacts) for the fixed benchmark set (indices $BENCHMARK_SET_START to $BENCHMARK_SET_START+$SENSITIVITY_SET_SIZE-1, seed 42). **Do NOT re-generate images**. **Re-use the existing images** to calculate FID for each threshold, ensuring the only variable is the canonical map. **Note**: The benchmark set size for this sensitivity sweep is **$SENSITIVITY_SET_SIZE** images to reduce computational load while maintaining statistical relevance for the sweep.
 4. Record the resulting FID score.
 **Output Schema**: Save sensitivity sweep results to `data/results/sensitivity_sweep.json` as a JSON list of objects: `[{"threshold": 0.01, "fid_score": 0.12, "range": 0.05, "robustness_conclusion": "...", "rationale": "..."},...]`. The output MUST explicitly report the **range of FID degradation** observed across the sweep and a **robustness conclusion** as required by SC-004. **Documentation**: The task MUST include a rationale for the chosen threshold set {$SENSITIVITY_THRESHOLDS} in the output artifact (e.g., "Selected to cover low, standard, and moderate sensitivity ranges based on empirical observation of routing variance").
 **Verification**:
 1. Save sensitivity sweep results to `data/results/sensitivity_sweep.json`.
 2. Verify the JSON contains a `range` field, `robustness_conclusion`, and `rationale`.
 3. **Calculate** `max(fid_scores) - min(fid_scores)` from the raw list and **assert** equality with the reported `range` field value.
 4. Verify the rationale for the threshold set is documented.

- [ ] T028 [US3] Generate final report in `data/results/final_report.json` containing mean/std, p-values (or bootstrap results), and sensitivity sweep range (min, max, range). **Verification**: Verify `data/results/final_report.json` exists with the specified structure.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

### Parallel Tasks

- [X] T030a [P] Create `docs/README.md` with project overview and installation instructions
- [X] T030b [P] Create `docs/usage.md` with usage instructions for all scripts

### Sequential Tasks (Must follow strict ordering)

- [ ] T030c Dependency: T011, T039. Create `docs/api.md` with API documentation for `src/` modules. **Requirement**: This documentation MUST include a section documenting the memory usage results (peak memory, OOM prevention efficacy) measured against the actual runner's available memory limit, referencing the data in `data/results/memory_profile.json` (generated by T011). **CRITICAL**: This task MUST fail to build if `data/results/memory_profile.json` does not exist. **Note**: Execute this task ONLY after T039 completes. This task does NOT wait for US2 or US3 completion, only for T039.

- [ ] T031a [P] Code cleanup: Linting configuration. **Deliverables**: Create `pyproject.toml` with ruff/black configuration, enable specific rules (e.g., E, F, W, I, N). **Verification**: Verify `pyproject.toml` exists and contains correct configuration.
- [ ] T031b [P] Code cleanup: Linting execution. **Deliverables**: Run `ruff check src/` and `black --check src/` with 0 errors. **Verification**: Verify `ruff check` and `black --check` return 0.
- [ ] T031c [P] Code cleanup: Print removal. **Deliverables**: Remove all `print()` calls (verify with `grep -r 'print(' src/`); replace with logging. **Verification**: Verify `grep` finds no `print(` calls.
- [X] T032a (Merged into T011) Performance optimization: Add memory profiling to `src/tracing.py` using `memory_profiler` to output `data/results/memory_profile_raw.jsonl`.
- [ ] T033 [P] Run quickstart.md validation: Execute commands in `docs/quickstart.md` and verify exit code 0 for all steps.
- [X] T034 (Merged into T035) Verify all data fetches use real, reachable URLs or package-based fetches (no synthetic fallbacks).

---

## Phase 7: Revision & Robustness (Review-Driven)

**Purpose**: Address specific reviewer concerns regarding data integrity, statistical rigor, and execution safety.

*Note: T040, T041, T042, T043 were resolved by integrating their logic into T011, T019, T026 respectively. No separate tasks remain.*

- [ ] T044 [US1] [Review] Implement robust error handling in `src/tracing.py` to explicitly log and halt on `CUDA` availability errors if the execution stage attempts to offload to GPU, ensuring the script fails loudly with a clear message if the model cannot be loaded on CPU or GPU as per the specific runner constraints. **Rationale**: Addresses concern that the tracing script might silently fail or hang if CUDA is requested but unavailable on the CPU-only runner, preventing the automatic offload mechanism from triggering correctly. **Verification**: Verify that running the script on a CPU-only runner without GPU access produces a clear error message and exit code 1 if CUDA is attempted.

- [ ] T045 [US2] [Review] Add a pre-flight check in `src/benchmark.py` to verify that the `canonical_map.json` file from T013 is valid and non-empty before attempting model injection, raising a `ValueError` if the file is missing or corrupted. **Rationale**: Addresses concern that the benchmark might crash with a cryptic error if the canonical map artifact is missing, rather than failing early with a clear dependency error. **Verification**: Verify that running the benchmark script without the canonical map artifact raises a `ValueError` with a clear message indicating the missing dependency.

- [ ] T046 [US3] [Review] Implement a cross-validation check in `src/stats_analysis.py` to verify that the static map derived from the trace set (indices 0-99) does not significantly degrade performance on a held-out validation set (indices -299) beyond the expected FID degradation, ensuring the map is not overfit to the trace images. **Rationale**: Addresses concern that the static map might be overfit to the specific images used in the trace set, leading to poor generalization on new data. **Verification**: Verify that the `statistical_analysis.json` file includes a `cross_validation_fid` field and that the script reports a warning if the cross-validation FID exceeds a threshold (e.g., 0.2).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories. **Note**: Includes Data Integrity tasks (T035) to ensure data loaders exist before tracing/benchmarking.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete, **EXCEPT** T030c which depends only on T039 (Phase 3).

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories. **CRITICAL**: Must complete before US2 as US2 requires the Canonical Map.
- **User Story 2 (P2)**: Depends on US1 completion (requires `canonical_map.json`). Can start after Foundational + US1.
- **User Story 3 (P3)**: Depends on US2 completion (requires benchmark results). Can start after Foundational + US2.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Tests within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members **only if** the dependency chain (US1 -> US2 -> US3) is respected.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories, includes Data Integrity)
3. Complete Phase 3: User Story 1 (Trace & Derive Map)
4. **STOP and VALIDATE**: Verify the tracing script produces valid tensors and the clustering logic correctly handles the null hypothesis.
5. Deploy/demo if ready (proof of concept for routing analysis).

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Generate Canonical Map (MVP!)
3. Add User Story 2 → Test independently → Benchmark Static vs Dynamic
4. Add User Story 3 → Test independently → Statistical validation
5. Each story adds value without breaking previous stories.

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Trace & Map)
 - Developer B: User Story 2 (Benchmark) - *Wait for US1 artifact*
 - Developer C: User Story 3 (Stats) - *Wait for US2 artifact*
3. Stories complete and integrate sequentially due to data dependencies.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **Crucial**: Data fetchers must fail loud on error; no synthetic fallbacks allowed (T035).
- **Crucial**: Memory management (one-by-one processing) is mandatory for US1 and US2 to run on CPU (T011).
- **Crucial**: Null hypothesis (low silhouette score) must be explicitly flagged, not ignored (T012).
- **Crucial**: Benchmark image count for T019 is fixed at $BENCHMARK_SET_SIZE images (indices $BENCHMARK_SET_START to $BENCHMARK_SET_START+$BENCHMARK_SET_SIZE-1) to match Spec US2; T025 uses $BENCHMARK_SEEDS images for statistical power.
- **Crucial**: Sensitivity analysis must use a concrete set of clustering distance thresholds {$SENSITIVITY_THRESHOLDS} with documented rationale (T027).
- **Crucial**: FID calculation must use frozen weights pre-trained on ImageNet (`IMAGENET1K_V1` in T006).
- **Crucial**: Memory report must be generated as an artifact (T011) and documented (T039).
- **Crucial**: Environment variables `TRACE_SET_SIZE` and `BENCHMARK_SET_START` are configurable with defaults (T008).
- **Crucial**: T029 was merged into T019 to resolve circular dependency.
- **Crucial**: T027 explicitly re-runs derivation (T012) per threshold and executes the benchmark loop internally.
- **Crucial**: T025 explicitly re-initializes models per seed using the SAME canonical map.
- **Crucial**: T026 explicitly documents N=5 limitations in output artifact and uses the percentile method, but allows the researcher to choose the bootstrap test.
- **Crucial**: T006 explicitly specifies `Inception_V_Weights.IMAGENET1K_V1` and pinned `torchvision`, and logs the model hash.
- **Crucial**: Memory report must be generated as an artifact (T011) and documented (T039).
- **Crucial**: T030c is moved to sequential block and depends on T039 only, not waiting for US2/US3.
- **Crucial**: T011, T012, T013, T018, T026, T027, T040, T043 have been updated with explicit schemas and counts to ensure executability.
- **Crucial**: T012 now preserves per-block dimensionality for clustering to satisfy FR-002.
- **Crucial**: T011 now handles all dataset metadata logging (T040 logic) and memory warnings (T043 logic) to ensure Single Source of Truth, and now generates `data/results/memory_profile.json` directly.
- **Crucial**: T019 now consumes T011's metadata artifact to avoid redundancy.
- **Crucial**: T027 dependency updated to reflect in-memory logic re-execution (bypassing T013 artifact) and explicit re-generation of benchmark images.
- **Crucial**: T027 now explicitly reuses T018 logic instead of re-implementing it.
- **Crucial**: Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence.
- **Crucial**: T011 now saves aggregated `.npy` files per image to avoid fragmentation.
- **Crucial**: T012 now explicitly loads aggregated files via glob and exposes `compute_canonical_map` for in-memory use.
- **Crucial**: T011 and T039 enforce hard memory limits to prevent OOM crashes.
- **Crucial**: T019 includes disjointness check logic intrinsically.
- **Crucial**: T040-T043 removed as they are integrated into earlier tasks.
- **Crucial**: T005 and T011 use `torch.float16` (not 8-bit) to comply with Spec Assumptions and SC-005.
- **Crucial**: T027 now uses 100 images for the sensitivity sweep to reduce computational load.
- **Crucial**: T027 now requires a rationale for the threshold set in the output artifact.
- **Crucial**: T006 now invokes the Reference-Validator Agent for citation verification.
- **Crucial**: T011 now includes checksum generation and state file recording.
- **Crucial**: T025 now uses pre-defined random seeds for reproducibility.
- **Crucial**: T026 now mandates the bootstrap test.
- **Crucial**: T027 now re-uses existing benchmark images to satisfy Single Source of Truth.
- **Crucial**: T025 now depends on T019.
- **Crucial**: T027 now depends on T012 and T018, bypassing T013.
- **Crucial**: T030c now depends on T011 and T039.
- **Crucial**: T044 addresses GPU offload failure handling.
- **Crucial**: T045 adds pre-flight checks for canonical map validity.
- **Crucial**: T046 implements cross-validation for static map generalization.