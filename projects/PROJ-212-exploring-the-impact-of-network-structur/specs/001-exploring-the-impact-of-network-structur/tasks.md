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
- [X] T002 Initialize Python project with pinned dependencies in `requirements.txt` (networkx, scipy, scikit-learn, pandas, matplotlib, datasets)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools with explicit `pyproject.toml` settings for the project's coding standards (e.g., `max-line-length=88`, `target-version=py311`). **Verification**: Assert `pyproject.toml` contains non-default configuration sections for `tool.ruff` and `tool.black`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create `config.yaml` for seeding (random seeds), thresholds (r > 0.8, t > 100), and paths
- [ ] T006 [P] Create `src/data_models.py` defining `NetworkGraph`, `SimulationResult`, and `RegressionModel` entities
- [ ] T005a [P] [US1] Implement `src/loader.py` data fetching logic: Fetch real data from SNAP (a subset of valid `.mtx` files from the 'web' category) and Network Repository (a subset of valid `.mtx` files). **Verification**: Assert files exist in `data/raw/` and count is recorded in `logs/fetch_count.log`.
- [ ] T005c [P] [US1] Implement checksumming logic in `src/loader.py`: Calculate SHA256 hashes for all files downloaded in T005a and write them to `data/checksums.txt` in the format `hash  filename`. **Verification**: Assert `data/checksums.txt` exists and contains valid hashes for all files in `data/raw/`.
- [ ] T005b [P] [US1] [FR-004] Implement logic to check `data/raw/` count. IF count < 10: Generate `results/descriptive_stats.json` (schema: `{"mean": float, "median": float, "std_dev": float, "count": int, "warning_message": "Insufficient data for regression"}`), set `state/data_availability.yaml` flag `regression_blocked: true`, and log warning to `logs/warning.log`. IF count >= 10: Do nothing. **Verification**: Assert correct artifacts exist based on count.
 *Note: T005b is a single atomic task. If N < 10, simulation proceeds to generate descriptive stats, but regression is blocked downstream. NO synthetic data is generated.*
- [ ] T007 Setup `src/utils.py` for logging, error handling, and result checksumming
- [X] T008a [P] Setup `pytest` framework configuration in `tests/conftest.py`
- [X] T008b [P] Implement `tests/test_properties.py` with specific hypothesis properties (e.g., 'graph connectivity invariance', 'metric bounds')
- [X] T009 Create `src/validators.py` for data integrity checks (e.g., disconnected graph detection)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Topological Feature Extraction & Synchronization Simulation (Priority: P1) 🎯 MVP

**Goal**: Compute topological metrics and run Kuramoto simulations to determine critical coupling strength.

**Independent Test**: Load a single known small network (e.g., Barabási-Albert), compute metrics, run simulation, verify output JSON contains valid threshold and metrics.

### Tests for User Story 1 (MANDATORY - TDD Order)

- [ ] T010 [P] [US1] Write unit tests for `src/topology.py` metrics calculation in `tests/test_topology.py`. Test cases: `test_degree_distribution_sum_equals_edges`, `test_clustering_coefficient_bounds`, `test_path_length_disconnected_graph`. (TDD approach).
- [ ] T011 [P] [US1] Write unit tests for `src/simulation.py` RK45 integration and threshold detection in `tests/test_simulation.py`. Test cases: `test_ring_graph_analytical_match_pct`, `test_bisection_search_logic`. (TDD approach).
- [X] T012 [P] [US1] Write contract tests for disconnected graph handling (returns infinity/null) in `tests/test_simulation.py`. **Description**: This test verifies the interface contract (return type and value for disconnected graphs) using mocks. It can run before implementation (T015) if mocks are provided.

### Implementation for User Story 1 (Reordered for Execution Flow)

