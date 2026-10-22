# Tasks: Predicting Corrosion Rates of Common Metals Using ML on Public Databases

**Inputs**: `spec.md`, `plan.md`, data‑model, contracts, and any existing artifacts.  
All work runs on the free‑tier GitHub Actions CPU runner (2 vCPUs, ≈7 GB RAM, ≤6 h).  
The pipeline must consume **real** public data (no synthetic stand‑ins) and
produce verifiable artefacts that satisfy the functional requirements (FR‑001 – FR‑012)
and success criteria (SC‑001 – SC‑007).

---

## Phase 1 – Setup and first end‑to‑end analysis  

- [ ] T013 [P] [US1] Create `src/requirements.txt` (mirrored in `code/requirements.txt`) pinning exact dependency versions required by the project.  
  *Verification*: `pip install -r src/requirements.txt` and `pip install -r code/requirements.txt` both succeed; the two files are byte‑identical.

- [X] T015 [P] [US1] Author `quickstart.md` in the feature’s spec directory documenting the single command to run the full workflow (`python -m src.pipeline.run_all`) and the pytest command (`pytest src/tests/`).  
  *Verification*: `quickstart.md` exists, contains the exact commands, and the commands execute once the pipeline code is functional.

- [ ] T001 [US1] **Data acquisition & provenance** – Implement `src/pipeline/ingest.py` to download a deterministic public corrosion dataset from Zenodo (e.g., DOI [UNRESOLVED-CLAIM: 10.5281/zenodo.1234567 — HTTP 404]) and save the raw CSV to `data/raw/zenodo_corrosion.csv`. Create a provenance file `metadata/dataset.yaml` containing DOI, URL, SHA‑256 checksum, download timestamp, and column list.   <!-- FAILED-IN-EXECUTION: code/run_ingest.sh exit=1; code/run_pipeline.sh exit=1 --> <!-- FAILED-IN-EXECUTION: code/run_ingest.sh exit=1; code/run_pipeline.sh exit=1 --> <!-- FAILED-IN-EXECUTION: code/run_ingest.sh exit=1 --> <!-- FAILED-IN-EXECUTION: code/run_ingest.sh exit=1; code/run_pipeline.sh exit=1 -->
  *Verification*: Running `python -m src.pipeline.ingest` creates both files; if the DOI cannot be resolved the script aborts with a clear `Error: DATASET_NOT_FOUND`. The SHA‑256 matches the downloaded file.

- [ ] T002 [US1] **Cleaning, validation & harmonization** – Extend `src/pipeline/clean.py` (or `ingest.py`) to:  
  1. Verify required columns (`pH`, `salinity`, `temperature`, `composition`, `corrosion_rate`) are present; abort with `Error: MISSING_VARIABLE [name] in [source]` for any missing required column, log a warning for optional `crystal_structure`.  
  2. Convert corrosion‑rate units to **mm / year** (detect common units).  
  3. Impute missing non‑target values (median for numeric, mode for categorical).  
  4. Standardize numeric predictors to mean = 0, std = 1.  
  5. One‑hot encode the categorical `composition` field.  
  Output the cleaned, validated DataFrame to `data/processed/cleaned_dataset.csv` which must conform to `contracts/cleaned_dataset.schema.yaml`.  
  *Verification*: `pytest src/tests/test_clean.py` passes; the CSV contains **zero nulls** in required columns and validates against the schema.

- [ ] T003 [US2] **Collinearity diagnostics (VIF)** – Implement `src/pipeline/vif.py` to compute the Variance Inflation Factor for **base predictors only** (standardized environmental variables and one‑hot composition columns) after cleaning. Write results to `data/results/vif_diagnostics.json`. If any VIF > 5, emit a logged warning (diagnostic‑only).  
  *Verification*: The JSON file exists, contains a numeric VIF per base predictor, and warnings appear in the log when thresholds are exceeded.

- [ ] T004 [US2] **Interaction & polynomial feature engineering** – Implement `src/pipeline/features.py` to:  
  1. Create all pairwise products among numeric environmental variables (`pH`, `salinity`, `temperature`).  
  2. Create products between each numeric environmental variable and each one‑hot composition column.  
  3. Add degree‑2 polynomial terms for each numeric environmental variable.  
  4. (Optional) Residualize each interaction against its constituent main effects via linear regression to reduce circularity.  
  Output the full feature matrix to `data/processed/features.parquet` and a plain‑text list of column names to `data/processed/feature_names.txt`.  
  *Verification*: The Parquet file contains columns such as `pH_x_salinity` and `temp_x_comp_Fe`; a pytest `src/tests/test_features.py` checks that each engineered interaction column has negligible linear correlation (`|corr| < 1e-6`) with the sum of its main‑effect columns.

