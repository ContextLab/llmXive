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

- [ ] T003 Create `requirements.txt` in `projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/` with pinned dependencies: `pandas`, `numpy`, `scikit-learn`, `geopandas`, `rasterio`, `requests`, `matplotlib`, `seaborn`, `pyyaml`, `jupyter`, `s3fs`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Implement `utils/config.py` to define paths, random seeds, and constants.
- [ ] T005 [Depends on T004] Implement `utils/provenance.py` to generate SHA-256 hashes for all data artifacts and write them to `data/metadata.yaml`. This task must also include a function to record source URLs, versions, and extraction dates for all external datasets to satisfy Constitution Principle VI (Habitat Data Provenance).
- [X] T006a [Depends on T004, T005] Create `tests/test_data_contract.py` with a failing `test_schema_compliance` function stub that asserts `False` and verify `pytest` returns exit code 1.
- [ ] T006b [Depends on T004, T005] Create `tests/test_metrics.py` with a failing `test_metrics_calc` function stub that asserts `False` and verify `pytest` returns exit code 1.
- [ ] T007.5a [Depends on T004, T005] Create `run_pipeline.sh` orchestration script skeleton in `projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/` with placeholder steps for each pipeline phase.
- [ ] T007.5b [Depends on T036, T037, T038, T039, T040, T041, T042, T043, T044, T045] Implement full `run_pipeline.sh` to orchestrate all data, model, and viz steps in dependency order. The script MUST: (1) execute `code/data/download_ebd.py` (T036); (2) execute `code/data/download_nlcd.py` (T037); (3) execute `code/data/select_top_species.py` (T038); (4) execute `code/data/merge_and_buffer.py` (T039); (5) execute `code/data/aggregate.py` (T040); (6) execute `code/models/train.py` (T041); (7) execute `code/models/evaluate.py` (T042); (8) execute `code/viz/plot_confusion.py` (T043); (9) execute `code/viz/plot_importance.py` (T044); and (10) execute `code/viz/map_habitat.py` (T045). It MUST implement error handling (stop on first failure), log each step's exit code, and return a non-zero exit code if any step fails. **Note**: This script does NOT depend on fallback tasks; it relies on T036 and T037 raising on failure to satisfy Constitution Principle VI.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Extraction and Merging Pipeline (Priority: P1) 🎯 MVP

**Goal**: Extract eBird EBD records for top species, merge with NLCD land cover data within m buffers, and filter for statistical power (≥50 obs/species).

**Independent Test**: Verify that the top species are selected., species with <50 observations are excluded, and the output CSV contains complete land cover proportions and assigned foraging guilds.

### Implementation for User Story 1

