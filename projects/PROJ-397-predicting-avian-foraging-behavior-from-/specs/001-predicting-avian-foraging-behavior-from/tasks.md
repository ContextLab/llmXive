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

- [ ] T001 [P] Initialize project directory structure: Create `projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/` with subdirectories `data`, `models`, `viz`, `notebooks`, `utils`, `tests`.
- [ ] T002 [P] Create placeholder files `README.md` and `run_pipeline.sh` in `projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/`.
- [ ] T003 [P] Create `requirements.txt` in `projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/` with pinned dependencies: `pandas`, `numpy`, `scikit-learn`, `geopandas`, `rasterio`, `requests`, `matplotlib`, `seaborn`, `pyyaml`, `jupyter`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Implement `utils/config.py` to define paths, random seeds, and constants.
- [ ] T005 [P] Implement `utils/provenance.py` for metadata logging and hash generation.
- [X] T006a [P] Create `tests/test_data_contract.py` with a failing `test_schema_compliance` function stub that asserts `False` and verify `pytest` returns exit code 1.
- [ ] T006b [P] Create `tests/test_metrics.py` with a failing `test_metrics_calc` function stub that asserts `False` and verify `pytest` returns exit code 1.
- [ ] T007 [P] Create `run_pipeline.sh` orchestration script skeleton in `projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/` with placeholder steps for each pipeline phase.
- [ ] T007.5 [P] Implement `run_pipeline.sh` to orchestrate all data, model, and viz steps in dependency order, calling `code/data/download_ebd.py`, `code/data/download_nlcd.py`, `code/data/select_top_species.py`, `code/data/merge_and_buffer.py`, `code/data/aggregate.py`, `code/models/train.py`, `code/models/evaluate.py`, `code/viz/plot_confusion.py`, `code/viz/plot_importance.py`, and `code/viz/map_habitat.py` sequentially.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Extraction and Merging Pipeline (Priority: P1) 🎯 MVP

**Goal**: Extract eBird EBD records for top species, merge with NLCD land cover data within m buffers, and filter for statistical power (≥50 obs/species).

**Independent Test**: Verify that the top species are selected., species with <50 observations are excluded, and the output CSV contains complete land cover proportions and assigned foraging guilds.

### Implementation for User Story 1