- [ ] T013 [P] [US1] Implement `src/topology.py` to compute degree distribution, clustering coefficient, and average path length (handling disconnected graphs as infinity) using NetworkX. **Verification**: Run `pytest -k test_topology_metrics`.
- [ ] T014 [US1] Implement `src/simulation.py` with Kuramoto model (N=200, RK45) and robustness threshold logic (r > 0.8 for t > 100). **Primary Method**: Bisection search on K within a bounded interval with tolerance 0.001 and max 50 iterations. **Fallback**: If bisection fails to converge within 50 iterations, fallback to discrete sweep (step=0.1) as per Spec FR-002. **Verification**: Run `pytest -k test_kuramoto_threshold`.
- [ ] T015 [US1] Implement pre-check guard clause in `src/simulation.py` for disconnected graphs (skip K-sweep, return infinity). **Dependency**: T014 core logic must exist; T015 wraps T014's entry point to prevent execution on invalid inputs. **Verification**: Run `pytest -k test_disconnected_graph`.
- [ ] T016 [US1] Create `main.py` orchestration script to process **ALL** networks in `data/raw/`, run topology, run simulation, and save aggregated `results/sim_results.json`. **Verification**: Assert `results/sim_results.json` exists, is valid JSON, and contains keys: `network_id`, `metrics`, `threshold` for all processed networks.
- [X] T017 [P] [US1] Implement validation for analytical solution check (Ring Graph N=200, K=0.5) within `tests/test_simulation.py`. **Verification**: Run `pytest -k test_ring_graph_analytical`.
- [ ] T017b [US1] Implement logic to verify the presence of valid network files and generate verification reports: 1) Filter `data/raw/` for any valid `.mtx` or `.csv` files (ignoring filename patterns), 2) Sort the filtered list alphabetically by filename, 3) Read `results/sim_results.json` generated by T016. **IF** `sim_results.json` is empty or missing, generate `results/verification_report.json` with `status: "skipped"` and `reason: "No simulation data"`. **ELSE** 4) Extract the first 5 networks from the sorted list, 5) Generate `results/verification_report.json` containing the sorted IDs and their threshold values. 6) Generate `results/manual_verification_log.csv` by populating rows with the actual results from the extracted 5 networks. **Constraint**: MUST execute against REAL data from T016. NO simulation or synthetic population of rows is permitted. **Purpose**: This log provides the data for human manual verification of SC-003. Schema for JSON: `{"networks": [{"id": "string", "threshold": "float | null"}], "status": "string"}`. CSV headers: `network_id,threshold,verified_by,timestamp`. **Dependency**: Reads output of T016. **Verification**: Assert `results/verification_report.json` exists and matches schema, `results/manual_verification_log.csv` exists with correct headers AND populated rows (if data exists), and only valid network files are listed in the report.
- [ ] T017c [US1] [SC-003] Generate a "Manual Review Gate" report: Create `results/manual_verification_pending.md` containing the instructions for a human reviewer to inspect `results/manual_verification_log.csv` and confirm that the reported thresholds match the order parameter condition (r > 0.8 sustained for t > 100). **Output**: Update `results/verification_report.json` with a `review_pending: true` flag. **Verification**: Assert `results/manual_verification_pending.md` exists and `results/verification_report.json` contains `review_pending: true`.
- [ ] T018 [US1] [FR-001] Implement strict verification of standard topological metrics: Ensure `src/topology.py` computes ONLY degree distribution, clustering coefficient, and average path length as per FR-001. **Verification**: Run `pytest -k test_standard_metrics_only` to assert no other metrics (e.g., motifs) are computed or included in the output.
- [ ] T019 [US1] [Review-Response] Implement exploratory higher-order structure analysis: Extend `src/topology.py` to optionally compute network motifs (triangles, 4-node cliques) and community modularity (using Louvain algorithm) for comparison. **Constraint**: These metrics MUST be excluded from the primary regression analysis (FR-001) and stored in a separate `results/secondary_metrics.json`. **Purpose**: To address the reviewer's concern about whether pairwise metrics capture the full story, allowing for a post-hoc correlation check between these higher-order features and synchronization without violating the primary scope. **Verification**: Run `pytest -k test_secondary_metrics_generation` and assert `results/secondary_metrics.json` contains motif counts and modularity scores.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Correlation & Regression Analysis (Priority: P2)

