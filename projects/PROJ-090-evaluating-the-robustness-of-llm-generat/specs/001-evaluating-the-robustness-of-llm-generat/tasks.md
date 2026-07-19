# Tasks: Evaluating the Robustness of LLM-Generated Code to Input Perturbations

**Input**: Design documents from `/specs/001-evaluating-robustness-llm-code/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this belongs to (e.g., US1, US2, US3)
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

- [ ] T001 [P] Create `data/` directory at repository root with 755 permissions
- [ ] T002 [P] Create `data/raw/`, `data/processed/`, `data/logs/` subdirectories with 755 permissions
- [ ] T003 [P] Create `tests/`, `tests/unit/`, `tests/contract/` directories with 755 permissions
- [X] T004 [P] Create `requirements.txt` with pinned versions for `transformers`, `datasets`, `sentence-transformers`, `bitsandbytes`, `scikit-learn`, `statsmodels`, `pandas`, `pytest`
- [X] T005 [P] Configure linting (ruff) and formatting (black) tools in `pyproject.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T006 [P] Setup sandbox execution environment (Docker or `subprocess` with `resource` limits) in `code/model/sandbox.py` with network disabled
- [X] T007 [P] Configure environment variables for model paths, timeouts, and random seeds in `code/config.py`
- [X] T008 [P] Create base logging infrastructure to capture raw scores, perturbation types, and execution errors in `code/utils/logging.py`
- [X] T009 [P] Implement checksum validation script in `code/utils/validate_checksums.py` to verify `data/` integrity
- [X] T010 [P] Setup experiment state management to track sample counts and budget caps in `code/utils/state.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Semantic-Preserving Perturbation Generation (Priority: P1) 🎯 MVP

**Goal**: Download HumanEval, generate perturbed variants, and filter via semantic similarity (>0.95) while retaining raw scores.

**Independent Test**: The pipeline can be tested by running the perturbation generator on a mock HumanEval task and verifying the output JSON contains up to 3 distinct variants (or fewer if semantic validation fails), correctly tagged by type (`synonym`, `typo`, `rephrase`), with a recorded raw semantic similarity score for every candidate and a filtered score > 0.95 for retained items, without running model inference.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T011 [P] [US1] Contract test for perturbation output schema in `tests/contract/test_perturbation_schema.py`: Assert JSON schema matches v1.0 defined in `contracts/perturbation_schema.json` with required fields `task_id`, `perturbation_type`, `raw_score`, `is_valid`. **Note**: Ensure `contracts/perturbation_schema.json` is created in Phase 1.

### Implementation for User Story 1

- [X] T012 [US1] Implement HumanEval download script in `code/data/download_humaneval.py` using `datasets.load_dataset("openai_humaneval")`
- [X] T013 [US1] Implement `substitute_synonyms()` function in `code/data/perturbations.py` for non-keyword token replacement
- [X] T014 [US1] Implement `inject_typos()` function in `code/data/perturbations.py` for random character typo injection
- [X] T015 [US1] Implement `rephrase_syntax()` function in `code/data/perturbations.py` for syntactic rephrasing
- [X] T016 [US1] Implement semantic validation using `sentence-transformers/all-MiniLM-L6-v2` in `code/data/semantic_validator.py` to calculate cosine similarity. **STRICT CONSTRAINT**: Only perturbations with score > 0.95 are retained. **NO FALLBACK LOGIC ALLOWED**. **Note**: The Plan's "fallback to >0.90" strategy contradicts Spec FR-002/FR-003 and is invalid. This task enforces the Spec.
- [X] T017 [US1] Implement perturbation generation pipeline in `code/data/generate_perturbations.py` that generates up to 3 variants per task (as per FR-002), scores all, and filters to a primary set of max 1 best variant per task (as per Plan feasibility) based on the strict >0.95 threshold. **Logic**: Prioritize all original tasks, then fill remaining budget with perturbed prompts in deterministic order (FR-011).
- [ ] T018 [US1] Implement logging for ALL generated candidates (included and excluded) to `data/processed/perturbation_candidates.json` using JSON format with fields: `task_id`, `perturbation_type`, `raw_score`, `is_valid`, `reason`. **Verification**: Verify file exists, is non-empty, and contains required schema fields. **Execution Order**: This task consumes the raw generation output from T017 before final filtering is applied to the primary dataset.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 3.1: Budget Cap Logic (Cross-Cutting / Post-US1)

**Goal**: Enforce the total generation budget cap (FR-011) after data generation is complete, using a dynamic feasibility calculation.

*Note: Budget cap logic is integrated into T017 to ensure pre-check before inference.*

---

## Phase 4: User Story 2 - CPU-Compatible Model Inference and Execution (Priority: P2)

**Goal**: Execute StarCoder (quantized) on CPU, generate code, capture pass/fail results.

**Independent Test**: The pipeline can be tested by running inference on a single sample task and verifying the output code executes in the sandbox, returning a pass/fail status within the defined timeout, independent of statistical analysis.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [P] [US2] Unit test for sandbox timeout enforcement in `tests/unit/test_sandbox_timeout.py`: Verify `subprocess.run` raises TimeoutExpired after a specified timeout duration.
- [X] T020 [P] [US2] Mock test for model loading in `tests/unit/test_model_load.py`: Verify `bitsandbytes` -bit quantization flag is set and CPU device is used.

### Implementation for User Story 2

- [X] T021 [US2] Implement StarCoder2-3B loading with `bitsandbytes` 4-bit quantization and CPU offload in `code/model/inference.py`
- [X] T022 [US2] Implement generation loop with a configurable timeout, fixed seed in `code/model/inference.py`
- [ ] T023 [US2] Integrate sandbox executor to run generated code with a **Fixed timeout per test case

The research question, method, and references remain as originally planned, with the specific duration parameter generalized to a fixed timeout setting to accommodate implementation variability.** in `code/model/sandbox.py`. **Note**: This explicitly implements the requirement from FR-005 and US-2 Acceptance Scenario 2.
- [X] T024 [US2] Implement raw error tagging logic (syntax, timeout, OOM, pass, fail) in `code/model/execution_results.py`
- [X] T025 [US2] Add OOM handling to skip sample and log "OOM" flag in `code/model/inference.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis, Multiplicity Correction, Calibration, and Error Classification (Priority: P3)

