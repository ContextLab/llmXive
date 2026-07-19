---
description: "Task list template for feature implementation"
---

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
- [X] T002 Initialize Python 3.x project with `pandas`, `numpy`, `scipy`, `networkx`, `matplotlib`, `seaborn`, `openpyxl`, `xlrd`, `requests`, `psutil` in `requirements.txt`.
- [X] T003 [P] Configure linting: Create `.flake8` (max-line-length=88, exclude=.git,__pycache__) and `pyproject.toml` with `[tool.black]` section (line-length=88, target-version=['py311']) in the project root.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin, including runtime feasibility gates and constitutional checks.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Create `code/config.py` defining paths (`data/raw`, `data/processed`, `output/results`), random seeds, and default thresholds. **Define the 6 specific UCI datasets explicitly** with their verified download URLs:
 1. Wine: `https://archive.ics.uci.edu/ml/machine-learning-databases/wine/wine.data`
 2. Abalone: `https://archive.ics.uci.edu/ml/machine-learning-databases/abalone/abalone.data`
 3. Breast Cancer Wisconsin: `https://archive.ics.uci.edu/ml/machine-learning-databases/breast-cancer-wisconsin/breast-cancer-wisconsin.data`
 4. Student Performance: `https://archive.ics.uci.edu/ml/machine-learning-databases/00234/student-mat.zip` (Requires unzip logic and merging of `student-mat.csv` for both genders)
 5. Air Quality: `https://archive.ics.uci.edu/ml/machine-learning-databases/00360/AirQualityUCI.zip` (Requires unzip logic)
 6. Concrete Compressive Strength: `https://archive.ics.uci.edu/ml/machine-learning-databases/00292/Concrete_Compressive_Strength.xls`
 **Note**: If fewer than 3 valid datasets (>=20 continuous variables) are found after processing these 6, the system MUST trigger T005b to attempt fallback.
- [X] T005 [P] Implement `code/loaders.py` with functions to fetch the **6 specific UCI datasets** defined in T004 via verified URLs and handle CSV/Excel ingestion. **Implement the fallback strategy**: If the primary list yields <3 valid datasets, the system MUST automatically query the UCI repository for the next available multivariate datasets with >=20 continuous variables (e.g., 'Parkinsons', 'Libras', 'Isolet') until valid datasets are found or the repository is exhausted.
- [X] T005b [US1] **Fallback Discovery Logic**: (Sequential dependency on T005) If T005 fails to find >=3 valid datasets, implement the logic to query the UCI repository for additional datasets. This task is triggered by T005 if the primary list is insufficient.
- [X] T006 [P] Implement data hygiene logic in `code/loaders.py`: drop rows with missing values, detect/exclude constant variables, and filter datasets with <20 continuous variables.
- [X] T007 [P] Create `code/stats_engine.py` skeleton with **exact function stubs** and required imports (`import pandas as pd`, `import numpy as np`, `from scipy import stats`, `import networkx as nx`):
 - `def compute_correlation(df: pd.DataFrame, method: str) -> pd.DataFrame:`
 - `def construct_graph(corr_matrix: pd.DataFrame, threshold: float) -> nx.Graph:`
 - `def calculate_stats(graph: nx.Graph) -> dict:`
 - `def generate_null_distribution(df: pd.DataFrame, n_permutations: int, stats_func: callable) -> dict:`
