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
- [X] T005b [US1] **Define `TrackMetadata` class schema** in `src/code/models.py` to represent the *join keys* and *enrichment status* (e.g., `mb_id`, `genre_tag`, `match_confidence`) without merging them into the native `Track` object. **Dependency**: Depends on T005. **Rationale**: Defines a schema for the join view to distinguish native vs. derived attributes, preventing source leakage per Constitution Principle VI (Cross-Source Independence) by keeping the `Track` model pure until the explicit join step in T022.
- [X] T005c [US1] **Implement validation logic** for `match_confidence` in `src/code/models.py` to ensure values are normalized to a unit interval (0.0 to 1.0). **Dependency**: Depends on T005b. **Rationale**: Isolates validation logic for atomicity.
- [X] T006 [P] Implement checksum verification script in `src/code/verify_checksums.py` for raw data integrity (Constitution Check)
- [X] T007 [P] Implement `src/code/memory_utils.py` with functions to monitor RAM usage using `psutil.Process(os.getpid()).memory_info().rss`, trigger garbage collection at >90% of A defined memory limit (5.4GB), and log warnings before critical thresholds (FR-011)

- [X] T016 [P] **Governance**: Document the Scope Deviation (MPD-only vs Spec FR-001/FR-009 Last.fm requirement). Create `specs/001-genre-evolution/scope_deviation_log.md` explicitly stating the omission of Last.fm in the Plan, the pending Spec Amendment requirement, and linking this deviation to the pending Spec Amendment task T058. **Dependency**: None. **Rationale**: Ensures the scope decision is documented before ingestion logic is implemented.

- [X] T057 **Governance**: Document the deviation from FR-001/FR-009 (Last.fm) and the waiver of FR-006 (Sensitivity Sweep). Create `specs/001-genre-evolution/scope_deviation_log.md` (updated) to explicitly state the MPD-only execution path and the Cook's Distance replacement. **Dependency**: Depends on T016. **Rationale**: Consolidates scope deviation documentation.
- [X] T058 **Governance**: Verify that `spec_amendment_lastfm.md` exists in `specs/001-genre-evolution/` and correctly requests the removal of the Last.fm requirement (FR-001, FR-009) and the adjustment of SC-001 to MPD-only. **Dependency**: Depends on T057. **Rationale**: Formalizes the governance state for data source omission. **Status**: Complete (Spec already amended).
- [X] T059 **Governance**: Verify that `spec_amendment_fr006.md` exists in `specs/001-genre-evolution/` and correctly requests the amendment of FR-006 from "Sensitivity Sweep" to "Cook's Distance Outlier Analysis" as a methodological refinement. **Dependency**: Depends on T057. **Rationale**: Formalizes the governance state for robustness check refinement. **Status**: Complete (Spec already amended).
- [X] T060 **Governance**: Verify that `spec_amendment_sc001.md` exists in `specs/001-genre-evolution/` and correctly requests the adjustment of SC-001 denominator to MPD tracks only. **Dependency**: Depends on T059. **Rationale**: Formalizes the governance state for success criterion adjustment. **Status**: Complete (Spec already amended).

- [X] T052 [P] **Governance**: Define the Cook's Distance replacement logic in `specs/001-genre-evolution/cooks_distance_spec.md` to serve as the source of truth for T032b. **Dependency**: Depends on T059. **Rationale**: Provides the specific implementation details for the Cook's Distance analysis that replaces FR-006.

- [X] T040 [P] **Architecture**: Refactor `src/code/ingest.py` to remove hardcoded URLs and implement a streaming loader using `datasets.load_dataset("spotify_million_playlist", streaming=True)`. **Constraint**: Must process data in chunks to stay under available RAM without loading the full large-scale dataset into memory. **Dependency**: None. **Rationale**: Addresses the "Large real datasets" rule by replacing a fixed subset with a streamable real dataset to ensure full data contribution without fabrication.
- [X] T041 **Architecture**: Add a strict `try/except` block to the new streaming loader in `src/code/ingest.py` that raises a `RuntimeError` if the MPD dataset fetch fails, ensuring no synthetic fallback data is ever generated. **Constraint**: Must NOT contain any `generate_synthetic_*` or mock data logic. **Dependency**: Depends on T040. **Rationale**: Enforces the "Loader must FAIL LOUDLY" rule to prevent silent fabrication of data.