**Goal**: Calculate pass@1 rates, apply McNemar's test with Bonferroni correction, perform Mixed-Effects Logistic Regression, analyze sensitivity to semantic thresholds, and classify errors.

**Independent Test**: The pipeline can be tested by feeding a mock CSV of pass/fail results and threshold metadata into the analysis script and verifying the statistical output (p-values, corrected alpha, mixed-effects coefficients, sensitivity report) matches expected calculations.

**Scope Boundary**: The study is strictly limited to FR-001 through FR-013.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T026 [P] [US3] Unit test for McNemar's test calculation in `tests/unit/test_statistics.py`: Verify p-value calculation against known contingency table.
- [X] T027 [P] [US3] Unit test for sensitivity analysis threshold handling in `tests/unit/test_sensitivity.py`: Verify filtering logic for thresholds {, 0.90, 0.95, 0.99}.
- [X] T028 [P] [US3] Unit test for error classifier in `tests/unit/test_error_classifier.py`: Verify stratified sampling logic.

### Implementation for User Story 3

- [X] T029 [US3] Implement pass@1 calculation for original and perturbed prompts in `code/analysis/statistics.py`
- [X] T030 [US3] Implement McNemar's test aggregation across tasks for each perturbation type in `code/analysis/statistics.py`
- [ ] T031 [US3] Implement Bonferroni correction for multiple comparisons (multiple types) in `code/analysis/statistics.py`
- [ ] T032 [US3] Implement Mixed-Effects Logistic Regression with 'task' as random effect using `statsmodels` in `code/analysis/statistics.py`. **Deliverable**: Output variance component for 'task' to `data/processed/mixed_effects_results.json` for SC-007. **Verification**: Verify file exists and contains variance component for 'task'.
- [ ] T033 [US3] Implement sensitivity analysis on semantic thresholds across the specific range {0.85, 0.90, 0.95, 0.99} as defined in FR-009 in `code/analysis/statistics.py`. **Deliverable**: Generate `data/processed/sensitivity_report.csv` with columns: `threshold`, `pass_rate`, `delta_from_baseline`. **Verification**: Verify file exists, columns match spec, and sweep range is exactly {0.85, 0.90, 0.95, 0.99}.
- [ ] T034 [US3] Implement error classifier for stratified sampling (≤50 failures or sample of 50) to tag as syntax/logic in `code/analysis/error_classifier.py` using stratification by perturbation type and random seed=42. **Deliverable**: Output tags to `data/processed/error_classification_report.json` for consumption by T035. **Verification**: Verify file exists, contains stratified sample tags, and uses seed=42.
- [ ] T035 [US3] Generate final report aggregating pass@1 degradation, statistical significance, mixed-effects variance, sensitivity metrics in `code/analysis/report_generator.py`. **Deliverable**: `docs/research_report.md`. **Verification**: Verify file exists and contains all required sections (pass@1, McNemar, Mixed-Effects, Sensitivity).

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T036 [P] Documentation updates in `docs/` including metric definitions (pass@1, McNemar, Bonferroni)
- [ ] T037 [P] Remove unused imports and dead code across all modules
- [ ] T038 [P] Optimize memory usage to ensure CPU usage < 6GB per process
- [ ] T039 [P] Add unit tests for edge cases (timeout, OOM, empty dataset) in `tests/unit/`
- [ ] T040 [P] Security hardening for sandbox execution
- [ ] T041 [P] Run `quickstart.md` validation

