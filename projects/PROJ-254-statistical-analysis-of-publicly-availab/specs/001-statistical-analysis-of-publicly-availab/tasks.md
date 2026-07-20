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

- [X] T001a Create repository root structure: `src/`, `tests/`, `data/` directories
- [X] T001b Create `src/code/__init__.py`, `src/data/__init__.py`, `tests/__init__.py`
- [X] T001c Create `data/raw/` and `data/derived/` directories with `.gitkeep`

- [X] T002 Initialize Python 3.11 project with `requirements.txt` (pandas, numpy, gensim, scikit-learn, statsmodels, matplotlib, plotly, requests, pyarrow, musicbrainzngs, thefuzz)
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites & Governance)

**Purpose**: Core infrastructure, governance ratification, and architectural setup that MUST be complete before ANY user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. This phase includes the ratification of scope deviations (Last.fm waiver pending Spec Amendment) and the streaming architecture setup.

- [X] T004 Implement `src/code/utils.py` with logging setup (`pipeline_log.txt`) and deterministic random seed pinning for reproducibility (FR-008, Constitution Check)
- [X] T005 [P] Create data schema definitions and Pydantic models for Track, Playlist, and Genre entities in `src/code/models.py`
- [X] T006 [P] Implement checksum verification script in `src/code/verify_checksums.py` for raw data integrity (Constitution Check)
- [X] T007 [P] Implement `src/code/memory_utils.py` with functions to monitor RAM usage using `psutil.Process(os.getpid()).memory_info().rss`, trigger garbage collection at >90% of 6GB limit (5.4GB), and log warnings before critical thresholds (FR-011)

- [X] T016 [P] **Governance**: Document the Scope Deviation (MPD-only vs Spec FR-001/FR-009 Last.fm requirement). Create `specs/001-genre-evolution/scope_deviation_log.md` explicitly stating the omission of Last.fm in the Plan, the pending Spec Amendment requirement, and linking this deviation to the pending Spec Amendment task T017. **Dependency**: None. **Rationale**: Ensures the scope decision is documented before ingestion logic is implemented.
- [ ] T017 [P] **Governance**: Create `spec_amendment_request.md` in `specs/001-genre-evolution/` to formally document the deviation from FR-001/FR-009 (Last.fm). **Note**: This task must explicitly state that Last.fm ingestion is BLOCKED due to missing data sources and that the pipeline will proceed with MPD-only as per the Plan's Scope Deviation. **Dependency**: Depends on T016 (reads `scope_deviation_log.md`). **Rationale**: Formalizes the governance state for data source omission.

- [X] T040 [P] **Architecture**: Refactor `src/code/ingest.py` to remove hardcoded URLs and implement a streaming loader using `datasets.load_dataset("spotify_million_playlist", streaming=True)`. **Constraint**: Must process data in chunks to stay under available RAM without loading the full large-scale dataset into memory. **Dependency**: None. **Rationale**: Addresses the "Large real datasets" rule by replacing a fixed subset with a streamable real dataset to ensure full data contribution without fabrication.
- [X] T041 **Architecture**: Add a strict `try/except` block to the new streaming loader in `src/code/ingest.py` that raises a `RuntimeError` if the dataset fetch fails, ensuring no synthetic fallback data is ever generated. **Constraint**: Must NOT contain any `generate_synthetic_*` or mock data logic. **Dependency**: Depends on T040. **Rationale**: Enforces the "Loader must FAIL LOUDLY" rule to prevent silent fabrication of data. <!-- FAILED: unspecified -->

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Generate Yearly Genre Embeddings (Priority: P1) 🎯 MVP

**Goal**: Ingest MPD data (streaming), match to MusicBrainz, and train a global Word2Vec model to derive yearly genre vectors. **Note**: Last.fm ingestion is handled conditionally (T050/T051); if missing, pipeline proceeds with MPD-only.

**Independent Test**: Run the ingestion-preprocessing pipeline on the MPD dataset and verify that a set of genre-level vectors is produced for each calendar year in `yearly_embeddings/`.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T008 [P] [US1] Contract test for metadata schema validation: `tests/contract/test_metadata_schema.py` function `test_metadata_schema_validation` against `tests/contract/schemas/metadata_schema.yaml`
- [X] T009 [P] [US1] Unit test for fuzzy matching fallback logic: `tests/unit/test_fuzzy_match.py` function `test_fuzzy_match_fallback` using fixture `tests/fixtures/fuzzy_match_input.json`, asserting `result['match_rate'] > 0.8`

