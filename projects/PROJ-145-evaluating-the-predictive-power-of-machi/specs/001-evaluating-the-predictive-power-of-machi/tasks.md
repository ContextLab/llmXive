# Tasks: Evaluating the Predictive Power of Machine Learning for Identifying Novel High‑Entropy Alloy Compositions  

**Input**: `specs/001-evaluating-the-predictive-power-of-machi/` (spec, plan, contracts, data‑model)  

**Goal**: Deliver a fully reproducible, CPU‑only pipeline that  
1. ingests a verified HEA thermodynamic dataset,  
2. creates disjoint **Training**, **Hold‑out Known**, and **True Novel** splits,  
3. computes compositional descriptors,  
4. trains Random Forest and Gradient Boosting regressors,  
5. evaluates extrapolation error and uncertainty calibration, and  
6. assembles a final report (including optional DFT validation).  

All tasks are expressed as Markdown check‑boxes following the canonical format  
`- [ ] T### [P?] [USx?] description … with exact artifact paths`.  
Checked boxes (`[X]`) indicate completed work that already satisfies the
specification; unchecked boxes (`[ ]`) are pending.

---  

## Phase 0 – Project Skeleton  

- [X] T001 **Project Initialization** – Create root directories (`code/`, `data/raw/`, `data/processed/`, `models/`, `tests/unit/`, `tests/integration/`, `specs/`) and add `__init__.py` files.  
  - **Outputs**: Directory tree, empty `__init__.py` files.  
  - **Verification**: `tree` shows required folders; `pytest -q` runs with no collection errors.  

- [X] T002 **Config Definitions** – Add `code/config.py` with random seed, path constants, and placeholder `EXPECTED_AFLOW_CHECKSUM`.  
  - **Outputs**: `code/config.py`.  
  - **Verification**: Import succeeds; `config.RANDOM_SEED == 42`.  

- [X] T003 **Package Boilerplate** – Implement `code/__init__.py` and ensure `tests/__init__.py` exist.  
  - **Outputs**: `code/__init__.py`, `tests/__init__.py`.  
  - **Verification**: `python -c "import code"` runs without error.  

- [X] T004 **Logging Infrastructure** – Configure basic rotating logger in `code/config.py` (log file `code/logs/app.log`).  
  - **Outputs**: Updated `code/config.py`.  
  - **Verification**: Log file created on first script run; contains timestamped entries.  

---  

## Phase 1 – Test Infrastructure  

- [ ] T005 **Test Directory Structure & Init Files** – Establish the verification framework by creating:  
  - `tests/unit/__init__.py` and `tests/integration/__init__.py`.  
  - `tests/unit/test_ingestion.py` (validating data loading and checksums).  
  - `tests/unit/test_descriptors.py` (validating pymatgen calculations).  
  - `tests/integration/test_pipeline.py` (end-to-end smoke test).  
  - **Verification**: `pytest -q` discovers all modules and reports at least one passed test per file.  

---  

## Phase 2 – Data Ingestion & Integrity Checks  

- [ ] T006 **Ingestion Script (data_ingestion.py)** – Implement `code/data_ingestion.py` to:  
  1. Load a **verified** HEA Parquet dataset from Hugging Face via `datasets.load_dataset(..., streaming=True)`.  
  2. Filter for entries with ≥ 5 elements and non‑null `formation_energy` / `mixing_enthalpy`.  
  3. Export the filtered training set to `data/processed/heas_train.csv`.  
  4. Build an in‑memory composition‑hash index for later split logic.  
  - **Outputs**: `code/data_ingestion.py`, `data/processed/heas_train.csv`.  
  - **Verification**: Running `python -m code.data_ingestion` creates `heas_train.csv` with >0 rows.  

- [ ] T007 **Checksum Validation & Exponential Backoff** – Implement strict data hygiene in `code/data_ingestion.py` (or `code/utils.py`):  
  1. Compute SHA‑256 checksum of the downloaded raw Parquet file and compare against `config.EXPECTED_AFLOW_CHECKSUM`.  
  2. Implement exponential backoff for remote fetches: retry up to **3** times (intervals: 2 s, 4 s, 8 s).  
  3. Abort with a `ConnectionError` if all retries fail; no synthetic fallback allowed.  
  - **Verification**: Unit test `tests/unit/test_ingestion.py` asserts exactly three retry attempts on failure and a checksum mismatch error on tampered files.  

