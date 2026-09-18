# Tasks: Evaluating the Robustness of Common Statistical Tests to Non-Independence in Public Datasets

**Input**: Design documents from `/specs/001-evaluating-the-robustness-of-common-stat/`
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

- [X] T001 Create project structure per implementation plan (`projects/PROJ-483-evaluating-the-robustness-of-common-stat/`)
- [X] T002 Initialize Python 3.11+ project with dependencies: `numpy`, `scipy`, `pandas`, `statsmodels`, `matplotlib`, `seaborn`, `pyyaml`, `pytest` in `requirements.txt`
- [X] T003 [P] Configure linting (flake8/black) and formatting tools in `pyproject.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented.
**⚠️ CRITICAL**: No user story work can begin until this phase is complete.
**⚠️ NOTE**: Tasks in this phase define *libraries* and *interfaces*. They do NOT execute the Monte Carlo simulation (which happens in Phase 3).

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `code/config.py` to load and validate `code/config.yaml` against `contracts/simulation_config.schema.yaml`
- [X] T004b [P] **Configuration & Schema Definition**: Create `contracts/config_schema.schema.yaml` defining fields for `seed`, `n_replications`, `dependency_strengths`, `test_types`, `dataset_manifest_path`, `use_real_data`, and `use_streaming`. THEN Populate `code/config.yaml` with default values: `seed=42`, `n_replications=10000`, `dependency_strengths: [0.0, 0.1, 0.2, 0.3, 0.5]`, `use_real_data: true`, `use_streaming: false`. **Note**: This single task handles both schema creation and config population. **Depends on T004.**
- [X] T005a [P] **Dataset Schema Definition**: Create `contracts/dataset_schema.schema.yaml` defining fields for `dataset_id`, `source_url`, `variable_names` (continuous/categorical), `target_column`, and `data_type`. **Note**: This task creates the schema file. **Depends on T004b.**
- [X] T005c [P] **Dataset Population**: Populate `data/manifests/datasets.yaml` with **verified UCI URLs** for datasets with **native categorical variables** suitable for Chi-squared tests. **Mandatory Inclusions**: UCI Wine (continuous), UCI Car Evaluation (categorical), UCI Zoo (categorical). **Explicit URLs**: `, `, `. **Ensure the set covers all required test types AND includes datasets suitable for spatial injection (via proxy or native coords).** **Do NOT include 'Adult' or 'Mixed' datasets.** **Note**: This task depends on T005a. **Depends on T005a.**
- [X] T005 [P] Implement `code/data_loader.py` (FR-001): Fetch datasets from **verified URLs defined in `data/manifests/datasets.yaml`** (after T005c), parse them, **verify they contain continuous or categorical variables suitable for t-tests/ANOVA/chi-squared** (continuous: variance > 0; categorical: at least 2 unique levels), and save raw CSVs to `data/raw/` and generate `data/manifests/checksums.json`. **Note**: This task iterates over the *entire* set defined in the manifest. **Depends on T005c and T004b.**
- [X] T035 [P] [US1] **Execution**: Implement `code/data_loader.py` (FR-001, Spec Assumptions): **Dataset validation logic** to verify $N$ is sufficient. If $N < 50$, skip the dataset and log a violation to `results/validation_report.json`. **If a dataset fails validation, it is skipped; the pipeline continues with remaining valid datasets. If NO valid datasets remain, the pipeline halts with a clear error.** **Note**: This task applies to ALL user stories. **Depends on T005 completion.**
- [X] T037 [P] Implement `code/dependency_injector.py` (FR-003): **Feature-space clustering proxy** logic to generate spatial proxies for datasets lacking explicit spatial coordinates. Use **K-Means with k=3** to generate proxy coordinates. Output a proxy generation report to `data/manifests/spatial_proxy_report.json`. **Note**: The specific algorithm and parameters are implementation choices, not mandated by the Spec. **If proxy generation fails, skip spatial injection for this dataset (Do NOT fallback).**
- [X] T041 Implement `code/dependency_injector.py` (FR-003): **Validation logic** for the feature-space clustering proxy. Validate the proxy using **silhouette score** (threshold > 0.25). Ensure the proxy is validated as per FR-003 requirements. Output a validation report to `data/manifests/spatial_proxy_validation.json`. **Must complete before T006c.** **Note**: This task is sequential after T037. **Depends on T037.**
- [X] T006a [P] Implement `code/dependency_injector.py` (FR-003): Vectorized **AR(1) resampling** function with **tunable strength restricted strictly to the discrete set** $r \in \{0, 0.1, 0.2, 0.3, 0.5\}$ as per FR-007. **Validation**: Verify injected autocorrelation matches target $r$ within 5% tolerance. **Note**: This library supports ONLY the discrete set mandated by the spec to prevent implementation drift.
- [X] T006b [P] Implement `code/dependency_injector.py` (FR-003): **Block bootstrap** function for hierarchical dependency with tunable block size determined by **block size = sqrt(N)**. **Validation**: Verify block size distribution matches target. **Note**: This function is for **Dependency Injection ONLY (comparative baseline), NOT for Null Hypothesis Construction.**
- [X] T006c-native [P] Implement `code/dependency_injector.py` (FR-003): **Spatial kernel smoothing** function for datasets with **explicit spatial coordinates**. Use **Gaussian kernel** and **scipy.stats.gaussian_kde default bandwidth (Silverman's rule)** for bandwidth selection. **Note**: This task is for datasets with native coordinates, not proxies.
- [X] T006c [P] Implement `code/dependency_injector.py` (FR-003): **Spatial kernel smoothing** function for datasets using a **validated feature-space clustering proxy** (from T041). Use **Gaussian kernel** and **Silverman's rule** for bandwidth selection. **Requirement**: Must use **Euclidean distance** on the proxy coordinates. **Note**: Depends on T041 completion. **DO NOT run in parallel with T041.** **Depends on T041.**
- [X] T006e [P] **Sweep Configuration**: Create `code/sweep_config.yaml` with the **mandatory dependency strength sweep set** $r \in \{0, 0.1, 0.2, 0.3, 0.5\}$ as per FR-007. **Note**: Execution tasks (T013) must consume this configuration.
- [X] T007 [P] **Library Definition**: Create `code/metrics.py` (FR-005, SC-001). **Define** functions `calculate_type1_error`, `calculate_power`, `clopper_pearson_ci`, and `train_logistic_model`. **Do NOT run the simulation here**. Ensure all functions are designed to accept aggregated p-values and return metrics with **Clopper-Pearson confidence intervals**.
- [X] T016-def [P] **Library Definition**: Extend `code/metrics.py` (Constitution Principle VII): **Define** the logic to train and save logistic regression models relating **error rate to dependency strength** to `results/logistic_models.pkl`. **Verification**: Ensure model convergence logic is defined. **Execution** of this training will occur in Phase 3 after data generation.
- [X] T008 [P] **Library Definition**: Implement `code/visualizer.py` (FR-006). **Define** plot generation logic for error rate curves and power comparisons. **Do NOT generate plots here**.
- [X] T043 [P] [US1] Unit test for AR(1) injection logic in `tests/unit/test_dependency_injector.py` (verify autocorrelation matches target $r$)
- [X] T044 [P] [US1] Unit test for Block Bootstrap injection logic in `tests/unit/test_dependency_injector.py` (verify block size distribution)
- [X] T045 [P] [US1] Unit test for Spatial Kernel Smoothing injection logic in `tests/unit/test_dependency_injector.py` (verify smoothing effect on proxy coordinates)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Type I Error Inflation Quantification (Priority: P1) 🎯 MVP

**Goal**: Quantify false-positive rate inflation of t-tests/ANOVA under varying dependency strengths (AR(1), Block Bootstrap, Spatial).

**Independent Test**: Run a large number of replications for a single test (t-test) and single dependency (AR(1), $r=0.3$) on a sampled dataset, outputting a table of observed error rates vs. nominal alpha with Clopper-Pearson CI.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Unit test for AR(1) injection logic in `tests/unit/test_dependency_injector.py` (verify autocorrelation matches target $r$)
- [X] T011 [P] [US1] Unit test for Null Hypothesis construction in `tests/unit/test_simulation_runner.py` (verify p-values are uniform under $r=0$). **Note**: Create failing stub first. Test function: `test_null_hypothesis_validity`.

### Implementation for User Story 1

- [X] T012a [US1] **Execution**: Implement `code/simulation_runner.py` (FR-004, FR-005): **Synthetic Data Generator**. Generate synthetic data under the true null hypothesis (independence) with parameters **defined in `code/config.yaml`** (from T004b). **Note**: This task is for **synthetic data only**. Do NOT use permutation of labels on real data here. Ensure a sufficient number of replications per config to achieve statistical robustness. **Output**: Save raw p-values to `results/simulation_raw.csv`. **This task is the PRODUCER of data for T007/T008 functions.** **Depends on T007 (Library Definition) and T004b-Populate (Config Population).**
- [X] T012b [US1] **Execution**: Implement `code/simulation_runner.py` (FR-003): **Dependency Injector for Synthetic Data**. Inject dependency structure (AR(1)/Block Bootstrap/Spatial) with strength $r$ into the synthetic data generated by T012a. **Note**: This task satisfies FR-003 for synthetic data. **Output**: Append results to `results/simulation_raw.csv`. **Depends on T012a.**
- [X] T012c [US1] **Execution**: Implement `code/simulation_runner.py` (FR-004): **Test Runner for Synthetic Data**. Apply statistical test (t-test/ANOVA) to the injected synthetic data. Record p-value. **Note**: This task applies the test. **Output**: Append results to `results/simulation_raw.csv`. **Depends on T012b.**
- [X] T012d [US1] **Execution**: Implement `code/simulation_runner.py` (FR-002): **Null Hypothesis Construction for Real Data (Primary Path)**. Load real data (from T005), **Inject dependency structure** (AR(1)/Block/Spatial) with strength $r$, **Permute labels via random shuffle of the target column** to break any existing effect. **Note**: This task satisfies FR-002's requirement to construct a null hypothesis on *original data* via permutation. **Output**: Append results to `results/simulation_raw.csv`. **Depends on T005 (Data Fetch) and T012a (Simulation Loop Logic).**
- [X] T013 [US1] **Execution**: Implement sensitivity analysis sweep in `code/main.py` for **all dependency structures** (temporal, hierarchical, spatial) and **all test types** (t-test, ANOVA, Chi-squared). **Consume the discrete set** $r \in \{0, 0.1, 0.2, 0.3, 0.5\}$ **from `code/sweep_config.yaml` (T006e)** and run simulations for both T012 (synthetic) and T012d (real) modes. **Aggregation**: Merge results into a **single unified artifact** `results/aggregated_unified.csv` (schema: `test_type:str, dependency_structure:str, r:float, error_rate:float, ci_lower:float, ci_upper:float, source_mode:str`). **Note**: This task replaces the split T013a/T013b to prevent data fragmentation. **Depends on T012c and T012d completion.**
- [X] T013b [US1] **Execution**: Implement **Table Artifact Generation** in `code/main.py` to format `results/aggregated_unified.csv` into a human-readable Markdown table `results/type1_error_table.md` as required by US-1 AC-1. **Note**: This task ensures the "Independent Test" requirement is met. **Depends on T013.**
- [X] T014 [US1] **Execution**: Implement trend verification logic in `code/metrics.py`: Calculate **Spearman rank correlation** to verify monotonic increase of error rates with $r$ (p < 0.05) as per US-1 AC-2. **This task consumes `results/aggregated_unified.csv` from T013**. Output `trend_status` column to `results/aggregated_unified.csv`. **Depends on T013 completion.**
- [X] T014b [US1] **Execution**: Implement **CI Width Verification** in `code/metrics.py` to calculate the **Clopper-Pearson CI width** and verify it meets the **$\pm 0.5\%$ precision target** (SC-003). Log pass/fail status to `results/precision_report.json`. **Depends on T013 completion.**
- [X] T040 [US1] **Execution**: Implement edge case handling logic in `code/simulation_runner.py`: Define and implement behavior for datasets where the **null hypothesis cannot be cleanly constructed** (e.g., all variables highly correlated) or when **injected dependency violates normality assumptions** beyond non-independence, as defined in **spec.md Edge Cases**. Log specific edge case failures to `results/edge_case_report.json`. **Note**: This task applies to all user stories.
- [X] T016-exec [US1] **Execution**: **Run** the logistic regression training defined in T016-def (Phase 2) using the **unified aggregated data from T013, T020c, and T028**. Save model to `results/logistic_models.pkl`. **Verification**: Ensure model convergence. **Save the model regardless of AUC**, as long as it converges, to preserve all valid trend data. **Depends on T013, T020c, and T028 completion.**

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Cross-Test and Structure Comparison (Priority: P2)

**Goal**: Compare robustness of t-test, ANOVA, and Chi-squared across temporal, spatial, and hierarchical dependency structures.

**Independent Test**: Run simulation for all three tests and at least two dependency structures, producing a comparative plot showing error rate curves.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T017 [P] [US2] Integration test for multi-test pipeline in `tests/integration/test_cross_test_comparison.py`
- [X] T018 [P] [US2] Contract test for output CSV schema in `tests/contract/test_result_schema.py`

### Implementation for User Story 2

- [X] T020a [US2] Extend `code/simulation_runner.py` to include **Chi-squared test logic** and block bootstrap for hierarchical structures. **Requirement**: Implement **contingency table construction logic** using **Sturges' rule (k = 1 + log2(N))** for binning continuous variables if the dataset lacks categorical ones.
- [X] T020b [US2] Extend `code/metrics.py` to implement **Chi-squared error rate calculation and reporting** as required by FR-005.
- [X] T020c [US2] **Execution**: Implement **Chi-squared simulation sweep** in `code/main.py`: Sweep $r$ across the **specific discrete set** $r \in \{0, 0.1, 0.2, 0.3, 0.5\}$ **from `code/sweep_config.yaml`** for Chi-squared tests on **public datasets** (both synthetic and real/permutation modes) for all dependency structures (AR(1), Block, Spatial). **Depends on T020a and T020b completion**. Aggregate results using functions defined in T020b to `results/aggregated_unified.csv` (append mode).
- [X] T020d [US2] **Execution**: Extend `code/dependency_injector.py` to support **spatial kernel smoothing** for Chi-squared tests, ensuring all tests can run under all structures as per US-2 AC-1. **Depends on T006c.**
- [X] T020e [US2] **Execution**: Extend `code/dependency_injector.py` to support **Block Bootstrap** for Chi-squared tests (hierarchical dependency). **Depends on T006b.**
- [X] T021 [US2] Implement aggregation logic in `code/main.py` to group results by test type and dependency structure (partial aggregation).
- [X] T021b [US2] **Execution**: Implement **Multi-Test Merge Logic** in `code/main.py` to merge t-test, ANOVA, and Chi-squared results from T013 and T020c into a single unified artifact `results/aggregated_unified.csv` for visualization. **Depends on T013 and T020c.**
- [X] T022 [US2] Update `code/visualizer.py` to generate comparative line plots (x=dependency strength, y=error rate, hue=test type) per AC-1 using `results/aggregated_unified.csv`. **Depends on T021b.**
- [X] T023 [US2] Implement threshold detection logic to report specific $r$ where error rate exceeds $\alpha=0.10$ per AC-2. **Use linear interpolation** between discrete points if the exact threshold is not hit.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Power Analysis under Dependency (Priority: P3)

**Goal**: Quantify the reduction in statistical power when non-independence is present.

**Independent Test**: Inject true effects (mean shift $\delta=1.0\sigma$) into dependency-injected data and measure proportion of significant results vs. baseline.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T024 [P] [US3] Unit test for effect injection logic in `tests/unit/test_effect_injection.py`
- [X] T025 [P] [US3] Integration test for power calculation in `tests/integration/test_power_analysis.py`

### Implementation for User Story 3

- [X] T026 [P] [US3] Extend `code/simulation_runner.py` to support "True Effect" mode (inject mean shift $\delta$ before dependency injection). **Depends on T012a** (Synthetic Generator).
- [X] T026b [US3] **Execution**: Implement the **mean shift injection logic** in `code/simulation_runner.py` to inject true effects (e.g., mean shift $\delta=1.0\sigma$) into the synthetic data before dependency injection. **Note**: This task explicitly implements the injection mechanism required by US-3 AC-1. **Shift the target variable; calculate $\sigma$ as the population std dev of the original data.**
- [X] T026c [US3] **Execution**: Implement **Power Analysis Simulation Sweep** in `code/main.py` to run the Monte Carlo loop for power analysis (injecting effects) for $r=0$ and $r=0.3$ across all test types. **Output**: Append results to `results/aggregated_unified.csv`. **Depends on T026b and T020a.**
- [X] T027a [US3] Implement power calculation logic in `code/metrics.py`: Calculate observed power at $r=0$ and $r=0.3$ for true effect scenarios.
- [X] T027b [US3] Implement delta calculation logic in `code/metrics.py`: Calculate **percentage reduction in power** between $r=0$ and $r=0.3$ as required by US-3 AC-2.
- [X] T028 [US3] Update `code/visualizer.py` to generate power loss curves (x=dependency strength, y=power)
- [X] T029 [US3] Add reporting logic in `code/main.py` to output the **percentage reduction in power** calculated by **T027b** to `results/power_analysis.csv` and the final report. **Note**: This task ensures the specific metric is preserved. **Depends on T027b.**

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T030 [P] Documentation updates in `docs/` and `README.md`
- [X] T031a [P] Refactor: Extract simulation loop into `run_single_replication` function in `code/simulation_runner.py`
- [X] T031b [P] Refactor: Vectorize aggregation logic in `code/main.py` for CPU efficiency
- [X] T032a-Profile [P] **Execution**: Profile `code/simulation_runner.py` using **cProfile** to identify bottlenecks. **Metric**: Measure **wall-clock time** and **peak RSS** (Resident Set Size) for a single replication loop with $N=100$ and $r=0.3$. **Output**: Save profile stats to `results/perf_profile.json`. **Note**: This task replaces the non-executable T032a.
- [X] T032a-Target [P] **Execution**: Define the **performance target** in `code/main.py`: 10,000 replications must complete in **< 6 hours** on a 2-core, 7GB RAM runner. **Metric**: Verify total wall-clock time for the largest configuration. **Output**: Log target and actual time to `results/perf_log.json`. **Note**: This task replaces the non-executable T032a.
- [X] T032a-Optimize [P] **Execution**: Apply **vectorization** (numpy) or **chunking** strategies to `code/simulation_runner.py` to meet the 6-hour target defined in T032a-Target. **Technique**: Replace explicit Python loops with `numpy` vectorized operations where possible. **Output**: Update `results/perf_log.json` with optimization details. **Note**: This task replaces the non-executable T032a.
- [ ] T033 [P] Additional unit tests for edge cases (null hypothesis construction, small N) in `tests/unit/`
- [ ] T034 Run quickstart.md validation to ensure reproducibility

---

## Phase N+1: Revision & Robustness (Addressing Review Concerns)

**Purpose**: Address specific concerns raised in prior reviews regarding data sourcing, scientific validity, and execution constraints.

- [X] T050 [P] [Review: Data Sourcing] Update `data/manifests/datasets.yaml` to **remove any placeholder or generic "UCI" entries**. Replace with **exact, canonical, verified URLs** for specific datasets (e.g., ` for Wine, ` for Car). **Add a comment** in the file explaining the verification status of each URL. **Depends on T005a.** **Note**: Do NOT include 'Adult' URL.
- [X] T051 [P] [Review: Scientific Validity] **Refactor `code/simulation_runner.py` (T012a)**: Explicitly document and implement the **"Generate-then-Inject"** paradigm as the *only* method for null hypothesis construction on synthetic data. Add a **validation check** that verifies the synthetic data generation under $r=0$ yields uniform p-values, confirming the null is true. **Add a unit test** in `tests/unit/test_simulation_runner.py` to verify that under $r=0$ (no injection), the p-values are uniform. **Depends on T012a.**
- [X] T052 [P] [Review: Execution Constraints] Add a **pre-flight check** in `code/main.py` to estimate the memory footprint of the simulation for the largest dataset and highest replication count. **Threshold**: **6GB**. **Formula**: `(dataset_rows * 8 bytes * 10000) / (1024^3)`. If the estimate exceeds **a significant threshold**, **log a warning and SKIP the specific dataset** to ensure **a sufficient number of replications** can be completed. **Do NOT reduce the replication count below 10,000, nor reduce the sample size below N=50**, as this violates FR-008 and statistical validity. Log the optimization steps in `results/perf_log.json`. **Depends on T032a.**
- [X] T053 [P] [Review: Spatial Proxy Validity] Enhance `code/dependency_injector.py` (T037/T041) to **log the validity metric score** of the clustering proxy generation. **Threshold**: **silhouette_score > 0.25**. If the score falls below **0.25**, **log a warning** in `data/manifests/spatial_proxy_report.json` and **skip** the spatial dependency injection for that specific dataset. **Do NOT fallback to block bootstrap**. **Depends on T037, T041.**
- [X] T054 [P] [Review: Edge Cases] Implement a **robustness test** in `code/simulation_runner.py` (T040) that attempts to run a single replication with a **highly correlated dataset** (where null construction is difficult). If the test fails or produces nonsensical p-values (e.g., all 0 or all 1), **log the specific failure mode** to `results/edge_case_report.json` and **skip** that specific configuration for the full run. **Depends on T040.**
- [X] T056b [P] [Review: Data Fetch Robustness] **Refactor `code/data_loader.py`**: Implement a **fail-loud** policy for verified URLs. If a fetch fails, raise a `DataFetchError` and **halt the pipeline**. **Do NOT trigger any fallback to synthetic data**. Synthetic data generation is a **separate execution path** configured via `code/config.yaml` (e.g., `use_real_data: false`), not a runtime fallback for failed real data fetches. This ensures that if real data is unavailable, the pipeline fails explicitly rather than fabricating results. **Note**: This resolves the deadlock where a fetch failure would otherwise stop the entire project, while preserving the rule that real data fetches must not silently fall back to synthetic data. **Depends on T005.**
- [X] T057-def [P] [Review: Data Streaming] **Defensive**: Implement **streaming logic** in `code/data_loader.py` for datasets that exceed the 7GB RAM limit. Use `datasets.load_dataset(..., streaming=True)` or chunked CSV reading to process large real datasets without loading them entirely into memory. **Only run if `config.use_streaming` is true (default: false)**. **If streaming is required, the dataset is EXCLUDED** to preserve the 7GB RAM constraint. Log the streaming strategy and chunk sizes to `results/perf_log.json`. **Depends on T005.**
- [X] T058 [P] [Review: Normality Assumption] **Defensive**: Extend `code/simulation_runner.py` (T040) to **log the Shapiro-Wilk test statistic** for the **residuals of the injected data**. **Threshold**: **p < 0.01**. If the injected dependency structure causes a severe violation of normality (p < 0.01), **log the specific configuration** to `results/edge_case_report.json` and **flag** the results for that configuration as potentially invalid for parametric tests. **Depends on T040.**
- [X] T059 [P] [Review: Replication Count Verification] Add a **post-run verification** task in `code/main.py` to count the actual number of replications executed for each configuration. If the count deviates from the target by a significant margin, log a critical warning. to `results/perf_log.json` and **flag** the corresponding error rate estimates in `results/aggregated_unified.csv` as potentially imprecise. **Depends on T013.**
- [X] T060 [P] [Review: Trend Test Robustness] Enhance `code/metrics.py` (T014) to include a **Mann-Kendall trend test** in addition to Spearman correlation for verifying monotonicity. This provides a non-parametric check that is robust to outliers in the error rate estimates. **Depends on T014.**
- [X] T061 [P] [Review: Chi-Squared Binning] Document the **binning strategy** (Sturges' rule) used for Chi-squared tests in `docs/binning_strategy.md`. Ensure the strategy is applied consistently across all datasets and dependency configurations. **Depends on T020a.**
- [X] T062 [P] [Review: Power Calculation Baseline] Ensure `code/metrics.py` (T027a) explicitly calculates the **theoretical power** for the independent case ($r=0$) using standard formulas (e.g., from `statsmodels.stats.power`) to compare against the observed power. Log the comparison to `results/power_analysis.csv`. **Depends on T027a.**
- [X] T063 [P] [Review: Visualization Confidence Intervals] Update `code/visualizer.py` (T022, T028) to **explicitly plot the Clopper-Pearson 95% confidence intervals** as error bars on all error rate and power curves. Ensure the legend clearly indicates the CI method used. **Depends on T007.**
- [X] T064 [P] [Review: Configuration Audit] Generate a **configuration audit report** (`results/config_audit.json`) at the start of the pipeline that lists all active parameters (datasets, $r$ values, test types, injection methods) and their sources (config file, manifest). This ensures full traceability of the experimental setup. **Depends on T004.**
- [X] T064b [P] [Review: Per-Dataset Manifest] Generate `data/dependency_manifest.yaml` that records chosen parameters (r, method) for **each dataset** processed, updating dynamically if specific datasets are skipped due to size or validity (T035). **Depends on T035 and T064.**

---

## Phase N+2: Final Validation & Cleanup

**Purpose**: Final checks to ensure the project is ready for the next analyze pass.

- [ ] T065 [P] **Final Integration Test**: Run the full pipeline (T012a -> T016-exec) on a small subset of configurations to verify end-to-end correctness. **Output**: `results/final_integration_test.json`. **Note**: This task must pass before the project is considered "clean".
- [ ] T066 [P] **Documentation Finalization**: Ensure all `docs/` files are up to date with the final implementation details, including the "Generate-then-Inject" and "Inject-then-Permute" paradigms.
- [ ] T067 [P] **Code Cleanup**: Remove any unused imports, debug prints, or temporary files. Ensure `requirements.txt` is minimal and accurate.
- [ ] T068 [P] **README Update**: Update `README.md` with the final execution instructions, including how to run the pipeline on CPU-only runners and how to interpret the results.
- [ ] T069 [P] **License Check**: Ensure all third-party libraries used are compatible with the project's license.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
 - T005a must run before T005c.
 - T005c must run before T005.
 - T037 and T041 must run before T006c (or T006c must handle missing proxy gracefully).
 - T035 must run after T005 to validate fetched data.
 - **T007/T008 (Library Definitions)** must be completed before T012/T022 (Execution) to ensure functions exist.
 - **T004b (Config Population)** must run before T012.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - **T012a (Synthetic Generator)** is the **first** execution task in Phase 3. It produces the data consumed by T012b.
 - **T012d (Permutation on Real Data)** depends on T012a (Code Reuse) and T005.
 - **T013** depends on **T012c and T012d completion**.
 - **T014** depends on **T013** completion.
 - **T016-exec (Execution)** depends on **T013, T020c, and T028** completion.
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Revision (Phase N+1)**: Can be run in parallel with Polish tasks, but depends on the core implementation (Phases 3-5) to have defined the behaviors being reviewed.
- **Final Validation (Phase N+2)**: Depends on all previous phases being complete.

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
- Revision tasks (T050-T064) can be run in parallel with Polish tasks.
- Final Validation tasks (T065-T069) must run sequentially after all other tasks.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for AR(1) injection logic in tests/unit/test_dependency_injector.py"
Task: "Unit test for Null Hypothesis construction in tests/unit/test_simulation_runner.py"

# Launch all models for User Story 1 together:
Task: "Implement code/simulation_runner.py (FR-004, FR-005)"
Task: "Implement sensitivity analysis sweep in code/main.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Execution Order: T012a -> T012b -> T012c -> T012d -> T013 -> T014 -> T016-exec)
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
- **Critical Constraint**: All tasks must run on CPU-only GitHub Actions (multi-core, sufficient RAM). No GPU, no deep learning, no low-bit quantization. Use vectorized NumPy operations.
- **Scientific Validity**: The "Generate-then-Inject" paradigm (Plan Update) is the authoritative method for null hypothesis construction on synthetic data. The "Inject-then-Permute" paradigm (FR-002) is required for validation on real public datasets.
- **Data Integrity**: All datasets must be fetched from verified, canonical URLs (UCI/OpenML) defined in `data/manifests/datasets.yaml`. No synthetic or fake data generation for input. If fetch fails, the pipeline MUST halt with a clear error. Synthetic runs are a separate execution path defined in config, not a fallback.
- **Reproducibility**: All random seeds must be pinned in `code/config.yaml` and logged in `results/perf_log.json`.
- **Edge Cases**: T040 ensures robust handling of datasets where standard null construction fails.
- **Task ID Integrity**: T016-def is the unique ID for the logistic regression library definition. T016-exec is the unique ID for the logistic regression execution task.
- **Execution Flow**: Phase 2 defines *how* to calculate metrics (Library). Phase 3 *runs* the simulation (Producer) and then *applies* the metrics (Consumer).
- **Revision Concerns**: Phase N+1 tasks (T050-T064) address specific reviewer concerns regarding data sourcing, scientific validity, execution constraints, data loader robustness, edge case handling, streaming, normality, replication verification, trend robustness, binning strategy, power baseline, visualization CIs, and configuration audit. These must be addressed before the project is considered "clean" for the next analyze pass.
- **Constitution Check**: The plan's Constitution Check section explicitly states **10,000 replications** (FR-004) to achieve $\pm 0.5\%$ precision (SC-003).
- **Final Validation**: Phase N+2 tasks (T065-T069) ensure the project is fully integrated, documented, and ready for the next analyze pass.