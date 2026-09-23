# Tasks: Investigating the Impact of Network Structure on Energy Dissipation in Driven Oscillators

**Input**: Design documents from `/specs/001-investigate-network-dissipation/`
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

**Purpose**: Project initialization, basic structure, and draft schemas

- [ ] T001a [P] Create directory structure: `code/`, `data/`, `data/raw/`, `data/processed/`, `data/analysis/`, `tests/`, `contracts/`, `state/` using `mkdir -p code data/raw data/processed data/analysis tests contracts state`.
- [X] T001b Create `code/__init__.py` and `data/.gitkeep` files
- [X] T001c Initialize `code/requirements.txt` with pinned versions for `networkx`, `scipy`, `numpy`, `pandas`, `matplotlib`, `scikit-learn`, `statsmodels`, `pytest`
- [X] T002 [P] Configure linting: Create `pyproject.toml` with `[tool.ruff]` section, set `line-length = 88`, `target-version = "py311"`, and run `ruff init` to initialize the configuration.
- [ ] T003 [P] Configure pre-commit hooks: Run `pre-commit init`, create `.pre-commit-config.yaml` with hooks for `ruff` (linting) and `black` (formatting), and run `pre-commit install`.
- [ ] T006a [P] Draft `contracts/network_schema.schema.yaml` using Pydantic v2 to define expected structure for `data/raw/networks.csv` (columns: id, class, N, clustering_coeff, avg_path_length, degree_dist_summary...).
- [ ] T006b [P] Draft `contracts/energy_schema.schema.yaml` using Pydantic v2 to define expected structure for `data/processed/energy_decay.csv` (columns: graph_id, decay_rate, r_squared, status, convergence_std...).
- [ ] T006c [P] Draft `contracts/regression_schema.schema.yaml` using Pydantic v2 to define expected structure for `data/analysis/regression_results.json`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement `code/utils/metrics.py` with functions to compute clustering coefficient, average path length, and degree distribution statistics
- [X] T005 [P] Implement `code/utils/diagnostics.py` with functions for VIF calculation, convergence plotting, and Laplacian eigenvalue validation
- [X] T008 Implement `code/utils/checksums.py` to generate SHA256 checksums for all files in `data/`. **CRITICAL**: The script MUST parse the YAML file `state/projects/PROJ-440-investigating-the-impact-of-network-stru.yaml`, locate the `artifact_hashes` map, and update it with the new checksums for the generated data files. [UNRESOLVED-CLAIM: c_5f124589 — status=not_enough_info] Run `python code/utils/checksums.py --update` to register artifacts. **Depends on**: T001a (directory creation).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Generate Topological Networks and Compute Metrics (Priority: P1) 🎯 MVP

**Goal**: Generate diverse synthetic oscillator network topologies (Random, Scale-Free, Small-World, Lattice, Star) and compute static structural metrics.

**Independent Test**: Verify output CSV contains ≥50 rows (min 10 per class), valid metrics (clustering 0-1), and theoretical matches (KS-test p>0.05 for Scale-Free).

### Tests for User Story 1 (OPTIONAL -only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T009a [P] [US1] Unit test `test_generate_random_graphs` in `tests/test_generation.py`: {{claim:c_1a2af28f}} (OEIS A003024, https://oeis.org/A003024)
- [X] T009b [P] [US1] Unit test `test_generate_scale_free_graphs` in `tests/test_generation.py`: assert 10 graphs generated, all labeled "scale_free", power-law fit p>0.05
- [X] T009c [P] [US1] Unittest `test_generate_all_classes` in `tests/test_generation.py`: assert a set of graphs distributed across multiple classes, with a balanced representation per class.
- [X] T010a [P] [US1] Unit test `test_clustering_coefficient_bounds` in `tests/test_generation.py`: assert clustering coefficient is between 0 and 1 for all generated graphs
- [X] T010b [P] [US1] Unit test `test_path_length_bounds` in `tests/test_generation.py`: assert average path length is positive and finite for all generated graphs
- [X] T011a [P] [US1] Integration test `test_full_generation_pipeline` in `tests/test_generation.py`: assert `data/raw/networks.csv` exists and contains a representative set of network instances., columns match schema (id, class, clustering, path_length...)

### Implementation for User Story 1

