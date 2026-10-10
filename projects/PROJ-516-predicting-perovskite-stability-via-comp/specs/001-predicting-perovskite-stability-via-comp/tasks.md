# Tasks: Predicting Perovskite Stability via Compositional Fingerprints  

**Inputs**: `spec.md`, `plan.md`, existing research artifacts, and reviewer feedback (instrument‑precision, metadata provenance, and missing artifact concerns).  

The goal is to deliver a fully reproducible end‑to‑end pipeline that:

1. **Acquires real experimental data** from Materials Project and NREL (no synthetic stand‑ins).  
2. **Computes compositional descriptors** and rigorously handles missing values, collinearity (VIF), and measurement uncertainty.  
3. **Trains three baseline regressors** under strict CPU‑only constraints, with stratified k‑fold CV and uncertainty weighting.  
4. **Performs interpretability** (SHAP) and **external out‑of‑distribution validation** on a literature dataset.  
5. **Documents every step** (instrumentation audit, uncertainty propagation, feature‑importance significance) for a clean hand‑off to the paper stage.  

All tasks follow the canonical `- [ ] T### [USx?] description …` format, list exact artifact paths, and include indented verification steps.

---

## Phase 1 – Project scaffolding & reproducibility foundation  

- [X] T001 [US0] Create core directories `code/`, `data/raw/`, `data/processed/`, `tests/`, `docs/`, `state/`.  
  - **Verification**: `tree -L 2` lists the directories; CI asserts they exist before any later task runs.  

- [ ] T002 [US0] Create `code/requirements.txt` with pinned versions:  
  ```text
  pandas==2.2.2
  numpy==1.26.4
  scikit-learn==1.5.0
  shap==0.45.1
  pymatgen==2024.5.1
  mp-api==0.38.5
  requests==2.32.3
  pyyaml==6.0.2
  ```  
  - **Verification**: `pip install -r code/requirements.txt` succeeds in a fresh venv.  

- [ ] T003 [US0] Add minimal `README.md` and `docs/quickstart.md` stub (to be expanded later).  
  - **Verification**: Both files exist and contain at least one non‑comment line; CI checks for required sections (`Project overview`, `Installation`, `Running the pipeline`).  

- [ ] T038 [US0] Implement **state manager** (`code/state_manager.py`) with `compute_hash(path)` and `update_state(path)` utilities.  
  - **Verification**: Running `python -m code.state_manager data/raw/dummy.csv` creates/updates `state/project_state.yaml` with correct SHA‑256 hash and ISO‑8601 timestamp.  

- [ ] T039 [US0] Initialise `state/project_state.yaml` (empty YAML with top‑level `artifacts: {}` and `updated_at:` timestamp).  
  - **Verification**: File exists, is valid YAML, and is updated by `state_manager.update_state`.  

- [ ] T005 [US0] Add deterministic seed module (`code/seed.py`) containing `SEED = 42`. All other scripts import this constant.  
  - **Verification**: `code/seed.py` exists, contains the line `SEED = 42`, and a CI test imports it from three pipeline modules to confirm consistency.  

- [ ] T006 [US0] Enforce immutability of raw data (`code/data_hygiene.py`). After a successful download, the script sets read‑only permissions (`chmod 444`) on every file under `data/raw/`. Attempts to modify any raw file raise `PermissionError`.  
  - **Verification**: CI test tries to append a line to `data/raw/nrel_perovskites.csv` and expects a `PermissionError`.  

---

## Phase 2 – Data acquisition, cleaning, and provenance  

- [ ] T007 [US1] Fetch NREL perovskite data (`code/data_ingestion.py::fetch_nrel`).  
  - **Endpoint**: Zenodo DOI `10.5281/zenodo.10972088` → raw CSV URL `[UNRESOLVED-CLAIM: https://zenodo.org/records/10972088/files/nrel_perovskite_data.csv` — HTTP 404].  
  - **Behaviour**: Uses `code/utils/data_fetcher.py` with exponential‑backoff retry (delays 1 s, 2 s, 4 s).  
  - **Output**: `data/raw/nrel_perovskites.csv`.  
  - **Verification**: File exists, row count ≥ 200, all rows have non‑null `T_d`, **and** column `measurement_origin` equals `"experimental"` for every row.  

