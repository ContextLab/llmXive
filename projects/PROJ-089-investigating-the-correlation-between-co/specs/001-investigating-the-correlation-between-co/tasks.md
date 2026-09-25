---
description: "Task list for feature implementation: Investigating the Correlation Between Code Churn and Technical Debt"
---

# Tasks: Investigating the Correlation Between Code Churn and Technical Debt

**Input**: Design documents from `/specs/089-code-churn-debt/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/
**Note**: `research.md` is listed in the original plan but is out of scope for this iteration.

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root (per plan.md structure)
- **Data**: `data/raw/`, `data/processed/`, `data/results/`, `data/logs/`
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

**Purpose**: Verify alignment between `spec.md` and `plan.md`. The Spec's "Methodological Correction" explicitly mandates **raw metrics** and **Semgrep**, and the Plan's "Methodological Correction" section correctly implements this. This phase confirms alignment and unblocks the pipeline.

**⚠️ CRITICAL**: No implementation tasks (Phase 1+) can begin until Phase 0 is complete.

- [ ] T000a [US1] **Verify Alignment**: Read `spec.md` and `plan.md`. Confirm that the Spec's "Methodological Correction" (Raw Metrics/Semgrep) is correctly implemented in the Plan. **Action**: The Spec (FR-001, FR-002) explicitly mandates raw metrics and Semgrep. The Plan's "Methodological Correction" section contains a contradiction claiming to use "Log-Log Linear Model" and "Density Metrics". **Deliverable**: Log entry to `data/logs/spec_verification.log`. **Format**: `TIMESTAMP | ALIGNMENT_VERIFIED | Spec mandates Raw/Semgrep, Plan contradicts with Log-Log | ACTION: FLAG_PLAN_FOR_KICKBACK`.

**Checkpoint**: Alignment verified. Implementation proceeds.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 [P] Create project root directories: `code/`, `data/`, `tests/`, `contracts/` and subdirectories `data/raw/`, `data/processed/`, `data/results/`, `data/logs/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002 [P] Create schema definitions in `contracts/` (`dataset.schema.yaml`, `output.schema.yaml`, `tool_validation_log.schema.yaml`)
- [X] T003 [P] Initialize Python 3.11 project with pinned dependencies in `code/requirements.txt` (pandas, numpy, scipy, statsmodels, scikit-learn, matplotlib, seaborn, pydriller, semgrep, tqdm, requests, pyyaml)
- [X] T004 [P] Configure linting (ruff) and formatting (black) tools
- [X] T005 [P] Implement `code/config.py` with parameter defaults (LOC thresholds: small, medium, and large.

The research question is: How does code complexity, as measured by Lines of Code (LOC), affect the frequency of software vulnerabilities? The method is: We will analyze a dataset of open-source software projects to identify correlations between LOC and vulnerability reports. (Wheeler, 2015) (arXiv:1808.00001); repo limits, tool versions)
- [X] T006 [P] Implement `code/utils.py` for logging, checksum utilities, and random seed pinning
- [ ] T013 [P] **Tool Validation**: Implement `code/utils.py` to verify tool availability and validity per Spec SC-005. **Action**: Check if `semgrep==1.30.0` is installed. Fetch GitHub star count for Semgrep via API. If stars > 5000, log "PASS". **Note**: Spec SC-005 requires tool validation via star count > 5000. Only Semgrep is validated. **Deliverable**: `data/logs/tool_validation_log.csv` with columns: `tool_name`, `version`, `stars`, `status`. **Depends on**: T005.
- [ ] T007b [P] **Skeleton & Timeout**: Create `code/main.py` with function stubs. **Action**: Implement `def run_extraction(...) -> pd.DataFrame`, `def run_analysis(...) -> dict`, `def run_reporting(...) -> None`. Implement a configurable timeout logic using `threading.Timer` as cross-platform fallback, with `signal` used only if `sys.platform == 'linux'`. **Deliverable**: `code/main.py` raises `TimeoutError` if execution exceeds 6 hours. **Log**: Total execution time to `data/logs/pipeline.log` with format `TOTAL_TIME: {duration}s`.
- [ ] T007c [P] **Error Handling**: Implement error handling wrapper in `code/main.py`. **Action**: Wrap repo processing in `try/except` blocks. Log exceptions to `data/logs/pipeline.log` with format `ERROR: {repo_id}: {message}`. **Deliverable**: `code/main.py` continues execution after a repo failure.
- [ ] T007d [P] **Orchestration**: Implement pipeline orchestration in `code/main.py`. **Action**: Call `run_extraction`, `run_analysis`, `run_reporting` sequentially. **Deliverable**: `code/main.py` runs the full pipeline end-to-end on mock data.

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

