# Tasks: Analyzing the Prevalence of Unmaintained Dependencies in Popular NPM Packages

**Input**: Design documents from `/specs/001-analyzing-the-prevalence-of-unmaintained/`
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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan: execute `mkdir -p src/models src/services src/analysis src/cli src/utils data/raw data/processed tests/unit tests/integration docs`
 *Note*: Do NOT create `contracts/` here; it belongs under `specs/001-analyzing-the-prevalence-of-unmaintained/` per plan.md structure.
- [ ] T002 Initialize Python 3.11 project with `requests`, `pandas`, `scipy`, `statsmodels`, `matplotlib`, `pyyaml` dependencies by creating `pyproject.toml` at repository root
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Create data models for `Package`, `Dependency`, and `AnalysisResult` in `src/models/data_models.py` (Pydantic/Dict schemas)
- [ ] T005 [P] Implement utility functions for exponential backoff in `src/utils/backoff.py` with EXPLICIT parameters: max_retries=3 (per FR-009), initial_delay=1s, multiplier=2.0, max_delay=60s.
- [ ] T005a Implement checksum generation in `src/utils/checksum.py` for file integrity verification.
 *Note*: Requires T002 (Initialize Python project) for dependencies. This is NOT parallel-safe until T002 completes.
- [ ] T006 [P] Setup environment configuration management in `src/config/settings.py`: create file with default values for `NPM_API_KEY`, `GITHUB_TOKEN`, and `RATE_LIMIT` (requests/min)
- [ ] T007 Create base logging infrastructure in `src/utils/logging_config.py` to track API success/failure rates (FR-009)
- [ ] T007a [P] Implement API log aggregation utility in `src/utils/api_metrics.py` to calculate and report the success/failure ratio as required by SC-004.
- [ ] T008 [P] Implement local file caching mechanism in `src/utils/cache.py` to save raw API responses to `data/raw/` with immutable checksums (Constitution Principle III & VI).
 *Implementation Details*: Create function `save_response_to_cache(request_params: dict, response: dict) -> str` that writes JSON to `data/raw/{hash}.json` and returns the checksum. Create function `load_from_cache(request_params: dict) -> dict | None`. Ensure `data/raw/` files are named with a hash of the request parameters and timestamp to guarantee immutability and reproducibility.
 *Verification*: Verify that a second run loads data from `data/raw/{hash}.json` without re-fetching API. Verify that cache files are named with request hashes and contain no PII.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Collection and Variable Extraction (Priority: P1) 🎯 MVP

**Goal**: Programmatically retrieve top NPM packages, extract dependency trees, and gather maintenance/security metadata.

**Independent Test**: A script runs and outputs a JSON/CSV file with N rows, each containing a list of dependencies with `last_release_date`, `last_commit_date`, and `vulnerability_count`.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: These are 'Write Test' tasks. They define the expected behavior and can be written in parallel with each each. They verify the logic once the implementation (T012-T018) is present.

- [ ] T009 [US1] Write unit test for dependency age calculation (handling null dates) in `tests/unit/test_age_calc.py`
- [ ] T010 [US1] Write unit test for backoff logic (max retries) in `tests/unit/test_backoff.py`
- [ ] T011 [US1] Write integration test for replaying NPM/GitHub API responses using cached snapshots from `data/raw/` in `tests/integration/test_api_clients_replay.py`.
 *Note*: Replaces mocked API tests. Must use real cached snapshots to adhere to Constitution Principle VI (API Snapshot Integrity) and FR-007 (real-call testing).

### Implementation for User Story 1

