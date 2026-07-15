# Tasks: Evaluating the Impact of Code Generation Models on Code Testability

**Input**: Design documents from `/specs/001-evaluating-the-impact-of-code-generation/`
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

- [X] T001 Create project structure per implementation plan (`projects/PROJ-294-evaluating-the-impact-of-code-generation/`)
- [X] T002 Initialize a Python project with pinned dependencies in `code/requirements.txt`
- [X] T003 [P] Configure linting (flake8/black) and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup logging infrastructure in `code/utils.py` with timestamp and task ID tracking (FR-007)
- [X] T005 Implement SHA256 checksum utility in `code/utils.py` for dataset and artifact verification (FR-001, FR-011)
- [X] T006 Create `state/artifact_hashes.yaml` structure and update logic (FR-011)
- [ ] T007 [P] Implement Reference-Validator Agent wrapper in `code/validate_citations.py` (FR-010). **BLOCKING**: Must complete before T010 starts.
- [ ] T008 Create data directory structure: `data/raw/`, `data/generated/`, `data/analysis/`
- [ ] T009 Create results directory structure: `results/figures/`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Paired Analysis Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download HumanEval, generate LLM code, compute metrics (Complexity, Halstead, Coverage), and produce paired JSON dataset.

**Independent Test**: Run the pipeline on a local copy of HumanEval. Verify that `data/analysis/metrics.json` contains `cyclomatic_complexity`, `halstead_volume`, `branch_coverage_pct`, and `pass_rate` for every valid pair, with at least 40 valid samples.

### Implementation for User Story 1

- [X] T010 [US1] Implement `code/download_data.py` to download HumanEval from HuggingFace, verify SHA256, and save to `data/raw/` (FR-001)
- [X] T011 [US1] Implement stratified sampling logic in `code/download_data.py` to select a representative subset of tasks based on human pass-rate quartiles (Plan: Sampling Strategy). **Includes assertion**: Verify the final selected subset size is exactly 50 to satisfy FR-001 count constraint.
- [X] T012 [US1] Implement `code/generate_code.py` to load `Salesforce/codegen-mono` on CPU and generate code for a set of tasks with 3-retry logic (FR-002)
- [X] T013 [US1] Implement error handling in `code/generate_code.py` to log failures to `errors.log` and mark samples as missing (Edge Cases)
- [X] T014 [US1] Implement `code/analyze_metrics.py` to run `radon` for cyclomatic complexity and Halstead volume on all samples (FR-003)
- [X] T015 [US1] Implement logic in `code/analyze_metrics.py` to execute `pytest` against the HumanEval test suite for each sample and record the binary `pass_rate` (1 = all tests passed, 0 = any failure) as per FR-005.
- [X] T042 [US1] Implement logic in `code/analyze_metrics.py` to run `pytest --cov` for `branch_coverage_pct`, recording `[deferred]` if execution fails while still recording the `pass_rate` (FR-003, Edge Cases)
- [X] T016 [US1] Implement logic in `code/analyze_metrics.py` to handle execution failures (record `[deferred]` for coverage) (Edge Cases)
- [~] T017 [US1] Implement aggregation in `code/analyze_metrics.py` to produce `data/analysis/metrics.json` with all required fields (US-1 Independent Test)

**Sensitivity Analysis Sub-Phase (within US1)**

- [X] T028a [US3] **Prerequisite**: Attempt to load `CodeLlama-3B` locally on CPU with 4-bit quantization in `code/generate_code.py` to prepare for fallback. If loading fails (RAM constraint), log error and mark local fallback as unavailable. (FR-009)
- [X] T028 [US3] Implement sensitivity analysis logic in `code/generate_code.py` to call HuggingFace Inference API for `CodeLlama-7B` for a subset of tasks. **Trigger**: Run only if API is available. (FR-009)
- [X] T029 [US3] Implement fallback logic in `code/generate_code.py`: If `CodeLlama-7B` local 4-bit quantization fails (if attempted) OR if API is unavailable, use the locally loaded `CodeLlama-3B` (from T028a) for generation. If T028a failed, skip sensitivity generation for this path. (FR-009)
- [ ] T041 [US1] **Dependency**: Must run after T028/T029. Re-run analysis (T014/T042 logic) on sensitivity samples generated by T028/T029 and **merge** results into `data/analysis/metrics.json` using unique keys to ensure a unified Single Source of Truth before statistical testing. (FR-009, Plan: Data Model Traceability)

- [X] T018 [US1] Write unit tests for `code/download_data.py` to verify checksum logic and sampling distribution (tests/unit/test_download.py)
- [X] T019 [US1] Write integration test for `code/analyze_metrics.py` to verify metric extraction on a known Python snippet (tests/integration/test_metrics.py)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (including sensitivity data merged into metrics.json)

