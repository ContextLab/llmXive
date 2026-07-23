---
description: "Task list template for feature implementation"
---

# Tasks: Assessing Statistical Significance of Observed Correlations in Public Databases

**Input**: Design documents from `/specs/001-assessing-statistical-significance-of-ob/`
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

- [X] T004 [P] Create `code/config.py` defining paths (`data/raw`, `data/processed`, `output/results`), random seeds, and default thresholds. **Define the specific UCI datasets explicitly** with their verified download URLs:
 1. Wine: `
 2. Abalone: `
 3. Breast Cancer Wisconsin: `
 4. Student Performance: ` (Requires merging with `student-mat.csv` from the same directory if available, or handling the specific UCI structure for this dataset. Note: The UCI repository for Student Performance often provides two CSVs: `student-mat.csv` (Math) and `student-mat.csv` (Portuguese) or similar. The task must implement logic to fetch both if they exist, or handle the single file if only one is present, and merge them if necessary. If the URL provided points to a single file, the task must handle that specific file. The specific logic for handling multi-file datasets is required.)
 5. Air Quality: ` (Requires handling the specific archive format, potentially unzipping or parsing the specific CSV structure provided by UCI for this dataset. The URL provided must be verified to be the correct, direct link to the CSV file.)
 6. Concrete Compressive Strength: `
 **Note**: If a limited number of valid datasets (>=20 continuous variables) are found after processing these 6, the system MUST trigger the fallback logic defined in T005.
- [X] T005 [P] Implement `code/loaders.py` with functions to fetch the **specific UCI datasets** defined in T004 via verified URLs and handle CSV/Excel ingestion. **Implement the fallback strategy**: If a dataset has < 20 continuous variables, it is excluded. If the primary list yields < 3 valid datasets, the system MUST automatically query the UCI repository for the next available multivariate datasets with >=20 continuous variables (e.g., 'Parkinsons', 'Libras', 'Isolet') until valid datasets are found or the repository is exhausted. **Note**: Fallback logic is fully integrated into this task.
- [X] T006 [P] Implement data hygiene logic in `code/loaders.py`: drop rows with missing values, detect/exclude constant variables, and filter datasets with <20 continuous variables.
- [X] T007 [P] Create `code/stats_engine.py` skeleton with **exact function stubs** and required imports (`import pandas as pd`, `import numpy as np`, `from scipy import stats`, `import networkx as nx`):
 - `def compute_correlation(df: pd.DataFrame, method: str) -> pd.DataFrame:`
 - `def construct_graph(corr_matrix: pd.DataFrame, threshold: float) -> nx.Graph:`
 - `def calculate_stats(graph: nx.Graph) -> dict:`
 - `def generate_null_distribution(df: pd.DataFrame, n_permutations: int, stats_func: callable) -> dict:`
- [X] T007c [P] **Constitutional State Generation (Producer)**: Implement a function in `code/constitution.py` to **create or update** `state/projects/PROJ-297-assessing-statistical-significance-of-ob.yaml`. This function MUST ensure the file exists with the key `amendment_status` set to `"pending"` if the file is missing or the key is absent. The YAML schema MUST be: `{amendment_status: str, ratified_by: str | null, date: str | null}`. **This task MUST run BEFORE T007b** to guarantee the artifact required by the gate check is present. **Note**: This is a temporary bridge for local development. The 'Advancement-Evaluator Agent' is the sole writer of state in production; this code must be replaced by agent-driven state management in the final pipeline.
- [X] T007b [P] **Constitutional Gate Block**: Implement a check in `code/main.py` (or a dedicated `code/constitution.py`) that verifies the ratification status of the Constitutional Amendment regarding the Benjamini-Yekutieli (BY) procedure. **Logic**:
 - If the amendment status is `"ratified"`, proceed normally.
 - If the amendment status is `"pending"`, raise a `ConstitutionalError` and **HALT execution** with a critical error message: "Amendment for BY procedure is pending ratification. Execution blocked."
 - If the file is missing or malformed, raise a `ConstitutionalError` and **HALT execution**.
 - **Note**: This task is a temporary bridge for local development. The 'Advancement-Evaluator Agent' is the sole writer of state in production; this code must be replaced by agent-driven state management in the final pipeline.
