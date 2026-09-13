---
description: "Task list template for feature implementation"
---

# Tasks: Predicting Avian Foraging Guilds from Public eBird Data and Land Cover Maps

**Input**: Design documents from `/specs/001-avian-foraging-land-cover/`  
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

- [ ] T001 Initialize Project Directory Structure: Create directories `projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/data/`, `models/`, `viz/`, `notebooks/`, `utils/`, and `tests/` using `mkdir -p` and create a `.gitkeep` file inside each using `touch`.

- [ ] T002 Create placeholder files `README.md` and `run_pipeline.sh` in `projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/`.

- [ ] T003 [P] Create `requirements.txt` in `projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/` with pinned dependencies: `pandas`, `numpy`, `scikit-learn`, `geopandas`, `rasterio`, `requests`, `matplotlib`, `seaborn`, `pyyaml`, `jupyter`, `s3fs`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Implement `utils/config.py` to define paths, random seeds, and constants.
- [ ] T005 [P] Implement `utils/provenance.py` to generate SHA-256 hashes for all data artifacts and write them to `data/metadata.yaml`. This task must also include a function to record source URLs, versions, and extraction dates for all external datasets to satisfy Constitution Principle VI (Habitat Data Provenance).
- [X] T006a [Depends on T004, T005] Create `tests/test_data_contract.py` with a failing `test_schema_compliance` function stub that asserts `False` and verify `pytest` returns exit code 1.
- [ ] T006b [P] [Depends on T004, T005] Create `tests/test_metrics.py` with a failing `test_metrics_calc` function stub that asserts `False` and verify `pytest` returns exit code 1.
- [ ] T007.5a [Depends on T004, T005] Create `run_pipeline.sh` orchestration script skeleton in `projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/` with placeholder steps for each pipeline phase.
- [ ] T007.5b [Depends on T036, T037, T038, T039, T040, T041, T042, T043, T044, T045] Implement full `run_pipeline.sh` to orchestrate all data, model, and viz steps in dependency order. The script MUST: (1) execute `code/data/download_ebd.py` (T036); (2) execute `code/data/download_nlcd.py` (T037); (3) execute `code/data/select_top_species.py` (T038); (4) execute `code/data/merge_and_buffer.py` (T039); (5) execute `code/data/aggregate.py` (T040); (6) execute `code/models/train.py` (T041); (7) execute `code/models/evaluate.py` (T042); (8) execute `code/viz/plot_confusion.py` (T043); (9) execute `code/viz/plot_importance.py` (T044); and (10) execute `code/viz/map_habitat.py` (T045). It MUST implement error handling (stop on first failure), log each step's exit code, and return a non‑zero exit code if any step fails. **Note**: This script does NOT depend on fallback tasks; it relies on T036 and T037 raising on failure to satisfy Constitution Principle VI.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Extraction and Merging Pipeline (Priority: P1) 🎯 MVP

**Goal**: Extract eBird EBD records for top species, merge with NLCD land cover data within 100 m buffers, and filter for statistical power (≥ 50 obs/species).

**Independent Test**: Verify that the top species are selected, species with < 50 observations are excluded, and the output CSV contains complete land‑cover proportions and assigned foraging guilds.

### Implementation for User Story 1

