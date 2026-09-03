# Tasks: llmXive follow-up: extending "Multi-Turn Reflective Masking Elicits Reasoning in Mask Diffusion Mode"

**Input**: Design documents from `/specs/001-llmxive-topological-limits/`
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

- [ ] T001 Create project directories matching `plan.md` structure: `data/raw/`, `data/processed/`, `code/`, `code/utils/`, `tests/`, `results/paper_figures/`
- [ ] T002 Create `__init__.py` files in `code/`, `code/utils/`, and `tests/` directories
- [X] T003 Initialize Python 3.11 project with `requirements.txt` (torch, transformers, datasets, networkx, lifelines, scikit-learn, pandas, numpy, pytest) with **explicit version pinning** (e.g., `torch==2.1.0`) for reproducibility
- [ ] T004 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 [P] Implement `code/utils/logging_utils.py` for standardized experiment logging and checksum generation
- [X] T006 [P] Implement `code/utils/graph_utils.py` containing DAG validation (acyclic check), `nesting_depth` (longest path), `branching_factor` (mean in-degree), and **longest_path** calculators
- [X] T007 [P] [US1] Unit test for `code/utils/graph_utils.py` DAG validation and metric calculation in `tests/test_graph_utils.py`
- [ ] T008 Configure environment variables for random seeds and model paths

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Synthetic Data Generation with Controlled Topology (Priority: P1) 🎯 MVP

**Goal**: Generate a synthetic dataset of logical puzzles where `nesting_depth` and `branching_factor` are explicitly controlled, verified as acyclic, and recorded in metadata.

**Independent Test**: The generation script can be executed in isolation to produce a JSONL file. A validation script can parse this file and verify that the distribution of `nesting_depth` and `branching_factor` matches the requested ranges, and that the ground-truth solution is derivable from the graph structure.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T009 [P] [US1] Contract test for `code/graph_generator.py` output schema in `tests/test_graph_generator.py` (validate against `LogicalPuzzle` entity in `data-model.md`)
- [X] T010 [P] [US1] Integration test for stratified orthogonalization (depth vs branching correlation < 0.2) in `tests/test_graph_generator.py` (Input: N=500, depth 3-6, branching 1-5; Assertion: |r| < 0.2)
- [X] T011 [P] [US1] Unit test for `code/utils/graph_utils.py` DAG validation and metric calculation in `tests/test_graph_utils.py`

### Implementation for User Story 1

- [X] T012 [US1] Implement `code/graph_generator.py` using `networkx` to generate Directed Acyclic Graphs (DAGs) with target `nesting_depth` and `branching_factor`
- [ ] T013 [US1] Implement **Stratified Orthogonalization** logic: Rejection sampling loop to ensure |r| < 0.2 between depth and branching factors; **Verify and log final correlation coefficient**
- [X] T014 [US1] Implement **Deterministic Template Engine** in `code/graph_generator.py` to map DAG structure to logical text prompts (no LLM involved)
- [X] T015 [US1] Implement **Randomized Path Perturbation** (FR-007) to select a valid ground-truth path different from the longest path; **Calculate the cycle rate (discarded/total attempts) and write the cycle rate to `data/validation_metrics.json` with the literal status marker '[deferred]' as required by SC-005**
- [ ] T016 [US1] Write generated instances to `data/raw/logical_puzzles.jsonl` with metadata (`instance_id`, `text`, `ground_truth_path`, `nesting_depth`, `branching_factor`, `graph_structure`)
- [ ] T017 [US1] Implement checksum generation for `data/raw/logical_puzzles.jsonl` and record in `data/checksums.txt`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - CPU-Feasible Baseline Execution (Priority: P2)

**Goal**: Execute the Reflective Masking (RM) loop on the generated dataset using a pre-trained Mask Diffusion Model on CPU, recording turns to convergence or failure.

**Independent Test**: The execution script can be run on a standard CPU environment. It must complete within the CI limit for the full dataset. The output must be a log file containing `instance_id`, `turns_to_converge` (or `failure`), and `final_accuracy`.

### Tests for User Story 2

- [X] T018 [P] [US2] Contract test for `code/rm_executor.py` input/output schema in `tests/test_rm_executor.py`
- [X] T019 [P] [US2] Integration test for Independent Logical Validator (ILV) verifying path coverage in `tests/test_rm_executor.py`
- [X] T020 [P] [US2] Unit test for hard turn limit enforcement (50 turns) and censored data flagging in `tests/test_rm_executor.py`

### Implementation for User Story 2

