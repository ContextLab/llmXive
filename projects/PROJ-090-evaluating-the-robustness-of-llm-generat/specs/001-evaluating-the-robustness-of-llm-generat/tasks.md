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
- [X] T004 [P] Create `requirements.txt` with pinned versions: `transformers==4.42.0`, `datasets==2.20.0`, `sentence-transformers==3.0.1`, `bitsandbytes==0.43.1`, `scikit-learn==1.5.0`, `statsmodels==0.14.2`, `pandas==2.2.2`, `pytest==8.2.2`, `numpy==1.26.4`.
- [X] T005 [P] Configure linting (ruff) and formatting (black) tools in `pyproject.toml` at the repository root with explicit settings: `line-length = 88`, `target-version = 'py311'`, `select = ['E', 'F', 'W', 'I']`. **Verification**: Run `ruff check --config pyproject.toml` and assert exit code 0; verify `black --check` passes.

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
- [X] T013 [P] [US1] Implement `substitute_synonyms()` function in `code/data/perturbations.py` for non-keyword token replacement.
- [X] T014 [P] [US1] Implement `inject_typos()` function in `code/data/perturbations.py` for random character typo injection.
- [X] T015 [P] [US1] Implement `rephrase_syntax()` function in `code/data/perturbations.py` for syntactic rephrasing.
- [ ] T017 [US1] Implement perturbation generation pipeline in `code/data/generate_perturbations.py` that generates **up to 3 candidates** (one per transformation type: synonym, typo, rephrase) per task. **Logic**: Iterate through transformation types; generate candidate; log raw score for EVERY candidate regardless of validity; continue to next type until 3 candidates are generated. **CRITICAL**: The system MUST persist the **full unfiltered** list of all generated candidates to `data/processed/perturbation_candidates_raw.json`. **Schema**: The JSON file MUST be a list of objects, where each object contains: `task_id` (str), `perturbation_type` (str: "synonym"|"typo"|"rephrase"), `raw_score` (float), `is_valid` (bool), `candidate_text` (str). **Verification**: Run `python -c "import json; d=json.load(open('data/processed/perturbation_candidates_raw.json')); from collections import Counter; counts=Counter(x['task_id'] for x in d); assert all(c==3 for c in counts.values())"` and assert success; verify file contains up to 3 items per task with raw scores. **Traceability**: Plan-driven budget cap; Spec-compliant raw logging. **Dependency**: T012, T013, T014, T015.
- [ ] T016 [US1] Implement semantic validation using `sentence-transformers/all-MiniLM-L6-v2` in `code/data/semantic_validator.py` to calculate cosine similarity. **STRICT CONSTRAINT**: Primary set retains only perturbations with score > 0.95 [FR-003]. **Logic**: Load `data/processed/perturbation_candidates_raw.json`; calculate similarity; update `is_valid` field; write to `data/processed/perturbation_candidates_validated.json`. **Halt Condition**: If the valid yield is < 1 (zero candidates) across the entire dataset, the system MUST log a critical error to `data/logs/halt_report.json` with reason "ZERO_YIELD" and exit with code 1. **Verification**: Run `python -c "import json; d=json.load(open('data/processed/perturbation_candidates_validated.json')); assert all('raw_score' in x for x in d)"` AND verify that if yield is zero, `data/logs/halt_report.json` exists and contains `{"reason": "ZERO_YIELD"}`. **Dependency**: T017.
- [ ] T018 [US1] Implement filtering logic in `code/data/filter_perturbations.py` to create the primary dataset `data/processed/perturbation_candidates.json` from the validated log. **Logic**: Retain ALL candidates with score > 0.95. **Halt Condition**: If the count of retained candidates is insufficient, the system MUST log a critical error to `data/logs/halt_report.json` with reason "ZERO_YIELD" and exit with code 1. **Traceability**: Cites FR-003 and FR-009. **Verification**: Run `python code/utils/validate_schema.py --input data/processed/perturbation_candidates.json` and assert success; verify file contains valid items per task with `raw_score > 0.95`. **Dependency**: T016 must complete before T018. <!-- ATOMIZE: requested -->

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - CPU-Compatible Model Inference and Execution (Priority: P2)

**Goal**: Execute StarCoder (quantized) on CPU, generate code, capture pass/fail results AND confidence metrics (token probabilities) for calibration analysis.

