# Tasks: Predicting Perovskite Stability via Compositional Fingerprints  

**Inputs**: `spec.md`, `plan.md`, existing research artifacts, and reviewer feedback (especially the instrumentation‑uncertainty concerns).  

The goal is to deliver a fully reproducible end‑to‑end pipeline that:

1. **Acquires real experimental data** from Materials Project and NREL (no synthetic stand‑ins).  
2. **Computes compositional descriptors** and rigorously handles missing values, collinearity (VIF), and measurement uncertainty.  
3. **Trains three baseline regressors** under strict CPU‑only constraints, with stratified k‑fold CV and uncertainty weighting.  
4. **Performs interpretability** (SHAP) and **external out‑of‑distribution validation** on a literature dataset.  
5. **Documents every step** (instrumentation audit, uncertainty propagation, feature‑importance significance) for a clean hand‑off to the paper stage.  

All tasks follow the canonical `- [ ] T### [P?] [USx?] description …` format, list exact artifact paths, and include indented verification steps.

---

## Phase 1 – Project scaffolding & reproducible state tracking  

- [ ] T001a [P] Create core directories `code/`, `data/raw/`, `data/processed/`, `tests/`, `docs/`, `state/`.  
  - **Verification**: `tree` shows the directories; `git status` reports them as untracked (intended).  

- [ ] T001b [P] Create `code/requirements.txt` with pinned versions:  
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

- [ ] T001c [P] Add a minimal `README.md` and `quickstart.md` stub (to be filled later).  
  - **Verification**: `README.md` and `quickstart.md` exist and each contains at least one non‑comment line; CI parses them to confirm required sections (`Project overview`, `Installation`, `Running the pipeline`).  

- [ ] T001d [P] Implement **state manager** (`code/state_manager.py`) and initialise `state/project_state.yaml`.  
  1. Provides `compute_hash(path)` returning SHA‑256.  
  2. Provides `update_state(path)` that writes/updates the YAML with `artifacts.{relative_path}.hash` and ISO‑8601 `timestamp`.  
  - **Verification**: Running `python -m code.state_manager data/raw/dummy.csv` creates an entry in `state/project_state.yaml` with a correct hash.  

- [ ] T002 [US0] Implement **state manager** (`code/state_manager.py`) that:  
  1. Computes SHA‑256 hashes for any file path passed.  
  2. Writes/updates `state/project_state.yaml` with keys `artifacts.{relative_path}.hash` and ISO‑8601 `timestamp`.  
  3. Creates the YAML file if missing.  
  - **Verification**: Run `python -m code.state_manager data/raw/dummy.csv`; `state/project_state.yaml` contains a correct hash entry for `data/raw/dummy.csv`.  

---

## Phase 2 – Data acquisition, cleaning, and descriptor generation (User Story 1, P1)  

- [ ] T003 [US1] **Fetch NREL perovskite data** (`code/data_ingestion.py::fetch_nrel`).  
  - **Endpoint**: Zenodo DOI `10.5281/zenodo.10972088` → raw CSV URL `[UNRESOLVED-CLAIM: https://zenodo.org/records/10972088/files/nrel_perovskite_data.csv` — HTTP 404].  
  - **Behaviour**: Uses `code/utils/data_fetcher.py` with exponential‑backoff retry (delays 1 s, 2 s, 4 s).  
  - **Output**: `data/raw/nrel_perovskites.csv` containing at least columns `formula`, `T_d`, `instrument_model`, `manufacturer`.  
  - **Post‑filter**: Retain only rows where `T_d` is non‑null **and** flagged as experimentally measured (`measurement_type == "experimental"` if present).  
  - **Verification**: File exists, row count ≥ 200, all retained rows have non‑null experimental `T_d`, schema validation against `contracts/metadata.schema.yaml` passes.  

- [ ] T004 [US1] **Fetch Materials Project data** (`code/data_ingestion.py::fetch_mp`).  
  - **Method**: Uses `mp-api` with the environment variable `MP_API_KEY`. Queries `structure_type="perovskite"` and extracts `expt_decomp_temp` (preferred) or `decomp_temp`.  
  - **Post‑filter**: Keep only entries with a non‑null experimental decomposition temperature (`expt_decomp_temp`).  
  - **Output**: `data/raw/mp_perovskites.csv` with the same column set as NREL plus `source="MaterialsProject"`.  
  - **Verification**: File exists, ≥ 200 rows, all retained rows have experimental `T_d`, passes the same schema validation.  

