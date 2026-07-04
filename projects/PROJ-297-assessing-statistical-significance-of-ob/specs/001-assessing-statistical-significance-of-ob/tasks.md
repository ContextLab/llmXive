# Tasks: Assessing Statistical Significance of Observed Correlations in Public Databases

**Input**: Design documents from `/specs/001-assess-correlation-significance/`
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

- [ ] T001 Create project structure: `mkdir -p data/raw data/processed code/tests/unit code/tests/integration output/results output/plots output/reports output/exploratory` and create `requirements.txt` in the project root.
- [ ] T002 Initialize Python 3.x project with `pandas`, `numpy`, `scipy`, `networkx`, `matplotlib`, `seaborn` in `requirements.txt`.
- [ ] T003 [P] Configure linting: Create `.flake8` (max-line-length=88, exclude=.git,__pycache__) and `pyproject.toml` with `[tool.black]` section (line-length=88, target-version=['py311']) in the project root.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Create `code/config.py` defining paths (`data/raw`, `data/processed`, `output/results`), random seeds, default thresholds, and the **fallback dataset list**: `['Parkinsons', 'Libras', 'Isolet']` for use by T017.
- [ ] T005 [P] Implement `code/loaders.py` with functions to fetch UCI datasets via verified URLs and handle CSV ingestion.
- [ ] T006 [P] Implement data hygiene logic in `code/loaders.py`: drop rows with missing values, detect/exclude constant variables, and filter datasets with <20 continuous variables.
- [ ] T017 [P] Implement data gate logic in `code/loaders.py`: read fallback dataset list from `config.py`; if primary list yields <3 valid datasets, query UCI for secondary datasets in order ('Parkinsons', 'Libras', 'Isolet') until a sufficient number of valid datasets are found.
- [ ] T007 [P] Create `code/stats_engine.py` skeleton with **exact function stubs** and required imports (`import pandas as pd`, `import numpy as np`, `from scipy import stats`, `import networkx as nx`):
  - `def compute_correlation(df: pd.DataFrame, method: str) -> pd.DataFrame: ...`
  - `def construct_graph(corr_matrix: pd.DataFrame, threshold: float) -> nx.Graph: ...`
  - `def calculate_stats(graph: nx.Graph) -> dict: ...`
  - `def generate_null_distribution(df: pd.DataFrame, n_permutations: int, stats_func: callable) -> dict: ...`
- [ ] T008 [P] Implement `code/correction.py` with the Benjamini-Yekutieli (BY) procedure function (blocking FR-004).
- [ ] T009 [P] Implement `code/viz.py` skeleton with **exact function stubs** and required imports (`import matplotlib.pyplot as plt`, `import seaborn as sns`):
  - `def plot_heatmap(matrix: pd.DataFrame, title: str, output_path: str) -> None: ...` (Output: PNG, high resolution)
  - `def plot_histogram(null_dist: list, observed_val: float, title: str, output_path: str) -> None: ...` (Output: PNG, 300 DPI)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Core Permutation Null Model Generation (Priority: P1) 🎯 MVP

**Goal**: Ingest multivariate datasets, compute observed statistics, and generate empirical null distributions via permutation.

**Independent Test**: Run pipeline on synthetic data (identity covariance) and verify observed stats fall within central [deferred] of null distribution (p > 0.05) in >=95% of runs.

### Tests for User Story 1

- [ ] T010 [P] [US1] Unit test in `tests/unit/test_stats_engine.py`: implement function `test_permutation_preserves_marginals` to verify marginal distribution preservation after permutation.
- [ ] T011 [P] [US1] Integration test in `tests/integration/test_pipeline.py`: implement function `test_synthetic_validation` to verify p > 0.05 for null data.

### Implementation for User Story 1

- [ ] T012 [P] [US1] Implement Pearson and Spearman correlation matrix computation in `code/stats_engine.py` using `scipy.stats`; store both matrices but mark Spearman as 'exploratory'.
- [ ] T013 [US1] Implement graph construction in `code/stats_engine.py`: threshold **absolute Pearson correlations** at a configurable value from `config.py` (default) using `networkx`; explicitly exclude Spearman from graph construction and significance testing (Spearman is stored for exploratory comparison only).
- [ ] T013b [US1] Implement storage logic in `code/stats_engine.py`: save Spearman correlation matrices to `output/exploratory/` and ensure they are **excluded** from primary significance testing and BY correction.
- [ ] T014 [US1] Implement network statistic calculation in `code/stats_engine.py`: Mean Absolute Correlation, Edge Density, Max Absolute Correlation, Average Clustering Coefficient.
- [ ] T016 [US1] Implement synthetic dataset generator in `code/stats_engine.py` (N=500, V=20, identity covariance) for FR-009 validation; **must be executed before T015** to validate the null model.
- [ ] T016b [US1] Implement **repeated validation loop** in `code/main.py`: run synthetic validation (T016 + T015) **100 times**; verify that observed statistics fall within the central [deferred] of the null distribution (p > 0.05) in at least 95 runs (>=95% success rate).
- [ ] T015 [US1] Implement permutation engine in `code/stats_engine.py`: **N=2,000** permutations per dataset (aligning with FR-003 and Constitution Principle VI). *Note: This overrides Plan feasibility concern; Spec requirement takes precedence.* preserving marginals, computing stats for each perm.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Multiple Testing Correction and Significance Reporting (Priority: P2)

