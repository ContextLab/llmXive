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

- [ ] T001 [P] Initialize project directory structure: Create `projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/` with subdirectories `data`, `models`, `viz`, `notebooks`, `utils`, `tests` and create placeholder files `requirements.txt`, `run_pipeline.sh`, and `README.md`.
- [ ] T002a [P] Verify Python 3.11.x is available in the environment by running `python --version` and ensuring the output matches the major.minor version 3.11.
- [ ] T002b [P] Create `requirements.txt` in `projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/` with pinned dependencies: `pandas`, `numpy`, `scikit-learn`, `geopandas`, `rasterio`, `requests`, `matplotlib`, `seaborn`, `pyyaml`, `jupyter`.
- [ ] T003 [P] Configure linting and formatting: Create `pyproject.toml` in `projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/` with `[tool.black] line-length=88` and `[tool.ruff]` rules enabled.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Implement `utils/config.py` to define paths, random seeds, and constants.
- [ ] T005 [P] Implement `utils/provenance.py` for metadata logging and hash generation.
- [ ] T006a [P] Create `tests/test_data_contract.py` with a failing `test_schema_compliance` function stub.
- [ ] T006b [P] Create `tests/test_metrics.py` with a failing `test_metrics_calc` function stub.
- [ ] T007 Setup `run_pipeline.sh` orchestration script in `projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/` to execute `python data/download_ebd.py && python data/download_nlcd.py && python data/merge_and_buffer.py --part A && python data/merge_and_buffer.py --part B && python data/aggregate.py && python models/train.py && python models/evaluate.py && python viz/plot_confusion.py && python viz/plot_importance.py && python viz/map_habitat.py`.
- [ ] T008 [P] [US1] Implement `data/generate_guild_mapping.py` to scrape or load the verified 'Birds of the World' source (as defined in `data/metadata.yaml` Verified Datasets), extract species_id and foraging_guild, and save to `data/processed/guild_mapping.csv`. The output CSV MUST include columns `species_id`, `foraging_guild`, `source_citation`, and `extraction_date` to prove provenance. {{claim:c_a1c3e9cf}} <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Extraction and Merging Pipeline (Priority: P1) 🎯 MVP

**Goal**: Extract eBird EBD records for top species, merge with NLCD 2019 land cover data within 100m buffers, and filter for statistical power (≥50 obs/species).

**Independent Test**: Verify the top 25 species are selected, species with <50 observations are excluded, and the output CSV contains complete land cover proportions and assigned foraging guilds.

### Implementation for User Story 1

- [ ] T011 [P] [US1] Implement `data/download_ebd.py` to fetch EBD data from the verified S3 bucket `s3://ebird-data/ebd_release/EBD_rel_2023-12-01.parquet` (or the specific verified fallback defined in the plan) and generate checksums in `data/metadata.yaml`. <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->
- [ ] T012 [P] [US1] Implement `data/download_nlcd.py` to fetch NLCD 2019 land cover data using the specific dataset ID `NLCD_2019_Land_Cover_Land_Use` via the USGS EarthExplorer verified download URL pattern defined in `data/metadata.yaml` and generate checksums.
- [ ] T012.5 [US1] Implement `data/select_top_species.py` to load `data/raw/ebd_train.csv` (from T011), calculate record counts per species, sort by count descending, and select a representative subset of species. **Tie-breaking rule**: If multiple species have the same count at the 25th rank, select the one with the alphabetically earliest species_id. Save the list of top species identifiers to `data/processed/top_species_ids.json`.
- [ ] T014 [US1] Implement `data/filter_observations.py` to load `data/raw/ebd_train.csv` (from T011), filter to retain ONLY the species listed in `data/processed/top_25_species_ids.json` (from T012.5), and further filter to retain only records where the species has ≥50 observations in the filtered set. Save the result to `data/processed/ebd_filtered.csv`.
- [ ] T013a [US1] Implement `data/merge_and_buffer.py` (Part A) to load `data/processed/ebd_filtered.csv` (from T014), calculate buffer land cover proportions using NLCD 2019 data (from T012) within 100m buffers, and save the intermediate result to `data/processed/merged_observations_intermediate.csv`. The output schema MUST include `species_id`, `observation_id`, `lat`, `lon`, `land_cover_proportions` (dict of class:proportion).
- [ ] T013b [US1] Implement `data/merge_and_buffer.py` (Part B) to join the intermediate merged data (from T013a) with `data/processed/guild_mapping.csv` (from T008) to assign foraging guilds, saving the final result to `data/processed/merged_observations.csv`.
- [ ] T015 [US1] Implement `validate_schema()` in `data/merge_and_buffer.py` that raises `ValueError` if columns `species_id`, `foraging_guild`, `land_cover_proportions` are missing, and add unit test `test_validate_schema`. (Depends on T013b).
- [ ] T010 [P] [US1] Validate schema compliance in `projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/tests/test_data_contract.py` by asserting `merged_observations.csv` matches `contracts/dataset.schema.yaml`, specifically validating columns `species_id`, `foraging_guild`, and `land_cover_proportions` (Depends on T013b).
- [ ] T016 [US1] Implement `data/aggregate.py` to aggregate filtered observations from `data/processed/merged_observations.csv` into species-level profiles and save to `data/processed/species_profiles.csv`.
- [ ] T017 [US1] Implement `data/extract_top_species.py` to extract the top 2 species by observation count from `data/processed/species_profiles.csv` and persist to `data/processed/top_species.json`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Classification Model Training and Evaluation (Priority: P2)

**Goal**: Train a Random Forest classifier to predict foraging guild from land cover proportions and validate signal via a Stratified Permutation of Land Cover Features within Species.