- [ ] T036 [US1] [P] Implement `data/download_ebd.py` to list the S3 bucket `s3://ebird-data/ebd_release/`, sort files by `last_modified` descending, select the first `.parquet` file, download it to `data/raw/ebd_train.parquet`, and generate checksums in `data/metadata.yaml`. The script MUST raise `FileNotFoundError` on failure and **must not** provide a fallback.
- [ ] T037 [US1] [P] Implement `data/download_nlcd.py` to fetch NLCD 2019 land‑cover data from the USGS EarthExplorer API, download tiles to `data/raw/nlcd_2019.zip`, and record version/date in `data/metadata.yaml`. On failure the script MUST raise `FileNotFoundError` (no fallback).
- [ ] T008a [US1] [P] Implement `data/download_guild_source.py` to fetch a pre‑compiled CSV of foraging‑guild labels from a verified static URL (recorded in `data/metadata.yaml`). Save to `data/raw/guild_source.csv` and verify a `source_citation` column is present.
- [ ] T008b [US1] [Depends on T008a] Implement `data/generate_guild_mapping.py` to read `data/raw/guild_source.csv` and write `data/processed/guild_mapping.csv` with columns `species_id`, `foraging_guild`, `source_citation`, `extraction_date`.
- [ ] T012.5a [US1] [P] Implement `data/load_and_count.py` to read `data/raw/ebd_train.parquet` and write per‑species record counts to `data/processed/species_counts.json`.
- [ ] T012.5b [US1] [P] Implement `data/select_top_species.py` to read `species_counts.json`, sort descending, select the top 25 species (deterministic tie‑break by alphabetical `species_id`), and write `data/processed/top_25_species_ids.json`.
- [ ] T012.5c [US1] Implement `data/filter_and_log.py` to load `top_25_species_ids.json` and the raw EBD, keep only selected species, enforce the ≥ 50‑observation rule, log exclusions to `data/processed/selection_log.txt`, and write `data/processed/filtered_ebd.csv`.
- [ ] T039 [US1] [Depends on T012.5c, T037, T008b] Implement `data/merge_and_buffer.py` to (1) read `filtered_ebd.csv`, (2) read NLCD raster(s) from `nlcd_2019.zip`, (3) compute 100 m buffer land‑cover proportions for each observation (output columns `forest_prop_100m`, `grassland_prop_100m`, `wetland_prop_100m`, `urban_prop_100m`, `other_prop_100m`), (4) join with `guild_mapping.csv` to assign `foraging_guild`, and (5) write `data/processed/merged_observations.csv` with full provenance metadata.
- [ ] T015 [US1] Add a `validate_schema()` function inside `data/merge_and_buffer.py` that raises `ValueError` if required columns are missing, and add a unit test `test_validate_schema` in `tests/test_data_contract.py`.
- [ ] T010 [US1] Add a test in `tests/test_data_contract.py` that asserts `merged_observations.csv` conforms to `contracts/dataset.schema.yaml` (columns `species_id`, `foraging_guild`, and the individual land‑cover proportion columns).
- [ ] T040 [US1] Implement `data/aggregate.py` to collapse `merged_observations.csv` to species‑level profiles (`species_profiles.csv`) by averaging land‑cover proportions, logging any dropped rows with structured `reason_code`/`details`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Classification Model Training and Evaluation (Priority: P2)

**Goal**: Train a Random Forest classifier to predict foraging guild from land‑cover proportions and validate signal via a **Stratified Permutation Test (stratified by species)**.

**Independent Test**: Verify balanced accuracy vs. chance, per‑class F1 scores, and that the permutation test yields *p* < 0.05.

### Implementation for User Story 2

- [ ] T041 [US2] Implement `models/train.py` to load `species_profiles.csv`, standardize predictors, encode `foraging_guild`, perform *k*‑fold cross-validation with a fixed `random_state`, train a `RandomForestClassifier`, save the fitted model to `data/models/random_forest.pkl` and training metrics to `data/models/training_metrics.json`.
- [ ] T042 [US2] Implement `models/evaluate.py` to (1) load the trained model and metrics, (2) compute balanced accuracy and per‑class F1, (3) run the **Stratified Permutation Test (stratified by species)** as required by FR‑005/FR‑008 (shuffle guild labels **within each species**), (4) compare observed accuracy to the null distribution, save results (`p_value`, metrics) to `data/models/evaluation_results.json`. The script must include logging of seeds and the α = 0.05 threshold.
- [ ] T021 [US2] Add detailed logging in `models/evaluate.py` (p‑value, seed, metrics, pass/fail flag).
- [ ] T023 [US2] Implement an integration test `tests/test_integration.py` that runs `models/train.py` then `models/evaluate.py` and checks that both output files exist and contain valid JSON.
- [ ] T018 [US2] Add unit tests in `tests/test_metrics.py` for balanced accuracy and F1 calculations (use a tiny synthetic dataset with known outcomes).

