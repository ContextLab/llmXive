# Tasks: Quantifying the Impact of Code Ownership on Software Quality

**Input**: Design documents from `/specs/001-code-ownership-analysis/`
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

- [ ] T001 Create project structure per implementation plan (`projects/PROJ-062-quantifying-the-impact-of-code-ownership/`)
- [ ] T002 Initialize Python 3.11 project with `requirements.txt` (GitPython, scikit-learn, scipy, pandas, numpy, radon, matplotlib, pyyaml)
- [ ] T003 [P] Configure linting (flake8/black) and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Setup `data/raw/`, `data/intermediate/`, `data/results/` directory structure with `.gitkeep`
- [X] T005 [P] Implement `code/utils/backoff.py` with exponential backoff logic (≤3 retries, ≥60s delay) for GitHub API
- [X] T006 [P] Implement `code/utils/path_normalizer.py` for FR-009 (lowercase, strip extensions, normalize slashes)
- [X] T007 Create `code/config.py` for environment variables (cutoff date T, depth limit, repo list)
- [X] T008 Setup `code/__init__.py` and logging infrastructure to disk
- [X] T009 Implement `code/state_manager.py` for content hashing and versioning. **CRITICAL**: This task MUST ensure that raw ownership attribution CSVs are committed to the repository (e.g., in `data/ownership_metrics/`) to satisfy Constitution Principle VI ("raw files MUST be version-controlled and included in the repository"). Additionally, generate content hashes for these files and record them in `state/...yaml` for state management.
 **Specific Instructions**:
 1. Update `.gitignore` to explicitly ignore `data/raw/` and `data/intermediate/` while allowing `data/ownership_metrics/*.csv`.
 2. Commit only the CSV files matching the pattern `*_ownership.csv` in `data/ownership_metrics/`.
 3. This task implements a specific deviation from the Plan's 'Versioning Discipline' section: aggregated ownership metrics (CSVs) are committed while raw git data is hashed. Document this deviation in the task output.
 4. Do not exclude raw files from Git if the Constitution requires them to be included; instead, ensure only the small CSVs are committed.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Repository Data Collection and Processing (Priority: P1) 🎯 MVP

**Goal**: Download Git repositories, parse commit logs for ownership, and extract bug counts via path-based proximity.

**Independent Test**: Verify 10 valid repos are cloned with depth 1000, ownership data is parsed, and bug metadata is retrieved for ≥8 repos.

### Implementation for User Story 1

- [X] T010 [US1] Implement `code/data_collection.py` to clone a set of GitHub repos with `git clone --depth` (up to cutoff T), using a sufficient depth to capture relevant version history. **Verification**: After cloning, run `git rev-list --count HEAD` in `data/raw/<repo_name>/`. The task MUST assert `count >= 1000` OR `count == total_commits` (if the repo has < 1000 commits). If the repo has ≥1000 commits, the shallow clone must have exactly 1000 commits. If the count is < 1000 and < total_commits, the task fails.
- [X] T011 [US1] Implement logic in `code/data_collection.py` to validate commit count (≥1000) and skip if insufficient, logging warnings
- [X] T012 [US1] Implement `code/data_collection.py` to parse shallow history into intermediate CSVs (commits: author, timestamp, file_path)
- [X] T013 [US1] Implement `code/data_collection.py` to fetch GitHub Issues for time window T+1, handling rate limits via `utils/backoff.py`
- [X] T014 [US1] Implement `code/data_collection.py` to apply `utils/path_normalizer.py` and link issues to modules using exact path matching (FR-009)
- [X] T015 [US1] Implement disk-based storage logic in `code/data_collection.py` to write intermediate CSVs immediately, ensuring peak RAM ≤7 GB
- [X] T016 [US1] Implement validation in `code/data_collection.py` to verify dataset-variable fit (committers, timestamps, file paths, line counts) and skip invalid repos
- [X] T017 [US1] Create `tests/unit/test_data_collection.py` to mock Git and GitHub API responses and verify cloning/parsing logic
- [X] T018 [US1] Create `tests/integration/test_data_pipeline.py` to run end-to-end on a small sample repo (e.g., `apache/httpd`) and verify output CSVs

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Ownership and Quality Metric Calculation (Priority: P2)

**Goal**: Calculate Gini coefficient, code churn, cyclomatic complexity, and normalized bug density.

**Independent Test**: Verify Gini ∈ [0,1], complexity ≥95% valid, and bug density per KLOC calculated correctly.

### Implementation for User Story 2

- [X] T019 [US2] Implement `code/metrics_calc.py` to calculate Gini coefficient per module from ownership CSVs (precision ≥3 decimals)
- [X] T020 [US2] Implement `code/metrics_calc.py` to filter out modules deleted between T and T+1 for BOTH predictor and outcome (FR-008)
- [X] T021 [US2] Implement `code/metrics_calc.py` to calculate code churn (lines added/deleted) per module
- [X] T022 [US2] Implement `code/metrics_calc.py` to compute cyclomatic complexity using `radon` on the latest snapshot (exclude non-Python files). **Verification**: Count total Python modules and modules with valid scores. Assert that `valid_count / total_count >= 0.95`. If the threshold is not met, log a critical warning and fail the task (or stop the pipeline) to prevent downstream analysis on invalid data.
- [ ] T023 [US2] Implement `code/metrics_calc.py` to calculate normalized bug density (bugs/KLOC), excluding modules with 0 lines of code
- [ ] T024 [US2] Implement `code/metrics_calc.py` to calculate module Size (KLOC) and Age (months since creation). **Note**: This task must also generate the `Gini²` (Gini squared) term for use in T031.
- [ ] T025 [US2] Create `tests/unit/test_metrics_calc.py` to verify Gini calculation, KLOC normalization, and complexity scoring
- [ ] T026 [US2] Create `tests/integration/test_metrics_pipeline.py` to verify end-to-end metric generation from intermediate CSVs

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Correlation Analysis and Visualization (Priority: P3)

