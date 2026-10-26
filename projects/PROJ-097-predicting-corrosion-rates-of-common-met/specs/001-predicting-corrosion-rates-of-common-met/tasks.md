# Tasks: Predicting Corrosion Rates of Common Metals Using Machine Learning on Public Databases  

**Inputs**: `spec.md`, `plan.md`, `data‑model.md`, contracts, and any existing artifacts.  
All work runs on the free‑tier GitHub Actions CPU runner (2 vCPUs, ≈7 GB RAM, ≤ 6 h).  
The pipeline must consume **real** public data (no synthetic stand‑ins) and
produce verifiable artefacts that satisfy every functional requirement
(FR‑001 – FR‑012) and success criterion (SC‑001 – SC‑007).

---

## Phase 1 – Data ingestion, validation & harmonisation (User Story 1)

- [ ] T000 [P] **Citation validation** – Run the Reference‑Validator Agent on `spec.md` and `plan.md` and store the report at `reports/citation_validation.json`.  
  *Verification*: The JSON contains only entries with `"status": "verified"`.

- [ ] T001 [US1] **Ingest raw corrosion dataset & record provenance** – Implement `src/pipeline/ingest.py` to download the dataset from a deterministic public URL (e.g. `[UNRESOLVED-CLAIM: https://zenodo.org/records/1041234/files/corrosion_dataset.csv?download=1` — HTTP 404]).  
  *Outputs*:  
  - `data/raw/corrosion_dataset.csv` (unchanged original file)  
  - `metadata/dataset.yaml` (DOI, URL, SHA‑256 checksum, download timestamp, column list).  
  *Verification*: Running `python -m src.pipeline.ingest` creates both files; if the URL returns a non‑200 status the script aborts with `Error: DATASET_NOT_FOUND`. The SHA‑256 in the YAML matches the downloaded file and the provenance fields are present.

- [ ] T002 [US1] **Cleaning, validation & unit harmonisation** – Extend `src/pipeline/clean.py` to:  
  1. Verify presence of required columns (`pH`, `salinity`, `temperature`, `composition`, `corrosion_rate`). Abort with `Error: MISSING_VARIABLE [name] in [source]` for any missing required column; log a warning for optional `crystal_structure`.  
  2. Detect and convert corrosion‑rate units to **mm / year** (supporting “mm/yr”, “µm/h”, etc.).  
  3. Impute missing non‑target values (median for numeric, mode for categorical).  
  4. Standardise numeric predictors to z‑scores (mean = 0, std = 1).  
  5. One‑hot encode `composition`.  
  *Outputs*: `data/processed/cleaned_dataset.csv` (conforms to `contracts/cleaned_dataset.schema.yaml`).  
  *Verification*: `pytest src/tests/test_clean.py` passes; the CSV contains **zero nulls** in all required columns, matches the JSON schema, and the provenance metadata file is present.

- [ ] T002_val [US1] **Ingestion‑validation pass‑rate** – Create `src/pipeline/validation.py` that runs the T001 → T002 pipeline three times on a held‑out validation CSV (`data/validation/validation_subset.csv`). Compute the empirical pass‑rate based on (a) zero runtime errors, (b) presence of all required columns, (c) zero nulls in required columns.  
  *Output*: `data/results/ingestion_validation_metrics.json` (field `pass_rate`).  
  *Verification*: The JSON exists and `pass_rate ≥ 0.95`, satisfying SC‑007.

- [ ] T003 [US2] **Collinearity diagnostics (VIF) for base predictors** – Implement `src/pipeline/vif.py` to compute the Variance Inflation Factor for each base predictor (standardised env. variables + one‑hot composition columns) after cleaning.  
  *Output*: `data/results/vif.log` (plain‑text log listing each predictor and its VIF; warnings for any VIF > 5).  
  *Verification*: The log file is present; the run‑log contains a warning line for any predictor with VIF > 5.

- [ ] T004 [US2] **Interaction & polynomial feature engineering** – Implement `src/pipeline/features.py` to:  
  1. Create all pairwise products among numeric env. variables (`pH`, `salinity`, `temperature`).  
  2. Create products between each numeric env. variable and each one‑hot composition column.  
  3. Add degree‑2 polynomial terms for each numeric env. variable.  
  *Outputs*:  
  - `data/processed/features.parquet` (full feature matrix).  
  - `data/processed/feature_names.txt` (plain‑text, one name per line, matching column order in the Parquet file).  
  *Verification*: `pytest src/tests/test_features.py` checks that every engineered interaction column exists and that its values equal the element‑wise product of the constituent columns (tolerance < 1e‑6); additionally the test asserts that `feature_names.txt` exists and its line order matches the Parquet column order.