**Goal**: Perform regression analysis to quantify the relationship between topology and synchronization threshold.

**Independent Test**: Feed synthetic CSV of a representative number of rows with pre-calculated features, run regression, verify R², p-values, and coefficients output.

### Implementation for User Story 2

- [ ] T022 [US2] Extend `main.py` logic to aggregate `results/sim_results.json` into `data/processed_metrics.csv`. **Verification**: Assert `data/processed_metrics.csv` exists and contains valid rows.
- [ ] T025 [US2] Implement `src/stats.py` dataset size checks: Read `state/data_availability.yaml` (schema: `{"regression_blocked": boolean}`) and `data/processed_metrics.csv`. **Logic**: If `regression_blocked` is true OR N < 10, **SKIP** regression (file `results/descriptive_stats.json` already generated by T005). If N >= 10, proceed to regression. **Dependency**: Must run after T022. **Verification**: If N < 10, assert `results/descriptive_stats.json` exists (generated by T005) and regression is skipped. If N >= 10, assert `results/descriptive_stats.json` is not generated and regression proceeds.
- [ ] T023a [US2] Implement `src/stats.py` linear and polynomial regression model fitting functions. Define signatures: `fit_linear(X, y)`, `fit_polynomial(X, y, degree)`. **Dependency**: Must run after T025 confirms N >= 10. **Verification**: Run `pytest -k test_regression_output`.
- [ ] T023b [US2] Implement `src/stats.py` statistical calculation functions (R², p-values, ANOVA). **Verification**: Run `pytest -k test_statistical_calcs`.
- [ ] T024 [US2] Implement `src/stats.py` VIF check logic: if VIF > 5, perform (A) Remove predictor and re-run regression, OR (B) Switch to Ridge Regression with documented alpha parameter. **Output**: Pass `final_model_type` (Linear, Poly, or Ridge) and `remediation_action` (string describing removal or switch) to T023c. **Verification**: Run `pytest -k test_vif_logic`. Assert `results/regression_summary.json` (generated by T023c) contains the `remediation_action` field if VIF > 5 was detected.
- [ ] T023c [US2] Implement `src/stats.py` output generation to produce `results/regression_summary.json`. Schema: `{"model_type": "string", "coefficients": {"feature": "float"}, "r_squared": "float", "p_values": {"feature": "float"}, "remediation_action": "string | null"}`. **Dependency**: Must run after T024 (VIF check) provides final model type and remediation action. **Verification**: Validate `results/regression_summary.json` against schema using `pytest -k test_regression_summary_schema`.
- [ ] T026 [US2] Implement null hypothesis testing logic (p < 0.05 required for support) in `src/stats.py`. **Verification**: Run `pytest -k test_null_hypothesis`.
- [ ] T027 [US2] Ensure `results/regression_summary.json` is generated with model type, coefficients, R², and p-values. **Verification**: Assert file exists and contains required fields.
- [ ] T028 [US2] Implement `src/stats.py` cross-validation logic: IF dataset size < 50, execute **Leave-One-Out Cross-Validation (LOOCV)**. IF dataset size >= 50, execute **10-fold Cross-Validation** (with fixed seed). Report mean R² and std dev. **Function Signature**: `run_cv(model, X, y) -> dict{mean_r2, std_dev}`. **Verification**: Run `pytest -k test_cross_validation`.
- [ ] T029 [US2] Implement `src/stats.py` instability flagging and robustness verification: Check if CV std dev > 0.1 using results from T028. **Verification**: Run `pytest -k test_instability_flag`. **Output**: Generate `results/cv_report.json` containing `mean_r2`, `std_dev`, `stability_flag` (true if std > 0.1), and `robustness_pass` (true if std < 0.1, satisfying SC-002). **Verification**: Assert `results/cv_report.json` exists with fields `mean_r2`, `std_dev`, `stability_flag`, and `robustness_pass`.
- [ ] T029b [US2] [Review-Response] Implement secondary correlation analysis: Run a parallel regression model using the higher-order metrics (motifs, modularity) from T019 as predictors. Compare the R² and p-values against the primary model. **Output**: Append a `secondary_analysis` block to `results/regression_summary.json` containing the model type, R², and p-values for the higher-order features. **Purpose**: To directly address the reviewer's hypothesis about higher-order structures by quantifying their predictive power relative to standard metrics. **Verification**: Assert `results/regression_summary.json` contains the `secondary_analysis` block and that the secondary model was computed without modifying the primary model's results.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Cross-Validation & Visualization Generation (Priority: P3)

