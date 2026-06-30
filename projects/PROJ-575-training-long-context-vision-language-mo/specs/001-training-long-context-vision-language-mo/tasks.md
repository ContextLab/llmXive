# Tasks: Reproduce & Validate Long-Context VLM Training with MMLongBench

**Input**: Design documents from `/specs/575-reproduce-long-context-vlm/`
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

- [X] T001 Create project structure: `mkdir -p src/eval src/contracts tests/contract tests/integration tests/unit data/raw data/processed results docs`
- [X] T002 Initialize Python 3.11 project: Create `pyproject.toml` and `requirements.txt` with pinned versions for `torch`, `transformers`, `datasets`, `pandas`, `scikit-learn`
- [X] T003 [P] Configure linting and formatting: Create `.ruff.toml` and `.black.toml` configuration files

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup data directory structure: Create `data/raw`, `data/processed` directories and add `*.parquet`, `models/*`, `results/*` to `.gitignore`
- [X] T005 [P] Implement memory monitoring: Create `src/eval/memory_utils.py` with functions to monitor RAM usage and detect OOM conditions
- [X] T006 [P] Implement error handling: Create `src/eval/error_utils.py` with functions for graceful failure on missing data and hardware mismatches
- [X] T007 Create base data schemas: Create `contracts/evaluation_run.schema.yaml` and `contracts/benchmark_result.schema.yaml` defining JSON schemas
- [X] T008 Configure environment management: Create `src/eval/config.py` with a `Config` class loading `HF_TOKEN` and `DATA_PATH` from `os.environ`
- [X] T011 [P] [US1] Implement data download: Create `src/eval/download_data.py` using `datasets.load_dataset("yubo2333/MMLongBench-Doc", split="test")` and save to `data/raw/`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Execute MMLongBench Evaluation Pipeline on CPU (Priority: P1) 🎯 MVP

**Goal**: Run the vendored evaluation scripts on a standard GitHub Actions free-tier runner with a limited CPU configuration to generate valid artifacts without crashing.

**Independent Test**: Run `src/eval/run_cpu_eval.py` with `--sample-size 10` and verify exit code 0 and output file existence.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T009 [P] [US1] Contract test for `EvaluationRun` schema validation in `tests/contract/test_evaluation_run.py`
- [X] T010 [P] [US1] Integration test for CPU-only execution flow in `tests/integration/test_cpu_smoke.py`

### Implementation for User Story 1

- [X] T012 [US1] Implement `run_cpu_eval.py` entry point with `--sample-size` argument parsing in `src/eval/run_cpu_eval.py`
- [X] T013 [US1] Implement CPU-optimized model loading: **MUST use 4-bit quantization via `transformers`** (override Spec FR-008 float16 mandate due to 7GB RAM constraint) in `src/eval/run_cpu_eval.py`
- [X] T014 [US1] Implement data validation check to fail fast if required fields (`context_length`, `task_type`, `question`, `answer`) are missing in `src/eval/run_cpu_eval.py`
- [X] T015 [US1] Implement memory usage monitoring and OOM graceful failure handling; **FAIL immediately if float16 loading is attempted** in `src/eval/run_cpu_eval.py`
- [X] T016 [US1] Modify `src/eval/run_cpu_eval.py` to write output to `results/sample_results.json` with columns `[context_length, task_type, model_baseline_score, model_target_score]`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Validate Reproduction of Paper's Key Findings (Priority: P2)

**Goal**: Compare generated evaluation metrics against paper claims (e.g., long-document VQA improvement, generalization beyond 128K) to confirm reproduction validity.

**Independent Test**: Run evaluation on "long-document VQA" and compute delta; verify performance at 256K/512K is ≥80% of 128K performance.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T017 [P] [US2] Unit test for percentage improvement calculation logic in `tests/unit/test_metric_validation.py`
- [X] T018 [P] [US2] Integration test for generalization retention rate check in `tests/integration/test_generalization_validation.py`

### Implementation for User Story 2

