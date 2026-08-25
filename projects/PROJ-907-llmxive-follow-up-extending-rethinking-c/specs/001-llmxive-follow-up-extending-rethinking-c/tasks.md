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

- [X] T002 Initialize Python project by creating `projects/PROJ-907-llmxive-follow-up-extending-rethinking-c/code/requirements.txt` containing pinned versions: `torch==2.3.0+cpu ` (install via `--index-url https://download.pytorch.org/whl/cpu`), `torchvision==0.18.0 `, `transformers`, `diffusers`, `scikit-learn`, `numpy`, `pandas`, `matplotlib`. **Note**: `torchmetrics` removed as FID is implemented manually via `torchvision`.
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools
- [X] T005 [P] Implement `projects/PROJ-907-llmxive-follow-up-extending-rethinking-c/code/src/model_loader.py`: Load canonical pre-trained SiT-XL model with DAR enabled (CPU compatible, reduced or standard precision). **Verification**: Task is complete only when `src/model_loader.py` exists and can be imported without error.
- [X] T006 [P] Implement `projects/PROJ-907-llmxive-follow-up-extending-rethinking-c/code/src/metrics.py`: Implement FID calculation using a frozen, pre-trained Inception network **from `torchvision.models.inception_v3`** using **`Inception_V3_Weights.DEFAULT`** (ensuring compatibility with pinned `torchvision==0.18.0 ` and matching the canonical baseline). **Specific Function**: `calculate_fid(image_list_1, image_list_2)`. **Constraint**: MUST load the network in `inference-only` mode (`model.eval()`) and explicitly wrap all inference calls in `torch.no_grad()` to freeze weights and prevent gradient computation. **Preprocessing**: Inputs MUST be resized to 299x299 and center-cropped to match the canonical baseline. **Verification**: Verify `src/metrics.py` contains `calculate_fid` function that accepts two image lists, uses `model.eval()` and `torch.no_grad()`, applies correct resizing/cropping, loads `DEFAULT` weights, and returns a float.
- [X] T007 [P] Implement `projects/PROJ-907-llmxive-follow-up-extending-rethinking-c/code/src/utils.py`: Helper functions for batch processing, memory management, and error handling. **Specific Functions**:
 1. `batch_iterator(iterable, batch_size)`: Yields chunks of size `batch_size` from `iterable`.
 2. `memory_guard(threshold_gb)`: Returns `True` if current RAM usage < `threshold_gb`, else raises a `MemoryError` exception.
 **Verification**: Verify functions exist, have correct signatures, and `memory_guard` raises an exception when the threshold is exceeded.
- [X] T008 Configure environment variables by creating `.env` file at project root with exact keys and **default values**: `TRACE_SET_SIZE=100` (default), `BENCHMARK_SET_START=100` (default), `RANDOM_SEED=42` (fixed integer). **Verification**: Verify `.env` exists, contains these keys with the specified default values, and the code validates that these values can be overridden via environment variables.
- [X] T035 [P] Implement `projects/PROJ-907-llmxive-follow-up-extending-rethinking-c/code/src/data_loader.py` to fetch ImageNet subsets using `datasets.load_dataset("imagenetk", split="validation", streaming=True)`. **CRITICAL**: Remove any `try/except` blocks that fall back to synthetic/mock data; the loader MUST raise an exception if the real source is unreachable. **Verification**: Verify that a failed fetch raises an exception and no synthetic data is generated.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Trace Dynamic Routing and Identify Canonical Map (Priority: P1) 🎯 MVP

**Goal**: Execute pre-trained SiT-XL with DAR on a subset of validation images, record routing weight matrices at every timestep, and derive a canonical static routing map (or global average fallback).

**Independent Test**: Run tracing on a representative set of images; verify output contains complete routing tensors for every block/timestep; verify clustering logic outputs valid k and silhouette score; verify fallback logic triggers correctly on null results.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T009 [P] [US1] Write unit test file `projects/PROJ-907-llmxive-follow-up-extending-rethinking-c/code/tests/unit/test_clustering.py` with assertions for the expected fallback behavior (global average generation when k < 2 or silhouette < 0.25). **Verification**: Test must assert that the *expected system output* flags the null result condition.

### Implementation for User Story 1