- [ ] T008 [US1] Fetch Materials Project data (`code/data_ingestion.py::fetch_mp`).  
  - **Method**: Uses `mp-api` with `MP_API_KEY`. Queries `structure_type="perovskite"` and extracts `expt_decomp_temp`.  
  - **Post‑filter**: Keep only entries with a non‑null experimental decomposition temperature and `measurement_origin == "experimental"`.  
  - **Output**: `data/raw/mp_perovskites.csv`.  
  - **Verification**: File exists, ≥ 200 rows, all `T_d` non‑null and `measurement_origin` == `"experimental"`.  

- [ ] T009 [US1] Merge & deduplicate raw datasets (`code/data_ingestion.py::merge_raw`).  
  - **Logic**: Concatenates the two CSVs; retains both rows when the same `formula` appears in both sources, distinguished by the `source` column.  
  - **Deduplication**: Drops exact duplicates on (`formula`, `source`).  
  - **Output**: `data/raw/perovskites_merged.csv`.  
  - **Verification**: Row count equals sum of source rows minus duplicate count; `logs/merge.log` records duplicate statistics.  

- [ ] T010 [US1] Verify required predictor & outcome columns (`code/utils/column_verifier.py`).  
  - Checks that `data/raw/perovskites_merged.csv` contains every column required by the spec (e.g., `formula`, `T_d`, `T_d_uncertainty`, `instrument_model`, `manufacturer`, `measurement_origin`).  
  - **Output**: `data/processed/variable_presence_report.csv`.  
  - **Verification**: Report shows all required columns present; CI fails if any are missing.  

- [ ] T011 [US1] Create instrumentation registry (`data/raw/instrument_registry.csv`).  
  - **Columns**: `instrument_model,manufacturer,precision_celsius`.  
  - **Sample rows**:  
    ```csv
    instrument_model,manufacturer,precision_celsius
    TA Instruments Q500,TA Instruments,2.0
    Mettler Toledo TGA/DSC 1,MT,1.5
    ```  
  - **Verification**: File exists, checksum recorded by `state_manager.update_state`.  

- [ ] T040 [US1] Generate `metadata.json` (`code/utils/metadata_parser.py`).  
  - For each entry in `perovskites_merged.csv`:  
    1. Look up `instrument_model` in `instrument_registry.csv`.  
    2. If found → `precision_source="registry"` and `precision` set to the registry value.  
    3. If missing → log to `data/raw/instrumentation_fallbacks.log`, set `precision_source="default"` and `precision=10.0` °C.  
  - **Output**: `data/raw/metadata.json` (list of objects with `formula`, `instrument_model`, `manufacturer`, `precision`, `precision_source`, `source`).  
  - **Verification**: JSON validates against `contracts/metadata.schema.yaml`; fallback log contains at least one entry.  

- [ ] T012 [US1] Compute total uncertainty (`code/utils/uncertainty_calculator.py`). *(new implementation)*  
  - Reads `data/raw/perovskites_merged.csv` and `data/raw/metadata.json`.  
  - Applies `sigma = sqrt(precision^2 + experimental_error^2)`, where `experimental_error` is taken from column `T_d_uncertainty` if present, otherwise `0`.  
  - Writes:  
    - `data/processed/descriptors_uncertainty.csv` (original columns + `total_uncertainty`).  
    - `data/processed/exclusion_log.csv` listing any rows with `total_uncertainty ≤ 0` (should be empty).  
  - **Verification**: All `total_uncertainty` values > 0; exclusion log is empty; CI loads the CSV and asserts the column exists and contains only positive numbers.  

---

## Phase 3 – Feature engineering and data hygiene  

- [ ] T014 [US1] Compute compositional descriptors (`code/feature_engineering.py`).  
  - Uses `pymatgen` to parse each formula, assign A/B/X sites, and retrieve elemental properties: ionic radius (coordination 6), electronegativity (Pauling), formation enthalpy, first ionization energy.  
  - Calculates atomic fractions (A, B, X), weighted averages, and variances across sites.  
  - **Output**: `data/processed/descriptors_features.csv` containing all descriptor columns listed in the spec **except** VIF‑related columns.  
  - **Verification**: Spot‑check on `FAPbI3` against `tests/reference_descriptors/FAPbI3.json`; CI loads the CSV and asserts required columns are present and contain no NaNs.  

