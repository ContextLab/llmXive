# Tasks: Evaluating the Impact of Code Generation on Code Review Time

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

- [ ] T001 Create project structure per implementation plan: `mkdir -p code/data code/analysis data/raw data/processed data/baseline_corpus tests/unit tests/integration docs/reports`. (FR-001, FR-002)
- [ ] T002 Initialize Python 3.11 project with `requirements.txt` containing pinned versions: `pandas==2.0.3`, `numpy==1.24.3`, `requests==2.31.0`, `statsmodels==0.14.0`, `scikit-learn==1.3.0`, `matplotlib==3.7.2`, `seaborn==0.12.2`, `pyyaml==6.0.1`, `pytest==7.4.0`. (FR-001)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create `code/config.py` to manage API keys and constants. Schema: `GITHUB_TOKEN` (str), `RATE_LIMIT_HOURLY` (int=5000), `BACKOFF_INITIAL` (int=1), `BACKOFF_MAX` (int=60), `STRATIFICATION_SEED` (int=42), `MAX_REVIEW_DAYS` (int=30). (FR-007)
- [ ] T005 [P] Implement `code/data/__init__.py` and base data utilities
- [ ] T006 [P] Setup rate limiting infrastructure (Token Bucket algorithm) in `code/data/rate_limiter.py`
- [ ] T007 Create base data models/entities in `code/data/models.py`. Define: `PullRequest(repo_id: str, pr_number: int, author: str, code_lines_changed: int, origin_label: str)`, `ReviewMetrics(median_time: float, mean_time: float, std_dev: float, sample_size: int)`. (FR-001)
- [ ] T008 Configure logging infrastructure to output to `data/run_logs.txt` and console
- [~] T009 Setup environment configuration management for GitHub API tokens

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Classification (Priority: P1) 🎯 MVP

**Goal**: Download PR metadata from high-star repos, classify as "Disclosing" (keywords) or "Non-Disclosing", and validate heuristics.

**Independent Test**: Execute `code/data/fetch_prs.py` on a small sample of PRs and verify `data/raw/` contains CSVs with columns (repo, pr_number, origin_label) and `data/validation_log.csv` exists with accuracy metrics.

**⚠️ TDD Execution Note**: Execute T010-T012 (Tests) BEFORE T013-T018 (Implementation) to satisfy TDD requirements.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Unit test for Token Bucket rate limiter in `tests/unit/test_rate_limit.py`. **Requirement**: Must explicitly test exponential backoff logic with specific parameters (initial 1s, max 60s) as per FR-007. (FR-007)
- [~] T011 [P] [US1] Unit test for classification heuristic logic in `tests/unit/test_classify.py`
- [~] T012 [P] [US1] Integration test for API fetch with mock response in `tests/integration/test_fetch_prs.py`

### Implementation for User Story 1

- [~] T013 [US1] Implement `code/data/fetch_prs.py`: Query GitHub API for PRs with ≥1000 stars, filter by keywords "copilot", "llm", "generated". **Input**: Read repo list from `data/config/repo_list.txt`. **Constraint**: Strictly fetch raw data; do NOT apply sampling or exclusion logic here. **Output**: Save raw JSON to `data/raw/prs_raw.json` with schema `[repo, pr_number, title, body, created_at, merged_at, author, lines_changed]`. (FR-001, FR-007)
- [~] T014 [US1] Implement stratified sampling and >50% exclusion logic in `code/data/fetch_prs.py`. **Algorithm**: Stratify by repo star count bins: 1k-10k, 10k-100k, >100k. **Exclusion**: Exclude any repository where >50% of PRs contain LLM keywords. **Output**: Save filtered dataset to `data/processed/sampled_prs.csv`. (FR-009)
- [~] T015 [US1] Implement `code/data/classify.py`: Apply keyword-based "Disclosing" label. **Constraint**: Per Plan Override, heuristics (formatting, comments) are ONLY for validation/covariates, NOT primary labeling. **Output**: Add `origin_label` (Disclosing/Non-Disclosing) and heuristic scores to `data/processed/sampled_prs.csv`. (FR-002, Plan Override)
- [ ] T016 [US1] Implement manual validation subset logic: Load `data/manual_labels.csv` (format: `pr_number, manual_label`). Calculate Cohen's Kappa against the `origin_label` to validate the **disclosure signal**. **Constraint**: If Kappa < 0.6, halt execution and flag dataset in `data/validation_log.csv`. **Output**: Log results to `data/validation_log.csv`. (FR-002, SC-002)
- [ ] T017 [US1] Implement sensitivity analysis sweep across a range of classification thresholds and report error rates. **Context**: Apply thresholds to validation/covariate heuristics, not the primary binary label. **Output**: Append sensitivity metrics to `data/validation_log.csv`. (FR-008)
- [ ] T018 [US1] Implement false positive estimation using external baseline corpus. **Input**: Download `data/baseline_corpus/codeparrot_sample.csv` from `https://huggingface.co/datasets/codeparrot/codeparrot-small`. **Output**: Calculate and save false positive rate to `data/baseline_corpus/estimated_fp_rate.json`. (FR-010)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Analysis of Review Duration (Priority: P2)

**Goal**: Calculate review times, filter outliers, and perform Mann-Whitney U and Linear Mixed-Effects Regression with SIMEX correction.

**Independent Test**: Run `code/analysis/models.py` on a synthetic CSV with known distributions and verify output coefficients/p-values match manual calculations.

