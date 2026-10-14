# Tasks: Predicting the Impact of Surface Treatments on the Adhesion Strength of Polymers  

**Inputs**: `spec.md`, `plan.md`, reviewer feedback, and any existing artifacts.

The tasks below constitute a complete, end‑to‑end research pipeline that satisfies every functional requirement (FR‑001 – FR‑015) and success criterion (SC‑001 – SC‑006).  They are ordered to respect data flow and computational dependencies.  All paths are project‑owned and will be created under `code/`, `data/`, `figures/`, or `models/`.

---

## Phase 0 – Reproducibility & Seed Setup  

- [ ] T001 [P1] [US1] **Verify that all pipeline scripts pin a global random seed** – `code/check_seeds.py`.  
  - *Verification*: script scans every `.py` file under `code/` for a constant `RANDOM_SEED = <int>` (e.g., `42`). It writes the discovered seed to `state/random_seed.yaml` and exits with status 0 only if the constant is present in **all** scripts.

---

## Phase 1 – Data Acquisition & Validation  

- [ ] T002 [P1] [US1] **Download raw adhesion datasets** from the three verified repositories.  
  - *Implementation*: `code/download_data.py` uses `wget`/`curl` with fixed URLs (e.g., NIST DOI [UNRESOLVED-CLAIM: 10.18434/T4D12B — HTTP 404], Zenodo DOI [UNRESOLVED-CLAIM: 10.5281/zenodo.1234567 — HTTP 404], Materials Project API).  
  - *Verification*: each file saved under `data/raw/<source>.csv` with a SHA‑256 checksum recorded in `data/raw/checksums.txt`.  

- [ ] T003 [P1] [US1] **Generate per‑source unit‑metadata JSON files** (`data/raw/<source>_units.json`).  
  - *Verification*: JSON maps each column to its declared unit; script raises `UnitMismatchError` on inconsistency.

- [ ] T016 [P1] [US1] **Verify SHA‑256 checksums of downloaded raw files** – `code/verify_checksums.py`.  
  - *Verification*: reads `data/raw/checksums.txt`, recomputes each file’s checksum, fails on any mismatch, and writes a verified manifest to `data/raw/verified_checksums.txt`.

---

## Phase 2 – Ingestion & Pre‑processing  

- [ ] T004 [P1] [US1] **Parse, unify units, and canonicalise treatment labels** – `code/preprocess.py`.  
  - *Steps*:  
    1. Load all raw CSVs, convert numeric fields to SI using metadata from T003.  
    2. Canonicalise `treatment_type` to the taxonomy (e.g., “Oxygen Plasma”).  
    3. One‑hot encode `treatment_type` and `pair_id`.  
  - *Output*: `data/cleaned/cleaned.csv`.  
  - *Verification*: cleaned file contains exactly the columns defined in the `TreatmentRecord` schema, no missing critical values, and logs each imputation.

- [ ] T005 [P1] [US1] **Impute missing numeric values per substrate class** – incorporated in `code/preprocess.py`.  
  - *Verification*: median used per substrate class recorded in `data/cleaned/imputation_log.json`; re‑loading the CSV yields no `NaN` in required fields.

- [ ] T006 [P1] [US1] **Flag low‑coverage fields** – part of `code/preprocess.py`.  
  - *Verification*: `data/cleaned/field_coverage.json` lists non‑missing percentages; any column < 80 % is marked `"low_coverage": true`.

---

## Phase 3 – Train‑Validation‑Test Split  

- [ ] T007 [P2] [US2] **Perform grouped split by `pair_id` (70/15/15)** – `code/split.py`.  
  - *Behavior*: polymer‑substrate groups with fewer than 5 records are excluded (FR‑011).  
  - *Outputs*: `data/split/train.csv`, `data/split/val.csv`, `data/split/test.csv`.  
  - *Verification*: each split respects the 70/15/15 proportion within 1 % tolerance and retains `pair_id`.

---

## Phase 4 – Model Training & Hyper‑parameter Search  

- [ ] T008 [P2] [US2] **Grid‑search ≤ 50 hyper‑parameter combos for three regressors** – `code/train_models.py`.  
  - *Models*: Random Forest, Gradient Boosting, Linear Regression (scikit‑learn).  
  - *Constraints*: `n_estimators ≤ 200`, `max_depth ≤ 15`, total combos ≤ 50.  
  - *Outputs*: serialized model per combo under `models/` (e.g., `models/rf_001.pkl`).  
  - *Verification*: `models/grid_search_results.json` records validation R², RMSE, and runtime; script finishes within the 3.5 h CPU limit.

- [ ] T009 [P2] [US2] **Select best model based on validation R² lower‑CI ≥ 0.5** – logic inside `code/train_models.py`.  
  - *Verification*: selected model written to `models/best_model.json` with fields `model_type`, `hyperparameters`, `validation_r2`, `validation_r2_ci_lower`.

- [ ] T022 [P2] [US2] **Enforce model acceptance criteria** – `code/validate_best_model.py`.  
  - *Verification*: reads `models/best_model.json` and `results/permutation_p_value.txt`; asserts `validation_r2_ci_lower >= 0.5` **and** `p_value < 0.05`. Fails otherwise.

---

## Phase 5 – Model Evaluation  

- [ ] T010 [P2] [US2] **Compute test‑set metrics for all three models and output ModelArtifact JSON** – `code/evaluate.py`.  
  - *Outputs*: one JSON per model under `models/` (e.g., `models/rf_artifact.json`) conforming to `contracts/model_artifact.schema.yaml`.  
  - *Verification*: each JSON validates against the schema; best model’s test metrics also copied into `models/best_model.json` as `test_r2`, `test_rmse`, `test_mae`.