- [X] T061 **Governance**: Finalize and merge `spec_amendment_lastfm.md` (T058) into the main `spec.md` to officially remove the Last.fm 1-Billion requirement from FR-001 and FR-009. **Dependency**: T058, T079. **Rationale**: Aligns the specification with the implemented MPD-only reality to prevent future confusion. **Note**: This task ratifies the Plan's scope deviation ONLY AFTER T079 verifies data sufficiency. **Status**: Complete.
- [X] T062 **Governance**: Finalize and merge `spec_amendment_fr006.md` (T059) into the main `spec.md` to officially amend the "Sensitivity Sweep" requirement to "Cook's Distance Outlier Analysis". **Dependency**: T059, T052. **Rationale**: Ensures the specification mandates the scientifically valid robustness check actually implemented. **Status**: Complete.
- [X] T063 **Governance**: Finalize and merge `spec_amendment_sc001.md` (T060) into the main `spec.md` to adjust Success Criterion SC-001 to reflect the MPD-only denominator. **Dependency**: T060. **Rationale**: Ensures success metrics are measured against the actual available data. **Status**: Complete.
- [X] T064 **Governance**: Implement `src/code/cleanup.py` script to explicitly remove any residual Last.fm import logic, comments, or placeholders from the codebase, ensuring the codebase reflects the MPD-only waiver. **Dependency**: T061. **Rationale**: Ensures the codebase is clean of deprecated logic.
- [X] T065 **Governance**: Update the `state` YAML file's `updated_at` timestamp after T061-T063 complete. **Dependency**: Depends on T061, T062, T063. **Rationale**: Satisfies Constitution Principle V (Versioning Discipline) for every artifact change.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Generate Yearly Genre Embeddings (Priority: P1) 🎯 MVP

**Goal**: Ingest MPD data (streaming), match to MusicBrainz, and train a global Word2Vec model to derive yearly genre vectors. **Note**: The pipeline operates on MPD data only. Last.fm ingestion is WAIVED and removed from the codebase.

**Independent Test**: Run the ingestion-preprocessing pipeline on the MPD dataset and verify that a set of genre-level vectors is produced for each year in `yearly_embeddings/`.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T008 [P] [US1] Contract test for metadata schema validation: `tests/contract/test_metadata_schema.py` function `test_metadata_schema_validation` against `tests/contract/schemas/metadata_schema.yaml`
- [X] T009 [P] [US1] Unit test for fuzzy matching fallback logic: `tests/unit/test_fuzzy_match.py` function `test_fuzzy_match_fallback` using fixture `tests/fixtures/fuzzy_match_input.json`, asserting `result['match_rate'] > 0.8`

### Implementation for User Story 1