- [ ] T012 [P] [US1] Implement `NpmClient` in `src/services/npm_client.py` to query top packages by weekly downloads and fetch package metadata
- [ ] T013 [P] [US1] Implement `GithubClient` in `src/services/github_client.py` to fetch `last_commit_date` and `last_release_date` for repositories
- [ ] T014 [P] [US1] Implement `AuditClient` in `src/services/audit_client.py` to query npm audit for unpatched CVE counts
- [ ] T015 [US1] Implement recursive dependency tree resolver in `src/services/dependency_resolver.py` to flatten direct and transitive dependencies (FR-002)
- [ ] T016 [US1] Implement the main data collection pipeline in `src/cli/collect_data.py` that orchestrates clients, handles missing repos (null dates), and skips private packages
- [ ] T017 [US1] Implement logic to calculate `age_in_days` and exclude dependencies with missing release metadata from age calculation but include in vulnerability counts (FR-010). **VERIFY**: rows with null release_date have age_in_days=null but non-null vulnerability_count.
 *Implementation Details*: Ensure that if `release_date` is null, `age_in_days` is set to null, but `vulnerability_count` is populated from the audit data. Add an assertion in the code or a test to verify this behavior.
- [ ] T018 [US1] Implement the export logic within `src/cli/collect_data.py` to write `data/processed/dependencies_raw.csv` and `data/processed/metrics.json`. This task ensures the code exists to write the files but does not execute the run.
 *Implementation Details*: Ensure `collect_data.py` has an `--export` flag that triggers the CSV and JSON write. Ensure `metrics.json` includes `missing_release_metadata_ratio` and `total_dependencies`.
- [ ] T019 [US1] **Execute Data Collection & Export**: Run `python src/cli/collect_data.py --export --metrics --top-packages $TOP_PACKAGES` (adjust count as needed) to generate `data/processed/dependencies_raw.csv` and `data/processed/metrics.json`. **CRITICAL**: This task MUST fail loudly if the file is not created.
 *Note*: `$TOP_PACKAGES` must be resolved from the research phase/plan.md (e.g., a specific number like 100 for a staged validation run, or the final deferred count). This is a staged execution for validation.
 *Execution*: `python src/cli/collect_data.py --export --metrics --top-packages $TOP_PACKAGES`
 *Verification*: Verify `data/processed/dependencies_raw.csv` exists with columns: name, version, age_in_days, vulnerability_count. Verify `data/processed/metrics.json` exists with keys: missing_release_metadata_ratio, total_dependencies. If files are missing, the task fails and must be re-attempted with debug logging enabled.
 *Dependency*: Requires T008 (caching) and T018 (export logic) to be complete.
- [ ] T020 [US1] **Verify Data Integrity**: Run `python -c "import pandas as pd; df = pd.read_csv('data/processed/dependencies_raw.csv'); assert len(df) > 0; print('Data integrity check passed')"` to ensure the exported CSV is non-empty and valid. **BLOCKER**: If this fails, US2 and US3 cannot proceed.
 *Execution*: `python -c "import pandas as pd; df = pd.read_csv('data/processed/dependencies_raw.csv'); assert len(df) > 0; print('Data integrity check passed')"`
 *Verification*: Confirm script exits with code 0 and prints success message. If it fails, investigate T019 logs and re-run T019.

**Checkpoint**: At this point, User Story 1 data collection is functional. Metrics calculation (T017a - merged into T019) and Analysis (US2/US3) follow.

---

## Phase 4: User Story 2 - Statistical Correlation Analysis & Metrics (Priority: P2)

**Goal**: Compute Spearman rank correlation, calculate data quality metrics, and generate visualizations.

**Independent Test**: A script takes the dataset from US-1 and outputs a correlation coefficient (r), p-value, and a scatter plot. Test verifies r in [, 1] and p in [0, 1].

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T021 [P] [US2] Write unit test for Spearman correlation calculation bounds in `tests/unit/test_stats.py`
- [ ] T022 [P] [US2] Write integration test for end-to-end analysis pipeline on a small synthetic dataset in `tests/integration/test_analysis_pipeline.py`

### Implementation for User Story 2

