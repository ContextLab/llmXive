# Tasks: Reproduce & Validate MemLens Benchmark

**Input**: Design documents from `/specs/578-reproduce-memlens-benchmark/`
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

- [X] T001 Create project structure: `mkdir -p src/ tests/ contracts/ data/ results/`
- [X] T002 Initialize Python 3.10+ project: Create `requirements.txt` with pinned versions and `pyproject.toml` with `[build-system]`
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T008 Configure logging infrastructure to capture memory peaks and API failures (create `src/logging_config.py`)
- [X] T005 [P] Implement `src/api_client.py` with exponential backoff retry logic for external API calls, including a 'limited number of attempts' constraint and logic to skip failed models while continuing the batch (FR-005)
- [X] T006 [P] Implement `src/memory_monitor.py` with peak memory detection and graceful OOM termination logic (FR-006)
- [X] T007 Create `contracts/evaluation_run.schema.yaml` and `contracts/result_metric.schema.yaml` for output validation
- [X] T004 Setup `src/memlens_runner.py` entry point with CLI argument parsing for `--cpu-only`, `--context-length`, and `--mode`
- [X] T009 [P] Setup environment configuration management: Create `.env.example` with keys `API_KEY`, `DATASET_PATH` and implement `src/config.py` using `pydantic-settings`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Execute MemLens Evaluation Pipeline on CPU (Priority: P1) 🎯 MVP

**Goal**: Execute the vendored MemLens evaluation scripts on a CPU-only runner with a small data subset, producing valid JSON artifacts.

**Independent Test**: Run `src/memlens_runner.py --cpu-only --subset-size <SUBSET_SIZE>` and verify `results.json` exists with non-null metrics.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Contract test for `results.json` schema in `tests/contract/test_schemas.py`
- [X] T011 [P] [US1] Integration test for CPU-only execution flow in `tests/integration/test_eval_flow.py`

### Implementation for User Story 1

- [X] T012 [US1] Implement CPU-only device configuration in `src/memlens_runner.py` (FR-001)
- [X] T013 [US1] Implement data subset loading logic to handle small data samples (e.g., a limited set of questions) or a [deferred] sample from `data/` in JSONL format
- [X] T014 [US1] Integrate `src/memory_monitor.py` into the evaluation loop to detect OOM before processing
- [X] T015 [US1] Implement error handling for missing image files (skip with warning)
- [X] T016 [US1] Add logging for execution duration and memory usage peaks
- [X] T017 [US1] Verify output `results.json` contains `run_id`, `status="completed"`, and metric values

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Validate Visual Evidence Dependency (Priority: P2)

**Goal**: Implement image-ablation mode to programmatically remove images and verify accuracy drops to ≤ 2% on image-dependent questions.

**Independent Test**: Run `src/memlens_runner.py --mode ablation --subset image-evidence` and verify `ablation_accuracy` ≤ 0.02.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Contract test for `ablation_accuracy` field in `tests/contract/test_schemas.py`
- [X] T019 [P] [US2] Unit test for image replacement logic in `tests/unit/test_ablation.py`

### Implementation for User Story 2

- [X] T020 [P] [US2] Create `src/ablation.py` module with function to replace image inputs with null tokens
- [X] T021 [US2] Implement `--mode ablation` logic in `src/memlens_runner.py` to trigger image removal
- [X] T022 [US2] Integrate ablation logic with the evaluation pipeline (FR-002)
- [X] T023 [US2] Add logic to filter results specifically for "image-evidence" subset questions using the `has_image` or `evidence_type` field in the dataset
- [X] T024 [US2] Verify `results.json` captures `ablation_accuracy` and compares it against baseline
- [X] T025 [US2] Log the observed accuracy drop percentage for later comparison against the <2% claim (do not assert pass/fail here)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Reproduce Scaling & Memory Ability Trends (Priority: P3)

**Goal**: Generate a summary report categorizing performance by multiple memory abilities and context lengths (tens of thousands to hundreds of thousands) to verify degradation trends.

**Independent Test**: Run evaluations at K and 256K, aggregate results, and verify performance drop in `results.json`.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T026 [P] [US3] Contract test for `ability_breakdown` structure in `tests/contract/test_schemas.py`
- [X] T027 [P] [US3] Integration test for multi-context aggregation in `tests/integration/test_aggregation.py`

### Implementation for User Story 3

- [X] T028 [P] [US3] Create `src/context_manager.py` with logic to slice data for scalable context lengths including 64K, 128K, and 256K (FR-003)
- [X] T029 [US3] Implement logic to categorize questions into distinct memory abilities (information extraction, multi-session reasoning, temporal reasoning, knowledge update, answer refusal) using the `memory_ability` field in the dataset (FR-004)
- [X] T030 [US3] Implement aggregation logic in `src/memlens_runner.py` to group results by ability and context length
- [X] T031 [US3] Add logic to calculate and flag performance degradation trends (32K > 256K)
- [X] T032 [US3] Update `results.json` schema to include `ability_breakdown` and `context_scaling_metrics`
- [X] T033 [US3] Generate human-readable summary report at `results/summary_report.md` (Markdown) including accuracy by ability and context length trend

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T040 [P] Update `docs/quickstart.md` with CPU-only instructions and setup steps
- [X] T041 [P] Update `README.md` with project overview and usage examples
- [X] T042 Code cleanup and refactoring of `src/` modules
- [X] T043 [P] Additional unit tests for edge cases (corrupted files, rate limits) in `tests/unit/`
- [X] T044 Run `docs/quickstart.md` validation to ensure end-to-end reproducibility

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
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
Task: "Contract test for results.json schema in tests/contract/test_schemas.py"
Task: "Integration test for CPU-only execution flow in tests/integration/test_eval_flow.py"

# Launch all models for User Story 1 together:
Task: "Implement CPU-only device configuration in src/memlens_runner.py"
Task: "Implement data subset loading logic"
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
- **Critical Constraint**: All tasks MUST run on CPU-only, limited RAM, multi-core CI. No GPU dependencies.