- [ ] T011 [US1] Implement `projects/PROJ-907-llmxive-follow-up-extending-rethinking-c/code/src/tracing.py`: Load SiT-XL/2, iterate through `$TRACE_SET_SIZE` ImageNet validation images (streamed/batched to stay < 7GB RAM) with a **fixed -timestep schedule (linear spacing -99, seed from `$RANDOM_SEED`)**, record routing weight matrices (softmax distributions) for every block and timestep. **File Naming**: Save a **single aggregated** `.npy` file per image as `routing_{image_id}.npy`. **Schema**: Each `.npy` file MUST contain a 4D numpy array of shape `[num_timesteps, num_blocks, history_dim]` representing the routing weights for all timesteps and blocks for that specific image. **Sampling Strategy**: Use the first `$TRACE_SET_SIZE` images in the validation split to ensure reproducibility. **Memory Constraint**: Process strictly in **batches of small size** to guarantee < 7GB RAM usage. **Hard Halt**: MUST invoke `memory_guard(7.0)` before processing each image; if RAM exceeds 7GB, the script MUST raise `MemoryError` and halt immediately. **Logging**: Log progress as JSON lines to `data/results/tracing_log.jsonl` with keys: `image_index`, `peak_memory_mb`, `routing_shape`. Log memory profiles to `data/results/memory_profile_raw.jsonl`.
 **Data Hygiene**:
 1. Query the HuggingFace `datasets` library for the exact `dataset_version` and `revision` of the loaded `imagenetk` split.
 2. Save this metadata to `data/results/dataset_metadata.json` with keys: `dataset_name`, `split`, `revision`, `timestamp`, and `checksum` (cryptographic hash of the first shard).
 3. **CRITICAL**: Metadata MUST be saved **before** any routing files are generated.
 **Verification**:
 1. Verify `data/routing_cache/` contains valid `.npy` files with naming pattern `routing_*.npy`.
 2. Verify each `.npy` file loads as a 4D array with shape `[100, num_blocks, history_dim]` and dtype `float32`.
 3. Verify `data/results/dataset_metadata.json` exists and was created **before** the first `routing_*.npy` file (check timestamps).
 4. Verify `data/results/memory_profile_raw.jsonl` contains a `MemoryError` event if the limit was breached, or a `status: "PASS"` if not.

- [ ] T012 [US1] [FR-002] Dependency: T011. Implement `projects/PROJ-907-llmxive-follow-up-extending-rethinking-c/code/src/clustering.py`: Load recorded routing tensors. **Loading Logic**: Use `glob.glob("data/routing_cache/routing_*.npy")` to discover all files and load them into a single 5D tensor `[num_images, num_timesteps, num_blocks, history_dim]`. **Aggregation Logic**: For each block `b` in `num_blocks`, compute the mean routing vector across all images and all timesteps for that specific block. **Clustering**: Apply k-means clustering **independently to the routing vectors of each block** (clustering the rows of the `[num_timesteps, history_dim]` tensor for that block) to identify distinct phases. Compute the silhouette score for each block's clustering. **Null Hypothesis Handling**: If for any block the clustering identifies < 2 clusters or a silhouette score < 0.25, that block MUST default to a global average vector for that block. **Function**: Expose a pure function `compute_canonical_map(routing_tensor, distance_threshold)` that performs the clustering and returns the map without file I/O. **Output**: Save cluster centers and silhouette scores to `data/routing_cache/cluster_centers.json` with a structure that preserves the block dimension (e.g., `{"block_0": {"centers": [...], "silhouette": 0.5, "null_hypothesis_triggered": false, "null_reason": null},...}`). **Verification**:
 1. Verify `cluster_centers.json` loads and has keys matching `num_blocks`.
 2. Verify for any block where `null_hypothesis_triggered` is `true`, the `centers` field contains the exact global average vector (recompute mean and assert equality).
 3. Verify the `compute_canonical_map` function exists and can be called in memory without re-loading files.
 4. **Deterministic Check**: Run `python -c "import json, sys; d=json.load(open('data/routing_cache/cluster_centers.json')); assert len(d)==NUM_BLOCKS, f'Expected {NUM_BLOCKS} blocks, got {len(d)}'"` where NUM_BLOCKS is the model's block count.

