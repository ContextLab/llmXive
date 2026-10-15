---
description: "Task list for feature 001‑predict‑molecular‑diffusion"
---

# Tasks: Predicting Molecular Diffusion Coefficients in Liquids with Graph Neural Networks

**Input**: `specs/001-predict-molecular-diffusion-coefficie/spec.md`, `plan.md`  
**Prerequisites**: None (all tasks are self‑contained and ordered to respect data flow)

The checklist follows the canonical format  

```
- [ ] T### [P] [USx] <description> – <file‑path>
    • <verification / requirement / note>
```

* `[P]` = can run in parallel with other tasks that do **not** share files.  
* `[USx]` = the user story satisfied (US1 = data ingestion & featurization, US2 = training & baseline, US3 = sensitivity & robustness).

---

## Phase 0 – Data acquisition & provenance

- [ ] T001 [P] [US1] Create the raw‑data directory – `data/raw/`  
    • Verify that `data/raw` exists after running the setup script (`ls data/raw` returns a folder).

- [ ] T002 [US1] Generate a deterministic synthetic dataset (fallback when no real data) – `code/ingestion/generate_synthetic.py`  
    • The script writes `data/raw/dataset.csv` with **exactly 500** rows and the columns `smiles,solvent_type,diffusion_coefficient,viscosity,dielectric_constant`.  
    • Uses a fixed random seed (`42`).  
    • Verification: the CSV exists, size > 0 KB, row count = 500, and validates against `contracts/ingestion_schema.schema.yaml`.

- [ ] T003 [US1] Download a verified real dataset (if a URL is recorded in `plan.md`) – `code/ingestion/fetch_real.py`  
    • Reads a line `Dataset URL: <url>` from `plan.md`, downloads the CSV to `data/raw/dataset.csv`, and raises an exception on any network or HTTP error (no silent fallback).  
    • Verification: file exists, non‑empty, and passes schema validation (`contracts/ingestion_schema.schema.yaml`).

- [ ] T004 [US1] Record the data‑source flag – `code/ingestion/flag_source.py`  
    • Writes `data_source_flag.json` with `{ "source": "real" }` if `fetch_real.py` succeeded, otherwise `{ "source": "synthetic" }`.  
    • Verification: the JSON file exists and contains the correct `"source"` value.

---

## Phase 1 – Ingestion & featurization pipeline

- [ ] T005 [P] [US1] Validate raw records (SMILES syntax, missing fields) – `code/ingestion/validate.py`  
    • Returns a list of **valid** records, logs `[ERROR_SMILES]` for unparsable SMILES and `[MISSING_DATA_EXCLUDED]` for incomplete rows.  
    • Verification: after running on `data/raw/dataset.csv`, the log `data/logs/ingestion.log` contains the expected tags and the returned list length equals the number of rows marked *valid*.

- [ ] T006 [US1] Featurize validated records into PyTorch‑Geometric graphs and solvent descriptors – `code/ingestion/featurize.py`  
    • Produces a JSON Lines file `data/processed/featurized_data.jsonl`.  
    • Each line conforms to `contracts/dataset.schema.yaml` (graph fields, solvent_features, status).  
    • Records peak memory usage during processing to `artifacts/reports/memory_profile.json` (SC-005).  
    • Verification: a random line parsed with `jsonschema.validate` passes the schema; file size > 0 KB; memory profile contains `peak_memory_mb`.

- [ ] T007 [US1] End‑to‑end ingestion script that ties validation and featurization together – `code/ingestion/ingest.py`  
    • Calls `validate.py` → `featurize.py` → writes the JSONL output.  
    • Skips invalid records, logs reasons, and updates `data_source_flag.json` if needed.  
    • Verification: after execution, `data/processed/featurized_data.jsonl` exists and the number of records equals the count of *valid* rows reported in the log.

---

## Phase 2 – Model implementation & training (CPU‑only)

- [ ] T008 [P] [US2] Implement a CPU‑only single‑layer Message Passing Neural Network – `code/models/mpnn.py`  
    • On import, asserts `torch.cuda.is_available() is False`; logs “Device: CPU”.  
    • Provides a `forward` method that accepts a batch of `torch_geometric.data.Data`.  
    • Verification: unit test runs a forward pass on a tiny synthetic batch without raising; the log contains “Device: CPU”.

- [ ] T009 [P] [US2] Implement a linear‑regression baseline using Morgan fingerprints + solvent descriptors – `code/models/baseline.py`  
    • Uses `sklearn.linear_model.LinearRegression`.  
    • Includes a helper to compute 2048‑bit fingerprints from SMILES.  
    • Verification: training on a 10‑sample synthetic dataset produces a non‑empty coefficient vector.

- [ ] T010 [P] [US2] 5‑fold cross‑validation strategy stratified by solvent type – `code/training/cv_strategy.py`  
    • Raises `ConfigurationError` if the dataset contains fewer than 50 samples; a downstream fallback (Leave‑One‑Out) is handled elsewhere.  
    • Verification: given a processed dataset with ≥ 50 rows, the script returns exactly 5 folds where the solvent-type distribution per fold deviates from the global distribution by ≤ 5% (checked in a unit test).