**Independent Test**: The pipeline can be tested by running inference on a single sample task and verifying the output code executes in the sandbox, returning a pass/fail status AND confidence metrics within the defined timeout, independent of statistical analysis.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [P] [US2] Unit test for sandbox timeout enforcement in `tests/unit/test_sandbox_timeout.py`: Verify `subprocess.run` raises TimeoutExpired after a specified timeout duration.
- [X] T020 [P] [US2] Mock test for model loading in `tests/unit/test_model_load.py`: Verify `bitsandbytes` low-bit quantization flag is set and CPU device is used.

### Implementation for User Story 2

- [ ] T021 [US2] Implement StarCoder loading with `bitsandbytes` low-bit quantization and CPU offload in `code/model/inference.py`. **Model ID**: Must use `bigcode/starcoder2-1.5b` (Primary CPU run per Plan.md Compute Feasibility Strategy). **Spec Compliance**: Spec FR-004 mandates StarCoder2-3B; Plan.md authorizes StarCoder2-1.5B for CPU with GPU fallback for 3B. **CRITICAL**: The inference engine MUST enforce the specified timeouts, capture **logits/token probabilities** for confidence calculation, and log execution status. **Schema**: Output `data/processed/inference_logs.json` MUST be a list of objects, where each object contains: `task_id` (str), `prompt` (str), `code` (str), `status` (str: "pass"|"fail"|"timeout"|"oom"), `confidence_score` (float 0.0-1.0). **Verification**: Run `python -c "import json; d=json.load(open('data/processed/inference_logs.json')); assert 'code' in d[0] and 'status' in d[0] and 'confidence_score' in d[0]"` and assert success. **Dependency**: T018. **Traceability**: FR-004 (Plan Override), Plan.md Compute Feasibility.
- [X] T023 [US2] Integrate sandbox executor to run generated code with a **Fixed timeout per test case** in `code/model/sandbox.py`. **Note**: This explicitly implements the requirement from FR-005 and US-2 Acceptance Scenario 2.
- [X] T024 [US2] Implement raw error tagging logic (syntax, timeout, OOM, pass, fail) in `code/model/execution_results.py`.
- [X] T025 [US2] Add OOM handling to skip sample and log "OOM" flag in `code/model/inference.py`.
- [ ] T026 [US2] Implement confidence extraction logic in `code/model/confidence_metrics.py` to compute **Expected Calibration Error (ECE)** bins and per-sample confidence scores from model logits. **Rationale**: Addresses "Daniel Kahneman" review concern regarding overconfidence bias; measures if model confidence tracks accuracy under perturbation. **Deliverable**: Append `confidence_score` (float 0.0-1.0) and `ece_bin` to `data/processed/inference_logs.json`. **Verification**: Run `python -c "import json; d=json.load(open('data/processed/inference_logs.json')); assert all('confidence_score' in x for x in d)"` and verify values are in [0,1]. **Dependency**: T021. **Traceability**: Plan.md Scope Boundary (ECE as critical extension per Daniel Kahneman review), Prior Review: Daniel Kahneman.
- [X] T031 [US3] Create unit test for ECE calculation in `tests/unit/test_ece.py`: Verify binning logic and ECE score calculation against known synthetic data (perfectly calibrated vs. overconfident). **Dependency**: Required for T038 verification. **Traceability**: Plan.md Scope Boundary (ECE as critical extension per Daniel Kahneman review), Prior Review: Daniel Kahneman.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis, Multiplicity Correction, and Error Classification (Priority: P3)

**Goal**: Calculate pass@1 rates, apply McNemar's test with Bonferroni correction, perform Mixed-Effects Logistic Regression, analyze sensitivity to semantic thresholds, classify errors, AND analyze calibration (ECE) across perturbation types.

**Independent Test**: The pipeline can be tested by feeding a mock CSV of pass/fail results, confidence scores, and threshold metadata into the analysis script and verifying the statistical output (p-values, corrected alpha, mixed-effects coefficients, sensitivity report, ECE metrics) matches expected calculations.

