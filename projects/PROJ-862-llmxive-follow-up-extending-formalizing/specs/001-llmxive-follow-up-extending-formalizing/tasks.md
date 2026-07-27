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

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Create `code/requirements.txt` with pinned versions (transformers, torch, sentence-transformers, scikit-learn, bertscore, pandas, numpy, pytest, statsmodels)
- [X] T005 [P] Setup virtual environment instructions in `docs/` (or `code/scripts/setup.sh`)
- [X] T006 [P] Implement `code/data_loader.py` to fetch the reasoning dataset (`bigbench_lite`) from a verified HuggingFace URL: **Check for column `expected_answer` in the dataset schema BEFORE fetching; if missing, raise `ConfigurationError` with message "Dataset missing required column: expected_answer" and halt immediately (NO synthetic fallback)** (FR-006). This is the SINGLE SOURCE OF TRUTH for this validation.
- [X] T007 [P] Implement `code/model_utils.py` to load the frozen transformer model (Llama or distilled variant) in CPU-only mode with `torch.no_grad()` and `model.eval()`
- [X] T008 [P] Implement `code/streaming_utils.py` to provide chunked/batched iteration over large datasets to respect the available RAM limit. **Explicitly implement a streaming strategy (e.g., `itertools.islice` with a fixed chunk size, online accumulation) to process pairs in chunks so the process NEVER holds the full dataset in memory, proactively avoiding the GB limit rather than just crashing when it is exceeded.** (SC-004).
- [X] T008b [P] Implement `code/memory_monitor.py`: Create a module wrapping `tracemalloc` with a function `check_memory_limit()` that raises `MemoryLimitExceeded` if peak RSS > 7GB, and logs peak RSS to `data/processed/memory_profile.json` on exit. **This check is a final safety net; the streaming logic in T008 must ensure RSS never approaches 7GB. If this check triggers, it indicates a failure in T008's streaming implementation.** Do NOT mark as [P] as this is a global state constraint.
- [X] T008c [P] Integrate `code/memory_monitor.py` into `code/main.py`: Import `check_memory_limit()` and invoke it at the start of the main loop and after every major processing block (baseline extraction, per-sigma sweep) to enforce the hard failure condition (SC-004). **Depends on T008b.**
- [X] T009 [P] Implement `code/config.py` to define noise sweep parameters: Create a `NoiseConfig` dataclass with fields `sigma_min`, `sigma_max`, `step`, model paths, random seeds, and memory limits
- [X] T010a [P] Create `specs/001-lm-axive-noise-injection/contracts/dataset.schema.yaml`: Define fields `pair_id`, `task_type`, `question`, `expected_answer`, `input_token_ids`.
- [X] T010b [P] Create `specs/001-lm-axive-noise-injection/contracts/latent-vector.schema.yaml`: Define fields `pair_id`, `task_type`, `vector_base64` (L2 normalized), `norm_status`.
- [X] T010c [P] Create `specs/001-lm-axive-noise-injection/contracts/statistical-result.schema.yaml`: Define fields `task_type`, `sigma`, `p_value`, `mean_diff`, `ci_lower`, `ci_upper`, `test_type` (t-test/Wilcoxon), `validity_collapse_point`.
- [X] T010d [P] Create `specs/001-lm-axive-noise-injection/contracts/validity-log.schema.yaml`: Define fields `task_type`, `sigma`, `pass_rate`, `collapse_point` (boolean), `semantic_drift_score`, `output_validity_score`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Baseline Latent Vector Extraction (Priority: P1) 🎯 MVP

**Goal**: Extract baseline "thought" token hidden states for the reasoning dataset to establish the control group.

**Independent Test**: Run extraction on a single task type; verify output CSV contains normalized vectors matching model hidden size and correct PairIDs.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T011 [P] [US1] Contract test for baseline output schema in `tests/contract/test_baseline_vectors.py`
- [X] T012 [P] [US1] Unit test for hidden state extraction logic in `tests/unit/test_extract_hidden.py`

### Implementation for User Story 1

- [X] T013 [US1] Extend `code/data_loader.py` to pair questions by task type and assign unique `PairID`s (output: `data/processed/pairing_config.json`)
- [X] T013b [US1] Implement dataset split logic in `code/data_loader.py`: **Explicitly create a reserved 'validation_subset' distinct from 'test_pairs'** for validity checks (Constitution Principle VI). Output `data/processed/validation_subset.json` and `data/processed/test_pairs.json`.
- [X] T015 [US1] Implement `code/main.py` baseline extraction loop: Load data -> Extract vectors -> Normalize (L2, base64 serialized) -> Validate dimensions -> Save to `data/processed/baseline_vectors.csv` (columns: `pair_id`, `task_type`, `vector_base64`, `norm_status`). **Depends on T008c for memory monitoring.**
- [X] T016 [US1] Implement `code/model_utils.py` function `normalize_vector(vector)`: Explicitly handle L2 normalization logic, ensuring unit length, and return the normalized vector. This task isolates the normalization logic previously merged into T015 to ensure distinct testing and verification.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Noise-Augmented Perturbation & Re-Extraction (Priority: P2)

