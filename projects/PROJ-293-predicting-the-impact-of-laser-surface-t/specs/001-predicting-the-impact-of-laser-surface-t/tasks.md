# Tasks: Predicting the Impact of Laser Surface Texturing on Wear Resistance

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, contract schemas in `specs/001-predict-lst-wear/contracts/`
**Prerequisites**: All tasks operate in the project root layout from `plan.md` (`code/`, `data/`, `reports/`, `models/`, `code/tests/`).
**Verification**: Each task names a concrete output artifact and a deterministic check. Real data only — no synthetic/mock stand-ins anywhere in the pipeline; failed real fetches must raise, never fall back.

## Phase 1: Setup and first end-to-end analysis

- [ ] T001 [P1] [US1] Establish the runnable pipeline entry point and static source registry. <!-- FAILED-IN-EXECUTION: code/ingest.py exit=1; code/preprocess.py exit=1 --> <!-- FAILED: unspecified -->
  *Implementation*: `code/main.py` provides subcommands (`ingest`, `preprocess`, `train`, `interpret`, `report`) with a global fixed seed (numpy/random, seed=42) in `code/seed.py`. Write `specs/001-predict-lst-wear/research.md` listing the static, verified data sources (HuggingFace dataset id, OpenML dataset id, and literature-supplement URLs) with `url` and `dataset_id` fields — no dynamic search code. Write `code/config/schema_map.json` mapping source column aliases (e.g., `"power": ["laser_power", "avg_power"]`) to the canonical schema from `data-model.md`.
  *Outputs*: `code/main.py`, `code/seed.py`, `code/config/schema_map.json`, `specs/001-predict-lst-wear/research.md`, `specs/001-predict-lst-wear/quickstart.md` documenting `python -m code.main <subcommand>`.
  *Verification*: `python -m code.main --help` exits 0; `code/tests/test_schema_map.py` asserts every canonical key from `dataset.schema.yaml` appears in `schema_map.json`; `code/tests/test_research.py` asserts each source entry has non-empty `url` and `dataset_id`.

- [ ] T002 [P1] [US1] Implement real-data ingestion with schema mapping and loud failure (FR-001, SC-007). <!-- FAILED-IN-EXECUTION: code/ingest.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/ingest.py exit=1 --> <!-- FAILED: unspecified -->
  *Implementation*: `code/ingest.py::fetch_sources` reads the static sources from `research.md`, downloads each real dataset (e.g., `datasets.load_dataset("<verified-id>")` for HuggingFace, `ucimlrepo` or a named raw URL for others), applies `schema_map.json` to map columns to the canonical schema, and writes `data/intermediate/merged.csv` with a `source_id` column. If a source lacks the required LST columns (`pulse_duration`, `power`, `scanning_speed`, `wear_rate`), halt with `data_schema_mismatch` (exit 1). If any real download fails, raise — NEVER fall back to synthetic/mock data. Verify source count: <1 → halt; <3 → log `data_source_limitation` warning and proceed (FR-012), writing `reports/source_validation.json`.
  *Outputs*: `data/intermediate/merged.csv`, `reports/source_validation.json`.
  *Verification*: `code/tests/test_ingest.py::test_fetch_and_schema` loads `merged.csv`, asserts all required canonical columns present, ≥1 distinct `source_id`, and no synthetic‑fallback code path exists (grep limited to `code/` directory only, excluding `code/tests/`).