- [X] T019 [US1] Implement `src/code/ingest.py` function `ingest_mpd` to download MPD parquet files using `datasets.load_dataset("spotify_million_playlist", streaming=True)`, parse playlists, extract track IDs/years, and integrate memory monitoring (≤6GB) to prevent OOM (FR-001, FR-009, FR-011). **Logic**: Implement batched, out-of-core processing for the full dataset. **Constraint**: Must write total track count to `data/derived/track_count.txt` atomically by writing to a temporary file (e.g., `track_count.txt.tmp`) first, then using `os.replace()` to rename to the final path. **Format**: `track_count.txt` MUST contain a single integer representing the count of unique tracks with valid release years (1950-2024). **Validation**: Must immediately calculate coverage (Tracks with Genre Tags / Total MPD Tracks). **Action**: If coverage < 80%, **DO NOT ABORT**. Instead, write a detailed diagnostic report to `data/derived/coverage_report.json` with the exact schema: `{"total_tracks": int, "covered_tracks": int, "coverage_pct": float, "status": "CRITICAL", "message": "Coverage below 80% threshold"}`. Log "WARNING: Coverage < 80% (X%). Proceeding with data but flagging for review." to `pipeline_log.txt` and set a global flag `COVERAGE_CRITICAL = True`. **Error Handling**: Must raise a `RuntimeError` if the atomic write fails, ensuring downstream tasks do not proceed with missing data. **Requirement**: Must include a complete Google-style docstring detailing the streaming chunk size, memory management strategy, and error handling logic. **Dependency**: Depends on T041. **Blocker**: None. **Log**: Must log "Ingestion complete: X tracks processed" to `pipeline_log.txt` regardless of coverage status.
- [X] T019a [US1] Implement `src/code/embeddings.py` function `generate_track_sequences` to accept the streaming iterator from T019 and yield track sequences (lists of track IDs) in playlist order, ready for Word2Vec. **Constraint**: Must handle streaming chunks without loading full dataset. **Dependency**: Depends on T019. **Rationale**: Explicitly isolates sequence generation for FR-003.
- [X] T021 [US1] Implement `src/code/ingest.py` function `fetch_musicbrainz` to fetch MusicBrainz metadata via API with exponential back-off. **Logic**: Use `musicbrainzngs` for ID lookup. If ID missing, delegate to `match_fuzzy_tracks` (internal helper function within this task) with `threshold=0.85`. Retry with exponential backoff (max limited retries). **Constraint**: Must NOT fall back to synthetic data. **Dependency**: Depends on T019 (to ensure coverage is sufficient), **Depends on T005** (to use Track model for validation), **Depends on T005b** (to use TrackMetadata model). **Rationale**: Implements the mandatory fuzzy matching fallback required by FR-002. **Note**: This task includes the logic for fuzzy matching and application, consolidating previous T021a and T021b.
- [X] T022 [US1] Implement `src/code/ingest.py` function `join_mpd_mb` to join MPD and MusicBrainz data, filter tracks with missing years, and save normalized `data/derived/metadata_mpd.parquet`. **Logic**: Only MPD tracks are processed. Coverage (SC-001) is calculated against MPD tracks only. **Dependency**: Depends on T021, **Depends on T005b** (to use TrackMetadata model). **Rationale**: Implements the join logic using the defined schema.
- [X] T042 [US1] **Logic**: Implement `src/code/embeddings.py` function `train_global_word2vec` to accept an iterator of track sequences from `generate_track_sequences` (T019a) instead of a pre-loaded list, ensuring the Word2Vec training step processes data in batches. **Requirement**: Must use `gensim` with **algorithm='skip-gram'**, `dim=100`, `window=10`, `epochs=5` as **default parameters**, but these MUST be **configurable** via a config file named `config/embeddings.yaml` (YAML format) or CLI arguments (flag: `--embeddings-config`). **Justification**: Skip-gram is preferred for sparse data (common in music sequences) and dim=100 is a standard balance between noise and signal. **Dependency**: Depends on T019a (streaming iterator). **Note**: Removed [P] tag as it consumes T019a's stream.
- [X] T042a [US1] **Documentation**: Create `docs/decisions/001-word2vec-hyperparameters.md` documenting the justification for `algorithm='skip-gram'` and `dim=100` (e.g., literature review, empirical testing) to satisfy "Verified Accuracy" principles. **Dependency**: Depends on T042. **Rationale**: Ensures every parameter choice is justified or pinned to a specific research decision.
- [X] T053 [US1] Implement `src/code/ingest.py` function `calculate_coverage` to compute the percentage of MPD tracks with genre tags successfully represented (adjusted SC-001). **Logic**: Coverage = (Tracks with Genre Tags) / (Total MPD Tracks with Valid Years). **Dependency**: Depends on T022, T063. **Rationale**: Calculates coverage against MPD-only denominator as per Plan.
- [X] T023a [US1] Implement `src/code/embeddings.py` function `aggregate_yearly_embeddings` to aggregate base track vectors by genre and year. **Logic**: Identify years with < 100 unique tracks. **Action**: **DO NOT EXCLUDE** these years. Instead, **flag them** and **return** the list of flagged years as a Python list. **Constraint**: Must NOT include low-coverage years in `yearly_embeddings/` as zero-filled vectors; include them with actual data but flag them for downstream analysis. **Verification**: After aggregation, count remaining years and verify temporal density (e.g., at least 5 consecutive years or >10 years total). If insufficient, log a warning but proceed. **Dependency**: Depends on T042 and T022. **Output**: Intermediate aggregated vectors written to `data/derived/temp_embeddings.npz` and **return value** is the list of flagged years. **Note**: This task returns the list of flagged years but does NOT write to disk.
- [X] T023d [US1] **Logging**: Implement `src/code/embeddings.py` function `log_flagged_years` to accept the list of flagged years **returned by T023a** (call T023a and capture the return value) and write it to `data/derived/flagged_low_coverage_years.json`. **Constraint**: Must be called after T023a completes and must ensure the file is fully flushed before returning. **Dependency**: Depends on T023a. **Rationale**: Ensures transparency of data exclusion and resolves file-write race conditions.
- [X] T023b [US1] Implement `src/code/embeddings.py` function `save_yearly_embeddings` to load aggregated vectors from `data/derived/temp_embeddings.npz` (from T023a) and save to `yearly_embeddings/{year}.npy` files. **Dependency**: Depends on T023a, **T023d**. **Output**: `yearly_embeddings/{year}.npy`. **Constraint**: Must strictly depend on T023d completion and **fail with a clear error if `flagged_low_coverage_years.json` is missing**. **Note**: This task reads `flagged_low_coverage_years.json` (written by T023d) for logging, ensuring the file is fully written before read.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Compute & Visualize Temporal Similarity (Priority: P2)

