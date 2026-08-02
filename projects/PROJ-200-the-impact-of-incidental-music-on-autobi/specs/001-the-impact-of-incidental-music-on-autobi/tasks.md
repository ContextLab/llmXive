# Tasks: The Impact of Incidental Music on Autobiographical Memory Retrieval

**Input**: Design documents from `/specs/001-impact-of-incidental-music-on-autobi/`
**Prerequisites**: `plan.md` (required), `spec.md` (required for user stories), `research.md`, `data-model.md`, `contracts/`

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

## Phase 1: Setup (Shared Infrastructure)

- [X] T001 Create project structure per implementation plan (`code/`, `data/`, `tests/`)
- [X] T002 Initialize a Python project with `requirements.txt` dependencies (`pandas`, `numpy`, `scipy`, `statsmodels`, `scikit-learn`, `pyarrow`, `huggingface_hub`, `levenshtein`) using a compatible Python 3.x version.
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black)

---

## Phase 2: Foundational (Blocking Prerequisites)

- [X] T004 Create `contracts/dataset.schema.yaml` defining Track, CohortListen, MemoryCue, and AggregatedMetric schemas
- [X] T005 Create `contracts/output.schema.yaml` for regression results and sensitivity analysis outputs
- [X] T006 [P] Implement `code/config.py` with paths, thresholds (Levenshtein ≤ 4), seeds, and fallback flags
- [X] T007 Setup `data/raw/`, `data/processed/`, and `data/final/` directories with `.gitkeep`
- [X] T008 Implement `code/__init__.py` and basic logging configuration in `code/utils.py`
- [X] T009 Create `state.yaml` mechanism for checksum tracking of derived files (initial empty `artifact_hashes` map)
- [X] **T018** Initialize `state.yaml` with an empty `artifact_hashes` map and version metadata. Must run before any checksum updates.
- [X] T052 [P] Generate `quickstart.md` with step‑by‑step instructions to run the pipeline, required for T046 validation.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Cohort Exposure Scoring (Priority: P1) 🎯 MVP

### Tests for User Story 1
- [X] T010 [US1] Unit test for birth year filtering logic in `tests/unit/test_ingestion.py`
- [X] T011 [US1] Unit test for exposure score calculation in `tests/unit/test_ingestion.py`
- [X] T012 [US1] Unit test for fallback 'global exposure' trigger in `tests/unit/test_ingestion.py`

### Implementation for User Story 1
- [X] T013 [US1] Implement `code/data_ingestion.py` function `download_datasets` to download/verify MSD and AMT datasets from canonical URLs defined in `config.py`.  
  **Constraints**:  
  1. Use `datasets.load_dataset(..., streaming=True)` for large files.  
  2. Prototype mode (`config.USE_MOCK_DATA = True`) loads local mock data; final mode raises if real sources are unreachable.  
  3. No filtering – pure download/verification.

- [X] T023a [US1] **Pre‑check**: Implement `code/data_ingestion.py` function `check_fallback_trigger`.  
  **Logic**:  
  1. Scan the *raw* ingested cohort (output of T013) and compute `missing_pct = count(missing_birth_year) / total_records`.  
  2. Write `fallback_state.json` with fields `{ "missing_pct": <value>, "global_exposure_mode": <bool> }`.  
  3. If `missing_pct > 0.5`, set `global_exposure_mode` to `true` and log a WARN. Otherwise set to `false`.  
  4. No artifact is produced beyond the JSON file.

- [X] T112 [US1] **Global Exposure Calculation** (FR‑008). Implements `code/data_ingestion.py` function `calculate_global_exposure`.  
  **Logic**:  
  1. Triggered only when `global_exposure_mode` in `fallback_state.json` is `true`.  
  2. Stream the full MSD population for the relevant birth decade (e.g., 1980‑1999 for a 1990 birth) and compute the mean `adolescent_exposure_ratio`.  
  3. Append `"global_exposure_proxy": <value>` to `fallback_state.json`.  
  4. This proxy will be used to fill missing exposure ratios in downstream modeling.

- [X] **T112b** Validate representativeness of the Global Exposure proxy. Compare the distribution of the proxy against the distribution of exposure ratios from users with known birth years (e.g., KS test). Log a summary and a warning if the proxy appears non‑representative. This satisfies the reproducibility/verified‑accuracy concern.

- [X] T013a [US1] Implement `code/data_ingestion.py` function `filter_cohort`.  
  **Logic**:  
  1. Reads raw cohort data (output of T013).  
  2. Loads `fallback_state.json` to obtain `global_exposure_mode` and `global_exposure_proxy`.  
  3. If `global_exposure_mode` is `true`, **fills** missing `adolescent_exposure_ratio` for users with missing birth years using `global_exposure_proxy`; retains those users for downstream modeling (per FR‑008).  
  4. Otherwise, retains only records with a non‑missing `birth_year` and adds a computed adolescent window column (`adolescence_start`, `adolescence_end`).  
  5. Writes filtered cohort to `data/processed/filtered_cohort.parquet`.

