# Tasks: Evaluating the Impact of Code Generation on Code Review Quality

**Input**: Design documents from `/specs/001-evaluating-llm-code-review-impact/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: The examples below include test tasks. Tests are **OPTIONAL** - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root
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

- [ ] T001a [P] Create `code/` directory
- [ ] T001b [P] Create `data/raw/` directory
- [ ] T001c [P] Create `data/processed/` directory
- [ ] T001d [P] Create `tests/` directory
- [ ] T001e [P] Create `reports/` directory
- [ ] T001f [P] Create `code/__init__.py`
- [ ] T001g [P] Create `tests/__init__.py`
- [ ] T001h [P] Create `reports/figures/` directory
- [ ] T002 Initialize Python 3.11 project with `requirements.txt` (pandas, scikit-learn, scipy, textblob, radon, lizard, seaborn, matplotlib, datasets, lifelines, statsmodels, pytest)
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools
- [ ] T004 [P] Setup gitignore for `data/raw/`, `data/processed/`, `__pycache__`, `reports/figures`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 Implement `code/config.py` for reproducible random seeds and global constants
- [ ] T006 [P] Implement `code/utils/logging.py` for structured, reproducible logging
- [ ] T010 Create `code/labeling/config.yaml` with heuristic parameters (keyword list, threshold)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Dataset Acquisition and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Load public GitHub PR dataset, classify commits, extract review/complexity metrics, and validate data completeness.

**Independent Test**: Can be tested by loading the dataset, running the classification pipeline, and verifying that ≥95% of records have complete required fields and classification heuristics produce ≥500 LLM-labeled and ≥500 human-labeled PRs.

### Implementation for User Story 1

- [ ] T017 [US1] Implement full data download and checksum verification in `code/data/download.py` (Fetch `numenta/prs-v-sample` from HuggingFace, verify SHA-256 checksum against `data/raw/.checksums`)
- [ ] T018 [US1] Implement schema validation and filtering in `code/data/preprocess.py` (Halt if `commit_message` missing, handle nulls per FR-011)
- [ ] T019 [US1] Implement code complexity metrics (Cyclomatic, LOC) using `radon`/`lizard` in `code/data/metrics.py` (FR-003)
- [ ] T020 [US1] Implement Bug Density calculation (warnings per 100 LOC) in `code/data/metrics.py` (FR-013)
- [ ] T021 [US1] Implement Sentiment Score calculation using `textblob` in `code/data/metrics.py`
- [ ] T011 [US1] Implement `code/labeling/classify.py` with keyword-based LLM vs Human classification logic (FR-002)
- [ ] T012 [US1] Implement `code/audit/manual_review.py` to generate `data/raw/audit_ground_truth.csv` using deterministic simulation algorithm (seed=42, specific keyword-to-label mapping rules from T011) for CI validation (FR-015)
- [ ] T012b [US1] Generate `data/raw/audit_ground_truth.csv` with a balanced set of synthetic labels comprising both LLM and Human samples using the keyword thresholds defined in T011 (Depends on T011, seed=42)
- [ ] T022 [US1] Execute manual audit sampling in `code/audit/manual_review.py` (Load `data/raw/audit_ground_truth.csv`, compare against T011 heuristics using deterministic simulation algorithm (seed=42, specific keyword-to-label mapping rules))
- [ ] T023 [US1] Implement heuristic accuracy check in `code/audit/manual_review.py` (Halt if <70% per FR-015)
- [ ] T024 [US1] Implement data completeness validation (≥95% records) in `code/data/preprocess.py` (FR-011)
- [ ] T025 [US1] Save cleaned dataset to `data/processed/` with derivation logs

### Tests for User Story 1 ⚠️

- [ ] T013 [P] [US1] Unit test for download schema validation in `tests/unit/test_download.py`
- [ ] T014 [P] [US1] Unit test for keyword classification logic in `tests/unit/test_classify.py` (maps to FR-002)
- [ ] T015 [P] [US1] Unit test for audit sampling and accuracy calculation in `tests/unit/test_audit.py` (maps to FR-015)
- [ ] T016 [P] [US1] Unit test for complexity metric calculation in `tests/unit/test_metrics.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Comparison Analysis (Priority: P2)

**Goal**: Perform statistical comparisons (Mann-Whitney U, Cox PH) with error correction, power analysis, and covariate adjustment.

**Independent Test**: Can be tested by running the statistical pipeline on the preprocessed dataset and verifying that at least 3 pairwise comparisons are performed with adjusted p-values, and covariate adjustment methods are executed.

### Implementation for User Story 2

