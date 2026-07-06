# Tasks: Quantifying the Impact of Codebase Age on LLM Code Understanding

**Input**: Design documents from `/specs/001-quantify-age-impact/`
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

- [ ] T001 Create project structure per implementation plan: Create directories `code/`, `code/extraction/`, `code/inference/`, `code/analysis/`, `code/utils/`, `data/raw/`, `data/extracted/`, `data/aggregated/`, `data/results/`, `data/models/`, `tests/unit/`, `tests/integration/`.
- [ ] T002 Initialize Python 3.11 project with dependencies in `requirements.txt` (including `huggingface_hub`, `transformers`, `torch`, `bitsandbytes`, `gitpython`, `pandas`, `scipy`, `ast`, `tokenizers`, `networkx`).
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup `code/utils/config.py` for constants, random seeds, and -hour timeout limits.
- [X] T005 [P] Implement `code/utils/logging.py` for unified logging across the pipeline.
- [X] T006 [P] Create `code/utils/hasher.py` to generate SHA-256 hashes for artifacts (Constitution V).
- [X] T007 [P] Create `code/utils/reference_validator.py` to verify citations in markdown artifacts. The validator MUST check both legacy paths (`idea/`, `technical-design/`, `implementation-plan/`, `paper/`) and the active project structure (`specs/`) to ensure no citations are missed.
- [X] T008 Create base data models/entities structure in `code/models.py` defining classes: `Snippet` (snippet_id, repo_url, file_path, median_commit_age, snippet_content, token_count, complexity), `Repository` (repo_url, commit_count, median_age), `InferenceResult` (snippet_id, perplexity, functional_correctness_rate, status), and `FileMetric` (file_path, mean_perplexity, mean_correctness, mean_complexity, mean_length, median_age).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Core Data Extraction and Age Calculation (Priority: P1) 🎯 MVP

**Goal**: Extract up to 200 function-level Python snippets from 3-5 distinct repositories and calculate `median_commit_age` for each snippet based on git history.

**Independent Test**: Run the extraction script against 3 known repos and verify the output CSV contains a structured set of rows corresponding to the experimental design with non-null `median_commit_age` and `snippet_content` columns.

### Implementation for User Story 1

- [ ] T009 [US1] Implement `code/extraction/git_utils.py` to fetch git history and calculate `median_commit_age` per file (handling sparse history edge cases).
- [~] T010 [US1] Implement `code/extraction/snippet_extractor.py` using AST to extract function-level Python snippets, filter by token length (≥50 tokens), and calculate `complexity` using `networkx` Control Flow Graph analysis.
- [ ] T010.1 [US1] Ensure `snippet_extractor.py` outputs `token_length` and `complexity` columns for every snippet to support later covariate control.
- [~] T011 [US1] Implement `code/extraction/run_extraction.py` CLI entry point to orchestrate repo cloning, snippet extraction, age calculation, and complexity calculation for 3-5 repos.
- [~] T012 [US1] Add error handling in `run_extraction.py` to log and skip repos with inaccessible git history while ensuring a minimum of 3 valid repos are processed.
- [~] T013 [US1] Verify extraction output CSV structure matches requirements (columns: `snippet_id`, `repo_url`, `file_path`, `median_commit_age`, `snippet_content`, `token_count`, `complexity`, `token_length`).
- [ ] T013.1 [US1] Create `tests/verify_extraction.py` to programmatically assert the CSV columns exist and row count is at least 800 (minimum viable dataset per FR-001).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - CPU-Only Inference and Metric Generation (Priority: P2)

**Goal**: Run a quantized small-scale CodeLLM on CPU

Research Question: Can quantized small-scale CodeLLMs perform effectively on CPU hardware?

Method: Deploy and evaluate a quantized small-scale CodeLLM on a CPU environment.

References: Nijkamp et al. (2023) to generate `perplexity` and `functional_correctness_rate` for extracted snippets within a fixed time budget.

**Independent Test**: Run the inference script on a subset of snippets and verify the output file contains valid `perplexity` (float > 1.0 or NaN) and `functional_correctness_rate` (float in [0.0, 1.0] or NaN) columns.

### Implementation for User Story 2

