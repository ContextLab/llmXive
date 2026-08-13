# Tasks: llmXive follow-up: extending "Rethinking Cross-Layer Information Routing in Diffusion Transformers"

**Input**: Design documents from `/specs/001-llmxive-static-routing/`
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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan by executing: `mkdir -p projects/PROJ-907-llmxive-follow-up-extending-rethinking-c/code/{src,tests,data/imagenet_trace,data/imagenet_benchmark,data/routing_cache,data/results,docs}`. **Note**: This creates all necessary directories including `src/` as defined in the plan.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin. This phase includes Data Integrity tasks (T035) to ensure safe data handling and verified loaders before any processing begins.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T002 Initialize Python project by creating `projects/PROJ-907-llmxive-follow-up-extending-rethinking-c/code/requirements.txt` containing pinned versions: `torch==2.3.0+cpu` (install via `--index-url https://download.pytorch.org/whl/cpu`), `torchvision==0.18.0`, `transformers`, `diffusers`, `scikit-learn`, `torchmetrics`, `datasets`, `numpy`, `pandas`, `matplotlib`.
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools
- [X] T005 [P] Implement `projects/PROJ-907-llmxive-follow-up-extending-rethinking-c/code/src/model_loader.py`: Load canonical pre-trained SiT-XL model with DAR enabled (CPU compatible, reduced or standard precision). **Verification**: Task is complete only when `src/model_loader.py` exists and can be imported without error.
- [X] T006 [P] Implement `projects/PROJ-907-llmxive-follow-up-extending-rethinking-c/code/src/metrics.py`: Implement FID calculation using a frozen, pre-trained Inception network **from `torchvision.models.inception_v3`** using **`Inception_V3_Weights.DEFAULT`** (ensuring compatibility with pinned `torchvision==0.18.0` and matching the canonical baseline). **Specific Function**: `calculate_fid(image_list_1, image_list_2)`. **Constraint**: MUST load the network in `inference-only` mode (`model.eval()`) and explicitly wrap all inference calls in `torch.no_grad()` to freeze weights and prevent gradient computation. **Preprocessing**: Inputs MUST be resized to 299x299 and center-cropped to match the canonical baseline. **Verification**: Verify `src/metrics.py` contains `calculate_fid` function that accepts two image lists, uses `model.eval()` and `torch.no_grad()`, applies correct resizing/cropping, loads `DEFAULT` weights, and returns a float.
- [X] T007 [P] Implement `projects/PROJ-907-llmxive-follow-up-extending-rethinking-c/code/src/utils.py`: Helper functions for batch processing, memory management, and error handling. **Specific Functions**:
 1. `batch_iterator(iterable, batch_size)`: Yields chunks of size `batch_size` from `iterable`.
 2. `memory_guard(threshold_gb)`: Returns `True` if current RAM usage < `threshold_gb`, else raises a `MemoryError` exception.
 **Verification**: Verify functions exist, have correct signatures, and `memory_guard` raises an exception when the threshold is exceeded.
- [X] T008 Configure environment variables by creating `.env` file at project root with exact keys and **default values**: `TRACE_SET_SIZE=100` (default), `BENCHMARK_SET_START=100` (default), `RANDOM_SEED=42` (fixed integer). **Verification**: Verify `.env` exists, contains these keys with the specified default values, and the code validates that these values can be overridden via environment variables.
- [X] T035 [P] Implement `projects/PROJ-907-llmxive-follow-up-extending-rethinking-c/code/src/data_loader.py` to fetch ImageNet subsets using `datasets.load_dataset("imagenet-1k", split="validation", streaming=True)`. **CRITICAL**: Remove any `try/except` blocks that fall back to synthetic/mock data; the loader MUST raise an exception if the real source is unreachable. **Verification**: Verify that a failed fetch raises an exception and no synthetic data is generated.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Trace Dynamic Routing and Identify Canonical Map (Priority: P1) 🎯 MVP

**Goal**: Execute pre-trained SiT-XL with DAR on a subset of validation images, record routing weight matrices at every timestep, and derive a canonical static routing map (or global average fallback).