- [ ] T011 [US2] Training loop with checkpointing for both models – `code/training/train.py`  
    • Executes the CV strategy, trains the MPNN and baseline on each fold, saves model checkpoints to `artifacts/models/mpnn_fold_{i}.pt` and `artifacts/models/baseline_fold_{i}.pt`.  
    • Records peak memory usage during training to `artifacts/reports/memory_profile.json` (SC-005).  
    • Logs device verification and runtime per fold.  
    • Verification: after running on the processed JSONL (real or synthetic), the expected checkpoint files exist for all folds and `training.log` records start‑to‑end timestamps.

---

## Phase 3 – Evaluation & statistical testing

- [ ] T012 [P] [US2] Compute per‑fold and aggregated metrics; write `evaluation.json` – `code/evaluation/evaluate.py`  
    • Calculates Pearson r, RMSE, and number of test samples for each fold; aggregates mean ± std.  
    • Records total pipeline runtime (`total_runtime_seconds`) in the results report (SC-003).  
    • Logic is exercised for both real and synthetic data, but the final `evaluation.json` is **only** written when `data_source_flag.json` reports `"real"`; otherwise exits with a clear message (“Synthetic data – metrics suppressed”).  
    • Verification: for a real dataset the file `artifacts/reports/evaluation.json` exists and validates against `contracts/output.schema.yaml`; for synthetic runs the script exits with status 0 (logic verified) but no JSON is created.

- [ ] T013 [P] [US2] Perform paired statistical testing on per‑sample absolute errors – `code/evaluation/statistics.py`  
    • Executes a paired t‑test (or Wilcoxon if normality fails) between GNN and baseline errors; inserts results under `statistical_test` in `evaluation.json`.  
    • Verification: after `evaluate.py` finishes on real data, `evaluation.json` contains a `statistical_test` object with fields `test_type`, `p_value`, and `significant`.

---

## Phase 4 – Sensitivity analysis, ablation & robustness

- [ ] T014 [P] [US3] Hyperparameter sweep (message‑passing steps ∈ {1,2,3}) – `code/evaluation/sensitivity.py`  
    • Retrains both models for every grid point, records metrics, and writes `artifacts/reports/sensitivity_report.json`.  
    • Verification: the JSON file contains an entry for each combination (3 entries) and each entry conforms to the `sensitivity_analysis` schema.

- [ ] T015 [P] [US3] Ablation study removing solvent descriptors – `code/evaluation/ablation.py`  
    • When `data_source_flag.json` = `"real"`, drops `solvent_features` from the input, retrains the MPNN, and writes `artifacts/reports/ablation_report.json`.  
    • Skips execution for synthetic data with a logged notice.  
    • Verification: for real data the ablation JSON exists and contains fields `r` and `rmse`; for synthetic runs the script exits with status 0 and logs “Ablation skipped: synthetic data”.

- [ ] T016 [P] [US3] Outlier‑robustness analysis – `code/evaluation/outlier_analysis.py`  
    • Computes Pearson r on the full test set and again after removing the top 5 % highest residuals; writes `artifacts/reports/outlier_analysis.json`.  
    • Verification: the JSON includes `full_set_r` and `trimmed_set_r` numeric fields.

---

## Phase 5 – Documentation, quick‑start & CI

- [ ] T017 [P] Write a user‑facing quick‑start script that runs the full pipeline on synthetic data – `run_quickstart.py`  
    • Calls the synthetic generator, ingestion, featurization, training (CPU‑only), and sensitivity sweep; **does not** attempt to write `evaluation.json` (synthetic flag prevents it).  
    • Exits with status 0 and leaves a complete set of artifacts under `artifacts/`.  
    • Verification: after execution, `run_quickstart.py` returns 0 and the directory `artifacts/reports/` contains `sensitivity_report.json` and `outlier_analysis.json` but no `evaluation.json`.

- [ ] T018 [P] Add a CI workflow that lints, runs all unit/integration tests, and executes the quick‑start script – `.github/workflows/ci.yml`  
    • Uses the default free‑tier runner (2 CPU cores, ≤ 7 GB RAM).  
    • Fails on any lint warning, test failure, or non‑zero exit from `run_quickstart.py`.  
    • Verification: the workflow file exists and a local execution of the test suite (e.g., `pytest`) returns 0.

- [ ] T019 [P] Validate final reports against project contracts – `code/evaluation/validate_reports.py`  
    • Validates `artifacts/reports/evaluation.json` against `contracts/results.schema.yaml` and `artifacts/reports/results_report.json` against `contracts/results_report.schema.yaml`.  
    • Verification: script exits with status 0 if all real-data reports conform to their respective schemas.

---

### Dependency‑to‑requirement mapping (summary)

| Spec requirement | Satisfying task(s) |
|------------------|--------------------|
| FR‑001 | T003 |
| FR‑002 | T006, T007 |
| FR‑003 | T008, T011 |
| FR‑004 | T010, T011 |
| FR‑005 | T013, T012 |
| FR‑006 | T014, T015, T016 |
| FR‑007 | T005, T006, T007 |
| SC‑001 | T012 |
| SC‑002 | T013 |
| SC‑003 | T012 |
| SC‑004 | T014, T015, T016 |
| SC‑005 | T006, T011 |
| Edge‑case handling (large molecules, missing data, synthetic fallback) | T005, T006, T002, T015, T012 |

All tasks respect the data flow: directory creation → raw‑data acquisition → validation → featurization → model training → evaluation → analysis → reporting.