- [~] T014 [US2] Implement `code/inference/model_loader.py` to load CodeGen-small with CPU-only quantization (8-bit/4-bit via `bitsandbytes` or `llama.cpp`), explicitly disabling CUDA.
- [ ] T014.1 [US2] Create `code/inference/model_downloader.py` to download and cache CodeGen-350M weights to `data/models/` before inference begins.
- [~] T015 [US2] Implement `code/inference/metrics_calculator.py` to calculate `perplexity` and `functional_correctness_rate`.
- [ ] T015.1 [US2] In `metrics_calculator.py`, implement logic to locate and execute associated unit tests for each snippet if available; if not, generate synthetic semantic validation by attempting code execution (syntax + type + basic runtime logic) to assign a binary valid/invalid score.
- [ ] T015.2 [US2] Implement `code/inference/file_aggregator.py` to group snippets by `file_path` and calculate mean `perplexity`, mean `functional_correctness_rate`, mean `complexity`, and mean `token_length` into `data/aggregated/file_metrics.csv` (Key Methodological Adjustment).
- [ ] T015.3 [US2] Implement `code/inference/age_aggregator.py` to aggregate `median_commit_age` from snippet-level to file-level (using mean or median) and merge this with `data/aggregated/file_metrics.csv`, ensuring the unit of analysis matches the Plan's 'Key Methodological Adjustment'.
- [~] T016 [US2] Implement `code/inference/run_inference.py` CLI entry point to process the extraction CSV, applying a per-snippet timeout and total global timeout.
- [~] T017 [US2] Add robust error handling in `run_inference.py` to log failures, record `NaN` for metrics on timeouts/OOMs, and continue processing without crashing.
- [~] T018 [US2] Implement logic in `run_inference.py` to stop new inferences if total runtime approaches a predefined threshold. If the time limit is reached, finalize the report with available data and mark the run as 'incomplete' ONLY IF the 800-snippet minimum is not met; otherwise mark as 'complete' with available data.
- [~] T019 [US2] Verify inference output CSV structure (columns: `snippet_id`, `perplexity`, `functional_correctness_rate`, `inference_time`, `status`) and verify `file_metrics.csv` exists with aggregated data.
- [ ] T019.1 [US2] Create `tests/unit/test_inference_structure.py` to programmatically assert the inference CSV columns exist and `file_metrics.csv` contains valid aggregated rows.
- [ ] T019.2 [US2] Create `tests/verify_completeness.py` to calculate the data completeness rate (valid data points / total valid snippets) and assert it meets the ≥95% target defined in SC-004.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Correlation and Reporting (Priority: P3)

**Goal**: Perform Spearman rank correlation analysis between `median_commit_age` and metrics, producing a final report with coefficients and p-values.

**Independent Test**: Feed the analysis script a pre-calculated results CSV and verify the generated report contains valid `spearman_correlation_age_perplexity` and `spearman_correlation_age_correctness` with p-values.

### Implementation for User Story 3

- [~] T020 [US3] Implement `code/analysis/correlation.py` to perform Spearman rank correlation on `data/aggregated/file_metrics.csv` (which now includes file-level `median_commit_age`), handling NaNs by excluding rows, and controlling for `complexity` and `token_length` covariates.
- [~] T021 [US3] Implement `code/analysis/report_generator.py` to generate a final Markdown/JSON report stating correlation coefficients, p-values, and statistical significance flags.
- [~] T022 [US3] Add logic in `report_generator.py` to explicitly state "No significant correlation" if p-value > 0.05.
- [~] T023 [US3] Integrate `code/utils/hasher.py` to hash the final results CSV and update the project state YAML (Constitution V).
- [~] T024 [US3] Verify final report contains all required metrics and correctly interprets statistical significance based on p < 0.05 threshold.
- [ ] T024.1 [US3] Create `tests/verify_report.py` to programmatically assert the report JSON keys exist and values are numeric.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [~] T025 [P] Documentation updates in `README.md` and `specs/001-quantify-age-impact/quickstart.md`.
- [ ] T026.1 Refactor `code/inference/metrics_calculator.py` to reduce cyclomatic complexity to a low level.
- [ ] T026.2 Refactor `code/analysis/correlation.py` to reduce cyclomatic complexity to a lower, manageable level.
- [ ] T027.1 Implement batching in `code/inference/model_loader.py` to target average inference time < 30s per snippet.
- [~] T028 [P] Add unit tests for extraction logic in `tests/unit/test_extraction.py`.
- [~] T029 [P] Add unit tests for inference logic in `tests/unit/test_inference.py`.
- [ ] T030 Run `quickstart.md` validation.

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
- **User Story 2 (P2)**: Depends on US1 completion (needs extracted CSV)
- **User Story 3 (P3)**: Depends on US2 completion (needs inference results CSV)

### Within Each User Story

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
# Launch all models for User Story 1 together:
Task: "Implement git_utils.py"
Task: "Implement snippet_extractor.py"
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
 - Developer B: User Story 2 (after US1 data ready)
 - Developer C: User Story 3 (after US2 data ready)
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
- **Critical Constraint**: All inference tasks must strictly adhere to CPU-only, a reasonable time budget, and GB RAM limits.. No GPU dependencies allowed.