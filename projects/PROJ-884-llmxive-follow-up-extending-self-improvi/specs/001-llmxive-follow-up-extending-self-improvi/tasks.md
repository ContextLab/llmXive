# Tasks: llmXive follow-up: extending "Self-Improving Language Models with Bidirectional Evolutionary Search"

**Input**: Design documents from `/specs/001-symbolic-bes/`
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

- [ ] T001a Create project directory structure per implementation plan by executing: `mkdir -p projects/PROJ-884-llmxive-follow-up-extending-self-improvi/{data/raw,data/processed,code/{dataset,symbolic,bes,analysis,utils},tests/{unit,integration}}`

- [ ] T001b Initialize git repository and configure basic `.gitignore` for Python artifacts

- [ ] T002a Initialize Python 3.11 virtual environment in `projects/PROJ-884-llmxive-follow-up-extending-self-improvi/` <!-- FAILED: unspecified -->

- [ ] T002b Install dependencies in `requirements.txt` containing: `scikit-learn==1.3.0`, `numpy==1.24.0`, `transformers==4.35.0`, `datasets==2.14.0`, `pyyaml==6.0.1`, `pytest==7.4.0`, `optimum==1.13.0`. **Constraint**: If `research.md` exists, read version constraints from it; otherwise, default to versions listed in `plan.md` to ensure determinism.

- [ ] T003 [P] Configure linting (flake8/black) and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Setup data directory structure: `data/raw/` for immutable puzzles, `data/processed/` for logs/results

- [~] T005 [P] Implement base logging infrastructure in `code/__init__.py` to capture wall-clock time and resource usage; output must be JSON format to `data/processed/experiment.log` with fields: `timestamp`, `wall_clock`, `resource_usage`

- [~] T006 [P] Setup random seed management utility in `code/utils/seed.py` for reproducibility

- [~] T007 Create base configuration loader in `code/config.py` to handle experiment parameters (population size, generations)

- [~] T008 Setup error handling framework by creating `code/exceptions.py` defining custom exception classes for `PARSE_FAILURE`, `CONTRADICTION_DETECTED`, and `VERIFIER_ERROR` (to handle internal verifier failures, addressing robustness gap)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Dataset Construction and Symbolic Verification Pipeline (Priority: P1) 🎯 MVP

**Goal**: Instantiate a dataset of logic/arithmetic puzzles with deterministic Python verifiers capable of validating solution paths without LLMs.

**Independent Test**: Run verification scripts on a known set of correct and incorrect solutions to ensure high accuracy in classification before the LLM or evolutionary loop is engaged.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST (TDD), ensure they FAIL before implementation. Do NOT mark as [P] as they must precede implementation.

- [~] T009 [US1] Contract test for `code/dataset/generator.py` in `tests/unit/test_generator.py::test_generator_handles_empty_input`

- [~] T010 [US1] Unit test for `code/dataset/verifier.py` with known valid/invalid solutions in `tests/unit/test_verifier.py::test_verifier_rejects_invalid_solution`

### Implementation for User Story 1

- [~] T011 [P] [US1] Implement `code/dataset/generator.py` to create logic puzzles (Sudoku variants, constrained pathfinding) with systematic complexity scaling (N=10..500)

- [~] T013 [US1] Curate an initial dataset of logic/arithmetic puzzles of sufficient size to support preliminary method validation. in `data/raw/` by running `generator.py`; output must follow the JSON schema defined in `../contracts/dataset.schema.yaml` (relative path)

- [~] T012 [US1] Implement `code/dataset/verifier.py` to execute deterministic validation logic for each puzzle instance, returning boolean validity and specific constraint violation codes (e.g., `DUPLICATE_ROW`, `INVALID_PATH`) within 100ms. **Note**: T012 validates the code, T013 generates the data.

- [~] T014 [US1] Add checksum validation for all files in `data/raw/` to ensure data integrity (Principle III)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Hybrid Evolutionary Search Execution (Priority: P2)

**Goal**: Execute the BES framework where the forward step uses a small CPU-tractable LLM and the backward step is replaced by a symbolic planner.

**Independent Test**: Run the evolutionary loop on a subset of puzzles and verify that the symbolic planner generates sub-goals and the LLM attempts to satisfy them, with the verifier correctly parsing the output.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [~] T016 [P] [US2] Unit test for `code/symbolic/planner.py` with edge cases (non-linear constraints, impossible goals) in `tests/unit/test_symbolic_planner.py::test_planner_handles_nonlinear_constraints`

- [~] T017 [US2] Integration test for the BES loop with a small population in `tests/integration/test_bes_loop.py::test_bes_loop_executes_symbolic_backward_step`. **Note**: Written first (TDD) but executes after T024. <!-- ATOMIZE: requested -->

### Implementation for User Story 2

- [~] T018 [P] [US2] Implement `code/symbolic/parser.py` to convert puzzle constraints into a formal language parseable by the planner

- [~] T019 [US2] Implement `code/symbolic/planner.py` to generate sub-goal decompositions, including logic to detect and flag `CONTRADICTION_DETECTED` or `PARSE_FAILURE`

