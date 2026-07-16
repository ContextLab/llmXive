# Tasks: Evaluating the Robustness of LLM-Generated Code to Input Perturbations

**Input**: Design documents from `/specs/001-evaluating-robustness-llm-code/`
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

- [ ] T001 [P] Create `code/`, `code/data/`, `code/model/`, `code/analysis/`, `code/utils/` directories
- [ ] T002 [P] Create `data/`, `data/raw/`, `data/processed/`, `data/logs/` directories
- [ ] T003 [P] Create `tests/`, `tests/unit/`, `tests/contract/` directories
- [ ] T004 [P] Initialize Python 3.11 project with `transformers`, `datasets`, `sentence-transformers`, `bitsandbytes`, `scikit-learn`, `statsmodels`, `pandas` dependencies
- [ ] T005 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T006 [P] Setup sandbox execution environment (Docker or `subprocess` with `resource` limits) in `code/model/sandbox.py`
- [ ] T007 [P] Configure environment variables for model paths, timeouts, and random seeds in `code/config.py`
- [ ] T008 [P] Create base logging infrastructure to capture raw scores, perturbation types, and execution errors in `code/utils/logging.py`
- [ ] T009 [P] Implement checksum validation script in `code/utils/validate_checksums.py` to verify `data/` integrity
- [ ] T010 [P] Setup experiment state management to track sample counts and budget caps in `code/utils/state.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Semantic-Preserving Perturbation Generation (Priority: P1) 🎯 MVP

**Goal**: Download HumanEval, generate perturbed variants, and filter via semantic similarity (>0.95) while retaining raw scores.

**Independent Test**: The pipeline can be tested by running the perturbation generator on a mock HumanEval task and verifying the output JSON contains up to 3 distinct variants (or fewer if semantic validation fails), correctly tagged by type (`synonym`, `typo`, `rephrase`), with a recorded raw semantic similarity score for every candidate and a filtered score > 0.95 for retained items, without running model inference.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T011 [P] [US1] Contract test for perturbation output schema in `tests/contract/test_perturbation_schema.py`: Assert JSON schema matches v1.0 defined in `contracts/perturbation_schema.json` with required fields `task_id`, `perturbation_type`, `raw_score`, `is_valid`.
- [ ] T012 [P] [US1] Unit test for synonym substitution logic in `tests/unit/test_perturbation_synonyms.py`: Verify `substitute_synonyms()` replaces only non-keyword tokens and preserves code syntax structure.

### Implementation for User Story 1

- [ ] T013 [US1] Implement HumanEval download script in `code/data/download_humaneval.py` using `datasets.load_dataset("openai_humaneval")`
- [ ] T014 [US1] Implement `substitute_synonyms()` function in `code/data/perturbations.py` for non-keyword token replacement
- [ ] T015 [US1] Implement `inject_typos()` function in `code/data/perturbations.py` for random character typo injection
- [ ] T016 [US1] Implement `rephrase_syntax()` function in `code/data/perturbations.py` for syntactic rephrasing
- [ ] T017 [US1] Implement semantic validation using `sentence-transformers/all-MiniLM-L6-v2` in `code/data/semantic_validator.py` to calculate cosine similarity. **STRICT CONSTRAINT**: Only perturbations with score > 0.95 are retained. No fallback logic allowed.
- [ ] T018 [US1] Implement perturbation generation pipeline in `code/data/generate_perturbations.py` that generates up to 3 variants, scores all, and filters primary set (>0.95).
- [ ] T020 [US1] Implement logging for ALL generated candidates (included and excluded) to `data/processed/perturbation_candidates.json` using JSON format with fields: `task_id`, `perturbation_type`, `raw_score`, `is_valid`, `reason`. **Note**: This file must contain the full candidate pool for sensitivity analysis (FR-009).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 3.1: Budget Cap Logic (Cross-Cutting / Post-US1)

**Goal**: Enforce the total generation budget cap (FR-011) after data generation is complete, using a dynamic feasibility calculation.

- [ ] T029a [US1] Implement feasibility estimator in `code/utils/feasibility.py` to calculate `MAX_SAMPLES` based on estimated runtime/memory constraints (SC-003/SC-006). Output result to `data/config/feasibility.json`.
- [ ] T029b [US1/US2] Implement budget cap enforcer in `code/main.py` to read `MAX_SAMPLES` from `data/config/feasibility.json`, prioritize all original tasks first, and fill remaining slots with perturbed prompts in deterministic order (sorted by task_id, then perturbation type).

**Checkpoint**: Data generation and budgeting are finalized. Ready for Inference.

---

## Phase 4: User Story 2 - CPU-Compatible Model Inference and Execution (Priority: P2)

**Goal**: Execute StarCoder-3B (4-bit quantized) on CPU, generate code, capture pass/fail results.

**Independent Test**: The pipeline can be tested by running inference on a single sample task and verifying the output code executes in the sandbox, returning a pass/fail status within the defined timeout, independent of statistical analysis.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T022 [P] [US2] Unit test for sandbox timeout enforcement in `tests/unit/test_sandbox_timeout.py`: Verify `subprocess.run` raises TimeoutExpired after a specified timeout duration..
- [ ] T023 [P] [US2] Mock test for model loading in `tests/unit/test_model_load.py`: Verify `bitsandbytes` 4-bit quantization flag is set and CPU device is used.

### Implementation for User Story 2

- [ ] T024 [US2] Implement StarCoder2-3B loading with `bitsandbytes` 4-bit quantization and CPU offload in `code/model/inference.py`
- [ ] T025 [US2] Implement generation loop with a configurable timeout, fixed seed in `code/model/inference.py`
- [ ] T026 [US2] Integrate sandbox executor to run generated code with a fixed timeout per test case in `code/model/sandbox.py`
- [ ] T027 [US2] Implement raw error tagging logic (syntax, timeout, OOM, pass, fail) in `code/model/execution_results.py`
- [ ] T028 [US2] Add OOM handling to skip sample and log "OOM" flag in `code/model/inference.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis, Multiplicity Correction, and Error Classification (Priority: P3)