- [ ] T036 [US1] [P] Implement `data/download_ebd.py` to list the S3 bucket `s3://ebird-data/ebd_release/`, sort files by `last_modified` descending, select the first `.parquet` file, download it to `data/raw/ebd_train.csv` (or parquet), and generate checksums in `data/metadata.yaml`. **Primary Source**: The script MUST download from the canonical S3 bucket. If the download fails (e.g., authentication error, timeout), the script MUST raise a `FileNotFoundError` and exit. **Note**: No fallback task exists; the pipeline stops on failure to satisfy Constitution Principle VI.
- [ ] T037 [US1] [P] Implement `data/download_nlcd.py` to fetch NLCD land cover data from the canonical USGS EarthExplorer API (Constitution Principle VI) using a deterministic key pattern for the contiguous US (e.g., `NLCD_2019_Land_Cover_Land_Use_2019.tif`), handling API authentication and pagination to download tiles to `data/raw/nlcd_2019.zip`, and record the exact version/date of the raster in `data/metadata.yaml`. **Primary Source**: This task MUST attempt the EarthExplorer download first. If it fails (e.g., auth error), it MUST raise `FileNotFoundError`. **Note**: No fallback task exists; the pipeline stops on failure to satisfy Constitution Principle VI.
- [ ] T008a [US1] [P] [Depends on T005] Implement `data/download_guild_source.py` to fetch a pre-compiled CSV containing foraging guild labels for the selected species from a verified static source. The URL MUST be defined in `data/metadata.yaml` (e.g., `). Save the result to `data/raw/guild_source.csv`. This task must explicitly fetch ONLY the necessary guild labels (not the full 'Birds of the World' database) and verify that the downloaded file contains a 'source_citation' field confirming its origin. The task must support CSV, JSON, or XML formats.
- [ ] T008b [US1] [Depends on T008a] Implement `data/generate_guild_mapping.py` to load `data/raw/guild_source.csv` (from T008a), extract species_id and foraging_guild, and save to `data/processed/guild_mapping.csv`. The output CSV MUST include columns `species_id`, `foraging_guild`, `source_citation`, and `extraction_date` to prove provenance.
- [ ] T012.5a [US1] [P] [Depends on T036] Implement `data/load_and_count.py` to load `data/raw/ebd_train.csv` (from T036) and count total records per species. Save the counts to `data/processed/species_counts.json`.
- [ ] T012.5b [US1] [P] [Depends on T012.5a] Implement `data/select_top_species.py` to load `data/processed/species_counts.json` (from T012.5a). The logic MUST: (1) Sort the full pool by total record count descending. (2) Select a representative subset of species. (3) Handle ties at the 25th rank by selecting the species with the lexicographically smallest `species_id` (deterministic tie-breaking) to ensure exactly 25 species are selected. (4) Save the final list of top species identifiers to `data/processed/top_25_species_ids.json`. This file serves as the single source of truth for both analysis and visualization.
- [ ] T012.5c [US1] [Depends on T012.5b] Implement `data/filter_and_log.py` to load `data/processed/top_25_species_ids.json` (from T012.5b) and `data/raw/ebd_train.csv` (from T036), filter the EBD data to retain ONLY the selected species, apply the ≥50 observations filter, log the final count and rationale to `data/processed/selection_log.txt`, and save the filtered EBD subset to `data/processed/filtered_ebd.csv`.
- [ ] T039 [US1] [Depends on T012.5c, T037, T008b] Implement `data/merge_and_buffer.py` to load `data/processed/filtered_ebd.csv` (from T012.5c), load `data/raw/nlcd_2019.zip` (from T037), calculate buffer land cover proportions using NLCD 2019 data within **100m buffers** (using EPSG Web Mercator projection for deterministic radii), join with `data/processed/guild_mapping.csv` (from T008b) to assign foraging guilds, and save the final result to `data/processed/merged_observations.csv`. The output schema MUST include `species_id`, `foraging_guild`, and **individual columns** for land cover proportions: `forest_prop_100m`, `grassland_prop_100m`, `wetland_prop_100m`, `urban_prop_100m`, `other_prop_100m`. Embed provenance fields (source URL, version, date) into the output CSV metadata or header comments to satisfy Constitution Principle VI.
- [ ] T015 [US1] [Depends on T039] Implement `validate_schema()` function in `data/merge_and_buffer.py` that raises `ValueError` if columns `species_id`, `foraging_guild`, and individual land cover proportion columns are missing, and add unit test `test_validate_schema` in `tests/test_data_contract.py` to verify the schema validation logic.
- [ ] T010 [US1] [Depends on T039] Validate schema compliance in `projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/tests/test_data_contract.py` by asserting `merged_observations.csv` matches `contracts/dataset.schema.yaml`, specifically validating columns `species_id`, `foraging_guild`, and land cover proportion columns.
- [ ] T040 [US1] [Depends on T039] Implement `data/aggregate.py` to aggregate filtered observations from `data/processed/merged_observations.csv` into species-level profiles and save to `data/processed/species_profiles.csv`. Log the exact number of observations dropped during aggregation due to missing land cover data and the specific reasons for the drop in a structured format: `reason_code` (e.g., 'missing_tile', 'invalid_value', 'out_of_bounds') and `details`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Classification Model Training and Evaluation (Priority: P2)

**Goal**: Train a Random Forest classifier to predict foraging guild from land cover proportions and validate signal via a Stratified Permutation Test.

**Independent Test**: Verify balanced accuracy is measured against chance, per-class F scores are computed, and the permutation test (a sufficient number of iterations) yields p < 0.05.

### Implementation for User Story 2

- [ ] T041 [US2] [Depends on T040] Implement `models/train.py` to load `data/processed/species_profiles.csv` (from T040), normalize land cover proportions, encode foraging guilds, handle missing values, and train a Random Forest (k-fold CV, CPU-only). The script MUST save the trained model to `data/models/random_forest.pkl` and a training metrics log to `data/models/training_metrics.json`. Completion is defined by the existence of these two files with valid content.
- [ ] T042 [US2] [Depends on T041] Implement `models/evaluate.py` to load the trained model (from T041) and the training metrics. Compute balanced accuracy and per-class F1 scores. Perform the **Stratified Permutation Test (stratified by species)** as mandated by FR-005/FR-008. The script MUST shuffle the foraging guild labels across species ONLY if a specific 'Spec Amendment' log entry exists (which does not exist); otherwise, it MUST implement the stratified resampling by species. The script MUST compare the observed accuracy against the null distribution to determine if land cover predicts guild independent of species identity. It MUST include a sanity check that the permutation test distribution is not degenerate and raise an error if it is. The script MUST save the evaluation results (p-value, metrics) to `data/models/evaluation_results.json`. **Correction**: The task MUST implement the **Stratified Permutation Test (stratified by species)** as explicitly required by FR-005 and FR-008. The plan's description of "Across-Species Permutation" is incorrect and must be ignored. The script MUST shuffle the foraging guild labels across species ONLY if a specific 'Spec Amendment' log entry exists (which does not exist); otherwise, it MUST implement the stratified resampling by species. The script MUST compare the observed accuracy against the null distribution to determine if land cover predicts guild independent of species identity. It MUST include a sanity check that the permutation test distribution is not degenerate and raise an error if it is. The script MUST save the evaluation results (p-value, metrics) to `data/models/evaluation_results.json`.
- [ ] T021 [US2] Add logging in `models/evaluate.py` to record p-values, random seeds, and performance metrics against the α = 0.05 threshold.
- [ ] T023 [US2] [Depends on T041, T042] Implement integration test in `tests/test_integration.py` to ensure `models/train.py` (output: `random_forest.pkl`) and `models/evaluate.py` (output: `evaluation_metrics.json`) work together end-to-end, distinct from the orchestration script T007.
- [ ] T018 [US2] [Depends on T042] Unit test for metric calculations in `projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/tests/test_metrics.py`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualization and Feature Importance Reporting (Priority: P3)

**Goal**: Generate confusion matrix, feature importance chart, spatial map for top species, and a summary report of top land cover predictors per guild.

**Independent Test**: Verify output files (PNG/GeoJSON) exist for the top species and the report lists top predictors per guild with validation.

### Implementation for User Story 3

- [ ] T043 [US3] [Depends on T012.5b, T041, T042, T021] Implement `viz/plot_confusion.py` to load `data/processed/top_25_species_ids.json` (from T012.5b) and generate the confusion matrix image (predicted vs actual foraging guilds) for the specified species list. Output filename: `docs/results/confusion_matrix.png`, format: PNG, Figure size: standard dimensions appropriate for publication, colormap: 'viridis'. The script MUST also generate a `docs/results/confusion_matrix_metadata.json` containing the species list used and the confusion matrix data. Completion is defined by the existence of both files.
- [ ] T044 [US3] [Depends on T041, T042, T021] Implement `viz/plot_importance.py` to generate the feature importance bar chart and identify top predictors per guild. The script MUST output `docs/results/feature_importance.png` (PNG format) and list the top land cover predictors per guild by mean decrease impurity in the console log and a metadata JSON file.
- [ ] T045 [US3] [Depends on T041, T042, T021] Implement `viz/map_habitat.py` to: (A) Apply the trained model to a spatial grid to generate a continuous raster prediction surface with resolution at a high spatial granularity and CRS EPSG:; (B) Iterate over all species listed in `data/processed/top_25_species_ids.json` (from T012.5b) and produce individual maps saved as `docs/results/habitat_map_{species_id}.png`; (C) Validate that the spatial grid covers actual observation coordinates and does not extrapolate beyond known data ranges. Save the final map to `docs/results/habitat_map.png` or `docs/results/habitat_map.geojson`.
- [ ] T028 [US3] [Depends on T041, T042, T021] Implement logic in `viz/plot_importance.py` to generate the summary report listing the top land cover predictors for each foraging guild and save to `docs/results/feature_importance_report.md`.
- [ ] T028.5 [US3] [SC-003] [Depends on T028] Implement `viz/validate_importance.py` to perform a **qualitative assessment** of the generated feature importance rankings against **domain literature sources** (e.g., 'Birds of the World', 'Handbook of the Birds of the World') as defined in `data/metadata.yaml`. For each foraging guild, list the top land cover predictors identified by the model and cross-reference them with the key habitat descriptors in the source literature. Generate a table in `feature_importance_report.md` showing the comparison and a qualitative note on ecological validity. **Note**: No specific pass/fail threshold (e.g., overlap count < 2) is imposed; the assessment is qualitative.
- [ ] T029 [US3] Update `notebooks/01_analysis.ipynb` to orchestrate the full pipeline, load results, and serve as the Single Source of Truth.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T030 [P] Documentation updates in `docs/` including `quickstart.md`: Add "Installation", "Data Download", and "Running the Pipeline" sections.
- [ ] T031 [P] Code cleanup and refactoring in `code/`: Refactor `merge_and_buffer.py` to ensure max cyclomatic complexity < 10. Specifically refactor the `calculate_buffer_proportions` and `merge_land_cover` functions.
- [ ] T032 [SC-004] Performance optimization: Profile `merge_and_buffer.py` and optimize buffer calculation using vectorization; verify total runtime < 6h.
- [ ] T033 [P] Additional unit tests in `tests/unit/`: Add unit tests for `utils/config.py` and `utils/provenance.py`.
- [ ] T034 [P] Run `quickstart.md` validation: Execute the shell commands listed in the "Running the Pipeline" section of `docs/quickstart.md` in a fresh venv and verify all artifacts exist.
- [ ] T035 [SC-004] [FR-002] [Depends on T007.5b] Implement `utils/measure_pipeline.py` to explicitly measure and log the total pipeline runtime (must be < 6h) and peak memory usage (must be < 7GB) during execution of T007.5b. This task must wrap `run_pipeline.sh` as a subprocess using `subprocess.Popen` and monitor the parent process PID via `psutil` to capture these metrics. **Placement**: This task is in Phase N (Polish) as it measures the pipeline execution.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output (T040)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 model output

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Data download tasks (T036, T037) MUST complete before selection (T012.5a, T012.5b, T012.5c)
- **T012.5a depends on T036 (EBD)**
- **T012.5b depends on T012.5a**
- **T012.5c depends on T012.5b**
- Selection (T012.5c) MUST complete before merging (T039)
- **T039 depends on T012.5c, T037, and T008b (guild mapping)**
- Merging (T039) MUST complete before schema validation (T015, T010) and aggregation (T040)
- Aggregation (T040) MUST complete before training (T041)
- Training (T041) MUST complete before evaluation (T042)
- Evaluation (T042) MUST complete before visualization (T043, T044, T045, T028)

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members
- **T043, T044, T045, T028 are parallel to each other after T042 completes.**

---

## Parallel Example: User Story 1

```bash
# Launch all data download tasks for User Story 1 together:
Task: "Implement data/download_ebd.py to fetch EBD data via verified S3 path"
Task: "Implement data/download_nlcd.py to fetch NLCD 2019 land cover data via USGS S3"
Task: "Implement data/download_guild_source.py to fetch Birds of the World guild data"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (verify top-ranked species, filtering, and merged data)
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
 - Developer A: User Story 1 (Data Extraction)
 - Developer B: User Story 2 (Model Training) - *Wait for US1 data*
 - Developer C: User Story 3 (Visualization) - *Wait for US2 model*
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
- **CRITICAL**: All data download tasks must use real, reachable URLs (eBird S3/USGS). No synthetic data generation is allowed.
- **CRITICAL**: All models must run on CPU-only (scikit-learn default precision). No GPU/CUDA dependencies.
- **CRITICAL**: Permutation test MUST use 'Stratified by Species' resampling. The plan's 'Across-Species Permutation' description is incorrect and must be ignored.
- **CRITICAL**: T012.5b (select top 25) MUST enforce exactly 25 species using deterministic tie-breaking (alphabetical species_id) if ties occur at the 25th rank.
- **CRITICAL**: T008a must fetch ONLY the pre-compiled guild labels for the selected species, not the full 'Birds of the World' database.
- **CRITICAL**: T045 must explicitly iterate over all species in `top_25_species_ids.json` to generate the spatial map, not just 2.
- **CRITICAL**: T028.5 must perform a qualitative assessment with literature sources from metadata.yaml, without imposing a specific pass/fail rubric.
- **CRITICAL**: T036 must explicitly check for the existence of the `.parquet` files in the S3 bucket and raise a `FileNotFoundError` only if the primary source fails.
- **CRITICAL**: T039 must expand 'land_cover_proportions' into individual columns (e.g., forest_prop) to match the schema validation requirements.
- **CRITICAL**: T035 must explicitly validate that the total pipeline runtime is < 6h and peak memory usage is < 7GB, and must be placed in Phase N.
- **CRITICAL**: T012.5 tie-breaking: Enforce exactly 25 species with deterministic tie-breaking (alphabetical species_id).
- **CRITICAL**: Constitution Principle VI requires data 'exclusively' from USGS EarthExplorer. No fallback tasks (T011.1, T012.1) are permitted.
- **CRITICAL**: T007.5b depends on atomic execution tasks (T036-T045), not conditional fallbacks.
- **CRITICAL**: T042 must implement 'Stratified Permutation Test (stratified by species)' unconditionally.