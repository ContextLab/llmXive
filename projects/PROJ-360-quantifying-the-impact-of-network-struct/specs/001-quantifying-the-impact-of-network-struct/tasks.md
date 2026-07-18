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

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004a [P] Implement `code/utils.py` with logging, exponential backoff retry logic, and deterministic seed pinning
- [ ] T004b [P] Setup environment configuration management for API keys and random seeds
- [X] T006 Create `data/metadata.yaml` schema for snapshot timestamp and material IDs

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Download and Construct Atomic Networks from Materials Project (Priority: P1) 🎯 MVP

**Goal**: Download ≥50 CIF files from Materials Project and construct atomic network graphs using covalent radii.

**Independent Test**: Verify ≥50 CIF files exist in `data/raw/cif/` and ≥50 valid graph objects exist in `data/processed/networks/` with correct node/edge counts.

### Implementation for User Story 1

- [X] T007 [US1] Implement `code/download.py` to query Materials Project API for materials with thermal conductivity, handling rate-limiting (HTTP client error) and server errors with a limited number of retries using exponential backoff
- [X] T008 [US1] Implement `code/download.py` logic to fetch and save ≥50 CIF files to `data/raw/cif/` within 30 minutes, skipping materials missing thermal conductivity data
- [X] T009a [US1] **New Task**: Implement `code/validate_dataset.py` function `check_api_availability()` to verify SC-003 (Dataset-variable fit) *before* proceeding to network construction. Query Materials Project to confirm ≥50 materials exist with all required variables (crystallography, thermal conductivity tensor, bond connectivity). Log the count of valid materials.
- [X] T009b [US1] **New Task**: Implement `code/validate_dataset.py` function `verify_downloaded_files()` to verify SC-003 on *actual* artifacts. After T007/T008, parse the downloaded CIF files in `data/raw/cif/` and confirm each contains the required thermal conductivity tensor and crystallography data. Skip malformed files and log errors to `results/power_analysis.log`. This ensures SC-003 is measured against the real dataset, not just API metadata. **Dependency**: T009b MUST run AFTER T008. **Note**: T009b is NOT parallel ([P] removed) due to dependency on T008.
- [X] T009 [US1] Implement `code/construct_network.py` to parse CIF files using `pymatgen`, detect bonds via covalent radius summation with an empirically determined tolerance threshold, and create `networkx.Graph` objects
- [X] T010 [US1] Implement fallback bond detection in `code/construct_network.py` (progressive distance cutoffs) for disconnected graphs; log and skip materials with no edges after fallbacks
- [X] T011 [US1] Save constructed `networkx.Graph` objects to `data/processed/networks/` (pickle format). **CRITICAL**: Update `data/metadata.yaml` to include: 1) Checksums for the source CIF files used (read from `data/raw/cif/`), 2) Checksums for the derived graph objects, and 3) A documented derivation step linking the CIF to the graph (e.g., `derivation: "CIF -> Network via covalent radii + fallback"`). **Constitution Compliance**: Additionally, compute the SHA-256 checksum of each graph file and **immediately** update the `state/projects/PROJ-360-quantifying-the-impact-of-network-struct.yaml` file's `artifact_hashes` map to record these hashes, satisfying Constitution Principle III (Data Hygiene) and Principle V (Versioning Discipline). This must happen within the same task execution to ensure versioning discipline is maintained even if the pipeline crashes later.
- [X] T012 [US1] Implement validation in `code/validate_graphs.py` to ensure every graph has ≥2 nodes and ≥1 edge, or is explicitly skipped with a log entry. **Dependency**: This task MUST run AFTER T011 completes to validate the saved artifacts. **Note**: T012 is NOT parallel ([P] removed) due to strict dependency on T011.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Compute Network Metrics and Correlate with Thermal Conductivity (Priority: P2)

**Goal**: Compute ≥3 network metrics per material and perform correlation analysis with thermal conductivity.

**Independent Test**: Verify `data/processed/metrics.csv` contains ≥3 metrics per material and `results/correlations.json` contains Pearson/Spearman coefficients with Bonferroni-corrected p-values.

