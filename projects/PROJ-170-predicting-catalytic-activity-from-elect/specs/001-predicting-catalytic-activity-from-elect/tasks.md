# Tasks: Predicting Catalytic Activity from Electronic Structure and Reaction Path Features

**Inputs**: `specs/001-predicting-catalytic-activity/spec.md`, `plan.md`, `research.md`, all contracts in `specs/001-predicting-catalytic-activity/contracts/`, and any existing verified artifacts.

The checklist implements the full end‑to‑end study while respecting the functional requirements (FR‑001 – FR‑010), success criteria (SC‑001 – SC‑007), and reviewer notes. Tasks are ordered to respect data flow; each task lists its concrete output paths and the verification steps that must succeed for the task to be considered complete.

---

- [X] T000 **Skeleton Setup** `code/setup_skeleton.py`  
  - Creates the required directory hierarchy: `data/raw/`, `data/processed/`, `outputs/`.  
  - **Verification**: all three directories exist and are writable; a tiny `README.txt` is written in each confirming creation.

- [ ] T001 **Download OC20 & Materials Project descriptors** `code/download_data.py` <!-- FAILED-IN-EXECUTION: code/download_data.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/download_data.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/download_data.py exit=1 -->
  - Streams the OC20 dataset via `datasets.load_dataset(..., streaming=True)` and writes a stratified sample to `data/raw/oc20_sample.parquet`.  
  - Retrieves bulk electronic descriptors from the Materials Project API (`mp-api`) and caches them as `data/raw/mp_descriptors.json`.  
  - Generates `data/raw/required_columns.json` describing the mandatory columns for the unified DataFrame.  
  - **Verification**: the three files exist, are non‑empty, and their SHA‑256 checksums are recorded in `data/checksums.txt`. The checksum entry for `required_columns.json` is also present.

- [ ] T014 **Acquire open experimental TOF dataset** `code/acquire_tof.py` *(Pending/Deferred)*  
  - Attempts to locate a publicly available 2025 CO₂ hydrogenation TOF dataset (e.g., via DOI resolution or open data repository).  
  - If found, downloads the CSV to `data/raw/experimental_tof.csv` and updates `data/checksums.txt`.  
  - If not found, **invokes task T015** to submit a formal scope‑revision request and then raises an exception that halts further downstream steps until the dataset is provided.  
  - **Verification**: either `experimental_tof.csv` exists with a valid checksum **or** task T015 has been executed and logged.

- [ ] T015 **Submit scope‑revision request for experimental TOF dataset** `code/request_scope_revision.py` *(New task)*  
  - Generates a JSON request `outputs/scope_revision_request.json` describing the missing open experimental TOF dataset, the impact on FR‑001, and a proposed mitigation (e.g., provision of a public dataset by the sponsor).  
  - Sends this request to the project governance channel (simulated by writing the file).  
  - **Verification**: the JSON file exists, contains the fields `request_id`, `missing_dataset`, `impact`, and `proposed_action`, and its SHA‑256 checksum is recorded in `data/checksums.txt`.

- [ ] T002 **Extract DFT‑derived descriptors** `code/extract_descriptors.py`  
  - Reads `data/raw/oc20_sample.parquet`, computes the required numeric descriptors (`d_band_center`, `p_band_center`, `bader_charges`, `activation_barrier`, `reaction_energy`, `coordination_number`, `surface_area`) using `pymatgen`/`numpy`.  
  - Writes the per‑entry descriptor table to `data/processed/oc20_descriptors.parquet`.  
  - **Verification**: the parquet file contains all seven descriptor columns, no row contains `NaN` in any descriptor, and the row count > 0.

- [ ] T003 **Align descriptors with experimental TOFs** `code/preprocess_alignment.py` *(Deferred until TOF dataset is available)*  
  - Performs exact string matching on `composition`, `surface_facet`, `synthesis_condition`, **and** `temperature`/`pressure` (when present) between `data/processed/oc20_descriptors.parquet` and `data/raw/experimental_tof.csv`.  
  - Generates a unified DataFrame and writes it to `data/processed/unified_dataset.parquet`.  
  - Computes `alignment_rate = matched_entries / total_experimental_entries` and writes `outputs/alignment_metrics.json` (must contain the field `alignment_rate`).  
  - **Verification**: `alignment_rate` ≥ 0.80, unified dataset has ≥ 500 rows (or ≥ 1500 if source data permit), and the JSON is well‑formed.

