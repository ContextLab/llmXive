# Tasks: Investigating the Impact of Code Ownership on LLM Code Understanding

**Input**: Design documents from `/specs/001-code-ownership-llm-understanding/`
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

- [ ] T001 Create project structure per implementation plan (mkdir -p code/{extractors,inference,analysis,utils}, data/{raw,processed,results}, tests)
- [ ] T002 Initialize Python 3.11 project with pinned requirements.txt (gitpython, radon, scikit-learn, transformers, torch==2.3.0+cpu, pandas, scipy, pyyaml, statsmodels, bitsandbytes-cpu) ensuring CPU-only torch variant and bitsandbytes-cpu are explicitly specified for SC-004 compliance
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools in code/

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Implement `code/utils/config.py` with random seed pinning and environment variable loading
- [ ] T005 [P] Implement `code/utils/logger.py` with structured logging and file rotation
- [ ] T006 Create `code/__init__.py` and package init files for all sub-packages
- [ ] T007 Setup data directory structure and `.gitkeep` files for `data/raw`, `data/processed`, `data/results`
- [ ] T008 Implement `code/main.py` entry point with argument parsing for pipeline stages
- [ ] T009 [P] [US3] Implement progressive sample reduction logic in `code/main.py` that dynamically reduces snippets per repo (5 -> 3 -> 2) if time/memory constraints are threatened, ensuring the Plan's fallback strategy is available before T041 triggers. This logic must be callable by T041.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Extract Socio-Technical Ownership Metrics (Priority: P1) 🎯 MVP

**Goal**: Extract quantitative ownership metrics (LOC-weighted Gini coefficient of commit distribution, developer count) from git history for target repositories, implementing the Plan's approved deviation from the Spec's simpler proxy.

**Independent Test**: Run extraction script on a known small repository and verify output JSON contains valid, non-null values for the LOC-weighted Gini coefficient and commit counts, matching manual `git blame` verification.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [ ] T010 [P] [US1] Contract test for ownership metrics schema in `tests/contract/test_ownership_metrics.py`
- [ ] T011 [P] [US1] Integration test for git history extraction in `tests/integration/test_git_extraction.py`

### Implementation for User Story 1

- [ ] T012 [P] [US1] Implement `code/extractors/git_metrics.py` to calculate the **LOC-weighted Gini coefficient** of commit distribution (using `git blame` to attribute lines to authors) and unique developer count, strictly adhering to the Plan's Complexity Tracking decision (deviating from Spec FR-001's simpler commit-count proxy to ensure accuracy). This task produces the artifact required by T028.
- [ ] T013 [US1] Implement temporal alignment logic in `code/extractors/git_metrics.py` to explicitly **checkout the specific commit SHA before running git log/blame** to ensure metrics reflect the state at that point in time, as required by Plan Phase 1.
- [ ] T014 [US1] Implement edge case handling in `code/extractors/git_metrics.py` for missing history or non-Python/Java repos (set metrics to null, log warning)
- [ ] T015 [US1] Create data loader in `code/extractors/__init__.py` to fetch repository URLs and CodeXGLUE sample metadata
- [ ] T016 [US1] Implement output serialization in `code/extractors/git_metrics.py` to save `OwnershipMetrics` JSON (containing `gini_coefficient` based on LOC-weighted distribution) to `data/processed/ownership_metrics.json`
- [ ] T040 [US1] Create a `code/analysis/deviation_rationale.md` document explaining the Spec/Plan conflict resolution (why LOC-weighted Gini and LMM were chosen over Spec defaults) to ensure auditability

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Compute Code Complexity and Documentation Controls (Priority: P2)

**Goal**: Calculate code complexity (cyclomatic) and documentation density for code snippets to serve as control variables.

**Independent Test**: Run complexity analyzer on a known code snippet and verify the cyclomatic complexity score matches the output of the `radon` CLI tool.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T017 [P] [US2] Contract test for code snippet metrics schema in `tests/contract/test_code_snippet_metrics.py`
- [ ] T018 [P] [US2] Integration test for complexity calculation in `tests/integration/test_complexity_calc.py`

### Implementation for User Story 2

- [ ] T019 [P] [US2] Implement `code/extractors/complexity.py` to calculate Cyclomatic Complexity using `radon`
- [ ] T020 [US2] Implement `code/extractors/complexity.py` to calculate Documentation Density (comment lines / total lines)
- [ ] T021 [US2] Implement filtering logic in `code/extractors/complexity.py` to skip non-Python/Java files and log warnings
- [ ] T022 [US2] Create `code/extractors/complexity.py` function to process snippets from `data/raw` and output `CodeSnippet` metrics to `data/processed/code_metrics.json`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Execute LLM Inference and Statistical Correlation (Priority: P3)

**Goal**: Run lightweight LLM inference on code snippets and perform Linear Mixed-Effects Regression (LMM) to correlate ownership with performance, implementing the Plan's approved statistical methodology.

**Independent Test**: Run full pipeline on a representative subset and verify output includes a regression summary table with p-values for the ownership coefficient from the LMM.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T023 [P] [US3] Contract test for regression output schema in `tests/contract/test_regression_output.py`
- [ ] T024 [P] [US3] Integration test for full pipeline execution in `tests/integration/test_full_pipeline.py`

### Implementation for User Story 3

