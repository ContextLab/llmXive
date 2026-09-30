# Tasks: Exploring the Impact of Network Structure on Synchronization in Complex Physical Systems

**Input**: Design documents from `/specs/001-network-synchronization-impact/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are MANDATORY to satisfy the "Independent Test" requirement in the spec.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan (`src/`, `tests/`, `data/`, `results/`) by executing: `mkdir -p src tests data results data/raw data/processed state`.
  *Note: Plan defines `src/` at repository root, not `projects/.../code/`.*
- [X] T002 Initialize Python 3.11 project with pinned dependencies in `requirements.txt` (networkx, scipy, scikit-learn, pandas, matplotlib, datasets)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create `config.yaml` for seeding (random seeds), thresholds (r > 0.8, t > 100), and paths
- [ ] T006 [P] Create `src/data_models.py` defining `NetworkGraph`, `SimulationResult`, and `RegressionModel` entities
- [ ] T005 [US1] Implement `src/loader.py` with strict real-data fetching (SNAP/Network Repository). Logic: 1) Fetch real data. 2) Count files in `data/raw/`. 3) If count < 10, generate `results/descriptive_stats.json` containing `mean`, `median`, `std_dev` for all available metrics, set `state/data_availability.yaml` flag `regression_blocked: true`, and log a warning to `logs/warning.log` with message "Insufficient data (N<10). Regression blocked." per Spec FR-004. **DO NOT** generate synthetic graphs. **DO NOT** halt the pipeline; proceed to simulation but block regression downstream. **Verification**: Assert `state/data_availability.yaml` exists, contains `regression_blocked` flag, `logs/warning.log` exists with the specific message, and `results/descriptive_stats.json` exists with required fields if N < 10.
- [ ] T007 Setup `src/utils.py` for logging, error handling, and result checksumming
- [X] T008a [P] Setup `pytest` framework configuration in `tests/conftest.py`
- [X] T008b [P] Implement `tests/test_properties.py` with specific hypothesis properties (e.g., 'graph connectivity invariance', 'metric bounds')
- [ ] T009 Create `src/validators.py` for data integrity checks (e.g., disconnected graph detection)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Topological Feature Extraction & Synchronization Simulation (Priority: P1) 🎯 MVP

**Goal**: Compute topological metrics and run Kuramoto simulations to determine critical coupling strength.

**Independent Test**: Load a single known small network (e.g., Barabási-Albert), compute metrics, run simulation, verify output JSON contains valid threshold and metrics.

### Tests for User Story 1 (MANDATORY - TDD Order)

- [ ] T010 [P] [US1] Write unit tests for `src/topology.py` metrics calculation in `tests/test_topology.py`. Test cases: `test_degree_distribution_sum_equals_edges`, `test_clustering_coefficient_bounds`, `test_path_length_disconnected_graph`. (TDD approach).
- [ ] T011 [P] [US1] Write unit tests for `src/simulation.py` RK45 integration and threshold detection in `tests/test_simulation.py`. Test cases: `test_ring_graph_analytical_match_5pct`, `test_bisection_search_logic`. (TDD approach).
- [ ] T012 [P] [US1] Contract test for disconnected graph handling (returns infinity/null) in `tests/test_simulation.py`. **Description**: This test verifies the interface contract (return type and value for disconnected graphs) using mocks. It can run before implementation (T015) if mocks are provided.

### Implementation for User Story 1 (Reordered for Execution Flow)

- [ ] T013 [P] [US1] Implement `src/topology.py` to compute degree distribution, clustering coefficient, and average path length (handling disconnected graphs as infinity) using NetworkX. **Verification**: Run `pytest -k test_topology_metrics`.
- [ ] T014 [US1] Implement `src/simulation.py` with Kuramoto model (N=200, RK45) and robustness threshold logic (r > 0.8 for t > 100) using **bisection search** on K in [0, 5] with tolerance 0.001. **Fallback**: If bisection fails to converge, fallback to discrete sweep (step=0.1) as per Spec FR-002. **Verification**: Run `pytest -k test_kuramoto_threshold`.
- [ ] T015 [US1] Implement `src/simulation.py` early-exit logic for disconnected graphs (skip K-sweep, return infinity). **Verification**: Run `pytest -k test_disconnected_graph`.
- [ ] T016 [US1] Create `main.py` orchestration script to process **ALL** networks in `data/raw/`, run topology, run simulation, and save aggregated `results/sim_results.json`. **Verification**: Assert `results/sim_results.json` exists, is valid JSON, and contains keys: `network_id`, `metrics`, `threshold` for all processed networks.
- [X] T017 [P] [US1] Implement validation for analytical solution check (Ring Graph N=200, K=0.5) within `tests/test_simulation.py`. **Verification**: Run `pytest -k test_ring_graph_analytical`.
- [ ] T017b [US1] Implement logic to verify the presence of specific SNAP files: 1) Filter `data/raw/` for files matching SNAP naming pattern (`snap_*.mtx` or files in `data/raw/snap/`), 2) Sort the filtered list alphabetically by filename, 3) Read `results/sim_results.json` generated by T016, 4) Generate `results/verification_report.json` containing the sorted IDs and their threshold values (first 5 only). **Additionally**, generate `results/manual_verification_log.csv` as a CSV template with headers `network_id,threshold,verified_by,timestamp`. Schema for JSON: `{"networks": [{"id": "string", "threshold": "float | null"}]}`. To satisfy SC-003. **Dependency**: Reads output of T016. **Verification**: Assert `results/verification_report.json` exists and matches schema, `results/manual_verification_log.csv` exists with correct headers, and only SNAP files are listed in the report.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Correlation & Regression Analysis (Priority: P2)

**Goal**: Perform regression analysis to quantify the relationship between topology and synchronization threshold.

**Independent Test**: Feed synthetic CSV of a representative number of rows with pre-calculated features, run regression, verify R², p-values, and coefficients output.

### Global Wrapper for Phase 4 (Timeout Detection)

- [ ] T030 [P] [US2] Implement full pipeline timeout detection logic in `main.py` (global wrapper): **Executes in parallel/wraps entire Phase 4**. Tracks total execution time from `main.py` start (T022) to end of regression analysis (T029). If total time > 6 hours (aligned with SC-004), log 'TIMEOUT' to `results/pipeline_status.json` with JSON structure `{network_id: "<last_completed_network_id or 'aggregate'>", duration: <seconds>, status: "TIMEOUT"}`; if successful, log `{network_id: "aggregate", duration: <seconds>, status: "SUCCESS"}` to satisfy SC-004. **Verification**: Assert `results/pipeline_status.json` exists with correct status field and specific network_id or 'aggregate' if timeout occurs.

### Implementation for User Story 2

- [ ] T022 [US2] Extend `main.py` logic to aggregate `results/sim_results.json` into `data/processed_metrics.csv`. **Verification**: Assert `data/processed_metrics.csv` exists and contains valid rows.
- [ ] T025 [US2] Implement `src/stats.py` dataset size checks: Read `state/data_availability.yaml` (set by T005) and `data/processed_metrics.csv`. **Logic**: If `regression_blocked` is true OR N < 10, **SKIP** regression (file `results/descriptive_stats.json` already generated by T005). If N >= 10, proceed to regression. **Verification**: If N < 10, assert `results/descriptive_stats.json` exists (generated by T005) and regression is skipped. If N >= 10, assert `results/descriptive_stats.json` is not generated and regression proceeds.
- [ ] T023a [US2] Implement `src/stats.py` linear and polynomial regression model fitting functions. Define signatures: `fit_linear(X, y)`, `fit_polynomial(X, y, degree)`. **Dependency**: Must run after T025 confirms N >= 10. **Verification**: Run `pytest -k test_regression_output`.
- [ ] T023b [US2] Implement `src/stats.py` statistical calculation functions (R², p-values, ANOVA). **Verification**: Run `pytest -k test_statistical_calcs`.
- [ ] T023c [US2] Implement `src/stats.py` output generation to produce `results/regression_summary.json`. Schema: `{"model_type": "string", "coefficients": {"feature": "float"}, "r_squared": "float", "p_values": {"feature": "float"}}`. **Dependency**: Must run after T024 (VIF check) provides final model type. **Verification**: Validate `results/regression_summary.json` against schema using `pytest -k test_regression_summary_schema`.
- [ ] T024 [US2] Implement `src/stats.py` VIF check logic: if VIF > 5, flag predictor, remove it, or switch to Ridge Regression; document the alpha parameter used in config and logs. **Output**: Pass `final_model_type` (Linear, Poly, or Ridge) to T023c. **Verification**: Run `pytest -k test_vif_logic`.
- [ ] T026 [US2] Implement null hypothesis testing logic (p < 0.05 required for support) in `src/stats.py`. **Verification**: Run `pytest -k test_null_hypothesis`.
- [ ] T027 [US2] Ensure `results/regression_summary.json` is generated with model type, coefficients, R², and p-values. **Verification**: Assert file exists and contains required fields.
- [ ] T028 [US2] Implement `src/stats.py` cross-validation logic: IF dataset size < 50, execute **Leave-One-Out Cross-Validation (LOOCV)**. IF dataset size >= 50, execute **10-fold Cross-Validation** (with fixed seed). Report mean R² and std dev. **Function Signature**: `run_cv(model, X, y) -> dict{mean_r2, std_dev}`. **Verification**: Run `pytest -k test_cross_validation`.
- [ ] T029 [US2] Implement `src/stats.py` instability flagging if CV std dev > 0.1. **Verification**: Run `pytest -k test_instability_flag`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Cross-Validation & Visualization Generation (Priority: P3)

**Goal**: Validate regression model robustness and generate visualizations.

**Independent Test**: Run validation on small fixed dataset, verify plot file (PNG) and JSON report with mean CV R² and std dev.

### Tests for User Story 3 (MANDATORY)

- [ ] T032 [P] [US3] Unit test for `src/stats.py` CV logic (LOOCV for N<50, 10-fold for N>=50). Test cases: `test_loocv_small_dataset`, `test_kfold_large_dataset`.
- [ ] T033 [P] [US3] Unit test for `src/viz.py` heatmap generation and file saving. Test case: `test_heatmap_file_exists`.
- [ ] T033b [P] [US3] Unit test for `src/viz.py` generation of comparative plots (if applicable). Test case: `test_comparative_plot_exists`.

### Implementation for User Story 3

- [ ] T034 [P] [US3] Implement `src/viz.py` to generate heatmaps (X: metric A, Y: metric B, Color: Threshold) saved to `results/heatmap_thresholds.png`. **Function Signature**: `generate_heatmap(df, x_col, y_col, z_col, output_path)`. **Verification**: Assert `results/heatmap_thresholds.png` exists and size > 0.
- [ ] T034b [P] [US3] Implement `src/viz.py` to generate comparative bar charts or scatter plots visualizing the predictive power of the model. **Function Signature**: `generate_comparison_plot(df, output_path)`. **Verification**: Assert `results/comparison_plot.png` exists and size > 0.
- [ ] T035 [US3] Create `main.py` logic to trigger CV and viz generation after regression completion. **Verification**: Run `pytest -k test_viz_trigger`.
- [ ] T036 [US3] Generate `results/cv_report.json` with mean R², std dev, and stability flag. **Verification**: Assert `results/cv_report.json` exists with fields `mean_r2`, `std_dev`, `stability_flag`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Secondary Analysis - Higher-Order Topology (Hypothesis Testing) (Priority: P2 Revision)

**Goal**: Address reviewer concern regarding higher-order structures (motifs) and the sufficiency of pairwise metrics. **Note**: This is a secondary hypothesis test, NOT part of the primary regression model defined in FR-001.

**Independent Test**: Run motif extraction on a known network, verify motif counts match expected values, and confirm regression model performance does not significantly degrade when motifs are excluded (or improve if included as a secondary analysis).

### Implementation for Higher-Order Analysis

- [ ] T045 [Phase6] [Phase6] Implement `src/topology.py` extension to compute **Motif Participation Profiles** for 3-node and 4-node subgraphs using `networkx.algorithms.isomorphism`. **Constraint**: Limit to small-scale motifs to maintain CPU feasibility on free tier.. **Verification**: Assert motif counts for a standard graph (e.g., `erdos_renyi`) match theoretical expectations within tolerance.
- [ ] T046 [Phase6] [Phase6] Implement `src/stats.py` extension to include motif counts as **secondary predictors** in a separate regression model. **Logic**: Load baseline from `results/regression_summary.json`, run motif-enhanced regression, compare R² and AIC/BIC to determine if higher-order structure adds predictive power. **Output**: Generate `results/motif_data.json` containing both models' statistics and a boolean `motif_significance` flag. **Verification**: Assert `results/motif_data.json` exists with required fields.
- [ ] T047 [Phase6] [Phase6] Implement sensitivity analysis in `src/stats.py` to test if the inclusion of motif data changes the significance (p-value) of the primary topological predictors (Degree, Clustering, Path Length). **Output**: Generate `results/sensitivity_report.txt` with comparison of p-values. **Verification**: Assert `results/sensitivity_report.txt` exists.
- [ ] T048 [Phase6] [Phase6] Generate `results/motif_analysis_report.json` summarizing the comparison between baseline and motif-enhanced models. **Verification**: Assert `results/motif_analysis_report.json` exists.

**Checkpoint**: Higher-order structures evaluated; decision made on whether to include in final model.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T038 [P] Documentation updates in `docs/` including `quickstart.md` and `data-model.md`. **Content**: Add API docs for `src/topology.py`, `src/simulation.py`, `src/stats.py`. **Verification**: Assert `docs/` exists and contains `quickstart.md`, `data-model.md`, `api_topology.md`, `api_simulation.md`, `api_stats.md` (all non-empty).
- [ ] T039 Code cleanup and refactoring (remove unused imports, ensure type hinting). **Files**: `src/*.py`, `tests/*.py`. **Verification**: Run `ruff check` and `black --check`.
- [ ] T040 Performance optimization for large network loading (streaming if necessary). **Technique**: Use `datasets.load_dataset(..., streaming=True)` for large files. **Files**: `src/loader.py`. **Verification**: Run `pytest -k test_streaming_load`.
- [ ] T041 [P] Additional unit tests for edge cases (e.g., N=2 graphs, self-loops) in `tests/unit/`. **Test Cases**: `test_n2_graph`, `test_self_loops`. **Verification**: Run `pytest -k test_edge_cases`.
- [ ] T042 Run `quickstart.md` validation to ensure end-to-end pipeline works. **Steps**: Execute `python main.py --config config.yaml`. **Verification**: Assert all expected output files exist.
- [ ] T043 [P] Update `research.md` with findings on topological metrics vs. synchronization thresholds, citing specific results. **Content**: Insert R² values, p-values, and conclusions from `results/regression_summary.json`, specifically addressing the contribution of standard topological metrics. **Verification**: Assert `research.md` contains a statement regarding the R-squared metric. from `results/regression_summary.json`.
- [ ] T044 [P] Update `research.md` with findings from the higher-order motif analysis (T046), explicitly stating whether motifs provided additional predictive power over standard pairwise metrics. **Verification**: Assert `research.md` contains string "Higher-Order Topology" AND (contains "motifs did not provide additional predictive power" OR contains "motifs provided additional predictive power").

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Higher-Order Analysis (Phase 6)**: Depends on US1 and US2 completion (requires baseline regression results)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Consumes US1 output (T016/T017b)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Consumes US2 output
- **Higher-Order Analysis (Phase 6)**: Depends on US2 baseline regression results

### Within Each User Story

- Tests (mandatory) MUST be written and FAIL before implementation (TDD methodology)
- Implementation tasks are listed first in this document to break circular dependency for sequential runners, but logical flow is Source -> Test -> Integration
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
# Launch all tests for User Story 1 together:
Task: "Write unit tests for src/topology.py metrics calculation in tests/test_topology.py"
Task: "Write unit tests for src/simulation.py RK45 integration in tests/test_simulation.py"
Task: "Contract test for disconnected graph handling in tests/test_simulation.py"

# Launch all models for User Story 1 together:
Task: "Implement src/topology.py to compute degree distribution..."
Task: "Implement src/simulation.py with Kuramoto model..."
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (including mandatory tests)
4. **STOP and VALIDATE**: Test User Story 1 independently (Ring Graph check, verification report)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (incorporating LOOCV/10-fold CV, VIF checks)
4. Add User Story 3 → Test independently → Deploy/Demo (comparative plots)
5. Add Phase 6 (Higher-Order) → Test independently → Deploy/Demo (motif analysis)
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Simulation Core + Tests)
 - Developer B: User Story 2 (Regression Core + CV)
 - Developer C: User Story 3 (CV & Viz)
3. Stories complete and integrate independently
4. Phase 6 (Higher-Order) can be tackled by a specialist after baseline is established.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Data Integrity**: All data loaders MUST attempt real fetch first; if N < 10, generate descriptive stats and set state flag to block regression (per Spec Assumptions & FR-004). NO synthetic data.
- **Timeout Handling**: SC-004 compliance is ensured by T030 (global wrapper) in Phase 4. Threshold set to 6 hours. Specific network_id or 'aggregate' logged on timeout.
- **Statistical Rigor**: FR-006 compliance ensured by T024 (documenting alpha parameter) and T028 (LOOCV/10-fold CV per Spec FR-005).
- **Validation**: SC-003 compliance ensured by T017b (SNAP list filtering, verification report, and manual verification log generation).
- **Constitution Alignment**: All tasks align with Plan.md and Constitution Principle VII (LOOCV/10-fold CV per Spec FR-005).
- **Dependency Flow**: T005 checks raw count and sets state. T022 aggregates. T025 checks state/N and blocks or proceeds. T030 wraps the phase.
- **Plan/Spec Conflict (CV Method)**: Task T028 explicitly follows Spec FR-005 (LOOCV for N<50, 10-fold for N>=50). The Plan's Constitution Check already reflects this.
- **Reviewer Concern Addressed (Dan Rockmore)**: Tasks T045, T046, T047, and T048 explicitly address the concern regarding higher-order structures (motifs). They implement a rigorous test to see if motifs add predictive power beyond pairwise metrics, without violating the "standard toolkit" constraint of the primary analysis.
- **No Motif Analysis (Original)**: Tasks T018, T031, T037 (Motif Participation Profiles) have been REMOVED from the primary US1/US2 flow to strictly comply with Spec FR-001 and Plan Constraints limiting *primary* predictors to degree distribution, clustering coefficient, and average path length. Motifs are now treated as a secondary, hypothesis-driven investigation in Phase 6 to answer the specific reviewer query.