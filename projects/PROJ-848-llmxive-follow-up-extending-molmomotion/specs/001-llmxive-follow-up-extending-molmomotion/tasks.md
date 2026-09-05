# Tasks: llmXive follow-up: extending "MolmoMotion: Forecasting Point Trajectories in 3D with Language Instru"

**Input**: Design documents from `/specs/001-llmxive-motion-scaling/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

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

- [ ] T001a [P] Create directory structure: `projects/PROJ-848-llmxive-follow-up-extending-molmomotion/{code,data,specs,state}`
- [ ] T001b [P] Create `__init__.py` in `code/src/`, `code/tests/`, and `code/tests/integration/`
- [ ] T001c [P] Create `.gitkeep` in `data/raw/`, `data/processed/`, `data/results/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004a [P] Create `data_loader.py` skeleton in `code/src/data_loader.py` with empty functions and imports (for test mocking)
- [X] T004b [P] Implement `load_molmomotion_streaming` in `code/src/data_loader.py`: fetch from verified URL (spec), implement retry logic (up to 3 attempts), fail loudly (exit code 1, message "Download failed after 3 retries") on final failure. **Do NOT implement subsampling logic here**; this task is strictly for streaming and fetching.
- [ ] T005a [P] Create `dataset.schema.yaml` in `specs/001-llmxive-motion-scaling/contracts/` defining fields for `instance_id`, `ground_truth_points`, `kinematic_metadata`, `instruction_nl`, `instruction_struct`.
- [ ] T005b [P] Create `prediction.schema.yaml` in `specs/001-llmxive-motion-scaling/contracts/` defining fields for `predicted_points`, `ate`, `adherence_score`, `instruction_type`, `status`.
- [X] T006 Create base configuration management in `code/src/config.py` for random seeds, device constraints (`cpu`), and artifact paths
- [X] T007 [P] Setup logging infrastructure in `code/src/logging_config.py` to capture latency, memory usage, and NaN/Inf warnings
- [X] T019 [P] Implement `DualHeadLinearModel` in `code/src/model.py` (non-autoregressive, linear projection) with `torch.set_device('cpu')` enforcement

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Dataset Subsampling and Instruction Synthesis (Priority: P1) 🎯 MVP

**Goal**: Prepare a computationally feasible dataset by subsampling MolmoMotion-1M and generating dual instruction modalities (coarse NL and structured kinematic) for every trajectory.

**Independent Test**: Execute `code/src/data_loader.py` and `code/src/instruction_synthesizer.py` to verify output contains valid instruction pairs for subsampled instances, total memory ≤ 7GB, and no OOM errors.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T008 [P] [US1] Unit test for subsampling logic in `code/tests/test_data_loader.py` verifying memory constraints using mocked data/interfaces
- [X] T009 [P] [US1] Unit test for instruction synthesis in `code/tests/test_synthesis.py` verifying both NL and structured outputs are derived strictly from metadata using mocked data/interfaces

### Implementation for User Story 1

- [ ] T010 [Removed - functionality merged into T004b/T011 flow]
- [ ] T011 [US1] Implement `subsample_instances` in `code/src/data_loader.py`: Read `random_seed` and `target_memory_gb` from `config.py`. Use `datasets.load_dataset(..., streaming=True)` to iterate, implementing a **random subsampling strategy** (e.g., reservoir sampling or random selection with seed) to select instances until `target_memory_gb` is reached. **Do NOT use 'first N' logic**. Write output to `data/processed/subsampled_instances.parquet`.
- [ ] T011b [US1] Implement `validate_sample_size` in `code/src/data_loader.py`: Immediately after T011, verify the count of valid instances in `data/processed/subsampled_instances.parquet` meets the minimum threshold (e.g., a sufficiently large magnitude) required for statistical power. If not, raise a critical error to stop the pipeline before inference.
- [ ] T012 [US1] Implement `generate_natural_language_instruction` in `code/src/instruction_synthesizer.py` creating coarse descriptions (e.g., "move left") from metadata
- [ ] T013 [US1] Implement `generate_kinematic_instruction` in `code/src/instruction_synthesizer.py` creating structured vectors (velocity, duration) from ground-truth metadata (Input: `data/processed/subsampled_instances.parquet`)
- [ ] T014 [US1] Implement `synthesize_instruction_pairs` in `code/src/instruction_synthesizer.py` to pair NL and structured instructions for every instance, handling edge cases (ambiguous metadata: if velocity vector or duration is missing/null) by logging warnings and skipping
- [ ] T015 [US1] Write combined instruction pairs to `data/processed/instruction_pairs.jsonl` with schema compliance
- [ ] T016 [US1] Add validation to ensure no synthetic data is used; if real fetch fails, raise error immediately (FR-001, FR-002)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - CPU-Optimized Inference Pipeline Execution (Priority: P2)

