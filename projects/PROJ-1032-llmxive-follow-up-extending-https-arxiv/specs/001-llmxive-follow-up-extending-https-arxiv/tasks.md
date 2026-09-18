# Tasks: llmXive Follow-up: Extending Asynchronous RL Staleness Bounds for Low-Capacity Models

**Input**: Design documents from `/specs/001-llmxive-staleness-scaling/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: Tests are included for US1, US2, and US3 as requested in the specification to ensure reproducibility and statistical validity.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- Paths shown below assume single project structure as defined in `plan.md`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per `plan.md` (src/llmxive, src/cli, src/utils, tests/, data/)
- [X] T002 Initialize Python 3.11 project with `requirements.txt` (transformers, datasets, torch, bitsandbytes, scipy, numpy, accelerate, lifelines)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `src/llmxive/config.py` for loading staleness, seeds, and model configurations; includes deterministic seed sequence management (FR-004).
- [X] T005a [P] Define custom exceptions in `src/llmxive/exceptions.py`: `DATA_INTEGRITY_ERROR`, `ERR_CPU_LOAD_FAIL`, `STALENESS_OVERFLOW` (for executability of T005, T006, T007)
- [X] T005 Implement `src/llmxive/data_loader.py` to stream GSM8K from `openai/gsm8k` with checksum verification; MUST raise `DATA_INTEGRITY_ERROR` (from T005a) on truncation (FR-006, Edge Case)
- [X] T005b [P] Implement `src/llmxive/data_loader.py` (FR-006 compliance): Assert no overlap between training staleness queue indices and test set indices before training begins; raise `DATA_INTEGRITY_ERROR` if overlap detected.
- [X] T006 Implement `src/llmxive/model_factory.py` to load Phi-2 and Qwen1.5-1.8B with 8-bit CPU quantization; MUST raise `ERR_CPU_LOAD_FAIL` (from T005a) if OOM (FR-001, Edge Case)
- [X] T007 Implement `src/llmxive/staleness_queue.py` to buffer gradients; MUST clamp staleness to `buffer_size - 1` if exceeded (Edge Case)
- [X] T008 Implement `src/utils/logging.py` for structured JSON logging to `data/processed/`
- [X] T009 Implement `src/llmxive/metrics.py` for real-time reward and gradient norm monitoring (excluding baseline loading logic)
- [X] T035 [P] [US1] Refactor `src/llmxive/data_loader.py` to remove any implicit `try/except` blocks that might catch `datasets` download errors and fall back to `generate_synthetic_*` or `mock_*` functions. Ensure the loader raises `DATA_INTEGRITY_ERROR` immediately on any fetch failure, allowing the execution stage to detect the issue and retry with a verified source.
- [X] T036 [P] [US1] Add explicit unit tests in `tests/unit/test_data_loader.py` to verify that `data_loader.py` raises `DATA_INTEGRITY_ERROR` when `datasets.load_dataset` fails, ensuring no silent fallback occurs.
- [X] T037 [P] [US1] Implement a "Verified Source" check in `src/llmxive/config.py`: If the execution environment provides a "VERIFIED REAL DATA SOURCE" block (e.g., a specific package or URL), the loader MUST adopt this source exclusively and ignore any default `openai/gsm8k` configuration.
- [X] T038 [P] [US1] Add a `streaming=True` flag enforcement in `src/llmxive/data_loader.py** to ensure GSM8K is processed in chunks, preventing OOM on a resource-constrained runner with limited RAM. Verify that the loader does not attempt to load the full dataset into memory.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Reproducible CPU-Only Training Loop with Configurable Staleness (Priority: P1) 🎯 MVP

**Goal**: Execute an asynchronous RL training loop on CPU with configurable staleness for Phi-2 and Qwen1.5-1.8B.

**Independent Test**: The system can be tested by running a single training job with a fixed staleness value and verifying that the training log outputs a sequence of reward values and gradient norms without crashing due to OOM or CUDA errors. [UNRESOLVED-CLAIM: c_603e3ecf — status=not_enough_info]

