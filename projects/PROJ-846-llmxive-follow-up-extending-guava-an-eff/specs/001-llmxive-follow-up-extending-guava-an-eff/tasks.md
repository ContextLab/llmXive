# Tasks: llmXive follow-up: extending "Guava: An Effective and Universal Harness for Embodied Manipulation"

**Input**: Design documents from `/specs/001-symbolic-guava-perception/`
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

- [ ] T001a [P] Create project root directory: `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/` <!-- ATOMIZE: requested -->
- [ ] T001b [P] Create code directory: `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/code/`
- [ ] T001c [P] Create data directory: `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/data/`
- [ ] T001d [P] Create tests directory: `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/tests/`
- [ ] T002a [P] Create `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/code/requirements.txt` with dependencies: `opencv-python`, `onnxruntime`, `datasets`, `transformers`, `torch`, `scikit-learn`, `pandas`, `numpy`, `pytest`
- [ ] T002b [P] Add Python version check script to verify Python 3.11+ is available
- [ ] T003 [P] Configure linting and formatting tools (ruff/black) in `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on plan.md):

- [ ] T004a [P] Create `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/data/raw/` with `.gitkeep`
- [ ] T004b [P] Create `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/data/processed/` with `.gitkeep`
- [ ] T004c [P] Create `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/data/artifacts/` with `.gitkeep`
- [ ] T005 [P] Implement `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/code/utils/state_manager.py` to update `state/projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff.yaml` with content hashes
- [X] T006 [P] Setup `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/code/utils/config.py` for seeds, paths, and hyperparameters
- [X] T007 [P] Create base data models (`SymbolicObservation`, `Trajectory`, `TaskOutcome`, `PerceptionLog`) in `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/code/data/models.py`
- [ ] T008 [P] Configure error handling infrastructure and `DatasetUnavailableError` exception
- [ ] T009 [P] Setup environment configuration management for CPU-only runner constraints

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Symbolic Pipeline Construction & Dataset Transformation (Priority: P1) 🎯 MVP

**Goal**: Ingest Guava visual trajectories and transform them into a "Symbolic-Guava" dataset using a CPU-only perception module.

**Independent Test**: The pipeline runs on a subset of trajectories. Output JSON contains valid bounding boxes/class labels. Processing time ≤ 150ms/frame on CPU. No raw pixel data in output.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Contract test for `SymbolicObservation` schema validation in `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/tests/contract/test_symbolic_observation.py`
- [X] T011 [P] [US1] Integration test for full trajectory transformation in `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/tests/integration/test_transform_pipeline.py`
- [X] T012 [P] [US1] Unit test for YOLO-tiny inference latency (must be < 150ms) and 4-hour full dataset completion in `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/tests/unit/test_performance.py`

### Implementation for User Story 1

- [ ] T013 [US1] Implement `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/code/data/download_guava.py` to fetch raw Guava data to `data/raw/guava/` and generate `data/raw/guava/checksums.json` (raise `DatasetUnavailableError` if fetch fails; NO synthetic fallback)
- [X] T014 [P] [US1] Implement `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/code/data/transform_symbolic.py` to ingest raw frames and generate `SymbolicObservation` JSONs to `data/processed/symbolic_guava/{trajectory_id}.json` (FR-001, FR-002)
- [X] T015 [P] [US1] Integrate OpenCV + ONNX Runtime YOLO-tiny in `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/code/data/transform_symbolic.py` for object detection (class, bbox, centroid, color histogram)
- [ ] T016 [US1] Implement `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/code/utils/logger.py` function `log_perception_ground_truth` to generate a continuous 'Perception Ground-Truth Log' (`data/artifacts/perception_log.json`) for every frame, tracking `object_missing_if_visible` flags (FR-007, FR-008)
- [ ] T017 [US1] Implement logic to handle empty frames (empty object list or "scene_empty" flag) in `transform_symbolic.py`
- [X] T018 [P] [US1] Implement `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/code/utils/logger.py` function `log_latency` to add perception latency measurements to `PerceptionLog` in `code/utils/logger.py` (FR-007, FR-008)
- [X] T019 [US1] Implement `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/code/data/validate_perception.py` to validate YOLO precision/recall and verify the 4-hour completion time constraint for the full transformation (FR-001, FR-002)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Model Re-distillation on Symbolic States (Priority: P2)

**Goal**: Fine-tune a compact LLM (Phi-3-mini) on the Symbolic-Guava dataset to reason over symbolic states.

**Independent Test**: Fine-tuning converges (loss decrease ≥15%) within 4 hours on CPU (or triggers GPU escape hatch). Model accepts symbolic JSON input without crashing.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T020 [P] [US2] Contract test for model input format (symbolic JSON) in `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/tests/contract/test_model_input.py`
- [X] T021 [P] [US2] Integration test for training loop convergence in `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/tests/integration/test_training_convergence.py`

### Implementation for User Story 2

- [X] T022 [US2] Implement `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/code/models/train_llm.py` to load Phi-3-mini and prepare symbolic dataset
- [~] T023 [US2] Implement LoRA fine-tuning logic using original Guava prompt templates and action abstraction schemas (FR-003)
- [ ] T024 [US2] Implement training monitoring to track loss decrease (target: ≥15% in 4h), logging to `data/artifacts/training_metrics.json` with keys: epoch, loss, timestamp
- [~] T025 [US2] Implement checkpoint saving mechanism for partial training runs (FR-003)
- [~] T026 [US2] Implement GPU escape hatch logic: if CPU training time > 4h, trigger script `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/code/models/trigger_gpu_run.sh`. **CRITICAL**: If GPU is used, log "CPU convergence failed" to `data/artifacts/gpu_escape_log.json` and mark the primary CPU constraint (FR-003) as NOT MET. The GPU run is for validation only, not for reporting primary metrics.
- [~] T027 [US2] Ensure model inference accepts `SymbolicObservation` JSON directly (no pixel tensors) in `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/code/models/inference_symbolic.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Evaluation & Statistical Comparison (Priority: P3)

