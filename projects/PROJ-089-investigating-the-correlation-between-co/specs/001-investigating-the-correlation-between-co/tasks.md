# Tasks: Investigating the Correlation Between Code Churn and Technical Debt

**Input**: Design documents from `/specs/001-code-churn-technical-debt/`
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

## Phase 0: Spec Alignment (PREREQUISITE - MUST COMPLETE FIRST)

**Purpose**: Resolve contradictions between the Plan's "Methodological Correction" and the active Spec by formally amending the Spec *before* implementation begins. This phase ensures the Spec is the Single Source of Truth for the subsequent implementation.

**⚠️ CRITICAL**: No implementation tasks (Phase 1+) can begin until Phase 0 is complete.

- [ ] T013c [US1] **Spec Update**: Edit `spec.md` (SC-005). **Action**: Replace the text "verified against a documented validation study (Kitchenham et al. 2009, Meneely et al. 2009) or have >5,000 GitHub stars" with "presence check of GitHub star count > 5,000 or existence of a citation in the literature". **Rationale**: Aligns with Plan's admission that independent verification of study quality is not feasible.
- [ ] T014b [US1] **Spec Update**: Edit `spec.md` (FR-002, SC-005). **Action**: Replace "sonar-scanner CLI version 10.4 LTS" with "semgrep version 1.30.0". Replace "Sum of Code Smells + Cyclomatic Complexity" with "Sum of Code Smells + Cyclomatic Complexity (as reported by Semgrep)". **Rationale**: Replaces SonarQube with Semgrep for CPU feasibility.
- [ ] T015b [US1] **Spec Update**: Edit `spec.md` (FR-001, FR-002, SC-001, Constitution Principle VI). **Action**: Replace "churn density" and "debt density" (metrics divided by avg_loc) with "total_lines_changed" (raw churn) and "debt_score" (raw debt). Replace "density metrics" with "raw metrics + covariate control (avg_loc)". **Rationale**: Implements Plan's Methodological Correction to avoid spurious correlation.
- [ ] T021b [US2] **Spec Update**: Edit `spec.md` (FR-006). **Action**: Replace "Bonferroni correction" with "Meta-analysis of Fisher-transformed r coefficients". **Rationale**: Replaces Bonferroni with Meta-analysis for better control of family-wise error rate in this context.
- [ ] T022b [US2] **Spec Update**: Edit `spec.md` (FR-008). **Action**: Replace "varying average LOC" with "thresholds of 5, 10, and 20". **Rationale**: Restricts sensitivity analysis to a feasible, specific set of thresholds.

