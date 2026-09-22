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
- [ ] T003 [P] Create `projects/PROJ-367-the-influence-of-algorithmic-recommendat/code/requirements.txt` with pinned versions for `pandas`, `numpy`, `scikit-learn`, `statsmodels`, `scipy`, `datasets`, `pyyaml`, `pytest`. **Verification**: Run `pip install -r requirements.txt` to confirm all packages install without errors.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Create `code/config.py` for paths, seeds, and statistical parameters. **Verification**: Run `python -c "from code.config import *; print(SEED)"` to confirm config loads.
- [X] T005a [P] Define `DataSchemaError` exception class in `code/ingestion.py`. **Verification**: Run `python -c "from code.ingestion import DataSchemaError; print(DataSchemaError.__doc__)"` to confirm class exists.
- [X] T005b [P] Implement schema validation logic in `code/ingestion.py` that raises `DataSchemaError` with the exact message: "Required columns [recommended_categories, enrolled_categories] missing. Dataset does not support the specified experimental design." **Verification**: Run `pytest tests/unit/test_ingestion.py::test_schema_error` to confirm test passes.
- [ ] T006 [P] Setup `code/metrics.py` for Shannon entropy calculation (log base 2) (FR-001). **Verification**: Write a unit test with known input `['A', 'B', 'C']` and assert output is within 0.001 of `log2(3)` (approx 1.585).
- [ ] T007 [P] Create `code/modeling.py` skeleton for Propensity Score Weighting (PSW) and GLS fallback. **Verification**: Run `python -c "import code.modeling"` to confirm skeleton loads without errors.
- [ ] T008 [P] Create `code/robustness.py` skeleton for permutation tests. **Verification**: Run `python -c "import code.robustness"` to confirm skeleton loads without errors.
- [ ] T010 [P] Implement runtime logging function in `code/main.py` that writes start/end timestamps to `data/processed/runtime_log.json`. **Verification**: Create a minimal mock script that calls the logging function (without running the full pipeline) and verify `data/processed/runtime_log.json` is created with correct keys (start, end, duration). **Note**: Verification does not require the full pipeline, only the logging function.
- [ ] T011 [P] Create `pytest.ini` configuration file with specific options (e.g., `testpaths = tests/`, `markers = us1, us2, us3`). **Verification**: Run `pytest --collect-only` to confirm configuration is valid.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Diversity Metric Calculation (Priority: P1) 🎯 MVP

**Goal**: Ingest course enrollment data and compute Shannon entropy-based diversity scores for recommendations and enrollments.

**Independent Test**: Run preprocessing script on a known sample dataset and verify the output JSON contains calculated entropy scores for both recommendation and enrollment lists that match manual calculations within a tolerance of 0.001.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T012 [P] [US1] Unit test for entropy calculation (log base 2) in `tests/unit/test_metrics.py`. **Verification**: Run `pytest tests/unit/test_metrics.py` to confirm test fails initially.
- [ ] T013 [P] [US1] Unit test for schema validation (FR-007) in `tests/unit/test_ingestion.py`. **Verification**: Run `pytest tests/unit/test_ingestion.py` to confirm test fails initially.

### Implementation for User Story 1

- [ ] T014 [US1] **Implement Real Data Validation**: Create `code/validate_real_data.py` to load a real CSV and verify it contains `recommended_categories` and `enrolled_categories` columns. If missing, raise `DataSchemaError` (FR-007). **Verification**: Run on a CSV named `data/raw/mock_missing_columns.csv` (created for this test) missing these columns and confirm `DataSchemaError` is raised with the exact message.
- [ ] T015 [US1] **Fetch Real Educational Dataset**: Create `code/data_fetcher.py` to fetch a real educational dataset from a verified source (e.g., OpenML or Zenodo) containing `recommended_categories` and `enrolled_categories`. **Requirements**:
 - **Hard Fail**: If the fetch fails or the dataset does not match the schema, raise a `DataAvailabilityError` with the message: "Verified educational dataset not found or inaccessible. Project blocked per Data Availability Gate."
 - **No Synthetic Fallback**: Do NOT generate synthetic data. The pipeline must halt if real data is unavailable.
 - **Verification**: Run the script. If a verified dataset is found, `data/raw/verified_dataset.csv` must exist. If not, the script must exit with code 1 and the specific error message. Verification must check that the CSV contains the required columns (order independent, i.e., set equality).