### Implementation for User Story 2

- [ ] T013a [US2] **New Task**: Implement `code/compute_metrics.py` function `check_distribution(df)` to perform Shapiro-Wilk test on thermal conductivity and metrics. If non-normal, apply log-transformation and save transformed data to `data/processed/metrics_transformed.csv`. **Reproducibility**: Log whether transformation was applied to `data/metadata.yaml` and ensure the transformed data is linked to the original via a flag, satisfying FR-004 reproducibility requirements. <!-- FAILED: unspecified -->
- [X] T013 [US2] Implement `code/compute_metrics.py` to calculate average degree, average shortest path length (on LCC), and clustering coefficient for each graph in `data/processed/networks/`. **Verification**: Explicitly verify the "largest connected component" (LCC) is correctly identified before computing average path length to avoid silent failures on disconnected graphs.
- [ ] T014a [US2] **New Task**: Implement `code/compute_metrics.py` function `compute_physical_descriptors(cif_path)` to calculate Unit Cell Volume, Total Atom Count, and Mean Atomic Mass for each material. Append these columns to `data/processed/metrics.csv` to satisfy Plan.md Phase 1 Step 2 and FR-006. **Dependency**: T014a MUST run AFTER T013 (metrics.csv creation) to avoid race conditions. **Note**: T014a is NOT parallel ([P] removed) due to dependency on T013.
- [X] T014 [US2] Implement logic in `code/compute_metrics.py` to handle disconnected graphs (report NaN for path length) and compute network density as a diagnostic only
- [ ] T015 [US2] Implement extraction of thermal conductivity scalar ($\frac{k_x + k_y + k_z}{3}$) from CIF metadata (via pymatgen) and append column `thermal_conductivity_scalar` to `data/processed/metrics.csv`. **Verification**: Before appending, implement an explicit assertion that the calculated scalar matches the mean of the three tensor components within a tolerance of 1e-6 to ensure FR-004 compliance. **Recovery**: If the assertion fails, skip the material, log the discrepancy to `results/power_analysis.log`, and continue processing other materials (do not abort the entire pipeline). **Dynamic Sample Size**: Note that skipping a material reduces `n`; subsequent tasks (T016-T018) must use the updated `n` for power analysis and Bonferroni adjustments. **Dependency**: This task MUST run AFTER T013 (metrics.csv creation) to avoid race conditions. **Note**: T015 is NOT parallel ([P] removed) due to dependency on T013.
- [ ] T016 [US2] Implement `code/analyze.py` to compute Pearson and Spearman correlations between each **network metric** (average degree, path length, clustering) and thermal conductivity, storing results in `results/correlations.json`. Do NOT include physical descriptors in this analysis. **Dependency**: Ensure this runs after T015 has appended the target variable to `metrics.csv`. **Note**: T016 is NOT parallel ([P] removed) due to dependency on T015.
- [X] T017 [US2] Implement Bonferroni correction in `code/analyze.py` for the 3 correlation tests to control family-wise error rate at α ≤ 0.05. **Logic**: If sample size n < 50, adjust the Bonferroni correction as per spec Edge Cases; otherwise use fixed divisor k=3.
- [ ] T018a [US2] **New Task**: Implement `code/analyze.py` function `log_sample_size(n)` to log sample size `n` and a warning to `results/power_analysis.log` if `n < 50` (FR-010). **Dependency**: This task is part of a sequential group (T018a -> T018b -> T018c).
- [ ] T018b [US2] **New Task**: Implement `code/analyze.py` function `calculate_alpha(n)` to return the Bonferroni alpha threshold. **Logic**: If n < 50, adjust the alpha threshold (e.g., using a power-adjusted formula or noting the limitation); otherwise return 0.05 / 3. **Note**: T018b must run before T018c.
- [ ] T018c [US2] **New Task**: Implement `code/analyze.py` function `apply_significance(p_value, alpha)` to compare p-values against the calculated alpha threshold and flag significance. **Dependency**: Must run after T018b. **Note**: T018a, T018b, T018c are NOT parallel ([P] removed) and must run sequentially.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Train Predictive Model and Validate Performance (Priority: P3)

