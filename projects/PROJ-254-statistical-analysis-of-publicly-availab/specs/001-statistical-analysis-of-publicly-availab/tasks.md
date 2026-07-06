# Tasks: Statistical Analysis of Publicly Available Music Streaming Data for Genre Evolution

**Input**: Design documents from `/specs/001-genre-evolution/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this story belongs to (e.g., US1, US2, US3)
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

- [X] T001a Create repository root structure: `src/`, `tests/`, `data/` directories <!-- FAILED: unspecified -->
- [X] T001b Create `src/code/__init__.py`, `src/data/__init__.py`, `tests/__init__.py`
- [X] T001c Create `data/raw/` and `data/derived/` directories with `.gitkeep`

- [X] T002 Initialize Python 3.11 project with `requirements.txt` (pandas, numpy, gensim, scikit-learn, statsmodels, matplotlib, plotly, requests, pyarrow)
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `src/code/utils.py` with logging setup (`pipeline_log.txt`) and deterministic random seed pinning for reproducibility (FR-008, Constitution Check)
- [X] T005 [P] Create data schema definitions and Pydantic models for Track, Playlist, and Genre entities in `src/code/models.py`
- [ ] T006 [P] Implement checksum verification script in `src/code/verify_checksums.py` for raw data integrity (Constitution Check) <!-- FAILED: unspecified -->
- [X] T007 [P] Implement `src/code/memory_utils.py` with functions to monitor RAM usage, trigger garbage collection at >90% of 6GB limit (5.4GB), and log warnings before critical thresholds (FR-011)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Generate Yearly Genre Embeddings (Priority: P1) 🎯 MVP

**Goal**: Ingest MPD data, match to MusicBrainz, and train a global Word2Vec model to derive yearly genre vectors. (Note: Last.fm data is waived per plan.md).

**Independent Test**: Run the ingestion-preprocessing pipeline on a sample of the MPD dataset and verify that a set of genre-level vectors is produced for each calendar year in `yearly_embeddings/`.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T008 [P] [US1] Contract test for metadata schema validation: `tests/contract/test_metadata_schema.py` function `test_metadata_schema_validation` against `tests/contract/schemas/metadata_schema.yaml`
- [X] T009 [P] [US1] Unit test for fuzzy matching fallback logic: `tests/unit/test_fuzzy_match.py` function `test_fuzzy_match_fallback` using fixture `tests/fixtures/fuzzy_match_input.json`, asserting `result['match_rate'] > 0.8`

### Implementation for User Story 1

- [ ] T010 [US1] Implement `src/code/ingest.py` function `ingest_mpd` to download MPD parquet files from ` Name or service not known)"))], parse playlists, extract track IDs/years, and integrate memory monitoring (≤6GB) to prevent OOM (FR-001, FR-009, FR-011) <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested -->
- [ ] T011 [US1] Implement `src/code/ingest.py` function `fetch_musicbrainz` to fetch MusicBrainz metadata via API with exponential back-off and fuzzy matching fallback (FR-010)
- [ ] T012 [US1] Implement `src/code/ingest.py` function `join_mpd_mb` to join MPD and MusicBrainz data, filter tracks with missing years, and save normalized `data/derived/metadata_mpd.parquet` (FR-001, FR-002, FR-009, FR-010)
- [ ] T013 [US1] Implement `src/code/embeddings.py` function `train_global_word2vec` to load metadata in batches, generate track sequences (playlists), and train a single global Word2Vec model (gensim, dim=100, window=10, epochs=5) producing base track vectors, with integrated memory management (FR-003, FR-011)
- [ ] T014 [US1] Implement `src/code/embeddings.py` function `aggregate_yearly_embeddings` to aggregate base track vectors by genre and year, handling low-coverage years (<1,000 unique tracks) by flagging them (not excluding entirely yet) and missing genres (zero-fill), saving `yearly_embeddings/{year}.npy` (FR-003, Edge Cases)
- [~] T015 [US1] Add logging for ingestion stats (match rates, exclusion rates) and explicit warning logic: `if missing_genre_rate > 0.2: log warning` to `pipeline_log.txt` (FR-008, Edge Cases)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Compute & Visualize Temporal Similarity (Priority: P2)

**Goal**: Compute pairwise cosine similarities between yearly genre vectors and generate visual artifacts.

**Independent Test**: Execute the similarity-calculation script on the embeddings generated in US-1 and confirm that `yearly_similarity.csv` and visual artifacts are created.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [~] T017 [P] [US2] Contract test for `yearly_similarity.csv` schema: `tests/contract/test_similarity_schema.py` function `test_similarity_schema_validation` against `tests/contract/schemas/similarity_schema.yaml`
- [~] T018 [P] [US2] Unit test for cosine similarity calculation logic: `tests/unit/test_similarity_calc.py` function `test_cosine_similarity` using fixture `tests/fixtures/similarity_input.npy` (dim=100), asserting a stringent tolerance threshold

