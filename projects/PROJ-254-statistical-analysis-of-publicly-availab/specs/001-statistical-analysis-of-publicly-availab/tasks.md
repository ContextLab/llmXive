---
description: "Task list template for feature implementation"
---

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

- [X] T002 Initialize Python project with `requirements.txt` (pandas, numpy, gensim, scikit-learn, statsmodels, matplotlib, plotly, requests, pyarrow, musicbrainzngs, thefuzz)
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites & Governance)

**Purpose**: Core infrastructure, governance ratification, and architectural setup that MUST be complete before ANY user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. This phase includes the ratification of scope deviations (Last.fm waiver) and the streaming architecture setup.

- [X] T004 Implement `src/code/utils.py` with logging setup (`pipeline_log.txt`) and deterministic random seed pinning for reproducibility (FR-008, Constitution Check)
- [X] T005 [P] Create data schema definitions and Pydantic models for `Track` (native MPD fields only) and `Playlist` entities in `src/code/models.py`. **Constraint**: Do NOT include `Genre` here. **Dependency**: None. **Rationale**: Separates native data from enriched attributes to satisfy Constitution Principle III (Data Hygiene).
- [X] T005b [US1] Create Pydantic model `TrackMetadata` in `src/code/models.py` to represent the *join keys* and *enrichment status* (e.g., `mb_id`, `genre_tag`, `match_confidence`) without merging them into the native `Track` object. **Dependency**: Depends on T005. **Rationale**: Defines a schema for the join view to distinguish native vs. derived attributes, preventing source leakage per Constitution Principle VI (Cross-Source Independence) by keeping the `Track` model pure until the explicit join step in T022.
- [X] T006 [P] Implement checksum verification script in `src/code/verify_checksums.py` for raw data integrity (Constitution Check)
- [X] T007 [P] Implement `src/code/memory_utils.py` with functions to monitor RAM usage using `psutil.Process(os.getpid()).memory_info().rss`, trigger garbage collection at >90% of 6GB limit (5.4GB), and log warnings before critical thresholds (FR-011)

- [X] T016 [P] **Governance**: Document the Scope Deviation (MPD-only vs Spec FR-001/FR-009 Last.fm requirement). Create `specs/001-genre-evolution/scope_deviation_log.md` explicitly stating the omission of Last.fm in the Plan, the pending Spec Amendment requirement, and linking this deviation to the pending Spec Amendment task T058. **Dependency**: None. **Rationale**: Ensures the scope decision is documented before ingestion logic is implemented.

- [X] T057 [P] **Governance**: Document the deviation from FR-001/FR-009 (Last.fm) and the waiver of FR-006 (Sensitivity Sweep). Create `specs/001-genre-evolution/scope_deviation_log.md` (updated) to explicitly state the MPD-only execution path and the Cook's Distance replacement. **Dependency**: Depends on T016. **Rationale**: Consolidates scope deviation documentation.

- [X] T058 [P] **Governance**: Verify that `spec_amendment_lastfm.md` exists in `specs/001-genre-evolution/` and correctly requests the removal of the Last.fm requirement (FR-001, FR-009) and the adjustment of SC-001 to MPD-only. **Dependency**: Depends on T057. **Rationale**: Formalizes the governance state for data source omission. **Status**: Complete (Spec already amended).
- [X] T059 **Governance**: Verify that `spec_amendment_fr006.md` exists in `specs/001-genre-evolution/` and correctly requests the amendment of FR-006 from "Sensitivity Sweep" to "Cook's Distance Outlier Analysis" as a methodological refinement. **Dependency**: Depends on T057. **Rationale**: Formalizes the governance state for robustness check refinement. **Status**: Complete (Spec already amended).
- [X] T060 [P] **Governance**: Verify that `spec_amendment_sc001.md` exists in `specs/001-genre-evolution/` and correctly requests the adjustment of SC-001 denominator to MPD tracks only. **Dependency**: Depends on T060. **Rationale**: Formalizes the governance state for success criterion adjustment. **Status**: Complete (Spec already amended).

- [X] T052 [P] **Governance**: Define the Cook's Distance replacement logic in `specs/001-genre-evolution/cooks_distance_spec.md` to serve as the source of truth for T032b. **Dependency**: Depends on T059. **Rationale**: Provides the specific implementation details for the Cook's Distance analysis that replaces FR-006.