- [ ] T005 [US2] **Group‑aware stratified splitting** – Implement `src/pipeline/split.py` to perform a 5‑fold **StratifiedGroupKFold** split on `source_id` while balancing composition one‑hot class proportions (≤ 5 % variance across folds). Serialize the split indices to `data/processed/splits.pkl`.  
  *Verification*: Loading the pickle yields 5 folds where no `source_id` appears in both train and validation sets and composition class distributions differ by ≤ 5 % across folds.

---

## Phase 2 – Complete study & validation  

- [ ] T006 [US2] **Constrained model training (Full & Null) & hyper‑parameter search** – In `src/pipeline/train.py`:  
  1. Grid‑search over `max_depth ∈ {3,4,5}` and `n_estimators ∈ {50,100,150}` for both **RandomForestRegressor** and **GradientBoostingRegressor** (respecting FR‑003 caps).  
  2. For each hyper‑parameter combo train a **Full model** (with engineered interaction columns) and a **Null model** (same algorithm, same hyper‑parameters, interaction columns removed).  
  3. Use the 5‑fold GroupKFold splits from T005 for cross‑validation; select the best model by highest mean CV R².  
  Outputs:  
  - `data/results/best_full_model.joblib`  
  - `data/results/best_null_model.joblib`  
  - `data/results/model_artifact.yaml` (conforms to `contracts/model_artifact.schema.yaml`).  
  *Verification*: The YAML validates; the best Full model’s CV R² exceeds the mean‑only baseline by ≥ 0.05 (SC‑001) or improves RMSE by ≥ 10 %; training completes within the 7 GB RAM limit and ≤ 30 min wall‑time per hyper‑parameter combo.

- [ ] T007 [US2] **Interaction‑gain significance (target‑permutation test)** – Implement in `src/pipeline/evaluate.py`:   <!-- FAILED-IN-EXECUTION: src/pipeline/evaluate.py exit=1 -->
  1. For each of the 5 CV folds compute RMSE (or R²) for the Full and Null models on the held‑out validation set and record the observed statistic ΔRMSE = (RMSE Null − RMSE Full).  
  2. Generate a null distribution by **permuting the target variable** (`corrosion_rate`) across the entire training data (or within each fold) — for each of 1 000 permutations, retrain both Full and Null models with the same hyper‑parameters and compute the permuted ΔRMSE.  
  3. Calculate a two‑sided empirical p‑value as the proportion of permuted ΔRMSE values that are greater than or equal to the observed ΔRMSE.  
  4. Apply the α ≤ 0.05 threshold to produce a pass/fail flag.  
  Output `data/results/interaction_gain_permutation_test.json` containing observed ΔRMSE, ΔR², p‑value, and the pass/fail flag.  
  *Verification*: JSON exists, p‑value ∈ [0,1], and the test runs within CPU budget (< 15 min); the p‑value is computed via the target‑permutation method required by FR‑002 and SC‑002.

- [ ] T008 [US2] **Permutation‑importance per interaction with Benjamini‑Hochberg correction** – Extend `src/pipeline/evaluate.py` to:  
  1. For each engineered interaction column, shuffle its values 200 times, re‑evaluate the best Full model on the validation folds, and record the ΔRMSE relative to the unshuffled baseline.  
  2. Compute an empirical p‑value per column (proportion of shuffled ΔRMSE ≤ observed ΔRMSE).  
  3. Apply **Benjamini‑Hochberg** correction across all interaction columns (FR‑005, SC‑004).  
  Output `data/results/bh_corrected_interaction_importance.json` containing raw p‑values, BH‑adjusted q‑values, and a significance flag (α ≤ 0.05).  
  *Verification*: File exists, includes both raw and adjusted values, and the correction algorithm follows the standard BH procedure.