**Goal**: Compute pairwise cosine similarities between yearly genre vectors and generate visual artifacts.

**Independent Test**: Execute the similarity-calculation script on the embeddings generated in US-1 and confirm that `yearly_similarity.csv` and visual artifacts are created.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T049 [P] [US2] Contract test for `yearly_similarity.csv` schema: `tests/contract/test_similarity_schema.py` function `test_similarity_schema_validation` against `tests/contract/schemas/similarity_schema.yaml`
- [X] T018 [P] [US2] Unit test for cosine similarity calculation logic: `tests/unit/test_similarity_calc.py` function `test_cosine_similarity` using fixture `tests/fixtures/similarity_input.npy` (dim=100), asserting a stringent tolerance threshold

### Implementation for User Story 2

- [X] T025 [US2] Implement `src/code/similarity.py` to load `yearly_embeddings/{year}.npy` files, compute pairwise cosine similarity matrices, and calculate mean off-diagonal similarity and intra-genre variance (FR-004). **Log**: Must log "Similarity calculation complete" to `pipeline_log.txt`. **Dependency**: Depends on T023b (embeddings must exist).
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

- [X] T077 [US3] **Filter Low-Coverage Years**: Implement `src/code/regression.py` function `filter_low_coverage_years` to load `data/derived/yearly_similarity.csv` and `data/derived/flagged_low_coverage_years.json` (from T023d). **Logic**: Remove any year present in `flagged_low_coverage_years.json` from the dataset **before** regression. **Constraint**: Must log the number of filtered years and write the filtered dataset to `data/derived/filtered_similarity.csv`. **Dependency**: Depends on T026, T023d. **Rationale**: Ensures regression is performed only on statistically valid data points, preserving the robustness of FR-005 and preventing noise from low-coverage years from invalidating Cook's Distance analysis.
- [X] T029a [US3] **Calculate Cook's Distance and Generate Report**: Implement `src/code/regression.py` function `calculate_cooks_distance` to load `data/derived/filtered_similarity.csv` (from T077), calculate Cook's Distance for each point, identify points exceeding the threshold $D_i > 4/n$ (where $n$ is the number of observations), and generate `data/derived/cooks_distance_report.csv`. **Logic**: Do NOT exclude years based on track count or arbitrary thresholds; only statistical outliers identified by this threshold are removed in the robustness check. **Constraint**: Must derive `n` from the actual number of data points in `filtered_similarity.csv` **before any outlier filtering**, ensuring independence from metadata quality. **Requirement**: Must generate `data/derived/cooks_distance_report.csv` as a direct output of this task, listing all points and their Cook's Distance values. **Format**: Must create `data/derived/cooks_threshold.json` with keys `{"threshold": <float>, "n": <int>}`. **Constraint**: This task must complete before T030 runs. **Dependency**: Depends on T062, T077, T026. **Output**: `data/derived/cooks_threshold.json`, `data/derived/cooks_distance_report.csv`.
- [X] T030 [US3] Implement `src/code/regression.py` function `fit_linear_regression` to load `data/derived/filtered_similarity.csv` (from T077), load `data/derived/cooks_threshold.json` (from T029a), fit a linear regression model (year vs. mean_off_diagonal_similarity) using statsmodels with Newey-West HAC standard errors (FR-005). **Logic**: Fit the model on ALL **filtered** valid years (excluding low-coverage years per T077) to establish the baseline. **Log**: Must log "Regression fit complete" to `pipeline_log.txt`. **Dependency**: Depends on T026 (similarity CSV must exist) AND T029a AND T077.
- [X] T033 [US3] Output regression results (slope, confidence interval, p-value) to console and `data/derived/regression_results.json` (FR-005). **Dependency**: Depends on T030.
- [X] T032b [US3] **Robustness Check**: Implement `src/code/regression.py` function `re_fit_excluding_outliers` to read `data/derived/cooks_distance_report.csv` (from T029a), identify points exceeding the threshold from T029a, and re-fit the regression excluding these points to confirm trend stability (SC-003). **Constraint**: Must NOT regenerate `cooks_distance_report.csv`; must read it from T029a. **Dependency**: Depends on T030, T029a.
- [X] T032c [US3] **Robustness Validation**: Implement `src/code/regression.py` function `verify_robustness` to compare the p-value from the re-fitted model (T032b) against the threshold p < 0.05 (per SC-002/SC-003). **Logic**: If p-value < 0.05, mark the trend as "Robust"; otherwise "Not Robust". **Output**: Append a `robustness_status` field, `original_slope`, `original_pvalue`, `revised_slope`, and `revised_pvalue` to `data/derived/regression_results.json` and log the conclusion to `pipeline_log.txt`. **Dependency**: Depends on T032b.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T031a [P] Update `README.md` sections: Installation, Usage, Data Sources (MPD only), and Results Interpretation. Ensure all sections are populated with concrete content.
- [X] T031b [P] Add Google-style docstrings to `src/code/ingest.py`, `src/code/embeddings.py`, `src/code/similarity.py`, `src/code/regression.py`, and `src/code/viz.py` functions. **Requirement**: Every public function must have a docstring with Args, Returns, and Raises sections.
- [X] T031c [P] Implement `tests/unit/test_docstring_validation.py` to programmatically verify that all public functions in `src/code/` have docstrings containing 'Args', 'Returns', and 'Raises' sections. **Dependency**: Depends on T031b.
- [X] T034 [P] Additional unit tests for edge cases in `tests/unit/test_edge_cases.py`: specifically `test_empty_year_handling`, `test_api_failure_retry`, and `test_missing_genre_exclusion`.
- [X] T048 [P] Update `quickstart.md` to reflect the streaming architecture and MPD-only data sources. **Dependency**: Depends on T019.
- [X] T035 [P] Run `quickstart.md` validation script and generate `validation_log.txt` containing the output and exit code. Verify that the exit code is 0 to confirm reproducibility (Constitution Check). **Dependency**: Depends on T048.
- [X] T037 [P] Implement `tests/integration/test_pipeline_e2e.py` to run the full flow from ingestion to regression on a sampled subset of MPD data to verify data flow and file generation (FR-001, FR-003, FR-005)
- [X] T038 [P] Implement `src/code/cli.py` to expose a single entry point `python -m src.code.run_pipeline` that orchestrates the full workflow with optional flags for specific stages (e.g., `--stage regression`) to facilitate testing and debugging (FR-008, Constitution Check)
- [X] T071 [P] **Data Flow Ordering**: Refactor `src/code/cli.py` to enforce strict execution order: `ingest` → `embeddings` → `similarity` → `regression`. **Logic**: Add a dependency graph check that prevents `similarity` from running if `embeddings` files are missing, and prevents `regression` from running if `similarity` CSV is missing. **Constraint**: Must raise a `DependencyError` with a clear message if a task is invoked out of order. **Dependency**: Depends on T038. **Rationale**: Prevents the common failure mode where verification scripts run before the data they verify has been computed, ensuring the "task ordering MUST respect data flow" rule is enforced at runtime.

