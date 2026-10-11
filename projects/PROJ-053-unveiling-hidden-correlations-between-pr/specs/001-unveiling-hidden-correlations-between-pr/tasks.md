# Tasks: Unveiling Hidden Correlations Between Processing Parameters and Mechanical Properties in Additively Manufactured Alloys

**Inputs**: Active `spec.md`, `plan.md`, data-model.md, contracts (dataset, model_output, visualization schemas), prior tasks.md with verified work.

**Organization**: Consolidated from the prior task list into substantive research tasks. Verified completed work (schema validation, config, preprocessing/model/viz unit tests, GPR trainer, baseline, metrics, stratified analysis, contour/heatmap/PDP plots, linting, download/independence unit tests) is preserved as checked. Pending work is regrouped without dropping any acceptance criterion. Paths are relative to the project root (`code/`, `data/`, `results/`, `docs/`).

## Phase 1: Setup and first end-to-end analysis

- [ ] T001 [P] [US1] Establish the runnable pipeline entry point and real data source. Implement `code/data/download.py` to fetch the NIST AM-Bench (Zenodo) AM alloy dataset via a concrete reachable URL (Zenodo record download or `requests` with retry + backoff, max 3 attempts); on failure raise `FileNotFoundError` with the exact message "No verified source found for AM-Machine-Learning dataset. Automated download failed after retries. Please manually place a valid CSV file at `data/raw/am_raw_data.csv`." — NO synthetic/mock fallback anywhere (FR-001, edge case: download failure). Save raw CSV to `data/raw/am_raw_data.csv`. Document the runnable command (`python code/main.py --stage ingest`) in the feature's `quickstart.md`.
  - Verify: script downloads real data or fails loudly with the exact message; no `generate_synthetic`/`mock`/random fallback exists in `code/data/download.py`.

- [ ] T002 [US1] Complete data validation and preprocessing (FR-001, FR-002, US-1 acceptance scenarios 1–3, edge cases). In `code/data/preprocess.py` (reusing the verified `schema_validator.py`, `config.py`, logger, and unit tests already in place):
  - Validate N ≥ 50; if fewer, halt with the exact error "Insufficient data for GPR training; minimum 50 samples required."
  - Detect zero-variance features (e.g., Layer Thickness), log a warning, exclude them; if VIF > 5 for any predictor, log a warning and record derived columns (e.g., `energy_density`) in `data/processed/excluded_columns.yaml` rather than feeding them to the model (Constitution VII).
  - Run source-independence validation in `code/data/validate_source_independence.py`: predictor and target column sets must be strictly disjoint; halt on any overlap or missing `data/raw/source_independence_log.txt` (JSON `{"predictors": [...], "targets": [...]}`) with a clear Constitution Principle VII error.
  - Scope detection: if `fatigue_life` is absent, log `[SCOPE] Reduced scope: fatigue_life missing; analysis restricted to yield_strength and ductility.` to `data/processed/preprocessing.log` and write `data/processed/target_config.json` with `{"active_targets": ["yield_strength", "ductility"]}`.
  - Median-impute missing numeric values (log imputation counts), one-hot encode `alloy_type` into `is_<type>` binary columns and drop the original, stratified train/test split (70/15/15) BEFORE scaling, fit `MinMaxScaler` on train only, save `data/processed/train.csv`, `test.csv`, `normalization_bounds.json`, `original_target.npy`, and imputation/dropped-column/normalization entries in `data/processed/preprocessing.log`.
  - Verify: processed CSVs have no missing values, all normalized columns strictly within [0,1], binary alloy columns present, log entries recorded; `tests/unit/test_preprocess.py` and `tests/integration/test_pipeline.py` pass.

