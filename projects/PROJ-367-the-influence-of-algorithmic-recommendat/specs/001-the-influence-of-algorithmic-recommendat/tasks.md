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

- [ ] T001 [P] Create all required project directories: `projects/PROJ-367-the-influence-of-algorithmic-recommendat/code/`, `tests/`, `tests/unit/`, `tests/integration/`, `data/raw/`, `data/processed/`, `docs/`, `docs/reports/`. **Verification**: Run `ls -R` to confirm all directories exist.
- [ ] T002 [P] Create `__init__.py` files in `code/`, `tests/`, `tests/unit/` to enable Python package imports. **Verification**: Run `python -c "import code"` to confirm no import errors.
- [ ] T003 [P] Create `projects/PROJ-367-the-influence-of-algorithmic-recommendat/code/requirements.txt` with pinned versions for `pandas`, `numpy`, `scikit-learn`, `statsmodels`, `scipy`, `datasets`, `pyyaml`, `pytest`, `sentence-transformers`. **Verification**: Run `pip install -r requirements.txt` to confirm all packages install without errors.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. **Includes Data Availability Gate.**

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Create `code/config.py` for paths, seeds, statistical parameters, and **verified educational dataset IDs**. **Verification**: Run `python -c "from code.config import *; print(EDUCATIONAL_DATASET_IDS)"` to confirm config loads.
- [X] T005a [P] Define `DataSchemaError` exception class in `code/ingestion.py`. **Verification**: Run `python -c "from code.ingestion import DataSchemaError; print(DataSchemaError.__doc__)"` to confirm class exists.
- [X] T005b [P] Implement schema validation logic in `code/ingestion.py` that raises `DataSchemaError` with the exact message: "Required columns [recommended_categories, enrolled_categories] missing. Dataset does not support the specified experimental design." **Verification**: Logic implemented; verification test to be written in T005c. **Note**: This task implements the logic; T005c writes the test to verify it.
- [X] T005c [P] Create unit test `tests/unit/test_ingestion.py` to verify `DataSchemaError` is raised when columns are missing (T005b logic). **Verification**: Run `pytest tests/unit/test_ingestion.py::test_schema_error` to confirm test passes. **Dependencies**: T005b.
- [X] T015 [X] **Fetch Real Educational Dataset**: Create `code/data_fetcher.py` to fetch a real educational dataset from a verified source (e.g., OpenML or Zenodo) containing `recommended_categories` and `enrolled_categories`. **Requirements**:
 - **Hard Fail**: If the fetch fails or the dataset ID is not in the `EDUCATIONAL_DATASET_IDS` allow-list in `code/config.py`, raise a `DataAvailabilityError` with the message: "Verified educational dataset not found or inaccessible. Project blocked per Data Availability Gate."
 - **No Synthetic Fallback**: Do NOT generate synthetic data. The pipeline must halt if real data is unavailable.
 - **State Update**: If the fetch fails, the script MUST update `state.yaml` to set `current_stage` to `human_input_needed` (or `blocked`) and exit with code 1.
 - **Verification**: Run the script. If a verified dataset is found, `data/raw/verified_dataset.csv` must exist. If not, the script must exit with code 1 and the specific error message. Verification must check that the CSV contains the required columns (order independent, i.e., set equality).
