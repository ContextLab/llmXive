# Tasks: Predicting Avian Foraging Guilds from Public eBird Data and Land Cover Maps

**Input**: Design documents from `/specs/001-avian-foraging-land-cover/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this story belongs to (e., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Initialize Project Directory Structure: Create directories `projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/data/`, `models/`, `viz/`, `notebooks/`, `utils/`, and `tests/` using `mkdir -p` and create a `.gitkeep` file inside each using `touch`.

- [X] T002 Create placeholder files `README.md` and `run_pipeline.sh` in `projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/`.

- [X] T003 [P] Create `requirements.txt` in `projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/` with pinned dependencies: `pandas`, `numpy`, `scikit-learn`, `geopandas`, `rasterio`, `requests`, `matplotlib`, `seaborn`, `pyyaml`, `jupyter`, `s3fs`.

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure and data preparation that MUST be complete before ANY user story can be implemented. Includes data filtering and selection logic required for the pipeline.

- [ ] T004 [P] Implement `utils/config.py` to define paths, random seeds, and constants. The file MUST define the following keys: `RANDOM_SEED` (int, e.g., a fixed seed for reproducibility), `EBD_URL` (string, S3 path), `NLCD_URL` (string, USGS path), `BUFFER_SIZE` (int, 100), `N_PERMUTATIONS` (int, 1000). Verification: `import config; assert config.RANDOM_SEED == 42`.
- [X] T005 [P] Implement `utils/provenance.py` to generate SHA-256 hashes for all data artifacts and write them to `data/metadata.yaml`. This task must also include a function to record source URLs, versions, and extraction dates for all external datasets to satisfy Constitution Principle VI (Habitat Data Provenance).
- [X] T006a [Depends on T004, T005] Create `tests/test_data_contract.py` with a failing `test_schema_compliance` function stub that asserts `False` and verify `pytest` returns exit code 1.
- [X] T006b [P] [Depends on T004, T005] Create `tests/test_metrics.py` with a failing `test_metrics_calc` function stub that asserts `False` and verify `pytest` returns exit code 1.
- [ ] T007.5a [Depends on T004, T005] Implement `run_pipeline.sh` orchestration script in `projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/`. The script MUST: (1) have a shebang and `set -e`; (2) execute `code/data/download_ebd.py` (T036); (3) execute `code/data/download_nlcd.py` (T037); (4) execute `code/data/load_and_count.py` (T012.5a); (5) execute `code/data/select_top_species.py` (T012.5b); (6) execute `code/data/preprocess.py` (T012.5c); (7) execute `code/data/merge_and_buffer.py` (T039d); (8) execute `code/data/aggregate.py` (T040); (9) execute `code/models/train.py` (T041); (10) execute `code/models/evaluate.py` (T042c); (11) execute `code/viz/plot_confusion.py` (T043); (12) execute `code/viz/plot_importance.py` (T044); and (13) execute `code/viz/map_habitat.py` (T045). It MUST implement error handling (stop on first failure), log each step's exit code, and return a non‑zero exit code if any step fails.
- [ ] T007.5b [P] [Depends on T007.5a] Implement an error handling test for `run_pipeline.sh`. Simulate a failure in step 3 (e.g., `exit 1` in a mock script) and assert the final exit code is 1.
- [ ] T008a [US1] [P] Implement `data/download_guild_source.py` to generate `data/raw/guild_mapping_manual.csv` from authoritative ornithological literature. The script MUST read a hardcoded dictionary of species-to-guild mappings derived from "Birds of the World" (Cornell Lab of Ornithology) with the following explicit content (BIRDS ONLY): `{'Passer domesticus': 'ground', 'Turdus migratorius': 'canopy', 'Sialia sialis': 'aerial', 'Cardinalis cardinalis': 'canopy', 'Buteo jamaicensis': 'aerial', 'Anas platyrhynchos': 'ground', 'Pelecanus occidentalis': 'aerial', 'Pipilo maculatus': 'ground', 'Troglodytes aedon': 'canopy', 'Sturnella neglecta': 'ground', 'Agelaius phoeniceus': 'ground', 'Zonotrichia albicollis': 'ground', 'Junco hyemalis': 'ground', 'Spizella passerina': 'ground', 'Vireo gilvus': 'canopy', 'Empidonax minimus': 'aerial', 'Contopus virens': 'aerial', 'Sayornis phoebe': 'aerial', 'Tyrannus tyrannus': 'aerial', 'Sitta carolinensis': 'canopy', 'Poecile atricapillus': 'canopy', 'Parus major': 'canopy', 'Corvus brachyrhynchos': 'canopy', 'Cyanocitta cristata': 'canopy', 'Quiscalus quiscula': 'ground'}`. The script MUST write this to `data/raw/guild_mapping_manual.csv` with columns `species_id`, `foraging_guild`, `source_citation`. The script MUST raise `FileNotFoundError` if the dictionary is empty or malformed. Save the file to `data/raw/guild_source.csv` with a `source_citation` column.
- [ ] T008b [US1] [Depends on T008a] Implement `data/generate_guild_mapping.py` to read `data/raw/guild_source.csv` and write `data/processed/guild_mapping.csv` with columns `species_id`, `foraging_guild`, `source_citation`, `extraction_date`.
- [ ] T012.5a [US1] [P] Implement `data/load_and_count.py` to read `data/raw/ebd_train.parquet`, compute the TOTAL record count for EVERY species in the dataset (not just a subset), and write per‑species record counts to `data/processed/species_counts.json`. This step MUST ensure a global count is available to deterministically select the top species. The implementation MUST NOT use streaming mode that prevents a global count; it must process the entire dataset (in chunks if needed) to ensure accurate ranking.
- [ ] T012.5b [US1] [Depends on T012.5a] Implement `data/select_top_species.py` to read `species_counts.json`, sort descending, select a subset of top-ranked species by record count (deterministic tie‑break by alphabetical `species_id`), and write `data/processed/top_species_ids.json`.
- [ ] T012.5c [US1] [Depends on T012.5b] Implement `data/preprocess.py` to load `top_n_species_ids.json