- [X] T007c [P] **Constitutional State Generation (Producer)**: Implement a function in `code/constitution.py` to **create or update** `state/projects/PROJ-297-assessing-statistical-significance-of-ob.yaml`. This function MUST ensure the file exists with the key `amendment_status` set to `"pending"` if the file is missing or the key is absent. **This task MUST run BEFORE T007b** to guarantee the artifact required by the gate check is present.
- [X] T007b [P] **Constitutional Gate Block**: Implement a check in `code/main.py` (or a dedicated `code/constitution.py`) that verifies the ratification status of the Constitutional Amendment regarding the Benjamini-Yekutieli (BY) procedure. **The check MUST read from `state/projects/PROJ-297-assessing-statistical-significance-of-ob.yaml`**. **If the amendment is NOT ratified (status != "ratified"), the system MUST log a FATAL error and raise a `SystemExit` immediately, halting the pipeline.** The pipeline MUST NOT proceed with the Benjamini-Hochberg (BH) procedure. This enforces the Plan's requirement that execution is blocked until ratification. **Depends on T007c**.
- [X] T008 [P] Implement `code/correction.py` with the **Benjamini-Yekutieli (BY)** procedure function `apply_by_correction(p_values, alpha=0.05)`. **Gating**: This task depends on T007b passing. If T007b halts the pipeline, this code is not reached. If the pipeline proceeds, ONLY BY is used.
- [X] T009 [P] Implement `code/viz.py` skeleton with **exact function stubs** and required imports (`import matplotlib.pyplot as plt`, `import seaborn as sns`):
 - `def plot_heatmap(matrix: pd.DataFrame, title: str, output_path: str) -> None:` (Output: PNG, high resolution)
 - `def plot_histogram(null_dist: list, observed_val: float, title: str, output_path: str) -> None:` (Output: PNG, high-resolution)
- [X] T061 [P] **Runtime Feasibility Gate & Adaptive Reduction**: Implement a pre-flight check in `code/main.py` that estimates the total runtime for N=1,000 permutations (baseline per Plan Complexity Tracking) across all valid datasets based on a 10-permutation pilot run. **Logic**:
 1. Run a pilot of 10 permutations per dataset.
 2. Read the pilot log to calculate `estimated_time_per_permutation`.
 3. Calculate the total estimated runtime for N=1,000 across all datasets and thresholds.
 4. If the estimated runtime exceeds the allocated time budget (6 hours), **reduce N** to fit the budget, starting with reducing N for Average Clustering Coefficient to 500, and then reducing N globally if necessary.
 5. The system MUST enforce a lower bound of N=100 for the Average Clustering Coefficient and N=500 for other statistics. If the calculated N falls below these bounds, the system MUST log a WARNING but continue with the minimum allowed N to ensure the pipeline produces some results (partial success) rather than failing completely.
 6. Log the estimated time, the calculated N for each statistic, and the reason for any reduction.
 7. The pipeline must NOT raise a fatal exit if the budget is exceeded; it must adapt to the minimum allowed N.
 **Requirement**: The final report must explicitly state the N used and the reason for any reduction.
- [X] T062 [P] **Parallel Permutation Optimization**: Refactor `code/stats_engine.py` to use `multiprocessing.Pool` or `joblib` to parallelize the permutation loop across available CPU cores, ensuring maximum utilization of the runner's resources to meet the runtime constraint.
- [X] T063 [P] **Memory Profiling for Clustering**: Implement memory monitoring hooks in `code/stats_engine.py` specifically for the clustering coefficient calculation during permutations. The hooks must log peak memory usage to `output/reports/memory_log.json` and trigger a **graceful exit** if the usage exceeds **5.6 GB** (`MAX_MEMORY_GB = 5.6`). **Note**: This task sets up the monitoring logic; the actual monitoring occurs during the execution of T015.
- [X] T048 [P] **Memory Check Logic**: (Merged into T063)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Core Permutation Null Model Generation (Priority: P1) 🎯 MVP

**Goal**: Ingest multivariate datasets, compute observed statistics, and generate empirical null distributions via permutation.

**Independent Test**: Run pipeline on synthetic data (identity covariance) and verify observed stats fall within central [deferred] of null distribution (p > 0.05).

### Implementation for User Story 1