- [ ] T003 [P1] [US1] Implement missing-value handling, Archard normalization, and dataset splitting (FR-002, FR-009, FR-013, FR-018). <!-- FAILED-IN-EXECUTION: code/preprocess.py exit=1 -->
  *Implementation*: `code/ingest.py` gains three functions, each producing real output files from `data/intermediate/merged.csv`:
  - `handle_missing_values`: drop rows missing any required predictor (`pulse_duration`, `power`, `scanning_speed`, `pattern_geometry`, `hardness`, `elastic_modulus`); NO imputation; retain rows missing only `contact_load`/`sliding_speed`; increment `missing_record_count`. Writes `data/processed/aggregated_dropped.csv`.
  - `archard_normalization`: convert `wear_rate` (linear mm or mass mg) to volume V via density/contact_area (FR-018); compute `K = V / (contact_load × sliding_distance)` where load and sliding data exist, set `normalization_method='normalized'`; otherwise keep raw `wear_rate` and set `normalization_method='raw'` (FR-009). Writes `data/processed/aggregated_clean.csv`.
  - `split_dataset` / `split_test_set`: write `data/processed/normalized_only.csv`, `data/processed/raw_only.csv`, `data/processed/split_summary.json` (`normalized_count`, `raw_count`, `total_count`); stratified 20% held‑out test split with fixed seed writing `data/processed/test_split.csv` and `data/processed/train_split.csv`.
  *Verification*: `code/tests/test_ingest.py::test_missing_predictor_handling` (no NaN in required predictors of `aggregated_dropped.csv`), `test_archard` (normalized rows have non-null K; raw rows keep original `wear_rate`), `test_split` (counts in `split_summary.json` match CSV lengths; test/train indices disjoint).

- [ ] T004 [P1] [US1] Enforce data‑sufficiency gates, power analysis, and primary‑analysis flag (SC-004, SC-006, FR-014).
  *Implementation*: `code/ingest.py::count_records` writes `data/processed/record_counts.json` (`total_records`, `normalized_count`, `raw_count`, `missing_record_count`). `compare_thresholds` reads it and writes `reports/pre_check.json` with `status` (`"pass"`, `"pilot_warning"`, `"insufficient_error"`), `reason`, and `study_scope` (`"full_study"`/`"pilot_study"`). Instead of exiting, it also writes `reports/primary_analysis_flag.json` containing `{ "run_primary": <bool> }` where `run_primary` is false if `normalized_count < 100` and `total_records >= 100` (graceful degradation) and true otherwise. Power analysis (`statsmodels`, medium effect f²=0.15, α=0.05) on the normalized subset writes `reports/power_analysis.json` with `power`, `warning`, `status`.
  *Verification*: `code/tests/test_thresholds.py::test_threshold_logic` checks the flag file; `code/tests/test_power_analysis.py` asserts `warning=True` for low‑count inputs; `code/tests/test_counts.py` cross‑validates `record_counts.json` against `split_summary.json`.

- [ ] T005 [P2] [US2] Build leakage‑safe preprocessing pipeline with interaction terms, min‑max scaling, and VIF reduction (Constitution VI, FR-010, FR-015).
  *Implementation*: `code/preprocess.py::preprocess_pipeline` returns a scikit‑learn `Pipeline` that (1) one‑hot encodes `pattern_geometry`, (2) **applies min‑max scaling** to all numeric features, (3) **creates interaction features such as `power_x_scanning_speed` inside the Pipeline** so they are recomputed within each CV fold, (4) passes the result to the model. `run_vif_diagnostics` computes VIF on the training features; iteratively drops the highest‑VIF feature of any pair with VIF > 5, records the deterministic removal order, and drops zero‑variance features with a recorded reason. Writes `reports/vif_report.json` (initial VIFs) and `reports/vif_resolution.json` (dropped features list).
  *Verification*: `code/tests/test_pipeline.py` asserts pipeline step order, presence of min‑max scaling and interaction term creation, and that interaction terms are generated by a custom `FunctionTransformer` within the pipeline; `code/tests/test_vif.py` asserts all final VIFs ≤ 5 and that the dropped list matches `vif_resolution.json`.

- [ ] T015 [P2] [US2] Conditional primary regression execution based on flag (covers SC‑006 graceful degradation).
  *Implementation*: `code/train.py::conditional_primary_train` reads `reports/primary_analysis_flag.json`. If `run_primary` is true, it proceeds to train the primary regression models (calls existing training functions). If false, it skips primary model training, writes placeholder `reports/primary_model_skipped.json` with `status: "skipped_due_to_insufficient_normalized_data"`, and ensures downstream tasks (e.g., sensitivity analysis) still run. Exit code 0 in both cases.
  *Outputs*: Either `models/best_model.joblib` and `reports/model_performance.json` (if run) or `reports/primary_model_skipped.json`.
  *Verification*: `code/tests/test_primary_flag.py` simulates both flag states and asserts correct artifact creation.