- [ ] T027 **Verified Dataset Replacement** – To satisfy FR-001 and Constitution II, replace `data/raw/hea_placeholder.csv` with the real verified HEA Parquet dataset:  
  1. Update `config.EXPECTED_AFLOW_CHECKSUM` to match the real source.  
  2. Re-run the ingestion pipeline.  
  - **Outputs**: Updated `data/raw/` file and checksum constant.  
  - **Verification**: Ingestion succeeds; raw file checksum matches the updated `config.EXPECTED_AFLOW_CHECKSUM`.  

---  

## Phase 3 – Split Generation (Hold‑out Known & True Novel)  

- [ ] T023 **Local Proxy Client Implementation** – Implement `code/proxy_client.py` that queries the local hash index of the raw dataset to determine presence/absence of a composition (Hill‑system string). Provides a function `is_known(composition_id) -> bool`.  
  - **Outputs**: `code/proxy_client.py`.  
  - **Verification**: Unit test confirms correct True/False responses for known and unknown hashes.  

- [ ] T009 **True Novel Generation** – Generate candidate compositions and filter them:  
  1. Enumerate 5‑element combinations from `config.ELEMENT_SOURCE_LIST`.  
  2. Use the **local proxy client (T023)** to ensure the candidate is **not** present in the raw dataset.  
  3. Compute descriptor‑space distance from the training centroid (from T011). Keep only those with distance ≥ 0.5 σ.  
  4. Stop at `config.NOVEL_TARGET_SIZE` (default 5 000) or pool exhaustion.  
  5. Export to `data/processed/true_novel.csv`.  
  - **Verification**: Final CSV contains a `distance_from_centroid` column; all rows are absent from the raw dataset via proxy check.  

- [ ] T010 **Split Validation Script** – Implement `code/validate_splits.py` to assert:  
  - `train ∩ holdout = ∅`, `train ∩ novel = ∅`, `holdout ∩ novel = ∅`.  
  - All `holdout` entries exist in the raw dataset (proxy “Found”).  
  - All `novel` entries return “Not Found”.  
  - **Outputs**: Exit code 0 on success; log summary to stdout.  

---  

## Phase 4 – Descriptor Calculation  

- [ ] T011 **Feature Engineering (feature_engineering.py)** – Implement `code/feature_engineering.py` to:  
  1. Load `heas_train.csv`.  
  2. Compute weighted **mean** and **variance** of atomic radius, electronegativity, VEC, and melting point using `pymatgen`.  
  3. Clamp any variance < 1e‑6 to exactly 1e‑6.  
  4. Write to `data/processed/heas_train_features.csv` matching `contracts/heas_train_features.schema.yaml`.  
  - **Verification**: Unit test `tests/unit/test_descriptors.py` checks known composition values and confirms clamping.  

---  

## Phase 5 – Model Training  

- [ ] T012 **Model Training Script (train_models.py)** – Implement `code/train_models.py` to:  
  1. Load `heas_train_features.csv`.  
  2. Perform 5‑fold cross‑validation (fixed seed) for `RandomForestRegressor` and `GradientBoostingRegressor`.  
  3. Grid‑search `max_depth ∈ {5,10,15}` and `n_estimators ∈ {100,200}`.  
  4. Save best models as `models/rf_model.pkl` and `models/gb_model.pkl`.  
  5. Persist overall cross‑validation interpolation R² to `data/results/interpolation_metrics.csv`.  
  - **Verification**: `.pkl` files exist; `metrics.csv` contains CV scores; runtime logged < 5 h.  

---  

## Phase 6 – Evaluation & Statistical Analysis  

- [ ] T013 **Hold‑out Evaluation** – `code/evaluate.py` loads trained models and `holdout_known.csv`, computes predictions, $R^{2}$, MAE, and writes `data/results/holdout_metrics.csv`.  
  - **Verification**: CSV contains columns `metric_name`, `value`, `test_type='none'`, `dataset='holdout'`.  

- [ ] T014 **True Novel Prediction & Uncertainty** – Extend `code/evaluate.py` to:  
  1. Predict on `true_novel.csv` using an **ensemble** (mean of RF & GB).  
  2. Calculate ensemble variance (difference between the two model predictions).  
  3. Append `prediction_variance` and `distance_from_hull` (computed in T015) columns.  
  4. Write `data/processed/true_novel_predictions.csv`.  
  - **Verification**: Variance column ≥ 0; distance column ≥ 0.  

- [ ] T015 **Convex Hull Distance Calculation** – Within `code/evaluate.py`:  
  1. Build a convex hull on the 8 descriptor columns of `heas_train_features.csv` (`scipy.spatial.ConvexHull`).  
  2. For each novel point, compute Euclidean distance to the hull (0 if inside).  
  3. Fall back to Mahalanobis distance with regularization 1e‑6 if `ConvexHull` fails.  
  - **Verification**: Distance values are numeric; log entry notes fallback usage if triggered.  

