---
description: "Task list template for feature implementation"
---

# Tasks: Evaluating the Impact of Code Generation on Code Review Quality

**Input**: Design documents from `/specs/001-evaluating-llm-code-review-impact/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root
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

- [X] T001 Create project structure per implementation plan (create `code/`, `data/`, `docs/`, `tests/` directories)
- [X] T002 [P] Create `code/utils/config.py`. Deliverable: A file containing `load_config()` function (returns dict of environment variables) and `set_seed(seed=42)` function that sets random seeds for `numpy`, `pandas`, and `random` libraries to 42. (FR-012)
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools in `pyproject.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup `code/utils/hash_artifacts.py` to compute SHA-256 checksums for data and stats artifacts (Constitution Principle V)
- [X] T005 [P] Create `code/data/__init__.py` and `code/labeling/__init__.py` package structures
- [X] T006 [P] Create `contracts/dataset.schema.yaml` defining required fields (code diff, review comments, merge timestamp, project metadata)
- [X] T008 [P] Create `contracts/output.schema.yaml`. Deliverable: YAML file defining JSON schemas for: 1) Mann-Whitney U results (keys: `statistic`, `pvalue`, `method`), 2) VIF diagnostics (keys: `predictor`, `vif_score`), 3) Power analysis (keys: `sample_size`, `min_detectable_effect`), and 4) Error reports (keys: `error_code`, `observed_counts`). (FR-005, FR-008, FR-010)
- [X] T007 [P] Setup `code/utils/logger.py` for structured logging and error reporting (Power Insufficiency, Data Completeness)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Dataset Acquisition and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Load public GitHub PR dataset, classify commits, and extract review/complexity metrics with data validation.

**Independent Test**: Verify that loading the dataset, running the classification pipeline, and checking completeness yields ≥95% valid records and ≥500 items per group.

### Tests for User Story 1

- [X] T009 [P] [US1] Unit test for keyword classification logic in `tests/unit/test_classify.py` (test ≥2 keyword threshold logic: verify that a message with a single keyword is 'Human' and a message with multiple keywords is 'LLM')
- [X] T010 [P] [US1] Integration test for data completeness check in `tests/integration/test_data_completeness.py` (verify <95% completeness triggers ValueError with 'Data Completeness Error' message)
- [X] T011 [P] [US1] Integration test for power insufficiency check in `tests/integration/test_power_check.py` (verify <500 per group triggers ValueError with 'Power Insufficiency Error' message)

### Implementation for User Story 1

