# Tasks: Assessing the Validity of p-Values in High-Dimensional Data

**Input**: Design documents from `/specs/001-assess-p-value-validity/`
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
- [X] T010a [P] Implement a memory monitor in `code/utils/simulation.py` that logs a warning if RSS > 6 GB and suggests an abort. **Constraint**: This task MUST NOT raise a hard error or abort the simulation automatically. The Spec defines memory usage < 6 GB as a performance goal, not a hard error condition. The task implements the warning only to avoid false failures during valid high-memory simulation runs.
- [X] T010b [P] Implement covariance singularity detector in `code/utils/regularization.py` that checks condition number > 10^12 and raises `ERR_HIGH_DIMENSIONAL_INSTABILITY` if regularization fails (FR‑009)
- [X] T011a [P] Implement power analysis utility function in `code/utils/simulation.py` to calculate the minimum simulation iteration count required to achieve statistical power ≥ 0.8 for detecting a KS statistic deviation > 0.05 (For reference only; not used for iteration count in this project).
- [X] T011b-doc [P] **Justification for Iteration Count**: Create `docs/power_analysis_justification.md` explicitly documenting why 1000 iterations is sufficient for SC-005 (Power ≥ 0.8). **Content**: Must cite the Plan's design parameter, reference the power analysis utility from T011a, and state that 1000 iterations provides >90% power to detect a KS deviation of 0.05. **Output**: `docs/power_analysis_justification.md`. **Note**: `data/sweep/power_analysis_result.json` is NOT generated. (SC‑005).
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

- [X] T017 [US1] Implement parameter sweep logic in `code/generate_data.py` for **n** ∈ {50, 100, 200, 500}, **p** ∈ {500, 1000, 2000, 5000}, **ρ** ∈ {0, 0.1, 0.3, 0.5, 0.7, 0.9}, **AND distribution_type** ∈ {Normal, t-dist, Skewed Normal}. **Logic**: The system MUST iterate over the **full Cartesian product** of these four parameter sets to generate every combination (4 x 4 x 6 x 3 = 288 unique parameter sets). **Iteration Count**: Use **1000 iterations** per parameter set as the fixed design parameter (Plan Design Parameters). **Seed Generation**: Seeds are generated deterministically using the formula: `seed = master_seed + (index * offset) + (n*100 + p*10 + rho_idx)` where `master_seed` is read from `data/sweep/master_seed.txt`. **Pre-condition**: This task MUST create `data/sweep/master_seed.txt` if it does not exist (default=42) before generating seeds. **Output**: `data/sweep/params.csv` with **exact schema**: Header `seed,n,p,rho,distribution_type,iteration`, delimiter `,`, UTF-8 encoding. **Pre-condition**: None (uses fixed 1000 iterations).
- [X] T018 [US1] Write `data/synthetic/{seed}.json` containing `sha256` (of the parameter row), `rho`, `n`, `p`, `distribution_type`, and `seed` for each unique parameter combination. **Serialization**: Serialize the parameter row as a JSON object with keys sorted alphabetically before hashing. Verify file exists and `sha256` matches the parameter hash (Constitution Principle III).
- [X] T019a [US1] Implement a parameter reader in `code/generate_data.py` that loads `data/sweep/params.csv` and yields rows as dictionaries. **Dependency**: T017. **Output**: Iterator of parameter dicts.
- [X] T019b [US1] Implement a streaming data generator in `code/generate_data.py` that accepts a parameter dict, sets `np.random.seed(seed_value)` **immediately before** generating each matrix, and yields the numpy array. **Constraint**: Must raise `ERR_HIGH_DIMENSIONAL_INSTABILITY` internally if `p/n > 10` or if the covariance matrix is near-singular after regularization attempts. **Thresholds**: 'Near-singular' is defined as condition number > 10^12. Regularization epsilon is 10^-6. **Dependency**: T019a.
- [X] T019c [US1] Implement a streaming data generator in `code/generate_data.py` that iterates through `data/sweep/params.csv`, sets `np.random.seed(seed_value)` **immediately before** generating each matrix, produces the data on‑the‑fly, and **yields numpy arrays to a downstream callback function**. **Callback Interface**: The callback must accept `def callback(data: np.ndarray, params: dict) -> bool`. The callback is defined locally within the generator function or passed as a lambda. **Error Handling**: The generator MUST raise `ERR_HIGH_DIMENSIONAL_INSTABILITY` internally if `p/n > 10` (FR‑009) or if the covariance matrix is near-singular after regularization attempts. **Pre-condition**: `data/sweep/params.csv` must exist (output of T017).
- [X] T019d [US1] Generate a **seed map** file `data/sweep/seed_map.json` that maps each unique `(n, p, rho, distribution_type)` tuple to a list of deterministic integer seeds. **Dependency**: Explicitly depends on T017 completion to ensure parameter rows exist. **Algorithm**: read master seed from `data/sweep/master_seed.txt` (create if missing, default = 42); for each parameter combination, assign sequential seeds starting at the master seed and incrementing by 1 for each required simulation iteration. **Verification**: This task MUST verify that `seed_map.json` contains [deferred] entries (288 params x 1000 iterations) matching the `params.csv` iteration count. **Note**: T017 generates the seeds; T019d organizes them.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Hypothesis Test Execution and p-Value Collection (Priority: P2)

