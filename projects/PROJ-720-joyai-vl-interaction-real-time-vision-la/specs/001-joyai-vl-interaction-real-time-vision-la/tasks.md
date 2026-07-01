# Tasks: JoyAI-VL-Interaction: Real-Time Vision-Language Interaction Intelligence Reproduction

**Input**: Design documents from `/specs/720-joyai-vl-interaction-reproduction/`
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

- [X] T001a [P] Create project directories: `src/joyai/`, `src/joyai/core/`, `src/joyai/services/`, `src/joyai/pipeline/`, `src/joyai/utils/`, `tests/`, `data/samples/`, `artifacts/`, `logs/`, `install/`, `contracts/`
- [X] T001b [P] Create empty `__init__.py` files in all `src/joyai/` subdirectories to make them valid Python packages
- [X] T002 [P] Initialize Python 3.11 project with `pyproject.toml` defining dependencies: `torch` (CPU), `transformers`, `accelerate`, `opencv-python-headless`, `pytest`, `pyyaml`, `fastapi`, `pydantic`
- [X] T003 [P] Configure linting (`ruff`) and formatting (`black`) tools in `pyproject.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [X] T004 Setup base logging infrastructure in `src/joyai/utils/logger.py` to capture decision paths (FR-008) and pipeline events
- [X] T005 [P] Implement mock service interfaces in `src/joyai/services/`: `asr_mock.py`, `tts_mock.py`, `agent_mock.py`, `memory_mock.py`, `viz_mock.py`
- [X] T006 [P] Create base schema definitions in `contracts/` specifically: `decision_artifact.schema.yaml`, `delegation_artifact.schema.yaml`, `memory_summary_artifact.schema.yaml`, `visualization_artifact.schema.yaml`
- [X] T007 Create base data models in `src/joyai/core/` for `Frame`, `Decision`, `ScenarioResult`
- [X] T008 Implement error handling wrapper in `src/joyai/utils/exceptions.py` to support graceful degradation (FR-007)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Environment Verification and Dependency Installation (Priority: P1) 🎯 MVP

**Goal**: Verify CI runner environment (CPU-only, ≤7 GB RAM) and install dependencies without GPU/CUDA.

**Independent Test**: Execute `install/tests/verify_real_env.py` and `install/install.sh` on a fresh runner; assert exit code 0 and "GPU not available" report.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T009 [P] [US1] Contract test for environment verification in `tests/unit/test_env_verification.py`
- [X] T010 [P] [US1] Integration test for dependency installation in `tests/integration/test_installation.py`

### Implementation for User Story 1

- [X] T011 [US1] Implement `install/tests/verify_real_env.py` to check CPU cores (≥2), RAM (≤7GB), and confirm absence of CUDA/GPU. Must run in a fresh container context.
- [X] T012 [US1] Implement `install/install.sh` to install `torch` (CPU-only), `transformers`, `opencv-python-headless` without CUDA dependencies
- [X] T013 [US1] Add logging to `logs/env_verification.log` capturing system specs and installation status
- [X] T014 [US1] Add validation logic to ensure that if the 8B model fails to load, `load_in_4bit` is used as the approved fallback; explicitly allow `load_in_4bit` in the installation/config logic

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Core Model Execution and Response Decision Validation (Priority: P2)

**Goal**: Execute a CPU-tractable vision-language model on sample video frames and validate real artifacts (silent/respond/delegate decisions).

**Independent Test**: Run model inference on sample frames; verify `artifacts/decisions.json` contains varied, semantically consistent decisions within 10 minutes.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T015 [P] [US2] Contract test for decision artifact schema in `tests/contract/test_decision_schema.py`
- [X] T016 [P] [US2] Integration test for model inference logic in `tests/integration/test_model_inference.py`

### Implementation for User Story 2

- [X] T017 [P] [US2] Implement `src/joyai/core/video_processor.py` to extract frames from `data/samples/` (real public domain clips or generated frames)
- [X] T018a [US2] Implement logic in `src/joyai/core/model_loader.py` to **attempt** loading the largest available model first (without quantization)
- [X] T018b [US2] Implement fallback logic in `src/joyai/core/model_loader.py`: if 8B load fails (OOM/Timeout), switch to B distilled model and **log the deviation** in `artifacts/model_metadata.json`
- [X] T018 [US2] Implement `src/joyai/core/model_loader.py` to load the selected CPU-optimized VLM (1.3B or quantized 8B) and update `model_metadata` in artifacts if a deviation occurs
- [X] T019 [US2] Implement `src/joyai/core/decision_engine.py` to parse model output and classify as "silent", "respond", or "delegate"
- [X] T020 [US2] Implement logic to verify semantic consistency: "delegate" decisions must contain reasoning keywords matching regex `r'(hard|complex|delegate)'` in the model output
- [X] T021 [US2] Implement "triviality check": verify that for 3+ consecutive frames, `len(set(decisions)) > 1`; flag as "Invalid Logic Fidelity" if all decisions are identical
- [X] T022 [US2] Implement `src/joyai/core/model_runner.py` to run inference on 3+ consecutive frames (minimum 1 second temporal spacing) and write `artifacts/decisions.json`
- [X] T023 [US2] Add fallback logic: If 8B model OOMs, switch to 1.3B model and update `model_metadata` in `artifacts/` accordingly (covered by T018a/b, but ensure integration)
- [X] T024 [US2] Add logging to `logs/decision.log` tracing every decision to the input frame and model reasoning

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - End-to-End System Integration and Human Preference Validation (Priority: P3)

**Goal**: Integrate all components (ASR, TTS, Memory, Viz, Agent, Video, Model) and process a real-world scenario, producing artifacts for qualitative comparison.

**Independent Test**: Run `pipeline/run_scenario.py` on a sample scenario; verify all artifact types exist in `artifacts/` and pipeline completes in < 2 hours.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T025 [P] [US3] Contract test for pipeline artifacts in `tests/contract/test_pipeline_artifacts.py`
- [X] T026 [P] [US3] Integration test for error injection and graceful degradation in `tests/integration/test_error_handling.py`

### Implementation for User Story 3

- [X] T027 [P] [US3] Implement `src/joyai/pipeline/run_scenario.py` to orchestrate ASR (mock), Video, Model, TTS (mock), Memory (mock), Viz (mock), Agent (mock). Ensure `torch.no_grad()` and batch size 1 are used.
- [X] T028 [US3] Implement explicit invocation of `memory_mock.py` to generate `MemorySummaryArtifact` in `artifacts/`
- [X] T029 [US3] Implement explicit invocation of `viz_mock.py` to generate `VisualizationArtifact` in `artifacts/`
- [X] T030 [US3] Implement error injection mechanism to simulate ASR/TTS failures and verify graceful degradation (FR-007)
- [X] T031 [US3] Implement timing logic in `logs/pipeline.log` to measure total runtime and ensure < 2 hours
- [X] T031a [US3] Implement assertion logic to **fail** the task if total runtime exceeds 2 hours, verifying FR-006
- [X] T032 [US3] Implement artifact collection logic to gather transcripts, audio, decisions, memory, viz, and delegation logs
- [X] T033 [US3] Implement validation of `DelegationArtifact` against `contracts/delegation_artifact.schema.yaml`
- [X] T034a [US3] Implement the **Qualitative Validation Rubric** logic: check Existence (all artifacts present), Semantic Trigger (keywords match), Consistency (no crashes), and Triviality (varied decisions)
- [X] T034b [US3] Generate the qualitative comparison report at `artifacts/quality_report.md` including the rubric results and explicitly stating "Human Preference" is Unvalidated in CI
- [X] T035a [P] Update `README.md` with Setup instructions and how to run the reproduction pipeline
- [X] T035b [P] Update `quickstart.md` with the specific path to sample data and the expected output artifacts

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T036 Code cleanup and refactoring of mock services
- [X] T037 Performance optimization: ensure batch size 1 and `torch.no_grad()` are used in model inference (verify in T027)
- [X] T038 [P] Additional unit tests for edge cases (network timeout, RAM limits) in `tests/unit/`
- [X] T039 Run `quickstart.md` validation to ensure end-to-end reproducibility

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
Task: "Contract test for environment verification in tests/unit/test_env_verification.py"
Task: "Integration test for dependency installation in tests/integration/test_installation.py"

# Launch all models for User Story 1 together:
Task: "Implement install/tests/verify_real_env.py"
Task: "Implement install/install.sh"
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
- **Critical Constraint**: All model inference MUST be CPU-only. If 8B model fails, switch to smaller distilled model and document deviation.
- **Critical Constraint**: No fake data. Use real public domain video clips or generated frames.
- **Critical Constraint**: "Human Preference" is explicitly marked as Unvalidated in CI; focus on Logic Fidelity.
- **Critical Constraint**: T014 allows `load_in_4bit` as the approved fallback for 8B model OOM.