- [X] T012 [P] [US1] Implement `code/data/fetch.py` to download dataset `codeparliament/github-code-search` from HuggingFace using `datasets.load_dataset()` (FR-001, Verified Accuracy)
- [X] T014a [P] [US1] Implement `code/data/preprocess.py` function `load_and_extract()`. Logic: Load raw data, extract code diffs, review comments, merge timestamps, and project metadata into a DataFrame. Output: `data/raw/raw_prs.parquet`. (FR-001)
- [X] T014b [US1] Implement `code/data/preprocess.py` function `validate_completeness()`. Logic: Check for ≥95% completeness of required fields. If <95%, raise `ValueError` with 'Data Completeness Error'. Output: `docs/reports/completeness_report.json`. (FR-011, FR-014)
- [X] T014c [P] [US1] Implement `code/data/preprocess.py` function `compute_basic_stats()`. Logic: Calculate initial descriptive statistics (row counts, null counts) on the validated data. Output: `data/processed/basic_stats.json`. (FR-011)
- [X] T014d [P] [US1] Create `code/labeling/keywords.yaml` containing the EXACT list of LLM-associated keywords required for FR-002: ["copilot", "generated by llm", "ai code", "github copilot", "code generated by", "llm generated", "ai generated"] (FR-002)
- [X] T014e [P] [US1] Implement `code/labeling/classify.py`. Logic: Load keywords from `code/labeling/keywords.yaml` and apply the ≥2 threshold rule. Output: `data/processed/classified_prs.parquet` with `predicted_label` column. (FR-002, FR-015)
- [X] T015a [P] [US1] Implement `code/data/preprocess.py` function `iterate_code_diffs()`. Logic: Iterate over all code diffs in the DataFrame. Handle unsupported languages by logging warnings. Output: A generator yielding (pr_id, code_snippet) tuples. (FR-003)
- [X] T015b [P] [US1] Implement `code/data/preprocess.py` function `compute_complexity_metrics()`. Logic: Use `radon.cc` and `radon.loc` on code snippets from T015a. Output: `data/processed/complexity_metrics.parquet` with columns `cyclomatic_complexity`, `lines_of_code`. (FR-003)
- [X] T015c [P] [US1] Implement `code/data/preprocess.py` function `handle_complexity_errors()`. Logic: Set metrics to `NaN` for unsupported languages and log warnings. (FR-003 edge case)
- [X] T014f [P] [US1] Implement `code/data/preprocess.py` function `validate_power()`. Logic: Count LLM and Human labels. If either <500, raise `ValueError` with 'Power Insufficiency Error'. Output: `docs/reports/power_status.json`. (FR-013)
- [X] T016 [P] [US1] Implement `code/data/preprocess.py` function `generate_audit_sample()`. Logic: Create a random sample (seed fixed for reproducibility, size sufficient for manual audit) of classified PRs for manual audit. Output: `docs/reports/audit_sample_unlabeled.csv` with columns `pr_id`, `commit_message`, `code_snippet`. (FR-015)
- [ ] T017a [US1] **Manual Step**: A human reviewer must open the PRs listed in `docs/reports/audit_sample_unlabeled.csv` (generated by T016), determine if the code is LLM-generated or human-written, and save the results to `docs/reports/audit_sample_labeled.csv` with an additional column `human_label`. This step is a blocking gate. (FR-015)
- [ ] T017b [US1] **Automated Ingestion**: Implement `code/utils/wait_for_manual_input.py`. Logic: Poll `docs/reports/audit_sample_labeled.csv` every 30 seconds. If found, validate schema (`pr_id`, `human_label`, no nulls). If valid, log success and exit 0. If invalid, log error and exit 1. (FR-015)
- [X] T018 [US1] Implement `code/data/preprocess.py` function `calculate_audit_accuracy()`. Logic: Load the original classified data (from T014e) and the human-labeled CSV (from T017b). Compare `predicted_label` vs `human_label` and calculate accuracy. Output: `docs/reports/audit_accuracy.json`. (FR-015, SC-009)
- [X] T019 [US1] Implement `code/data/preprocess.py` function `write_error_report()`. Logic: Write `error_report.json` to `docs/reports/` with specific error codes ('POWER_INSUFFICIENCY', 'DATA_COMPLETENESS_ERROR') and observed counts if T014b or T014f fails. (FR-013, FR-014)
- [X] T020 [US1] Integrate `code/utils/hash_artifacts.py` invocation after `preprocess.py` completes. Hash artifacts: `data/processed/cleaned.parquet`, `data/processed/classified_prs.parquet`, `docs/reports/audit_sample_unlabeled.csv` (IF EXISTS). Runs ONLY if T014b (validation) passes. (Constitution Principle V)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (data loaded, classified, metrics computed, audit accuracy recorded)

---

## Phase 4: User Story 2 - Statistical Comparison Analysis (Priority: P2)

**Goal**: Perform Mann-Whitney U tests, linear regression with VIF diagnostics, and power analysis.

**Independent Test**: Verify that Mann-Whitney U tests run with Bonferroni/BH correction, regression VIF < 5 is reported, and power analysis is documented.

### Tests for User Story 2

- [X] T022 [P] [US2] Unit test for Mann-Whitney U test wrapper in `tests/unit/test_stats.py`
- [X] T023 [P] [US2] Unit test for multiple comparison correction (Bonferroni/BH) in `tests/unit/test_stats.py`
- [X] T024 [P] [US2] Unit test for VIF calculation in `tests/unit/test_stats.py`

### Implementation for User Story 2

- [X] T025 [P] [US2] Implement `code/analysis/stats.py` Mann-Whitney U test function for comment count, sentiment, merge time. Input: `data/processed/classified_prs.parquet`. (FR-004)
- [X] T026 [P] [US2] Implement `code/analysis/stats.py` multiple comparison correction logic supporting BOTH Bonferroni and Benjamini-Hochberg (BH) methods, configurable via `code/utils/config.py`. Input: p-values from T025. (FR-005)
- [X] T027 [P] [US2] Implement `code/analysis/stats.py` power analysis function using `statsmodels.stats.power` to calculate minimum detectable effect size for 80% power at α = 0.05. Output: `docs/reports/power_analysis.json`. (FR-008)
- [X] T028 [US2] Implement `code/analysis/stats.py` linear regression with complexity covariates and VIF diagnostics. Input: `data/processed/complexity_metrics.parquet`. Output: `docs/reports/vif_diagnostics.json`. (FR-010)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (data ready, stats computed)