- [ ] T011 [P] [US1] Implement `data/download_ebd.py` to list the S3 bucket `s3://ebird-data/ebd_release/`, dynamically select the most recent `.parquet` file, download it to `data/raw/ebd_train.csv` (or parquet), and generate checksums in `data/metadata.yaml`. If the official source fails, automatically fall back to downloading a verified, pre-filtered S3 subset to ensure CI completion. Raise `FileNotFoundError` only if both sources fail.
- [ ] T012 [P] [US1] Implement `data/download_nlcd.py` to fetch NLCD land cover data using the specific dataset ID `NLCD_2019_Land_Cover_Land_Use` via the USGS EarthExplorer verified download URL pattern, download tiles to `data/raw/nlcd_2019.zip`, and record the exact version/date of the raster in `data/metadata.yaml`.
- [ ] T008a [US1] [P] Implement `data/download_guild_source.py` to fetch the 'Birds of the World' foraging guild data from the verified Cornell Lab of Ornithology public URL (or equivalent open access source) and save it to `data/raw/guild_source.csv`. This task must explicitly download the external literature source to satisfy FR-001 and Constitution Principle VI.
- [ ] T008b [US1] [Depends on T008a] Implement `data/generate_guild_mapping.py` to load `data/raw/guild_source.csv` (from T008a), extract species_id and foraging_guild, and save to `data/processed/guild_mapping.csv`. The output CSV MUST include columns `species_id`, `foraging_guild`, `source_citation`, and `extraction_date` to prove provenance.
- [ ] T008c [US1] [P] Implement logic in `data/download_nlcd.py` or a dedicated `data/record_nlcd_provenance.py` script to explicitly record the exact version, date, and source URL of the downloaded NLCD 2019 raster in `data/metadata.yaml` to satisfy Constitution Principle VI (Habitat Data Provenance) for the spatial input.
- [ ] T012.5 [US1] [Depends on T011, T012] Implement `data/select_top_species.py` to load `data/raw/ebd_train.csv` (from T011), **FIRST** filter to retain ONLY species with ≥50 observations, **THEN** sort the filtered list by total record count descending and select a representative subset of top species (handling ties by including all tied species at the specified rank threshold). If fewer than 25 valid species exist, proceed with the available count and log the shortfall to `data/processed/selection_log.txt`. Save the final list of top species identifiers to `data/processed/top_25_species_ids.json`.
- [ ] T013 [US1] [Depends on T012.5, T012, T008b] Implement `data/merge_and_buffer.py` to load `data/raw/ebd_train.csv` (from T011), filter to retain ONLY the species listed in `data/processed/top_25_species_ids.json` (from T012.5), load `data/raw/nlcd_2019.zip` (from T012), calculate buffer land cover proportions using NLCD 2019 data within 100m buffers, join with `data/processed/guild_mapping.csv` (from T008b) to assign foraging guilds, and save the final result to `data/processed/merged_observations.csv`. The output schema MUST include `species_id`, `foraging_guild`, and **individual columns** for land cover proportions (e.g., `forest_prop`, `grass_prop`, `wetland_prop`, `urban_prop`) to match the validation schema. Embed provenance fields (source URL, version, date) into the output CSV metadata or header comments to satisfy Constitution Principle VI.
- [ ] T015 [US1] Implement `validate_schema()` in `data/merge_and_buffer.py` that raises `ValueError` if columns `species_id`, `foraging_guild`, and individual land cover proportion columns are missing, and add unit test `test_validate_schema`. (Depends on T013).
- [ ] T010 [P] [US1] Validate schema compliance in `projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/tests/test_data_contract.py` by asserting `merged_observations.csv` matches `contracts/dataset.schema.yaml`, specifically validating columns `species_id`, `foraging_guild`, and land cover proportion columns (Depends on T013).
- [ ] T016 [US1] Implement `data/aggregate.py` to aggregate filtered observations from `data/processed/merged_observations.csv` into species-level profiles and save to `data/processed/species_profiles.csv`. Log the exact number of observations dropped during aggregation due to missing land cover data and the specific reasons for the drop.
- [ ] T017 [US1] [Depends on T016, T012.5] Implement `data/extract_top_species.py` to extract the **top 25 species** (N=25) by observation count from `data/processed/species_profiles.csv` (reading the list from `data/processed/top_25_species_ids.json` from T012.5) and persist to `data/processed/top_25_species_for_viz.json`. This ensures the visualization scope matches the analysis scope defined in US-1.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Classification Model Training and Evaluation (Priority: P2)

**Goal**: Train a Random Forest classifier to predict foraging guild from land cover proportions and validate signal via a Stratified Permutation Test.

**Independent Test**: Verify balanced accuracy is measured against chance, per-class F1 scores are computed, and the permutation test (a sufficient number of iterations) yields p < 0.05.

### Implementation for User Story 2