---

## Phase 7: Governance & Spec Alignment (Revision Pass)

**Purpose**: Tasks added to resolve specific review concerns regarding data source consistency, statistical validity, and governance alignment.

### Implementation for Governance Alignment

- [X] T067 [P] **Verification**: Implement a script `verify_spec_amendments.py` that checks if T061, T062, T063 have been applied to `spec.md` by verifying the removal of Last.fm references and the presence of Cook's Distance text. **Dependency**: T061, T062, T063. **Rationale**: Ensures the spec amendments are actually merged.
- [X] T079 [P] **Governance**: Implement `verify_data_sufficiency.py` to verify that the *actual* MPD data volume is sufficient to meet the *original* research intent (spanning multiple decades with diverse genres) **before** T061 is marked complete. **Logic**: Check that the dataset contains at least 30 years of data with >1000 tracks per year. **Constraint**: If insufficient, raise a `GovernanceError` and prevent T061 from completing. **Dependency**: Depends on T019, T022. **Rationale**: Prevents "silent" scope reduction where the project succeeds technically but fails the original research question, satisfying Constitution Principle I (Single Source of Truth).

**Note**: T061-T063 have been moved to Phase 2 to ensure governance precedes implementation. T067 remains in Phase 7 as a verification step. T079 is added to Phase 7 as a prerequisite for T061.

