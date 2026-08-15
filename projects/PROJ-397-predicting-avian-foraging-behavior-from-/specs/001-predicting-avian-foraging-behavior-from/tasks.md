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

- [ ] T001a [P] Initialize `data/` directory: Create directory `projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/data/` using `mkdir -p` and create a `.gitkeep` file inside using `touch .gitkeep`.
- [ ] T001b [P] Initialize `models/` directory: Create directory `projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/models/` using `mkdir -p` and create a `.gitkeep` file inside using `touch .gitkeep`.
- [ ] T001c [P] Initialize `viz/` directory: Create directory `projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/viz/` using `mkdir -p` and create a `.gitkeep` file inside using `touch .gitkeep`.
- [ ] T001d [P] Initialize `notebooks/` directory: Create directory `projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/notebooks/` using `mkdir -p` and create a `.gitkeep` file inside using `touch .gitkeep`.
- [ ] T001e [P] Initialize `utils/` directory: Create directory `projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/utils/` using `mkdir -p` and create a `.gitkeep` file inside using `touch .gitkeep`.
- [ ] T001f [P] Initialize `tests/` directory: Create directory `projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/tests/` using `mkdir -p` and create a `.gitkeep` file inside using `touch .gitkeep`.
- [ ] T002 [P] Create placeholder files `README.md` and `run_pipeline.sh` in `projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/`.
- [ ] T003 [P] Create `requirements.txt` in `projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/` with pinned dependencies: `pandas`, `numpy`, `scikit-learn`, `geopandas`, `rasterio`, `requests`, `matplotlib`, `seaborn`, `pyyaml`, `jupyter`, `s3fs`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Implement `utils/config.py` to define paths, random seeds, and constants.
- [ ] T005 [P] Implement `utils/provenance.py` for metadata logging and hash generation.
- [ ] T006a [P] Create `tests/test_data_contract.py` with a failing `test_schema_compliance` function stub that asserts `False` and verify `pytest` returns exit code 1.
- [ ] T006b [P] Create `tests/test_metrics.py` with a failing `test_metrics_calc` function stub that asserts `False` and verify `pytest` returns exit code 1.
- [ ] T007 [P] Create `run_pipeline.sh` orchestration script skeleton in `projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/` with placeholder steps for each pipeline phase.
- [ ] T007.5 [P] Implement `run_pipeline.sh` to orchestrate all data, model, and viz steps in dependency order. The script MUST: (1) execute `code/data/download_ebd.py`, (2) `code/data/download_nlcd.py`, (3) `code/data/select_top_species.py`, (4) `code/data/merge_and_buffer.py`, (5) `code/data/aggregate.py`, (6) `code/models/train.py`, (7) `code/models/evaluate.py`, (8) `code/viz/plot_confusion.py`, (9) `code/viz/plot_importance.py`, and (10) `code/viz/map_habitat.py` sequentially. It MUST implement error handling (stop on first failure), log each step's exit code, and return a non-zero exit code if any step fails.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Extraction and Merging Pipeline (Priority: P1) 🎯 MVP

**Goal**: Extract eBird EBD records for top species, merge with NLCD land cover data within 100m buffers, and filter for statistical power (≥50 obs/species).

**Independent Test**: Verify that the top species are selected., species with <50 observations are excluded, and the output CSV contains complete land cover proportions and assigned foraging guilds.

### Implementation for User Story 1

