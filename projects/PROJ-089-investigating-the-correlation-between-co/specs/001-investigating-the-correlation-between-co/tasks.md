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
- **[Story]**: Which user story this task belongs to (e.,g., US1, US2, US3)
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

## Phase 0: Spec Verification & Plan Alignment (PREREQUISITE - MUST COMPLETE FIRST)

**Purpose**: Verify alignment between `spec.md` and `plan.md`. The Spec's "Methodological Correction" explicitly mandates **raw metrics** and **Semgrep**, and the Plan's "Methodological Correction" section must correctly implement this by documenting a **Constitution Exception** for Principles VI and VII. This phase confirms the Plan's legal resolution and unblocks the pipeline.

**⚠️ CRITICAL**: No implementation tasks (Phase 1+) can begin until Phase 0 is complete.

- [X] T000a [US1] **Verify Alignment**: Read `spec.md` and `plan.md`. Confirm that the Spec's "Methodological Correction" (Raw Metrics/Semgrep) is correctly implemented in the Plan. **Action**: Verify the existence and content of the "Constitution Check" table in `plan.md`. Confirm that Principles VI and VII are listed as exceptions *resolved by the Spec's mandate*. **Deliverable**: Verification passed. **Note**: If the Plan's exception is missing or contradictory, the task fails; the pipeline cannot proceed.

- [X] T040 [US1] **Plan Narrative Correction**: Update `plan.md` to resolve contradictions. **Action**:
 1. Locate the "Summary" section in `plan.md`.
 2. **Remove** any statement claiming the study uses "Density Metrics" as a primary approach or that the Plan "diverges" from the Spec.
 3. **Replace** with: "This study uses **Raw Metrics** (`total_lines_changed`, `debt_score`) as the primary analysis, with `avg_loc` as a covariate in a Meta-analysis of Fisher-transformed r coefficients, strictly adhering to Spec FR-001 and FR-006."
 4. Ensure the "Methodological Correction" section explicitly states that the Plan **implements** the Spec's Raw Metrics requirement.
 5. Verify the "Constitution Exception" table correctly lists Principles VI and VII as exceptions *resolved by the Spec's mandate*.
 6. **Verification**: Confirm that `plan.md` no longer contains the phrase "Density Metrics" in the Summary or Methodological Correction sections and that the "Log-Log Linear Model" claim is replaced with the Spec's mandated Meta-analysis approach.
 **Deliverable**: Updated `plan.md` with consistent narrative. **Depends on**: T000a.

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
- [X] T003 [P] Initialize Python project with pinned dependencies in `code/requirements.txt` (pandas, numpy, scipy, statsmodels, scikit-learn, matplotlib, seaborn, pydriller, semgrep, tqdm, requests, pyyaml)
- [X] T004 [P] Configure linting (ruff) and formatting (black) tools
- [X] T005 [P] Implement `code/config.py` with parameter defaults (LOC thresholds: 5, 10, 20. Repo limits, tool versions, state file path from Constitution)
- [X] T006 [P] Implement `code/utils.py` for logging, checksum utilities, and random seed pinning
- [X] T013 [US1] **Tool Validation**: Implement `code/utils.py` to verify tool availability and validity per Spec SC-005. **Action**:
 1. **Primary Check**: Attempt to fetch GitHub star count for Semgrep via API. If stars > 5000, log "PASS".
 2. **Secondary Check**: If star check fails, perform a **static verification** against a **hardcoded list of known citations** embedded in the code (e.g., `["Semgrep: Lightweight Static Analysis for Everyone",...]`). If the tool name/version matches an entry in this hardcoded list, log "PASS".
 3. **Fail**: If neither check passes, raise an error. **Note**: The list is hardcoded in `code/utils.py` to ensure determinism; no external file is required.
 **Deliverable**: `data/logs/tool_validation_log.csv` with columns: `tool_name`, `version`, `stars`, `status`. **Depends on**: T005.
