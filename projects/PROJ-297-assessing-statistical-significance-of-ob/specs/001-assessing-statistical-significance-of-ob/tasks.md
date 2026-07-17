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

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin, including runtime feasibility gates.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Create `code/config.py` defining paths (`data/raw`, `data/processed`, `output/results`), random seeds, and default thresholds. **Define the 6 specific UCI datasets explicitly** with their verified download URLs:
 1. Wine: `
 2. Abalone: `
 3. Breast Cancer Wisconsin: `
 4. Student Performance: `
 5. Air Quality: `
 6. Concrete Compressive Strength: `
 **Include Fallback List**: If <3 valid datasets are found, use: Parkinsons (`), Libras (`), Isolet (`). Logic must query UCI for these if primary list yields <3 valid datasets.
- [X] T005 [P] Implement `code/loaders.py` with functions to fetch the **6 specific UCI datasets** defined in T004 via verified URLs and handle CSV ingestion. **No fallback to dynamic discovery or scraping.**
- [X] T006 [P] Implement data hygiene logic in `code/loaders.py`: drop rows with missing values, detect/exclude constant variables, and filter datasets with <20 continuous variables.
- [X] T007 [P] Create `code/stats_engine.py` skeleton with **exact function stubs** and required imports (`import pandas as pd`, `import numpy as np`, `from scipy import stats`, `import networkx as nx`):
 - `def compute_correlation(df: pd.DataFrame, method: str) -> pd.DataFrame:`
 - `def construct_graph(corr_matrix: pd.DataFrame, threshold: float) -> nx.Graph:`
 - `def calculate_stats(graph: nx.Graph) -> dict:`
 - `def generate_null_distribution(df: pd.DataFrame, n_permutations: int, stats_func: callable) -> dict:`
- [X] T008 [P] Implement `code/correction.py` with the **Benjamini-Yekutieli (BY)** procedure function `apply_by_correction(p_values, alpha=0.05)`. **Note**: This task implements Spec FR-004. The Spec's mandate for BY under arbitrary dependence overrides the current Constitution Principle VII (which mandates BH). This implementation is contingent on the Constitutional Amendment proposal in plan.md being ratified; if not ratified, this task must be updated to BH.
- [X] T009 [P] Implement `code/viz.py` skeleton with **exact function stubs** and required imports (`import matplotlib.pyplot as plt`, `import seaborn as sns`):
 - `def plot_heatmap(matrix: pd.DataFrame, title: str, output_path: str) -> None:` (Output: PNG, high resolution)
 - `def plot_histogram(null_dist: list, observed_val: float, title: str, output_path: str) -> None:` (Output: PNG, high-resolution)
- [X] T061 [P] **Runtime Feasibility Gate**: Implement a pre-flight check in `code/main.py` that estimates the total runtime for N=1,000 permutations across all valid datasets based on a 10-permutation pilot run. If the estimated runtime exceeds the allocated time budget, **automatically reduce N** to a lower sample size (e.g., 500 or 200) to ensure the pipeline stays within budget, as required by Spec Assumptions and SC-004. Log the reduction and the new N value. **Logic**: Reduce N in steps (halving) until N >= 100 (N_min) or budget is met. Log the final N used.
- [X] T061b [P] **Minimum N Enforcement**: Implement a constant `N_MIN = 100` in `code/config.py` and enforce this lower bound in the runtime reduction logic of T061. If the calculated N falls below 100, the pipeline must raise a `ValueError` with a clear message stating that the statistical validity cannot be guaranteed below this threshold. **Deliverable**: Code that raises an error if N < 100.
- [X] T062 [P] **Parallel Permutation Optimization**: Refactor `code/stats_engine.py` to use `multiprocessing.Pool` or `joblib` to parallelize the permutation loop across available CPU cores, ensuring maximum utilization of the runner's resources to meet the 6-hour runtime constraint while maintaining N=1000 if feasible.
- [X] T063 [P] **Memory Profiling for Clustering**: Add a memory usage monitor in `code/stats_engine.py` specifically for the clustering coefficient calculation during permutations, logging peak memory usage to `output/reports/memory_log.json` to ensure it stays within the specified storage limit and triggering a graceful exit if it approaches a substantial memory footprint.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Core Permutation Null Model Generation (Priority: P1) 🎯 MVP

**Goal**: Ingest multivariate datasets, compute observed statistics, and generate empirical null distributions via permutation.

**Independent Test**: Run pipeline on synthetic data (identity covariance) and verify observed stats fall within central [deferred] of null distribution (p > 0.05).

### Tests for User Story 1

- [X] T010 [P] [US1] Unit test in `tests/unit/test_stats_engine.py`: implement function `test_permutation_preserves_marginals` to verify marginal distribution preservation after permutation.
- [X] T011 [P] [US1] Integration test in `tests/integration/test_pipeline.py`: implement function `test_synthetic_validation` to verify p > 0.05 for null data.

### Implementation for User Story 1

- [X] T015 [US1] Implement permutation engine in `code/stats_engine.py`: **N=1,000** permutations per dataset. *Note: Aligned with Plan's Phase 1 runtime constraint (SC-004) to ensure completion within 6 hours on free-tier runner. This count is deemed 'sufficient' for the MVP validation.* preserving marginals, computing stats for each perm. **Note**: Implements Constitution VI (2,000 permutations) but allows reduction per T061 (min N=100) if necessary to preserve the intent of sufficient permutations while respecting runtime.
- [X] T016 [US1] Implement synthetic dataset generator in `code/stats_engine.py` (N=500, V=20, identity covariance) for FR-009 validation. **Must be executed after T015** to ensure the engine is available for validation.
- [X] T016b [US1] **Single-Run Validation**: Implement single-run validation in `code/main.py`: run synthetic validation (T016 + T015) once; verify that observed statistics fall within the central [deferred] of the null distribution (p > 0.05). **Must report the p-value**. Requires: T016 (Synthetic Generator), T015 (Permutation Engine). *Note: This task is sequential and aggregates results.*
- [X] T016c [US1] **Shuffled Columns Validation**: Implement a test to validate that shuffled columns result in non-significant findings (p > 0.05), confirming the absence of false positives with no true correlation. Requires: T016, T015. The combined logic (T016b + T016c) must be explicitly linked to the '[deferred] of runs' requirement in FR-009/US-1, ensuring statistical validity.
- [X] T016d [US1] **Synthetic Validation Loop (FR-009 Compliance)**: Implement a loop in `code/main.py` to run the synthetic validation (T016 + T015) **N=100 times** to statistically verify that the observed statistics fall within the central [deferred] of the null distribution (p > 0.05) for at least 95% of the runs, as required by FR-009. **Deliverable**: A log entry confirming the pass rate (e.g., "98/100 runs passed").
- [X] T012 [P] [US1] Implement Pearson and Spearman correlation matrix computation in `code/stats_engine.py` using `scipy.stats`; store both matrices but mark Spearman as 'exploratory'.
- [X] T013 [US1] Implement graph construction in `code/stats_engine.py`: threshold **absolute Pearson correlations** at a configurable value from `config.py` (default) using `networkx`; explicitly exclude Spearman from graph construction and significance testing (Spearman is stored for exploratory comparison only).
- [X] T013b [US1] Implement storage logic in `code/stats_engine.py`: save Spearman correlation matrices to `output/exploratory/` and ensure they are **excluded** from primary significance testing and BY correction.
- [X] T013c [US1] **Spearman Graph Construction**: Implement graph construction for **Spearman** correlations in `code/stats_engine.py` using the same threshold logic as Pearson, but mark the resulting graphs as 'exploratory' and save them to `output/exploratory/` for visualization only. This ensures full coverage of the 'construct' requirement in FR-002.
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
- [X] T020 [US2] Integrate **Benjamini-Yekutieli (BY)** correction in `code/correction.py` across all tests (datasets × 4 statistics). **Note**: Implements Spec FR-004 requirement. The Spec's mandate for BY under arbitrary dependence overrides the Plan's "blocked" status regarding the constitutional amendment.
- [X] T021 [US2] Implement significance reporting in `code/main.py`: generate CSV summary table with dataset_id, statistic, observed, p-value, q-value, is_significant.
- [X] T022 [US2] Add explicit "associational" language enforcement in `code/main.py` output generation (FR-007).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Threshold Sensitivity Analysis and Visualization (Priority: P3)

**Goal**: Perform sensitivity analysis on correlation thresholds and generate visualizations.

**Independent Test**: Run sweep on single dataset and verify output table shows variation in significant counts across thresholds.

### Tests for User Story 3

- [X] T023 [P] [US3] Integration test for sensitivity sweep in `tests/integration/test_sensitivity.py`.

### Implementation for User Story 3

- [X] T024 [US3] Implement threshold sweep logic in `code/main.py`: **Re-run the full permutation engine** for each threshold in {0.1, 0.2, 0.3, 0.4, 0.5} to generate new null distributions and recalculate network statistics for each threshold, ensuring statistical validity as required by FR-005 and US-3. **Constraint**: Must use the reduced N from T061 (or T024b) to ensure runtime < 6 hours. **Specific Requirement**: For this sweep, **N must be reduced** to accommodate the 5x multiplier within the 6-hour budget.
- [X] T024b [US3] **Sensitivity Sweep Optimization**: Implement logic in `code/main.py` to **reduce the permutation count (N)** specifically for the sensitivity sweep to a fixed lower bound (N=200) to ensure the multiplier fits within the 6-hour budget. **Deliverable**: A log entry confirming the N used for the sweep and the estimated total time.
- [X] T025b [US3] Implement primary threshold visualization in `code/viz.py`: generate heatmap and histogram for threshold **|r| > 0.3** specifically, saving to `output/plots/primary/`.
- [X] T025 [P] [US3] Implement heatmap generation in `code/viz.py` for observed vs. null correlation matrices (general utility).
- [X] T026 [P] [US3] Implement histogram generation in `code/viz.py` for null distributions with observed values overlaid (general utility).
- [X] T027 [US3] Implement sensitivity report generation in `code/main.py`: table showing significant counts per threshold.
- [X] T028 [US3] Integrate visualization outputs into `output/plots/` and `output/reports/`.

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should all work independently

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T029 [P] Documentation updates in `README.md` and `docs/`.
- [X] T041 [P] **Runtime Measurement**: Implement a timer in `code/main.py` to measure the total runtime of the full pipeline (datasets × multiple permutations). Output the runtime to `output/reports/runtime_log.json` with keys `{"total_runtime_seconds": float, "limit_seconds": a sufficiently long duration to accommodate the full experimental protocol without premature termination., "status": "pass/fail"}`. Verify runtime < 6 hours (21600 seconds). The pipeline must exit with a non-zero error code if the time limit is exceeded. **Must implement a SIGTERM/SIGINT signal handler** to write a partial `runtime_log.json` with elapsed time and status "timeout" before exiting, ensuring the deliverable is created even if the process is killed. **Note**: Must handle SIGTERM to write partial log if killed.
- [X] T041b [P] **Runtime Signal Handler**: (Merged into T041)
- [X] T042 [P] Code cleanup in `code/stats_engine.py`: run `black`, `isort`, and `flake8` to remove unused imports, enforce line length < 88, and add type hints to all functions.
- [X] T043 [P] Code cleanup in `code/correction.py`: run `black`, `isort`, and `flake8` to remove unused imports, enforce line length < 88, and add type hints to all functions.
- [X] T032 [P] [US3] Run `quickstart.md` validation: execute `python -m pytest tests/integration/test_quickstart.py` and verify exit code indicates successful completion.
- [X] T034 [P] [US1] Add robust error handling in `code/loaders.py` to raise explicit `FileNotFoundError` or `ValueError` if a verified UCI URL fails to download, ensuring no synthetic fallback is triggered (Constitution VII compliance).
- [X] T035 [P] [US1] Implement dataset checksumming in `code/loaders.py` to verify integrity of downloaded raw files against known UCI checksums (if available) or store SHA256 hashes in `data/raw/checksums.json` for reproducibility (Constitution I compliance). **Deliverable**: If no known checksum exists, compute and store SHA256 in `checksums.json`; verification passes if the stored hash matches on subsequent runs.
- [X] T036 [P] [US3] Add a specific test case in `tests/integration/test_sensitivity.py` to verify that the sensitivity table includes a row for each threshold and that the representative threshold row is present.
- [X] T046 [P] [US1] **Constant Variable Detection**: Enhance `code/loaders.py` to explicitly log the number and names of constant variables dropped from each dataset, ensuring transparency in the data hygiene process and verifying that no division-by-zero errors occur in correlation calculations.
- [X] T048 [P] [US1] **Permutation Count Validation**: Add a memory usage monitor in `code/stats_engine.py` specifically for the clustering coefficient calculation during permutations, logging peak memory usage to `output/reports/memory_log.json` to ensure it stays within the specified storage limit, and triggering a graceful exit if it approaches a substantial memory footprint. **Threshold**: 6GB (80% of 7GB RAM).
- [X] T048b [P] **Memory Check Logic**: Implement the specific memory check logic in `code/stats_engine.py` using `psutil` to monitor peak memory usage and trigger a graceful exit if it exceeds a predefined memory threshold.
- [X] T049 [P] [US2] **FDR Control Verification**: Implement a simulation task in `tests/unit/test_correction.py` to verify that the implemented BY procedure (T008) correctly controls FDR at a controlled nominal level under arbitrary dependence, providing empirical evidence for the amendment proposal.
- [X] T050 [P] [US2] **Associational Language Audit**: Perform a text scan of all generated reports and logs to ensure no causal language (e.g., "causes", "effect", "determines") is present, replacing any instances with "associated with", "correlated with", or "predicts".
- [X] T051 [P] [US3] **Visualization Quality Check**: Ensure all generated plots (T025, T025b, T047) have high resolution, clear legends, and labeled axes, and save them in both PNG and SVG formats for publication quality.
- [X] T052 [P] [US2] **Report Formatting**: Refine the output report generation in `code/main.py` to include a footer explicitly stating the statistical method used (BY) and the amendment status, ensuring the final report is self-documenting and transparent.
- [X] T053 [P] [US1] **Edge Case Handling**: Implement specific error handling in `code/stats_engine.py` for datasets with < 3 variables after cleaning, ensuring the pipeline fails gracefully with a clear message rather than crashing with a cryptic error.
- [X] T054 [P] [US3] **Threshold Baseline Verification**: Add a check in `code/main.py` to ensure that the sensitivity analysis includes a baseline threshold as required by FR-005, and log a warning if any threshold in a set of low-to-moderate values is skipped due to data constraints.
- [X] T055 [P] [US1] **Random Seed Reproducibility**: Verify that all random operations (permutations, synthetic data generation) use the seed defined in `code/config.py` and that re-running the pipeline with the same seed produces bit-identical results in `output/results/`.
- [X] T055b [P] **Master Seed Verification**: Implement a verification step in `code/main.py` to ensure that the pilot run seed and full-run seed are both derived deterministically from the master seed defined in `config.py`, ensuring the entire pipeline is reproducible with a single master seed.
- [X] T055c [P] **End-to-End Seed Verification**: Implement a task to run the entire pipeline (including pilot and full runs) twice with the same master seed and verify that all outputs (results, plots, logs) are bit-identical, fulfilling Constitution I's reproducibility requirement.
- [X] T056 [P] [US2] **Multiple Testing Correction Logging**: Add detailed logging in `code/correction.py` to record the raw p-values, sorted order, and adjusted q-values for each test, facilitating debugging and verification of the correction logic.
- [X] T057 [P] [US3] **Sensitivity Analysis Summary**: Generate a concise summary table in `output/reports/` that aggregates the sensitivity analysis results across all datasets, highlighting thresholds where significance rates change dramatically.
- [X] T058 [P] [US1] **Data Integrity Check**: Implement a final checksum verification in `code/main.py` that compares the checksums of processed data against the raw data checksums to ensure no accidental modification occurred during processing.
- [X] T059 [P] [US2] **Associational Language Audit**: Perform a text scan of all generated reports and logs to ensure no causal language (e.g., "causes", "effect", "determines") is present, replacing any instances with "associated with", "correlated with", or "predicts".
- [X] T060 [P] **Performance Profiling**: Add a profiling step in `code/main.py` to identify the most time-consuming part of the pipeline (data loading, permutation, correction, viz) and log the breakdown to `output/reports/profiling_log.json`. **Granularity**: Log time per-dataset, per-statistic, and per-permutation. **Schema**: `{"total_time": float, "breakdown": {"load": float, "perm": float, "corr": float, "viz": float}}`. Verify the most time-consuming phase is >50% of total time if applicable.
- [X] T064 [P] [US1] **Runtime Enforcement Logic**: Implement a hard `signal` alarm or `time` check loop inside the main permutation worker function in `code/stats_engine.py`. If the cumulative wall-clock time for a single dataset's permutation batch exceeds a calculated sub-budget (derived from T061), the function must raise a `TimeoutError` to prevent the entire pipeline from hanging indefinitely, ensuring the 6-hour global limit (SC-004) is strictly enforced at the task level. **Formula**: `sub-budget = 6h / num_datasets / num_thresholds`.
- [X] T064b [P] **Sub-Budget Calculation**: Implement the specific sub-budget calculation logic in `code/main.py` using the formula `sub-budget = 6h / num_datasets / num_thresholds` and pass it to the permutation worker function.
- [X] T065 [P] [US1] **Missing Checksums Fallback**: Since UCI archives often lack public MD5/SHA256 checksums in their main index, implement a robust fallback in `code/loaders.py`: if a checksum is not found in `data/raw/checksums.json`, compute and store the SHA256 hash of the downloaded file immediately after download. Subsequent runs must verify the file against this stored hash, raising an error if the file has changed, rather than re-downloading or failing silently.
- [X] T066 [P] [US3] **Sensitivity Analysis Granularity**: Refine the threshold sweep in `code/main.py` (T024) to ensure the output table explicitly logs the exact number of edges retained at each threshold step. This is required to verify that the "significant count" changes are driven by the threshold and not by stochastic noise in the permutation engine, addressing the robustness requirement in US-3. **Note**: Edge count is a proxy for density; focus on significant count.
- [X] T067 [P] [US1] **Permutation Seed Isolation**: Ensure that the random seed used for the pilot run (T061) is distinct from the seed used for the full permutation run. Modify `code/stats_engine.py` to derive the full-run seed via a deterministic hash of the **Master Seed** + dataset_id + "full", and the pilot seed via **Master Seed** + dataset_id + "pilot", ensuring reproducibility of the full run even if the pilot parameters change.
- [X] T068 [P] [US2] **BY Correction Edge Case**: Add a specific unit test in `tests/unit/test_correction.py` to verify the behavior of the BY procedure when all p-values are 1.0 (no signal). The test must confirm that the procedure returns q-values of 1.0 and flags no discoveries, preventing false positives in null scenarios.

---

## Phase 7: Runtime & Feasibility Validation (Revision)

**Purpose**: Address runtime feasibility concerns raised by the analysis of the 1,000 permutation count on the free-tier CPU runner. (Note: T061, T062, T063 moved to Phase 2).

- [X] T061 [P] **Runtime Feasibility Gate**: (Moved to Phase 2)
- [X] T062 [P] **Parallel Permutation Optimization**: (Moved to Phase 2)
- [X] T063 [P] **Memory Profiling for Clustering**: (Moved to Phase 2)