**Independent Test**: Run tracing on a representative set of images; verify output contains complete routing tensors for every block/timestep; verify clustering logic outputs valid k and silhouette score; verify fallback logic triggers correctly on null results.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T009 [P] [US1] Write unit test file `projects/PROJ-907-llmxive-follow-up-extending-rethinking-c/code/tests/unit/test_clustering.py` with assertions for the expected fallback behavior (global average generation when k < 2 or silhouette < 0.25). **Verification**: Test must assert that the *expected system output* flags the null result condition.

### Implementation for User Story 1

- [ ] T011 [US1] Implement `projects/PROJ-907-llmxive-follow-up-extending-rethinking-c/code/src/tracing.py`: Load SiT-XL/2, iterate through `$TRACE_SET_SIZE` ImageNet validation images (streamed/batched to stay < 7GB RAM) with a **fixed 100-timestep schedule (linear spacing 0-99, seed from `$RANDOM_SEED`)**, record routing weight matrices (softmax distributions) for every block and timestep to `data/routing_cache/`. **Sampling Strategy**: Use the first `$TRACE_SET_SIZE` images in the validation split to ensure reproducibility. **Memory Constraint**: Process strictly in **batches of size 1** to guarantee < 7GB RAM usage. **Logging**: Log progress as JSON lines to `data/results/tracing_log.jsonl` with keys: `image_index`, `peak_memory_mb`, `routing_shape`. Log memory profiles to `data/results/memory_profile_raw.jsonl`. **Data Hygiene**: Log the **HuggingFace dataset version ID** and the **SHA-256 checksum** of the first downloaded shard file (computed via `hashlib.sha256` on the raw bytes of the first shard file downloaded by `datasets.load_dataset`) to satisfy **Constitution Principle III (Data Hygiene)**. **Note**: The exact count `$TRACE_SET_SIZE` is a research-phase decision [deferred], currently defaulting to a representative magnitude. **Verification**: Verify `data/routing_cache/` contains valid `.npy` or `.pt` files for `$TRACE_SET_SIZE` images with schema [block, timestep, history_dim] and `data/results/tracing_log.jsonl` exists with valid entries.
- [ ] T012 [US1] Dependency: T011. Implement `projects/PROJ-907-llmxive-follow-up-extending-rethinking-c/code/src/clustering.py`: Load recorded routing tensors, compute the mean routing vector across all images/blocks for each timestep (input shape: [timesteps, history_dim]), apply k-means clustering to group timesteps based on this mean vector, compute silhouette score, and handle null hypothesis (k < 2 or score < 0.25) by generating global average vector. **Null Hypothesis Handling**: Explicitly output a warning and a specific flag in `data/results/null_hypothesis_flag.json` if the silhouette score < 0.25, ensuring this edge case is not silently ignored. **Verification**: Save cluster centers to `data/routing_cache/cluster_centers.json` and print silhouette score.
- [ ] T013 [US1] Dependency: T012. Implement `projects/PROJ-907-llmxive-follow-up-extending-rethinking-c/code/src/canonical_map.py`: Derive the "Canonical Routing Map" (static weight vector per block) from the dominant cluster or global average, save to `data/routing_cache/canonical_map.json`. **Verification**: Verify `data/routing_cache/canonical_map.json` exists and contains a dict with keys [block_id, weight_vector].

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Benchmark Static Approximation vs. Dynamic Baseline (Priority: P2)

**Goal**: Replace dynamic DAR module with static routing weights, benchmark inference latency and FID against the dynamic baseline on a disjoint image set.

**Independent Test**: Run static and dynamic models on a representative set of images.; verify latency reduction calculation; verify FID difference calculation; ensure results are logged to structured CSV/JSON.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T016 [P] [US2] Unit test for latency measurement logic in `projects/PROJ-907-llmxive-follow-up-extending-rethinking-c/code/tests/unit/test_benchmark.py` (verify timing accuracy)
- [X] T017 [P] [US2] Integration test for FID comparison in `projects/PROJ-907-llmxive-follow-up-extending-rethinking-c/code/tests/integration/test_fid_comparison.py` (verify FID calculation on dummy samples)