### Baseline Generation & Seed Management (Critical Prerequisites for US1 Divergence Logic)
**⚠️ CRITICAL**: These tasks MUST be completed and executed before T013 (Async Trainer) or T020/T021 (Divergence Logic).

- [ ] T016 [P] [US1] Implement deterministic seed sequence generator and stability validator in `src/llmxive/seed_manager.py`. Logic must manage the pre-defined integer sequence (e.,g., 1-5), verify stability of the synchronous baseline for each seed, and handle the discard-and-retry logic per FR-004. **Output**: `data/processed/seed_audit.json` containing `discarded_seeds`, `reasons` (variance > 5% of mean), and `final_sequence`.
- [X] T019a [US1/US2] Implement `src/llmxive/baseline_generator.py`: Logic to perform synchronous run, compute static mean reward/gradient of the **first 50 steps**, verify stability (variance < 5% of mean calculated over the first 50 steps), and save manifest. MUST verify seed stability before saving. If unstable, **discard** and **retry** with the next seed in the pre-defined integer sequence. **Max retry limit**: Infinite (bounded only by total seed pool size) to guarantee 5 valid runs per FR-004. **Output Artifact**: `data/processed/baseline_manifests/{seed}.json` containing `mean_reward`, `mean_grad_norm`, `status`, `seed_id`.
- [ ] T019b [US1/US2] Implement `src/llmxive/baseline_orchestrator.py`: Logic to orchestrate the generation of baseline manifests for all required seeds. This task implements the loop that calls `baseline_generator.py` (T019a) for each seed in the sequence, handles the retry logic defined in T019a, and ensures all 5 valid manifests are generated before proceeding. This task provides the *orchestration logic* but does NOT execute the runs itself; T019c/T019d execute the runs.
- [ ] T019c [US1/US2] [P] Execute synchronous baseline runs for a small-scale language model across multiple seeds using `src/llmxive/baseline_orchestrator.py`. Generates `data/processed/baseline_manifests/phi2_{seed}.json`.
- [ ] T019d [US1/US2] [P] Execute synchronous baseline runs for Qwen across 5 seeds using `src/llmxive/baseline_orchestrator.py`. Generates `data/processed/baseline_manifests/qwen15_{seed}.json`.
- [X] T020 [US1/US2] Implement `src/llmxive/baseline_loader.py`: Logic to load and validate the pre-computed manifest from `data/processed/baseline_manifests/{seed}.json` (generated by T019a/T019b).
- [X] T021 [US1/US2] Implement `src/llmxive/baseline_loader.py` (FR-004 compliance): Read the manifest from T019a for the current seed and verify `variance < 5% of mean` before proceeding with async runs; discard seed if unstable.
- [X] T022 [US1/US2] Implement the discard-and-retry loop logic: Handle unstable seeds by selecting the next seed in the sequence (incrementing integer index) and calling the generation logic in `src/llmxive/baseline_generator.py` (T019a) for that specific seed. **Constraint**: Max attempts per seed slot removed; infinite retry until 5 valid seeds are found (FR-004). **Input**: `data/processed/baseline_manifests/{seed}.json`. **Output**: Updated manifest or `DATA_INTEGRITY_ERROR` if pool exhausted.

**Checkpoint**: Baseline generation and stability logic complete.

### Implementation for User Story 1

- [ ] T014 [US1] [P] Integrate `src/llmxive/staleness_queue.py` (T007) into the training loop logic. This task ensures the queue is correctly instantiated and configured for the trainer.
- [ ] T013 [US1] Implement `src/llmxive/trainer.py` main RL loop with `device="cpu"`, `bitsandbytes` quantization, and integrated `staleness_queue` (FR-001, FR-002).
 *Dependency*: T007, T014, T020 (Baseline Loading), T021 (Stability Check), T022 (Retry Logic), **T019a (Baseline Generator)**, and **T019b (Orchestrator)** MUST be completed first to provide thresholds and valid seeds for FR-003.
 *Note*: This task includes the integration of the staleness queue as the trainer cannot function without it.
