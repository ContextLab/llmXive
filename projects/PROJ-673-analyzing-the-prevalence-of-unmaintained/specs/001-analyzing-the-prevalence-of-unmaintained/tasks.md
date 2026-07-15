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

- [X] T001 Create project structure per implementation plan: execute `mkdir -p src/models src/services src/analysis src/cli src/utils data/raw data/processed tests/unit tests/integration docs`
- [X] T002 Initialize Python 3.11 project with `requests`, `pandas`, `scipy`, `statsmodels`, `matplotlib`, `pyyaml` dependencies by creating `pyproject.toml` at repository root
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create data models for `Package`, `Dependency`, and `AnalysisResult` in `src/models/data_models.py` (Pydantic/Dict schemas)
- [X] T005 [P] Implement utility functions for exponential backoff in `src/utils/backoff.py` with EXPLICIT parameters: a limited number of retries, initial delay=1s, multiplier=2.0, max delay=60s. Also implement checksum generation in `src/utils/checksum.py`.
- [X] T006 [P] Setup environment configuration management in `src/config/settings.py`: create file with default values for `NPM_API_KEY`, `GITHUB_TOKEN`, and `RATE_LIMIT` (requests/min)
- [ ] T007 Create base logging infrastructure in `src/utils/logging_config.py` to track API success/failure rates (FR-009)
- [ ] T007a [P] Implement API log aggregation utility in `src/utils/api_metrics.py` to calculate and report the success/failure ratio as required by SC-004.
- [ ] T008 Implement local file caching mechanism to save raw API responses to `data/raw/` with immutable checksums (Constitution Principle III & VI)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Collection and Variable Extraction (Priority: P1) 🎯 MVP

**Goal**: Programmatically retrieve top NPM packages, extract dependency trees, and gather maintenance/security metadata.

**Independent Test**: A script runs and outputs a JSON/CSV file with N rows, each containing a list of dependencies with `last_release_date`, `last_commit_date`, and `vulnerability_count`.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: These are 'Write Test' tasks. They define the expected behavior and can be written in parallel with each other. They verify the logic once the implementation (T012-T018) is present.

- [ ] T009 [US1] Write unit test for dependency age calculation (handling null dates) in `tests/unit/test_age_calc.py`
- [ ] T010 [US1] Write unit test for backoff logic (max retries) in `tests/unit/test_backoff.py`
- [ ] T011 [US1] Write integration test for mocked NPM/GitHub API responses in `tests/integration/test_api_clients.py`

### Implementation for User Story 1

- [X] T012 [P] [US1] Implement `NpmClient` in `src/services/npm_client.py` to query top packages by weekly downloads and fetch package metadata
- [ ] T013 [P] [US1] Implement `GithubClient` in `src/services/github_client.py` to fetch `last_commit_date` and `last_release_date` for repositories
- [ ] T014 [P] [US1] Implement `AuditClient` in `src/services/audit_client.py` to query npm audit for unpatched CVE counts
- [X] T015 [US1] Implement recursive dependency tree resolver in `src/services/dependency_resolver.py` to flatten direct and transitive dependencies (FR-002)
- [ ] T016 [US1] Implement the main data collection pipeline in `src/cli/collect_data.py` that orchestrates clients, handles missing repos (null dates), and skips private packages <!-- ATOMIZE: requested -->
- [~] T017 [US1] Implement logic to calculate `age_in_days` and exclude dependencies with missing release metadata from age calculation but include in vulnerability counts (FR-010). **VERIFY**: rows with null release_date have age_in_days=null but non-null vulnerability_count. <!-- FAILED: unspecified -->
- [ ] T017a [US1] Implement calculation of the proportion of dependencies with missing release metadata and write the result to `data/processed/metrics.json` to satisfy SC-002.
- [ ] T018 [US1] Implement data export to `data/processed/dependencies_raw.csv` with checksum generation (must contain calculated `age_in_days` from T017 and depend on T017a completion)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Correlation Analysis (Priority: P2)