**Goal**: Validate regression model robustness and generate visualizations.

**Independent Test**: Run validation on small fixed dataset, verify plot file (PNG) and JSON report with mean CV R² and std dev.

### Tests for User Story 3 (MANDATORY)

- [ ] T032 [P] [US3] Unit test for `src/stats.py` CV logic (LOOCV for N<50, 10-fold for N>=50). Test cases: `test_loocv_small_dataset`, `test_kfold_large_dataset`.
- [ ] T033 [P] [US3] Unit test for `src/viz.py` heatmap generation and file saving. Test case: `test_heatmap_file_exists`.

### Implementation for User Story 3

- [ ] T034 [P] [US3] Implement `src/viz.py` to generate heatmaps (X: metric A, Y: metric B, Color: Threshold) saved to `results/heatmap_thresholds.png`. **Function Signature**: `generate_heatmap(df, x_col, y_col, z_col, output_path)`. **Verification**: Assert `results/heatmap_thresholds.png` exists and size > 0.
- [ ] T034b [P] [US3] Implement `src/viz.py` to generate comparative bar charts or scatter plots visualizing the predictive power of the model. **Function Signature**: `generate_comparison_plot(df, output_path)`. **Verification**: Assert `results/comparison_plot.png` exists and size > 0.
- [ ] T034c [P] [US3] [Review-Response] Implement visualization for higher-order vs. standard metrics: Generate a side-by-side scatter plot comparing the correlation strength (R²) of the primary model vs. the secondary model (from T029b). **Output**: Save to `results/model_comparison_plot.png`. **Verification**: Assert `results/model_comparison_plot.png` exists and clearly labels the two model types.
- [ ] T035 [US3] Create `main.py` logic to trigger CV and viz generation after regression completion. **Verification**: Run `pytest -k test_viz_trigger`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T030 [US1] [SC-004] Implement global timeout wrapper in `main.py`: Wrap the entire execution flow of the pipeline (starting from data fetch T005 through regression T029) with a timer. If total time > 6 hours, log 'TIMEOUT' to `results/pipeline_status.json` with JSON structure `{network_id: "<last_completed_network_id or 'aggregate'>", duration: <seconds>, status: "TIMEOUT"}`; if successful, log `{network_id: "aggregate", duration: <seconds>, status: "SUCCESS"}`. **Verification**: Assert `results/pipeline_status.json` exists with correct status field and specific network_id or 'aggregate' if timeout occurs. **Dependency**: Must be implemented in `main.py` after T016 (Orchestration) is defined.
- [ ] T038 [P] Documentation updates in `docs/` including `quickstart.md` and `data-model.md`. **Content**: Add API docs for `src/topology.py`, `src/simulation.py`, `src/stats.py`. **Verification**: Assert `docs/` exists and contains `quickstart.md`, `data-model.md`, `api_topology.md`, `api_simulation.md`, `api_stats.md` (all non-empty).
- [ ] T039 Code cleanup and refactoring (remove unused imports, ensure type hinting). **Files**: `src/*.py`, `tests/*.py`. **Verification**: Run `ruff check` and `black --check`.
- [ ] T040 Performance optimization for large network loading (streaming if necessary). **Technique**: Use `datasets.load_dataset(..., streaming=True)` for large files. **Files**: `src/loader.py`. **Verification**: Run `pytest -k test_streaming_load`.
- [ ] T041 [P] Additional unit tests for edge cases (e.g., N=2 graphs, self-loops) in `tests/unit/`. **Test Cases**: `test_n2_graph`, `test_self_loops`. **Verification**: Run `pytest -k test_edge_cases`.
- [ ] T042 Run `quickstart.md` validation to ensure end-to-end pipeline works. **Steps**: Execute `python main.py --config config.yaml`. **Verification**: Assert all expected output files exist.
- [ ] T043 [P] Update `specs/001-network-synchronization-impact/research.md` with findings on topological metrics vs. synchronization thresholds, citing specific results. **Content**: Insert R² values, p-values, and conclusions from `results/regression_summary.json`, specifically addressing the contribution of standard topological metrics. **Verification**: Assert `research.md` contains a statement regarding the R-squared metric from `results/regression_summary.json`.
- [ ] T043b [P] [Review-Response] Update `research.md` with comparative findings: Include a dedicated section discussing the results of the secondary analysis (higher-order metrics) compared to the primary analysis. **Content**: Discuss whether higher-order structures provided a statistically significant improvement in predictive power (R²) or if standard metrics sufficed, citing the specific R² and p-values from T029b. **Verification**: Assert `research.md` contains a comparative discussion section with specific statistical values.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Phase 5 (Viz)**: Depends on Phase 4 (US2) completion.
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Consumes US1 output (T016/T017b)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Consumes US2 output
- **Phase N (Polish)**: Depends on all desired user stories being complete

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
3. Add User Story 2 → Test independently → Deploy/Demo (incorporating LOOCV/10-fold CV, VIF checks, and secondary analysis)
4. Add User Story 3 → Test independently → Deploy/Demo (comparative plots)
5. Phase N (Polish) can be tackled by a specialist after baseline is established.

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Simulation Core + Tests)
 - Developer B: User Story 2 (Regression Core + CV + Secondary Analysis)
 - Developer C: User Story 3 (CV & Viz + Comparison Plots)