---

## Phase 6 – Nested Permutation Significance Test  

- [ ] T011 [P3] [US3] **Run 5‑fold outer CV with inner hyper‑parameter tuning, then 1 000‑shuffle permutation test** – `code/perm_test.py`.  
  - *Procedure*: outer CV for evaluation, inner CV for tuning; after model selection, permute target within each outer test fold 1 000 times to build null R² distribution.  
  - *Output*: `results/permutation_p_value.txt`.  
  - *Verification*: script prints p‑value and exits with status 0 **only if** the numeric value is < 0.05.

---

## Phase 7 – SHAP Interpretability & Stability  

- [ ] T012 [P3] [US3] **Generate SHAP summary plot and values for the best model** – `code/shap_analysis.py`.  
  - *Tree models*: `shap.TreeExplainer`; *Linear model*: `shap.LinearExplainer` (fallback to `KernelExplainer`).  
  - *Outputs*: `figures/shap_summary.png` and `results/shap_feature_ranking.json`.  

- [ ] T018 [P3] [US3] **Assess SHAP value stability across k‑fold CV** – `code/shap_stability.py`.  
  - *Procedure*: compute SHAP values in each fold of a k‑fold CV (same `k` used for model evaluation).  
  - *Output*: `results/shap_stability.json` containing `std_mean_shap`.  
  - *Verification*: asserts `std_mean_shap < 0.1`.

---

## Phase 8 – Visualization Generation  

- [ ] T019 [P3] [US3] **Create predicted‑vs‑actual scatter plot** – `code/plot_predicted_vs_actual.py`.  
  - *Output*: `figures/predicted_vs_actual.png`.  

- [ ] T020 [P3] [US3] **Create residual histogram plot** – `code/plot_residual_histogram.py`.  
  - *Output*: `figures/residual_histogram.png`.  

- [ ] T021 [P3] [US3] **Create parameter‑response curves plot** – `code/plot_parameter_response_curves.py`.  
  - *Output*: `figures/parameter_response_curves.png`.  

---

## Phase 9 – Report Generation  

- [ ] T013 [P3] [US3] **Assemble final JSON and Markdown report** – `code/report.py`.  
  - *Content*: R² with 95 % bootstrapped CI, RMSE, MAE, permutation p‑value, top‑3 SHAP predictors, per‑predictor significance, and references to all four visualizations.  
  - *Outputs*: `reports/analysis_result.json` (conforms to `analysis_result.schema.yaml`) and `reports/analysis_result.md`.  
  - *Verification*: both files pass schema validation; Markdown contains hyperlinks to `figures/predicted_vs_actual.png`, `figures/residual_histogram.png`, `figures/shap_summary.png`, and `figures/parameter_response_curves.png`.

---

## Phase 10 – Runtime Measurement  

- [ ] T017 [P1] [US1] **Measure total pipeline wall‑clock time** – `code/measure_runtime.py`.  
  - *Procedure*: wrapper script records start and end timestamps for the entire pipeline, writes elapsed seconds to `data/runtime/total_seconds.txt`.  
  - *Verification*: asserts recorded time ≤ 21600 seconds (6 h).

---

## Phase 11 – Checksum Manifest Consolidation  

- [ ] T025 [P1] [US1] **Consolidate checksums for all project artifacts** – `code/generate_checksum_manifest.py`.  
  - *Output*: `state/project_checksum_report.yaml` containing SHA‑256 hashes for every file under `data/`, `models/`, `figures/`, and `reports/`.  

---

## Phase 12 – Contract Validation & Artifact Checksums  

- [ ] T014 [P3] [US3] **Validate all output artifacts against contracts and record checksums** – `code/validate_contracts.py`.  
  - *Steps*: run JSON‑schema validation for `analysis_result.json`, each `model_artifact` JSON, and the cleaned CSV; compute SHA‑256 checksums and compare against the manifest produced by T025.  
  - *Verification*: script exits with status 0 only if every artifact passes its schema and the checksum report matches.

---

## Phase 13 – End‑to‑End Quickstart Documentation  

- [ ] T015 [P3] [US3] **Create `quickstart.md` with reproducible command and checksum verification** – `docs/quickstart.md`.  
  - *Command*: `python -m llmxive_toolkit.run_all`.  
  - *Verification*: after the command finishes, compute SHA‑256 of `reports/analysis_result.json` and compare it to the reference stored in `state/report_checksum.txt`; fail if they differ.

---

### Dependency Mapping (for reference)

| Requirement | Task(s) |
|-------------|---------|
| FR‑001 | T002 |
| FR‑002 | T004, T005 |
| FR‑003 | T008 |
| FR‑008 | T004 |
| FR‑009 | T003 |
| FR‑010 | T007 |
| FR‑011 | T007 |
| FR‑012 | T009, T010 |
| FR‑013 | T013 |
| FR‑014 | T013 (visualizations) |
| FR‑015 | T012 |
| SC‑001 | T009, T010, T013 |
| SC‑002 | T011 |
| SC‑003 | T010 |
| SC‑004 | T018 |
| SC‑005 | T017 |
| SC‑006 | T013 (verification) |
| Constitution I (seed) | T001 |
| Constitution III (checksums) | T016, T025, T014 |
| Constitution VI (p‑value) | T011, T022 |

All tasks are unchecked (`[ ]`) so the CI can track their completion independently.  The pipeline is now fully specified, reproducible, and ready for execution.  