**Goal**: Apply standard t‑tests and F‑tests to the synthetic null data and collect all resulting p‑values to empirically observe their distribution under violated assumptions.

**Independent Test**: Can be fully tested by running hypothesis tests on a known null dataset and verifying that p‑values are collected for every test without missing values.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T020 [P] [US2] Unit test for t‑test/F‑test execution on null data in `tests/unit/test_stats.py`
- [X] T021 [P] [US2] Integration test for full iteration loop (multiple iterations) without runtime errors in `tests/integration/test_stats.py`

### Implementation for User Story 2

- [X] T022a [US2] Implement data ingestion pipeline in `code/run_tests.py` that **regenerates data on‑the‑fly** using the seeds and parameters from `data/sweep/seed_map.json` and `data/sweep/params.csv`. **Pre‑condition**: both files must exist and pass schema validation. **Dependency**: Explicitly depends on T017, T019b, and **T019e** (RNG Wrapper). **Algorithm**: For each iteration, read seed from seed_map, call `RNGWrapper.reset(seed)`, generate matrix using `RNGWrapper`, run tests, and discard the matrix. **Lookup**: Use `(n, p, rho, dist)` tuple to find the exact seed index in `seed_map.json`.
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

- [X] T028a-raw [US3] Implement permutation test generator in `code/analyze_pvalues.py` (Gold Standard respecting correlation structure). **Dependency**: Explicitly depends on T019b and **T019e** (RNG Wrapper). **Deterministic regeneration**: for each seed, call `RNGWrapper.reset(seed)` **immediately before** generating the matrix (using the same seed map) to ensure the permutation respects the original correlation structure. **Permutation Logic**: **Shuffle rows of the latent factor matrix BEFORE applying the Cholesky transform** to break the null hypothesis while preserving the correlation structure between features. **Constraint**: Must use the exact same seed sequence as T022 via T019e to ensure valid comparison. **Output**: Store the full array of permutation p-values in `data/results/permutation_pvalues_{seed}.npz` (compressed NumPy format). **Pre-condition**: `data/sweep/seed_map.json` must exist. **Note**: This task MUST complete before T028b.
- [X] T028b [US3] Implement KS statistic calculation comparing standard tests to the permutation reference (FR‑004) and store results in `data/results/ks_stats.json`. **Schema**: The JSON file MUST contain a list of objects: `[{ "seed": int, "n": int, "p": int, "rho": float, "distribution_type": str, "ks_stat": float }]`. **Input**: Read `data/results/pvalues_{seed}.csv` (standard) and `data/results/permutation_pvalues_{seed}.npz` (reference). **Constraint**: **Do store** the full array of permutation p-values (generated by T028a-raw) to enable verification. **Pre-condition**: T022 and T028a-raw must complete; `data/results/pvalues_*.csv` and `permutation_pvalues_*.npz` must exist. **Redundancy Note**: This is the sole task covering FR-004. Unit tests (T026) are designed to provide secondary validation.
- [X] T028c [US3] Implement QQ‑plot generation for visual inspection (FR‑005) and save to `docs/plots/qq_{seed}.png`. **Visual Style**: Highlight the point of maximum deviation with a red circle and a text annotation showing the KS value. Verify file existence and non‑emptiness. **Redundancy Note**: This is the sole task covering FR-005. Unit tests (T027) are designed to provide secondary validation.
- [X] T029 [US3] Implement sensitivity analysis sweep for **ρ** ∈ {0, 0.1, 0.3, 0.5, 0.7, 0.9}. Read from `data/results/ks_stats.json` (output of T028b). Output `data/results/sensitivity.csv` with columns `rho,n,p,ks_stat,worst_case_flag`. **Tie-breaking**: If multiple rows share the exact maximum KS for a given rho, select the one with the highest p/n ratio, then highest rho, then highest n. Set `worst_case_flag` to True for the selected row (FR‑007). **Pre-condition**: T028b must complete; `data/results/ks_stats.json` must exist. **Redundancy Note**: This is the sole task covering FR-007. Integration tests (T021) and logic verification in T043-raw are designed to provide secondary validation.
- [X] T030 [US3] [Constitution Principle VII] Implement bootstrap confidence interval calculation for KS statistics. **Justification**: Constitution Principle VII mandates reporting KS + bootstrap CI. **Methodology**: Perform **10,000 bootstrap resamples** ONLY for the **worst-case scenario** identified in T029, and **100 resamples** for all other seeds to satisfy SC-004 (≤6h runtime). Compute the confidence interval for the KS statistic against the **fixed** permutation reference distribution. **Runtime Guard**: Before starting, estimate total runtime. If estimated runtime > 5.5 hours, automatically reduce resamples for non-worst-case seeds to 50 or abort with a clear error message. **Storage**: Store only the KS statistic and its 95 % bootstrap CI in `data/results/bootstrap_cis.csv` with columns `seed,n,p,rho,KS_statistic,bootstrap_ci_lower,bootstrap_ci_upper`. Read from `data/results/ks_stats.json` (output of T028b) to ensure consistency. Do **not** store raw permutation p‑value arrays to satisfy Data Hygiene (Principle III) and size constraints. **Note**: This task produces a distinct file from T029; T029 stores aggregated KS stats, T030 stores CIs per seed.
- [X] T043-gen [US3] [Review: Feynman] **Embarrassment Log Generation**: Read `data/results/ks_stats.json` (output of T028b). **Process ALL rows (do not filter by threshold)**. Flag rows where `ks_stat > 0.05` as "high deviation" for the report, but include all rows in the output. **Output**: Write `data/results/embarrassment_log.csv` with columns `seed, rho, n, p, distribution_type, ks_stat`. **Dependency**: T028b. **Note**: This task replaces the missing input for T043 and T049.
- [X] T043 [US3] [Review: Feynman] **Theory Embarrassment Detector**: Read `data/results/embarrassment_log.csv` (from **T043-gen**). Report the **full range** of KS statistics observed and flag the top [deferred] of deviations as "high deviation" for detailed review. Output a detailed report `data/results/embarrassment_log_report.csv` listing `seed`, `rho`, `p`, `n`, and the specific deviation magnitude (KS value). **Rationale**: Directly addresses the reviewer's challenge to "show me the simulation where the data fails" and "embarrass the theory" by explicitly cataloging the breakdown points without cherry-picking a single threshold. **Dependency**: T043-gen.
- [X] T044 [US3] [Review: Feynman] [FR-005, SC-001] Generate a "Reality Check" composite plot in `docs/plots/reality_check.png` that overlays the theoretical Uniform distribution, the observed p-value distribution for the worst-case scenario, and the permutation-based Gold Standard. **Data Sources**: Use the worst-case scenario identified in T029 for the observed distribution. **Annotation**: Include a textual annotation explaining *why* the standard test fails (e.g., "Correlation inflates variance, causing p-values to cluster near 0"). **Bias Calculation**: Explicitly calculate and report the **False Positive Rate (FPR)** for the standard test vs the permutation test at alpha=0.05 for the worst-case scenario in `data/results/bias_magnitude.csv`. **Rationale**: Directly answers the reviewer's demand to "show me the jagged line" and provide "understanding" rather than just "rituals" by visually contrasting the broken theory with the empirical reality. **Note**: This is a reviewer-requested visualization, not a mandatory FR.
- [X] T045 [US3] [Constitution Principle IV] Documentation updates in `docs/` including methodology for data generation and analysis. **Must** extract the "worst‑case" scenario from `data/results/sensitivity.csv` and report the exact KS deviation (e.g., "At ρ = 0.9, KS = 0.XX") to satisfy Constitution Principle IV. **Template**: Include a "Validity Breakdown" section calculating the false positive rate (X%) for the standard test vs the permutation test (Y%) at alpha=0.05 for the worst-case scenario. Update `docs/methodology.md` and `docs/results.md`. **Tie-breaking**: If multiple rows have the same max KS, use the one with the highest p/n ratio, then highest rho, then highest n. **Pre-condition**: T029 must complete; `data/results/sensitivity.csv` must exist.