**Goal**: Inject controlled Gaussian noise into input embeddings, project to nearest valid token, and re-extract latent vectors while enforcing semantic validity.

**Independent Test**: Inject known perturbation; verify embedding distance matches expected Euclidean distance and output retains ground truth (BERTScore ≥ 0.85).

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Unit test for noise injection and token projection math in `tests/unit/test_perturbation.py`
- [X] T019 [P] [US2] Contract test for validity log schema in `tests/contract/test_validity_log.py`

### Implementation for User Story 2

- [X] T020 [P] [US2] Implement `code/perturbation.py` function `inject_and_project(embedding, sigma, model_embedding_matrix)` that adds Gaussian noise and **projects to nearest valid token by minimizing Euclidean distance against model.embedding_matrix**, returning `perturbed_token_ids` and `perturbed_embeddings`
- [X] T021 [S] [US2] Implement `code/validity_check.py` function `check_input_drift(baseline_input, perturbed_input)`: **Instantiate a frozen `sentence-transformers/all-MiniLM-L6-v2` model as `GLOBAL_SBERT` singleton at module load time.** **Exclude pairs with cosine similarity < 0.95** and **MUST explicitly exclude these pairs from downstream statistical analysis**. Save the filtered set to `data/processed/filtered_pairs_input_drift.csv` with columns: `PairID`, `baseline_embedding_hash`, `perturbed_embedding_hash`, `drift_score`, `pass/fail`. **Mark as [S] to prevent concurrent access to the global singleton `GLOBAL_SBERT`, ensuring thread safety.** (FR-009). **Depends on `data/processed/baseline_vectors.csv` from T015.**
- [X] T022 [US2] Implement `code/validity_check.py` function `check_output_validity(model_output, expected_answer)` using BERTScore (F1 ≥ 0.85) and perplexity bound (≤ 2.0x baseline); **Assume `expected_answer` column exists (validated in T006); do NOT re-check or raise error here.** (FR-006). **Depends on T006.**
- [X] T023 [US2] Implement `code/validity_check.py` function `check_validity_collapse(pass_rate, threshold)` to detect if >90% of pairs fail at a specific $\sigma$
- [X] T024a [US2] Implement `code/main.py` noise sweep loop orchestration: Iterate $\sigma$ across a defined range. **Inside the loop:** (1) Call streaming logic (T008), (2) Perturb inputs (T020), (3) Extract vectors, (4) Run validity checks (T021, T022). **(5) AGGREGATE pass-rates across ALL task types for the current sigma to calculate the GLOBAL semantic validity pass-rate (FR-011).** **Wait for all task types to finish sigma X, THEN calculate global rate. If GLOBAL pass-rate < 10%, record 'validity collapse point' (global) to `data/processed/validity_log.csv` IMMEDIATELY and break the OUTER sigma-loop ENTIRELY (aborting all remaining task types and sigmas).** **Depends on T015 and T008c.**
- [X] T025 [US2] Save perturbed vectors and metadata to `data/processed/perturbed_vectors.csv` linked by `PairID` and `sigma`
- [X] T026 [US2] Implement logging for sweep progress: **MUST write to `data/processed/sweep.log` in JSON lines format with fields: `sigma`, `validity_rate`, `current_rss`, `pairs_processed`, `status`.** (FR-011, FR-007). **Depends on T024a.**

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Separability Analysis (Priority: P3)

**Goal**: Perform statistical hypothesis testing on the filtered pairs to determine if noise injection significantly increased latent separability.

**Independent Test**: Feed mock dataset with known difference; verify test selects correct distribution (t-test vs Wilcoxon) and reports correct p-value.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T027 [P] [US3] Unit test for normality check and test selection logic in `tests/unit/test_statistical_test.py`
- [X] T028 [P] [US3] Integration test for end-to-end analysis pipeline in `tests/integration/test_analysis.py`

### Implementation for User Story 3

- [X] T029 [P] [US3] Implement `code/analysis.py` function `calculate_pairwise_cosine_similarity(vectors, pair_ids)` to generate similarity distributions for baseline and perturbed sets
- [X] T030 [US3] Implement `code/analysis.py` function `generate_per_task_trade_off(task_results)`:
 - **Consume `data/processed/validity_log.csv`** to filter pairs (FR-009, FR-011).
 - Calculate the trade-off curve (perturbation magnitude vs. semantic validity pass-rate) for EACH task type.
 - **Save per-task trade-off curves to `data/processed/trade_off_curve.csv`** (FR-007, SC-002).
 - **Depends on `data/processed/validity_log.csv` from T024a.**
