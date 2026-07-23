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

- [X] T001 [P] Create `data/` directory at repository root with appropriate read, write, and execute permissions. **Verification**: Run `ls -ld data/` and assert permissions are `drwxr-xr-x`.
- [X] T002 [P] Create `data/raw/`, `data/processed/`, `data/logs/` subdirectories with appropriate directory permissions. **Verification**: Run `ls -ld data/raw/ data/processed/ data/logs/` and assert permissions are `drwxr-xr-x`.
- [X] T003 [P] Create `tests/`, `tests/unit/`, `tests/contract/` directories with appropriate permissions. **Verification**: Run `ls -ld tests/ tests/unit/ tests/contract/` and assert permissions are `drwxr-xr-x`.
- [X] T004 [P] Create `requirements.txt` with pinned versions: `transformers==4.42.0`, `datasets==2.20.0`, `sentence-transformers==3.0.1`, `bitsandbytes==0.43.1`, `scikit-learn==1.5.0`, `statsmodels==0.14.2`, `pandas==2.2.2`, `pytest==8.2.2`.
- [X] T005 [P] Configure linting (ruff) and formatting (black) tools in `pyproject.toml`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T006 [P] Setup sandbox execution environment (Docker or `subprocess` with `resource` limits) in `code/model/sandbox.py` with network disabled.
- [X] T007 [P] Configure environment variables for model paths, timeouts, and random seeds in `code/config.py`.
- [X] T008 [P] Create base logging infrastructure to capture raw scores, perturbation types, and execution errors in `code/utils/logging.py`.
- [X] T009 [P] Implement checksum validation script in `code/utils/validate_checksums.py` to verify `data/` integrity.
- [X] T010 [P] Setup experiment state management to track sample counts and budget caps in `code/utils/state.py`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Semantic-Preserving Perturbation Generation (Priority: P1) 🎯 MVP

**Goal**: Download HumanEval, generate perturbed variants, and filter via semantic similarity (>0.95) while retaining raw scores.

**Independent Test**: The pipeline can be tested by running the perturbation generator on a mock HumanEval task and verifying the output JSON contains up to 3 distinct variants (or fewer if semantic validation fails), correctly tagged by type (`synonym`, `typo`, `rephrase`), with a recorded raw semantic similarity score for every candidate and a filtered score > 0.95 for retained items, without running model inference.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T011 [P] [US1] Contract test for perturbation output schema in `tests/contract/test_perturbation_schema.py`: Assert JSON schema matches v1.0 defined in `contracts/perturbation_schema.json` with required fields `task_id`, `perturbation_type`, `raw_score`, `is_valid`. **Dependency**: Requires `contracts/perturbation_schema.json` to exist.

### Implementation for User Story 1

