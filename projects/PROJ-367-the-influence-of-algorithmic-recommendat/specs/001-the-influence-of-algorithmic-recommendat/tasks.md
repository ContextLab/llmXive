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

- [ ] T001a [P] Create `projects/PROJ-367-the-influence-of-algorithmic-recommendat/code/` and `tests/` directories. **Verification**: Run `mkdir -p projects/PROJ-367-the-influence-of-algorithmic-recommendat/code projects/PROJ-367-the-influence-of-algorithmic-recommendat/tests` and confirm directories exist. <!-- ATOMIZE: requested -->
- [ ] T001b [P] Create `data/raw/` and `data/processed/` directories. **Verification**: Run `mkdir -p projects/PROJ-367-the-influence-of-algorithmic-recommendat/data/raw projects/PROJ-367-the-influence-of-algorithmic-recommendat/data/processed` and confirm directories exist.
- [ ] T001c [P] Create `docs/` and `docs/reports/` directories. **Verification**: Run `mkdir -p projects/PROJ-367-the-influence-of-algorithmic-recommendat/docs/reports` and confirm directories exist.
- [ ] T001d [P] Create `__init__.py` files in `code/`, `tests/`, `tests/unit/` to enable Python package imports. **Verification**: Run `python -c "import code"` to confirm no import errors.
- [ ] T002 [P] Create `projects/PROJ-367-the-influence-of-algorithmic-recommendat/code/requirements.txt` with pinned versions for `pandas`, `numpy`, `scikit-learn`, `statsmodels`, `scipy`, `datasets`, `pyyaml`, `pytest`. **Verification**: Run `pip install -r requirements.txt` to confirm all packages install without errors.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 [P] Create `code/config.py` for paths, seeds, and semantic similarity thresholds. **Verification**: Run `python -c "from code.config import *; print(SEED)"` to confirm config loads.
- [X] T004a [P] Define `DataSchemaError` exception class in `code/ingestion.py`. **Verification**: Run `python -c "from code.ingestion import DataSchemaError; print(DataSchemaError.__doc__)"` to confirm class exists.
- [X] T004b [P] Implement schema validation logic in `code/ingestion.py` that raises `DataSchemaError` with the exact message: "Required columns [recommended_categories, enrolled_categories] missing. Dataset does not support the specified experimental design." **Verification**: Write a unit test that triggers this exception and asserts the exact message.
- [ ] T005 [P] Setup `code/metrics.py` for Shannon entropy calculation (log base 2) (FR-001). **Verification**: Write a unit test with known input `['A', 'B', 'C']` and assert output `1.585`.
- [ ] T006 [P] Create `code/modeling.py` skeleton for Propensity Score Weighting (PSW) and GLS fallback. **Verification**: Run `python -c "import code.modeling"` to confirm skeleton loads without errors.
- [ ] T007 [P] Create `code/robustness.py` skeleton for permutation tests and sensitivity analysis. **Verification**: Run `python -c "import code.robustness"` to confirm skeleton loads without errors.
- [ ] T008 [P] Implement category merging logic in `code/metrics.py` based on semantic similarity threshold (FR-009), consuming config from T003. **Note**: T008 depends on T003 being complete; do not run in parallel with T003. **Verification**: Write a unit test with two categories and a threshold to verify merging logic.
- [ ] T009 [P] Create `pytest.ini` configuration file with specific options (e.g., `testpaths = tests/`, `markers = us1, us2, us3`). **Verification**: Run `pytest --collect-only` to confirm configuration is valid.
- [ ] T010 [P] **Implement Runtime Instrumentation**: Add logging of start/end timestamps in `code/main.py` (orchestration script) to measure total pipeline runtime. **Verification**: Run a dummy pipeline and verify the log contains "Total Runtime: X seconds". (Moved from Phase 6 to Phase 2 to ensure instrumentation is present for all runs).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Diversity Metric Calculation (Priority: P1) 🎯 MVP

**Goal**: Ingest course enrollment data and compute Shannon entropy-based diversity scores for recommendations and enrollments.

