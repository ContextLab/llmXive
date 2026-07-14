# Tasks: llmXive follow-up: extending "AdaPlanBench: Evaluating Adaptive Planning in Large Language Model Age"

**Input**: Design documents from `/specs/001-llmxive-follow-up-extending-adaplanbench/`
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

- [ ] T001 [P] Create `data/raw/` directory
- [ ] T002 [P] Create `data/processed/` directory
- [ ] T003 [P] Create `code/` directory structure including `dataset/`, `agent/`, `analysis/`
- [ ] T004 [P] Create `tests/unit/` and `tests/integration/` directories
- [ ] T005 [P] Initialize Python 3.11 project with `requirements.txt` (transformers, datasets, pandas, statsmodels, scikit-learn, pytest)
- [ ] T006 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T007 Implement `code/config.py` with paths, random seeds, and resource limits (2 vCPU, 7GB RAM)
- [ ] T008 Implement `code/main.py` orchestration script with resource monitor wrapper (logs CPU/RAM per task, fails fast on limit)
- [ ] T009 Create base `code/agent/base.py` abstract agent interface

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Dataset Preparation and Constraint Filtering (Priority: P1) 🎯 MVP

**Goal**: Isolate the specific subset of AdaPlanBench where constraints are revealed progressively (≥5) to establish the independent variable.

**Independent Test**: Load raw dataset, apply filter, verify output count and `constraint_count` field for a sample of 10 tasks against metadata.

### Implementation for User Story 1

- [ ] T010 [US1] Unit test for filter logic in `tests/unit/test_filter.py` (verifies exclusion of <5 constraints)
- [ ] T011 [P] [US1] Integration test for dataset content validation in `tests/integration/test_dataset_content.py` (verifies 'progressive_constraints' schema and 'constraint_count' field presence; Run AFTER T012/T013 implementation)
- [ ] T012 [US1] Implement `code/dataset/loader.py` to fetch AdaPlanBench household tasks from ` (verify dataset contains household tasks and progressive_constraints; if fetch fails, generate a deterministic mock dataset as fallback)
- [ ] T013 [US1] Implement filtering logic in `code/dataset/loader.py` to select tasks with ≥5 progressive constraint reveals
- [ ] T014 [US1] Add `constraint_count` metadata column to filtered output in `data/processed/filtered_tasks.csv`
- [ ] T015 [US1] Implement validation script in `code/dataset/validate_subset.py` to sample 10 tasks and verify constraint counts match original metadata

**Checkpoint**: Filtered dataset ready; independent variable established.

---

## Phase 4: User Story 2 - Dual-Track Agent Execution and Constraint Logging (Priority: P2)

**Goal**: Execute dual-track architecture (SLM generator + deterministic constraint store) and monolithic baseline, logging violations and corrections.

**Independent Test**: Run agent on a known task with a specific constraint violation; verify rule-based module intercepts, corrects, and logs the event.

### Tests for User Story 2

- [ ] T016 [P] [US2] Unit test for `code/agent/resolver.py` in `tests/unit/test_resolver.py` (verifies string matching and negation patterns)
- [ ] T017 [P] [US2] Contract test for execution log schema in `tests/contract/test_execution_log_schema.py`

### Implementation for User Story 2

- [ ] T018 [US2] Implement `code/agent/monolithic.py` (direct SLM prompt) using a CPU-tractable small model (e.g., Phi-mini) in default precision
- [ ] T019 [US2] Implement `code/agent/constraint_store.py` (deterministic key-value store for active constraints)
- [ ] T020 [US2] Implement `code/agent/resolver.py` with exact string matching, case-insensitive substring matching, and explicit negation patterns (FR-007)
- [ ] T021 [US2] Implement `code/agent/dual_track.py` to orchestrate generator, store, and resolver; log "false_negative" if intent parsing fails (FR-008)
- [ ] T022 [US2] Implement logic to log "implicit_unverified" for constraints requiring common-sense reasoning, excluding them from primary violation rate (FR-009)
- [ ] T023 [US2] Implement execution loop in `code/main.py` to run both architectures on `data/processed/filtered_tasks.csv`
- [ ] T024 [US2] Generate `data/processed/execution_traces.csv` containing architecture type, constraint count, violation boolean, and final score

**Checkpoint**: Dual-track and monolithic agents executed; violation logs generated.

---

## Phase 5: User Story 3 - Statistical Analysis and Validation (Priority: P3)

**Goal**: Perform GLMM analysis and human annotation validation to determine if explicit constraint tracking mitigates performance degradation.

**Independent Test**: Run GLMM on logs; verify output includes fixed effect estimates, p-values, and convergence diagnostics.

### Tests for User Story 3

- [ ] T025 [P] [US3] Unit test for GLMM model fitting in `tests/unit/test_glmm.py` (sanity check on synthetic data)
- [ ] T026 [P] [US3] Integration test for power analysis in `tests/integration/test_power_analysis.py`

### Implementation for User Story 3

- [ ] T027 [US3] Implement `code/analysis/power.py` to perform power analysis on filtered subset (target: detect medium effect size f² ≥ 0.15, power ≥ 0.80); if power < 0.80, abort execution, log error to `data/logs/power_analysis_fail.log` with message "Insufficient power for GLMM" (FR-011)
- [ ] T028 [US3] Implement `code/analysis/glmm.py` to fit GLMM with binomial link function testing interaction between "number of constraints" and "architecture"
- [ ] T029 [US3] Implement `code/hash_artifacts.py` to compute SHA-256 hashes for existing files in `data/` (if any exist) and update state YAML (Constitution Principle V)
- [ ] T030 [US3] Implement `code/dataset/annotator.py` CLI to randomly select 50 tasks from `data/processed/filtered_tasks.csv` (T014 output); Pre-check: verify `data/processed/filtered_tasks.csv` exists; output `data/processed/annotation_sample.csv` and generate a printable PDF report with unique task IDs for human review (FR-010)
- [ ] T031 [US3] Implement script to compare rule-based detection results against human-annotated ground truth (FR-010, FR-005)
- [ ] T032 [US3] Generate `data/processed/statistical_results.json` with p-values, effect sizes, and convergence status; structure must match schema in `contracts/statistical-results.schema.yaml`
- [ ] T033 [US3] Generate final report in `research.md` comparing dual-track vs. monolithic violation rates across constraint counts

**Checkpoint**: Statistical significance established; hypothesis tested.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T034 [P] Refactor `code/agent/resolver.py` to reduce cyclomatic complexity to <15 by extracting method `parse_intent` and `match_constraint` to separate modules
- [ ] T035 [P] Add unit tests for edge cases in `tests/unit/` including: implicit constraint handling (no violation logged), parsing failures (false_negative logged), and empty constraint lists
- [ ] T036 Run `quickstart.md` validation and ensure all steps complete within 6 hours on CI

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 (filtered data) for execution
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 (execution logs) for analysis

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US1, US2, and US3 implementation can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Unit test for filter logic in tests/unit/test_filter.py"
Task: "Integration test for dataset content validation in tests/integration/test_dataset_content.py"

# Launch implementation tasks:
Task: "Implement code/dataset/loader.py to fetch AdaPlanBench"
Task: "Implement filtering logic in code/dataset/loader.py"
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
 - Developer A: User Story 1 (Data)
 - Developer B: User Story 2 (Agent Execution)
 - Developer C: User Story 3 (Analysis)
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
- **Critical Constraint**: All tasks must run on free CPU-only CI (2 vCPU, 7GB RAM, no GPU). No 8-bit quantization or large model training.