---

## Phase 5: User Story 3 - Visualization and Report Generation (Priority: P3)

**Goal**: Generate reproducible visualizations and final report with sensitivity analysis.

**Independent Test**: Verify that ≥3 plots are generated with significance markers and a sensitivity plot for keyword thresholds across a range of values.

### Tests for User Story 3

- [X] T030 [P] [US3] Unit test for plot generation (boxplots, histograms) in `tests/unit/test_viz.py`
- [X] T031 [P] [US3] Unit test for sensitivity analysis logic in `tests/unit/test_viz.py`

### Implementation for User Story 3

- [X] T032 [P] [US3] Implement `code/analysis/viz.py` boxplot generation for review metrics with significance markers (p < 0.05, p < 0.01, p < 0.001). Output: `docs/reports/boxplot_comment_count.png`, `docs/reports/boxplot_sentiment.png`, `docs/reports/boxplot_merge_time.png`. Figure size: appropriate dimensions for clarity and aspect ratio. (FR-006)
- [X] T033 [P] [US3] Implement `code/analysis/viz.py` histogram generation for metric distributions. Output: `docs/reports/histogram_comment_count.png`, `docs/reports/histogram_sentiment.png`. Binning: Sturges. (FR-006)
- [X] T034 [US3] Implement `code/analysis/viz.py` sensitivity analysis plot. Logic: Sweep keyword thresholds (low to high) and plot Classification Rate vs Threshold. Input: `code/labeling/classify.py` logic. Output: `docs/reports/sensitivity_analysis.png`. (FR-007)
- [X] T029a [US3] Implement `code/report/generate.py` function `append_disclaimer()`. Logic: Append a specific text block to `docs/reports/final_report.md` stating: "All findings are associational, not causal. Code complexity is a mediator; controlling for it may introduce collider bias." (FR-009)
- [X] T035a [US3] Implement `code/report/generate.py` function `aggregate_data()`. Logic: Load VIF, Power, Stats, and Audit results from their respective JSON files. Output: `docs/reports/report_data.json`. (FR-008, FR-010)
- [X] T035b [US3] Implement `code/report/generate.py` function `render_template()`. Logic: Load `docs/templates/report_template.md` and inject `report_data.json`. Output: `docs/reports/draft_report.md`.
- [X] T035c [US3] Implement `code/report/generate.py` function `write_final_report()`. Logic: Read `draft_report.md`, append disclaimer from T029a, and write to `docs/reports/final_report.md`. (FR-009)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T037 [P] Documentation updates: Update `docs/research.md` (Methodology, Data Sources) and `docs/quickstart.md` (Installation, Execution) with specific content from the implementation.
- [X] T038 [P] Code cleanup: Remove unused imports, ensure type hints, standardize docstrings in `code/`. Verify linting passes (ruff check).
- [X] T039 [P] Run quickstart.md validation: Execute `python code/main.py --validate`. Verify exit code 0 and no errors in log.
- [X] T040 [P] Verify all random seeds are consistently applied.: Run `grep -r "random.seed" code/` and verify all instances use a consistent configuration parameter..
- [X] T041 [P] Performance optimization: Implement chunked reading in `code/data/fetch.py` and verify benchmark script runs and records time < 6 hours for 50k PRs. (FR-012)

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 statistical output

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Data fetch/preprocessing before classification
- Classification before complexity metrics
- Stats computation before visualization
- Story complete before moving to next priority
- **Note on T015a/T015b/T015c**: T015a (Iterator) is marked [P] for parallel setup, but T015b (Calculation) depends on T015a. T015c (Error Handling) is parallel to T015b but logically part of the same flow.

### Explicit Task Dependencies