**Goal**: Evaluate the Symbolic-Guava agent against the Baseline-Guava (visual) agent and perform statistical analysis.

**Independent Test**: Evaluation runs on a held-out set of tasks. Outputs success rates, step counts, and a p-value from a Permutation Test. Failure categorization works correctly.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T028 [P] [US3] Contract test for `TaskOutcome` schema in `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/tests/contract/test_task_outcome.py`
- [X] T029 [P] [US3] Integration test for evaluation loop on tasks in `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/tests/integration/test_evaluation_loop.py`
- [ ] T030 [P] [US3] Unit test for Permutation Test (sufficient iterations) logic in `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/tests/unit/test_permutation_test.py`

### Implementation for User Story 3

- [ ] T031 [US3] Implement `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/code/models/inference_symbolic.py` to run the fine-tuned Symbolic-Guava agent on a held-out set of tasks (FR-004)
- [ ] T032a [US3] Implement `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/code/models/inference_baseline.py` to run the **Baseline-Guava (visual)** agent on the same set of tasks for comparison against the Symbolic agent (FR-004, SC-001, Spec Requirement).
- [ ] T032b [P] [US3] Implement `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/code/models/inference_oracle.py` to run the **Oracle-Symbolic** agent (perfect policy) on the same set of tasks for secondary analysis of reasoning gaps (Plan Methodology).
- [ ] T033 [US3] Implement `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/code/analysis/failure_categorizer.py` to categorize failures (geometric, semantic, perception, latency) using `PerceptionLog` (FR-006, FR-007)
- [ ] T034 [US3] Implement logic to flag "latency-induced failures" (>150ms) in `TaskOutcome` records
- [ ] T035 [US3] Implement logic to filter out latency-induced failures from the primary success rate calculation and write updated outcomes to `data/processed/evaluation_outcomes.json` (FR-008)
- [ ] T036 [US3] Implement `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/code/analysis/stats_test.py` to perform a Permutation Test with a sufficient number of iterations to ensure statistical robustness., comparing the Symbolic-Guava agent success rate against the Baseline-Guava (visual) agent success rate (FR-005).
- [ ] T037 [US3] Implement output generation for success rate, step efficiency, p-value, and failure distribution to `data/artifacts/evaluation_results.json` (FR-005, SC-001, SC-002)
- [ ] T038 [US3] Implement logic to calculate the ratio of semantic failures to total failures **excluding perception and latency failures**, and verify the ≥40% threshold (SC-004), writing result to `data/artifacts/sc004_verification.json`
- [ ] T039 [US3] Implement unit test for the semantic failure ratio calculation in `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/tests/unit/test_semantic_ratio.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T040 [P] Refactor `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/code/utils/logger.py` to reduce cyclomatic complexity to <10
- [ ] T041 [P] Update README.md with setup instructions
- [ ] T042 [P] Create docs/quickstart.md with execution examples
- [ ] T043 [P] Update docs/api.md with function signatures
- [ ] T044 [P] Run `state_manager.py` to finalize project state hashes
- [ ] T045 [P] Run quickstart.md validation

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

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories. **CRITICAL**: Must complete before US2 and US3 as it produces the dataset.
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 output (Symbolic-Guava dataset).
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 (dataset) and US2 (trained model).

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
Task: "Contract test for SymbolicObservation schema validation in tests/contract/test_symbolic_observation.py"
Task: "Integration test for full trajectory transformation in tests/integration/test_transform_pipeline.py"
Task: "Unit test for YOLO-tiny inference latency in tests/unit/test_perception_latency.py"

# Launch implementation tasks for User Story 1 together:
Task: "Implement code/data/download_guava.py"
Task: "Implement code/data/transform_symbolic.py"
Task: "Implement code/utils/logger.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Dataset Generation)
4. **STOP and VALIDATE**: Verify Symbolic-Guava dataset is valid and YOLO precision/recall meets thresholds.
5. Deploy/demo if ready.

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
 - Developer A: User Story 1 (Dataset)
 - Developer B: User Story 2 (Model Training) - *Note: Can start partially but depends on US1 data*
 - Developer C: User Story 3 (Evaluation) - *Note: Can start partially but depends on US1 & US2*
3. Stories complete and integrate independently.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Data Integrity**: All data loading tasks MUST fail loudly if real data is unavailable. No synthetic fallbacks.
- **Compute Constraints**: Adhere to CPU-only limits unless GPU escape hatch is triggered for training. If GPU is used, CPU constraint is considered failed.
- **Baseline Correction**: T032a implements the **Baseline-Guava (visual)** agent as required by the Spec (FR-004). T032b implements the **Oracle-Symbolic** agent as per the Plan's secondary analysis. The primary evaluation compares Symbolic vs. Visual.
- **Statistical Robustness**: T036 uses exactly 10,000 permutations as per FR-005.
- **Failure Logic**: T038 explicitly excludes perception and latency failures from the semantic ratio calculation as per SC-004.