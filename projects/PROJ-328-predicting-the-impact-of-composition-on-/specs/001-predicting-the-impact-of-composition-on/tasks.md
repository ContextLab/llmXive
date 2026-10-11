# Tasks: Predicting the Impact of Composition on the Vickers Hardness of Solder Alloys

**Inputs**: `specs/001-predict-solder-hardness/spec.md`, `plan.md`, `data-model.md`, `contracts/solder_dataset.schema.yaml`, prior `tasks.md` and verifier feedback.

The goal is to deliver a fully reproducible, CPU‑only research pipeline that satisfies **all** functional requirements (FR‑001 – FR‑014) and success criteria (SC‑001 – SC‑007).  
Each task is a concrete, unchecked work item that produces a real artifact on the free‑tier GitHub Actions runner.  Tasks are ordered to respect data flow; later tasks never depend on artifacts that are produced later.

---

## Phase 1 – Setup and first end‑to‑end analysis  

- [ ] **T001** [US1] **Curate a citation‑backed solder‑hardness dataset**  
  *Create* `data/raw/solder_hardness_curated.csv` (real rows extracted from open‑access literature and the Materials Project, NIST, OpenAlloy) with columns `id,source_citation,source_url,alloy_family,elements,hardness_hv,hardness_unit,temperature_c,notes`.  
  *Also create* `data/raw/curation_notes.md` documenting the literature search, per‑source record counts, and any gaps.  
  *Compute* SHA‑256 of the CSV and write it to `data/checksums.txt`.  
  **Verification**: CSV parses with pandas, contains ≥ 50 rows, every row has a non‑empty `source_citation` and numeric `hardness_hv`. The hash in `checksums.txt` matches the file.

- [ ] **T017** [US1] **API data fetcher**  
  Fetch raw composition‑hardness data from the Materials Project (or other open API) using a lightweight script `code/ingestion/api_fetcher.py`.  
  Store the JSON response as `data/raw/api_fetched.json`.  
  Compute SHA‑256 of this file and **append** the hash to `data/checksums.txt`.  
  **Verification**: File exists, JSON parses, checksum line present and matches.

- [ ] **T018** [US1] **Aggregator helper – copy sources & ingestion status**  
  Copy all source files (`solder_hardness_curated.csv`, `api_fetched.json`, any auxiliary CSVs) into `data/raw/` (ensuring they are present).  
  Generate `data/raw/.ingestion_status.json` summarising each raw file (`filename`, `size_bytes`, `sha256`).  
  Update `data/checksums.txt` to include entries for every file now in `data/raw/`.  
  **Verification**: Status JSON lists all files, each entry’s SHA matches the line in `checksums.txt`.

- [ ] **T002** [US1] **Ingestion, cleaning & validation pipeline**  
  Implement `code/ingestion/run_ingestion.py` that:  
  1. Loads `data/raw/solder_hardness_curated.csv` (fails loudly if missing).  
  2. Applies cleaning rules from `code/config.py` (`MAX_ELEMENTS=5`, composition‑sum ≥ 95 %, temperature ≈ 25 °C, HV unit conversion).  
  3. Writes the cleaned dataset to `data/processed/solder_hardness_cleaned.csv`.  
  4. Writes `data/processed/excluded_records.csv` with reason codes for every dropped row.  
  5. Writes `data/processed/.ingestion_status.json` containing `threshold_status` (`N>=100`, `50<=N<100`, or `N<50`), `exact_N`, `excluded_count`, `power_limitation_warning` (null or string), `reduced_n_flag`.  
  6. Writes `data/processed/validation_metrics.yaml` (`total_raw_records`, `passed_threshold_count`, `failed_threshold_count`, `pass_rate_percentage`).  
  7. Writes `data/processed/validation_report.yaml` summarising the above and flagging any power‑limitation warning (FR‑001, FR‑002, SC‑004).  
  **Verification**: Running `python -m code.ingestion.run_ingestion` produces all seven files, each conforms to its schema, and unit tests in `code/tests/test_ingestion.py` pass.

- [ ] **T003** [US1] **Document and run the first thin end‑to‑end analysis**  
  Add the command `python -m code.ingestion.run_ingestion` to `specs/001-predict-solder-hardness/quickstart.md`.  
  Execute the command on a clean checkout and record in `quickstart.md` the exact `exact_N` and whether a power‑limitation warning was emitted.  
  **Verification**: The command runs without error, produces the cleaned CSV, and the numbers recorded in the markdown match the JSON status file.