- [X] T015 [US1] Implement permutation engine in `code/stats_engine.py`: **N=1,000** permutations per dataset (per Plan Complexity Tracking), subject to adaptive reduction as defined in T061. **Note**: Implements Constitution VI. The final N is determined by T061's adaptive logic. **CRITICAL**: This task MUST save the **aggregated null distribution statistics** (mean, density, max, clustering) to `output/processed/null_stats.csv` with a defined schema: one row per dataset-statistic-permutation combination, including columns `dataset_id`, `statistic_name`, `permutation_id`, and `value`. **DO NOT save raw permuted correlation matrices** to avoid memory risks.
- [X] T016 [US1] Implement synthetic dataset generator in `code/stats_engine.py` (N=500, V=20, identity covariance) for FR-009 validation. **Must be executed after T015** to ensure the engine is available for validation.
- [X] T016b [US1] **Single-Run Validation Logic**: Implement the logic for a single synthetic validation run (T016 + T015) to be called by T016d. This includes generating the data, running permutations, calculating the p-value, and returning the result (p > 0.05). **Note**: This logic is executed 3 times by T016d.
- [X] T016c [US1] **Shuffled Columns Validation Logic**: Implement the logic for a single shuffled column validation run to be called by T016d. This includes shuffling columns, running permutations, calculating the p-value, and returning the result (p > 0.05). **Note**: This logic is executed 3 times by T016d.
- [X] T016d [US1] **Synthetic Validation Loop (FR-009 Compliance)**: Implement a loop in `code/main.py` to run the synthetic validation (T016 + T015) **3 times** (operational proxy for % confidence within budget) to statistically verify that the observed statistics fall within the central th-97.5th percentile of the null distribution (p > 0.05) for at least 95% of the runs. **Aggregation Logic**: Count the number of runs where p > 0.05. **If (count / 3) < 1.0 (i.e., less than 3/3 passes), the system MUST raise a `SystemExit` with a fatal error stating "Synthetic validation failed: Pass rate < 100% (required for 3 runs to approximate 95% confidence)."** This halts the pipeline. **Deliverable**: A log entry confirming the pass rate (e.g., "3/3 runs passed") written to `output/reports/synthetic_validation_log.json`. **Note**: T016b and T016c are sub-components of this loop. This task depends on T061 for the N value used in the loop.
- [X] T012 [P] [US1] Implement Pearson and Spearman correlation matrix computation in `code/stats_engine.py` using `scipy.stats`; store both matrices but mark Spearman as 'exploratory'.
- [X] T013 [US1] Implement graph construction in `code/stats_engine.py`: threshold **absolute Pearson correlations** at a configurable value from `config.py` (default) using `networkx`. **Explicitly DO NOT construct graphs for Spearman correlations**; Spearman matrices are stored for exploratory comparison only.
- [X] T013b [US1] Implement storage logic in `code/stats_engine.py`: save Spearman correlation matrices to `output/exploratory/` and ensure they are **excluded** from primary significance testing and BY correction.
- [X] T014 [US1] Implement network statistic calculation in `code/stats_engine.py`: Mean Absolute Correlation, Edge Density, Max Absolute Correlation, Average Clustering Coefficient.

### Tests for User Story 1

- [X] T010 [P] [US1] Unit test in `tests/unit/test_stats_engine.py`: implement function `test_permutation_preserves_marginals` to verify marginal distribution preservation after permutation.
- [X] T011 [P] [US1] Integration test in `tests/integration/test_pipeline.py`: implement function `test_synthetic_validation` to verify p > 0.05 for null data.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Multiple Testing Correction and Significance Reporting (Priority: P2)

**Goal**: Apply Benjamini-Yekutieli correction to empirical p-values and generate summary tables.

**Independent Test**: Feed known p-values to `code/correction.py` and verify q-values and significance flags match expected BY results.

### Tests for User Story 2

- [X] T018 [P] [US2] Unit test for BY procedure in `tests/unit/test_correction.py` (verify FDR control under arbitrary dependence).

### Implementation for User Story 2

- [X] T019 [US2] Implement empirical p-value calculation in `code/stats_engine.py` using formula $(r+1)/(N+1)$ to avoid 0/1.
- [X] T020 [US2] Integrate **Benjamini-Yekutieli (BY)** correction in `code/correction.py` across all tests (datasets × multiple statistics). **Gating**: This task depends on T007b passing. If T007b indicates BY is not ratified, the pipeline halts. If it proceeds, ONLY BY is used.
- [X] T021 [US2] Implement significance reporting in `code/main.py`: generate CSV summary table with dataset_id, statistic, observed, p-value, q-value, is_significant.
- [X] T022 [US2] Add explicit "associational" language enforcement in `code/main.py` output generation (FR-007).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Threshold Sensitivity Analysis and Visualization (Priority: P3)

