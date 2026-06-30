# Tasks: Reproduce & Validate EffOPD On-Policy Distillation

**Input**: Design documents from `/specs/597-reproduce-effopd-validation/`
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

- [X] T001 [P] Create source directories: `Analysis/`, `Analysis/eval/`, `Analysis/utils/`
- [X] T002 [P] Create test directories: `tests/`, `tests/contract/`, `tests/integration/`, `tests/unit/`
- [X] T003 [P] Create data and artifact directories: `data/`, `data/gsm8k/`, `data/aime24/`, `artifacts/`
- [X] T004 [P] Create documentation directories: `docs/`, `scripts/`
- [X] T005 [P] Initialize Python 3.10+ environment with CPU-only `torch`, `transformers`, `datasets`, `scikit-learn`, `numpy`, `pandas` in `requirements.txt`
- [X] T006 [P] Configure `git` to ignore large artifacts in `.gitignore` (keep `artifacts/` tracked only for small JSON/CSV outputs)
- [X] T007 [P] Setup `pytest` configuration in `tests/conftest.py` for contract and integration testing

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T008 [P] Implement `Analysis/utils/memory_guard.py` to enforce ≤7 GB RAM usage via proactive dataset sampling and chunked loading (FR-005)
- [X] T009 [P] Implement `Analysis/utils/prep_data.py` to download and sample `gsm8k` (≤500 samples) and `aime24` (≤50 samples) to `data/`, including error logging for download failures (FR-005, Edge Case)
- [X] T010 Implement `Analysis/utils/simulate_step.py` to perform a single CPU-tractable training step using `Qwen2.5-0.5B-Instruct` on `data/gsm8k/test.jsonl` with cross-entropy loss to generate `artifacts/delta_w.pt` (EffOPD proxy) and `artifacts/sft_delta_w.pt` (Baseline). **Note: This is a proxy for the on-policy step to satisfy FR-001/FR-002 under resource constraints.** (FR-001, FR-002)
- [X] T011 [P] Create `tests/contract/test_artifact_schemas.py` to validate output formats of SVD, Rank, and Eval scripts (SC-001, SC-002, SC-003)
- [X] T012 [P] Create `tests/unit/test_memory_guard.py` to verify sampling logic stays within 7 GB limit under mock load (FR-005)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Environment Initialization and Dependency Resolution (Priority: P1) 🎯 MVP

**Goal**: Initialize the reproduction environment within free-tier constraints without triggering GPU errors.

**Independent Test**: Execute the environment setup script on a fresh runner; verify `pip install` completes without CUDA errors and `EffOPD` submodule exists.

### Tests for User Story 1

- [X] T013 [P] [US1] Contract test for CUDA-free import in `tests/contract/test_cuda_free_import.py` (Verifies FR-004)
- [X] T014 [P] [US1] Integration test for submodule presence in `tests/integration/test_submodule_exists.py`

### Implementation for User Story 1

