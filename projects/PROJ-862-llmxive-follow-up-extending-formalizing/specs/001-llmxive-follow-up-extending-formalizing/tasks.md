# Tasks: llmXive Follow-up: Input Noise Injection for Latent Separability

**Input**: Design documents from `/specs/001-lm-axive-noise-injection/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[S]**: Must run serially (shared state, global resources)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
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

- [X] T001 [P] Create `code/` directory and `code/__init__.py`
- [X] T002 [P] Create `data/` directory and `data/raw/.gitkeep`, `data/processed/.gitkeep`
- [X] T003 [P] Create `tests/` directory and `tests/__init__.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure, data integrity, and safety logic that MUST be complete before ANY user story can begin. Includes merged data loader hardening, checksum verification, modular sweep logic, and execution order enforcement.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T010 [P] Create data schema contracts: Create YAML files in `specs/*/contracts/` defining the exact structure for all data artifacts., referencing FR-001, FR-002, FR-003, FR-005, FR-009, FR-011, SC-004, SC-006.
 - `dataset.schema.yaml`: Fields `pair_id`, `task_type`, `question`, `expected_answer`, `input_token_ids`.
 - `latent-vector.schema.yaml`: Fields `pair_id`, `task_type`, `vector_base64` (L2 normalized), `norm_status`.
 - `statistical-result.schema.yaml`: Fields `task_type`, `sigma`, `p_value`, `mean_diff`, `ci_lower`, `ci_upper`, `test_type` (t-test/Wilcoxon), `validity_collapse_distribution` (list of values across task types).
 - `validity-log.schema.yaml`: Fields `task_type`, `sigma`, `pass_rate`, `collapse_point` (boolean), `semantic_drift_score`, `output_validity_score`.