- [X] T015 [US1] Implement `code/data_ingestion.py` function `apply_frequency_threshold`.  
  **Depends on**: T013a.  
  **Logic**: Remove user‑track pairs where `total_listens < 3` (minimum listen threshold, FR‑009).

- [X] T013b [US1] Implement `code/data_ingestion.py` function `fetch_popularity_scores`.  
  **Depends on**: T013a.  
  **Logic**: Pull `overall_popularity_score` from MSD metadata and merge into the filtered cohort.

- [X] T014 [US1] Implement `code/data_ingestion.py` function `calculate_ratio_score`.  
  **Depends on**: T013a, T015.  
  **Logic**: Compute `adolescent_exposure_ratio = adolescent_listens / total_listens` for each user‑track pair (using global proxy where needed).

- [X] T120 [US1] Write `data/processed/ingested_cohort.parquet`.  
  **Depends on**: T014.  
  Calls `utils.write_parquet` to persist the cohort with exposure ratios.

- [X] T121 [US1] Compute SHA‑256 checksum for `ingested_cohort.parquet`.  
  **Depends on**: T120.

- [X] T122 [US1] Update `state.yaml` with the checksum entry for `ingested_cohort.parquet`.  
  **Depends on**: T121 and **T018** (state file must exist).

- [X] T025 [US2] Implement `code/aggregation.py` function `join_exposure_data`.  
  **Depends on**: T120 (exposure data) and raw cue data (produced by T038/T039a).  
  Joins exposure scores to matched cues.

- [X] T026 [US2] Implement `code/aggregation.py` function `aggregate_to_user_track`.  
  **Depends on**: T025.  
  Produces `data/processed/user_track_pairs.parquet` with mean vividness & valence.

- [X] T027 [US2] Implement `code/aggregation.py` function `filter_zero_variance`.  
  **Depends on**: T026.  
  Removes tracks that have no associated memory cues.

- [X] T123 [US2] Write `data/processed/user_track_pairs.parquet`.  
  **Depends on**: T027.

- [X] T124 [US2] Compute SHA‑256 checksum for `user_track_pairs.parquet`.  
  **Depends on**: T123.

- [X] T125 [US2] Update `state.yaml` with the checksum entry for `user_track_pairs.parquet`.  
  **Depends on**: T124 and **T018**.

- [X] T028 [US1] Orchestrator `code/main.py` to enforce the exact order:  
  `download_datasets (T013)` → `check_fallback_trigger (T023a)` → `calculate_global_exposure (T112)` → `validate_global_exposure (T112b)` → `filter_cohort (T013a)` → `apply_frequency_threshold (T015)` → `fetch_popularity_scores (T013b)` → `calculate_ratio_score (T014)` → `write_ingested_cohort (T120)` → `checksum_ingested (T121)` → `state_update_ingested (T122)` → `join_exposure_data (T025)` → `aggregate_to_user_track (T026)` → `filter_zero_variance (T027)` → `write_user_track_pairs (T123)` → `checksum_user_track (T124)` → `state_update_user_track (T125)` → `verify_artifacts (T050)`.

**Checkpoint**: User Story 1 is fully functional and produces all required intermediate artifacts, including a valid Global Exposure proxy used where required.

---

## Phase 4: User Story 2 - Cue Matching and Memory Attribute Aggregation (Priority: P2)

### Tests for User Story 2
- [X] T019 [US2] Unit test for text normalization (lowercase, remove punctuation) in `tests/unit/test_matching.py`
- [X] T020 [US2] Unit test for fuzzy matching logic (Levenshtein distance ≤ 4) in `tests/unit/test_matching.py`
- [X] T021 [US2] Unit test for aggregation logic (mean vividness/valence per User‑Track) in `tests/unit/test_matching.py`

### Implementation for User Story 2
- [X] T029 [US2] Load raw MSD track metadata (streaming) into an in‑memory searchable index.  
  **Outputs**: `data/interim/track_index.pkl`.

- [X] T038 [US2] Load raw AMT cue dataset (streaming) and store as `data/interim/raw_cues.parquet`.

- [X] T039a [US2] Preprocess cues: normalize text, remove punctuation, lower‑case.  
  **Depends on**: T038.  
  Writes `data/interim/normalized_cues.parquet`.

- [X] T022 [US2] Implement `code/cue_matching.py` function `normalize_cues` (now calls T039a).

- [X] T047 [US2] Implement `code/cue_matching.py` function `match_cues` with Levenshtein ≤ 4, logs unmatched cues to `data/logs/unmatched_cues.log`.

- [X] T024 [US2] Implement `code/cue_matching.py` function `resolve_collisions` to handle ambiguous matches and log collisions.