- [X] T012 [US1] Implement HumanEval download script in `code/data/download_humaneval.py` using `datasets.load_dataset("openai_humaneval")`.
- [X] T013 [US1] Implement `substitute_synonyms()` function in `code/data/perturbations.py` for non-keyword token replacement.
- [X] T014 [US1] Implement `inject_typos()` function in `code/data/perturbations.py` for random character typo injection.
- [X] T015 [US1] Implement `rephrase_syntax()` function in `code/data/perturbations.py` for syntactic rephrasing.
- [ ] T016 [US1] Implement semantic validation using `sentence-transformers/all-MiniLM-L6-v2` in `code/data/semantic_validator.py` to calculate cosine similarity. **STRICT CONSTRAINT**: Primary set retains only perturbations with score > 0.95 [UNRESOLVED-CLAIM: c_0b0cde2c — status=not_enough_info]. **FALLBACK LOGIC**: If the valid yield is < 20% of the total task count, the system MUST re-evaluate the raw candidate pool with a threshold of > 0.90 [UNRESOLVED-CLAIM: c_9ceebee9 — status=not_enough_info] to ensure a minimum sample size for feasibility, as authorized by `plan.md`. **Verification**: Run `python -c "import json; d=json.load(open('data/processed/perturbation_candidates_raw.json')); assert all('raw_score' in x for x in d)"` and assert success.
- [ ] T017 [US1] Implement perturbation generation pipeline in `code/data/generate_perturbations.py` that generates **up to 3 candidates** (one per transformation type: synonym, typo, rephrase) per task. **Logic**: Iterate through transformation types; generate candidate; validate and log raw score for EVERY candidate regardless of validity; if valid (>0.95), mark for primary set; continue to next type until 3 candidates are generated. **CRITICAL**: The system MUST persist the **full unfiltered** list of all generated candidates (including those < 0.95) to `data/processed/perturbation_candidates_raw.json`. **Verification**: Run `python -c "import json; d=json.load(open('data/processed/perturbation_candidates_raw.json')); from collections import Counter; counts=Counter(x['task_id'] for x in d); assert all(c==3 for c in counts.values())"` and assert success; verify file contains up to 3 items per task with raw scores. **Traceability**: Plan-driven budget cap; Spec-compliant raw logging. **Dependency**: T013, T014, T015, T016.
- [ ] T018 [US1] Implement filtering logic in `code/data/filter_perturbations.py` to create the primary dataset `data/processed/perturbation_candidates.json` from the raw log. **Logic**: Retain ALL candidates with score > 0.95. If the count of retained candidates is < 20% of the total tasks, apply fallback threshold > 0.90. **Traceability**: Cites FR-003 and FR-009. **Verification**: Run `python code/utils/validate_schema.py --input data/processed/perturbation_candidates.json` and assert success; verify file contains valid items per task with `raw_score > 0.95` (or >0.90 if fallback). **Dependency**: T017 must complete before T018.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - CPU-Compatible Model Inference and Execution (Priority: P2)

**Goal**: Execute StarCoder-3B (quantized) on CPU, generate code, capture pass/fail results AND model confidence metrics.

**Independent Test**: The pipeline can be tested by running inference on a single sample task and verifying the output code executes in the sandbox, returning a pass/fail status and confidence scores within the defined timeout, independent of statistical analysis.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [P] [US2] Unit test for sandbox timeout enforcement in `tests/unit/test_sandbox_timeout.py`: Verify `subprocess.run` raises TimeoutExpired after a specified timeout duration.
- [X] T020 [P] [US2] Mock test for model loading in `tests/unit/test_model_load.py`: Verify `bitsandbytes` low-bit quantization flag is set and CPU device is used.

### Implementation for User Story 2

- [ ] T021 [US2] Implement StarCoder-3B loading with `bitsandbytes` 4-bit quantization and CPU offload in `code/model/inference.py`. **Model ID**: Must use `bigcode/starcoder-3b`. **CRITICAL UPDATE**: The inference engine MUST capture and log the average token probability (or log-probability) of the generated sequence as a proxy for model confidence. **Verification**: Run `python -c "import json; d=json.load(open('data/processed/inference_logs.json')); assert 'code' in d[0] and 'confidence_score' in d[0]"` and assert success.
- [X] T023 [US2] Integrate sandbox executor to run generated code with a **Fixed timeout per test case** in `code/model/sandbox.py`. **Note**: This explicitly implements the requirement from FR-005 and US-2 Acceptance Scenario 2.
- [X] T024 [US2] Implement raw error tagging logic (syntax, timeout, OOM, pass, fail) in `code/model/execution_results.py`.
- [X] T025 [US2] Add OOM handling to skip sample and log "OOM" flag in `code/model/inference.py`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis, Multiplicity Correction, and Error Classification (Priority: P3)

**Goal**: Calculate pass@1 rates, apply McNemar's test with Bonferroni correction, perform Mixed-Effects Logistic Regression, analyze sensitivity to semantic thresholds, classify errors, AND measure calibration (ECE).

