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

- **Single project**: `code/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan in `projects/PROJ-062-quantifying-the-impact-of-code-ownership/`
- [X] T002 Initialize a Python project with `requirements.txt` containing `GitPython`, `scikit-learn`, `scipy`, `pandas`, `numpy`, `radon`, `matplotlib`, `pyyaml` in `code/requirements.txt`
- [ ] T003 [P] Configure linting (flake8/black) and formatting tools in `code/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Create directory structure: `data/raw`, `data/intermediate`, `data/results`, `tests/contract`, `tests/integration`, `tests/unit`, `docs` in `projects/PROJ-062-quantifying-the-impact-of-code-ownership/`
- [ ] T005 [P] Implement logging infrastructure with file rotation to `logs/pipeline.log` ensuring disk usage stays within 14 GB limit
- [X] T006 [P] Implement path normalization function in `code/utils/path_utils.py` (lowercase, strip.bak/.pyc/.min.js/.lock, normalize slashes) per FR-009
- [~] T007 Create data schema definitions in `specs/001-code-ownership-analysis/contracts/dataset.schema.yaml` and `output.schema.yaml`
- [~] T008 [P] Implement memory management utility in `code/utils/memory_utils.py` to process one repository at a time and clear memory between iterations to ensure peak RAM ≤7 GB (FR-007)
- [~] T009 [P] Implement exponential backoff utility in `code/utils/api_utils.py` with ≤3 retries and ≥60-second delay for GitHub API calls (FR-006)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Repository Data Collection and Processing (Priority: P1) 🎯 MVP

**Goal**: Download Git repositories, parse commit logs for ownership, and extract bug counts via path-based heuristic.

**Independent Test**: Can be fully tested by verifying that a set of valid repositories are successfully cloned with shallow history (sufficient depth), commit logs are parsed into ownership data, and bug metadata is retrieved for at least 8 repositories.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [~] T010 [P] [US1] Contract test for data schema validation in `tests/contract/test_data_schema.py`
- [~] T011 [P] [US1] Integration test for repository cloning and shallow history extraction in `tests/integration/test_clone_repo.py`
- [~] T012 [P] [US1] Unit test for path normalization logic in `tests/unit/test_path_normalization.py`

### Implementation for User Story 1

- [~] T013 [US1] Implement `code/data_collection.py` to clone a representative set of GitHub repositories using `git clone --depth 1000` up to analysis cutoff T (FR-001)
- [~] T014 [US1] Implement commit log parsing in `code/data_collection.py` to extract committer, timestamp, file path, and line counts (FR-014)
- [~] T015 [US1] Implement bug retrieval in `code/data_collection.py` using GitHub Issues API with exponential backoff (FR-006)
- [ ] T016 [US1] Implement Bug-File Proximity Heuristic in `code/metrics_calc.py` to link issues to modules via exact path match (case-insensitive, normalized) by explicitly calling `code/utils/path_utils.py::normalize_path` (reuse T006) per FR-009
- [ ] T016b [US1] Implement word-boundary match logic in `code/metrics_calc.py` to ensure the Bug-File Proximity Heuristic performs exact full-filename matching (e.g., 'main.py' in text matches 'src/main.py' only if the full path is present) as required by FR-009
- [ ] T017 [US1] Implement logic to exclude modules deleted between time window T and T+1 from both predictor and outcome calculations (FR-008)
- [ ] T018 [US1] Write intermediate ownership CSVs to `data/intermediate/ownership.csv` and bug metadata to `data/intermediate/bugs.csv` with disk-based storage (FR-007)
- [ ] T019 [US1] Implement logic to skip repositories with <1000 commits (FR-001), log warnings, and ensure >=8 valid repositories remain (Edge Case handling)
- [ ] T020 [US1] Implement logic to handle division by zero when calculating KLOC for modules with 0 lines of code (Edge Case handling)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Ownership and Quality Metric Calculation (Priority: P2)

**Goal**: Calculate ownership concentration (Gini), code churn, complexity, and normalized bug density.

**Independent Test**: Can be fully tested by verifying that Gini coefficients are computed for all modules, code churn values are calculated for ≥90% of modules, and normalized bug density is available for statistical analysis.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T021 [P] [US2] Unit test for Gini coefficient calculation with precision ≥3 decimal places in `tests/unit/test_gini.py`
- [ ] T022 [P] [US2] Unit test for cyclomatic complexity calculation using `radon` in `tests/unit/test_complexity.py`
- [ ] T023 [P] [US2] Integration test for end-to-end metric calculation pipeline in `tests/integration/test_metrics_pipeline.py`

### Implementation for User Story 2

- [ ] T024 [US2] Implement Gini coefficient calculation in `code/metrics_calc.py` using shallow history (depth 1000) up to time T, explicitly excluding modules deleted between T and T+1 from the predictor (ownership) calculation (FR-002, FR-008)
- [ ] T025 [US2] Implement code churn calculation (lines added/deleted) per module in `code/metrics_calc.py`
- [ ] T026 [US2] Implement cyclomatic complexity calculation using `radon` library on the latest snapshot for ≥95% of modules (FR-003)
- [ ] T027 [US2] Implement normalized bug density calculation (bugs per KLOC) with ≥2 decimal precision in `code/metrics_calc.py`
- [ ] T028 [US2] Implement logic to explicitly exclude modules deleted between T and T+1 from outcome (bug density) calculations (FR-008)
- [ ] T029 [US2] Write calculated metrics to `data/intermediate/metrics.csv` with module ID, Gini, churn, complexity, and bug density
- [ ] T030 [US2] Implement validation to ensure Gini coefficient values are ∈ [0.0, 1.0] (Acceptance Scenario 1)
- [ ] T050 [US2] Implement validation logic to explicitly verify the temporal alignment of the T and T+1 windows for excluded modules, ensuring no data leakage or survivorship bias occurs due to misaligned windows by cross-referencing the exclusion logic from T024 and T028 (FR-008)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Correlation Analysis and Visualization (Priority: P3)