- [ ] T007b [P] **Skeleton & Timeout**: Create `code/main.py` with function stubs. **Action**: Implement `def run_extraction(...) -> pd.DataFrame`, `def run_analysis(...) -> dict`, `def run_reporting(...) -> None`. Implement a configurable timeout logic using `threading.Timer` as cross-platform fallback, with `signal` used only if `sys.platform == 'linux'`. **Deliverable**: `code/main.py` raises `TimeoutError` if execution exceeds **6 hours**. **Log**: Total execution time to `data/logs/pipeline.log` with format `TOTAL_TIME: {duration}s`.
- [ ] T007c [P] **Error Handling**: Implement error handling wrapper in `code/main.py`. **Action**: Wrap repo processing in `try/except` blocks. Log exceptions to `data/logs/pipeline.log` with format `ERROR: {repo_id}: {message}`. **Deliverable**: `code/main.py` continues execution after a repo failure.
- [ ] T007d [P] **Orchestration**: Implement pipeline orchestration in `code/main.py`. **Action**: Call `run_extraction`, `run_analysis`, `run_reporting` sequentially. **Deliverable**: `code/main.py` runs the full pipeline end-to-end on mock data.
- [X] T007e [P] **Quickstart Creation**: Create `quickstart.md` in the project root. **Action**: Write initial content including:
 1. **Installation**: Steps to install Python 3.11, Semgrep, and dependencies from `code/requirements.txt`.
 2. **Execution**: Command `python code/main.py` and expected output summary.
 **Deliverable**: `quickstart.md` with the above sections. **Depends on**: T003, T005.
- [ ] T043 [US1] **Timeout Enforcement**: Enhance `code/main.py` to enforce a hard 6-hour timeout across the entire pipeline execution. **Action**:
 1. Implement a global watchdog in `code/main.py` that triggers a `SystemExit` if the total runtime exceeds 360 minutes.
 2. **Linux**: Use `signal` module with `signal.SIGALRM` to set a hard timeout on the main thread.
 3. **Cross-Platform Fallback**: Use `subprocess` to launch the pipeline as a child process with a timeout, or use `os`/`psutil` to monitor the parent process and terminate it if the limit is exceeded.
 4. Log the timeout trigger to `data/logs/pipeline.log` with the message "TIMEOUT: Pipeline exceeded 6-hour limit. Aborting."
 5. Verify that partial results are NOT saved if the timeout is hit, to prevent false positives in downstream analysis.
 **Deliverable**: `code/main.py` with robust global timeout enforcement. **Depends on**: T007b.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Automatically select repositories, clone them, extract git history and static analysis metrics, and produce a unified CSV with **raw** metrics (total_lines_changed, debt_score) and `avg_loc` as a covariate.

**Independent Test**: Run the pipeline on a set of fixed public repos; verify `data/processed/unified_metrics.csv` contains non-null rows for `total_lines_changed`, `debt_score`, `avg_loc`, and `contributor_count` for every file, and that `tool_validation_log.csv` records star counts and validation status.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T008 [P] [US1] Contract test for `unified_metrics.csv` schema in `tests/contract/test_dataset_schema.py`
- [ ] T009 [P] [US1] Integration test for repo cloning and filtering in `tests/integration/test_data_extraction.py`

### Implementation for User Story 1

