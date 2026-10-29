---
description: "Task list for feature 001‑predict‑molecular‑diffusion"
---

# Tasks: Predicting Molecular Diffusion Coefficients in Liquids with Graph Neural Networks

**Input**: `specs/001-predict-molecular-diffusion-coefficie/spec.md`, `plan.md`  
**Prerequisites**: Tasks are ordered to respect data flow; parallel (`[P]`) tasks do not share files.

The checklist follows the canonical format  

```
- [ ] T### [P] [USx] <description> – <file‑path>
    • <verification / requirement / note>
```

* `[P]` = can run in parallel with other tasks that do **not** share files.  
* `[USx]` = the user story satisfied (`US1` = data ingestion & featurization, `US2` = training & baseline, `US3` = sensitivity & robustness).

---

## Phase 0 – Data acquisition & provenance

- [~] T001 [P] [US1] Create the raw‑data directory – `data/raw/`  
    • Verification: after running the setup script, `ls data/raw` lists a directory (exit code 0).  

- [~] T002 [P] [US1] Generate a deterministic synthetic dataset (validation‑only fallback) – `code/ingestion/generate_synthetic.py`  
    • The script writes `data/raw/dataset.csv` with **exactly 500** rows and columns `smiles,solvent_type,diffusion_coefficient,viscosity,dielectric_constant`, using a fixed random seed (`42`).  
    • **Note:** This synthetic dataset is **only** for pipeline validation and does **not** satisfy FR‑001, which requires experimental data.  
    • Verification: the CSV exists, its row count equals 500, and it validates against `contracts/ingestion_schema.schema.yaml`.  

- [ ] T003 [P] [US1] Download a verified real dataset – `code/ingestion/fetch_real.py`   <!-- FAILED-IN-EXECUTION: code/ingestion/fetch_real.py exit=1 -->
    • Reads a line `Dataset URL: <url>` from `plan.md`, downloads the CSV to `data/raw/dataset.csv`, and raises an exception on any network or HTTP error (no silent fallback).  
    • If `plan.md` does **not** contain a URL, the script aborts with a clear error (“No real dataset URL – FR‑001 cannot be satisfied”).  
    • Verification: on success the file exists, is non‑empty, and passes schema validation (`contracts/ingestion_schema.schema.yaml`). On missing URL the script exits with non‑zero status and logs the abort message.  

- [~] T004 [P] [US1] Record the data‑source flag – `code/ingestion/flag_source.py`  
    • Writes `data/data_source_flag.json` with `{ "source": "real" }` if `fetch_real.py` succeeded, otherwise `{ "source": "synthetic" }`.  
    • Verification: the JSON file exists and contains the correct `"source"` value.  

- [~] T019 [P] [US1] Compute SHA‑256 checksums of raw dataset files – `code/ingestion/checksums.py`  
    • Reads all files under `data/raw/`, computes their SHA‑256 hashes, and writes `data/checksums.txt` (one `<hash>  <relative_path>` per line).  
    • Verification: `data/checksums.txt` exists, contains a line for `dataset.csv`, and each hash matches the file’s content.  

- [ ] T020 [P] [US1] Update project versioning metadata – `code/ingestion/update_state.py`  
    • After any raw‑data artifact creation (directory, CSV, checksum file), updates the project's `state/.../artifact_hashes` map with the new file hashes and refreshes the `updated_at` ISO‑8601 timestamp.  
    • Verification: the state YAML file contains entries for the newly created artifacts and a recent `updated_at` timestamp.  

---

## Phase 1 – Ingestion & featurization pipeline

- [~] T005 [P] [US1] Validate raw records (SMILES syntax, missing fields) – `code/ingestion/validate.py`  
    • Returns a list of **valid** records, logs `[INVALID_SMILES]` for unparsable SMILES and `[MISSING_DATA_EXCLUDED]` for incomplete rows.  
    • Writes `data/processed/valid_record_count.txt` containing the integer count of valid records.  
    • Verification: after execution on `data/raw/dataset.csv`, `data/logs/ingestion.log` contains the expected tags, `data/processed/valid_record_count.txt` exists and its integer value equals the number of records marked *valid*.  

- [~] T006 [P] [US1] Featurize validated records into PyTorch‑Geometric graphs and solvent descriptors – `code/ingestion/featurize.py`  
    • Produces `data/processed/featurized_data.jsonl`; each line conforms to `contracts/dataset.schema.yaml`.  
    • Records peak memory usage during processing to `artifacts/reports/memory_profile.json` (SC‑005).  
    • Verification: a random line parsed with `jsonschema.validate` passes the schema; file size > 0 KB; `memory_profile.json` contains `peak_memory_mb` and asserts `peak_memory_mb ≤ 7000`.  

- [~] T007 [P] [US1] End‑to‑end ingestion orchestrator – `code/ingestion/ingest.py`
    • Calls `validate.py` → `featurize.py` → writes the JSONL output; skips invalid records, logs reasons, and updates `data/data_source_flag.json` if needed.  
    • Verification: after execution, `data/processed/featurized_data.jsonl` exists and the number of records equals the count recorded in `data/processed/valid_record_count.txt`.  

- [~] T021 [P] [US1] Batch‑process extremely large molecules to stay within memory limits – `code/ingestion/batch_featurize.py`  
    • Detects molecules whose atom count exceeds a configurable threshold (e.g., 200 atoms) and processes them in smaller sub‑batches or logs `[EXCEEDED_MEMORY]` and skips them.  
    • Verification: logs contain no unhandled OOM errors; `memory_profile.json` reports peak memory ≤ 7000 MB even when large‑molecule records are present.  

---

## Phase 2 – Model implementation & training (CPU‑only)