- [ ] T023 [US2] Implement the power analysis script in `src/analysis/power.py` to calculate statistical power based on sample size.
 *Mandatory Parameters*: effect_size (rho) >= 0.2, alpha = 0.05, target_power = 0.8 (per SC-006 and Assumptions).
 *Verification*: The script must explicitly assert or verify that the calculated power meets the target (>= 0.8) given the sample size and parameters.
- [ ] T024 [US2] **Execute Power Analysis**: Run `python src/analysis/power.py` to generate `data/processed/power_analysis.json`. **DEPENDENCY**: Requires `data/processed/dependencies_raw.csv` from T020.
 *Execution*: `python src/analysis/power.py`
 *Verification*: Verify `data/processed/power_analysis.json` exists with keys: effect_size, alpha, sample_size, actual_power, methodology_notes.
- [ ] T025 [US2] Implement visualization generator in `src/analysis/visualizer.py` to create scatter plots (age vs. vulnerability count) (FR-008).
- [ ] T026 [US2] Implement the core correlation script in `src/analysis/correlation.py` to compute Spearman rho and p-value.
- [ ] T027 [US2] **Execute Core Correlation**: Run `python src/analysis/correlation.py` to generate `data/processed/results_correlation.json` (Spearman rho, p-value). **DEPENDENCY**: T020.
 *Execution*: `python src/analysis/correlation.py`
 *Verification*: Verify `data/processed/results_correlation.json` exists with keys: correlation_coefficient, p_value, sample_size.
- [ ] T028 [US2] **Execute Visualization**: Run `python src/analysis/visualizer.py --plot-scatter` to generate scatter plots. **DEPENDENCY**: T027.
 *Execution*: `python src/analysis/visualizer.py --plot-scatter`
 *Verification*: Verify `data/processed/scatter_plot.png` exists.
- [ ] T029 [US2] **Execute Analysis Runner**: Run `python src/cli/run_analysis.py` to orchestrate correlation, visualization, and reporting. **DEPENDENCY**: T024, T027, T028.
 *Execution*: `python src/cli/run_analysis.py`
 *Verification*: Verify all output artifacts exist.
- [ ] T030 [US2] Add logic to flag statistical significance (p < 0.05) in the output report (US-2 Acceptance 3)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Stratified Analysis and Reporting (Priority: P3)

**Goal**: Stratify analysis by package category and generate summary reports.

**Independent Test**: A script outputs a table of correlation coefficients per category (N ≥ 30) and a histogram of unmaintained dependency percentages.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T031 [P] [US3] Write unit test for category assignment logic (keyword matching vs. topology fallback) in `tests/unit/test_categorization.py`
- [ ] T032 [P] [US3] Write integration test for stratified analysis filtering (N < 30 exclusion) in `tests/integration/test_stratification.py`

### Implementation for User Story 3

- [ ] T033 [US3] Implement category classifier in `src/analysis/categorizer.py` using package metadata keywords. **MANDATORY FALLBACK**: If keywords are missing/noisy, classify using dependency graph topology: map 'degree centrality' > 0.8 to 'core', 'betweenness centrality' > 0.5 to 'infrastructure', otherwise 'other'. (FR-007). **DEPENDENCY**: Requires graph structure from T015.
 *Implementation Details*: Use `networkx.algorithms.centrality.degree_centrality` and `networkx.algorithms.centrality.betweenness_centrality` to calculate metrics. Ensure fallback logic is ONLY triggered when keyword data is missing or noisy, as per spec.
 *Verification*: Verify that the classifier correctly identifies categories based on keywords when available, and falls back to topology only when necessary.
- [ ] T034 [US3] Implement the stratified stats script in `src/analysis/stratified_stats.py` to compute per-category coefficients.
- [ ] T035 [US3] **Execute Stratified Correlation**: Run `python src/analysis/stratified_stats.py` to compute per-category coefficients (excluding groups with N < 30). **DEPENDENCY**: T020.
 *Execution*: `python src/analysis/stratified_stats.py`
 *Verification*: Verify `data/processed/results_stratified.json` exists with per-category coefficients.
