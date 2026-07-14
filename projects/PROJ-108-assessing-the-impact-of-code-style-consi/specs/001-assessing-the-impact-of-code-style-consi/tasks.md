# Tasks: Assessing the Impact of Code Style Consistency on LLM Code Understanding

**Input**: Design documents from `/specs/001-assessing-the-impact-of-code-style-consi/`
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

- [X] T001 [P] Create `code/`, `data/`, `tests/`, `data/raw/`, `data/processed/`, `data/metadata/`, `tests/unit/`, `tests/integration/` directories at repository root
- [X] T002 Initialize Python 3.10 project with pinned dependencies in `code/requirements.txt`
- [X] T003 [P] Configure linting (flake8/black) and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement `code/00_validate_urls.py` to verify CodeSearchNet and Defects4J dataset URLs before download
- [X] T005 Implement `code/00_hash_artifacts.py` to generate content hashes for data artifacts and update `state/*.yaml` (Depends on T004 success)
- [X] T006 [P] Create `code/utils/metrics.py` with helper functions for BLEU, F1, and statistical calculations
- [ ] T007 [P] Setup `data/raw/` and `data/metadata/` directory structure with `.gitkeep`
- [X] T008 [P] Implement CPU-safe model loading utilities in `code/utils/model_loader.py` (no CUDA/bitsandbytes)
- [ ] T009 [P] Implement `code/00_extract_metadata.py` to extract `file_age` (from git log), `file_size` (bytes), and `cyclomatic_complexity` (from radon) for all source files, outputting to `data/metadata/file_metadata.csv`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Compute Style Consistency Metrics (Priority: P1) 🎯 MVP

**Goal**: Automatically calculate normalized style-consistency scores for code files to enable stratification.

**Independent Test**: Run `code/01_style_scoring.py` on a small subset of Python files; verify output CSV contains valid scores (0.0–1.0) and handles parse errors gracefully.

### Tests for User Story 1

- [ ] T010 [P] [US1] Unit test for style scoring logic in `tests/unit/test_style_scoring.py` (verify score range and metric aggregation)
- [ ] T011 [P] [US1] Unit test for error handling in `tests/unit/test_style_scoring.py` (verify parse errors skip without crash) <!-- ATOMIZE: requested -->
- [ ] T012 [P] [US1] Unit test for stratification logic in `tests/unit/test_stratification.py` (verify High/Med/Low group assignment)

### Implementation for User Story 1

- [ ] T013 [US1] Implement `code/01_style_scoring.py` to run `pylint` (indentation/naming) and `radon` (line-length), compute composite score, AND extract `file_size` and `cyclomatic_complexity` (if not already in T009), logging errors for skipped files. Output to `data/metadata/style_scores_raw.csv`.
- [~] T014 [US1] Implement `code/02_stratification.py` to read style scores and accept threshold arguments (e.g., `--low-threshold 0.25 --high-threshold 0.75`) to assign groups: Low (<low), Medium (low-high), High (>high). Output to `data/processed/style_scores_threshold_<low>_<high>.csv`.
- [~] T015 [US1] Implement `code/03_sensitivity_analysis.py` to run T014 with multiple threshold sets (15/85, 25/75, 30/70), compare group stability (e.g., variance of group means), and output `data/processed/sensitivity_report.json` identifying the optimal threshold set.
- [~] T016 [US1] Generate `data/processed/style_scores.csv` using the optimal thresholds from T015, containing columns: `file_path`, `pylint_indent`, `radon_line_len`, `composite_score`, `group`, `file_size`, `cyclomatic_complexity`, `file_age`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Execute LLM Inference on Stratified Data (Priority: P2)

**Goal**: Run StarCoder (CPU-only) on stratified samples to generate summaries and bug predictions.

**Independent Test**: Run `code/inference.py` on a small number of samples from the "High" group; verify output JSONL contains generated text and predictions without memory timeout.

### Tests for User Story 2

- [~] T017 [P] [US2] Integration test for inference pipeline in `tests/integration/test_inference.py` (verify output format and timeout handling)
- [~] T018 [P] [US2] Unit test for metrics calculation in `tests/unit/test_metrics.py` (verify BLEU handles null references gracefully)
- [~] T019 [P] [US2] Integration test for timeout enforcement in `tests/integration/test_timeout.py` (verify exit code on resource exhaustion)