### Implementation for User Story 2

- [~] T019 [US2] Implement `src/code/similarity.py` to load `yearly_embeddings/{year}.npy` files, compute pairwise cosine similarity matrices, and calculate mean off-diagonal similarity and intra-genre variance (FR-004)
- [~] T020 [US2] Save results to `data/derived/yearly_similarity.csv` with columns: year, mean_off_diagonal_similarity, intra_genre_variance (FR-004)
- [~] T021 [US2] Implement `src/code/viz.py` to generate `similarity_trend.png` (line plot with 95% CI bands) using matplotlib (FR-007)
- [~] T022 [US2] Implement `src/code/viz.py` to generate `genre_similarity_heatmap.html` (interactive heatmap) using plotly (FR-007)
- [~] T023 [US2] Add error handling for missing embedding files and logging of visualization generation status to `pipeline_log.txt` (FR-008)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistically Test Trend & Perform Robustness Checks (Priority: P3)

**Goal**: Fit linear regression to test trend significance and perform robustness analysis (Cook's Distance). Note: FR-006 sensitivity sweep is waived per plan.md.

**Independent Test**: Run the regression script on `yearly_similarity.csv` and verify slope, CI, p-value, and Cook's Distance report are generated.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [~] T024 [P] [US3] Contract test for regression output schema: `tests/contract/test_regression_schema.py` function `test_regression_schema_validation` against `tests/contract/schemas/regression_schema.yaml`
- [~] T025 [P] [US3] Unit test for Cook's Distance calculation: `tests/unit/test_cooks_distance.py` function `test_cooks_distance` using fixture `tests/fixtures/cooks_input.csv`, asserting `abs(calculated - expected) < 1e-5` for specific row

### Implementation for User Story 3

- [~] T029 [US3] Implement `src/code/regression.py` function `flag_low_coverage` to identify years with <1,000 unique tracks (flag for exclusion from regression only) and years with >20% missing genre tags (log warning), without creating a separate filtered artifact (Edge Cases). Logic: 1) Filter tracks with missing genre tags and log warning if >20%. 2) Count remaining unique tracks; if <1,000, flag year for regression exclusion.
- [~] T026 [US3] Implement `src/code/regression.py` function `fit_linear_regression` to load `data/derived/yearly_similarity.csv`, internally filter out flagged low-coverage years, and fit a linear regression model (year vs. mean_off_diagonal_similarity) using statsmodels with robust standard errors (FR-005) <!-- FAILED: unspecified -->
- [~] T027 [US3] Output regression results (slope, 95% CI, p-value) to console and `data/derived/regression_results.json` (FR-005)
- [~] T036 [US3] Implement `src/code/regression.py` function `calculate_cooks_distance` to calculate Cook's Distance for outliers using the regression model from T026 and generate `data/derived/cooks_distance_report.csv` (Robustness Check, replacing waived FR-006)
- [~] T030 [US3] Add comprehensive logging of model parameters, convergence status, and outlier counts to `pipeline_log.txt` (FR-008)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [~] T031a Update `README.md` sections: Installation, Usage, Data Sources, and Results Interpretation
- [~] T031b Add docstrings to `src/code/ingest.py`, `src/code/embeddings.py`, and `src/code/similarity.py` functions
- [~] T032a Refactor batch processing logic in `src/code/ingest.py` for modularity
- [~] T032b Refactor memory management logic in `src/code/embeddings.py` for clarity
- [~] T033a Implement chunked loading for MPD parquet files (chunk size: k) in `src/code/ingest.py`
- [~] T034 [P] Additional unit tests for edge cases (empty years, API failures) in `tests/unit/`
- [~] T035 Run `quickstart.md` validation to ensure end-to-end reproducibility <!-- FAILED: unspecified -->

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - **Depends on T014** (embeddings must exist before similarity can be computed)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - **Depends on T020** (similarity CSV must exist before regression)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

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
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for metadata schema validation in tests/contract/test_metadata_schema.py"
Task: "Unit test for fuzzy matching fallback logic in tests/unit/test_fuzzy_match.py"

# Launch all models for User Story 1 together:
Task: "Implement src/code/ingest.py to download MPD parquet files"
Task: "Implement src/code/ingest.py logic to fetch MusicBrainz metadata"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (verify `yearly_embeddings/` exists)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (requires US1 output)
4. Add User Story 3 → Test independently → Deploy/Demo (requires US2 output)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Ingest/Embed)
 - Developer B: User Story 2 (Similarity/Viz) - *Can start once T014 is done*
 - Developer C: User Story 3 (Regression) - *Can start once T020 is done*
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
- **Data Source Note**: Only MPD dataset is used as per plan.md waiver of Last.fm.
- **Sensitivity Note**: FR-006 threshold sweep is waived; Cook's Distance analysis (T036) is implemented as the robustness check per plan.md.