**Goal**: Train a linear regression model using VIF-filtered metrics and validate via k-fold cross-validation.

**Independent Test**: Verify `models/thermal_predictor.pkl` exists, and `results/model_performance.json` contains R² and RMSE for multiple folds with mean ± std deviation.

### Implementation for User Story 3

- [ ] T020a [US3] **New Task**: Implement `code/analyze.py` function `calculate_vif(features_df)` to calculate Variance Inflation Factor (VIF) for network metrics AND physical descriptors using `statsmodels` OLS. **Input**: `data/processed/metrics.csv` (columns: avg_degree, path_length, clustering, volume, atom_count, mean_mass). **Output**: VIF values for each feature.
- [ ] T020b [US3] **New Task**: Implement `code/analyze.py` function `log_vif_results(vif_dict)` to log VIF values to `results/power_analysis.log` in format `VIF: <feature_name> = <value>`.
- [X] T020c [US3] **New Task**: Define input/output schema for VIF calculation to ensure deterministic execution.
- [ ] T020d [US3] **New Task**: Implement `code/analyze.py` function `verify_vif_scope(vif_dict)` to explicitly verify that the VIF filtering logic correctly distinguishes between network metrics (required for FR-009) and physical descriptors (optional). Log any ambiguity or error. **Dependency**: T020d must run after T020a.
- [ ] T021 [US3] Implement `code/analyze.py` function `filter_features(features_df, vif_threshold=5)` to filter features: **MUST exclude any feature with VIF ≥ 5**. **Action**: Log every excluded feature and its VIF value to `results/power_analysis.log` in format `EXCLUDED: <feature_name> (VIF=<value>)`. **Action**: Log every included feature and its VIF value to `results/power_analysis.log` in format `INCLUDED: <feature_name> (VIF=<value>)`. **Constraint**: **Write the filtered DataFrame to a new derived artifact `data/processed/filtered_features.csv`** to satisfy Constitution Principle III (Data Hygiene). **Constitution Compliance**: Additionally, compute the SHA-256 checksum of `filtered_features.csv` and **immediately** update the `state/projects/PROJ-360-quantifying-the-impact-of-network-struct.yaml` file's `artifact_hashes` map, satisfying Constitution Principle III and V. **Edge Case**: If all features are excluded, log a critical error and halt the pipeline. **Dependency**: T021 MUST run after T020a.
- [ ] T022 [US3] Implement `code/analyze.py` function `train_model(features_df, target_series)` to train a `scikit-learn` Linear Regression model using **ONLY** the features from `data/processed/filtered_features.csv` (generated by T021). Save the model to `models/thermal_predictor.pkl`. **Dependency**: T022 MUST run after T021.
- [ ] T023 [US3] Implement `code/analyze.py` function `run_cross_validation(model, X, y, k=5)` to perform **k-fold cross-validation** on CPU-only hardware. **Methodology**: Use standard k-fold cross-validation (random splitting) as specified in FR-007. **Configuration**: Use `k=5` as default (configurable). **Strategy**: Compute R² and RMSE for each fold. **Requirement**: If mean R² < 0.30, write the exact string "Weak predictive power (R² < 0.30), consistent with null hypothesis." to the JSON key `r2_interpretation` in `results/model_performance.json`. **Dependency**: T023 MUST run after T022.
- [ ] T024 [US3] Implement `code/analyze.py` function `aggregate_cv_results(cv_results)` to aggregate CV results (mean ± std dev) and save to `results/model_performance.json`. **Dependency**: T024 MUST run after T023.
- [X] T025 [US3] Implement `code/report.py` to generate `results/final_report.md`. **Mandatory**: Insert the exact "Limitations" text defined in FR-008: "This study is observational. Correlations do not imply causality. The thermal conductivity tensor was reduced to a scalar by averaging principal components, which may obscure anisotropic effects." **Action**: This text MUST be written **regardless of the state of `model_performance.json`**. **Action**: Read `r2_interpretation` from `model_performance.json` (if present); if present, append it as a **separate paragraph** immediately following the mandatory Limitations text. If the key is missing, omit the interpretation line. **Dependency**: T025 MUST run after T024.
- [X] T025b [US3] **New Task**: Implement `code/report.py` function `generate_power_analysis_section(n)` to generate the specific power analysis text for `results/final_report.md` as required by FR-010. This section must document sample-size and power considerations, including any warnings logged in `results/power_analysis.log`. **Dependency**: T025b MUST run before T025 (or be integrated into T025) to ensure the report contains the power analysis section.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final reporting and mandatory limitations disclosure