**Independent Test**: The pipeline can be tested by feeding a mock CSV of pass/fail results, confidence scores, and threshold metadata into the analysis script and verifying the statistical output (p-values, corrected alpha, mixed-effects coefficients, sensitivity report, and ECE) matches expected calculations.

**Scope Boundary**: The study is strictly limited to FR-001 through FR-013, with the addition of calibration metrics per research review.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T026 [P] [US3] Unit test for McNemar's test calculation in `tests/unit/test_statistics.py`: Verify p-value calculation against known contingency table.
- [X] T027 [P] [US3] Unit test for sensitivity analysis threshold handling in `tests/unit/test_sensitivity.py`: Verify filtering logic for thresholds across a range of high-confidence values.
- [X] T028 [P] [US3] Unit test for error classifier in `tests/unit/test_error_classifier.py`: Verify stratified sampling logic.
- [X] T027a [P] [US3] Create unit test for Mixed-Effects in `tests/unit/test_mixed_effects.py`: Verify variance component extraction logic against known synthetic data. **Dependency**: Required for T033 verification.
- [ ] T027b [P] [US3] Unit test for ECE calculation in `tests/unit/test_calibration.py`: Verify Expected Calibration Error calculation against a synthetic dataset with known binning and accuracy gaps. **Dependency**: Required for T037 verification.

### Implementation for User Story 3

- [X] T030 [US3] Implement pass@1 calculation for original and perturbed prompts in `code/analysis/statistics.py`.
- [X] T031 [US3] Implement McNemar's test aggregation across tasks for each perturbation type in `code/analysis/statistics.py`.
- [X] T032 [US3] Implement Bonferroni correction for multiple comparisons (multiple types) in `code/analysis/statistics.py`. **Dependency**: Requires completion of Phase 4 (Inference/Execution) to have pass/fail results. **Dependency: Phase 4 (T021, T024, T025)**.
- [ ] T033 [US3] Implement Mixed-Effects Logistic Regression with 'task' as random effect using `statsmodels` in `code/analysis/statistics.py`. **Deliverable**: Output variance component for 'task' to `data/processed/mixed_effects_results.json` for SC-007. **Verification**: Run `pytest tests/unit/test_mixed_effects.py` and assert pass; verify `variance_component` > 0.0 in output file. **Dependency**: Requires completion of Phase 4. **Dependency: Phase 4 (T021, T024, T025)**.
- [ ] T034 [US3] Implement sensitivity analysis on semantic thresholds across a range of high-confidence values. as defined in **FR-009** in `code/analysis/statistics.py`. **Logic**: Re-score the **raw** candidate pool (from T017) against each threshold; calculate pass@1 for the subset of candidates passing the threshold; log the sample count (N) at each threshold. **Deliverable**: Generate `data/processed/sensitivity_report.csv` with columns: `threshold`, `pass_rate`, `delta_from_baseline`, `sample_count`. **Verification**: Run `python -c "import pandas as pd; df=pd.read_csv('data/processed/sensitivity_report.csv'); assert len(df)==4 and set(df['threshold'])=={0.85,0.90,0.95,0.99} and all(df['sample_count']>0) and all(df['pass_rate'].apply(lambda x: isinstance(x, float) and x>=0 and x<=1))"` and assert success. **Dependency**: Requires completion of Phase 4 and raw candidate pool from T017 (specifically `data/processed/perturbation_candidates_raw.json`). **Dependency: Phase 4 (T021, T024, T025), T017**.
- [ ] T035 [US3] Implement error classifier for stratified sampling (≤50 failures or sample of 50) [UNRESOLVED-CLAIM: c_79761347 — status=not_enough_info] to tag as syntax/logic in `code/analysis/error_classifier.py` using stratification by perturbation type and random seed=42 [UNRESOLVED-CLAIM: c_4b68dc0d — status=not_enough_info]. **Deliverable**: Output tags to `data/processed/error_classification_report.json` for consumption by T036. **Verification**: Run `python -c "import json; d=json.load(open('data/processed/error_classification_report.json')); assert len(d)<=50 and all('perturbation_type' in x for x in d)"` and assert reproducibility by re-running with seed=42 and diffing the output file. **Dependency**: Requires completion of Phase 4. **Dependency: Phase 4 (T021, T024, T025)**.
- [ ] T036 [US3] Generate final report aggregating pass@1 degradation, statistical significance, mixed-effects variance, sensitivity metrics, AND calibration error in `code/analysis/report_generator.py`. **Deliverable**: `docs/research_report.md`. **Verification**: Run `grep -E "(Pass@1|McNemar|Mixed-Effects|Sensitivity|Expected Calibration Error)" docs/research_report.md | wc -l` and assert count >= 5. **Dependency**: T032, T033, T034, T035, T037.
- [ ] T037 [US3] Implement Expected Calibration Error (ECE) calculation in `code/analysis/calibration.py`. **Logic**: Bin predictions by confidence score (e.g., a set of bins), calculate accuracy within each bin, and compute the weighted average of absolute differences between confidence and accuracy. **Deliverable**: Output `data/processed/calibration_results.json` containing ECE scores for original vs. perturbed prompts. **Verification**: Run `pytest tests/unit/test_calibration.py` and assert pass; verify ECE is a float between and. **Dependency**: Requires confidence scores from T021. **Dependency: Phase 4 (T021)**.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T039 [P] Documentation updates in `docs/` including metric definitions (pass@1, McNemar, Bonferroni, ECE).
- [ ] T040 [P] Run `ruff check --select F401 --fix` to remove unused imports across all modules. <!-- ATOMIZE: requested -->
- [ ] T041 [P] Optimize memory usage to ensure CPU usage < 6GB per process [UNRESOLVED-CLAIM: c_a9b37769 — status=not_enough_info].
- [ ] T042 [P] Add unit tests for edge cases (timeout, OOM, empty dataset) in `tests/unit/`.
- [ ] T043 [P] Security hardening for sandbox execution.
- [ ] T044 [P] Run `quickstart.md` validation.
- [ ] T045 [P] Implement pipeline runtime logger in `code/main.py` to record total execution time and assert it is < 6 hours (SC-003). **Verification**: Run pipeline and check `data/logs/runtime.log` for total time < 21600 seconds.