- [X] T040 [P] **Architecture**: Refactor `src/code/ingest.py` to remove hardcoded URLs and implement a streaming loader using `datasets.load_dataset("spotify_million_playlist", streaming=True)`. **Constraint**: Must process data in chunks to stay under available RAM without loading the full large-scale dataset into memory. **Dependency**: None. **Rationale**: Addresses the "Large real datasets" rule by replacing a fixed subset with a streamable real dataset to ensure full data contribution without fabrication.
- [X] T041 **Architecture**: Add a strict `try/except` block to the new streaming loader in `src/code/ingest.py` that raises a `RuntimeError` if the MPD dataset fetch fails, ensuring no synthetic fallback data is ever generated. **Constraint**: Must NOT contain any `generate_synthetic_*` or mock data logic. **Dependency**: Depends on T040. **Rationale**: Enforces the "Loader must FAIL LOUDLY" rule to prevent silent fabrication of data. <!-- FAILED: unspecified -->

- [X] T061 [P] **Governance**: Finalize and merge `spec_amendment_lastfm.md` (T058) into the main `spec.md` to officially remove the Last.fm 1-Billion requirement from FR-001 and FR-009. **Dependency**: T058. **Rationale**: Aligns the specification with the implemented MPD-only reality to prevent future confusion. **Note**: This task ratifies the Plan's scope deviation. **Status**: Complete.
- [X] T062 [P] **Governance**: Finalize and merge `spec_amendment_fr006.md` (T059) into the main `spec.md` to officially amend the "Sensitivity Sweep" requirement to "Cook's Distance Outlier Analysis". **Dependency**: T059, T052. **Rationale**: Ensures the specification mandates the scientifically valid robustness check actually implemented. **Status**: Complete.
- [X] T063 [P] **Governance**: Finalize and merge `spec_amendment_sc001.md` (T060) into the main `spec.md` to adjust Success Criterion SC-001 to reflect the MPD-only denominator. **Dependency**: T060. **Rationale**: Ensures success metrics are measured against the actual available data. **Status**: Complete.
- [X] T064 [P] **Governance**: Implement `src/code/cleanup.py` script to explicitly remove any residual Last.fm import logic, comments, or placeholders from the codebase, ensuring the codebase reflects the MPD-only waiver. **Dependency**: T061. **Rationale**: Ensures the codebase is clean of deprecated logic.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Generate Yearly Genre Embeddings (Priority: P1) 🎯 MVP

**Goal**: Ingest MPD data (streaming), match to MusicBrainz, and train a global Word2Vec model to derive yearly genre vectors. **Note**: The pipeline operates on MPD data only. Last.fm ingestion is WAIVED and removed from the codebase.

**Independent Test**: Run the ingestion-preprocessing pipeline on the MPD dataset and verify that a set of genre-level vectors is produced for each calendar year in `yearly_embeddings/`.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T008 [P] [US1] Contract test for metadata schema validation: `tests/contract/test_metadata_schema.py` function `test_metadata_schema_validation` against `tests/contract/schemas/metadata_schema.yaml`
- [X] T009 [P] [US1] Unit test for fuzzy matching fallback logic: `tests/unit/test_fuzzy_match.py` function `test_fuzzy_match_fallback` using fixture `tests/fixtures/fuzzy_match_input.json`, asserting `result['match_rate'] > 0.8`

### Implementation for User Story 1

