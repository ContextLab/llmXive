# Tasks: llmXive follow-up: extending "MiniMax Sparse Attention"

**Input**: Design documents from `/specs/001-llmxive-sparse-attention-heuristics/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: Unit tests for heuristics and metrics are included as part of the implementation flow. Integration tests are included for the full RULER loop.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `data/`, `tests/` at repository root
- Paths shown below assume single project - adjusted based on `plan.md` structure

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001a [P] Create `code/`, `data/raw`, `data/processed`, `results`, `tests/unit`, `tests/integration` directories
- [X] T001b [P] Create `code/__init__.py`, `code/heuristics/__init__.py`, `code/eval/__init__.py`, `code/data/__init__.py`, `code/utils/__init__.py`
- [X] T001c [P] Create `tests/unit/__init__.py`, `tests/integration/__init__.py`
- [X] T002 Initialize Python 3.11 project with `requirements.txt` (dependencies: `transformers`, `torch`, `datasets`, `scipy`, `pandas`, `numpy`, `pytest`)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `code/utils/config.py` for seed pinning, threshold configs, and CPU device enforcement
- [X] T005 [P] Implement `code/utils/logger.py` for structured logging and memory/CPU usage tracking
- [X] T006 [P] Implement `code/data/loader.py` to fetch RULER dataset from HuggingFace `datasets` library (verified URL)
- [X] T037 [P] [Execution Order: Must run AFTER T006] Implement `code/data/loader.py` verification logic: Add a checksum validation step after downloading RULER data to `data/raw/` to ensure file integrity before processing. (Note: T006 must be executed before T037 within this parallel phase).
- [X] T007a [P] Implement `code/data/preprocess.py` chunking logic: `split_context(context, chunk_size)` returning generator of chunks.
- [X] T007b [P] Implement `code/data/preprocess.py` memory check: `check_memory_usage()` returning boolean if usage > 6.5 GB. [UNRESOLVED-CLAIM: c_3755c1bf — status=not_enough_info]
- [X] T007c [P] Implement `code/data/preprocess.py` batch reduction: `reduce_batch_size(batch)` returning smaller batch if memory check fails.
- [X] T007d [P] Implement `code/data/preprocess.py` exit logic: `exit_on_memory_exceeded()` raising RuntimeError with "Memory constraint exceeded" if all reduction modes fail.
- [X] T008 [P] Implement `code/heuristics/__init__.py` and base abstract class `HeuristicSelector`
- [X] T009 [P] [US1] Setup `tests/unit/test_heuristics.py` and `tests/unit/test_metrics.py` with failing placeholders: Implement `test_entropy_returns_float`, `test_gradient_returns_float`, `test_recency_returns_float` in `test_heuristics.py` and `test_exact_match_returns_float`, `test_f1_returns_float` in `test_metrics.py` with `assert False` to ensure they fail initially.
- [X] T048 [P] [US1] Implement `code/main.py` model loading mechanism: Use `transformers` pipeline with `device_map="cpu"` and manual layer sharding (or other valid methods) to ensure MiniMax-M3 fits within 7 GB RAM without 4-bit/8-bit quantization. [UNRESOLVED-CLAIM: c_db5c360d — status=not_enough_info] **CRITICAL**: Explicitly reiterate the "no quantization" constraint in the implementation.
- [X] T047 [P] [US1] Implement `code/main.py` context reduction logic: Check memory -> If exceeded, set config for reduced context (truncate input tokens) -> THEN load model. Must handle "reduce context to [deferred] tokens" clause of FR-003. **CRITICAL**: If reduction strategies fail, the system MUST explicitly `exit with code 1` and log the exact message "Memory constraint exceeded".

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - CPU-Feasible Heuristic Evaluation (Priority: P1) 🎯 MVP

**Goal**: Execute block-sparse attention selection logic using three deterministic heuristics on CPU-only environment without GPU.

**Independent Test**: Run `code/main.py` with `device="cpu"` and heuristic selection enabled on a small RULER subset; verify no CUDA errors and completion within 6 hours. [UNRESOLVED-CLAIM: c_49c84b72 — status=not_enough_info]

### Tests for User Story 1 (Must run BEFORE implementation)

- [X] T010 [P] [US1] Unit test for `code/heuristics/entropy.py` in `tests/unit/test_heuristics.py`: Implement `test_entropy_block_returns_expected` (asserting float output for known input) to verify Block Entropy calculation.
- [X] T011 [P] [US1] Unit test for `code/heuristics/gradient.py` in `tests/unit/test_heuristics.py`: Implement `test_gradient_norms_match_proxy_loss` (asserting gradient norms correlate with proxy loss) to verify Local Gradient Magnitude.
- [X] T012 [P] [US1] Unit test for `code/heuristics/recency.py` in `tests/unit/test_heuristics.py`: Implement `test_recency_bias_weights_sum_to_one` to verify Recency Bias weighting.

### Implementation for User Story 1

- [X] T018 [P] [US1] {{claim:c_bfbc14f8}} Must include `test_fallback_selects_first_k_when_scores_zero` in `tests/unit/test_heuristics.py`.
- [X] T017a [P] [US1] Implement `code/main.py` model loading logic: Load MiniMax-M3 (frozen) using T048 mechanism.
- [X] T017b [P] [US1] Implement `code/main.py` Dense Attention mode: Implement "Dense Attention mode (full context, no sparsity, no Index Branch)" as the baseline for comparison, aligning with the Plan's definition. This replaces the ambiguous "disable Index Branch" description.
- [X] T017c [P] [US1] Implement `code/main.py` heuristic routing logic: Route to T018 fallback if scores are near-zero, otherwise route to heuristics. (Depends on T018).
- [X] T014 [P] [US1] Implement `code/heuristics/entropy.py`: Calculate block entropy from attention logits
- [X] T015 [P] [US1] Implement `code/heuristics/gradient.py`: Compute local gradient magnitude via proxy next-token prediction loss (frozen model)
- [X] T016 [P] [US1] Implement `code/heuristics/recency.py`: Apply recency bias weighting to block selection
- [X] T019 [DEPRECATED] [US1] Implement memory guard in `code/main.py` using `psutil.virtual_memory().percent`: (Logic superseded by T040; kept for reference only. Original requirement: If > 85% of 7 GB, dynamically switch between reducing context to 4096 tokens (first priority) OR reducing batch size to 1 (second priority) [UNRESOLVED-CLAIM: c_f63b8ac5 — status=not_enough_info]; exit with code 1 only if both modes fail, logging "Memory constraint exceeded".)

**Checkpoint**: US1 fully functional; heuristics run on CPU without errors.

---

## Phase 4: User Story 2 - Retrieval Accuracy & Perplexity Benchmarking (Priority: P2)

**Goal**: Measure retrieval accuracy (Exact Match/F1) and perplexity of heuristics against the Dense Attention baseline.

**Independent Test**: Compare F1 scores of "Block Entropy" vs "Dense Attention" on the same RULER task subset; verify delta is reported.

### Tests for User Story 2

- [X] T020 [P] [US2] Unit test for `code/eval/metrics.py` (Exact Match, F1, Perplexity calculators) in `tests/unit/test_metrics.py`

### Implementation for User Story 2

- [X] T021b [P] [US2] Implement `code/eval/metrics.py` proxy loss calculation: Calculate perplexity on a frozen model using a proxy next-token prediction loss (cross-entropy) without backpropagation. [UNRESOLVED-CLAIM: c_965220c2 — status=not_enough_info]
- [X] T021 [P] [US2] Implement `code/eval/metrics.py`: Functions to calculate Exact Match, F1, and Perplexity (depends on T021b)
- [X] T022c [US2] Implement `code/eval/baseline_runner.py`: A dedicated runner that executes the model in "Dense Attention" mode (Full Context, no sparsity, no Index Branch) to generate the ground truth selection set and baseline metrics for comparison, satisfying FR-004.
- [ ] T024 [US2] Implement result aggregation to write `results/benchmark_report.json` with F1, PPL, and delta vs Dense Attention baseline for each heuristic. **Schema Requirement**: Must include all keys: `f1_score`, `p_value`, `false_positive_rate`, `sensitivity_table`, `ttest_stat`, `wilcoxon_stat`, `significance_statement`. (Note: This schema is the source of truth and must include all keys required by T031).
- [X] T023a [US2] Integrate heuristic runner in `code/main.py` to execute heuristics and generate selection sets.
- [X] T023b [US2] Integrate metric calculator in `code/main.py` to compute metrics using T021/T021b.
- [X] T023c [US2] Implement output formatting in `code/main.py` to structure results for T024.
- [X] T023 [US2] Integrate heuristic execution with metric calculation in `code/main.py` to output results per task, comparing against T022c's Dense Attention baseline. (Depends on T024, T022c, T021b)
- [ ] T025 [US2] Add logging for exclusion counts if RULER dataset samples are corrupted or missing "needle" strings

**Checkpoint**: US2 complete; accuracy and perplexity measured against baseline.

---

## Phase 5: User Story 3 - Statistical Significance & Sensitivity Analysis (Priority: P3)

**Goal**: Perform Paired t-test (Primary per Plan/Constitution) and Wilcoxon signed-rank test (Secondary per Spec) and sensitivity analysis on selection thresholds.

**Independent Test**: Run analysis script outputting p-value for Paired t-test and a table of accuracy variance across thresholds representing varying levels of statistical significance.

### Tests for User Story 3

- [X] T026b [P] [US3] Unit test for `code/eval/statistical.py` (Wilcoxon, Paired t-test) in `tests/unit/test_statistical.py`: Implement `test_wilcoxon_returns_p_value`, `test_ttest_returns_p_value`, `test_holm_bonferroni_corrects_p_values` with specific assertions.

### Implementation for User Story 3

- [X] T027 [P] [US3] Implement `code/eval/statistical.py`: **PRIMARY** Wilcoxon signed-rank test (per Spec FR-005/SC-003) AND **SECONDARY** Paired t-test with **Holm-Bonferroni correction** (per Constitution Principle VII and Plan). Both tests must be executed as mandatory outputs.
- [X] T027b [P] [US3] Implement `code/eval/statistical.py`: Wilcoxon as primary output (per Spec FR-005) with Holm-Bonferroni correction applied if multiple comparisons are made, and Paired t-test as secondary robustness check.
- [X] T028 [P] [US3] Implement `code/eval/statistical.py`: Sensitivity sweep logic across a range of thresholds mapping to: 'normalized attention score' for Recency, 'gradient magnitude threshold' for Gradient Magnitude, and 'entropy probability cutoff' for Block Entropy.
- [X] T029 [US3] {{claim:c_7c5336b9}} (Note: T028 already includes these thresholds as a strict constraint).
- [ ] T032a [US3] Implement logic to calculate false-positive rates during sensitivity analysis: Compare heuristic selection set vs. Dense Attention baseline selection set (from T022c) to identify blocks selected by heuristic but NOT by baseline (false positives).
- [ ] T032b [US3] Ensure `false_positive_rate` is explicitly calculated and written to `results/benchmark_report.json` for each threshold in the sensitivity sweep, verifying SC-004.
- [ ] T030a [US3] Implement statistical test runner in `code/main.py` to execute T027/T027b tests.
- [ ] T030b [US3] Implement report prioritization logic in `code/main.py` to prioritize Paired t-test p-values in the report (per Constitution), while including Wilcoxon results as secondary checks.
- [X] T030 [US3] Integrate statistical tests into `code/main.py` to compare best heuristic vs Dense Attention baseline (from T022c), prioritizing Paired t-test p-values in the report. (Depends on T032b, T030a, T030b)
- [ ] T031 [US3] Generate final `results/benchmark_report.json` updates including p-values (Paired t-test primary), significance statements, and sensitivity tables. Format: `{"p_value": float, "significance_statement": "p < 0.05" or "p >= 0.05", "sensitivity_table": [{"threshold": float, "accuracy": float, "false_positive_rate": float}]}`. (Note: Must include all keys from T024 schema: `f1_score`, `p_value`, `false_positive_rate`, `sensitivity_table`, `ttest_stat`, `wilcoxon_stat`, `significance_statement`).
- [X] T032a [US3] Implement logic to calculate false-positive rates during sensitivity analysis (selection without target vs Dense Attention selection from T022c). (Replaced by refined T032a above)
- [X] T032b [US3] Ensure `false_positive_rate` is explicitly calculated and written to `results/benchmark_report.json` for each threshold in the sensitivity sweep, verifying SC-004. (Replaced by refined T032b above)

**Checkpoint**: All user stories complete; statistical validation and robustness checks implemented.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T033 [P] Documentation updates: Add `quickstart.md` with CPU-only execution instructions
- [ ] T035 [P] Run full `pytest` suite on CPU-only runner to verify all tests pass
- [ ] T036 Verify `results/benchmark_report.json` contains all required metrics and statistical tests, specifically checking for keys: `f1_score`, `p_value`, `false_positive_rate`, `sensitivity_table`, `ttest_stat`, `wilcoxon_stat`, `significance_statement`.

---

## Phase 7: Resource Constraint Validation (Revision)

**Purpose**: Address reviewer concerns regarding strict adherence to 7GB RAM and 6-hour time limits (Review Concern: "Compute feasibility")

- [X] T040 [P] [US1] Implement `code/utils/resource_monitor.py`: A background thread that logs RAM usage at regular intervals and triggers an early exit with a failure code if usage exceeds a predefined safety threshold below the system limit. to prevent OOM crashes. (Supersedes T019).
- [ ] T041 [US1] Add a "Timeout Guard" to `code/main.py`: Implement signal-based timeout of 21600 seconds (6 hours) to forcibly terminate the process if the RULER subset run exceeds the time threshold.
- [X] T042 [P] [US3] Implement a "Batch Size Auto-Reducer" in `code/data/preprocess.py`: If a single batch causes memory pressure, automatically split the batch into smaller chunks (size reduced to unit level) and re-aggregate results, logging the auto-reduction event.

---

## Phase 8: Data Integrity & Streaming Robustness (Revision)

**Purpose**: Address reviewer concerns regarding "Real data + real results only" and "Loader must fail loudly" (Review Concern: "Data Hygiene & Fabrication Gate")

- [ ] T043 [P] [US1] Refactor `code/data/loader.py` to REMOVE any `try/except` blocks that catch download failures and fall back to `generate_synthetic_*()` or `mock_*()` functions; ensure that any failure to fetch the RULER dataset from the verified HuggingFace URL raises a `RuntimeError` immediately. **CRITICAL**: The refactored loader MUST enforce the 'checksum validation' step required by Constitution Principle III before returning data.
- [ ] T044 [P] [US2] Implement `code/data/streaming_chunker.py` to handle the RULER dataset using `datasets.load_dataset(..., streaming=True)` to process the full dataset in chunks without loading it all into RAM, ensuring compliance with FR-007 and SC-002. API: `stream_chunker(dataset, chunk_size)` returning generator.
- [ ] T045 [US2] Add a "Data Source Verification" task in `code/main.py`: Implement `verify_needle_presence(sample)` function that checks for the presence of the "needle" string in the loaded sample before processing; if the needle is missing, **log a warning** and skip the sample, updating the exclusion count in `results/benchmark_report.json`.
- [ ] T046 [US3] Implement a "Sample Representativeness" check in `code/eval/statistical.py`: Add field `sampling_method` to `results/benchmark_report.json` documenting the exact number of rows processed and the sampling method (streaming vs. fixed seed random sample) to satisfy SC-004 requirements for transparency. (Depends on T045 for exclusion count).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
 - **Note**: T037 (Loader Verification) is now in Phase 2 to ensure data integrity before any data consumption. T006 must be executed before T037.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Revision Phases (7 & 8)**: Can be implemented in parallel with US2/US3 implementation but must be completed before final validation.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires US1 heuristics to be implemented
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires US2 results to be generated

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Heuristics models before integration
- Core implementation before statistical analysis
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if staffed)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members
- Revision tasks (T037-T046) can run in parallel with US2/US3 implementation as they focus on specific validation logic.

### Specific Task Dependencies

- **T047 -> T017**: Context reduction (T047) must be complete before model loading (T017a).
- **T048 -> T017**: Model loading mechanism (T048) must be complete before model loading (T017a).
- **T022c -> T023**: Baseline runner (T022c) must be complete before integration (T023).
- **T024 + T022c + T021b -> T023**: Integration (T023) requires aggregation schema (T024), baseline (T022c), and proxy loss (T021b).
- **T024 + T022c + T021b + T023 -> T030**: Statistical integration (T030) requires heuristic results (T023), aggregation schema (T024), baseline (T022c), and proxy loss (T021b).
- **T031 + T024 + T032b -> T036**: Verification (T036) requires the final report generation (T031) and all metric calculations.
- **T043 -> T044**: Data loader refactoring (T043) must be complete before implementing the streaming chunker (T044) to ensure no synthetic fallbacks are introduced.
- **T045 -> T046**: Data source verification (T045) must be complete before implementing the sample representativeness check (T046) to ensure the sample is valid.
- **T032a -> T032b -> T030**: False positive calculation (T032a) must precede writing (T032b), which must precede statistical integration (T030).

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Unit test for entropy.py in tests/unit/test_heuristics.py"
Task: "Unit test for gradient.py in tests/unit/test_heuristics.py"
Task: "Unit test for recency.py in tests/unit/test_heuristics.py"

# Launch all heuristic implementations together (AFTER tests are ready):
Task: "Implement Block Entropy in code/heuristics/entropy.py"
Task: "Implement Local Gradient Magnitude in code/heuristics/gradient.py"
Task: "Implement Recency Bias in code/heuristics/recency.py"

# NOTE: While tests and implementations can be developed in parallel by different people,
# the execution order is strict: Tests MUST fail before Implementation begins.
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (CPU execution, no errors)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Heuristics)
 - Developer B: User Story 2 (Metrics & Baseline)
 - Developer C: User Story 3 (Statistical Analysis)
 - Developer D: Revision Tasks (Data Integrity & Resource Validation)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Constraint**: All tasks must run on a multi-core CPU, sufficient RAM, no GPU. No -bit/4-bit quantization.
- **Data Integrity**: All data must be fetched from real sources (HuggingFace RULER). No synthetic data generation.
- **Statistical Priority**: **Wilcoxon signed-rank test** is the PRIMARY method per Spec FR-005; **Paired t-test** is SECONDARY per Plan/Constitution. Both must be executed.
- **Baseline Priority**: **Dense Attention (Full Context)** is the ground truth baseline (T022c). The Learned Index Branch must remain DISABLED.
- **Memory Buffer**: Task T040 uses a 6.5 GB exit trigger as a documented safety buffer below the 7 GB spec limit (FR-007) to prevent OOM crashes on the runner.
- **Deprecated**: Task T019 is deprecated; its logic is superseded by T040.
- **Revision Concerns**: Phase 8 tasks (T043-T046) address specific reviewer concerns regarding data hygiene and streaming robustness to prevent fabrication and ensure real data usage.
- **Threshold Constraint**: T028 explicitly mandates thresholds {0.01, 0.05, 0.1} for sensitivity analysis.
- **Error Handling**: T047 explicitly mandates 'exit with code 1' and 'Memory constraint exceeded' log message.
- **Warning Log**: T045 explicitly mandates 'log a warning' for missing needle strings.
- **Holm-Bonferroni**: T027/T027b explicitly mandate Holm-Bonferroni correction for multiple comparisons.
- **Checksum Validation**: T043 explicitly mandates enforcing checksum validation in the loader.