- [ ] T013 [US1] Dependency: T012. Implement `projects/PROJ-907-llmxive-follow-up-extending-rethinking-c/code/src/canonical_map.py`: Derive the "Canonical Routing Map" (static weight vector per block) from the dominant cluster or global average for each block. **Output Schema**: Save to `data/routing_cache/canonical_map.json` as a JSON object with keys: `{"block_0": [float, float,...], "block_1": [float, float,...],...}` where each value is the static weight vector for that block. **Verification**: Verify `data/routing_cache/canonical_map.json` exists, contains the correct schema, and that the number of keys matches the number of blocks in the model.

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
- [ ] T019 [US2] Dependency: T018. Implement `projects/PROJ-907-llmxive-follow-up-extending-rethinking-c/code/src/benchmark.py`: Run inference for both dynamic (original) and static models on a set of disjoint ImageNet validation images, starting from a specified initial index. to ensure disjointness from T011; measure time-to-solution for a representative number of timesteps; generate samples. **Logic**: Include FID comparison using `src/metrics.py`. **Validation**: **Implement validation logic** to ensure the benchmark set is disjoint from the trace set (indices 0 to `$TRACE_SET_SIZE-1`); raise an error if sets overlap. **Data Hygiene**: **CRITICAL**: Read dataset metadata from `data/results/dataset_metadata.json` (produced by T011) to satisfy data hygiene requirements; DO NOT re-fetch or re-log dataset version/checksums to avoid redundancy. **Error Handling**: Must report high FID degradation (> 0.5) as a valid negative result **by appending the result to `data/results/benchmark_results.csv` and `.json`** without halting. **Output Schema**: `data/results/benchmark_results.csv` and `data/results/benchmark_results.json` must contain columns/keys: `timestamp`, `model_type` (dynamic/static), `seed`, `latency_s`, `fid_score`, `fid_degradation`. **Note**: The exact count `$BENCHMARK_SET_SIZE` and start index `$BENCHMARK_SET_START` are research-phase decisions [deferred], currently defaulting to a representative subset of images. **Verification**:
 1. Verify `data/results/benchmark_results.csv` and `data/results/benchmark_results.json` are generated with the specified schema.
 2. Verify that running the script with overlapping configuration (e.g., `BENCHMARK_SET_START=50`) triggers a `ValueError` with a clear message.
 3. Verify no overlap errors occurred by checking logs for the absence of ValueError regarding set intersection, and confirm `benchmark_results.csv`/`.json` contain keys: timestamp, model_type, seed, latency_s, fid_score, fid_degradation.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Significance and Sensitivity Analysis (Priority: P3)

**Goal**: Perform statistical significance tests on FID scores across Multiple random seeds and sensitivity analysis on clustering thresholds.

**Independent Test**: Re-run benchmark 5 times with different seeds; verify mean/std reporting; sweep clustering thresholds; verify robustness reporting.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T023 [P] [US3] Unit test for bootstrap significance test in `projects/PROJ-907-llmxive-follow-up-extending-rethinking-c/code/tests/unit/test_stats.py` (verify non-parametric bootstrap implementation)
- [X] T024 [P] [US3] Unit test for sensitivity sweep logic in `projects/PROJ-907-llmxive-follow-up-extending-rethinking-c/code/tests/unit/test_sensitivity.py`

### Implementation for User Story 3

- [ ] T025 [US3] Dependency: T019 (script logic). Implement `projects/PROJ-907-llmxive-follow-up-extending-rethinking-c/code/src/stats_analysis.py`: **Re-execute the benchmark logic (T019) 5 times** with different random seeds. **CRITICAL**: For each seed, the script MUST **re-initialize the static model and re-run the dynamic baseline** to ensure independence and prevent "warm cache" or state leakage. Collect FID scores for **both** static and dynamic models; compute the **paired difference** (static - dynamic) for each seed; compute mean and standard deviation of these differences. **Verification**: Verify `data/results/statistical_analysis.json` exists and contains keys [mean, std, bootstrap_results].
 1. Verify `data/results/statistical_analysis.json` contains `statistical_limitations` string mentioning N=5.
 2. Verify `bootstrap_results` contains `n_resamples=1000`.
 3. Confirm the file lists 5 distinct seeds and a `paired_differences` array.

- [ ] T026 [US3] Implement non-parametric bootstrap in `src/stats_analysis.py` on the **paired differences** to test significance. **Parameters**: Use **n_resamples=1000**, a **A confidence interval will be used to estimate the precision of the parameter estimates. ** calculated using the **percentile method**, and a **% confidence interval **. **Documentation**: Explicitly write a string field `"statistical_limitations"` to the output artifact `data/results/statistical_analysis.json` explaining the limitation of N=5 for parametric tests, as required by Spec FR-006 and Constitution Principle VI. **Output**: Save p-values, bootstrap distribution, and the limitation string to `data/results/statistical_analysis.json`. **Verification**: Verify `data/results/statistical_analysis.json` contains `n_resamples=1000` in the bootstrap results and the `statistical_limitations` string explicitly stating "Analysis based on N=5 seeds...".