- [X] T004 [P] Create `code/requirements.txt` with pinned versions (transformers, torch, sentence-transformers, scikit-learn, bertscore, pandas, numpy, pytest). **MUST pin `sentence-transformers` to `sentence-transformers==2.2.2`** (verified stable version for `all-MiniLM-L6-v2`). The implementer must verify the commit hash for this version in the final run but this string is the required baseline.
- [X] T005 [P] Setup virtual environment instructions in `docs/` (or `code/scripts/setup.sh`)
- [X] T006 [P] Implement `code/config.py` to define noise sweep parameters: Create a `NoiseConfig` dataclass with fields `sigma_min=0.01`, `sigma_max=0.20`, `step=0.01`, model paths, random seeds, and memory limits. **MUST include a pre-flight feasibility check method: if the estimated runtime for the FIXED `step=0.01` (based on the output of T006b `data/processed/pilot_estimate.json`) exceeds the time budget (SC-004), the method MUST raise a `ConfigurationError` and HALT execution ONLY if the `--pilot` flag is active. If `--pilot` is NOT active, it MUST log a warning and proceed, relying on the pilot measurement to have validated feasibility.** (Replaces vague feasibility check with specific halting logic).
- [X] T006b [P] [Foundational] Implement Pilot Run: Create `code/pilot_runner.py` to execute a small-scale run (e.g., a task type, 10 pairs, 3 sigma values) to measure actual runtime per pair. **MUST save the measured runtime per pair and estimated total runtime to `data/processed/pilot_estimate.json`.** This file is the source of truth for T006's feasibility check.
- [X] T007 [P] Implement `code/model_utils.py` to load the frozen transformer model (Llama or distilled variant) in CPU-only mode with `torch.no_grad()` and `model.eval()`
- [X] T008 [P] Implement `code/streaming_utils.py` to provide chunked/batched iteration over large datasets to respect the available RAM limit
- [ ] T008b [P] Implement `code/memory_monitor.py` to instrument `tracemalloc` and enforce a hard "peak RSS ≤ 7GB" failure condition for the **entire process**; raise `MemoryLimitExceeded` if the aggregate threshold is breached (SC-004). **MUST log the peak RSS value to `data/processed/memory_profile.json` for EVERY run (both success and failure cases) to verify computational feasibility (SC-004).**
- [X] T010b [P] Refactor `code/main.py` to extract the sigma sweep loop into a new function `run_sweep` that accepts `sigma_range` and `callback` arguments. **This function MUST implement the early-exit logic to record the 'validity collapse point' and stop processing higher sigma values for a task type immediately upon detection, as mandated by FR-003.** (Replaces T035).
- [X] T010c [P] [Foundational] Implement Early-Exit Logic: Implement the specific algorithm in `run_sweep` (T010b) to detect the 'validity collapse point' (weighted pass-rate < 10%) and break the sigma loop. **This task is strictly the logic implementation, distinct from the refactoring in T010b.**
- [X] T011 [P] Implement `code/data_loader.py` to fetch the reasoning dataset from the verified HuggingFace URL specified in `code/config.py` (DATASET_NAME='google/bigbench_lite', DATASET_URL='https://huggingface.co/datasets/google/bigbench_lite'). **MUST explicitly check if the 'expected_answer' column exists and if the dataset contains 'within-task question pairs'. If the primary fetch fails OR the schema is invalid, raise DataFetchError and halt immediately (FR-006). MUST remove any try/except blocks that could fall back to synthetic data or alternative datasets like 'google/lambada'; if fetch fails, raise DataFetchError and halt (Constitution Principle III).** (Merged T006 & T044).
- [X] T012 [P] Add a pre-flight checksum verification in `code/data_loader.py`: **Calculate the SHA256 hash of the downloaded dataset file and compare it against the expected hash stored in `data/checksums.json`**. If the hash mismatches or the file is missing, raise `DataIntegrityError` and halt execution (Constitution Principle III). (Replaces T045).
- [X] T013 [P] Implement a "Real Data Only" assertion in `code/config.py`: **Add a runtime check that scans the `data/raw/` directory for any files named `synthetic_*` or `mock_*` and raises a `ConfigurationError` if found**, preventing accidental contamination of the pipeline with non-real data sources (Constitution Principle III). (Replaces T046).
- [X] T014 [P] Add robust error handling to `code/perturbation.py`: Ensure that if the projection to the nearest valid token fails (e.g., embedding matrix mismatch), the script **raises a specific `ProjectionError`** rather than silently failing or using a fallback, preventing corrupted data from entering the analysis pipeline (Phase O T041).
- [ ] T015 [P] Implement a "No Valid Sigma" handler in `code/analysis.py`: If the `validity_log.csv` shows that **no** $\sigma$ level passes the 90% validity threshold, the system must **generate a specific `NoValidSigmaReport`** in `data/processed/` detailing the trade-off curve and explicitly flagging the experiment as "Inconclusive" rather than attempting a statistical test on an empty set (Phase O T042).
- [ ] T016 [P] Add a `--dry-run` mode to `code/main.py`: Execute the entire pipeline logic up to the point of data writing, verifying all file paths, schema validations, and dependency checks, but **skip actual model inference** to validate the execution order and memory constraints before committing to a full run (Phase O T043).
- [ ] T047 [P] [Foundational] Implement Data Fetch Integrity Check: **Add a pre-flight check in `code/main.py` that explicitly validates the existence of `data/raw/` files and their checksums against `data/checksums.json` BEFORE any model loading or data pairing occurs.** If the dataset is missing or corrupted, the script must exit with code 1 and a clear error message, preventing any downstream processing on empty or fake data. (Logic integrated into T048a).
- [ ] T048a [P] [Foundational] Implement Execution Order Enforcement in `code/main.py`: **Add strict pre-checks BEFORE any processing:** Assert existence of `data/raw/` files and checksums (T047 logic). Assert that `pairing_config.json` exists (T019) before baseline extraction. Assert that `baseline_vectors.csv` (T021) exists before the sweep loop (T029). **If any assertion fails, halt with a specific error code distinguishing 'missing data' vs 'corrupted data'.** (Moved from Phase O).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Baseline Latent Vector Extraction (Priority: P1) 🎯 MVP

**Goal**: Extract baseline "thought" token hidden states for the reasoning dataset to establish the control group.