- [X] T026 [US3] Ensure `code/report.py` includes the R² interpretation (from T023/T024) in the Limitations section if R² < 0.30. (Note: This is now integrated into T025 logic).
- [X] T027 [P] Run full pipeline integration test to verify end-to-end data flow from download to report generation within 6 hours on CPU-only hardware
- [ ] T028 [P] Implement `code/validate_outputs.py` to check that `metrics.csv`, `correlations.json`, `model_performance.json`, and `final_report.md` exist and contain required keys as defined in spec.md, exiting with code 0 on success.
- [X] T029 [P] Implement `code/runtime_monitor.py` as a **wrapper script** that invokes the main pipeline. **Requirement**: Enforce a 6-hour timeout during execution. If the pipeline exceeds 21600 seconds, log `ERROR: Runtime exceeds 6h limit` and **exit with code 1** immediately to enforce SC-005. **Success Verification**: If the pipeline completes successfully, log the actual runtime duration to `results/runtime_log.json` and verify it is < 6 hours. This satisfies SC-005 by providing a mechanism to prove the pipeline completed within the limit. **Dependency**: T029 must run *during* execution, not post-hoc.
- [ ] T030 [P] Run quickstart.md validation to ensure reproducibility with pinned seeds and dependencies
- [ ] T031 [P] **New Task**: Implement `code/update_state.py` to update `state/projects/PROJ-360-quantifying-the-impact-of-network-struct.yaml` with `artifact_hashes` for all derived data files (`metrics.csv`, `filtered_features.csv`, `correlations.json`, etc.) as required by Constitution Principle V (Versioning Discipline). This task ensures that every change to data/code is reflected in the project state file. **Dependency**: T031 must run after all data generation tasks (T011, T013, T021, T016, T024). Note: T011 and T021 already perform immediate updates for their specific artifacts; T031 serves as a final consolidation step.

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
- **User Story 2 (P2)**: Depends on US1 completion (requires `data/processed/networks/`)
- **User Story 3 (P3)**: Depends on US2 completion (requires `data/processed/metrics.csv` AND VIF calculation from T020)

### Critical Data-Flow Dependencies (Within/Across Stories)

- **T011 (Save Graphs)** must complete before **T012 (Validate Graphs)** can execute.
- **T011 (Save Graphs)** must complete before **T013 (Compute Metrics)** can execute.
- **T013 (Compute Metrics)** must complete before **T014a (Physical Descriptors)** and **T015 (Extract Thermal Conductivity)** can execute.
- **T014a (Physical Descriptors)** must complete before **T020a (VIF Calculation)** can execute.
- **T020a (VIF Calculation)** must complete before **T021 (VIF Filtering)**.
- **T021 (VIF Filtering)** must complete before **T022 (Model Training)**.
- **T022 (Model Training)** must complete before **T023 (Cross-Validation)**.
- **T023** and **T024** must complete before **T025 (Report Generation)**.
- **T025** must execute after T024 to ensure the report contains both the mandatory boilerplate and the specific R² interpretation.
- **T020a, T020b, T020c, T020d, T021, T022, T023, T024** are strictly sequential and CANNOT be run in parallel. **US3 cannot begin until T020a is complete.**
- **T018a, T018b, T018c** are strictly sequential.
- **T013a, T013, T014a, T014, T015** are sequential or have dependencies (T013 -> T014a/T015).
- **T031** must run after all data generation tasks (T011, T013, T021, T016, T024) to capture all artifact hashes.
- **T009b** must run after T008.
- **T016** must run after T015.
- **T014a** must run after T013.
- **T012** must run after T011.
- **T015** must run after T013.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel (T001a-c, T003).
- T002, T004a, T004b, T006 have implicit ordering dependencies and are not fully parallel with T001.
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows).
- All tests for a user story marked [P] can run in parallel.
- Models within a story marked [P] can run in parallel.
- Different user stories can be worked on in parallel by different team members.
- **NOTE**: T013a, T013, T014a, T014, T015 are sequential or have dependencies (T013 -> T014a/T015).
- **NOTE**: T016, T017, T018a, T018b, T018c are sequential (T018b -> T017, T018c).
- **NOTE**: T020a-T024 are strictly sequential.