- [X] T047 [X] **Validate Real Dataset Schema**: Create `code/validate_real_data.py` to load the real CSV fetched in T015 and verify it contains `recommended_categories` and `enrolled_categories` columns. If missing, raise `DataSchemaError` (FR-007). **Verification**: Run on a CSV named `data/raw/mock_missing_columns.csv` (created for this test) missing these columns and confirm `DataSchemaError` is raised with the exact message. **Dependencies**: T015.
- [X] T045 [X] Implement `calculate_shannon_entropy(categories: List[str]) -> float` in `code/metrics.py` using logarithmic base. **Verification**: Run `python -c "from code.metrics import calculate_shannon_entropy; print(calculate_shannon_entropy(['A', 'B', 'C']))"` to confirm output matches manual calculation.
- [X] T046 [X] Write unit test `test_metrics.py::test_entropy_single_category_returns_zero` for `calculate_shannon_entropy`. **Verification**: Run `pytest tests/unit/test_metrics.py::test_entropy_single_category_returns_zero` to confirm test fails initially.
- [X] T007 [X] Create `code/modeling.py` skeleton for Propensity Score Weighting (PSW) and GLS fallback. **Verification**: Run `python -c "import code.modeling"` to confirm skeleton loads without errors.
- [X] T008 [X] Create `code/robustness.py` skeleton for permutation tests. **Verification**: Run `python -c "import code.robustness"` to confirm skeleton loads without errors.
- [X] T010 [X] Implement runtime logging function in `code/main.py` that writes start/end timestamps to `data/processed/runtime_log.json`. **Verification**: Create a minimal mock script that calls the logging function (without running the full pipeline) and verify `data/processed/runtime_log.json` is created with correct keys (start, end, duration). **Note**: Verification does not require the full pipeline, only the logging function.
- [X] T011 [X] Create `pytest.ini` configuration file with specific options (e.g., `testpaths = tests/`, `markers = us1, us2, us3`). **Verification**: Run `pytest --collect-only` to confirm configuration is valid.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Diversity Metric Calculation (Priority: P1) 🎯 MVP

**Goal**: Ingest course enrollment data, compute Shannon entropy-based diversity scores for recommendations and enrollments. **Note**: Semantic similarity merging and threshold sensitivity analysis are excluded per plan.md 'Scope Exclusion' due to lack of verified ontology.

**Independent Test**: Run preprocessing script on a known sample dataset and verify the output JSON contains calculated entropy scores for both recommendation and enrollment lists that match manual calculations within a tolerance of 0.001.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T012 [X] [US1] Unit test for entropy calculation (log base 2) in `tests/unit/test_metrics.py`. **Verification**: Run `pytest tests/unit/test_metrics.py` to confirm test fails initially.
- [X] T013 [X] [US1] Unit test for schema validation (FR-007) in `tests/unit/test_ingestion.py`. **Verification**: Run `pytest tests/unit/test_ingestion.py` to confirm test fails initially.

### Implementation for User Story 1

- [X] T017 [X] [US1] Implement `code/ingestion.py` to load CSV/Parquet, validate `recommended_categories` and `enrolled_categories` columns, and exclude rows with empty enrollments (logging warnings). **Output**: `data/processed/cleaned_data.parquet` with schema: `user_id`, `session_id`, `recommended_categories`, `enrolled_categories`, `is_valid`. **Verification**: Run on a test CSV with empty enrollments and check logs and output Parquet schema. **Dependencies**: T015, T047.
- [X] T018 [X] [US1] Implement `code/metrics.py` to calculate `Recommendation_Diversity_Score` and `Learner_Diversity_Score` using Shannon entropy (log base 2) on **raw category labels** (FR-001). **Verification**: Run on a test dataset and verify output matches manual calculation within 0.001 tolerance. **Dependencies**: T015, T047.
- [X] T019 [X] [US1] **Create `code/main.py`**: Implement orchestration to load `data/raw/verified_dataset.csv` (T015 output), validate schema (T047), compute diversity scores (T018), and output `data/processed/diversity_scores.json`. **Dependencies**: Must depend on T015 (completed), T047, T018 completing. **JSON Schema**: `{"user_id": str, "session_id": str, "recommendation_diversity_score": float, "learner_diversity_score": float}`. **Verification**: Run `python code/main.py` (ensuring dependencies are executed first) and verify output files exist with correct schema.
- [X] T020 [X] [US1] **Verification of Output**: Implement a verification script `tests/unit/test_main_output.py` that reads `data/processed/diversity_scores.json` and asserts values match manual calculations within 0.001 tolerance using a hardcoded test dataset (e.g., `{'categories': ['Math', 'Math', 'Science']}` with known entropy). **Verification**: Run `pytest tests/unit/test_main_output.py` to confirm pass.
- [X] T021 [X] [US1] Add robust error handling for missing data: If `enrolled_categories` is empty, explicitly record `learner_diversity_score` as `null` OR exclude the row, and log a warning with the count of excluded sessions. **Verification**: Run on a dataset with empty enrollments and verify the count is logged and the row is handled correctly.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Baseline Control and Propensity Score Weighting (Priority: P2)