**Independent Test**: Run extraction on a single task type; verify output CSV contains normalized vectors matching model hidden size and correct PairIDs.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T017 [P] [US1] Contract test for baseline output schema in `tests/contract/test_baseline_vectors.py`
- [X] T018 [P] [US1] Unit test for hidden state extraction logic in `tests/unit/test_extract_hidden.py`

### Implementation for User Story 1

- [ ] T019 [US1] Extend `code/data_loader.py` to pair questions by task type and assign unique `PairID`s. **Logic: Group questions by `task_type`. For each group, create pairs sequentially (Q1-Q2, Q3-Q4, etc.) or randomly if count is odd. Output: `data/processed/pairing_config.json` with schema: `pair_id` (int), `task_type` (str), `question_1` (str), `question_2` (str).** **Depends on T054 (Streaming) to ensure memory safety during buffering.** <!-- FIXED: Implemented logic and schema -->
- [X] T020 [US1] Extend `code/model_utils.py` with function `extract_thought_vector(model, input_ids, thought_token_pos)` to return the hidden state vector
- [ ] T021 [US1] Implement `code/main.py` baseline extraction loop: Load data -> Extract vectors -> **Save to `data/processed/baseline_vectors.csv`** with columns `pair_id`, `task_type`, `vector_base64` (L2 normalized, base64 encoded string), `norm_status`. **Include validation that raises ValueError if dimensions mismatch model hidden size, and log progress/peak RSS via tracemalloc.**
- [ ] T022 [US1] Verify `code/main.py` baseline extraction: **Verify that T021 correctly logs progress and memory usage** to `data/processed/memory_profile.json`. **Log format: `{"phase": "baseline", "peak_rss_mb": <float>, "timestamp": "<iso>"}`. Pass criteria: peak_rss_mb < 7000.** <!-- FIXED: Defined log format and criteria -->

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Noise-Augmented Perturbation & Re-Extraction (Priority: P2)

**Goal**: Inject controlled Gaussian noise into input embeddings, project to nearest valid token, and re-extract latent vectors while enforcing semantic validity.

**Independent Test**: Inject known perturbation; verify embedding distance matches expected Euclidean distance and output retains ground truth (BERTScore ≥ 0.85).

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T023 [P] [US2] Unit test for noise injection and token projection math in `tests/unit/test_perturbation.py`
- [X] T024 [P] [US2] Contract test for validity log schema in `tests/contract/test_validity_log.py`

### Implementation for User Story 2