- [X] T030b [US3] Implement `code/analysis.py` function `aggregate_global_results(task_results)`:
 - Aggregate per-task trade-off curves and validity collapse points into a global distribution.
 - **Save global distribution to `data/processed/global_trade_off_curve.csv`**.
 - **Generate `data/processed/sensitivity_report.json`** containing the global distribution and validity collapse point distribution (SC-006).
 - **Handle 'No Valid Sigma' edge case by setting `validity_collapse_distribution: []`, `status: 'inconclusive'`, and reporting the trade-off curve.**
 - **Depends on T030.**
- [X] T031a [US3] Implement `code/main.py` analysis orchestration (Load & Filter): **Load `perturbed_vectors.csv` and `validity_log.csv`. Filter out all pairs where `sigma` >= `validity_collapse_point` for that task type (inclusive of the collapse point) using the validity log as the filter source.** Save filtered dataset to `data/processed/filtered_vectors_for_analysis.csv`. **Depends on T024a and T030.**
- [X] T031b [US3] Implement `code/main.py` analysis orchestration (Run Tests): Run statistical tests (paired t-test if normality holds and n ≥ 30; otherwise Wilcoxon signed-rank test) on the **filtered** dataset. **Verify sample size (n) before running; switch to Wilcoxon if n < 30 and report reduced power.** **Explicitly calculate and log `reduced_power_estimate` and include `power_warning: true` in `statistical_results.json` (FR-012).** (FR-005, FR-012).
- [X] T031c [US3] Implement `code/main.py` analysis orchestration (Correction): **Collect all p-values from all task types AND all sigma levels into a single list. Execute family-wise error correction using `statsmodels.stats.multitest.multipletests` with `method='holm'` on this combined list. Store the corrected p-values in a new column 'p_value_corrected' in the results dataframe.** (FR-005, SC-005).
- [X] T031d [US3] Implement `code/main.py` analysis orchestration (Generate Results): **Generate and save `data/processed/statistical_results.json`** with keys: `p_value`, `mean_diff`, `ci`, `validity_collapse_distribution`, `trade_off_curve`, `reduced_power_estimate`. **Include logic to flag "Significant Separability Increase" if corrected p-value (from `p_value_corrected` column) < 0.05.** **Depends on T030b and T031c.** (FR-005, SC-005).

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T034 [P] Documentation updates in `docs/` including **create `docs/quickstart.md`** with exact run commands for CPU-only execution
- [X] T035 Code cleanup and refactoring of `main.py` for clarity
- [ ] T036 Performance optimization for the perturbation sweep loop (vectorized operations where possible)
- [ ] T037 [P] Additional unit tests for edge cases (e.g., normality violation, no valid sigma) in `tests/unit/`
- [ ] T038 Security hardening: Ensure no PII leaks in logs or output files
- [X] T039 [P] Run `docs/quickstart.md` validation to verify end-to-end execution on a small subset

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

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
- **Note**: T021 is marked [S] (Serial) due to global SBERT model loading and thread safety requirements.

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
- **Resource Limits**: Strictly enforce a constrained RAM limit via `tracemalloc` and streaming/batching (T008, T008b, T008c).
- **CPU Constraint**: All model operations must be CPU-only; do not attempt CUDA offloading unless explicitly re-targeted to a GPU runner.
- **Revision Note**: T036 and T037 added to address performance optimization and edge-case robustness concerns raised in prior review cycles, specifically targeting the perturbation loop efficiency and statistical test failure modes.
- **Revision Note (Global Abort)**: T024a updated to enforce GLOBAL validity collapse logic across all task types, explicitly waiting for all task types to finish before checking the global rate.
- **Revision Note (Correction)**: T031c updated to explicitly execute Holm-Bonferroni correction using `statsmodels` and store results in `p_value_corrected` column.
- **Revision Note (Filtering)**: T031a added to explicitly filter invalid data before analysis using the validity log, with inclusive logic for the collapse point.
- **Revision Note (Model)**: T021 updated to mandate `all-MiniLM-L6-v2`, marked [S] for thread safety, and clarified singleton usage.
- **Revision Note (Streaming)**: T008 updated to mandate proactive streaming strategy.
- **Revision Note (Single Source of Truth)**: T022 updated to remove duplicate `expected_answer` check.
- **Revision Note (Sweep Log)**: T026 updated to explicitly list required JSON fields.
- **Revision Note (No Valid Sigma)**: T030b updated to handle 'No Valid Sigma' edge case in JSON output.
- **Revision Note (Memory Safety Net)**: T008b updated to clarify that streaming logic must be proactive and the check is a safety net.