- [ ] T016 **Permutation Test (Mann‑Whitney U)** – Implement in `code/evaluate.py`:  
  - Compare absolute errors of `holdout_known` vs. training‑fold errors using Mann‑Whitney U.  
  - Record p‑value in `data/results/novel_stats.json` under key `holdout_mannwhitney_p`.  
  - **Verification**: JSON contains the p‑value (0 ≤ p ≤ 1).  

- [ ] T017 **Spearman Correlation (Uncertainty vs. Hull Distance)** – Implement in `code/evaluate.py`:  
  - If `true_novel_predictions.csv` contains ≥ 10 rows, compute Spearman ρ between `prediction_variance` and `distance_from_hull`.  
  - Store `spearman_rho` and `spearman_p` in `novel_stats.json`.  
  - **Verification**: JSON fields present; if <10 rows, script logs “Insufficient samples for Spearman test”.  

- [ ] T025 **Variance Distribution Generation** – Run 10 independent Random Forest models (seeds 0‑9) on the training data to collect per‑sample variance estimates; save to `data/results/rf_variance_distribution.npy`.  
  - **Verification**: Numpy file exists; shape matches `(num_samples, 10)`.  

---  

## Phase 7 – Report Assembly  

- [ ] T018 **Candidate Ranking & Thresholding** – Using the variance distribution from T025:  
  - Compute 10th‑percentile variance threshold.  
  - Filter `true_novel_predictions.csv` for variance ≤ threshold.  
  - Rank by `prediction_variance` (ascending) then `distance_from_hull`.  
  - Write `data/results/top_novel_candidates.csv`.  
  - **Verification**: CSV contains `rank` column starting at 1; number of rows ≤ 100.  

- [ ] T019 **Final Report Generation** – `code/report.py` creates `data/results/report.csv` containing:  
  - Interpolation CV $R^{2}$, Hold‑out $R^{2}$, MAE, Mann‑Whitney p‑value, Spearman ρ & p‑value, and top-10 novel candidates.  
  - Append disclaimer if `data/processed/dft_validation_status.txt` indicates DFT was not performed.  
  - **Verification**: CSV has header row with all fields; disclaimer appears when appropriate.  

---  

## Phase 8 – Optional DFT Validation  

- [ ] T020 **DFT Attempt Script** – `code/dft_attempt.py` tries to run a lightweight DFT (Quantum ESPRESSO) on the top 5 novel candidates:  
  1. Launch each calculation with a 1 h timeout.  
  2. On success, write `data/processed/dft_results.csv`; on failure, write `data/processed/dft_validation_status.txt` with the exact required disclaimer string.  
  - **Verification**: Presence of either `dft_results.csv` **or** `dft_validation_status.txt`.  

---  

## Phase 9 – Cross‑Cutting Clean‑up & Documentation  

- [ ] T021 **README & Quickstart Update** – Add installation steps, data‑flow diagram, and a command‑line example (`python -m code.pipeline`) for the end‑to‑end pipeline.  
  - **Verification**: `README.md` renders correctly; `make quickstart` executes without error.  

- [ ] T022 **PEP8 & Lint Compliance** – Run `ruff` and `black`; commit auto‑formatted changes.  
  - **Verification**: CI passes `ruff` and `black --check .`.  

- [ ] T024 **Pipeline Runtime Measurement** – Implement a timer in the top‑level pipeline entry point (`code/pipeline.py`) that:  
  1. Records total wall‑clock time to `data/results/runtime.txt`.  
  2. **Asserts** that the total recorded time is ≤ 6 h to satisfy SC‑004; fail the run if exceeded.  
  - **Verification**: `runtime.txt` exists and contains a numeric hour value ≤ 6.  

---  

## Dependency & Execution Order Summary  

| Phase | Tasks (IDs) | Must complete before |
|------|--------------|----------------------|
| 0 | T001‑T004 | – |
| 1 | T005 | Phase 0 |
| 2 | T006‑T007, T027 | Phase 1 |
| 3 | T023, T009, T010 | T006‑T007 (raw data must exist) |
| 4 | T011 | T023, T009, T010 (descriptor columns needed for splits) |
| 5 | T012 | T011 |
| 6 | T013‑T017, T025 | T012 |
| 7 | T018‑T019 | T016‑T017, T025 |
| 8 | T020 | T019 |
| 9 | T021‑T022, T024 | All prior phases |

---  

**End of `tasks.md`.**  