- [ ] T019a [US2] [Depends on T016] Implement `models/train.py` (Part A) to load `data/processed/species_profiles.csv` (from T016) and perform data loading and preprocessing: normalize land cover proportions, encode foraging guilds, and handle missing values.
- [ ] T019b [US2] [Depends on T019a] Implement `models/train.py` (Part B) to train a Random Forest (k-fold CV, CPU-only) on the preprocessed data (from T019a) and save the model to `data/models/random_forest.pkl`.
- [ ] T020a [US2] [Depends on T019] Implement `models/evaluate.py` (Part A) to compute balanced accuracy and per-class F1 scores from the trained model.
- [ ] T020b [US2] [Depends on T019] Implement `models/evaluate.py` (Part B) to perform the **Across-Species Permutation Test** with a sufficient number of iterations (1000). This test operates on the **species-level aggregated data** (from T016). For each iteration, **shuffle the foraging guild labels across species** (breaking the species-guild link) while keeping the land cover profiles fixed. Calculate the balanced accuracy for each permuted dataset to generate a null distribution. Compare the observed accuracy against this null distribution to determine if land cover predicts guild independent of species identity. This method satisfies FR-005 and FR-008 by controlling for species identity. Include a sanity check that the permutation test distribution is not degenerate and raise an error if it is.
- [ ] T021 [US2] Add logging in `models/evaluate.py` to record p-values, random seeds, and performance metrics against the α = 0.05 threshold.
- [ ] T021.5 [US2] [FR-005] [FR-008] Update `notebooks/01_analysis.ipynb` to explicitly validate that the 'Across-Species Permutation Test' (shuffling guild labels across species) satisfies the statistical intent of FR-005/FR-008. Add a markdown cell in Section 3.2 titled 'Statistical Methodology' stating the method, and a code cell that asserts the p-value calculation logic matches the spec's intent.
- [ ] T023 [US2] Implement integration test in `tests/test_integration.py` to ensure `models/train.py` (output: `random_forest.pkl`) and `models/evaluate.py` (output: `evaluation_metrics.json`) work together end-to-end, distinct from the orchestration script T007.
- [ ] T018 [P] [US2] Unit test for metric calculations in `projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/tests/test_metrics.py` (Depends on T020a logic).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualization and Feature Importance Reporting (Priority: P3)

**Goal**: Generate confusion matrix, feature importance chart, spatial map for top species, and a summary report of top land cover predictors per guild.

**Independent Test**: Verify output files (PNG/GeoJSON) exist for the top species and the report lists top predictors per guild with validation.

### Implementation for User Story 3