- [ ] **T004** [US1] **Verify literature citations (research_verified.md)**  
  Run the platform’s Reference‑Validator Agent on the `source_citation` fields of `data/raw/solder_hardness_curated.csv`.  
  Write the validated list of citations (with URLs and DOI checks) to `specs/001-predict-solder-hardness/research_verified.md`.  
  **Verification**: The file exists, contains one entry per row of the curated CSV, and each entry has a resolved DOI/URL (the verifier reports zero unresolved citations).

- [ ] **T005** [US1] **Task‑ordering audit**  
  Generate a JSON file `data/outputs/task_ordering_audit.json` that enumerates all tasks (T001‑T023) with their dependencies (e.g., T002 depends on T001). This aids reproducibility audits.  
  **Verification**: The JSON is syntactically valid, lists every task ID exactly once, and each `depends_on` array references only tasks that appear earlier in the list.

---

## Phase 2 – Complete the study and validate its evidence  

- [ ] **T006** [US2] **Feature engineering: CLR transform & compositional descriptors**  
  Extend `code/features/descriptor_engine.py` (called by `code/features/run_features.py`) to:  
  1. Load `data/processed/solder_hardness_cleaned.csv`.  
  2. Apply a manual Centered Log‑Ratio (CLR) transform to the elemental composition vectors (no external `compositional` package).  
  3. Write `data/processed/clr_features.csv` (CLR columns named `clr_<element>`).  
  4. Compute physical descriptors using `mendeleev` (weighted mean atomic mass, electronegativity variance, atomic radius variance, weighted average melting point, valence electron concentration) and write `data/processed/descriptors.csv` with a **deterministic** `transformation_hash` per record (SHA‑256 of the sorted `elements` string concatenated with a fixed parameter identifier).  
  Include unit tests in `code/tests/test_features.py` (zero vector for a uniform composition, hand‑checked descriptor values for Sn‑3 Ag‑0.5 Cu).  
  **Verification**: Both CSV files exist, have the same row order as the cleaned dataset, and all tests pass.

- [ ] **T007** [US2] **Collinearity diagnostics (VIF)**  
  Implement `code/features/collinearity.py` that reads the combined feature matrix (`clr_features.csv` + `descriptors.csv`) and computes Variance Inflation Factors for every predictor using `statsmodels`.  
  Write `data/processed/vif_report.yaml` listing each predictor, its VIF score, and `is_collinear: true` for VIF ≥ 5.  
  **Verification**: The YAML contains an entry for every column, VIF values are numeric, and at least one predictor is flagged if its VIF ≥ 5 (FR‑013, SC‑006).

- [ ] **T008** [US2] **Model training (XGBoost & Linear Regression) with k‑fold CV**  
  Create `code/models/train.py` that:  
  1. Merges `clr_features.csv` and `descriptors.csv` to form X, loads `hardness_hv` as y.  
  2. Performs an 80/20 stratified train‑test split by `alloy_family` (seed pinned in `code/seed.py`).  
  3. Executes 5‑fold CV on the training set for both XGBoost (grid ≤ 10 combos, **CPU‑only** build) and Linear Regression.  
  4. Writes per‑fold R² and RMSE to `data/processed/cv_results.yaml`.  
  5. Saves the fitted models under `models/xgboost_model.pkl` and `models/linear_model.pkl`.  
  **Verification**: The YAML contains exactly five fold entries per model, and the script runs within the free‑tier CPU budget.

- [ ] **T019** [US2] **Null‑model baseline computation**  
  Implement `code/evaluation/null_baseline.py` that:  
  1. Computes the mean hardness of the training set.  
  2. Predicts this constant value for every instance in the held‑out test set.  
  3. Calculates R² and RMSE for these predictions.  
  4. Writes `data/processed/null_baseline.yaml` with `r2_score` and `rmse_score`.  
  5. Appends a dedicated entry `null_model` to `data/processed/cv_results.yaml` for easy downstream comparison.  
  **Verification**: The YAML files exist and contain numeric values; a sanity check confirms R² ≤ 0.

