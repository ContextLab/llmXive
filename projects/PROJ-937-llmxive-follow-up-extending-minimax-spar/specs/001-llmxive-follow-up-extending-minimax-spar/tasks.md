# Tasks: llmXive follow-up: extending "MiniMax Sparse Attention"

**Input**: Design documents from `/specs/001-llmxive-sparse-attention-heuristics/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: Unit tests for heuristics and metrics are included as part of the implementation flow. Integration tests are included for the full RULER loop.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]****: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `data/`, `tests/` at repository root
- Paths shown below assume single project - adjusted based on `plan.md` structure

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per `plan.md` (directories: `code/`, `data/raw`, `data/processed`, `results`, `tests/unit`, `tests/integration`)
- [ ] T002 Initialize Python 3.11 project with `requirements.txt` (dependencies: `transformers`, `torch`, `datasets`, `scipy`, `pandas`, `numpy`, `pytest`)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `code/utils/config.py` for seed pinning, threshold configs, and CPU device enforcement
- [ ] T005 [P] Implement `code/utils/logger.py` for structured logging and memory/CPU usage tracking
- [ ] T006 [P] Implement `code/data/loader.py` to fetch RULER dataset from HuggingFace `datasets` library (verified URL)
- [X] T037 [P] [US1] Implement `code/data/loader.py` verification logic: Add a checksum validation step after downloading RULER data to `data/raw/` to ensure file integrity before processing. (Moved from Phase 7 to ensure data integrity before consumption)
- [ ] T007 Implement `code/data/preprocess.py` for streaming chunking logic with dynamic fallback: 1) Attempt to reduce context window to a constrained length; 2) If memory still exceeds available capacity, Reduce batch size to a minimal value.; 3) Only exit with code 1 if both modes fail.
- [X] T008 [P] Implement `code/heuristics/__init__.py` and base abstract class `HeuristicSelector`
- [~] T009 [P] [US1] Setup `tests/unit/test_heuristics.py` and `tests/unit/test_metrics.py` with failing placeholders: Implement `test_entropy_returns_float`, `test_gradient_returns_float`, `test_recency_returns_float` in `test_heuristics.py` and `test_exact_match_returns_float`, `test_f1_returns_float` in `test_metrics.py` with `assert False` to ensure they fail initially.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - CPU-Feasible Heuristic Evaluation (Priority: P1) 🎯 MVP

**Goal**: Execute block-sparse attention selection logic using three deterministic heuristics on CPU-only environment without GPU.

**Independent Test**: Run `code/main.py` with `device="cpu"` and heuristic selection enabled on a small RULER subset; verify no CUDA errors and completion within 6 hours.

### Tests for User Story 1 (Must run BEFORE implementation)

- [~] T010 [P] [US1] Unit test for `code/heuristics/entropy.py` in `tests/unit/test_heuristics.py`: Implement `test_entropy_block_100_returns_0.5` (asserting specific float output for known input) to verify Block Entropy calculation.
- [~] T011 [P] [US1] Unit test for `code/heuristics/gradient.py` in `tests/unit/test_heuristics.py`: Implement `test_gradient_norms_match_proxy_loss` (asserting gradient norms correlate with proxy loss) to verify Local Gradient Magnitude.
- [~] T012 [P] [US1] Unit test for `code/heuristics/recency.py` in `tests/unit/test_heuristics.py`: Implement `test_recency_bias_weights_sum_to_one` to verify Recency Bias weighting.

### Implementation for User Story 1

- [ ] T014 [P] [US1] Implement `code/heuristics/entropy.py`: Calculate block entropy from attention logits
- [ ] T015 [P] [US1] Implement `code/heuristics/gradient.py`: Compute local gradient magnitude via proxy next-token prediction loss (frozen model)
- [ ] T016 [P] [US1] Implement `code/heuristics/recency.py`: Apply recency bias weighting to block selection
- [ ] T017 [US1] Implement `code/main.py`: Entry point to load MiniMax-M3 (frozen), disable Index Branch, and route to heuristics
- [ ] T018 [US1] Implement fallback logic in `code/heuristics/` to select first k blocks if all scores are near-zero
- [ ] T019 [DEPRECATED] [US1] Implement memory guard in `code/main.py` using `psutil.virtual_memory().percent`: (Logic superseded by T040; kept for reference only. Original requirement: If > 85% of 7 GB, dynamically switch between reducing context to 4096 tokens (first priority) OR reducing batch size to 1 (second priority); exit with code 1 only if both modes fail, logging "Memory constraint exceeded".)

**Checkpoint**: US1 fully functional; heuristics run on CPU without errors.

---

## Phase 4: User Story 2 - Retrieval Accuracy & Perplexity Benchmarking (Priority: P2)

**Goal**: Measure retrieval accuracy (Exact Match/F1) and perplexity of heuristics against the Dense Attention baseline.

**Independent Test**: Compare F1 scores of "Block Entropy" vs "Dense Attention" on the same RULER task subset; verify delta is reported.

### Tests for User Story 2

- [ ] T020 [P] [US2] Unit test for `code/eval/metrics.py` (Exact Match, F1, Perplexity calculators) in `tests/unit/test_metrics.py`

### Implementation for User Story 2

- [ ] T021 [P] [US2] Implement `code/eval/metrics.py`: Functions to calculate Exact Match, F1, and Perplexity
- [ ] T022 [US2] Implement `code/main.py` logic to run "Dense Attention" baseline (Full Context) for ground truth comparison
- [ ] T022c [US2] Implement `code/eval/baseline_runner.py`: A dedicated runner that executes the model in "Dense Attention" mode (Full Context, no sparsity, no Index Branch) to generate the ground truth selection set and baseline metrics for comparison, satisfying FR-004. (Replaces T022b to ensure compliance with FR-001).
- [ ] T023 [US2] Integrate heuristic execution with metric calculation in `code/main.py` to output results per task, comparing against T022c's Dense Attention baseline.
- [ ] T024 [US2] Implement result aggregation to write `results/benchmark_report.json` with F1, PPL, and delta vs Dense Attention baseline for each heuristic
- [ ] T025 [US2] Add logging for exclusion counts if RULER dataset samples are corrupted or missing "needle" strings

**Checkpoint**: US2 complete; accuracy and perplexity measured against baseline.

---

## Phase 5: User Story 3 - Statistical Significance & Sensitivity Analysis (Priority: P3)

**Goal**: Perform Paired t-test (Primary per Plan/Constitution) and Wilcoxon signed-rank test (Secondary per Spec) and sensitivity analysis on selection thresholds.

**Independent Test**: Run analysis script outputting p-value for Paired t-test and a table of accuracy variance across thresholds representing varying levels of statistical significance.

### Tests for User Story 3

- [ ] T026b [P] [US3] Unit test for `code/eval/statistical.py` (Wilcoxon, Paired t-test) in `tests/unit/test_statistical.py`: Implement `test_wilcoxon_returns_p_value`, `test_ttest_returns_p_value`, `test_holm_bonferroni_corrects_p_values` with specific assertions.

### Implementation for User Story 3

- [ ] T027 [P] [US3] Implement `code/eval/statistical.py`: **Primary** Paired t-test with Holm-Bonferroni correction (per Constitution Principle VII and Plan); **Secondary** Wilcoxon signed-rank test for robustness check (per FR-005 fallback).
- [ ] T028 [P] [US3] Implement `code/eval/statistical.py`: Sensitivity sweep logic across thresholds {0.01, 0.05, 0.1}
- [ ] T029 [US3] Implement `code/eval/statistical.py`: Sensitivity sweep logic across thresholds {0.01, 0.05, 0.1} mapping to: 'normalized attention score' for Recency, 'gradient magnitude threshold' for Gradient Magnitude, and 'entropy probability cutoff' for Block Entropy.
- [ ] T030 [US3] Integrate statistical tests into `code/main.py` to compare best heuristic vs Dense Attention baseline (from T022c), prioritizing Paired t-test p-values in the report.
- [ ] T031 [US3] Generate final `results/benchmark_report.json` updates including p-values (Paired t-test primary), significance statements, and sensitivity tables.
- [ ] T032a [US3] Implement logic to calculate false-positive rates during sensitivity analysis (selection without target vs Dense Attention selection from T022c).
- [ ] T032b [US3] Ensure `false_positive_rate` is explicitly calculated and written to `results/benchmark_report.json` for each threshold in the sensitivity sweep, verifying SC-004.

**Checkpoint**: All user stories complete; statistical validation and robustness checks implemented.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T033 [P] Documentation updates: Add `quickstart.md` with CPU-only execution instructions
- [ ] T035 [P] Run full `pytest` suite on CPU-only runner to verify all tests pass
- [ ] T036 Verify `results/benchmark_report.json` contains all required metrics and statistical tests, specifically checking for keys: `f1_score`, `p_value`, `false_positive_rate`, `sensitivity_table`, `ttest_stat`, `wilcoxon_stat`.

---

## Phase 7: Resource Constraint Validation (Revision)

**Purpose**: Address reviewer concerns regarding strict adherence to 7GB RAM and 6-hour time limits (Review Concern: "Compute feasibility")

- [ ] T040 [P] [US1] Implement `code/utils/resource_monitor.py`: A background thread that logs RAM usage at regular intervals and triggers an early exit with a failure code if usage exceeds 6.5 GB (documented safety buffer below GB limit) to prevent OOM crashes. (Supersedes T019).
- [ ] T041 [US1] Add a "Timeout Guard" to `code/main.py`: Use `signal` or a subprocess wrapper to forcibly terminate the process if the RULER subset run exceeds a predefined time threshold, ensuring the -hour CI limit is respected.
- [ ] T042 [P] [US3] Implement a "Batch Size Auto-Reducer" in `code/data/preprocess.py`: If a single batch causes memory pressure, automatically split the batch into smaller chunks (size 1) and re-aggregate results, logging the auto-reduction event.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
 - **Note**: T037 (Loader Verification) is now in Phase 2 to ensure data integrity before any data consumption.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Revision Phases (7)**: Can be implemented in parallel with US2/US3 implementation but must be completed before final validation.

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
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members
- Revision tasks (T037-T042) can run in parallel with US2/US3 implementation as they focus on specific validation logic.

### Specific Task Dependencies

- **T007 -> T040**: Resource monitor (T040) relies on the chunking logic defined in T007. (T019 is deprecated).
- **T022c -> T023**: Baseline runner (T022c) must be complete before integration (T023).
- **T024 + T022c -> T030**: Statistical integration (T030) requires both heuristic results (T024) and baseline metrics (T022c).
- **T031 + T024 + T032b -> T036**: Verification (T036) requires the final report generation (T031) and all metric calculations.

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
- **Critical Constraint**: All tasks must run on a multi-core CPU, 7 GB RAM, no GPU. No 8-bit/4-bit quantization.
- **Data Integrity**: All data must be fetched from real sources (HuggingFace RULER). No synthetic data generation.
- **Statistical Priority**: **Paired t-test** is the PRIMARY method per Constitution Principle VII and Plan; Wilcoxon is SECONDARY.
- **Baseline Priority**: **Dense Attention (Full Context)** is the ground truth baseline (T022c). The Learned Index Branch must remain DISABLED.
- **Memory Buffer**: Task T040 uses a 6.5 GB exit trigger as a documented safety buffer below the 7 GB spec limit (FR-007) to prevent OOM crashes on the runner.
- **Deprecated**: Task T019 is deprecated; its logic is superseded by T040.