- [ ] T005 [US1] **Merge & deduplicate raw datasets** (`code/data_ingestion.py::merge_raw`).  
  - **Logic**: Concatenates the two CSVs; if the same `formula` appears in both sources, *both* rows are retained (source column distinguishes them).  
  - **Deduplication**: Drops exact duplicates on (`formula`, `source`).  
  - **Output**: `data/raw/perovskites_merged.csv`.  
  - **Verification**: Row count equals sum of source rows minus duplicate count; a log file `logs/merge.log` records duplicate statistics.  

- [ ] T005b [US1] **Verify required predictor & outcome columns** (`code/utils/column_verifier.py`).  
  - Checks that `data/raw/perovskites_merged.csv` contains every column required by the spec (e.g., `formula`, `T_d`, `T_d_uncertainty`, `instrument_model`, `manufacturer`, plus any additional metadata).  
  - **Output**: `data/processed/variable_presence_report.csv` listing missing/present status.  
  - **Verification**: Report shows all required columns present; CI fails if any are missing.  

- [ ] T006 [US1] **Create instrumentation registry** (`data/raw/instrument_registry.csv`).  
  - **Columns**: `instrument_model,manufacturer,precision_celsius`.  
  - **Sample rows** (real examples):  
    ```csv
    instrument_model,manufacturer,precision_celsius
    TA Instruments Q500,TA Instruments,2.0
    Mettler Toledo TGA/DSC 1,MT,1.5
    ```  
  - **Verification**: File exists, checksum recorded by `state_manager.compute_and_update_hash`.  

- [ ] T007 [US1] **Parse instrumentation metadata & produce `metadata.json`** (`code/utils/metadata_parser.py`).  
  - For each entry in `perovskites_merged.csv`:
    1. Look up `instrument_model` in `instrument_registry.csv`.  
    2. If found → `precision_source="registry"` and `precision=registry value`.  
    3. If missing → log to `data/raw/instrumentation_fallbacks.log`, set `precision_source="default"` and `precision=10.0` °C.  
  - **Output**: `data/raw/metadata.json` – a list of objects with keys: `formula`, `instrument_model`, `manufacturer`, `precision`, `precision_source`, `source`.  
  - **Verification**: JSON validates against `contracts/metadata.schema.yaml`; fallback log contains at least one entry (expected for missing models).  

- [ ] T008 [US1] **Compute total uncertainty** (`code/utils/uncertainty_calculator.py`).  
  - Reads `metadata.json` and the original `T_d` column.  
  - Applies `sigma = sqrt(precision^2 + experimental_error^2)`, where `experimental_error` is taken from a column `T_d_uncertainty` if present, otherwise `0`.  
  - Writes `data/processed/descriptors_uncertainty.csv` = `perovskites_merged.csv` + `total_uncertainty`.  
  - Logs any rows with `total_uncertainty` ≤ 0 to `data/processed/exclusion_log.csv`.  
  - **Verification**: All `total_uncertainty` values > 0; exclusion log is empty for the default dataset.  

- [ ] T009 [US1] **Compute compositional descriptors** (`code/feature_engineering.py`).  
  - Uses `pymatgen` to parse each formula, assign A/B/X sites, and retrieve elemental properties: ionic radius (coordination 6), electronegativity (Pauling), formation enthalpy, first ionization energy.  
  - Calculates: atomic fractions (A, B, X), weighted averages, variances across sites.  
  - **Output**: `data/processed/descriptors_features.csv` containing all descriptor columns listed in the spec (including `weighted_ionization_energy`, `variance_ionization_energy`).  
  - **Verification**: Spot‑check on `FAPbI3` matches hand‑calculated values; no NaNs in any descriptor column.  

- [ ] T010 [US1] **Merge uncertainty & descriptors** (`code/feature_engineering.py::merge_uncertainty`).  
  - Joins `descriptors_uncertainty.csv` and `descriptors_features.csv` on `formula` + `source`.  
  - **Output**: `data/processed/descriptors_v1.csv`.  
  - **Verification**: Row count unchanged; all descriptor columns plus `total_uncertainty` present.  

