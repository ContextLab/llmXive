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

- [ ] T001a [P] Create directory structure: `projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/{data,models,viz,notebooks,utils,tests}` by running `mkdir -p` and `touch` commands for each subdirectory to ensure the folder hierarchy exists.
- [ ] T001b [P] Create placeholder files: `requirements.txt` (containing base dependencies: pandas, numpy, scikit-learn, geopandas, rasterio, requests, matplotlib, seaborn, pyyaml, jupyter), `run_pipeline.sh`, and `README.md` in `projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/`.
- [ ] T002 Initialize Python 3.11 project: Add `pandas`, `geopandas`, `scikit-learn`, `rasterio`, `requests`, `numpy`, `matplotlib`, `seaborn`, `pyyaml`, `jupyter` to `projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/requirements.txt` and verify `python --version` returns 3.11.x.
- [ ] T003 [P] Configure linting and formatting: Create `pyproject.toml` in `projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/` with `[tool.black] line-length=88` and `[tool.ruff]` rules enabled.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Implement `utils/config.py` to define paths, random seeds, and constants.
- [ ] T005 [P] Implement `utils/provenance.py` for metadata logging and hash generation.
- [ ] T006 [P] Create `tests/test_data_contract.py` with a failing `test_schema_compliance` function stub and `tests/test_metrics.py` with a failing `test_metrics_calc` function stub.
- [ ] T007 Setup `run_pipeline.sh` orchestration script in `projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/` to execute `python data/download_ebd.py && python data/download_nlcd.py && python data/merge_and_buffer.py && python models/train.py && python models/evaluate.py && python viz/plot_confusion.py && python viz/plot_importance.py && python viz/map_habitat.py`.
- [ ] T008 [P] Implement `data/fetch_guild_mapping.py` to download the external foraging guild lookup table from the Cornell Lab of Ornithology (Birds of the World) via the defined HTTPS URL, validate its schema (species_id, foraging_guild), and save to `data/processed/guild_mapping.csv`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Extraction and Merging Pipeline (Priority: P1) 🎯 MVP

**Goal**: Extract eBird EBD records for top 25 species, merge with NLCD 2019 land cover data within 100m buffers, and filter for statistical power (≥50 obs/species).

**Independent Test**: Verify the top 25 species are selected, species with <50 observations are excluded, and the output CSV contains complete land cover proportions and assigned foraging guilds.

### Implementation for User Story 1

- [ ] T011 [P] [US1] Implement `data/download_ebd.py` to fetch EBD data from official eBird HTTPS URL (or verified S3 fallback per Plan 'Risks & Mitigations' if official fails) and generate checksums in `data/metadata.yaml`.
- [ ] T012 [P] [US1] Implement `data/download_nlcd.py` to fetch NLCD 2019 land cover data from USGS EarthExplorer and generate checksums. <!-- FAILED: unspecified -->
- [ ] T012.5 [US1] Implement `data/filter_top_25.py` to load raw EBD data (from T011), calculate record counts per species, select the top 25 species by count, and save the filtered subset to `data/processed/ebd_top25.csv`.
- [ ] T013 [US1] Implement `data/merge_and_buffer.py` to join filtered EBD records (from T012.5) with NLCD data, calculate 100m buffer land cover proportions, and assign foraging guilds by joining with `data/processed/guild_mapping.csv` (produced by T008).
- [ ] T014 [US1] Implement filtering logic in `data/merge_and_buffer.py` to retain only species with ≥50 observations and log excluded species to `data/processed/excluded_species.log`.
- [ ] T015 [US1] Implement `validate_schema()` in `data/merge_and_buffer.py` that raises `ValueError` if columns `species_id`, `foraging_guild`, `land_cover_proportions` are missing, and add unit test `test_validate_schema`.
- [ ] T016 [US1] Implement `data/aggregate.py` to aggregate filtered observations into species-level profiles and save to `data/processed/species_profiles.csv`.
- [ ] T017 [US1] Implement logic to extract the top-ranked species by observation count from `data/processed/species_profiles.csv` and persist to `data/processed/top_species.json`.
- [ ] T010 [P] [US1] Validate schema compliance in `projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/tests/test_data_contract.py` by asserting `merged_observations.csv` matches `contracts/dataset.schema.yaml` (Depends on T014 output).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Classification Model Training and Evaluation (Priority: P2)

**Goal**: Train a Random Forest classifier to predict foraging guild from land cover proportions and validate signal via a Random Guild Permutation Test (Across-Species).