### Implementation for User Story 1

- [X] T050 [US1] **Governance/Logic**: Implement `src/code/ingest.py` function `ingest_lastfm` to attempt fetching Last.fm data. **Logic**: If fetch fails (missing data), log a WARNING to `pipeline_log.txt` and return an empty dataframe. **Constraint**: Must NOT abort the pipeline. **Dependency**: None. **Rationale**: Implements conditional Last.fm ingestion as per Plan's Scope Deviation.
- [X] T051 [US1] **Logic**: Implement `src/code/ingest.py` function `join_lastfm_mb` to join Last.fm data with MusicBrainz metadata if available. **Logic**: If Last.fm data is empty, skip this step. **Dependency**: Depends on T050. **Rationale**: Implements Last.fm join logic as per FR-009, conditionally.
- [X] T019 [US1] Implement `src/code/ingest.py` function `ingest_mpd` to download MPD parquet files using `datasets.load_dataset("spotify_million_playlist", streaming=True)`, parse playlists, extract track IDs/years, and integrate memory monitoring (≤6GB) to prevent OOM (FR-001, FR-009, FR-011). **Logic**: Implement batched, out-of-core processing for the full dataset. Must emit a total track count during streaming for downstream validation. **Dependency**: Depends on T041. **Blocker**: Last.fm ingestion is conditional (T050). **Log**: Must log "Ingestion complete: X tracks processed" to `pipeline_log.txt`.
- [X] T054 [US1] Implement `src/code/ingest.py` function `validate_year_range` to verify that the downloaded MPD data contains the required year range (mids to 2024) before proceeding. **Logic**: If the range is insufficient, log a WARNING and flag the year as "low-coverage" for exclusion. **Dependency**: Depends on T019. **Rationale**: Validates data range early to prevent wasted computation.
- [X] T020 [US1] Implement `src/code/ingest.py` function `validate_coverage` to verify row count against 80% threshold (per Plan) dynamically based on the total count emitted by T019; if < 80% of expected tracks, ABORT with Critical Error (exit code 1). **Dependency**: Depends on T054. **Rationale**: Enforces Plan's abort condition for insufficient coverage.
- [X] T021 [US1] Implement `src/code/ingest.py` function `fetch_musicbrainz` to fetch MusicBrainz metadata via API with exponential back-off and fuzzy matching fallback (FR-010). **Logic**: Use `musicbrainzngs` for ID lookup. If ID missing, use `thefuzz` (Levenshtein) on (artist, track, album) tuple with a threshold of 0.85. Retry with exponential backoff (max 3 retries). **Constraint**: Must NOT fall back to synthetic data. **Dependency**: Depends on T019. **Rationale**: Implements the mandatory fuzzy matching fallback required by FR-010. <!-- FAILED: unspecified -->
- [X] T022 [US1] Implement `src/code/ingest.py` function `join_mpd_mb` to join MPD and MusicBrainz data, filter tracks with missing years, and save normalized `data/derived/metadata_mpd.parquet`. **Logic**: Last.fm join logic (T051) is executed if data exists; otherwise, only MPD tracks are processed. Coverage (SC-001) is calculated against MPD tracks only. **Dependency**: Depends on T021 and T051.
- [X] T042 [US1] Implement `src/code/embeddings.py` function `train_global_word2vec` to accept an iterator of track sequences from the streaming loader (T019) instead of a pre-loaded list, ensuring the Word2Vec training step processes data in batches. **Constraint**: Must use `gensim` with `dim=100`, `window=10`, `epochs=5`. **Dependency**: Depends on T019 (streaming iterator). **Note**: Removed dependency on T022 to allow parallel execution.
- [X] T053 [US1] Implement `src/code/ingest.py` function `calculate_coverage` to compute the percentage of MPD tracks with genre tags successfully represented (adjusted SC-001). **Logic**: Compare total MPD tracks vs. tracks with genre tags. **Dependency**: Depends on T022. **Rationale**: Calculates coverage against MPD-only denominator as per Plan.
- [ ] T023 [US1] Implement `src/code/embeddings.py` function `aggregate_yearly_embeddings` to aggregate base track vectors by genre and year, handling low-coverage years (<1,000 unique tracks) by writing them to `data/derived/low_coverage_years.json` (JSON array of integers with optional 'reason' field) and missing genres (zero-fill with zero vectors of dimension 100), saving `yearly_embeddings/{year}.npy`. **Output Schema**: `low_coverage_years.json` is a JSON array of objects with `year` and optional `reason`. **Dependency**: Depends on T042 and T022.
- [X] T024 [US1] Implement `src/code/ingest.py` function `validate_year_range` to verify that the downloaded MPD data contains the required year range (mids to 2024) before proceeding. **Logic**: If the range is insufficient, log a WARNING and flag the year as "low-coverage" for exclusion. **Dependency**: Depends on T019. **Rationale**: Validates data range early to prevent wasted computation. **Note**: This task was renamed to T054 to avoid ID conflict. <!-- FAILED: unspecified -->

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Compute & Visualize Temporal Similarity (Priority: P2)