- [X] T012 [P] [US1] Implement `code/generate_networks.py` to generate 50+ networks (N=100-200) across 5 classes (Random, Scale-Free, Small-World, Lattice, Star) with pinned random seeds. [UNRESOLVED-CLAIM: c_02dd576d — status=not_enough_info] **Ensure at least 10 realizations per class ** to meet FR-001.
- [X] T013 [US1] Implement metric calculation logic in `code/generate_networks.py` by CALLING functions from `code/utils/metrics.py` (T004) to compute average degree, clustering, path length, degree distribution
- [X] T014a [US1] Implement theoretical validation for Scale-Free graphs: Perform KS-test on degree distribution against power law (p > 0.05) in `code/generate_networks.py`
- [X] T014b [US1] Implement theoretical validation for Random graphs: Verify average degree and clustering coefficient within 5% of theoretical expectations in `code/generate_networks.py`
- [ ] T016a [P] [US1] Implement error logging for generation failures: **Catch all exceptions** during graph generation. Log to `state/failedGraphs.log` in format `GRAPH_ID|ISO8601_TIMESTAMP|ERROR_TYPE|MESSAGE`. ERROR_TYPE must be one of: 'NETWORKX_ERROR', 'METRIC_CALC_FAILURE', 'KS_TEST_FAIL'. Continue processing remaining graphs on failure.
- [ ] T016b [US1] Implement filtering logic: Read `state/failedGraphs.log` and filter out any graph IDs listed before final export.
- [X] T015 [US1] Implement data export to `data/raw/networks.csv` with checksum generation. **Depends on T016b**: The export logic must read `state/failedGraphs.log` to exclude entries, ensuring only valid graphs are written to the final CSV.
- [ ] T028 [US1] [P] **REMOVED**: Power limitation check logic moved to generation task T012 to ensure generation guarantees the count, not a runtime halt.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Simulate Driven Damped Oscillator Dynamics (Priority: P2)

**Goal**: Numerically integrate coupled harmonic oscillator equations on generated topologies to extract energy decay rates.

**Independent Test**: Verify decay rate matches analytical solution (λ = damping/2) within 1% error on a known ring graph [UNRESOLVED-CLAIM: c_27db228c — status=not_enough_info]; verify R² ≥ 0.95 for fits.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T017a [P] [US2] Unit test `test_energy_conservation_no_damping` in `tests/test_simulation.py`: assert energy variance < 1e-6 for undamped system
- [X] T017b [P] [US2] Unit test `test_analytical_decay_match` in `tests/test_simulation.py`: assert decay rate matches λ = damping/2 within 1% for ring graph [UNRESOLVED-CLAIM: c_87169312 — status=not_enough_info]
- [X] T018a [P] [US2] Unit test `test_decay_extraction_fit` in `tests/test_simulation.py`: assert damped sinusoid fit on synthetic data returns R² ≥ 0.95 and correct λ
- [X] T019a [P] [US2] Unit test `test_resonance_detection` in `tests/test_simulation.py`: assert negative decay rate is flagged when driving frequency matches natural mode

### Implementation for User Story 2