- [ ] T019b [US2] Implement logging mechanism for exclusion reasons in `code/symbolic/planner.py` to record `PARSE_FAILURE` or `CONTRADICTION_DETECTED` reasons as required by FR-006

- [ ] T020 [P] [US2] Select and configure a small pre-trained LLM (`distilbert-base-uncased`) in `code/bes/forward_step.py` compatible with CPU-only inference (no CUDA, no 8-bit quantization)

- [ ] T021 [US2] Implement `code/bes/forward_step.py` to perform trajectory recombination guided by symbolic sub-goals. **Constraint**: Must use `optimum` CPU-optimized inference flags (`device='cpu'`, `torch.no_grad`) and specify exact Hugging Face model ID with pinned `revision` hash for reproducibility.

- [ ] T022 [US2] Implement `code/bes/population.py` to manage the evolutionary population, ensuring memory usage stays under a manageable threshold. **Note**: Must be implemented before T023 if T023 updates population state.

- [ ] T023 [US2] Implement `code/bes/backward_step.py` to integrate the symbolic planner output into the evolutionary loop, replacing the neural verifier

- [ ] T024 [US2] Implement the main BES loop in `code/main.py` to orchestrate forward (LLM) and backward (Symbolic) steps, logging all transitions

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Performance Measurement and Statistical Analysis (Priority: P3)

**Goal**: Record success rates and computational costs for both symbolic-guided and neural-verifier baselines, applying statistical tests for significance.

**Independent Test**: Feed synthetic success rate data with known differences to the analysis script to verify z-test and t-test accuracy.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T025 [P] [US3] Unit test for `code/analysis/stats.py` with synthetic data in `tests/unit/test_stats.py::test_z_test_identifies_significance`

### Implementation for User Story 3

- [ ] T026 [P] [US3] Implement `code/analysis/metrics.py` to calculate success rates, wall-clock time, and energy consumption (Joules) from execution logs

- [ ] T027 [US3] Implement `code/analysis/stats.py` to perform **two-tailed two-proportion z-test** for success rates (as mandated by FR-005) with null hypothesis H0: p1 = p2 and alpha=0.05 to determine statistical significance

- [ ] T028 [US3] [SC-001] Implement TOST (Two One-Sided Tests) logic in `code/analysis/stats.py` for equivalence testing as per SC-001. **Note**: This task addresses the 'equivalence' requirement in SC-001, distinct from the z-test in FR-005.

- [ ] T029 [US3] Implement scalability analysis in `code/analysis/metrics.py` to derive the formal **complexity class (Big-O)** via **log-log linear regression** on problem size vs. time. **Requirement**: Must implement classification logic to compare regression slope to thresholds (e.g., ~1 for O(n), ~2 for O(n^2)) to output a discrete `complexity_class` column. Output must be saved to `data/processed/scaling_analysis.csv`. **Note**: Depends on T024 (BES loop) and T026 (metrics).

- [ ] T030 [US3] Create `code/main.py` entry point to run the full experiment (Symbolic vs. Neural Baseline) and output results to `data/processed/`

- [ ] T031 [US3] Generate final report in `data/processed/final_report.md` (Markdown format) containing sections: Success Rate Comparison, Cost Comparison, Complexity Analysis, and Statistical Significance (p-values)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T032 [P] Documentation updates in `README.md` detailing how to run the BES loop and interpret results

- [ ] T033 Code cleanup and refactoring of `code/bes/` and `code/symbolic/` modules

- [ ] T034 Performance optimization of the verification loop to ensure <100ms execution per solution

- [ ] T036 [P] Run `quickstart.md` validation to ensure the entire pipeline executes within the CI time limit

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

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories. **MUST be completed first** to provide the verifier for US2.
- **User Story 2 (P2)**: Depends on US1 (verifier) and Foundational. Requires the symbolic planner and LLM setup.
- **User Story 3 (P3)**: Depends on US1 and US2 to generate the data logs required for analysis.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Generators before Verifiers
- Verifiers before Evolutionary Loop
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
Task: "Contract test for generator in tests/unit/test_generator.py::test_generator_handles_empty_input"
Task: "Unit test for verifier in tests/unit/test_verifier.py::test_verifier_rejects_invalid_solution"

# Launch all models for User Story 1 together:
Task: "Implement code/dataset/generator.py"
Task: "Curate initial dataset in data/raw/"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Dataset + Verifier)
4. **STOP and VALIDATE**: Test User Story 1 independently (run verifier on known solutions)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Hybrid Loop)
4. Add User Story 3 → Test independently → Deploy/Demo (Analysis)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Dataset/Verifier)
 - Developer B: User Story 2 (Symbolic/LLM Loop)
 - Developer C: User Story 3 (Analysis/Stats)
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
- **CRITICAL**: All LLM tasks must use CPU-only models (no CUDA, no bitsandbytes).
- **CRITICAL**: All puzzle data must be real or deterministically generated; no fake data.
- **CRITICAL**: The symbolic planner must handle constraint failures gracefully (exclude and log).