---

## Phase 8: Data Integrity & Execution Safety (Revision Pass)

**Purpose**: Tasks added to address specific execution failures regarding data verification, coverage validation, and synthetic data prevention.

- [X] T068 [US1] **Data Integrity**: Implement `src/code/ingest.py` function `verify_streaming_integrity` to perform a post-streaming sanity check on `data/derived/metadata_mpd.parquet`. **Logic**: Verify that the row count matches the sum of unique tracks processed in `track_count.txt` and that no rows contain null values in critical fields (`track_id`, `release_year`, `genre_tag`). **Constraint**: If input files are missing or invalid, raise `DataIntegrityError` and halt execution. **Dependency**: Depends on T022, T019.
- [X] T070 [US1] **Synthetic Data Guard**: Implement `src/code/analysis.py` function `detect_synthetic_injection` to scan `yearly_embeddings/` and `data/derived/yearly_similarity.csv` for signs of synthetic data. **Logic**: Check for: 1) if any year has 0 variance in similarity, 2) if mean similarity > 0.99, 3) if a year is missing from the time series sequence. If detected, log a CRITICAL error, append a "SYNTHETIC_DATA_DETECTED" flag to `pipeline_log.txt`, and generate `data/derived/synthetic_detection_report.json` documenting the detection step (timestamp, result). **Dependency**: Depends on T023b, T025.

- [X] T070 [US1] **Synthetic Data Guard**: Implement `src/code/analysis.py` function `detect_synthetic_injection` to scan `yearly_embeddings/` and `data/derived/yearly_similarity.csv` for signs of synthetic data. **Logic**: Check for: 1) if any year has 0 variance in similarity (defined as variance < 1e-9), 2) if a year is missing from the time series sequence (gaps in integer year sequence). If detected, log a CRITICAL error, append a "SYNTHETIC_DATA_DETECTED" flag to `pipeline_log.txt`, and generate `data/derived/synthetic_detection_report.json` documenting the detection step (timestamp, result). **Dependency**: Depends on T023b, T025. **Rationale**: Provides a final safety net against the "silent synthetic fallback" failure mode, ensuring the "Real data + real results only" rule is enforced at the output stage. Note: Zero vectors are not generated; this task checks for data gaps instead.