**Independent Test**: Run preprocessing script on a 100-row mock CSV and verify output JSON contains calculated entropy scores matching manual calculations within 0.001 tolerance.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T011 [P] [US1] Unit test for entropy calculation (log base 2) in `tests/unit/test_metrics.py`. **Verification**: Run `pytest tests/unit/test_metrics.py` to confirm test fails initially.
- [ ] T012 [P] [US1] Unit test for schema validation (FR-007) in `tests/unit/test_ingestion.py`. **Verification**: Run `pytest tests/unit/test_ingestion.py` to confirm test fails initially.

### Implementation for User Story 1

- [ ] T013a [US1] **Generate Synthetic Dataset**: Create `code/data_generation.py` to generate a synthetic dataset mimicking user-algorithm interactions. **Requirements**:
 - Output file: `data/raw/synthetic_enrollments.csv`.
 - Columns: `user_id`, `session_id`, `recommended_categories` (list), `enrolled_categories` (list).
 - Distributions: `recommended_categories` generated from Poisson(lambda=5) for category counts; `enrolled_categories` generated from a Normal distribution centered on recommendations with added noise (sigma=0.2).
 - Ensure temporal separation in the generator logic to satisfy the "Causal Independence" assumption.
 - Use a fixed random seed to ensure reproducibility.
 - **Verification**: Run `python -c "import pandas as pd; df = pd.read_csv('data/raw/synthetic_enrollments.csv'); assert list(df.columns) == ['user_id', 'session_id', 'recommended_categories', 'enrolled_categories']; print('Schema OK')"`.
- [ ] T013b [US1] **Document Synthetic Data Provenance**: Update `docs/reports/final_analysis.md` template and `docs/data-model.md` to explicitly state that the dataset is synthetic, generated by `code/data_generation.py` with seed X, and that this is a methodological demonstration due to the lack of a verified real-world dataset. **Verification**: Run `grep -q "Synthetic Data" docs/reports/final_analysis.md` to confirm text is present.
- [ ] T014 [US1] Implement `code/ingestion.py` to load CSV/Parquet, validate `recommended_categories` and `enrolled_categories` columns, and exclude rows with empty enrollments (logging warnings). **Verification**: Run on a test CSV with empty enrollments and check logs.
- [ ] T015 [US1] Implement `code/metrics.py` to calculate `Recommendation_Diversity_Score` and `Learner_Diversity_Score` using Shannon entropy (FR-001). **Verification**: Run on a test dataset and verify output matches manual calculation.
- [ ] T016a [US1] **Create `code/main.py`**: Implement orchestration to load `data/raw/synthetic_enrollments.csv` (T013a output), compute diversity scores, and output `data/processed/diversity_scores.json`. **Note**: T016a depends on T013a being complete. **Verification**: Run `python code/main.py` and verify `data/processed/diversity_scores.json` exists.
- [ ] T016b [US1] **Verification of Output**: Implement a verification script `tests/unit/test_main_output.py` that reads `data/processed/diversity_scores.json` and asserts values match manual calculations within 0.001 tolerance using a hardcoded test dataset (e.g., `{'categories': ['Math', 'Math', 'Science']}` with known entropy). **Verification**: Run `pytest tests/unit/test_main_output.py` to confirm pass.
- [ ] T017 [US1] Add robust error handling for missing data: If `enrolled_categories` is empty, explicitly record `learner_diversity_score` as `null` OR exclude the row, and log a warning with the count of excluded sessions. **Verification**: Run on a dataset with empty enrollments and verify the count is logged and the row is handled correctly.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Baseline Control and Propensity Score Weighting (Priority: P2)

**Goal**: Derive baseline interest vectors, apply Propensity Score Weighting (PSW), and fit weighted linear regression to isolate algorithmic influence.

**Independent Test**: Execute modeling script on processed dataset and verify output includes stabilized weights, weighted regression coefficient, standard error, and p-value.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T020 [P] [US2] Unit test for baseline vector derivation in `tests/unit/test_modeling.py`. **Verification**: Run `pytest tests/unit/test_modeling.py` to confirm test fails initially.
- [ ] T021 [P] [US2] Unit test for PSW weight stability check (extreme weights > 10x median) in `tests/unit/test_modeling.py`. **Verification**: Run `pytest tests/unit/test_modeling.py` to confirm test fails initially.