The specific value to remove/generalize: 'n'

Rewritten passage:` and the raw EBD, keep only selected species, enforce the ≥ 50‑observation rule, cross-reference with `guild_mapping.csv` to drop species with missing guilds (logging exclusions to `data/processed/guild_missing_log.txt`), and write `data/processed/filtered_ebd.csv`. This replaces the previous `filter_and_log.py` to match the plan's design document.
- [ ] T036 [US1] [P] Implement `data/download_ebd.py` to attempt download of the latest EBD parquet from `s3://ebird-data/ebd_release/`. If the download fails, automatically fall back to a verified subset stored at `s3://ebird-data/ebd_subset/ebd_subset.parquet`. Save the file to `data/raw/ebd_train.parquet` and generate checksums in `data/metadata.yaml`. The script MUST raise `FileNotFoundError` only after both attempts fail.
- [ ] T037 [US1] [P] Implement `data/download_nlcd.py` to fetch NLCD 2019 land‑cover data from the USGS EarthExplorer API, download tiles to `data/raw/nlcd_2019.zip`, and record version/date in `data/metadata.yaml`. On failure the script MUST raise `FileNotFoundError` (no fallback).

## Phase 3: User Story 1 - Data Extraction and Merging Pipeline (Priority: P1) 🎯 MVP

**Goal**: Extract eBird EBD records for top species, merge with NLCD land cover data within 100m buffers, and filter for statistical power (≥ 50 obs/species).

### Implementation for User Story 1

- [ ] T039a [US1] [Depends on T012.5c, T037, T008b] Implement `data/load_and_validate_inputs.py` to read `filtered_ebd.csv`, `nlcd_2019.zip`, and `guild_mapping.csv`, validate that required columns exist, check for null lat/long, and verify column names match `contracts/dataset.schema.yaml`. Raise `ValueError` if inputs are malformed.
- [ ] T039b [US1] [Depends on T039a] Implement `data/calculate_100m_buffers.py` to compute land‑cover proportions for a **fixed buffer of 100m** around each observation point (strictly adhering to FR-002). Create columns explicitly named `forest_prop_100m`, `grassland_prop_100m`, `wetland_prop_100m`, `urban_prop_100m`, and `other_prop_100m`. Do NOT compute 50m or 200m buffers. This task MUST also create `tests/fixtures/buffer_test_fixture.json` containing a specific test coordinate (lat: 42.3601, long: [generalized longitude value]) and the expected land cover proportions (e.g., `{'forest': 0.45, 'grassland': 0.30, ...}`) for a 100m buffer around it, to be used in a unit test. Verification: Run a unit test on the known coordinate; assert sum of proportions == 1.0 within tolerance.
- [ ] T039c [US1] [Depends on T039b] Implement `data/join_guild_labels.py` to join the buffered land cover data with `guild_mapping.csv` to assign `foraging_guild` to each observation, ensuring all required columns are present.
- [ ] T039d [US1] [Depends on T039c] Implement `data/write_merged_observations.py` to write `data/processed/merged_observations.csv` with full provenance metadata and a `validate_schema()` function that raises `ValueError` if required columns are missing.
- [ ] T010 [Depends on T039d] Add a test in `tests/test_data_contract.py` that asserts `merged_observations.csv` conforms to `contracts/dataset.schema.yaml` (columns `species_id`, `foraging_guild`, and all land‑cover proportion columns for 100m buffer).
- [ ] T040 [Depends on T039d] Implement `data/aggregate.py` to collapse `merged_observations.csv` to species‑level profiles (`species_profiles.csv`) by averaging land‑cover proportions across all observations, logging any dropped rows with structured `reason_code`/`details`.