- [ ] T019 [US1] Implement `src/code/ingest.py` function `ingest_mpd` to download MPD parquet files using `datasets.load_dataset("spotify_million_playlist", streaming=True)`, parse playlists, extract track IDs/years, and integrate memory monitoring (≤6GB) to prevent OOM (FR-001, FR-009, FR-011). **Logic**: Implement batched, out-of-core processing for the full dataset. **Constraint**: Must write total track count to `data/derived/track_count.txt` atomically upon completion. **Format**: `track_count.txt` MUST contain a single integer representing the count of unique tracks with valid release years (1950-2024). Must handle streaming errors by raising a clear `RuntimeError` (no silent fallback). **Requirement**: Must include a complete Google-style docstring detailing the streaming chunk size, memory management strategy, and error handling logic. **Dependency**: Depends on T041. **Blocker**: None. **Log**: Must log "Ingestion complete: X tracks processed" to `pipeline_log.txt`.
- [X] T019a [US1] Implement `src/code/embeddings.py` function `generate_track_sequences` to accept the streaming iterator from T019 and yield track sequences (lists of track IDs) in playlist order, ready for Word2Vec. **Constraint**: Must handle streaming chunks without loading full dataset. **Dependency**: Depends on T019. **Rationale**: Explicitly isolates sequence generation for FR-003.
- [ ] T019b [US1] Implement `src/code/ingest.py` function `verify_track_count_file` to check existence and format of `data/derived/track_count.txt` before T020 attempts to read it. **Constraint**: Must raise `FileNotFoundError` if missing. **Dependency**: Depends on T019. **Rationale**: Ensures deterministic fail condition for SC-001 validation.
- [X] T054 [US1] Implement `src/code/ingest.py` function `validate_year_range` to verify that the downloaded MPD data contains the required historical year range before proceeding. **Logic**: If the range is insufficient, log a WARNING and flag the year as "low-coverage" for exclusion. **Dependency**: Depends on T019. **Rationale**: Validates data range early to prevent wasted computation.
- [ ] T020 [US1] Implement `src/code/ingest.py` function `validate_coverage` to verify row count against % threshold (per Plan) dynamically based on the total count of unique tracks with valid release years (mid-20th century to 2024) read from `data/derived/track_count.txt` (from T019) and verified by T019b; if < 80% of total MPD tracks, ABORT with Critical Error (exit code 1). **Constraint**: Must strictly read the count from `track_count.txt` and abort if the file is missing or the count is insufficient. **Denominator**: The denominator is the total count of unique tracks in the MPD dataset with valid release years (1950-2024). **Dependency**: Depends on T019, T019b. **Rationale**: Enforces Plan's abort condition for insufficient coverage with explicit denominator definition. **Note**: This implements SC-001 as a binary pass/fail. <!-- FAILED: unspecified -->
- [X] T021 [US1] Implement `src/code/ingest.py` function `fetch_musicbrainz` to fetch MusicBrainz metadata via API with exponential back-off. **Logic**: Use `musicbrainzngs` for ID lookup. If ID missing, delegate to `match_fuzzy_tracks` (T021a) with `threshold=0.85`. Retry with exponential backoff (max limited retries). **Constraint**: Must NOT fall back to synthetic data. **Dependency**: Depends on T019, **Depends on T005** (to use Track model for validation). **Rationale**: Implements the mandatory fuzzy matching fallback required by FR-002.
- [X] T021a [US1] Implement `src/code/ingest.py` function `match_fuzzy_tracks` to perform fuzzy matching of (artist, track, album) tuples using `thefuzz` with a strict `threshold=0.85`. **Constraint**: Must return match confidence and ID. **Dependency**: Depends on T021. **Rationale**: Isolates the fuzzy matching logic for FR-002.
- [X] T021b [US1] Implement `src/code/ingest.py` function `apply_matching_logic` to encapsulate the decision tree for selecting the best MusicBrainz match (ID lookup vs. fuzzy match vs. exclusion) as a standalone unit. **Constraint**: Must be testable independently of network calls. **Dependency**: Depends on T021, T021a. **Rationale**: Isolates the matching logic for FR-002 to ensure it is a verifiable unit.
- [X] T022 [US1] Implement `src/code/ingest.py` function `join_mpd_mb` to join MPD and MusicBrainz data, filter tracks with missing years, and save normalized `data/derived/metadata_mpd.parquet`. **Logic**: Only MPD tracks are processed. Coverage (SC-001) is calculated against MPD tracks only. **Dependency**: Depends on T021, **Depends on T005b** (to use TrackMetadata model). **Rationale**: Implements the join logic using the defined schema.
- [X] T042 [US1] **Logic**: Implement `src/code/embeddings.py` function `train_global_word2vec` to accept an iterator of track sequences from `generate_track_sequences` (T019a) instead of a pre-loaded list, ensuring the Word2Vec training step processes data in batches. **Constraint**: Must use `gensim` with **algorithm='skip-gram'**, `dim=100`, `window=10`, `epochs=5`. **Justification**: Skip-gram is preferred for sparse data (common in music sequences) and dim=100 is a standard balance between noise and signal. **Dependency**: Depends on T019a (streaming iterator). **Note**: Removed [P] tag as it consumes T019a's stream.
- [X] T042a [US1] **Documentation**: Create `docs/decisions/001-word2vec-hyperparameters.md` documenting the justification for `algorithm='skip-gram'` and `dim=100` (e.g., literature review, empirical testing) to satisfy "Verified Accuracy" principles. **Dependency**: Depends on T042. **Rationale**: Ensures every parameter choice is justified or pinned to a specific research decision.
- [X] T053 [US1] Implement `src/code/ingest.py` function `calculate_coverage` to compute the percentage of MPD tracks with genre tags successfully represented (adjusted SC-001). **Logic**: Compare total MPD tracks (valid tracks with year 1950-2024) vs. tracks with genre tags. **Dependency**: Depends on T022, T063. **Rationale**: Calculates coverage against MPD-only denominator as per Plan. <!-- FAILED: unspecified -->
- [X] T023a [US1] Implement `src/code/embeddings.py` function `aggregate_yearly_embeddings` to aggregate base track vectors by genre and year. **Logic**: Identify years with <unique tracks. **Action**: EXCLUDE these years from the final aggregated vectors to prevent synthetic data fabrication. Do NOT generate zero-filled vectors. Log the excluded years to `data/derived/excluded_years.json`. **Constraint**: Must NOT include low-coverage years in `yearly_embeddings/`. **Dependency**: Depends on T042 and T022. **Output**: Intermediate aggregated vectors written to `data/derived/temp_embeddings.npz`. **Note**: This task writes `excluded_years.json` for logging.
- [X] T023d [US1] **Logging**: Implement `src/code/embeddings.py` function `log_excluded_years` to write the list of excluded low-coverage years to `data/derived/excluded_years.json`. **Constraint**: Must be called after T023a completes. **Dependency**: Depends on T023a. **Rationale**: Ensures transparency of data exclusion.
- [X] T023c [US1] **Robustness**: Implement `src/code/analysis.py` function `validate_synthetic_impact` to compare the similarity trend with and without the synthetic (zero-filled) years and log the difference. **Dependency**: Depends on T023a, T026. **Rationale**: Validates the impact of synthetic vectors on the trend line to satisfy SC-003 robustness. **Note**: Since T023a now excludes low-coverage years, this task verifies that the exclusion does not significantly alter the trend compared to a hypothetical inclusion.
- [X] T023b [US1] Implement `src/code/embeddings.py` function `save_yearly_embeddings` to load aggregated vectors from `data/derived/temp_embeddings.npz` (from T023a) and save to `yearly_embeddings/{year}.npy` files. **Dependency**: Depends on T023a. **Output**: `yearly_embeddings/{year}.npy`. **Note**: This task reads `excluded_years.json` (written by T023a) for logging, does not overwrite it.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Compute & Visualize Temporal Similarity (Priority: P2)