- [ ] T011 [P] [US1] Implement `data/download_ebd.py` to list the S3 bucket `s3://ebird-data/ebd_release/`, dynamically select the most recent `.parquet` file, download it to `data/raw/ebd_train.csv` (or parquet), and generate checksums in `data/metadata.yaml`. If the official source fails, automatically fall back to downloading the verified S3 subset at `s3://ebird-data/ebd_release/ebd_train_sample.parquet` to ensure CI completion. Raise `FileNotFoundError` only if both sources fail.
- [ ] T011.1 [US1] [P] Implement `data/download_ebd_fallback.py` to explicitly fetch the verified S3 subset `s3://ebird-data/ebd_release/ebd_train_sample.parquet` and save to `data/raw/ebd_train_fallback.parquet`. This task provides the deterministic fallback source for T011.
- [ ] T012 [P] [US1] Implement `data/download_nlcd.py` to fetch NLCD land cover data from the public USGS LPDAAC S3 bucket `s3://usgs-landsat/nlcd/2019/` using a deterministic key pattern for the contiguous US (e.g., `NLCD_2019_Land_Cover_Land_Use_2019.tif`), download tiles to `data/raw/nlcd_2019.zip`, and record the exact version/date of the raster in `data/metadata.yaml`. No authentication required.
- [ ] T012.1 [US1] [P] Implement `data/download_nlcd_fallback.py` to fetch NLCD 2019 from an alternative verified S3 path (e.g., `s3://usgs-nlcd/nlcd_2019_conus.zip`) and save to `data/raw/nlcd_2019_fallback.zip`. This task provides the deterministic fallback source for T012.
- [ ] T012.6 [US1] [Depends on T012, T012.1] Implement `data/stream_nlcd_tiles.py` to handle large NLCD raster files by streaming tiles one-by-one into memory rather than loading the entire raster at once. This task must use `rasterio`'s windowed reading capabilities to process tiles sequentially, ensuring the merged dataset never exceeds the available RAM limit. Log the number of tiles processed and any tiles skipped due to missing data.
- [ ] T008a [US1] [P] Implement `data/download_guild_source.py` to fetch the 'Birds of the World' foraging guild data from a verified static CSV source at `https://raw.githubusercontent.com/eBird/ebird-status-and-trends/main/data/guilds/birds_of_the_world_guilds.csv` or a fallback CSV from `https://raw.githubusercontent.com/eBird/ebird-status-and-trends/main/data/guilds/guild_fallback.csv`. Save the result to `data/raw/guild_source.csv`. This task must explicitly download the external literature source to satisfy FR-001 and Constitution Principle VI, and verify that the downloaded CSV contains a 'source_citation' field confirming its origin as 'Birds of the World'.
- [ ] T008b [US1] [Depends on T008a] Implement `data/generate_guild_mapping.py` to load `data/raw/guild_source.csv` (from T008a), extract species_id and foraging_guild, and save to `data/processed/guild_mapping.csv`. The output CSV MUST include columns `species_id`, `foraging_guild`, `source_citation`, and `extraction_date` to prove provenance.
- [ ] T008c [US1] [P] Implement logic in `data/download_nlcd.py` or a dedicated `data/record_nlcd_provenance.py` script to explicitly record the exact version, date, and source URL of the downloaded NLCD 2019 raster in `data/metadata.yaml` to satisfy Constitution Principle VI (Habitat Data Provenance) for the spatial input.
- [ ] T012.5 [US1] [Depends on T011, T011.1] Implement `data/select_top_species.py` to load `data/raw/ebd_train.csv` (from T011) OR `data/raw/ebd_train_fallback.parquet` (from T011.1). The logic MUST: (1) Check if `data/raw/ebd_train.csv` exists; if not, check for `data/raw/ebd_train_fallback.parquet`; if neither, raise `FileNotFoundError`. (2) Filter the full pool of species to retain ONLY species with ≥50 observations. (3) Sort the filtered list by total record count descending and select a fixed set of N=25 top species (handling ties by including all tied species at the 25th rank threshold). If fewer than 25 valid species exist, proceed with the available count and log the shortfall to `data/processed/selection_log.txt`. Save the final list of top species identifiers to `data/processed/top_25_species_ids.json`.
- [ ] T013 [US1] [Depends on T012.5, T012, T012.1, T008b, T012.6] Implement `data/merge_and_buffer.py` to load `data/raw/ebd_train.csv` (from T011), filter to retain ONLY the species listed in `data/processed/top_25_species_ids.json` (from T012.5), load `data/raw/nlcd_2019.zip` (from T012) OR `data/raw/nlcd_2019_fallback.zip` (from T012.1) if T012 failed, calculate buffer land cover proportions using NLCD 2019 data within **multiple buffer radii (e.g., 50m, 100m, 200m)** (using a projected CRS for deterministic radii), join with `data/processed/guild_mapping.csv` (from T008b) to assign foraging guilds, and save the final result to `data/processed/merged_observations.csv`. The output schema MUST include `species_id`, `foraging_guild`, and **individual columns** for land cover proportions for EACH radius (e.g., `forest_prop_50m`, `forest_prop_100m`, `forest_prop_200m`) to match the validation schema. Embed provenance fields (source URL, version, date) into the output CSV metadata or header comments to satisfy Constitution Principle VI. <!-- [FR-002] [SC-004] -->
- [ ] T015 [US1] [Depends on T013] Implement `validate_schema()` function in `data/merge_and_buffer.py` that raises `ValueError` if columns `species_id`, `foraging_guild`, and individual land cover proportion columns are missing, and add unit test `test_validate_schema` in `tests/test_data_contract.py` to verify the schema validation logic.
- [ ] T010 [US1] [Depends on T013] Validate schema compliance in `projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/tests/test_data_contract.py` by asserting `merged_observations.csv` matches `contracts/dataset.schema.yaml`, specifically validating columns `species_id`, `foraging_guild`, and land cover proportion columns.
- [ ] T016 [US1] [Depends on T013] Implement `data/aggregate.py` to aggregate filtered observations from `data/processed/merged_observations.csv` into species-level profiles and save to `data/processed/species_profiles.csv`. Log the exact number of observations dropped during aggregation due to missing land cover data and the specific reasons for the drop in a structured format: `reason_code` (e.g., 'missing_tile', 'invalid_value', 'out_of_bounds') and `details`.
- [ ] T017 [US1] [Depends on T016, T012.5] Implement `data/extract_top_species.py` to extract the **top 25 species** (N=25) by observation count from `data/processed/species_profiles.csv` (reading the list from `data/processed/top_25_species_ids.json` from T012.5) and persist to `data/processed/top_25_species_for_viz.json`. If the filtered list contains fewer than 25 species, this task MUST process all available species and log the count to `data/processed/viz_selection_log.txt` to match the spec's intent for 'top species'. This ensures the visualization scope matches the analysis scope defined in US-1.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Classification Model Training and Evaluation (Priority: P2)

