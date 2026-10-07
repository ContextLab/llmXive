# Tasks: Quantifying the Impact of Network Structure on Heat Diffusion in Crystalline Solids

**Input**: Design documents from `/specs/001-network-structure-thermal-conductivity/`
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

 Tasks MUST be organized by user story so each story can be independently completable and testable.

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001a [P] Create directory `data/raw/cif/`
- [X] T001b [P] Create directory `data/processed/networks/`
- [X] T001c [P] Create directories `data/processed/`, `models/`, `results/`, `code/`
- [X] T002 Initialize Python 3.11 project with `pymatgen`, `networkx`, `scikit-learn`, `pandas`, `requests`, `numpy`, `statsmodels` dependencies
- [X] T003 [P] Configure linting and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can proceed

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004a [P] Implement `code/utils.py` with logging, exponential backoff retry logic, and deterministic seed pinning
- [X] T004b [P] Setup environment configuration management by creating `code/config.py` to handle API keys and random seeds. **Artifact**: `code/config.py` must define a `Config` class or dictionary structure for loading these values. **Implementation**: Load API key from environment variable `MATERIALS_PROJECT_API_KEY`; pin random seeds in a `SEEDS` dictionary with fixed values for reproducibility.
- [X] T006 Create `data/metadata.yaml` schema for snapshot timestamp and material IDs

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Download and Construct Atomic Networks from Materials Project (Priority: P1) 🎯 MVP

**Goal**: Download ≥50 CIF files from Materials Project and construct atomic network graphs using covalent radii.

**Independent Test**: Verify ≥50 CIF files exist in `data/raw/cif/` and ≥50 valid graph objects exist in `data/processed/networks/` with correct node/edge counts.

### Implementation for User Story 1

- [X] T007 [US1] **Sequential**: Download ≥50 CIF files from Materials Project API. **Implementation**: Query the API for materials with thermal conductivity data. **Provenance**: Immediately after download, compute the SHA-256 checksum of each file and store it in `data/metadata.yaml` along with the material ID and download timestamp. This satisfies Constitution Principle VII (Data Provenance). **Output**: CIF files stored in `data/raw/cif/`.
- [X] T008 [US1] **Sequential**: Verify data integrity of downloaded CIF files in `data/raw/cif/` by recomputing and comparing SHA-256 checksums against the values stored in `data/metadata.yaml`. **Dependencies**: [T007].
- [X] T009 [US1] **Sequential**: Implement `code/construct_network.py` to parse CIF files using `pymatgen`, detect bonds via covalent radius summation with a tolerance threshold, and create `networkx.Graph` objects. **Fallback**: If no bonds found, attempt distance cutoffs of increasing magnitude sequentially. **Dependencies**: [T008].
- [X] T010 [US1] Implement fallback bond detection in `code/construct_network.py` (progressive distance cutoffs) for disconnected graphs; log and skip materials with no edges after fallbacks. **Dependencies**: [T009].
- [X] T011 [US1] Save constructed `networkx.Graph` objects to `data/processed/networks/` (pickle format). **Checksum Generation**: Compute SHA-256 checksums for the source CIF files and the derived graph objects. **State Update**: Write these checksums to the `state/projects/PROJ-360-quantifying-the-impact-of-network-struct.yaml` file in the `artifact_hashes` map, and also write a local `data/processed/checksums.json` for convenience. **Dependencies**: [T010].
- [X] T012 [US1] Implement validation in `code/validate_graphs.py` to ensure every graph has ≥2 nodes and ≥1 edge, or is explicitly skipped with a log entry. **Dependencies**: [T011].

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Compute Network Metrics and Correlate with Thermal Conductivity (Priority: P2)

**Goal**: Compute ≥3 network metrics per material and perform correlation analysis with thermal conductivity.

**Independent Test**: Verify `data/processed/metrics.csv` contains ≥3 metrics per material and `results/correlations.json` contains Pearson/Spearman coefficients with Bonferroni-corrected p-values.