- [ ] T006 [P2] [US2] Train models with nested 5‑fold cross‑validation and grid search respecting power analysis and primary‑analysis flag (FR-003, FR-004, FR-014).
  *Implementation*: `code/train.py::run_nested_cv` now performs **outer 5‑fold cross‑validation** on the normalized‑only training split. Within each outer fold, `GridSearchCV` (inner 5‑fold) searches a grid of ≥10 total hyperparameter combinations (`n_estimators`, `max_depth`, `learning_rate`) for Random Forest and Gradient Boosting, while Linear Regression has no hyperparameters. The pipeline from T005 is used inside the inner CV to ensure interaction terms and min‑max scaling are recomputed per fold. After outer CV, the model (and hyperparameters) achieving the highest mean test R² across outer folds is selected. The final selected model is then **re‑trained on the full normalized training data** and evaluated on the held‑out test split (`data/processed/test_split.csv`) for reporting. The task respects the `run_primary` flag from T015 and the `power` warning from `reports/power_analysis.json`; if `power < 0.8`, it either forces Linear Regression only or records `power_insufficiency_warning` as before. Writes `models/best_model.joblib`, `reports/grid_search_summary.json` (detailing inner‑grid results and outer‑fold scores), and `reports/model_performance.json` conforming to `model_output.schema.yaml` (including `shap_importance` placeholder to be filled later).
  *Verification*: `code/tests/test_grid_search.py` asserts ≥10 combos, that outer CV is performed, and that the warning flag appears when appropriate; `code/tests/test_evaluation.py` validates `model_performance.json` against its schema and checks that the reported test R² matches the evaluation on the held‑out split.

- [ ] T016 [P2] [US2] Power‑analysis‑driven model selection or warning (FR-014 branch).
  *Implementation*: `code/validate.py::apply_power_policy` reads `reports/power_analysis.json`. If `power < 0.8`, it either (i) forces Linear Regression only (overriding any other model choice) or (ii) records `power_insufficiency_warning: true` in `reports/model_performance.json`. This task runs after T006 and updates the model performance artifact accordingly.
  *Outputs*: Updated `reports/model_performance.json` with `power_insufficiency_warning` field.
  *Verification*: `code/tests/test_power_policy.py` checks both branches.

- [ ] T007 [P2] [US2] Run leave‑one‑material‑class‑out validation with fallback (FR-006, SC-003).
  *Implementation*: `code/train.py::lomo_cv` performs LOMO CV if ≥3 material classes exist; otherwise falls back to 5‑fold K‑Fold, logs a warning, sets `fallback_active: true`, and records the scope shift to "within‑material prediction". If a class has <30 normalized records, restrict that fold to Linear Regression. Computes the ratio `test_R²_loo / test_R²_standard`; ratio < 0.8 → `transferability_failure_flag: true` (ratio undefined/zero‑denominator → ratio 0 with `ratio_undefined: true`). Handles unseen material classes in test without crashing (records error, continues). Writes `reports/lomo_validation.json` and updates `reports/model_performance.json` with `loo_r2_ratio`, `transferability_failure`, `fallback_active`.
  *Verification*: `code/tests/test_lomo.py` asserts correct fallback on a <3‑class input, correct ratio/flag computation, and that `model_performance.json` contains the new validation fields.

- [ ] T008 [P2] [US2] Run raw‑subset validity check and sensitivity analysis (FR-011, FR-017).
  *Implementation*: `code/train.py::sensitivity_analysis` first runs Shapiro‑Wilk and Levene's tests on the raw subset; if either p < 0.05, excludes it and reports `raw_subset_invalid`. Otherwise trains the best model type on (a) normalized‑only and (b) full (normalized + raw) subsets and reports the difference in R² and MAE. Writes `reports/sensitivity_analysis.json` with both models' metrics, deltas, and validity‑test p‑values.
  *Verification*: `code/tests/test_sensitivity.py` asserts deltas are computed from the recorded metrics and that the `raw_subset_invalid` branch fires for a non‑normal input.

