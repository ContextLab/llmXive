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
- [X] T004b [P] Setup environment configuration management by creating `code/config.py` to handle API keys and random seeds. **Artifact**: `code/config.py` must define a `Config` class or dictionary structure for loading these values. **Implementation**: Load API key from environment variable `MATERIALS_PROJECT_API_KEY`; pin random seeds in a `SEEDS` dictionary with fixed values for reproducibility.
- [X] T006 Create `data/metadata.yaml` schema for snapshot timestamp and material IDs

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Download and Construct Atomic Networks from Materials Project (Priority: P1) 🎯 MVP

**Goal**: Download ≥50 CIF files from Materials Project and construct atomic network graphs using covalent radii.

**Independent Test**: Verify ≥50 CIF files exist in `data/raw/cif/` and ≥50 valid graph objects exist in `data/processed/networks/` with correct node/edge counts.

### Implementation for User Story 1

- [X] T007 [US1] Implement `code/download.py` to query Materials Project API for materials with thermal conductivity. **Validation**: Query must verify ≥50 materials exist with required variables (crystallography, thermal conductivity tensor) as per spec Assumptions, logging the count to satisfy SC-003. **API Details**: Use endpoint `https://next-gen.materialsproject.org/api/v2/docs/crystal` with header `Authorization: Bearer $MATERIALS_PROJECT_API_KEY` and query parameter `has_thermal_conductivity=true`. Handle rate-limiting (HTTP 429) and server errors (HTTP 503) with exponential backoff (1s, 2s, 4s) up to 3 retries. **Dependency**: This task includes the validation previously in T009a/T009b, integrated into the download flow to preserve US-1 structure.
- [X] T008 [US1] Implement `code/download.py` logic to fetch and save ≥50 CIF files to `data/raw/cif/` within 30 minutes, skipping materials missing thermal conductivity data.
- [X] T009 [US1] Implement `code/construct_network.py` to parse CIF files using `pymatgen`, detect bonds via covalent radius summation with a tolerance threshold, and create `networkx.Graph` objects. **Fallback**: If no bonds found, attempt distance cutoffs of increasing magnitude sequentially. **Tolerance Logic**: Bond exists if distance ≤ (covalent_radius_i + covalent_radius_j + δ), where δ represents an empirically determined tolerance threshold.
- [X] T010 [US1] Implement fallback bond detection in `code/construct_network.py` (progressive distance cutoffs) for disconnected graphs; log and skip materials with no edges after fallbacks.
- [X] T011 [US1] Save constructed `networkx.Graph` objects to `data/processed/networks/` (pickle format). **CRITICAL**: Update `data/metadata.yaml` to include: 1) Checksums for the source CIF files used (read from `data/raw/cif/`), 2) Checksums for the derived graph objects, and 3) A documented derivation step linking the CIF to the graph (e.g., `derivation: "CIF -> Network via covalent radii + fallback"`). **Constitution Compliance**: Additionally, compute the SHA-256 checksum of each graph file and **immediately** update the `state/projects/PROJ-360-quantifying-the-impact-of-network-struct.yaml` file's `artifact_hashes` map to record these hashes, satisfying Constitution Principle III (Data Hygiene) and Principle V (Versioning Discipline). **Implementation**: Write to temp file, then atomic rename; YAML path: `artifact_hashes -> {file_path: sha256_hash}`. This must happen within the same task execution to ensure versioning discipline is maintained even if the pipeline crashes later.
- [X] T012 [US1] Implement validation in `code/validate_graphs.py` to ensure every graph has ≥2 nodes and ≥1 edge, or is explicitly skipped with a log entry. **Dependencies**: [T011] **Note**: T012 is NOT parallel ([P] removed) due to strict dependency on T011.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Compute Network Metrics and Correlate with Thermal Conductivity (Priority: P2)

**Goal**: Compute ≥3 network metrics per material and perform correlation analysis with thermal conductivity.