- [ ] T010 [P] [US1] **Repo Selection**: Implement `code/data_extraction.py`. **Action**: Load the PINNED list of repositories from `data/raw/repos_metadata.csv`. **Definition**: The file must match the Data Model schema: columns `repo_id`, `owner`, `name`, `language`, `url`. **Validation**: The task must validate the loaded CSV against this schema. **Hardcoded List**: If `data/raw/repos_metadata.csv` is missing, create it using the following verified list of public repos: `psf/requests`, `tensorflow/tensorflow`, `vuejs/vue`, `django/django`, `pallets/flask`. **Deliverable**: `data/raw/repos_metadata.csv` (created from the hardcoded list in `code/config.py` if missing, or loaded if present) and load it into memory. **Format**: `repo_id`, `owner`, `name`, `language`, `url`.
- [ ] T011 [P] [US1] **Git History**: Implement `code/data_extraction.py`. **Action**: Clone each repo from T010. Use `pydriller` to extract per-file commit counts and lines changed (additions + deletions) for the last 12 months. **Deliverable**: `data/raw/git_history/{repo_id}/commits.csv` with columns: `file_path`, `total_lines_changed`, `commit_count`. **Depends on**: T010.
- [ ] T014 [US1] **Static Analysis**: Implement `code/static_analysis.py`. **Action**: Run `semgrep==1.30.0` on ALL files (Python, Java, JS, TS, Go, Rust). **Pre-check**: Verify Semgrep rules exist for each supported language by running `semgrep --validate --config code/semgrep_rules.yaml` (or equivalent config file) before execution. If a language is unsupported, log a warning and skip.
 **Calculation**:
 - For Python: `debt_score` = Sum(Cyclomatic Complexity from Semgrep) + (100 - Maintainability Index from Semgrep). **Fallback**: If Semgrep does not provide Maintainability Index (MI) for a file, calculate `debt_score` = Sum(Cyclomatic Complexity) + 0 (or use a default MI of 100 if configured) and log a warning: "MI missing for {file_path}, using fallback." **Do NOT exclude the file**.
 - For Java, JS, TS, Go, Rust: `debt_score` = Sum(Code Smells + Cyclomatic Complexity) as reported by Semgrep.
 - **Deliverable**: `data/raw/static_analysis/{repo_id}/semgrep_results.json` with per-file scores. **Depends on**: T010, T011, T013.
- [ ] T015a [US1] **Filtering**: Implement `code/preprocessing.py`. **Action**: Filter non-source-code files from T011 and T014 outputs. **Input**: `data/raw/git_history/*/commits.csv` and `data/raw/static_analysis/*/semgrep_results.json`.
 **Logic**:
 1. Include only files with extensions: `.py`, `.java`, `.js`, `.ts`, `.go`, `.rs`.
 2. Exclude files with `total_lines_changed` < 1 or `debt_score` < 0.
 3. Calculate `avg_loc` as the average lines of code per file (from git history or static analysis source lines).
 **Output**: `data/processed/unified_metrics.csv`.
 **Schema**: `repo_id`, `file_path`, `total_lines_changed`, `debt_score`, `avg_loc`, `contributor_count`, `language`. **Depends on**: T014, T011.
- [ ] T015b [US1] **Sensitivity Analysis Prep**: Implement `code/analysis.py`. **Action**: Implement a reusable function `run_correlation_analysis(dataframe, thresholds=[5, 10, 20])` that filters the dataframe for `avg_loc >= threshold` for **each** threshold in the provided list and computes correlation statistics (Pearson/Spearman) on the **full** filtered dataset. **Rationale**: This filter isolates files with average lines of code greater than or equal to the threshold to test robustness in larger files. **Deliverable**: The function `run_correlation_analysis` in `code/analysis.py`. **Note**: This function will be called by T022 with the fixed set of values {5, 10, 20}. **Return Type**: A dictionary with keys `{'r': float, 'p': float, 'n': int}` for each threshold. **Depends on**: T015a.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Correlation Analysis (Priority: P2)

**Goal**: Calculate correlation between **raw** churn and **raw** debt, controlling for `avg_loc` and other confounders, and perform sensitivity analysis.

**Independent Test**: Feed the pipeline a synthetic CSV with known correlation; verify output reports `r` within ±0.05 and `p < 0.05`, and that VIF warnings trigger Ridge regression if collinearity is high.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T016 [P] [US2] Contract test for `correlation_results.csv` schema in `tests/contract/test_output_schema.py`
- [ ] T017 [P] [US2] Integration test for mixed-effects model execution in `tests/integration/test_analysis.py`

### Implementation for User Story 2