### Implementation for User Story 2

- [X] T013 [US2] **Sequential**: Implement `code/compute_metrics.py` to compute average degree, average shortest path length (on LCC), and clustering coefficient for each graph in `data/processed/networks/`. **Physical Descriptors**: Also compute Unit Cell Volume, Total Atom Count, and Mean Atomic Mass for each material. **Output**: Save a unified `data/processed/metrics.csv` containing both network metrics AND physical descriptors (columns: `material_id`, `average_degree`, `average_path_length`, `clustering_coefficient`, `thermal_conductivity_scalar`, `unit_cell_volume`, `total_atom_count`, `mean_atomic_mass`). **Dependencies**: [T011].
- [X] T014c [US2] **Sequential**: Merge physical descriptors from `data/processed/confounders.csv` (if generated separately) into the main `data/processed/metrics.csv` to ensure they are available for downstream analysis. **Verification**: Confirm that `metrics.csv` contains columns `unit_cell_volume`, `total_atom_count`, and `mean_atomic_mass` after merging. **Dependencies**: [T013].
- [X] T016a [US2] Compute Pearson and Spearman correlations between each network metric and thermal conductivity, storing results in temporary files before writing final data. **Dependencies**: [T014c].
- [X] T016b [US2] Save the correlation results to `results/correlations.json`. **Dependencies**: [T016a].
- [X] T016c [US2] Update `data/processed/checksums.json` with the checksum for `results/correlations.json`. **Dependencies**: [T016b].
- [X] T017 [US2] Implement Bonferroni correction for the correlation tests. **Dynamic Denominator**: Calculate the number of actual tests performed (`n_tests`) based on the available network metrics (a set of metrics including average_degree, average_path_length, and clustering_coefficient). Calculate alpha as the nominal significance level divided by `n_tests`. Apply this correction to all p-values to control family-wise error rate. **Dependencies**: [T016b].
- [X] T018a [US2] Log sample size and a warning if n < 50. **Dependencies**: [T017].
- [X] T018b [US2] Verify that at least 50 materials remain after filtering in previous steps and log the final count. **Dependencies**: [T012, T013, T014c].

**Checkpoint**: At this point, User Story 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Train Predictive Model and Validate Performance (Priority: P3)

**Goal**: Train a linear regression model using VIF-filtered network metrics and physical descriptors (to control confounders) and validate via stratified k-fold cross-validation.

**Independent Test**: Verify `models/thermal_predictor.pkl` exists, and `results/model_performance.json` contains R² and RMSE for multiple folds with mean ± std deviation.

### Implementation for User Story 3

- [X] T020a [US3] Calculate VIF for all candidate **features** (average_degree, average_path_length, clustering_coefficient, unit_cell_volume, total_atom_count, mean_atomic_mass) from `data/processed/metrics.csv`. **Scope**: Include physical descriptors to control for confounding. **Filtering**: Exclude features with VIF ≥ 5. **Dependencies**: [T014c].
- [X] T020b [US3] Write the filtered feature set (network metrics + physical descriptors) to `data/processed/filtered_features.csv`. **Dependencies**: [T020a].
- [X] T020c [US3] Log VIF values and update checksums for filtered features. **Dependencies**: [T020b].
- [X] T022 [US3] Train a linear regression model using the **filtered features + physical descriptors** from `data/processed/filtered_features.csv` as features to predict thermal conductivity. **Validation**: Explicitly verify that `filtered_features.csv` contains the columns `unit_cell_volume`, `total_atom_count`, and `mean_atomic_mass` before training; raise an error if missing. Save the model to `models/thermal_predictor.pkl`. **Dependencies**: [T020b].
- [X] T023 [US3] Perform **stratified** k-fold cross-validation on CPU-only hardware. **Stratification Method**: Since the target is continuous, bin the thermal conductivity values into 5 quantile-based bins to enable stratification. **Adaptive k**: Default to k=5. If the sample size n < 10, set k = min(n-1, 2). Do NOT bin the target for the final prediction, only for stratification. Compute R² and RMSE for each fold. **Dependencies**: [T022].
- [X] T024 [US3] Aggregate the CV results (mean ± std dev) and save them to `results/model_performance.json`. **Dependencies**: [T023].
- [X] T025 [US3] Generate `results/final_report.md`. **Implementation**: Read performance data from `results/model_performance.json`. Unconditionally insert the mandatory "Limitations" text: "This study is observational. Correlations do not imply causality. The thermal conductivity tensor was reduced to a scalar by averaging principal components, which may obscure anisotropic effects." Append the R² interpretation if performance data is available. **Dependencies**: [T024].

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, documentation, and cleanup

