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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Initialize Project Directory Structure: Create directories `projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/data/`, `models/`, `viz/`, `notebooks/`, `utils/`, and `tests/` using `mkdir -p` and create a `.gitkeep` file inside each using `touch`.

- [ ] T002 Create placeholder files `README.md` and `run_pipeline.sh` in `projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/`.

- [ ] T003 [P] Create `requirements.txt` in `projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/` with pinned dependencies: `pandas`, `numpy`, `scikit-learn`, `geopandas`, `rasterio`, `requests`, `matplotlib`, `seaborn`, `pyyaml`, `jupyter`, `s3fs`.

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

- [ ] T004 Implement `utils/config.py` to define paths, random seeds, and constants.
- [ ] T005 [P] Implement `utils/provenance.py` to generate SHA-256 hashes for all data artifacts and write them to `data/metadata.yaml`. This task must also include a function to record source URLs, versions, and extraction dates for all external datasets to satisfy Constitution Principle VI (Habitat Data Provenance).
- [X] T006a [Depends on T004, T005] Create `tests/test_data_contract.py` with a failing `test_schema_compliance` function stub that asserts `False` and verify `pytest` returns exit code 1.
- [ ] T006b [P] [Depends on T004, T005] Create `tests/test_metrics.py` with a failing `test_metrics_calc` function stub that asserts `False` and verify `pytest` returns exit code 1.
- [ ] T007.5a [Depends on T004, T005] Create `run_pipeline.sh` orchestration script skeleton in `projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/` with placeholder steps for each pipeline phase.
- [ ] T007.5b_skel Create skeleton of `run_pipeline.sh` with step placeholders and error‑handling structure.
- [ ] T007.5b_impl Implement full `run_pipeline.sh` to orchestrate all data, model, and viz steps in dependency order. The script MUST: (1) execute `code/data/download_ebd.py` (T036); (2) execute `code/data/download_nlcd.py` (T037); (3) execute `code/data/select_top_species.py` (T038); (4) execute `code/data/merge_and_buffer.py` (T039); (5) execute `code/data/aggregate.py` (T040); (6) execute `code/models/train.py` (T041); (7) execute `code/models/evaluate.py` (T042); (8) execute `code/viz/plot_confusion.py` (T043); (9) execute `code/viz/plot_importance.py` (T044); and (10) execute `code/viz/map_habitat.py` (T045). It MUST implement error handling (stop on first failure), log each step's exit code, and return a non‑zero exit code if any step fails.

## Phase 3: User Story 1 - Data Extraction and Merging Pipeline (Priority: P1) 🎯 MVP

**Goal**: Extract eBird EBD records for top species, merge with NLCD land cover data within multiple buffers, and filter for statistical power (≥ 50 obs/species).

### Implementation for User Story 1