**Goal**: Perform Spearman correlation, VIF diagnostics, non-linearity tests, sensitivity analysis, and visualization.

**Independent Test**: Verify correlation coefficients, p-values, VIF, sensitivity sweeps, and scatter plots are generated.

### Implementation for User Story 3

- [ ] T027 [US3] Implement `code/statistical_analysis.py` to perform Spearman rank correlation (Gini vs. bug density) using `scipy.stats`
- [ ] T028 [US3] Implement `code/statistical_analysis.py` to calculate 95% confidence intervals for correlation coefficients
- [ ] T029 [US3] Implement `code/statistical_analysis.py` to calculate VIF for predictors (Gini, Gini², Size, Age) as required by FR-013. **Specifics**: Calculate VIF for all listed terms. If VIF is infinite or ≥5, flag the result in the output JSON with a message stating "independent effects cannot be claimed". Note: While Gini and Gini² are collinear, the task must still attempt the calculation and report the result (including infinity) to satisfy the spec's diagnostic requirement.
- [ ] T030 [US3] Implement `code/statistical_analysis.py` to apply multiple-comparison correction (Bonferroni or Benjamini-Hochberg) (FR-011)
- [ ] T031 [US3] Implement `code/statistical_analysis.py` to test for non-linearity. **Specifics**: Fit a linear model (Outcome ~ Gini + Size + Age) and a quadratic model (Outcome ~ Gini + Gini² + Size + Age).
 1. Perform a Likelihood Ratio Test (LRT) to compare models.
 2. **Crucially**: Perform a standard t-test on the quadratic model to obtain the p-value for the Gini² coefficient.
 3. **Output**: Report the t-test p-value of the Gini² coefficient as the primary metric for FR-016 compliance. Also report the LRT p-value for model improvement.
 4. **Dependency**: Ensure this task executes after T024 (which generates Gini²) and T029 (which calculates VIF).
- [ ] T032 [US3] Implement `code/statistical_analysis.py` to perform p-value sensitivity analysis. **Sweep Set**: Explicitly use the set `{0.01, 0.05, 0.1}` as defined in SC-008. **Output**: Generate a CSV file at `data/results/sensitivity_pvalue.csv` with columns: `cutoff`, `count_significant`, `count_total`.
- [ ] T033 [US3] Implement `code/statistical_analysis.py` to perform correlation magnitude sensitivity analysis. **Sweep Set**: Explicitly use the set `{0.2, 0.3, 0.4}` as defined in SC-011. **Output**: Generate a CSV file at `data/results/sensitivity_rho.csv` with columns: `cutoff`, `count_significant`, `count_total`.
- [ ] T034 [US3] Implement `code/visualizations.py` to generate scatter plots with regression lines (≥300 DPI) for ≥8 repos
- [ ] T035 [US3] Implement `code/main.py` to orchestrate the full pipeline, ensuring temporal separation (T vs T+1) and associational framing (FR-010). **Output**: Write the final report to `data/results/final_report.json`, explicitly including the text "associational rather than causal" in the report metadata.
- [ ] T036 [US3] Create `tests/unit/test_statistical_analysis.py` to verify correlation, VIF, and regression logic
- [ ] T037 [US3] Create `tests/integration/test_analysis_pipeline.py` to verify full statistical output JSON and plot generation

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T038 [US1] **New Task**: Calculate the global "Bug-File linkage rate" as required by SC-007. **Logic**: Aggregate total issues mentioning paths across all repos and total issues successfully linked to modules. Calculate `linkage_rate_percentage = (linked_issues / total_issues) * 100`. **Execution Order**: Execute AFTER all repositories in Phase 3 are successfully processed to ensure global aggregation includes all valid repos. **Output**: Write to `data/results/linkage_rate.json` with schema: `{ "total_issues": <int>, "linked_issues": <int>, "linkage_rate_percentage": <float> }`.
- [ ] T039 [US2] **New Task**: Calculate "Code churn correlation with bug density" as required by SC-006. **Logic**: Perform Spearman rank correlation between code churn (from T021) and bug density. **Output**: Include the correlation coefficient and p-value in `data/results/final_report.json` under a key `code_churn_correlation`.
- [ ] T040 [P] Documentation updates in `docs/README.md` and `specs/001-code-ownership-analysis/research.md`
- [ ] T041 Code cleanup and refactoring to ensure peak RAM ≤7 GB and runtime ≤6 hours
- [ ] T042 [P] Run `quickstart.md` validation and verify all JSON outputs match schema
- [ ] T043 Verify all findings are framed as associational in final report outputs

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data (intermediate CSVs)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 metrics

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
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for [endpoint] in tests/contract/test_[name].py"
Task: "Integration test for [user journey] in tests/integration/test_[name].py"

# Launch all models for User Story 1 together:
Task: "Create [Entity1] model in src/models/[entity1].py"
Task: "Create [Entity2] model in src/models/[entity2].py"
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