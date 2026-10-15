---
description: "Task list for feature 001‑predict‑molecular‑diffusion"
---

# Tasks: Predicting Molecular Diffusion Coefficients in Liquids with Graph Neural Networks

**Input**: Design documents from `specs/001-predict-molecular-diffusion-coefficie/`  
**Prerequisites**: `plan.md` (required), `spec.md` (required for user stories)  

All tasks follow the canonical checklist format  

```
- [ ] T### [P] [USx] <description> – <file‑path>
    • <verification / requirement / note>
```

The optional **[P]** flag indicates the task can run in parallel with other tasks that do **not** share files.  
**[USx]** tags the user story the task satisfies (US1, US2, US3).  

---

## Phase 0 – Data Acquisition & Validation (blocked until a verified dataset is available)

- [ ] T000a [P] [US1] Create `data/raw/` directory for source CSVs – `data/raw/`  
  • Verify the directory exists in the repository (`ls data/raw` returns a folder).

- [ ] T000b [P] [US1] Download the curated experimental diffusion dataset CSV – `data/raw/dataset.csv`  
  • If `plan.md` contains a line `Dataset URL: <url>`, the script must download the CSV from that URL.  
  • On download failure, the script must raise an exception (no silent fallback).  
  • Verify `data/raw/dataset.csv` exists, is non‑empty, and validates against `contracts/ingestion_schema.schema.yaml`.

- [ ] T007b [P] [US1] Implement deterministic synthetic dataset generator – `code/ingestion/generate_synthetic.py`  
  • Generates `data/raw/dataset.csv` with exactly 500 rows and columns `smiles, solvent_type, diffusion_coefficient, viscosity, dielectric_constant`.  
  • Uses a fixed random seed (`42`).  
  • Verify the CSV schema matches `contracts/ingestion_schema.schema.yaml` and file size > 0 KB.

- [ ] T007b_test [P] [US1] Add contract test for synthetic CSV generation – `tests/contract/test_synthetic_csv.py`  
  • Runs `generate_synthetic.py` and asserts the output file exists, has 500 rows, and validates against the ingestion schema.

- [ ] T000c [P] [US1] Implement real‑dataset fetcher – `code/ingestion/fetch_real.py`  
  • Reads the `Dataset URL:` line from `plan.md`, downloads the CSV, writes to `data/raw/dataset.csv`.  
  • Raises `FileNotFoundError` or `ConnectionError` on failure (no silent fallback).  
  • Verify that on success the file validates against the ingestion schema.

- [ ] T000d [P] [US1] Verify `plan.md` records the dataset source – `plan.md`  
  • After a successful real download, a line `Dataset URL: <url>` must be present.  
  • If synthetic data is used, `data_source_flag.json` must contain `"source": "synthetic"`.  
  • Test `tests/contract/test_plan_dataset_url.py` checks for one of the two conditions.

- [ ] T007c [P] [US1] Write source‑flag file – `code/ingestion/flag_source.py`  
  • Writes `data_source_flag.json` with `{"source": "real"}` or `{"source": "synthetic"}` based on which ingestion path succeeded.  
  • Verify the JSON file exists and contains the correct `"source"` value.

- [ ] T007c_test [P] [US1] Add unit test for the source‑flag file – `tests/unit/test_flag_source.py`  
  • Simulates both real and synthetic runs and asserts the JSON content matches the expected source.

---

## Phase 1 – Project Setup (shared infrastructure)

- [ ] T001 [P] Create project directory layout – `code/`, `data/raw/`, `data/processed/`, `data/checksums.txt`, `artifacts/`  
  • Verify all directories exist after running the setup script.

- [ ] T002 [P] Initialise Python 3.11 environment and generate `requirements.txt` – `requirements.txt`  
  • Must list pinned versions for `rdkit`, `torch` (CPU‑only), `torch‑geometric` (CPU‑only), `scikit‑learn`, `pandas`, `pyyaml`, `psutil`, `pytest`.  
  • Verify `pip install -r requirements.txt` completes without errors.