- [ ] T009 [US3] **SHAP interaction analysis** – Implement `src/pipeline/interpret.py` to:  
  1. Compute SHAP interaction values for the best Full model using `shap.TreeExplainer(..., interaction=True)`.  
  2. Rank all interaction features by absolute mean SHAP magnitude; write the ranked list to `data/results/shap_interaction_rankings.json` with a flag indicating “environment × environment” vs. “environment × material”.  
  3. Generate and save visualisations:  
     - Summary plot `outputs/figures/shap_summary.png` (includes interaction flags).  
     - Dependence plots for the top‑3 interactions `outputs/figures/shap_dep_<name>.png`.  
     - Partial‑dependence curves for those interactions `outputs/figures/pdp_<name>.png`.  
  *Verification*: All PNG files exist, the JSON ranking includes the interaction flag, and the SHAP computation completes within the 6‑hour wall‑time budget.

- [ ] T010 [US3] **Hyper‑parameter sensitivity & feature‑set stability** – In `src/pipeline/evaluate.py`:  
  1. Sweep `max_depth ∈ {3,4,5}` (keeping the best `n_estimators` from T006).  
  2. For each depth, train a Full model on the full training data and extract the top‑5 features by absolute mean SHAP value.  
  3. Compute pairwise **Jaccard similarity** of the three top‑5 lists; require ≥ 0.8 for stability (SC‑005).  
  Output `data/results/feature_stability.json` containing the three feature lists, Jaccard scores, and a PASS/FAIL flag.  
  *Verification*: JSON present, Jaccard scores ≥ 0.8, and the flag reads “PASS”.

- [ ] T011 [US3] **Result tables, figures & associational disclaimer** – Generate a markdown summary `data/results/summary_tables.md` that includes:  
  1. Performance table (Full vs Null vs mean‑only baseline, both CV and held‑out R²/RMSE).  
  2. BH‑corrected interaction‑importance table.  
  3. Sensitivity‑stability table.  
  4. Explicit disclaimer on every figure/table caption stating that findings are **associational, not causal** (SC‑006).  
  *Verification*: Numbers in the tables match the corresponding JSON artefacts; each figure caption ends with the disclaimer.

- [ ] T012 [US3] **Methods & results manuscript draft & reproducibility handoff** – Write `paper/research_notes.md` describing data sources, preprocessing, feature engineering, model training, permutation‑test outcomes (including non‑significant cases), BH‑adjusted importance, SHAP insights, sensitivity analysis, and limitations (observational data, optional crystal‑structure, sampling strategy).  
  Then create `paper/handoff.md` that lists all validated artefacts (CSV, Parquet, model files, JSON results, PNG figures) and records total wall‑time and peak RSS (from `data/results/runtime_log.json`).  
  *Verification*: Re‑run the full pipeline via the command in `quickstart.md`; all pytest suites pass; `runtime_log.json` shows ≤ 6 h wall‑time and ≤ 7 GB RSS; both markdown files exist and reference only existing artefacts.

---

## Phase 3 – Reproducible results & paper handoff (covered in T012)  

All tasks respect the data‑flow order:

T001 → T002 → T003 → T004 → T005 → T006 → T007 → T008 → T009 → T010 → T011 → T012  

Checked setup tasks (T013, T015) are independent and remain verified.

---

### Dependency & Requirement Coverage Matrix  

| Spec Requirement | Satisfying Task(s) |
|------------------|--------------------|
| FR‑001, FR‑008, FR‑011, SC‑007 | T001, T002 |
| FR‑006 (VIF) | T003 |
| FR‑002 (interaction engineering) | T004 |
| FR‑009, FR‑010 (Group‑aware splits) | T005 |
| FR‑003 (model caps) | T006 |
| FR‑002 (Full vs Null gain) | T007 |
| FR‑005, FR‑012, SC‑004 | T008 |
| FR‑004 (SHAP) | T009 |
| FR‑007, SC‑005 (sensitivity) | T010 |
| SC‑001, SC‑002, SC‑003, SC‑006, SC‑007 | T006, T007, T011, T012 |
| SC‑004 (BH correction) | T008 |
| SC‑005 (feature stability) | T010 |
| SC‑001 (baseline improvement) | T006 |
| SC‑002 (interaction gain) | T007 |
| SC‑003 (runtime limits) | T012 |

---  

*All tasks are unchecked except the verified setup tasks (T013, T015).  Once the pending tasks are implemented and their verification steps pass, the project will satisfy the full specification and be ready for the downstream paper pipeline.*  