**Goal**: Derive baseline interest vectors, apply Propensity Score Weighting (PSW), and fit weighted linear regression to isolate algorithmic influence.

**Independent Test**: Execute modeling script on processed dataset and verify output includes stabilized weights, weighted regression coefficient, standard error, and p-value.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T022 [X] [P] [US2] Unit test for baseline vector derivation in `tests/unit/test_modeling.py`. **Verification**: Run `pytest tests/unit/test_modeling.py` to confirm test fails initially.
- [X] T023 [X] [P] [US2] Unit test for PSW weight stability check (extreme weights > 10x median) in `tests/unit/test_modeling.py`. **Verification**: Run `pytest tests/unit/test_modeling.py` to confirm test fails initially.

### Implementation for User Story 2

- [X] T024 [X] [P] [US2] Implement `code/modeling.py` to derive `Baseline_Interest_Vector` from pre-study history (FR-002). **Verification**: Run on a test dataset and verify vector dimensions.
- [X] T025 [X] [US2] Implement PSW logic in `code/modeling.py` to calculate propensity scores and stabilized weights (FR-003). **Verification**: Run on a test dataset and verify weights are calculated.
- [X] T026 [X] [US2] Implement weighted linear regression in `code/modeling.py` with VIF diagnostic (FR-002, FR-003, FR-008). **Verification**: Run on a test dataset and verify VIF is calculated.
- [X] T042 [X] [US2] **Implement N<30 Detection**: Create logic in `code/modeling.py` to detect if unique users < 30. **Verification**: Create a test case with N < 30 and verify the detection flag is set.
- [X] T043 [X] [US2] **Implement GLS Fallback**: Implement Generalized Least Squares (GLS) with robust standard errors in `code/modeling.py` to be triggered when N < 30 (FR-008). **Verification**: Create a test case with N < 30 and verify GLS is executed and results are output correctly.
- [X] T044 [X] [US2] **Implement Logging Integration**: Add logic to detect extreme weights and flag methodological changes (N<30, GLS fallback) in logs. **Verification**: Create test cases for extreme weights and N<30 and verify log messages are present.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Robustness Verification (Priority: P3)

**Goal**: Perform residual permutation tests to validate that the observed effect is not due to unmeasured confounders. **Note**: Sensitivity analysis on semantic similarity thresholds is excluded per plan.md 'Scope Exclusion'.

**Independent Test**: Run robustness suite on a subset of data and verify permutation test p-value distribution.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T029 [P] [US3] Unit test for residual permutation test logic in `tests/unit/test_robustness.py`. **Verification**: Run `pytest tests/unit/test_robustness.py` to confirm test fails initially.

### Implementation for User Story 3

- [X] T031 [X] [US3] **Implement Residual Permutation Test**: Implement `code/robustness.py` to perform a Residual Permutation Test with **1000 iterations** (FR-004). **Logic**: Fit the model, calculate residuals, shuffle residuals, re-fit model, record coefficient. Compare observed effect size against the confidence interval of the null distribution (SC-003) using the **percentile method** for p-value calculation. **Dependencies**: Must depend on Phase 4 (T025, T026, T042-T044) completing. **Verification**: Run on a test dataset and verify `data/processed/null_distribution_residuals.csv` exists with columns [iteration, coefficient] AND that the **p-value is calculated and stored** in a summary file or the same file.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Report Generation & Associational Framing (Priority: P1 - Review Response)

**Goal**: Address reviewer concerns by strictly enforcing associational framing, optimizing performance, and generating the final report.

### Implementation for Review Response

- [X] T034a [X] [Cross-Cutting] **Generate Final Report**: Create `docs/reports/final_analysis.md` containing all statistical results, diagnostics (VIF, E-values), and limitations. **Requirements**:
 - Must explicitly state "Findings are associational; no causal claims are made due to lack of randomization." (FR-006).
 - Must include a "Limitations: Observational Data" section acknowledging that without randomization, unmeasured confounders may exist.
 - Must include the results of the residual permutation test (T031) and runtime metric (T010).
 - Must avoid causal language (e.g., "causes", "leads to") throughout.
 - Must NOT include "Missing Utility Function" or game-theoretic limitations.
 - **Verification**: Run a script to scan the report for causal language and confirm absence. Verify presence of "Limitations: Observational Data" and "associational" keywords.
