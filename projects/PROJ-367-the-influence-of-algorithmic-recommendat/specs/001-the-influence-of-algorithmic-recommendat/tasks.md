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

- [ ] T001a [P] Create project directory structure: `projects/PROJ-367-the-influence-of-algorithmic-recommendat/code/`, `data/raw/`, `data/processed/`, `tests/unit/`, `tests/integration/`, `docs/reports/`
- [ ] T001b [P] Create `__init__.py` files in `code/`, `tests/`, and `tests/unit/` to enable Python package imports
- [ ] T001c [P] Create `projects/PROJ-367-the-influence-of-algorithmic-recommendat/code/requirements.txt` with pinned versions for `pandas`, `numpy`, `scikit-learn`, `statsmodels`, `scipy`, `datasets`, `pyyaml`, `pytest`
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create `code/config.py` for paths, seeds, and semantic similarity thresholds
- [X] T005 [P] Implement `code/ingestion.py` schema validation (FR-007): Define a custom exception class named `DataSchemaError` and ensure it is raised with the exact message: "Required columns [recommended_categories, enrolled_categories] missing. Dataset does not support the specified experimental design."
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
- [X] T014 [P] [US1] Implement `code/metrics.py` to calculate `Recommendation_Diversity_Score` and `Learner_Diversity_Score` using Shannon entropy (FR-001)
- [ ] T014b [US1] **Generate Synthetic Dataset**: Create `code/data_generation.py` to generate a synthetic dataset mimicking user-algorithm interactions with distinct `recommended_categories` and `enrolled_categories` columns. Ensure temporal separation in the generator logic to satisfy the "Causal Independence" assumption. Save output to `data/raw/synthetic_enrollments.csv`.
- [ ] T015 [US1] Create `code/main.py` entry point to orchestrate ingestion and metric calculation, outputting `data/processed/diversity_scores.json`. Verify output contains columns `user_id`, `session_id`, `recommendation_diversity_score`, `learner_diversity_score` and values match manual calc within 0.001 tolerance. Verification must use a hardcoded test dataset (e.g., `{'categories': ['Math', 'Math', 'Science']}`) with known entropy values (e.g., log2(1.5) ≈ 0.585) embedded in the test script.
- [ ] T016 [US1] Add robust error handling for missing data: If `enrolled_categories` is empty, explicitly record `learner_diversity_score` as `null` OR exclude the row, and log a warning with the count of excluded sessions.

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
- [X] T022 [US2] Implement weighted linear regression in `code/modeling.py` with VIF diagnostic (FR-002, FR-003, FR-008)
- [ ] T023 [US2] Implement fallback logic to Generalized Least Squares (GLS) with robust standard errors if N < 30 or PSW fails (FR-008, Edge Cases). **Must log the methodological change** if fallback is triggered.
- [ ] T024 [US2] Add logic to detect extreme weights and flag methodological changes in logs
- [X] T025 [US2] Update `docs/reports/final_analysis.md` template to enforce associational framing (FR-006) throughout the report, explicitly avoiding causal language.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Robustness Verification and Sensitivity Analysis (Priority: P3)

**Goal**: Perform residual permutation tests and sensitivity analysis on semantic similarity thresholds to validate result stability.

**Independent Test**: Run robustness suite on a subset of data and verify permutation test p-value distribution and sensitivity analysis table.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T042 [P] [US3] Unit test for residual permutation test logic in `tests/unit/test_robustness.py`
- [X] T043 [P] [US3] Integration test for sensitivity analysis sweep in `tests/integration/test_robustness.py`

### Implementation for User Story 3