- [ ] T036 [US3] **Execute Variance Calculation**: Run `python src/analysis/stratified_stats.py --variance` to calculate variance in correlation coefficients across categories and append to `data/processed/results_correlation.json`. **DEPENDENCY**: T035.
 *Implementation Details*: Calculate 'overall_variance' (variance of category correlations) and compare it against the overall dataset correlation as required by SC-003.
 *Verification*: Verify `data/processed/results_correlation.json` contains appended keys: category_variances, overall_variance.
- [ ] T037 [US3] Implement the sensitivity analysis script in `src/analysis/sensitivity.py` to perform threshold sweep.
- [ ] T038 [US3] **Execute Sensitivity Analysis**: Run `python src/analysis/sensitivity.py` to perform threshold sweep and generate `data/processed/sensitivity_analysis.json`. **DEPENDENCY**: T027.
 *Execution*: `python src/analysis/sensitivity.py`
 *Verification*: Verify `data/processed/sensitivity_analysis.json` exists with keys: threshold_sweep.
- [ ] T039 [US3] Implement histogram generator for unmaintained dependency percentages by category in `src/analysis/visualizer.py` (FR-008)
- [ ] T040 [US3] **Execute Report Generation**: Run `python src/cli/generate_report.py` to aggregate US-2, US-3, and sensitivity analysis results into `docs/report.md`. **DEPENDENCY**: T029, T035, T036, T038.
 *Execution*: `python src/cli/generate_report.py`
 *Verification*: Verify `docs/report.md` exists and contains all required sections.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T041 [P] Documentation updates in `docs/` including `quickstart.md` for running the pipeline
 *Update*: Add specific instructions on setting `NPM_API_KEY` and `GITHUB_TOKEN` environment variables and handling rate limits.
- [ ] T042 Code cleanup and refactoring of API client error handling
 *Refactor*: Ensure all `try/except` blocks in API clients strictly adhere to the "fail loud, no synthetic fallback" rule.
- [ ] T043 [P] Performance verification: Run the full pipeline on CI and measure total runtime. Log result to `data/processed/runtime_log.json` with schema: `{'total_runtime_seconds': float, 'api_calls_made': int, 'cache_hits': int}`. **VERIFICATION**: Ensure runtime < 6 hours (SC-005) primarily via efficient rate-limit backoff (FR-009) and caching (T008). Do NOT implement parallel fetching unless explicitly required by spec. Use 'sys.time()' or 'wall-clock' time for measurement. **VERIFY**: Verify that `data/processed/runtime_log.json` exists and contains keys: total_runtime_seconds, api_calls_made, cache_hits.
- [ ] T044 [P] Additional unit tests for edge cases (private packages, rate limits) in `tests/unit/`
- [ ] T045 Security hardening: verify no secrets are logged and API keys are handled via environment variables
- [ ] T046 Run quickstart.md validation to ensure reproducibility

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on data output from US-1 (T020)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on data output from US-1 and results from US-2

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
- All 'Write Test' tasks for a user story marked [P] can run in parallel (with each other)
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all 'Write Test' tasks for User Story 1 together (if tests requested):
Task: "Write unit test for dependency age calculation in tests/unit/test_age_calc.py"
Task: "Write unit test for backoff logic in tests/unit/test_backoff.py"

# Launch all services for User Story 1 together:
Task: "Implement NpmClient in src/services/npm_client.py"
Task: "Implement GithubClient in src/services/github_client.py"
Task: "Implement AuditClient in src/services/audit_client.py"
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
- **Data Integrity**: All data fetching tasks must fail loudly on API errors; no synthetic data generation is permitted.
- **Compute Constraints**: Ensure all scripts are optimized for the available vCPU, 7GB RAM, and 6-hour limit.