3. Stories complete and integrate independently
4. Phase N (Polish) can be tackled by a specialist after baseline is established.

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
- **Timeout Handling**: SC-004 compliance is ensured by T030 (global wrapper) in Phase N. Threshold set to 6 hours. Specific network_id or 'aggregate' logged on timeout.
- **Statistical Rigor**: FR-006 compliance ensured by T024 (documenting alpha parameter and remediation action) and T028 (LOOCV/10-fold CV per Spec FR-005).
- **Validation**: SC-003 compliance ensured by T017b (file filtering by extension, verification report, and manual verification log generation) and T017c (Manual Review Gate).
- **Constitution Alignment**: All tasks align with Plan.md and Constitution Principle VII (LOOCV/10-fold CV per Spec FR-005).
- **Dependency Flow**: T005a-c checks raw count and sets state. T022 aggregates. T025 checks state/N and blocks or proceeds. T030 wraps the phase.
- **Plan/Spec Conflict (CV Method)**: Task T028 explicitly follows Spec FR-005 (LOOCV for N<50, 10-fold for N>=50). The Plan's Constitution Check already reflects this.
- **No Synthetic Data**: All tasks explicitly forbid synthetic data generation.
- **Scope Limitation**: All tasks strictly adhere to FR-001 (standard metrics only) for the primary model. Secondary metrics (motifs, modularity) are computed in T019/T029b strictly for comparative analysis and are NOT included in the primary regression model to avoid scope creep, addressing the reviewer's concern without violating the spec's core constraints.
- **Review Response**: Tasks T019, T029b, T034c, and T043b directly address the reviewer's concern about higher-order structures by implementing a parallel, non-invasive analysis path.