- [X] T008 [P] [US2] Implement `code/correction.py` with the Benjamini-Yekutieli (BY) procedure for multiple testing correction.
- [X] T068 [P] [US2] Unit test in `tests/unit/test_correction.py`: implement function `test_by_correction` to verify the BY procedure on a known set of p-values.
- [X] T069 [P] [US2] Unit test in `tests/unit/test_correction.py`: implement function `test_by_correction_edge_cases` to verify the BY procedure on edge cases (e.g., all p-values 1, all p-values 0).
- [X] T074 [P] [US2] Implement input validation in `code/correction.py` for the BY procedure (e.g., check for negative p-values, NaNs).
- [X] T085 [P] [US2] Implement a stability check in `code/correction.py` to ensure the BY procedure produces stable results across multiple runs.
- [X] T096 [P] [US2] Implement formatting logic in `code/correction.py` to round q-values to a specific number of decimal places.
- [X] T049 [P] [US2] Implement a simulation in `tests/unit/test_correction.py` to verify FDR control of the BY procedure.
- [X] T056 [P] [US2] Add logging in `code/correction.py` for the BY procedure.
- [X] T043 [P] Code cleanup for `code/correction.py`.
- [X] T018 [P] [US2] Integration test in `tests/integration/test_correction.py`: implement function `test_by_correction_integration` to verify the BY procedure in the context of the full pipeline.
- [X] T020 [P] [US2] Integrate BY correction into `code/main.py`.

---

## Phase 3: User Story 1 - Core Permutation Null Model Generation (Priority: P1) 🎯 MVP

**Goal**: Ingest multivariate datasets, compute observed statistics, and generate empirical null distributions via permutation.

**Independent Test**: Run pipeline on synthetic data (identity covariance) and verify observed stats fall within central [deferred] of null distribution (p > 0.05).

### Implementation for User Story 1

- [DEPRECATED] T012 [US1] **Removed**: Logic merged into T015. This task is removed to resolve ordering violation.
- [DEPRECATED] T013 [US1] **Removed**: Logic merged into T015. This task is removed to resolve ordering violation.
- [DEPRECATED] T014 [US1] **Removed**: Logic merged into T015. This task is removed to resolve ordering violation.
- [DEPRECATED] T013b [US1] **Removed**: Logic merged into T015. This task is removed to resolve ordering violation.
- [X] T015 [US1] **Implement Permutation Engine**: Implement the core permutation logic in `code/stats_engine.py`. **This task implements the code only, not the execution**. N=2,000 permutations per dataset. **Includes**: Pearson and Spearman correlation matrix computation, graph construction, and network statistic calculation (merged from T012, T013, T014).
- [X] T016 [US1] **Implement Synthetic Dataset Generator**: Implement a function in `code/stats_engine.py` to generate synthetic datasets (N=500, V=20, identity covariance) for FR-009 validation.
- [X] T016b [US1] **Single-Run Validation Logic**: Implement the logic for a single synthetic validation run to be called by T016d.
- [X] T016c [US1] **Shuffled Columns Validation Logic**: Implement the logic for a single shuffled column validation run to be called by T016d.
- [X] T016d [US1] **Synthetic Validation Loop (FR-009 Compliance)**: Implement a loop in `code/main.py` to run the synthetic validation multiple times to statistically verify that observed statistics fall within the central 95th percentile of the null distribution, requiring at least **19** of 20 runs passing for validation.
- [X] T062 [P] [US1] **Parallel Permutation Optimization**: Refactor `code/stats_engine.py` to use `multiprocessing.Pool` or `joblib` to parallelize the permutation loop across available CPU cores, ensuring maximum utilization of the runner's resources to meet the runtime constraint. **Depends on T015**.
- [X] T063 [P] [US1] **Memory Profiling**: Implement monitoring hooks in `code/stats_engine.py` to log peak memory usage (in GB using `psutil.Process(memory_info=RSS)`). Set a limit within the runner's capacity, accounting for a safety margin. **Depends on T015**.
- [X] T064 [P] [US1] **Runtime Enforcement Logic**: Implement a timeout check inside the permutation worker function in `code/stats_engine.py`. **Depends on T015**.
- [X] T067 [P] [US1] **Permutation Seed Isolation**: Modify `code/stats_engine.py` to use a **single, pinned master seed** for all runs (including pilots) to ensure full reproducibility. **Depends on T015**.
- [X] T077 [P] [US1] **Permutation Random State Isolation**: Modify `code/stats_engine.py` to use explicit seeding for random state with the **master seed**. **Depends on T015**.
- [X] T083 [P] [US1] **Permutation Count Validation**: Implement logic in `code/stats_engine.py` to validate the permutation count (N=2,000). **Depends on T015**.
- [X] T086 [P] [US1] **Memory Leak Prevention**: Refactor `code/stats_engine.py` to prevent memory leaks. **Depends on T015**.
- [X] T094 [P] [US1] **Permutation Output Verification**: Add a verification step in `code/stats_engine.py` to ensure permutation outputs are correct. **Depends on T015**.
- [X] T076 [P] [US1] **Synthetic Data Variance Check**: Add a check in `code/stats_engine.py` for synthetic data variance. **Depends on T016**.
- [X] T010 [P] [US1] Unit test in `tests/unit/test_stats_engine.py`: implement function `test_permutation_preserves_marginals` to verify marginal distribution preservation after permutation.
- [X] T011 [P] [US1] Integration test in `tests/integration/test_pipeline.py`: implement function `test_synthetic_validation` to verify p > 0.05 for null data.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Multiple Testing Correction and Significance Reporting (Priority: P2)

