# Tasks: Investigating the Impact of Network Topology on Neural Entrainment to Rhythmic Stimuli

**Input**: Design documents from `/specs/001-network-topology-entrainment/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `data/`, `tests/` at repository root
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

 Tasks MUST be organized by user story so each story can:
 - Implemented independently
 - Tested independently
 - Delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001b [P] Create subdirectories: `code/`, `data/`, `data/raw/`, `data/processed/`, `data/visualizations/`, `tests/`, `tests/unit/`, `tests/integration/`, `docs/`.
- [ ] T001c [P] Initialize `.gitkeep` files in all empty directories.
- [X] T002a [P] Create `requirements.txt` pinning: `networkx==2.8.8`, `numpy==1.24.0`, `pandas==2.0.0`, `scikit-learn==1.2.0`, `scipy==1.10.0`, `matplotlib==3.7.0`, `pyyaml==6.0`, `pytest==7.3.0`.
- [X] T002b [P] Create `code/__init__.py` and `tests/__init__.py`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004a [P] Implement `code/config.py` skeleton: Define `ATLAS_TYPES` as the immutable list of representative parcellation schemes, including Schaefer, AAL, and Power. and `RANDOM_SEED`.
- [X] T004b [P] Extend `code/config.py`: Add `atlas_type` parameter support for alternative atlases (AAL, Power 264) and corresponding data paths.
- [X] T005a [P] Implement `code/data_loader.py` skeleton: Define function signatures for `validate_entrainment_csv()`, `validate_topology_columns()`.
- [X] T005b [P] Implement `code/data_loader.py`: `validate_entrainment_csv()` to check for `subject_id`, `entrainment_metric` columns and numeric types (FR-008).
- [X] T005c [P] Implement `code/data_loader.py`: `validate_topology_columns()` to check for required topology metric columns (FR-007).
- [X] T006 [P] **GENERATE SIMULATED RAW DATA**: Implement `code/data_loader.py`: Generate deterministic simulated raw correlation matrices for the Schaefer atlas (N=50 subjects, 200x200 matrices) to satisfy FR-001 given the "Dataset Availability" assumption that real matched data is unavailable. **Schema**: `subject_id` (str), `matrix_data` (flattened list of [deferred] floats representing the upper triangle of the correlation matrix). **Constraint**: Must be reproducible (use `RANDOM_SEED` from config). Do NOT attempt a download; generate the data directly. (FR-001, Spec Assumption: Dataset Availability).
- [X] T007 [P] Implement `code/main.py` orchestration skeleton: Argument parsing, error handling wrapper, and "Data Gap" exit protocol (Plan: Data Gap Handling Protocol).
- [X] T008 [P] Setup `data/checksums.json` structure (optional cache) but ensure primary state is in YAML.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Core Correlation Analysis (Priority: P1) 🎯 MVP

**Goal**: Compute resting-state network topology metrics from HCP fMRI data (or simulated) and correlate them with external entrainment strength metrics. **Since real matched data is unavailable, the system MUST trigger the Simulated Data Fallback (FR-009) to generate synthetic data with target r=0.5.**

**Independent Test**: Can be fully tested by executing the correlation pipeline on a subset of subjects (simulated) and verifying that a scatter plot and correlation coefficient (r, p-value) are generated for the primary hypothesis.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010a [P] [US1] Create `tests/unit/test_network_metrics.py` and write a test for `calculate_clustering_coefficient()` using a synthetic small matrix.
- [X] T010b [P] [US1] Create `tests/unit/test_network_metrics.py` and write a test for `calculate_path_length()` using a synthetic small matrix.
- [X] T011a [P] [US1] Create `tests/unit/test_analysis.py` and write a test for Spearman correlation logic with known synthetic data.
- [X] T011b [P] [US1] Create `tests/unit/test_analysis.py` and write a test for VIF calculation logic.

### Implementation for User Story 1

- [ ] T012a [US1] **INGEST ENTRAINMENT DATA (STRICT)**: Implement `code/data_loader.py`: Function `load_entrainment_csv()`. **Logic**: Attempt to load `data/raw/entrainment_metrics.csv`. **If the file exists**, validate columns (`subject_id`, `entrainment_metric`) and numeric types (FR-008, FR-003). **If the file is MISSING**, return a status object `{"exists": false, "reason": "missing"}`. **DO NOT** raise an exception; allow T012b to trigger the fallback. (FR-003). **Dependency**: None.
- [ ] T012b [US1] **JOIN & FALLBACK TRIGGER**: Implement `code/data_loader.py`: Function `join_and_check_n()`. **Logic**: 1. Load topology metrics (from T006). 2. Call T012a. 3. If T012a returns "missing" OR if the inner join on `subject_id` yields N < 30, **trigger T012c**. 4. If T012a succeeds and N >= 30, proceed with real data. **Output**: `data/processed/joined_data.csv` (if N>=30) or signal to T012c. Update `data/processed/metadata.json` with `data_source` ("Real" or "Simulated") and `N`. (FR-003, FR-009). **Dependency**: T012a, T006.
- [ ] T012c [US1] **SIMULATION FALLBACK & GENERATION**: Implement `code/simulation.py`: Function `generate_entrainment_fallback()`. **Logic**: If triggered by T012b (due to missing file or N < 30), generate synthetic entrainment metrics correlated with the available topology metrics (target r = 0.5, noise = 0.2) per FR-009. **Algorithm**: Use Cholesky decomposition on a target correlation matrix to ensure the generated data has the exact target correlation. **If topology metrics are also missing**, generate both synthetic topology and entrainment metrics. **Label the data source as "Simulated" in all outputs**. Save to `data/raw/entrainment_metrics.csv` (if missing) and `data/processed/joined_data_simulated.csv`. **Dependency**: T012b (trigger signal).
- [X] T013a [US1] Implement `code/graph_metrics.py`: Function `calculate_clustering_coefficient()` for weighted correlation matrices (from T012b/T012c output). **Dependency**: T012b/T012c must complete successfully to provide input.
- [X] T013b [US1] Implement `code/graph_metrics.py`: Function `calculate_path_length()` for weighted correlation matrices (from T012b/T012c output). **Dependency**: T012b/T012c must complete successfully to provide input.
- [ ] T013c [US1] Implement `code/graph_metrics.py`: Zero-variance detection: If a metric has zero variance (std < 1e-9), flag it as "Non-informative" and write this flag to `data/processed/metric_flags.json`. **Schema**: `{"metric_name": "str", "status": "str", "reason": "str"}`. **Output**: `data/processed/metric_flags.json`. (Edge Case: Zero Variance). **Dependency**: T013a, T013b.
- [ ] T014 [US1] Implement `code/analysis.py`: Calculate **Spearman correlation** between topology metrics and entrainment strength. **Read 'Non-informative' flags from `data/processed/metric_flags.json` (T013c)**. If a metric is flagged, skip calculation and set `status` to 'Non-informative' in the output. (Edge Case: Zero Variance). **Dependency**: T012b, T013c.
- [X] T015a [US1] Implement `code/analysis.py`: Calculate **VIF** between the two topology metrics to check collinearity in the joint model.
- [X] T015b [US1] Implement `code/analysis.py`: **Fitting the MLR Model**: Fit a Multiple Linear Regression (MLR) model with entrainment strength as the dependent variable and Clustering Coefficient and Characteristic Path Length as independent predictors. **Conditional Logic**: If VIF > 5 (from T015a), **suppress individual p-values for those predictors and report only the joint model R-squared**. If VIF ≤ 5, report standardized coefficients, p-values, and apply **Holm-Bonferroni correction** (using `scipy.stats.multitest.multipletests` with method='holm') for the two tested predictors; add `adjusted_p_value` and `is_significant` columns (FR-004, SC-003). **Output Specification**: If VIF > 5, set `p_value` and `adj_p_value` columns to `NaN` and `status` column to 'Collinear'. **Do NOT use simple Bonferroni**. **Dependency**: T015a, T012b.
- [X] T015c [US1] Implement `code/analysis.py`: Generate `data/processed/correlation_results.csv` containing subject IDs, metrics, r, p, adjusted p, `collinearity_warning` (boolean), `vif_value`, and data source label ("Simulated" or "Real"). **Verification**: Ensure columns `raw_p`, `adjusted_p_value`, `is_significant`, `vif_value`, `collinearity_warning` are present and correctly populated. **Dependency**: T014, T015b.
- [ ] T016 [US1] Implement `code/viz.py`: Generate scatter plot with **95% confidence intervals** using `matplotlib`; save to `data/visualizations/scatter_topology_entrainment.png`. **Method**: Calculate 95% CI using **parametric t-distribution on residuals**. Ensure the 95% CI bands are explicitly calculated and rendered. **Dependency**: T015c.
- [~] T017a [US1] **GENERATE SUMMARY REPORT**: Implement `code/analysis.py`: Generate `data/processed/summary_report.txt`. **Content**: Include MLR statistics, effect sizes, and **explicitly include the string "Power Warning: N < 30 (Exploratory)"** if N < 30. **Dependency**: T015c, T021.
- [X] T017 [US1] Implement `code/main.py`: Orchestrate full US1 pipeline: Load -> Validate -> Compute Metrics -> Correlate -> Plot -> Report. **Invoke `code/state_manager.py` to compute SHA256 and update the project state YAML atomically after the pipeline completes.** **Artifacts to hash**: `data/processed/correlation_results.csv`, `data/visualizations/scatter_topology_entrainment.png`, `data/processed/summary_report.txt`. **State Key**: Update `state/projects/PROJ-486-investigating-the-impact-of-network-topo.yaml` under `artifact_hashes`. **Dependency**: T017a, T016, T015c.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Multiple Comparisons & Power Correction (Priority: P2)

**Goal**: Apply Holm-Bonferroni correction to p-values and report power limitations.

**Independent Test**: Can be fully tested by providing a synthetic dataset with known raw p-values, running the correction module, and verifying that the output p-values are correctly adjusted using the Holm-Bonferroni method and the significance threshold is correctly updated.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [P] [US2] Unit test for Holm-Bonferroni correction logic in `tests/unit/test_analysis.py` with known inputs.

### Implementation for User Story 2

- [X] T021 [US2] Implement `code/analysis.py`: Inject "Power Warning: N < 30 (Exploratory)" string into the summary report if N < 30 (FR-002). **Dependency**: T017a.
- [X] T022 [US2] Update `code/main.py` to ensure the final report generation includes the corrected p-values and power warning logic.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Robustness Sensitivity Analysis (Priority: P3)

**Goal**: Re-run core correlation using alternative parcellation schemes (AAL, Power 264) to verify robustness.

**Independent Test**: Can be fully tested by swapping the input atlas config to "AAL" and verifying that the pipeline completes without error and produces a comparative result table.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T024 [P] [US3] Integration test swapping atlas config in `tests/integration/test_sensitivity.py`.

### Implementation for User Story 3

- [X] T025 [US3] Implement `code/graph_metrics.py`: Ensure metric calculation is atlas-agnostic (works with any correlation matrix input).
- [X] T026 [US3] Implement `code/analysis.py`: Re-run correlation pipeline for alternative atlases (AAL, Power 264); generate comparative result table (`data/processed/sensitivity_results.csv`).
- [~] T027a [US3] **AGGREGATE SENSITIVITY RESULTS**: Implement `code/analysis.py`: Aggregate results from T026 (Schaefer, AAL, Power) into a single dataset `data/processed/sensitivity_aggregated.csv`. **Schema**: `atlas_type`, `effect_size`, `p_value`. Calculate `absolute_diff` from Schaefer baseline for AAL and Power. **Output**: `data/processed/sensitivity_aggregated.csv`. **Dependency**: T026.
- [~] T027 [US3] Implement `code/viz.py`: Generate a **single comparative bar chart** (PNG format) showing the **absolute difference** in effect sizes between the primary Schaefer baseline and **BOTH** alternative atlases. **Input**: `data/processed/sensitivity_aggregated.csv` (T027a). The chart must contain **exactly two bars** labeled "AAL Diff" and "Power Diff" with **numeric values in the title** (Format: "Sensitivity Analysis: AAL Diff: {val:.3f}, Power Diff: {val:.3f}"). Save to `data/visualizations/sensitivity_comparison.png`. **Dependency**: T027a.
- [X] T028 [US3] Implement `code/main.py`: Add loop or flag to execute sensitivity analysis if `--sensitivity` is passed.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T029 [P] Update `docs/quickstart.md` with execution instructions and data requirements.
- [~] T030a [P] **EXECUTE RUNTIME VERIFICATION**: Run full integration test on a **subset (N=5)** of simulated data to verify pipeline flow. **Pass Criteria**: Runtime < 1 minute for N=5. Capture timing logs to `data/logs/runtime_subset.log`. **Dependency**: None.
- [ ] T030b [P] **VERIFY RUNTIME**: Parse `data/logs/runtime_subset.log` and verify runtime < 1 minute. Also verify full pipeline (N=50) runtime < 6h (SC-004) if executed. **Pass Criteria**: Logs exist and show valid runtime. **Dependency**: T030a.
- [ ] T031a [P] **GENERATE DATA GAP REPORT**: Implement `code/data_loader.py`: On fallback trigger (T012b), write `data_gap_report.json` with schema `{"fallback_triggered": true, "data_source": "Simulated", "reason": "missing_file|low_n"}`. **Dependency**: T012b.
- [ ] T031 [P] **VERIFY DATA GAP PROTOCOL**: Verify `data_gap_report.json` exists and contains correct keys/values after a simulated run. Ensure `data/processed/metadata.json` indicates "Simulated Data Used". **Dependency**: T031a.
- [ ] T033 [P] **ADD DATA SOURCE METADATA**: Update `code/main.py` and `code/analysis.py` to explicitly write `data_source: "Simulated"` or `data_source: "Real"` to `data/processed/metadata.json` and include this field in the header of all output CSVs (`correlation_results.csv`, `sensitivity_results.csv`). (Addressing FR-009 requirement to label data source).
- [ ] T035a [P] **IMPLEMENT UNIT TEST FOR CI**: Create `tests/unit/test_viz.py` and write a unit test to verify that the scatter plot generation function calculates 95% confidence intervals using the specified parametric t-distribution method and renders them as shaded regions. **Dependency**: T016.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 results for correction
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 logic for re-execution

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- **Data Flow**: T012a -> T012b -> T012c -> T006 -> T013a/b -> T013c -> T014 -> T015 -> T016 -> T017a -> T017
- Data loading/validation before metric calculation
- Metric calculation before correlation
- Correlation before visualization
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if staffed)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for network_metrics.py using synthetic small matrix in tests/unit/test_network_metrics.py"
Task: "Unit test for analysis.py correlation logic with known synthetic data in tests/unit/test_analysis.py"

# Launch implementation for User Story 1 (sequential dependencies):
Task: "Implement simulation.py: Generate synthetic data with target r=0.5..."
Task: "Implement graph_metrics.py: Calculate Clustering Coefficient..."
Task: "Implement analysis.py: Calculate Spearman correlation..."
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
- **Constraint**: All tasks MUST run on CPU-only CI (cores, GB RAM). No GPU, no 8-bit models, no large LLMs.
- **Data**: Use real HCP data if available, but **default to Simulated Data Fallback (FR-009)** as per spec assumptions. Do not fabricate scientific results; use simulation for pipeline validation.
- **Data Hygiene**: Checksums are recorded by `code/state_manager.py` after pipeline completion to ensure atomicity, NOT during individual data loading steps.
- **Correction**: Ensure Holm-Bonferroni is used, not simple Bonferroni.
- **File Naming**: All topology metric tasks must use `code/graph_metrics.py` as defined in plan.md.
- **Critical Fix**: The data loader must **fail loudly** on missing real data; fallback logic must be isolated to the join/check step.
- **Critical Fix**: All outputs must explicitly label the data source as "Simulated" or "Real".
- **Critical Fix**: Zero-variance metrics must be detected and flagged before correlation.
- **Critical Fix**: Scatter plots must include calculated 95% confidence intervals.