- [ ] T027 [US3] Dependency: T012 (logic), T019 (logic). Implement sensitivity analysis in `projects/PROJ-907-llmxive-follow-up-extending-rethinking-c/code/src/sensitivity.py`: **Sweep the `clustering.distance_threshold` parameter over the concrete set A range of low significance thresholds (e.g., 0.05, 0.1 (2309.06305, https://arxiv.org/abs/2309.06305)) will be evaluated to determine the optimal cutoff for statistical inference. **. For each threshold in this set:
 1. **Call `compute_canonical_map` from `src/clustering.py` in memory** (passing theloaded routing tensor) to compute a new canonical map using the specified threshold. This step **bypasses the static `canonical_map.json` artifact from T013** and re-executes the clustering logic with the new threshold. This must explicitly handle the case where the threshold triggers the fallback to a global average (null hypothesis).
 2. **Execute the script generated in T019** using the newly computed map and the benchmark set defined by environment variables.
 3. Record the resulting FID score.
 **Output Schema**: Save sensitivity sweep results to `data/results/sensitivity_sweep.json` as a JSON list of objects: `[{"threshold": 0.01, "fid_score": 0.12,...}, {"threshold": 0.05,...},...]`. The output MUST explicitly report the **range of FID degradation** observed across the sweep.
 **Verification**:
 1. Save sensitivity sweep results to `data/results/sensitivity_sweep.json`.
 2. Verify the JSON contains a `range` field.
 3. **Calculate** `max(fid_scores) - min(fid_scores)` from the raw list and **assert** equality with the reported `range` field value.

- [ ] T028 [US3] Generate final report in `data/results/final_report.json` containing mean/std, p-values (or bootstrap results), and sensitivity sweep range (min, max, range). **Verification**: Verify `data/results/final_report.json` exists with the specified structure.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

### Parallel Tasks

- [X] T030a [P] Create `docs/README.md` with project overview and installation instructions
- [X] T030b [P] Create `docs/usage.md` with usage instructions for all scripts

### Sequential Tasks (Must follow strict ordering)

- [ ] T039 [US3] Dependency: T011. Implement a script to parse memory logs and **generate** `docs/memory_report.md` and `data/results/memory_profile.json` containing peak memory usage statistics and a summary of OOM prevention efficacy. **Logic**: Parse `data/results/memory_profile_raw.jsonl`, calculate peak memory usage, and explicitly compare it against the GitHub Actions free-tier limit. **Output**: `data/results/memory_profile.json` MUST contain a boolean field `within_limit` (true if peak < 7GB) and a string field `status` ("PASS" or "FAIL"). **Verification**:
 1. Verify both output files exist and contain valid data.
 2. Verify `data/results/memory_profile.json` contains `within_limit` (boolean) and `status` (string "PASS"/"FAIL") fields with values consistent with the 7GB limit check.
 3. Verify that if a `MemoryError` was logged in T011, `status` is "FAIL".

- [ ] T030c Dependency: T039. Create `docs/api.md` with API documentation for `src/` modules. **Requirement**: This documentation MUST include a section documenting the memory usage results (peak memory, OOM prevention efficacy) measured against the actual runner's available memory limit, referencing the data in `data/results/memory_profile.json` (generated by T039). **CRITICAL**: This task MUST fail to build if `data/results/memory_profile.json` does not exist. **Note**: Execute this task ONLY after T039 completes.

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

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories. **Note**: Includes Data Integrity tasks (T035) to ensure data loaders exist before tracing/benchmarking.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

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
- **Crucial**: Benchmark image count and start index are controlled by `$BENCHMARK_SET_SIZE` and `$BENCHMARK_SET_START` environment variables [deferred].
- **Crucial**: Sensitivity analysis must use a concrete set of clustering distance thresholds {, 0.05, 0.1} (T027).
- **Crucial**: FID calculation must use frozen weights pre-trained on ImageNet (`DEFAULT` weights in T006).
- **Crucial**: Memory report must be generated as an artifact (T039) and documented (T030c).
- **Crucial**: Environment variables `TRACE_SET_SIZE` and `BENCHMARK_SET_START` are configurable with defaults (T008).
- **Crucial**: T029 was merged into T019 to resolve circular dependency.
- **Crucial**: T027 explicitly re-runs derivation (T012) per threshold and executes the T019 script.
- **Crucial**: T025 explicitly re-initializes models per seed.
- **Crucial**: T026 explicitly documents N=5 limitations in output artifact and uses the percentile method.
- **Crucial**: T006 explicitly specifies `Inception_V3_Weights.DEFAULT` and pinned `torchvision`.
- **Crucial**: T030c is moved to sequential block and depends on T039.
- **Crucial**: T011, T012, T013, T018, T026, T027, T040, T043 have been updated with explicit schemas and counts to ensure executability.
- **Crucial**: T012 now preserves per-block dimensionality for clustering to satisfy FR-002.
- **Crucial**: T011 now handles all dataset metadata logging (T040 logic) and memory warnings (T043 logic) to ensure Single Source of Truth.
- **Crucial**: T019 now consumes T011's metadata artifact to avoid redundancy.
- **Crucial**: T027 dependency updated to reflect in-memory logic re-execution (bypassing T013 artifact).
- **Crucial**: Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence.
- **Crucial**: T011 now saves aggregated `.npy` files per image to avoid fragmentation.
- **Crucial**: T012 now explicitly loads aggregated files via glob and exposes `compute_canonical_map` for in-memory use.
- **Crucial**: T011 and T039 enforce hard memory limits to prevent OOM crashes.
- **Crucial**: T019 includes disjointness check logic intrinsically.
- **Crucial**: T040-T043 removed as they are integrated into earlier tasks.