- [ ] T025 [P] [US3] Implement `code/inference/runner.py` to load a large language model in low-bit quantization on CPU with `device_map="cpu"`. This task MUST include **context truncation logic to limit input sequence length to a fixed maximum threshold** and reference the **progressive sample reduction logic from T009** for fallback if OOM occurs.
- [ ] T026 [US3] Implement memory management in `code/inference/runner.py` to unload model and run `gc.collect()` after each snippet inference to prevent OOM
- [ ] T027 [US3] Implement retry logic in `code/inference/runner.py` (with a configurable maximum number of retries) for timeout/failure cases as per FR-005
- [ ] T028 [US3] Implement BLEU score calculation in `code/inference/runner.py` against CodeXGLUE ground truth
- [ ] T029 [US3] Implement `code/analysis/regression.py` to perform **Linear Mixed-Effects Model (LMM)** where the **unit of analysis is the Snippet** (n=150), using snippet-level ownership metrics (aggregated from repo-level LOC-weighted Gini), complexity, and documentation density as predictors, with Repository as a random effect, outputting p-values for the ownership coefficient.
- [ ] T030 [US3] Implement Variance Inflation Factor (VIF) calculation in `code/analysis/regression.py` to check for collinearity (SC-005); **MUST apply Logit transformation to BLEU scores** and include a **Gini^2 non-linearity term**; **MUST perform a Likelihood Ratio Test** for the non-linearity check as mandated by the Plan's Complexity Tracking table.
- [ ] T031 [US3] Implement sensitivity analysis in `code/analysis/regression.py` to sweep the **'Gini aggregation window'** (number of commits included in the Gini calculation) over **a range of values** (covering Spec {100, 500} and Plan's broad range) and **generate a stability report** comparing the regression coefficients across these windows to demonstrate result stability (SC-003, FR-007, Plan Phase 4). Reference T040 for rationale.
- [ ] T032 [US3] Implement Bonferroni/FDR correction logic in `code/analysis/regression.py` for multiple hypothesis testing (FR-006)
- [ ] T033 [US3] Create `code/main.py` orchestration logic to merge ownership, complexity, and inference data, filter failed samples, and prepare snippet-level data for LMM input (no aggregation to repo-level for the model input)
- [ ] T034 [US3] Implement output generation in `code/analysis/regression.py` to save regression tables, plots, and sensitivity reports to `data/results/`
- [ ] T041 [US3] Implement runtime monitoring and auto-stop logic in `code/main.py` that tracks total pipeline time; **if runtime > 5.5h, auto-stop the pipeline** and trigger the **progressive sample reduction logic from T009** (5 -> 3 -> 2) for subsequent runs if configured, logging the reduction to ensure the 6h constraint is met without failing the run.
- [ ] T042 [US3] Implement **context truncation** logic in `code/inference/runner.py` to **truncate input sequence length to 2048 tokens** to ensure feasibility on 7GB RAM as per Plan Phase 3. (Note: This is a duplicate of T025's requirement; T025 handles the main logic, this task ensures the specific 2048 limit is enforced in the runner).

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T034 [P] **Update `README.md`** with usage examples and installation instructions
- [ ] T043 [P] **Generate API docs** for `code/extractors`, `code/inference`, `code/analysis` using Sphinx or similar
- [ ] T035 [P] **Code formatting**: Apply black formatting to all Python files and run ruff for linting
- [ ] T044 [P] **Code refactoring**: Remove unused imports and extract helper functions to improve modularity
- [ ] T036 [P] Performance optimization: **Add a CI step/assertion** that fails if total pipeline runtime > 6 hours (relying on T041 for runtime management)
- [ ] T037 [P] Additional unit tests in `tests/unit/`
- [ ] T038 Run `quickstart.md` validation and ensure all acceptance scenarios pass
- [ ] T039 [P] **Implement memory monitoring** in `code/main.py` that logs and fails the pipeline if memory usage exceeds a predefined threshold or if GPU is detected, ensuring SC-004 compliance; verify `torch` CPU-only pin from T002 and environment has no GPU. (Note: T041 handles runtime monitoring; T039 handles environment verification).

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on data from US1 for temporal alignment context, but can be implemented independently
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on data from US1 and US2 for regression inputs
  - **Critical Order**: T012 (US1) and T019 (US2) must complete before T029 (US3) can run the full regression

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
Task: "Contract test for ownership metrics schema in tests/contract/test_ownership_metrics.py"
Task: "Integration test for git history extraction in tests/integration/test_git_extraction.py"

# Launch all models for User Story 1 together:
Task: "Implement code/extractors/git_metrics.py to calculate LOC-weighted Gini coefficient..."
Task: "Implement temporal alignment logic in code/extractors/git_metrics.py..."
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
- **Compute Constraint**: All inference tasks (T025-T028, T042) MUST respect the 2 CPU / 7GB RAM limit. If OOM occurs, reduce snippets per repo as per Plan.md fallback strategy (T009, T041).
- **Data Integrity**: T012 and T019 must use REAL git history and REAL code snippets from CodeXGLUE repositories. No synthetic data generation is allowed.
- **Spec/Plan Alignment**: T012 implements **LOC-weighted Gini** (Plan deviation from Spec FR-001). T029 implements **LMM** (Plan deviation from Spec FR-004). These deviations are documented in T040.