**Goal**: Perform sensitivity analysis on correlation thresholds and generate visualizations.

**Independent Test**: Run sweep on single dataset and verify output table shows variation in significant counts across thresholds.

### Implementation for User Story 3

- [X] T024 [US3] Implement threshold sweep logic in `code/main.py`: **Re-run the permutation engine** for each threshold in a set of representative low-to-moderate values to ensure statistical validity. **DO NOT reuse a single null distribution** generated at one threshold unless the statistic is proven to be threshold-independent (e.g., Mean Absolute Correlation). **Smart Sweep Logic**:
 1. For each threshold, calculate a **threshold-specific N** by dividing the base adaptive N (from T061) by 5 (the number of thresholds) to ensure the total runtime remains within the 6-hour budget.
 2. If a statistic (e.g., Mean Absolute Correlation) can be computed directly from the raw data without thresholding, reuse the null distribution from T015. For statistics requiring graph construction (Density, Clustering), **re-run the full permutation engine** with the threshold-specific N.
 3. Log the `reuse_strategy` (reused vs. re-run) for each statistic-threshold pair.
 **Constraint**: Must use the threshold-specific N defined above. **Note**: This task depends on T061 for the base N enforcement logic and T015 for the aggregated `null_stats.csv` if reuse is applicable.
- [X] T024c [US3] **Sensitivity Analysis Trade-off Validation**: Generate a report in `output/reports/` that explicitly documents the trade-off between the sensitivity analysis runtime and statistical power. The report must confirm the N used (and any reduction) and that statistical validity was preserved.
- [X] T025b [US3] Implement primary threshold visualization in `code/viz.py`: generate heatmap and histogram for threshold **|r| > 0.3** specifically, saving to `output/plots/primary/`.
- [X] T025 [P] [US3] Implement heatmap generation in `code/viz.py` for observed vs. null correlation matrices (general utility).
- [X] T026 [P] [US3] Implement histogram generation in `code/viz.py` for null distributions with observed values overlaid (general utility).
- [X] T027 [US3] Implement sensitivity report generation in `code/main.py`: table showing significant counts per threshold.
- [X] T028 [US3] Integrate visualization outputs into `output/plots/` and `output/reports/`.

### Tests for User Story 3

- [X] T023 [P] [US3] Integration test for sensitivity sweep in `tests/integration/test_sensitivity.py`.

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should all work independently

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T029 [P] Documentation updates in `README.md` and `docs/`.
- [X] T041 [P] **Runtime Measurement**: Implement a timer in `code/main.py` to measure the total runtime of the full pipeline (datasets × multiple permutations). Output the runtime to `output/reports/runtime_log.json` with keys `{"total_runtime_seconds": float, "limit_seconds": 21600, "status": "pass/fail/timeout_partial"}`.
 - If the pipeline completes successfully, status is "pass".
 - **If the pipeline exceeds the predefined time limit naturally AFTER adaptive reduction (T061)**, status is "timeout_partial" and the pipeline must write a partial log with `completed_count` and `phase` before exiting gracefully.
 - **If the pipeline receives a SIGTERM/SIGINT signal**, write a partial `runtime_log.json` with status "timeout_partial" and the elapsed time. The schema for the partial log MUST include: `{"total_runtime_seconds": float, "status": "timeout_partial", "phase": "<current_phase>", "dataset_id": "<current_dataset_or_null>", "completed_count": int}`.
 - The pipeline must exit with a non-zero error code **only if** the time limit is exceeded AND the adaptive reduction logic (T061) failed to produce any valid results, or if the pipeline cannot even start.
 - **Must implement a SIGTERM/SIGINT signal handler** to write the partial log if killed, ensuring the deliverable is created even if the process is killed.