- [X] T020 [P] [US2] Implement `code/simulate_oscillators.py` to define coupled harmonic oscillator equations of motion using Laplacian matrix
- [X] T021a [P] [US2] Implement ODE function `dynamics(t, y, adj_matrix, damping, driving_freq)` in `code/simulate_oscillators.py` (Parallel-safe, no data dependency)
- [X] T021b [US2] Implement `solve_ivp` integration (T=200, driving active T=0-100) using `RK45` or `DOP853` [UNRESOLVED-CLAIM: c_8fe4b455 — status=not_enough_info] in `code/simulate_oscillators.py` (Depends on T015: requires `data/raw/networks.csv`)
- [ ] T022a [P] [US2] Implement energy decay extraction logic: Define function `fit_damped_sinusoid(t, E)` in `code/simulate_oscillators.py` using `scipy.optimize.curve_fit` to fit `E(t) = A * exp(-λt) * cos(ωt + φ) + C` to post-transient phase (t > 100). Output: dictionary with fitted parameters (A, λ, ω, φ, C) and R².
- [ ] T022b [US2] Implement fit validation (R² ≥ 0.95) and resonance detection (negative decay rate flagging) (Depends on T022a, T021b)
- [ ] T022c [US2] Implement explicit resonance detection logic: Calculate decay rate from fit; if decay rate is negative, flag instance as 'resonant' and set status column to 'resonant' in output. (Depends on T022b)
- [ ] T023a [P] [US2] Implement convergence testing logic: Define function `run_convergence_test(graph_id, num_seeds=10)` in `code/simulate_oscillators.py` that runs simulation with 10 different random seeds for a given graph. [UNRESOLVED-CLAIM: c_5c3d77ce — status=not_enough_info] Output: `data/analysis/convergence_data.csv` containing decay rates per seed and calculated std/mean.
- [X] T024a [US2] Select representative topologies: Load `data/raw/networks.csv` (T015), select **one graph per topological class** (Random, Scale-Free, Small-World, Lattice, Star) by calculating the median average degree for each class; if ties, select the graph with the lowest graph ID. Output list of selected graph IDs to `data/analysis/convergence_targets.json`. (Depends on T015; US2 cannot start until US1 data is generated)
- [ ] T024b [US2] Execute convergence testing: Run simulation with multiple random seeds for each graph ID in `data/analysis/convergence_targets.json` using the algorithm from T023a. Calculate standard deviation of decay rates. **Contingency**: If `std/mean >= 0.01` (SC-006), log a 'Numerical Instability Warning' to `state/simulation_failures.log`, mark the result as 'unstable' (do not fail the build), and proceed. If `std/mean < 0.01`, mark as 'stable'. [UNRESOLVED-CLAIM: c_3ba88909 — status=not_enough_info] (Depends on T024a, T023a)
- [ ] T024c [US2] Generate convergence plot artifact: Create `data/analysis/convergence_plot.png` showing decay rate variance across seeds to satisfy Spec FR-008. (Depends on T024b)
- [ ] T027a [P] [US2] Implement error logging for non-convergence: Catch exceptions during `solve_ivp`, log the specific graph ID and error message to `state/simulation_failures.log` with format `GRAPH_ID|ISO8601_TIMESTAMP|ERROR_TYPE|MESSAGE`. ERROR_TYPE must be one of: 'SOLVE_IVP_CONVERGENCE_FAIL', 'FIT_R2_LOW', 'NUMERICAL_INSTABILITY'.
- [ ] T027b [US2] Implement filtering logic for simulation failures: Read `state/simulation_failures.log` and filter out any graph IDs listed before final export.
- [ ] T025 [US2] Implement Laplacian eigenvalue validation against analytical solution for a ring graph
- [ ] T026 [US2] Export results to `data/processed/energy_decay.csv` with checksums; include a 'status' column ('dissipative' or 'resonant') to flag resonant instances (per Edge Cases) and record exclusion counts in the final report. **Depends on T027b**.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Perform Statistical Correlation Analysis (Priority: P3)

**Goal**: Perform **Partial Least Squares (PLS) Regression** (per Plan.md "Statistical Rigor" section) with multiple-comparison corrections, sensitivity analysis, and VIF checks to correlate topology with dissipation. **Note**: While Spec FR-004 requests PCR, the Plan explicitly selects PLS to maximize covariance and handle collinearity better; this task implements the Plan's chosen method.

**Independent Test**: Verify PLS output includes coefficients, corrected p-values, VIP scores, and that sensitivity sweep reports stability.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T028a [P] [US3] Unit test `test_pcr_coefficient_calculation` in `tests/test_regression.py`: assert PCR coefficients are calculated correctly for a known input matrix (Adapt to PLS)
- [X] T029a [P] [US3] Unit test `test_bonferroni_correction` in `tests/test_regression.py`: assert corrected p-values match expected values for a known input list

### Implementation for User Story 3