- [ ] T018 [US2] **VIF Check**: Implement `code/analysis.py`. **Action**: Load `unified_metrics.csv`. Use `statsmodels.stats.outliers_influence.variance_inflation_factor` on numeric covariates: `avg_loc`, `contributor_count`. If `language` is to be included, one-hot encode it first. If any VIF > 5, log warning. **Deliverable**: `data/results/vif_report.csv` with columns: `covariate_name`, `vif_value`, `status`. **Note**: `project_age` is NOT in the schema and must not be used. **Depends on**: T015a.
- [ ] T020 [US2] **Correlation**: Implement `code/analysis.py`. **Action**: Calculate Pearson and Spearman correlation coefficients on **raw** `total_lines_changed` vs `debt_score`. Control for `avg_loc` using `pingouin.partial_corr` (X=churn, Y=debt, covariates=[avg_loc]). **Output**: Generate `data/processed/per_repo_correlations.csv` with columns: `repo_id`, `metric_type`, `r_value`, `p_value`, `n`. **Note**: The `r_value` output from this task is the specific input required for the Fisher-transformed meta-analysis in T021. **Deliverable**: `data/results/correlation_results.csv` (aggregated summary) and `data/processed/per_repo_correlations.csv` (per-repo data). **Depends on**: T015a.
- [ ] T021 [US2] **Meta-Analysis**: Implement `code/analysis.py`. **Action**:
 1. Load `r` values from `data/processed/per_repo_correlations.csv` (metric_type=pearson).
 2. Compute Fisher's Z: `z = 0.5 * np.log((1 + r) / (1 - r))`.
 3. Compute SE: `se = 1 / np.sqrt(n - 3)`.
 4. Inverse-variance weighted meta-analysis: `z_combined = np.sum(z / se**2) / np.sum(1 / se**2)`.
 5. Convert back to r: `r_combined = (np.exp(2 * z_combined) - 1) / (np.exp(2 * z_combined) + 1)`.
 6. Calculate p-value for `z_combined`.
 **Deliverable**: `data/results/meta_analysis_results.csv` with columns: `method`, `combined_r`, `combined_se`, `p_value`, `k_studies`. **Depends on**: T020.
- [ ] T022 [US2] **Sensitivity Analysis Aggregation**: Implement `code/analysis.py`. **Action**:
 1. Load `unified_metrics.csv` from T015a.
 2. For each threshold in the **fixed set** of values: `5`, `10`, `20`:
 a. Filter data for `avg_loc >= threshold`.
 b. Run the full correlation logic from T020 (Pearson/Spearman, controlling for `avg_loc`) on the filtered data.
 c. Record `r_value`, `p_value`, `n`.
 3. Aggregate results into a single CSV.
 **Deliverable**: `data/results/sensitivity_analysis.csv` with columns: `threshold`, `r_value`, `p_value`, `n`. **Depends on**: T015a, T020.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualization and Reporting (Priority: P3)

**Goal**: Generate scatter plots with regression lines and a summary report.

**Independent Test**: Run the reporting module on sample data; verify `data/results/plots/` contains PNGs with annotated `r` and `p` values, and `summary_report.txt` exists.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T024 [P] [US3] Contract test for `summary_report.txt` content in `tests/contract/test_report_schema.py`
- [X] T025 [P] [US3] Integration test for plot generation in `tests/integration/test_visualization.py`

### Implementation for User Story 3

- [X] T026 [US3] **Plots**: Implement `code/visualization.py`. **Action**: Generate scatter plots using `matplotlib.pyplot`. X-axis: `total_lines_changed`, Y-axis: `debt_score`. Overlay regression line. **Deliverable**: `data/results/plots/repo_{id}_scatter.png` (size=(10, 6), dpi=300).
- [X] T027 [US3] **Annotation**: Implement `code/visualization.py`. **Action**: Annotate plots with correlation coefficient (`r`) and p-value formatted as `r = {r:.3f}, p = {p:.4f}`. **Deliverable**: Annotated PNGs in `data/results/plots/`.
- [X] T028a [US3] **Report Data**: Implement `code/reporting.py`. **Action**: Generate table data for `summary_report.txt`. **Format**: Markdown table with columns: `repo_id`, `r`, `p`, `significance`. **Logic**: Flag `|r| >= 0.3` as 'moderate'.
- [ ] T028b [US3] **Report File**: Implement `code/reporting.py`. **Action**: Read `data/results/correlation_results.csv` (from T020), `data/results/meta_analysis_results.csv` (from T021), and `data/results/sensitivity_analysis.csv` (from T022). Format data into a structured text report.
 **Template**:
 1. **Executive Summary**: Key findings.
 2. **Methodology**: Brief description of raw metrics and meta-analysis.
 3. **Results**: Tables from correlation, meta-analysis, and sensitivity analysis.
 4. **Conclusion**: Final interpretation.
 **Deliverable**: `data/results/summary_report.txt`. **Depends on**: T020, T021, T022.
