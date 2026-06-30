# Tasks: DragMesh-2: Physically Plausible Dexterous Hand-Object Interaction with Articulated Objects

**Input**: Design documents from `/specs/750-dragmesh-2/`
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

- [X] T001 Create project structure per implementation plan (`src/`, `tests/`, `external/DragMesh-2/`)
- [X] T002 Initialize Python 3.9+ project with CPU-only PyTorch, MuJoCo, Gymnasium, and Hydra dependencies in `requirements.txt`
- [X] T003 [P] Configure linting and formatting tools (`ruff`, `black`) in `.pre-commit-config.yaml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement CPU-only physics environment wrapper in `src/environment/cpu_mujoco_env.py` (disables CUDA, sets device to CPU)
- [X] T005 [P] Implement asset integrity checker in `src/utils/asset_validator.py` to verify URDFs/Meshes from `external/DragMesh-2/assets` before execution
- [X] T006 [P] Create base configuration loader in `src/utils/config_loader.py` using Hydra to handle `train_config_gla_pica.yaml`
- [X] T007 Implement checkpoint manager in `src/utils/checkpoint_manager.py` to save/load state every 10 minutes for CI resilience
- [X] T008 Setup logging infrastructure in `src/utils/logger.py` to capture standard metrics and custom force/energy traces

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Environment Setup and Dependency Resolution (Priority: P1) 🎯 MVP

**Goal**: Instantiate a reproducible execution environment on GitHub Actions free-tier (CPU, standard memory allocation) that installs dependencies and initializes physics without GPU errors.

**Independent Test**: Can be fully tested by executing the installation script in a clean container and verifying imports of `pica`, `ppo`, and `src.environment` without CUDA errors.

### Tests for User Story 1

- [X] T009 [P] [US1] Unit test for `src/utils/asset_validator.py` ensuring it fails fast on missing files in `tests/unit/test_asset_validator.py`
- [X] T010 [P] [US1] Integration test for environment initialization in `tests/integration/test_env_setup.py` verifying CPU-only device detection

### Implementation for User Story 1

- [X] T011 [US1] Verify `external/DragMesh-2` submodule integrity and load assets per FR-001 in `src/utils/asset_validator.py`
- [X] T012 [US1] Configure MuJoCo/PyBullet backend in `src/environment/cpu_mujoco_env.py` to explicitly disable CUDA per FR-002
- [X] T013 [US1] Implement CI-compatible install script in `scripts/install_deps.sh` ensuring no `bitsandbytes` or GPU drivers are pulled
- [X] T014 [US1] Add error handling for physics simulation singularities (finger penetration) in `src/environment/cpu_mujoco_env.py` to trigger episode resets

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Training Pipeline Execution (Priority: P2)

**Goal**: Execute the PICA training loop on a single GAPartNet object on CPU, completing an epoch within 6 hours and generating checkpoints.

**Independent Test**: Can be fully tested by running `ppo/train.py` with minimal config and verifying checkpoint generation and loss convergence.

### Tests for User Story 2

- [X] T015 [P] [US2] Contract test for training output schema in `tests/contract/test_training_output.py` (validates `.pt` file structure)
- [X] T016 [P] [US2] Integration test for single-epoch training in `tests/integration/test_train_epoch.py` ensuring completion < 6h

### Implementation for User Story 2

- [X] T017 [US2] Integrate PICA agent logic from `external/DragMesh-2/pica` with CPU environment wrapper in `src/environment/cpu_mujoco_env.py`
- [X] T018 [US2] Implement training loop in `src/ppo/train.py` (or wrap `external/DragMesh-2/ppo/train.py`) to support configurable iterations and checkpointing per FR-003
- [X] T019 [US2] Add domain randomization for damping parameters during training in `src/environment/cpu_mujoco_env.py`
- [X] T020 [US2] Implement logging of loss curves and reward signals in `src/utils/logger.py` to verify learning per US-2 acceptance criteria

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Evaluation and Robustness Validation (Priority: P3)

**Goal**: Evaluate the trained policy across 7 damping conditions, generate comparative analysis, and produce the specific "work-energy" trace requested by the reviewer.

**Independent Test**: Can be fully tested by running the evaluation script across damping levels and verifying the output CSV/JSON and force-work plots.

### Tests for User Story 3

- [X] T021 [P] [US3] Contract test for evaluation result schema in `tests/contract/test_eval_results.py` (validates CSV columns)
- [X] T022 [P] [US3] Integration test for work-energy trace generation in `tests/integration/test_work_energy_trace.py`

### Implementation for User Story 3

- [X] T023 [US3] Implement evaluation runner in `src/scripts/eval/eval_damping.py` to iterate over 7 damping levels and record success rates per FR-004
- [X] T024 [US3] Implement post-processing script in `src/scripts/eval_postprocess.py` to generate comparative tables (PICA vs. Baseline) per FR-005
- [X] T025 [US3] **Reviewer Task**: Implement "Work-Energy" trace logger in `src/validation/work_energy_logger.py` to record normal force, friction, displacement, and kinetic energy change per step (FR-006, SC-003)
- [X] T026 [US3] Generate visualization artifacts (PNG/PDF) in `src/scripts/generate_plots.py` showing force vectors and energy vs. time plots for the "toy-problem sanity check"
- [X] T027 [US3] Validate force-balance consistency (sum of forces ≈ 0 in steady motion) in `src/validation/work_energy_logger.py` and log warnings if violated

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T028 [P] Documentation updates in `README.md` and `docs/` including the "Work-Energy" verification methodology
- [X] T029 Code cleanup and refactoring of `external/DragMesh-2` wrappers to ensure no GPU references remain
- [X] T030 [P] Run `quickstart.md` validation to ensure end-to-end reproducibility on CI
- [X] T031 Security hardening for asset loading paths

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 for environment
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 for trained checkpoints

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Utilities before Services/Logic
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Unit test for src/utils/asset_validator.py"
Task: "Integration test for environment initialization"

# Launch all models for User Story 1 together:
Task: "Verify external/DragMesh-2 submodule integrity"
Task: "Configure MuJoCo/PyBullet backend for CPU"
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
- **Reviewer Concern Addressed**: Task T025 and T026 specifically address the "Work-Energy" sanity check and "toy-problem" visualization requested by the Richard Feynman simulated review.
