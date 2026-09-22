# Tasks: Quantifying the Impact of Code Ownership on Software Quality

**Input**: Design documents from `/specs/001-code-ownership-analysis/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.,g., US1, US2, US3)
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
- [X] T002 Initialize Python 3.11 project with `requirements.txt` (GitPython, scikit-learn, scipy, pandas, numpy, radon, matplotlib, pyyaml)
- [ ] T003 [P] Configure linting (flake8/black) and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Setup `data/raw/`, `data/intermediate/`, `data/results/` directory structure with `.gitkeep`
- [X] T005 [P] Implement `code/utils/backoff.py` with exponential backoff logic (≤3 retries, ≥60s delay) for GitHub API
- [X] T006 [P] Implement `code/utils/path_normalizer.py` for FR-009 (lowercase, strip extensions, normalize slashes)
- [X] T007 Create `code/config.py` for environment variables (cutoff date T, depth limit, repo list, **and RANDOM SEED**). **CRITICAL**:
 1. Define a `RANDOM_SEED` constant as `RANDOM_SEED = 42` (a fixed integer).
 2. **Usage Mandate**: This task MUST explicitly document that the `RANDOM_SEED` is passed to and used by all statistical analysis scripts (T029-T037) and that the seed value is logged in the final output artifacts (`final_report.json`, sensitivity outputs).
 3. The seed must be accessible via `config.RANDOM_SEED` by downstream tasks.
- [X] T008 Setup `code/__init__.py` and logging infrastructure to disk

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Repository Data Collection and Processing (Priority: P1) 🎯 MVP

**Goal**: Download Git repositories, parse commit logs for ownership, and extract bug counts via path-based proximity.

**Independent Test**: Verify that a set of valid repositories are cloned with depth 1000 (or full history), ownership data is parsed, and bug metadata is retrieved for ≥8 repos.

### Implementation for User Story 1

- [X] T010 [US1] Implement `code/data_collection.py` to clone a set of GitHub repos with `git clone --depth <sufficient_depth>`.
 **Verification Logic**:
 1. After cloning, run `git rev-list --count HEAD` in `data/raw/<repo_name>/`.
 2. **PASS Condition**: The task MUST pass if `count >= 1000` OR `count == total_commits` (where `total_commits` is the count without depth limit).
 3. **FAIL Condition**: The task MUST fail ONLY if `count < 1000` AND `count < total_commits` (i.e., the repo is incomplete and shallow).
 4. **Constraint**: This logic implements Spec US1 Acceptance Criteria: "depth 1000 (or full history if <1000)".
 5. **Note**: This `--depth 1000` overrides Constitution Principle VI's "depth 100" as per Spec US1 requirement.
- [X] T011 [US1] Implement logic in `code/data_collection.py` to validate commit count (≥1000 or full history) and skip if insufficient, logging warnings
- [X] T012 [US1] Implement `code/data_collection.py` to parse shallow history into intermediate CSVs (commits: author, timestamp, file_path)
- [X] T013 [US1] Implement `code/data_collection.py` to fetch GitHub Issues for time window T+1, handling rate limits via `utils/backoff.py`
- [X] T014 [US1] Implement `code/data_collection.py` to apply `utils/path_normalizer.py` and link issues to modules using exact path matching (FR-009)
- [X] T015 [US1] Implement disk-based storage logic in `code/data_collection.py` to write intermediate CSVs immediately, ensuring peak RAM ≤7 GB
- [X] T016 [US1] Implement validation in `code/data_collection.py` to verify dataset-variable fit (committers, timestamps, file paths, line counts) and skip invalid repos
- [X] T017 [US1] Create `tests/unit/test_data_collection.py` to mock Git and GitHub API responses and verify cloning/parsing logic
- [X] T018 [US1] Create `tests/integration/test_data_pipeline.py` to run end-to-end on a small sample repo (e.g., `apache/httpd`) and verify output CSVs

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Raw Attribution Generation & State Management (Priority: P2)

**Goal**: Generate raw per-file owner lists (Constitution Principle VI) and version-control them.

**Independent Test**: Verify that raw per-file owner lists exist, are hashed, and are tracked by Git.

### Implementation for User Story 2 (Raw Attribution)

- [X] T019 [US2] Implement `code/raw_attribution.py` to generate **raw ownership attribution files** (per-file owner lists) for each repo.
 **Specifics**:
 1. Parse commit history to create a CSV for each repo: `data/intermediate/raw_ownership_<repo_name>.csv`.
 2. Columns: `file_path`, `author`, `commit_hash`, `timestamp`.
 3. **Constitution VI Compliance**: These files are the "raw ownership attribution files" required by Constitution Principle VI. They MUST be version-controlled.
 4. **Output**: One CSV per repo containing the full list of authors for every file in the shallow history.

### Implementation for User Story 2 (State Management)

- [X] T020 [US2] Implement `code/state_manager.py` for content hashing and versioning. **Specifics**:
 1. **Constitution Principle VI Compliance**: Compute content hashes for all `raw_ownership_*.csv` files in `data/intermediate/`.
 2. **Versioning Logic**: Record these hashes in `state/projects/PROJ-062-quantifying-the-impact-of-code-ownership.yaml`.
 3. **Dependency**: This task MUST run after T019 (Raw Attribution Generation).
 4. **Rationale**: This aligns with Constitution Principle VI by ensuring the raw attribution data is hashed and recorded in the state file.

### Implementation for User Story 2 (Git Tracking)

- [X] T021 [US2] Update `.gitignore` to ensure `raw_ownership_*.csv` files are **TRACKED** by Git. **Specifics**:
 1. **Constitution Principle VI Compliance**: Ensure `raw_ownership_*.csv` files are **NOT** ignored.
 2. **Gitignore Logic**: Add `data/raw/` and `data/intermediate/*.csv` (generic) to `.gitignore`, but explicitly **DO NOT** add `raw_ownership_*.csv` to the ignore list.
 3. **Verification**: Confirm that `git status` shows `raw_ownership_*.csv` files as tracked, not ignored.
 4. **Dependency**: This task MUST run after T019 (Generation) and T020 (Hashing) to ensure files exist before tracking.
 5. **Rationale**: This satisfies Constitution Principle VI's requirement for files to be "included in the repository" and "version-controlled" (Git tracking) for reviewer recomputation.

**Checkpoint**: Raw attribution files generated, hashed, and tracked by Git.

---

## Phase 5: User Story 2 - Ownership and Quality Metric Calculation (Priority: P2)

**Goal**: Calculate Gini coefficient, code churn, cyclomatic complexity, and normalized bug density.

**Independent Test**: Verify Gini ∈ [0,1], complexity ≥95% valid, and bug density per KLOC calculated correctly.

### Implementation for User Story 2 (Metrics)

- [X] T022 [US2] Implement `code/metrics_calc.py` to calculate Gini coefficient per module from raw ownership CSVs (precision ≥3 decimals)
- [X] T023 [US2] Implement `code/metrics_calc.py` to filter out modules deleted between T and T+1 for BOTH predictor and outcome (FR-008)
- [X] T024 [US2] Implement `code/metrics_calc.py` to calculate code churn (lines added/deleted) per module
- [X] T025 [US2] Implement `code/metrics_calc.py` to compute cyclomatic complexity using `radon` on the latest snapshot (exclude non-Python files). **Verification**: Count total Python modules and modules with valid scores. Assert that `valid_count / total_count >= 0.95`. If the threshold is not met, log a critical warning and fail the task (or stop the pipeline) to prevent downstream analysis on invalid data.
- [X] T026 [US2] Implement `code/metrics_calc.py` to calculate normalized bug density (bugs/KLOC), excluding modules with 0 lines of code
- [X] T027 [US2] Implement `code/metrics_calc.py` to calculate module Size (KLOC) and Age (months since creation). **Note**: This task must also generate the `Gini²` (Gini squared) term for use in T033.
- [X] T028 [US2] Create `tests/unit/test_metrics_calc.py` to verify Gini calculation, KLOC normalization, and complexity scoring
- [X] T029 [US2] Create `tests/integration/test_metrics_pipeline.py` to verify end-to-end metric generation from intermediate CSVs

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 6: User Story 3 - Statistical Correlation Analysis and Visualization (Priority: P3)

**Goal**: Perform Spearman correlation, VIF diagnostics, non-linearity tests, sensitivity analysis, and visualization.

**Independent Test**: Verify correlation coefficients, p-values, VIF, sensitivity sweeps, and scatter plots are generated.

### Implementation for User Story 3

- [X] T030 [US3] Implement `code/statistical_analysis.py` to perform Spearman rank correlation (Gini vs. bug density) using `scipy.stats`. **Reproducibility**: Read `RANDOM_SEED` from `code/config.py` (set in T007) and log it in the output. **Dependencies**: Depends on T007.
- [X] T031 [US3] Implement `code/statistical_analysis.py` to calculate confidence intervals for correlation coefficients. **Reproducibility**: Read `RANDOM_SEED` from `code/config.py` and log it. **Dependencies**: Depends on T007, T030.
- [X] T032 [US3] Implement `code/statistical_analysis.py` to calculate VIF for predictors as required by FR-013. **Specifics**:
 1. **Calculate VIF for non-collinear predictors**: Size, Age.
 2. **Exclusion Logic**: Explicitly **exclude** Gini and Gini² from VIF calculation because they are mathematically collinear (Plan Complexity Tracking).
 3. **Output Requirement**: Report "N/A" or "Excluded (Collinear)" for Gini/Gini² in the VIF table. **Log the exclusion reason** in the final report to satisfy the "all predictors" requirement by addressing the collinearity constraint.
 4. **Traceability**: This exclusion is authorized by the Plan's "Complexity Tracking" section which states "Standard VIF on Gini+Gini² is mathematically infinite". The Spec's "all predictors" is interpreted as "all non-collinear predictors" per this technical constraint, with explicit documentation of the exclusion.
 5. **Dependencies**: Depends on T007, T030, T031.
- [X] T033 [US3] Implement `code/statistical_analysis.py` to apply multiple-comparison correction (Bonferroni or Benjamini-Hochberg) (FR-011). **Reproducibility**: Read `RANDOM_SEED` from `code/config.py` and log it. **Dependencies**: Depends on T007, T030, T031, T032.
- [X] T034 [US3] Implement `code/statistical_analysis.py` to test for non-linearity. **Specifics**:
 1. Fit a linear model (Outcome ~ Gini + Size + Age) and a quadratic model (Outcome ~ Gini + Gini² + Size + Age).
 2. **Important**: Gini² is **EXCLUDED** from VIF (T032) but **INCLUDED** in this quadratic model.
 3. Perform a Likelihood Ratio Test (LRT) to compare models.
 4. **Primary Metric**: Report the **LRT p-value** as the primary metric for non-linearity evidence (FR-016, Plan.md).
 5. **Secondary Metric**: Report the t-test p-value for the Gini² coefficient as a secondary diagnostic.
 6. **Output Artifact**: Write results to `data/results/nonlinearity_test.json` containing LRT p-value, t-test p-value, and model coefficients.
 7. **Dependencies**: Depends on T007, T027 (Gini² generation), T030, T031. (Note: Does NOT depend on T032 VIF).
- [X] T035 [US3] [SC-008] Implement `code/statistical_analysis.py` to perform p-value sensitivity analysis. **Sweep Set**: Explicitly use the set `{0.01, 0.05, 0.1}` as defined in SC-008. **Reproducibility**: Read the `RANDOM_SEED` from `code/config.py` (set in T007) and log this seed in the output. **Algorithm**: For each cutoff in the sweep set, filter the correlation results, count how many are significant, and write the summary to a CSV. **Output**:
 1. **Raw Data**: Generate `data/results/sensitivity_pvalue_raw.csv` containing the full list of correlations tested (columns: `repo_id`, `gini`, `bug_density`, `p_value`, `significant_at_0.01`, `significant_at_0.05`, `significant_at_0.1`, `random_seed`).
 2. **Summary**: Generate `data/results/sensitivity_pvalue.csv` (columns: `cutoff`, `count_significant`, `count_total`, `random_seed`).
 3. **Plot**: Generate `data/results/sensitivity_stability_plot.png` showing the stability of significant counts across cutoffs.
 4. **Summary JSON**: Generate `data/results/sensitivity_summary.json` summarizing the robustness findings.
 5. **Dependencies**: Depends on T007, T030, T031, T032, T033, T034.
- [X] T036 [US3] [SC-011] Implement `code/statistical_analysis.py` to perform correlation magnitude sensitivity analysis. **Sweep Set**: Explicitly use the set `{0.2, 0.3, 0.4}` as defined in SC-011. **Reproducibility**: Read the `RANDOM_SEED` (value 42) from `code/config.py` (set in T007) and log this seed in the output. **Algorithm**: For each cutoff in the sweep set, filter the correlation results by magnitude, count how many are significant, and write the summary to a CSV. **Output**:
 1. **Raw Data**: Generate `data/results/sensitivity_rho_raw.csv` containing the full list of correlations tested (columns: `repo_id`, `gini`, `bug_density`, `rho`, `significant_at_0.2`, `significant_at_0.3`, `significant_at_0.4`, `random_seed`).
 2. **Summary**: Generate `data/results/sensitivity_rho.csv` (columns: `cutoff`, `count_significant`, `count_total`, `random_seed`).
 3. **Plot**: Generate `data/results/sensitivity_stability_plot.png` (or a combined plot) showing stability.
 4. **Summary JSON**: Generate `data/results/sensitivity_summary.json` summarizing the robustness findings.
 5. **Dependencies**: Depends on T007, T030, T031, T032, T033, T034, T035.
- [X] T037 [US3] Implement `code/visualizations.py` to generate scatter plots with regression lines (≥300 DPI) for ≥8 repos. **Reproducibility**: Read `RANDOM_SEED` from `code/config.py` and log it.
- [X] T038 [US3] Implement `code/main.py` to orchestrate the full pipeline, ensuring temporal separation (T vs T+1) and associational framing (FR-010). **Output**: Write the final report to `data/results/final_report.json`. **Critical Requirement**: The report's "Interpretation" and "Conclusion" sections MUST explicitly frame results as "associational rather than causal" and discuss limitations (e.g., observational nature, path-based heuristic), not just include a metadata string. **Dependencies**: Ensure T034, T035, T036 complete before final report generation. **Reproducibility**: Log `RANDOM_SEED` in the final report.
- [X] T039 [US3] Create `tests/unit/test_statistical_analysis.py` to verify correlation, VIF, and regression logic. **Reproducibility**: Verify that `RANDOM_SEED` is used.
- [X] T040 [US3] Create `tests/integration/test_analysis_pipeline.py` to verify full statistical output JSON and plot generation.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T041 [P] Documentation updates in `docs/README.md` and `specs/001-code-ownership-analysis/research.md`
- [ ] T042 Code cleanup and refactoring to ensure peak RAM ≤7 GB and runtime ≤6 hours
- [X] T043 [P] [Review] Add explicit `streaming=True` logic in `code/data_collection.py` for any large repo fetches to prevent OOM, with fallback to `itertools.islice` for the first N rows if RAM limits are approached, ensuring no synthetic data is ever used.
- [X] T044 [P] [Review] Add a strict `try/except` block in `code/data_collection.py` that raises a `DataFetchError` if GitHub API or git clone fails, ensuring NO synthetic/mock data fallback is possible per Constitution Data Hygiene rules.
- [X] T045 [P] [Review] Update `code/metrics_calc.py` to explicitly log the exact sample size and any streaming/sampling rules used, ensuring transparency on data representativeness as per Constitution Principle II.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Raw Attribution & State (Phase 4)**: Depends on Phase 3 (Data Collection) completion
 - **T019 must complete before T020 and T021**.
 - **T020 must complete before T021**.
- **Metrics (Phase 5)**: Depends on Phase 4 (Raw Attribution) completion
- **Analysis (Phase 6)**: Depends on Phase 5 (Metrics) completion
 - **T029-T040 depend on T007 (RANDOM_SEED)**.
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **Raw Attribution (Phase 4)**: Depends on US1 data (intermediate CSVs)
- **Metrics (Phase 5)**: Depends on Raw Attribution (Phase 4)
- **Analysis (Phase 6)**: Depends on Metrics (Phase 5)

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
3. Add Raw Attribution (Phase 4) → Test independently → Deploy/Demo
4. Add Metrics (Phase 5) → Test independently → Deploy/Demo
5. Add Analysis (Phase 6) → Test independently → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1
 - Developer B: Raw Attribution (Phase 4)
 - Developer C: Metrics (Phase 5)
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