**Goal**: Compute pairwise cosine similarities between yearly genre vectors and generate visual artifacts.

**Independent Test**: Execute the similarity-calculation script on the embeddings generated in US-1 and confirm that `yearly_similarity.csv` and visual artifacts are created.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T049 [P] [US2] Contract test for `yearly_similarity.csv` schema: `tests/contract/test_similarity_schema.py` function `test_similarity_schema_validation` against `tests/contract/schemas/similarity_schema.yaml`
- [X] T018 [P] [US2] Unit test for cosine similarity calculation logic: `tests/unit/test_similarity_calc.py` function `test_cosine_similarity` using fixture `tests/fixtures/similarity_input.npy` (dim=100), asserting a stringent tolerance threshold

### Implementation for User Story 2

- [X] T025 [US2] Implement `src/code/similarity.py` to load `yearly_embeddings/{year}.npy` files (Must run after T023b completes), compute pairwise cosine similarity matrices, and calculate mean off-diagonal similarity and intra-genre variance (FR-004). **Log**: Must log "Similarity calculation complete" to `pipeline_log.txt`. **Dependency**: Depends on T023b (embeddings must exist).
- [X] T026 [US2] Save results to `data/derived/yearly_similarity.csv` with columns: year, mean_off_diagonal_similarity, intra_genre_variance (FR-004). **Dependency**: Depends on T025.
- [X] T027 [US2] Implement `src/code/viz.py` function `plot_similarity_trend` to generate `similarity_trend.png` (line plot with % CI bands) using matplotlib (FR-007). **Dependency**: Depends on T026.
- [X] T028 [US2] Implement `src/code/viz.py` function `plot_similarity_heatmap` to generate `genre_similarity_heatmap.html` (interactive heatmap) using plotly (FR-007). **Dependency**: Depends on T026.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistically Test Trend & Perform Robustness Checks (Priority: P3)