## Phase 4: User Story 2 - Classification Model Training and Evaluation (Priority: P2)

**Goal**: Train a Random Forest classifier to predict foraging guild from land‑cover proportions and validate signal via a **Across-Species Permutation Test** to control for species identity as required by FR-005.

### Implementation for User Story 2

- [ ] T041 [US2] [Depends on T040] Implement `models/train.py` to load `species_profiles.csv`, standardize predictors, encode `foraging_guild`, perform *k*‑fold cross‑validation with a fixed `random_state`, train a `RandomForestClassifier`, save the fitted model to `data/models/random_forest.pkl`, save training metrics to `data/models/training_metrics.json`, AND save `out_of_fold_predictions` and `true_labels` to `data/models/cv_predictions.json` to support cross-validated evaluation.
- [ ] T059 [US2] [P] Implement `models/stratified_permutation.py` to perform an **Across-Species Permutation Test** on the aggregated `species_profiles.csv`. **Note**: Although FR-005 requests a test "stratified by species", guild labels are constant per species (US-1), making traditional stratification impossible. Therefore, this test shuffles `foraging_guild` labels **ACROSS species IDs** (breaking the link between land cover and guild at the species level) to create a valid null distribution. This satisfies FR-005 by testing if land cover predicts guild assignment better than chance while maintaining the species structure in the null model. Output: Save the null distribution array to `data/models/null_distribution.npy`. Verification: Assert `len(null_distribution) == 1000`.
- [ ] T042a [US2] [Depends on T041] Implement `models/load_model_and_metrics.py` to load the trained model and metrics, and compute initial balanced accuracy and per‑class F1 scores.
- [ ] T042b [US2] [Depends on T042a, T059] Implement `models/run_permutation_test.py` to run the **Across-Species Permutation Test** using the logic from T059: permute guild labels across species, repeat for a sufficient number of iterations, and compare observed accuracy to the null distribution.
- [ ] T042c [US2] [Depends on T042b] Implement `models/calculate_pvalue_and_save.py` to calculate the p‑value from the null distribution, log seeds, the α = 0.05 threshold, and a pass/fail flag, and save results (`p_value`, metrics) to `data/models/evaluation_results.json`.
- [ ] T023 [Depends on T041, T042c] Implement an integration test `tests/test_integration.py` that runs `models/train.py` then `models/evaluate.py` (via T042c) and checks that both output files exist and contain valid JSON.
- [X] T018 Add unit tests in `tests/test_metrics.py` for balanced accuracy and F1 calculations (use a tiny synthetic dataset with known outcomes).
- [ ] T054 [US2] [P] Implement a test to verify that the Across-Species Permutation Test in `models/evaluate.py` produces a p‑value below 0.01 on a known synthetic dataset where the signal is injected. The synthetic dataset MUST be generated with land cover proportions perfectly correlated with guild labels (e.g., generate 100 rows: 50 with forest_prop=0.9 for 'canopy', 50 with grassland_prop=0.9 for 'ground') to ensure a strong signal. The test must assert the p-value is < 0.01.

## Phase 5: User Story 3 - Visualization and Feature Importance Reporting (Priority: P3)

**Goal**: Produce a confusion matrix, feature‑importance bar chart, spatial habitat maps for the **top-ranked species by observation count**, and a summary report of top land‑cover predictors per foraging guild.

### Implementation for User Story 3