### Implementation for User Story 2

- [ ] T022 [P] [US2] Implement `code/modeling.py` to derive `Baseline_Interest_Vector` from pre-study history (FR-002). **Verification**: Run on a test dataset and verify vector dimensions.
- [ ] T023 [US2] Implement PSW logic in `code/modeling.py` to calculate propensity scores and stabilized weights (FR-003). **Verification**: Run on a test dataset and verify weights are calculated.
- [ ] T024 [US2] Implement weighted linear regression in `code/modeling.py` with VIF diagnostic (FR-002, FR-003, FR-008). **Verification**: Run on a test dataset and verify VIF is calculated.
- [ ] T025a [US2] Implement detection logic for N < 30 unique users in `code/modeling.py`. **Verification**: Create a test case with N < 30 and verify the detection flag is raised.
- [ ] T025b [US2] Implement Generalized Least Squares (GLS) fallback logic with robust standard errors in `code/modeling.py`. **Verification**: Create a test case with N < 30 and verify GLS is triggered.
- [ ] T025c [US2] Implement logging for methodological change (fallback to GLS) in `code/modeling.py`. **Verification**: Create a test case with N < 30 and verify the log message is present.
- [ ] T026 [US2] Add logic to detect extreme weights and flag methodological changes in logs. **Verification**: Create a test case with extreme weights and verify the log message is present.
- [ ] T027 [US2] Update `docs/reports/final_analysis.md` template to enforce associational framing (FR-006) throughout the report, explicitly avoiding causal language. **Verification**: Run a linter or manual check to ensure no causal language in the template.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Robustness Verification and Sensitivity Analysis (Priority: P3)

**Goal**: Perform outcome permutation tests and sensitivity analysis on semantic similarity thresholds to validate result stability.

**Independent Test**: Run robustness suite on a subset of data and verify permutation test p-value distribution and sensitivity analysis table.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T028 [P] [US3] Unit test for outcome permutation test logic in `tests/unit/test_robustness.py`. **Verification**: Run `pytest tests/unit/test_robustness.py` to confirm test fails initially.
- [ ] T029 [P] [US3] Integration test for sensitivity analysis sweep in `tests/integration/test_robustness.py`. **Verification**: Run `pytest tests/integration/test_robustness.py` to confirm test fails initially.

### Implementation for User Story 3

- [ ] T030a [US3] **Update Spec for Methodology**: Update `spec.md` FR-004 to explicitly state that the "Residual Permutation Test" has been replaced by the "Outcome Permutation Test" as per plan.md's methodological correction, ensuring traceability. **Verification**: Run `grep -q "Outcome Permutation Test" specs/001-the-influence-of-algorithmic-recommendations/spec.md` to confirm text is present.
- [ ] T030b [US3] Implement **Outcome Permutation Test** in `code/robustness.py` with ≥1,000 iterations (FR-004, updated by T030a). **Logic**: Shuffle the outcome variable (`Learner_Diversity`) to generate a null distribution, re-fit model with original predictors and shuffled outcome, record coefficient. Repeat to generate null distribution. Compare observed effect size against the confidence interval of the null distribution (SC-003). **Note**: This task implements the "Outcome Permutation Test" as mandated by the plan.md, overriding the spec's FR-004 "Residual Permutation" requirement due to the plan's methodological correction. **Verification**: Run on a test dataset and verify `data/processed/null_distribution.csv` exists with columns [iteration, coefficient] and that the p-value is calculated correctly.
- [ ] T031 [US3] Implement sensitivity analysis sweep for semantic similarity thresholds across a range of low values. in `code/robustness.py` (FR-005). **Verification**: Run on a test dataset and verify the sweep is executed.
- [ ] T032a [US3] **Generate Sensitivity Analysis Table**: Implement logic to execute the sensitivity sweep and output a table (CSV) showing the `Recommendation_Diversity` coefficient and p-value for each threshold {0.01, 0.05, 0.1}. **Output File**: `data/processed/sensitivity_analysis.csv`. **Columns**: `threshold`, `coefficient`, `p_value`. **Verification**: Run the script and verify the file exists and contains the correct columns and values.
- [ ] T032b [US3] **Verify Stability Metric**: Implement logic to read the sensitivity table from T032a, count how many thresholds have p-value < 0.05, and report the stability metric (e.g., "Stable at 2/3 thresholds") in the final report. **Do not fail the pipeline; report the metric as a finding.** (SC-002). **Verification**: Run the script and verify the metric is calculated and logged.
- [ ] T033 [US3] Generate final report in `docs/reports/final_analysis.md` with all diagnostics and associational framing. **Verification**: Run the script and verify the report is generated.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Associational Framing & Performance (Priority: P1 - Review Response)