- [ ] T031 [US3] **Versioning**: Implement `code/main.py`. **Action**: Finalize pipeline by computing checksums and updating the state file path defined in `code/config.py` (derived from Constitution). **Action**: Write checksums to `artifact_hashes` key and update `updated_at` timestamp. **Depends on**: T028b.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T032a [US3] **Quickstart Creation**: Create `quickstart.md` with Installation and Execution sections. **Action**: Write the complete "Installation" and "Execution" sections to `quickstart.md`. **Content Requirements**:
 1. Steps to install Python.
 2. Steps to install Semgrep (`pip install semgrep==1.30.0`).
 3. Steps to install dependencies from `code/requirements.txt`.
 4. Command `python code/main.py`.
 5. Expected output summary (e.g., "Pipeline completed successfully", path to `data/results/summary_report.txt`).
 **Deliverable**: `quickstart.md` with a complete "Installation" and "Execution" section. **Depends on**: T007e.
- [ ] T033b [US3] **Streaming & Memory**: Refactor `code/preprocessing.py` to implement streaming iterator for large files. **Action**: Replace `pandas.read_csv` with `pd.read_csv(..., chunksize=1000)` and use a generator to accumulate statistics. **Success Criteria**: Peak memory usage < 7GB as measured by `code/utils.py` memory monitor (aligned with Plan's 7GB limit). **Depends on**: T015a.
- [ ] T034 [US1] **Batch Logic**: Implement batch processing logic in `code/data_extraction.py` using `queue.Queue`. **Action**: Use `queue.Queue` with `maxsize=100`. **Params**: Batch size = 100 repos; Trigger = RAM > 5GB. **Depends on**: T011.
- [X] T035 [P] **Unit Tests**: Implement unit tests in `tests/unit/test_metrics.py`. **Action**: Create functions: `test_debt_score_calculation`, `test_churn_calculation`, `test_avg_loc_calculation`. Each function must assert specific expected values. **Depends on**: T015a.
- [ ] T036 [US3] **Quickstart Validation**: Run `quickstart.md` validation to ensure end-to-end reproducibility. **Action**: Execute `python code/main.py` as described in `quickstart.md`. **Success Criteria**: Exit code 0 and output contains "Pipeline completed successfully". **Depends on**: T032a.

---

## Phase 7: Plan Alignment & Data Integrity (REVISION ROUND 1)

**Purpose**: Address review findings regarding the contradiction between the Plan's narrative and the Spec's requirements, and ensure strict data hygiene (no synthetic fallbacks).

**⚠️ CRITICAL**: These tasks address specific gaps identified in the initial review of the plan/spec alignment and data loading logic.

- [ ] T041 [US1] **Data Loader Hardening**: Refactor `code/data_extraction.py` to enforce "Fail Loudly" policy. **Action**:
 1. Locate the repo cloning logic (T011).
 2. Remove any `try/except` block that catches network errors and falls back to `generate_synthetic_repos()` or `mock_data()`.
 3. Add a pre-clone validation step to check that the `url` field in the pinned repo list points to a public GitHub repository (SC-004).
 4. Ensure that if `pydriller` or `git` fails to clone a repo from the PINNED list, the script raises a `RuntimeError` with a clear message: "Failed to clone real repo {repo_id}. Aborting pipeline to prevent synthetic data fabrication."
 5. Add a comment referencing the "Real Data + Real Results Only" rule.
 **Deliverable**: Updated `code/data_extraction.py` with no synthetic fallbacks and public URL validation. **Depends on**: T011.
- [ ] T042 [US1] **Dataset Sourcing**: Implement a robust repo list generator if `data/raw/repos_metadata.csv` is missing. **Action**:
 1. In `code/data_extraction.py` (T010), if `data/raw/repos_metadata.csv` is missing, do NOT generate random data or fetch from API.
 2. **Hardcode** the following verified list of top Python/JS/Java repos: `psf/requests`, `tensorflow/tensorflow`, `vuejs/vue`, `django/django`, `pallets/flask`.
 3. Write this hardcoded list to `data/raw/repos_metadata.csv`.
 4. **Format**: CSV with headers `repo_id,owner,name,language,url`. **Delimiter**: `,`. **Encoding**: `utf-8`. **repo_id**: Generated as `{owner}/{name}` (e.g., `psf/requests`).
 5. Log the source of the list (Hardcoded Set) to `data/logs/validation.log`.
 **Deliverable**: `data/raw/repos_metadata.csv` populated with real, reachable repos. **Depends on**: T010.

**Checkpoint**: Execution safety measures implemented. Pipeline ready for final validation.

---

## Phase 8: Execution Safety & Verification (REVISION ROUND 2)

**Purpose**: Address specific execution risks regarding timeout handling and memory constraints on the free-tier runner, ensuring the pipeline does not hang or crash due to resource exhaustion.

**⚠️ CRITICAL**: These tasks are required to ensure the pipeline executes successfully within the 6-hour timeout and 7GB memory limit defined in SC-001 and SC-003.

- [ ] T044 [US1] **Memory Streaming Implementation**: Refactor `code/preprocessing.py` to strictly adhere to the 7GB memory limit. **Action**:
 1. Replace all `pandas.read_csv` calls with `pd.read_csv(..., chunksize=...)` iterators.
 2. Implement a generator-based accumulation function that processes data in chunks and discards raw data after aggregation.
 3. Add a memory monitor in `code/utils.py` that logs current memory usage every 60 seconds.
 4. If memory usage exceeds 6.5GB, trigger a graceful shutdown with an error message: "MEMORY_LIMIT: Exceeded 7GB limit. Aborting to prevent crash."
 **Deliverable**: `code/preprocessing.py` with streaming logic and `code/utils.py` with memory monitoring. **Depends on**: T033b.
- [ ] T045 [US1] **Repo Cloning Retry Logic**: Implement a retry mechanism for `pydriller` cloning in `code/data_extraction.py`. **Action**:
 1. Wrap the cloning logic in a `for` loop with a maximum of 3 retries.
 2. Use exponential backoff between retries for transient network failures.
 3. Log each retry attempt to `data/logs/pipeline.log`.
 4. If all retries fail, raise the `RuntimeError` defined in T041 (Fail Loudly).
 **Deliverable**: `code/data_extraction.py` with robust retry logic. **Depends on**: T041.

**Checkpoint**: Execution safety measures implemented. Pipeline ready for final validation.

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
- **Phase 7 (Revision)**: Must be completed before final execution to ensure plan/spec consistency and data integrity.
- **Phase 8 (Safety)**: Must be completed before final execution to ensure timeout and memory constraints are met.

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
- All Foundational tasks marked [P] can run in parallel (within Phase 2, excluding dependencies like T013->T005)
- Once Foundational phase completes, all user stories can start in parallel (if staffed)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members (e.g., T010-T015 vs T018-T023)

---

## Parallel Example

```bash
# Launch all independent data extraction tasks for User Story 1 together:
Task: "Load pinned repo list" (T010)
# T011 (Clone) depends on T010. T013 (Validation) depends on T005.
# T014 (Static Analysis) depends on T010, T011, T013.
# These are NOT all parallel. Only T010 and T005 (if in Phase 2) are parallel.
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
- **Correction**: Sensitivity analysis thresholds strictly limited to the fixed set of values: 5, 10, and 20. Analysis is performed by filtering the dataset for `avg_loc >= threshold` for each of these values, as per Spec FR-008.
- **Correction**: Tool validation includes a static citation check (not dynamic API) as per Spec SC-005, replacing any hardcoded JSON file fallback.
- **Note**: The Plan's Summary and Next Steps sections contain contradictions regarding the Spec (claiming it mandates density metrics/SonarQube). The tasks strictly follow the **Spec** (which mandates raw metrics/Semgrep). The Plan requires a kickback to align its narrative with the Spec.
- **Revision**: Phase 7 tasks (T040-T042) explicitly address the Plan's narrative contradictions and enforce strict "Fail Loudly" data loading to prevent synthetic data fabrication.
- **Revision**: Phase 8 tasks (T043-T045) address execution safety, ensuring the pipeline respects the 6-hour timeout and 7GB memory limit, and implements robust retry logic for network failures.