- [X] T026 [P] Verify `results/final_report.md` contains the mandatory "Limitations" section text exactly as specified in FR-008. **Dependencies**: [T025].
- [X] T027 [P] Run full pipeline integration test: Execute `code/download.py` → `code/construct_network.py` → `code/compute_metrics.py` → `code/analyze.py` → `code/report.py` in sequence and verify all artifacts are generated and checksums match. **Dependencies**: [T007, T009, T013, T022, T025].
- [ ] T028 [P] Update `quickstart.md` with exact commands to run the full pipeline and verify the "Limitations" text in the output report. **Dependencies**: [T027].

---

## Phase 7: Revision & Robustness (Review-Driven)

**Goal**: Address specific reviewer concerns regarding data integrity, API resilience, and statistical rigor.

### Implementation for Revision Concerns

- [X] T029 [US1] **Robustness**: Refactor `code/download.py` to strictly enforce "Fail Loudly" semantics. **Requirement**: Remove any `try/except` blocks that fallback to synthetic/mock data if the Materials Project API fails. If the API returns an error or timeout, the script MUST raise an exception and halt execution. **Rationale**: Prevents silent fabrication of data which is rejected by the execution gate. **Dependencies**: [T007].
- [X] T030 [US1] **API Resilience**: Implement a dedicated `APIRateLimiter` class in `code/utils.py` that tracks request timestamps and enforces a 1-second minimum delay between requests to avoid 429 errors, integrated into the download loop. **Dependencies**: [T004a].
- [X] T031 [US2] **Statistical Rigor (FR-004)**: Add a task to `code/analyze.py` to perform a Shapiro-Wilk normality test on the thermal conductivity and network metric distributions. **Verification**: If non-normal (p < 0.05), apply a log-transformation to the affected columns. **Output**: Save the transformed dataset to `data/processed/metrics_transformed.csv`. **Dependency Update**: Subsequent correlation tasks (T016a) MUST check for the existence of `data/processed/metrics_transformed.csv` and use it if present; otherwise, use the original `metrics.csv`. **Dependencies**: [T013].
- [ ] T032a [US3] **Model Robustness Check**: Perform a multiple regression analysis using the filtered network metrics AND the physical descriptors (unit_cell_volume, total_atom_count, mean_atomic_mass) as features to predict thermal conductivity. **Rationale**: This serves as a robustness check to confirm the predictive power of network metrics when controlling for physical confounders, authorized by FR-006 and FR-009. **Output**: Save results to `results/robustness_check.json` with schema: `{model_r2, model_rmse, feature_coefficients}`. **Dependencies**: [T020a]. <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->
- [ ] T033 [US3] **Model Validation**: Add a task to generate a residual plot (predicted vs. actual thermal conductivity) and save it to `results/model_residuals.png` to visually inspect heteroscedasticity or bias. **Dependencies**: [T024].

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Revision (Phase 7)**: Depends on completion of US1, US2, US3 implementation

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
- Revision tasks (T029-T033) can run in parallel with each each other once the base implementation is complete

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
- **Critical Rule**: Never fallback to synthetic data. If data fetch fails, the run must fail.