**Goal**: Address reviewer concerns by strictly enforcing associational framing, optimizing performance, and merging runtime tasks.

### Implementation for Review Response

- [ ] T034 [US3] Update `code/robustness.py` to ensure all permutation test outputs are clearly labeled as "Null Distribution" and "Observed Statistic" without causal inference claims. **Verification**: Run the script and check the output labels.
- [ ] T035 [US3] Update `code/modeling.py` to ensure VIF diagnostics and weight stability flags are prominently displayed in the final report as limitations. **Verification**: Run the script and check the report for these flags.
- [ ] T036 [US3] Refine `docs/reports/final_analysis.md` template to include a dedicated "Limitations" section that explicitly states: "Findings are associational; no causal claims are made due to lack of randomization." (FR-006). **Verification**: Check the template for the exact text.
- [ ] T037 [US3] **Verify Sensitivity Metric Framing**: Implement a verification script that reads `docs/reports/final_analysis.md` and asserts the presence of the sensitivity metric text and the absence of causal language. **Verification**: Run the script and confirm it passes.
- [ ] T038 [US3] Audit the final report text for any instances of "causes", "leads to", or "effect" and replace with "associated with", "predicts", or "correlates with". **Verification**: Run a script to search for these terms and confirm none exist.
- [ ] T039 [US3] **Measure and Report Total Pipeline Runtime**: Implement logging of start/end timestamps in `code/main.py` and aggregate these in the final report `docs/reports/final_analysis.md` to measure against SC-005 (6-hour limit). **Verification**: Run the pipeline and verify the runtime is logged and reported. **Note**: This task now includes a specific check: `assert runtime_seconds < 6 * 3600` to satisfy SC-005's "measured against" requirement. (Moved from Phase 2 to Phase 6 for reporting, but instrumentation is in Phase 2).
- [ ] T040 [US3] **Document Baseline_Interest_Vector Assumption**: Update `docs/reports/final_analysis.md` to explicitly state that `Baseline_Interest_Vector` is the sole proxy for intrinsic preferences, as per spec assumptions. Acknowledge that without an explicit utility function, the study cannot distinguish between passive manipulation and active equilibrium strategy, framing the "Algorithmic Influence" metric strictly as a predictor of variance. (Ref: spec.md Assumptions). **Verification**: Check the report for the exact text.

**Checkpoint**: The analysis now strictly adheres to associational framing and verifies all success criteria.

---

## Phase 7: Performance Optimization (Review Response)

**Goal**: Address executability concerns by implementing specific optimizations to ensure the pipeline runs within a reasonable CPU time limit.

### Implementation

- [ ] T041 [US3] **Optimize Permutation Test Loop**: Refactor `code/robustness.py` to use `multiprocessing.Pool` with 4 workers for the outcome permutation test. Ensure the loop does not re-compile the model unnecessarily. Add a timing check to ensure this specific step completes in < 30 minutes on a standard CPU. **Verification**: Run the optimization test with [deferred] iterations and verify time < 30 mins. **Note**: This task depends on T030b being complete and stable; do not run in parallel with T030b. T041 and T042 are parallel-safe (different files).
- [ ] T042 [US2] **Vectorize Metrics Calculation**: Refactor `code/metrics.py` to use `pandas` vectorized operations (e.g., `apply` with optimized lambda or `numpy` vectorization) for entropy calculation across the entire dataframe, avoiding row-wise `apply` loops where possible. **Verification**: Run the script and verify the runtime is reduced.