**Checkpoint**: User Stories 1 & 2 should both work independently

---

## Phase 5: User Story 3 - Visualization and Feature Importance Reporting (Priority: P3)

**Goal**: Produce a confusion matrix, feature‑importance bar chart, spatial habitat maps for the top species, and a summary report of top land‑cover predictors per foraging guild.

**Independent Test**: Verify that the three visual files exist for the deterministic set of focal species and that the importance report lists the top predictors per guild.

### Implementation for User Story 3

- [ ] T043 [US3] Implement `viz/plot_confusion.py` to load predictions/true labels from `evaluation_results.json`, generate a confusion‑matrix PNG (`docs/results/confusion_matrix.png`) and accompanying metadata JSON (`confusion_matrix_metadata.json`) that records the species list used.
- [ ] T044 [US3] Implement `viz/plot_importance.py` to extract feature‑importance scores from the trained Random Forest, plot a bar chart (`docs/results/feature_importance.png`), and write a JSON file with the raw importance values.
- [ ] T045 [US3] Implement `viz/map_habitat.py` to (A) rasterize model predictions over a high‑resolution grid, (B) for each species in `top_25_species_ids.json` generate a PNG map (`docs/results/habitat_map_{species_id}.png`) and a consolidated GeoJSON (`docs/results/habitat_map.geojson`), ensuring the grid does not extrapolate beyond observed coordinates.
- [ ] T028 [US3] Implement `viz/plot_importance.py` to write a markdown summary report `docs/results/feature_importance_report.md` that lists, for each foraging guild, the top land‑cover predictors (by mean decrease impurity) with their importance scores.
- [ ] T028.5 [US3] Implement `viz/validate_importance.py` to perform a qualitative cross-reference between the model‑identified top predictors and habitat descriptors from literature sources recorded in `data/metadata.yaml`. Produce a comparative table in `feature_importance_report.md` with a free‑form ecological‑validity note.
- [ ] T029 Update `notebooks/01_analysis.ipynb` to orchestrate the full pipeline, load all intermediate artifacts, and serve as the Single Source of Truth for results and figures.

**Checkpoint**: All three user stories should now be independently functional

---

## Phase N: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T030 [P] Documentation updates in `docs/` (add `quickstart.md` with Installation, Data Download, and Running the Pipeline sections).
- [ ] T031 [P] Refactor `merge_and_buffer.py` to keep cyclomatic complexity < 10 (focus on `calculate_buffer_proportions` and `merge_land_cover` functions).
- [ ] T032 [SC-004] Profile `merge_and_buffer.py` and optimise buffer calculations via vectorisation; verify total runtime < 6 h.
- [ ] T033 [P] Add unit tests for `utils/config.py` and `utils/provenance.py` in `tests/unit/`.
- [ ] T034 [P] Execute the commands in `docs/quickstart.md` in a fresh virtual environment and assert that all expected artifacts are produced.
- [ ] T035 [SC-004] [FR-002] Implement `utils/measure_pipeline.py` to wrap `run_pipeline.sh`, record total wall‑clock time (< 6 h) and peak memory usage (< 7 GB) using `psutil`, and write a JSON summary `pipeline_performance.json`. This task belongs in the Polish phase because it measures the whole pipeline (depends on T007.5b).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)** – no dependencies; can start immediately.  
- **Foundational (Phase 2)** – depends on Setup; blocks all user‑story work.  
- **User Stories (Phases 3‑5)** – depend on Foundational; can run in parallel once Phase 2 is complete.  
- **Polish (Phase N)** – depends on completion of the desired user stories.