- [ ] T010 [P] [US1] **Repo Selection**: Implement `code/data_extraction.py`. **Action**: Load the PINNED list of repositories. **Definition**: The list is hardcoded in `code/data_extraction.py` as a constant `PINNED_REPOS` containing a diverse set of public GitHub repos (Python, Java, JS/TS, Go, Rust) selected for diversity and activity. Do NOT query the GitHub API for selection. **Deliverable**: `data/raw/repos_metadata.csv` (created from `PINNED_REPOS` constant) and load it into memory. **Format**: `repo_id`, `owner`, `name`, `language`, `url`.
- [ ] T011 [P] [US1] **Git History**: Implement `code/data_extraction.py`. **Action**: Clone each repo from T010. Use `pydriller` to extract per-file commit counts and lines changed (additions + deletions) for the last 12 months. **Deliverable**: `data/raw/git_history/{repo_id}/commits.csv` with columns: `file_path`, `total_lines_changed`, `commit_count`.
- [ ] T014 [US1] **Static Analysis**: Implement `code/static_analysis.py`. **Action**: Run `semgrep==1.30.0` on ALL files (Python, Java, JS, TS, Go, Rust). **Calculation**: 
  - For Python: `debt_score` = Sum(Cyclomatic Complexity from Semgrep) + (Maximum Maintainability Index - Maintainability Index). **Note**: If Semgrep does not provide MI, calculate MI using a pure Python implementation of the formula (Sum(Cyclomatic Complexity) / Lines of Code) or default to 50, then combine with Semgrep CC. **Do NOT use Radon**.
  - For Others: `debt_score` = Sum(Code Smells + Cyclomatic Complexity) as reported by Semgrep.
  - **Deliverable**: `data/raw/static_analysis/{repo_id}/semgrep_results.json` with per-file scores. **Depends on**: T010, T011, T013.
- [ ] T015a [US1] **Filtering**: Implement `code/preprocessing.py`. **Action**: Filter non-source-code files from T011 and T014 outputs. **Input**: `data/raw/git_history/*/commits.csv` and `data/raw/static_analysis/*/semgrep_results.json`. **Output**: `data/processed/unified_metrics.csv`.
- [ ] T015b [US1] **Sensitivity Analysis Prep**: Implement `code/analysis.py` (pre-analysis step). **Action**: Load `unified_metrics.csv`. Filter for `avg_loc >= 5`, `avg_loc >= 10`, and `avg_loc >= 20`. **Action**: Save each filtered subset to a persistent CSV file. **Deliverable**: `data/processed/unified_metrics_loc5.csv`, `data/processed/unified_metrics_loc10.csv`, `data/processed/unified_metrics_loc20.csv`. **Note**: These files are required for reproducibility (Constitution Principle I). **Depends on**: T015a.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Correlation Analysis (Priority: P2)

**Goal**: Calculate correlation between **raw** churn and **raw** debt, controlling for `avg_loc` and other confounders, and perform sensitivity analysis.

**Independent Test**: Feed the pipeline a synthetic CSV with known correlation; verify output reports `r` within ±0.05 and `p < 0.05`, and that VIF warnings trigger Ridge regression if collinearity is high.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T016 [P] [US2] Contract test for `correlation_results.csv` schema in `tests/contract/test_output_schema.py`
- [X] T017 [P] [US2] Integration test for mixed-effects model execution in `tests/integration/test_analysis.py`

### Implementation for User Story 2

- [ ] T018 [US2] **VIF Check**: Implement `code/analysis.py`. **Action**: Load `unified_metrics.csv`. Use `statsmodels.stats.outliers_influence.variance_inflation_factor` on covariates: `project_age`, `language`, `contributor_count`. If any VIF > 5, log warning. **Deliverable**: `data/results/vif_report.csv` with columns: `covariate_name`, `vif_value`, `status`.
- [ ] T020 [US2] **Correlation**: Implement `code/analysis.py`. **Action**: Calculate Pearson and Spearman correlation coefficients on **raw** `total_lines_changed` vs `debt_score`. Control for `avg_loc` using `pingouin.partial_corr` (X=churn, Y=debt, covariates=[avg_loc]). **Deliverable**: `data/results/correlation_results.csv` with columns: `metric_type`, `r_value`, `p_value`, `n`, `threshold`. **Depends on**: T015a (for base data).
- [ ] T021 [US2] **Meta-Analysis**: Implement `code/analysis.py`. **Action**:
 1. Load `r` values from `correlation_results.csv` (metric_type=pearson).
 2. Compute Fisher's Z: `z = 0.5 * np.log((1 + r) / (1 - r))`.
 3. Compute SE: `se = 1 / np.sqrt(n - 3)`.
 4. Inverse-variance weighted meta-analysis: `z_combined = np.sum(z / se**2) / np.sum(1 / se**2)`.
 5. Convert back to r: `r_combined = (np.exp(2 * z_combined) - 1) / (np.exp(2 * z_combined) + 1)`.
 6. Calculate p-value for `z_combined`.
 **Deliverable**: `data/results/meta_analysis_results.csv` with columns: `method`, `combined_r`, `combined_se`, `p_value`, `k_studies`. **Depends on**: T020.