- [X] T078 [US1] **Statistical Distribution Check**: Implement `src/code/analysis.py` function `verify_genre_distribution` to perform a Chi-squared test on the genre tags of the remaining [deferred] (or flagged low-coverage years) to ensure they are not systematically biased (e.g., only easy-to-match tracks). **Logic**: Compare the genre distribution of the full dataset vs. the low-coverage subset. **Constraint**: If p-value < 0.05, log a WARNING and flag the dataset as "POTENTIALLY_BIASED" in `pipeline_log.txt`. **Dependency**: Depends on T022, T023a. **Rationale**: Satisfies Constitution Principle II (Verified Accuracy) by ensuring the dataset meets data quality intent, not just numeric thresholds.

## Phase 9: Final Verification & Reporting (New)

**Purpose**: Tasks to ensure the final output artifacts meet all success criteria and are ready for publication.

- [ ] T071 [US3] **Final Report Generation**: Implement `src/code/report.py` function `generate_final_report` to compile `data/derived/regression_results.json`, `data/derived/cooks_distance_report.csv`, and `data/derived/yearly_similarity.csv` into a single human-readable `data/derived/final_report.md`. **Logic**: The report must include: 1) Executive Summary with trend direction and significance, 2) Methodology section citing Cook's Distance as the robustness check, 3) Data Coverage section confirming MPD-only scope and coverage %, 4) Visualizations (embedded or linked), 5) Limitations section explicitly stating the exclusion of low-coverage years and the Cook's Distance threshold used. **Dependency**: Depends on T032c, T053, T029a.
- [ ] T072 [US3] **Reproducibility Check**: Implement `src/code/repro_check.py` to re-run the entire pipeline from `data/derived/yearly_similarity.csv` (skipping ingestion and embedding) and verify that the regression results match the original run within floating-point tolerance. **Logic**: The script must output a checksum of the final regression results and compare it to a stored baseline. **Dependency**: Depends on T032c.

---

## Phase 9: Execution Readiness & Final Validation (New Revision Pass)

**Purpose**: Final tasks to ensure the pipeline is ready for execution, addressing data flow ordering and explicit dataset documentation requirements.