- [ ] T003 [US2] Run the first end-to-end GPR analysis on the real preprocessed data. Wire `code/main.py` to execute ingest → preprocess → train → evaluate using the verified `code/models/gpr_trainer.py` (RBF kernel, 5-fold CV maximizing log marginal likelihood, seed 42), `code/models/baseline_trainer.py` (linear regression), and `code/models/metrics.py`. Produce `results/metrics.json` conforming to `model_output.schema.yaml` with real measured `r2_score`, `rmse`, `mae`, `rmse_percentage_range` (null if test-set range < 1e-6), `baseline_r2`, `delta_r2`, `percentage_improvement`, optimized `hyperparameters` (length_scale, sigma), and `sample_size`/`sampling_method`/`representativeness_limitation` documentation keys (T054 revision concern). Save the serialized GPR model artifact.
  - Verify: `results/metrics.json` exists, validates against the schema, and all values are computed from the real dataset; repeated runs with seed 42 produce identical metrics and artifacts (US-2 scenario 3).

**Checkpoint**: The documented command executes end-to-end on real data and its numerical outputs are checkable. No report writing from expected or invented results.

## Phase 2: Complete the study and validate its evidence

- [ ] T004 [US3] Compute permutation importance and correlate against a baseline (FR-006, SC-004). Using the trained GPR, compute permutation importance over all predictor features and write `results/permutation_importance.json` (feature_name, importance_score per feature). Then in `code/analysis/importance.py`: load `data/baseline_importance.json` if present, else `data/literature_baseline_importance.json`, else fall back to a stability analysis (re-computed importance across CV folds) and log that SC-004 is "Partially Met" — never raise on a missing baseline. Compute Spearman rank correlation between model importance and the baseline and record it as `importance_correlation` in `results/metrics.json`.
  - Verify: importance file lists every feature with real scores; correlation value or documented fallback present in `results/metrics.json`; `tests/unit/test_importance.py` passes.

- [ ] T005 [US3] Quantify uncertainty and flag high-uncertainty regimes (FR-007, SC-003, US-3 scenario 2). In `code/analysis/uncertainty.py`: extract predictive means and standard deviations on the test set, compute the fraction of test samples with σ > 2× median σ, record `high_uncertainty_ratio` in `results/metrics.json`, and write the coordinates of flagged parameter regions to `results/high_uncertainty_regions.csv` for future data-collection prioritization.
  - Verify: ratio in [0,1] present in `results/metrics.json`; CSV lists real parameter coordinates of flagged regions; `tests/unit/test_viz.py` threshold test passes.

- [ ] T006 [US2] Produce the residual analysis and confounder report (plan T055/T030, SC-001 support). In `code/models/residual_analysis.py`: analyze GPR test-set residuals for heteroscedasticity (e.g., Breusch-Pagan or Spearman correlation of |residual| with fitted values) and non-linearity via a permutation test comparing GPR R² to the linear baseline; write `results/residual_analysis.json` with `heteroscedasticity_detected` (boolean) and `method_used`. Ensure per-alloy stratified metrics from the verified `code/models/stratified_analysis.py` are written to `results/confounder_analysis.json`.
  - Verify: `results/residual_analysis.json` exists (prior rejection: file was missing) with real computed values; `results/confounder_analysis.json` contains per-alloy-type R²/RMSE/MAE.

- [ ] T007 [US3] Generate all specified figures from the validated outputs (FR-005, US-3 scenarios 1–3). Using the verified `code/viz/contour_plots.py`, `code/viz/importance.py`: generate contour plots of predicted yield strength (and ductility) over laser power × scan speed in physical units (via `normalization_bounds.json`), uncertainty heatmaps with σ > 2× median regions colored red, and partial dependence plots for the top-3 parameters from `results/permutation_importance.json`. Write PNGs (each ≤ 5 MB) to `results/plots/` with sidecar JSON metadata conforming to `visualization.schema.yaml` (file_name, x_axis, y_axis, z_axis, uncertainty_flag, max/median uncertainty).
  - Verify: PNGs and sidecar JSONs exist and match the schema; heatmap red regions correspond to flagged cells from T005; `tests/integration/test_pipeline.py` viz tests pass.

- [ ] T008 [P] Add runtime, memory, and feasibility checks (SC-005, plan T040/T047). Wrap the full pipeline in a timer and write `results/runtime.json` with `runtime_seconds` and `feasibility_status` ("PASSED"/"FAILED", warning only, never abort) compared against the free-tier CI limit when `GITHUB_ACTIONS` is set. Profile peak memory during GPR training (memory_profiler or `resource`/tracemalloc) and write `results/memory_profile.json` with `max_memory_mb` and status; if usage ≥ 7340 MB or N > 500, apply the sparse-GPR fallback in `code/models/gpr_trainer.py` (inducing-point/FITC-style approximation, documented in `requirements.txt` if a new dependency is added) and re-profile.
  - Verify: both JSON artifacts contain real measured values; runtime recorded in `results/metrics.json` as `runtime_seconds`.