- [X] T026 [US3] Implement **Residual Permutation Test** in `code/robustness.py` with ≥1,000 iterations (FR-004). Logic: Calculate residuals from the weighted regression, shuffle residuals, re-fit model with original predictors and shuffled residuals, record coefficient. Repeat to generate null distribution. Compare observed effect size against 95% CI of null distribution (SC-003). **Note: Adheres to spec.md FR-004 requirement for residual permutation.**
- [X] T027 [US3] Implement sensitivity analysis sweep for semantic similarity thresholds {0.01, 0.05, 0.1} in `code/robustness.py` (FR-005)
- [ ] T028a [US3] **Generate Sensitivity Analysis Table**: Implement logic to execute the sensitivity sweep and output a table (CSV/JSON) showing the `Recommendation_Diversity` coefficient and p-value for each threshold {0.01, 0.05, 0.1}.
- [ ] T028b [US3] **Verify Stability Metric**: Implement logic to read the sensitivity table from T028a, count how many thresholds have p-value < 0.05, and report the stability metric (e.g., "Stable at 2/3 thresholds") in the final report. **Do not fail the pipeline; report the metric as a finding.** (SC-002)
- [X] T030 [US3] Generate final report in `docs/reports/final_analysis.md` with all diagnostics and associational framing

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Associational Framing & Performance (Priority: P1 - Review Response)

**Goal**: Address reviewer concerns by strictly enforcing associational framing, optimizing performance, and merging runtime tasks.

### Implementation for Review Response

- [X] T031 [US3] Update `code/robustness.py` to ensure all permutation test outputs are clearly labeled as "Null Distribution" and "Observed Statistic" without causal inference claims.
- [X] T032 [US3] Update `code/modeling.py` to ensure VIF diagnostics and weight stability flags are prominently displayed in the final report as limitations.
- [X] T033 [US3] Refine `docs/reports/final_analysis.md` template to include a dedicated "Limitations" section that explicitly states: "Findings are associational; no causal claims are made due to lack of randomization." (FR-006)
- [ ] T034 [US3] Verify that the analysis is presented as a sensitivity metric for unmeasured confounding, not a causal effect size.
- [~] T035 [US3] Audit the final report text for any instances of "causes", "leads to", or "effect" and replace with "associated with", "predicts", or "correlates with".
- [X] T036 [US3] **Measure and Report Total Pipeline Runtime**: Implement logging of start/end timestamps in `code/main.py` and aggregate these in the final report `docs/reports/final_analysis.md` to measure against SC-005 (6-hour limit). (Merged T036/T037)
- [X] T043 [US3] **Document Baseline_Interest_Vector Assumption**: Update `docs/reports/final_analysis.md` to explicitly state that `Baseline_Interest_Vector` is the sole proxy for intrinsic preferences, as per spec assumptions. Acknowledge that without an explicit utility function, the study cannot distinguish between passive manipulation and active equilibrium strategy, framing the "Algorithmic Influence" metric strictly as a predictor of variance. (Ref: spec.md Assumptions)

**Checkpoint**: The analysis now strictly adheres to associational framing and verifies all success criteria.

---

## Phase 7: Performance Optimization (Review Response)

**Goal**: Address executability concerns by implementing specific optimizations to ensure the pipeline runs within a reasonable CPU time limit.

### Implementation

- [ ] T046 [P] [US3] **Optimize Permutation Test Loop**: Refactor `code/robustness.py` to use `multiprocessing.Pool` with 4 workers for the [deferred]+ iteration residual permutation test. Ensure the loop does not re-compile the model unnecessarily. Add a timing check to ensure this specific step completes in < 30 minutes on a standard CPU.
- [ ] T047 [P] [US2] **Vectorize Metrics Calculation**: Refactor `code/metrics.py` to use `pandas` vectorized operations (e.g., `apply` with optimized lambda or `numpy` vectorization) for entropy calculation across the entire dataframe, avoiding row-wise `apply` loops where possible.

---

## Phase 8: Limitations & Methodological Transparency (Review Response)

**Goal**: Explicitly document the limitations of the observational design regarding unmeasured confounding and the missing utility function, without introducing unverified game-theoretic concepts.

**Independent Test**: Verify that the final report includes a specific section discussing the "Missing Utility Function" limitation and how the PSW method attempts (and fails) to distinguish between algorithmic influence and equilibrium strategy.

### Implementation for Limitations

- [ ] T053 [US3] **Document Missing Utility Function Limitation**: Update `docs/reports/final_analysis.md` to include a subsection titled "Limitations: The Missing Utility Function." Explicitly state that without access to the user's internal reward model (payoff structure), the observed correlation `Recommendation_Diversity -> Learner_Diversity` is consistent with both "Algorithmic Influence" and "Equilibrium Strategy." Frame this as a standard methodological limitation of observational studies, avoiding any simulation or game-theoretic claims. (Addresses Game-Theoretic concerns without violating FR-006)