- [ ] T005 [US2] **Group‑aware 5‑fold split** – Implement `src/pipeline/split.py` to perform a `GroupKFold` (5 folds) on `source_id`, guaranteeing no `source_id` appears in both train and validation sets. Serialize the split indices to `data/processed/splits.pkl`.  
  *Output*: `data/processed/splits.pkl`.  
  *Verification*: Loading the pickle yields five `(train_idx, val_idx)` tuples that respect the group constraint and maintain composition‑class proportions within ± 5 % across folds.

- [ ] T006_baseline [US2] **Baseline mean‑only model** – Implement `src/pipeline/baseline.py` that, for each CV fold from T005, predicts the training‑set mean corrosion rate for every test sample and records R² and RMSE.  
  *Output*: `data/results/baseline_performance.json`.  
  *Verification*: The JSON contains fields `r2` and `rmse`; the values are used later to check SC‑001.

- [ ] T006 [US2] **Constrained model training (Full & Null) & hyper‑parameter search** – Implement `src/pipeline/train.py` to:  
  1. Grid‑search over `max_depth ∈ {3,4,5}` and `n_estimators ∈ {50,100,150}` for both `RandomForestRegressor` and `GradientBoostingRegressor` (respecting FR‑003 caps).  
  2. For each hyper‑parameter combo train a **Full model** (with engineered interaction columns) and a **Null model** (same algorithm, same hyper‑parameters, interaction columns removed).  
  3. Use the 5‑fold GroupKFold splits from T005 for cross‑validation; select the best model by highest mean CV R².  
  *Outputs*:  
  - `data/results/best_full_model.joblib`  
  - `data/results/best_null_model.joblib`  
  - `data/results/model_artifact.yaml` (conforms to `contracts/model_artifact.schema.yaml`).  
  *Verification*: The YAML validates; `src/tests/test_training.py` confirms that the best Full model’s CV R² exceeds the baseline R² by **≥ 0.05** (or improves RMSE by **≥ 10 %**) and that peak RSS stayed ≤ 7 GB (checked via `psutil` logs).

- [ ] T007 [US2] **Interaction‑gain permutation test (correct formulation)** – Implement `src/pipeline/evaluate.py` to assess whether interaction features add predictive value:  
  1. Compute the observed ΔRMSE = RMSE_Null − RMSE_Full on each CV fold using the best hyper‑parameters from T006.  
  2. For 1 000 repetitions, **shuffle only the engineered interaction columns** (keeping base predictors and the target fixed), retrain both Full and Null models on the shuffled data, and recompute ΔRMSE.  
  3. Empirical p‑value = proportion of shuffled ΔRMSE ≥ observed ΔRMSE (upper‑tail).  
  *Output*: `data/results/interaction_gain_test.json` (fields: `observed_delta_rmse`, `mean_shuffled_delta_rmse`, `p_value`, `pass`).  
  *Verification*: The JSON exists, `p_value` ∈ [0,1], and the test runs within ≤ 15 min on the CPU runner.

---

## Phase 2 – Interaction importance, interpretability & stability (User Story 3)

- [ ] T008 [US3] **Conditional permutation importance for *all* features with BH correction** – Extend `src/pipeline/evaluate.py` to:  
  1. For **every** feature (both base predictors and engineered interaction columns), shuffle its values 200 times, evaluate the best Full model on the validation folds, and record ΔRMSE relative to the unshuffled baseline.  
  2. Compute an empirical p‑value per column (proportion of shuffled ΔRMSE ≤ observed ΔRMSE).  
  3. Apply **Benjamini‑Hochberg** correction across **all** features (base + interaction) as required by FR‑005 and SC‑004.  
  *Output*: `data/results/bh_corrected_feature_importance_all.json` (raw p‑values, BH‑adjusted q‑values, significance flags for every feature).  
  *Verification*: `src/tests/test_permutation_importance.py` checks that the BH procedure follows the standard algorithm and that the file contains both raw and adjusted values for **all** features.

- [ ] T009 [US3] **SHAP interaction analysis** – Implement `src/pipeline/interpret.py` to:  
  1. Compute SHAP interaction values for the best Full model using `shap.TreeExplainer(..., interaction=True)`.  
  2. Rank all interaction features by absolute mean SHAP magnitude and write the ranking to `data/results/shap_interaction_rankings.json` (including a flag indicating “env × env” vs. “env × material”).  
  3. Generate visualisations:  
     - Summary plot `outputs/figures/shap_summary.png` (interaction terms flagged).  
     - Dependence plots for the top‑3 interactions `outputs/figures/shap_dep_<name>.png`.  
     - Partial‑dependence curves for those interactions `outputs/figures/pdp_<name>.png`.  
  *Verification*: All PNG files exist, the JSON ranking matches the plotted interactions, and `src/tests/test_shap.py` confirms that the SHAP computation finishes within the 6‑hour wall‑time budget.

