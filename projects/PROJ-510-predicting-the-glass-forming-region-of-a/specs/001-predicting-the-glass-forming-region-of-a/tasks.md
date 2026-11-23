# Tasks: Predicting the Glass Forming Region of Alloy Systems with Machine Learning  

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, and the JSON‑Schema contracts in `specs/001-predict-glass-forming-region/contracts/`.

The study must deliver a fully reproducible end‑to‑end pipeline that ingests real experimental alloy data, engineers thermodynamic descriptors from OQMD, trains and validates a Random Forest model, performs feature‑importance and sensitivity analyses, validates every artifact against its schema, and produces a final report that respects all functional and scientific requirements.

---  

## Phase 0 – Project scaffolding & validation utilities  

- [ ] T001 [P] Create a **quickstart guide** (`specs/001-predict-glass-forming-region/quickstart.md`) that lists the exact command chain to run the whole pipeline from a fresh checkout.   <!-- FAILED-IN-EXECUTION: code/run_all.py exit=1 --> <!-- FAILED: unspecified -->
    - *Verification*: `cat quickstart.md` shows the command `python -m code.run_all` and matches the ordering of tasks below.  

- [ ] T002 [P] Implement **schema‑validation script** `code/validate_schemas.py`.  
    - Loads each generated CSV/JSON and validates it against the corresponding YAML contract in `specs/001-predict-glass-forming-region/contracts/`.  
    - Writes a human‑readable log `data/logs/schema_validation.log` (zero errors = pass).  
    - *Verification*: `python code/validate_schemas.py && grep "ERROR" data/logs/schema_validation.log` returns no matches.  

---  

## Phase 1 – Data ingestion, cleaning, and provenance  

- [ ] T003 [US-1] Write `code/ingestion.py` to **download** the experimental CCR dataset from the verified URL `[UNRESOLVED-CLAIM: https://example.com/experimental_ccr_dataset.csv` — HTTP 404] (to be replaced with the actual curated source) and stream OQMD elemental properties via `datasets.load_dataset(..., streaming=True)`.   <!-- FAILED-IN-EXECUTION: code/ingestion.py exit=1 -->
    - Logs download status to `data/logs/download.log`.  
    - On any network failure, catches the exception **and writes** a concise entry to `data/logs/fetch_error.log`.  
    - *Verification*: Simulate a failed URL (e.g., `[UNRESOLVED-CLAIM: http://invalid` — ConnectionError: HTTPConnectionPool(host='invalid%60', port=80): Max retries exceeded with url: / (Caused by NameResolutionError("HTTPConnection(host='invalid%60', port=80): Failed to resolve 'invalid%60' ([Errno -2] Name or service not known)"))]) and confirm the file `data/logs/fetch_error.log` is created with the exception message.  

- [ ] T004 [US-1] Extend `code/ingestion.py` to **filter** entries:  
    - Remove rows with missing or non‑numeric `critical_cooling_rate` or undefined `glass_forming_label`.  
    - For each excluded row, write a line to `data/logs/exclusion_log.txt` containing the `composition` and reason, and increment counters stored in `data/logs/label_filtering_status.json`.  
    - *Verification*: After a run on the real dataset, `exclusion_log.txt` contains at least one line and `label_filtering_status.json` reports `"excluded": <int>`.  

- [ ] T005 [US-1] Add **empty‑dataset guard** in `code/ingestion.py`.  
    - After filtering, if the number of valid rows < 500, raise `ValueError("Dataset is empty after filtering. Check composition parsing logic and data source validity.")` and write the full traceback to `data/logs/empty_dataset_error.log`.  
    - *Verification*: Force a tiny synthetic CSV (< 500 rows) through the pipeline and confirm the exception is raised and the log file exists.  

- [ ] T006 [US-1] Output the cleaned, feature‑ready table to `data/processed/processed_alloys.csv` and **record its SHA‑256** checksum in `data/logs/ingestion_hash.txt`.  
    - The hash file must contain a single 64‑character hex string followed by the filename.  
    - *Verification*: `sha256sum data/processed/processed_alloys.csv > data/logs/ingestion_hash.txt` produces the same line as the script.  

---  