**Note**: The plan.md mentions missing numeric values for SC-003 (-hour limit) and SC-006 (sample size). This is flagged for kickback to the planning stage to document the justification for these assumptions.
**Note**: Tasks T024a, T039, T040, T041 (ECE/Calibration) have been removed as they lacked spec anchors (FR/SC).

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on data from US1
 - **Specific Note**: T017 (Generation) must complete before T018 (Logging/Filtering).
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on results from US1 and US2
 - **Specific Note**: T033 (Sensitivity) and T034 (Error Classifier) are independent statistical tasks.

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
3. Add User Story 2 → Test independently → Deploy/Demo (Includes CPU Inference)
4. Add User Story 3 → Test independently → Deploy/Demo (Includes Sensitivity Analysis, Error Classification, Mixed-Effects Models)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1
 - Developer B: User Story 2 (Focus on CPU Inference)
 - Developer C: User Story 3 (Focus on Sensitivity Metrics, Error Classification, Mixed-Effects Models)
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
- **Critical Constraint**: All model inference tasks (T021-T025) MUST run on CPU with 4-bit quantization; no CUDA dependencies allowed.
- **Critical Constraint**: All perturbation tasks (T013-T017) MUST use real HumanEval data; no synthetic/fake data generation.
- **Critical Constraint**: Semantic similarity threshold is strictly > 0.95; **NO FALLBACK LOGIC ALLOWED** per spec FR-002/FR-003. The Plan's "fallback to >0.90" is invalid and flagged for kickback.
- **Critical Revision**: Tasks T024a, T039, T040, T041 (ECE/Calibration) have been REMOVED as they lacked spec anchors.
- **Critical Revision**: T017 and T018 logic clarified: T017 generates up to 3, T018 logs raw output and applies strict filtering.
- **Critical Revision**: T033 explicitly lists thresholds {0.85, 0.90, 0.95, 0.99} to match FR-009.
- **Critical Revision**: T001-T003 updated with specific paths and permissions.
- **Critical Revision**: T037-T039 replaced vague polish tasks with specific, measurable actions.
- **Critical Revision**: T023 updated to explicitly bind the 10-second timeout to "per test case" as per FR-005 and US-2.
