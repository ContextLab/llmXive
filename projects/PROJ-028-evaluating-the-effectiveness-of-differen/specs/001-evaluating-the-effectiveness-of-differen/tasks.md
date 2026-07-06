# Tasks: Evaluating Prompting Strategies for Code Generation

**Input**: Design documents from `/specs/001-evaluate-prompting-strategies/`
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

- [ ] T001 Create project structure per implementation plan: `src/`, `tests/`, `data/`, `data/logs/`, `data/results/`, `data/reports/`, `specs/001-evaluate-prompting-strategies/contracts/`, `state/projects/`
- [ ] T002 Initialize Python 3.11 project with `requirements.txt` (transformers, torch[cpu], datasets, scipy, pytest, psutil)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Implement `src/utils/logging.py` for structured JSON resource logging and `data/logs/` directory setup
- [ ] T005 [P] Implement `src/models/loader.py` with FP32 default; explicitly implement RAM monitoring and automatic model reload to FP16 if usage > 6.5GB (FR-002). Do not use 8-bit/4-bit quantization.
- [ ] T006 [P] Create `src/evaluation/prompts.py` with templates for Zero-shot, Few-shot (3 examples), and Chain-of-Thought
- [~] T007 [P] Implement `src/evaluation/sandbox.py` using `resource.setrlimit` with hardcoded 10s timeout and A constrained memory limit will be imposed to evaluate system performance under resource restrictions. per subprocess (FR-004).
- [~] T008 Create `src/evaluation/metrics.py` for `pass@1` and `pass@10` calculation and aggregation logic
- [~] T009 [P] Implement `src/utils/data_loader.py` to fetch `google-research-datasets/mbpp`, filter test split, and select a representative subset of tasks. Compute SHA-256 checksum and record it in the `artifact_hashes` map of `state/projects/PROJ-028-evaluating-the-effectiveness-of-differen.yaml` (Constitution Principle V).
- [~] T010 [P] Create JSON schemas in `specs/001-evaluate-prompting-strategies/contracts/` (mbpp_task.schema.yaml, evaluation_result.schema.yaml)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Zero-Shot Baseline Execution (Priority: P1) 🎯 MVP

**Goal**: Establish a reproducible performance baseline using Zero-shot prompting on 3 seeds, generating k=10 samples per task.

**Independent Test**: Run pipeline with `--strategy zero-shot` and `--seeds` (multiple random seeds) on 50 tasks; verify valid JSON reports with pass@k scores (k=10) and no timeout crashes.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [~] T011 [P] [US1] Contract test for result schema validation in `tests/contract/test_result_schema.py`
- [~] T012 [P] [US1] Integration test for sandbox timeout handling in `tests/integration/test_sandbox_timeout.py`
- [~] T013 [P] [US1] Unit test for code block extraction regex in `tests/unit/test_prompt_parser.py`

### Implementation for User Story 1

- [~] T014 [US1] Implement `src/evaluation/runner.py` core loop: load task -> prompt (Zero-shot) -> generate -> execute -> record result
- [~] T014b [US1] **Instrument execution logic** in `src/evaluation/runner.py` (or `sandbox.py`) to explicitly count and log **execution timeouts** and **parsing failures** for every task, ensuring data is available for SC-004/SC-005 reporting.
- [~] T015 [US1] Integrate random seed management into `src/evaluation/runner.py` execution flow
- [~] T015b [US1] **Orchestrate 3 independent random seed runs** for Zero-shot strategy, ensuring the pipeline executes 3 distinct iterations and outputs to `data/results/zero_shot_seed_{seed}.json`
- [~] T016 [US1] Implement error handling in `src/evaluation/runner.py` to catch runtime errors in generated code and mark as failed without crashing
- [~] T017 [US1] Add memory monitoring hook in `src/evaluation/runner.py` to trigger GC or precision switch if RAM > 6.5GB
- [~] T018 [US1] Write results to `data/results/zero_shot_seed_{seed}.json` (for each of multiple seeds) with pass/fail status, execution time, and error logs <!-- ATOMIZE: requested -->
- [~] T021b [US1] **Implement k=10 sample generation for Zero-shot** in `src/evaluation/runner.py` to ensure `pass@10` calculation is possible for the baseline strategy as per FR-003. This is a mandatory requirement, not optional.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Few-Shot and Chain-of-Thought Comparison (Priority: P2)

**Goal**: Execute Few-shot and CoT strategies with k=10 samples per task for comparative analysis.