- [ ] T015 [US1] Add memory monitoring in `trainer.py` to log peak RAM usage and abort if > 6.5 GB (FR-001, SC-004)
- [ ] T017 [US1] Add logging for `model_id`, `staleness_level`, `seed`, and `reward_curve` to JSON manifests (FR-003)
- [ ] T013b [US1] [P] Execute multiple independent training runs for Low Staleness regime for Phi-2 (1.4B) using T013. Generates `data/processed/logs/phi2_low_{seed}.json`.
- [ ] T013c [US1] [P] Execute multiple independent training runs for High Staleness regime for Phi-2 (1.4B) using T013. Generates `data/processed/logs/phi2_high_{seed}.json`.
- [ ] T013d [US1] [P] Execute multiple independent training runs for Adaptive Staleness regime for Phi-2 (1.4B) using T013. Generates `data/processed/logs/phi2_adaptive_{seed}.json`.
- [ ] T013e [US1] [P] Execute multiple independent training runs for Low Staleness regime for Qwen1.5-1.8B using T013. Generates `data/processed/logs/qwen15_low_{seed}.json`.
- [ ] T013f [US1] [P] Execute multiple independent training runs for High Staleness regime for Qwen1.5-1.8B using T013. Generates `data/processed/logs/qwen15_high_{seed}.json`.
- [ ] T013g [US1] [P] Execute multiple independent training runs for Adaptive Staleness regime for Qwen1.5-1.8B using T013. Generates `data/processed/logs/qwen15_adaptive_{seed}.json`.

### Tests for User Story 1

- [ ] T010 [P] [US1] Unit test for `staleness_queue.py` in `tests/unit/test_staleness_queue.py` (verify clamping logic)
- [ ] T011 [P] [US1] Integration test for CPU model loading in `tests/integration/test_cpu_load.py` (verify no CUDA fallback)
- [ ] T012 [P] [US1] Integration test for training loop with `staleness=0` in `tests/integration/test_sync_loop.py` (verify 500 steps < 45 mins, no OOM)

**Checkpoint**: At this point, User Story 1 (including baseline generation) should be fully functional and testable independently

---

## Phase 4: User Story 2 - Divergence Detection and Threshold Mapping (Priority: P2)

**Goal**: Automatically detect divergence based on intrinsic thresholds and map staleness bounds per model.

**Independent Test**: The system can be tested by feeding a pre-generated log file with a known divergence point and verifying that the analysis script correctly flags the run as "diverged".

### Implementation for User Story 2

- [ ] T020b [US2] Implement `src/llmxive/divergence_detector.py`: Class structure and initialization for divergence detection logic.
- [ ] T020c [US2] Implement `src/llmxive/divergence_detector.py` (Static Mean Baseline): MUST implement Spec FR-003 as the primary method: Flag if reward < `baseline_mean_reward` (from T020) for 50 consecutive steps OR gradient norm > 2x `baseline_mean_grad_norm` (from T020) for 50 consecutive steps.
 *Input*: `data/processed/baseline_manifests/{seed}.json`.
 *Note*: This task implements the Spec's mandatory static mean approach.
- [ ] T020d [US2] Implement `src/llmxive/divergence_detector.py` (50-Step Check): Implement the 50-step consecutive check logic for both reward and gradient norm thresholds.
- [ ] T018 [P] [US2] Unit test for divergence logic in `tests/unit/test_divergence_logic.py` (verify -step drop detection for static mean method)
- [ ] T023 [US2] Create `src/cli/analyze_divergence.py` to aggregate logs from executed US1 runs and identify max stable staleness threshold per model (US-2, SC-002).
 *Input*: JSON logs from T017 (T013b-g). **Dependency**: Execution of T013 (Async Trainer) must be complete.
 *Output Artifact*: `data/processed/threshold_map.json` containing `model_id`, `max_stable_staleness`, `status`.
- [ ] T023b [US2] [P] Execute divergence analysis for Qwen1.5-1.8B across varying staleness levels to generate the necessary data for the 1.8B model comparison.
- [ ] T024 [US2] Implement output formatting for `status: DIVERGED/STABLE` and `divergence_point` (US-2, AC-1)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Comparison of Convergence Stability (Priority: P3)

