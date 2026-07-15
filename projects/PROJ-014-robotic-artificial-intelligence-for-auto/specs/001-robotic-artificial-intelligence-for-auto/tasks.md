# Tasks: Robotic AI Sensory Fidelity Ablation Study

**Input**: Design documents from `/specs/001-sensory-fidelity-ablation/`
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

- [ ] T001 Create project structure per implementation plan: `mkdir -p code/src/{environment,data,agents,analysis,utils} code/scripts code/tests code/data code/results`
- [X] T002 Initialize Python 3.11 project with `code/requirements.txt` (pinned versions: `torch==2.0.1+cpu`, `gymnasium==0.29.1`, `stable-baselines3==2.1.0`, `opencv-python==4.8.1.78`, `scikit-learn==1.3.2`, `pandas==2.1.4`, `numpy==1.26.2`)
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools
- [ ] T004 [P] Setup `pytest` configuration and test discovery

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Implement `code/src/utils/config.py` for hyperparameters, seeds, and path configuration
- [ ] T006 Implement `code/src/utils/logger.py` for RAM/CPU logging (FR-006) with `log_metrics()` function, JSON format, and -second interval sampling <!-- SKIPPED: YAML+regex parse failed (while scanning for the next token
found character '`' that cannot start any token
 in "<unicode string>", line 3, column 1:
 ```python
 ^) -->
- [X] T007 Create `code/src/environment/sim_wrapper.py` to wrap CARLA/KITTI simulation with noise injection (FR-004, US-1)
- [X] T008a [P] Create `code/src/data/calibration.py` for extrinsic calibration and coordinate transformation validation logic (FR-009, US-2)
- [ ] T008b [US2] Execute `scripts/validate_calibration.py` to perform coordinate transformation validation, generate `results/calibration_report.json`, and BLOCK if report is missing or validation fails (FR-009)
- [X] T009 Implement `code/scripts/hash_artifacts.py` to compute SHA-256 hashes for versioning discipline (Principle V)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Baseline Environment & Classical/Stochastic Planner Execution (Priority: P1) 🎯 MVP

**Goal**: Establish reproducible simulation environment and execute classical (Pure Pursuit/Dijkstra) and stochastic baselines to define performance bounds.

**Independent Test**: Run `scripts/run_baselines.py`; verify Pure Pursuit completes ≥80% episodes, stochastic ≤10%, and logs optimality ratios.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Contract test for baseline output schema in `code/tests/contract/test_baseline_schema.py`
- [X] T011 [P] [US1] Integration test for Pure Pursuit navigation in `code/tests/integration/test_pure_pursuit.py`

### Implementation for User Story 1

- [X] T012 [P] [US1] Implement Pure Pursuit controller in `code/src/environment/baselines.py`
- [X] T013 [P] [US1] Implement Dijkstra path planner in `code/src/environment/baselines.py` (CPU-optimized, x64 map resolution)
- [X] T014 [P] [US1] Implement Stochastic (Random) policy in `code/src/environment/baselines.py`
- [~] T015 [US1] Implement `code/scripts/run_baselines.py` to orchestrate N=30 seeds, handle crashes, and log results to `results/baseline_metrics.json` (schema: `{success_rate: float, path_optimality: float, seeds: list}`)
- [~] T016 [US1] Add error handling for memory pressure crashes (resume from checkpoint) per Edge Cases
- [~] T017 [US1] Add logging for baseline path optimality ratios and success rates

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Sensory Modality Data Pipeline & Preprocessing (Priority: P2)

**Goal**: Implement data pipeline to ingest raw sensor data and transform into three distinct modalities: Raw RGB (x84), Downsampled Depth, and 2D Occupancy Grids.

**Independent Test**: Run `scripts/generate_modalities.py` on fixed frames; verify output shapes (e.g., occupancy grid binary matrix) and obstacle alignment.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Contract test for modality tensor shapes in `code/tests/contract/test_modality_shapes.py`
- [X] T019 [P] [US2] Integration test for occupancy grid generation in `code/tests/integration/test_occupancy_grid.py`

### Implementation for User Story 2

- [X] T020 [P] [US2] Implement `code/src/data/pipeline.py` RGB preprocessing (center-crop, normalize, fixed spatial resolution)
- [ ] T021 [P] [US2] Implement `code/src/data/pipeline.py` Depth map downsampling logic
- [ ] T022 [P] [US2] Implement `code/src/data/pipeline.py` 2D Occupancy Grid generation (binary matrix, m-radius, noise handling)
- [ ] T023 [US2] Implement `code/scripts/generate_modalities.py` to process raw sensor data AND consume validated calibration parameters from `results/calibration_report.json` (produced by T008b) to ensure spatial alignment; save modalities to `data/modalities/` (FR-009, US-2)
- [ ] T024 [US2] Implement fallback logic for LiDAR dropout (substitute safe empty grid, log event) per Edge Cases
- [ ] T025 [US2] Verify spatial alignment across all three modalities for the same ground truth frame: Generate `results/alignment_report.json` with IoU scores (threshold > 0.95)
- [ ] T026 [P] [US2] Implement sensitivity analysis script `scripts/sweep_thresholds.py` for occupancy grid threshold (FR-008)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - DRL Training & Statistical Analysis (Priority: P3)

**Goal**: Train lightweight DQN agents (MobileNetV2 backbone, <1M params) for each modality under a fixed computational time budget, then perform statistical analysis (ANOVA/Kruskal-Wallis) on learning curves.

**Independent Test**: Run `scripts/train_and_analyze.py`; verify completion ≤6h, RAM ≤7GB, and output `results/statistical_report.json` with p-values.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T027 [P] [US3] Contract test for statistical report schema in `code/tests/contract/test_stats_schema.py`
- [ ] T028 [P] [US3] Integration test for DQN training loop resource limits in `code/tests/integration/test_dqn_resources.py`

### Implementation for User Story 3

- [ ] T029 [P] [US3] Implement `code/src/agents/dqn_agent.py` with pruned MobileNetV2 backbone (CPU-only, no CUDA)
- [ ] T030 [P] [US3] Implement `code/src/agents/memory.py` for replay buffer (CPU-optimized)
- [ ] T030a [US3] Implement `code/scripts/train_and_analyze.py` master orchestrator with a GLOBAL -hour wall-clock timer (FR-003, SC-005) that wraps the seed loop, saving checkpoints and halting execution if the total budget is exceeded; this task must execute BEFORE T031
- [ ] T031 [US3] Implement `code/scripts/train_and_analyze.py` to orchestrate training: (1) iterate through N=30 seeds per modality (RGB, Depth, Grid), (2) invoke T030a's global timer, (3) handle memory pressure crashes via checkpointing, and (4) output learning curve CSVs to `results/training_curves/`
- [ ] T032 [US3] Integrate training loop logic (T031) with DQN agent (T029) to produce training data
- [ ] T033 [US3] Implement `code/src/analysis/metrics.py` to calculate: (1) Area Under the Curve (AUC), (2) time-to-convergence, AND (3) **episodes to reach a high sustained success rate** (SC-001); output all metrics to `results/learning_metrics.json`
- [ ] T034 [US3] Implement `code/src/analysis/stats.py` for Welch's ANOVA/Kruskal-Wallis and post-hoc tests (Tukey/Dunn) (FR-005)
- [ ] T035 [US3] Implement inference latency measurement (ms/step) on CPU (SC-002) and output to `results/latency_report.json`
- [ ] T036 [US3] Inject "Findings are associational" header into `results/statistical_report.json` and validate schema for absence of causal keywords (FR-007)
- [ ] T036a [US3] Generate **novel, high-obstacle-density scenarios** for generalization testing (Plan Phase 3.2, SC-002) by configuring `sim_wrapper` with specific high-density parameters; save configuration and seed list to `results/novel_scenarios_config.json` (PREREQ for T037)
- [ ] T037 [US3] Execute `scripts/eval_generalization.py` on the **novel scenarios generated by T036a** to measure **success rate and generalization limits** (SC-002) in high-obstacle-density environments; output to `results/generalization_report.json` (Note: Focus on performance metrics, not just latency)
- [ ] T038 [US3] Aggregate AUCs across multiple seeds and perform stability analysis (SC-006): Calculate coefficient of variation and output `results/seed_stability_report.json`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T039 [P] Documentation updates in `docs/` and `README.md`
- [ ] T040 Code cleanup and refactoring of `code/src/`
- [ ] T041 Performance optimization for CPU training loop (batching, vectorization)
- [ ] T042 [P] Additional unit tests in `code/tests/unit/`
- [ ] T043 Security hardening (input validation in data pipeline)
- [ ] T044 Run `code/scripts/hash_artifacts.py` to update `state/` YAML (Phase 4.1)
- [ ] T045 Run `code/scripts/validate_quickstart.sh` and assert exit code 0 to ensure full pipeline reproducibility

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

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
Task: "Contract test for baseline output schema in code/tests/contract/test_baseline_schema.py"
Task: "Integration test for Pure Pursuit navigation in code/tests/integration/test_pure_pursuit.py"

# Launch all models for User Story 1 together:
Task: "Implement Pure Pursuit controller in code/src/environment/baselines.py"
Task: "Implement Dijkstra path planner in code/src/environment/baselines.py"
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
- **Critical Update**: Ta enforces the GLOBAL 6-hour limit; T036a generates novel scenarios for T037; T033 calculates the exact SC-001 metric.