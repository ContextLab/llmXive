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

 Tasks MUST be organized by user story so each story can be:
 - Implemented independently
 - Tested independently
 - Delivered as an MVP increment

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
- [X] T004b [P] Setup environment configuration management for API keys and random seeds
- [X] T006 Create `data/metadata.yaml` schema for snapshot timestamp and material IDs

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Download and Construct Atomic Networks from Materials Project (Priority: P1) 🎯 MVP

**Goal**: Download ≥50 CIF files from Materials Project and construct atomic network graphs using covalent radii.

**Independent Test**: Verify ≥50 CIF files exist in `data/raw/cif/` and ≥50 valid graph objects exist in `data/processed/networks/` with correct node/edge counts.

### Implementation for User Story 1

- [X] T007 [US1] Implement `code/download.py` to query Materials Project API for materials with thermal conductivity, handling rate-limiting (HTTP client error) and server errors with 3 retries (1s, 2s, 4s backoff)
- [X] T008 [US1] Implement `code/download.py` logic to fetch and save ≥50 CIF files to `data/raw/cif/` within 30 minutes, skipping materials missing thermal conductivity data
- [X] T009 [P] [US1] Implement `code/construct_network.py` to parse CIF files using `pymatgen`, detect bonds via covalent radius summation with an empirically determined tolerance threshold, and create `networkx.Graph` objects
- [X] T010 [US1] Implement fallback bond detection in `code/construct_network.py` (progressive distance cutoffs) for disconnected graphs; log and skip materials with no edges after fallbacks
- [X] T011 [US1] Save constructed `networkx.Graph` objects to `data/processed/networks/` (pickle format) and generate `data/processed/network_manifest.json`
- [X] T012 [P] [US1] Implement validation in `code/construct_network.py` to ensure every graph has ≥2 nodes and ≥1 edge, or is explicitly skipped with a log entry

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Compute Network Metrics and Correlate with Thermal Conductivity (Priority: P2)

**Goal**: Compute ≥3 network metrics per material and perform correlation analysis with thermal conductivity.

**Independent Test**: Verify `data/processed/metrics.csv` contains ≥3 metrics per material and `results/correlations.json` contains Pearson/Spearman coefficients with Bonferroni-corrected p-values.

### Implementation for User Story 2

- [X] T013 [P] [US2] Implement `code/compute_metrics.py` to calculate average degree, average shortest path length (on LCC), and clustering coefficient for each graph in `data/processed/networks/`
- [X] T014 [US2] Implement logic in `code/compute_metrics.py` to handle disconnected graphs (report NaN for path length) and compute network density as a diagnostic only
- [ ] T015 [US2] Implement extraction of thermal conductivity scalar ($\frac{k_x + k_y + k_z}{3}$) for `data/processed/metrics.csv` (Network metrics only per FR-003) <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->
- [ ] T015b [US2] Implement extraction of physical descriptors (columns: `unit_cell_volume`, `total_atom_count`, `mean_atomic_mass`) for `data/processed/metrics.csv`. **Action**: Append these columns to the existing CSV with a header comment `# DIAGNOSTICS: Physical descriptors excluded from regression features` to distinguish them from primary features. <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested -->
- [ ] T016 [P] [US2] Implement `code/analyze.py` to compute Pearson and Spearman correlations between each **network metric** (average degree, path length, clustering) and thermal conductivity, storing results in `results/correlations.json`. Do NOT include physical descriptors in this analysis.
- [ ] T017 [US2] Implement Bonferroni correction in `code/analyze.py` for the 3 correlation tests to control family-wise error rate at α ≤ 0.05
- [ ] T018 [US2] Implement power analysis logging in `code/analyze.py` to record warnings if $n < 50$ in `results/power_analysis.log`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Train Predictive Model and Validate Performance (Priority: P3)

**Goal**: Train a linear regression model using VIF-filtered metrics and validate via k-fold cross-validation.

**Independent Test**: Verify `models/thermal_predictor.pkl` exists, and `results/model_performance.json` contains R² and RMSE for multiple folds with mean ± std deviation.

### Implementation for User Story 3