## Phase 3: Reproducible results and paper handoff

- [ ] T009 [US1] [US2] [US3] Write the methods/results account in `docs/paper.md` (draft) linked directly to the actual output cells: metrics from `results/metrics.json`, importance ranking, uncertainty ratio, residual/confounder findings, and the generated figures. Include explicit data provenance (NIST AM-Bench source and access date), the scope-reduction log entry if `fatigue_life` was absent, which importance baseline source was used (user JSON, literature, or stability fallback), and honest limitations (epistemic-only uncertainty; sample size and representativeness constraints from T003's documentation keys). Describe negative findings (e.g., GPR not beating the linear baseline) honestly rather than thresholding.
  - Verify: every numeric claim in `docs/paper.md` traces to a `results/` artifact; no hand-typed values.

- [ ] T010 [US1] Finalize reproducibility and paper-stage handoff. Update `README.md`/`quickstart.md` with installation steps, pinned `requirements.txt`, the documented end-to-end command, and manual data placement instructions ("Download a valid AM alloy dataset and save it as `data/raw/am_raw_data.csv`"). Re-run the full documented workflow from `data/raw/am_raw_data.csv` with `PYTHONHASHSEED=0` and seed 42, confirm identical `results/metrics.json` and model artifacts, confirm all unit/integration tests pass, and record the paper-stage handoff (layout, PDF compilation, publication belong to the subsequent paper pipeline) in `docs/paper.md` final version.
  - Verify: fresh re-run reproduces byte-identical metrics; tests green; handoff section present.

## Dependencies and requirement coverage

| Requirement | Task(s) | Demonstrating command |
|---|---|---|
| FR-001 (download/validate ≥50 samples, real source) | T001, T002 | `python code/main.py --stage ingest` |
| FR-002 (impute, normalize, encode) | T002 | `pytest tests/unit/test_preprocess.py` |
| FR-003 (GPR RBF, 5-fold CV) | T003 | `python code/main.py --stage train` |
| FR-004 (R²/RMSE/MAE JSON) | T003 | inspect `results/metrics.json` vs schema |
| FR-005 (contour plots, heatmaps) | T007 | inspect `results/plots/` + sidecars |
| FR-006 (permutation importance) | T004 | inspect `results/permutation_importance.json` |
| FR-007 (σ > 2× median flags) | T005 | inspect `results/high_uncertainty_regions.csv` |
| SC-001 (GPR vs linear baseline) | T003, T006 | `delta_r2` in `results/metrics.json` |
| SC-002 (RMSE % of range) | T003 | `rmse_percentage_range` |
| SC-003 (high-uncertainty fraction) | T005 | `high_uncertainty_ratio` |
| SC-004 (importance correlation) | T004 | `importance_correlation` |
| SC-005 (runtime feasibility) | T008 | `results/runtime.json` |

Execution order: T001 → T002 → T003 → (T004, T005, T006 in sequence after T003; T007 after T004+T005; T008 after T003) → T009 → T010. T008 is [P] relative to T004–T007 (different files). Research scripts write only project-owned paths (`data/`, `results/`, `code/`, `docs/`); platform state under `state/` is never touched.

## Revision behavior

Verified completed work (T006/T007/T009/T010/T011–T013, T022–T027, T030, T033–T037, T046, T051, T052 from the prior list) is preserved inside the consolidated tasks above; their acceptance criteria are carried forward, not erased. The two verifier rejections are addressed: the missing `schema.yaml` artifact is covered by T002's schema validation against the active contracts, and the missing `results/residual_analysis.json` is the explicit deliverable of T006. Analyze revision concerns (no synthetic fallback — T001; sample-size documentation — T003; sparse GPR — T008; strict source-independence disjointness — T002) are folded into the consolidated tasks without duplication.