- [ ] T009 [P3] [US3] Compute SHAP values, plots, and interaction detection (FR-005).
  *Implementation*: `code/interpret.py` computes SHAP values for the best model on the held‑out test set; generates `reports/shap_summary.png` (features ranked by mean |SHAP|) and `reports/shap_dependency_power_speed.png`. Detects non‑linear interactions via SHAP interaction magnitude > 0.1 **or** degree‑2 polynomial fit R² > 0.5 on the dependency plot. Writes `data/processed/shap_values.npy` and `reports/interaction_analysis.json` (per‑pair flags and fit R²). The report explicitly states whether `scanning_speed` or `pattern_geometry` is the dominant predictor.
  *Verification*: `code/tests/test_shap.py` asserts the SHAP array shape matches (n_test, n_features) and that `interaction_analysis.json` contains per‑pair booleans; plot files exist and are non‑empty.

- [ ] T010 [P3] [US3] Run permutation significance testing and physical plausibility checks (FR-008, FR-007, SC-002, SC-008).
  *Implementation*: `code/interpret.py::permutation_significance` runs ≥2000 permutations per feature to produce p‑values; flags `no_significant_features` if none meet p < 0.05 and `unstable_significance` if p‑value variance > 0.05; marks features with 0.05 ≤ p < 0.1 as "suggestive". Writes `reports/feature_significance.json` conforming to `feature_importance.schema.yaml`. `physical_plausibility_check` validates SHAP signs against Archard's law (e.g., load positively correlates with wear); contradictions → `physical_plausibility_failure: true`; no external validation target → `validation_target_unavailable` recorded as a limitation, study classified "purely associational". Writes `reports/validation_status.json`. All reported relationships use associational language only (FR-007).
  *Verification*: `code/tests/test_permutation.py` asserts `permutation_count ≥ 2000`, p‑value structure, and both flag branches on synthetic count inputs; `code/tests/test_physical_check.py` asserts the plausibility flag logic.

- [ ] T018 [P2] [US2] Generate `reports/model_output.json` conforming to `output.schema.yaml` (orphan contract resolution).
  *Implementation*: `code/report.py::write_model_output` aggregates `reports/model_performance.json`, `reports/shap_summary.png` (feature importances), and `reports/feature_significance.json` to produce a single `reports/model_output.json` that satisfies all required fields in `output.schema.yaml` (including `analysis_stage`, `loco_insufficient_samples`, bootstrap CIs, etc.). It also records whether the analysis stage was "primary", "normalized", or "descriptive_only" based on which dataset was used for the best model.
  *Outputs*: `reports/model_output.json`.
  *Verification*: `code/tests/test_model_output.py` validates the JSON against `specs/001-predict-lst-wear/contracts/output.schema.yaml`.

- [ ] T011 [P2] [US2] Aggregate all metrics and flags into the final model report (FR-016, model_report.schema.yaml).
  *Implementation*: `code/report.py` merges `model_output.json`, `lomo_validation.json`, `sensitivity_analysis.json`, `feature_significance.json`, `vif_resolution.json`, `pre_check.json`, `power_analysis.json`, and `primary_analysis_flag.json` into `reports/model_report.json` conforming to `model_report.schema.yaml` (best_model_type, metrics, loo_ratio, transferability_failure_flag, fallback_active, study_scope, power_insufficiency_warning, data_source_limitation_warning, vif_reduced_features, significant_features, no_significant_features_flag). It also records `baseline_improvement_delta` from T017 and `primary_model_halted` flag from T015. `code/pipeline.py::instrument_runtime` records start/end timestamps to `reports/runtime_metrics.json` and exits 1 with `runtime_timeout` if the full pipeline exceeds 6 hours (FR-016, SC-005).
  *Verification*: `code/tests/test_report.py` validates `model_report.json` against its schema and cross‑checks every number against its source artifact; `code/tests/test_runtime.py` asserts the timeout branch.

- [ ] T017 [P2] [US2] Compute baseline Linear Regression R² and improvement delta (SC-001).
  *Implementation*: `code/evaluation.py::baseline_comparison` trains a plain Linear Regression on the same training split, computes its test R², reads the best model's R² from `model_performance.json`, and writes `reports/baseline_metrics.json` and `reports/improvement_delta.json` containing the baseline R² and the delta (best − baseline). These are later merged into `model_report.json`.
  *Verification*: `code/tests/test_baseline.py` asserts both JSON files exist and that the delta matches the difference of the two R² values.