**Goal**: Train a Random Forest classifier to predict foraging guild from land cover proportions and validate signal via a Stratified Permutation Test.

**Independent Test**: Verify balanced accuracy is measured against chance, per-class F1 scores are computed, and the permutation test (a sufficient number of iterations) yields p < 0.05.

### Implementation for User Story 2

- [ ] T019 [US2] [Depends on T016] Implement `models/train.py` to load `data/processed/species_profiles.csv` (from T016), normalize land cover proportions, encode foraging guilds, handle missing values, and train a Random Forest (k-fold CV, CPU-only). The script MUST save the trained model to `data/models/random_forest.pkl` and a training metrics log to `data/models/training_metrics.json`. Completion is defined by the existence of these two files with valid content.
- [ ] T020.1 [US2] [FR-005] [FR-008] Update `notebooks/01_analysis.ipynb` to explicitly validate that the 'Across-Species Permutation Test' (shuffling guild labels across species) satisfies the statistical intent of FR-005/FR-008. Add a markdown cell in Section 3.2 titled 'Statistical Methodology' stating the method, and a code cell that asserts the p-value calculation logic matches the spec's intent, confirming that 'Across-Species' is the mathematically valid equivalent of 'stratified by species' for constant labels.
- [ ] T020.2 [US2] [FR-005] [FR-008] Implement `models/validate_permutation_method.py` to explicitly validate that the 'Across-Species Permutation' (shuffling guild labels across species) satisfies the statistical intent of FR-005/FR-008. This script MUST: (1) Simulate a dataset with constant guild labels per species, (2) Perform the 'Across-Species' permutation, (3) Demonstrate mathematically that this method correctly controls for species identity by breaking the species-guild link, and (4) Generate a report confirming this method is the valid equivalent of 'stratified by species' for constant labels. Save the report to `data/models/permutation_validation_report.md`.
- [ ] T020 [US2] [Depends on T019, T020.1, T020.2] Implement `models/evaluate.py` to load the trained model (from T019) and the training metrics. Compute balanced accuracy and per-class F1 scores. Perform the **Across-Species Permutation Test** with 1000 iterations (shuffling guild labels across species). The script MUST compare the observed accuracy against the null distribution to determine if land cover predicts guild independent of species identity. It MUST include a sanity check that the permutation test distribution is not degenerate and raise an error if it is. The script MUST save the evaluation results (p-value, metrics) to `data/models/evaluation_results.json`. **Dependency Note**: This task requires the training metrics from T019 to compute the p-value; thus, T020 must run after T019 completes successfully.
- [ ] T021 [US2] Add logging in `models/evaluate.py` to record p-values, random seeds, and performance metrics against the α = 0.05 threshold.
- [ ] T023 [US2] Implement integration test in `tests/test_integration.py` to ensure `models/train.py` (output: `random_forest.pkl`) and `models/evaluate.py` (output: `evaluation_metrics.json`) work together end-to-end, distinct from the orchestration script T007.
- [ ] T018 [US2] [Depends on T020] Unit test for metric calculations in `projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/tests/test_metrics.py`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualization and Feature Importance Reporting (Priority: P3)