- [ ] T022 [US2] **Sensitivity Analysis Aggregation**: Implement `code/analysis.py`. **Action**: Load `unified_metrics_loc5.csv`, `unified_metrics_loc10.csv`, `unified_metrics_loc20.csv`. Compute correlation statistics for each. **Deliverable**: Finalized `data/results/sensitivity_analysis.csv` with columns: `threshold`, `r_value`, `p_value`, `n`. **Depends on**: T015b.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualization and Reporting (Priority: P3)

**Goal**: Generate scatter plots with regression lines and a summary report.

**Independent Test**: Run the reporting module on sample data; verify `data/results/plots/` contains PNGs with annotated `r` and `p` values, and `summary_report.txt` exists.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T024 [P] [US3] Contract test for `summary_report.txt` content in `tests/contract/test_report_schema.py`
- [X] T025 [P] [US3] Integration test for plot generation in `tests/integration/test_visualization.py`

### Implementation for User Story 3

- [ ] T026 [US3] **Plots**: Implement `code/visualization.py`. **Action**: Generate scatter plots using `matplotlib.pyplot`. X-axis: `total_lines_changed`, Y-axis: `debt_score`. Overlay regression line. **Deliverable**: `data/results/plots/repo_{id}_scatter.png` (size=(10, 6), dpi=300).
- [ ] T027 [US3] **Annotation**: Implement `code/visualization.py`. **Action**: Annotate plots with correlation coefficient (`r`) and p-value formatted as `r = {r:.3f}, p = {p:.4f}`. **Deliverable**: Annotated PNGs in `data/results/plots/`.
- [ ] T028a [US3] **Report Data**: Implement `code/reporting.py`. **Action**: Generate table data for `summary_report.txt`. **Format**: Markdown table with columns: `repo_id`, `r`, `p`, `significance`. **Logic**: Flag `|r| >= 0.3` as 'moderate'.
- [ ] T028c [US3] **Report Formatting**: Implement `code/reporting.py`. **Action**: Read `correlation_results.csv`, `meta_analysis_results.csv`, and `sensitivity_analysis.csv`. Format data into a structured text report. **Deliverable**: Intermediate formatted string or dict for `summary_report.txt`.
- [ ] T028b [US3] **Report File**: Implement `code/reporting.py`. **Action**: Read `meta_analysis_results.csv` (from T021) and `sensitivity_analysis.csv` (from T022). Combine with `correlation_results.csv` (from T020) to write `data/results/summary_report.txt`. **Depends on**: T020, T021, T022, T028c. **Deliverable**: `data/results/summary_report.txt`.
- [ ] T031 [P] [US3] **Versioning**: Implement `code/main.py`. **Action**: Finalize pipeline by computing checksums and updating `state/projects/...yaml` (Phase 7). **Action**: Write checksums to `artifact_hashes` key and update `updated_at` timestamp. **Depends on**: T028b.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T032a [P] **Quickstart Install**: Update `quickstart.md` with installation steps for Semgrep and dependencies.
- [ ] T032b [P] **Quickstart Exec**: Update `quickstart.md` with execution command and expected output.
- [ ] T033b [P] **Streaming & Memory**: Refactor `code/preprocessing.py` to implement streaming iterator for large files. **Action**: Replace `pandas.read_csv` with `pd.read_csv(..., chunksize=1000)` and use a generator to accumulate statistics. **Success Criteria**: Peak memory usage < 2GB as measured by `code/utils.py` memory monitor.
- [ ] T034a [P] **Batch Logic**: Define batch processing logic for git history extraction in `code/data_extraction.py`. **Action**: Use `queue.Queue` with `maxsize=100`. **Params**: Batch size = 100 repos; Trigger = RAM > 5GB.
- [ ] T034b [P] **Batch Implement**: Implement batch loop in `code/data_extraction.py` using logic from T034a. **Action**: Use `queue.Queue` to manage repo processing.
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
- Data Extraction (T010-T011) before Static Analysis (T014)
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
Task: "Load pinned repo list" (T010)
Task: "Clone repos" (T011)
```
**Note**: T014 depends on T010, T011, and T013. T015 depends on T014. These are NOT parallel.

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
- **Correction**: Sensitivity analysis thresholds strictly limited to 5, 10, 20 as per Spec FR-008. Analysis is performed on persistent intermediate files to satisfy Constitution Principle I.
- **Correction**: Tool validation is a "presence check" only (GitHub stars > 5000) as per Spec SC-005, superseding the general Constitution Principle II for this project.
- **Note**: The Plan's Summary and Next Steps sections contain contradictions regarding the Spec (claiming it mandates density metrics/SonarQube). The tasks strictly follow the **Spec** (which mandates raw metrics/Semgrep). The Plan requires a kickback to align its narrative with the Spec.