### Implementation for User Story 2

- [~] T020 [US2] Implement `code/03_inference.py` to load StarCoder in CPU mode, process stratified samples (from T016), and generate BOTH natural-language summaries (max 64 tokens) AND bug-localization predictions (line numbers) in a single pass. Handle errors (timeout, context overflow, missing ground truth) gracefully, outputting `data/processed/inference_results.jsonl`.
- [~] T021 [US2] Implement `code/04_evaluation.py` to compute BLEU-4 for summaries and Precision/Recall/F1 for bug localization, handling null metrics gracefully.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Perform Statistical Analysis and Reporting (Priority: P3)

**Goal**: Run ANCOVA and t-tests to determine if style consistency significantly impacts LLM accuracy.

**Independent Test**: Run `code/05_statistical_analysis.py` on a synthetic dataset with known properties; verify correct p-values, effect sizes, and covariate coefficients are reported.

### Tests for User Story 3

- [~] T022 [P] [US3] Integration test for statistical analysis in `tests/integration/test_analysis.py` (verify ANCOVA and t-test output schemas)
- [~] T023 [P] [US3] Unit test for multiple comparison corrections in `tests/unit/test_corrections.py` (verify Tukey HSD and Bonferroni logic)
- [~] T024 [P] [US3] Integration test for ablation analysis in `tests/integration/test_ablation.py` (verify complexity control)
- [~] T025 [P] [US3] Unit test for pre-check logic in `tests/unit/test_precheck.py` (verify effect size > 0.5 gate)

### Implementation for User Story 3

- [~] T026 [US3] Implement the statistical analysis script to perform one-way ANCOVA (controlling for `file_size` and `file_age` as covariates per FR-005) on BLEU scores, aligning with the Plan's resolution of the FR-008 conflict.
- [~] T027 [US3] Implement two-sample t-test logic in `code/05_statistical_analysis.py` for F1 scores between High and Low groups.
- [~] T028 [US3] Implement family-wise error rate correction (Tukey HSD, Bonferroni) as per FR-006.
- [~] T029 [US3] Implement ablation analysis to verify style score independence from code complexity. Note: While `cyclomatic_complexity` is extracted (T013), use `file_size` as the control variable in this ablation to avoid multicollinearity with the style score, as justified in the Plan. Explicitly mention `cyclomatic_complexity` and the justification in the script.
- [~] T030 [US3] Implement group separation verification (effect size > 0.5) and statistical power estimation (FR-009).
- [~] T031 [US3] Generate `data/processed/statistical_report.json` containing F-statistic, p-values, Cohen's d, CIs, and covariate coefficients (including `file_age`). <!-- FAILED: unspecified -->
- [~] T032 [US3] Implement a robustness check script (`code/06_robustness_check.py`) to attempt running a secondary model (CodeLlama 7B). If CPU constraints prevent execution, fallback to a CPU-feasible model (e.g., Phi-3-mini or StarCoder-3B) and compute the Spearman correlation of effect directions. Explicitly document the fallback in the output report to satisfy SC-005's metric requirement under hardware constraints.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [~] T033 [P] Update `README.md` with installation steps, usage examples, and statistical results section
- [~] T034 Code cleanup: remove unused imports and standardize docstrings in `code/utils/`
- [~] T035 [P] Add unit tests for edge cases in `tests/unit/test_style_scoring.py` (e.g., empty file, non-UTF8 encoding)
- [~] T036 Run `quickstart.md` validation to ensure end-to-end reproducibility <!-- ATOMIZE: requested -->

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - **CRITICAL**: Requires `data/processed/style_scores.csv` from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - **CRITICAL**: Requires `data/processed/inference_results.jsonl` from US2

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
Task: "Unit test for style scoring logic in tests/unit/test_style_scoring.py"
Task: "Unit test for stratification logic in tests/unit/test_stratification.py"

# Launch all models for User Story 1 together:
Task: "Implement code/01_style_scoring.py"
Task: "Implement code/02_stratification.py"
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
- **Hardware Constraint**: All tasks MUST run on CPU-only, multi-core, limited RAM, with a bounded time limit. No GPU/CUDA libraries.