# Tasks: Assessing the Validity of p-Values in High-Dimensional Data

**Input**: Design documents from `/specs/001-assess-p-value-validity/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root
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

- [X] T001 [P] Create `code/` directory at repository root
- [X] T002 [P] Create `data/` directory at repository root with subdirectories `raw/`, `synthetic/`, `results/`
- [X] T003 [P] Create `tests/` directory at repository root with subdirectories `unit/`, `integration/`
- [X] T004a [P] Initialize Python 3.11 project with `requirements.txt` (numpy, scipy, pandas, matplotlib, seaborn, pytest)
- [X] T005 [P] Configure linting (ruff/flake8) and formatting (black) tools in `code/.ruff.toml` and `code/.black`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T006 [P] Define error code `ERR_HIGH_DIMENSIONAL_INSTABILITY` in `code/utils/exceptions.py` specifically for condition number > 10^12 (required by T010b)
- [X] T007 [P] Implement covariance regularization utility in `code/utils/regularization.py` (FR‑009: handle singular matrices, condition number > 10^12, apply ε = 10⁻⁶ regularization OR raise `ERR_HIGH_DIMENSIONAL_INSTABILITY`; also detect p/n > 10 and raise the same error)
- [X] T008 [P] Create base `SyntheticDataset` data model and schema in `code/utils/simulation.py`
- [X] T009 [P] Setup simulation orchestration framework in `code/utils/simulation.py` (manages iterations, seeds, parameter sweeps)
- [X] T010a [P] Implement a memory monitor in `code/utils/simulation.py` that checks RSS usage. **Constraint**: This task MUST raise a hard error and abort the simulation if RSS > 6 GB to satisfy SC-004 (Computational feasibility) as a hard constraint. Do NOT just warn. The implementation must explicitly call `sys.exit(1)` or raise a custom exception that halts the process.
- [X] T010b [P] Implement covariance singularity detector in `code/utils/regularization.py` that checks condition number > 10^12 and raises `ERR_HIGH_DIMENSIONAL_INSTABILITY` if regularization fails (FR‑009)
- [X] T011a [P] Implement power analysis utility function in `code/utils/simulation.py` to calculate the minimum simulation iteration count required to achieve statistical power ≥ 0.8 for detecting a KS statistic deviation > 0.05. **Output**: Returns an integer iteration count and writes it to `data/sweep/power_analysis_result.json`.
- [X] T011b-doc [P] **Justification for Iteration Count**: Create `docs/power_analysis_justification.md` explicitly documenting why the iteration count is sufficient for SC-005. **Content**: Must cite the Plan's design parameter, reference the power analysis utility from T011a, and state that the **output of T011a** (stored in `data/sweep/power_analysis_result.json`) confirms the required count. **Output**: `docs/power_analysis_justification.md`. **Note**: The iteration count is derived from T011a, not assumed.
- [X] T017 [US1] Implement parameter sweep logic in `code/generate_data.py` for **n** ∈ {50, 100, 200, 500}, **p** ∈ {500, 1000, 2000, 5000}, **ρ** ∈ {0, 0.1, 0.3, 0.5, 0.7, 0.9}, **AND distribution_type** ∈ {Normal, t-dist(df=3), Skewed Normal(skew=2.0)}. **Logic**: The system MUST iterate over the **full Cartesian product** of these four parameter sets to generate every combination (4 x 4 x 6 x 3 = 288 unique parameter sets). **Iteration Count**: Read the required iteration count dynamically from `data/sweep/power_analysis_result.json` (output of T011a). **Seed Generation**: Seeds are generated deterministically using the formula: `seed = master_seed + (index * offset) + (n*100 + p*10 + rho_idx)` where `master_seed` is read from `data/sweep/master_seed.txt`. **Pre-condition**: This task MUST create `data/sweep/master_seed.txt` if it does not exist (default=42) before generating seeds. **Output**: `data/sweep/params.csv` with **exact schema**: Header `seed,n,p,rho,distribution_type,iteration`, delimiter `,`, UTF-8 encoding. **Pre-condition**: None (reads dynamic count). **Error Handling**: Must explicitly invoke T007/T010b to detect and handle p/n > 10 or singular matrices.
- [X] T019d [P] **Seed Map Generation**: Generate a **seed map** file `data/sweep/seed_map.json` that maps each unique `(n, p, rho, distribution_type)` tuple to a list of deterministic integer seeds. **Dependency**: Explicitly depends on T017 completion to ensure `master_seed.txt` is created and `params.csv` exists. **Algorithm**: read master seed from `data/sweep/master_seed.txt`; for each parameter combination, assign sequential seeds starting at the master seed and incrementing by 1 for each required simulation iteration (read from `data/sweep/power_analysis_result.json`). **Verification**: This task MUST verify that `seed_map.json` contains entries matching the iteration count specified in `data/sweep/power_analysis_result.json`. **Note**: T017 generates the seeds; T019d organizes them. **Placement**: Moved to Phase 2 to ensure US2 (T022a) can start after Foundational without waiting for US1 completion.
- [X] T019e [P] Implement a **Deterministic RNG Wrapper** in `code/utils/simulation.py` that provides a unified interface for resetting and advancing the global numpy random state. **Algorithm**: Accepts a seed and a 'step' count; ensures that `np.random.seed(seed)` followed by 'step' calls to `np.random` produces identical sequences across T022 and T028. **Dependency**: None. **Purpose**: Ensures T022 and T028 use the exact same seed sequence for bit-for-bit reproducibility.

**Checkpoint**: Foundation ready – user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Synthetic Data Generation with Controlled Correlation and Distribution Violations (Priority: P1) 🎯 MVP

**Goal**: Generate synthetic high‑dimensional datasets with precisely controlled correlation structures, sample‑to‑dimension ratios, and distributional violations (heavy‑tailed or skewed) under known ground‑truth null conditions.

**Independent Test**: Can be fully tested by verifying that generated data matrices have the exact correlation structure specified (within numerical tolerance) and that the null hypothesis is true by construction.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T012 [P] [US1] Unit test for correlation matrix generation accuracy in `tests/unit/test_data_gen.py`
- [X] T013 [P] [US1] Unit test for distribution shape validation (t‑distribution, skewed normal) in `tests/unit/test_data_gen.py` (Verify `test_t_dist_df3` passes with KS distance < 0.01)
- [X] T014 [P] [US1] Integration test for null hypothesis validity (no mean differences) in `tests/integration/test_data_gen.py`

### Implementation for User Story 1

- [X] T018 [US1] Write `data/synthetic/{seed}.json` containing `sha256` (of the parameter row), `rho`, `n`, `p`, `distribution_type`, and `seed` for each unique parameter combination. **Serialization**: Serialize the parameter row as a JSON object with keys sorted alphabetically before hashing. Verify file exists and `sha256` matches the parameter hash (Constitution Principle III). **State Update**: Explicitly update `state/projects/PROJ-054-assessing-the-validity-of-p-values-in-hi.yaml` `artifact_hashes` map with the new checksum to satisfy Constitution Principle III and V.
- [X] T019a [US1] Implement a parameter reader in `code/generate_data.py` that loads `data/sweep/params.csv` and yields rows as dictionaries. **Dependency**: T017. **Output**: Iterator of parameter dicts.
- [X] T019b [US1] Implement a streaming data generator in `code/generate_data.py` that accepts a parameter dict, sets `np.random.seed(seed_value)` **immediately before** generating each matrix, and yields the numpy array. **Constraint**: Must raise `ERR_HIGH_DIMENSIONAL_INSTABILITY` internally if `p/n > 10` or if the covariance matrix is near-singular after regularization attempts. **Thresholds**: 'Near-singular' is defined as condition number > 10^12. Regularization epsilon is 10^-6. **Dependency**: T019a. **Error Handling**: Explicitly invokes T007/T010b.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Hypothesis Test Execution and p-Value Collection (Priority: P2)

**Goal**: Apply standard t‑tests and F‑tests to the synthetic null data and collect all resulting p‑values to empirically observe their distribution under violated assumptions.

**Independent Test**: Can be fully tested by running hypothesis tests on a known null dataset and verifying that p‑values are collected for every test without missing values.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T020 [P] [US2] Unit test for t‑test/F‑test execution on null data in `tests/unit/test_stats.py`
- [X] T021 [P] [US2] Integration test for full iteration loop (multiple iterations) without runtime errors in `tests/integration/test_stats.py`

### Implementation for User Story 2

- [X] T022a [US2] Implement data ingestion pipeline in `code/run_tests.py` that **regenerates data on‑the‑fly** using the seeds and parameters from `data/sweep/seed_map.json` and `data/sweep/params.csv`. **Pre‑condition**: both files must exist and pass schema validation. **Dependency**: Explicitly depends on T017, T019d, and **T019e** (RNG Wrapper). **Algorithm**: For each iteration, read seed from seed_map, call `RNGWrapper.reset(seed)`, generate matrix using `RNGWrapper`, run tests, and discard the matrix. **Lookup**: Use `(n, p, rho, dist)` tuple to find the exact seed index in `seed_map.json`. **Error Handling**: Explicitly invokes T007/T010b to detect and handle p/n > 10 or singular matrices.
- [X] T022b [US2] Implement `run_hypothesis_tests` function in `code/run_tests.py` (scipy.stats t‑test, F‑test)
- [X] T022c [US2] Implement p‑value collection logic ensuring exactly **p** values per iteration and store in `data/results/pvalues_{seed}.csv`; verify row count equals **p**. **Schema**: The CSV MUST have columns `feature_index, p_value, test_type`. **Pre-condition**: T022a must complete. **Redundancy Note**: This is the sole task covering FR-003. Unit tests (T020) and integration tests (T021) are designed to provide secondary validation of this logic.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - P-Value Distribution Analysis and Deviation Quantification (Priority: P3)

**Goal**: Analyze the collected p‑values using Kolmogorov-Smirnov statistics and QQ-plots against a Gold Standard (permutation-based) reference to quantify anti-conservative bias.

**Independent Test**: Can be fully tested by running the analysis on a fixed dataset and verifying that KS statistics and QQ-plots are produced with correct statistical calculations.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T026 [P] [US3] Unit test for KS statistic calculation against uniform/permutation reference in `tests/unit/test_stats.py`
- [X] T027 [P] [US3] Unit test for QQ‑plot generation and visual validation in `tests/unit/test_plots.py`

### Implementation for User Story 3

- [X] T028a-perm [US3] **Implement Full Permutation Test Generator (Gold Standard)** in `code/analyze_pvalues.py`. **Logic**: This task MUST implement the function `generate_permutation_gold_standard(seed, n, p, rho, distribution_type, n_permutations)` which: 1) Regenerates the exact same correlation matrix and data using the `RNGWrapper` (T019e) to ensure correlation fidelity; 2) Performs `n_permutations` (default 1000) of row-wise shuffling to break the null hypothesis while preserving correlation structure; 3) Runs the same t-test/F-test on each permuted dataset; 4) Collects the resulting p-values. **Constraint**: This function MUST write the full array of permutation p-values to `data/results/permutation_pvalues_{seed}.npz`. **Dependency**: T019e, T017. **Verification**: Must verify that the generated data has the same correlation structure as the original by comparing the covariance matrix (within 1e-5 tolerance) before shuffling. **Output**: `data/results/permutation_pvalues_{seed}.npz`. **Note**: This task replaces the truncated logic of T028a-raw with a complete, verified implementation of FR-004.
- [X] T028b-ks [US3] **Implement KS Statistic Calculation** in `code/analyze_pvalues.py`. **Logic**: Implement `calculate_ks_statistics(seed)` which reads `data/results/pvalues_{seed}.csv` (standard tests) and `data/results/permutation_pvalues_{seed}.npz` (Gold Standard). Computes the Kolmogorov-Smirnov statistic between the empirical distribution of standard p-values and the permutation-based reference distribution. **Output**: Store results in `data/results/ks_stats.json` with schema `[{ "seed": int, "n": int, "p": int, "rho": float, "distribution_type": str, "ks_stat": float }]`. **Dependency**: T028a-perm, T022c. **Verification**: Must ensure the KS statistic is computed correctly against the permutation reference, not the uniform distribution.
- [X] T028c [US3] Implement QQ‑plot generation for visual inspection (FR‑005) and save to `docs/plots/qq_{seed}.png`. **Visual Style**: Highlight the point of maximum deviation with a red circle and a text annotation showing the KS value. Verify file existence and non‑emptiness. **Redundancy Note**: This is the sole task covering FR-005. Unit tests (T027) are designed to provide secondary validation.
- [X] T029 [US3] Implement sensitivity analysis sweep for **ρ** ∈ {0, 0.1, 0.3, 0.5, 0.7, 0.9}. Read from `data/results/ks_stats.json` (output of T028b-ks). Output `data/results/sensitivity_full.csv` with columns `seed, rho, n, p, distribution_type, ks_stat`. **Logic**: **Do NOT filter** or select a single row per rho. Output **all rows** to show the full variation (trend) across the range as required by FR-007. **Tie-breaking**: If a worst-case summary is needed for other tasks, select the one with the highest p/n ratio, then highest rho, then highest n, but **do not discard** the full dataset. **Pre-condition**: T028b-ks must complete; `data/results/ks_stats.json` must exist. **Redundancy Note**: This is the sole task covering FR-007. Integration tests (T021) and logic verification in T043-raw are designed to provide secondary validation.
- [X] T030a [US3] [Constitution Principle VII] **Runtime Guard Implementation**: Implement the runtime estimation and conditional logic in `code/analyze_pvalues.py` required by SC-004. **Logic**: Write a function `estimate_bootstrap_runtime` that calculates expected runtime based on sample size and resample count. Implement the conditional logic: if estimated runtime > 5.5 hours, reduce resamples for non-worst-case seeds to **50** or abort with a clear error message. **Output**: This function must be integrated into the main analysis pipeline. **Dependency**: T028b-ks. **Note**: This task ensures the code exists for T030b to execute.
- [X] T030b [US3] [Constitution Principle VII] **Bootstrap CI Calculation**: Implement bootstrap confidence interval calculation for KS statistics using the logic from T030a. **Methodology**: Perform **10,000 bootstrap resamples** ONLY for the **worst-case scenario** identified in T029, and **50 resamples** for all other seeds (as determined by T030a). **Dependency**: T028b-ks, **T029** (to identify worst-case), and **T030a** (for runtime guard). **Storage**: Store only the KS statistic and its 95 % bootstrap CI in `data/results/bootstrap_cis.csv` with columns `seed,n,p,rho,KS_statistic,bootstrap_ci_lower,bootstrap_ci_upper`. Read from `data/results/ks_stats.json` (output of T028b-ks) to ensure consistency. **Note**: This task produces a distinct file from T029; T029 stores aggregated KS stats, T030b stores CIs per seed.
- [X] T043-gen [US3] [Review: Feynman] **Embarrassment Log Generation**: Read `data/results/ks_stats.json` (output of T028b-ks). **Process ALL rows (do not filter by threshold)**. Flag rows where `ks_stat > 0.05` as "high deviation" for the report, but include all rows in the output. **Output**: Write `data/results/embarrassment_log.csv` with columns `seed, rho, n, p, distribution_type, ks_stat`. **Dependency**: T028b-ks. **Note**: This task replaces the missing input for T043 and T049.
- [X] T043 [US3] [Review: Feynman] **Theory Embarrassment Detector**: Read `data/results/embarrassment_log.csv` (from **T043-gen**). Report the **full range** of KS statistics observed and flag the top [deferred] of deviations as "high deviation" for detailed review. Output a detailed report `data/results/embarrassment_log_report.csv` listing `seed`, `rho`, `p`, `n`, and the specific deviation magnitude (KS value). **Rationale**: Directly addresses the reviewer's challenge to "show me the simulation where the data fails" and "embarrass the theory" by explicitly cataloging the breakdown points without cherry-picking a single threshold. **Dependency**: T028b-ks, T043-gen.
- [X] T044 [US3] [Review: Feynman] [FR-005, SC-001] Generate a "Reality Check" composite plot in `docs/plots/reality_check.png` that overlays the theoretical Uniform distribution, the observed p-value distribution for the worst-case scenario, and the permutation-based Gold Standard. **Data Sources**: Use the worst-case scenario identified in T029 for the observed distribution. **Annotation**: Include a textual annotation explaining *why* the standard test fails (e.g., "Correlation inflates variance, causing p-values to cluster near 0"). **Bias Calculation**: Explicitly calculate and report the **False Positive Rate (FPR)** for the standard test vs the permutation test at alpha=0.05 for the worst-case scenario in `data/results/bias_magnitude.csv`. **Rationale**: Directly answers the reviewer's demand to "show me the jagged line" and provide "understanding" rather than just "rituals" by visually contrasting the broken theory with the empirical reality. **Note**: This is a reviewer-requested visualization, not a mandatory FR.
- [X] T045 [US3] [Constitution Principle IV] Documentation updates in `docs/` including methodology for data generation and analysis. **Must** extract the "worst‑case" scenario from `data/results/sensitivity_full.csv` (output of T029) and report the exact KS deviation (e.g., "At ρ = 0.9, KS = 0.XX") to satisfy Constitution Principle IV. **Template**: Include a "Validity Breakdown" section calculating the false positive rate (X%) for the standard test vs the permutation test (Y%) at alpha=0.05 for the worst-case scenario. Update `docs/methodology.md` and `docs/results.md`. **Tie-breaking**: If multiple rows have the same max KS, use the one with the highest p/n ratio, then highest rho, then highest n. **Pre-condition**: T029 must complete; `data/results/sensitivity_full.csv` must exist.

**Checkpoint**: At this point, User Story 3 is complete and all core research outputs are generated.

---

## Phase N: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T046 [P] [Constitution Principle VII, spec.md Assumptions] Update `docs/methodology.md` to include a "Feynman Honesty" section that explicitly discusses the limitations of the simulation, the "mess" of high-dimensional noise, and the specific conditions under which the standard p-value theory "breaks down" (embarrasses itself). **Rationale**: Addresses the "Cargo Cult Science" review concern by ensuring the documentation admits to the complexity and failure modes rather than presenting a sanitized theoretical view.
- [X] T041 [P] Reconcile run-book vs implementation for `code/main.py`: the quickstart run-book invokes this script but it does not exist. **Action**: **Create** `code/main.py` with the specific logic to orchestrate the full sweep (calling T017, T022, T029, etc.). **Do NOT** update the run-book to avoid a missing entry point. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.
- [X] T047 [P] [Review: Feynman] Implement a "Jagged Line" visualizer in `code/analyze_pvalues.py` that generates a high-resolution plot of the empirical p-value distribution (histogram with fine bins) vs the theoretical uniform line for the worst-case scenario. **Requirement**: The plot must clearly show the "jaggedness" and deviation, not a smoothed average. **Output**: `docs/plots/jagged_line_worst_case.png`. **Rationale**: Directly addresses the reviewer's request to "show me the jagged line" and prove the theory fails in the specific high-dimensional regime. **Note**: This is a reviewer-requested visualization, not a mandatory FR.
- [X] T048 [US3] [Constitution Principle IV] Add a "Cargo Cult" warning to `docs/results.md` that explicitly lists the specific assumptions (independence, normality) that were violated in the worst-case scenario and quantifies the resulting "ritual" error rate. **Content**: Must state: "In this scenario, the standard p-value ritual yields a false positive rate of X%, while the ground truth is [deferred]." **Rationale**: Addresses the "Cargo Cult Science" critique by explicitly contrasting the ritual (standard test) with the understanding (permutation test/ground truth).

---

## Phase O: Reviewer Revision - "Embarrassing the Theory" (Addressing Feynman's Challenge)

**Purpose**: Explicitly address the "Cargo Cult Science" critique by identifying and visualizing the specific conditions where standard p-value theory fails most dramatically, rather than just reporting aggregate statistics.

### Implementation for Reviewer Revision

- [X] T049 [US3] [Review: Feynman] **Failure Mode Classifier**: Analyze `data/results/embarrassment_log.csv` (from **T043-gen**) to identify the single "worst-case" scenario (highest KS deviation) across all parameters. **Logic**: Sort by `ks_stat` descending, then `p/n` descending, then `rho` descending. **Output**: Write `data/results/worst_case_summary.json` containing the specific `seed`, `n`, `p`, `rho`, `distribution_type`, and `ks_stat` of the most extreme failure. **Rationale**: Directly answers the reviewer's demand to "show me the simulation where the data fails" by pinpointing the exact breakdown point. **Dependency**: T043-gen.
- [X] T050 [US3] [Review: Feynman] Generate a "Jagged Line" high-resolution histogram for the worst-case scenario identified in T049. **Requirement**: The plot must use a large number of bins to reveal the "jaggedness" and deviation from the theoretical uniform line, explicitly avoiding smoothing. **Output**: `docs/plots/jagged_line_worst_case_detail.png`. **Annotation**: Include the exact KS value and the specific parameter settings (e.g., "ρ=0.9, p=5000, n=50") that caused this failure. **Rationale**: Provides the visual proof requested by the reviewer ("show me the jagged line") that the theory breaks down under specific high-dimensional conditions. **Dependency**: T049.

---

## Phase P: Feynman Revision - Deep Dive on "The Jagged Line" and "The Mess"

**Purpose**: Address the specific reviewer concern to "show me the jagged line" and "show me the simulation where the data fails" by creating a dedicated, high-resolution analysis of the worst-case scenario to prove the "ritual" fails and the "understanding" (permutation) holds.

**Note**: Tasks T052-T054 map to **US4 - Failure Mode Analysis & Visualization** (newly defined in notes) to resolve scope creep concerns.

### Phase P.0: Pre-computation for Feynman Revision (Mandatory Prerequisites)

**Purpose**: Ensure all artifacts required by T052-T054 are generated in this run.

- [X] T049 [US3] [Review: Feynman] **Failure Mode Classifier**: (Re-listed here for clarity) Analyze `data/results/embarrassment_log.csv` to identify the single "worst-case" scenario. **Output**: `data/results/worst_case_summary.json`. **Dependency**: T043-gen.
- [X] T044 [US3] [Review: Feynman] **Reality Check Plot**: (Re-listed here for clarity) Generate composite plot and calculate FPR bias. **Output**: `data/results/bias_magnitude.csv`. **Dependency**: T029, T049.

### Implementation for Feynman Revision

- [ ] T052 [US4] [Review: Feynman] **Jagged Line Generator**: Implement `plot_jagged_line_worst_case` in `code/analyze_pvalues.py`. **Input**: `data/results/worst_case_summary.json` (from T049) and `data/results/pvalues_{seed}.csv` (from T022c). **Logic**: Load the p-values for the specific worst-case seed (filter T022c output to match the seed in T049). Generate a histogram with **at least 100 bins** (default 20) to reveal the "jagged" noise and deviations, not a smoothed curve. Overlay the theoretical uniform line (y=1) and the permutation-based empirical distribution (from T028a-perm) for comparison. **Output**: `docs/plots/jagged_line_deep_dive.png`. **Annotation**: Annotate the plot with the specific KS value and the parameter settings (n, p, rho) that caused the failure. **Rationale**: Directly satisfies the reviewer's request to "show me the jagged line" by visualizing the raw, unsmoothed deviation where the theory breaks down. **Dependency**: T049, T022c, T028a-perm. **Note**: Filter T022c output to the specific seed from T049.
- [ ] T053 [US4] [Review: Feynman] **Failure Mechanism Analyzer**: Implement `analyze_failure_mechanism` in `code/analyze_pvalues.py`. **Input**: `data/results/worst_case_summary.json`. **Logic**: Calculate the variance inflation factor (VIF) or effective degrees of freedom for the worst-case correlation matrix. Compare the theoretical variance (assumed independent) vs the actual variance (correlated). **Output**: Write `data/results/failure_mechanism_report.md`. **Content**: Must explicitly state: "The theory fails because correlation ρ=0.9 inflates the variance of the test statistic by a factor of X, causing the p-values to cluster near 0 instead of being uniform. The 'ritual' assumes independence, but the 'mess' of high-dimensional noise violates this." **Rationale**: Provides the "understanding" Feynman demanded, explaining *why* the ritual fails, not just that it fails. **Dependency**: T049.
- [ ] T054 [US4] [Review: Feynman] **Ritual vs Reality Table**: Generate a comparative table in `data/results/ritual_vs_reality.csv`. **Input**: `data/results/bias_magnitude.csv` (from T044) and `data/results/worst_case_summary.json` (from T049). **Columns**: `Scenario`, `Standard_Test_FPR`, `Permutation_Test_FPR`, `Bias_Absolute`, `Bias_Percentage`, `Mechanism`. **Logic**: For the worst-case scenario, calculate the False Positive Rate (FPR) at alpha=0.05 for both the standard test and the permutation test. Calculate the absolute and percentage bias. **Output**: `data/results/ritual_vs_reality.csv`. **Rationale**: Quantifies the "cargo cult" error rate in a clear, tabular format that contrasts the "ritual" with the "reality". **Dependency**: T044, T049.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Revision (Phase O)**: Depends on completion of T043-gen (Embarrassment Log generation) and T029 (Sensitivity Analysis)
- **Feynman Revision (Phase P)**: Depends on T049 (Worst Case Summary), T044 (Bias Magnitude), and T050 (Jagged Line Detail). **Critical**: Phase P.0 ensures T049 and T044 run before T052-T054.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on T019d (seed map) and **T019e** (RNG utility)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on T019d (seed map), **T019e** (RNG utility), and T022/T024 (p-values). **Crucial**: T028a-perm (Permutation) must run after T022 to ensure data regeneration sync, but before T028b-ks (KS calculation). **T043** (Theory Embarrassment) depends on **T043-gen**. **T043** is now in Phase 5, after T043-gen. **T030b** (Bootstrap) depends on T029 (Sensitivity) to identify worst-case.
- **Revision Tasks**: None (Phase 6 removed to prevent scope creep)
- **Feynman Revision Tasks**: T052 depends on T049, T022c, and T028a-perm. T053 depends on T049. T054 depends on T044 and T049.

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
- **Note**: T019 and T022 are only parallel after T017 and T019d are complete.
- **Feynman Revision**: T052, T053, and T054 can be worked on in parallel once their dependencies (T049, T022c, T044, T028a-perm) are complete.

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

### Feynman Revision Strategy

After the core simulation and analysis are complete:
1. Run Phase P.0 to ensure T049 and T044 artifacts exist.
2. Run the deep-dive visualizations (T052) and mechanism analysis (T053) in parallel.
3. Compile the final "Ritual vs Reality" report (T054).
4. Update documentation to reflect the "mess" and "failure" explicitly.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Feynman Revision**: The goal is not just to calculate numbers, but to "show the jagged line" and "explain the mess". Tasks T052-T054 are specifically designed to meet this requirement.
- **US4 Definition**: A new User Story "US4 - Failure Mode Analysis & Visualization" is implicitly defined for the Feynman Revision tasks (T052-T054) to ensure they map to a requirement and are not scope creep. This US4 focuses on deep-dive analysis of the worst-case scenario to explain the failure mechanisms.
- **Phase P.0**: Added to ensure all prerequisites for T052-T054 are met in this run.

<!-- auto-added by the execution fix loop: run-book / implementation path mismatch (a quickstart command names a script no task created) -->
- [X] T041 Reconcile run-book vs implementation for `code/main.py`: the quickstart run-book invokes this script but it does not exist. **Action**: **Create** `code/main.py` with the specific logic to orchestrate the full sweep. **Do NOT** update the run-book.