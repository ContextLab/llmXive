# Tasks: Predicting Corrosion Rates of Common Metals Using ML on Public Databases  

**Inputs**: `spec.md`, `plan.md`, `data‑model.md`, contracts, and any existing artifacts.  
All work runs on the free‑tier GitHub Actions CPU runner (2 vCPUs, ≈7 GB RAM, ≤ 6 h).  
The pipeline must consume **real** public data (no synthetic stand‑ins) and
produce verifiable artefacts that satisfy every functional requirement (FR‑001 – FR‑012) and success criterion (SC‑001 – SC‑007).

---

## Phase 1 — User Story 1: Data Ingestion, Validation, and Harmonization

- [ ] **T000** [P] **Citation Validation** – Use the Reference-Validator Agent to verify all external citations in `spec.md` and `plan.md` against primary sources.
  *Verification*: Reference-Validator report shows all citations as `verified` with title-token-overlap $\ge 0.7$.

- [ ] **T001** [US1] **Data acquisition & provenance** – Implement `src/pipeline/ingest.py` to download a deterministic public corrosion dataset from Zenodo (DOI [UNRESOLVED-CLAIM: 10.5281/zenodo.4393358 — HTTP 410]).  
  *Outputs*:  
  - `data/raw/zenodo_corrosion.csv` (raw file, unchanged)  
  - `metadata/dataset.yaml` containing DOI, URL, SHA‑256 checksum, download timestamp, and column list.  
  *Verification*: Running `python -m src.pipeline.ingest` creates both files; if the DOI cannot be resolved the script aborts with `Error: DATASET_NOT_FOUND`. The SHA‑256 in the YAML matches the downloaded file.

- [ ] **T002** [US1] **Cleaning, validation & harmonization** – Extend `src/pipeline/clean.py` to:  
  1. Verify required columns (`pH`, `salinity`, `temperature`, `composition`, `corrosion_rate`). Abort with `Error: MISSING_VARIABLE [name] in [source]` for any missing required column; log a warning for optional `crystal_structure`.  
  2. Convert corrosion‑rate units to **mm / year** (detect common units).  
  3. Impute missing non‑target values (median for numeric, mode for categorical).  
  4. Standardize numeric predictors (mean = 0, std = 1).  
  5. One‑hot encode `composition`.  
  *Outputs*: `data/processed/cleaned_dataset.csv` (must validate against `contracts/cleaned_dataset.schema.yaml`).  
  *Verification*: `pytest src/tests/test_clean.py` passes; the CSV contains **zero nulls** in required columns and conforms to the schema.

- [ ] **T002_val** [US1] **Ingestion Validation Pass-Rate** – Implement a validation script that runs the T001 $\rightarrow$ T002 pipeline three times on a held-out validation CSV. Compute the empirical pass-rate based on (a) zero runtime errors, (b) presence of all required columns, and (c) zero nulls in required columns.
  *Output*: `data/results/ingestion_validation_metrics.json` (containing pass-rate $\ge 95\%$).
  *Verification*: The JSON file exists and the calculated pass-rate is $\ge 95\%$, satisfying SC-007.

- [ ] **T013** [P] [US1] **Exact, mirrored requirements files** – Create `src/requirements.txt` with *exact* version pins (no wild‑cards) matching the list in `plan.md`. Copy the file byte‑for‑byte to `code/requirements.txt`.  
  *Verification*: `diff -q src/requirements.txt code/requirements.txt` reports no differences; `pip install -r src/requirements.txt` succeeds without warnings.

- [ ] **T015** [P] [US1] **Quick‑start documentation** – Ensure `quickstart.md` is present and documents the single command `python -m src.pipeline.run_all` and the pytest command `pytest src/tests/`.  
  *Verification*: Confirm `quickstart.md` exists and contains the exact command `python -m src.pipeline.run_all`.

---

## Phase 2 — User Story 2: Interaction Feature Engineering and Model Training

- [ ] **T003** [US2] **Collinearity diagnostics (VIF)** – Implement `src/pipeline/vif.py` to compute the Variance Inflation Factor for **base predictors only** (standardized env. variables + one‑hot composition columns) after cleaning.  
  *Outputs*: `data/results/vif_diagnostics.json` (mapping predictor $\rightarrow$ VIF).  
  *Verification*: The JSON file exists, contains numeric VIFs, and the run‑log includes a warning for any predictor with VIF > 5.