**Goal**: Apply BY correction and generate significance reports.

- [X] T019 [US2] **Empirical P-Value Calculation**: Implement function in `code/stats_engine.py` to calculate two-sided empirical p-values.
- [X] T021 [US2] **Significance Reporting**: Implement function in `code/main.py` to generate the summary table of significant findings.
- [X] T022 [US2] **Associational Language Enforcement**: Add enforcement in `code/main.py` to ensure all findings are framed as "associational" **at the source of generation**. **Depends on T021**.
- [X] T050 [P] [US2] **Associational Language Audit**: Implement a text scan of reports to verify associational language as a **secondary audit**. **Depends on T021**.
- [X] T059 [P] [US2] **Associational Language Audit**: Implement a text scan of reports to verify associational language as a **secondary audit**. **Depends on T021**.
- [X] T052 [P] [US2] **Report Formatting**: Refine output formatting in `code/main.py`. **Depends on T021**. <!-- ATOMIZE: requested -->
- [X] T078 [P] [US2] **P-Value Floor Enforcement**: Enforce logic in `code/stats_engine.py` to prevent p-values of 0 or 1. **Depends on T019**.

---

## Phase 5: User Story 3 - Threshold Sensitivity Analysis and Visualization (Priority: P3)

**Goal**: Perform sensitivity analysis and generate visualizations.

- [X] T023 [US3] **Sensitivity Test**: Implement test for sensitivity analysis.
- [X] T024 [US3] **Threshold Sweep**: Re-run the primary analysis for thresholds |r| ∈ {low to moderate values} **with N=2,000 permutations for each**. **Do NOT reduce N or the number of thresholds**. **Depends on T015**.
- [X] T024c [P] [US3] **Sensitivity Trade-off Validation**: Generate a report in `code/main.py` to validate sensitivity trade-offs. **Depends on T015**.
- [X] T025 [US3] **Heatmap Generation**: Implement heatmap generation in `code/viz.py`. **Depends on T015**.
- [X] T025b [US3] **Primary Threshold Visualization**: Implement visualization for the primary threshold in `code/viz.py`. **Depends on T015**.
- [X] T026 [US3] **Histogram Generation**: Implement histogram generation in `code/viz.py`. **Depends on T015**.
- [X] T027 [US3] **Sensitivity Report**: Generate a sensitivity report in `code/main.py`. **Depends on T015**.
- [X] T028 [US3] **Visualization Integration**: Integrate visualizations in `code/viz.py`. **Depends on T015**.

---

## Phase N: Additional Tasks

**Purpose**: Additional tasks for robustness, logging, and reporting.

