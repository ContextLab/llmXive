# Tasks: Co-Evolving Policy Distillation

**Input**: Design documents from `/specs/001-coevolving-policy-distillation/`
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

- [X] T001a [P] Create directory structure: `src/generators`, `src/agents`, `src/analysis`, `src/utils`, `tests/`, `data/`, `data/results/`
- [X] T001b [P] Create empty `__init__.py` files in all `src/` and `tests/` subdirectories
- [X] T001c [P] Initialize Python 3.11 project with dependencies: `sympy`, `networkx`, `numpy`, `scipy`, `pytest` in `pyproject.toml`
- [X] T001d [P] Configure linting (ruff/flake8) and formatting (black) tools in `pyproject.toml` and `.pre-commit-config.yaml`
- [X] T001e [P] Create `.gitignore` for Python and data artifacts

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement configuration loader in `src/utils/config.py` to handle seeding, generation counts, and rule evaluation budgets
- [ ] T005 [P] Implement checksum utility in `src/utils/checksums.py` to generate SHA-256 hashes for data artifacts and manage `data/checksums.json`
- [ ] T006 [P] Create base abstract agent class in `src/agents/base_agent.py` defining the interface for rule-set management and evaluation
- [ ] T007 [P] Implement CLI skeleton in `src/cli.py` (entry point only, no logic) to establish command structure
- [ ] T008 [P] Implement schema validators in `tests/contract/` based on existing contracts (`contracts/`) to validate `dataset`, `agent_state`, and `result` JSON structures

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Synthetic Task Environment Generation (Priority: P1) 🎯 MVP

**Goal**: Generate reproducible synthetic datasets of propositional logic proofs and grid-world navigation tasks with distinct rule sets, including held-out test instances.

**Independent Test**: The system can be tested by running the generator script and verifying that the output contains valid logical proofs and navigable grids with unique, identifiable rule signatures for each task domain.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T009 [P] [US1] Contract test for generated proof validity in `tests/contract/test_dataset_schema.py`
- [ ] T010 [P] [US1] Unit test for grid solvability and rule isolation in `tests/unit/test_logic_generation.py` <!-- FAILED: unspecified -->

### Implementation for User Story 1

- [~] T011 [P] [US1] Implement propositional logic proof generator in `src/generators/logic_generator.py` using `sympy` to create valid proofs from parameterized axioms, including retry logic (with a bounded number of retries) for invalid generations
- [~] T012 [P] [US1] Implement grid-world navigation generator in `src/generators/grid_generator.py` using `networkx` to create solvable grids with non-overlapping rule sets (e.g., "avoid red", "diagonal paths"), including retry logic (with a bounded number of retries) for invalid generations
- [~] T013 [US1] Implement held-out test instance generator in `src/generators/test_generator.py` to create `data/test_instances.json` using distinct seeds from training data, ensuring these instances are strictly separate from the training set for FR-005 compliance and providing the required baseline measurement data
- [~] T014 [US1] Implement data writing logic to save generated training datasets to `data/` with checksums recorded in `data/checksums.json`
- [~] T015 [US1] Implement validation script `src/analysis/validate_dataset.py` that checks generated datasets and exits with code 1 if validity < 99% for proofs or solvability < 99% for grids
- [~] T015b [US1] Implement and execute the validation script in `src/cli.py` as a mandatory blocking gate before any training (Phase 4) can commence, ensuring SC-005 is enforced in the pipeline flow and preventing training on invalid data

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Distillation Strategy Execution Engine (Priority: P2)

**Goal**: Execute three distinct agent training conditions (Sequential, Mixed-task, Co-evolving) with strict parity in total data exposure.

**Independent Test**: The system can be tested by running the three conditions in isolation and verifying that the total number of rule evaluations per task is identical across all three runs, while the internal logic of the co-evolving agent successfully exchanges rule-sets between sub-populations.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [~] T016 [P] [US2] Contract test for rule-evaluation counter parity in `tests/contract/test_result_schema.py`
- [~] T017 [P] [US2] Unit test for bidirectional exchange logic in `tests/unit/test_agent_conditions.py`

### Implementation for User Story 2