- [ ] **T004** [US2] **Interaction & polynomial feature engineering** – Implement `src/pipeline/features.py` to:  
  1. Create all pairwise products among numeric env. variables (`pH`, `salinity`, `temperature`).  
  2. Create products between each numeric env. variable and each one‑hot composition column.  
  3. Add degree‑2 polynomial terms for each numeric env. variable.  
  *Outputs*:  
  - `data/processed/features.parquet` (full feature matrix)  
  - `data/processed/feature_names.txt` (one feature name per line, matching column order).  
  *Verification*: A pytest `src/tests/test_features.py` checks that every engineered interaction column exists and that its Pearson correlation with the sum of its constituent main effects is < 1e‑6.

- [ ] **T005** [US2] **Group‑aware 5‑fold splitting** – Implement `src/pipeline/split.py` to perform a **GroupKFold** split (5 folds) on `source_id`, ensuring no `source_id` appears in both train and validation sets. Serialize the split indices.  
  *Outputs*: `data/processed/splits.pkl`.  
  *Verification*: Loading the pickle yields 5 folds satisfying the group‑aware constraint and with composition‑class proportions differing by ≤ 5 % across folds.

- [ ] **T006_baseline** [US2] **Baseline Mean-Only Model** – Implement a baseline predictor that predicts the training-set mean corrosion rate for every test sample. Evaluate using the GroupKFold splits from T005.
  *Output*: `data/results/baseline_performance.json` (containing R² and RMSE).
  *Verification*: The JSON file exists and contains valid metrics for comparison in T006.

- [ ] **T006** [US2] **Constrained model training (Full & Null) & hyper‑parameter search** – In `src/pipeline/train.py`:  
  1. Grid‑search over `max_depth ∈ {3,4,5}` and `n_estimators ∈ {50,100,150}` for both **RandomForestRegressor** and **GradientBoostingRegressor** (respecting FR‑003 caps).  
  2. For each hyper‑parameter combo train a **Full model** (with engineered interaction columns) and a **Null model** (same algorithm, same hyper‑parameters, interaction columns removed).  
  3. Use the 5-fold GroupKFold splits from T005 for cross‑validation; select the best model by highest mean CV R².  
  *Outputs*:  
  - `data/results/best_full_model.joblib`  
  - `data/results/best_null_model.joblib`  
  - `data/results/model_artifact.yaml` (conforms to `contracts/model_artifact.schema.yaml`).  
  *Verification*: The YAML validates; the best Full model’s CV R² exceeds the baseline in `baseline_performance.json` by ≥ 0.05 (or improves RMSE by ≥ 10 %) – verified by `src/tests/test_training.py`. Peak RSS stays ≤ 7 GB and each hyper‑parameter combo finishes within the 30‑minute per‑combo budget, as verified by `data/results/runtime_log.json`.

- [ ] **T007** [US2] **Interaction‑gain permutation test (correct formulation)** – Implement in `src/pipeline/evaluate.py` the *interaction‑column* permutation test defined in FR‑002:  
  1. Compute observed ΔRMSE = RMSE_Null − RMSE_Full on each CV fold (using the best hyper‑parameters).  
  2. For 1 000 repetitions, **shuffle only the engineered interaction columns** (keeping all base predictors and the target fixed), retrain Full and Null models on the shuffled data, and recompute ΔRMSE.  
  3. Empirical p‑value = proportion of shuffled ΔRMSE ≥ observed ΔRMSE (upper‑tail).  
  *Output*: `data/results/interaction_gain_test.json` containing observed ΔRMSE, mean ΔRMSE across folds, p‑value, and a PASS/FAIL flag (α ≤ 0.05).  
  *Verification*: The JSON file exists, p‑value is in [0,1], and the test runs within ≤ 15 min on the CPU runner.

---

## Phase 3 — User Story 3: Interpretability Analysis and Driver Ranking
*Handoff: This phase consumes the best Full model and feature matrix produced in Phase 2.*

- [ ] **T008** [US3] **Conditional permutation importance per interaction with BH correction** – Extend `src/pipeline/evaluate.py` to:  
  1. For each engineered interaction column, shuffle its values 200 times, evaluate the best Full model on the validation folds, and record ΔRMSE relative to the unshuffled baseline.  
  2. Compute an empirical p‑value per column (proportion of shuffled ΔRMSE ≤ observed ΔRMSE).  
  3. Apply **Benjamini‑Hochberg** correction across all interaction columns (FR‑005, SC‑004).  
  *Output*: `data/results/bh_corrected_interaction_importance.json` containing raw p‑values, BH‑adjusted q‑values, and significance flags (α ≤ 0.05).  
  *Verification*: The file includes both raw and adjusted values; a pytest `src/tests/test_permutation_importance.py` checks that the BH procedure follows the standard algorithm.