**Independent Test**: Verify `data/processed/metrics.csv` contains ≥3 metrics per material and `results/correlations.json` contains Pearson/Spearman coefficients with Bonferroni-corrected p-values.

### Implementation for User Story 2

- [ ] T013 [US2] Implement `code/compute_metrics.py` to calculate average degree, average shortest path length (on LCC), and clustering coefficient for each graph in `data/processed/networks/`. **Verification**: Explicitly verify the "largest connected component" (LCC) is correctly identified before computing average path length to avoid silent failures on disconnected graphs. **Output**: Save to `data/processed/metrics.csv` with columns: `material_id`, `avg_degree`, `path_length`, `clustering`. **State Update**: Immediately update `state/projects/PROJ-360-quantifying-the-impact-of-network-struct.yaml` with checksum of `metrics.csv`.
- [ ] T014a [US2] Implement `code/compute_metrics.py` function `compute_physical_descriptors(cif_path)` to calculate Unit Cell Volume, Total Atom Count, and Mean Atomic Mass for each material. **Output**: Log these values to `results/power_analysis.log` for diagnostic purposes ONLY. **Constraint**: Do NOT append these columns to `data/processed/metrics.csv` for regression features; they are strictly for logging. **Rationale**: Physical descriptors are excluded from regression to avoid confounding; their exclusion is documented in the final report. **Dependencies**: [T013] **Note**: T014a is NOT parallel ([P] removed) as it depends on T013.
- [X] T014 [US2] Implement logic in `code/compute_metrics.py` to handle disconnected graphs (report NaN for path length) and compute network density as a diagnostic only
- [ ] T015 [US2] Implement extraction of thermal conductivity scalar ($\frac{k_x + k_y + k_z}{3}$) from CIF metadata (via pymatgen: `structure.properties['thermal_conductivity_tensor']`) and append column `thermal_conductivity_scalar` to `data/processed/metrics.csv`. **Verification**: Before appending, implement an explicit assertion that the calculated scalar matches the mean of the three tensor components within a tolerance of 1e-6 to ensure FR-004 compliance. **Recovery**: If the metadata for thermal conductivity is missing, skip the material and log the discrepancy to `results/power_analysis.log` with count. **Constraint**: Do NOT implement assertion failures for calculation errors; only skip on missing metadata as per spec Edge Cases. **Dynamic Sample Size**: Note that skipping a material reduces `n`; subsequent tasks (T016-T018) must use the updated `n` for power analysis and Bonferroni adjustments. **Dependencies**: [T013] **Note**: T015 is parallel ([P]) relative to T014a, but both depend on T013. <!-- FAILED: unspecified -->
- [ ] T016 [US2] Implement `code/analyze.py` to compute Pearson and Spearman correlations between each **network metric** (average degree, path length, clustering) and thermal conductivity, storing results in `results/correlations.json`. Do NOT include physical descriptors in this analysis. **Dependencies**: [T015] **State Update**: Immediately update `state/projects/PROJ-360-quantifying-the-impact-of-network-struct.yaml` with checksum of `correlations.json`. **Note**: T016 is NOT parallel ([P] removed) due to dependency on T015.
- [X] T017 [US2] Implement Bonferroni correction in `code/analyze.py` for the 3 correlation tests to control family-wise error rate at α ≤ 0.05. **Logic**: Use fixed alpha = 0.05 / 3. Do NOT adjust alpha based on sample size n < 50. If n < 50, log a warning in `results/power_analysis.log` but maintain the fixed alpha threshold as per FR-005. **Dependencies**: [T016]
- [X] T018a [US2] Implement `code/analyze.py` function `log_sample_size(n)` to log sample size `n` and a warning to `results/power_analysis.log` if `n < 50` (FR-010). **Clarification**: Bonferroni alpha threshold remains fixed at a standard significance level.; power limitations are documented in the final report. **Dependencies**: [T017] **Note**: T018a is NOT parallel ([P] removed) and must run sequentially after T017. <!-- FAILED: unspecified -->
- [X] T018c [US2] Implement `code/analyze.py` function `apply_significance(p_value)` to compare p-values against the fixed alpha threshold (corrected for multiple comparisons) and flag significance. **Dependencies**: [T018a] **Note**: T018a and T018c are NOT parallel ([P] removed) and must run sequentially after T017.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Train Predictive Model and Validate Performance (Priority: P3)