- [ ] T015 [US1] Merge uncertainty and descriptor files (`code/feature_engineering.py::merge_uncertainty`).  
  - Joins `descriptors_uncertainty.csv` and `descriptors_features.csv` on `formula` + `source`.  
  - **Output**: `data/processed/descriptors_v1.csv`.  
  - **Verification**: Row count unchanged; all descriptor columns plus `total_uncertainty` present.  

- [ ] T016 [US1] Compute VIF diagnostics (`code/utils/vif_calculator.py`).  
  - Loads `descriptors_v1.csv`, fits a linear model for each descriptor against all others, obtains VIF via `statsmodels.stats.outliers_influence.variance_inflation_factor`.  
  - Writes `data/processed/vif_report.csv` with columns `descriptor`, `vif_value`, `flagged` (`True` if `vif_value>5`).  
  - **Verification**: At least one descriptor flagged (e.g., collinearity between `atomic_fraction_A` and `atomic_fraction_B`).  

- [ ] T041 [US1] Add per‑row `vif_score` column (`code/utils/vif_score_adder.py`).  
  - Computes a row‑wise VIF score (e.g., the maximum VIF among retained descriptors for that row) and appends it as `vif_score`.  
  - **Output**: `data/processed/descriptors_vif_scored.csv`.  
  - **Verification**: Column `vif_score` exists, numeric, and ≥ 1 for all rows.  

- [ ] T017 [US1] Filter high‑VIF descriptors (`code/utils/vif_filter.py`).  
  - Removes any descriptor where `flagged=True` from the feature matrix **but retains the `vif_score` column**.  
  - **Output**: `data/processed/descriptors_vif_filtered.csv`.  
  - **Verification**: Column list equals that of `descriptors_v1.csv` minus flagged descriptors; `vif_score` column still present.  

- [ ] T018 [US1] Exclude low‑quality entries (`code/data_cleaning.py`).  
  - Drops rows with **≥ 2** missing descriptor values after VIF filtering.  
  - Sets the required boolean `is_excluded` column (`True` for dropped rows, `False` otherwise).  
  - Logs counts to `data/processed/exclusion_log.csv`.  
  - **Output**: `data/processed/descriptors_final.csv`.  
  - **Verification**: Remaining rows have ≤ 1 missing value, `is_excluded` column exists, and total rows ≥ 200.  

- [ ] T019 [US1] Derive perovskite family (`code/feature_engineering.py::add_family`).  
  - Uses element composition to assign `family` ∈ {lead‑halide, tin‑halide, double, other} per data‑model rules.  
  - Overwrites `descriptors_final.csv` with the added `family` column.  
  - **Verification**: Frequency table printed in the log shows all three families present; CI asserts column exists and contains only allowed enum values.  

- [ ] T020 [US1] Create sample‑weight column (`code/model_training.py::add_weights`).  
  - Enforces a **minimum uncertainty of 1 °C**: `effective_uncertainty = max(total_uncertainty, 1.0)`.  
  - Weight = 1 / (`effective_uncertainty`²).  
  - Column added to `descriptors_final.csv`.  
  - **Verification**: All weights are positive; summary statistics logged; CI checks that `weight` column exists and has no nulls.  

- [ ] T021 [US1] Check minimum family representation (`code/data_cleaning.py::family_coverage_check`).  
  - Confirms each `family` has at least 5 samples in `descriptors_final.csv`.  
  - Logs warning if a family falls below the threshold but does not abort.  
  - **Verification**: `logs/family_coverage_report.log` lists counts; CI fails only if any family has zero samples.  

- [ ] T042 [US1] Schema compliance verification (`code/utils/schema_validator.py`).  
  - Validates `descriptors_final.csv` against `contracts/descriptor.schema.yaml`.  
  - **Output**: `data/processed/schema_validation_report.json`.  
  - **Verification**: CI fails if any row violates the schema.  