- [ ] T003 [P] Configure `pyproject.toml` for `ruff` linting and `black` formatting – `pyproject.toml`  
  • CI must run `ruff` with zero warnings.

---

## Phase 2 – Ingestion & Featurization (foundational)

- [ ] T004 [P] Implement configuration utilities – `code/utils/config.py`  
  • Provides path helpers, fixed random seed (`42`), and reads `RUNTIME_LIMIT_SEC` (default 21600 s).  
  • Test `tests/unit/test_config.py` validates seed and limit values.

- [ ] T005 [P] Implement logging utilities with required tags – `code/utils/logging.py`  
  • Writes to `data/logs/ingestion.log` and includes tags `[MISSING_DATA_EXCLUDED]` and `[ERROR_SMILES]`.  
  • Test `tests/unit/test_logging_tags.py` checks for tag presence after processing a mixed CSV.

- [ ] T006 [P] Implement resource monitor – `code/utils/monitor.py`  
  • Enforces runtime ≤ 21600 s and RAM ≤ 4096 MiB, raises `ResourceLimitExceeded` on breach.  
  • Records total runtime and peak memory to `artifacts/reports/runtime_memory.json`.  
  • Tests: `tests/unit/test_monitor_memory_capture.py`, `tests/unit/test_monitor_memory.py`.

- [ ] T006b [P] Implement graph‑size safety logic – `code/utils/graph_safety.py`  
  • Detects molecules with > 200 heavy atoms, truncates or samples to keep memory ≤ 4 GB.  
  • Test `tests/unit/test_graph_safety.py` validates safe handling of a large molecule.

- [ ] T008 [P] Implement SMILES validation & missing‑field exclusion – `code/ingestion/validate.py`  
  • Returns a list of valid records and logs `[ERROR_SMILES]` / `[MISSING_DATA_EXCLUDED]`.  
  • Test `tests/unit/test_validate.py` covers both error cases.

- [ ] T010 [P] Implement featurization (RDKit graph + solvent descriptors) – `code/ingestion/featurize.py`  
  • Calls `graph_safety.py` before building a `torch_geometric.data.Data` object.  
  • Test `tests/unit/test_featurize.py` checks a known SMILES produces expected node/edge shapes and correct solvent features.

- [ ] T015 [P] Create JSON‑L schema for featurized records – `specs/001-predict-molecular-diffusion-coefficie/contracts/dataset.schema.yaml`  
  • Defines required fields per the specification.  
  • Test `tests/contract/test_dataset_schema.py` validates a sample JSON‑L line.

- [ ] T012 [P] Implement full ingestion pipeline – `code/ingestion/ingest.py`  
  • Reads `data/raw/dataset.csv`, runs `validate.py`, featurizes with `featurize.py`, writes `data/processed/featurized_data.jsonl`.  
  • Skips invalid records, logs reasons.  
  • Depends on T006b, T008, T010, T015.  
  • Test `tests/integration/test_ingestion_pipeline.py` confirms only valid records appear in the output.

---

## Phase 3 – Model Training & Baseline Comparison (User Story 2)

- [ ] T016 [P] Implement CPU‑only single‑layer MPNN – `code/models/mpnn.py`  
  • Checks `torch.cuda.is_available()` at import; raises if GPU detected.  
  • Logs “Device: CPU”.  
  • Test `tests/unit/test_mpnn_device.py` asserts CPU‑only behavior.

- [ ] T017 [P] Implement Linear Regression baseline with fingerprints + solvent descriptors – `code/models/baseline.py`  
  • Uses `sklearn.linear_model.LinearRegression`.  
  • Test `tests/unit/test_baseline.py` validates training on a tiny synthetic dataset.

- [ ] T019a [P] Implement 5‑fold CV stratified by solvent type – `code/training/cv_strategy.py`  
  • Raises `ConfigurationError` if dataset < 50 samples (handled by T019b).  
  • Test `tests/unit/test_cv_strategy_strat.py` ensures solvent‑type distribution is preserved.

