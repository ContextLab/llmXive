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

- [ ] T001a Initialize `data/` directory: Create directory `projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/data/` using `mkdir -p` and create a `.gitkeep` file inside using `touch.gitkeep`.
- [ ] T001b Initialize `models/` directory: Create directory `projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/models/` using `mkdir -p` and create a `.gitkeep` file inside using `touch.gitkeep`.
- [ ] T001c Initialize `viz/` directory: Create directory `projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/viz/` using `mkdir -p` and create a `.gitkeep` file inside using `touch.gitkeep`.
- [ ] T001d Initialize `notebooks/` directory: Create directory `projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/notebooks/` using `mkdir -p` and create a `.gitkeep` file inside using `touch.gitkeep`.
- [ ] T001e Initialize `utils/` directory: Create directory `projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/utils/` using `mkdir -p` and create a `.gitkeep` file inside using `touch.gitkeep`.
- [ ] T001f Initialize `tests/` directory: Create directory `projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/tests/` using `mkdir -p` and create a `.gitkeep` file inside using `touch.gitkeep`.
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
- [ ] T007.5a Create `run_pipeline.sh` orchestration script skeleton in `projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/` with placeholder steps for each pipeline phase.
- [ ] T007.5b [Depends on T011, T012, T012.5, T013, T016, T019, T020, T025, T026, T027] Implement full `run_pipeline.sh` to orchestrate all data, model, and viz steps in dependency order. The script MUST: (1) execute `code/data/download_ebd.py`, (2) `code/data/download_nlcd.py`, (3) `code/data/select_top_species.py`, (4) `code/data/merge_and_buffer.py`, (5) `code/data/aggregate.py`, (6) `code/models/train.py`, (7) `code/models/evaluate.py`, (8) `code/viz/plot_confusion.py`, (9) `code/viz/plot_importance.py`, and (10) `code/viz/map_habitat.py` sequentially. It MUST implement error handling (stop on first failure), log each step's exit code, and return a non-zero exit code if any step fails. This task depends on the implementation of the downstream scripts to be fully functional.
- [ ] T035 [SC-004] [FR-002] [Depends on T005, T007.5b] Implement `utils/validate_resources.py` to explicitly measure and log the total pipeline runtime (must be < 6h) and peak memory usage (must be < 7GB) during execution of T007.5b. This task depends on T005 and T007.5b.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Extraction and Merging Pipeline (Priority: P1) 🎯 MVP

**Goal**: Extract eBird EBD records for top species, merge with NLCD land cover data within 100m buffers, and filter for statistical power (≥50 obs/species).

**Independent Test**: Verify that the top species are selected., species with <50 observations are excluded, and the output CSV contains complete land cover proportions and assigned foraging guilds.

### Implementation for User Story 1