---

## Phase 4: User Story 2 - Statistical Comparison and Hypothesis Testing (Priority: P2)

**Goal**: Perform Wilcoxon, McNemar, Fisher, and Permutation tests, and Power Analysis (A Priori/Post-Hoc) on the paired dataset.

**Independent Test**: Feed mock paired datasets; verify p-values are calculated correctly and power analysis reports required n ≥ 38 and achieved power ≥ 0.8.

### Implementation for User Story 2

- [X] T020 [US2] Implement `code/statistical_tests.py` with Wilcoxon Signed-Rank test for continuous metrics: **Cyclomatic Complexity, Halstead Volume, AND Branch Coverage** (FR-004, US-2)
- [X] T021 [US2] Implement `code/statistical_tests.py` with McNemar's test for binary pass-rate (FR-004)
- [X] T022 [US2] Implement `code/statistical_tests.py` with Fisher's Exact Test for **unpaired exploratory checks ONLY** (FR-004)
- [X] T040 [US2] Implement `code/statistical_tests.py` with Permutation Test specifically for paired branch coverage data (Plan: Complexity Tracking)
- [X] T023 [US2] Implement A Priori Power Analysis in `code/statistical_tests.py` (d=0.5, α=0.05, power≥0.8) to validate sample size (FR-008)
- [X] T024 [US2] Implement Post-Hoc Power Analysis in `code/statistical_tests.py` based on observed effect sizes (FR-008)
- [X] T025 [US2] Implement Spearman's rank correlation coefficient test in `code/statistical_tests.py` to explicitly test independence of structural complexity from functional success. **Specific Handling**: Use Point-Biserial correlation for the binary `pass_rate` component of functional success and Spearman for continuous metrics; output correlation coefficients and p-values for both. (FR-004)
- [X] T026 [US2] Write unit tests for statistical functions using mock data with known p-values (tests/unit/test_statistics.py)
- [X] T027 [US2] Write integration test verifying the full statistical report generation from `metrics.json` (tests/integration/test_stats_pipeline.py)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualization, Reporting, and Sensitivity Analysis (Priority: P3)

**Goal**: Generate automated Markdown report with figures, and perform sensitivity analysis using CodeLlama models.

**Independent Test**: Verify `results_report.md` contains all figures, tables, and sensitivity analysis results; verify API fallback logic works.

### Implementation for User Story 3

- [ ] T030 [US3] Implement `code/report_generator.py` to create histograms and boxplots using `matplotlib` for all continuous metrics (US-3)
- [ ] T031 [US3] Implement `code/report_generator.py` with Jinja2 template to compile `results_report.md` including figures, tables, and power analysis (FR-006)
- [ ] T032 [US3] Implement logic to include sensitivity analysis comparison (7B/3B vs 350M) in the final report (FR-009)
- [ ] T033 [US3] Write unit tests for `code/report_generator.py` to verify figure generation and template rendering (tests/unit/test_report.py)
- [ ] T034 [US3] Write integration test for the full pipeline from `metrics.json` to `results_report.md` (tests/integration/test_full_pipeline.py)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T035 [P] Documentation updates in `docs/` and `README.md`
- [ ] T036 Code cleanup and refactoring of `code/utils.py`
- [ ] T037 Performance optimization for `code/analyze_metrics.py` (parallel processing if safe)
- [ ] T038 [P] Additional unit tests for edge cases (e.g., 0 coverage, missing LLM samples) in `tests/unit/`
- [ ] T039 Run quickstart.md validation to ensure end-to-end reproducibility

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **Phase 3 (US1)**: **Depends on Phase 2 (Foundational) completion**. T007 must complete before T010 starts. **Includes T041** which must complete before Phase 4 starts.
- **Phase 4 (US2)**: **Depends on Phase 3 (US1) completion** (requires `metrics.json` from T017 and T041).
- **Phase 5 (US3)**: **Depends on Phase 4 (US2) completion** and **T041 completion** (requires statistical results and sensitivity analysis data).
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories. Includes sensitivity generation and analysis (T028a, T028, T029, T041).
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output (`metrics.json` including sensitivity data).
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 data, US2 results, and T041 for report generation.

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
Task: "Contract test for [endpoint] in tests/contract/test_[name].py"
Task: "Integration test for [user journey] in tests/integration/test_[name].py"

# Launch all models for User Story 1 together:
Task: "Create [Entity1] model in src/models/[entity1].py"
Task: "Create [Entity2] model in src/models/[entity2].py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (including T041 for sensitivity data merge)
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1
 - Developer B: User Story 2
 - Developer C: User Story 3
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