- [ ] T019 [P1] [US1] Compute checksums of raw downloads and update project state (Constitution III).
  *Implementation*: `code/ingest.py::checksum_raw` iterates over all files in `data/raw/`, computes SHA256 checksums, writes `data/raw_checksums.json`, and patches `state/projects/PROJ-293-predicting-the-impact-of-laser-surface-t.yaml` under `artifact_hashes` with the new values.
  *Outputs*: `data/raw_checksums.json`, updated `state/projects/PROJ-293-predicting-the-impact-of-laser-surface-t.yaml`.
  *Verification*: `code/tests/test_checksum.py` validates that each raw file has a corresponding checksum entry and that the state file is updated.

- [ ] T020 [P1] [US1] Create pinned `code/requirements.txt` (reproducibility requirement).
  *Implementation*: Write `code/requirements.txt` listing exact versions of all dependencies used throughout the pipeline (e.g., `pandas==2.2.2`, `scikit-learn==1.6.0`, `shap==0.45.0`, `numpy==1.26.4`, `statsmodels==0.14.2`, `datasets==2.18.0`, etc.).
  *Outputs*: `code/requirements.txt`.
  *Verification*: `code/tests/test_requirements.py` asserts the file exists and that each line matches a `pip freeze`‑style version pin.

- [ ] T021 [P2] [US2] Implement causal‑language filter and expose as a reusable validator (FR-007).
  *Implementation*: `code/validate.py::causal_language_filter` scans all generated textual artifacts (e.g., `reports/final_report.md`) for prohibited causal phrasing (e.g., "causes", "leads to") and replaces them with associational alternatives or flags them for manual review. It writes `reports/causal_filter_log.json` summarizing any modifications.
  *Outputs*: `reports/causal_filter_log.json`.
  *Verification*: `code/tests/test_causal_filter.py` feeds a sample text containing causal language and checks that the log reports the detected instances.

- [ ] T012 [P3] [US3] Generate result tables and figures from validated outputs.
  *Implementation*: `code/report.py::make_figures` reads only the computed artifacts (never hand‑typed numbers) and produces `reports/figures/model_comparison.png` (R²/MAE/RMSE per model), `reports/figures/feature_importance.png` (from SHAP + p‑values), and `reports/tables/performance_summary.csv`, `reports/tables/feature_significance.csv`.
  *Verification*: `code/tests/test_figures.py` asserts each file exists, is non‑empty, and that table values match the corresponding JSON artifacts row‑for‑row.

- [ ] T013 [P3] [US3] Write the methods/results account with honest limitations and paper‑stage handoff.
  *Implementation*: `reports/final_report.md` documents the methods (ingestion → Archard normalization → VIF → grid search → LOMO → SHAP), links every claim to the actual output files (`model_report.json`, figures, tables), states the study scope (`full_study`/`pilot_study`), reports negative findings (e.g., `no_significant_features`, `transferability_failure_flag`, `raw_subset_invalid`, `validation_target_unavailable`) honestly, and uses associational framing throughout (FR‑007). Includes a paper‑stage handoff section listing the figures/tables/JSON artifacts the paper pipeline should consume.
  *Verification*: `code/tests/test_final_report.py` asserts the associational‑framing disclaimer, a limitations section, and resolvable links to every generated artifact.

- [ ] T014 [P3] [US3] Re‑run the documented workflow end‑to‑end and confirm reproducibility.
  *Implementation*: Execute `python -m code.main ingest && python -m code.main preprocess && python -m code.main train && python -m code.main interpret && python -m code.main report` per `quickstart.md` from the declared inputs; confirm all `code/tests/` pass (`pytest -q` in `code/tests/`) and that a second run with the fixed seed reproduces identical metrics in `model_report.json`.
  *Verification*: Full re‑run exits 0 (or documented pilot exit code 2 with `study_scope: pilot_study`); `pytest -q` passes; a byte‑comparison of the two runs' `model_report.json` metric fields matches.

## Phase 3: Reproducible results and paper handoff (continued)

- (All tasks above collectively satisfy the remaining phases.)