**Goal**: Train a linear regression model using VIF-filtered network metrics and validate via k-fold cross-validation.

**Independent Test**: Verify `models/thermal_predictor.pkl` exists, and `results/model_performance.json` contains R² and RMSE for multiple folds with mean ± std deviation.

### Implementation for User Story 3

- [ ] T020a [US3] Implement `code/analyze.py` function `calculate_vif(features_df)` to calculate Variance Inflation Factor (VIF) for network metrics ONLY (average degree, path length, clustering). **Input**: `data/processed/metrics.csv` (columns: avg_degree, path_length, clustering). **Constraint**: Do NOT include physical descriptors (volume, atom count, mass) in this calculation. **Output**: VIF values for each feature. **Implementation**: Use `statsmodels.stats.outliers_influence.variance_inflation_factor`; handle singular matrix by logging error and skipping feature. **Dependencies**: [T013] **Note**: T020a is NOT parallel ([P] removed) as it is part of strict sequential chain.
- [ ] T020b [US3] Implement `code/analyze.py` function `log_vif_results(vif_dict)` to log VIF values to `results/power_analysis.log` in format `VIF: <feature_name> = <value>`. **Dependencies**: [T020a]
- [X] T020c [US3] Create `contracts/vif_schema.yaml` defining the input/output schema for VIF calculation to ensure deterministic execution. **Artifact**: `contracts/vif_schema.yaml`. **Schema Format**: YAML with required fields: `feature_name`, `vif_value`, `threshold`. **Dependencies**: [T020a]
- [ ] T020d [US3] Implement `code/analyze.py` function `verify_vif_scope(vif_dict)` to explicitly verify that the VIF filtering logic correctly distinguishes between network metrics (required for FR-009) and physical descriptors (excluded). Log any ambiguity or error. **Dependencies**: [T020a]
- [ ] T021 [US3] Implement `code/analyze.py` function `filter_features(features_df, vif_threshold=5)` to filter features: **MUST exclude any feature with VIF ≥ 5**. **Constraint**: Use ONLY network metrics as input. **Action**: Log every excluded feature and its VIF value to `results/power_analysis.log` in format `EXCLUDED: <feature_name> (VIF=<value>)`. **Action**: Log every included feature and its VIF value to `results/power_analysis.log` in format `INCLUDED: <feature_name> (VIF=<value>)`. **Constraint**: **Write the filtered DataFrame to a new derived artifact `data/processed/filtered_features.csv`** to satisfy Constitution Principle III (Data Hygiene). **Constitution Compliance**: Additionally, compute the SHA-256 checksum of `filtered_features.csv` and **immediately** update the `state/projects/PROJ-360-quantifying-the-impact-of-network-struct.yaml` file's `artifact_hashes` map, satisfying Constitution Principle III and V. **Edge Case**: If all features are excluded, log a critical error, generate a report stating "No valid features for regression", and exit successfully (or with a specific 'no-model' code) to ensure the research question is answered even if the model cannot be trained. **Dependencies**: [T020a]
- [ ] T022 [US3] Implement `code/analyze.py` function `train_model(features_df, target_series)` to train a `scikit-learn` Linear Regression model using **ONLY** the features from `data/processed/filtered_features.csv` (generated by T021). **Constraint**: Do NOT include physical descriptors. Save the model to `models/thermal_predictor.pkl`. **Dependencies**: [T021]
- [ ] T023 [US3] Implement `code/analyze.py` function `run_cross_validation(model, X, y, k=5)` to perform **k-fold cross-validation** (standard, not stratified, as target is continuous) on CPU-only hardware. **Methodology**: Use standard k-fold cross-validation (k=5) as stratification is inappropriate for continuous targets. **Configuration**: Use `k=5` as default (configurable). **Strategy**: Compute R² and RMSE for each fold. **Requirement**: If mean R² < 0.30, write the exact string "Weak predictive power (R² < 0.30), consistent with null hypothesis." to the JSON key `r2_interpretation` in `results/model_performance.json`. **Dependencies**: [T022]
- [ ] T024 [US3] Implement `code/analyze.py` function `aggregate_cv_results(cv_results)` to aggregate CV results (mean ± std dev) and save to `results/model_performance.json`. **State Update**: Immediately update `state/projects/PROJ-360-quantifying-the-impact-of-network-struct.yaml` with checksum of `model_performance.json`. **Dependencies**: [T023]
- [X] T025 [US3] Implement `code/report.py` to generate `results/final_report.md`. **Mandatory**: Insert the exact "Limitations" text defined in FR-008: "This study is observational. Correlations do not imply causality. The thermal conductivity tensor was reduced to a scalar by averaging principal components, which may obscure anisotropic effects." **Action**: This text MUST be written **regardless of the state of `model_performance.json`**. **Action**: Read `r2_interpretation` from `model_performance.json` (if present); if present, append it as a **separate paragraph** immediately following the mandatory Limitations text. If the key is missing, omit the interpretation line. **Dependencies**: [T024]
- [X] T025b [US3] Implement `code/report.py` function `generate_power_analysis_section(n)` to generate the specific power analysis text for `results/final_report.md` as required by FR-010. This section must document sample-size and power considerations, including any warnings logged in `results/power_analysis.log`. **Dependencies**: [T018a] **Note**: T025b MUST run before T025 (or be integrated into T025) to ensure the report contains the power analysis section.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final reporting and mandatory limitations disclosure