- [ ] **T009** [US3] **SHAP interaction analysis** – Implement `src/pipeline/interpret.py` to:  
  1. Compute SHAP interaction values for the best Full model using `shap.TreeExplainer(..., interaction=True)`.  
  2. Rank all interaction features by absolute mean SHAP magnitude and write the ranking to `data/results/shap_interaction_rankings.json` (including a flag indicating “env × env” vs. “env × material”).  
  3. Generate visualisations:  
     - Summary plot `outputs/figures/shap_summary.png` (interaction terms flagged).  
     - Dependence plots for the top‑3 interactions `outputs/figures/shap_dep_<name>.png`.  
     - Partial‑dependence curves for those interactions `outputs/figures/pdp_<name>.png`.  
  *Verification*: All PNG files exist, the JSON ranking matches the figures, and the SHAP computation completes within the 6‑hour wall‑time budget (checked by `src/tests/test_shap.py`).

- [ ] **T010** [US3] **Hyper‑parameter sensitivity & feature‑set stability** – In `src/pipeline/evaluate.py`:  
  1. Sweep `max_depth ∈ {3,4,5}` (keeping the best `n_estimators` from T006).  
  2. For each depth, train a Full model on the full training data and extract the top‑5 features by absolute mean SHAP value.  
  3. Compute pairwise **Jaccard similarity** of the three top‑5 lists; require ≥ 0.8 for stability (SC‑005).  
  *Output*: `data/results/feature_stability.json` containing the three feature lists, Jaccard scores, and a PASS/FAIL flag.  
  *Verification*: The JSON file exists, all Jaccard scores ≥ 0.8, and `src/tests/test_stability.py` validates the calculation.

- [ ] **T011** [US3] **Result tables, figures & associational disclaimer** – Generate a markdown summary `data/results/summary_tables.md` that includes:  
  1. Performance table (Full vs Null vs mean‑only baseline, CV and held‑out R²/RMSE).  
  2. BH‑corrected interaction‑importance table.  
  3. Sensitivity‑stability table.  
  4. Explicit disclaimer on every figure/table caption stating that findings are **associational, not causal** (SC‑006).  
  *Verification*: Numbers in the tables match the corresponding JSON artefacts; each figure caption ends with the disclaimer (checked by `src/tests/test_summary.py`).

- [ ] **T012** [US3] **Methods & results manuscript draft & reproducibility handoff** – Write `paper/research_notes.md` and `paper/handoff.md` describing the full process and outcomes.
  *Outputs*:  
  - `paper/research_notes.md`  
  - `paper/handoff.md`  
  - `data/results/runtime_log.json` (recording total wall-time and peak RSS)  
  - `data/results/ingestion_validation_metrics.json` (final aggregated pass-rate)  
  *Verification*: Re‑run the full pipeline via the command in `quickstart.md`; all pytest suites pass; `runtime_log.json` shows ≤ 6 h wall‑time and ≤ 7 GB RSS; both markdown files exist and reference only existing artefacts.

---

### Dependency & Requirement Coverage Matrix  

| Spec Requirement | Satisfying Task(s) |
|------------------|--------------------|
| FR‑001, FR‑008, FR‑011, SC‑007 | T001, T002, T002_val |
| FR‑006 (VIF) | T003 |
| FR‑002 (interaction engineering) | T004 |
| FR‑009, FR‑010 (Group‑aware splits) | T005 |
| FR‑003 (model caps) | T006 |
| FR‑002 (Full vs Null gain) | T007 |
| FR‑005, FR‑012, SC‑004 | T008 |
| FR‑004 (SHAP) | T009 |
| FR‑007, SC‑005 (sensitivity) | T010 |
| SC‑001, SC‑002, SC‑003, SC‑006, SC‑007 | T006_baseline, T006, T007, T011, T012 |
| SC‑004 (BH correction) | T008 |
| SC‑005 (feature stability) | T010 |
| SC‑001 (baseline improvement) | T006_baseline, T006 |
| SC‑002 (interaction gain) | T007 |
| SC‑003 (runtime limits) | T006, T012 |
| Principle II (Verified Accuracy) | T000 |

---  

*All tasks are unchecked except the verified setup tasks (`T013`, `T015`).  Once the pending tasks are implemented and their verification steps pass, the project will satisfy the full specification and be ready for the downstream paper pipeline.*