- **T014a** must be completed before **T014b** (load before validate)
- **T014b** must be completed before **T014c** (validate before stats)
- **T014d** must be completed before **T014e** (keywords must exist)
- **T015a** depends on **T014a** (data loaded)
- **T015b** depends on **T015a** (iterator ready)
- **T016** depends on **T014e** (classification complete)
- **T017a** depends on **T016** (unlabeled sample ready)
- **T017b** depends on **T017a** (manual step initiated) - **T017b polls for T017a's output**
- **T018** depends on **T017b** (human-labeled CSV validated)
- **T019** depends on **T014b** AND **T014f** (validation logic)
- **T020** depends on **T014b** (validation success) AND **T016** (if sample exists)
- **T025**, **T026**, **T028** depend on **T014a** (data loaded) and **T015b** (complexity metrics)
- **T032**, **T033**, **T034** depend on **T025**, **T026** (statistical results)
- **T034** depends on **T014e** (classification logic) - *Sensitivity analysis is a data-generation task*
- **T035a** depends on **T028**, **T027** (VIF/Power results available)
- **T035b** depends on **T035a** (data aggregated)
- **T035c** depends on **T035b** AND **T029a** (report assembly + disclaimer)
- **T029a** depends on **T035c** (report assembly available) - *Actually T029a is a step inside T035c flow*

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
# Launch all tests for User Story 1 together:
Task: "Unit test for keyword classification logic in tests/unit/test_classify.py"
Task: "Integration test for data completeness check in tests/integration/test_data_completeness.py"
Task: "Integration test for power insufficiency check in tests/integration/test_power_check.py"

# Launch all data tasks for User Story 1 together:
Task: "Implement code/data/fetch.py to download dataset from HuggingFace"
Task: "Create code/labeling/keywords.yaml with explicit keyword list"
Task: "Implement code/labeling/classify.py for keyword matching heuristics"
Task: "Implement code/data/preprocess.py logic to compute code complexity metrics (T015a, T015b, T015c)"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (data loaded, classified, metrics computed, audit accuracy recorded)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Stats computed)
4. Add User Story 3 → Test independently → Deploy/Demo (Visuals + Report)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Data)
 - Developer B: User Story 2 (Stats)
 - Developer C: User Story 3 (Viz/Report)
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
- **CRITICAL**: All data tasks must use real, reachable URLs (HuggingFace/UCI) — no synthetic data generation tasks allowed.
- **CRITICAL**: All statistical tasks must run on CPU-only CI (no GPU, no 8-bit quantization, no deep learning training).
- **CRITICAL**: FR-015 requires a manual audit sample generation (T016), a manual step (T017a), an automated ingestion/wait step (T017b), and accuracy calculation (T018). All four tasks are required to satisfy SC-009.
- **CRITICAL**: T021 (hashing) is conditional on T014b (validation) passing. If validation fails, hashing is skipped.
- **CRITICAL**: All error and audit reports must be written to `docs/reports/`, not `data/reports/`, to comply with project structure (data/ for datasets, docs/ for reports).
- **CRITICAL**: The keyword list for classification MUST be defined in `code/labeling/keywords.yaml` (T014d) to ensure reproducibility and satisfy FR-002.
- **CRITICAL**: The manual audit workflow is a hybrid process: T016 generates the unlabeled sample, a human performs the review (T017a) to create the labeled sample, T017b detects the file, and T018 consumes it to compute accuracy.
- **CRITICAL**: T017a is marked `[PENDING]` as it represents a manual human action. T017b is the automated trigger that follows.
- **CRITICAL**: T018 must load the original classified data (from T014e) to retrieve heuristic predictions for comparison with human labels.
- **CRITICAL**: T034 (Sensitivity Analysis) depends on T014e (Classification Logic) and implements the threshold sweep logic directly.
- **CRITICAL**: T025, T026, T028 are parallelizable with each other as they all consume the preprocessed data from T014a/T014c.
- **CRITICAL**: T012 (fetch.py) must use `datasets.load_dataset("codeparliament/github-code-search", split="train", streaming=True)` to stream data in chunks, ensuring memory usage stays within 7GB limits for large datasets. If the full dataset is too large, the task must implement an `itertools.islice` sample with a fixed seed and document the sample size and limitations explicitly in `docs/reports/sampling_methodology.md`. (FR-012, Constitution Principle: Real Data)
- **CRITICAL**: T028 is the sole producer of `vif_diagnostics.json`. T035a reads it. T035c does not write to it.
- **CRITICAL**: T029a appends the associational disclaimer to the final report, ensuring FR-009 is met in the output document.