**Goal**: Fit linear regression to test trend significance and perform robustness analysis using Cook's Distance (FR-006, SC-003). **Note**: The Sensitivity Sweep requirement (FR-006 old) has been WAIVED. Only Cook's Distance is implemented.

**Independent Test**: Run the regression script on `yearly_similarity.csv` and verify slope, CI, p-value, and Cook's Distance report are generated.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T055 [P] [US3] Contract test for regression output schema: `tests/contract/test_regression_schema.py` function `test_regression_schema_validation` against `tests/contract/schemas/regression_schema.yaml`
- [X] T056 [P] [US3] Unit test for Cook's Distance calculation: `tests/unit/test_cooks_distance.py` function `test_cooks_distance` using fixture `tests/fixtures/cooks_input.csv`, asserting `abs(calculated - expected) < 1e-5` for specific row

### Implementation for User Story 3

- [X] T029a [US3] **Robustness Check Definition**: Implement `src/code/regression.py` function `define_exclusion_criteria` to explicitly define the Cook's Distance threshold as $D_i > 4/n$ (where $n$ is the number of observations) and output this threshold to `data/derived/cooks_threshold.json`. **Logic**: Do NOT exclude years based on track count or arbitrary thresholds; only statistical outliers identified by this threshold are removed in the robustness check. **Constraint**: Must derive `n` from the actual number of data points in `yearly_similarity.csv` **before any outlier filtering**, ensuring independence from metadata quality. **Requirement**: Must generate `data/derived/cooks_distance_report.csv` as a direct output of this task, listing all points and their Cook's Distance values. **Format**: `cooks_threshold.json` must contain a JSON object: `{"threshold": <float>, "n": <int>}`. **Dependency**: Depends on T062. **Output**: `data/derived/cooks_threshold.json`, `data/derived/cooks_distance_report.csv`.
- [X] T030 [US3] Implement `src/code/regression.py` function `fit_linear_regression` to load `data/derived/yearly_similarity.csv`, load `data/derived/cooks_threshold.json` (from T029a), fit a linear regression model (year vs. mean_off_diagonal_similarity) using statsmodels with Newey-West HAC standard errors (FR-005). **Logic**: Fit the model on ALL valid years first (including low-coverage years) to establish the baseline. **Log**: Must log "Regression fit complete" to `pipeline_log.txt`. **Dependency**: Depends on T026 (similarity CSV must exist) AND T029a.
- [X] T033 [US3] Output regression results (slope, confidence interval, p-value) to console and `data/derived/regression_results.json` (FR-005). **Dependency**: Depends on T030.
- [X] T032b [US3] **Robustness Check**: Implement `src/code/regression.py` function `calculate_cooks_distance` to read `data/derived/cooks_distance_report.csv` (from T029a), identify points exceeding the threshold from T029a, and re-fit the regression excluding these points to confirm trend stability (SC-003). **Constraint**: Must NOT regenerate `cooks_distance_report.csv`; must read it from T029a. **Dependency**: Depends on T030, T029a, T059. **Rationale**: Implements the Cook's Distance analysis as the approved robustness check per Spec Amendment T062.
- [X] T032c [US3] **Robustness Validation**: Implement `src/code/regression.py` function `verify_robustness` to compare the p-value from the re-fitted model (T032b) against the A statistically significant threshold will be applied.. **Logic**: If p-value < 0.05, mark the trend as "Robust"; otherwise "Not Robust". **Output**: Append a `robustness_status` field to `data/derived/regression_results.json` and log the conclusion to `pipeline_log.txt`. **Dependency**: Depends on T032b. **Rationale**: Explicitly satisfies SC-003 by recording the robustness conclusion.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T031a [P] Update `README.md` sections: Installation, Usage, Data Sources (MPD only), and Results Interpretation. Ensure all sections are populated with concrete content.
- [X] T031b [P] Add Google-style docstrings to `src/code/ingest.py`, `src/code/embeddings.py`, `src/code/similarity.py`, `src/code/regression.py`, and `src/code/viz.py` functions. **Requirement**: Every public function must have a docstring with Args, Returns, and Raises sections. **Note**: Added `regression.py` and `viz.py` to ensure documentation coverage for statistical logic and visualization outputs.
- [X] T031c [P] Implement `tests/unit/test_docstring_validation.py` to programmatically verify that all public functions in `src/code/` have docstrings containing 'Args', 'Returns', and 'Raises' sections. **Dependency**: Depends on T031b. **Rationale**: Ensures documentation quality is verifiable.
- [X] T034 [P] Additional unit tests for edge cases in `tests/unit/test_edge_cases.py`: specifically `test_empty_year_handling`, `test_api_failure_retry`, and `test_missing_genre_exclusion`.
- [X] T048 [P] Update `quickstart.md` to reflect the streaming architecture and MPD-only data sources. **Dependency**: Depends on T040-T042 and T019.
- [X] T035 [P] Run `quickstart.md` validation script and generate `validation_log.txt` containing the output and exit code. Verify that the exit code is 0 to confirm reproducibility (Constitution Check). **Dependency**: Depends on T048.
- [X] T037 [P] Add end-to-end integration test script `tests/integration/test_pipeline_e2e.py` that runs the full flow from ingestion to regression on a sampled subset of MPD data to verify data flow and file generation (FR-001, FR-003, FR-005)
- [X] T038 [P] Implement `src/code/cli.py` to expose a single entry point `python -m src.code.run_pipeline` that orchestrates the full workflow with optional flags for specific stages (e.g., `--stage regression`) to facilitate testing and debugging (FR-008, Constitution Check)