- [ ] T020 [US3] Implement `code/analyze.py` to calculate Variance Inflation Factor (VIF) for network metrics using `statsmodels` OLS. **Input**: `data/processed/metrics.csv`. **Output**: VIF values for each network metric.
- [~] T021 [US3] Implement `code/analyze.py` to filter features: **MUST exclude any feature with VIF ≥ 5**. **Action**: Log every excluded feature and its VIF value to `results/power_analysis.log`. **Output**: Generate a new artifact `data/processed/filtered_features.csv` containing ONLY the columns for features with VIF < 5. This artifact MUST be used as input for T022.
- [~] T022 [US3] Implement `code/analyze.py` to train a `scikit-learn` Linear Regression model using **ONLY** the features listed in `data/processed/filtered_features.csv` from T021. Save the model to `models/thermal_predictor.pkl`. <!-- FAILED: unspecified -->
- [~] T023 [US3] Implement k-fold cross-validation in `code/analyze.py` on CPU-only hardware. **Stratification Strategy**: Bin thermal conductivity values into 5 quantile-based strata and use `StratifiedKFold(n_splits=5)`. Compute R² and RMSE for each fold. **Requirement**: If mean R² < 0.30, write the exact string "Weak predictive power (R² < 0.30), consistent with null hypothesis." to the JSON key `r2_interpretation` in `results/model_performance.json`.
- [~] T024 [US3] Aggregate CV results (mean ± std dev) and save to `results/model_performance.json`.
- [~] T025 [US3] Implement `code/report.py` to generate `results/final_report.md`. **Mandatory**: Insert the exact "Limitations" text defined in FR-008: "This study is observational. Correlations do not imply causality. The thermal conductivity tensor was reduced to a scalar by averaging principal components, which may obscure anisotropic effects." **Action**: Read `r2_interpretation` from `model_performance.json` (if present); if present, append it as a **separate paragraph** immediately following the mandatory Limitations text. If the key is missing, omit the interpretation line.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final reporting and mandatory limitations disclosure

- [~] T026 [US3] Ensure `code/report.py` includes the R² interpretation (from T023/T024) in the Limitations section if R² < 0.30. (Note: This is now integrated into T025 logic).
- [~] T027 [P] Run full pipeline integration test to verify end-to-end data flow from download to report generation within 6 hours on CPU-only hardware <!-- FAILED: unspecified -->
- [~] T028 [P] Validate all output artifacts (`metrics.csv`, `correlations.json`, `model_performance.json`, `final_report.md`) against `spec.md` requirements
- [~] T029 [P] Implement `code/analyze.py` (or a wrapper script) to instrument and measure the total pipeline runtime. Log the elapsed time to `results/runtime.log` and assert it is < 6 hours to verify compliance with SC-005.
- [~] T030 [P] Run quickstart.md validation to ensure reproducibility with pinned seeds and dependencies

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

- **T020 (VIF Calculation)** must complete before **T021 (VIF Filtering)**.
- **T021 (VIF Filtering)** must complete before **T022 (Model Training)**.
- **T022 (Model Training)** must complete before **T023 (Cross-Validation)**.
- **T023** and **T024** must complete before **T025 (Report Generation)**.
- **T025** must execute after T024 to ensure the report contains both the mandatory boilerplate and the specific R² interpretation.
- **T020, T021, T022, T023, T024** are strictly sequential and CANNOT be run in parallel.

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
- **NOTE**: T020, T021, T022, T023, T024 are strictly sequential and CANNOT be run in parallel. T013, T014, T015, T015b, T016, T017, T018 can run in parallel within US2.

---

## Parallel Example: User Story 1

```bash
# Launch all parallel tasks for User Story 1:
Task: "Implement `code/download.py` to query Materials Project API..."
Task: "Implement `code/construct_network.py` to parse CIF files..."
Task: "Implement validation in `code/construct_network.py`..."
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
 - Developer C: User Story 3 (Note: T020-T024 must be sequential)
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
- **Critical**: T020 -> T021 -> T022 -> T023 -> T024 is a strict sequential chain. Do not mark these as [P].
- **Critical**: T016 must NOT include physical descriptors. Only network metrics and thermal conductivity scalar.
- **Critical**: T021 must log excluded features to `results/power_analysis.log` and produce `data/processed/filtered_features.csv`.
- **Critical**: T025 must include both the mandatory "Limitations" text and the R² interpretation (if applicable) as a separate paragraph.
- **Critical**: T015b computes physical descriptors as diagnostics only, not primary features.