- [ ] T036 [US1] [P] Implement `data/download_ebd.py` to attempt download of the latest EBD parquet from `s3://ebird-data/ebd_release/`. If the download fails, automatically fall back to a verified subset stored at `s3://ebird-data/ebd_subset/ebd_subset.parquet`. Save the file to `data/raw/ebd_train.parquet` and generate checksums in `data/metadata.yaml`. The script MUST raise `FileNotFoundError` only after both attempts fail.
- [ ] T037 [US1] [P] Implement `data/download_nlcd.py` to fetch NLCD 2019 land‑cover data from the USGS EarthExplorer API, download tiles to `data/raw/nlcd_2019.zip`, and record version/date in `data/metadata.yaml`. On failure the script MUST raise `FileNotFoundError` (no fallback).
- [ ] T008a [US1] [P] Implement `data/download_guild_source.py` to fetch a pre‑compiled CSV of foraging‑guild labels from a verified static URL (recorded in `data/metadata.yaml`). Save to `data/raw/guild_source.csv` and verify a `source_citation` column is present.
- [ ] T008b [US1] [Depends on T008a] Implement `data/generate_guild_mapping.py` to read `data/raw/guild_source.csv` and write `data/processed/guild_mapping.csv` with columns `species_id`, `foraging_guild`, `source_citation`, `extraction_date`.
- [ ] T012.5a [US1] [P] Implement `data/load_and_count.py` to read `data/raw/ebd_train.parquet` and write per‑species record counts to `data/processed/species_counts.json`.
- [ ] T012.5b [US1] [P] Implement `data/select_top_species.py` to read `species_counts.json`, sort descending, select a representative set of top species (deterministic tie‑break by alphabetical `species_id`), and write `data/processed/top_25_species_ids.json`.
- [ ] T012.5c [US1] Implement `data/preprocess.py` to load `top_25_species_ids.json` and the raw EBD, keep only selected species, enforce the ≥ 50‑observation rule, log exclusions to `data/processed/selection_log.txt`, and write `data/processed/filtered_ebd.csv`. This replaces the previous `filter_and_log.py` to match the plan's design document.
- [ ] T039 [US1] [Depends on T012.5c, T037, T008b] Implement `data/merge_and_buffer.py` to (1) read `filtered_ebd.csv`, (2) read NLCD raster(s) from `nlcd_2019.zip`, (3) compute land‑cover proportions for **multiple buffer radii** (e.g., 50 m, 100 m, 200 m) for each observation, creating columns such as `forest_prop_50m`, `forest_prop_100m`, `forest_prop_200m`, etc., (4) join with `guild_mapping.csv` to assign `foraging_guild`, and (5) write `data/processed/merged_observations.csv` with full provenance metadata.
- [ ] T015 Add a `validate_schema()` function inside `data/merge_and_buffer.py` that raises `ValueError` if required columns are missing, and add a unit test `test_validate_schema` in `tests/test_data_contract.py`.
- [ ] T010 Add a test in `tests/test_data_contract.py` that asserts `merged_observations.csv` conforms to `contracts/dataset.schema.yaml` (columns `species_id`, `foraging_guild`, and all land‑cover proportion columns for each buffer radius).
- [ ] T040 Implement `data/aggregate.py` to collapse `merged_observations.csv` to species‑level profiles (`species_profiles.csv`) by averaging land‑cover proportions across all radii, logging any dropped rows with structured `reason_code`/`details`.

## Phase 4: User Story 2 - Classification Model Training and Evaluation (Priority: P2)

**Goal**: Train a Random Forest classifier to predict foraging guild from land‑cover proportions and validate signal via an **Across‑Species Permutation Test** (shuffling guild labels between species).

### Implementation for User Story 2

- [ ] T041 [US2] Implement `models/train.py` to load `species_profiles.csv`, standardize predictors, encode `foraging_guild`, perform *k*‑fold cross‑validation with a fixed `random_state`, train a `RandomForestClassifier`, save the fitted model to `data/models/random_forest.pkl` and training metrics to `data/models/training_metrics.json`.
- [ ] T042 [US2] Implement `models/evaluate.py` to (1) load the trained model and metrics, (2) compute balanced accuracy and per‑class F1, (3) run an **Across‑Species Permutation Test**: randomly permute the `foraging_guild` labels **across species** while preserving the species‑level structure, repeat for a sufficient number of iterations (e.g., 1 000), (4) compare observed accuracy to the null distribution, calculate a p‑value, and save results (`p_value`, metrics) to `data/models/evaluation_results.json`. The script must log seeds, the α = 0.05 threshold, and a pass/fail flag.
- [ ] T021 Add detailed logging in `models/evaluate.py` (p‑value, seed, metrics, pass/fail flag).
- [ ] T023 Implement an integration test `tests/test_integration.py` that runs `models/train.py` then `models/evaluate.py` and checks that both output files exist and contain valid JSON.
- [ ] T018 Add unit tests in `tests/test_metrics.py` for balanced accuracy and F1 calculations (use a tiny synthetic dataset with known outcomes).

## Phase 5: User Story 3 - Visualization and Feature Importance Reporting (Priority: P3)

**Goal**: Produce a confusion matrix, feature‑importance bar chart, a spatial habitat map for the **top species by observation count**, and a summary report of top land‑cover predictors per foraging guild.

### Implementation for User Story 3

- [ ] T043 [US3] Implement `viz/plot_confusion.py` to load predictions/true labels from `evaluation_results.json`, generate a confusion‑matrix PNG (`docs/results/confusion_matrix.png`) and accompanying metadata JSON (`confusion_matrix_metadata.json`) that records the species list used.
- [ ] T044 [US3] Implement `viz/plot_importance.py` to extract feature‑importance scores from the trained Random Forest, plot a bar chart (`docs/results/feature_importance.png`), and write a JSON file with the raw importance values.
- [ ] T045 [US3] Implement `viz/map_habitat.py` to (A) rasterize model predictions over a high‑resolution grid, (B) for the **single top species** (identified in `top_25_species_ids.json` as the one with the highest observation count) generate a PNG map (`docs/results/habitat_map_{species_id}.png`) and a consolidated GeoJSON (`docs/results/habitat_map.geojson`), ensuring the grid does not extrapolate beyond observed coordinates.
- [ ] T028 [US3] Implement `viz/plot_importance.py` to write a markdown summary report `docs/results/feature_importance_report.md` that lists, for each foraging guild, the top land‑cover predictors (by mean decrease impurity) with their importance scores.
- [ ] T028.5 [US3] Implement `viz/validate_importance.py` to **quantitatively** assess ecological validity: compare the top‑3 model‑identified predictors for each guild against a curated literature list (provided in `data/raw/literature_predictors.csv`). Compute the proportion of matches; require ≥ 70 % agreement to pass. Write the result and a pass/fail flag to `docs/results/importance_validation.json` and include a brief note in the markdown report.
- [ ] T029 Update `notebooks/01_analysis.ipynb` to orchestrate the full pipeline, load all intermediate artifacts, and serve as the Single Source of Truth for results and figures.

## Phase N: Polish & Cross‑Cutting Concerns

- [ ] T030 [P] Documentation updates in `docs/` (add `quickstart.md` with Installation, Data Download, and Running the Pipeline sections).
- [ ] T031 [P] Refactor `merge_and_buffer.py` to keep cyclomatic complexity < 10 (focus on `calculate_buffer_proportions` and `merge_land_cover` functions).
- [ ] T032 [SC-004] Profile `merge_and_buffer.py` and optimise buffer calculations via vectorisation; verify total runtime < 6 h.
- [ ] T033 [P] Add unit tests for `utils/config.py` and `utils/provenance.py` in `tests/unit/`.
- [ ] T034 [P] Execute the commands in `docs/quickstart.md` in a fresh virtual environment and assert that all expected artifacts are produced.
- [ ] T035 [SC-004] Implement `utils/measure_pipeline.py` to wrap `run_pipeline.sh`, record total wall‑clock time and peak memory usage using `psutil`, compare the wall‑clock time to the CI job limit of 6 hours (21600 s), and write a JSON summary `pipeline_performance.json` that includes a pass/fail field (`runtime_ok`: true/false).
- [ ] T050 [P] [US1] Add a verification step in `data/download_ebd.py` that checks the downloaded file size against the expected size stored in `data/metadata.yaml` (field `expected_bytes`). The task fails if the sizes differ.
- [ ] T051 [P] [US1] Implement a data quality check in `data/preprocess.py` to identify and log any missing or invalid coordinate values (latitude/longitude) in the EBD data.
- [ ] T052 [P] [US1] Implement a unit test for the `merge_and_buffer.py` script to verify that the land‑cover proportions for each buffer radius sum to ≤ 1 (allowing for rounding) for each observation.
- [ ] T053 [US2] Implement hyperparameter tuning for the Random Forest classifier using scikit‑learn’s `GridSearchCV` with a defined grid: `n_estimators` = [[deferred]], `max_depth` = [10,20,None], `min_samples_leaf` = [1,2]; optimise for balanced accuracy, and write the best parameters to `data/models/hyperparams.json`.
- [ ] T054 [US2] Implement a test to verify that the Across‑Species Permutation Test in `models/evaluate.py` produces a p‑value below 0.05 on a known synthetic dataset where the signal is injected.
- [ ] T055 [US3] Implement a task to generate a map showing the spatial distribution of the top species by observation count, highlighting areas with high foraging habitat suitability (reuse `viz/map_habitat.py` output).
- [ ] T056 [US3] Implement an interactive dashboard (e.g., using Streamlit) that allows users to explore the feature importance rankings and visualize the relationship between land cover types and foraging guilds; include it under `code/dashboard/`.