- [ ] T011 [US1] **Compute VIF diagnostics** (`code/utils/vif_calculator.py`).  
  - Loads `descriptors_v1.csv`, fits a linear model for each descriptor against all others, obtains VIF via `statsmodels.stats.outliers_influence.variance_inflation_factor`.  
  - Writes `data/processed/vif_report.csv` with columns `descriptor`, `vif_value`, `flagged` (`True` if `vif_value>5`).  
  - **Verification**: At least one descriptor flagged (e.g., `atomic_fraction_A` vs. `atomic_fraction_B` collinearity).  

- [ ] T012 [US1] **Filter high‑VIF descriptors** (`code/utils/vif_filter.py`).  
  - Removes any descriptor where `flagged=True` from the feature matrix.  
  - **Output**: `data/processed/descriptors_vif_filtered.csv`.  
  - **Verification**: The set of columns in the new CSV matches `descriptors_v1.csv` minus flagged ones; the VIF report is archived for reference.  

- [ ] T013 [US1] **Exclude low‑quality entries** (`code/data_cleaning.py`).  
  - Drops rows with **≥ 2** missing descriptor values (after VIF filtering).  
  - Logs counts to `data/processed/exclusion_log.csv`.  
  - **Output**: `data/processed/descriptors_final.csv`.  
  - **Verification**: Remaining rows have ≤ 1 missing value; total rows ≥ 200 (as required by the power analysis).  

- [ ] T014 [US1] **Derive perovskite family** (`code/feature_engineering.py::add_family`).  
  - Uses element composition to assign `family` ∈ {lead‑halide, tin‑halide, double, other} per the data‑model rules.  
  - Writes a new file `data/processed/descriptors_final.csv` (overwrites previous) with the added `family` column.  
  - **Verification**: Frequency table of `family` printed in the log shows all three families present.  

- [ ] T015 [US1] **Create sample‑weight column** (`code/model_training.py::add_weights`).  
  - Weight = 1 / (`total_uncertainty`²).  
  - If `total_uncertainty` ≤ 0 or NaN → weight = 1.0 and a warning logged.  
  - Column added to `descriptors_final.csv`.  
  - **Verification**: All weights are positive; summary statistics (mean, min, max) logged.  

- [ ] T015c [US1] **Ensure minimum family representation** (`code/data_cleaning.py::family_coverage_check`).  
  - Confirms each `family` has at least 5 samples in `descriptors_final.csv`.  
  - If a family falls below the threshold, logs a warning but does not abort.  
  - **Verification**: Log `family_coverage_report.log` lists counts; CI fails only if any family has zero samples.  

- [ ] T016 [US2] **Stratified 5‑fold CV split** (`code/model_training.py::stratified_cv`).  
  - Uses `StratifiedKFold` on the `family` column.  
  - **Pre‑flight check**: If a fold lacks a family, logs a **warning** (does not raise an error).  
  - **Verification**: Test run prints fold composition; warnings are captured in `logs/cv_warnings.log`.  

- [ ] T017 [US2] **Train baseline regressors with limited grid search** (`code/model_training.py`).  
  - **Random Forest**: `n_estimators` ∈ {100, 200}, `max_depth` ∈ {5, 10, None}.  
  - **Gradient Boosting**: `n_estimators` ∈ {100, 200}, `learning_rate` ∈ {0.05, 0.1}, `max_depth` ∈ {3, 5}.  
  - **Elastic Net**: `alpha` ∈ {0.01, 0.1, 1.0}, `l1_ratio` ∈ {0.5, 0.8}.  
  - **Constraint**: ≤ 10 hyper‑parameter combos per model (enforced by `GridSearchCV` with `max_iter=10`).  
  - Trains on each CV split, records mean ± std of **R²**, **RMSE**, **MAE**.  
  - **Outputs**: `data/processed/model_runs.json` (list of dicts with `model_type`, `best_params`, `cv_metrics`).  
  - **Verification**: JSON contains exactly three entries; each `hyperparams` dict has ≤ 10 keys; total runtime ≤ 4 h on the CI runner (checked via `code/main.py` timer).  

