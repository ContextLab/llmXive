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

**Purpose**: Project initialization and basic structure

- [ ] T001a Create directory structure: `code/`, `data/`, `data/raw/`, `data/processed/`, `data/analysis/`, `tests/`, `contracts/`, `state/`
- [X] T001b Create `code/__init__.py` and `data/.gitkeep` files
- [X] T001c Initialize `code/requirements.txt` with pinned versions for `networkx`, `scipy`, `numpy`, `pandas`, `matplotlib`, `scikit-learn`, `statsmodels`, `pytest`
- [ ] T002 [P] Configure linting (ruff/flake8) and formatting (black) tools
- [ ] T003 [P] Configure pre-commit hooks for linting and formatting

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement `code/utils/metrics.py` with functions to compute clustering coefficient, average path length, and degree distribution statistics
- [X] T005 [P] Implement `code/utils/diagnostics.py` with functions for VIF calculation, convergence plotting, and Laplacian eigenvalue validation
- [ ] T006a Create `contracts/network_schema.schema.yaml` defining structure for `data/raw/networks.csv` (columns: id, class, N, metrics...) per Spec data structure requirements
- [ ] T006b Create `contracts/energy_schema.schema.yaml` defining structure for `data/processed/energy_decay.csv` (columns: graph_id, decay_rate, r_squared, status...) per Spec data structure requirements
- [ ] T006c Create `contracts/regression_schema.schema.yaml` defining structure for `data/analysis/regression_results.json` per Spec data structure requirements
- [X] T008 Implement `code/utils/checksums.py` to generate and verify SHA256 checksums for all files in `data/`; run `python code/utils/checksums.py --update` to register artifacts in `state/`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Generate Topological Networks and Compute Metrics (Priority: P1) 🎯 MVP

**Goal**: Generate diverse synthetic oscillator network topologies (Random, Scale-Free, Small-World, Lattice, Star) and compute static structural metrics.

**Independent Test**: Verify output CSV contains ≥50 rows (min 10 per class), valid metrics (clustering 0-1), and theoretical matches (KS-test p>0.05 for Scale-Free).

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T009a [P] [US1] Unit test `test_generate_random_graphs` in `tests/test_generation.py`: assert 10 graphs generated, all labeled "random", N=100
- [X] T009b [P] [US1] Unit test `test_generate_scale_free_graphs` in `tests/test_generation.py`: assert 10 graphs generated, all labeled "scale_free", power-law fit p>0.05
- [X] T009c [P] [US1] Unit test `test_generate_all_classes` in `tests/test_generation.py`: assert a set of graphs distributed across multiple classes, with a balanced representation per class.
- [X] T010a [P] [US1] Unit test `test_clustering_coefficient_bounds` in `tests/test_generation.py`: assert clustering coefficient is between 0 and 1 for all generated graphs
- [X] T010b [P] [US1] Unit test `test_path_length_bounds` in `tests/test_generation.py`: assert average path length is positive and finite for all generated graphs
- [X] T011a [P] [US1] Integration test `test_full_generation_pipeline` in `tests/test_generation.py`: assert `data/raw/networks.csv` exists and contains a representative set of network instances., columns match schema (id, class, clustering, path_length...)

### Implementation for User Story 1

- [X] T012 [P] [US1] Implement `code/generate_networks.py` to generate 50+ networks (N=100-200) across 5 classes (Random, Scale-Free, Small-World, Lattice, Star) with pinned random seeds
- [X] T013 [US1] Implement metric calculation logic in `code/generate_networks.py` by CALLING functions from `code/utils/metrics.py` (T004) to compute average degree, clustering, path length, degree distribution
- [X] T014a [US1] Implement theoretical validation for Scale-Free graphs: Perform KS-test on degree distribution against power law (p > 0.05) in `code/generate_networks.py`
- [X] T014b [US1] Implement theoretical validation for Random graphs: Verify average degree and clustering coefficient within 5% of theoretical expectations in `code/generate_networks.py`
- [X] T014c [US1] Implement theoretical validation for Small-World and Lattice graphs: Verify **average path length** matches theoretical expectations (high clustering, low path length for Small-World; regular degree, high path length for Lattice) in `code/generate_networks.py`
- [X] T015 [US1] Implement data export to `data/raw/networks.csv` with checksum generation
- [ ] T016 [US1] Add error handling for generation failures (log specific graph ID, exclude from final set)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Simulate Driven Damped Oscillator Dynamics (Priority: P2)

**Goal**: Numerically integrate coupled harmonic oscillator equations on generated topologies to extract energy decay rates.

**Independent Test**: Verify decay rate matches analytical solution (λ = damping/2) within 1% error on a known ring graph; verify R² ≥ 0.95 for fits.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T017a [P] [US2] Unit test `test_energy_conservation_no_damping` in `tests/test_simulation.py`: assert energy variance < 1e-6 for undamped system
- [X] T017b [P] [US2] Unit test `test_analytical_decay_match` in `tests/test_simulation.py`: assert decay rate matches λ = damping/2 within 1% for ring graph
- [X] T018a [P] [US2] Unit test `test_decay_extraction_fit` in `tests/test_simulation.py`: assert damped sinusoid fit on synthetic data returns R² ≥ 0.95 and correct λ
- [X] T019a [P] [US2] Unit test `test_resonance_detection` in `tests/test_simulation.py`: assert negative decay rate is flagged when driving frequency matches natural mode