- [X] T042 [P] Code cleanup in `code/stats_engine.py`: run `black`, `isort`, and `flake8` to remove unused imports, enforce line length < 88, and add type hints to all functions.
- [X] T043 [P] Code cleanup in `code/correction.py`: run `black`, `isort`, and `flake8` to remove unused imports, enforce line length < 88, and add type hints to all functions.
- [X] T032 [P] [US3] Run `quickstart.md` validation: execute `python -m pytest tests/integration/test_quickstart.py` and verify exit code indicates successful completion.
- [X] T034 [P] [US1] Add robust error handling in `code/loaders.py` to raise explicit `FileNotFoundError` or `ValueError` if a verified UCI URL fails to download, ensuring no synthetic fallback is triggered (Constitution VII compliance).
- [X] T035 [P] [US1] Implement dataset checksumming in `code/loaders.py` to verify integrity of downloaded raw files. **Logic**:
 - If a known UCI checksum exists (from a hardcoded dictionary in `code/config.py`), verify against it.
 - **If no known checksum exists**, compute the SHA256 hash of the downloaded file immediately after download, store it in `data/raw/checksums.json`, and verify against this stored hash on subsequent runs.
 - **Deliverable**: If no known checksum exists, compute and store SHA256 in `checksums.json`; verification passes if the stored hash matches.