**Goal**: Generate confusion matrix, feature importance chart, spatial map for top species, and a summary report of top land cover predictors per guild.

**Independent Test**: Verify output files (PNG/GeoJSON) exist for the top species and the report lists top predictors per guild with validation.

### Implementation for User Story 3

- [ ] T025 [US3] [Depends on T017, T019, T020, T021] Implement `viz/plot_confusion.py` to load `data/processed/top_25_species_for_viz.json` (from T017) and generate the confusion matrix image (predicted vs actual foraging guilds) for the specified species list. Output filename: `docs/results/confusion_matrix.png`, format: PNG, Figure size: standard dimensions appropriate for publication, colormap: 'viridis'. The script MUST also generate a `docs/results/confusion_matrix_metadata.json` containing the species list used and the confusion matrix data. Completion is defined by the existence of both files.
- [ ] T026 [US3] [Depends on T019, T020, T021] Implement `viz/plot_importance.py` to generate the feature importance bar chart and identify top predictors per guild.
- [ ] T027a [US3] [Depends on T019, T020, T021] Implement `viz/map_habitat.py` (Part A: Inference) to apply the trained model to a spatial grid and generate the continuous raster prediction surface using `rasterio` for raster processing and `numpy` for array operations.
- [ ] T027b [US3] [Depends on T027a] Implement `viz/map_habitat.py` (Part B: Iteration) to iterate over all species listed in `data/processed/top_25_species_for_viz.json` and produce a composite map or a set of individual maps.
- [ ] T027c [US3] [Depends on T027b] Implement `viz/map_habitat.py` (Part C: Validation) to validate that the spatial grid used for prediction covers the actual observation coordinates and does not extrapolate beyond the known data range using `geopandas` for spatial bounds checking. Save the final map to `docs/results/habitat_map.png` or `docs/results/habitat_map.geojson`.
- [ ] T028 [US3] Implement logic in `viz/plot_importance.py` to generate the summary report listing the top land cover predictors for each foraging guild and save to `docs/results/feature_importance_report.md`.
- [ ] T028.5 [US3] [SC-003] Implement `viz/validate_importance.py` to perform a **quantitative comparison** of the generated feature importance rankings against **multiple domain literature sources** (e.g., 'Birds of the World', 'Handbook of the Birds of the World', 'Birds of North America') as defined in `data/metadata.yaml`. For each foraging guild, list the top land cover predictors identified by the model and cross-reference them with the habitat descriptions in the source literature. Generate a **markdown table** with columns: 'Guild', 'Top Predictor', 'Literature Description', 'Overlap Count' (number of top model predictors that appear in the top 3 literature mentions). A 'Match' is recorded if the overlap count is >= 1. Document agreements and divergences in the `feature_importance_report.md`.
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
- [ ] T035 [SC-004] [FR-002] Implement `utils/validate_resources.py` to explicitly measure and log the total pipeline runtime (must be < 6h) and peak memory usage (must be < 7GB) during execution of T007.5. This task depends on T012.6 and T007.5.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output (T016)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 model output

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Data download tasks (T011, T012) MUST complete before selection (T012.5)
- **T012.5 depends on T011 (EBD) and T011.1 (EBD Fallback)**
- Selection (T012.5) MUST complete before merging (T013)
- **T013 depends on T012.5, T012, T012.1, and T008b (guild mapping)**
- Merging (T013) MUST complete before schema validation (T015, T010) and aggregation (T016)
- Aggregation (T016) MUST complete before training (T019)
- Training (T019) MUST complete before evaluation (T020)
- Evaluation (T020) MUST complete before visualization (T025-T028)

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all data download tasks for User Story 1 together:
Task: "Implement data/download_ebd.py to fetch EBD data via verified S3 path"
Task: "Implement data/download_nlcd.py to fetch NLCD 2019 land cover data via USGS S3"
Task: "Implement data/download_guild_source.py to fetch Birds of the World guild data"
Task: "Implement data/download_ebd_fallback.py to fetch EBD fallback subset"
Task: "Implement data/download_nlcd_fallback.py to fetch NLCD fallback"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (verify top 25 species, filtering, and merged data)
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
- **CRITICAL**: Permutation test MUST use 'Across-Species Permutation' (shuffling guild labels across species) to satisfy FR-005's 'stratified by species' constraint and FR-008's control for species identity.
- **CRITICAL**: T012.5 (select top 25) MUST run after T011 and T011.1 to ensure the selection is made from the raw total count as mandated by the spec. T012.5 is NOT parallel-safe with T011/T011.1.
- **CRITICAL**: T020.2 must document and validate the 'Across-Species Permutation' method to ensure compliance with the statistical intent of FR-005/FR-008.
- **CRITICAL**: The `download_nlcd.py` script must implement streaming/chunked processing for raster tiles to ensure the merged dataset fits within the GB RAM limit, as NLCD tiles are large.
- **CRITICAL**: The `download_ebd.py` script must fall back to a verified S3 subset if the official source fails, and must NOT fall back to synthetic data generation if both fail.
- **CRITICAL**: T008a must download the 'Birds of the World' source data from a verified public API or static CSV, and T008b must generate the guild mapping from this downloaded file, including provenance fields (source_citation, extraction_date) to satisfy FR-001.
- **CRITICAL**: T027 must explicitly iterate over all 25 species in `top_25_species_for_viz.json` to generate the spatial map, not just 2.
- **CRITICAL**: T028.5 must perform a quantitative comparison with literature sources from metadata.yaml, using a specific testable rubric (overlap count) to avoid subjectivity.
- **CRITICAL**: T011 must explicitly check for the existence of the `.parquet` files in the S3 bucket and raise a `FileNotFoundError` only if both official and fallback sources fail.
- **CRITICAL**: T013 must implement a retry mechanism with exponential backoff for NLCD tile downloads to handle transient network errors, but must NOT fall back to synthetic data if all retries fail.
- **CRITICAL**: T016 must log the exact number of observations dropped during aggregation due to missing land cover data and the specific reasons for the drop in a structured format.
- **CRITICAL**: T020b must include a sanity check that the permutation test distribution is not degenerate (i.e., not all values are identical) and raise an error if it is.
- **CRITICAL**: T027 must validate that the spatial grid used for prediction covers the actual observation coordinates and does not extrapolate beyond the known data range.
- **CRITICAL**: T019a is NOT parallel-safe with T016; it must wait for T016 to complete.
- **CRITICAL**: T020a is NOT parallel-safe with T019; it must wait for T019 to complete.
- **CRITICAL**: T012.5 must explicitly filter for ≥50 observations FIRST, THEN select top 25, and handle the edge case where <25 valid species exist by proceeding with the available count and logging the shortfall.
- **CRITICAL**: T017 must explicitly depend on T012.5 and use N=25 to ensure visualization scope matches the analysis scope.
- **CRITICAL**: T013 must expand 'land_cover_proportions' into individual columns (e.g., forest_prop) to match the schema validation requirements.
- **CRITICAL**: T012.6 must ensure that the streaming implementation of NLCD tiles does not load the entire raster into memory, adhering to the 7 GB RAM constraint.
- **CRITICAL**: T035 must explicitly validate that the total pipeline runtime is < 6h and peak memory usage is < 7GB.