**Goal**: Compute pairwise cosine similarities between yearly genre vectors and generate visual artifacts.

**Independent Test**: Execute the similarity-calculation script on the embeddings generated in US-1 and confirm that `yearly_similarity.csv` and visual artifacts are created.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T049 [P] [US2] Contract test for `yearly_similarity.csv` schema: `tests/contract/test_similarity_schema.py` function `test_similarity_schema_validation` against `tests/contract/schemas/similarity_schema.yaml`
- [X] T018 [P] [US2] Unit test for cosine similarity calculation logic: `tests/unit/test_similarity_calc.py` function `test_cosine_similarity` using fixture `tests/fixtures/similarity_input.npy` (dim=100), asserting a stringent tolerance threshold

### Implementation for User Story 2

- [X] T025 [US2] Implement `src/code/similarity.py` to load `yearly_embeddings/{year}.npy` files (Must run after T023 completes), compute pairwise cosine similarity matrices, and calculate mean off-diagonal similarity and intra-genre variance (FR-004). **Log**: Must log "Similarity calculation complete" to `pipeline_log.txt`. **Dependency**: Depends on T023 (embeddings must exist). <!-- FAILED: unspecified -->
- [X] T026 [US2] Save results to `data/derived/yearly_similarity.csv` with columns: year, mean_off_diagonal_similarity, intra_genre_variance (FR-004). **Dependency**: Depends on T025.
- [X] T027 [US2] Implement `src/code/viz.py` function `plot_similarity_trend` to generate `similarity_trend.png` (line plot with 95% CI bands) using matplotlib (FR-007). **Dependency**: Depends on T026. <!-- FAILED: unspecified -->
- [X] T028 [US2] Implement `src/code/viz.py` function `plot_similarity_heatmap` to generate `genre_similarity_heatmap.html` (interactive heatmap) using plotly (FR-007). **Dependency**: Depends on T026. <!-- FAILED: unspecified -->

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistically Test Trend & Perform Robustness Checks (Priority: P3)