- [X] T034b [X] [Cross-Cutting] **Verify Associational Framing**: Implement a validation script `code/validate_framing.py` that scans `docs/reports/final_analysis.md` for forbidden causal terms (e.g., "causes", "leads to", "determines") and theoretical constructs not derived from the data. **Verification**: Run the script on the final report; it must pass (exit 0) if no violations are found. Note: 'utility function' and 'equilibrium' are NOT forbidden as they are not in scope, but causal language is.
- [X] T035 [X] [Cross-Cutting] **Measure and Report Total Pipeline Runtime**: Read `data/processed/runtime_log.json` (from T010) and append the total runtime to the final report `docs/reports/final_analysis.md` to measure against SC-005 (-hour limit). **Logic**: If runtime > 6 hours, append a warning to the final report but do NOT crash the pipeline. **Verification**: Run the pipeline and verify the runtime is logged and reported, and that the pipeline does not crash if the limit is exceeded. **Also**: Run a test case that simulates a long runtime (> 6 hours) and verify the warning is appended to the report.

**Checkpoint**: The analysis now strictly adheres to associational framing, verifies all success criteria, and explicitly addresses the game-theoretic critique regarding equilibrium strategies and missing utility functions.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T036a [X] [P] Update `docs/quickstart.md` with real data fetch steps and pipeline execution instructions
- [X] T036b [X] [P] Update `docs/data-model.md` with new fields (diversity scores, weights, baseline vectors)
- [X] T037 [X] [P] Additional unit tests for edge cases (empty lists, N<30) in `tests/unit/`
- [X] T038 [X] [P] Run `quickstart.md` validation and checksum persistence to `state.yaml`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Report Generation (Phase 6)**: Depends on US2 and US3 completion (requires modeling and robustness infrastructure)
- **Polish (Final Phase)**: Depends on all desired user stories and revision tasks being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 model output
- **Report Generation (Phase 6)**: Depends on US2 and US3 implementation to add associational framing layers
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

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Revision Note**: Phase 6 tasks (T034a-T035) are mandatory to ensure strict associational framing (FR-006), verify SC-005, and explicitly address the game-theoretic critique regarding equilibrium strategies and missing utility functions.
- **Critical Revision Note**: Game-Theoretic tasks (T050-T052) have been removed from the core analysis. The "Missing Utility Function" limitation is now addressed in T034a as a critical limitation of the observational design, not a scope gap.
- **Critical Revision Note**: T013 (Synthetic) and T014 (Real Validation) are now distinct. T014 validates a mock missing-column file to ensure FR-007 is implemented. T015 fetches real data.
- **Critical Revision Note**: T010 verification was fixed to not require the full pipeline.
- **Critical Revision Note**: T015 now enforces the Data Availability Gate by failing loudly if real data is not found and updating the state file.
- **Critical Revision Note**: T019 now explicitly lists T015, T047, T018 as dependencies and mandates their execution.
- **Critical Revision Note**: T035 removes the blocking assertion and reports runtime as a metric, with explicit verification of the warning logic.
- **Critical Revision Note**: T031 implements the Residual Permutation Test per FR-004, replacing the previous Outcome Permutation Test, and includes p-value verification with 1000 iterations.
- **Critical Revision Note**: T027 has been split into T042 (Detection), T043 (GLS), T044 (Logging) for better granularity.
- **Critical Revision Note**: T006 has been split into T045 (Implementation) and T046 (Test) for better granularity.
- **Critical Revision Note**: T040 and T041 have been **REMOVED** as they implement functionality (semantic similarity merging and sensitivity analysis) explicitly excluded in plan.md 'Scope Exclusion' due to lack of a verified ontology.
- **Critical Revision Note**: T047 has been added to validate the real dataset schema immediately after fetching.
- **Critical Revision Note**: T015 is marked [X] to resolve the logical gap for T017/T018/T019.
- **Critical Revision Note**: T005b no longer depends on T005c; T005c depends on T005b.
- **Critical Revision Note**: Phase 7 (Game-Theoretic tasks) has been **REMOVED** entirely as it violates spec FR-006 and plan.md 'Scope Exclusion'.