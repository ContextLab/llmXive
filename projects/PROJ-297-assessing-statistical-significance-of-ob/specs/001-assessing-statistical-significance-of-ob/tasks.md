# Tasks: Assessing Statistical Significance of Observed Correlations in Public Databases

**Input**: Design documents from `/specs/001-assess-correlation-significance/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

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

- [X] T001 Create project structure: `mkdir -p data/raw data/processed code/tests/unit code/tests/integration output/results output/plots output/reports output/exploratory` and create `requirements.txt` in the project root.
- [X] T002 Initialize Python 3.x project with `pandas`, `numpy`, `scipy`, `networkx`, `matplotlib`, `seaborn` in `requirements.txt`.
- [X] T003 [P] Configure linting: Create `.flake8` (max-line-length=88, exclude=.git,__pycache__) and `pyproject.toml` with `[tool.black]` section (line-length=88, target-version=['py311']) in the project root.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Create `code/config.py` defining paths (`data/raw`, `data/processed`, `output/results`), random seeds, and default thresholds. **Define the 6 specific UCI datasets explicitly** with their verified download URLs:
 1. Wine: `
 2. Abalone: `
 3. Breast Cancer Wisconsin: `
 4. Student Performance: ` (and student-mat.csv)
 5. Air Quality: `
 6. Concrete Compressive Strength: `
 **Include Fallback List**: If <3 valid datasets are found, use: Parkinsons (`), Libras (`), Isolet (`). Logic must query UCI for these if primary list yields <3 valid datasets.
- [X] T005 [P] Implement `code/loaders.py` with functions to fetch the **6 specific UCI datasets** defined in T004 via verified URLs and handle CSV ingestion. **No fallback to dynamic discovery or scraping.**
- [X] T006 [P] Implement data hygiene logic in `code/loaders.py`: drop rows with missing values, detect/exclude constant variables, and filter datasets with <20 continuous variables.
- [X] T007 [P] Create `code/stats_engine.py` skeleton with **exact function stubs** and required imports (`import pandas as pd`, `import numpy as np`, `from scipy import stats`, `import networkx as nx`):
 - `def compute_correlation(df: pd.DataFrame, method: str) -> pd.DataFrame:...`
 - `def construct_graph(corr_matrix: pd.DataFrame, threshold: float) -> nx.Graph:...`
 - `def calculate_stats(graph: nx.Graph) -> dict:...`
 - `def generate_null_distribution(df: pd.DataFrame, n_permutations: int, stats_func: callable) -> dict:...`
- [X] T008 [P] Implement `code/correction.py` with the **Benjamini-Yekutieli (BY)** procedure function `apply_by_correction(p_values, alpha=0.05)`. **Note**: This task implements the requirement from Spec FR-004. The Spec's mandate for BY under arbitrary dependence overrides the Plan's "blocked" status regarding the constitutional amendment. The Spec is the governing constraint for implementation.
- [X] T009 [P] Implement `code/viz.py` skeleton with **exact function stubs** and required imports (`import matplotlib.pyplot as plt`, `import seaborn as sns`):
 - `def plot_heatmap(matrix: pd.DataFrame, title: str, output_path: str) -> None:...` (Output: PNG, high resolution)
 - `def plot_histogram(null_dist: list, observed_val: float, title: str, output_path: str) -> None:...` (Output: PNG, high-resolution)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Core Permutation Null Model Generation (Priority: P1) 🎯 MVP

**Goal**: Ingest multivariate datasets, compute observed statistics, and generate empirical null distributions via permutation.

**Independent Test**: Run pipeline on synthetic data (identity covariance) and verify observed stats fall within central [deferred] of null distribution (p > 0.05) in >=95% of runs.

### Tests for User Story 1

- [X] T010 [P] [US1] Unit test in `tests/unit/test_stats_engine.py`: implement function `test_permutation_preserves_marginals` to verify marginal distribution preservation after permutation.
- [X] T011 [P] [US1] Integration test in `tests/integration/test_pipeline.py`: implement function `test_synthetic_validation` to verify p > 0.05 for null data.

### Implementation for User Story 1

