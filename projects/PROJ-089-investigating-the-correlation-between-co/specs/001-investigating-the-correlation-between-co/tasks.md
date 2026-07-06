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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001a Create project root directories: `code/`, `data/`, `tests/`, `contracts/`
- [ ] T001b Create data subdirectories: `data/raw/`, `data/processed/`, `data/results/`, `data/logs/`
- [ ] T002 Initialize Python 3.11 project with pinned dependencies in `requirements.txt` (pandas, numpy, scipy, statsmodels, scikit-learn, matplotlib, seaborn, pydriller, radon, sonar-scanner, tqdm, requests)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Create schema definitions in `contracts/` (`dataset.schema.yaml`, `output.schema.yaml`, `tool_validation_log.schema.yaml`)
- [ ] T005 Implement `config.py` with parameter defaults (LOC thresholds, repo limits, tool versions)
- [ ] T006 Implement `utils.py` for logging, checksum utilities, and random seed pinning
- [ ] T007 Create `data/` directory structure (`raw/`, `processed/`, `results/`, `logs/`)
- [ ] T008 Implement `main.py` orchestrator with error handling and timeout logic

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Automatically select repositories, clone them, extract git history and static analysis metrics, and produce a unified CSV with density metrics.

**Independent Test**: Run the pipeline on 3 fixed public repos; verify `data/processed/unified_metrics.csv` contains non-null rows for `churn_density`, `debt_density`, `debt_score`, and `avg_loc` for every file, and that `tool_validation_log.csv` records star counts and validation status.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T009 [P] [US1] Contract test for `unified_metrics.csv` schema in `tests/contract/test_dataset_schema.py`
- [ ] T010 [P] [US1] Integration test for repo cloning and filtering in `tests/integration/test_data_extraction.py`

### Implementation for User Story 1

- [ ] T011 [P] [US1] Implement `data_extraction.py`: Query GitHub API for >500-star repos, filter by age (>2 years) and language
- [ ] T012 [P] [US1] Implement `data_extraction.py`: Clone repos and extract per-file commit counts & lines changed (last 2 years) using `pydriller`
- [ ] T013 [P] [US1] Implement `static_analysis.py`: Run `radon` (v2.4.0) on Python files to calculate CC and MI
- [ ] T014 [P] [US1] Implement `static_analysis.py`: Run `sonar-scanner` CLI (v10.4 LTS) with 'SonarQube Community Rules' profile on Java, JS, TS, Go, Rust files to capture Code Smells and Cyclomatic Complexity; calculate `debt_score` = Sum(Code Smells + CC)
- [ ] T015 [US1] Implement `preprocessing.py`: Filter non-source-code files and exclude files with `avg_loc` < 10 (parameterized default)
- [ ] T015b [US1] Implement `preprocessing.py`: Re-run filtering logic for sensitivity thresholds (5, 10, 20, 30) to prepare datasets for FR-008 analysis
- [ ] T016 [US1] Implement `preprocessing.py`: Calculate `churn_density` (total_lines_changed / avg_loc), `debt_density` (debt_score / avg_loc), `avg_loc`, and `contributor_count`; generate `data/processed/unified_metrics.csv`
- [ ] T017 [US1] Implement `preprocessing.py`: Generate `data/raw/repos_metadata.csv`
- [ ] T018a [US1] Implement `utils.py`: Record tool versions and GitHub star counts in `data/logs/tool_validation_log.csv` (Depends on T011-T014 completion)
- [ ] T018b [US1] Implement `utils.py`: Verify tool validation per SC-005: check if tool matches 'Kitchenham et al. 2009' or 'Meneely et al. 2009' OR has >5,000 GitHub stars; log validation status

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Correlation Analysis (Priority: P2)

**Goal**: Calculate correlation between churn density and debt density, controlling for confounders, and perform sensitivity analysis.