**Independent Test**: Verify balanced accuracy is measured against chance, per-class F1 scores are computed, and the permutation test (1000 iterations) yields p < 0.05.

### Implementation for User Story 2

- [ ] T019a [P] [US2] Implement `models/train.py` (Part A) to load `data/processed/species_profiles.csv` (from T016) and perform data loading and preprocessing for training.
- [ ] T019b [US2] Implement `models/train.py` (Part B) to train a Random Forest (k-fold CV, CPU-only) on the preprocessed data (from T019a) and save the model to `data/models/random_forest.pkl`.
- [ ] T020a [P] [US2] Implement `models/evaluate.py` (Part A) to compute balanced accuracy and per-class F1 scores from the trained model.
- [ ] T020b [US2] Implement `models/evaluate.py` (Part B) to perform the **Stratified Permutation of Land Cover Features within Species** (1000 iterations). This test shuffles the `land_cover_proportions` values *within* each species group while keeping the `foraging_guild` labels fixed, to assess if land cover predicts guild independent of species-specific habitat preferences. {{claim:c_4dcf4ba6}} (Wikipedia: P-value, https://en.wikipedia.org/wiki/P-value) **Note**: This satisfies FR-005's 'stratified by species' constraint and FR-008's control for species identity.
- [ ] T021 [US2] Add logging in `models/evaluate.py` to record p-values, random seeds,and performance metrics against the α = 0.05 threshold.
- [ ] T021.5 [US2] [FR-005] [FR-008] Update `notebooks/01_analysis.ipynb` to explicitly validate that the 'Stratified Permutation of Land Cover Features within Species' method satisfies the statistical intent of FR-005/FR-008. Add a markdown cell in Section 3.2 titled 'Statistical Methodology' stating the method, and a code cell that asserts the p-value calculation logic matches the spec's intent.
- [ ] T023 [US2] Implement integration test in `tests/test_integration.py` to ensure `models/train.py` (output: `random_forest.pkl`) and `models/evaluate.py` (output: `evaluation_metrics.json`) work together end-to-end, distinct from the orchestration script T007.
- [ ] T018 [P] [US2] Unit test for metric calculations in `projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/tests/test_metrics.py` (Depends on T020a logic).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualization and Feature Importance Reporting (Priority: P3)

**Goal**: Generate confusion matrix, feature importance chart, spatial map for top 2 species, and a summary report of top land cover predictors per guild.

**Independent Test**: Verify output files (PNG/GeoJSON) exist for the top 2 species and the report lists top predictors per guild with validation.

### Implementation for User Story 3

- [ ] T025a [US3] Implement `viz/plot_confusion.py` (Part A) to generate the confusion matrix image (predicted vs actual foraging guilds) for a given species list.
- [ ] T025b [US3] Implement `viz/plot_confusion.py` (Part B) to load `data/processed/top_species.json` (from T017) and pass the top-ranked species to the confusion matrix generator (from T025a). (Depends on T017, T019, T020, T021).
- [ ] T026 [US3] Implement `viz/plot_importance.py` to generate the feature importance bar chart and identify top predictors per guild. (Depends on T019, T020, T021).
- [ ] T027 [US3] Implement `viz/map_habitat.py` to generate a continuous raster prediction surface (GeoJSON/PNG) of high-probability foraging habitats by applying the model to a spatial grid, **filtering the visualization scope to a limited set of top-ranked species listed in `data/processed/top_species.json`**.
- [ ] T028 [US3] Implement logic in `viz/plot_importance.py` to generate the summary report listing the top land cover predictors for each foraging guild and save to `docs/results/feature_importance_report.md`.
- [ ] T028.5 [US3] [SC-003] Implement `viz/validate_importance.py` to compare the generated feature importance rankings against the specific literature sources listed in `data/metadata.yaml` (e.g., 'Smith et al. 2020', 'Birds of the World'). Calculate a 'correlation match score' (percentage of top 3 predictors matching literature) and assert it is ≥66%. Append the validation results and pass/fail status to `docs/results/feature_importance_report.md`.
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
- Data download tasks (T011, T012) MUST complete before filtering (T014)
- Selecting top species (T012.5) MUST complete before filtering (T014) to ensure the correct pool is used
- Filtering (T014) MUST complete before merging (T013a)
- Merging (T013a) MUST complete before guild assignment (T013b)
- Guild assignment (T013b) MUST complete before schema validation (T010, T015) and aggregation (T016)
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
Task: "Implement data/generate_guild_mapping.py to load verified local guild lookup"
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
- **CRITICAL**: Permutation test must use 'Stratified Permutation of Land Cover Features within Species' to satisfy FR-005's 'stratified by species' constraint and FR-008's control for species identity.
- **CRITICAL**: T012.5 (select top 25) MUST run before T014 (filter ≥50) to ensure the selection is made from the raw total count as mandated by the spec.
- **CRITICAL**: T021.5 must document and validate the 'Stratified Permutation of Land Cover Features within Species' method to ensure compliance with the statistical intent of FR-005/FR-008.
- **CRITICAL**: The `download_nlcd.py` script must implement streaming/chunked processing for raster tiles to ensure the merged dataset fits within the GB RAM limit, as NLCD tiles are large.
- **CRITICAL**: The `download_ebd.py` script must fail loudly (raise exception) if the verified S3 source is unreachable, and must NOT fall back to synthetic data generation.
- **CRITICAL**: T008 must generate the guild mapping from 'Birds of the World' and include provenance fields (source_citation, extraction_date) to satisfy FR-001.
- **CRITICAL**: T027 must explicitly filter the spatial map to the top 2 species.
- **CRITICAL**: T028.5 must use specific literature sources from metadata.yaml and a quantitative pass/fail threshold (≥66% match).