**Goal**: Apply Benjamini-Yekutieli correction to empirical p-values and generate summary tables.

**Independent Test**: Feed known p-values to `code/correction.py` and verify q-values and significance flags match expected BY results.

### Tests for User Story 2

- [ ] T018 [P] [US2] Unit test for BY procedure in `tests/unit/test_correction.py` (verify FDR control under dependence).

### Implementation for User Story 2

- [ ] T019 [US2] Implement empirical p-value calculation in `code/stats_engine.py` using formula $(r+1)/(N+1)$ to avoid 0/1.
- [ ] T020 [US2] Integrate BY correction in `code/correction.py` across all tests (datasets × 4 statistics). *Note: Assumes Constitution Amendment (BH->BY) is ratified per Plan governance; implements FR-004 requirement.*
- [ ] T021 [US2] Implement significance reporting in `code/main.py`: generate CSV summary table with dataset_id, statistic, observed, p-value, q-value, is_significant.
- [ ] T022 [US2] Add explicit "associational" language enforcement in `code/main.py` output generation (FR-007).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Threshold Sensitivity Analysis and Visualization (Priority: P3)

**Goal**: Perform sensitivity analysis on correlation thresholds and generate visualizations.

**Independent Test**: Run sweep on single dataset and verify output table shows variation in significant counts across thresholds {0.1, 0.2, 0.3, 0.4, 0.5}.

### Tests for User Story 3

- [ ] T023 [P] [US3] Integration test for sensitivity sweep in `tests/integration/test_sensitivity.py`.

### Implementation for User Story 3

- [ ] T025b [US3] Implement **primary threshold visualization** in `code/viz.py`: generate heatmap and histogram for threshold **|r| > 0.3** specifically, saving to `output/plots/primary/`. **Must execute before T024.**
- [ ] T024 [US3] Implement threshold sweep logic in `code/main.py`: re-run permutation and significance for thresholds in **{0.1, 0.2, 0.3, 0.4, 0.5}** (including 0.1 baseline per FR-005); **requires T020 (Correction) to be complete**; output summary table showing significant counts per threshold. *Note: Aligns with Spec FR-005, overriding Plan omission of 0.1.*
- [ ] T025 [P] [US3] Implement heatmap generation in `code/viz.py` for observed vs. null correlation matrices (general utility).
- [ ] T026 [P] [US3] Implement histogram generation in `code/viz.py` for null distributions with observed values overlaid (general utility).
- [ ] T027 [US3] Implement sensitivity report generation in `code/main.py`: table showing significant counts per threshold, **explicitly including the 0.1 baseline data point**.
- [ ] T028 [US3] Integrate visualization outputs into `output/plots/` and `output/reports/`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T029 [P] Documentation updates in `README.md` and `docs/`.
- [ ] T030 Code cleanup and refactoring in `code/`: run `black .`, `isort .`, and `flake8 .` to remove unused imports, enforce line length < 88, and add type hints to all functions in `code/`.
- [ ] T031 Performance optimization: Implement a conditional check in `code/stats_engine.py` to reduce N to 500 for clustering coefficient if variable count > 50 to ensure runtime < 6h.
- [ ] T032 [P] Run `quickstart.md` validation: execute `python -m pytest tests/integration/test_quickstart.py` and verify exit code is 0.
- [ ] T033 Verify Constitution Amendment (BY vs BH) is noted in final report.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
  - **T017 (Data Gate)** must complete before T005/T006 ingestion tasks to ensure correct dataset set is established.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - **T016 (Synthetic Generator)** must complete before T015 (Permutation Engine).
  - **T020 (Correction)** must complete before T024 (Sensitivity Sweep).
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 statistics
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1/US2 pipeline (specifically T020)

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
# Launch all tests for User Story 1 together:
Task: "Unit test in tests/unit/test_stats_engine.py: test_permutation_preserves_marginals"
Task: "Integration test in tests/integration/test_pipeline.py: test_synthetic_validation"

# Launch all core logic for User Story 1 together (after T016):
Task: "Implement permutation engine in code/stats_engine.py"
Task: "Implement network statistic calculation in code/stats_engine.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently on synthetic data (T016b)
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
   - Developer A: User Story 1 (Core Engine)
   - Developer B: User Story 2 (Correction & Reporting)
   - Developer C: User Story 3 (Sensitivity & Viz)
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
- **Critical Constraint**: All tasks must run on CPU-only CI (cores, sufficient RAM, no GPU). No 8-bit quantization or large model loading.
- **Data Integrity**: Use only real UCI datasets. No synthetic data for final results (only for validation).
- **Constitution**: Await ratification of BY procedure amendment before finalizing Phase 1 execution. T020 enforces this gate.
- **Plan Alignment**: Tasks T015 and T024 implement N=2,000 and threshold {0.1..0.5} per spec FR-003/FR-005, overriding plan.md omissions (flagged for plan amendment).