- [ ] T004 **k‑NN imputation and exclusion flagging** `code/impute_and_flag.py` *(Deferred until alignment is complete)*  
  - Builds a stoichiometry‑based feature space (normalized element counts) from the unified dataset.  
  - Applies k‑nearest‑neighbors (k = 5) imputation to any missing descriptor values (target `experimental_tof` is never used for distance).  
  - Sets `is_imputed = true` for rows where any descriptor was filled, and `excluded_from_training = true` for rows with < 5 neighbors or alignment failures.  
  - Writes the intermediate result to `data/processed/imputed_dataset.parquet`.  
  - **Verification**: after imputation, all required descriptor columns contain no `NaN`; `is_imputed` and `excluded_from_training` columns are present and correctly populated.

- [ ] T005 **Feature scaling and final aligned CSV** `code/scale_and_export.py` *(Deferred until imputation is complete)*  
  - Loads `data/processed/imputed_dataset.parquet`, applies `StandardScaler` to all numeric features (including the placeholder `experimental_tof` if present).  
  - Writes scaling diagnostics (`mean_abs` and `std_abs` per feature) to `outputs/scaling_report.json`; each feature must satisfy |μ| < 0.01 and |σ − 1| < 0.01.  
  - Exports the fully processed table to `data/processed/aligned_dataset.csv`, which must validate against `specs/001-predicting-catalytic-activity/contracts/aligned_dataset.schema.yaml`.  
  - **Verification**: JSON scaling report meets thresholds; CSV passes JSON‑Schema validation (`jsonschema.validate`).  

- [ ] T006 **Create outer hold‑out split** `code/create_split.py` *(Deferred; split fraction TBD per FR‑010)*  
  - Once `aligned_dataset.csv` is available, splits it into training and test sets **before any hyper‑parameter tuning**.  
  - The exact hold‑out proportion will be defined after FR‑010 is resolved; for now the task records the intent and writes a placeholder `outputs/split_info.json` with a status field `"split_defined": false`.  
  - When the fraction is decided, the script will stratify by `composition` family, write `data/processed/train_set.csv`, `data/processed/test_set.csv`, and update `split_info.json` with concrete sizes and random seed.  
  - **Verification**: after execution, `split_info.json` contains either a concrete split (≥ 100 test rows) **or** a clear “pending” status; when concrete, the train/test sets have disjoint `catalyst_id`s.

- [ ] T007 **XGBoost hyper‑parameter search & model saving** `code/train_xgboost.py` *(Deferred until training data with TOF are available)*  
  - Performs a 5‑fold CV grid search on the training set (`max_depth ∈ {3,5,7}`, `learning_rate ∈ {0.01,0.1}`, `n_estimators ≤ 200`).  
  - Selects the hyper‑parameter set maximizing cross‑validated R²; ties broken by smallest `n_estimators`.  
  - Saves the chosen configuration to `outputs/best_params.json` and the trained model to `code/models/best_xgboost.json`.  
  - **Verification**: `best_params.json` contains `max_depth`, `learning_rate`, `n_estimators`; model file exists and can be loaded with `xgboost.Booster`.

- [ ] T008 **Linear baseline training** `code/train_linear.py` *(Deferred until training data with TOF are available)*  
  - Fits an ordinary least‑squares regression using only `d_band_center` and `activation_barrier` on the same training set.  
  - Saves the baseline model to `code/models/baseline_linear.json`.  
  - **Verification**: model file exists, coefficients are non‑null, and the model can predict on the test set without error.

- [ ] T009 **Model evaluation & statistical significance testing** `code/evaluate_models.py` *(Deferred until predictions exist)*  
  - Generates predictions for both XGBoost and linear baseline on `data/processed/test_set.csv`.  
  - Computes R², MAE (log‑TOF scale), and Pearson R for each model; writes all metrics to `outputs/metrics.json` conforming to `contracts/metrics.schema.yaml`.  
  - Performs Shapiro‑Wilk test on the absolute‑error differences; based on the p‑value selects either a paired t‑test or Wilcoxon signed‑rank test, records the test type, p‑value, and a `significant` flag (true only if p < 0.05 **and** ΔMAE ≥ 0.1) in `outputs/statistical_test.json`.  
  - **Verification**: `metrics.json` validates against its schema, `statistical_test.json` contains the required fields, and the `significant` flag matches FR‑008 logic.