- [~] T018 [P] [US2] Implement `SequentialAgent` in `src/agents/sequential_agent.py` to train on one task domain block at a time
- [~] T019 [P] [US2] Implement `MixedAgent` in `src/agents/mixed_agent.py` to train on mixed task domains randomly per generation
- [~] T020 [P] [US2] Implement `CoevolvingAgent` in `src/agents/coevolving_agent.py` to manage sub-populations and execute bidirectional rule-set exchanges at every generation step
- [~] T021 [US2] Implement selection pressure logic in `src/agents/coevolving_agent.py` to discard non-performing rule-sets and prevent population collapse
- [~] T022 [US2] Implement `src/utils/parity_checker.py` to enforce a hard integer cap on rule evaluations *during* the generation loop (clamping/capping) to ensure exact parity before analysis, and raise `ParityError` if checksums mismatch across conditions, implementing the enforcement logic required by SC-002
- [~] T023 [US2] Implement training loop logic in `src/cli.py` (training component only) that utilizes `parity_checker.py` to ensure exact parity of total rule evaluations across all three conditions (FR-002)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Catastrophic Forgetting Measurement & Analysis (Priority: P3)

**Goal**: Evaluate trained agents on held-out test instances, calculate forgetting rates, and perform statistical comparison (Mixed-Design ANOVA).

**Independent Test**: The system can be tested by taking a pre-trained agent, running it against a held-out test set, and verifying that the calculated forgetting rate is mathematically derived from the difference between initial and final accuracy scores.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [~] T024 [P] [US3] Contract test for forgetting metric schema in `tests/contract/test_result_schema.py`
- [~] T025 [P] [US3] Integration test for full statistical analysis pipeline in `tests/integration/test_full_pipeline.py`

### Implementation for User Story 3

- [~] T026 [P] [US3] Implement evaluation logic in `src/analysis/forgetting_metrics.py` to calculate accuracy drop from initial single-task to final multi-task performance
- [~] T027 [P] [US3] Implement statistical analysis module in `src/analysis/statistical_tests.py` using `scipy` and `statsmodels` to perform a Mixed-Design ANOVA (repeated measures) to account for within-subjects factors across sequential, mixed, and co-evolving conditions, followed by post-hoc Tukey tests to compare forgetting rates, strictly adhering to Constitution Principle VII
- [~] T029 [US3] Implement batch runner in `src/cli.py` (orchestration component) to execute 30+ independent runs per condition with unique seeds, generating the dataset required for SC-004 statistical power and ensuring the data exists for the ANOVA
- [~] T030 [US3] Implement data aggregation logic to collect results from the batch runner output in `data/results/`, verifying that the number of runs meets the SC-004 requirement (N ≥ 30) before proceeding to analysis
- [~] T031 [US3] Implement retention rate calculation in `src/analysis/forgetting_metrics.py` to compute and store raw retention rates of distinct logical rules for Co-evolving vs Mixed-task conditions (SC-003)
- [~] T032 [US3] Implement comparison logic in `src/analysis/statistical_tests.py` to compare retention rates between Co-evolving and Mixed-task conditions
- [~] T033 [US3] Implement report generation to output forgetting rates, ANOVA results (p-values), and retention comparisons to `data/results/forgetting_analysis.json`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [~] T034 [P] Implement full CLI logic in `src/cli.py` to orchestrate the complete pipeline: generation -> validation gate (T015b) -> training (T023) -> batch running (T029) -> analysis (T027-T033), integrating all previous components
- [~] T035 [P] Documentation updates in `docs/` and `quickstart.md` with examples of running the 3 conditions
- [~] T036 Code cleanup and refactoring to ensure type hints and docstrings are complete <!-- ATOMIZE: requested -->
- [~] T037 Performance optimization to ensure a sufficient number of runs complete within the CI time limit on a limited number of CPU cores
- [ ] T038 [P] Additional unit tests for edge cases (logical contradictions, floating-point drift) in `tests/unit/`
- [ ] T039 Run `quickstart.md` validation to ensure end-to-end reproducibility

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

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories. **Produces the data required by US2 and US3.**
- **User Story 2 (P2)**: Can start after Foundational (Phase 2). **Consumes data from US1; produces trained agents for US3.**
- **User Story 3 (P3)**: Can start after Foundational (Phase 2). **Consumes agents from US2 and test data from US1.**

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
Task: "Contract test for generated proof validity in tests/contract/test_dataset_schema.py"
Task: "Unit test for grid solvability and rule isolation in tests/unit/test_logic_generation.py"

# Launch all models for User Story 1 together:
Task: "Implement propositional logic proof generator in src/generators/logic_generator.py"
Task: "Implement grid-world navigation generator in src/generators/grid_generator.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (verify data validity and checksums)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (ensure parity checks pass)
4. Add User Story 3 → Test independently → Deploy/Demo (verify statistical output)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Data Generation)
 - Developer B: User Story 2 (Agent Training)
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
- **Critical Constraint**: All tasks must run on CPU-only CI with a limited number of cores and constrained memory.. No GPU, no 8-bit quantization, no large model loading. Use `sympy`, `networkx`, and `scipy` exclusively.