**Goal**: Statistically validate the difference in stability between low and high staleness regimes using the Spec-mandated t-test.

**Independent Test**: The system can be tested by running a mock dataset with known means and variances and verifying the t-test returns the correct p-value.

### Implementation for User Story 3

- [ ] T027 [US3] Implement aggregation script in `src/cli/run_experiment.py` to collect final rewards from multiple seeds per regime (Low, High) from executed runs (FR-004).
 *Input*: JSON logs from T017 (T013b-g); Output: aggregated lists for t-test. **Dependency**: Execution of T013 (Async Trainer) must be complete.
- [ ] T027b [US3] [P] Execute multiple runs for High Staleness/Phi-2 to generate data for t-test.
- [ ] T027c [US3] [P] Execute multiple runs for High Staleness/Qwen1.5 to generate data for t-test.
- [ ] T026 [US3] Implement `src/llmxive/stats.py` with two-sample t-test for equality of means on final reward (FR-005, US-3).
 *Note*: Per Spec FR-005, implement Two-Sample T-Test. This task satisfies the Spec requirement. Survival Analysis (Log-Rank) is excluded per Spec FR-005 constraints.
- [ ] T028 [US3] Generate statistical report outputting p-value, significance statement (alpha=0.05), and hypothesis confirmation status (SC-003, SC-001).
 *Output Artifact*: `data/processed/stats_report.json` containing `p_value`, `significant`, `hypothesis_status`.
- [ ] T029 [US3] Implement calculation of reward variance ratio (Low vs High staleness) and log confirmation status if ratio > 1.5 to confirm hypothesis (SC-001).
 *Behavior*: If ratio <= 1.5, log "HYPOTHESIS_NOT_CONFIRMED: ratio <= 1.5" at INFO level and continue; do NOT assert/fail.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T030 [P] Generate final plots using `src/llmxive/plot_generator.py` from `data/processed/` logs (US-2, US-3)
- [ ] T034 [P] [US2] Implement cross-model comparison script in `src/cli/compare_models.py` to aggregate thresholds from T023 for both models and generate the "non-linear trend" plot required by SC-002 (threshold 1.8B > 1.4B).
- [ ] T034b [US2] [P] Verify Non-Linear Trend: Programmatically assert that `threshold(1.8B) > threshold(1.4B)` and log success/failure to `data/processed/trend_verification.json`.
- [ ] T031 [P] Validate `requirements.txt` and `quickstart.md` for reproducibility
- [ ] T032a [P] Define "sampled dataset" for integration tests (e.g., first rows of GSM8K train split) in `tests/integration/conftest.py`.
- [ ] T032b [P] Define "full integration test suite" selection (e.g., T012, T018, T025) in `pytest.ini`.
- [ ] T032c1 [P] Execute integration test T012 (Sync Loop) and generate `pytest.xml` artifact; verify exit code 0.
- [ ] T032c2 [P] Execute integration test T018 (Divergence Logic) and generate `pytest.xml` artifact; verify exit code 0.
- [ ] T032c3 [P] Execute integration test T025 (Stats) and generate `pytest.xml` artifact; verify exit code 0.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Execution Safety & Data Integrity (Revision)

**Purpose**: Address execution gate concerns regarding data loading robustness and synthetic fallback prevention.
**Note**: Phase 7 tasks (T035-T038) were moved to Phase 2 (Foundational) to ensure data integrity before training logic implementation.

