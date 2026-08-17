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

**Purpose**: Core infrastructure, data integrity, and safety logic that MUST be complete before ANY user story can begin. Includes merged data loader hardening, checksum verification, and modular sweep logic.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T010 [P] Create data schema contracts: Create four YAML files in `specs/001-lm-axive-noise-injection/contracts/` defining the exact structure for all data artifacts, referencing FR-001, FR-002, FR-003, FR-005, FR-009, FR-011, SC-004, SC-006.
 - `dataset.schema.yaml`: Fields `pair_id`, `task_type`, `question`, `expected_answer`, `input_token_ids`.
 - `latent-vector.schema.yaml`: Fields `pair_id`, `task_type`, `vector_base64` (L2 normalized), `norm_status`.
 - `statistical-result.schema.yaml`: Fields `task_type`, `sigma`, `p_value`, `mean_diff`, `ci_lower`, `ci_upper`, `test_type` (t-test/Wilcoxon), `validity_collapse_distribution` (list of values across task types).
 - `validity-log.schema.yaml`: Fields `task_type`, `sigma`, `pass_rate`, `collapse_point` (boolean), `semantic_drift_score`, `output_validity_score`.
- [X] T004 [P] Create `code/requirements.txt` with pinned versions (transformers, torch, sentence-transformers, scikit-learn, bertscore, pandas, numpy, pytest). **MUST pin `sentence-transformers` to a specific version hash or commit SHA to ensure reproducibility of the `all-MiniLM-L-v2` model weights. **
- [X] T005 [P] Setup virtual environment instructions in `docs/` (or `code/scripts/setup.sh`)
- [X] T006 [P] Implement `code/config.py` to define noise sweep parameters: Create a `NoiseConfig` dataclass with fields `sigma_min=0.01`, `sigma_max=0.20`, `step=0.01`, model paths, random seeds, and memory limits. **MUST include a pre-flight feasibility check method: if the estimated runtime for the FIXED `step=0.01` (based on a small sample or heuristic) exceeds the time budget (SC-004), the method MUST raise a `ConfigurationError` and HALT execution with a clear message. The system MUST NOT automatically adjust the step size. The final `step` value MUST be logged to `data/processed/config_log.json` only after successful pre-flight validation. ** (Replaces vague feasibility check with specific halting logic).
- [X] T007 [P] Implement `code/model_utils.py` to load the frozen transformer model (Llama or distilled variant) in CPU-only mode with `torch.no_grad()` and `model.eval()`
- [X] T008 [P] Implement `code/streaming_utils.py` to provide chunked/batched iteration over large datasets to respect the available RAM limit
- [X] T008b [P] Implement `code/memory_monitor.py` to instrument `tracemalloc` and enforce a hard "peak RSS ≤ 7GB" failure condition for the **entire process**; raise `MemoryLimitExceeded` if the aggregate threshold is breached (SC-004). **MUST log the peak RSS value to `data/processed/memory_profile.json` for EVERY run (both success and failure cases) to verify computational feasibility (SC-004).**
- [X] T010b [P] Refactor `code/main.py` to extract the sigma sweep loop into a new function `run_sweep` that accepts `sigma_range` and `callback` arguments. **This function MUST implement the early-exit logic to record the 'validity collapse point' and stop processing higher sigma values for a task type immediately upon detection, as mandated by FR-003.** (Replaces T035).
- [X] T011 [P] Implement `code/data_loader.py` to fetch the reasoning dataset from the verified HuggingFace URL specified in `code/config.py` (DATASET_NAME='bigbench_lite', DATASET_URL='https://huggingface.co/datasets/google/bigbench_lite' [UNRESOLVED-CLAIM: c_ad998463 — status=not_enough_info]). **MUST explicitly check if the 'expected_answer' column exists; if missing, raise ConfigurationError and halt immediately [UNRESOLVED-CLAIM: c_1ca7699f — status=not_enough_info] (FR-006). MUST remove any try/except blocks that could fall back to synthetic data; if fetch fails, raise DataFetchError and halt (Constitution Principle III).** (Merged T006 & T044). <!-- FAILED: unspecified -->
- [X] T012 [P] Add a pre-flight checksum verification in `code/data_loader.py`: **Calculate the SHA256 hash of the downloaded dataset file and compare it against the expected hash stored in `data/checksums.json`**. If the hash mismatches or the file is missing, raise `DataIntegrityError` and halt execution (Constitution Principle III). (Replaces T045).
- [X] T013 [P] Implement a "Real Data Only" assertion in `code/config.py`: **Add a runtime check that scans the `data/raw/` directory for any files named `synthetic_*` or `mock_*` and raises a `ConfigurationError` if found**, preventing accidental contamination of the pipeline with non-real data sources (Constitution Principle III). (Replaces T046).
- [X] T014 [P] Add robust error handling to `code/perturbation.py`: Ensure that if the projection to the nearest valid token fails (e.g., embedding matrix mismatch), the script **raises a specific `ProjectionError`** rather than silently failing or using a fallback, preventing corrupted data from entering the analysis pipeline (Phase O T041).
- [X] T015 [P] Implement a "No Valid Sigma" handler in `code/analysis.py`: If the `validity_log.csv` shows that **no** $\sigma$ level passes the 90% validity threshold, the system must **generate a specific `NoValidSigmaReport`** in `data/processed/` detailing the trade-off curve and explicitly flagging the experiment as "Inconclusive" rather than attempting a statistical test on an empty set (Phase O T042).
- [X] T016 [P] Add a `--dry-run` mode to `code/main.py`: Execute the entire pipeline logic up to the point of data writing, verifying all file paths, schema validations, and dependency checks, but **skip actual model inference** to validate the execution order and memory constraints before committing to a full run (Phase O T043).

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