- [ ] **T009** [US2] **Bootstrap evaluation, test‑set predictions & model comparison**  
  Implement `code/evaluation/evaluate.py` that:  
  1. Loads the held‑out test set, generates predictions with both models, writes `data/processed/predictions.csv`.  
  2. Performs ≥ 1000 bootstrap resamples of the test set to compute 95 % confidence intervals for R² and RMSE; store in `data/processed/test_metrics.yaml`.  
  3. Runs a paired t‑test on the 5‑fold CV scores (XGBoost vs Linear) and writes `data/processed/paired_ttest_results.yaml`.  
  4. Executes a bootstrap model‑comparison (difference of R² distributions) and writes `data/processed/bootstrap_comparison.yaml`.  
  **Verification**: All four files exist, numeric fields are present, and bootstrap CI bounds enclose the point estimates.

- [ ] **T010** [US2] **SHAP feature‑importance ranking**  
  Create `code/evaluation/shap_analysis.py` that computes SHAP values for the XGBoost model on the test set, aggregates mean absolute SHAP per feature, and writes `data/processed/shap_ranking.yaml` (sorted, top‑3 flagged).  
  **Verification**: The YAML lists every predictor, includes `mean_abs_shap_value` and `rank`, and the top‑3 entries are later used by the PDP task.

- [ ] **T011** [US2] **Sensitivity analysis (R² threshold sweep)**  
  Implement `code/evaluation/sensitivity.py` that reads the best CV R² from `cv_results.yaml`, defines thresholds `np.linspace(0.0, best_r2, 11)`, and for each threshold computes the fraction of bootstrap test‑set R² samples exceeding it.  
  Write `data/processed/sensitivity_analysis.yaml` (threshold‑fraction pairs) and `data/outputs/sensitivity_plot.png` (threshold on x‑axis, fraction on y‑axis).  
  **Verification**: The YAML contains ≥ 5 points, fractions are monotonic decreasing, and the plot has correctly labeled axes.

- [ ] **T012** [US3] **Visualizations: predicted‑vs‑measured scatter & partial dependence plots**  
  Implement `code/visualization/plots.py` that:  
  1. Reads `predictions.csv` and creates `data/outputs/pred_vs_measured.png` (scatter with 95 % CI error bars, HV units).  
  2. Generates three partial dependence plots for the top‑3 SHAP features (`data/outputs/pdp_<feature>.png`).  
  **Verification**: All PNG files open without error, have axis labels (`Hardness (HV)`, `Predicted Hardness (HV)`, feature names) and appropriate legends.

- [ ] **T013** [US2] **Final report generation (associational framing & limitations)**  
  Write `code/evaluation/generate_report.py` that aggregates: `.ingestion_status.json`, `test_metrics.yaml`, `paired_ttest_results.yaml`, `bootstrap_comparison.yaml`, `vif_report.yaml`, `shap_ranking.yaml`, `sensitivity_summary.yaml`.  
  Produce `data/processed/final_report.yaml` containing: all summary metrics, `associational_framing_warning`, any power‑limitation warning, and a `limitations` block stating that only compositional effects are modeled and thermal‑history effects are not captured.  
  **Verification**: The YAML validates against a simple schema (all keys present, numeric values match upstream files), and the warning strings are exactly as required (FR‑007).

- [ ] **T023** [US2] **Aggregated final report assembly**  
  Implement `code/evaluation/aggregate_final_report.py` that:  
  1. Reads `data/raw/.ingestion_status.json`, `data/processed/final_report.yaml`, and `data/processed/null_baseline.yaml`.  
  2. Merges these sections into a single human‑readable YAML `data/processed/final_aggregated_report.yaml`.  
  3. Writes a concise Markdown summary `specs/001-predicting-the-impact-of-composition-on/results.md` (see Phase 3).  
  **Verification**: The aggregated YAML exists, contains keys `ingestion_status`, `model_performance`, `null_baseline`, and passes a sanity‑check script.

- [ ] **T014** [US2] **Compute‑feasibility audit**  
  Implement `code/evaluation/verify_runtime.py` that runs the entire pipeline from T001 to T013 on the real curated dataset, measures wall‑clock time, peak RAM, and total disk usage of `data/` + `models/`.  
  Write `data/processed/runtime_report.yaml` with fields `total_runtime_seconds`, `peak_ram_gb`, `total_disk_gb`, and a boolean `within_budget`.  
  **Verification**: The report shows `within_budget: true` (≤ 6 h, ≤ 7 GB RAM, ≤ 14 GB disk) on the free‑tier runner; if any limit is exceeded the report includes the offending value.