- [X] T025 [P] [US2] Implement `code/perturbation.py` function `inject_and_project(embedding, sigma, model_embedding_matrix)` that adds Gaussian noise and **projects to nearest valid token by minimizing Euclidean distance against model.embedding_matrix**, returning `perturbed_token_ids` and `perturbed_embeddings`
- [ ] T026 [P] [US2] Implement `code/validity_check.py` function `check_input_drift(baseline_input, perturbed_input)`. **Define `GLOBAL_SBERT` as a module-level lazy-loaded singleton. MUST explicitly pin the `sentence-transformers` library version in `requirements.txt`. Define constant `INPUT_DRIFT_THRESHOLD = 0.95 `. Exclude pairs with cosine similarity < 0.95. MUST implement an incremental write strategy with FILE LOCKING (using `filelock` library) to append results to `data/processed/validity_log.csv` immediately after processing each sigma step or batch to prevent race conditions.** (FR-009).
- [ ] T027 [P] [US2] Implement `code/validity_check.py` function `check_output_validity(model_output, expected_answer)` using BERTScore (F1 ≥ 0.85) and perplexity bound (≤ 2.0x baseline). **Save passing pairs to `data/processed/filtered_pairs_output_validity.csv` and failing pairs to `data/processed/failed_output_validity_pairs.csv`.** **Note: The primary halt for missing `expected_answer` is handled in T011.** (FR-006)
- [ ] T028 [US2] Implement `code/validity_check.py` function `check_validity_collapse(pass_rate, threshold)` to detect if >90% of pairs fail at a specific $\sigma$
- [ ] T029 [S] [US2] Implement `code/main.py` perturbation sweep loop logic: **Iterate sigma across a range of small values with fine-grained steps.** -> **Call streaming/batching logic (T008)** -> Perturb inputs -> Extract vectors -> Run validity checks (T026, T027) -> **MUST calculate the global semantic validity pass-rate for EVERY sigma level as the weighted average (by pair count) of pass-rates across all task types and record it to `data/processed/validity_log.csv` with columns `task_type`, `sigma`, `pass_rate`, `collapse_point` (boolean).** **MUST record the validity collapse point (task_type, sigma, pass_rate) IMMEDIATELY upon detection (when weighted average < 10%) and BEFORE breaking the sigma-loop for this task type**. **Record the full trade-off curve (sigma vs. pass_rate) for every sigma level**. **Explicitly mandate that the analysis phase must exclude the validity collapse point and all higher sigma values from the final statistical analysis ** -> Save results (FR-003, FR-007, FR-011). **Depends on `data/processed/baseline_vectors.csv` from T021. T026 and T027 are helper functions implemented in T026/T027 and called within this loop.** **Depends on T054 for streaming.**
- [ ] T030 [P] [US2] Verify `code/main.py` perturbation sweep: **Verify that T029 correctly generated `data/processed/perturbed_vectors.csv`** linked by `PairID` and `sigma`. **This is a verification task that runs AFTER T029 completes, ensuring data integrity.** <!-- FIXED: Clarified as post-loop verification -->
- [X] T031 [P] [US2] Implement logging for sweep progress: **MUST write to `logs/sweep.log` in JSON lines format** with fields: `current_sigma`, `pairs_processed`, `current_rss`, `status`. (FR-011).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Separability Analysis (Priority: P3)

**Goal**: Perform statistical hypothesis testing on the filtered pairs to determine if noise injection significantly increased latent separability.

**Independent Test**: Feed mock dataset with known difference; verify test selects correct distribution (t-test vs Wilcoxon) and reports correct p-value.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T032 [P] [US3] Unit test for normality check and test selection logic in `tests/unit/test_statistical_test.py`
- [X] T033 [P] [US3] Integration test for end-to-end analysis pipeline in `tests/integration/test_analysis.py`

### Implementation for User Story 3

- [X] T034 [P] [US3] Implement `code/analysis.py` function `calculate_pairwise_cosine_similarity(vectors, pair_ids)` to generate similarity distributions for baseline and perturbed sets
- [X] T035 [US3] Implement `code/analysis.py` function `filter_pairs_by_validity(validity_log_path, baseline_vectors_path, output_validity_path)`:
 - **Consume `data/processed/validity_log.csv`** (input drift) AND **`data/processed/filtered_pairs_output_validity.csv`** (output validity).
 - **Exclude pairs that failed the input drift check OR the output validity check.**
 - **Save filtered pairs to `data/processed/filtered_pairs_for_analysis.csv`** (FR-009, FR-011).
 - **Depends on `data/processed/validity_log.csv` from T029, and `data/processed/filtered_pairs_output_validity.csv` from T027.**
- [X] T036 [US3] Implement `code/analysis.py` function `calculate_per_task_trade_offs(filtered_pairs, validity_log)`:
 - Calculate the trade-off curve (perturbation magnitude vs. semantic validity pass-rate) for EACH task type.
 - **Save per-task trade-off curves to `data/processed/trade_off_curve.csv`** with columns: `task_type`, `sigma`, `validity_pass_rate`, `separability_metric` (FR-007, SC-002).
 - **Depends on `data/processed/validity_log.csv` from T029 and T035.**