### Implementation for User Story 2

- [X] T020 [P] [US2] Implement `code/simulate_oscillators.py` to define coupled harmonic oscillator equations of motion using Laplacian matrix
- [ ] T021 [US2] Implement `solve_ivp` integration (T=200, driving active T=0-100) using `RK45` or `DOP853` in `code/simulate_oscillators.py` (Depends on T015: requires `data/raw/networks.csv`)
- [ ] T022 [US2] Implement energy decay extraction: fit damped sinusoid model `E(t) = A * exp(-λt) * cos(ωt + φ) + C` to post-transient phase (t > 100) and enforce R² ≥ 0.95 as a hard pass/fail condition
- [ ] T023 [US2] Implement fit validation (R² ≥ 0.95) and resonance detection (negative decay rate flagging)
- [ ] T024 [US2] Implement convergence testing:
 1. **Wait for T015 completion** to access `data/raw/networks.csv`.
 2. Select a **representative topology**: the graph with the **median average degree** from `data/raw/networks.csv`.
 3. Run simulation on multiple random seeds for this topology.
 4. Calculate standard deviation of decay rates.
 5. **Assert `std/mean < 0.01`** (per SC-006).
 6. Output a variance plot to `data/analysis/convergence_plot.png` and metrics to `data/analysis/convergence_metrics.json`.
 (Depends on T015 completion to select topology)
- [ ] T025 [US2] Implement Laplacian eigenvalue validation against analytical solution for a ring graph
- [ ] T026 [US2] Export results to `data/processed/energy_decay.csv` with checksums; include a 'status' column ('dissipative' or 'resonant') to flag resonant instances (per Edge Cases) and record exclusion counts in the final report
- [ ] T027 [US2] Add robust error handling for non-convergence (log graph ID, exclude from analysis)
- [ ] T028 [US2] Implement power limitation check: Verify dataset size (samples) >= 10 * number of predictors. If insufficient, **halt execution** and generate `data/analysis/power_warning.txt` with a specific warning message. (Depends on T015 completion)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Perform Statistical Correlation Analysis (Priority: P3)

**Goal**: Perform Partial Least Squares (PLS) Regression (per Plan's Statistical Rigor section) with multiple-comparison corrections, sensitivity analysis, and null model validation to correlate topology with dissipation.

**Independent Test**: Verify PLS output includes coefficients, VIP scores, corrected p-values, and that sensitivity sweep reports stability.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T028a [P] [US3] Unit test `test_pcr_coefficient_calculation` in `tests/test_regression.py`: assert PCR coefficients are calculated correctly for a known input matrix
- [X] T029a [P] [US3] Unit test `test_bonferroni_correction` in `tests/test_regression.py`: assert corrected p-values match expected values for a known input list
- [ ] T030a [P] [US3] Unit test `test_null_model_permutation` in `tests/test_regression.py`: assert permutation test with N=1000 returns null distribution with mean ~0

### Implementation for User Story 3

- [ ] T031 [US3] Implement `code/analyze_regression.py` to load `data/raw/networks.csv` and `data/processed/energy_decay.csv` (Depends on T015, T026); filter out rows where status='resonant' before analysis. **Ensure consumption of the validated output of T026.**
- [ ] T032 [US3] Perform Principal Component Analysis (PCA) on topological metrics to handle collinearity. **Extract loadings of topological metrics on PC1 and PC2**. **Generate a markdown table of these loadings and append an "Interpretation of Physical Meaning" section to `data/analysis/regression_results.md`** that explicitly explains what physical network features (e.g., "local clustering" vs "global connectivity") the first two components represent, satisfying Spec FR-009.
- [ ] T033 [US3] Implement **Partial Least Squares (PLS) Regression** (per Plan's Statistical Rigor section; supersedes Spec FR-004's generic PCR mention) to correlate PCA components with decay rates. **Calculate VIP (Variable Importance in Projection) scores**. Apply Bonferroni or Holm-Bonferroni correction to p-values. **Document the rationale for choosing PLS over PCR in the report** (referencing Plan's specific requirement for handling collinearity and maximizing covariance). **Explicitly flag the Spec (FR-004) for update to match the Plan's PLS mandate.** Perform sensitivity analysis on p-value thresholds and VIF checks (VIF > 5) within this single task to ensure a unified analysis pipeline.
- [ ] T034 [US3] Implement sensitivity analysis: sweep significance threshold across standard levels and **report the variance in the number of significant predictors** across the sweep to satisfy SC-004.
- [ ] T035 [US3] Implement VIF check: flag metrics with VIF > 5 and frame results descriptively (integrated into T033)
- [ ] T036a [US3] Implement permutation test (null model validation) logic to ensure observed correlation exceeds a high percentile of null distribution. **Explicitly link output to the Plan's 'null model validation' requirement for PLS.**
- [ ] T036b [US3] Implement null model validation reporting: Generate a report section in `data/analysis/regression_results.md` explicitly stating the null model methodology and results, satisfying the Plan's specific requirement for null model validation.
- [ ] T037 [US3] Generate final regression results report and loadings table in `data/analysis/regression_results.json` and `data/analysis/regression_results.md`; include PLS coefficients, VIP scores, corrected p-values, **loadings for PC1/PC2 with interpretation**, and the count of excluded resonant instances

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
 - Developer B: User Story 2 (Simulation - can use mock data initially)
 - Developer C: User Story 3 (Analysis - can use mock data initially)
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