**Goal**: Execute the Dual-Head Linear Baseline model on the prepared dataset using both instruction modalities, strictly enforcing CPU-only execution.

**Independent Test**: Run `code/src/inference.py` on GitHub Actions runner; verify all predictions generated, zero GPU usage, and output files created within 6 hours.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T017 [P] [US2] Contract test for inference output format in `code/tests/contract/test_prediction_schema.py`
- [ ] T018 [P] [US2] Integration test for CPU-only enforcement in `code/tests/integration/test_cpu_enforcement.py`

### Implementation for User Story 2

- [ ] T020 [US2] Implement `run_inference_batch` in `code/src/inference.py` to process `instruction_pairs.jsonl` using both NL and structured inputs (Depends on T015, T019)
- [ ] T021 [US2] Add NaN/Inf detection in `code/src/inference.py` to flag failed instances (mark status='failed', exclude from output) and exclude them from analysis (Edge Case)
- [ ] T022 [US2] Record inference latency and peak memory usage per batch in `code/src/inference.py` and log to `data/results/inference_metrics.log` (FR-006)
- [ ] T023 [US2] Write prediction outputs to `data/results/predictions.jsonl` with `predicted_points`, `instruction_type`, and status fields
- [ ] T024 [US2] Verify no GPU access occurs during execution (FR-003)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Metric Calculation and Statistical Comparison (Priority: P3)

**Goal**: Calculate Average Trajectory Error (ATE) for all predictions and perform a paired t-test to determine statistical significance of the performance gap.

**Independent Test**: Run `code/src/analysis.py` on `predictions.jsonl` to verify ATE calculation, t-test execution, and generation of summary report with p-value and [deferred] reduction verdict.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T025 [P] [US3] Unit test for ATE calculation in `code/tests/test_metrics.py`
- [ ] T026 [P] [US3] Unit test for paired t-test logic in `code/tests/test_analysis.py`

### Implementation for User Story 3

- [ ] T027 [P] [US3] Implement `calculate_ate` in `code/src/metrics.py` to compute Average Trajectory Error in meters for every prediction against ground truth (FR-004)
- [ ] T028 [US3] Implement `calculate_instruction_adherence_score` in `code/src/metrics.py` to record the score for trade-off quantification (Constitution Principle VII) but **do not** use it for the pass/fail verdict (SC-001).
- [ ] T029a [US3] Implement `align_predictions_by_instance` in `code/src/analysis.py` to join/align the NL and Structured prediction results by `instance_id` to ensure strict pairing for the t-test (FR-005).
- [ ] T029 [US3] Implement `run_paired_ttest` in `code/src/analysis.py` to compare ATE distributions between NL and structured groups using the aligned data from T029a (FR-005) (Must follow T027 and T029a completion)
- [ ] T030 [US3] Generate summary report in `data/results/ate_comparison.csv` containing mean ATE and p-value (Exclude Adherence Score from success validation)
- [ ] T031 [US3] Implement logic to output p-value and determine statistical significance (p < 0.05) (FR-005)
- [ ] T031a [US3] Implement logic to calculate the **percentage reduction in Average Trajectory Error (ATE)** between the structured and natural language groups and compare it against the **% threshold** defined in SC-001 to generate the final pass/fail verdict. (Depends on T031)
- [ ] T031b [US3] Generate combined verdict table in `data/results/analysis_summary.txt` containing p-value, [deferred] reduction delta, and final success status (Depends on T031, T031a)
- [ ] T032a [US3] Implement `calculate_statistical_power` in `code/src/analysis.py` using `statsmodels.stats.power.TTestPower` to measure the statistical power of the paired t-test against the expected effect size, verifying sample size sufficiency per SC-005. (Depends on T011b validation)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T033a [P] Update `docs/quickstart.md` with run instructions and environment setup
- [ ] T033b [P] Update `docs/data-model.md` with schema definitions and data flow
- [ ] T034 Code cleanup and refactoring in `code/src/`
- [ ] T035 [P] Run end-to-end validation script in `code/run_pipeline.sh` to verify full pipeline execution within 6h and 7GB limits
- [ ] T036 Record content hashes of all artifacts in `state/projects/PROJ-848-llmxive-follow-up-extending-molmomotion.yaml` (V-005)

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on data output from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on prediction output from US2

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
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
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for [endpoint] in tests/contract/test_[name].py"
Task: "Integration test for [user journey] in tests/integration/test_[name].py"

# Launch all models for User Story 1 together:
Task: "Create [Entity1] model in src/models/[entity1].py"
Task: "Create [Entity2] model in src/models/[entity2].py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
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
 - Developer A: User Story 1
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