- [X] T019 [US2] Implement `validate_results.py` script to load `sample_results.json` and paper claims in `src/eval/validate_results.py` (Depends on T016)
- [X] T020 [US2] Implement logic to load target improvement value from config/research doc (default to '[deferred]' if missing) and calculate percentage improvement for "long-document VQA" in `src/eval/validate_results.py`
- [X] T021 [US2] Implement logic to calculate performance retention rate at 256K and 512K contexts relative to 128K in `src/eval/validate_results.py`
- [X] T022 [US2] Generate `results/validation_report.md` explicitly stating whether reproduction claims are met or failed in `src/eval/validate_results.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Analyze Scaling and Multiplicity of Results (Priority: P3)

**Goal**: Generate a summary report addressing scaling laws (Geoffrey West review) by aggregating results across context lengths and applying descriptive trend analysis.

**Independent Test**: Execute batch evaluation across multiple context lengths (32K-512K), fit regression, and output slope/trend classification.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T023 [P] [US3] Unit test for log-log regression fitting logic in `tests/unit/test_scaling_analysis.py`
- [X] T024 [P] [US3] Contract test for `ScalingAnalysis` output schema in `tests/contract/test_scaling_analysis.py`

### Implementation for User Story 3

- [X] T025 [US3] Implement `scaling_analysis.py` to load results across multiple distinct context lengths in `src/eval/scaling_analysis.py` (Depends on T016)
- [X] T026 [US3] Implement linear regression of `score` vs `log(context_length)` to calculate slope coefficient and R² in `src/eval/scaling_analysis.py`
- [X] T027 [US3] Implement logic to classify trend as "linear," "sublinear," or "superlinear" based on slope magnitude in `src/eval/scaling_analysis.py`
- [X] T028 [US3] Implement logic to append a "Limitations" section to `results/scaling_report.json` explicitly stating "Multiple-comparison correction was NOT applied due to insufficient statistical power (n=10)" in `src/eval/scaling_analysis.py`
- [X] T029 [US3] Generate `results/scaling_report.json` containing slope, R², trend classification, and statistical power disclaimer in `src/eval/scaling_analysis.py`
- [X] T030 [US3] Update `src/eval/report_generator.py` to include the `scaling_report.json` findings in the final `results/final_report.md` (Depends on T022 and T029)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [X] T031a [P] Update `README.md` with installation steps and usage examples
- [X] T031b [P] Add docstrings to all modules in `src/eval/`
- [X] T032a Refactor `run_cpu_eval.py` for modularity and separation of concerns
- [X] T032b Remove dead code and unused imports in `src/eval/utils.py`
- [X] T036 Commit implementation code for `src/eval/run_cpu_eval.py`, `src/eval/scaling_analysis.py`, and `src/eval/utils.py` to the repository, ensuring alignment with tasks.md logic and execution evidence artifacts.
- [X] T033a Optimize data loading in `download_data.py` with batch size metric (target < 5s for sample)
- [X] T033b Profile model loading time and document results
- [X] T034a Unit test for OOM handling in `tests/unit/test_memory_utils.py`
- [X] T034b Unit test for missing data handling in `tests/unit/test_error_utils.py`
- [X] T035a Execute `quickstart.md` steps and verify exit code 0
- [X] T035b Create CI script `.github/workflows/quickstart.yml` for validation

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on T016 (Data Generation)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on T016 (Data Generation)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] (T005, T006, T007, T008, T011) can run in parallel
- Once Foundational phase completes, T012 (US1) can start
- **CRITICAL**: T016 (US1) must complete before T019 (US2) and T025 (US3) can start
- Once T016 is done, T019 and T025 can run in parallel
- T030 (Final Report) must wait for both T022 and T029 to complete

### Verification Checklist

- [X] Verify all tasks respect data flow (e.g., data download before evaluation, evaluation before analysis)
- [X] Verify T013 enforces 4-bit quantization and fails on float16
- [X] Verify T020 loads target values dynamically and handles '[deferred]'
- [X] Verify T028 explicitly states correction was NOT applied

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Constraint**: All model loading MUST use 4-bit quantization to fit within 7GB RAM; float16 is disallowed (overrides Spec FR-008).
- **Critical Constraint**: No GPU usage; all execution must be CPU-only.
- **Critical Constraint**: Dataset must be downloaded via verified source (`yubo2333/MMLongBench-Doc`) before evaluation.
- **Critical Constraint**: Scaling analysis must explicitly state statistical limitations due to small sample size (n=10).