- [X] T019 [US1] Extend `code/data_loader.py` to pair questions by task type and assign unique `PairID`s (output: `data/processed/pairing_config.json`) <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->
- [X] T020 [US1] Extend `code/model_utils.py` with function `extract_thought_vector(model, input_ids, thought_token_pos)` to return the hidden state vector
- [X] T021 [US1] Implement `code/main.py` baseline extraction loop: Load data -> Extract vectors -> **Save to `data/processed/baseline_vectors.csv`** with columns `pair_id`, `task_type`, `vector_base64` (L2 normalized, base64 encoded string), `norm_status`. **Include validation that raises ValueError if dimensions mismatch model hidden size, and log progress/peak RSS via tracemalloc.**
- [X] T022 [US1] Verify `code/main.py` baseline extraction: **Verify that T021 correctly logs progress and memory usage** to `data/processed/memory_profile.json` and that the output CSV matches the schema. This task isolates the verification logic to ensure distinct testing. <!-- FAILED: unspecified -->

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
- [ ] T026 [S] [US2] Implement `code/validity_check.py` function `check_input_drift(baseline_input, perturbed_input)` using **ONLY** `sentence-transformers/all-MiniLM-L6-v2`. **Define `GLOBAL_SBERT` as a module-level lazy-loaded singleton. ** **MUST explicitly pin the `sentence-transformers` library version in `requirements.txt` to ensure reproducibility.** **Exclude pairs with cosine similarity < 0.95 [UNRESOLVED-CLAIM: c_268506b7 — status=not_enough_info] ** and **MUST explicitly exclude these pairs from downstream statistical analysis**. **MUST implement an incremental write strategy: append results to a temporary buffer or write per-step to `data/processed/validity_log.csv` immediately after processing each sigma step or batch, rather than accumulating in memory and writing only at the end. This ensures data hygiene and prevents loss if the process crashes or stops early due to validity collapse (FR-011).** (FR-009).
- [ ] T027 [US2] Implement `code/validity_check.py` function `check_output_validity(model_output, expected_answer)` using BERTScore (F1 ≥ 0.85) and perplexity bound (≤ 2.0x baseline). **Save passing pairs to `data/processed/filtered_pairs_output_validity.csv` and failing pairs to `data/processed/failed_output_validity_pairs.csv`.** **Note: The primary halt for missing `expected_answer` is handled in T011.** (FR-006) <!-- FAILED: unspecified -->
- [X] T028 [US2] Implement `code/validity_check.py` function `check_validity_collapse(pass_rate, threshold)` to detect if >90% of pairs fail at a specific $\sigma$
- [X] T029 [S] [US2] Implement `code/main.py` perturbation sweep loop logic: **Iterate sigma across a range of small values with fine-grained steps.** -> **Call streaming/batching logic (T008)** -> Perturb inputs -> Extract vectors -> Run validity checks (T026, T027) -> **MUST calculate the global semantic validity pass-rate for EVERY sigma level and record it to `data/processed/validity_log.csv` with columns `task_type`, `sigma`, `pass_rate`, `collapse_point` (boolean)**. **MUST record the validity collapse point (task_type, sigma, pass_rate) IMMEDIATELY upon detection and BEFORE breaking the sigma-loop for this task type**. **Record the full trade-off curve (sigma vs. pass_rate) for every sigma level**. **Explicitly mandate that the analysis phase must exclude the validity collapse point and all higher sigma values from the final statistical analysis** -> Save results (FR-003, FR-007, FR-011). **Depends on `data/processed/baseline_vectors.csv` from T021. T026 and T027 are helper functions called within this loop, not pre-requisites.**
- [ ] T030 [US2] Save perturbed vectors and metadata to `data/processed/perturbed_vectors.csv` linked by `PairID` and `sigma` <!-- FAILED: unspecified -->
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
 - **Depends on `data/processed/validity_log.csv` from T029, `data/processed/filtered_pairs_input_drift.csv` from T029, and `data/processed/filtered_pairs_output_validity.csv` from T029.**