### Implementation for User Story 2

- [~] T021 [US2] Implement `code/data/process.py`: Calculate `first_review_time` and `total_review_time` (minutes) from `data/processed/sampled_prs.csv`. **Output**: Append time columns to `data/processed/pr_data_cleaned.csv`. (FR-003)
- [~] T022 [US2] Implement outlier exclusion logic: Remove PRs with negative time or >30 days duration. **Output**: Save filtered dataset to `data/processed/pr_data_filtered.csv`. (FR-006)
- [ ] T023 [US2] Implement Mann-Whitney U test for primary hypothesis. **Context**: Per Plan Override, this satisfies the Plan's definition of SC-001 (overriding Spec FR-004/SC-001 which incorrectly cite LMER). **Input**: `data/processed/pr_data_filtered.csv`. **Output**: Write `statistic`, `p_value`, and `primary_p_value` to `data/analysis_results.json` under key `mann_whitney`. (SC-001, Plan Override)
- [ ] T024 [US2] Implement Linear Mixed-Effects Regression (random intercept by repo) with fixed effects (origin, code_size, reviewer_count). **Context**: Secondary analysis per Plan. **Output**: Write `coefficients`, `p_values`, `variance_components` to `data/analysis_results.json` under key `lmer`. (FR-004)
- [ ] T025 [US2] Implement Shapiro-Wilk test for distribution normality check on residuals. **Output**: Append `shapiro_p_value` to `data/analysis_results.json`. (SC-004)
- [ ] T026a [US2] Load baseline corpus false positive rate. **Input**: Read key "fp_rate" from `data/baseline_corpus/estimated_fp_rate.json` (output of T018). (FR-010)
- [ ] T026 [US2] Implement SIMEX correction for misclassification bias if false positive rate > 5% (from T026a). **Context**: Per Plan Override, use SIMEX (not Spec's "matrix correction"). **Logic**: If rate > 5%, apply SIMEX; else skip. **Output**: Append `simex_corrected_coefficients` to `data/analysis_results.json`. (FR-010, Plan Override)
- [ ] T027 [US2] Implement slope coefficient extraction for code size impact analysis. **Output**: Append `code_size_slopes` to `data/analysis_results.json`. (SC-003)

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T019 [P] [US2] Unit test for outlier filtering logic in `tests/unit/test_process.py`
- [ ] T020 [P] [US2] Unit test for SIMEX correction implementation in `tests/unit/test_models.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualization and Reporting (Priority: P3)

**Goal**: Generate diagnostic plots (boxplot, scatter, residuals) and a summary report.

**Independent Test**: Generate plots from a sample dataset and verify axes labels, color coding, and file formats.

### Implementation for User Story 3

- [ ] T029 [US3] Implement `code/analysis/viz.py`: Generate boxplot comparing review time distributions (Disclosing vs Non-Disclosing) with median lines. **Output**: Save to `docs/reports/boxplot_review_time.png`. (FR-005)
- [ ] T030 [US3] Implement `code/analysis/viz.py`: Generate scatter plot of code size vs. review time with separate regression lines and legend. **Output**: Save to `docs/reports/scatter_size_vs_time.png`. (FR-005)
- [ ] T031 [US3] Implement `code/analysis/viz.py`: Generate residual plots (residuals vs. predicted) to check model assumptions. **Output**: Save to `docs/reports/residuals.png`. (FR-005)
- [ ] T032 [US3] Implement summary report generation: Generate `docs/reports/summary.md` containing a table with columns: [Metric, Value, P-Value] and links to images in `docs/reports/`. Include primary p-value (Mann-Whitney) and LMER results. (FR-005)

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T028 [P] [US3] Integration test for plot generation in `tests/integration/test_viz.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [ ] T033 [P] Documentation updates: Add `README.md` with execution instructions and `quickstart.md`
- [ ] T034 Code cleanup and refactoring for readability
- [ ] T035 Performance optimization: Ensure memory usage < 7 GB via chunking/streaming if necessary (SC-005)
- [ ] T036 [P] Final integration test: Run full pipeline end-to-end and verify `data/` and `docs/` outputs
- [ ] T037 Run quickstart.md validation to ensure all steps complete within 6 hours. **Pass Criteria**: Exit code 0 and total runtime < 21600s. (SC-005)

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
- **User Story 2 (P2)**: Depends on US1 data output (`data/processed/pr_data_cleaned.csv`) to perform analysis
- **User Story 3 (P3)**: Depends on US2 analysis output (`data/analysis_results.json` or similar) to generate plots

### Within Each User Story

- **Implementation tasks MUST precede Test tasks** in execution order (see Phase 3, 4, 5 ordering).
- Tests (if included) MUST be written and FAIL before implementation (TDD approach).
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
Task: "Unit test for Token Bucket rate limiter in tests/unit/test_rate_limit.py"
Task: "Unit test for classification heuristic logic in tests/unit/test_classify.py"

# Launch all models for User Story 1 together:
Task: "Create base data models/entities in code/data/models.py"
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
 - Developer A: User Story 1 (Data Acquisition)
 - Developer B: User Story 2 (Statistical Analysis)
 - Developer C: User Story 3 (Visualization)
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
- **Methodological Note**: The Plan overrides the Spec regarding the primary statistical test (Mann-Whitney U vs LMER) and classification method (Disclosure vs Heuristics). Tasks reflect the Plan with explicit "Plan Override" tags where necessary for traceability.