- [X] T026 [US3] Ensure `code/report.py` includes the R² interpretation (from T023/T024) in the Limitations section if R² < 0.30. (Note: This is now integrated into T025 logic).
- [X] T027 [P] Run full pipeline integration test to verify end-to-end data flow from download to report generation within 6 hours on CPU-only hardware
- [ ] T028 [P] Implement `code/validate_outputs.py` to check that `metrics.csv`, `correlations.json`, `model_performance.json`, and `final_report.md` exist and contain required keys. **Required Keys**: `metrics.csv` must have `avg_degree`, `path_length`, `clustering`, `thermal_conductivity_scalar`; `correlations.json` must have `metric_name`, `pearson_coeff`, `spearman_coeff`, `p_value`, `bonferroni_adjusted_p`; `model_performance.json` must have `r2_mean`, `r2_std`, `rmse_mean`, `rmse_std`, `r2_interpretation`. **Exit**: Exit with code 0 on success. **Dependencies**: [T025, T024, T016, T013]
- [ ] T029 [P] Implement `code/runtime_monitor.py` as a **wrapper script** that invokes the main pipeline. **Requirement**: Enforce a timeout during execution. If the pipeline exceeds the configured time limit, log `ERROR: Runtime exceeds time limit` and **exit with code 1** immediately to enforce SC-005. **Success Verification**: If the pipeline completes successfully, log the actual runtime duration to `results/runtime_log.json` and verify it is < 6 hours. This satisfies SC-005 by providing a mechanism to prove the pipeline completed within the limit. **Dependencies**: [T027]
- [ ] T030 [P] Run quickstart.md validation to ensure reproducibility with pinned seeds and dependencies

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
- **T014a (Physical Descriptors)** and **T015 (Extract Thermal Conductivity)** can run in parallel relative to each other, but both depend on T013.
- **T015 (Extract Thermal Conductivity)** must complete before **T016 (Correlation Analysis)** can execute.
- **T016 (Correlation Analysis)** must complete before **T017 (Bonferroni Correction)** can execute.
- **T017 (Bonferroni Correction)** must complete before **T018a (Log Sample Size)** can execute.
- **T018a (Log Sample Size)** must complete before **T018c (Apply Significance)** can execute.
- **T013 (Compute Metrics)** must complete before **T020a (VIF Calculation)** can execute.
- **T020a (VIF Calculation)** must complete before **T021 (VIF Filtering)**.
- **T021 (VIF Filtering)** must complete before **T022 (Model Training)**.
- **T022 (Model Training)** must complete before **T023 (Cross-Validation)**.
- **T023** and **T024** must complete before **T025 (Report Generation)**.
- **T025** must execute after T024 to ensure the report contains both the mandatory boilerplate and the specific R² interpretation.
- **T020a, T020b, T020c, T020d, T021, T022, T023, T024** are strictly sequential and CANNOT be run in parallel. **US3 cannot begin until T020a is complete.**
- **T018a, T018c** are strictly sequential after T017. **Specifically: T017 -> T018a -> T018c.**
- **T016, T017, T018a, T018c** are sequential (T015 -> T016 -> T017 -> T018a -> T018c).
- **T028** must run after all data generation tasks.
- **T030** must run after T025.
- **T011, T013, T016, T021, T024** all perform immediate state updates; no separate consolidation task (T031) is needed.

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
- **NOTE**: T014a and T015 are parallel ([P]) relative to each other, but both depend on T013.
- **NOTE**: T016, T017, T018a, T018c are sequential.
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
- **Critical**: T015 must explicitly append `thermal_conductivity_scalar` to `data/processed/metrics.csv` and verify the scalarization logic with an assertion. **Recovery**: Skip material on missing metadata only; do NOT fail on calculation errors. **Dynamic Sample Size**: Subsequent tasks must use the updated `n`.
- **Critical**: T013 depends on T011 completion; T013 cannot run in parallel with T011.
- **Critical**: T029 logs runtime and fails the build (exit 1) if runtime exceeds 6 hours. **Must be a wrapper script**. **Success**: Log runtime to `results/runtime_log.json` and verify < 6h.
- **Critical**: T028 implements `code/validate_outputs.py` to validate artifacts with specific required keys.
- **Critical**: T012 must run after T011 to validate saved artifacts and is NOT parallel.
- **Critical**: US3 cannot begin until T020a is complete.
- **Critical**: T018a/c implement power analysis logging and fixed Bonferroni logic (alpha = 0.05/3).
- **Critical**: T011 must checksum both source CIFs and derived graphs and record the derivation step in `data/metadata.yaml` AND update `state/projects/...yaml` **immediately**.
- **Critical**: T020a-T024 must have distinct function entry points and output artifacts defined to allow independent execution units.
- **Critical**: T007 validates dataset-variable fit (SC-003) as part of the download flow.
- **Critical**: T014a computes physical descriptors for logging ONLY, not for regression.
- **Critical**: T020c creates `contracts/vif_schema.yaml`.
- **Critical**: T025b generates the power analysis section for the final report.
- **Critical**: T016 must run after T015.
- **Critical**: T014a and T015 are parallel relative to each other, but both depend on T013.
- **Critical**: T012 must run after T011.
- **Critical**: T015 must run after T013.
- **Critical**: T023 uses standard k-fold cross-validation (not stratified) for continuous target variable.
- **Critical**: T011, T013, T016, T021, T024 all perform immediate state updates; no separate consolidation task (T031) is needed.
- **Critical**: Physical descriptors (T014a) are for diagnostic logging only and excluded from regression; this limitation is documented in the final report.
- **Critical**: If all features are excluded in T021, generate a report stating "No valid features for regression" instead of halting the pipeline.
- **Critical**: Bonferroni alpha threshold remains fixed at 0.05/3 regardless of sample size; power limitations are documented in the report.
- **Critical**: T018c explicitly depends on T018a as defined in its `Dependencies` field and the execution order section.