---

## Parallel Example: User Story 1

```bash
# Launch all parallel tasks for User Story 1:
Task: "Implement `code/download.py` to query Materials Project API..."
Task: "Implement `code/construct_network.py` to parse CIF files..."
Task: "Implement validation in `code/validate_graphs.py`..."
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
 - Developer C: User Story 3 (Note: T020-T024 must be sequential; T020 must be completed first)
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
- **Critical**: T020a -> T020b -> T020c -> T020d -> T021 -> T022 -> T023 -> T024 is a strict sequential chain. Do not mark these as [P].
- **Critical**: T016 must NOT include physical descriptors. Only network metrics and thermal conductivity scalar.
- **Critical**: T021 must log excluded AND included features to `results/power_analysis.log` and write the filtered features to `data/processed/filtered_features.csv` (no in-memory only filtering). **Also**: Update `state/projects/...yaml` with artifact_hashes **immediately** within the task.
- **Critical**: T025 must include both the mandatory "Limitations" text (always) and the R² interpretation (if applicable) as a separate paragraph. The mandatory text is unconditional.
- **Critical**: T015 must explicitly append `thermal_conductivity_scalar` to `data/processed/metrics.csv` and verify the scalarization logic with an assertion. **Recovery**: Skip material on failure, do not abort. **Dynamic Sample Size**: Subsequent tasks must use the updated `n`.
- **Critical**: T013 depends on T011 completion; T013 cannot run in parallel with T011.
- **Critical**: T029 logs runtime and fails the build (exit 1) if runtime exceeds 6 hours. **Must be a wrapper script**. **Success**: Log runtime to `results/runtime_log.json` and verify < 6h.
- **Critical**: T028 implements `code/validate_outputs.py` to validate artifacts.
- **Critical**: T012 must run after T011 to validate saved artifacts and is NOT parallel.
- **Critical**: US3 cannot begin until T020a is complete.
- **Critical**: T018a/b/c implement power analysis logging and Bonferroni logic (adjust if n < 50).
- **Critical**: T011 must checksum both source CIFs and derived graphs and record the derivation step in `data/metadata.yaml` AND update `state/projects/...yaml` **immediately**.
- **Critical**: T020a-T024 must have distinct function entry points and output artifacts defined to allow independent execution units.
- **Critical**: T009a validates dataset-variable fit (SC-003) before network construction.
- **Critical**: T009b validates dataset-variable fit (SC-003) on *actual* downloaded files.
- **Critical**: T014a computes physical descriptors required for regression.
- **Critical**: T013a performs distribution checks and log-transformation, logging the transformation status.
- **Critical**: T025b generates the power analysis section for the final report.
- **Critical**: T031 updates `state/projects/...yaml` with artifact_hashes for all derived data files (final consolidation).
- **Critical**: T016 must run after T015.
- **Critical**: T014a must run after T013.
- **Critical**: T012 must run after T011.
- **Critical**: T015 must run after T013.
- **Critical**: T009b must run after T008.
- **Critical**: T023 uses standard k-fold, not stratified.