- [X] T036 [US3] Implement `code/analysis.py` function `calculate_per_task_trade_offs(filtered_pairs, validity_log)`:
 - Calculate the trade-off curve (perturbation magnitude vs. semantic validity pass-rate) for EACH task type.
 - **Save per-task trade-off curves to `data/processed/trade_off_curve.csv`** with columns: `task_type`, `sigma`, `validity_pass_rate`, `separability_metric` (FR-007, SC-002).
 - **Depends on `data/processed/validity_log.csv` from T029 and T035.**
- [X] T037 [US3] Implement `code/analysis.py` function `aggregate_global_results(task_results)`:
 - Aggregate per-task trade-off curves and validity collapse points into a global distribution.
 - **Calculate the statistical distribution (mean, std, histogram) of the 'validity collapse point' across all task types [UNRESOLVED-CLAIM: c_1be10a87 — status=not_enough_info] ** to satisfy SC-006. **Explicitly calculate and save these metrics (mean, std, histogram bins) to the output. **
 - **Save global distribution to `data/processed/global_trade_off_curve.csv`** with columns: `sigma`, `global_validity_pass_rate`, `global_separability_metric`.
 - **Generate `data/processed/sensitivity_report.json`** containing the global distribution and validity collapse point distribution. **MUST include a key `raw_collapse_points` containing the list of collapse points per task type ** for future re-analysis (SC-006). **MUST explicitly calculate the mean, standard deviation, and histogram bins of the collapse points and save these statistical metrics.**
 - **If no sigma passes the validity threshold, this JSON MUST include a flag `inconclusive: true` AND the full trade-off curve data (sigma vs. pass_rate) for all task types, as required by FR-007.**
 - **Depends on `data/processed/validity_log.csv` from T029 and T036.**
- [ ] T038 [US3] Implement `code/plot_sensitivity.py` and generate `docs/sensitivity_report.md`: Create the final sensitivity report document including visualizations of the trade-off curves and validity collapse points to validate the robustness of the findings (FR-007, SC-002). **Depends on `data/processed/sensitivity_report.json` from T037.**
- [ ] T039 [US3] Implement `code/main.py` analysis orchestration: Load filtered vectors -> Run tests -> **Apply Holm-Bonferroni correction to all resulting p-values across the full matrix of (task_type, sigma) results as a distinct step [UNRESOLVED-CLAIM: c_0ca245a1 — status=not_enough_info] ** -> Generate sensitivity report -> Save to `data/processed/statistical_results.json` with keys: `p_value`, `mean_diff`, `ci`, `validity_collapse_distribution`, `trade_off_curve`, `inconclusive` (if applicable) (FR-005). **Depends on T035/T036/T037.**
- [X] T040 [US3] Implement logic to flag "Significant Separability Increase" if corrected p-value < 0.05 (FR-005).

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T041 [P] Documentation updates in `docs/` including **create `docs/quickstart.md`** with exact run commands for CPU-only execution
- [ ] T042 [P] Code cleanup and refactoring of `main.py`: **Ensure the `run_sweep` function (T010b) is fully utilized and documented.**
- [X] T043 [P] Performance optimization for the perturbation sweep loop: **Refactor `inject_and_project` in `perturbation.py` to use `numpy` vectorization for batch processing** and **wrap SBERT inference in `validity_check.py` to process batches of pairs**.
- [X] T044 [P] Additional unit tests for edge cases (e.g., normality violation, no valid sigma) in `tests/unit/`
- [X] T045 [P] Security hardening: Ensure no PII leaks in logs or output files
- [X] T046 [P] Run `docs/quickstart.md` validation to verify end-to-end execution on a small subset