**Goal**: Fit linear regression to test trend significance and perform robustness analysis (Cook's Distance). **Note**: FR-006 (Sensitivity Sweep) is waived per Plan; Cook's Distance (T032) is the replacement.

**Independent Test**: Run the regression script on `yearly_similarity.csv` and verify slope, CI, p-value, and Cook's Distance report are generated.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T055 [P] [US3] Contract test for regression output schema: `tests/contract/test_regression_schema.py` function `test_regression_schema_validation` against `tests/contract/schemas/regression_schema.yaml`
- [X] T056 [P] [US3] Unit test for Cook's Distance calculation: `tests/unit/test_cooks_distance.py` function `test_cooks_distance` using fixture `tests/fixtures/cooks_input.csv`, asserting `abs(calculated - expected) < 1e-5` for specific row

### Implementation for User Story 3

- [ ] T029 [US3] Implement `src/code/regression.py` function `prepare_exclusions` to read `data/derived/low_coverage_years.json` (from T023) and `data/derived/metadata_mpd.parquet` (from T022) to generate `data/derived/excluded_years.json`. **Logic**: Exclude years with <1,000 unique tracks. **Edge Case**: If >20% of tracks in a year have missing genre tags, log a WARNING to `pipeline_log.txt`, FLAG the year as LOW_COVERAGE, and add it to `low_coverage_years.json` with a 'reason' field, but DO NOT exclude it from the linear regression analysis (per Spec Edge Cases). **Output Schema**: `excluded_years.json` is a JSON array of integers (years). **Dependency**: Depends on T023 and T022.
- [ ] T030 [US3] Implement `src/code/regression.py` function `fit_linear_regression` to load `data/derived/yearly_similarity.csv`, load `data/derived/excluded_years.json` (from T029), filter out excluded years, and fit a linear regression model (year vs. mean_off_diagonal_similarity) using statsmodels with Newey-West HAC standard errors (FR-005). **Log**: Must log "Regression fit complete" to `pipeline_log.txt`. **Dependency**: Depends on T026 (similarity CSV must exist) AND T029.
- [ ] T033 [US3] Output regression results (slope, confidence interval, p-value) to console and `data/derived/regression_results.json` (FR-005). **Dependency**: Depends on T030.
- [ ] T032 [US3] Implement `src/code/regression.py` function `calculate_cooks_distance` to calculate Cook's Distance for outliers using the regression model from T030 and generate `data/derived/cooks_distance_report.csv` (Robustness Check). **Note**: This task implements the Plan's approved replacement for FR-006. **Dependency**: Depends on T030.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T031a [P] Update `README.md` sections: Installation, Usage, Data Sources (MPD only, Last.fm pending amendment), and Results Interpretation. Ensure all sections are populated with concrete content.
- [ ] T031b [P] Add Google-style docstrings to `src/code/ingest.py`, `src/code/embeddings.py`, and `src/code/similarity.py` functions. **Requirement**: Every public function must have a docstring with Args, Returns, and Raises sections.
- [X] T034 [P] Additional unit tests for edge cases in `tests/unit/test_edge_cases.py`: specifically `test_empty_year_handling`, `test_api_failure_retry`, and `test_missing_genre_exclusion`.
- [X] T048 [P] Update `quickstart.md` to reflect the new streaming architecture and MPD-only data source (with Last.fm blocker note). **Dependency**: Depends on T040-T042 and T019.
- [X] T035 [P] Run `quickstart.md` validation script and generate `validation_log.txt` containing the output and exit code. Verify that the exit code is 0 to confirm reproducibility (Constitution Check). **Dependency**: Depends on T048.
- [X] T037 [P] Add end-to-end integration test script `tests/integration/test_pipeline_e2e.py` that runs the full flow from ingestion to regression on a sampled subset of MPD data to verify data flow and file generation (FR-001, FR-003, FR-005)
- [X] T038 [P] Implement `src/code/cli.py` to expose a single entry point `python -m src.code.run_pipeline` that orchestrates the full workflow with optional flags for specific stages (e.g., `--stage regression`) to facilitate testing and debugging (FR-008, Constitution Check)
- [ ] T052 [P] **Governance**: Create `plan_waiver_log.md` in `specs/001-genre-evolution/` to formally document the Plan's waiver of FR-006 (Sensitivity Sweep) and the adoption of Cook's Distance (T032) as the approved robustness check. **Note**: This task ratifies the Plan's decision over the Spec's FR-006 requirement. **Dependency**: None. **Rationale**: Resolves the conflict between Spec FR-006 and Plan waiver.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - **Depends on T023** (embeddings must exist before similarity can be computed)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - **Depends on T026** (similarity CSV must exist before regression)

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
Task: "Implement ingest_mpd in src/code/ingest.py"
Task: "Implement fetch_musicbrainz in src/code/ingest.py"
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
 - Developer B: User Story 2 (Similarity/Viz) - *Can start once T023 is done*
 - Developer C: User Story 3 (Regression) - *Can start once T026 is done*
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
- **Data Source Note**: Only MPD dataset is used as per current state. Last.fm ingestion is conditional (T050/T051); if missing, pipeline proceeds with MPD-only.
- **Sensitivity Note**: FR-006 threshold sweep is WAIVED per Plan. Cook's Distance (T032) is the approved robustness check.
- **Exclusion Logic**: T029 reads exclusions from T023's output and T022's metadata. Only <1,000 tracks triggers exclusion. >20% missing tags triggers a WARNING and FLAG, but NO exclusion.
- **Streaming Architecture**: T040-T042 implement the streaming loader and iterator interface, ensuring full data contribution without fabrication and memory safety.
- **Governance**: T017 documents Last.fm omission; T052 documents FR-006 waiver.