**Independent Test**: Feed the pipeline a synthetic CSV with known correlation; verify output reports `r` within ±0.05 and `p < 0.05`, and that VIF warnings trigger Ridge regression if collinearity is high.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T019 [P] [US2] Contract test for `correlation_results.csv` schema in `tests/contract/test_output_schema.py`
- [ ] T020 [P] [US2] Integration test for mixed-effects model execution in `tests/integration/test_analysis.py`

### Implementation for User Story 2

- [ ] T021 [US2] Implement `analysis.py`: Load `unified_metrics.csv` (Depends on T016); perform VIF check on covariates (`project_age`, `language`, `contributor_count`); apply Ridge regression if VIF > 5
- [ ] T022 [US2] Implement `analysis.py`: Fit mixed-effects model: `debt_density ~ churn_density + avg_loc + covariates + (1|repo_id)`
- [ ] T023 [US2] Implement `analysis.py`: Calculate Pearson and Spearman correlation coefficients on `churn_density` vs `debt_density`, controlling for `avg_loc`
- [ ] T024 [US2] Implement `analysis.py`: Perform Bonferroni correction on p-values across repositories (FR-006)
- [ ] T025 [US2] Implement `analysis.py`: Run sensitivity analysis (Phase 4b) re-running the model with `avg_loc` thresholds of 5, 10, 20, and 30 using datasets from T015b
- [ ] T026 [US2] Implement `analysis.py`: Generate `data/results/correlation_results.csv` and `data/results/sensitivity_analysis.csv`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualization and Reporting (Priority: P3)

**Goal**: Generate scatter plots with regression lines and a summary report.

**Independent Test**: Run the reporting module on sample data; verify `data/results/plots/` contains PNGs with annotated `r` and `p` values, and `summary_report.txt` exists.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T027 [P] [US3] Contract test for `summary_report.txt` content in `tests/contract/test_report_schema.py`
- [ ] T028 [P] [US3] Integration test for plot generation in `tests/integration/test_visualization.py`

### Implementation for User Story 3

- [ ] T029 [P] [US3] Implement `visualization.py`: Generate scatter plots (X: churn_density, Y: debt_density) with regression lines per repository
- [ ] T030 [US3] Implement `visualization.py`: Annotate plots with correlation coefficient (`r`) and p-value; save to `data/results/plots/`
- [ ] T031 [US3] Implement `reporting.py`: Generate `summary_report.txt` listing per-repo and aggregate results, flagging `|r| ≥ 0.3` as 'moderate' for density metrics
- [ ] T032 [US3] Implement `reporting.py`: Include Bonferroni-corrected meta-analysis outcome and sensitivity analysis table in the report
- [ ] T033a [US3] Implement `main.py`: Measure and log total pipeline execution time against 6-hour limit (SC-003)
- [ ] T033 [US3] Implement `main.py`: Finalize pipeline by computing checksums and updating `state/projects/...yaml` (Phase 7)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T034a [P] Update `quickstart.md` with installation and execution instructions
- [ ] T034b [P] Update `research.md` with methodology details and validation study citations
- [ ] T035 Code cleanup and refactoring of `preprocessing.py` and `analysis.py`
- [ ] T036 Performance optimization: Ensure parallelism is limited to 2 concurrent repo processes
- [ ] T037 [P] Additional unit tests in `tests/unit/` for metric calculation logic
- [ ] T038 Run `quickstart.md` validation to ensure end-to-end reproducibility

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
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 analysis output

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Config before services
- Data Extraction (T011-T012) before Static Analysis (T013-T014)
- Static Analysis before Preprocessing (T015-T017)
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members (e.g., T011-T018 vs T021-T026)

---

## Parallel Example: User Story 1

```bash
# Launch all data extraction tasks for User Story 1 together:
Task: "Query GitHub API and clone repos" (T011)
Task: "Run Radon on Python files" (T013)
Task: "Run SonarQube on other languages" (T014)
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
- **Critical**: The tasks now explicitly calculate density metrics (churn_density, debt_density) as required by FR-001, FR-002, and FR-003, and use Bonferroni correction as per FR-006.