### Implementation for User Story 2

- [ ] T018 [US2] Dependency: T013. Implement `projects/PROJ-907-llmxive-follow-up-extending-rethinking-c/code/src/static_model.py`: Create a modified model class that injects the static routing map (from T013) and removes per-timestep softmax overhead. **Dependency**: Must load `data/routing_cache/canonical_map.json` (Artifact from T013). **Verification**: Verify the model can be instantiated and runs without computing routing weights dynamically.
- [ ] T019 [US2] Dependency: T018. Implement `projects/PROJ-907-llmxive-follow-up-extending-rethinking-c/code/src/benchmark.py`: Run inference for both dynamic (original) and static models on **$BENCHMARK_SET_SIZE** disjoint ImageNet validation images (starting at index `$BENCHMARK_SET_START`, default 100) to ensure disjointness from T011; measure time-to-solution for a representative number of timesteps; generate samples. **Logic**: Include FID comparison using `src/metrics.py`. **Validation**: **Implement validation logic** to ensure the benchmark set is disjoint from the trace set (indices 0 to `$TRACE_SET_SIZE-1`); raise an error if sets overlap. **Error Handling**: Must report high FID degradation (> 0.5) as a valid negative result **by appending the result to `data/results/benchmark_results.csv` and `.json`** without halting. **Data Hygiene**: Log the **HuggingFace dataset version ID** and the **SHA-256 checksum** of the first downloaded shard file (computed via `hashlib.sha256` on the raw bytes of the first shard file downloaded by `datasets.load_dataset`) to satisfy **Constitution Principle III (Data Hygiene)**. **Output Schema**: `data/results/benchmark_results.csv` and `data/results/benchmark_results.json` must contain columns/keys: `timestamp`, `model_type` (dynamic/static), `seed`, `latency_s`, `fid_score`, `fid_degradation`. **Note**: The exact count `$BENCHMARK_SET_SIZE` and start index `$BENCHMARK_SET_START` are research-phase decisions [deferred], currently defaulting to a representative subset of images. **Verification**: Verify `data/results/benchmark_results.csv` and `data/results/benchmark_results.json` are generated with the specified schema.
- [ ] T021 [US2] (Merged into T019) Save benchmark results (latency, FID, reduction %) to `data/results/benchmark_results.csv` and `data/results/benchmark_results.json` with the defined schema.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Significance and Sensitivity Analysis (Priority: P3)

**Goal**: Perform statistical significance tests on FID scores across 5 random seeds and sensitivity analysis on clustering thresholds.

**Independent Test**: Re-run benchmark 5 times with different seeds; verify mean/std reporting; sweep clustering thresholds; verify robustness reporting.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T023 [P] [US3] Unit test for bootstrap significance test in `projects/PROJ-907-llmxive-follow-up-extending-rethinking-c/code/tests/unit/test_stats.py` (verify non-parametric bootstrap implementation)
- [X] T024 [P] [US3] Unit test for sensitivity sweep logic in `projects/PROJ-907-llmxive-follow-up-extending-rethinking-c/code/tests/unit/test_sensitivity.py`

### Implementation for User Story 3

