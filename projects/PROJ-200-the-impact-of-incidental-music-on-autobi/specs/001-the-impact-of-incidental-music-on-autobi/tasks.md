# Tasks: The Impact of Incidental Music on Autobiographical Memory Retrieval

**Input**: Design documents from `/specs/001-the-impact-of-incidental-music-on-autobi/`
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`

**Re-plan note**: The prior task list was rejected for a duplicate task identity (`T025` appeared both as `join_exposure_data` under US1 and under US2) and a malformed empty-ID entry. This revision assigns unique IDs, consolidates the many fine-grained checked steps into coherent task units, and preserves all completed, verified work. Previously completed requirements remain marked checked; the single remaining pending requirement (T140) is retained.

## Phase 1: Setup and first end-to-end analysis

- [ ] T001 Establish the project layout (`code/`, `data/raw/`, `data/processed/`, `data/final/`, `tests/`), `requirements.txt` (`pandas`, `numpy`, `scipy`, `statsmodels`, `scikit-learn`, `pyarrow`, `huggingface_hub`, `levenshtein`), `code/config.py` with paths, thresholds (Levenshtein ≤ 4, `MATCH_RATE_THRESHOLD`, seeds = 42, fallback flags), and `quickstart.md` documenting the runnable pipeline command. Verified by executing the documented command path.
- [ ] T002 Implement data contracts `contracts/dataset.schema.yaml` and `contracts/output.schema.yaml` defining the User-Track Pair analysis dataset and regression/sensitivity/permutation outputs, per the active read-only contracts.

## Phase 2: Data ingestion, exposure scoring, and aggregation (US-001, US-002)

- [ ] T003 [US1] Implement ingestion and cohort exposure scoring in `code/data/ingestion.py`: `download_datasets` (MSD via HuggingFace `datasets.load_dataset(..., streaming=True)`; mock AMT from `data/mock/amt_mock.json` in prototype mode, real sources raising loudly on failure — no synthetic fallback), `check_fallback_trigger` (compute `missing_pct` of `birth_year` on the raw cohort, write `data/processed/fallback_state.json` with `{missing_pct, global_exposure_mode}`, set `global_exposure_mode=true` if > 0.5 per EC-001 — checked BEFORE any filtering), `calculate_global_exposure` (FR-008: mean adolescent exposure ratio for the birth decade, streamed from the full population), `filter_cohort` (fills missing ratios with the global proxy when fallback mode is on; otherwise retains non-missing birth years with adolescence window columns), `apply_frequency_threshold` (FR-009: drop pairs with `total_listens < 3`), `fetch_popularity_scores`, and `calculate_ratio_score` (FR-001: raw `adolescent_exposure_ratio = adolescent_listens / total_listens`, no logit). Writes `data/processed/ingested_cohort.parquet` (T120) with SHA-256 checksum recorded via the `state.yaml` utility (T009/T121/T122). Unit tests in `tests/unit/test_ingestion.py` cover birth-year filtering, exposure calculation, fallback trigger (including T138's >50%-missing no-crash test), and fallback-ordering verification (EC-001, T023b logic: fallback check precedes the listen-threshold filter, raising `ConfigurationError` otherwise).
- [ ] T004 [US2] Implement cue matching and memory aggregation in `code/cue_matching.py` and `code/aggregation.py`: load MSD track metadata (streaming) into `data/interim/track_index.pkl`; load and normalize AMT cues to `data/interim/normalized_cues.parquet`; `match_cues` with Levenshtein ≤ 4 logging unmatched cues to `data/logs/unmatched_cues.log`; `resolve_collisions`; `enforce_match_rate` (SC-004: warn and proceed if rate < 80%, log actual rate to `data/logs/match_rate_stats.json` as `{"total", "matched", "rate"}`); `join_exposure_data` (joining matched cues to the exposure cohort from T003 — single consolidated implementation resolving the prior duplicate T025 identity); `aggregate_to_user_track` (FR-004: one row per User-Track Pair with mean vividness/valence); `filter_zero_variance` (EC-002: drop pairs with `n_cues == 0`). Writes `data/processed/user_track_pairs.parquet` (T123) with checksum in `state.yaml` (T124/T125). Unit tests in `tests/unit/test_matching.py` cover normalization, fuzzy matching, and aggregation.
- [ ] T005 [US1/US2/US3] Implement the orchestrator (`code/main.py` / `code/orchestrator.py`) wiring the full flow — ingest → fallback check → global exposure → filter → threshold → popularity → ratio → parquet → match → aggregate → model → verify — with logging initialization, configuration loading, and `state.yaml` verification at start. Integration test `tests/integration/test_pipeline.py` runs the full flow end-to-end.

## Phase 3: Statistical modeling and hypothesis testing (US-003)

- [ ] T006 [US3] Implement `code/modeling.py` `fit_mixed_model` (FR-005: LMM `mean_vividness ~ adolescent_exposure_ratio + popularity + (1|user_id)` with raw ratio per FR-001) and `check_collinearity` (EC-003: VIF > 5 → WARN, no crash; covered by T139's unit test in `tests/unit/test_modeling.py`). Unit tests cover formula construction.
- [ ] T007 [US3] Implement the sensitivity analysis loop (FR-006) in `code/modeling.py`/`code/analysis/sensitivity.py`: for each Levenshtein threshold in `[1,2,3,4,5]`, re-match cues, re-calculate raw exposure for the matched track subset, re-aggregate to User-Track pairs, and refit the model; write `data/final/sensitivity_results_threshold_{N}.csv` per iteration and the consolidated `data/final/sensitivity_analysis.csv`. Unit test covers the threshold loop.
- [ ] T008 [US3] Implement the block-permutation test (FR-007) in `code/analysis/permutation.py`: shuffle `mean_vividness` within each `user_id` block with predictors (`adolescent_exposure_ratio`, `popularity`) and `user_id` fixed; 5000 iterations, seed 42; `validate_permutation_constraints` raises on any predictor/outcome leakage; write the null distribution and observed-vs-null p-value to `data/final/permutation_results.csv`. The parametric bootstrap was removed in favor of the permutation test exclusively (documented, T135). Unit tests cover permutation constraint validation and residual-resampling logic.
- [ ] T009 [US3] Generate diagnostic plots to `data/final/plots/`: residuals (`residuals.png`), QQ plot (`qq.png`), exposure histogram (`exposure_hist.png`), coefficient confidence intervals (`coefficients.png`).

## Phase 4: Validation, reporting, and handoff

- [ ] T010 [P] Verify artifacts (T050): recompute SHA-256 checksums for `data/processed/ingested_cohort.parquet` and `data/processed/user_track_pairs.parquet`, compare against `state.yaml`, log PASS/FAIL; validate final CSVs against `contracts/output.schema.yaml` (T118); archive final artifacts (`results.zip`, T119); compile `report.md` linking all CSV results and plots (T074); run `quickstart.md` end-to-end within the 6-hour budget with streaming/chunking keeping memory < 5 GB (T043/T046); documentation and cleanup (T041/T042).
- [ ] T011 [P] [US2] Implement a contract test in `tests/contract/test_data_flow.py` verifying that `data/processed/user_track_pairs.parquet` and `data/final/regression_summary.csv` strictly adhere to `contracts/output.schema.yaml` (required columns, types, ranges — e.g. `total_listens >= 3`, `n_cues >= 1`, `p_value` in [0,1], `vif >= 1.0`) before downstream analysis tasks consume them.
    - Run with `pytest tests/contract/test_data_flow.py -v` after T003–T006 have produced the artifacts.
    - The test must FAIL loudly (not skip) when a required column is missing or out of range, so schema drift is caught before modeling.

## Dependencies and requirement coverage

| Requirement | Task | Verification |
| :--- | :--- | :--- |
| FR-001 raw exposure ratio | T003 | `tests/unit/test_ingestion.py` |
| FR-004 User-Track Pair aggregation | T004 | `tests/unit/test_matching.py` |
| FR-005 LMM formula | T006 | `tests/unit/test_modeling.py` |
| FR-006 sensitivity loop [1..5] | T007 | `data/final/sensitivity_analysis.csv` |
| FR-007 block permutation | T008 | `data/final/permutation_results.csv` |
| FR-008 global exposure fallback | T003 | `fallback_state.json` + T138 test |
| FR-009 min listens ≥ 3 | T003 | schema check in T011 |
| SC-004 match rate warning | T004 | `data/logs/match_rate_stats.json` |
| EC-001 fallback-before-filter ordering | T003 | ordering verification + T138 |
| EC-002 zero-variance filtering | T004 | `n_cues >= 1` in schema |
| EC-003 VIF warning | T006 | T139 test |
| Artifact checksums / state | T003, T004, T010 | T050 PASS logs |

Execution order: T001–T002 → T003 → T004 → T005 → T006 → T007/T008 → T009 → T010 → T011 (T011 requires the artifacts from T003–T006 and the contract files from T002).

## Revision behavior

This revision repaired the duplicate `T025` identity by consolidating both join implementations into a single step inside T004, removed the malformed empty-ID entry, and grouped the prior 80+ micro-tasks into 11 coherent units while preserving every acceptance criterion, path, threshold, and test obligation from the prior list. Only the contract-test requirement (formerly T140) remains open.
