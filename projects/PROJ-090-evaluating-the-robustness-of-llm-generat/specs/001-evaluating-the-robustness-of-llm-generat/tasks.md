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
- [X] T004 [P] Create `requirements.txt` with pinned versions: `transformers==4.42.0 `, `datasets==2.20.0 `, `sentence-transformers==3.0.1 `, `bitsandbytes==0.43.1 `, `scikit-learn==1.5.0 `, `statsmodels==0.14.2 `, `pandas==2.2.2 `, `pytest==8.2.2 `, `numpy==1.26.4 `, `psutil==5.9.0 `.
- [X] T005 [P] Configure linting (ruff) and formatting (black) tools in `pyproject.toml` at the repository root with explicit settings: `line-length = 88 `, `target-version = 'py311' `, `select = ['E', 'F', 'W', 'I']`. **Verification**: Run `ruff check --config pyproject.toml` and assert exit code 0; verify `black --check` passes.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T006 [P] Setup sandbox execution environment (Docker or `subprocess` with `resource` limits) in `code/model/sandbox.py` with network disabled.
- [X] T007 [P] Configure environment variables for model paths, timeouts, and random seeds in `code/config.py`.
- [X] T008 [P] Create base logging infrastructure to capture raw scores, perturbation types, and execution errors in `code/utils/logging.py`.
- [X] T009 [P] Implement checksum validation script in `code/utils/validate_checksums.py` to verify `data/` integrity.
- [ ] T011a [P] Create `contracts/perturbation_schema.json` defining the v1.0 schema for perturbation output (fields: `task_id`, `perturbation_type`, `raw_score`, `is_valid`, `candidate_text`). **Verification**: Run `python -c "import json; s=json.load(open('contracts/perturbation_schema.json')); assert 'task_id' in s['properties']"` and assert success. **Traceability**: Required for T011 (Contract Test).
- [ ] T009a [P] Create `code/utils/validate_schema.py` utility script to validate JSON files against a schema file. **Verification**: Run `python code/utils/validate_schema.py --input data/processed/test.json --schema contracts/perturbation_schema.json` (with dummy data) and assert it handles validation errors gracefully. **Traceability**: Required for T018.
- [X] T011b [P] Implement `code/model/model_selector.py` to enforce the Plan's override of FR-004: select `bigcode/starcoder-1.5b ` for CPU runs and `bigcode/starcoder-3b ` for GPU runs, logging the selection rationale. **Verification**: Run `python code/model/model_selector.py --cpu` and assert it returns `bigcode/starcoder-1.5b `. **Traceability**: Addresses FR-004 vs Plan.md conflict.
- [X] T010 [P] Setup experiment state management to track sample counts and budget caps in `code/utils/state.py`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Semantic-Preserving Perturbation Generation (Priority: P1) 🎯 MVP

**Goal**: Download HumanEval, generate perturbed variants, and filter via semantic similarity (>0.95) while retaining raw scores.

**Independent Test**: The pipeline can be tested by running the perturbation generator on a mock HumanEval task and verifying the output JSON contains up to 3 distinct variants (or fewer if semantic validation fails), correctly tagged by type (`synonym`, `typo`, `rephrase`), with a recorded raw semantic similarity score for every candidate and a filtered score > 0.95 for retained items, without running model inference.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T011 [P] [US1] Contract test for perturbation output schema in `tests/contract/test_perturbation_schema.py`: Assert JSON schema matches v1.0 defined in `contracts/perturbation_schema.json` with required fields `task_id`, `perturbation_type`, `raw_score`, `is_valid`. **Dependency**: Requires `contracts/perturbation_schema.json` (T011a) to exist.

### Implementation for User Story 1