- [ ] T010 [US3] **Hyper‑parameter sensitivity & feature‑set stability** – In `src/pipeline/evaluate.py`:  
  1. Sweep `max_depth ∈ {3,4,5}` (keeping the best `n_estimators` from T006).  
  2. For each depth, train a Full model on the full training data and extract the top‑5 features by absolute mean SHAP value.  
  3. Compute pairwise **Jaccard similarity** of the three top‑5 lists; require ≥ 0.8 for stability (SC‑005).  
  *Output*: `data/results/feature_stability.json` (lists of top‑5 features per depth, Jaccard scores, `pass` flag).  
  *Verification*: `src/tests/test_stability.py` validates the Jaccard calculations and that all scores meet the threshold.

- [ ] T011 [US3] **Summary tables, figures & associational disclaimer** – Generate `data/results/summary_tables.md` containing:  
  1. Performance table (Full vs Null vs baseline, CV and held‑out R²/RMSE).  
  2. BH‑corrected feature‑importance table (all features).  
  3. Sensitivity‑stability table.  
  4. Explicit disclaimer on every figure/table caption stating that findings are **associational, not causal** (fulfilling SC‑006).  
  *Verification*: Numbers in the markdown match the corresponding JSON artefacts; each figure caption ends with the disclaimer. `src/tests/test_summary.py` checks consistency.

- [ ] T012 [US3] **Methods & results manuscript draft & reproducibility handoff** – Write two markdown hand‑off documents:  
  - `paper/research_notes.md` (concise methods, results, interpretation).  
  - `paper/handoff.md` (step‑by‑step reproducibility instructions, including the command from `quickstart.md`).  
  Also produce `data/results/runtime_log.json` (total wall‑time, peak RSS) and copy the final `ingestion_validation_metrics.json` for completeness.  
  *Verification*: Running `python -m src.pipeline.run_all` reproduces all artefacts, all pytest suites pass, `runtime_log.json` reports ≤ 6 h wall‑time and ≤ 7 GB RSS, and both markdown files exist and reference only real artefacts.

- [ ] T014 [US3] **Quantify variance explained by interaction terms** – Using the SHAP interaction values from T009, compute the proportion of total SHAP variance attributable to interaction features and write the numeric result to `data/results/interaction_variance.json` (field `variance_explained_by_interactions`).  
  *Verification*: The JSON file exists, the value is a float between 0 and 1, and `src/tests/test_interaction_variance.py` checks that the sum of interaction SHAP contributions plus base‑feature contributions equals the total model SHAP variance (within tolerance 1e‑4).

---

## Phase 3 – Project scaffolding (already satisfied)

- [ ] T013 [P] **Exact, mirrored requirements files** – Create `src/requirements.txt` with *exact* version pins (no wild‑cards) matching the list in `plan.md`. Copy the file byte‑for‑byte to `code/requirements.txt`.  
  *Verification*: `diff -q src/requirements.txt code/requirements.txt` reports no differences; `pip install -r src/requirements.txt` succeeds without warnings.

- [ ] T015 [P] **Quick‑start documentation** – Ensure `quickstart.md` exists and documents the single command `python -m src.pipeline.run_all` and the pytest command `pytest src/tests/`.  
  *Verification*: The file contains the exact commands and they run successfully on a fresh checkout.

---

### Dependency & Requirement Coverage Matrix  

| Spec Requirement | Satisfying Task(s) |
|------------------|--------------------|
| FR‑001, FR‑008, FR‑011, SC‑007 | T001, T002, T002_val |
| FR‑006 (VIF) | T003 |
| FR‑002 (interaction engineering) | T004 |
| FR‑009, FR‑010 (Group‑aware splits) | T005 |
| FR‑003 (model caps) | T006 |
| FR‑002 (Full vs Null gain) | T007 |
| FR‑005, FR‑012, SC‑004 | T008 |
| FR‑004 (SHAP) | T009 |
| FR‑007, SC‑005 (sensitivity) | T010 |
| SC‑001, SC‑002, SC‑003, SC‑006, SC‑007 | T006_baseline, T006, T007, T011, T012 |
| SC‑004 (BH correction) | T008 |
| SC‑005 (feature stability) | T010 |
| SC‑001 (baseline improvement) | T006_baseline, T006 |
| SC‑002 (interaction gain) | T007 |
| SC‑003 (runtime limits) | T006, T012 |
| Principle II (Verified Accuracy) | T000 |
| Principle VI (Interaction‑Effect Quantification) | T014 |
| Reviewer comment on permutation test | T007 implements the correct interaction‑column permutation test (no target permutation). |

All pending tasks are unchecked; completed scaffolding tasks are checked. Once the unchecked tasks are implemented and their verification suites pass, the project will satisfy the full specification and be ready for downstream paper hand‑off.  