---

## Phase O: Revision & Safety Hardening (Addressing Reviewer Concerns)

**Purpose**: Address specific reviewer concerns regarding data integrity, execution order, and statistical rigor. These tasks are mandatory additions to the plan.

- [ ] T047 [P] [Review] Verify Data Fetch Integrity: Implement a pre-flight check in `code/main.py` that explicitly validates the existence of `data/raw/` files and their checksums against `data/checksums.json` **BEFORE** any model loading or data pairing occurs. If the dataset is missing or corrupted, the script must exit with code 1 and a clear error message, preventing any downstream processing on empty or fake data.
- [ ] T048 [Review] Enforce Execution Order: Refactor `code/main.py` to enforce a strict dependency chain: `Load Data` -> `Pair Questions` -> `Baseline Extraction` -> `Validity Check (Input)` -> `Perturbation Loop` -> `Validity Check (Output)` -> `Statistical Analysis`. **ENFORCE strict pre-checks: Assert the existence of `baseline_vectors.csv` (T021) BEFORE starting the sweep loop (T029). Assert the existence of `data/processed/validity_log.csv` AFTER the sweep loop. If the file is missing, distinguish between 'no valid sigma found' (success case: check for partial logs or specific error codes) and 'sweep crashed' (failure case: check for incomplete logs or missing error codes) before triggering the 'No Valid Sigma' reporting logic (T015/T037). Do NOT remove assertions; instead, strengthen them to prevent ambiguous states.** (FR-003, FR-011).
- [ ] T049 [Review] Statistical Power Verification: In `code/analysis.py`, add a pre-test check (T035) that calculates the effective sample size `n` after filtering for validity. If `n < 30` (or the threshold for the chosen test), the system must **automatically switch to Wilcoxon signed-rank test**, **calculate the reduced statistical power**, and **log the reduced power warning to `data/processed/statistical_results.json` under a key `power_warning`** (FR-012, SC-005).
- [X] T050 [Review] Family-Wise Error Correction Implementation: In `code/analysis.py` (T039), implement the Holm-Bonferroni correction as a distinct, testable function `apply_holm_bonferroni(p_values, alpha=0.05)`. Ensure this function is called **after** collecting all p-values from the (task_type, sigma) matrix but **before** determining significance, and log the adjusted p-values in the final output.
- [ ] T052 [Review] Memory Leak Prevention: Add a post-extraction garbage collection step in `code/main.py` after each major phase (Baseline, Perturbation Loop) to explicitly call `gc.collect()` to ensure RSS does not drift upward across the long sweep loop. **Removed `torch.cuda.empty_cache()` as it is CPU-only.**
- [X] T053 [Review] External Model Fallback Safety: In `code/validity_check.py`, ensure that the `sentence-transformers` model loading is wrapped in a try/except that **only** catches network/IO errors and retries the fetch. If the model file is missing locally, it MUST download it; it MUST NOT generate a random embedding vector as a fallback. If the download fails after a defined number of retries, the process must halt.

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

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data structure (PairIDs) but can be implemented independently
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
- **Resource Limits**: Strictly enforce a constrained RAM limit via `tracemalloc` and streaming/batching (T008b).
- **CPU Constraint**: All model operations must be CPU-only; do not attempt CUDA offloading unless explicitly re-targeted to a GPU runner.
- **Revision Concerns**: All revision tasks (T011-T016) have been integrated into the Foundational Phase to ensure data integrity and safety before implementation begins.
- **Execution Order**: T048 and T037/T039 logic must be implemented before the first full run to handle the 'No Valid Sigma' case gracefully.
- **Removed T010c**: Task removed to eliminate scope creep and unnecessary I/O overhead.
- **Removed T051**: Logic for 'No Valid Sigma' reporting is now explicitly handled in T037 and T039 to avoid unauthorized artifact creation.
- **T026 Execution**: T026 is a helper function called within T029; results are now written incrementally to ensure data hygiene.
- **T006 Logic**: Dynamic step adjustment removed; replaced with halting pre-flight check.