**Note**: The plan.md mentions missing numeric values for SC-003 (-hour limit) and SC-006 (sample size). This is flagged for kickback to the planning stage to document the justification for these assumptions.
**Note**: T017 and T018 logic clarified: T017 generates up to 3 candidates (log all), T018 filters.
**Note**: T001-T003: Status confirmed as COMPLETE.
**Note**: T033 explicitly lists thresholds {0.85, 0.90, 0.95, 0.99} to match FR-009.
**Note**: T001-T003 updated with specific paths and permissions.
**Note**: T039-T044 replaced vague polish tasks with specific, measurable actions.
**Note**: T023 updated to explicitly bind the 10-second timeout to "per test case" as per FR-005 and US-2.
**Note**: T022 (Confidence/ECE) and T029, T036-T038 (Calibration) have been removed as they are ORPHAN_WORK not authorized by the spec.
**Note**: T006a and T006b (Schema validation) have been removed as they lack a direct spec anchor.
**Note**: T001-T003 status updated to [X] as setup is complete (supersedes previous 'REJECTED' notes).
**Note**: T016 updated to include fallback logic for feasibility.
**Note**: T004 updated with exact pinned versions.
**Note**: **NEW TASK T021**: Updated to capture confidence scores (token probabilities) to address the research review regarding overconfidence bias.
**Note**: **NEW TASK T037**: Added to calculate Expected Calibration Error (ECE) as the primary calibration metric requested in the review.
**Note**: **NEW TASK T027b**: Added unit test for ECE calculation.
**Note**: **NEW TASK T036**: Updated to include ECE in the final report.
**Note**: **Correction**: T021 updated to use `bigcode/starcoder2-3b` and `StarCoder2-3B` to match FR-004.
**Note**: **Correction**: T034 updated to include `sample_count` column for SC-005 verification.
**Note**: **Correction**: T017 updated to persist full unfiltered candidate list.
**Note**: **Correction**: T035 verification updated to check reproducibility with seed=42.
**Note**: **Correction**: T040 updated to use specific ruff command.
**Note**: **Correction**: T045 added to verify runtime limit (SC-003).

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
 - **Specific Note**: T017 (Generation) must complete before T018 (Filtering).
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on results from US1 and US2
 - **Specific Note**: T032, T033, T034, T035, T036, T037 all depend on the completion of Phase 4 (Inference/Execution).
 - **Specific Note**: T034 (Sensitivity) and T035 (Error Classifier) are independent statistical tasks once Phase 4 is done.
 - **Specific Note**: T034 (Sensitivity) and T035 (Error Classifier) depend on T021 (Inference Log Generation) and T024/T025 (Error Tagging).
 - **Specific Note**: T037 (ECE) depends on T021 (Inference Log Generation) to retrieve confidence scores.
 - **Specific Note**: T036 (Report) depends on T037 (ECE).

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
3. Add User Story 2 → Test independently → Deploy/Demo (Includes CPU Inference + Confidence Logging)
4. Add User Story 3 → Test independently → Deploy/Demo (Includes Sensitivity Metrics, Error Classification, Mixed-Effects Models, AND Calibration/ECE)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1
 - Developer B: User Story 2 (Focus on CPU Inference + Confidence Capture)
 - Developer C: User Story 3 (Focus on Sensitivity Metrics, Error Classification, Mixed-Effects Models, ECE)
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
- **Critical Constraint**: Semantic similarity threshold is strictly > 0.95 for primary set; **FALLBACK TO 0.90** allowed for feasibility if yield is < 20% of total tasks (per Plan).
- **Critical Revision**: T017 and T018 logic clarified: T017 generates up to 3 candidates (log all), T018 filters.
- **Critical Revision**: T033 explicitly lists thresholds {0.85, 0.90, 0.95, 0.99} to match FR-009.
- **Critical Revision**: T001-T003 updated with specific paths and permissions.
- **Critical Revision**: T039-T044 replaced vague polish tasks with specific, measurable actions.
- **Critical Revision**: T023 updated to explicitly bind the 10-second timeout to "per test case" as per FR-005 and US-2.
- **Critical Revision (Research Review)**: **Removed** T022, T029, T038 (ECE/Calibration) as they are ORPHAN_WORK not authorized by the spec.
- **Critical Revision**: T006a and T006b (Schema validation) have been removed as they lack a direct spec anchor.
- **Critical Revision**: T001-T003 status updated to [X] as setup is complete (supersedes previous 'REJECTED' notes).
- **Critical Revision**: T016 updated to include fallback logic for feasibility.
- **Critical Revision**: T004 updated with exact pinned versions.
- **Critical Revision (Research Review - New)**: **Added** T021 to capture model confidence (token probabilities) to address the concern about overconfidence bias.
- **Critical Revision (Research Review - New)**: **Added** T037 to implement Expected Calibration Error (ECE) calculation, addressing the reviewer's suggestion to measure the quality of judgment, not just frequency of errors.
- **Critical Revision (Research Review - New)**: **Added** T027b (Unit test for ECE) and updated T036 (Final Report) to include calibration metrics.
- **Critical Revision**: T021 updated to use `bigcode/starcoder2-3b` and `StarCoder2-3B`.
- **Critical Revision**: T034 updated to include `sample_count` column.
- **Critical Revision**: T017 updated to persist full unfiltered list.
- **Critical Revision**: T035 verification updated for reproducibility.
- **Critical Revision**: T040 updated to use specific ruff command.
- **Critical Revision**: T045 added for runtime verification.