- [X] T016 [US1] Implement synthetic dataset generator in `code/stats_engine.py` (N=500, V=20, identity covariance) for FR-009 validation. **Must be executed before T015** to provide input for validation.
- [X] T015 [US1] Implement permutation engine in `code/stats_engine.py`: **N=1,000** permutations per dataset. *Note: Aligned with Plan's Phase 1 runtime constraint (SC-004) to ensure completion within 6 hours on free-tier runner. This count is deemed 'sufficient' for the MVP validation.* preserving marginals, computing stats for each perm.
- [X] T016b [US1] Implement **single-run validation** in `code/main.py`: run synthetic validation (T016 + T015) once; verify that observed statistics fall within the central [deferred] of the null distribution (p > 0.05). **Must report the p-value**. Requires: T016 (Synthetic Generator), T015 (Permutation Engine). *Note: This task is sequential and aggregates results. Replaces the unrequested 100-run meta-analysis with a single validation run matching Spec US-1.*
- [X] T012 [P] [US1] Implement Pearson and Spearman correlation matrix computation in `code/stats_engine.py` using `scipy.stats`; store both matrices but mark Spearman as 'exploratory'.
- [X] T013 [US1] Implement graph construction in `code/stats_engine.py`: threshold **absolute Pearson correlations** at a configurable value from `config.py` (default) using `networkx`; explicitly exclude Spearman from graph construction and significance testing (Spearman is stored for exploratory comparison only).
- [X] T013b [US1] Implement storage logic in `code/stats_engine.py`: save Spearman correlation matrices to `output/exploratory/` and ensure they are **excluded** from primary significance testing and BY correction.
- [X] T014 [US1] Implement network statistic calculation in `code/stats_engine.py`: Mean Absolute Correlation, Edge Density, Max Absolute Correlation, Average Clustering Coefficient.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Multiple Testing Correction and Significance Reporting (Priority: P2)

**Goal**: Apply Benjamini-Yekutieli correction to empirical p-values and generate summary tables.

**Independent Test**: Feed known p-values to `code/correction.py` and verify q-values and significance flags match expected BY results.

### Tests for User Story 2

- [X] T018 [P] [US2] Unit test for BY procedure in `tests/unit/test_correction.py` (verify FDR control under arbitrary dependence).

### Implementation for User Story 2

- [X] T019 [US2] Implement empirical p-value calculation in `code/stats_engine.py` using formula $(r+1)/(N+1)$ to avoid 0/1.
- [X] T020 [US2] Integrate **Benjamini-Yekutieli (BY)** correction in `code/correction.py` across all tests (datasets × 4 statistics). **Note**: Implements Spec FR-004 requirement. The Spec's mandate for BY under arbitrary dependence overrides the Plan's "blocked" status regarding the constitutional amendment. The Spec is the governing constraint.
- [X] T021 [US2] Implement significance reporting in `code/main.py`: generate CSV summary table with dataset_id, statistic, observed, p-value, q-value, is_significant.
- [X] T022 [US2] Add explicit "associational" language enforcement in `code/main.py` output generation (FR-007).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Threshold Sensitivity Analysis and Visualization (Priority: P3)

**Goal**: Perform sensitivity analysis on correlation thresholds and generate visualizations.

**Independent Test**: Run sweep on single dataset and verify output table shows variation in significant counts across thresholds.

The research question remains: Does the variation in significant counts depend on the chosen threshold?
The method remains: Systematic evaluation of significant counts across a range of threshold values.
References: (No specific references provided in the original passage to preserve).

### Tests for User Story 3

- [X] T023 [P] [US3] Integration test for sensitivity sweep in `tests/integration/test_sensitivity.py`.

### Implementation for User Story 3