**Checkpoint**: At this point, User Story 3 is complete and all core research outputs are generated.

---

## Phase N: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T046 [P] [Constitution Principle VII, spec.md Assumptions] Update `docs/methodology.md` to include a "Feynman Honesty" section that explicitly discusses the limitations of the simulation, the "mess" of high-dimensional noise, and the specific conditions under which the standard p-value theory "breaks down" (embarrasses itself). **Rationale**: Addresses the "Cargo Cult Science" review concern by ensuring the documentation admits to the complexity and failure modes rather than presenting a sanitized theoretical view.
- [X] T041 [P] Reconcile run-book vs implementation for `code/main.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/main.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.
- [X] T047 [P] [Review: Feynman] Implement a "Jagged Line" visualizer in `code/analyze_pvalues.py` that generates a high-resolution plot of the empirical p-value distribution (histogram with fine bins) vs the theoretical uniform line for the worst-case scenario. **Requirement**: The plot must clearly show the "jaggedness" and deviation, not a smoothed average. **Output**: `docs/plots/jagged_line_worst_case.png`. **Rationale**: Directly addresses the reviewer's request to "show me the jagged line" and prove the theory fails in the specific high-dimensional regime. **Note**: This is a reviewer-requested visualization, not a mandatory FR.
- [X] T048 [US3] [Constitution Principle IV] Add a "Cargo Cult" warning to `docs/results.md` that explicitly lists the specific assumptions (independence, normality) that were violated in the worst-case scenario and quantifies the resulting "ritual" error rate. **Content**: Must state: "In this scenario, the standard p-value ritual yields a false positive rate of X%, while the ground truth is [deferred]." **Rationale**: Addresses the "Cargo Cult Science" critique by explicitly contrasting the ritual (standard test) with the understanding (permutation test/ground truth).

---

## Phase O: Reviewer Revision - "Embarrassing the Theory" (Addressing Feynman's Challenge)

**Purpose**: Explicitly address the "Cargo Cult Science" critique by identifying and visualizing the specific conditions where standard p-value theory fails most dramatically, rather than just reporting aggregate statistics.

### Implementation for Reviewer Revision

- [X] T049 [US3] [Review: Feynman] Implement a "Failure Mode Classifier" in `code/analyze_pvalues.py` that analyzes the `data/results/embarrassment_log.csv` (from **T043-gen**) to identify the single "worst-case" scenario (highest KS deviation) across all parameters. **Logic**: Sort by `ks_stat` descending, then `p/n` descending, then `rho` descending. **Output**: Write `data/results/worst_case_summary.json` containing the specific `seed`, `n`, `p`, `rho`, `distribution_type`, and `ks_stat` of the most extreme failure. **Rationale**: Directly answers the reviewer's demand to "show me the simulation where the data fails" by pinpointing the exact breakdown point. **Dependency**: T043-gen.
- [X] T050 [US3] [Review: Feynman] Generate a "Jagged Line" high-resolution histogram for the worst-case scenario identified in T049. **Requirement**: The plot must use a large number of bins. to reveal the "jaggedness" and deviation from the theoretical uniform line, explicitly avoiding smoothing. **Output**: `docs/plots/jagged_line_worst_case_detail.png`. **Annotation**: Include the exact KS value and the specific parameter settings (e.g., "ρ=0.9, p=5000, n=50") that caused this failure. **Rationale**: Provides the visual proof requested by the reviewer ("show me the jagged line") that the theory breaks down under specific high-dimensional conditions. **Dependency**: T049.
- [X] T051 [US3] [Review: Feynman] Update `docs/results.md` with a "Feynman Honesty" section that explicitly contrasts the "ritual" (standard t-test) with the "understanding" (permutation test) for the worst-case scenario. **Content**: Must state: "In the scenario where ρ=0.9 and p/n=100, the standard test yields a false positive rate of X% (ritual), while the permutation test (ground truth) shows the true rate is Y%. The theory 'breaks down' because [specific mechanism: e.g., correlation inflates variance]." **Rationale**: Directly addresses the "Cargo Cult Science" critique by admitting to the mess and explaining *why* the ritual fails, rather than just presenting sanitized numbers. **Dependency**: T049.

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

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on T019d (seed map) and **T019e** (RNG utility)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on T019d (seed map), **T019e** (RNG utility), and T022/T024 (p-values). **Crucial**: T028a-raw (Permutation) must run after T022 to ensure data regeneration sync, but before T028b (KS calculation). **T043** (Theory Embarrassment) depends on **T043-gen**. **T043** is now in Phase 5, after T043-gen.
- **Revision Tasks**: None (Phase 6 removed to prevent scope creep)

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

<!-- auto-added by the execution fix loop: run-book / implementation path mismatch (a quickstart command names a script no task created) -->
- [X] T041 Reconcile run-book vs implementation for `code/main.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/main.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.