**Goal**: Calculate pass@1 rates, apply McNemar's test with Bonferroni correction, perform Mixed-Effects Logistic Regression, analyze sensitivity to semantic thresholds, and classify errors.

**Independent Test**: The pipeline can be tested by feeding a mock CSV of pass/fail results and threshold metadata into the analysis script and verifying the statistical output (p-values, corrected alpha, mixed-effects coefficients, sensitivity report) matches expected calculations.

**Scope Boundary**: The study is strictly limited to FR-001 through FR-013. Calibration metrics (ECE) are OUT OF SCOPE.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T031 [P] [US3] Unit test for McNemar's test calculation in `tests/unit/test_statistics.py`: Verify p-value calculation against known contingency table.
- [ ] T032 [P] [US3] Unit test for sensitivity analysis threshold handling in `tests/unit/test_sensitivity.py`: Verify filtering logic for a range of thresholds.

### Implementation for User Story 3

- [ ] T033 [US3] Implement pass@1 calculation for original and perturbed prompts in `code/analysis/statistics.py`
- [ ] T034 [US3] Implement McNemar's test aggregation across tasks for each perturbation type in `code/analysis/statistics.py`
- [ ] T035 [US3] Implement Bonferroni correction for multiple comparisons (multiple types) in `code/analysis/statistics.py`
- [ ] T036 [US3] Implement Mixed-Effects Logistic Regression with 'task' as random effect using `statsmodels` in `code/analysis/statistics.py`. **Deliverable**: Output variance component for 'task' to `data/processed/mixed_effects_results.json` for SC-007.
- [ ] T037 [US3] Implement sensitivity analysis on semantic thresholds across a range of high-confidence values in `code/analysis/statistics.py`. **Deliverable**: Generate `data/processed/sensitivity_report.csv` with columns: `threshold`, `pass_rate`, `delta_from_baseline`.
- [ ] T037a [US3] Generate final comparative report for threshold sweep (FR-013) in `code/analysis/report_generator.py`. **Deliverable**: Append sensitivity analysis summary to `docs/research_report.md`.
- [ ] T038 [US3] Implement error classifier for stratified sampling (≤50 failures or sample of 50) to tag as syntax/logic in `code/analysis/error_classifier.py` using stratification by perturbation type and random seed=42. **Deliverable**: Output tags to `data/processed/error_classification_report.json` for consumption by T042.
- [ ] T042 [US3] Generate final report aggregating pass@1 degradation, statistical significance, mixed-effects variance, and sensitivity metrics in `code/analysis/report_generator.py`. **Deliverable**: `docs/research_report.md`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T043 [P] Documentation updates in `docs/` including metric definitions (pass@1, McNemar, Bonferroni)
- [ ] T044 Code cleanup and refactoring
- [ ] T045 Performance optimization across all stories (ensure CPU usage < 7GB)
- [ ] T046 [P] Additional unit tests (if requested) in `tests/unit/`
- [ ] T047 Security hardening for sandbox execution
- [ ] T048 Run `quickstart.md` validation

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
- **Budget Cap (Phase 3.1)**: Depends on T018 (Perturbation Generation) to have counts available.
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on data from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on results from US1 and US2
 - **Specific Note**: T037 (Sensitivity) and T038 (Error Classifier) are independent statistical tasks.

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
Task: "Contract test for perturbation output schema in tests/contract/test_perturbation_schema.py"
Task: "Unit test for synonym substitution logic in tests/unit/test_perturbation_synonyms.py"

# Launch all models for User Story 1 together:
Task: "Implement substitute_synonyms() in code/data/perturbations.py"
Task: "Implement inject_typos() in code/data/perturbations.py"
Task: "Implement rephrase_syntax() in code/data/perturbations.py"
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
3. Add Budget Cap (T029a, T029b) → Ensure generation limits are respected
4. Add User Story 2 → Test independently → Deploy/Demo (Includes CPU Inference)
5. Add User Story 3 → Test independently → Deploy/Demo (Includes Sensitivity Analysis, Error Classification, and Mixed-Effects Models)
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1
 - Developer B: User Story 2 (Focus on CPU Inference)
 - Developer C: User Story 3 (Focus on Sensitivity Metrics, Error Classification, and Mixed-Effects Models)
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
- **Critical Constraint**: All model inference tasks (T024-T028) MUST run on CPU with 4-bit quantization; no CUDA dependencies allowed.
- **Critical Constraint**: All perturbation tasks (T014-T018) MUST use real HumanEval data; no synthetic/fake data generation.
- **Critical Constraint**: Semantic similarity threshold is strictly > 0.95; no fallback allowed per spec FR-002/FR-003. **Note**: The `plan.md` summary currently mentions a "fallback to >0.90" which contradicts the spec. This is flagged for kickback to the planning stage.
- **Critical Revision**: The study scope is strictly limited to FR-001 through FR-013. Tasks T050-T053 (ECE/Calibration) have been removed as they were unverified scope creep.
- **Critical Revision**: Budget cap logic (T029) has been split into T029a (feasibility estimation) and T029b (enforcement) to satisfy FR-011.
- **Critical Revision**: Tasks T030, T039, T040, T041 have been removed as they represented unapproved scope creep.