---

## Phase 8: Limitations & Methodological Transparency (Review Response)

**Goal**: Explicitly document the limitations of the observational design regarding unmeasured confounding and the missing utility function, without introducing unverified game-theoretic concepts.

**Independent Test**: Verify that the final report includes a specific section discussing the "Missing Utility Function" limitation and how the PSW method attempts (and fails) to distinguish between algorithmic influence and equilibrium strategy.

### Implementation for Limitations

- [ ] T043 [US3] **Document Missing Utility Function Limitation**: Update `docs/reports/final_analysis.md` to include a subsection titled "Limitations: The Missing Utility Function." Explicitly state that without access to the user's internal reward model (payoff structure), the observed correlation `Recommendation_Diversity -> Learner_Diversity` is consistent with both "Algorithmic Influence" and "Equilibrium Strategy." Frame this as a standard methodological limitation of observational studies, avoiding any simulation or game-theoretic claims. (Addresses Game-Theoretic concerns without violating FR-006). **Verification**: Run `grep -q "Limitations: The Missing Utility Function" docs/reports/final_analysis.md` to confirm the exact subsection title and text.

**Checkpoint**: The analysis now explicitly addresses the theoretical gap in the observational design as a standard limitation.

---

## Phase 9: Game-Theoretic Contextualization (Review Response - von Neumann)

**Goal**: Address the specific review concern regarding Nash Equilibrium and subject agency. The study cannot simulate utility functions, but it must explicitly contextualize its findings against the possibility that observed behavior is a rational response (equilibrium) rather than passive manipulation.

### Implementation for Review Response

- [ ] T044 [US3] **Add "Equilibrium vs. Influence" Discussion**: Update `docs/reports/final_analysis.md` to include a dedicated discussion section titled "Game-Theoretic Context: Equilibrium vs. Influence." **Verification**: Check the report for the exact section title.
- [ ] T045 [US3] **Theoretical Distinction**: In the T044 section, explicitly articulate the distinction: "If subjects are maximizing an unknown utility function, the observed correlation may represent a Nash Equilibrium where the algorithm's recommendations and user choices are mutually optimal responses, rather than a causal effect of the algorithm on user diversity." **Verification**: Check the report for the exact text.
- [ ] T046 [US3] **Limitation on Agency**: Add a specific limitation statement: "This observational study cannot distinguish between 'Algorithmic Influence' (passive manipulation) and 'Equilibrium Strategy' (active rational response) because the user's utility function (payoff structure) is unobserved. The results should be interpreted as a predictive association consistent with both models." **Verification**: Check the report for the exact text.
- [ ] T047 [US3] **Citation of Adjacent Work**: In the T044 section, cite standard game-theoretic literature regarding sequential decision problems under uncertainty and mixed strategies (as suggested by the reviewer) to ground the limitation in established theory, without attempting to implement such a model. **Verification**: Check the report for the citations.
- [ ] T048 [US3] **Verify Associational Framing**: Implement a verification script that reads `docs/reports/final_analysis.md` and asserts that the "Game-Theoretic Context" section contains NO causal language (e.g., "causes", "leads to") and strictly frames the discussion as a limitation. **Verification**: Run the script and confirm it passes.