- [~] T008 [P] [US2] Implement a CPU‑only single‑layer Message Passing Neural Network – `code/models/mpnn.py`  
    • On import, asserts `torch.cuda.is_available() is False` and logs “Device: CPU”.  
    • Provides a `forward` method that accepts a batch of `torch_geometric.data.Data`.  
    • Verification: unit test runs a forward pass on a tiny synthetic batch without raising; the log contains “Device: CPU”.  

- [ ] T009 [P] [US2] Implement a linear‑regression baseline using Morgan fingerprints + solvent descriptors – `code/models/baseline.py`  
    • Uses `sklearn.linear_model.LinearRegression` and a helper to compute 2048‑bit fingerprints from SMILES.  
    • Verification: training on a 10‑sample synthetic dataset produces a non‑empty coefficient vector and a successful `fit` call.  

- [ ] T010 [P] [US2] 5‑fold cross‑validation strategy stratified by solvent type – `code/training/cv_strategy.py`  
    • Raises `ConfigurationError` if the processed dataset contains fewer than 50 samples; otherwise returns exactly 5 folds with solvent‑type distribution deviation ≤ 5 % per fold.  
    • Verification: unit test on a processed dataset with ≥ 50 rows checks the number of folds and the distribution constraint.  

- [ ] T011 [P] [US2] Training loop with checkpointing for both models – `code/training/train.py`  
    • Executes the CV strategy, trains the MPNN and baseline on each fold, saves checkpoints to `artifacts/models/mpnn_fold_{i}.pt` and `artifacts/models/baseline_fold_{i}.pt`.  
    • Records peak memory usage to `artifacts/reports/memory_profile.json` (SC‑005) and logs runtime per fold.  
    • Verification: after running on `data/processed/featurized_data.jsonl`, checkpoint files exist for all folds, `training.log` contains start‑to‑end timestamps for each fold, `memory_profile.json` asserts `peak_memory_mb ≤ 7000`, and the log reports successful completion.  

---

## Phase 3 – Evaluation & statistical testing

- [ ] T012 [P] [US2] Compute per‑fold and aggregated metrics; write `evaluation.json` – `code/evaluation/evaluate.py`  
    • Calculates Pearson r, RMSE, and `n_samples` for each fold; aggregates mean ± std.  
    • Records total pipeline runtime (`total_runtime_seconds`) (SC‑003).  
    • **Only** writes `artifacts/reports/evaluation.json` when `data/data_source_flag.json` reports `"real"`; otherwise exits with a clear message (“Synthetic data – metrics suppressed”).  
    • Verification: for a real dataset the file exists and validates against `contracts/output.schema.yaml`; for synthetic runs the script exits with status 0 and no JSON is created.  

- [ ] T013 [P] [US2] Perform paired statistical testing on per‑sample absolute errors – `code/evaluation/statistics.py`  
    • Executes a paired t‑test (or Wilcoxon if normality fails) between GNN and baseline errors; inserts results under `statistical_test` in `evaluation.json`.  
    • Verification: after `evaluate.py` finishes on real data, `evaluation.json` contains a `statistical_test` object with fields `test_type`, `p_value`, and `significant`.  

---

## Phase 4 – Sensitivity analysis, ablation & robustness

- [ ] T014 [P] [US3] Hyperparameter sweep (message‑passing steps ∈ {1, 2, 3}) – `code/evaluation/sensitivity.py`  
    • Retrains both models for each step count, records metrics, and writes `artifacts/reports/sensitivity_results.json`.  
    • Verification: the JSON exists, contains exactly three entries (one per step), and each entry includes `hyperparameter`, `value`, `pearson_r`, and `rmse` fields as defined in `contracts/results.schema.yaml`’s `sensitivity_analysis` section.  

- [ ] T015 [P] [US3] Ablation study removing solvent descriptors – `code/evaluation/ablation.py`  
    • When `data/data_source_flag.json` = `"real"`, drops `solvent_features` from the input, retrains the MPNN, and writes `artifacts/reports/ablation_report.json`.  
    • Skips execution for synthetic data with a logged notice.  
    • Verification: for real data the ablation JSON exists and contains fields `r` and `rmse`; for synthetic runs the script exits with status 0 and logs “Ablation skipped: synthetic data”.  

---

## Phase 5 – Documentation, quick‑start & CI

- [ ] T016 [P] Write a user‑facing quick‑start script that runs the full pipeline on synthetic data – `run_quickstart.py`  
    • Calls the synthetic generator, ingestion, featurization, training (CPU‑only), and sensitivity sweep; **does not** attempt to write `evaluation.json` (synthetic flag prevents it).  
    • Exits with status 0 and leaves a complete set of artifacts under `artifacts/`.  
    • Verification: after execution, `run_quickstart.py` returns 0 and `artifacts/reports/` contains `sensitivity_results.json` (and `ablation_report.json` if generated) but no `evaluation.json`.  

- [ ] T017 [P] Add a CI workflow that lints, runs all unit/integration tests, and executes the quick‑start script – `.github/workflows/ci.yml`  
    • Uses the default free‑tier runner (2 CPU cores, ≤ 7 GB RAM).  
    • Fails on any lint warning, test failure, or non‑zero exit from `run_quickstart.py`.  
    • Verification: the workflow file exists and a local `pytest` run returns 0; `act` (or equivalent) can execute the workflow without errors.  

- [ ] T018 [P] Validate final reports against project contracts – `code/evaluation/validate_reports.py`  
    • Validates `artifacts/reports/evaluation.json` against `contracts/results.schema.yaml` and `artifacts/reports/results_report.json` against `contracts/results_report.schema.yaml`.  
    • Verification: script exits with status 0 if all real‑data reports conform; otherwise prints schema‑validation errors.  