## Phase 2 – Thermodynamic feature engineering & unit testing  

- [ ] T007 [US-1] Implement `code/features.py` that reads `processed_alloys.csv`, looks up OQMD elemental properties, and computes:  
    - `mixing_enthalpy` (ΔH_mix),  
    - `atomic_size_difference` (δ),  
    - `electronegativity_variance` (σ_χ).  
    - Missing elemental data must raise a `ValueError` (no synthetic fallback).  
    - **Writes the results to a new file** `data/processed/processed_alloys_with_features.csv` (preserving the original raw CSV).  
    - *Verification*: Spot‑check a known alloy (e.g., Zr50Cu30Al20) and confirm the three descriptor values are within the tolerances specified in the spec.  

- [ ] T008 [US-1] Create **unit‑test suite** `code/tests/test_features.py` containing at least:  
    - `test_mixing_enthalpy()` – compares computed ΔH_mix to a hand‑calculated reference (tolerance ±0.01 eV/atom).  
    - `test_atomic_size_difference()` – validates δ against the reference tolerance ±0.01.  
    - `test_electronegativity_variance()` – validates σ_χ within ±0.005.  
    - *Verification*: `pytest code/tests/test_features.py -q` reports all tests passed.  

- [ ] T009 [US-1] Add **filtering unit tests** `code/tests/test_filtering.py` with:  
    - `test_exclusion_logging()` – verifies that a row with missing `critical_cooling_rate` results in an entry in `exclusion_log.txt` and an incremented count in `label_filtering_status.json`.  
    - `test_empty_dataset_error()` – feeds a < 500‑row CSV and asserts that `empty_dataset_error.log` is created and contains the expected error message.  
    - *Verification*: `pytest code/tests/test_filtering.py -q` passes.  

---  

## Phase 3 – Model training, cross‑validation, and reproducible splits  

- [ ] T010 [US-2] Write `code/trainer.py` that:  
    - Loads `processed_alloys_with_features.csv`.  
    - Performs a **stratified 80/20 train‑test split** based on `glass_forming_label` (preserving class distribution), using `random_state=42`.  
    - Saves the split CSVs as `data/processed/train.csv` and `data/processed/test.csv`.  
    - Trains a `RandomForestRegressor(random_state=42)` on the training set.  
    - Executes **5‑fold cross‑validation** (RMSE) and also fits a `DummyRegressor(strategy="mean")`.  
    - Conducts a paired permutation test (10 000 permutations) to compute a p‑value comparing RF vs Dummy RMSE.  
    - Writes the trained model to `data/models/random_forest_model.pkl` and metrics to `data/models/cv_metrics.json` conforming to `metrics.schema.yaml`.  
    - *Verification*: `python code/trainer.py && cat data/models/cv_metrics.json` shows keys `fold_scores`, `mean_rmse`, `test_rmse`, `dummy_rmse`, `p_value`.  

- [ ] T011 [US-2] Add **unit test** `code/tests/test_training.py` that loads the saved `train.csv`, verifies that the number of rows equals 80 % of the filtered dataset and that `random_state=42` yields identical splits across runs.  
    - *Verification*: Running the test twice produces the same split sizes and identical SHA‑256 of `train.csv`.  

---  

## Phase 4 – Permutation importance analysis  

- [ ] T012 [US-2] Extend `code/evaluator.py` with a `run_permutation_importance()` function that:  
    - Uses the trained RF model and the full processed dataset.  
    - Performs **1000 permutations** (`random_state=42`) for each of the three descriptors.  
    - Computes mean importance scores and empirical p‑values against a shuffled baseline.  
    - Saves results to `data/reports/feature_importance.csv` matching `feature_importance.schema.yaml`.  
    - *Verification*: The CSV contains three rows (`mixing_enthalpy`, `atomic_size_difference`, `electronegativity_variance`) with non‑null `importance_mean` and `p_value` < 0.05 for at least one feature.  

---  

## Phase 5 – Sensitivity (binary‑threshold) analysis  