- [ ] T018 [US2] **Select best model & retrain on full data** (`code/model_training.py::retrain_best`).  
  - Chooses the model with highest mean CV R².  
  - Retrains on the entire `descriptors_final.csv` (using the same sample weights).  
  - Saves the fitted estimator to `models/best_model.pkl`.  
  - **Verification**: Pickle file loads without error; stored hyper‑parameters match the best CV run.  

---

## Phase 4 – Interpretability & external validation (User Story 3, P3)  

- [ ] T019 [US3] **Compute SHAP values** (`code/validation.py::shap_analysis`).  
  - Uses `shap.TreeExplainer` for tree‑based models or `shap.LinearExplainer` for Elastic Net.  
  - Generates per‑feature mean absolute SHAP values.  
  - **Output**: `data/processed/shap_values.csv` (columns `feature`, `mean_abs_shap`).  
  - **Verification**: Top‑5 features listed; file loads in pandas without error.  

- [ ] T020 [US3] **Permutation importance with 1 000 permutations** (`code/validation.py::perm_importance`).  
  - Applies `sklearn.inspection.permutation_importance` with `n_repeats=1000`.  
  **Output**: `data/processed/feature_importance_raw.csv` (raw p‑values).  
  - **Verification**: All p‑values ∈ [0, 1]; at least one feature has p < 0.05.  

- [ ] T021 [US3] **Multiple‑testing correction** (`code/validation.py::adjust_pvalues`).  
  - Implements Benjamini‑Hochberg FDR control (α = 0.05).  
  - Writes `data/processed/feature_importance.csv` with columns `feature`, `raw_p`, `adj_p`, `importance_score`.  
  - **Verification**: Adjusted p‑values are monotonically non‑decreasing; flagged significant features have `adj_p < 0.05`.  

- [ ] T022 [US3] **Fetch external literature validation dataset** (`code/data_sources/literature_fetcher.py`).  
  - Downloads Zenodo DOI `10.5281/zenodo.10972088` file `literature_perovskite_stability.csv`.  
  - Validates that the set of unique elements contains at least one not present in the training set (e.g., Sn or a double‑perovskite element).  
  - Writes `data/raw/literature_validation.csv` with columns `formula`, `T_d`, `source="Literature"`.  
  - **Verification**: OOD check passes; a log `data/raw/literature_ood_check.log` records the novel elements.  

- [ ] T023 [US3] **External validation of best model** (`code/validation.py::external_eval`).  
  - Loads `models/best_model.pkl` and predicts on `literature_validation.csv`.  
  - Computes **R²** and **RMSE** for the external set.  
  - Writes `data/processed/external_metrics.csv` (columns `R2`, `RMSE`).  
  - **Verification**: File exists; R² is reported (may be < 0.6 – still valid).  

- [ ] T024 [US3] **Generalizability gap report** (`code/validation.py::gap_report`).  
  - Reads CV mean R² from `model_runs.json` (best model) and external R² from `external_metrics.csv`.  
  - Writes `data/processed/generalizability_gap.csv` with rows `in_dist_R2`, `out_dist_R2`, `gap = in_dist_R2 - out_dist_R2`.  
  - **Verification**: Gap value is non‑negative; file loads cleanly.  

- [ ] T025 [US3] **Generate full validation report** (`docs/validation_report.md`).  
  - Sections:  
    1. **Instrumentation Audit** (table from `instrument_registry.csv` + fallback stats).  
    2. **Data Quality Assessment** (high‑ vs. low‑confidence counts from `metadata.json`).  
    3. **Model Performance** (CV metrics, best‑model hyper‑parameters).  
    4. **Feature Importance** (SHAP ranking, permutation significance, BH‑adjusted p‑values).  
    5. **External Validation & Generalizability Gap** (R², RMSE, gap).  
    6. **Uncertainty Propagation** (formula, distribution of `total_uncertainty`, impact of weighting vs. unweighted baseline).  
  - **Verification**: All tables cross‑referenced to CSV artifacts; a CI test parses the markdown to ensure required headings are present.  

---

## Phase 5 – Final hand‑off & reproducibility checks  

- [ ] T026 [US0] **Update `quickstart.md`** with a single reproducible command:  
  ```bash
  python -m code.main run_all
  ```  
  and description of required environment variables (`MP_API_KEY`, optional `NREL_API_KEY`).  
  - **Verification**: Running the command on a fresh runner executes the full pipeline without manual intervention and ends with “SUCCESS”.  