**Independent Test**: Verify balanced accuracy is measured against chance, per-class F1 scores are computed, and the permutation test (1000 iterations) yields p < 0.05.

### Implementation for User Story 2

- [ ] T019 [P] [US2] Implement `models/train.py` to load `data/processed/species_profiles.csv` (from T016), train a Random Forest (5-fold CV, CPU-only), and save the model.
- [ ] T020 [US2] Implement `models/evaluate.py` to compute balanced accuracy and per-class F1 scores.
- [ ] T021 [US2] Implement `models/evaluate.py` Across-Species Permutation test logic with 1000 iterations, shuffling guild labels across species, and calculate p-value against α = 0.05 (1411.7565, https://arxiv.org/abs/1411.7565) threshold. **Note**: This implements the intent of FR-005 (control for species identity) via the plan's "Across-Species" method, as "stratified by species" is mathematically invalid for constant labels.
- [ ] T021.5 [US2] Update `notebooks/01_analysis.ipynb` to explicitly document the statistical rationale for using Across-Species Permutation instead of "stratified by species" in Section 3.2, referencing FR-008.
- [ ] T022 [US2] Add logging in `models/evaluate.py` to record p-values, random seeds, and performance metrics against the α = 0.05 threshold.
- [ ] T023 [US2] Integrate `models/train.py` and `models/evaluate.py` into the pipeline to ensure the model is trained on the filtered dataset from US1.
- [ ] T018 [P] [US2] Unit test for metric calculations in `projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/tests/test_metrics.py` (Depends on T020 logic).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualization and Feature Importance Reporting (Priority: P3)

**Goal**: Generate confusion matrix, feature importance chart, spatial map for top species, and a summary report of top land cover predictors per guild.

**Independent Test**: Verify output files (PNG/GeoJSON) exist for the top species and the report lists top predictors per guild.

### Implementation for User Story 3

- [ ] T025 [US3] Implement `viz/plot_confusion.py` to generate the confusion matrix image (predicted vs actual foraging guilds) for the top 2 species (using model from T019). (Depends on T019, T020, T021).
- [ ] T026 [US3] Implement `viz/plot_importance.py` to generate the feature importance bar chart and identify top predictors per guild. (Depends on T019, T020, T021).
- [ ] T027 [US3] Implement `viz/map_habitat.py` to generate a continuous raster prediction surface (GeoJSON/PNG) of high-probability foraging habitats by applying the model to a spatial grid, filtering the visualization scope to a subset of priority species listed in `data/processed/top_species.json`.
- [ ] T028 [US3] Implement logic in `viz/plot_importance.py` to generate the summary report listing the top land cover predictors for each foraging guild and save to `docs/results/feature_importance_report.md`.
- [ ] T029 [US3] Update `notebooks/01_analysis.ipynb` to orchestrate the full pipeline, load results, and serve as the Single Source of Truth.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T030 [P] Documentation updates in `docs/` including `quickstart.md`: Add "Installation", "Data Download", and "Running the Pipeline" sections.
- [ ] T031 Code cleanup and refactoring in `code/`: Remove unused imports and refactor `merge_and_buffer.py` to reduce cyclomatic complexity below 10.
- [ ] T032 Performance optimization: Profile `merge_and_buffer.py` and optimize buffer calculation using vectorization; verify total runtime < 6h.
- [ ] T033 [P] Additional unit tests in `tests/unit/`: Add unit tests for `utils/config.py` and `utils/provenance.py`.
- [ ] T034 Run `quickstart.md` validation: Execute `bash docs/quickstart.md` commands in a fresh venv and verify all artifacts exist.

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
- Data download tasks (T011, T012) MUST complete before filtering (T012.5)
- Filtering (T012.5) MUST complete before merging (T013)
- Merging (T013) MUST complete before filtering (T014)
- Filtering (T014) MUST complete before aggregation (T016)
- Aggregation (T016) MUST complete before training (T019)
- Training (T019) MUST complete before evaluation (T020, T021)
- Evaluation (T020, T021) MUST complete before visualization (T025-T028)

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
Task: "Implement data/download_ebd.py to fetch EBD data via HTTPS or verified S3 fallback"
Task: "Implement data/download_nlcd.py to fetch NLCD 2019 land cover data from USGS EarthExplorer"
Task: "Implement data/fetch_guild_mapping.py to download external guild lookup"
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
- **CRITICAL**: Permutation test must use Across-Species shuffling to control for species identity, as "stratified by species" is mathematically invalid for constant labels.