- [ ] T016 [US1] **Document Data Provenance**: Update `docs/data-model.md` to explicitly state the source of the real dataset (URL, dataset ID, version) and the checksum of the downloaded file. **Verification**: Run `grep -q "Verified Dataset Source" docs/data-model.md` to confirm text is present.
- [ ] T017 [US1] Implement `code/ingestion.py` to load CSV/Parquet, validate `recommended_categories` and `enrolled_categories` columns, and exclude rows with empty enrollments (logging warnings). **Output**: `data/processed/cleaned_data.parquet` with schema: `user_id`, `session_id`, `recommended_categories`, `enrolled_categories`, `is_valid`. **Verification**: Run on a test CSV with empty enrollments and check logs and output Parquet schema.
- [ ] T018 [US1] Implement `code/metrics.py` to calculate `Recommendation_Diversity_Score` and `Learner_Diversity_Score` using Shannon entropy (log base 2) on **raw category labels** (FR-001). **Verification**: Run on a test dataset and verify output matches manual calculation within 0.001 tolerance.
- [ ] T019 [US1] **Create `code/main.py`**: Implement orchestration to load `data/raw/verified_dataset.csv` (T015 output), validate schema (T014), compute diversity scores (T018), and output `data/processed/diversity_scores.json`. **Dependencies**: Must depend on T014, T017, and T018 completing. **JSON Schema**: `{"user_id": str, "session_id": str, "recommendation_diversity_score": float, "learner_diversity_score": float}`. **Verification**: Run `python code/main.py` (ensuring T014, T017, T018 are executed first) and verify `data/processed/diversity_scores.json` exists with correct schema.
- [ ] T020 [US1] **Verification of Output**: Implement a verification script `tests/unit/test_main_output.py` that reads `data/processed/diversity_scores.json` and asserts values match manual calculations within 0.001 tolerance using a hardcoded test dataset (e.g., `{'categories': ['Math', 'Math', 'Science']}` with known entropy). **Verification**: Run `pytest tests/unit/test_main_output.py` to confirm pass.
- [ ] T021 [US1] Add robust error handling for missing data: If `enrolled_categories` is empty, explicitly record `learner_diversity_score` as `null` OR exclude the row, and log a warning with the count of excluded sessions. **Verification**: Run on a dataset with empty enrollments and verify the count is logged and the row is handled correctly.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Baseline Control and Propensity Score Weighting (Priority: P2)

**Goal**: Derive baseline interest vectors, apply Propensity Score Weighting (PSW), and fit weighted linear regression to isolate algorithmic influence.

**Independent Test**: Execute modeling script on processed dataset and verify output includes stabilized weights, weighted regression coefficient, standard error, and p-value.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T022 [P] [US2] Unit test for baseline vector derivation in `tests/unit/test_modeling.py`. **Verification**: Run `pytest tests/unit/test_modeling.py` to confirm test fails initially.
- [ ] T023 [P] [US2] Unit test for PSW weight stability check (extreme weights > 10x median) in `tests/unit/test_modeling.py`. **Verification**: Run `pytest tests/unit/test_modeling.py` to confirm test fails initially.

### Implementation for User Story 2

- [ ] T024 [P] [US2] Implement `code/modeling.py` to derive `Baseline_Interest_Vector` from pre-study history (FR-002). **Verification**: Run on a test dataset and verify vector dimensions.
- [ ] T025 [US2] Implement PSW logic in `code/modeling.py` to calculate propensity scores and stabilized weights (FR-003). **Verification**: Run on a test dataset and verify weights are calculated.
- [ ] T026 [US2] Implement weighted linear regression in `code/modeling.py` with VIF diagnostic (FR-002, FR-003, FR-008). **Verification**: Run on a test dataset and verify VIF is calculated.
- [ ] T027 [US2] **Implement N<30 Detection and GLS Fallback**: Combine detection, fallback logic, and logging into a single atomic task. Implement logic to detect if unique users < 30, trigger Generalized Least Squares (GLS) with robust standard errors, and log the methodological change (FR-008). **Verification**: Create a test case with N < 30 and verify GLS is triggered, logging is present, and results are output correctly.
- [ ] T028 [US2] Add logic to detect extreme weights and flag methodological changes in logs. **Verification**: Create a test case with extreme weights and verify the log message is present.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Robustness Verification (Priority: P3)

**Goal**: Perform residual permutation tests to validate that the observed effect is not due to unmeasured confounders.

**Note**: The plan explicitly excludes "threshold sensitivity analysis" (e.g., sweeping semantic similarity or min enrollment thresholds) as arbitrary. Robustness is validated solely through the Residual Permutation Test.

**Independent Test**: Run robustness suite on a subset of data and verify permutation test p-value distribution.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T029 [P] [US3] Unit test for residual permutation test logic in `tests/unit/test_robustness.py`. **Verification**: Run `pytest tests/unit/test_robustness.py` to confirm test fails initially.