- [ ] T029 [US2] Implement SIMEX Calibration in `code/audit/simex.py` (Estimate misclassification matrix from audit results in `data/raw/audit_ground_truth.csv`)
- [ ] T030 [US2] Implement Propensity Score Matching (PSM) in `code/analysis/stats.py` using covariates: `repo_size`, `language` (CRITICAL: DO NOT use code complexity as it is a mediator)
- [ ] T030b [US2] Implement Exact Matching on Discrete Bins fallback in `code/analysis/stats.py` for `repo_size` and `language` bins, Trigger ONLY if PSM fails or VIF > 5 (Plan: Complexity Tracking)
- [ ] T031 [US2] Implement Exact Matching on Discrete Bins fallback in `code/analysis/stats.py` (Plan: Complexity Tracking)
- [ ] T041 [US2] Implement correlation diagnostic (Sentiment vs Bug Density) in `code/analysis/viz.py` (FR-016)
- [ ] T042 [US2] Implement confounder flagging in `code/analysis/stats.py` (Compute Spearman correlation; if r > 0.5, set `confounder_flag=True` and include metric in report with 'Potential Confounder' warning, DO NOT exclude)
- [ ] T032 [US2] Implement Mann-Whitney U test for Comment Count and Sentiment in `code/analysis/stats.py` (FR-004)
- [ ] T033 [US2] Implement Cox Proportional Hazards (PRIMARY) and Mann-Whitney U (SECONDARY/Sensitivity) for Merge Latency in `code/analysis/stats.py` (FR-004, Plan: Key Methodological Adjustment)
- [ ] T034 [US2] Implement Benjamini-Hochberg correction for multiple comparisons in `code/analysis/stats.py` (FR-005)
- [ ] T035 [US2] Implement power analysis and minimum detectable effect size documentation in `code/analysis/stats.py` (FR-008)
- [ ] T036 [US2] Implement VIF calculation for covariates (repo_size, language) and switch to Exact Matching if VIF > 5 (FR-010, Plan: Risk Mitigation)
- [ ] T037 [US2] Apply SIMEX correction to effect sizes using the audit matrix (Plan: Phase 5)
- [ ] T037b [US2] Document SIMEX-adjusted effect sizes in power analysis report (FR-008)
- [ ] T038 [US2] Save matched sample and statistical results to `data/processed/`

### Tests for User Story 2 ⚠️

- [ ] T026 [P] [US2] Integration test for statistical pipeline in `tests/integration/test_pipeline.py` (maps to US-2, FR-005)
- [ ] T027 [P] [US2] Unit test for SIMEX correction logic in `tests/unit/test_simex.py`
- [ ] T028 [P] [US2] Unit test for Propensity Score Matching (PSM) and Exact Matching fallback in `tests/unit/test_psm.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualization and Report Generation (Priority: P3)

**Goal**: Generate reproducible visualizations, sensitivity analysis, and final report with associational disclaimers.

**Independent Test**: Can be tested by running the visualization pipeline and verifying that ≥3 plots are generated with significance markers, plus a sensitivity plot for the keyword threshold.

### Implementation for User Story 3

- [ ] T043 [US3] Implement Sensitivity Analysis loop (Thresholds {, 2, 3}) in `code/analysis/viz.py` (FR-007)
- [ ] T044 [US3] Generate Boxplots for Comment Count and Sentiment with significance markers in `code/analysis/viz.py` (FR-006)
- [ ] T045 [US3] Generate Survival Curve (Kaplan-Meier) for Merge Latency in `code/analysis/viz.py` (FR-006)
- [ ] T046 [US3] Generate Sensitivity Plot (Classification rate vs Threshold) in `code/analysis/viz.py` (FR-006)
- [ ] T047 [US3] Compile HTML report with "Associational Only" disclaimer and all findings (FR-009)
- [ ] T048 [US3] Save all figures and `reports/sensitivity_results.csv`

### Tests for User Story 3 ⚠️

- [ ] T039 [P] [US3] Unit test for sensitivity analysis plotting in `tests/unit/test_viz.py`
- [ ] T040 [P] [US3] Unit test for correlation diagnostic logic in `tests/unit/test_correlation.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T049 [P] Documentation updates in `docs/` and `README.md`
- [ ] T050a [P] Refactor `code/analysis/stats.py` to reduce cyclomatic complexity < 10 (Run `radon cc` on `code/analysis/stats.py` and refactor until max CC < 10)
- [ ] T050b [P] Remove unused imports and dead code in `code/`
- [ ] T051 [P] Run `quickstart.md` validation
- [ ] T052 [P] Final integration test run on CPU-only environment (limited core count, constrained RAM, 6h limit) (FR-012)

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
- Models/Download before Metrics
- Metrics before Labeling
- Labeling before Audit/PSM
- PSM before Statistical Testing
- Testing before Visualization
- **CRITICAL**: Correlation Diagnostic (T041/T042) MUST run BEFORE Statistical Testing (T032/T033) to enforce flagging logic.

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Unit test for download schema validation in tests/unit/test_download.py"
Task: "Unit test for keyword classification logic in tests/unit/test_classify.py"
Task: "Unit test for audit sampling and accuracy calculation in tests/unit/test_audit.py"

# Launch all models for User Story 1 together:
Task: "Implement code complexity metrics in code/data/metrics.py"
Task: "Implement Sentiment Score calculation in code/data/metrics.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Data, Metrics, Labeling, Audit)
4. **STOP and VALIDATE**: Test User Story 1 independently (Ensure ≥70% heuristic accuracy, ≥500 samples per group)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently (PSM, Cox PH, SIMEX) → Deploy/Demo
4. Add User Story 3 → Test independently (Viz, Report) → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Data pipeline, Metrics, Audit)
   - Developer B: User Story 2 (Stats, PSM, SIMEX)
   - Developer C: User Story 3 (Viz, Reporting)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **Critical Constraint**: All analysis must complete within 6 hours on 2 CPU cores, 7 GB RAM. Avoid loading full datasets into memory if necessary; use chunking or sampling.
- **Data Integrity**: Never fabricate data. Use real HuggingFace dataset `numenta/prs-v2-sample`.
- **Heuristic Validation**: FR-015 is a hard gate; if audit accuracy <70%, the pipeline must halt.
- **Sentiment Handling**: FR-016/SC-002 mandate flagging and reporting with a caveat if correlation > 0.5, NOT exclusion. T042 implements this flagging logic.
- **Ground Truth**: T012b generates `data/raw/audit_ground_truth.csv` for CI validation.
- **Note on Spec/Plan Conflict**: The Plan (Phase 3.5) explicitly rejects the Spec's (FR-016) exclusion logic in favor of flagging. Tasks follow the Plan.