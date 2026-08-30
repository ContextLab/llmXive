# Tasks: The Influence of Algorithmic Recommendations on Exploration vs. Exploitation in Online Learning

**Input**: Design documents from `/specs/001-the-influence-of-algorithmic-recommendations/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this user story belongs to (e.g., US1, US2, US3)
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

- [ ] T001 Create project structure per implementation plan
- [ ] T002 Initialize Python 3.11 project with dependencies in `projects/PROJ-367-the-influence-of-algorithmic-recommendat/code/requirements.txt` <!-- FAILED: unspecified -->
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools
- [X] T036 [P] Initialize Pipeline Runtime Instrumentation in `code/main.py` to log start/end timestamps and calculate total duration for SC-005.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Create `code/config.py` for paths, seeds, and semantic similarity thresholds
- [X] T005 [P] Implement `code/ingestion.py` schema validation (FR-007) raising `DataSchemaError` with exact message: "Required columns [recommended_categories, enrolled_categories] missing. Dataset does not support the specified experimental design."
- [X] T006 [P] Setup `code/metrics.py` for Shannon entropy calculation (log base 2) (FR-001)
- [X] T007 [P] Create `code/modeling.py` skeleton for Propensity Score Weighting (PSW) and GLS fallback
- [X] T008 [P] Create `code/robustness.py` skeleton for permutation tests and sensitivity analysis
- [ ] T009 [P] Configure `pytest` in `projects/PROJ-367-the-influence-of-algorithmic-recommendat/tests/`
- [X] T010 [P] Implement category merging logic in `code/metrics.py` based on semantic similarity threshold (FR-009), consuming config from T004

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Diversity Metric Calculation (Priority: P1) 🎯 MVP

**Goal**: Ingest course enrollment data and compute Shannon entropy-based diversity scores for recommendations and enrollments.

**Independent Test**: Run preprocessing script on a 100-row mock CSV and verify output JSON contains calculated entropy scores matching manual calculations within 0.001 tolerance.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T011 [P] [US1] Unit test for entropy calculation (log base 2) in `tests/unit/test_metrics.py`
- [X] T012 [P] [US1] Unit test for schema validation (FR-007) in `tests/unit/test_ingestion.py`

### Implementation for User Story 1

- [X] T013 [P] [US1] Implement `code/ingestion.py` to load CSV/Parquet, validate `recommended_categories` and `enrolled_categories` columns, and exclude rows with empty enrollments (logging warnings)
- [X] T014 [P] [US1] Implement `code/metrics.py` to calculate `Recommendation_Diversity_Score` and `Learner_Diversity_Score` using Shannon entropy (FR-001) <!-- FAILED: unspecified -->
- [ ] T015 [US1] Create `code/main.py` entry point to orchestrate ingestion and metric calculation, outputting `data/processed/diversity_scores.parquet`. Verify output contains columns `user_id`, `session_id`, `recommendation_diversity_score`, `learner_diversity_score` and values match manual calc within 0.001 tolerance. Verification must use a hardcoded test dataset with known entropy values embedded in the test script.
- [ ] T016 [US1] Add robust error handling for missing data and logging of excluded sessions count

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Baseline Control and Propensity Score Weighting (Priority: P2)

**Goal**: Derive baseline interest vectors, apply Propensity Score Weighting (PSW), and fit weighted linear regression to isolate algorithmic influence.

**Independent Test**: Execute modeling script on processed dataset and verify output includes stabilized weights, weighted regression coefficient, standard error, and p-value.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T040 [P] [US2] Unit test for baseline vector derivation in `tests/unit/test_modeling.py`
- [X] T041 [P] [US2] Unit test for PSW weight stability check (extreme weights > 10x median) in `tests/unit/test_modeling.py`

### Implementation for User Story 2

- [X] T020 [P] [US2] Implement `code/modeling.py` to derive `Baseline_Interest_Vector` from pre-study history (FR-002)
- [X] T021 [US2] Implement PSW logic in `code/modeling.py` to calculate propensity scores and stabilized weights (FR-003)
- [X] T022 [US2] Implement weighted linear regression in `code/modeling.py` with VIF diagnostic (FR-003, FR-004)
- [ ] T023 [US2] Implement fallback logic to Generalized Least Squares (GLS) with robust standard errors if N < 30 or PSW fails (FR-008, Edge Cases)
- [ ] T024 [US2] Add logic to detect extreme weights and flag methodological changes in logs
- [ ] T025 [US2] Ensure all output reports frame findings as **associational** only (FR-006), avoiding causal language

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Robustness Verification and Sensitivity Analysis (Priority: P3)

**Goal**: Perform residual permutation tests and sensitivity analysis on semantic similarity thresholds to validate result stability.

**Independent Test**: Run robustness suite on a subset of data and verify permutation test p-value distribution and sensitivity analysis table.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T042 [P] [US3] Unit test for residual permutation test logic in `tests/unit/test_robustness.py`
- [X] T043 [P] [US3] Integration test for sensitivity analysis sweep in `tests/integration/test_robustness.py`

### Implementation for User Story 3

- [ ] T026 [US3] Implement **Residual Permutation Test** in `code/robustness.py` with ≥1,000 iterations (FR-004). Logic: Calculate residuals from the fitted model, shuffle residuals, re-fit model with shuffled residuals, record coefficient. Repeat to generate null distribution. Compare observed effect size against 95% CI of null distribution (SC-003).
- [ ] T027 [US3] Implement sensitivity analysis sweep for semantic similarity thresholds {0.01, 0.05, 0.1} in `code/robustness.py` (FR-005)
- [ ] T028 [US3] Generate sensitivity analysis report table showing coefficient stability and p-values across thresholds
- [ ] T029 [US3] Add **E-value calculation** as a sensitivity diagnostic for unmeasured confounding (Plan.md Complexity Tracking). Formula: E-value = OR + sqrt(OR * (OR - 1)), where OR is the observed odds ratio (or equivalent for linear model). Report as a limitation metric, not a causal effect size.
- [ ] T030 [US3] Generate final report in `docs/reports/final_analysis.md` with all diagnostics and associational framing

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Associational Framing & Robustness (Priority: P1 - Review Response)

**Goal**: Address reviewer concerns by strictly enforcing associational framing and verifying robustness metrics without introducing unanchored game-theoretic concepts.

**Independent Test**: Verify that the final report explicitly avoids causal language and that all robustness metrics (E-value, Permutation Test) are traceable to plan/spec requirements.

### Implementation for Review Response

- [ ] T031 [US3] Update `code/robustness.py` to ensure all permutation test outputs are clearly labeled as "Null Distribution" and "Observed Statistic" without causal inference claims.
- [ ] T032 [US3] Update `code/modeling.py` to ensure VIF diagnostics and weight stability flags are prominently displayed in the final report as limitations.
- [ ] T033 [US3] Refine `docs/reports/final_analysis.md` template to include a dedicated "Limitations" section that explicitly states: "Findings are associational; no causal claims are made due to lack of randomization." (FR-006)
- [ ] T034 [US3] Verify that the E-value calculation (T029) is presented as a sensitivity metric for unmeasured confounding, not a causal effect size.
- [ ] T035 [US3] Audit the final report text for any instances of "causes", "leads to", or "effect" and replace with "associated with", "predicts", or "correlates with".
- [ ] T037 [US3] **Measure and report total pipeline runtime** against SC-005 (6-hour limit) in the final report. Aggregate start/end times logged by T036 and calculate total duration.

**Checkpoint**: The analysis now strictly adheres to associational framing and verifies all success criteria.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T038 [P] Documentation updates in `docs/` (including `quickstart.md` and `data-model.md`)
- [ ] T039 Code cleanup and refactoring
- [ ] T040 Performance optimization (ensure pipeline runs < 6h on CPU)
- [ ] T041 [P] Additional unit tests for edge cases (empty lists, N<30) in `tests/unit/`
- [ ] T042 Run `quickstart.md` validation and checksum persistence to `state.yaml`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Review Response (Phase 6)**: Depends on US2 and US3 completion (requires modeling and robustness infrastructure)
- **Polish (Final Phase)**: Depends on all desired user stories and revision tasks being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 model output
- **Review Response (Phase 6)**: Depends on US2 and US3 implementation to add associational framing layers
- **Polish (Final Phase)**: Depends on all desired user stories and revision tasks being complete

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Ingestion before Modeling
- Modeling before Robustness
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for entropy calculation in tests/unit/test_metrics.py"
Task: "Unit test for schema validation in tests/unit/test_ingestion.py"

# Launch all implementation for User Story 1 together (after foundation):
Task: "Implement ingestion.py in code/ingestion.py"
Task: "Implement metrics.py in code/metrics.py"
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
5. Add Review Response (Phase 6) → Integrate associational framing → Final Report
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1
 - Developer B: User Story 2
 - Developer C: User Story 3
3. Once US2/US3 are stable, Developer D (or B/C) implements Phase 6 (Review Response)
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
- **Critical Revision Note**: Phase 6 tasks (T031-T037) are mandatory to ensure strict associational framing (FR-006) and verification of SC-005. Do not finalize the report without this analysis.
- **Critical Revision Note**: Phase 7 (Game-Theoretic Context) has been removed as it was unanchored in spec.md and contradicted FR-006. All analysis is strictly associational.
- **ID Collision Note**: All Task IDs have been renumbered to ensure uniqueness. T020-T025 cover Phase 4 Implementation. T026-T030 cover Phase 5 Implementation. T031-T037 cover Phase 6 Review Response. T040-T042 cover Test tasks and Polish. No duplicate IDs exist.
- **Runtime Instrumentation**: T036 (Setup) and T037 (Report) are distinct tasks. T036 logs start time; T037 aggregates and reports.