**Checkpoint**: The report now directly addresses the reviewer's concern about the "payoff structure" and "Nash equilibrium" by framing the study's inability to resolve this ambiguity as a fundamental methodological limitation of observational data.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T049a [P] Update `docs/quickstart.md` with synthetic data generation steps and pipeline execution instructions
- [ ] T049b [P] Update `docs/data-model.md` with new fields (diversity scores, weights, baseline vectors)
- [ ] T050 [P] [P] Additional unit tests for edge cases (empty lists, N<30) in `tests/unit/`
- [ ] T051 [P] Run `quickstart.md` validation and checksum persistence to `state.yaml`

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
- **Game-Theoretic Context (Phase 9)**: Depends on Phase 8 completion to ensure the limitation is framed correctly before adding the specific equilibrium discussion
- **Polish (Final Phase)**: Depends on all desired user stories and revision tasks being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 model output
- **Review Response (Phase 6)**: Depends on US2 and US3 implementation to add associational framing layers
- **Performance Optimization (Phase 7)**: Depends on US3 implementation to optimize the permutation test
- **Limitations (Phase 8)**: Depends on Phase 6 completion to frame the limitations correctly
- **Game-Theoretic Context (Phase 9)**: Depends on Phase 8 completion to ensure the limitation is framed correctly before adding the specific equilibrium discussion
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
3. Complete Phase 3: User Story 1 (including T013a Synthetic Data Generation)
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
8. Add Game-Theoretic Context (Phase 9) → Explicitly address the "Equilibrium vs. Influence" distinction raised by the von Neumann review → Final Report
9. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (including T013a)
 - Developer B: User Story 2
 - Developer C: User Story 3
3. Once US2/US3 are stable, Developer D (or B/C) implements Phase 6 (Review Response)
4. Developer E (or C) implements Phase 7 (Optimization)
5. Developer F (or D) implements Phase 8 (Limitations)
6. Developer G (or F) implements Phase 9 (Game-Theoretic Context)
7. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Revision Note**: Phase 6 tasks (T034-T037, T038, T039, T040) are mandatory to ensure strict associational framing (FR-006) and verification of SC-005. Do not finalize the report without this analysis.
- **Critical Revision Note**: Game-Theoretic tasks (T044-T048) directly address the `john-von-neumann-simulated` review. They explicitly frame the "Equilibrium vs. Influence" ambiguity as a limitation of observational data (missing utility function) and cite relevant theory, without attempting to simulate a game-theoretic model which would violate the associational framing constraint. Task T048 ensures this section does not violate FR-006. This satisfies the reviewer's demand for a "payoff structure" discussion while adhering to the project's methodological constraints.
- **ID Collision Note**: All Task IDs have been renumbered to ensure uniqueness. T013-T017 cover Phase 3 Implementation. T022-T027 cover Phase 4 Implementation. T028-T033 cover Phase 5 Implementation. T034-T040 cover Phase 6 Review Response. T041-T042 cover Phase 7 Optimization. T043 covers Phase 8 Limitations. T044-T048 cover Phase 9 Game-Theoretic Context. No duplicate IDs exist.
- **Runtime Instrumentation**: T039 (merged) now handles both logging and reporting of total pipeline runtime.
- **Baseline_Interest_Vector**: Task T040 ensures the assumption about `Baseline_Interest_Vector` as the sole proxy is documented.
- **Synthetic Data**: Task T013a ensures the synthetic dataset generation is explicitly defined, resolving the "missing producer" dependency for downstream reporting tasks. Task T013b ensures its provenance is documented.
- **Performance Optimization**: Tasks T041 and T042 specifically address the executability concern by targeting the permutation test loop and vectorization, ensuring the 6-hour limit is met.
- **Limitations Framing**: Task T043 addresses the theoretical gap regarding the missing utility function by documenting it as a standard methodological limitation, without introducing unverified game-theoretic simulations.
- **Residual Permutation**: Task T030b now implements the "Outcome Permutation Test" as required by the plan.md, correcting the previous "Residual Permutation" deviation. Task T030a updates the spec to reflect this change. **Note**: This overrides the spec's FR-004 requirement due to the plan's methodological correction.
- **Output Format**: Task T016 now outputs JSON as required by spec.md US-1.
- **Traceability**: Task T024 now correctly cites FR-002, FR-003, and FR-008, removing the incorrect FR-004 citation.
- **Game-Theoretic Context**: Tasks T044-T048 directly address the `john-von-neumann-simulated` review. They explicitly frame the "Equilibrium vs. Influence" ambiguity as a limitation of observational data (missing utility function) and cite relevant theory, without attempting to simulate a game-theoretic model which would violate the associational framing constraint. Task T048 ensures this section does not violate FR-006. This satisfies the reviewer's demand for a "payoff structure" discussion while adhering to the project's methodological constraints.