- [X] T037 [US3] Implement `code/analysis.py` function `aggregate_global_results(task_results)`:
 - Aggregate per-task trade-off curves and validity collapse points into a global distribution.
 - **Calculate the statistical distribution (mean, std, histogram bins) of the 'validity collapse point' across all task types** to satisfy SC-006. **Explicitly calculate and save these metrics (mean, std, histogram bins) to the output.**
 - **Save global distribution to `data/processed/global_trade_off_curve.csv`** with columns: `sigma`, `global_validity_pass_rate`, `global_separability_metric`.
 - **Generate `data/processed/sensitivity_report.json`** containing the global distribution and validity collapse point distribution. **MUST include a key `raw_collapse_points` containing the list of collapse points per task type** for future re-analysis (SC-006). **MUST explicitly calculate the mean, standard deviation, and histogram bins of the collapse points and save these statistical metrics using Sturges' rule for binning.**
 - **If no sigma passes the validity threshold, this JSON MUST include a flag `inconclusive: true` AND the full trade-off curve data (sigma vs. pass_rate) for all task types, as required by FR-007.**
 - **Depends on `data/processed/validity_log.csv` from T029 and T036.**
- [ ] T038 [US3] Implement `code/plot_sensitivity.py` and generate `docs/sensitivity_report.md`: Create the final sensitivity report document including visualizations of the trade-off curves and validity collapse points to validate the robustness of the findings (FR-007, SC-002). **Depends on `data/processed/sensitivity_report.json` from T037.**
- [X] T039a [US3] Implement `code/analysis.py` function `apply_holm_bonferroni(p_values, {{claim:c_49db0550}} (Wikipedia: Misuse of p-values, https://en.wikipedia.org/wiki/Misuse_of_p-values))`: **Implement the Holm-Bonferroni correction as a distinct, testable function.**
- [X] T039b [US3] Implement `code/analysis.py` function `generate_report_object(statistical_results, sensitivity_data)`: **Generate the final report object containing p-values, mean differences, confidence intervals, and validity collapse distributions.**
- [ ] T039c [US3] Implement `code/main.py` analysis orchestration: Load filtered vectors -> Run tests -> **Apply Holm-Bonferroni correction (T039a)** -> Generate report (T039b) -> **Save to `data/processed/statistical_results.json` with keys: `p_value`, `mean_diff`, `ci`, `validity_collapse_distribution`, `trade_off_curve`, `inconclusive` (if applicable) (FR-005).** **Depends on T035/T036/T037/T039a/T039b.**
- [X] T040 [US3] Implement logic to flag "Significant Separability Increase" if corrected p-value < 0.05 (FR-005).

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T041 [P] Documentation updates in `docs/` including **create `docs/quickstart.md`** with exact run commands for CPU-only execution
- [ ] T042 [P] Code cleanup and refactoring of `main.py`: **Ensure the `run_sweep` function (T010b) is fully utilized and documented.**
- [ ] T043 [P] Performance optimization for the perturbation sweep loop: **Refactor `inject_and_project` in `perturbation.py` to use `numpy` vectorization for batch processing** and **wrap SBERT inference in `validity_check.py` to process batches of pairs**.
- [X] T044 [P] Additional unit tests for edge cases (e.g., normality violation, no valid sigma) in `tests/unit/`
- [X] T045 [P] Security hardening: Ensure no PII leaks in logs or output files
- [X] T046 [P] Run `docs/quickstart.md` validation to verify end-to-end execution on a small subset

---

## Phase P: CPU Feasibility & Dataset Streaming Optimization (Addressing Execution Constraints)

**Purpose**: Address the specific constraint that the default runner is CPU-only with ~7GB RAM and ~14GB disk. These tasks ensure the dataset is streamed correctly and the model fits within memory, preventing OOM crashes before the analysis begins.