- [X] T012 [US1] Implement HumanEval download script in `code/data/download_humaneval.py` using `datasets.load_dataset("openai_humaneval")`.
- [X] T013 [P] [US1] Implement `substitute_synonyms()` function in `code/data/perturbations.py` for non-keyword token replacement.
- [X] T014 [P] [US1] Implement `inject_typos()` function in `code/data/perturbations.py` for random character typo injection.
- [X] T015 [P] [US1] Implement `rephrase_syntax()` function in `code/data/perturbations.py` for syntactic rephrasing.
- [ ] T017 [US1] Implement perturbation generation pipeline in `code/data/generate_perturbations.py` that generates **up to 3 candidates** (one per transformation type: synonym, typo, rephrase) per task. **Logic**: Iterate through transformation types; generate candidate; log raw score for EVERY candidate regardless of validity; continue to next type until 3 candidates are generated. **CRITICAL**: The system MUST persist the **full unfiltered** list of all generated candidates to `data/processed/perturbation_candidates_raw.json`. **Schema**: The JSON file MUST be a list of objects, where each object contains: `task_id` (str), `perturbation_type` (str: "synonym"|"typo"|"rephrase"), `raw_score` (float), `is_valid` (bool), `candidate_text` (str). **Cap Logic**: Enforce the total sample cap of **656** (as defined in Plan.md). Prioritize original prompts, then fill remaining slots with perturbed prompts in a deterministic order (sorted by `task_id` ascending, then `perturbation_type` alphabetically). **Verification**: Run `python -c "import json; d=json.load(open('data/processed/perturbation_candidates_raw.json')); from collections import Counter; counts=Counter(x['task_id'] for x in d); assert all(c<=3 for c in counts.values())"` and assert success; verify file contains up to 3 items per task with raw scores. **Traceability**: Plan-driven budget cap (656); Spec-compliant raw logging. **Dependency**: T012, T013, T014, T015, T011a.
- [ ] T016 [US1] Implement semantic validation using `sentence-transformers/all-MiniLM-L-v2` in `code/data/semantic_validator.py` to calculate cosine similarity. **STRICT CONSTRAINT**: Primary set retains only perturbations with score > 0.95 [FR-003]. **Pre-Check**: Verify `data/processed/perturbation_candidates_raw.json` exists; if not, log error and exit. **Logic**: Load `data/processed/perturbation_candidates_raw.json`; calculate similarity; update `is_valid` field; write to `data/processed/perturbation_candidates_validated.json`. **Halt Condition**: If the valid yield is < 1 (zero candidates) across the entire dataset, log a **WARNING** to `data/logs/halt_report.json` with reason "ZERO_YIELD" and **proceed** with available data (if any). **DO NOT exit with code 1**. This aligns with Spec Edge Cases: "proceed with available data but flag reduced sample size". **Verification**: Run `python -c "import json; d=json.load(open('data/processed/perturbation_candidates_validated.json')); assert all('raw_score' in x for x in d)"` AND verify that if yield is zero, `data/logs/halt_report.json` exists and contains `{"reason": "ZERO_YIELD"}`. **Dependency**: T017 must complete before T016.
- [ ] T018 [US1] Implement filtering logic in `code/data/filter_perturbations.py` to create the primary dataset `data/processed/perturbation_candidates.json` from the validated log. **Logic**: Retain ALL candidates with score > 0.95. **Halt Condition**: If the count of retained candidates is insufficient, log a warning to `data/logs/halt_report.json` and proceed with available data. **Traceability**: Cites FR-003 and FR-009. **Verification**: Run `python code/utils/validate_schema.py --input data/processed/perturbation_candidates.json --schema contracts/perturbation_schema.json` and assert success; verify file contains valid items per task with `raw_score > 0.95`. **Dependency**: T016 must complete before T018. <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested -->

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - CPU-Compatible Model Inference and Execution (Priority: P2)

**Goal**: Execute StarCoder (quantized) on CPU, generate code, capture pass/fail results.

**Independent Test**: The pipeline can be tested by running inference on a single sample task and verifying the output code executes in the sandbox, returning a pass/fail status within the defined timeout, independent of statistical analysis.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [P] [US2] Unit test for sandbox timeout enforcement in `tests/unit/test_sandbox_timeout.py`: Verify `subprocess.run` raises TimeoutExpired after a specified timeout duration.
- [X] T020 [P] [US2] Mock test for model loading in `tests/unit/test_model_load.py`: Verify `bitsandbytes` low-bit quantization flag is set and CPU device is used.

### Implementation for User Story 2