- [X] T024 [US3] Implement threshold sweep logic in `code/main.py`: re-calculate network statistics on **existing permuted correlation matrices** for thresholds in a range of values (per Spec FR-005) to avoid re-running the permutation engine; **Requires: T015, T020**; output summary table showing significant counts per threshold. *Note: Explicitly lists thresholds to override Plan's ambiguity. Must complete before T025b. Reusing matrices ensures executability within 6-hour budget.*
- [X] T025b [P] [US3] Implement **primary threshold visualization** in `code/viz.py`: generate heatmap and histogram for threshold **|r| > 0.3** specifically, saving to `output/plots/primary/`. **Must execute after T024** (sweep generates data for visualization).
- [X] T025 [P] [US3] Implement heatmap generation in `code/viz.py` for observed vs. null correlation matrices (general utility).
- [X] T026 [P] [US3] Implement histogram generation in `code/viz.py` for null distributions with observed values overlaid (general utility).
- [X] T027 [US3] Implement sensitivity report generation in `code/main.py`: table showing significant counts per threshold, **explicitly including the 0.1 baseline data point**.
- [X] T028 [US3] Integrate visualization outputs into `output/plots/` and `output/reports/`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T029 [P] Documentation updates in `README.md` and `docs/`.
- [X] T041 [P] **Runtime Measurement**: Implement a timer in `code/main.py` to measure the total runtime of the full pipeline (datasets × 1,000 permutations). Output the runtime to `output/reports/runtime_log.json` with keys `{"total_runtime_seconds": float, "limit_seconds": 21600, "status": "pass/fail"}`. Verify runtime < 6 hours (21600 seconds). *Note: This task is required to satisfy SC-004.*
- [X] T042 [P] Code cleanup in `code/stats_engine.py`: run `black`, `isort`, and `flake8` to remove unused imports, enforce line length < 88, and add type hints to all functions.
- [X] T043 [P] Code cleanup in `code/correction.py`: run `black`, `isort`, and `flake8` to remove unused imports, enforce line length < 88, and add type hints to all functions.
- [X] T032 [P] [US3] Run `quickstart.md` validation: execute `python -m pytest tests/integration/test_quickstart.py` and verify exit code indicates successful completion.
- [X] T034 [P] [US1] Add robust error handling in `code/loaders.py` to raise explicit `FileNotFoundError` or `ValueError` if a verified UCI URL fails to download, ensuring no synthetic fallback is triggered (Constitution VII compliance).
- [X] T035 [P] [US1] Implement dataset checksumming in `code/loaders.py` to verify integrity of downloaded raw files against known UCI checksums (if available) or store SHA256 hashes in `data/raw/checksums.json` for reproducibility (Constitution I compliance).
- [X] T036 [P] [US3] Add a specific test case in `tests/integration/test_sensitivity.py` to verify that the sensitivity table includes a row for each threshold and that the representative threshold row is present.
- [X] T046 [P] [US1] **Constant Variable Detection**: Enhance `code/loaders.py` to explicitly log the number and names of constant variables dropped from each dataset, ensuring transparency in the data hygiene process and verifying that no division-by-zero errors occur in correlation calculations.
- [X] T048 [P] [US1] **Permutation Count Validation**: Add a diagnostic task in `code/main.py` to verify that the chosen permutation count (N=1,000) yields stable p-values (e.g., standard error < 0.01) by running a small pilot on one dataset, ensuring statistical power without unnecessary runtime.
- [X] T049 [P] [US2] **FDR Control Verification**: Implement a simulation task in `tests/unit/test_correction.py` to verify that the implemented BY procedure (T008) correctly controls FDR at a controlled nominal level under arbitrary dependence, providing empirical evidence for the amendment proposal.
- [X] T050 [P] [US1] **Missing Value Strategy Documentation**: Update `README.md` and `code/config.py` comments to explicitly document the "drop rows with missing values" strategy, explaining why imputation was rejected (to preserve marginal distribution integrity for permutation).
- [X] T051 [P] [US3] **Visualization Quality Check**: Ensure all generated plots (T025, T025b, T047) have high resolution, clear legends, and labeled axes, and save them in both PNG and SVG formats for publication quality.
- [X] T052 [P] [US2] **Report Formatting**: Refine the output report generation in `code/main.py` to include a footer explicitly stating the statistical method used (BY) and the amendment status, ensuring the final report is self-documenting and transparent.
- [X] T053 [P] [US1] **Edge Case Handling**: Implement specific error handling in `code/stats_engine.py` for datasets with < 3 variables after cleaning, ensuring the pipeline fails gracefully with a clear message rather than crashing with a cryptic error.
- [X] T054 [P] [US3] **Threshold Baseline Verification**: Add a check in `code/main.py` to ensure that the threshold sweep includes the 0.1 baseline as required by FR-005, and log a warning if any threshold in the set {0.1, 0.2, 0.3, 0.4, 0.5} is skipped due to data constraints.
- [X] T055 [P] [US1] **Random Seed Reproducibility**: Verify that all random operations (permutations, synthetic data generation) use the seed defined in `code/config.py` and that re-running the pipeline with the same seed produces bit-identical results in `output/results/`.
- [X] T056 [P] [US2] **Multiple Testing Correction Logging**: Add detailed logging in `code/correction.py` to record the raw p-values, sorted order, and adjusted q-values for each test, facilitating debugging and verification of the correction logic.
- [X] T057 [P] [US3] **Sensitivity Analysis Summary**: Generate a concise summary table in `output/reports/` that aggregates the sensitivity analysis results across all datasets, highlighting thresholds where significance rates change dramatically.
- [X] T058 [P] [US1] **Data Integrity Check**: Implement a final checksum verification in `code/main.py` that compares the checksums of processed data against the raw data checksums to ensure no accidental modification occurred during processing.
- [X] T059 [P] [US2] **Associational Language Audit**: Perform a text scan of all generated reports and logs to ensure no causal language (e.g., "causes", "effect", "determines") is present, replacing any instances with "associated with", "correlated with", or "predicts".
- [X] T060 [P] **Performance Profiling**: Add a profiling step in `code/main.py` to identify the most time-consuming part of the pipeline (data loading, permutation, correction, viz) and log the breakdown to `output/reports/profiling_log.json` with keys `{"phases": [{"name": str, "duration_seconds": float}], "most_time_consuming": str}`. Verify the most time-consuming phase is >50% of total time if applicable. *Note: This task is required to satisfy SC-004 and Plan performance goals.*