- [ ] T043 [US3] [Depends on T042c, T041] Implement `viz/plot_confusion.py` to load `out_of_fold_predictions` and `true_labels` from `data/models/cv_predictions.json` (produced by T041), generate a confusion‑matrix PNG (`docs/results/confusion_matrix.png`) and accompanying metadata JSON (`confusion_matrix_metadata.json`) that records the species list used. This ensures the matrix reflects cross-validated performance.
- [ ] T044 [US3] [Depends on T042c] Implement `viz/plot_importance.py` to extract feature‑importance scores from the trained Random Forest, plot a bar chart (`docs/results/feature_importance.png`), and write a JSON file with the raw importance values.
- [ ] T045 [US3] [Depends on T042c, T012.5b] Implement `viz/map_habitat.py` to (A) rasterize model predictions over a high‑resolution grid, (B) for the **top species by observation count** (identified in `top_25_species_ids.json`) generate a PNG map (`docs/results/habitat_map_{species_id}.png`) and a consolidated GeoJSON (`docs/results/habitat_map.geojson`), ensuring the grid does not extrapolate beyond observed coordinates.
- [ ] T028 [US3] [Depends on T044] Implement `viz/plot_importance.py` (report generation) to write a markdown summary report `docs/results/feature_importance_report.md` that lists, for each foraging guild, the top land‑cover predictors (by mean decrease impurity) with their importance scores.
- [ ] T028.0 [US3] [P] Implement `viz/fetch_literature_predictors.py` to download domain literature predictors from a verified source. The script MUST fetch real data from a valid URL (e.g., `https://raw.githubusercontent.com/birds-of-the-world/habitat-guilds/main/data/guild_mappings.csv` or a similar verified public repository) or fallback to a pre-cached local file `data/raw/literature_guilds.csv` if the URL fails. The output MUST be a CSV file `data/raw/literature_mappings.csv` with columns `guild` and `predictor_name`. The task MUST define the exact URL or package to use.
- [ ] T028.1 [US3] [Depends on T044, T028.0] Implement `viz/validate_importance.py` to **quantitatively** assess ecological validity: load `data/raw/literature_mappings.csv` (produced by T028.0), validate it is non-empty and correctly formatted, then compare the top‑3 model‑identified predictors for each guild against the **fetched real data**. Compute the Jaccard similarity of the top-3 sets and report the result in `docs/results/importance_validation.json` with a brief note in the markdown report.
- [ ] T029 [Depends on T043, T044, T045, T028, T028.1] Update `notebooks/01_analysis.ipynb` to orchestrate the full pipeline, load all intermediate artifacts, and serve as the Single Source of Truth for results and figures.

## Phase N: Polish & Cross‑Cutting Concerns

- [ ] T030 [P] Documentation updates in `docs/` (add `quickstart.md` with Installation, Data Download, and Running the Pipeline sections).
- [ ] T031 [P] Refactor `calculate_100m_buffers.py` and `write_merged_observations.py` to keep cyclomatic complexity < 10 (1412.6216, https://arxiv.org/abs/1412.6216) (focus on `calculate_100m_buffers` function). This task depends on T039d being complete.
- [ ] T031b [P] [Plan/Spec Conflict] Document the resolution of the contradiction between the Plan's 'Complexity Tracking' (buffers of varying scales) and the Spec (FR-002, fixed 100m buffer). Write a decision record in `docs/decisions.md` stating that the Spec (FR-002) takes precedence and the implementation will use a fixed 100m buffer, noting that the Plan's suggestion for varying scales was deemed out of scope for this MVP.
- [ ] T032 [SC-004] Profile `calculate_100m_buffers.py` and optimise buffer calculations via vectorisation; verify total runtime < 6 h. This task depends on T039d being complete.
- [ ] T033 [P] Add unit tests for `utils/config.py` and `utils/provenance.py` in `tests/unit/`.
- [ ] T034 [P] Execute the commands in `docs/quickstart.md` in a fresh virtual environment and assert that all expected artifacts are produced.
- [ ] T035 [SC-004] Implement `utils/measure_pipeline.py` to wrap `run_pipeline.sh`, record total wall‑clock time and peak memory usage using `psutil`, compare the wall‑clock time to the CI job limit, and write a JSON summary `pipeline_performance.json` that includes a pass/fail field (`runtime_ok`: true/false).
- [ ] T050 [P] [US1] Add a verification step in `data/download_ebd.py` that checks the downloaded file size against the expected size stored in `data/metadata.yaml` (field `expected_bytes`). The task fails if the sizes differ.
- [ ] T051 [P] [US1] Implement a data quality check in `data/preprocess.py` to identify and log any missing or invalid coordinate values (latitude/longitude) in the EBD data.
- [ ] T052 [P] [US1] Implement a unit test for the `calculate_100m_buffers.py` script (specifically T039b code) to verify that the land‑cover proportions for the 100m buffer sum to ≤ 1 (allowing for rounding) for each observation.
- [ ] T055 [US3] [P] Implement a task to generate a map showing the spatial distribution of the top species by observation count, highlighting areas with high foraging habitat suitability (reuse `viz/map_habitat.py` output).