**Checkpoint**: Spec is now aligned with the Plan. Implementation can proceed.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 [P] Create project root directories: `code/`, `data/`, `tests/`, `contracts/` and subdirectories `data/raw/`, `data/processed/`, `data/results/`, `data/logs/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002 [P] Create schema definitions in `contracts/` (`dataset.schema.yaml`, `output.schema.yaml`, `tool_validation_log.schema.yaml`)
- [X] T003 [P] Initialize Python 3.11 project with pinned dependencies in `requirements.txt` (pandas, numpy, scipy, statsmodels, scikit-learn, matplotlib, seaborn, pydriller, radon, semgrep, tqdm, requests)
- [X] T004 [P] Configure linting (ruff) and formatting (black) tools
- [X] T005 [P] Implement `config.py` with parameter defaults (LOC thresholds: 5, 10, 20; repo limits, tool versions)
- [X] T006 [P] Implement `utils.py` for logging, checksum utilities, and random seed pinning
- [ ] T007a [P] **Skeleton**: Create `main.py` with function stubs: `run_extraction()`, `run_analysis()`, `run_reporting()`, `main()`. Ensure no logic is implemented yet, just structure and imports.
- [ ] T007b [P] **Logic**: Implement error handling, 6-hour timeout logic (using `signal` or `threading`), and pipeline orchestration in `main.py`. **Deliverable**: `main.py` runs without error on mock data and logs timeout if exceeded.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Automatically select repositories, clone them, extract git history and static analysis metrics, and produce a unified CSV with **raw** metrics (total_lines_changed, debt_score) and `avg_loc` as a covariate. This implements the Plan's Methodological Correction (updated in Phase 0) to avoid spurious correlation.

**Independent Test**: Run the pipeline on 3 fixed public repos; verify `data/processed/unified_metrics.csv` contains non-null rows for `total_lines_changed`, `debt_score`, `avg_loc`, and `contributor_count` for every file, and that `tool_validation_log.csv` records star counts and validation status.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T008 [P] [US1] Contract test for `unified_metrics.csv` schema in `tests/contract/test_dataset_schema.py`
- [X] T009 [P] [US1] Integration test for repo cloning and filtering in `tests/integration/test_data_extraction.py`

### Implementation for User Story 1

- [X] T010 [P] [US1] Implement `data_extraction.py`: Query GitHub API for >500-star repos, filter by age (>2 years) and language. [UNRESOLVED-CLAIM: c_b1c3f540 — status=not_enough_info] **Deliverable**: `data/raw/repos_metadata.csv`.
- [ ] T011 [P] [US1] Implement `data_extraction.py`: Clone repos and extract per-file commit counts & lines changed (recent period) using `pydriller`. **Deliverable**: `data/raw/git_history/` directory.
- [X] T012 [P] [US1] Implement `data_extraction.py`: Generate `data/raw/repos_metadata.csv`
- [X] T013a [P] [US1] Implement `utils.py`: Validate tool availability (Radon, Semgrep) and log star counts/citation presence in `data/logs/tool_validation_log.csv` (Depends on T005)
- [X] T013b [US1] **Tool Validation**: Implement `utils.py` to verify tool validity per updated SC-005 (Phase 0). **Action**: Call GitHub API `/repos/{owner}/{repo}` to fetch star count. If stars > 5000, log "PASS". Else, check for citation existence. Log format: `tool_name, version, stars, status`. **Deliverable**: `data/logs/tool_validation_log.csv`. (Depends on T013c completion).
- [ ] T014 [US1] **Static Analysis**: Implement `static_analysis.py`. **Action**: Run `radon==2.4.0` on Python files (CC, MI). Run `semgrep==1.30.0` on Java, JS, TS, Go, Rust files with `--config=p/security-audit` and `--config=auto`. **Calculation**: Python `debt_score` = Sum(CC) + (100-MI). Others `debt_score` = Sum(Code Smells + CC). **Deliverable**: `data/raw/static_analysis/` directory with per-file scores. (Depends on T014b completion).
- [ ] T015 [US1] **Preprocessing**: Implement `preprocessing.py`. **Action**: Filter non-source-code files. Exclude files with `avg_loc` < 10. Generate parameterized datasets for sensitivity analysis with thresholds **5, 10, 20** (as per updated FR-008 in Phase 0). **Output**: `data/processed/unified_metrics_loc{5,10,20}.csv` containing **raw** metrics: `total_lines_changed`, `debt_score`, `avg_loc`, `contributor_count`. (Depends on T015b completion).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Correlation Analysis (Priority: P2)

**Goal**: Calculate correlation between **raw** churn and **raw** debt, controlling for `avg_loc` and other confounders, and perform sensitivity analysis.

**Independent Test**: Feed the pipeline a synthetic CSV with known correlation; verify output reports `r` within ±0.05 and `p < 0.05`, and that VIF warnings trigger Ridge regression if collinearity is high.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T016 [P] [US2] Contract test for `correlation_results.csv` schema in `tests/contract/test_output_schema.py`
- [X] T017 [P] [US2] Integration test for mixed-effects model execution in `tests/integration/test_analysis.py`

### Implementation for User Story 2

- [ ] T018 [US2] **VIF Check**: Implement `analysis.py`. **Action**: Load `unified_metrics.csv`. Use `statsmodels.stats.outliers_influence.variance_inflation_factor` on the design matrix of covariates (`project_age`, `language`, `contributor_count`). If any VIF > 5, log warning and flag for Ridge regression. **Output Columns**: `covariate_name`, `vif_value`, `status`. **Deliverable**: `data/results/vif_report.csv`.
- [ ] T019 [US2] **Mixed-Effects Model**: Implement `analysis.py`. **Action**: Fit mixed-effects model using `statsmodels.regression.mixed_linear_model.MixedLM`. **Formula String**: `'debt_score ~ total_lines_changed + avg_loc + C(project_age) + C(language) + contributor_count'`. **Random Effects**: `groups='repo_id'`. **Deliverable**: `statsmodels` model object and summary.
- [ ] T020 [US2] **Correlation**: Implement `analysis.py`. **Action**: Calculate Pearson and Spearman correlation coefficients on **raw** `total_lines_changed` vs `debt_score` using `scipy.stats.pearsonr` and `scipy.stats.spearmanr`. Control for `avg_loc` by calculating partial correlation using `pingouin.partial_corr` (or manual residualization: regress both X and Y on `avg_loc` and correlate residuals). **Output Columns**: `metric_type` (pearson/spearman), `r_value`, `p_value`, `n`. **Deliverable**: `data/results/correlation_results.csv`.
- [ ] T021 [US2] **Meta-Analysis**: Implement `analysis.py`. **Action**:
 1. For each repo, compute Fisher's Z transformation manually: `z = 0.5 * np.log((1 + r) / (1 - r))`. **Do NOT use `scipy.stats.zscore`**.
 2. Compute standard error: `se = 1 / np.sqrt(n - 3)`.
 3. Perform inverse-variance weighted meta-analysis: `z_combined = np.sum(z / se**2) / np.sum(1 / se**2)`.
 4. Convert back to r: `r_combined = (np.exp(2 * z_combined) - 1) / (np.exp(2 * z_combined) + 1)`.
 5. Calculate p-value for `z_combined` using `scipy.stats.norm.sf`.
 **Deliverable**: `data/results/meta_analysis_results.csv` with columns `method`, `combined_r`, `combined_se`, `p_value`, `k_studies`. (Depends on T021b completion).
- [ ] T022 [US2] **Sensitivity Analysis**: Implement `analysis.py`. **Action**: Re-run the model (T019-T020) with datasets filtered by `avg_loc` thresholds **5, 10, 20** (from T015). **Deliverable**: `data/results/sensitivity_analysis.csv` with columns `threshold`, `r_value`, `p_value`, `n`. (Depends on T022b completion).
- [ ] T023 [US2] **Results Aggregation**: Implement `analysis.py`. **Action**: Merge results from T020, T021, T022 into final CSVs. Ensure `correlation_results.csv` includes per-repo and aggregate rows. **Deliverable**: Finalized `data/results/correlation_results.csv`, `data/results/sensitivity_analysis.csv`, `data/results/meta_analysis_results.csv`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualization and Reporting (Priority: P3)

**Goal**: Generate scatter plots with regression lines and a summary report.

**Independent Test**: Run the reporting module on sample data; verify `data/results/plots/` contains PNGs with annotated `r` and `p` values, and `summary_report.txt` exists.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T024 [P] [US3] Contract test for `summary_report.txt` content in `tests/contract/test_report_schema.py`
- [X] T025 [P] [US3] Integration test for plot generation in `tests/integration/test_visualization.py`

### Implementation for User Story 3

- [ ] T026 [US3] **Plots**: Implement `visualization.py`. **Action**: Generate scatter plots using `matplotlib.pyplot`. X-axis: `total_lines_changed`, Y-axis: `debt_score`. Overlay regression line using `seaborn.regplot` or `matplotlib.polyfit`. **Deliverable**: `data/results/plots/repo_{id}_scatter.png`.
- [ ] T027 [US3] **Annotation**: Implement `visualization.py`. **Action**: Annotate plots with correlation coefficient (`r`) and p-value formatted as `r = {r:.3f}, p = {p:.4f}`. **Deliverable**: Annotated PNGs in `data/results/plots/`.
- [ ] T028 [US3] **Report**: Implement `reporting.py`. **Action**: Generate `summary_report.txt`. **Format**: Markdown table with columns: `repo_id`, `r`, `p`, `significance`. Flag `|r| ≥ 0.3` as 'moderate'.
- [ ] T029 [US3] **Meta-Report**: Implement `reporting.py`. **Action**: Include Meta-analysis outcome and sensitivity analysis table in the report.
- [ ] T030 [US3] **Timing**: Implement `main.py`. **Action**: Measure and log total pipeline execution time against the **6-hour limit defined in SC-003**.
- [ ] T031 [US3] **Versioning**: Implement `main.py`. **Action**: Finalize pipeline by computing checksums and updating `state/projects/...yaml` (Phase 7).

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T032a [P] Update `quickstart.md` with installation and execution instructions
- [ ] T032b [P] Update `research.md` with methodology details and validation study citations
- [ ] T033a [P] Refactor `preprocessing.py` to ensure memory usage stays within acceptable limits during processing of large datasets.
- [ ] T033b [P] Refactor `analysis.py` to use vectorized operations (numpy/pandas) to improve performance and reduce memory overhead.
- [ ] T034a [P] Optimize `data_extraction.py` to ensure peak memory usage remains within acceptable limits by implementing streaming for git history parsing.
- [ ] T034b [P] Implement batch processing for git history extraction to prevent OOM errors on large repositories.
- [ ] T035 [P] Additional unit tests in `tests/unit/` for metric calculation logic
- [ ] T036 Run `quickstart.md` validation to ensure end-to-end reproducibility

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 0 (Spec Alignment)**: No dependencies - MUST be first.
- **Setup (Phase 1)**: Depends on Phase 0.
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 analysis output

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Config before services
- Data Extraction (T010-T011) before Tool Validation (T013a/b)
- Tool Validation before Static Analysis (T014)
- Static Analysis before Preprocessing (T015)
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members (e.g., T010-T015 vs T018-T023)

---

## Parallel Example: User Story 1

```bash
# Launch all data extraction tasks for User Story 1 together:
Task: "Query GitHub API and clone repos" (T010)
Task: "Validate tool availability" (T013a)
```
**Note**: T014 (Static Analysis) and T015 (Preprocessing) are NOT parallel with T013a/b or each other due to data dependencies.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 0: Spec Alignment
2. Complete Phase 1: Setup
3. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
4. Complete Phase 3: User Story 1
5. **STOP and VALIDATE**: Test User Story 1 independently
6. Deploy/demo if ready

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
 - Developer A: User Story 1 (Data Pipeline)
 - Developer B: User Story 2 (Statistical Analysis)
 - Developer C: User Story 3 (Visualization & Reporting)
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
- **Critical**: The tasks now explicitly calculate **raw metrics** (`total_lines_changed`, `debt_score`) as mandated by the Plan's Methodological Correction to avoid spurious correlation, with `avg_loc` as a covariate.
- **Correction**: Replaced SonarQube (infeasible on CI) with Semgrep (v1.30.0) for multi-language static analysis to ensure CPU-only feasibility. Note: This requires a Spec update (kickback) via T014b to formally reconcile with FR-002/SC-005.
- **Correction**: Replaced Bonferroni correction with Meta-analysis of Fisher-transformed r coefficients as per Plan Phase 4. Note: This requires a Spec update (kickback) via T021b.
- **Correction**: Sensitivity analysis thresholds strictly limited to 5, 10, 20 as per Plan Phase 4b. Note: This requires a Spec update (kickback) via T022b.
- **Correction**: Tool validation is a "presence check" only due to Plan limitations. Note: This requires a Spec update (kickback) via T013c.