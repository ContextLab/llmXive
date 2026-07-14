# Tasks: llmXive follow-up: extending PhysisForcing (Physics Filter)

**Input**: Design documents from `/specs/001-llmxive-physs-filter/`
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

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan (`projects/PROJ-951-llmxive-follow-up-extending-physisforcin/code/`) matching the exact directory tree in `plan.md:Project Structure` section.
- [ ] T002 Initialize Python 3.11 project with CPU-only `torch`, `pybullet`, `mujoco`, `diffusers`, `transformers`, `scikit-learn`, `opencv-python`, `pandas`, `numpy`, `requests`, `sam2`, `zoe_depth`
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools
- [ ] T004 [P] Create `requirements.txt` with pinned versions and verify `pip install` on CPU-only runner

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 Setup data directory structure: `data/raw`, `data/curated`, `data/eval` with checksumming utilities in `src/utils/io_utils.py`
- [ ] T006 [P] Implement logging configuration in `src/utils/logging.py` with file rotation and JSON logging for metrics
- [ ] T007 Create base configuration management in `src/training/config.py` to handle hyperparameters and CPU-only flags
- [ ] T008 Setup environment validation script `src/utils/verify_env.py` to ensure PyBullet/MuJoCo/PyTorch CPU modes are active and no CUDA is detected
- [ ] T009 Implement deterministic seed setting utility in `src/utils/io_utils.py` for reproducibility across batches

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Generate and Filter Synthetic Video Dataset (Priority: P1) 🎯 MVP

**Goal**: Generate synthetic robotic manipulation videos using Wan2.1, filter them via CPU-based PyBullet simulation, and produce a curated dataset.

**Independent Test**: Run generation on a small subset, verify physics filtering discards the bottom % based on score distribution, and ensure remaining videos pass continuity checks.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [ ] T010 [P] [US1] Unit test for prompt-to-scene translation logic in `tests/unit/test_prompt_to_scene.py`
- [ ] T011 [P] [US1] Integration test for the full generate-filter pipeline on 5 samples in `tests/integration/test_generate_filter_pipeline.py`

### Implementation for User Story 1

- [ ] T012 [P] [US1] Implement prompt management in `src/generation/prompts.py` loading verified RobotBench prompts
- [ ] T013 [US1] Implement Wan2.1 video generation wrapper in `src/generation/wan21_generator.py` (CPU-compatible subset/distilled version)
- [ ] T014 [US1] Implement prompt-to-scene translation in `src/filtering/prompt_to_scene.py` to map text to PyBullet assets and initial poses
- [ ] T015 [US1] Implement canonical simulation in `src/filtering/pybullet_filter.py` (DEPENDS ON T014) to generate ground truth trajectories using PyBullet headless mode
- [ ] T016 [P] [US1] Implement CV pipeline in `src/filtering/cv_pipeline.py` using SAM2 and ZoeDepth for 3D trajectory extraction with Kalman filtering
- [ ] T017a [US1] Implement metric calculation in `src/filtering/score_utils.py` to calculate trajectory continuity and contact conservation scores using ground truth from T015
- [ ] T017 [US1] Orchestrate physics scoring in `src/filtering/pybullet_filter.py` (DEPENDS ON T015, T016, T017a) to apply metrics and generate raw scores
- [ ] T018 [US1] Implement filtering logic in `src/filtering/score_utils.py` to read `filter_discard_percent` from `config.yaml`, calculate the corresponding percentile threshold (e.g., 60th for 40% discard), discard bottom videos, and save curated dataset to `data/curated/`
- [ ] T019 [US1] Add error handling for corrupted video frames (assign score 0.0, log error) in `src/filtering/pybullet_filter.py`
- [ ] T020 [US1] Add memory usage monitoring to ensure < 6 GB RAM during filtering in `src/utils/io_utils.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Train Distilled Diffusion Model on Curated Data (Priority: P2)

**Goal**: Train a distilled diffusion model of substantial capacity on the curated dataset using CPU-only optimization.

**Independent Test**: Train for a sufficient number of epochs on CPU, verify loss decreases, and ensure no CUDA libraries are loaded.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T021 [P] [US2] Unit test for NaN loss detection and retry logic in `tests/unit/test_training_stability.py`
- [ ] T022 [P] [US2] Integration test for training on 10 curated samples in `tests/integration/test_cpu_training.py`

### Implementation for User Story 2

- [ ] T023 [P] [US2] Implement data augmentation module in `src/training/augmentation.py` (temporal jittering, geometric flipping) for FR-009
- [ ] T024 [US2] Implement 50M parameter diffusion model architecture in `src/training/diffusion_trainer.py` (CPU-optimized, no CUDA)
- [ ] T025 [US2] Implement training loop in `src/training/diffusion_trainer.py` with NaN detection, learning rate adjustment, and 4-hour timeout enforcement
- [ ] T026 [US2] Implement data loader for curated dataset in `src/training/diffusion_trainer.py` with batch size optimization for 7 GB RAM
- [ ] T027 [US2] Add checkpointing and model saving logic in `src/training/diffusion_trainer.py`
- [ ] T028 [US2] Add resource monitoring to ensure < 6 GB RAM during training in `src/utils/io_utils.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Evaluate and Compare Performance on Benchmarks (Priority: P3)

