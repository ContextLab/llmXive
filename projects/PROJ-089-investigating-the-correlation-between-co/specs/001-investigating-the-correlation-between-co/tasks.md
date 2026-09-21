# Tasks: Investigating the Correlation Between Code Churn and Technical Debt

**Input**: Design documents from `/specs/001-code-churn-technical-debt/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), data-model.md, contracts/
**Note**: `research.md` is listed in the original plan but is out of scope for this iteration.

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

## Phase 0: Spec Verification (PREREQUISITE - MUST COMPLETE FIRST)

**Purpose**: Identify contradictions between `spec.md` and `plan.md`. The Spec mandates **raw metrics** and **Semgrep**, while the Plan's Summary claims the Spec mandates **density metrics** and **SonarQube**. This phase logs the contradiction as a `CRITICAL_DEVIATION` requiring a kickback to amend the Constitution/Plan before implementation proceeds.

**⚠️ CRITICAL**: No implementation tasks (Phase 1+) can begin until Phase 0 is complete.

- [ ] T000a [US1] **Read Artifacts**: Read `spec.md` and `plan.md`. Identify the contradiction: Spec (Methodological Correction) mandates raw metrics/Semgrep; Plan (Summary/Next Steps) claims Spec mandates density metrics/SonarQube. <!-- FAILED: unspecified -->
- [X] T000b [US1] **Log Deviation**: Write a log entry to `data/logs/spec_verification.log`. **Format**: `TIMESTAMP | CRITICAL_DEVIATION | Spec mandates Raw/Semgrep, Plan mandates Density/SonarQube | ACTION: KICKBACK_REQUIRED`. Do NOT claim alignment.

**Checkpoint**: Contradiction logged. Implementation proceeds with the understanding that the Plan's narrative is currently incorrect and requires a kickback.

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
- [ ] T007b [P] **Skeleton & Timeout**: Create `main.py` with function stubs (`run_extraction`, `run_analysis`, `run_reporting`, `main`). Implement 6-hour timeout logic using `signal` or `threading`. **Deliverable**: `main.py` raises `TimeoutError` if execution exceeds 6 hours. **Log**: Total execution time to `data/logs/pipeline.log` with format `TOTAL_TIME: {duration}s`.
- [ ] T007c [P] **Error Handling**: Implement error handling wrapper in `main.py` to catch exceptions, log them to `data/logs/pipeline.log`, and continue to the next repo if one fails. **Deliverable**: `main.py` continues execution after a repo failure.
- [ ] T007d [P] **Orchestration**: Implement pipeline orchestration in `main.py` to call `run_extraction`, `run_analysis`, `run_reporting` sequentially. **Deliverable**: `main.py` runs the full pipeline end-to-end on mock data.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Automatically select repositories, clone them, extract git history and static analysis metrics, and produce a unified CSV with **raw** metrics (total_lines_changed, debt_score) and `avg_loc` as a covariate.

**Independent Test**: Run the pipeline on 3 fixed public repos; verify `data/processed/unified_metrics.csv` contains non-null rows for `total_lines_changed`, `debt_score`, `avg_loc`, and `contributor_count` for every file, and that `tool_validation_log.csv` records star counts and validation status.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T008 [P] [US1] Contract test for `unified_metrics.csv` schema in `tests/contract/test_dataset_schema.py`
- [X] T009 [P] [US1] Integration test for repo cloning and filtering in `tests/integration/test_data_extraction.py`

### Implementation for User Story 1

- [ ] T010 [P] [US1] **Repo Selection**: Implement `data_extraction.py`. **Action**: Query GitHub API (`/search/repositories`) for Python, Java, JS/TS, Go, Rust repos with `stars:>500` and `pushed:>2years ago`. Filter by language. **Deliverable**: `data/raw/repos_metadata.csv` with columns: `repo_id`, `owner`, `name`, `language`, `stars`, `pushed_at`.
- [ ] T010a [US1] **Data Source Verification**: Implement `data_extraction.py`. **Action**: Verify `is_public` status for each repo selected in T010. **Deliverable**: Update `data/raw/repos_metadata.csv` with a `is_public` column (True/False). Filter out non-public repos.
- [ ] T011 [P] [US1] **Git History**: Implement `data_extraction.py`. **Action**: Clone each repo from T010. Use `pydriller` to extract per-file commit counts and lines changed (additions + deletions) for the last 12 months. **Deliverable**: `data/raw/git_history/{repo_id}/commits.csv` with columns: `file_path`, `total_lines_changed`, `commit_count`.
- [X] T013a [P] [US1] **Tool Validation**: Implement `utils.py`. **Action**: Validate tool availability (Radon, Semgrep). Log star counts/citation presence in `data/logs/tool_validation_log.csv` (Depends on T005).
- [ ] T013b [US1] **Tool Validation Logic**: Implement `utils.py` to verify tool validity per SC-005. **Action**: Call GitHub API `/repos/{owner}/{repo}` to fetch star count. If stars > 5000, log "PASS". Else, search `data/logs/citations.csv` for a matching paper title. If neither, log "FAIL". **Deviation Note**: This simplified check does not satisfy Constitution Principle II (Reference-Validator Agent) but is required by Spec SC-005. Log as `DEVIATION: Principle II`. **Deliverable**: `data/logs/tool_validation_log.csv`.
- [ ] T014 [US1] **Static Analysis**: Implement `static_analysis.py`. **Action**: Run `radon==2.4.0` on Python files (CC, MI). Run `semgrep==1.30.0` on Java, JS, TS, Go, Rust files with `--config=p/security-audit` and `--config=auto`. **Calculation**: Python `debt_score` = Sum(CC) + (100-MI). Others `debt_score` = Sum(Code Smells + CC). **Deviation Note**: This uses Semgrep, violating Constitution Principle VII (SonarQube/CodeClimate). Log as `DEVIATION: Principle VII`. **Deliverable**: `data/raw/static_analysis/{repo_id}/semgrep_results.json` with per-file scores.
- [ ] T015a [US1] **Filtering**: Implement `preprocessing.py`. **Action**: Filter non-source-code files from T011 and T014 outputs. **Input**: `data/raw/git_history/*/commits.csv` and `data/raw/static_analysis/*/semgrep_results.json`. **Output**: `data/processed/filtered_metrics.csv`.
- [ ] T015b [US1] **Threshold 5**: Implement `preprocessing.py`. **Action**: Filter `filtered_metrics.csv` for `avg_loc >= 5`. **Output**: `data/processed/unified_metrics_loc5.csv`.
- [ ] T015c [US1] **Threshold 10**: Implement `preprocessing.py`. **Action**: Filter `filtered_metrics.csv` for `avg_loc >= 10`. **Output**: `data/processed/unified_metrics_loc10.csv`.
- [ ] T015d [US1] **Threshold 20**: Implement `preprocessing.py`. **Action**: Filter `filtered_metrics.csv` for `avg_loc >= 20`. **Output**: `data/processed/unified_metrics_loc20.csv`. **Deviation Note**: This produces raw metrics, violating Constitution Principle VI (Density Metrics). Log as `DEVIATION: Principle VI`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Correlation Analysis (Priority: P2)

**Goal**: Calculate correlation between **raw** churn and **raw** debt, controlling for `avg_loc` and other confounders, and perform sensitivity analysis.

**Independent Test**: Feed the pipeline a synthetic CSV with known correlation; verify output reports `r` within ±0.05 and `p < 0.05`, and that VIF warnings trigger Ridge regression if collinearity is high.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T016 [P] [US2] Contract test for `correlation_results.csv` schema in `tests/contract/test_output_schema.py`
- [X] T017 [P] [US2] Integration test for mixed-effects model execution in `tests/integration/test_analysis.py`

### Implementation for User Story 2

- [ ] T018 [US2] **VIF Check**: Implement `analysis.py`. **Action**: Load `unified_metrics.csv`. Use `statsmodels.stats.outliers_influence.variance_inflation_factor` on covariates: `project_age`, `language`, `contributor_count`. If any VIF > 5, log warning. **Deliverable**: `data/results/vif_report.csv` with columns: `covariate_name`, `vif_value`, `status`.
- [ ] T019a [US2] **Model Definition**: Implement `analysis.py`. **Action**: Define the Mixed-Effects Model formula exactly as per FR-006: `'debt_score ~ total_lines_changed + avg_loc + C(project_age) + C(language) + contributor_count + (1|repo_id)'`. **Deliverable**: String constant in `analysis.py`.
- [ ] T019b [US2] **Model Execution**: Implement `analysis.py`. **Action**: Fit mixed-effects model using `statsmodels.regression.mixed_linear_model.MixedLM` using the formula from T019a. Handle categorical variables via one-hot encoding. **Deliverable**: `data/results/model_summary.csv` with model coefficients and p-values.
- [ ] T020 [US2] **Correlation**: Implement `analysis.py`. **Action**: Calculate Pearson and Spearman correlation coefficients on **raw** `total_lines_changed` vs `debt_score`. Control for `avg_loc` using `pingouin.partial_corr` (X=churn, Y=debt, covariates=[avg_loc]). **Deliverable**: `data/results/correlation_results.csv` with columns: `metric_type`, `r_value`, `p_value`, `n`, `threshold`.
- [ ] T021 [US2] **Meta-Analysis**: Implement `analysis.py`. **Action**:
 1. Load `r` values from `correlation_results.csv` (metric_type=pearson).
 2. Compute Fisher's Z: `z = 0.5 * np.log((1 + r) / (1 - r))`.
 3. Compute SE: `se = 1 / np.sqrt(n - 3)`.
 4. Inverse-variance weighted meta-analysis: `z_combined = np.sum(z / se**2) / np.sum(1 / se**2)`.
 5. Convert back to r: `r_combined = (np.exp(2 * z_combined) - 1) / (np.exp(2 * z_combined) + 1)`.
 6. Calculate p-value for `z_combined`.
 **Deliverable**: `data/results/meta_analysis_results.csv` with columns: `method`, `combined_r`, `combined_se`, `p_value`, `k_studies`.
- [ ] T022 [US2] **Sensitivity Analysis**: Implement `analysis.py`. **Action**: Re-run the model (T019b-T020) with datasets filtered by `avg_loc` thresholds **5, 10, 20**. **Deliverable**: `data/results/sensitivity_analysis.csv` with columns: `threshold`, `r_value`, `p_value`, `n`.
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

- [ ] T026 [US3] **Plots**: Implement `visualization.py`. **Action**: Generate scatter plots using `matplotlib.pyplot`. X-axis: `total_lines_changed`, Y-axis: `debt_score`. Overlay regression line. **Deliverable**: `data/results/plots/repo_{id}_scatter.png` (size=(10, 6), dpi=300).
- [ ] T027 [US3] **Annotation**: Implement `visualization.py`. **Action**: Annotate plots with correlation coefficient (`r`) and p-value formatted as `r = {r:.3f}, p = {p:.4f}`. **Deliverable**: Annotated PNGs in `data/results/plots/`.
- [ ] T028a [US3] **Report Data**: Implement `reporting.py`. **Action**: Generate table data for `summary_report.txt`. **Format**: Markdown table with columns: `repo_id`, `r`, `p`, `significance`. **Logic**: Flag `|r| >= 0.3` as 'moderate'.
- [ ] T028b [US3] **Report File**: Implement `reporting.py`. **Action**: Write `data/results/summary_report.txt` using the data from T028a. Include Meta-analysis outcome and sensitivity analysis table.
- [ ] T031 [P] [US3] **Versioning**: Implement `main.py`. **Action**: Finalize pipeline by computing checksums and updating `state/projects/...yaml` (Phase 7).

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T032a [P] **Quickstart Install**: Update `quickstart.md` with installation steps for Semgrep and dependencies.
- [ ] T032b [P] **Quickstart Exec**: Update `quickstart.md` with execution command and expected output.
- [ ] T033b [P] **Streaming & Memory**: Refactor `preprocessing.py` to implement streaming iterator for large files. **Success Criteria**: Peak memory usage < 2GB as measured by `utils.py` memory monitor.
- [ ] T034a [P] **Batch Logic**: Define batch processing logic for git history extraction in `data_extraction.py`. **Params**: Batch size = 100 repos; Trigger = RAM > 5GB.
- [ ] T034b [P] **Batch Implement**: Implement batch loop in `data_extraction.py` using logic from T034a.
- [ ] T035 [P] Additional unit tests in `tests/unit/` for metric calculation logic
- [ ] T036 Run `quickstart.md` validation to ensure end-to-end reproducibility

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 0 (Spec Verification)**: No dependencies - MUST be first.
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
**Note**: T013b depends on T010 (Repo Selection). T014 depends on T011 and T013a. T015 depends on T014. These are NOT parallel.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 0: Spec Verification
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
- **Critical**: The tasks now explicitly calculate **raw metrics** (`total_lines_changed`, `debt_score`) as mandated by the Spec's Methodological Correction to avoid spurious correlation, with `avg_loc` as a covariate.
- **Correction**: Replaced SonarQube (infeasible on CI) with Semgrep (v1.30.0) for multi-language static analysis to ensure CPU-only feasibility. The Spec already mandates this.
- **Correction**: Replaced Bonferroni correction with Meta-analysis of Fisher-transformed r coefficients as per Spec FR-006.
- **Correction**: Sensitivity analysis thresholds strictly limited to 5, 10, 20 as per Spec FR-008.
- **Correction**: Tool validation is a "presence check" only as per Spec SC-005.
- **Deviation Note**: This implementation plan explicitly overrides Constitution Principle VI (Density Metrics) and Principle VII (SonarQube) as per the Spec's Methodological Correction. This is logged as a `CRITICAL_DEVIATION` in Phase 0, pending a formal kickback to amend the Constitution.
- **Deviation Note**: T013b uses a simplified citation check (local file) which does not satisfy the full Reference-Validator Agent requirement of Constitution Principle II. This is logged as a `DEVIATION`.
- **Note**: The Plan's Summary and Next Steps sections contain contradictions regarding the Spec (claiming it mandates density metrics/SonarQube). The tasks strictly follow the **Spec** (which mandates raw metrics/Semgrep). The Plan requires a kickback to align its narrative with the Spec.