---

## Phase 5 – Modeling (User Story 2, P2)  

- [ ] T022 [US2] Stratified 5‑fold CV split (`code/model_training.py::stratified_cv`).  
  - Uses `StratifiedKFold` on the `family` column.  
  - **Pre‑flight check**: If a fold lacks a family, logs a **warning** (does not raise).  
  - **Verification**: Test run prints fold composition; warnings captured in `logs/cv_warnings.log`.  

- [ ] T023 [US2] Train baseline regressors with limited grid search (`code/model_training.py`).  
  - **Random Forest**: `n_estimators` ∈ {100, 200}, `max_depth` ∈ {5, 10, None}.  
  - **Gradient Boosting**: `n_estimators` ∈ {100, 200}, `learning_rate` ∈ {0.05, 0.1}, `max_depth` ∈ {3, 5}.  
  - **Elastic Net**: `alpha` ∈ {0.01, 0.1, 1.0}, `l1_ratio` ∈ {0.5, 0.8}.  
  - **Constraint**: ≤ 10 hyper‑parameter combos per model (enforced by `GridSearchCV` with `max_iter=10`).  
  - Records mean ± std of **R²**, **RMSE**, **MAE** across folds.  
  - **Outputs**: `data/processed/model_runs.json` (list of dicts with `model_type`, `best_params`, `cv_metrics`).  
  - **Verification**: JSON contains exactly three entries; each `hyperparams` dict ≤ 10 keys; total runtime ≤ 4 h on the CI runner (checked via `code/main.py` timer).  

- [ ] T024 [US2] Select best model & retrain on full data (`code/model_training.py::retrain_best`).  
  - Chooses the model with highest mean CV R².  
  - Retrains on the entire `descriptors_final.csv` using the same sample weights.  
  - Saves the fitted estimator to `models/best_model.pkl`.  
  - **Verification**: Pickle loads without error; stored hyper‑parameters match the best CV run; CI runs a quick inference on a single row to confirm predictability.  

---

## Phase 6 – Interpretability & external validation (User Story 3, P3)  

- [ ] T025 [US3] Compute SHAP values (`code/validation.py::shap_analysis`).  
  - Uses `shap.TreeExplainer` for tree‑based models or `shap.LinearExplainer` for Elastic Net.  
  - Generates per‑feature mean absolute SHAP values.  
  - **Output**: `data/processed/shap_values.csv` (columns `feature`, `mean_abs_shap`).  
  - **Verification**: File exists, loads in pandas, and top‑5 features match the reference list in `tests/reference_shap/top5.json`.  

- [ ] T026 [US3] Permutation importance with 1 000 permutations (`code/validation.py::perm_importance`).  
  - Applies `sklearn.inspection.permutation_importance` with `n_repeats=1000`.  
  - **Output**: `data/processed/feature_importance_raw.csv` (columns `feature`, `raw_p`, `importance_score`).  
  - **Verification**: All `raw_p` values in [0, 1]; at least one feature has `raw_p < 0.05`.  

- [ ] T027 [US3] Multiple‑testing correction (`code/validation.py::adjust_pvalues`).  
  - Implements Benjamini‑Hochberg FDR control (α = 0.05).  
  - Writes `data/processed/feature_importance.csv` with columns `feature`, `raw_p`, `adj_p`, `importance_score`, `significant` (`True` if `adj_p < 0.05`).  
  - **Verification**: Adjusted p‑values are monotonic; CI checks that at least one feature is flagged `significant=True`.  

- [ ] T028 [US3] Fetch external literature validation dataset (`code/data_sources/literature_fetcher.py`).  
  - Downloads Zenodo DOI `10.5281/zenodo.10972088` file `literature_perovskite_stability.csv`.  
  - Validates that the set contains at least one element not present in the training set (e.g., Sn or a double‑perovskite element).  
  - **Output**: `data/raw/literature_validation.csv` (columns `formula`, `T_d`, `source="Literature"`).  
  - **Verification**: OOD check passes; log `data/raw/literature_ood_check.log` records the novel elements.  