**Scope Boundary**: The study is strictly limited to FR-001 through FR-013. ECE and confidence logging are now **included** as a critical extension to address the "overconfidence bias" concern raised by the simulated Daniel Kahneman review, ensuring the model is treated as a system operating under uncertainty.

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
- [ ] T036 [US3] Implement sensitivity analysis on semantic thresholds across a representative set of high-confidence values. as explicitly defined in FR-013 (replacing vague FR-009 high-confidence values) and SC-005 in `code/analysis/statistics.py`. **Logic**: Re-score the **raw** candidate pool (from T017) against each threshold using `sentence-transformers/all-MiniLM-L6-v2` (same as T016); calculate pass@1 for the subset of candidates passing the threshold; log the sample count (N) at each threshold. **Deliverable**: Generate `data/processed/sensitivity_report.csv` with columns: `threshold`, `pass_rate`, `delta_from_baseline`, `sample_count`. **Verification**: Run `python -c "import pandas as pd; import os; assert os.path.exists('data/processed/sensitivity_report.csv'); df=pd.read_csv('data/processed/sensitivity_report.csv'); assert 'threshold' in df.columns and 'sample_count' in df.columns and 'pass_rate' in df.columns; expected_thresholds = {0.85, 0.90, 0.95, 0.99}; assert set(df['threshold']).issubset(expected_thresholds); assert all(df['sample_count'] >= 0) and all(df['pass_rate'].apply(lambda x: isinstance(x, float) and x>=0 and x<=1))"` and assert success. **Dependency**: Requires completion of Phase 4 and raw candidate pool from T017 (specifically `data/processed/perturbation_candidates_raw.json`). **Dependency: Phase 4 (T021, T024, T025), T017, T018**. **Traceability**: FR-013, SC-005.
- [ ] T037 [US3] Implement error classifier for stratified sampling (≤50 failures or sample of 50) in `code/analysis/error_classifier.py` using stratification by perturbation type and random seed=42. **Deliverable**: Output tags to `data/processed/error_classification_report.json` for consumption by T038. **Verification**: Run `python -c "import json; d=json.load(open('data/processed/error_classification_report.json')); assert len(d)<=50 and all('perturbation_type' in x for x in d)"` and assert reproducibility by re-running with seed=42 and diffing the output file. **Dependency**: Requires completion of Phase 4. **Dependency: Phase 4 (T021, T024, T025)**.
- [ ] T038 [US3] Implement **Expected Calibration Error (ECE)** analysis across perturbation types in `code/analysis/calibration.py`. **Rationale**: Directly addresses the "Daniel Kahneman" review concern regarding overconfidence bias. Measures the gap between model confidence (token probabilities) and actual accuracy (pass/fail) for original vs. perturbed prompts. **Logic**: Bin samples by confidence (e.g., 10 bins), calculate average confidence and accuracy per bin, compute weighted average absolute difference. **Deliverable**: Generate `data/processed/calibration_report.json` containing ECE scores per perturbation type and per-bin data. **Verification**: Run `python -c "import json; d=json.load(open('data/processed/calibration_report.json')); assert 'ece_by_type' in d and 'bins' in d; assert all(isinstance(v, float) for v in d['ece_by_type'].values())"` and verify ECE > 0 for overconfident cases. **Dependency**: Requires completion of Phase 4 (T026 for confidence scores). **Traceability**: Plan.md Scope Boundary (ECE as critical extension per Daniel Kahneman review), Prior Review: Daniel Kahneman.
- [ ] T039 [US3] Generate final report aggregating pass@1 degradation, statistical significance, mixed-effects variance, sensitivity metrics, error classification findings, AND **calibration metrics (ECE)** in `code/analysis/report_generator.py`. **Deliverable**: `docs/research_report.md`. **Verification**: Run `grep -E "(Pass@1|McNemar|Mixed-Effects|Sensitivity|Error Classification|Expected Calibration Error)" docs/research_report.md | wc -l` and assert count >= 6. **Dependency**: T034, T035, T036, T037, T038. **Traceability**: Plan.md Scope Boundary (ECE as critical extension per Daniel Kahneman review), Prior Review: Daniel Kahneman.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T040a [P] Append metric definitions (pass@1, McNemar, Bonferroni, ECE) to `docs/metrics.md`. **Verification**: Run `grep -E "(Expected Calibration Error|Pass@1|McNemar)" docs/metrics.md | wc -l` and assert count >= 4.
- [ ] T040b [P] Verify documentation completeness in `docs/metrics.md`. **Verification**: Run `python -c "import os; assert os.path.exists('docs/metrics.md')"` and assert file is not empty.
- [ ] T041 [P] Run `ruff check --select F401 --fix` to remove unused imports across all modules. **Verification**: Run `ruff check --select F401` and assert exit code 0 (no errors).
- [ ] T042a [P] Refactor `code/model/inference.py` to use chunked loading to ensure CPU usage < 6GB per process. **Verification**: Run `python -m memory_profiler code/model/inference.py` and assert peak memory < 6GB in output log `data/logs/memory_profile.log`.
- [ ] T042b [P] Generate `data/logs/memory_profile.log` with peak memory < 6GB. **Verification**: Run `python -c "import re; log=open('data/logs/memory_profile.log').read(); assert '6GB' in log or 'peak < 6GB' in log"` (or check specific numeric value).
- [ ] T043 [P] Add unit tests for edge cases (timeout, OOM, empty dataset, zero-confidence) in `tests/unit/`.
- [ ] T044 [P] Security hardening for sandbox execution.
- [ ] T045 [P] Run `quickstart.md` validation.
- [ ] T046 [P] Implement pipeline runtime logger in `code/main.py` to record total execution time and assert it is < 6 hours (SC-003). **Verification**: Run pipeline and check `data/logs/runtime.log` for total time < seconds. **Traceability**: SC-003 (Per Plan.md SC-003 Resolution: corrected from -hour defect).