- [ ] T021 [US2] Implement StarCoder loading with `bitsandbytes` low-bit quantization and CPU offload in `code/model/inference.py`. **Model ID**: **Per Spec FR-004**, target `bigcode/starcoder-3b `. **Plan Override**: Per Plan.md Compute Feasibility Strategy, if 3B exceeds memory/time limits on CPU, use `bigcode/starcoder2-1.5b ` as a fallback for CPU runs only. Log the selection rationale. **Spec Compliance**: The inference engine MUST enforce the specified timeouts, capture pass/fail results, and log execution status. **Schema**: Output `data/processed/inference_logs.json` MUST be a list of objects, where each object contains: `task_id` (str), `prompt` (str), `code` (str), `status` (str: "pass"|"fail"|"timeout"|"oom"). **Verification**: Run `python -c "import json; import os; f='data/processed/inference_logs.json'; assert os.path.exists(f); d=json.load(open(f)); assert len(d)==0 or ('code' in d[0] and 'status' in d[0])"` and assert success. **Dependency**: T018, T011b. **Traceability**: FR-004 (Spec Primary), Plan.md Compute Feasibility (CPU Fallback).
- [X] T023 [US2] Integrate sandbox executor to run generated code with a **Fixed timeout per test case** in `code/model/sandbox.py`. **Note**: This explicitly implements the requirement from FR-005 and US-2 Acceptance Scenario 2.
- [X] T024 [US2] Implement raw error tagging logic (syntax, timeout, OOM, pass, fail) in `code/model/execution_results.py`.
- [X] T025 [US2] Add OOM handling to skip sample and log "OOM" flag in `code/model/inference.py`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis, Multiplicity Correction, and Error Classification (Priority: P3)

**Goal**: Calculate pass@1 rates, apply McNemar's test with Bonferroni correction, perform Mixed-Effects Logistic Regression, analyze sensitivity to semantic thresholds, and classify errors.

**Independent Test**: The pipeline can be tested by feeding a mock CSV of pass/fail results and threshold metadata into the analysis script and verifying the statistical output (p-values, corrected alpha, mixed-effects coefficients, sensitivity report) matches expected calculations.

**Scope Boundary**: The study is strictly limited to FR-001 through FR-013.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T027 [P] [US3] Unit test for McNemar's test calculation in `tests/unit/test_statistics.py`: Verify p-value calculation against known contingency table.
- [X] T028 [P] [US3] Unit test for sensitivity analysis threshold handling in `tests/unit/test_sensitivity.py`: Verify filtering logic for thresholds across a range of high-confidence values.
- [X] T029 [P] [US3] Unit test for error classifier in `tests/unit/test_error_classifier.py`: Verify stratified sampling logic.
- [X] T030 [P] [US3] Create unit test for Mixed-Effects in `tests/unit/test_mixed_effects.py`: Verify variance component extraction logic against known synthetic data. **Dependency**: Required for T033 verification.

### Implementation for User Story 3