**Goal**: Perform Spearman correlation, VIF diagnostics, non-linearity tests, sensitivity analysis, and generate visualizations.

**Independent Test**: Can be fully tested by verifying that correlation coefficients are computed with p-values, VIF is reported, multiple-comparison correction is applied, non-linearity is tested, and scatter plots are generated.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T031 [P] [US3] Unit test for Spearman correlation and p-value calculation in `tests/unit/test_correlation.py`
- [ ] T032 [P] [US3] Unit test for VIF calculation and non-linearity detection in `tests/unit/test_vif_nonlinear.py`
- [ ] T033 [P] [US3] Integration test for full statistical analysis and visualization generation in `tests/integration/test_stats_analysis.py`

### Implementation for User Story 3

- [ ] T034 [US3] Implement Spearman rank correlation analysis using `scipy.stats` in `code/statistical_analysis.py` (FR-004)
- [ ] T035 [US3] Implement confidence interval calculation for correlation coefficients (Acceptance Scenario 1)
- [ ] T036 [US3] Implement Variance Inflation Factor (VIF) calculation for predictors (Gini, Gini², Size, Age) in `code/statistical_analysis.py` (FR-013)
- [ ] T037 [US3] Implement logic to flag VIF ≥5 and generate a descriptive framing statement in the output explicitly stating independent effects are not claimed (FR-013, SC-009)
- [ ] T038 [US3] Implement multiple-comparison correction (Bonferroni or Benjamini-Hochberg) for >1 hypothesis tests (FR-011, SC-010)
- [ ] T039 [US3] Implement non-linearity test by fitting a quadratic regression model (Outcome ~ Gini + Gini² + Size + Age), performing a Likelihood Ratio Test (LRT) to compare it against the linear model, AND explicitly extracting and reporting the p-value for the Gini² coefficient to verify its statistical significance (FR-016, SC-012)
- [ ] T040 [US3] Implement sensitivity analysis for p-value threshold by sweeping values over a set of small magnitudes and writing a JSON object mapping each threshold to the count of significant findings to `data/results/sensitivity_pvalue.json` (FR-012, SC-008)
- [ ] T041 [US3] Implement sensitivity analysis for correlation magnitude threshold by sweeping values over a set of representative low-magnitude parameters and writing a JSON object mapping each threshold to the count of significant findings to `data/results/sensitivity_correlation.json` (FR-015, SC-011)
- [ ] T042 [US3] Generate scatter plots with regression lines using `matplotlib` saved as PNG files (≥300 DPI) for ≥8 repositories (FR-005, SC-005)
- [ ] T043 [US3] Write final JSON summary to `data/results/statistical_summary.json` containing correlation, p-value, CI, VIF, and correction results (FR-004, SC-001)
- [ ] T044 [US3] Add a `framing_notes` field to `data/results/statistical_summary.json` explicitly stating findings are associational, not causal (FR-010, SC-004)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T045 [P] Documentation updates in `docs/README.md` and `quickstart.md`
- [ ] T046 Validate peak RAM usage ≤7 GB during full pipeline run and document results (NFR-001)
- [ ] T047 [P] Additional unit tests for edge cases (empty modules, API failures) in `tests/unit/`
- [ ] T048 Run quickstart.md validation to ensure end-to-end reproducibility
- [ ] T049 Verify all artifacts are hashed and recorded in `state/` for versioning discipline (Constitution Principle V)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - **Strict Sequential Data Flow**: US2 implementation requires US1 data output (T018, T016b). US3 implementation requires US2 metric output (T029).
 - Implementation tasks CANNOT be parallelized across US1, US2, and US3 unless data interfaces are mocked.
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on US1 data output (T018) - Cannot start until US1 data is generated
- **User Story 3 (P3)**: Depends on US2 metric output (T029) - Cannot start until US2 metrics are generated

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Utilities before services
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel.
- All Foundational tasks marked [P] can run in parallel (within Phase 2).
- **Implementation Parallelism**: US1, US2, and US3 implementation tasks CANNOT run in parallel on real data. They must be executed sequentially (US1 -> US2 -> US3) because US2 depends on US1's CSV outputs and US3 depends on US2's CSV outputs.
- **Mocking Exception**: Parallel execution is ONLY possible if developers mock the intermediate CSV outputs (US1 data for US2, US2 data for US3) to decouple implementation. Without mocking, strict sequential execution is required.
- All tests for a specific user story marked [P] can run in parallel.

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

1. Team completes Setup + Foundational together.
2. **Sequential Execution Required**:
 - Developer A: User Story 1 (Data Collection) -> Must complete first.
 - Developer B: User Story 2 (Metric Calculation) -> Can only start after US1 data is available (or mocked).
 - Developer C: User Story 3 (Statistical Analysis) -> Can only start after US2 metrics are available (or mocked).
3. If mocking is used, developers can work in parallel on logic, but integration requires the real data flow.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **CPU Constraint**: All tasks must run on a limited CPU configuration with constrained memory and disk space, without GPU acceleration. No 8-bit/4-bit models, no CUDA, no large LLMs.
- **Data Integrity**: All data must come from real sources (GitHub API, git clone). No synthetic/fake data generation.