- [ ] T019b [P] Implement Leave‑One‑Out CV for tiny datasets – `code/training/loo_strategy.py`  
  • Invoked automatically when `cv_strategy` raises `ConfigurationError`.  
  • Test `tests/unit/test_loo_strategy.py` checks correct number of folds.

- [ ] T041 [P] Implement training loop with checkpointing – `code/training/train.py`  
  • Performs CV using the strategy from T019a/T019b, trains both MPNN and baseline, saves models to `artifacts/models/`.  
  • Logs device verification.  
  • Test `tests/integration/test_training_pipeline.py` runs a mini‑dataset through the full loop.

- [ ] T020 [P] Implement evaluation metrics – `code/training/evaluate.py`  
  • Computes Pearson r, RMSE for each fold, aggregates across folds, writes `artifacts/reports/evaluation.json`.  
  • Skips metric generation if `data_source_flag.json` = `"synthetic"` (see T046).  
  • Test `tests/contract/test_evaluation_report.py` validates JSON schema and presence/absence depending on data source.

- [ ] T046 [P] Enforce “no metrics on synthetic data” rule – `code/training/evaluate.py` (extension)  
  • Exits with non‑zero status and message “Scientific metrics suppressed for synthetic data” when synthetic.  
  • Test `tests/integration/test_no_metrics_synthetic.py` confirms the exit code and missing `evaluation.json`.

- [ ] T021 [P] Perform paired statistical test – `code/training/statistics.py` (called by T020)  
  • Executes paired t‑test (or Wilcoxon if normality fails) on per‑sample absolute errors between GNN and baseline.  
  • Adds results to `evaluation.json` under `statistical_test`.  
  • Test `tests/unit/test_statistics.py` checks p‑value computation on a known toy dataset.

---

## Phase 4 – Sensitivity Analysis & Robustness (User Story 3)

- [ ] T024 [P] Define hyperparameter grid – `code/training/sensitivity.py` (part 1)  
  • Grid includes `message_passing_steps ∈ {1,2,3}` and `learning_rate ∈ {0.001,0.01,0.1}`.  
  • Test `tests/unit/test_sensitivity_grid.py` verifies the grid contents.

- [ ] T042 [P] Implement sweep loop – `code/training/sensitivity.py` (part 2)  
  • Retrains models for each grid point, records metrics, writes `artifacts/reports/sensitivity_report.json`.  
  • Test `tests/contract/test_sensitivity_report.py` validates JSON structure.

- [ ] T025a [P] Add solvent‑removal flag to data pipeline – `code/training/ablation_pipeline.py`  
  • When `remove_solvent=True`, drops `solvent_features` before model input.  
  • Test `tests/unit/test_ablation_flag.py` ensures the flag removes solvent descriptors.

- [ ] T025b [P] Execute ablation study – `code/training/ablation_study.py`  
  • Retrains both models without solvent descriptors, computes Δr (full – ablated) for GNN and baseline, writes `artifacts/reports/ablation_report.json`.  
  • Test `tests/contract/test_ablation_report.py` validates required fields.

- [ ] T025c [P] Guard ablation study on synthetic data – `code/training/ablation_gate.py`  
  • Skips ablation when `data_source_flag.json` = `"synthetic"` and logs “Ablation study skipped: synthetic data”.  
  • Test `tests/unit/test_ablation_gate.py` confirms skip behavior.

- [ ] T026 [P] Implement outlier robustness analysis – `code/training/robustness.py`  
  • For datasets ≥ 50 samples uses 5‑fold CV; otherwise LOO.  
  • Computes Pearson r on full set and after removing top 5 % residuals, writes `artifacts/reports/outlier_analysis.json`.  
  • Test `tests/unit/test_outlier_analysis.py` checks both `full_set_r` and `trimmed_set_r` fields.