- [ ] T013 [US-2] In `code/evaluator.py` add `run_sensitivity_analysis()` that:  
    - Binarizes `critical_cooling_rate` at thresholds **50, 100, 150 K/s**.  
    - For each threshold, trains a `RandomForestClassifier(random_state=42)` on the same stratified split, computes **F1‑score**, and records it.  
    - Applies a Bonferroni‑corrected significance check; if the variance of the three F1 scores ≤ 0.05, set `stability_status` to `"PASS"` else `"FAIL"`.  
    - Writes `data/reports/sensitivity_report.json` conforming to `sensitivity.schema.yaml`.  
    - *Verification*: The JSON contains `"thresholds": [50,100,150]`, three numeric `f1_scores`, and a `"stability_status"` field.  

---  

## Phase 6 – Full‑pipeline validation & reproducibility audit  

- [ ] T014 Execute the **full pipeline** from ingestion to report generation using a single entry point `code/run_all.py` that sequentially calls the scripts created above.  
    - The script must abort on any uncaught exception, ensuring no silent fallbacks.  
    - After successful run, invoke `python code/validate_schemas.py` and confirm `data/logs/schema_validation.log` contains “0 errors”.  
    - *Verification*: Running `python code/run_all.py` completes without error and the validation log reports zero errors.  

- [ ] T015 Perform a **clean‑room reproducibility run**:  
    - Delete the entire `data/` directory, re‑execute `code/run_all.py` in a fresh environment, and compare the newly generated `data/logs/ingestion_hash.txt` with the one produced in the previous run.  
    - The two SHA‑256 hashes must be identical, demonstrating deterministic processing.  
    - *Verification*: `diff <(cat data/logs/ingestion_hash.txt) <(cat data/logs/ingestion_hash.txt.previous)` yields no differences.  

---  

## Phase 7 – Final report generation & handoff  

- [ ] T016 [US-2] Implement `code/generate_report.py` that reads `cv_metrics.json`, `feature_importance.csv`, and `sensitivity_report.json` and writes a concise `REPORT.md`.  
    - The report must explicitly:  
        1. Frame all findings as **associational** (FR‑006).  
        2. Discuss the limitation of using only three thermodynamic descriptors and note omitted predictors (FR‑007).  
        3. Include tables summarizing RMSE, F1 scores, and feature‑importance rankings.  
    - *Verification*: Grep the generated `REPORT.md` for the words “associational” and “limitation” – both must appear.  

---  

## Additional Verification Tasks  

- [ ] T017 [US-1] Add a verification step in `code/ingestion.py` that asserts every `critical_cooling_rate` entry originates from the experimental dataset; raise an error if any synthetic or imputed value is detected.  
    - *Verification*: Running the ingestion script on a dataset containing a fabricated CCR triggers a `ValueError` and logs the issue.  

- [ ] T018 [SC‑002] After model training, compute a paired permutation test (10 000 permutations) comparing RF RMSE to Dummy RMSE and record the p‑value in `cv_metrics.json`. Add a check that asserts `p_value < 0.05`.  
    - *Verification*: The pipeline fails if the p‑value is ≥ 0.05, ensuring SC‑002 is met.  

- [ ] T019 [SC‑006] After sensitivity analysis, assert that each recorded `f1_score` ≥ 0.70. If any falls below, raise a warning and log it in `data/logs/sensitivity_warning.log`.  
    - *Verification*: The pipeline logs a warning only when the threshold is not met; successful runs have all F1 ≥ 0.70.  

---  

## Success Criteria Table (updated)  

| Criterion | Artifact | Verification Task |
|-----------|----------|-------------------|
| SC‑001 | `processed_alloys.csv` | T006 ensures ≥ 500 rows |
| SC‑002 | `cv_metrics.json` (p‑value) | T018 checks statistical significance |
| SC‑003 | `empty_dataset_error.log` | T005 guard |
| SC‑004 | `feature_importance.csv` | T012 reports p‑values < 0.05 |
| SC‑005 | `exclusion_log.txt` & `label_filtering_status.json` | T004 & T009 |
| SC‑006 | `sensitivity_report.json` (F1 scores) | T019 enforces ≥ 0.70 |
| SC‑007 | All artifacts validated | T002 & T037 (validation log) |

---  

*All tasks are unchecked; the verifier will mark them as completed when the corresponding artifacts exist and pass the described checks.*  