- [ ] (Moved to Phase 2) T035 [P] [US1] Refactor `src/llmxive/data_loader.py` to remove any implicit `try/except` blocks that might catch `datasets` download errors and fall back to `generate_synthetic_*` or `mock_*` functions. Ensure the loader raises `DATA_INTEGRITY_ERROR` immediately on any fetch failure, allowing the execution stage to detect the issue and retry with a verified source.
- [ ] (Moved to Phase 2) T036 [P] [US1] Add explicit unit tests in `tests/unit/test_data_loader.py` to verify that `data_loader.py` raises `DATA_INTEGRITY_ERROR` when `datasets.load_dataset` fails, ensuring no silent fallback occurs.
- [ ] (Moved to Phase 2) T037 [P] [US1] Implement a "Verified Source" check in `src/llmxive/config.py`: If the execution environment provides a "VERIFIED REAL DATA SOURCE" block (e.g., a specific package or URL), the loader MUST adopt this source exclusively and ignore any default `openai/gsm8k` configuration.
- [ ] (Moved to Phase 2) T038 [P] [US1] Add a `streaming=True` flag enforcement in `src/llmxive/data_loader.py` to ensure GSM8K is processed in chunks, preventing OOM on the 7GB RAM runner. Verify that the loader does not attempt to load the full dataset into memory.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - **Critical Dependency**: T019a (Baseline Gen Impl), T019b (Orchestrator Impl), T019c/T019d (Baseline Runs), T020 (Loader Impl), T021 (Stability Check), T022 (Retry Logic), T016 (Seed Manager), T007 (Queue Impl), and T014 (Queue Integration) MUST complete before T013 (Async Trainer).
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Execution Safety (Phase 7)**: Moved to Phase 2 to ensure data integrity before training.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2). **T019a, T019b, T019c, T019d, T020, T021, T022, T016, T007, T014 are part of US1 flow and must precede T013.**
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 for training logs (T013) and Baseline Manifests (T019a/T019b).
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1/US2 for aggregated results from executed runs.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Config before services
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Unit test for staleness_queue.py in tests/unit/test_staleness_queue.py"
Task: "Integration test for CPU model loading in tests/integration/test_cpu_load.py"
Task: "Integration test for training loop in tests/integration/test_sync_loop.py"

# Launch Baseline Generation (T019a/T019b) AND Stability Check (T022) BEFORE Async Trainer (T013):
Task: "Implement and execute synchronous baseline generation (T019a, T019b, T019c, T019d)"
Task: "Implement stability check and retry loop (T022)"
# THEN:
Task: "Implement src/llmxive/trainer.py (T013)"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Including T019a/T019b Baseline Gen, T019c/T019d Baseline Runs, T020/T021/T022 Stability/Retry, T016 Seed Manager, T014 Queue Integration)
4. **STOP and VALIDATE**: Test User Story 1 independently (including divergence detection using generated manifests)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 (including Baseline Gen, Stability, Retry, Seed Manager, Baseline Runs) → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (T019a/T019b Baseline Gen, T019c/T019d Baseline Runs, T020/T021/T022 Stability/Retry, T016 Seed Manager, T013 Async Trainer)
 - Developer B: User Story 2
 - Developer C: User Story 3
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
- **Data Hygiene**: Ensure `data_loader.py` strictly raises on failure; no synthetic fallbacks allowed (T035, T036).
- **Hardware**: All training tasks must explicitly target `device="cpu"` and 8-bit quantization.
- **Critical Data Flow**: T019a, T019b, T019c, T019d, T020, T021, T022, T016, T007, and T014 MUST execute before T013 (Async Training) to provide the seed-specific thresholds required by FR-003.
- **Statistical Method**: Only Two-Sample T-Test (Spec FR-005) is implemented (T026). Survival Analysis is excluded per Spec constraints.
- **Divergence Method**: Only Static Mean Baseline (Spec FR-003) is implemented (T020c). Intrinsic Variance is excluded per Spec constraints.
- **Spec vs Plan**: Tasks implement Spec requirements. Where Plan contradicts Spec (e.g., Survival Analysis, Intrinsic Variance), Spec takes precedence and Plan requirements are excluded to prevent constraint violation.
- **Execution Safety**: Phase 7 tasks (T035-T038) moved to Phase 2 to ensure data integrity before training.
- **Seed Audit**: T016 explicitly logs discarded seeds to `data/processed/seed_audit.json` to satisfy Constitution Principle IV.
- **Trend Verification**: T034b programmatically verifies the non-linear trend (SC-002).