- [ ] T011 [US1] Implement `data/download_ebd.py` to list the S3 bucket `s3://ebird-data/ebd_release/`, dynamically select the most recent `.parquet` file, download it to `data/raw/ebd_train.csv` (or parquet), and generate checksums in `data/metadata.yaml`. **Primary Source**: The script MUST first attempt to download from the canonical USGS EarthExplorer API (as per Constitution Principle VI). If the primary source fails, it MUST raise a `FileNotFoundError` and NOT fall back to S3 within this task. The fallback is handled by T011.1. <!-- FAILED: unspecified -->
- [ ] T011.1 [US1] [Depends on T011 failure] Implement `data/download_ebd_fallback.py` to explicitly fetch the verified S3 subset `s3://ebird-data/ebd_release/ebd_train_sample.parquet` and save to `data/raw/ebd_train_fallback.parquet`. This task provides the deterministic fallback source for T011.
- [ ] T012 [US1] Implement `data/download_nlcd.py` to fetch NLCD land cover data from the canonical USGS EarthExplorer API (Constitution Principle VI) using a deterministic key pattern for the contiguous US (e.g., `NLCD_2019_Land_Cover_Land_Use_2019.tif`), download tiles to `data/raw/nlcd_2019.zip`, and record the exact version/date of the raster in `data/metadata.yaml`. **Primary Source**: This task MUST attempt the EarthExplorer download first. If it fails, it MUST raise `FileNotFoundError`. The fallback is handled by T012.1. <!-- FAILED: unspecified -->
- [ ] T012.1 [US1] [Depends on T012 failure] Implement `data/download_nlcd_fallback.py` to fetch NLCD 2019 from an alternative verified S3 path (e.g., `s3://usgs-nlcd/nlcd_2019_conus.zip`) and save to `data/raw/nlcd_2019_fallback.zip`. This task provides the deterministic fallback source for T012.
- [ ] T008a [US1] [P] Implement `data/download_guild_source.py` to fetch the 'Birds of the World' foraging guild data from a verified static source defined in `data/metadata.yaml` (e.g., `). Save the result to `data/raw/guild_source.csv`. This task must explicitly download the external literature source to satisfy FR-001 and Constitution Principle VI, and verify that the downloaded file contains a 'source_citation' field confirming its origin as 'Birds of the World'. The source URL must be configurable via `data/metadata.yaml` to ensure reproducibility. The task must support CSV, JSON, or XML formats.
- [ ] T008b [US1] [Depends on T008a] Implement `data/generate_guild_mapping.py` to load `data/raw/guild_source.csv` (from T008a), extract species_id and foraging_guild, and save to `data/processed/guild_mapping.csv`. The output CSV MUST include columns `species_id`, `foraging_guild`, `source_citation`, and `extraction_date` to prove provenance.
- [ ] T012.5 [US1] [Depends on T011, T011.1] Implement `data/select_top_species.py` to load `data/raw/ebd_train.csv` (from T011) OR `data/raw/ebd_train_fallback.parquet` (from T011.1). The logic MUST: (1) Load the full pool of species and count total records per species. (2) Sort the full pool by total record count descending. (3) Select a representative subset of species. (handling ties by including ALL tied species at the 25th rank, potentially resulting in >25 species). (4) Apply the ≥50 observations filter ONLY to this selected subset. If a limited number of valid species exist after filtering, proceed with the available count. and log the shortfall to `data/processed/selection_log.txt`. Save the final list of top species identifiers to `data/processed/top_25_species_ids.json`. This file serves as the single source of truth for both analysis and visualization.
- [ ] T013 [US1] [Depends on T012.5, T012, T012.1, T008b] Implement `data/merge_and_buffer.py` to load `data/raw/ebd_train.csv` (from T011), filter to retain ONLY the species listed in `data/processed/top_25_species_ids.json` (from T012.5), load `data/raw/nlcd_2019.zip` (from T012) OR `data/raw/nlcd_2019_fallback.zip` (from T012.1) if T012 failed, calculate buffer land cover proportions using NLCD 2019 data within **a fixed buffer** (using a projected CRS for deterministic radii), join with `data/processed/guild_mapping.csv` (from T008b) to assign foraging guilds, and save the final result to `data/processed/merged_observations.csv`. The output schema MUST include `species_id`, `foraging_guild`, and **individual columns** for land cover proportions for a defined buffer zone <!-- ATOMIZE: requested -->

The research question remains: What are the land cover proportions within the buffer zone?
The method remains: Remote sensing analysis of land cover classes.
References: [Insert DOI/arXiv/author-year citations here] (e.g., `forest_prop_100m`, `grassland_prop_100m`, `wetland_prop_100m`, `urban_prop_100m`). Embed provenance fields (source URL, version, date) into the output CSV metadata or header comments to satisfy Constitution Principle VI. <!-- [FR-002] [SC-004] -->
- [ ] T015 [US1] [Depends on T013] Implement `validate_schema()` function in `data/merge_and_buffer.py` that raises `ValueError` if columns `species_id`, `foraging_guild`, and individual land cover proportion columns are missing, and add unit test `test_validate_schema` in `tests/test_data_contract.py` to verify the schema validation logic.
- [ ] T010 [US1] [Depends on T013] Validate schema compliance in `projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/tests/test_data_contract.py` by asserting `merged_observations.csv` matches `contracts/dataset.schema.yaml`, specifically validating columns `species_id`, `foraging_guild`, and land cover proportion columns.
- [ ] T016 [US1] [Depends on T013] Implement `data/aggregate.py` to aggregate filtered observations from `data/processed/merged_observations.csv` into species-level profiles and save to `data/processed/species_profiles.csv`. Log the exact number of observations dropped during aggregation due to missing land cover data and the specific reasons for the drop in a structured format: `reason_code` (e.g., 'missing_tile', 'invalid_value', 'out_of_bounds') and `details`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Classification Model Training and Evaluation (Priority: P2)

**Goal**: Train a Random Forest classifier to predict foraging guild from land cover proportions and validate signal via a Stratified Permutation Test.

**Independent Test**: Verify balanced accuracy is measured against chance, per-class F scores are computed, and the permutation test (a sufficient number of iterations) yields p < 0.05.

### Implementation for User Story 2

- [ ] T019 [US2] [Depends on T016] Implement `models/train.py` to load `data/processed/species_profiles.csv` (from T016), normalize land cover proportions, encode foraging guilds, handle missing values, and train a Random Forest (k-fold CV, CPU-only). The script MUST save the trained model to `data/models/random_forest.pkl` and a training metrics log to `data/models/training_metrics.json`. Completion is defined by the existence of these two files with valid content.
- [ ] T020 [US2] [Depends on T019] Implement `models/evaluate.py` to load the trained model (from T019) and the training metrics. Compute balanced accuracy and per-class F1 scores. Perform the **Stratified Permutation Test** (stratified by species) as mandated by FR-005/FR-008. **Note**: If the implementation requires an 'Across-Species Permutation' (shuffling guild labels across species) due to constant labels, this task MUST explicitly check for a 'Spec Amendment' log entry in `data/models/amendment_log.txt` authorizing this deviation. If no amendment is found, the task MUST raise an error. The script MUST compare the observed accuracy against the null distribution to determine if land cover predicts guild independent of species identity. It MUST include a sanity check that the permutation test distribution is not degenerate and raise an error if it is. The script MUST save the evaluation results (p-value, metrics) to `data/models/evaluation_results.json`.
- [ ] T021 [US2] Add logging in `models/evaluate.py` to record p-values, random seeds, and performance metrics against the α = 0.05 threshold.
- [ ] T023 [US2] [Depends on T019, T020] Implement integration test in `tests/test_integration.py` to ensure `models/train.py` (output: `random_forest.pkl`) and `models/evaluate.py` (output: `evaluation_metrics.json`) work together end-to-end, distinct from the orchestration script T007.
- [ ] T018 [US2] [Depends on T020] Unit test for metric calculations in `projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/tests/test_metrics.py`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualization and Feature Importance Reporting (Priority: P3)

**Goal**: Generate confusion matrix, feature importance chart, spatial map for top species, and a summary report of top land cover predictors per guild.

**Independent Test**: Verify output files (PNG/GeoJSON) exist for the top species and the report lists top predictors per guild with validation.

### Implementation for User Story 3

- [ ] T025 [US3] [Depends on T012.5, T019, T020, T021] Implement `viz/plot_confusion.py` to load `data/processed/top_25_species_ids.json` (from T012.5) and generate the confusion matrix image (predicted vs actual foraging guilds) for the specified species list. Output filename: `docs/results/confusion_matrix.png`, format: PNG, Figure size: standard dimensions appropriate for publication, colormap: 'viridis'. The script MUST also generate a `docs/results/confusion_matrix_metadata.json` containing the species list used and the confusion matrix data. Completion is defined by the existence of both files.
- [ ] T026 [US3] [Depends on T019, T020, T021] Implement `viz/plot_importance.py` to generate the feature importance bar chart and identify top predictors per guild.
- [ ] T027 [US3] [Depends on T019, T020, T021] Implement `viz/map_habitat.py` to: (A) Apply the trained model to a spatial grid to generate a continuous raster prediction surface; (B) Iterate over all species listed in `data/processed/top_25_species_ids.json` (from T012.5) and produce a composite map or individual maps; (C) Validate that the spatial grid covers actual observation coordinates and does not extrapolate beyond known data ranges. Save the final map to `docs/results/habitat_map.png` or `docs/results/habitat_map.geojson`.
- [ ] T028 [US3] [Depends on T019, T020, T021] Implement logic in `viz/plot_importance.py` to generate the summary report listing the top land cover predictors for each foraging guild and save to `docs/results/feature_importance_report.md`.
- [ ] T028.5 [US3] [SC-003] [Depends on T028] Implement `viz/validate_importance.py` to perform a **measurable assessment** of the generated feature importance rankings against **domain literature sources** (e.g., 'Birds of the World', 'Handbook of the Birds of the World') as defined in `data/metadata.yaml`. For each foraging guild, List the top land cover predictors. identified by the model and cross-reference them with the A limited set of key habitat descriptors in the source literature. Generate a table in `feature_importance_report.md` showing the overlap count (non-negative integer) for each guild. Flag any guild where the overlap is < 2 as 'Ecological Validity: Low'. The assessment must verify ecological validity using this specific rubric.
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
- **CRITICAL**: Permutation test MUST use 'Stratified by Species' resampling unless a Spec Amendment authorizes 'Across-Species Permutation'.
- **CRITICAL**: T012.5 (select top 25) MUST run after T011 and T011.1 to ensure the selection is made from the raw total count as mandated by the spec. T012.5 is NOT parallel-safe with T011/T011.1.
- **CRITICAL**: The `download_nlcd.py` script must handle NLCD tiles without streaming logic as the dataset fits in RAM.
- **CRITICAL**: T008a must download the 'Birds of the World' source data from a verified public API or static CSV, and T008b must generate the guild mapping from this downloaded file, including provenance fields (source_citation, extraction_date) to satisfy FR-001.
- **CRITICAL**: T027 must explicitly iterate over all species in `top_25_species_ids.json` to generate the spatial map, not just 2.
- **CRITICAL**: T028.5 must perform a measurable assessment with literature sources from metadata.yaml, using a specific testable rubric (overlap count) to avoid subjectivity.
- **CRITICAL**: T011 must explicitly check for the existence of the `.parquet` files in the S3 bucket and raise a `FileNotFoundError` only if both official and fallback sources fail.
- **CRITICAL**: T013 must implement a retry mechanism with exponential backoff for NLCD tile downloads to handle transient network errors, but must NOT fall back to synthetic data if all retries fail.
- **CRITICAL**: T016 must log the exact number of observations dropped during aggregation due to missing land cover data and the specific reasons for the drop in a structured format.
- **CRITICAL**: T020 must include a sanity check that the permutation test distribution is not degenerate (i.e., not all values are identical) and raise an error if it is.
- **CRITICAL**: T027 must validate that the spatial grid used for prediction covers the actual observation coordinates and does not extrapolate beyond the known data range.
- **CRITICAL**: T019a is NOT parallel-safe with T016; it must wait for T016 to complete.
- **CRITICAL**: T020a is NOT parallel-safe with T019; it must wait for T019 to complete.
- **CRITICAL**: T012.5 must explicitly select the top 25 species from the full pool FIRST, THEN apply the ≥50 observations filter to that subset.
- **CRITICAL**: T013 must expand 'land_cover_proportions' into individual columns (e.g., forest_prop) to match the schema validation requirements.
- **CRITICAL**: T035 must explicitly validate that the total pipeline runtime is < 6h and peak memory usage is < 7GB.
- **CRITICAL**: T012.5 tie-breaking: Include ALL tied species at the 25th rank, resulting in N >= 25 species.