- [ ] T027 [P] Summarize sensitivity & stability – `artifacts/reports/sensitivity_summary.md`  
  • Aggregates results from sensitivity and ablation reports, declares `stability: stable` if **all** reported r ≥ 0.7, else `unstable`.  
  • Test `tests/contract/test_sensitivity_stability.py` verifies the stability statement and presence of all r values.

---

## Phase 5 – Documentation, Quick‑Start & CI

- [ ] T029 [P] Write user‑facing README with execution instructions – `code/README.md`  
  • Describes required dataset, synthetic fallback, and full pipeline command.

- [ ] T030 [P] Ensure zero `ruff` warnings – (already verified)  
  • Test `tests/unit/test_ruff_clean.py` runs `ruff` and asserts no warnings.

- [ ] T032a [P] Provide quick‑start script that runs the full pipeline on synthetic data – `run_quickstart.py`  
  • Exits with status 0, creates all artifacts except `evaluation.json` (because synthetic).  
  • Test `tests/unit/test_quickstart.py` checks exit code and artifact presence.

- [ ] T035 [P] Record resource summary (runtime & memory) – `artifacts/reports/resource_summary.json` (generated by `monitor.py`)  
  • Test `tests/contract/test_resource_summary.py` ensures numeric `total_seconds` < 21600 and `peak_memory_mb` < 7000.

- [ ] T036 [P] Add contract test for hypothesis status based on Pearson r – `tests/contract/test_pearson_threshold.py`  
  • Loads `evaluation.json` and asserts `hypothesis_status` matches the r‑threshold logic (r > 0.7 → “positive”, r < 0.3 → “null”).

- [ ] T039 [P] Add contract test that the sensitivity summary includes a clear stability statement – `tests/contract/test_sensitivity_stability_report.py`.

- [ ] T040 [P] Add CI workflow that runs the full synthetic pipeline, linting, and all tests – `.github/workflows/ci.yml`  
  • Ensures CI fails on any warning, missing artifact, or test failure.

---

## Phase 6 – Verification & Cleanup

- [ ] T057 [P] Verify error handling when a URL is present but download fails – `code/ingestion/fetch_real.py` (already updated)  
  • Test `tests/unit/test_url_validation.py` confirms proper exception.

- [ ] T047 [P] Register successful real‑data download – `code/ingestion/register_dataset.py` writes `data/verified_datasets.json` and updates `plan.md`.  
  • Test `tests/contract/test_dataset_registry.py` validates JSON fields and plan update.

- [ ] T048 [P] Verify `plan.md` reflects real dataset URL after download – (covered by T000d).

- [ ] T049_test_flag_source_1 [P] Unit test ensuring `data_source_flag.json` records `"real"` correctly – `tests/unit/test_flag_source_real.py`  
  • Checks both branches of the flag logic for the real source.

- [ ] T050_test_flag_source_2 [P] Unit test ensuring `data_source_flag.json` records `"synthetic"` correctly – `tests/unit/test_flag_source_synthetic.py`  
  • Mirrors the above test for the synthetic branch.

- [ ] T051 [P] Ensure all task identifiers are unique and follow the `T###` pattern – (manual audit performed)  
  • No action required in code; verification passes.

---

### Dependencies & Requirement Coverage

| Spec Requirement | Satisfying Task(s) |
|------------------|--------------------|
| FR‑001 | T000b, T012 |
| FR‑002 | T010, T015 |
| FR‑003 | T016, T041 |
| FR‑004 | T019a, T019b |
| FR‑005 | T021, T046 |
| FR‑006 | T025a, T025b, T024, T042 |
| FR‑007 | T008, T005, T006b |
| SC‑001 | T020, T036 |
| SC‑002 | T021, T046 |
| SC‑003 | T004, T006, T035 |
| SC‑004 | T025b, T027 |
| SC‑005 | T006, T035 |
| Edge‑case handling (large molecules, missing data, synthetic fallback) | T006b, T008, T007c, T025c, T046 |

All tasks are ordered to respect data flow: directory creation → raw data acquisition → ingestion → featurization → model training → evaluation → analysis → reporting.