**Independent Test**: Run pipeline with `--strategy few-shot` and `--strategy cot`; verify JSON reports contain a set number of samples per task and calculated pass@k scores.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [~] T019 [P] [US2] Contract test for Few-shot prompt structure in `tests/unit/test_fewshot_prompt.py`
- [~] T020 [P] [US2] Integration test for CoT reasoning extraction in `tests/integration/test_cot_extraction.py`

### Implementation for User Story 2

- [~] T021 [P] [US2] Update `src/evaluation/prompts.py` to inject a small set of examples for Few-shot and reasoning instructions for CoT
- [~] T022 [US2] Modify `src/evaluation/runner.py` to generate **k=10 independent samples** per task for **all strategies** (Zero-shot, Few-shot, and CoT) to enable `pass@10` comparison
- [~] T022b [US2] **Instrument execution logic** in `src/evaluation/runner.py` (or `sandbox.py`) to explicitly count and log **execution timeouts** and **parsing failures** for every task in Few-shot and CoT runs, ensuring data is available for SC-004/SC-005 reporting.
- [~] T023 [US2] Implement code block extraction logic in `src/evaluation/prompts.py` to handle CoT outputs (extract final code block) <!-- SKIPPED: non-mapping output -->
- [ ] T024 [US2] Update `src/evaluation/metrics.py` to calculate `pass@k` (at least one of k samples passed) for each task
- [ ] T025 [US2] Write results to `data/results/few_shot_seed_{seed}.json` and `data/results/cot_seed_{seed}.json`
- [ ] T025b [US2] **Orchestrate 3 independent random seed runs** for Few-shot and CoT strategies, ensuring the pipeline executes 3 distinct iterations and outputs to `data/results/{strategy}_seed_{seed}.json`
- [ ] T026 [US2] Implement consolidated reporting logic to **aggregate pass/fail outcomes across strategies into a paired dataset structure (contingency table) suitable for McNemar's test** (SC-001), mapping task IDs to results across all three strategies.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis and Resource Reporting (Priority: P3)

**Goal**: Perform McNemar's test on paired outcomes and generate resource utilization reports.

**Independent Test**: Run analysis script on generated JSONs; verify p-value output, mean pass rates, and resource warning flags.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T027 [P] [US3] Unit test for McNemar's test implementation in `tests/unit/test_stats.py`
- [ ] T028 [P] [US3] Integration test for resource log aggregation in `tests/integration/test_resource_logging.py`

### Implementation for User Story 3

- [ ] T029 [P] [US3] Implement `src/analysis/stats.py` with McNemar's test for paired binary outcomes (Zero-shot vs CoT)
- [ ] T030 [US3] Implement `src/analysis/report.py` to aggregate pass rates, calculate means/std, **calculate execution timeout rate and parsing success rate (SC-004/SC-005)** using the counts collected in T014b/T022b, and generate final summary JSON
- [ ] T031 [US3] Integrate `psutil`/`resource` monitoring in `src/utils/logging.py` to track peak RAM and total wall-clock time
- [ ] T032 [US3] Add logic to `src/analysis/report.py` to flag "Resource Constraint Warning" if RAM > 7GB or time > 6h (but do not stop execution)
- [ ] T033 [US3] Generate final report `data/reports/analysis_summary.json` containing p-values, metrics, **timeout_rate**, **parsing_success_rate**, and resource logs
- [ ] T034 [US3] Implement CLI entry point in `src/cli/main.py` to orchestrate the full pipeline (Load -> Evaluate -> Analyze)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T035 [P] Documentation updates in `specs/001-evaluate-prompting-strategies/quickstart.md`
- [ ] T036 Code cleanup and refactoring of `src/evaluation/runner.py`
- [ ] T037 Performance optimization: Ensure batch size 1 is enforced to prevent OOM
- [ ] T038 [P] Additional unit tests for edge cases (missing unit tests in MBPP) in `tests/unit/`
- [ ] T039 Security hardening: Verify sandbox isolation prevents file system access outside temp dir
- [ ] T040 Run quickstart.md validation to ensure reproducibility on clean environment

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
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on data from US1 and US2 for statistical comparison

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Utilities before services
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
Task: "Contract test for result schema validation in tests/contract/test_result_schema.py"
Task: "Integration test for sandbox timeout handling in tests/integration/test_sandbox_timeout.py"

# Launch all models for User Story 1 together:
Task: "Implement src/evaluation/runner.py core loop"
Task: "Integrate random seed management into src/evaluation/runner.py"
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
- **CRITICAL**: All tasks must run on CPU-only CI (a limited number of cores, constrained RAM).. No GPU, no 8-bit quantization.
- **CRITICAL**: Dataset must be fetched from real HuggingFace source, never fabricated.
- **CRITICAL**: Execution order must respect data flow (Download -> Evaluate -> Analyze).