- [ ] T010 **SHAP importance calculation & visualization** `code/compute_shap.py` *(Deferred until XGBoost model is trained)*  
  - Loads `code/models/best_xgboost.json` and the test set, computes SHAP values with `shap.TreeExplainer`.  
  - Ranks descriptors by mean absolute SHAP impact, writes `outputs/shap_rankings.csv` (validated against `contracts/feature_importance.schema.yaml`), and generates a bar plot `outputs/shap_barplot.png` showing the top 5 descriptors.  
  - **Verification**: CSV passes schema validation, plot file exists, and the top‑5 list is non‑empty.

- [ ] T011 **Reduced‑model verification (SC‑003)** `code/train_reduced.py` *(Deferred until SHAP rankings are available)*  
  - Trains a new XGBoost model using only the top‑5 descriptors identified in T010, with the same grid‑search limits.  
  - Evaluates on the test set, computes R², and writes `outputs/reduced_model_metrics.json` containing `r_squared_full`, `r_squared_reduced`, `ratio`, and `SC-003_status` (PASS if `ratio ≥ 0.50`).  
  - **Verification**: `ratio` ≥ 0.50 and `SC-003_status` = "PASS".

- [ ] T012 **Generate final report** `code/report.py` *(Deferred until all upstream results are ready)*  
  - Collates alignment metrics, model performance, statistical‑test outcome, SHAP rankings, reduced‑model ratio, and compares the top‑5 descriptors against the Nørskov reference list (`data/norskov_descriptors.json`).  
  - Writes a human‑readable markdown report to `outputs/final_report.md` and a machine‑readable companion `outputs/final_report.json` validated against `contracts/report_schema.json.schema.yaml`.  
  - **Verification**: both files exist, schema validation succeeds, and every numeric entry can be traced back to its source artifact (e.g., `metrics.json`, `statistical_test.json`).

- [ ] T013 **Document reproducible workflow & integration test** `quickstart.md` & `tests/integration/test_full_pipeline.py`  
  - `quickstart.md` lists the exact command sequence, now including the new skeleton and acquisition steps:  
    ```bash
    python -m code.setup_skeleton
    python -m code.download_data
    python -m code.acquire_tof          # may pause pending dataset
    python -m code.request_scope_revision  # manual trigger if acquire fails
    python -m code.extract_descriptors
    python -m code.preprocess_alignment
    python -m code.impute_and_flag
    python -m code.scale_and_export
    python -m code.create_split
    python -m code.train_xgboost
    python -m code.train_linear
    python -m code.evaluate_models
    python -m code.compute_shap
    python -m code.train_reduced
    python -m code.report
    ```  
  - The integration test now conditionally checks for the presence of deferred artifacts; it passes if the pipeline runs up to the point where a missing TOF dataset is reported, and it validates all generated artifacts that do exist.  
  - **Verification**: `pytest -q tests/integration/test_full_pipeline.py` passes on a clean environment, and `outputs/metrics.json.total_seconds` (when present) is ≤ 21600 s.

---  

**Dependency Mapping**

| FR | Covered by Task(s) |
|----|--------------------|
| FR‑001 | T001, T014, T015 |
| FR‑002 | T003 |
| FR‑003 | T004, T005 |
| FR‑004 | T007 |
| FR‑005 | T008, T009 |
| FR‑006 | T010 |
| FR‑007 | T012 |
| FR‑008 | T009 (significance logic) |
| FR‑009 | T003 (exact temperature/pressure matching) |
| FR‑010 | T006 (deferred until FR‑010 is defined) |
| FR‑011 | T005 (schema compliance) |

All tasks are unchecked (`[ ]`) pending implementation; completed work from previous iterations that already satisfies any of the above requirements should be re‑checked after the corresponding task passes its verification steps.  