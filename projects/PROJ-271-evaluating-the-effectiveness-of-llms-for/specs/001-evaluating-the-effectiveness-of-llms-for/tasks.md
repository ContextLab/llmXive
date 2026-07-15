# Tasks: Evaluating the Effectiveness of LLMs for Detecting Code Smells

**Input**: Design documents from `/specs/001-evaluating-the-effectiveness-of-llms-for/`
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

- [ ] T001a [P] Create `projects/PROJ-271-evaluating-the-effectiveness-of-llms-for/code/` directory
- [ ] T001b [P] Create `projects/PROJ-271-evaluating-the-effectiveness-of-llms-for/data/raw/`, `data/processed/`, and `results/` directories
- [ ] T001c [P] Create `projects/PROJ-271-evaluating-the-effectiveness-of-llms-for/tests/unit/` and `tests/contract/` directories
- [ ] T002 [P] Initialize Python 3.11 project with `requirements.txt` containing `datasets`, `pandas`, `radon`, `pylint`, `sentence-transformers`, `llama-cpp-python`, `scikit-learn`, `statsmodels`, `numpy`, `psutil`
- [ ] T003 [P] Configure linting (flake8/black) and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Create `code/config.py` defining paths (`data/`, `results/`), random seeds, and batch size constants (LLM batch ≤ 10)
- [ ] T005 [P] Implement `code/__init__.py` and ensure directory structure matches `data/raw`, `data/processed`, `results`
- [X] T006a [P] Setup logging configuration in `code/config.py` to define log format, file handlers, and levels for metrics (FR-008)
- [X] T006b [P] Implement `code/monitoring.py` to capture RAM usage, CPU utilization, and inference time using `psutil` for use in inference loops (FR-008)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Automated Data Pipeline and Static Analysis Baseline (Priority: P1) 🎯 MVP

**Goal**: Ingest a sampled subset of `codeparrot/github-code`, compute structural metrics via `radon`, and generate a baseline "smell label" set using Pylint.

**Independent Test**: Run the pipeline on a local subset (e.g., 10 functions) and verify `data/static_baseline.csv` exists with correct columns (`code`, `loc`, `cyclomatic_complexity`, `static_smell_labels`).

### Implementation for User Story 1

- [X] T007 [US1] Implement `code/data_pipeline.py` to sample 800 functions from `codeparrot/github-code` using HuggingFace `datasets` (FR-001)
- [X] T008 [US1] Implement structural metric calculation in `code/data_pipeline.py` using `radon` for LOC and Cyclomatic Complexity (FR-002)
- [X] T009 [US1] Implement Pylint execution in `code/data_pipeline.py` to generate static smell labels AND normalize raw Pylint codes to canonical smell names for deterministic baseline (FR-003)
- [X] T010 [US1] Implement error handling in `code/data_pipeline.py` to catch `radon` parsing errors, log the file, and exclude from final count (Edge Case)
- [~] T011 [US1] Implement CSV serialization in `code/data_pipeline.py` to write `data/static_baseline.csv` with normalized smell codes (FR-001)
- [ ] T012 [US1] Add validation to ensure `data/static_baseline.csv` contains ≥ 95% of sampled functions with all required columns (FR-001, SC-005)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Semantic Feature Extraction and LLM Inference (Priority: P2)

**Goal**: Compute semantic embeddings and generate "smell labels" via a CPU-quantized LLM (CodeLlama-7B-GGUF) using a standardized prompt.

**Independent Test**: Process a single function through the embedding model and LLM, verifying a dense vector is produced and the LLM returns a parsable list of smells.

**Depends on**: T011 (US1) must complete to provide `data/static_baseline.csv`.

### Implementation for User Story 2