- [ ] T025 [US3] Dependency: T019 (script artifact). Implement `projects/PROJ-907-llmxive-follow-up-extending-rethinking-c/code/src/stats_analysis.py`: **Re-execute the benchmark script (T019) 5 times** with different random seeds. **CRITICAL**: For each seed, the script MUST **re-initialize the static model and re-run the dynamic baseline** to ensure independence and prevent "warm cache" or state leakage. Collect FID scores for **both** static and dynamic models; compute the **paired difference** (static - dynamic) for each seed; compute mean and standard deviation of these differences. **Verification**: Verify `data/results/statistical_analysis.json` exists and contains keys [mean, std, bootstrap_results].
- [ ] T026 [US3] Implement non-parametric bootstrap in `src/stats_analysis.py` on the **paired differences** to test significance. **Parameters**: Use **a sufficient number of resamples**, a **95% confidence interval** calculated using the **percentile method**, and a **95% confidence interval**. **Documentation**: Explicitly write a string field `"statistical_limitations"` to the output artifact `data/results/statistical_analysis.json` explaining the limitation of N=5 for parametric tests, as required by Spec FR-006 and Constitution Principle VI. **Output**: Save p-values, bootstrap distribution, and the limitation string to `data/results/statistical_analysis.json`.
- [ ] T027 [US3] Dependency: T013, T019. Implement sensitivity analysis in `projects/PROJ-907-llmxive-follow-up-extending-rethinking-c/code/src/sensitivity.py`: **Sweep the `clustering.distance_threshold` parameter over the concrete set {0.01, 0.05, 0.1}**. For each threshold in this set:
 1. **Re-run the derivation logic (T012/T013)** to compute a new canonical map using the specified threshold.
 2. **Execute the script generated in T019** using the newly computed map and the benchmark set defined by environment variables.
 3. Record the resulting FID score.
 **Verification**: Save sensitivity sweep results to `data/results/sensitivity_sweep.json`. The output MUST explicitly report the **range of FID degradation** observed across the sweep.
- [ ] T028 [US3] Generate final report in `data/results/final_report.json` containing mean/std, p-values (or bootstrap results), and sensitivity sweep range (min, max, range). **Verification**: Verify `data/results/final_report.json` exists with the specified structure.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

### Parallel Tasks

- [ ] T030a [P] Create `docs/README.md` with project overview and installation instructions
- [ ] T030b [P] Create `docs/usage.md` with usage instructions for all scripts

### Sequential Tasks (Must follow strict ordering)

- [ ] T039 [P] Dependency: T011. Implement a script to parse memory logs and **generate** `docs/memory_report.md` and `data/results/memory_profile.json` containing peak memory usage statistics and a summary of OOM prevention efficacy. **Verification**: Verify both output files exist and contain valid data. (Note: This task is the sole generator of `memory_profile.json`; T030c depends on this artifact).
- [ ] T030c Dependency: T039. Create `docs/api.md` with API documentation for `src/` modules. **Requirement**: This documentation MUST include a section documenting the memory usage results (peak memory, OOM prevention efficacy) measured against the actual runner's available memory limit, referencing the data in `data/results/memory_profile.json` (generated by T039). **CRITICAL**: This task MUST fail to build if `data/results/memory_profile.json` does not exist. **Note**: Execute this task ONLY after T039 completes.

- [ ] T031 Code cleanup and refactoring: **Deliverables**: Run linter with 0 errors (`ruff check src/`); remove all `print()` calls (verify with `grep -r 'print(' src/`); replace with logging. **Verification**: Verify `ruff check` returns 0 and `grep` finds no `print(` calls.
- [ ] T032a (Merged into T011) Performance optimization: Add memory profiling to `src/tracing.py` using `memory_profiler` to output `data/results/memory_profile_raw.jsonl`.
- [ ] T033 [P] Run quickstart.md validation: Execute commands in `docs/quickstart.md` and verify exit code 0 for all steps.
- [ ] T034 (Merged into T035) Verify all data fetches use real, reachable URLs or package-based fetches (no synthetic fallbacks).

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
- **Crucial**: Sensitivity analysis must use a concrete set of clustering distance thresholds {0.01, 0.05, 0.1} (T027).
- **Crucial**: FID calculation must use frozen weights pre-trained on ImageNet (`DEFAULT` weights in T006).
- **Crucial**: Memory report must be generated as an artifact (T039) and documented (T030c).
- **Crucial**: Environment variables `TRACE_SET_SIZE` and `BENCHMARK_SET_START` are configurable with defaults (T008).
- **Crucial**: T029 was merged into T019 to resolve circular dependency.
- **Crucial**: T027 explicitly re-runs derivation (T012/T013) per threshold and executes the T019 script.
- **Crucial**: T025 explicitly re-initializes models per seed.
- **Crucial**: T026 explicitly documents N=5 limitations in output artifact and uses the percentile method.
- **Crucial**: T006 explicitly specifies `Inception_V3_Weights.DEFAULT` and pinned `torchvision`.
- **Crucial**: T030c is moved to sequential block and depends on T039.
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence.