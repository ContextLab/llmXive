# Tasks: Exploring the Convergence of Iterated Function Systems with Non-Contractive Maps

**Input**: Design documents from `/specs/001-gene-regulation/`
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

- [ ] T001 Create project structure: `mkdir -p projects/PROJ-550-exploring-the-convergence-of-iterated-fu/{code,data/raw,data/derived,tests/unit,tests/contract,docs}`
- [ ] T002 Initialize Python project: Create `requirements.txt` with pinned versions (`numpy==1.26.4`, `scipy==1.12.0`, `scikit-learn==1.4.0`, `pandas==2.1.4`, `pytest==7.4.3`, `matplotlib==3.8.2`, `pyarrow==14.0.1`) and run `pip install -r requirements.txt` then `pip freeze > requirements.txt`
- [ ] T003 [P] Configure linting (flake8/ruff) and formatting (black) tools: Add `.ruff.toml` and `.pre-commit-config.yaml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Implement `code/config.py` with exact keys: `SEED=42`, `GRID_SIZE_CONTRACTIVE=1000`, `GRID_SIZE_NON_CONTRACTIVE=5000` (for non-contractive validation), `BOX_COUNTING_SCALES=50`, `ITERATIONS_DEFAULT=1000000`, `ITERATIONS_EDGE_CASE=5000000`, `BOUNDING_BOX_MIN=-1.0`, `BOUNDING_BOX_MAX=2.0`, `W2_THRESHOLD=0.01`, `FILE_PATHS` (dict mapping raw/derived paths).
- [ ] T005 [P] Create `code/generators.py` skeleton: Define `IFSInstance` dataclass with fields `id`, `maps`, `lipschitz_target`, `grid_size` (type stubs only, no logic).
- [ ] T006 [P] Create `code/chaos_game.py` skeleton: Define `run_chaos_game(ifs_instance, iterations, seed)` function signature (type stubs only).
- [ ] T007 [P] Create `code/topology.py` skeleton: Define `compute_box_counting_dimension(points, scales)` function signature (type stubs only).
- [ ] T008 [P] Create `code/analysis.py` skeleton: Define `fit_logistic_regression(features, labels)` and `sensitivity_analysis(results)` function signatures (type stubs only).
- [ ] T009 [P] Create `code/benchmarks.py` skeleton: Define `load_benchmarks()` function signature returning list of `IFSInstance` (type stubs only).
- [ ] T010 Setup `data/raw/`, `data/derived/`, and `tests/unit/` directories (ensure write permissions).
- [ ] T011 Implement `code/checksums.py` utility: Function `generate_checksums(data_dir)` to write `data/checksums.json` with SHA256 hashes for all files in `data/`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Synthetic IFS Generation and Lipschitz Validation (Priority: P1) 🎯 MVP

**Goal**: Generate diverse synthetic IFS with controlled Lipschitz constants (0.5 to 2.0 in 0.1 increments) and validate numerical properties.

**Independent Test**: Generate 50 instances, compute Lipschitz on 1000-point grid, verify computed values are within ±0.05 of targets. [UNRESOLVED-CLAIM: c_11a4e600 — status=not_enough_info]

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T012 [P] [US1] Unit test `test_lipschitz_accuracy` in `tests/unit/test_generators.py`: Generate 50 instances with seed 42, compute Lipschitz on 1000-point grid, verify MAE ≤ 0.05 against targets. [UNRESOLVED-CLAIM: c_f9ba40b6 — status=not_enough_info]
- [ ] T013 [P] [US1] Unit test `test_benchmark_reconstruction` in `tests/unit/test_benchmarks.py`: Load benchmarks, verify Sierpinski/Barnsley parameters match literature values.

### Implementation for User Story 1

- [ ] T014 [US1] Implement synthetic IFS generator in `code/generators.py`: Create 2-4 affine maps with **Lipschitz targets in fine increments from 0.5 to 2.0** (discrete set, not continuous random).
- [ ] T015 [US1] Implement numerical Lipschitz estimator in `code/generators.py`: Gradient estimation on a fine-point grid for contractive, a denser grid for non-contractive. (as per config).
- [ ] T016 [US1] Implement validation logic in `code/generators.py`: Flag outliers (>±0.05 error) and trigger re-generation.
- [ ] T017 [US1] Implement benchmark loader in `code/benchmarks.py`: Hardcode Sierpinski Triangle, Barnsley Fern, and da Cunha expanding map parameters per **da Cunha et al. (2021)** (Affine matrix: `[[scale_factor, 0.0], [0.0, scale_factor]]`, Translation: `[0.0, 0.0]`, Probability: `1.0`).
- [ ] T017B [US1] **Execute** benchmark validation: Run `code/benchmarks.py` to verify benchmarks, compute initial metrics, and write `data/derived/benchmark_results.parquet` (Depends on T017).
- [ ] T018 [US1] Create script `code/run_generation.py`: CLI `--count [specified_quantity] --seed 42`, generates `data/raw/ifs_instances.parquet` with schema: `id`, `lipschitz_target`, `maps`, `grid_size`.
- [ ] T019 [US1] Add edge case handling in `code/generators.py`: Exclude non-affine maps if gradient estimation fails and log to `data/raw/excluded_instances.log`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Invariant Measure Approximation via Monte Carlo (Priority: P2)

**Goal**: Approximate empirical invariant measures using Chaos Game and classify convergence vs. divergence.

**Independent Test**: Run Chaos Game on Sierpinski (contractive) and verify box-counting dimension matches theory; verify non-contractive classification logic.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T020 [P] [US2] Unit test `test_chaos_convergence` in `tests/unit/test_chaos_game.py`: Verify Wasserstein-2 check works on known contractive case.
- [ ] T021 [P] [US2] Unit test `test_divergence_detection` in `tests/unit/test_chaos_game.py`: Verify points escaping `[-1, 2]²` are flagged immediately.

### Implementation for User Story 2

- [ ] T022 [US2] Implement Chaos Game loop in `code/chaos_game.py`: Vectorized NumPy operations for efficiency.
- [ ] T023 [US2] Implement divergence detector in `code/chaos_game.py`: Stop simulation if points leave `[-1, 2]²` bounding box.
- [ ] T024 [US2] Implement convergence classifier in `code/chaos_game.py`: Classify as "Converged" (W2 < 0.01 AND bounded) or "Divergent" (escape OR W2 >= 0.01). **Note: No "Chaotic Boundedness" state; bounded non-convergent cases are "Divergent" or "Uniform Filling" (distinct from escape).**
- [ ] T025 [US2] Implement histogram generator in `code/chaos_game.py`: Use Sturges' rule for binning.
- [ ] T026 [US2] Create script `code/run_simulation.py`: Process `data/raw/ifs_instances.parquet`, output `data/derived/chaos_results.parquet` with schema: `id`, `lipschitz`, `w2_distance`, `convergence_status`, `histogram_bins`, `escape_flag`.
- [ ] T027 [US2] Add edge case handling for Lipschitz = 1.0: Run extended iterations before classifying.
- [ ] T028 [US2] Implement logic to distinguish "Uniform Filling" (bounded, high entropy, W2 fails) from "Divergence" (escape) based on density checks, but map both to "Divergent" status for downstream binary analysis unless explicitly logged as "Uniform Filling" for research notes.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Topological Analysis and Threshold Sensitivity (Priority: P3)

**Goal**: Compute topological descriptors and perform sensitivity analysis on Lipschitz thresholds.

**Independent Test**: Analyze instances crossing L=1.0 boundary and verify dimension shift > 0.05 or regression slope change p < 0.05.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T029 [P] [US3] Unit test `test_box_counting_accuracy` in `tests/unit/test_topology.py`: Verify dimension estimates on Sierpinski (target theoretical fractal dimension).
- [ ] T030 [P] [US3] Unit test `test_logistic_regression` in `tests/unit/test_analysis.py`: Verify AUC > random chance on synthetic labels.

### Implementation for User Story 3

- [ ] T031 [US3] Implement box-counting dimension calculator in `code/topology.py`: Multi-scale grid analysis using **exactly 50 scale levels** as mandated by Constitution Principle VI.
- [ ] T031B [US3] **Validate SC-002**: Load `data/derived/benchmark_results.parquet` (Depends on T017B), compute box-counting dimensions for benchmarks, compare against theoretical values, record MAE in `data/derived/benchmark_validation.csv`. **Fail build if MAE > 0.1 **.
- [ ] T032 [US3] Implement map overlap geometry calculator in `code/topology.py`: Intersection area ratio of map images to unit square.
- [ ] T033 [US3] Implement logistic regression model in `code/analysis.py`: Predict "convergence stability" from **Lipschitz parameters AND map overlap geometry (output of T032)**.
- [ ] T034 [US3] Implement sensitivity analysis in `code/analysis.py`: Sweep thresholds over the **discrete set of representative values**, compute stability rate std dev.
- [ ] T035 [US3] Implement permutation test in `code/analysis.py`: Validate logistic regression AUC significance (p < 0.05).
- [ ] T036 [US3] Create script `code/run_analysis.py`: Generate `data/derived/topology_results.parquet` and `data/derived/analysis_summary.csv` with schema: `lipschitz`, `overlap_geometry`, `predicted_stability`, `actual_stability`, `auc`, `p_value`. (Depends on T032, T033, T034, T035).
- [ ] T037 [US3] **Ensure Benchmark Validation Precedes**: Verify `data/derived/benchmark_results.parquet` exists and passes validation before running synthetic analysis (gate in `run_analysis.py`).

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Reviewer Concerns - Distinction & Visualization (Priority: P2/P3)

**Goal**: Address Dan Rockmore's concern on distinguishing divergence vs. chaotic boundedness and Stephen Wolfram's call for empirical visualization.

**Independent Test**: Visual comparison of orbit behavior for contractive vs. non-contractive seeds; clear classification of "Chaotic Boundedness" vs "Divergence".

### Implementation for Reviewer Concerns

- [ ] T038 [US2] **REMOVED**: Task T038 (Chaotic Boundedness classification) has been removed to strictly adhere to FR-004 binary classification. Bounded non-convergent cases are handled in T024/T028 as "Divergent" or "Uniform Filling" (logged) without creating a new state label.
- [ ] T039 [P] [US3] Implement `code/visualizer.py`: Generate side-by-side orbit plots for contractive vs. non-contractive IFS with same seed.
- [ ] T040 [P] [US3] Implement `code/visualizer.py`: Generate density heatmaps distinguishing "Uniform Filling" from "Fractal Attractor".
- [ ] T041 [US3] Add "Transient Dimension" calculation in `code/topology.py`: Quantify rate of escape or mixing for non-contractive cases.
- [ ] T042 [US3] Create script `code/run_visualization.py`: Generate `data/derived/visualizations/` (PDF/PNG) for key threshold cases (L=0.8, 1.0, 1.2).
- [ ] T043 [US3] **Address Rockmore**: Implement `code/complex_dynamics_bridge.py`: Compute and compare Mandelbrot-like boundary metrics for selected IFS maps to visualize the "boundary between interior and exterior" analogous to complex dynamics. **Depends on T026**.
- [ ] T044a [US3] **Address Wolfram (Metric)**: Define "complexity metric" for orbit traces (e.g., entropy, Lyapunov exponent approximation) in `code/ruliad_explorer.py`.
- [ ] T044b [US3] **Address Wolfram (Sweep)**: Run a large-scale parameter sweep of non-contractive maps using the metric from Ta. [UNRESOLVED-CLAIM: c_7e780a0a — status=not_enough_info]
- [ ] T044c [US3] **Address Wolfram (Selection)**: Select top 100 most "complex" cases (high entropy, bounded) and save raw orbit traces to `data/derived/ruliad_samples/`.
- [ ] T044d [US3] **Address Wolfram (Taxonomy)**: Generate a "behavioral taxonomy" plot based on visual inspection of the traces from T044c. **Scope Justification**: These tasks address explicit reviewer feedback (Wolfram) regarding empirical visualization and are not silent scope expansion.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T045 [P] Documentation updates in `docs/` and `README.md`.
- [ ] T046 Code cleanup and refactoring for vectorization efficiency.
- [ ] T047a [US3] **Refactor**: Refactor `code/chaos_game.py` to use vectorized NumPy operations.
- [ ] T047b [US3] **Benchmark**: Run `code/run_simulation.py` on 500 instances locally on 2-core runner; verify runtime < 5.5 hours.
- [ ] T048 [P] Additional unit tests for edge cases (L=1.0, non-affine maps) in `tests/unit/`.
- [ ] T049 Run `quickstart.md` validation to ensure full pipeline reproducibility.
- [ ] T050 Generate final `data/checksums.json` covering all derived artifacts.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data generation (T018)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 data and US2 results
- **Reviewer Concerns (Phase 6)**: Depends on US2 completion (requires simulation results)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2) - **Note**: T005 defines dataclass; T006-T009 import it but use type stubs only, allowing parallel writing of stubs.
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test test_lipschitz_accuracy in tests/unit/test_generators.py"
Task: "Unit test test_benchmark_reconstruction in tests/unit/test_benchmarks.py"

# Launch all models for User Story 1 together:
Task: "Implement synthetic IFS generator in code/generators.py"
Task: "Implement numerical Lipschitz estimator in code/generators.py"
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
- **CPU Constraint**: All tasks must run on a limited number of CPU cores, with modest RAM and no GPU. Use vectorized NumPy and batch processing.
- **Data Integrity**: Never fabricate data. All results must come from real simulation of generated or benchmark IFS instances.
- **Classification Contract**: Strictly binary ("Converged"/"Divergent") per FR-004. "Uniform Filling" is a research note, not a model state.
- **Reviewer Alignment**: Tasks T038-T044d specifically address the "divergence vs. chaotic boundedness" distinction (Rockmore) and the "empirical visualization/ruliad" exploration (Wolfram) requested in prior reviews.