- [~] T013 [US2] [Depends: T011] Implement `code/semantic_analysis.py` to load `sentence-transformers/all-MiniLM-L6-v2` and compute dense vectors for functions in `data/static_baseline.csv` (FR-005)
- [X] T014 [US2] Implement `code/semantic_analysis.py` to load `CodeLlama-7B-Instruct-GGUF` (4-bit) using `llama-cpp-python` on CPU device (FR-004)
- [X] T015 [US2] Implement the standardized "Code Smell Detection" prompt in `code/semantic_analysis.py` to request a JSON list of smell categories (FR-004)
- [X] T016 [US2] Implement batched inference loop in `code/semantic_analysis.py` with batch size ≤ 10 (within ≤ 50 constraint) and explicit `gc.collect()` between batches to manage RAM, and record batch-level metrics (RAM, CPU, time) (FR-004, FR-008)
- [X] T017 [US2] Implement JSON parsing and error handling in `code/semantic_analysis.py` to log "Unparseable" for malformed LLM outputs (Edge Case)
- [X] T018 [US2] Implement context window check in `code/semantic_analysis.py` to truncate or skip functions exceeding model limits and log the count (Edge Case)
- [ ] T019 [US2] Write embeddings and LLM labels to `data/processed/semantic_results.json` (FR-004, FR-005)
- [~] T020 [US2] [Depends: T006b] Add monitoring in `code/semantic_analysis.py` to record peak RAM, CPU utilization, and inference time per batch to `results/resource_metrics.json` using `code/monitoring.py` (FR-008)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Comparative Statistical Analysis and Reporting (Priority: P3)

**Goal**: Correlate features with outcomes, perform McNemar's test, logistic regression (with VIF check), sensitivity analysis, and generate a summary report.

**Independent Test**: Run the analysis script on `data/processed/semantic_results.json` and verify `results/` contains p-values, regression coefficients, and sensitivity reports.

**Depends on**: T019 (US2) must complete to provide `data/processed/semantic_results.json`.

### Implementation for User Story 3

- [~] T021 [US3] [Depends: T019] Implement `code/statistical_analysis.py` to merge `data/static_baseline.csv` and `data/processed/semantic_results.json` into a unified dataset
- [~] T021a [US3] Validate merged dataset completeness (≥95% rows have all required fields: code, metrics, static labels, semantic vectors, LLM labels) of the 800 sampled functions before proceeding to statistical analysis (SC-005)
- [X] T022 [US3] Implement McNemar's test per smell category (aggregating paired detection outcomes per function) in `code/statistical_analysis.py` (FR-006)
- [X] T023 [US3] Implement Variance Inflation Factor (VIF) calculation in `code/statistical_analysis.py` for predictors (LOC, Cyclomatic, Semantic Mean) (FR-010)
- [ ] T024 [US3] Implement logistic regression fitting in `code/statistical_analysis.py` that excludes predictors with VIF ≥ 5, flags high-VIF predictors in output, and implements exclusion as the only fallback path (FR-007, FR-010)
- [ ] T025 [US3] Implement sensitivity analysis in `code/statistical_analysis.py` sweeping LOC thresholds (50, 100, 150) and calculating false-positive/negative rates (FR-009)
- [ ] T026 [US3] Generate `results/statistical_significance.json` containing McNemar p-values (FR-006, SC-003)
- [ ] T027 [US3] Generate `results/logistic_regression.json` containing coefficients and VIF scores (FR-007, SC-001, SC-002)
- [ ] T028 [US3] Generate `results/sensitivity_report.md` listing smells detected *only* by static, *only* by LLM, and sensitivity results (FR-009)
- [ ] T029 [US3] Verify `results/` artifacts contain valid data for ≥ 95% of the sample (SC-005)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T030a [P] Add usage instructions to `README.md`
- [ ] T030b [P] Update dependencies list in `README.md`
- [ ] T030c [P] Create `quickstart.md` with setup and run instructions
- [ ] T031a [P] Remove unused imports from all `code/` modules
- [ ] T031b [P] Apply black formatting to all `code/` modules
- [ ] T031c [P] Extract helper functions from `code/statistical_analysis.py`
- [ ] T032a [P] Profile and optimize batch loading in `code/semantic_analysis.py` to reduce RAM peak
- [ ] T032b [P] Verify total runtime ≤ 6h via dry-run on CI with mock data
- [ ] T033a [P] Add `tests/unit/test_data_pipeline.py::test_radon_metrics`
- [ ] T033b [P] Add `tests/unit/test_semantic_analysis.py::test_parsing`
- [ ] T034 Run `quickstart.md` validation to ensure end-to-end reproducibility

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on data output from US1 (`data/static_baseline.csv`)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on data output from US1 and US2

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
3. Complete Phase 3: User Story 1
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