### Implementation for User Story 3

- [ ] T031 [US3] **Implement Residual Permutation Test**: Implement `code/robustness.py` to perform a Residual Permutation Test with ≥1,000 iterations (FR-004). **Logic**: Fit the model, calculate residuals, shuffle residuals, re-fit model, record coefficient. Compare observed effect size against the confidence interval of the null distribution (SC-003) using the **percentile method** for p-value calculation. **Dependencies**: Must depend on Phase 4 (T025, T026) completing. **Verification**: Run on a test dataset and verify `data/processed/null_distribution_residuals.csv` exists with columns [iteration, coefficient] AND that the **p-value is calculated and stored** in a summary file or the same file.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Report Generation & Associational Framing (Priority: P1 - Review Response)

**Goal**: Address reviewer concerns by strictly enforcing associational framing, optimizing performance, and generating the final report.

### Implementation for Review Response

- [ ] T034a [Cross-Cutting] **Generate Final Report**: Create `docs/reports/final_analysis.md` containing all statistical results, diagnostics (VIF, E-values), and limitations. **Requirements**:
 - Must explicitly state "Findings are associational; no causal claims are made due to lack of randomization." (FR-006).
 - Must include a "Limitations: Observational Data" section acknowledging that without randomization, unmeasured confounders may exist.
 - Must include the results of the residual permutation test (T031) and runtime metric (T010).
 - Must avoid causal language (e.g., "causes", "leads to") throughout.
 - Must NOT include "Missing Utility Function" or game-theoretic limitations.
 - **Verification**: Run a script to scan the report for causal language and confirm absence. Verify presence of "Limitations: Observational Data" and "associational" keywords.
- [ ] T034b [Cross-Cutting] **Verify Associational Framing**: Implement a validation script `code/validate_framing.py` that scans `docs/reports/final_analysis.md` for forbidden causal terms (e.g., "causes", "leads to", "determines") and theoretical constructs not derived from the data. **Verification**: Run the script on the final report; it must pass (exit 0) if no violations are found. Note: 'utility function' and 'equilibrium' are NOT forbidden as they are not in scope, but causal language is.
- [ ] T035 [Cross-Cutting] **Measure and Report Total Pipeline Runtime**: Read `data/processed/runtime_log.json` (from T010) and append the total runtime to the final report `docs/reports/final_analysis.md` to measure against SC-005 (-hour limit). **Logic**: If runtime > 6 hours, append a warning to the final report but do NOT crash the pipeline. **Verification**: Run the pipeline and verify the runtime is logged and reported, and that the pipeline does not crash if the limit is exceeded.

**Checkpoint**: The analysis now strictly adheres to associational framing and verifies all success criteria.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T036a [P] Update `docs/quickstart.md` with real data fetch steps and pipeline execution instructions
- [ ] T036b [P] Update `docs/data-model.md` with new fields (diversity scores, weights, baseline vectors)
- [ ] T037 [P] Additional unit tests for edge cases (empty lists, N<30) in `tests/unit/`
- [ ] T038 [P] Run `quickstart.md` validation and checksum persistence to `state.yaml`

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
- **Critical Revision Note**: Phase 6 tasks (T034a-T035) are mandatory to ensure strict associational framing (FR-006) and verification of SC-005. Do not finalize the report without this analysis.
- **Critical Revision Note**: Game-Theoretic tasks have been removed. The "Missing Utility Function" limitation is removed from scope. T034b explicitly verifies no causal language or theoretical constructs are introduced.
- **Critical Revision Note**: T013 (Synthetic) and T014 (Real Validation) are now distinct. T014 validates a mock missing-column file to ensure FR-007 is implemented. T015 fetches real data.
- **Critical Revision Note**: T010 verification was fixed to not require the full pipeline.
- **Critical Revision Note**: T015 now enforces the Data Availability Gate by failing loudly if real data is not found.
- **Critical Revision Note**: T019 now explicitly lists T014, T017, T018 as dependencies and mandates their execution.
- **Critical Revision Note**: T035 removes the blocking assertion and reports runtime as a metric.
- **Critical Revision Note**: T031 implements the Residual Permutation Test per FR-004, replacing the previous Outcome Permutation Test, and includes p-value verification.
- **Critical Revision Note**: T027 combines N<30 detection, GLS fallback, and logging into one atomic task.
- **Critical Revision Note**: T009, T032, T033a, T033b, T039 have been removed to align with scope and FR-006. The plan explicitly excludes threshold sensitivity analysis and game-theoretic constructs.
- **Critical Revision Note**: T006 verification now specifies a tolerance of 0.001.