- [X] T032 [US3] Implement pass@1 calculation for original and perturbed prompts in `code/analysis/statistics.py`.
- [X] T033 [US3] Implement McNemar's test aggregation across tasks for each perturbation type in `code/analysis/statistics.py`.
- [X] T034 [US3] Implement Bonferroni correction for multiple comparisons (multiple types) in `code/analysis/statistics.py`. **Dependency**: Requires completion of Phase 4 (Inference/Execution) to have pass/fail results. **Dependency: Phase 4 (T021, T024, T025)**.
- [ ] T035 [US3] Implement Mixed-Effects Logistic Regression with 'task' as random effect using `statsmodels` in `code/analysis/statistics.py`. **Deliverable**: Output variance component for 'task' to `data/processed/mixed_effects_results.json` for SC-007. **Verification**: Run `pytest tests/unit/test_mixed_effects.py` and assert pass; verify `variance_component` > 0.0 in output file. **Dependency**: Requires completion of Phase 4. **Dependency: Phase 4 (T021, T024, T025)**.
- [ ] T036 [US3] Implement sensitivity analysis on semantic thresholds across a representative set of high-confidence values as explicitly defined in FR-013 and SC-005 in `code/analysis/statistics.py`. **Logic**: Re-score the **raw** candidate pool (from T017 `data/processed/perturbation_candidates_raw.json`) against each threshold using `sentence-transformers/all-MiniLM-L6-v2` (same as T016); calculate pass@1 for the subset of candidates passing the threshold; log the sample count (N) at each threshold. **Threshold Set**: {0.85, 0.90, 0.95, 0.99} (as defined in FR-013/SC-005). **Pre-Check**: Verify `data/processed/perturbation_candidates_raw.json` exists. **Deliverable**: Generate `data/processed/sensitivity_report.csv` with columns: `threshold`, `pass_rate`, `delta_from_baseline`, `sample_count`. **Verification**: Run `python -c "import pandas as pd; import os; assert os.path.exists('data/processed/sensitivity_report.csv'); df=pd.read_csv('data/processed/sensitivity_report.csv'); assert 'threshold' in df.columns and 'sample_count' in df.columns and 'pass_rate' in df.columns; expected_thresholds = {0.85, 0.90, 0.95, 0.99}; assert set(df['threshold']).issubset(expected_thresholds); assert all(df['sample_count'] >= 0) and all(df['pass_rate'].apply(lambda x: isinstance(x, float) and x>=0 and x<=1))"` and assert success. **Dependency**: Requires completion of Phase 4 and raw candidate pool from T017 (specifically `data/processed/perturbation_candidates_raw.json`). **Traceability**: FR-013, SC-005.
- [ ] T037 [US3] Implement error classifier for stratified sampling (≤50 failures or a representative sample) in `code/analysis/error_classifier.py` using stratification by perturbation type and random seed=42. **Deliverable**: Output tags to `data/processed/error_classification_report.json` for consumption by T039. **Verification**: Run `python -c "import json; d=json.load(open('data/processed/error_classification_report.json')); assert len(d)<=50 and all('perturbation_type' in x for x in d)"` and assert reproducibility by re-running with seed=42 and diffing the output file. **Dependency**: Requires completion of Phase 4. **Dependency: Phase 4 (T021, T024, T025)**.
- [ ] T039 [US3] Generate final report aggregating pass@1 degradation, statistical significance, mixed-effects variance, sensitivity metrics, and error classification findings in `code/analysis/report_generator.py`. **Deliverable**: `docs/research_report.md`. **Verification**: Run `grep -E "(Pass@1|McNemar|Mixed-Effects|Sensitivity|Error Classification)" docs/research_report.md | wc -l` and assert count >= 5. **Dependency**: T034, T035, T036, T037. **Traceability**: Spec FR-001..FR-013.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T040a [P] Append metric definitions (pass@1, McNemar, Bonferroni) to `docs/metrics.md`. **Verification**: Run `grep -E "(Pass@1|McNemar)" docs/metrics.md | wc -l` and assert count >= 2.
- [ ] T040b [P] Verify documentation completeness in `docs/metrics.md`. **Verification**: Run `python -c "import os; assert os.path.exists('docs/metrics.md')"` and assert file is not empty.
- [ ] T041 [P] Run `ruff check --select F401 --fix` to remove unused imports across all modules. **Verification**: Run `ruff check --select F401` and assert exit code 0 (no errors).
- [ ] T042 [P] Refactor `code/model/inference.py` to use chunked loading to ensure CPU usage < 6GB per process and verify memory usage < 6GB using `psutil` as a fallback if `memory_profiler` is unavailable. **Verification**: Run `python -c "import psutil; p=psutil.Process(); print(f'Peak memory: {p.memory_info().rss / 1e9:.2f} GB'); assert p.memory_info().rss / 1e9 < 6"` and assert peak memory < 6GB in output log `data/logs/memory_profile.log`. **Traceability**: SC-004.
- [ ] T043 [P] Add unit tests for edge cases (timeout, OOM, empty dataset, zero-confidence) in `tests/unit/`.
- [ ] T044 [P] Security hardening for sandbox execution.
- [ ] T045 [P] Run `quickstart.md` validation.
- [ ] T046 [P] Implement pipeline runtime logger in `code/main.py` to record total execution time and assert it is < 6 hours (SC-003). **Verification**: Run pipeline and check `data/logs/runtime.log` for total time < A duration of approximately six hours will be employed.. **Traceability**: SC-003 (Per Plan.md SC-003 Resolution: corrected from -hour defect).