- [X] T036 [P] [US3] Add a specific test case in `tests/integration/test_sensitivity.py` to verify that the sensitivity table includes a row for each threshold and that the representative threshold row is present.
- [X] T046 [P] [US1] **Constant Variable Detection**: Enhance `code/loaders.py` to explicitly log the number and names of constant variables dropped from each dataset, ensuring transparency in the data hygiene process and verifying that no division-by-zero errors occur in correlation calculations.
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
- [X] T064 [P] [US1] **Runtime Enforcement Logic**: Implement a hard `signal` alarm or `time` check loop inside the main permutation worker function in `code/stats_engine.py`. If the cumulative wall-clock time for a single dataset's permutation batch exceeds a calculated sub-budget (derived from T061), the function must raise a `TimeoutError` to prevent the entire pipeline from hanging indefinitely, ensuring the 6-hour global limit (SC-004) is strictly enforced at the task level. **Formula**: `sub-budget = 6 hours / num_datasets / num_thresholds`. **Requirement**: `num_datasets` and `num_thresholds` must be calculated **before** the loop and passed as arguments.
- [X] T065 [P] [US1] **Missing Checksums Fallback**: Since UCI archives often lack public MD5/SHA256 checksums in their main index, implement a robust fallback in `code/loaders.py`: if a checksum is not found in `data/raw/checksums.json`, compute and store the SHA256 hash of the downloaded file immediately after download. Subsequent runs must verify the file against this stored hash, raising an error if the file has changed, rather than re-downloading or failing silently.
- [X] T066 [P] [US3] **Sensitivity Analysis Granularity**: Refine the threshold sweep in `code/main.py` (T024) to ensure the output table explicitly logs the exact number of edges retained at each threshold step. This is required to verify that the "significant count" changes are driven by the threshold and not by stochastic noise in the permutation engine, addressing the robustness requirement in US-3. **Note**: Edge count is a proxy for density; focus on significant count.
- [X] T067 [P] [US1] **Permutation Seed Isolation**: Ensure that the random seed used for the pilot run (T061) is distinct from the seed used for the full permutation run. Modify `code/stats_engine.py` to derive the full-run seed via a deterministic hash of the **Master Seed** + dataset_id + "full", and the pilot seed via **Master Seed** + dataset_id + "pilot", ensuring reproducibility of the full run even if the pilot parameters change.
- [X] T068 [P] [US2] **BY Correction Edge Case**: Add a specific unit test in `tests/unit/test_correction.py` to verify the behavior of the BY procedure when all p-values are 1.0 (no signal). The test must confirm that the procedure returns q-values of 1.0 and flags no discoveries, preventing false positives in null scenarios.
- [X] T069 [P] [US1] **Explicit URL Verification for Air Quality**: Update `code/config.py` (T004) to use the direct CSV link for Air Quality (extract from ZIP if necessary) or a verified raw link instead of the ZIP file, as ZIP extraction adds unnecessary complexity and potential failure points in the free-tier runner. If the CSV is not directly available, implement a `unzip` step in `code/loaders.py` that strictly handles the specific structure of the Air Quality ZIP.
- [X] T070 [P] [US1] **Student Performance Data Cleaning**: Update `code/loaders.py` to handle the specific format of the Student Performance dataset (semicolon separator, two files `student-mat.csv` for two genders) and ensure the correct merging or selection logic is applied to reach the >=20 variable threshold.
- [X] T071 [P] [US1] **Concrete Compressive Strength Handling**: Update `code/loaders.py` to handle the Excel format (`.xls`) of the Concrete dataset using `pandas.read_excel` (requiring `openpyxl` or `xlrd` in `requirements.txt`) and ensure the specific column mapping to continuous variables is correct.
- [X] T072 [P] [US1] **Variable Count Verification**: Add a pre-processing step in `code/main.py` that explicitly logs the number of continuous variables found in each dataset *after* dropping missing values and constant columns, and explicitly states which datasets are excluded due to <20 variables, ensuring the ">=20" constraint is transparently enforced.
- [X] T073 [P] [US1] **Clustering Coefficient Robustness**: In `code/stats_engine.py`, add a check for disconnected graphs before calculating the average clustering coefficient. If a graph is disconnected, calculate the coefficient only on the largest connected component or handle the `nx.average_clustering` behavior explicitly to avoid `NaN` results, logging a warning if this occurs.
- [X] T074 [P] [US2] **BY Correction Input Validation**: Add a validation step in `code/correction.py` (T008) to ensure that the input `p_values` list is non-empty and contains only values in the range [0, 1]. Raise a descriptive `ValueError` if the input is invalid, preventing silent failures in the multiple testing correction.
- [X] T075 [P] [US3] **Threshold Sweep Edge Case**: In `code/main.py` (T024), add a check to ensure that the threshold sweep does not produce empty graphs (0 edges) for high thresholds (e.g., 0.5). If a graph is empty, log a warning and record the density as 0, ensuring the sensitivity table remains complete.
- [X] T076 [P] [US1] **Synthetic Data Variance Check**: In `code/stats_engine.py` (T016), add a check to ensure the synthetic identity covariance matrix actually produces a dataset with non-zero variance in all columns after generation, preventing division-by-zero errors in the correlation calculation.
- [X] T077 [P] [US1] **Permutation Random State Isolation**: Ensure that the random state used for the permutation loop in `code/stats_engine.py` is explicitly seeded using `np.random.default_rng(seed)` for each permutation iteration or block, rather than relying on global state, to guarantee reproducibility across parallel workers.
- [X] T078 [P] [US2] **P-Value Floor Enforcement**: In `code/stats_engine.py` (T019), explicitly enforce a minimum p-value floor of `1/(N+1)` to prevent `p=0` which can cause issues in log-transformations or downstream analysis, ensuring the formula `(r+1)/(N+1)` is strictly applied.
- [X] T079 [P] [US3] **Visualization Error Handling**: In `code/viz.py` (T009, T025), add try-except blocks around plot generation to handle cases where the input matrix is empty or contains `NaN` values, logging a warning and skipping the plot generation instead of crashing the entire pipeline.
- [X] T082 [P] [US1] **Dataset Variable Type Enforcement**: Add a strict type-checking step in `code/loaders.py` to ensure that only *continuous* (numeric) variables are retained for correlation analysis. Explicitly convert or drop ordinal/categorical columns that might be misidentified as numeric, and log the count of dropped variables per dataset.
- [X] T083 [P] [US1] **Permutation Count Validation for Small Datasets**: Implement a logic check in `code/stats_engine.py` to adjust the permutation count `N` dynamically if the dataset size `n` is small (e.g., `n < 50`), ensuring `N` does not exceed the theoretical maximum number of unique permutations (`n!` or a practical subset) to avoid redundant calculations.
- [X] T084 [P] [US3] **Sensitivity Analysis Threshold Range Validation**: Add a validation step in `code/main.py` to ensure the threshold sweep range {0.1, 0.2, 0.3, 0.4, 0.5} is appropriate for the specific dataset's correlation distribution. If the maximum observed correlation is < 0.1, log a warning and adjust the sweep range to start from the observed maximum to avoid generating empty graphs for all thresholds.
- [X] T085 [P] [US2] **BY Correction Stability Check**: Implement a check in `code/correction.py` to detect if the number of tests (datasets × statistics) is very small (e.g., < 5), in which case the BY procedure may be overly conservative. Log a warning if the number of tests is low, suggesting that results should be interpreted with caution.
- [X] T086 [P] [US1] **Memory Leak Prevention in Permutations**: Refactor `code/stats_engine.py` to explicitly delete intermediate numpy arrays and graph objects after each permutation iteration within the loop to prevent memory accumulation during the permutation process, ensuring stable memory usage on the GB runner.
- [X] T087 [P] [US1] **Correlation Method Consistency Check**: Add a unit test in `tests/unit/test_stats_engine.py` to verify that the Pearson and Spearman correlation calculations produce identical results for perfectly linear data, ensuring the `scipy.stats` implementation is correct and consistent.
- [X] T088 [P] [US3] **Visualization Scaling for Large Matrices**: Implement a scaling mechanism in `code/viz.py` to handle datasets with >50 variables, where the correlation heatmap becomes unreadable. The mechanism should downsample or cluster variables for visualization while preserving the overall structure, or generate a zoomed-in view of the most significant clusters.
- [X] T089 [P] [US2] **P-Value Distribution Analysis**: Add a diagnostic step in `code/main.py` to plot the histogram of all raw p-values across all datasets and statistics. This plot should be saved to `output/plots/diagnostics/p_value_distribution.png` to verify that the null distribution is correctly centered and that the test has appropriate power.
- [X] T090 [P] [US1] **Edge Case: Single Variable Dataset**: Add a specific check in `code/loaders.py` to handle datasets that, after cleaning, result in only 1 continuous variable. The system should explicitly skip such datasets and log a clear message, as correlation matrices cannot be computed for single-variable datasets.
- [X] T091 [P] [US1] **Data Hygiene Logging**: Add detailed logging in `code/loaders.py` to record exactly which rows were dropped due to missing values and which columns were dropped due to being constant or non-continuous for each dataset, ensuring full transparency of the data cleaning process.
- [X] T092 [P] [US3] **Sensitivity Analysis Visualization**: Implement a plot in `code/viz.py` that visualizes the variation in network density and significant counts across the swept thresholds {0.1, 0.2, 0.3, 0.4, 0.5}, saving it to `output/plots/sensitivity/`.
- [X] T093 [P] [US2] **Final Report Generation**: Implement a function in `code/main.py` to generate a comprehensive final report in Markdown format, summarizing all findings, methods used (BY), and explicitly stating the associational nature of the results, saving it to `output/reports/final_report.md`.
- [X] T094 [P] [US1] **Permutation Output Verification**: Add a verification step in `code/stats_engine.py` to ensure that the saved `null_stats.csv` file contains the correct number of permutations and that the data types are preserved correctly.
- [X] T095 [P] [US3] **Threshold Sweep Consistency Check**: Add a check in `code/main.py` to verify that the threshold sweep produces consistent results when re-run with the same seed and data, ensuring the stability of the sensitivity analysis.
- [X] T096 [P] [US2] **Q-Value Rounding and Formatting**: Implement a formatting step in `code/correction.py` to round q-values to a consistent number of decimal places (e.g., 4) in the output CSV, ensuring readability and consistency in the final report.
- [X] T097 [P] [US1] **Dataset Metadata Extraction**: Implement a function in `code/loaders.py` to extract and store metadata (e.g., number of rows, columns, variable names) for each dataset in `output/reports/dataset_metadata.json` for reference.
- [X] T098 [P] [US3] **Visualization Colorblind Accessibility**: Ensure all generated plots in `code/viz.py` use colorblind-friendly palettes and include patterns or labels to distinguish between different elements, enhancing accessibility.
- [X] T099 [P] [US2] **Final Data Integrity Audit**: Perform a final audit in `code/main.py` to verify that all intermediate files (raw data, processed data, results, plots) are present and correctly formatted before generating the final report.
- [X] T100 [P] [US3] **Sensitivity Analysis Interpretation**: Add a section in the final report generation (T093) that provides a brief interpretation of the sensitivity analysis results, highlighting any thresholds where the conclusions change significantly.