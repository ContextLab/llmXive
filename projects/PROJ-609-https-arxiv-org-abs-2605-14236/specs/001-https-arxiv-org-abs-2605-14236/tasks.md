# Tasks: Reproduce & Validate Active Learners as Efficient PRP Rerankers

**Input**: Design documents from `/specs/609-reproduce-prp-rerankers/`
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

- [X] T001 Create project structure per implementation plan: `src/rerankers`, `src/evaluation`, `src/utils`, `data/external`, `data/processed`, `reports/beir-metrics`, `reports/budget_enforcer_logs`, `tests/unit`, `tests/integration`, `tests/contract`, `contracts/`. Include `__init__.py` files in all `src` and `tests` directories and a `.gitignore` file.
- [X] T002 Initialize Python 3.10+ project with `transformers`, `beir`, `pandas`, `scikit-learn`, `numpy`, `pyyaml`, `pytest` dependencies
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement `src/utils/data_loader.py` with BEIR dataset loading and `FileNotFoundError` fast-fail logic
- [X] T005 [P] Implement `src/utils/stratifier.py` for query difficulty stratification (High/Med/Low) and representative query sampling
- [X] T006 [P] Create `contracts/dataset_schema.schema.yaml` (defining Query, Document, Pair with fields: query_id, doc_id, score), `contracts/output_schema.schema.yaml`, and `contracts/budget_enforcer_log.schema.yaml`
- [X] T007 [P] Implement `src/config/defaults.yaml` with budgets, seeds, and `flan-t5-large` path
- [X] T008 [P] Setup global seed management in `src/main.py` to ensure reproducibility (SC-004)
- [X] T009 [P] Implement `src/utils/metrics.py` for NDCG@ calculation and CSV summary generation

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Execute Core BEIR Evaluation Pipeline (Priority: P1) 🎯 MVP

**Goal**: End-to-end execution of the evaluation pipeline on `dbpedia-entity` producing valid ranking files and metrics.

**Independent Test**: Run `run_beir_eval.py` with default arguments; verify exit code 0, artifacts in `reports/beir-metrics/`, and no unhandled exceptions.

### Implementation for User Story 1

- [X] T010 [P] [US1] Unit test for data loading validation in `tests/unit/test_data_loader.py`
- [X] T011 [P] [US1] Integration test for end-to-end pipeline on small subset in `tests/integration/test_end_to_end.py`
- [X] T012 [US1] Implement `src/rerankers/base.py` with abstract `IReranker` interface, including LLM retry logic with a configurable maximum number of attempts and timeout handling
- [X] T013 [US1] Implement `src/rerankers/classic.py` with `ClassicReranker` using deterministic sorting
- [X] T014a [US1] Implement `src/evaluation/run_beir_eval.py` entry point to process `dbpedia-entity` dataset, output ranking files to `reports/beir-metrics/[model]/dbpedia-entity/`, and generate `summary.csv` with NDCG@10, calls, and seed (FR-001, FR-004)
- [X] T014b [US1] Extend `src/evaluation/run_beir_eval.py` (T014a) to process `scifact` dataset and validate cross-dataset compatibility, outputting to `reports/beir-metrics/[model]/scifact/summary.csv`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Validate Active Learning vs. Classic Sorting Performance (Priority: P2)

**Goal**: Reproduce the comparative analysis showing AL rankers achieve higher NDCG@10 per call than classic sorters under a call budget.

**Independent Test**: Execute `limit_comparisons.py` with budget 100; verify CSV contains distinct NDCG@10 values for AL and Classic oracles.

### Tests for User Story 2

- [X] T018 [P] [US2] Unit test for budget enforcement logic in `tests/unit/test_budget_enforcer.py`
- [X] T019 [P] [US2] Contract test for `limit_comparisons_experiment.csv` schema in `tests/contract/test_schemas.py`

### Implementation for User Story 2

- [X] T020 [P] [US2] Implement `src/rerankers/oracles.py` with `RandomizedOracle` logic (FR-002)
- [X] T022 [US2] Implement `src/rerankers/base.py` with `BudgetEnforcer` wrapper to strictly limit calls (FR-003) and log to `budget_enforcer_logs/`
- [X] T021 [US2] Implement `src/rerankers/active.py` with `ActiveLearnerReranker` using `BudgetEnforcer` from T022 and `RandomizedOracle` from T020
- [X] T023 [US2] Implement `src/evaluation/limit_comparisons.py` to sweep budgets [, 50, 100, 200] and record NDCG@10 (FR-005)
- [X] T025b [US2] Implement sensitivity analysis logic in `src/evaluation/limit_comparisons.py` (or new script) to sweep budgets ±10 calls and report variation in NDCG@10 rates (FR-006)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Reproduce Sensitivity Analysis and Noise Robustness (Priority: P3)

**Goal**: Validate that the randomized-direction oracle converts position bias into zero-mean noise.

**Independent Test**: Run `order_effects.py`; verify `flip_rate` column shows randomized oracle bias cancellation vs bidirectional baseline.

### Tests for User Story 3

- [X] T026 [P] [US3] Unit test for oracle symmetry and randomization in `tests/unit/test_oracles.py`

### Implementation for User Story 3

- [X] T028 [US3] Implement `src/evaluation/order_effects.py` to process a representative set of query-doc pairs (US3). Logic: Calculate flip rates and mean absolute differences; Verify zero-mean noise claim (mean absolute difference ≤ 0.05); Generate `reports/order_effects_fliprate_summary.csv` with columns: `flip_rate`, `mean_abs_diff`, `oracle_type`; Generate `reports/order_effects_variance_summary.csv` with `p-value` and `F-statistic` from Levene's test; Conditionally generate `bias_residual` column ONLY if mean absolute difference > 0.05 (US-3, SC-003)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [X] T033 [P] Update `quickstart.md` with final run commands and expected outputs
- [X] T034 Code cleanup: remove debug prints, ensure consistent logging levels
- [X] T035 Performance optimization: verify `dbpedia-entity` (200 queries, budget 100) completes < 4 hours on CPU
- [X] T036 [P] Run full contract test suite to validate all output schemas
- [X] T037 Run `run_beir_eval.py` on `scifact` to ensure cross-dataset compatibility
- [X] T038 Final review: verify all FRs (001-006) and SCs (001-005) are addressed in code and docs
- [X] T032 [P] Reproducibility verification: Re-run `order_effects.py` with a fixed random seed; verify bitwise/tolerance match for `flip_rate` values in `reports/order_effects_fliprate_summary.csv` (SC-004, US-3)

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
Task: "Unit test for data loading validation in tests/unit/test_data_loader.py"
Task: "Integration test for end-to-end pipeline on small subset in tests/integration/test_end_to_end.py"

# Launch all models for User Story 1 together:
Task: "Implement src/rerankers/base.py with abstract IReranker interface"
Task: "Implement src/rerankers/classic.py with ClassicReranker using deterministic sorting"
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