- [X] T054 [P] [Foundational] Implement Streaming Dataset Loader: Refactor `code/data_loader.py` to use `datasets.load_dataset(..., streaming=True)` for the primary BigBench source. **MUST NOT load the entire dataset into RAM.** Instead, iterate over the streaming generator and **buffer only the subset of data for a single `task_type` at a time** to form pairs (satisfying FR-003), then discard that buffer before loading the next task type. **If the dataset source does not support streaming, implement a chunked download and read strategy using `pandas.read_csv(..., chunksize=...)` or `json` line iteration.** This ensures the memory footprint remains constant regardless of dataset size (SC-004). **Depends on T008 (Streaming Utils).** <!-- FAILED: unspecified -->
- [X] T055 [P] [Foundational] Implement Batched Inference Wrapper: Create `code/model_utils.py` function `run_batched_inference(model, input_ids_list, batch_size=4)`. **This function MUST process inputs in small batches to prevent GPU/CPU memory spikes during the sweep loop.** It must handle the accumulation of hidden states and ensure that intermediate tensors are detached and garbage collected after each batch. This is critical for the perturbation phase (US2) where multiple forward passes occur per pair.
- [X] T056 [P] [Foundational] Add Dynamic Memory Guardrails: Enhance `code/memory_monitor.py` to include a **dynamic check during the sweep loop**. If the RSS approaches 6.5GB (leaving 0.5GB buffer), the system MUST **pause processing, force garbage collection (`gc.collect()`), and log a warning** before resuming. If RSS exceeds a defined memory threshold, it MUST raise `MemoryLimitExceeded` immediately. This prevents the "silent OOM" crash that often occurs during long sweep loops.
- [ ] T057 [P] [US2] Implement Adaptive Batching for SBERT: Refactor `code/validity_check.py` to process SBERT checks in configurable batches. **MUST NOT load the SBERT model for every single pair.** Instead, accumulate pairs in a buffer and run inference on the batch to minimize overhead. **If the batch size causes memory pressure, the system must dynamically reduce the batch size to 1.** <!-- FAILED: unspecified -->

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Revision (Phase O)**: Integrates into Foundational and Analysis phases; T048 and T037/T039 logic must be implemented before the first full run.
- **Feasibility (Phase P)**: MUST be implemented before any US2 execution to ensure the sweep loop does not crash due to memory limits. **T054 is a prerequisite for T019 and T029.**

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data structure (PairIDs) but can be implemented independently. **MUST wait for Phase P completion to ensure memory safety.**
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on data produced by US1 and US2 (vectors and validity logs)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Helpers before Services/Logic
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members
- **Note**: T021 and T029 are marked [S] (Serial) due to global SBERT model loading and thread safety requirements.
- **Note**: Phase P tasks (T054-T057) can be implemented in parallel with US1/US2 implementation tasks as they are foundational utilities.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for baseline output schema in tests/contract/test_baseline_vectors.py"
Task: "Unit test for hidden state extraction logic in tests/unit/test_extract_hidden.py"

# Launch all models for User Story 1 together:
Task: "Implement data_loader.py function to pair questions by task type"
Task: "Implement model_utils.py function extract_thought_vector"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (verify CSV output and vector dimensions)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Verify perturbation and validity checks)
4. Add User Story 3 → Test independently → Deploy/Demo (Verify statistical results)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Baseline extraction)
 - Developer B: User Story 2 (Perturbation & Validity)
 - Developer C: User Story 3 (Statistical Analysis)
 - Developer D: Phase P (Streaming & Memory Optimization)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [S] tasks = Serial (shared state, global resources)
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Data Hygiene**: NEVER use synthetic data. If real data fetch fails, the script MUST crash (raise error) rather than falling back to mock data.
- **Resource Limits**: Strictly enforce a constrained RAM limit via `tracemalloc` and streaming/batching (T008b, T054, T055).
- **CPU Constraint**: All model operations must be CPU-only; do not attempt CUDA offloading unless explicitly re-targeted to a GPU runner.
- **Revision Concerns**: All revision tasks (T011-T016) have been integrated into the Foundational Phase to ensure data integrity and safety before implementation begins.
- **Execution Order**: T048 and T037/T039 logic must be implemented before the first full run to handle the 'No Valid Sigma' case gracefully.
- **Removed T010c**: Task removed to eliminate scope creep and unnecessary I/O overhead.
- **Removed T051**: Logic for 'No Valid Sigma' reporting is now explicitly handled in T037 and T039 to avoid unauthorized artifact creation.
- **T026 Execution**: T026 is a helper function called within T029; results are now written incrementally to ensure data hygiene.
- **T006 Logic**: Dynamic step adjustment removed; replaced with halting pre-flight check.
- **CPU Feasibility**: Phase P tasks are mandatory to ensure the project runs within the 7GB RAM limit on the default runner.