- [X] T072 [US1] **Dataset Documentation**: Update `README.md` and **update the module docstring in `src/code/ingest.py`** to explicitly state the exact streaming rule used: `datasets.load_dataset("spotify_million_playlist", streaming=True)`, iterating over the full `train` split, and the specific chunking strategy (e.g., `batch_size=1000`). **Logic**: Must include the exact code snippet used for streaming in the documentation. **Dependency**: Depends on T040, T019. **Rationale**: Satisfies the requirement to "State the exact streaming/sampling rule" in the task/documentation, ensuring transparency and reproducibility of the data processing strategy.
- [X] T076 [US1] **Coverage Enforcement**: Implement `src/code/cli.py` to check the `COVERAGE_CRITICAL` flag set by T019. **Logic**: If `COVERAGE_CRITICAL` is True, log "CRITICAL: Coverage < 80%. Aborting pipeline." and exit with code 1 **after** all data processing tasks are complete. **Dependency**: Depends on T019, T038. **Rationale**: Ensures the pipeline "processes" the data first (satisfying SC-001's "process" requirement) and then enforces the success criterion, resolving the logical contradiction in T019.

---

## Phase 10: Execution Safety & Resource Optimization (Revision Pass)

**Purpose**: Tasks added to address specific execution concerns regarding runtime limits, resource constraints, and fail-safe behaviors identified during the analysis phase.

- [ ] T073 [US1] **Execution Safety**: Implement a timeout mechanism in `src/code/ingest.py` for the MusicBrainz API calls using `requests` with a `timeout=10` parameter per request and a global `timeout=300` for the entire **batch operation** (defined as the processing of a single playlist). **Logic**: If the global timeout is exceeded, log a "TIMEOUT_EXCEEDED" warning to `pipeline_log.txt`, save the partial results to `data/derived/partial_metadata_mpd.parquet`, and exit with code 2 (Partial Success) instead of crashing. **Dependency**: Depends on T021. **Rationale**: Prevents the pipeline from hanging indefinitely on API rate limits or network issues, ensuring the 6-hour execution cap is respected.
- [ ] T074 [US1] **Resource Optimization**: Refactor `src/code/embeddings.py` `train_global_word2vec` to explicitly set `workers=2` and `min_count=5` to reduce memory footprint and training time on the free runner. **Logic**: Ensure `workers` is capped at 2 to match the CI runner's CPU core count, preventing thread contention. **Dependency**: Depends on T042. **Rationale**: Optimizes the Word2Vec training for the specific hardware constraints of the free runner (2 cores, ~7GB RAM) to prevent OOM errors during the most memory-intensive phase.
- [ ] T075 [US3] **Statistical Robustness**: Implement a fallback check in `src/code/regression.py` `fit_linear_regression` to detect if the Newey-West HAC correction fails due to insufficient data points (n < 10). **Logic**: If n < 10, log a "HAC_FAILED_INSUFFICIENT_DATA" warning, fall back to standard OLS standard errors, and append a `methodology_note` field to `regression_results.json` stating the fallback was used. **Dependency**: Depends on T030. **Rationale**: Ensures the pipeline produces a result even if the time series is too short for the preferred HAC correction, preventing a hard crash while maintaining transparency about the statistical method used.

**Checkpoint**: Execution safety and resource optimization verified.

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
- **Data Integrity (Phase 8)**: Depends on completion of Ingestion (T019), Join (T022), and Embedding (T023b) tasks.
- **Execution Readiness (Phase 9)**: Depends on completion of CLI (T038) and Ingestion/Embedding tasks (T019, T040).
- **Execution Safety (Phase 10)**: Depends on completion of Ingestion (T021) and Embedding (T042) tasks.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on T023b (embeddings must exist)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on T026 (similarity CSV must exist)

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
- Data Integrity tasks (Phase 8) can be executed in parallel once their specific dependencies (T019, T022, T023b) are complete.
- Execution Readiness tasks (Phase 9) can be executed once CLI and core pipeline tasks are complete.
- Execution Safety tasks (Phase 10) can be executed once their specific dependencies (T021, T042) are complete.

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

### Data Integrity Strategy

1. Implement streaming loader with strict error handling (T019).
2. Add post-processing integrity checks (T068) to verify data completeness.
3. Refactor coverage validation to use explicit denominators (T053).
4. Implement final synthetic data detection (T070) before output generation.

### Execution Readiness Strategy

1. Enforce strict data flow ordering in CLI (T071) to prevent race conditions.
2. Explicitly document streaming rules (T072) to ensure reproducibility and transparency.

### Execution Safety Strategy

1. Implement API timeouts (T073) to prevent hanging.
2. Optimize Word2Vec for 2-core runners (T074) to prevent OOM.
3. Add statistical fallbacks for small n (T075) to prevent crashes.

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
- **Exclusion Logic**: T029a defines the Cook's Distance threshold. No arbitrary track count exclusion is used. Low-coverage years are flagged (T023a) but NOT excluded to prevent selection bias. **However**, T077 explicitly filters them for regression to ensure statistical validity.
- **Streaming Architecture**: T040-T042 implement the streaming loader and iterator interface, ensuring full data contribution without fabrication and memory safety.
- **Governance**: T061-T063 (moved to Phase 2) finalize amendments; T067 verifies the merge. T079 verifies data sufficiency before T061.
- **Data Integrity**: T068-T070 ensure streaming data is complete, coverage is validated correctly, and no synthetic data is injected. T078 adds statistical distribution checks.
- **Execution Readiness**: T071-T072 ensure data flow ordering and explicit documentation of streaming rules. T076 enforces coverage abort post-processing.
- **Execution Safety**: T073-T075 ensure the pipeline respects API timeouts, runner resource limits, and handles edge cases in statistical methods gracefully.