- [X] T041 [P] [Runtime] **Runtime Measurement**: Implement a timer in `code/main.py` with `limit_seconds: 21600` (6 hours). **Depends on T015**.
- [X] T060 [P] [Runtime] **Performance Profiling**: Add profiling in `code/main.py`. **Depends on T015**.
- [ ] T093 [P] [Reporting] **Final Report Generation**: Generate a report in `code/main.py`. **Depends on T015**.
- [ ] T099 [P] [Data Integrity] **Final Data Integrity Audit**: Perform an audit in `code/main.py`. **Depends on T015**.
- [ ] T097 [P] [Data Integrity] **Dataset Metadata Extraction**: Implement a function in `code/loaders.py`. **Depends on T015**.
- [ ] T095 [P] [Data Integrity] **Threshold Sweep Consistency Check**: Add a check in `code/main.py`. **Depends on T015**.
- [ ] T091 [P] [Data Integrity] **Data Hygiene Logging**: Add logging in `code/loaders.py`. **Depends on T015**.
- [ ] T090 [P] [Data Integrity] **Edge Case: Single Variable Dataset**: Add a check in `code/loaders.py`. **Depends on T015**.
- [ ] T089 [P] [Data Integrity] **P-Value Distribution Analysis**: Add a diagnostic in `code/main.py`. **Depends on T015**.
- [ ] T084 [P] [Data Integrity] **Sensitivity Analysis Threshold Range Validation**: Add a check in `code/main.py`. **Depends on T015**.
- [ ] T082 [P] [Data Integrity] **Dataset Variable Type Enforcement**: Add a check in `code/loaders.py`. **Depends on T015**.
- [ ] T075 [P] [Data Integrity] **Threshold Sweep Edge Case**: Add a check in `code/main.py`. **Depends on T015**.
- [X] T073 [P] [Data Integrity] **Clustering Coefficient Robustness**: Add a check in `code/stats_engine.py`. **Depends on T015**.
- [ ] T072 [P] [Data Integrity] **Variable Count Verification**: Add a check in `code/main.py`. **Depends on T015**.
- [ ] T071 [P] [Data Integrity] **Concrete Compressive Strength Handling**: Update `code/loaders.py`. **Depends on T015**.
- [ ] T070 [P] [Data Integrity] **Student Performance Data Cleaning**: Update `code/loaders.py`. **Depends on T015**.
- [ ] T069b [P] [Data Integrity] **Explicit URL Verification for Air Quality**: Update `code/config.py`. **Depends on T015**.
- [ ] T066 [P] [Data Integrity] **Sensitivity Analysis Granularity**: Refine `code/main.py`. **Depends on T015**.
- [ ] T065 [P] [Data Integrity] **Missing Checksums Fallback**: Update `code/loaders.py`. **Depends on T015**.
- [ ] T058 [P] [Data Integrity] **Data Integrity Check**: Implement a check in `code/main.py`. **Depends on T015**.
- [ ] T055c [P] [Data Integrity] **End-to-End Seed Verification**: Implement a task in `code/main.py`. **Depends on T015**.
- [ ] T055b [P] [Data Integrity] **Master Seed Verification**: Implement a verification in `code/main.py`. **Depends on T015**.
- [ ] T055 [P] [Data Integrity] **Random Seed Reproducibility**: Verify `code/main.py`. **Depends on T015**.
- [ ] T054 [P] [Data Integrity] **Threshold Baseline Verification**: Add a check in `code/main.py`. **Depends on T015**.
- [X] T053 [P] [Data Integrity] **Edge Case Handling**: Implement error handling in `code/stats_engine.py`. **Depends on T015**.
- [X] T051 [P] [Data Integrity] **Visualization Quality Check**: Ensure `code/viz.py` outputs are high quality. **Depends on T015**.
- [X] T048 [P] [Data Integrity] **Memory Check Logic**: Merge into T063. **Depends on T063**.
- [X] T047 [P] [Data Integrity] **Visualization Quality Check**: Covered by T051.
- [ ] T046 [P] [Data Integrity] **Constant Variable Detection**: Enhance `code/loaders.py`. **Depends on T015**.
- [X] T045 [P] [Data Integrity] **Data Hygiene Logging**: Covered by T091.
- [X] T044 [P] [Data Integrity] **Data Hygiene Logging**: Covered by T091.
- [X] T042 [P] [Data Integrity] **Code Cleanup**: Clean `code/stats_engine.py`. **Depends on T015**.
- [X] T036 [P] [Data Integrity] **Sensitivity Analysis Test**: Add a test in `code/test_sensitivity.py`. **Depends on T015**.
- [ ] T035 [P] [Data Integrity] **Dataset Checksumming**: Implement checksumming in `code/loaders.py`. **Depends on T015**.
- [ ] T034 [P] [Data Integrity] **Error Handling**: Add error handling in `code/loaders.py`. **Depends on T015**.
- [ ] T032 [P] [Data Integrity] **Quickstart Validation**: Run a test in `code/main.py`. **Depends on T015**.
- [X] T029 [P] [Data Integrity] **Documentation**: Update docs. **Depends on T015**.

---

## Phase N+1: Final Tasks

**Purpose**: Final tasks for reporting and data integrity.

- [X] T107 [P] [Reporting] **Final Report Generation Implementation**: Implement T093. **Depends on T093**.
- [X] T109 [P] [Data Integrity] **Final Data Integrity Audit Implementation**: Implement T099. **Depends on T099**.
- [X] T108 [P] [Data Integrity] **Dataset Metadata Extraction Implementation**: Implement T097. **Depends on T097**.
- [X] T106 [P] [Data Integrity] **Comprehensive Data Hygiene Log Implementation**: Implement T091. **Depends on T091**.
- [X] T105 [P] [Data Integrity] **Single-Variable Dataset Handling Implementation**: Implement T090. **Depends on T090**.
- [X] T104 [P] [Data Integrity] **P-Value Distribution Diagnostic Implementation**: Implement T089. **Depends on T089**.
- [X] T103 [P] [Data Integrity] **Dynamic Threshold Range Adjustment**: Refine T084. **Depends on T084**.
- [X] T102 [P] [Data Integrity] **Ordinal vs. Continuous Discrimination**: Extend T082. **Depends on T082**.
- [X] T101 [P] [Data Integrity] **Robust UCI URL Discovery**: Update T004. **Depends on T004**.
- [X] T110 [P] [Data Integrity] **Fallback Dataset Verification**: Extend T005. **Depends on T005**.