**Note**: The plan.md mentions missing numeric values for SC-003 (-hour limit) and SC-006 (sample size). This is flagged for kickback to the planning stage to document the justification for these assumptions.
**Note**: T017 and T018 logic clarified: T017 generates up to 3 candidates (log all), T016 validates, T018 filters.
**Note**: T001-T003: Status confirmed as COMPLETE.
**Note**: T034 verification logic updated to handle empty results or missing thresholds robustly (no hard-coded row counts).
**Note**: T016 [P] tag removed to enforce sequential dependency with T017.
**Note**: T001-T003 updated with specific paths and permissions.
**Note**: T016 updated to remove fallback logic and add halt condition with artifact (aligned to Spec Edge Cases).
**Note**: T004 updated with exact pinned versions.
**Note**: **NEW TASK T021**: Updated to use `bigcode/starcoder2-1.5b ` (Primary CPU run) and include confidence logging, with explicit Spec/Plan traceability. (Note: ECE removed, confidence logging removed to align with Spec).
**Note**: **NEW TASK T026**: Removed (ECE scope not authorized).
**Note**: **NEW TASK T038**: Removed (ECE scope not authorized).
**Note**: **NEW TASK T031**: Removed (ECE test not authorized).
**Note**: **NEW TASK T039**: Updated final report to exclude ECE findings.
**Note**: **NEW TASK T040**: Updated documentation to exclude ECE definitions.
**Note**: **Correction**: T021 updated to use `bigcode/starcoder2-1.5b ` and include Spec/Plan traceability.
**Note**: **Correction**: T034 updated to include `sample_count` column and strict threshold verification.
**Note**: **Correction**: T017 updated to persist full unfiltered list.
**Note**: **Correction**: T035 verification updated to check reproducibility with seed=42.
**Note**: **Correction**: T040 updated to use specific ruff command with verification.
**Note**: **Correction**: T045 added to verify runtime limit (SC-003) with Plan resolution traceability.
**Note**: **Removed**: Fallback threshold logic from T016/T017/T018 to enforce spec strictness.
**Note**: **CRITICAL FIX**: T034 verification logic updated to handle empty results or missing thresholds robustly (no hard-coded row counts).
**Note**: **CRITICAL FIX**: T016 [P] tag removed to enforce sequential dependency with T017.
**Note**: **CRITICAL FIX**: T037 removed from dependencies and task list.
**Note**: **CONSTITUTIONAL FIX**: T016, T017, T018 updated to define 'halt' as a reproducible outcome (exit code 1 + halt_report.json) to satisfy Constitution Principle I (adjusted to Spec Edge Cases: proceed with warning). (Note: Updated to strictly follow Spec Edge Cases: proceed with warning, no exit code 1).
**Note**: **LOGIC REORDER**: T017 (Generation) now precedes T016 (Validation) to resolve circular dependency. T017 generates raw data, T016 validates it.
**Note**: **SPEC CORRECTION**: FR-004 updated to mandate StarCoder2-1.5B (with Plan override for 3B). SC-003 corrected to 6-hour. FR-014 and SC-008 added for ECE (via Plan/Review). (Note: ECE removed; FR-004 restored to Spec priority with Plan fallback).
**Note**: **NEW TASK T011a**: Added to create contract schema for T011.
**Note**: **NEW TASK T009a**: Added to create schema validator utility for T018.
**Note**: **NEW TASK T011b**: Added to enforce model selection logic (1.5B vs 3B) per Plan override.
**Note**: **NEW TASK T042**: Merged T042a and T042b; updated verification to use `psutil`.
**Note**: **REVISION**: Removed all ECE-related tasks (T026, T031, T038, T039, T040a/b) as they were based on unauthorized scope.
**Note**: **REVISION**: Updated T016 to strictly follow Spec Edge Cases (proceed with warning, no exit code 1).
**Note**: **REVISION**: Updated T021 to explicitly reference Spec FR-004 and Plan override logic.
**Note**: **REVISION**: Corrected T011b verification typo.
**Note**: **REVISION**: Clarified T017 cap logic and sort key.
**Note**: **REVISION**: Removed [P] tag from T016 to reflect sequential dependency.
**Note**: **REVISION**: Removed [P] tag from T026 (deleted).
**Note**: **REVISION**: Updated T036 dependencies to remove unnecessary Phase 4 tasks.

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
 - **Specific Note**: T017 (Generation) must complete before T016 (Validation). T016 must complete before T018 (Filtering).
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on results from US1 and US2
 - **Specific Note**: T032, T033, T034, T035, T036, T037, T039 all depend on the completion of Phase 4 (Inference/Execution).
 - **Specific Note**: T036 (Sensitivity) and T037 (Error Classifier) are independent statistical tasks once Phase 4 is done.
 - **Specific Note**: T036 (Sensitivity) depends on T021 (Inference Log Generation) and T024/T025 (Error Tagging) only for the final report, but the calculation itself runs on the raw pool from T017.
 - **Specific Note**: T036 (Sensitivity) depends on T017 (Raw Pool) and bypasses T018 (Filtered Set).

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
- **Conditional Parallelism**: T032, T033, T035, T037 can run in parallel *after* Phase 4 (T021, T024, T025) is complete. T039 must be the final step in this chain. T036 (Sensitivity) is NOT [P] due to specific dependencies on T017/T016.

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
4. Add User Story 3 → Test independently → Deploy/Demo (Includes Sensitivity Metrics, Error Classification, Mixed-Effects Models)
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
- **Critical Constraint**: All model inference tasks (T021) MUST run on CPU with -bit quantization using `bigcode/starcoder2-1.5b ` (Plan fallback) if 3B exceeds limits; otherwise use `bigcode/starcoder2-3b` (Spec FR-004).
- **Critical Constraint**: All perturbation tasks (T013-T017) MUST use real HumanEval data; no synthetic/fake data generation.
- **Critical Constraint**: Semantic similarity threshold is strictly > 0.95 for primary set; **NO FALLBACK** allowed. Zero yield triggers a warning and proceeds with available data (Spec Edge Cases).
- **Critical Revision**: T017 and T018 logic clarified: T017 generates up to 3 candidates (log all), T016 validates, T018 filters.
- **Critical Revision**: T033 explicitly lists thresholds {0.90, 0.95, 0.99} and a lower boundary within the high-confidence range to match FR-013/SC-005.
- **Critical Revision**: T001-T003 updated with specific paths and permissions.
- **Critical Revision**: T039-T044 replaced vague polish tasks with specific, measurable actions.
- **Critical Revision**: T023 updated to explicitly bind the timeout to "per test case" as per FR-005 and US-2.
- **Critical Revision**: T006a and T006b (Schema validation) have been removed as they lack a direct spec anchor.
- **Critical Revision**: T001-T003 status updated to [X] as setup is complete (supersedes previous 'REJECTED' notes).
- **Critical Revision**: T016 updated to remove fallback logic and add halt condition with artifact (aligned to Spec Edge Cases: proceed with warning).
- **Critical Revision**: T004 updated with exact pinned versions.
- **Critical Revision**: T021 updated to use `bigcode/starcoder2-1.5b ` (fallback) and include Spec/Plan traceability.
- **Critical Revision**: T034 updated to include `sample_count` column and strict threshold verification.
- **Critical Revision**: T017 updated to persist full unfiltered list.
- **Critical Revision**: T035 verification updated for reproducibility.
- **Critical Revision**: T040 updated to use specific ruff command with verification.
- **Critical Revision**: T045 added for runtime verification with Plan resolution traceability.
- **Critical Revision**: T041 restored with specific memory profiling strategy and artifact.
- **Critical Revision**: T016 [P] tag removed to enforce sequential dependency.
- **Critical Revision**: T034 verification logic updated to handle empty results robustly.
- **Critical Revision**: T037 removed from task list and dependencies.
- **Critical Revision**: Removed all ECE-related tasks (T026, T031, T038, T039, T040a/b) as they were based on unauthorized scope.
- **Critical Revision**: Updated T016 to strictly follow Spec Edge Cases (proceed with warning, no exit code 1).
- **Critical Revision**: Updated T021 to explicitly reference Spec FR-004 and Plan override logic.
- **Critical Revision**: Corrected T011b verification typo.
- **Critical Revision**: Clarified T017 cap logic and sort key.
- **Critical Revision**: Removed [P] tag from T016 to reflect sequential dependency.
- **Critical Revision**: Removed [P] tag from T026 (deleted).
- **Critical Revision**: Updated T036 dependencies to remove unnecessary Phase 4 tasks.