- [ ] T031a [US3] Implement data loading and validation in `code/analyze_regression.py`: Load `data/raw/networks.csv` and `data/processed/energy_decay.csv`. **Depends on T015 and T026**.
- [ ] T031b [P] [US3] Implement filtering logic: Define function `filter_resonant(dataset)` in `code/analyze_regression.py` to filter out rows where `status='resonant'`. Output: filtered dataset in memory or `data/analysis/filtered_decay.csv`. (Depends on T031a, T022c)
- [ ] T031c [P] [US3] Initialize regression model structure in `code/analyze_regression.py` (Parallel-safe, no data dependency)
- [ ] T032a [US3] **Compute PCA Loadings**: Implement `compute_pca_loadings` in `code/analyze_regression.py`. Input: filtered topological metrics. Output: `data/analysis/pca_loadings.json` containing loadings for PC1 and PC2 for each metric. **Depends on T031b**.
- [ ] T032b [US3] **Generate Loadings Table**: Implement `generate_loadings_table` in `code/analyze_regression.py`. Input: `data/analysis/pca_loadings.json`. Output: `data/analysis/loadings_table.md` containing a markdown table of PC1/PC2 loadings. **Depends on T032a**.
- [ ] T032c [US3] **Generate Interpretation Report**: Implement `generate_interpretation_report` in `code/analyze_regression.py`. Input: `data/analysis/pca_loadings.json`. **Apply strict deterministic template rule**: For each metric, if `|loading| > 0.5`, write "Strong association with PC[1/2]"; if `0.3 < |loading| <= 0.5`, write "Moderate association"; else "Weak association". Output: `data/analysis/interpretation_report.md`. **Depends on T032a**.
- [ ] T032 [US3] **Perform Partial Least Squares (PLS) Regression**: Implement `run_pls` in `code/analyze_regression.py`. 1) Load PC loadings from T032a. 2) Perform PLS regression of decay rates against topological metrics (using `PLSRegression` from `sklearn`). 3) Output regression coefficients, VIP scores, and p-values to `data/analysis/regression_results.json`. **CRITICAL**: Ensure the output explicitly reports the loadings for PC1 and PC2 as required by FR-009. **Note**: This implements the Plan's chosen PLS method, deviating from Spec FR-004's PCR requirement. **Depends on T032a**.
- [ ] T033 [US3] Implement statistical inference for PLS: Calculate regression coefficients, standard errors, p-values. Apply Bonferroni or Holm-Bonferroni correction to p-values. (Depends on T032)
- [ ] T034 [US3] Implement sensitivity analysis: sweep significance threshold across standard levels (e.g., p ∈ {typical small values, conventional significance levels}) and **report the variance in the number of significant predictors** across the sweep to satisfy SC-004. Output: `data/analysis/sensitivity_report.csv` with columns: threshold, significant_count, stability_metric. (Depends on T033)
- [ ] T035 [US3] Implement VIF check: {{claim:c_37432b56}} (Wikidata Q113106917, https://www.wikidata.org/wiki/Q113106917) and frame results descriptively (integrated into T033)
- [ ] T037 [US3] Generate final regression results report and loadings table in `data/analysis/regression_results.json` and `data/analysis/regression_results.md`; include PLS coefficients, corrected p-values, **loadings for PC1/PC2**, and the count of excluded resonant instances (Depends on T034, T032b, T032c)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T041a [P] Update `quickstart.md` with environment setup, data generation, simulation, and analysis steps
- [ ] T041b [P] Update `README.md` with project overview, installation instructions, and usage examples
- [ ] T042a Code cleanup: run linter (ruff) and fix all errors/warnings
- [ ] T042b Code cleanup: run formatter (black) and remove unused imports
- [ ] T043 [US3] Execute `code/benchmark_pipeline.py` to run the full pipeline on the standard runner; record the total wall-clock time in `state/projects/PROJ-440-investigating-the-impact-of-network-stru.yaml` and verify it is ≤ 6 hours (validating Plan's < 2h estimate and Spec FR-007)
- [ ] T044a [P] Additional unit test `test_stiff_network_convergence` in `tests/test_simulation.py` for scale-free networks with extreme degree disparity
- [ ] T044b [P] Additional unit test `test_resonance_edge_case` in `tests/test_simulation.py` for driving frequency matching natural mode
- [ ] T045 Run `quickstart.md` validation to ensure full pipeline reproducibility
- [ ] T046 [P] Implement `code/benchmark_pipeline.py` script to automate the full pipeline execution and timing measurement for T043

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data generation (needs `data/raw/networks.csv`)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 and US2 data (needs `data/raw/networks.csv` and `data/processed/energy_decay.csv`)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Utils/Metrics before Generation/Simulation
- Generation/Simulation before Analysis
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models/Utils within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members (once data dependencies are managed via mock data or sequential execution)
- **Split Tasks**: Tasks marked [P] within a story (e.g., T021a, T022a, T023a) can be implemented in parallel before the integration tasks (T021b, T022b, T024b) that require real data.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for graph generation logic in tests/test_generation.py"
Task: "Unit test for metric computation in tests/test_generation.py"

# Launch all models for User Story 1 together:
Task: "Implement code/generate_networks.py to generate 50+ networks"
Task: "Implement metric calculation logic in code/generate_networks.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (generate 50 networks, verify metrics)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (needs US1 data)
4. Add User Story 3 → Test independently → Deploy/Demo (needs US1 & US2 data)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Data Generation)
 - Developer B: User Story 2 (Simulation - can use mock data initially for T021a, T022a, T023a)
 - Developer C: User Story 3 (Analysis - can use mock data initially for T031c)
3. Stories complete and integrate independently; final run uses real generated data.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence