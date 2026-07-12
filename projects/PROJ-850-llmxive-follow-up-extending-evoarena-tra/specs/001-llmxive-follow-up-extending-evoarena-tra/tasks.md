# Tasks: EvoMem-Conflict Filtering for Robust LLM Agents

**Input**: Design documents from `/specs/001-evoconflict-filtering/`
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

- [ ] T001a [P] Create root directories: `src/`, `tests/`, `specs/`, `data/`, `docs/`
- [ ] T001b [P] Create source subdirectories: `src/agents/`, `src/heuristics/`, `src/data/generators/`, `src/data/benchmarks/`, `src/analysis/`, `src/utils/`, `src/cli/`
- [ ] T001c [P] Create test subdirectories: `tests/unit/`, `tests/integration/`, `tests/contract/`
- [ ] T001d [P] Create documentation subdirectories: `specs/001-evoconflict-filtering/contracts/`
- [ ] T002 [P] Initialize Python 3.11 project with `requirements.txt` containing **pinned versions** for: `transformers>=4.30.0`, `scikit-learn>=1.3.0`, `pandas>=2.0.0`, `pytest>=7.0.0`, `datasets>=2.14.0`, `tqdm>=4.65.0`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Implement `src/utils/logging.py` for structured logging of context tokens, inference time, and success status
- [ ] T005 [P] Create `src/data/generators/synthetic_pairs.py` to generate labeled JSON pairs for conflict detection validation. **Schema**: `{"patch_a": str, "patch_b": str, "is_contradiction": bool}`. **Logic**: Generate "contradiction" pairs by negating a key fact in `patch_b` relative to `patch_a` (e.g., "File X exists" vs "File X deleted"); generate "non-contradiction" pairs by updating unrelated facts or repeating facts. Target dataset size is configurable via `research.md`.
- [ ] T006 [P] Create `src/data/benchmarks/terminal_bench_evo.py` to **synthetically generate** the `Terminal-Bench-Evo` dataset (code-generated, not external download) with explicit state patches and version updates. Target task count is configurable via `research.md`.
- [ ] T007 Create `src/agents/base_agent.py` abstract base class defining the agent interface and retrieval strategy hooks
- [ ] T008 Configure deterministic random seeds in all scripts to ensure reproducible execution
- [ ] T009 [P] Implement `tests/unit/test_synthetic_generator.py` to verify the synthetic dataset generation logic and checksum integrity

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Conflict-Detection Heuristic Implementation (Priority: P1) 🎯 MVP

**Goal**: Implement a CPU-tractable conflict detector using DistilBERT to flag semantic contradictions in memory patches.

**Independent Test**: Run the detector on the synthetic pairs; verify precision/recall ≥ 80% against ground truth.

### Implementation for User Story 1

- [ ] T012 [P] [US1] Implement `src/heuristics/conflict_detector.py` using `distilbert-base-uncased` (CPU-only, default precision) to compute semantic contradiction scores. Must support loading alternative CPU-tractable models for sensitivity analysis.
- [ ] T013 [US1] Implement threshold logic in `src/heuristics/conflict_detector.py` (softmax > 0.90 = conflict; else non-conflict)
- [ ] T014 [US1] Implement `src/heuristics/conflict_detector.py` sensitivity analysis **scaffolding interface** and **configuration loader** to support loading and testing multiple model sizes (e.g., DistilBERT vs. a small parameter-efficient model) as required by FR-008. **Note**: Actual execution of multi-model sensitivity analysis is deferred pending plan updates to allow model size variation; this task implements the framework to enable future execution.
- [ ] T015 [US1] Add error handling in `src/heuristics/conflict_detector.py` to default to safe retrieval mode on timeout or failure (FR-007)
- [ ] T010 [P] [US1] Unit test `tests/unit/test_conflict_detector.py` for conflict detection logic on static synthetic pairs (Run after T012)
- [ ] T011 [P] [US1] Test fallback behavior when no conflicts are detected (must return latest state only) (Run after T012)
- [ ] T016 [P] [US1] Run validation script on synthetic dataset to confirm ≥80% precision/recall baseline before integration

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Dual-Agent Execution Pipeline (Priority: P2)

**Goal**: Instantiate and run `EvoMem-All` and `EvoMem-Conflict` agents on the task dataset, logging execution metrics.

**Independent Test**: Run a subset of tasks on both agents; verify `EvoMem-Conflict` retrieves fewer patches than `EvoMem-All` and both produce valid logs.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T017 [P] [US2] Integration test `tests/integration/test_agent_pipeline.py` verifying context token counts differ between variants
- [ ] T018 [P] [US2] Test that `EvoMem-Conflict` correctly filters non-conflict patches using the heuristic from US1 (Requires T012)

### Implementation for User Story 2

- [ ] T019 [P] [US2] Implement `src/agents/evomem_all.py` to retrieve the last N patches (baseline)
- [ ] T020 [US2] Implement `src/agents/evomem_conflict.py` to retrieve only the latest state + patches flagged as conflicts by US1 heuristic
- [ ] T021 [US2] Implement `src/agents/evomem_conflict.py` fallback logic to retrieve latest state only if no conflicts are found (Edge Case)
- [ ] T022 [US2] Implement `src/analysis/runner.py` to execute tasks from `Terminal-Bench-Evo` on both agent variants sequentially
- [ ] T023 [US2] Ensure `src/analysis/runner.py` logs `task_id`, `agent_variant`, `context_tokens`, `inference_time`, `success_status` to CSV
- [ ] T024 [P] [US2] Run the full experiment and verify execution completes within 6 hours on CPU (SC-005)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Comparison and Reporting (Priority: P3)

**Goal**: Analyze execution logs to calculate accuracy, hallucination rates, and statistical significance (Wilcoxon).

**Independent Test**: Feed mock CSV with known differences; verify script outputs p-value < 0.05 and correct effect direction.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T025 [P] [US3] Unit test `tests/unit/test_stats.py` with mock data to verify Wilcoxon test and metric calculations

### Implementation for User Story 3

- [ ] T026 [P] [US3] Implement `src/analysis/stats.py` to calculate chain-level accuracy and hallucination rates. **Hallucination Definition**: (incorrect terminal command execution **OR** state misinterpretation where string similarity < 90%). **Mechanism**: For command execution, compare LLM output commands against the **Sandbox Oracle** (actual file system state) to determine correctness; for state misinterpretation, calculate string similarity between LLM state description and ground truth.
- [ ] T027 [US3] Implement `src/analysis/stats.py` to perform **Wilcoxon signed-rank test** on accuracy distributions (FR-005, SC-004). **Note**: This requirement overrides any references to McNemar's test in plan.md summary; Wilcoxon is mandated by Spec FR-005 for continuous accuracy distributions.
- [ ] T028 [US3] Implement `src/analysis/stats.py` to calculate "memory noise" reduction rate (non-conflict patches removed) (FR-006)
- [ ] T029 [US3] Generate final `research.md` report with p-values, accuracy comparisons, and dataset limitation flags if conflicts are scarce
- [ ] T030 [P] [US3] Validate the full pipeline: Data Gen → Heuristic → Agent Run → Stats → Report

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T031 [P] Documentation updates in `docs/` and `README.md` explaining the conflict filtering logic
- [ ] T032 Code cleanup and refactoring of `src/analysis/runner.py` for efficiency
- [ ] T033 [P] Additional unit tests for edge cases (empty conflict list, timeout handling) in `tests/unit/`
- [ ] T034 Run `quickstart.md` validation to ensure reproducibility on a fresh environment
- [ ] T035 Verify checksums for all generated artifacts (datasets, logs) per Constitution Check III

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - **US1 (P1)**: Can start after Foundational.
  - **US2 (P2)**: **Cannot proceed in parallel with US1 implementation**. Must wait for T012 (Conflict Detector) to be merged.
  - **US3 (P3)**: **Cannot proceed in parallel with US2 implementation**. Must wait for T022 (Agent Execution) to produce logs.
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - **Depends on T012** (Conflict Detector) to function correctly
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - **Depends on T022** (Agent Execution) to have log data

### Within Each User Story

- **Implementation (Models/Helpers)** MUST be written before **Tests** can run against them.
- Tests (if included) MUST be written as scaffolding first, but **executed** only after the implementation task (e.g., T012) is complete.
- Services/Agents before Analysis/Reporting
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] (T004, T005, T006, T009) can run in parallel
- Once Foundational phase completes, T012 (Detector) and T019 (All Agent) can run in parallel, but T020 (Conflict Agent) and T018 (Integration Test) must wait for T012.
- All tests for a user story marked [P] can run in parallel (once the implementation exists).
- Different user stories **cannot** be worked on in parallel by different team members if they share hard dependencies (e.g., US2 depends on US1).

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Conflict Detector)
4. **STOP and VALIDATE**: Test User Story 1 independently on synthetic pairs
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Dual Agent Run)
4. Add User Story 3 → Test independently → Deploy/Demo (Statistical Report)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Heuristic)
   - Developer B: User Story 2 (Agent Pipeline - All Variant) - *Can start, but Conflict Variant blocked*
   - Developer C: User Story 3 (Stats Framework) - *Can start, but data blocked*
3. Developer B merges User Story 1 (Heuristic) to complete Conflict Variant
4. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **CRITICAL**: No task may load models in 8-bit/4-bit or require GPU. All models must run on default precision CPU.
- **CRITICAL**: All data must be real or synthetically generated by code (no hardcoded fake data).
- **CRITICAL**: Statistical analysis uses **Wilcoxon signed-rank test** (FR-005).
- **CRITICAL**: Hallucination metric includes **both** incorrect command execution and state misinterpretation (SC-002).