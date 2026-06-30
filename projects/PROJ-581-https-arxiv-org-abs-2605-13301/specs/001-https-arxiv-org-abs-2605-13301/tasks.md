# Tasks: Reproduce & Validate SU-01 Olympiad Reasoning

**Input**: Design documents from `/specs/581-reproduce-su01-olympiad/`
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

- [X] T001 Create project structure: `src/`, `tests/`, `scripts/`, `output/`, `docs/`, `external/` directories and `__init__.py` files

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [X] T004 Initialize git submodule `external/SU-01` and verify file tree presence
- [X] T005 [P] Implement CPU-only dependency installation script (`scripts/setup_env.sh`)
- [X] T006 [P] Setup environment configuration management for CPU-only flags
- [X] T008 Create `scripts/logger.py` with `get_logger` function returning a Rich logger, configuring logging to output to `output/logs/pipeline.log`
- [X] T009 Setup timeout enforcement mechanism (configurable time limit per script)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Validate Submodule Integrity and Environment Bootstrapping (Priority: P1) 🎯 MVP

**Goal**: Initialize the `SU-01` submodule and ensure a CPU-only environment can import evaluation scripts without CUDA errors.

**Independent Test**: The CI job initializes the submodule, installs dependencies, and successfully imports `su01_eval` and `su01_train_slime` without `ImportError` or CUDA exceptions.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Contract test `test_submodule_init` in `tests/test_submodule.py` that asserts `external/SU-01` exists and contains `su01-eval`
- [X] T011 [P] [US1] Integration test `test_env_bootstrap` in `tests/test_env_bootstrap.py` that asserts `import su01_eval` succeeds and `torch.cuda.is_available() is False`

### Implementation for User Story 1

- [X] T012 [P] [US1] Create `.gitmodules` configuration for `external/SU-01`
- [X] T013 [US1] Implement `scripts/setup_env.sh` to install `torch` with `--index-url, `transformers` (pinned version), and `accelerate` (pinned version) ensuring NO CUDA dependencies are installed
- [X] T014 [US1] Implement validation script `scripts/verify_imports.py` to check `import su01_eval` works
- [X] T015 [US1] Implement `scripts/verify_direct_gen.py` to run `direct_gen.py --help` and confirm CLI availability
- [X] T016 [US1] Modify `scripts/setup_env.sh` to check for CUDA availability and exit 0 with warning if missing
- [X] T017 [US1] Add logging for environment setup and import verification steps

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Execute Direct Inference on Verifiable Benchmarks (Priority: P2)

**Goal**: Run `SU` inference on a small subset of problems from `imo25.jsonl` or `usamo2026.jsonl`. and verify the evaluation pipeline produces structured results.

**Independent Test**: The system runs `direct_gen.py` on a set of problems, generates output files, and `eval_verifiable_answer.py` produces a JSON result with a `status` field.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Contract test `test_inference_output_format` in `tests/contract/test_inference_output.py` that asserts output JSON contains `status` and `reason` keys
- [X] T019 [P] [US2] Integration test `test_inference_eval_flow` in `tests/integration/test_inference_eval.py` that asserts end-to-end flow produces `output/results.json`

### Implementation for User Story 2

- [X] T020 [P] [US2] Create sample dataset fetcher script `scripts/fetch_sample_dataset.py` (targets `imo25.jsonl` subset)
- [X] T021 [US2] Implement `scripts/run_subset_eval.sh` to orchestrate `direct_gen.py` with 2-problem limit, gated on weight existence
- [X] T022 [US2] Modify `scripts/run_subset_eval.sh` to check for model weights; if missing, skip inference and call `scripts/update_results.py` to set `status='FAILED'` and `reason='MISSING_WEIGHTS'` in `output/results.json`
- [X] T023 [US2] Implement `scripts/run_eval.py` to wrap `eval_verifiable_answer.py` and aggregate results into `output/results.json`
- [X] T024 [US2] Ensure `scripts/run_subset_eval.sh` execution is gated on the successful completion of T014/T015 (environment validation)
- [X] T025 [US2] Enforce -minute timeout on `run_subset_eval.sh` and handle `MemoryError` explicitly

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Generate Reproduction Artifacts and Validation Report (Priority: P3)

**Goal**: Aggregate logs, metrics, and artifacts to generate `reproduction_report.md` with a clear verdict.

**Independent Test**: The system produces `reproduction_report.md` containing execution logs, observed metrics, and a "Verdict" field.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T026 [P] [US3] Contract test `test_report_schema` in `tests/contract/test_report_schema.py` that asserts `reproduction_report.md` contains "Verdict" field with valid values
- [X] T027 [P] [US3] Integration test `test_report_gen_flow` in `tests/integration/test_report_gen.py` that asserts report generation flow produces valid `reproduction_report.md`

### Implementation for User Story 3

- [X] T028 [P] [US3] Create `scripts/generate_report.sh` to aggregate logs and metrics
- [X] T029 [US3] Implement `scripts/compile_report.py` to parse `results.json` and logs into `reproduction_report.md`
- [X] T030 [US3] Modify `scripts/compile_report.py` to set the Verdict field based on `results.json` status: if status is 'FAILED' and reason is 'MISSING_WEIGHTS', set Verdict to 'Failed'; otherwise, use 'Reproduced' or 'Partially Reproduced' as per spec SC-003
- [X] T031 [US3] Copy files from `external/SU-01/output/figures/` to `output/artifacts/` in `scripts/generate_report.sh`
- [X] T032 [US3] Add validation to ensure report contains required sections: Token Distribution, Pass Rates, Verdict
- [X] T033 [US3] Add logging for report generation steps and final artifact paths

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T034 [P] Update `docs/README.md` with installation steps and create `docs/CONTRIBUTING.md`
- [X] T035 Refactor `scripts/setup_env.sh` to use a single function for dependency installation
- [X] T036 Optimize `scripts/run_subset_eval.sh` to reduce peak memory usage to <6GB.
- [X] T037 [P] Additional unit tests (if requested) in `tests/unit/`
- [X] T038 Add input validation to `scripts/run_subset_eval.sh` to reject non-existent file paths and invalid JSONL lines
- [X] T039 Verify `docs/quickstart.md` exists, is non-empty, and contains valid Markdown syntax

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 for environment stability
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 for result data

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
Task: "Contract test for submodule initialization in tests/test_submodule.py"
Task: "Integration test for CPU-only environment bootstrap in tests/test_env_bootstrap.py"

# Launch all models for User Story 1 together:
Task: "Create.gitmodules configuration for external/SU-01"
Task: "Implement scripts/setup_env.sh to install torch (CPU-only), transformers, accelerate"
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
- **Critical Constraint**: No task may attempt to load the 30B model without first checking for weight existence and enforcing CPU-only constraints. If weights are missing, the task must log a warning, skip inference, and record a 'FAILED' status with reason 'MISSING_WEIGHTS' in the results JSON.