- [X] T021 [US2] Implement `code/rm_executor.py` to load pre-trained Mask Diffusion Model with `device="cpu"` <!-- FAILED: unspecified -->
- [ ] T022 [US2] Implement **Reflective Masking Loop**: Mask -> Predict -> Unmask -> Check Convergence <!-- FAILED: unspecified -->
- [X] T023 [US2] Implement **Independent Logical Validator (ILV)** in `code/utils/graph_utils.py`: Parse model output into logic graph, verify `path_coverage` >= 0.95 against original DAG
- [ ] T024 [US2] **Read `ground_truth_path` metadata from `data/raw/logical_puzzles.jsonl` (generated by T016) and calculate divergence metric (e.g., Jaccard distance or path edit distance) between the model's path and the `ground_truth_path` (perturbed) in `data/processed/execution_log.csv`**; **Ensure FR-007 compliance by validating against the perturbed ground truth, NOT the longest path**
- [ ] T025 [US2] Implement hard turn limit for primary run; mark as "failure" if exceeded (censored data)
- [ ] T026 [US2] Implement batch processing logic to stay within RAM constraints (streaming if necessary)
- [ ] T027 [US2] Write execution results to `data/processed/execution_log.csv` with `instance_id`, `turns_to_converge`, `convergence_status`, `path_coverage`, `divergence_from_ground_truth`
- [ ] T028 [US2] Implement **Extended Budget Validation Run** (FR-008): **Filter `data/processed/execution_log.csv` for instances where `convergence_status=failure`; re-run ONLY these instances with an extended turn limit of 1000 turns**; **Write results to `data/processed/extended_budget_log.csv`**
- [ ] T029 [US2] Generate checksums for `data/processed/execution_log.csv` and `data/processed/extended_budget_log.csv`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Correlation & Threshold Analysis (Priority: P3)

**Goal**: Perform Survival Analysis (Cox PH) and Segmented Regression to correlate topological metrics with convergence, and execute sensitivity analysis on thresholds.

**Independent Test**: The analysis script can be run on the results log. It must produce a report containing correlation coefficients, p-values, and a plot/table showing how convergence rates change when the success threshold is varied.

### Tests for User Story 3

- [ ] T030 [P] [US3] Contract test for `code/analyzer.py` output report schema in `tests/test_analyzer.py`
- [ ] T031 [P] [US3] Unit test for Cox Proportional Hazards model handling of censored data in `tests/test_analyzer.py`
- [ ] T032 [P] [US3] Unit test for Segmented Regression tipping point detection in `tests/test_analyzer.py`

### Implementation for User Story 3

- [ ] T033 [US3] **FR-004 Compliance**: Implement **Survival Analysis (Cox PH)** in `code/analyzer.py` (Primary) AND **Spearman rank correlation analysis** (Descriptive) between `nesting_depth` and `turns_to_converge`; **Output Spearman coefficient and p-value explicitly** to satisfy FR-004 and SC-001
- [ ] T034 [US3] Implement **Segmented Regression** to identify the specific `nesting_depth` "tipping point" where degradation rate changes; **Explicitly calculate and report failure rates at adjacent depths (depth-1, depth, depth+1) to satisfy SC-002**
- [ ] T035 [US3] Implement **Sensitivity Analysis**: Re-evaluate failure rates at **three specific cutoffs (40, 50, and 60 turns)** to verify the stability of the identified "tipping point" (FR-005)
- [ ] T036 [US3] Implement **Extended Budget Analysis**: **Compare short-horizon failures vs. long-horizon convergences to quantify the rate of budget exhaustion**; **Read `data/processed/extended_budget_log.csv` and generate `results/extended_budget_analysis.md` containing the percentage of 50-turn failures that converge at 1000 turns**
- [ ] T037 [US3] Apply Bonferroni correction for multiple comparisons
- [ ] T038 [US3] Generate `results/paper_figures/` plots and `results/statistical_report.md` with all metrics, p-values, and tipping point values
- [ ] T039 [US3] **Update README.md** with usage examples and setup instructions

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T040 [P] **Update `docs/api.md`** with function signatures for `code/` modules
- [ ] T041 [P] Code cleanup and refactoring of `code/utils/` modules
- [ ] T042 [US2] Implement batch processing to ensure memory constraints (split from performance check)
- [ ] T043 [US2] Run benchmark script and record timing in `results/benchmark.log` (split from performance check)
- [ ] T044 [P] Additional unit tests coverage validation in `tests/`
- [ ] T045 Run `quickstart.md` validation to ensure reproducibility

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires `data/raw/logical_puzzles.jsonl` from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires `data/processed/execution_log.csv` from US2

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Utilities (graph_utils) before Generators/Executors
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
Task: "Contract test for graph_generator.py output schema in tests/test_graph_generator.py"
Task: "Integration test for stratified orthogonalization in tests/test_graph_generator.py"

# Launch all models for User Story 1 together:
Task: "Implement graph_generator.py using networkx"
Task: "Implement Deterministic Template Engine in code/graph_generator.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (verify topology control)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Execution loop)
4. Add User Story 3 → Test independently → Deploy/Demo (Statistical insights)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Data Gen)
 - Developer B: User Story 2 (Execution)
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
- **Critical Constraint**: All data generation must be real (synthetic but controlled) and execution must be CPU-only. No synthetic fallbacks for data loading.