**Checkpoint**: The analysis now explicitly addresses the theoretical gap in the observational design as a standard limitation.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T038a [P] Update `docs/quickstart.md` with synthetic data generation steps and pipeline execution instructions
- [ ] T038b [P] Update `docs/data-model.md` with new fields (diversity scores, weights, baseline vectors)
- [ ] T044 [P] [P] Additional unit tests for edge cases (empty lists, N<30) in `tests/unit/`
- [ ] T045 [P] Run `quickstart.md` validation and checksum persistence to `state.yaml`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Review Response (Phase 6)**: Depends on US2 and US3 completion (requires modeling and robustness infrastructure)
- **Performance Optimization (Phase 7)**: Depends on US3 implementation to optimize the permutation test
- **Limitations (Phase 8)**: Depends on Phase 6 completion (requires final report template and associational framing)
- **Polish (Final Phase)**: Depends on all desired user stories and revision tasks being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 model output
- **Review Response (Phase 6)**: Depends on US2 and US3 implementation to add associational framing layers
- **Performance Optimization (Phase 7)**: Depends on US3 implementation to optimize the permutation test
- **Limitations (Phase 8)**: Depends on Phase 6 completion to frame the limitations correctly
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
- Once Foundational phase completes, all user stories can start in parallel (if staffed)
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
3. Complete Phase 3: User Story 1 (including T014b Synthetic Data Generation)
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 (with Synthetic Data) → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Add Review Response (Phase 6) → Integrate associational framing + Baseline_Interest_Vector documentation → Final Report
6. Add Performance Optimization (Phase 7) → Ensure runtime < 6h → Final Report
7. Add Limitations (Phase 8) → Explicitly document the missing utility function limitation → Final Report
8. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (including T014b)
 - Developer B: User Story 2
 - Developer C: User Story 3
3. Once US2/US3 are stable, Developer D (or B/C) implements Phase 6 (Review Response)
4. Developer E (or C) implements Phase 7 (Optimization)
5. Developer F (or D) implements Phase 8 (Limitations)
6. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Revision Note**: Phase 6 tasks (T031-T035, T036, T043) are mandatory to ensure strict associational framing (FR-006) and verification of SC-005. Do not finalize the report without this analysis.
- **Critical Revision Note**: Game-Theoretic tasks (T048-T052 old) have been removed as they were unanchored in spec.md and contradicted FR-006. All analysis is strictly associational. Limitations are documented in Phase 8 (T053).
- **ID Collision Note**: All Task IDs have been renumbered to ensure uniqueness. T020-T025 cover Phase 4 Implementation. T026-T028b, T030 cover Phase 5 Implementation. T031-T036, T043 cover Phase 6 Review Response. T040-T045 cover Test tasks and Polish. T046-T047 cover Phase 7 Optimization. T053 covers Phase 8 Limitations. No duplicate IDs exist.
- **Runtime Instrumentation**: T036 (merged) now handles both logging and reporting of total pipeline runtime.
- **Baseline_Interest_Vector**: Task T043 ensures the assumption about `Baseline_Interest_Vector` as the sole proxy is documented.
- **Synthetic Data**: Task T014b ensures the synthetic dataset generation is explicitly defined, resolving the "missing producer" dependency for downstream reporting tasks.
- **Performance Optimization**: Tasks T046 and T047 specifically address the executability concern by targeting the permutation test loop and vectorization, ensuring the 6-hour limit is met.
- **Limitations Framing**: Task T053 addresses the theoretical gap regarding the missing utility function by documenting it as a standard methodological limitation, without introducing unverified game-theoretic simulations.
- **Residual Permutation**: Task T026 now implements the "Residual Permutation Test" as required by spec.md FR-004, correcting the previous "Outcome Permutation" deviation.
- **Output Format**: Task T015 now outputs JSON as required by spec.md US-1.
- **Traceability**: Task T022 now correctly cites FR-002, FR-003, and FR-008, removing the incorrect FR-004 citation.