**Note**: The plan.md mentions missing numeric values for SC-003 (-hour limit) and SC-006 (sample size). This is flagged for kickback to the planning stage to document the justification for these assumptions.
**Note**: T017 and T018 logic clarified: T017 generates up to 3 candidates (log all), T016 validates, T018 filters.
**Note**: T001-T003: Status confirmed as COMPLETE.
**Note**: T034 verification logic updated to handle empty results or missing thresholds robustly (no hard-coded row counts).
**Note**: T016 [P] tag removed to enforce sequential dependency with T017.
**Note**: T001-T003 updated with specific paths and permissions.
**Note**: T016 updated to remove fallback logic and add halt condition with artifact.
**Note**: T004 updated with exact pinned versions.
**Note**: **NEW TASK T021**: Updated to use `bigcode/starcoder2-1.5b` (Primary CPU run) and include confidence logging, with explicit Spec/Plan traceability.
**Note**: **NEW TASK T026**: Added to extract confidence scores from logits for ECE analysis (Kahneman Review), with explicit Plan/Review traceability.
**Note**: **NEW TASK T038**: Added to implement ECE analysis (Kahneman Review), with explicit Plan/Review traceability.
**Note**: **NEW TASK T031**: Added unit test for ECE, with explicit Plan/Review traceability.
**Note**: **NEW TASK T039**: Updated final report to include ECE findings, with explicit Plan/Review traceability.
**Note**: **NEW TASK T040**: Updated documentation to include ECE definitions.
**Note**: **Correction**: T021 updated to use `bigcode/starcoder2-1.5b` and include Spec/Plan traceability.
**Note**: **Correction**: T034 updated to include `sample_count` column and strict threshold verification.
**Note**: **Correction**: T017 updated to persist full unfiltered list.
**Note**: **Correction**: T035 verification updated to check reproducibility with seed=42.
**Note**: **Correction**: T040 updated to use specific ruff command with verification.
**Note**: **Correction**: T045 added to verify runtime limit (SC-003) with Plan resolution traceability.
**Note**: **Removed**: Fallback threshold logic from T016/T017/T018 to enforce spec strictness.
**Note**: **CRITICAL FIX**: T034 verification logic updated to handle empty results or missing thresholds robustly (no hard-coded row counts).
**Note**: **CRITICAL FIX**: T016 [P] tag removed to enforce sequential dependency with T017.
**Note**: **CRITICAL FIX**: T037 removed from dependencies and task list.
**Note**: **REVISION (Research Review - Kahneman)**: Added T026, T031, T038, T039 to address "overconfidence bias" and include Expected Calibration Error (ECE) as a primary metric, with explicit Plan/Review traceability.
**Note**: **CONSTITUTIONAL FIX**: T016, T017, T018 updated to define 'halt' as a reproducible outcome (exit code 1 + halt_report.json) to satisfy Constitution Principle I.
**Note**: **LOGIC REORDER**: T017 (Generation) now precedes T016 (Validation) to resolve circular dependency. T017 generates raw data, T016 validates it.
**Note**: **SPEC CORRECTION**: FR-004 updated to mandate StarCoder2-1.5B (with Plan override for 3B). SC-003 corrected to 6-hour. FR-014 and SC-008 added for ECE (via Plan/Review).

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
 - **Specific Note**: T026 (Confidence) depends on T021 (Inference).
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on results from US1 and US2
 - **Specific Note**: T032, T033, T034, T035, T036, T037, T038, T039 all depend on the completion of Phase 4 (Inference/Execution).
 - **Specific Note**: T034 (Sensitivity) and T035 (Error Classifier) are independent statistical tasks once Phase 4 is done.
 - **Specific Note**: T034 (Sensitivity) and T035 (Error Classifier) depend on T021 (Inference Log Generation) and T024/T025 (Error Tagging).
 - **Specific Note**: T038 (ECE) depends on T026 (Confidence Extraction).

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
- **Conditional Parallelism**: T032, T033, T035, T037 can run in parallel *after* Phase 4 (T021, T024, T025, T026) is complete. T039 must be the final step in this chain. T036 (Sensitivity) and T038 (ECE) are NOT [P] due to specific dependencies on T017/T021 and T026 respectively. T038 is excluded from the parallel group due to its strict dependency on T026.

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
3. Add User Story 2 → Test independently → Deploy/Demo (Includes CPU Inference + Confidence Metrics)
4. Add User Story 3 → Test independently → Deploy/Demo (Includes Sensitivity Metrics, Error Classification, Mixed-Effects Models, ECE Calibration Analysis)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1
 - Developer B: User Story 2 (Focus on CPU Inference + Confidence Extraction)
 - Developer C: User Story 3 (Focus on Sensitivity Metrics, Error Classification, Mixed-Effects Models, ECE Analysis)
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
- **Critical Constraint**: All model inference tasks (T021-T026) MUST run on CPU with 4-bit quantization using `bigcode/starcoder2-1.5b` (per Plan override); no CUDA dependencies allowed for primary run.
- **Critical Constraint**: All perturbation tasks (T013-T017) MUST use real HumanEval data; no synthetic/fake data generation.
- **Critical Constraint**: Semantic similarity threshold is strictly > 0.95 for primary set; **NO FALLBACK** allowed. Zero yield triggers a critical halt with artifact generation.
- **Critical Revision**: T017 and T018 logic clarified: T017 generates up to 3 candidates (log all), T016 validates, T018 filters.
- **Critical Revision**: T033 explicitly lists thresholds {0.85, 0.90, 0.95, 0.99} to match FR-013/SC-005.
- **Critical Revision**: T001-T003 updated with specific paths and permissions.
- **Critical Revision**: T039-T044 replaced vague polish tasks with specific, measurable actions.
- **Critical Revision**: T023 updated to explicitly bind the timeout to "per test case" as per FR-005 and US-2.
- **Critical Revision**: T006a and T006b (Schema validation) have been removed as they lack a direct spec anchor.
- **Critical Revision**: T001-T003 status updated to [X] as setup is complete (supersedes previous 'REJECTED' notes).
- **Critical Revision**: T016 updated to remove fallback logic and add halt condition with artifact.
- **Critical Revision**: T004 updated with exact pinned versions.
- **Critical Revision**: T021 updated to use `bigcode/starcoder2-1.5b` and include confidence logging, with Spec/Plan traceability.
- **Critical Revision**: T034 updated to include `sample_count` column and strict threshold verification.
- **Critical Revision**: T017 updated to persist full unfiltered list.
- **Critical Revision**: T035 verification updated for reproducibility.
- **Critical Revision**: T040 updated to use specific ruff command with verification.
- **Critical Revision**: T045 added for runtime verification with Plan resolution traceability.
- **Critical Revision**: T041 restored with specific memory profiling strategy and artifact.
- **Critical Revision**: T037 (ECE) and T027b (ECE test) removed as unapproved scope creep.
- **Critical Revision**: T016 [P] tag removed to enforce sequential dependency.
- **Critical Revision**: T034 verification logic updated to handle empty results robustly.
- **Critical Revision**: T037 removed from task list and dependencies.
- **REVISION (Research Review - Kahneman)**: Added T026, T031, T038, T039 to address "overconfidence bias" and include Expected Calibration Error (ECE) as a primary metric, with explicit Plan/Review traceability.
- **CONSTITUTIONAL FIX**: T016, T017, T018 updated to define 'halt' as a reproducible outcome (exit code 1 + halt_report.json) to satisfy Constitution Principle I.
- **LOGIC REORDER**: T017 (Generation) now precedes T016 (Validation) to resolve circular dependency. T017 generates raw data, T016 validates it.
- **SPEC CORRECTION**: FR-004 updated to mandate StarCoder2-1.5B (with Plan override for 3B). SC-003 corrected to 6-hour. FR-014 and SC-008 added for ECE (via Plan/Review).