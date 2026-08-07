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

- [X] T007 [US1] **Sequential**: Download ≥50 CIF files from Materials Project API, verify data integrity, and immutably snapshot them into `data/raw/cif/`. **Implementation**: Query the API for materials with thermal conductivity data. Verify each downloaded file's checksum against an expected value. **Output**: Immediately after download, write a snapshot record to `data/metadata.yaml` including the download timestamp and list of material IDs to satisfy Constitution Principle VII (Data Provenance).
- [ ] T008 [US1] **Sequential**: Save downloaded CIF files to `data/raw/cif/` and compute their SHA-256 checksums. **Dependencies**: [T007]. <!-- FAILED: unspecified -->
- [X] T009 [US1] **Sequential**: Implement `code/construct_network.py` to parse CIF files using `pymatgen`, detect bonds via covalent radius summation with a tolerance threshold, and create `networkx.Graph` objects. **Fallback**: If no bonds found, attempt distance cutoffs of increasing magnitude sequentially. **Dependencies**: [T008].
- [X] T010 [US1] Implement fallback bond detection in `code/construct_network.py` (progressive distance cutoffs) for disconnected graphs; log and skip materials with no edges after fallbacks. **Dependencies**: [T009].
- [ ] T011 [US1] Save constructed `networkx.Graph` objects to `data/processed/networks/` (pickle format). **Checksum Generation**: Compute SHA-256 checksums for the source CIF files and the derived graph objects. Write these checksums to a new artifact `data/processed/checksums.json` with the structure: `{ "source_cifs": {...}, "derived_graphs": {...}, "derivation": "CIF -> Network via covalent radii + fallback" }`. **Dependencies**: [T010].
- [X] T012 [US1] Implement validation in `code/validate_graphs.py` to ensure every graph has ≥2 nodes and ≥1 edge, or is explicitly skipped with a log entry. **Dependencies**: [T011].

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Compute Network Metrics and Correlate with Thermal Conductivity (Priority: P2)

**Goal**: Compute ≥3 network metrics per material and perform correlation analysis with thermal conductivity.

**Independent Test**: Verify `data/processed/metrics.csv` contains ≥3 metrics per material and `results/correlations.json` contains Pearson/Spearman coefficients with Bonferroni-corrected p-values.

### Implementation for User Story 2

- [X] T013 [US2] Implement `code/compute_metrics.py` to compute average degree, average shortest path length (on LCC), and clustering coefficient for each graph in `data/processed/networks/`. **Output**: Save results to `data/processed/metrics.csv` with columns `[material_id, average_degree, average_path_length, clustering_coefficient, unit_cell_volume, total_atom_count, mean_atomic_mass, thermal_conductivity_scalar]`. **Dependencies**: [T011].
- [X] T014a [US2] Implement `code/compute_metrics.py` function `compute_physical_descriptors(cif_path)` to calculate Unit Cell Volume, Total Atom Count, and Mean Atomic Mass for each material. **Output**: Append these columns (`unit_cell_volume`, `total_atom_count`, `mean_atomic_mass`) to `data/processed/metrics.csv`.
- [X] T014b [US2] Append the computed physical descriptors from T014a to `data/processed/metrics.csv`. **Dependencies**: [T013, T014a].
- [X] T014c [US2] Compute checksums for both `data/processed/metrics.csv` and write them into the `checksums.json` file.
- [X] T015 [US2] Implement extraction of thermal conductivity scalar from CIF metadata (via pymatgen) and append column `thermal_conductivity_scalar` to `data/processed/metrics.csv`. **Dependencies**: [T014b].
- [ ] T016a [US2] Compute Pearson and Spearman correlations between each network metric and thermal conductivity, storing results in temporary files before writing final data.
- [ ] T016b [US2] Save the correlation results to `results/correlations.json`. **Dependencies**: [T015, T016a].
- [ ] T016c [US2] Update `data/processed/checksums.json` with the checksum for `results/correlations.json`. **Dependencies**: [T016b].
- [ ] T017 [US2] Implement Bonferroni correction for the correlation tests to control family-wise error rate. Calculate alpha dynamically as `0.05 / 3` (fixed denominator for the 3 planned metric-conductivity pairs), regardless of missing data or dropped features, to strictly control Type I error as per Spec FR-005 and SC-004.
- [ ] T018a [US2] Log sample size and a warning if n < 50. **Dependencies**: [T017].
- [ ] T018b [US2] Verify that at least 50 materials remain after filtering in previous steps and log the final count. **Dependencies**: [T012, T015].

**Checkpoint**: At this point, User Story 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Train Predictive Model and Validate Performance (Priority: P3)

**Goal**: Train a linear regression model using VIF-filtered network metrics AND physical descriptors, and validate via k-fold cross-validation.

**Independent Test**: Verify `models/thermal_predictor.pkl` exists, and `results/model_performance.json` contains R² and RMSE for multiple folds with mean ± std deviation.

### Implementation for User Story 3

- [ ] T020a [US3] Calculate VIF for all candidate features (network metrics AND physical descriptors).
- [ ] T020b [US3] Write the filtered feature set to `data/processed/filtered_features.csv`. **Dependencies**: [T020a].
- [ ] T020c [US3] Log VIF values and update checksums for filtered features. **Dependencies**: [T020b].
- [ ] T022 [US3] Train a linear regression model using the features from `data/processed/filtered_features.csv` and save it to `models/thermal_predictor.pkl`. **Dependencies**: [T020b].
- [ ] T023 [US3] Perform stratified k-fold cross-validation (k=5) on CPU-only hardware. **Implementation**: Bin the continuous thermal conductivity target into quantiles to enable stratification. Compute R² and RMSE for each fold.
- [ ] T024 [US3] Aggregate the CV results (mean ± std dev) and save them to `results/model_performance.json`. **Dependencies**: [T023].
- [ ] T025a [US3] Read performance data from `results/model_performance.json`.
- [ ] T025b [US3] Generate the final report content. **Implementation**: Unconditionally insert the mandatory "Limitations" text: "This study is observational. Correlations do not imply causality. The thermal conductivity tensor was reduced to a scalar by averaging principal components, which may obscure anisotropic effects." Append the R² interpretation if performance data is available. **Dependencies**: [T024, T025a].
- [ ] T025c [US3] Write the generated report to `results/final_report.md`. **Dependencies**: [T025b].