**Goal**: Evaluate the trained model against PhysisForcing baseline and unfiltered baseline on R-Bench and PAI-Bench with statistical significance testing.

**Independent Test**: Run evaluation suite, generate JSON report with scores and p-values, and verify performance gap calculation.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T029 [P] [US3] Unit test for statistical significance calculation (t-test/Mann-Whitney U) in `tests/unit/test_stats.py`
- [ ] T030 [P] [US3] Integration test for full evaluation pipeline on 30 samples in `tests/integration/test_evaluation_suite.py`

### Implementation for User Story 3

- [ ] T031 [P] [US3] Implement R-Bench scorer in `src/evaluation/r_bench.py`
- [ ] T032 [P] [US3] Implement PAI-Bench scorer in `src/evaluation/pai_bench.py`
- [ ] T033a [US3] Implement physics-informed loss function in `src/training/losses.py` (DEPENDS ON US2 completion)
- [ ] T033b [US3] Implement baseline training loop in `src/training/baseline_trainer.py` (DEPENDS ON US2 completion, T033a)
- [ ] T033c [US3] Implement baseline artifact management in `src/evaluation/baseline_proxy.py` to load and manage the trained proxy model
- [ ] T034 [US3] Implement stratified sampling for evaluation set (n=30) in `src/evaluation/stats.py`
- [ ] T035a [US3] Implement t-test and Mann-Whitney U statistical testing in `src/evaluation/stats.py` (FR-006 compliance)
- [ ] T035b [US3] Implement Linear Mixed Model (LMM) testing in `src/evaluation/stats.py` (Plan Phase 4 complexity)
- [ ] T036 [US3] Implement performance gap calculation and 15% threshold check in `src/evaluation/stats.py`
- [ ] T037a [US3] Generate distinct ground truth simulation files in `src/evaluation/ground_truth_gen.py` using prompt-to-scene logic for independent validation
- [ ] T037 [US3] Implement MuJoCo independent validation in `src/evaluation/mujoco_validator.py` (INPUT: curated videos + ground truth from T037a) to produce `data/eval/mujoco_scores.json`
- [ ] T038 [US3] Implement correlation analysis in `src/evaluation/stats.py` comparing PyBullet scores (on CV-extracted trajectories) vs MuJoCo scores (on distinct ground truth from T037a) to verify correlation < 0.95 (non-circularity)
- [ ] T039 [US3] Generate final JSON report in `data/eval/results.json` with all metrics and p-values
- [ ] T040 [US3] Add logic to trigger data augmentation if n < 30 before statistical testing in `src/evaluation/stats.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T041 [P] Documentation updates in `docs/` including `quickstart.md` and `data-model.md`
- [ ] T042 Code cleanup and refactoring for memory efficiency across all modules to reduce peak RAM by [deferred] (verified by profiling)
- [ ] T043 Performance optimization for CV pipeline (SAM2/ZoeDepth) to reduce processing time per video to < 2 minutes
- [ ] T044 [P] Additional unit tests for edge cases (corrupted frames, NaN loss, small dataset) in `tests/unit/`
- [ ] T045 Run `quickstart.md` validation to ensure all phases execute correctly on CPU-only runner
- [ ] T046 Verify all artifacts have content hashes recorded in `state/projects/PROJ-951-llmxive-follow-up-extending-physisforcin.yaml`

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 output (curated dataset)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 output (trained model) and US1 output (baseline data)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US1 can start immediately; US2 and US3 can start in parallel if US1 output is available
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for prompt-to-scene translation logic in tests/unit/test_prompt_to_scene.py"
Task: "Integration test for the full generate-filter pipeline on 5 samples in tests/integration/test_generate_filter_pipeline.py"

# Launch all models for User Story 1 together:
Task: "Implement prompt management in src/generation/prompts.py"
Task: "Implement prompt-to-scene translation in src/filtering/prompt_to_scene.py"
Task: "Implement CV pipeline in src/filtering/cv_pipeline.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (generate, filter, verify discard rate)
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
   - Developer A: User Story 1 (Data Generation & Filtering)
   - Developer B: User Story 2 (Model Training) - *Wait for US1 output*
   - Developer C: User Story 3 (Evaluation) - *Wait for US1 & US2 output*
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
- **CRITICAL**: All tasks MUST run on CPU-only (limited cores, 7 GB RAM). No CUDA, no large model training, no GPU-specific libraries.
- **CRITICAL**: All data must be real. No fabricated datasets. Use verified URLs for RobotBench prompts and Wan2.1 weights.