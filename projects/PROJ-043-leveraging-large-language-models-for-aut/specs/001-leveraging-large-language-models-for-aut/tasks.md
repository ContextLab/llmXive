# Tasks: Leveraging Large Language Models for Automated Code Refactoring

**Input**: Design documents from `/specs/001-leveraging-llm-refactoring/`
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

- [ ] T001a Create directory `code/` at repository root
- [ ] T001b Create directory `data/` at repository root
- [ ] T001c Create directory `tests/` at repository root
- [ ] T001d Create directory `paper/` at repository root
- [X] T002 Initialize Python 3.11 project with pinned dependencies in `code/requirements.txt`
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools: Create `pyproject.toml` and `.ruff.toml` enabling rules E, F, W, I in `code/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [US1] Implement configuration management in `code/config.py`: Define variables `HF_API_KEY` (str), `RANDOM_SEED` (int), `MAX_ATTEMPTS` (int), `MIN_VALID_FUNCTIONS` (int), `BATCH_SIZE` (int) with default values and type validation.
- [ ] T005 [P] Setup schema validation using `pydantic` for `contracts/config.schema.yaml` and `contracts/output.schema.yaml`
- [X] T006 [P] Implement robust logging and error handling infrastructure in `code/utils/logging.py`
- [X] T007 [US1] Create base data models in `code/models/entities.py`: Define `FunctionSample` (fields: `code: str`, `metrics: dict`, `hash: str`) and `MetricDelta` (fields: `complexity_delta: float`, `pylint_delta: float`, `maintainability_delta: float`).
- [X] T008 [US1] Implement caching mechanism in `code/utils/cache.py` (disk-based, keyed by function hash)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Structural Analysis (Priority: P1) 🎯 MVP

**Goal**: Download Python functions from BigCode, compute structural metrics (LOC, nesting, PEP-8), and filter for valid code.

**Independent Test**: Run `code/data/download.py` and `code/data/static_analysis.py` on a local subset (10 functions) to verify a JSON file is produced with original code and 5 metrics, with no LLM API calls.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T009 [P] [US1] Unit test for metric calculation (radon/pylint) in `tests/unit/test_static_analysis.py`
- [X] T010 [P] [US1] Unit test for dataset sampling logic in `tests/unit/test_download.py`
- [X] T011 [P] [US1] Integration test for full data pipeline (fetch -> analyze -> save) in `tests/integration/test_data_pipeline.py`

### Implementation for User Story 1

- [ ] T012 [US1] Implement `code/data/download.py`: Fetch `bigcode/the-stack-dedup` via `datasets.load_dataset`. **Strict Constraints**: Max attempts: 400. Stop immediately if 200 valid samples are found. Minimum valid required: 100. If <100 valid samples are found after 400 attempts, log a warning and halt with a clear error. Handle rate limits with exponential backoff. **FAIL LOUDLY** if the canonical dataset is inaccessible.
- [ ] T013 [US1] Implement `code/data/static_analysis.py`: Parse Python AST to compute LOC, max nesting depth, parameter count, and **docstring presence** (boolean); use `radon` for cyclomatic complexity; use `pylint` to compute **PEP-8 adherence score** (normalized score) as the predictor. Flag unparseable functions. **Distinction**: Compute these metrics strictly on the *original* code to serve as predictors.
- [ ] T014 [US1] Implement `code/data/processor.py`: Orchestrate download and analysis, filter out unparseable functions, **validate that count >= 100 before saving**, and save `data/processed/raw_metrics.json` with original code and structural predictors.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Zero-Shot Refactoring, Null Baseline, and Quality Measurement (Priority: P2)

**Goal**: Invoke WizardCoder API for refactoring and identity baseline, compute quality deltas (ΔComplexity, ΔPylint).

**Independent Test**: Process 5 functions, verify API returns refactored code, identity baseline is generated, and quality metrics are calculated for original/refactored/baseline with non-null deltas.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T016 [P] [US2] Unit test for API retry logic and timeout handling in `tests/unit/test_llm_client.py`
- [ ] T017 [P] [US2] Unit test for null baseline generation in `tests/unit/test_baseline.py`
- [ ] T018 [P] [US2] Integration test for refactoring batch processing in `tests/integration/test_refactoring_pipeline.py`

### Implementation for User Story 2

- [ ] T019 [US2] Implement `code/llm/refactoring.py`: Invoke HuggingFace Inference API for `WizardCoder-Python-13B` with zero-shot prompts; implement batching (≤10), retry logic (limited number of attempts), and **timeout=60** seconds per attempt.
- [ ] T020 [US2] Implement `code/llm/baseline.py`: Generate null baseline (identity transformation) for each valid function.
- [ ] T021 [US2] Implement `code/llm/quality.py`: Calculate cyclomatic complexity and pylint scores for original, refactored, and baseline code; compute deltas (Δ) for each. **Validation**: After computing the baseline delta (original vs. identity), verify that `|delta| < 0.01`. If this condition fails, raise a `ValueError` with a message indicating baseline generation failure.
- [ ] T023 [US2] [P] Integrate caching: Modify `code/llm/refactoring.py` to use `code/utils/cache.py` with `function_hash` as the cache key; ensure cache check occurs before API call.
- [ ] T022 [US2] Implement `code/llm/pipeline.py`: Orchestrate refactoring and baseline generation (calling T019, T020, T021, T023), handle syntax errors in LLM output (mark as "Refactoring Failed"), and save `data/processed/refactoring_results.json` with deltas.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Predictive Modeling and Statistical Validation (Priority: P3)

**Goal**: Fit Multiple Linear Regression (OLS), Ridge Regression, and GLM models; perform Paired T-Test and One-Sample T-Test; validate significance.

**Independent Test**: Feed `data/processed/refactoring_results.json` to `code/models/regression.py` and verify output of coefficients, adjusted R², and t-test p-values.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T024 [P] [US3] Unit test for VIF calculation and predictor filtering in `tests/unit/test_regression.py`
- [ ] T025 [P] [US3] Unit test for one-sample t-test implementation in `tests/unit/test_stats.py`
- [ ] T026 [P] [US3] Integration test for full modeling pipeline in `tests/integration/test_modeling_pipeline.py`

### Implementation for User Story 3

- [ ] T027 [US3] Implement `code/models/stats.py`: Perform **One-Sample T-Test** against zero for improvement metrics (ΔComplexity, ΔPylint). **Decision Logic**: This test is the primary validator ONLY if the baseline delta (from T021) is effectively zero (|delta| < 0.01). If the baseline delta is non-zero, skip this test and rely on the Paired T-Test (T029).
- [ ] T030 [US3] [P] Implement VIF Filtering: In `code/models/regression.py`, calculate Variance Inflation Factors (VIF) for all predictors; **iteratively drop the predictor with the highest VIF and re-fit the model** until all remaining predictors have VIF ≤ 5. Output the filtered predictor set.
- [ ] T028 [US3] [P] Implement `code/models/regression.py` (OLS): Fit a standard **Multiple Linear Regression (OLS)** model using the VIF-filtered predictors; calculate coefficients, p-values, and Adjusted R² (as per FR-004).
- [ ] T029 [US3] [P] Implement `code/models/stats.py` (Paired): Perform a **Paired T-Test** comparing original vs. refactored metric values (as per FR-005 and SC-002). **Decision Logic**: This test is the primary validator if the baseline delta (from T021) is non-zero (|delta| >= 0.01). If the baseline delta is effectively zero, skip this test to avoid redundancy.
- [ ] T031 [US3] [P] Implement `code/models/regression.py` (Ridge/GLM): Fit Ridge Regression (continuous) and GLM (count data) with robust standard errors using the VIF-filtered predictors.
- [ ] T032 [US3] [P] Implement `code/main.py`: Final pipeline orchestration. **Logic**:
 1. Load processed data.
 2. Run VIF filtering (T030).
 3. Fit OLS (T028).
 4. **Execute Statistical Tests**: Check baseline delta. If |delta| >= 0.01, run T029 (Paired) and use its result as the primary conclusion. If |delta| < 0.01, run T027 (One-Sample) and use its result as the primary conclusion.
 5. **Cross-Validation**: Implement **k-fold cross-validation** (e.g., 5-fold). Split data, iterate through folds, fit the model on each fold, and **aggregate the mean coefficients** from all folds.
 6. Run Ridge/GLM (T031).
 7. Validate output against `contracts/output.schema.yaml`.
 8. Generate `data/results/model_summary.json` including the **mean coefficients from folds**, adjusted R², and the primary statistical test result (Paired or One-Sample) based on the decision logic. **References FR-004, FR-005, FR-008, FR-010**.
- [ ] T033 [US3] [P] Add logic to report mean coefficients from folds as final result and ensure model validity (p < 0.05 for F-test and at least one predictor).

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T034 [P] Generate draft paper in `paper/draft.md` from `data/results/model_summary.json` using the template in `specs/001-leveraging-llm-refactoring/research.md`
- [ ] T035 [P] Update `README.md` with project status, dependencies, and run instructions
- [ ] T036 [P] Security hardening: Implement API key masking in logs and use `secrets` module for env var loading in `code/config.py`
- [ ] T037 [P] Run validation: Execute `python code/main.py --validate` and verify exit code 0
- [ ] T038 [P] Profile API latency in `code/llm/refactoring.py` to ensure batch processing meets <60s per attempt constraint
- [ ] T039 [P] Run `ruff check.` and `black.` to enforce code cleanup standards

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data (raw metrics)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 data (deltas)
 - *Note: While US2 and US3 can be coded in parallel, US3 cannot run until US2 produces `refactoring_results.json`.*

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
Task: "Unit test for metric calculation in tests/unit/test_static_analysis.py"
Task: "Unit test for dataset sampling logic in tests/unit/test_download.py"

# Launch all models for User Story 1 together:
Task: "Implement download.py"
Task: "Implement static_analysis.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (verify `raw_metrics.json` with 5 predictors).
5. Deploy/demo if ready.

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Verify deltas)
4. Add User Story 3 → Test independently → Deploy/Demo (Verify statistical significance)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Data & Metrics)
 - Developer B: User Story 2 (LLM & Deltas)
 - Developer C: User Story 3 (Modeling & Stats)
3. Stories complete and integrate independently (US3 depends on US2 output).

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **Critical Data Constraint**: The pipeline MUST fail loudly if the BigCode dataset is inaccessible; no synthetic fallbacks allowed.
- **Critical API Constraint**: No silent fallback to smaller models; if WizardCoder API fails, the run halts.
- **Statistical Constraint**: Use both paired t-test (FR-005) and one-sample t-test (Plan correction) with clear decision logic: Paired is primary unless baseline is identity.
- **Model Constraint**: Implement both OLS (FR-004) and Ridge/GLM (Plan) to satisfy all requirements.
- **Cross-Validation Requirement**: T032 MUST implement k-fold cross-validation and report mean coefficients.