- [X] T015 [US1] Create `scripts/setup_env.sh` to install dependencies filtering out `bitsandbytes` and forcing CPU `torch` (FR-004)
- [X] T016 [US1] Implement `scripts/init_submodule.sh` to fetch `EffOPD` from `external/EffOPD` using a valid git URL (e.g., `) (FR-004)
- [X] T017 [US1] Add validation logic in `scripts/setup_env.sh` to fail immediately if `ImportError: No module named 'bitsandbytes'` is detected (FR-004)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Execution of Lightweight Validation Scripts (Priority: P1)

**Goal**: Execute SVD and Rank analysis scripts on sampled data to confirm mechanism validity.

**Independent Test**: Run `svd.py` and `upd_rank.py` on `gsm8k` subset; verify output files contain valid numerical data.

### Tests for User Story 2

- [X] T018 [P] [US2] Contract test for SVD output schema in `tests/contract/test_svd_schema.py` (Verifies SC-001)
- [X] T019 [P] [US2] Contract test for Rank output schema in `tests/contract/test_rank_schema.py` (Verifies SC-002)
- [X] T020 [P] [US2] Integration test for end-to-end SVD execution in `tests/integration/test_svd_execution.py`

### Implementation for User Story 2

- [X] T021 [US2] Implement `Analysis/eval/svd.py` to compute singular values of `artifacts/delta_w.pt` (generated by T010) and output `artifacts/svd_results.csv` (FR-001)
- [X] T022 [US2] Implement `Analysis/eval/upd_rank.py` to compute rank concentration metrics on `artifacts/delta_w.pt` and output `artifacts/upd_rank_results.csv` (FR-002)
- [X] T023 [US2] Add chunked processing logic in `svd.py` to handle potential memory spikes on larger samples (FR-005)
- [X] T024 [US2] Ensure `upd_rank.py` outputs `concentration_score` in range [0.0, 1.0] (SC-002)
- [X] T025 [US2] Add timing instrumentation to `svd.py` and `upd_rank.py` to verify completion within 45 minutes (FR-001, FR-002)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Full Pipeline Execution and Artifact Generation (Priority: P2)

**Goal**: Execute reasoning evaluation and baseline comparison to validate output formats and theoretical efficiency.

**Independent Test**: Run `reasoning_eval.py` on `aime24` subset; verify output JSON contains non-null `Pass@k` metrics.

### Tests for User Story 3

- [X] T026 [P] [US3] Contract test for Reasoning Eval JSON schema in `tests/contract/test_reasoning_schema.py` (Verifies SC-003)
- [X] T027 [P] [US3] Integration test for full pipeline execution in `tests/integration/test_full_pipeline.py`

### Implementation for User Story 3

- [X] T028 [US3] Implement `Analysis/eval/reasoning_eval.py` to run inference on `data/aime24/test.jsonl` using `Qwen2.5-0.5B-Instruct` and output `artifacts/reasoning_results.json` (FR-003)
- [X] T029 [US3] Implement `Analysis/eval/baseline_comparison.py` to compare EffOPD rank/FLOPs against SFT (from `artifacts/sft_delta_w.pt` generated in T010) and Null Baseline (zero-matrix of same shape) to satisfy FR-006 (SC-006) (FR-006, SC-006)
- [X] T030 [US3] Implement `Analysis/utils/timeout_guard.py` as a Python context manager (`TimeoutGuard`) to enforce the 4-hour total runtime limit for the full pipeline, raising `TimeoutError` if exceeded (SC-004)
- [X] T031 [US3] Ensure `reasoning_eval.py` handles missing files with clear error codes (Edge Case: Data Availability)
- [X] T032 [US3] Verify `reasoning_results.json` contains `Pass@1`, `Pass@5`, `Pass@10` with numerical values (SC-003)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T033 [P] Documentation updates in `docs/` summarizing the CPU-only validation strategy
- [X] T034 Code cleanup and refactoring of `Analysis/utils/` scripts
- [X] T035 [P] Add `Makefile` targets for `make setup`, `make run-svd`, `make run-eval`, `make test`
- [X] T036 [P] Run `quickstart.md` validation to ensure all scripts are documented correctly
- [X] T037 [P] Final verification: Run full pipeline on GitHub Actions runner to confirm zero CUDA errors and ≤7 GB RAM usage

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - **Depends on T010 (Delta W generation)** to run SVD/Rank
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on T009 (Data Prep), T010 (Delta W), T022 (Rank Analysis), and T029 (Baseline Comparison)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Utilities before scripts
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] (T008, T009, T011, T012) can run in parallel
- **T010 (Simulation) is NOT parallel ([P] removed) because it generates input for T021/T022**
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 2

```bash
# Launch all tests for User Story 2 together:
Task: "Contract test for SVD output schema in tests/contract/test_svd_schema.py"
Task: "Contract test for Rank output schema in tests/contract/test_rank_schema.py"

# Launch implementation tasks in parallel (after data prep AND simulation):
Task: "Implement Analysis/eval/svd.py"
Task: "Implement Analysis/eval/upd_rank.py"
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
 - Developer A: User Story 1 (Env Setup)
 - Developer B: User Story 2 (SVD/Rank Scripts)
 - Developer C: User Story 3 (Eval Scripts)
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
- **CRITICAL**: All tasks MUST run on CPU-only, free-tier GitHub Actions (limited vCPU, constrained RAM, no GPU). No 8-bit quantization or large model training allowed.
- **Execution Order**: T010 (Simulation) MUST complete before T021 (SVD) and T022 (Rank). T022 (Rank) MUST complete before T029 (Baseline Comparison).
- **Parallel Note**: T010 is a blocking dependency for T021/T022/T029 and must NOT be run in parallel with them.