- [ ] T027 [US0] **Implement pipeline driver** (`code/main.py`).  
  - Calls tasks in strict order, checks hashes via `state_manager` before each major step, aborts with `DataIntegrityError` on mismatch.  
  - Logs elapsed time per phase; writes `data/processed/runtime_report.json` with `total_seconds` and `budget_status` (`PASS`/`WARN`/`FAIL`).  
  - Enforces the hard runtime limit of 6 h (soft target 4 h).  
  - **Verification**: Simulated slowdown (sleep) that exceeds 6 h triggers a graceful failure with the appropriate error code.  

- [ ] T027b [US0] **Pin and record global random seed** (`code/seed.py`).  
  - Defines `SEED = 42` and writes it to `code/seed.py`. All other scripts import `SEED` from this module.  
  - **Verification**: `code/seed.py` exists, contains `SEED = 42`, and a CI test imports it from at least three pipeline modules to confirm consistency.  

- [ ] T028 [US0] **Immutable raw‑data enforcement** (`code/data_hygiene.py`).  
  - Sets read‑only permissions (`chmod 444`) on all files under `data/raw/`.  
  - Attempts to modify any raw file raise `PermissionError`.  
  - **Verification**: A CI test tries to append a line to `data/raw/nrel_perovskites.csv` and expects a `PermissionError`.  

- [ ] T028b [US0] **Citation title‑token‑overlap validation** (`code/citation_validator.py`).  
  - For every citation in `spec.md` and `plan.md`, retrieves the referenced document (via DOI or URL) and computes token overlap between the citation title and the document title.  
  - Generates `data/processed/citation_validation_report.json` indicating pass/fail per citation.  
  - **Verification**: CI fails if any citation reports overlap < 0.7.  

- [ ] T029 [US0] **Data lineage reporting** (`code/data_hygiene.py::lineage_report`).  
  - For each processed artifact, creates a sibling `.lineage.json` containing:  
    ```json
    {
      "input_hashes": {"data/raw/nrel_perovskites.csv": "...", "data/raw/mp_perovskites.csv": "..."},
      "git_commit": "<current SHA>",
      "timestamp": "2026-10-09T12:34:56Z"
    }
    ```  
  - **Verification**: Sample lineage file exists for `descriptors_final.csv` and hashes match entries in `state/project_state.yaml`.  

- [ ] T030 [US0] **Finalize repository state** – commit all generated artifacts, ensure `state/project_state.yaml` is up‑to‑date, and tag the commit as `v0.1.0‑pipeline`.  
  - **Verification**: `git show` displays the tag; CI checks that the tag points to a commit where all verification tests pass.  

- [ ] T031 [US0] **SC‑006 Variable‑presence verification** (`code/utils/sc006_verifier.py`).  
  - Confirms that every predictor (all descriptor columns) and the outcome variable `T_d` exist in the source raw files (`nrel_perovskites.csv`, `mp_perovskites.csv`).  
  - Produces `data/processed/sc006_report.csv` summarising presence/absence.  
  - **Verification**: CI fails if any required column is missing; otherwise logs a success message.  

---

### Dependency‑to‑requirement mapping (summary)

| Spec / FR | Satisfying Task(s) |
|-----------|--------------------|
| FR‑001 – download & filter experimental Tₙ | T003, T004, T005 |
| FR‑002 – compute compositional descriptors | T009, T010 |
| FR‑003 – three baseline regressors | T017 |
| FR‑004 – k‑fold CV with metrics | T016, T017 |
| FR‑005 – SHAP & permutation importance | T019, T020, T021 |
| FR‑006 – external OOD validation | T022, T023 |
| FR‑007 – multiple‑testing correction | T021 |
| FR‑008 – VIF diagnostics & flagging | T011, T012 |
| Instrumentation & uncertainty (US‑1 edge cases) | T006, T007, T008, T028, T029 |
| Runtime & reproducibility constraints | T027, T027b, T030 |
| SC‑006 – variable presence check | T031, T005b |
| Constitution II – citation validation | T028b |
| Constitution I – pinned seeds | T027b |

---

**Checkpoint**: After completing **T030**, the pipeline can be launched from `quickstart.md` and will produce a fully traceable, measurement‑grounded set of results that satisfy all functional requirements, success criteria, and reviewer concerns.  