---

## Phase 7: Governance & Spec Alignment (Revision Pass)

**Purpose**: Tasks added to resolve specific review concerns regarding data source consistency, statistical validity, and governance alignment.

### Implementation for Governance Alignment

- [X] T067 [P] **Verification**: Implement a script `verify_spec_amendments.py` that checks if T061, T062, T063 have been applied to `spec.md` by verifying the removal of Last.fm references and the presence of Cook's Distance text. **Dependency**: T061, T062, T063. **Rationale**: Ensures the spec amendments are actually merged.

**Note**: T061-T063 have been moved to Phase 2 to ensure governance precedes implementation. T067 remains in Phase 7 as a verification step.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Governance (Phase 7)**: Depends on completion of relevant User Story tasks and Spec Amendments.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - **Depends on T023b** (embeddings must exist before similarity can be computed)
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
- Governance tasks (Phase 7) can be executed in parallel once their specific dependencies (T058, T059, T060) are complete.

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
 - Developer B: User Story 2 (Similarity/Viz) - *Can start once T023b is done*
 - Developer C: User Story 3 (Regression) - *Can start once T026 is done*
3. Stories complete and integrate independently

### Governance Strategy

1. Identify scope deviations (Last.fm, FR-006) early.
2. Draft amendment documents (T058, T059, T060) in parallel with implementation.
3. Finalize amendments (T061, T062, T063) in Phase 2 to ensure spec/code alignment before coding begins.
4. Implement runtime checks (T067) to enforce governance decisions.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Data Source Note**: Pipeline is MPD-only. Last.fm ingestion is WAIVED and removed.
- **Robustness Note**: Only Cook's Distance (T032b) is implemented. Sensitivity Sweep is WAIVED.
- **Exclusion Logic**: T029a defines the Cook's Distance threshold. No arbitrary track count exclusion is used. Low-coverage years are excluded (T023a) to prevent synthetic data.
- **Streaming Architecture**: T040-T042 implement the streaming loader and iterator interface, ensuring full data contribution without fabrication and memory safety.
- **Governance**: T061-T063 (moved to Phase 2) finalize amendments; T067 verifies the merge.

---