### User‑Story Dependencies

- **US 1 (P1)** – starts after Foundational; no cross‑story dependencies.  
- **US 2 (P2)** – starts after Foundational; requires the aggregated dataset from US 1 (`species_profiles.csv`).  
- **US 3 (P3)** – starts after Foundational; requires the trained model and evaluation results from US 2.

### Within Each User Story

- Write failing tests **before** implementation.  
- Data‑download tasks (T036, T037) → species‑selection tasks (T012.5a‑c) → merging (T039) → aggregation (T040) → training (T041) → evaluation (T042) → visualisation (T043‑T045, T028, T028.5).  
- All dependent tasks list their prerequisites explicitly.

### Parallel Opportunities

- All `[P]` tasks within a phase can run concurrently.  
- Different user stories can be worked on simultaneously by separate developers once the foundational layer is ready.  
- All tests for a user story marked `[P]` can run in parallel.
- Models within a story marked `[P]` can run in parallel.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 (Setup).  
2. Complete Phase 2 (Foundational).  
3. Complete Phase 3 (User Story 1).  
4. **STOP & VALIDATE**: run the independent test for US 1.  
5. Deploy/Demo if ready.

### Incremental Delivery

1. Setup + Foundational → foundation ready.  
2. Add US 1 → test → demo (MVP).  
3. Add US 2 → test → demo.  
4. Add US 3 → test → demo.  
5. Polish (Phase N) – documentation, performance checks, extra tests.

### Parallel Team Strategy

- **Team A** finishes Setup + Foundational.  
- **Team B** works on US 1.  
- **Team C** works on US 2 (once US 1 data exists).  
- **Team D** works on US 3 (once the model from US 2 is available).

---

## Notes & Critical Constraints

- All data‑download tasks must use **real, reachable URLs** (eBird S3 bucket, USGS EarthExplorer). No synthetic fallbacks are permitted.  
- All computations must be **CPU‑only**; scikit-learn’s default implementations satisfy this.  
- The **Stratified Permutation Test (stratified by species)** is mandatory (see T042). The previously mentioned “Across-Species Permutation” must be ignored.  
- Exactly **25 species** must be selected; ties at rank 25 are resolved alphabetically (deterministic).  
- `merge_and_buffer.py` must output **individual land‑cover proportion columns** (not a single aggregated column) to satisfy schema validation.  
- `run_pipeline.sh` (T007.5b) must **fail loudly** if any step raises; no silent fallbacks.  
- `utils/measure_pipeline.py` (T035) must enforce the **< 6 h runtime** and **< 7 GB peak memory** limits.  
- All provenance metadata (source URLs, versions, extraction dates) must be recorded in `data/metadata.yaml` and carried forward into output files to satisfy Constitution Principle VI.

---
- [ ] T050 [P] [US1] Add a task to verify the download of the EBD file by checking its size against a known expected value.
- [ ] T051 [P] [US1] Implement a data quality check in `data/filter_and_log.py` to identify and log any missing or invalid coordinate values (latitude/longitude) in the EBD data.
- [ ] T052 [US1] Implement a unit test for the `merge_and_buffer.py` script to verify that the land cover proportions sum to 1 for each observation.
- [ ] T053 [US2] [P] Add a task to perform hyperparameter tuning for the Random Forest classifier using cross-validation and a grid search to optimize performance.
- [ ] T054 [US2] Implement a test to verify that the stratified permutation test is correctly implemented by comparing its results to a known baseline or a simplified simulation.
- [ ] T055 [US3] [P] Implement a task to generate a map showing the spatial distribution of the top species by observation count, highlighting areas with high foraging habitat suitability.
- [ ] T056 [US3] Implement a task to create an interactive dashboard that allows users to explore the feature importance rankings and visualize the relationship between land cover types and foraging guilds.