- [ ] **T020** [US2] **CPU‑only environment verification**  
  Run a script `code/evaluation/check_cpu_xgboost.py` that imports `xgboost`, inspects `xgboost.__config__` (or equivalent) to confirm it contains `'cpu'` and does **not** contain `'gpu'`.  
  Write `data/processed/cpu_check.yaml` with `cpu_only: true/false`.  
  The task fails (non‑zero exit) if `cpu_only` is false, causing the pipeline to abort.  
  **Verification**: The YAML exists and reports `cpu_only: true`.

- [ ] **T021** [US2] **Schema validation of cleaned dataset**  
  Use `jsonschema` to validate `data/processed/solder_hardness_cleaned.csv` (converted to JSON records) against `specs/001-predicting-the-impact-of-composition-on/contracts/solder_dataset.schema.yaml`.  
  Write `data/processed/schema_validation.yaml` with `valid: true/false` and an optional `errors` list.  
  **Verification**: The file reports `valid: true`; any failure aborts the pipeline.

---

## Phase 3 – Reproducible results and paper handoff  

- [ ] **T015** [US2] **Methods & results markdown (results.md)**  
  Write `specs/001-predicting-the-impact-of-composition-on/results.md` that:  
  * Summarises dataset size, provenance (from `curation_notes.md`), and power‑limitation status.  
  * Presents model comparison (CV R²/RMSE, paired t‑test, bootstrap comparison, **null‑model baseline**).  
  * Lists SHAP top‑3 features, VIF flags, and sensitivity‑analysis outcomes.  
  * Embeds figure references (`pred_vs_measured.png`, `pdp_*.png`, `sensitivity_plot.png`).  
  * Includes the associational framing warning and limitations verbatim from `final_report.yaml`.  
  **Verification**: All referenced artifact paths exist, and the markdown can be rendered without broken links.

- [ ] **T016** [US2] **Full reproducibility re‑run & verification**  
  Update `specs/001-predicting-the-impact-of-composition-on/quickstart.md` with the complete workflow command chain (ingestion → features → training → evaluation → visualization → report → aggregation).  
  Execute the chain from a clean checkout, ensuring:  
  * All unit tests in `code/tests/` pass.  
  * Every artifact listed in `results.md` is regenerated and matches the previously recorded checksum (store a `data/checksums_final.txt` containing SHA‑256 of each final artifact).  
  * Record the outcome (“re‑run successful, all checksums identical”) in `results.md`.  
  **Verification**: The checksum file contains entries for every final artifact, and a script `code/evaluation/check_reproducibility.py` confirms exact matches.

---  

### Dependency & Requirement Coverage  

| Spec Requirement | Satisfying Task(s) |
|------------------|--------------------|
| FR‑001 / FR‑002 / SC‑004 | T001 → T002 → T003 |
| FR‑003 / FR‑014 | T006 |
| FR‑013 / SC‑006 | T007 |
| FR‑004 / FR‑010 | T008 |
| FR‑005 / SC‑001 / SC‑002 | T009 + **T019** (null baseline) |
| FR‑006 / SC‑003 | T010 |
| FR‑009 / SC‑005 | T011 |
| FR‑007 | T013, T015 |
| FR‑010 / FR‑011 / FR‑012 / SC‑007 | T014 + **T020** (CPU‑only check) |
| FR‑030 (schema) | **T021** |
| US‑001 | T001‑T003 |
| US‑002 | T006‑T012 |
| US‑003 | T012 |
| Edge‑case handling (N < 50, >5 elements, unit conversion) | T002, T014 |
| Data‑hygiene & checksums | **T017**, **T018**, T005 |
| Final aggregated report | **T023** |

Execution order (chronological):  
T017 → T001 → T018 → T002 → T003 → T004 → T005 → T006 → T007 → T008 → T019 → T009 → T010 → T011 → T012 → T013 → T023 → T014 → T020 → T021 → T015 → T016.  

All tasks remain unchecked; the verifier will run them, confirm artifact existence and correctness, and then allow the boxes to be ticked.  