**Goal**: Compute Spearman rank correlation between dependency age and vulnerability density, and generate visualizations.

**Independent Test**: A script takes the dataset from US-1 and outputs a correlation coefficient (r), p-value, and a scatter plot. Test verifies r in [-1, 1] and p in [0, 1].

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [P] [US2] Write unit test for Spearman correlation calculation bounds in `tests/unit/test_stats.py`
- [X] T020 [P] [US2] Write integration test for end-to-end analysis pipeline on a small synthetic dataset in `tests/integration/test_analysis_pipeline.py`

### Implementation for User Story 2

- [ ] T021 [US2] Implement statistical analysis module in `src/analysis/correlation.py` to calculate Spearman rho and p-value (FR-006). **DEPENDENCY**: Must run after T018 to access `dependencies_raw.csv`.
- [~] T021a [US2] Document statistical power assumptions (target ≥ 0.8) and sample size justification in `data/processed/power_analysis_notes.md` to satisfy SC-006, treating it as a documented assumption rather than a verification gate.
- [~] T024 [US2] Create the analysis runner script in `src/cli/run_analysis.py` that loads `dependencies_raw.csv`, runs correlation, and saves results to `data/processed/results_correlation.json`
- [X] T023 [US2] Implement visualization generator in `src/analysis/visualizer.py` to create scatter plots (age vs. vulnerability count) (FR-008)
- [~] T025 [US2] Add logic to flag statistical significance (p < 0.05) in the output report (US-2 Acceptance 3)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Stratified Analysis and Reporting (Priority: P3)

**Goal**: Stratify analysis by package category and generate summary reports.

**Independent Test**: A script outputs a table of correlation coefficients per category (N ≥ 30) and a histogram of unmaintained dependency percentages.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T026 [P] [US3] Write unit test for category assignment logic (keyword matching vs. topology fallback) in `tests/unit/test_categorization.py`
- [X] T027 [P] [US3] Write integration test for stratified analysis filtering (N < 30 exclusion) in `tests/integration/test_stratification.py`

### Implementation for User Story 3

- [ ] T028 [US3] Implement category classifier in `src/analysis/categorizer.py` using package metadata keywords. **MANDATORY FALLBACK**: MUST implement a generic fallback using dependency graph topology when keywords are missing or noisy (FR-007). **DEPENDENCY**: Requires graph structure from T015.
- [ ] T029 [US3] Implement stratified correlation logic in `src/analysis/stratified_stats.py` to compute per-category coefficients (excluding groups with N < 30)
- [ ] T029a [US3] Implement variance calculation and comparative measurement of correlation coefficients across categories against overall dataset, appending results to `data/processed/results_correlation.json` to satisfy SC-003.
- [ ] T032 [US3] Implement sensitivity analysis for "unmaintained" threshold (90, 180, 365 days) applied ONLY to visualization and secondary metrics (binary threshold), NOT to the primary continuous correlation. Write robustness results to `data/processed/sensitivity_analysis.json`.
- [X] T030 [US3] Implement histogram generator for unmaintained dependency percentages by category in `src/analysis/visualizer.py` (FR-008)
- [ ] T031 [US3] Create the reporting script in `src/cli/generate_report.py` that aggregates US-2, US-3, and sensitivity analysis results into a final summary report generated at `docs/report.md`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [~] T033 [P] Documentation updates in `docs/` including `quickstart.md` for running the pipeline
- [~] T034 Code cleanup and refactoring of API client error handling
- [~] T035 Performance optimization: ensure full pipeline runs within 6 hours on 2 vCPU (SC-005)
- [~] T036 [P] Additional unit tests for edge cases (private packages, rate limits) in `tests/unit/`
- [~] T037 Security hardening: verify no secrets are logged and API keys are handled via environment variables
- [~] T038 Run quickstart.md validation to ensure reproducibility

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on data output from US-1 (T018)
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