---

## Phase 6: Future Work & Optimization

**Purpose**: Tasks marked as optional/future work, to be addressed after MVP completion.

- [X] T044 [P] [US1] **Data Stream Optimization**: Refactor `code/loaders.py` and `code/stats_engine.py` to process datasets in chunks if memory usage exceeds a significant threshold, ensuring the pipeline remains within the GB RAM limit of the free runner. This task addresses the constraint that large datasets might cause OOM errors during the 1,000 permutation loop.
- [X] T047 [P] [US3] **Sensitivity Plot Generation**: Implement a line plot in `code/viz.py` showing the number of significant findings (y-axis) vs. correlation threshold (x-axis) for the full set of datasets, providing a visual summary of robustness as required by FR-005.

---

## Phase 7: Runtime & Feasibility Validation (Revision)

**Purpose**: Address runtime feasibility concerns raised by the analysis of the 1,000 permutation count on the free-tier CPU runner.

- [X] T061 [P] [US1] **Runtime Feasibility Gate**: Implement a pre-flight check in `code/main.py` that estimates the total runtime for N=1,000 permutations across all valid datasets based on a 10-permutation pilot run. If the estimated runtime exceeds several hours, log a CRITICAL warning and suggest reducing N to a lower sample size, but **do not** automatically reduce it; instead, require explicit user confirmation or a configuration override to proceed, ensuring the Plan's N=1,000 requirement is respected unless manually overridden.
- [X] T062 [P] [US1] **Parallel Permutation Optimization**: Refactor `code/stats_engine.py` to use `multiprocessing.Pool` or `joblib` to parallelize the permutation loop across available CPU cores (A limited number of cores on the free tier), ensuring maximum utilization of the runner's resources to meet the 6-hour runtime constraint while maintaining N=1,000.
- [X] T063 [P] [US1] **Memory Profiling for Clustering**: Add a memory usage monitor in `code/stats_engine.py` specifically for the clustering coefficient calculation during permutations, logging peak memory usage to `output/reports/memory_log.json` to ensure it stays within the specified storage limit, and triggering a graceful exit if it approaches a substantial memory footprint..

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

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