- [ ] T029 [US3] External validation of best model (`code/validation.py::external_eval`).  
  - Loads `models/best_model.pkl` and predicts on `literature_validation.csv`.  
  - Computes **R²** and **RMSE** for the external set.  
  - **Output**: `data/processed/external_metrics.csv` (columns `R2`, `RMSE`).  
  - **Verification**: File exists; R² and RMSE are numeric; CI parses them without error.  

- [ ] T030 [US3] Generalizability gap report (`code/validation.py::gap_report`).  
  - Reads CV mean R² from `model_runs.json` (best model) and external R² from `external_metrics.csv`.  
  - Writes `data/processed/generalizability_gap.csv` with rows `in_dist_R2`, `out_dist_R2`, `gap = in_dist_R2 - out_dist_R2`.  
  - **Verification**: Gap value is non‑negative; file loads cleanly.  

- [ ] T031 [US3] Generate full validation report (`docs/validation_report.md`).  
  - Sections:  
    1. Instrumentation audit (table from `instrument_registry.csv` + fallback stats).  
    2. Data quality assessment (high‑ vs. low‑confidence counts from `metadata.json`).  
    3. Model performance (CV metrics, best‑model hyper‑parameters).  
    4. Feature importance (SHAP ranking, permutation significance, BH‑adjusted p‑values).  
    5. External validation & generalizability gap (R², RMSE, gap).  
    6. Uncertainty propagation (formula, distribution of `total_uncertainty`, impact of weighting).  
  - **Verification**: All tables cross‑referenced to CSV artifacts; CI parses the markdown to ensure required headings are present.  

---

## Phase 7 – Final hand‑off & reproducibility checks  

- [ ] T033 [US0] Implement pipeline driver (`code/main.py`).  
  - Calls tasks in strict order, checks hashes via `state_manager` before each major step, aborts with `DataIntegrityError` on mismatch.  
  - Logs elapsed time per phase; writes `data/processed/runtime_report.json` with `total_seconds` and `budget_status` (`PASS`/`WARN`/`FAIL`).  
  - Enforces the hard runtime limit of 6 h (soft target 4 h).  
  - **Verification**: Simulated slowdown (sleep) exceeding 6 h triggers graceful failure with appropriate error code; normal run completes within budget.  

- [ ] T032 [US0] Update `docs/quickstart.md` with a single reproducible command:  
  ```bash
  python -m code.main run_all
  ```  
  and description of required environment variables (`MP_API_KEY`, optional `NREL_API_KEY`).  
  - **Verification**: Running the command on a fresh runner executes the full pipeline without manual intervention and ends with “SUCCESS”.  

- [ ] T034 [US0] Data lineage reporting (`code/data_hygiene.py::lineage_report`).  
  - For each processed artifact, creates a sibling `.lineage.json` containing input hashes, current git commit SHA, and timestamp.  
  - **Verification**: Sample lineage file exists for `descriptors_final.csv` and hashes match entries in `state/project_state.yaml`.  

- [ ] T035 [US0] Citation title‑token‑overlap validation (`code/citation_validator.py`).  
  - For every citation in `spec.md` and `plan.md`, retrieves the referenced document (via DOI or URL) and computes token overlap between citation title and document title.  
  - Generates `data/processed/citation_validation_report.json` indicating pass/fail per citation (threshold ≥ 0.7).  
  - **Verification**: CI fails if any citation reports overlap < 0.7.  

- [ ] T036 [US0] Finalize repository state: commit all generated artifacts, ensure `state/project_state.yaml` is up‑to‑date, and tag the commit as `v0.1.0-pipeline`.  
  - **Verification**: `git show` displays the tag; CI checks that the tag points to a commit where all verification tests pass.  

- [ ] T037 [US0] SC‑006 Variable‑presence verification (`code/utils/sc006_verifier.py`).  
  - Confirms that every predictor (all descriptor columns) and the outcome variable `T_d` exist in the source raw files (`nrel_perovskites.csv`, `mp_perovskites.csv`).  
  - Produces `data/processed/sc006_report.csv` summarising presence/absence.  
  - **Verification**: CI fails if any required column is missing; otherwise logs a success message.  