- [ ] T025a [US3] Implement `viz/plot_confusion.py` (Part A) to generate the confusion matrix image (predicted vs actual foraging guilds) for a given species list. Output filename: `docs/results/confusion_matrix.png`, format: PNG, Figure size: standard dimensions appropriate for publication, colormap: 'viridis'.
- [ ] T025b [US3] [Depends on T017, T019, T020, T021] Implement `viz/plot_confusion.py` (Part B) to load `data/processed/top_25_species_for_viz.json` (from T017) and pass the top 2 species to the confusion matrix generator (from T025a).
- [ ] T026 [US3] [Depends on T019, T020, T021] Implement `viz/plot_importance.py` to generate the feature importance bar chart and identify top predictors per guild.
- [ ] T027 [US3] [Depends on T019, T020, T021, T017] Implement `viz/map_habitat.py` to generate a continuous raster prediction surface (GeoJSON/PNG) of high-probability foraging habitats by applying the model to a spatial grid, **strictly filtering the visualization scope to the top 2 species listed in `data/processed/top_25_species_for_viz.json`**. Validate that the spatial grid covers the actual observation coordinates for these species and does not extrapolate beyond the known data range.
- [ ] T028 [US3] Implement logic in `viz/plot_importance.py` to generate the summary report listing the top land cover predictors for each foraging guild and save to `docs/results/feature_importance_report.md`.
- [ ] T028.5 [US3] [SC-003] Implement `viz/validate_importance.py` to perform a **qualitative comparison** of the generated feature importance rankings against the 'Birds of the World' descriptions (from T008a). For each foraging guild, list the top 3 land cover predictors identified by the model and cross-reference them with the habitat descriptions in the source literature. Generate a **markdown table** with columns: 'Guild', 'Top Predictor', 'Literature Description', 'Match/Mismatch' (binary flag based on whether the predictor aligns with the literature description). Document agreements and divergences in the `feature_importance_report.md`. Do NOT calculate a Spearman correlation as no quantitative literature ranking artifact exists; instead, provide a narrative assessment of ecological validity based on the table results.
- [ ] T029 [US3] Update `notebooks/01_analysis.ipynb` to orchestrate the full pipeline, load results, and serve as the Single Source of Truth.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T030 [P] Documentation updates in `docs/` including `quickstart.md`: Add "Installation", "Data Download", and "Running the Pipeline" sections.
- [ ] T031 Code cleanup and refactoring in `code/`: Remove unused imports and refactor `merge_and_buffer.py` to reduce cyclomatic complexity to a maintainable level.
- [ ] T032 Performance optimization: Profile `merge_and_buffer.py` and optimize buffer calculation using vectorization; verify total runtime < 6h.
- [ ] T033 [P] Additional unit tests in `tests/unit/`: Add unit tests for `utils/config.py` and `utils/provenance.py`.
- [ ] T034 [P] Run `quickstart.md` validation: Execute `bash docs/quickstart.md` commands in a fresh venv and verify all artifacts exist.

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
- **T012.5 depends on T011 (EBD) and T012 (NLCD)**
- Selection (T012.5) MUST complete before merging (T013)
- **T013 depends on T012.5, T012, and T008b (guild mapping)**
- Merging (T013) MUST complete before schema validation (T010, T015) and aggregation (T016)
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
Task: "Implement data/download_nlcd.py to fetch NLCD 2019 land cover data via USGS API"
Task: "Implement data/download_guild_source.py to fetch Birds of the World guild data"
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
- **CRITICAL**: T012.5 (select top 25) MUST run after T011 and T012 to ensure the selection is made from the raw total count as mandated by the spec. T012.5 is NOT parallel-safe with T011/T012.
- **CRITICAL**: T021.5 must document and validate the 'Across-Species Permutation' method to ensure compliance with the statistical intent of FR-005/FR-008.
- **CRITICAL**: The `download_nlcd.py` script must implement streaming/chunked processing for raster tiles to ensure the merged dataset fits within the GB RAM limit, as NLCD tiles are large.
- **CRITICAL**: The `download_ebd.py` script must fall back to a verified S3 subset if the official source fails, and must NOT fall back to synthetic data generation if both fail.
- **CRITICAL**: T008a must download the 'Birds of the World' source data, and T008b must generate the guild mapping from this downloaded file, including provenance fields (source_citation, extraction_date) to satisfy FR-001.
- **CRITICAL**: T027 must explicitly filter the spatial map to the top 2 species.
- **CRITICAL**: T028.5 must perform a qualitative comparison with literature sources from metadata.yaml, using a specific testable rubric (markdown table with binary flags) to avoid subjectivity.
- **CRITICAL**: T011 must explicitly check for the existence of the `.parquet` files in the S3 bucket and raise a `FileNotFoundError` only if both official and fallback sources fail.
- **CRITICAL**: T013 must implement a retry mechanism with exponential backoff for NLCD tile downloads to handle transient network errors, but must NOT fall back to synthetic data if all retries fail.
- **CRITICAL**: T016 must log the exact number of observations dropped during aggregation due to missing land cover data and the specific reasons for the drop.
- **CRITICAL**: T020b must include a sanity check that the permutation test distribution is not degenerate (i.e., not all values are identical) and raise an error if it is.
- **CRITICAL**: T027 must validate that the spatial grid used for prediction covers the actual observation coordinates and does not extrapolate beyond the known data range.
- **CRITICAL**: T019a is NOT parallel-safe with T016; it must wait for T016 to complete.
- **CRITICAL**: T020a is NOT parallel-safe with T019; it must wait for T019 to complete.
- **CRITICAL**: T012.5 must explicitly filter for ≥50 observations FIRST, THEN select top 25, and handle the edge case where <25 valid species exist by proceeding with the available count and logging the shortfall.
- **CRITICAL**: T017 must explicitly depend on T012.5 and use N=25 to ensure visualization scope matches the analysis scope.
- **CRITICAL**: T013 must expand 'land_cover_proportions' into individual columns (e.g., forest_prop) to match the schema validation requirements.