- [X] T036 [US2] Implement `code/preprocess.py` function `enforce_match_rate`.  
  **Logic**:  
  1. Read `config.MATCH_RATE_THRESHOLD`.  
  2. If the value is a numeric threshold, compute actual match rate; if rate < threshold, log a WARN (per SC‑004) and continue.  
  3. If the value is the placeholder `'[deferred]'` or `None`, log a WARN indicating the threshold is unset and continue without enforcing a numeric cutoff.

- [X] T036a [US2] Log the actual match rate (as a percentage) after enforcement for auditability.

---

## Phase 5: User Story 3 - Statistical Modeling and Hypothesis Testing (Priority: P3)

### Tests for User Story 3
- [X] T030 [US3] Unit test for model formula construction in `tests/unit/test_modeling.py`
- [X] T031 [US3] Unit test for sensitivity analysis loop (thresholds ranging from low to high values) in `tests/unit/test_modeling.py`
- [X] T032 [US3] Unit test for parametric bootstrap logic (resampling residuals) in `tests/unit/test_modeling.py`

### Implementation for User Story 3
- [X] T033 [US3] Implement `code/modeling.py` function `fit_mixed_model` (LMM with random intercept for `user_id`).

- [X] T035 [US3] Implement `code/modeling.py` function `check_collinearity` (VIF > 5 → WARN).

- [X] T044a [US3] Implement `code/modeling.py` function `run_sensitivity_loop_setup` (prepare data structures for thresholds).

- [X] T115 [US3] **Re‑calculate Exposure** – depends on `user_track_pairs.parquet` (T123) and the **filtered** track set after T027. Generates a refreshed exposure column for the current threshold.

- [X] T116 [US3] **Re‑match Cues** – depends on updated track metadata (T029) and cue data (T039a). Produces a new matched cue set for the current threshold.

- [X] T117 [US3] **Re‑aggregate** – depends on T116 and T115; joins the newly matched cues with the newly calculated exposure and aggregates to User‑Track pairs.

- [X] T044c [US3] **Run Sensitivity Analysis** – orchestrates the loop for each Levenshtein threshold `[1,2,3,4,5]`. **Explicit ordering** enforced via `DEPENDS ON: T116 → T117 → T115` for each iteration, guaranteeing the required sequence.

- [X] T045a [US3] Implement `code/modeling.py` helper `run_bootstrap_setup` (prepare residuals, define number of iterations).

- [X] T045b [US3] Implement `code/modeling.py` helper `run_bootstrap_iteration` (resample residuals, refit model, store coefficient).

- [X] T045c-1 [US3] **Block‑Permutation Test** (FR‑007).  
  **Pre‑condition**: Checks that `spec.md` still contains FR‑007; if not, aborts with a clear error.  
  **Logic**: Shuffle `mean_vividness` within each `user_id` block, refit the mixed model, record the coefficient for `adolescent_exposure_ratio`. Repeats for `N=5000` iterations to build a null distribution.

- [X] T045c-2 [US3] **Write Permutation Results** – aggregates the null distribution and writes `data/final/permutation_results.csv`. Also logs the observed statistic vs. null p‑value.

- [X] T045d [US3] **Parametric Bootstrap** (retained for robustness). Generates `data/final/bootstrap_results.csv`.

- [X] T040 [US3] Generate diagnostic plots (residuals, QQ plots) and save to `data/final/plots/`.

---

## Phase 6: Polish & Cross‑Cutting Concerns

- [X] T041 [P] Documentation updates in `README.md` and `code/` docstrings.
- [X] T042 Code cleanup and refactoring of `code/main.py`.
- [X] T043 Performance optimization: ensure all large‑scale steps use streaming/chunking to stay <5 GB RAM.
- [X] T051 [P] Add integration test `tests/integration/test_pipeline.py` to run the full flow on synthetic data and verify sensitivity analysis logic.
- [X] T046 [P] Run `quickstart.md` validation to ensure pipeline runs end‑to‑end within 6 hours (SC‑005).
- [X] T068 [P] Generate residual diagnostic plot (`residuals.png`).
- [X] T070 [P] Generate QQ plot (`qq.png`).
- [X] T071 [P] Plot distribution of `adolescent_exposure_ratio` (`exposure_hist.png`).
- [X] T072 [P] Plot model coefficient confidence intervals (`coefficients.png`).
- [X] T074 [P] Compile final report (`report.md`) linking all CSV results and plots.
- [X] T118 [P] Validate final CSV files against their respective contracts (`contracts/output.schema.yaml`).
- [X] T119 [P] Archive all final artifacts into `results.zip` for reproducibility.
- [X] T050 [P] Verify artifacts: read `state.yaml`, recompute SHA‑256 checksums for `data/processed/ingested_cohort.parquet` and `data/processed/user_track_pairs.parquet`, compare against stored values, and log PASS/FAIL for each. This task must run after checksum updates (see T028).

- [X] T135 [P] Document the resolution of the FR‑007 vs. plan mismatch (now both block‑permutation and bootstrap are provided, with a guard against silent weakening).
