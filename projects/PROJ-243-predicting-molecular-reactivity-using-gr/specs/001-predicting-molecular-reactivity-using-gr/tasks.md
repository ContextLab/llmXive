---
description: "Task list for Predicting Molecular Reactivity Using Graph Neural Networks and Public Databases"
---

# Tasks: Predicting Molecular Reactivity Using Graph Neural Networks and Public Databases

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, contracts, and the research question.  
**Goal**: Deliver a reproducible, CPU‑first end‑to‑end pipeline that (1) downloads and preprocesses QM9, (2) trains two lightweight GNNs and a Random‑Forest baseline, (3) performs feature‑attribution and external validation, and (4) archives all artifacts for hand‑off.

---

## Phase 0 – Project Setup & Infrastructure

- [ ] T001 [P] **Create core directories**  
  `data/raw`, `data/processed`, `data/assets`, `code`, `artifacts`, `tests` (add a `.gitkeep` in each).  
  **Verification**: `git ls-files` shows the directories and a `.gitkeep` file inside each.

- [ ] T002 [P] **Add linting configuration and run checks**   <!-- FAILED-IN-EXECUTION: code/run_lint_checks.py exit=1 -->
  - Create a `.flake8` file at the repository root with a basic configuration (e.g., `max-line-length = 88`).  
  - Ensure `requirements.txt` pins all required packages, `pyproject.toml` contains Black configuration, and `ruff.toml` contains ruff settings.  
  - Execute `ruff check . --output-format=json > artifacts/ruff_report.json` **and** `black --check . > artifacts/black_report.txt`. Both commands must exit with status 0.  
  **Verification**:  
  1. `.flake8` exists at the repository root.  
  2. `artifacts/ruff_report.json` contains zero violations.  
  3. `artifacts/black_report.txt` reports “All done! ✨” with no formatting differences.

- [ ] T003 [P] **Define empty checksum manifest**  
  - Create `data/raw/checksums.json` containing exactly an empty JSON array: `[]`.  
  - No entries are added at this stage; the file must validate against `contracts/checksums.schema.yaml` (fields `file_path` and `sha256`).  
  **Verification**: JSON‑schema validation passes and the file’s content is `[]`.

- [ ] T004 [US1] **Download QM9 subset & record its checksum**  
  Stream the QM9 dataset (≈100 k molecules) via `torch_geometric.datasets.QM9` to `data/raw/qm9_subset.parquet`. Compute its SHA‑256 hash and **append** an entry to `data/raw/checksums.json` with fields `file_path: "data/raw/qm9_subset.parquet"` and `sha256`.  
  **Verification**: `data/raw/qm9_subset.parquet` exists, is non‑empty, the hash entry matches the computed value, and schema validation succeeds.

- [ ] T005 [US1] **Curate reference substructures CSV & record its checksum**  
  - Place the curated reference substructures (50 rows, columns `smiles,source_doi,description`) at `data/raw/reference_substructures_raw.csv`.  
  - Compute its SHA‑256 hash and **add** a corresponding entry to `data/raw/checksums.json` (`file_path: "data/raw/reference_substructures_raw.csv"`).  
  **Verification**: CSV exists with required columns, checksum entry is present, and `checksums.json` validates against the schema.

- [ ] T006 [US1] **Curate kinetic dataset CSV & record its checksum**  
  - Place the external kinetic dataset (≥20 molecules, columns `smiles,reaction_rate,reaction_type,source_doi`) at `data/raw/kinetic_dataset_raw.csv`.  
  - Compute its SHA‑256 hash and **append** an entry to `data/raw/checksums.json`.  
  **Verification**: CSV exists with required columns, checksum entry is present, and schema validation passes.

- [ ] T007 [P] **Validator script & run**  
  Implement `code/utils/validator.py` that reads `checksums.json`, recomputes SHA‑256 for each listed file, and writes a pass/fail report to `artifacts/validation_report.json`. Run it as a CI step.  
  **Verification**: `artifacts/validation_report.json` reports “all files verified”.

- [ ] T018 [P] **Pin random seeds & verify deterministic execution**  
  Create `code/config.py` that sets fixed seeds for Python `random`, NumPy, and PyTorch (`torch.manual_seed`). Add a small sanity script that generates a reproducible random tensor and writes its value to `artifacts/seed_check.txt`. Verify that re‑running the script produces the same value.  
  **Verification**: `artifacts/seed_check.txt` contains the same number on consecutive runs.

---

## Phase 1 – Data Acquisition & Integrity (Preprocessing)

- [ ] T008 [US1] **Preprocess QM9 to graph objects**  
  `code/data/preprocess.py` streams `qm9_subset.parquet`, converts each SMILES to a `torch_geometric.data.Data` object using RDKit (node features: atomic number, hybridization, formal charge, num_neighbors; edge features: bond type, conjugation, in_ring).  
  - Generates `artifacts/exclusion_report.json` (invalid SMILES < 0.1 % of total).  
  - Generates `artifacts/memory_adjustment.log` (any batch‑size reductions when RAM > 4 GB).  
  - Outputs `data/processed/graphs_intermediate.pt`.  
  **Verification**: Files exist, exclusion count < 0.1 %, and the intermediate file loads with `torch.load`.

- [ ] T009 [US1] **Murcko scaffold split & final graph serialization**  
  `code/data/split.py` loads `graphs_intermediate.pt`, performs Murcko scaffold splitting (80 % train + val, 20 % test), writes split index tensors to `data/processed/splits/train_indices.pt`, `val_indices.pt`, `test_indices.pt`, and creates the final dataset `data/processed/graphs.pt` that conforms to `contracts/dataset.schema.yaml`.  
  **Verification**: All four files exist; loading `graphs.pt` yields graph objects each with a valid `split` field; schema validation passes.

---

## Phase 2 – Model Implementation & Training

- [ ] T010 [US2] **Model definitions**  
  Add three modules under `code/models/`:  
  - `spectral_gnn.py` (lightweight spectral GNN, CPU‑only).  
  - `hetero_gnn.py` (heterophily‑aware GNN based on VR‑GNN, CPU‑only).  
  - `rf_baseline.py` (Random Forest on Morgan fingerprints).  
  Each module exports a `train` function and a `predict` function.  
  **Verification**: Files import without error (`python -c "import code.models.spectral_gnn"` etc.).

- [ ] T027 [US2] **Shared hyper‑parameter grid search**  
  Perform a **grid search** over learning rate ∈ {1e‑3,5e‑4} and hidden dimension ∈ {64,128} using 5‑fold cross‑validation on the training split. Select the best configuration (based on validation MAE) and write the chosen values to `code/config.py` so that all three models use identical hyper‑parameters and comparable training budgets.  
  **Verification**: `code/config.py` contains `LEARNING_RATE` and `HIDDEN_DIM` fields matching the selected best config; a log `artifacts/hyperparam_search.log` records the search results.

- [ ] T011‑a [US2] **Train Spectral GNN**  
  `code/train/train_spectral.py` loads `graphs.pt`, trains the Spectral GNN with early stopping (patience = 5), monitors RAM (reduces batch size if > 4 GB), and saves best weights to `artifacts/models/best_spectral_gnn.pt`.  
  **Verification**: Checkpoint file exists and training log records early‑stopping event.

- [ ] T011‑b [US2] **Train Heterophily‑aware GNN**  
  `code/train/train_hetero.py` performs analogous training for the heterophily‑aware model, saving to `artifacts/models/best_hetero_gnn.pt`.  
  **Verification**: Checkpoint file exists and early‑stopping log present.

- [ ] T011‑c [US2] **Train Random Forest baseline**  
  `code/train/train_rf.py` computes Morgan fingerprints (radius 2, nBits = 2048) from the training split, trains a Random Forest with early stopping on validation MAE, and saves the model to `artifacts/models/best_rf.pkl`.  
  **Verification**: Model file exists and validation MAE improvement log is present.

- [ ] T011‑d [US2] **Generate predictions for test set**  
  `code/train/predict_test.py` loads the three trained models, runs inference on the test split, and writes `artifacts/predictions.json` conforming to `contracts/model-output.schema.yaml`.  
  **Verification**: Prediction file exists and schema validation passes.

- [ ] T011‑e [US2] **Compute evaluation metrics**  
  `code/eval/compute_metrics.py` reads `artifacts/predictions.json`, calculates MSE, MAE, and Pearson R for each model, and writes `artifacts/metrics.json` (conforms to `contracts/metrics.schema.yaml`).  
  **Verification**: Metrics file exists and schema validation passes.

- [ ] T011‑f [US2] **Run statistical tests**  
  `code/eval/run_stats.py` performs a paired t‑test (GNN vs RF) and a Fisher‑Z test on Pearson R, applies Bonferroni correction (α = 0.05), and appends the results to `artifacts/metrics.json` under `statistical_tests`.  
  **Verification**: Statistical test entries are present with `p_value`, `is_significant`, and `alpha_adjusted` fields.

---

## Phase 3 – Interpretability & External Validation

- [ ] T012 [US3] **Feature attribution & alignment scoring**  
  `code/interpret/attribution_and_alignment.py` runs GNNExplainer on a random 100‑molecule subset of the test set, outputs `artifacts/attribution_maps.json` (conforms to `contracts/attribution.schema.yaml`).  
  - Compares top‑5 substructures per molecule to `data/raw/reference_substructures_raw.csv`, computes:  
    * `alignment_score` (mean‑max Tanimoto similarity),  
    * `recall_at_k`,  
    * `null_model_score`.  
  - Writes `artifacts/alignment_score.json` and asserts `alignment_score ≥ 0.7`.  
  **Verification**: Files exist, schema validation passes, and the alignment threshold is met.

- [ ] T013 [US3] **Kinetic‑dataset proxy validation**  
  `code/interpret/kinetic_validation.py` loads `data/raw/kinetic_dataset_raw.csv` and test‑set predictions from `artifacts/predictions.json`, computes Pearson correlation between predicted HOMO‑LUMO gaps and experimental reaction rates, and writes `artifacts/kinetic_correlation_report.json`.  
  - Fails with a clear error if the kinetic set contains < 20 entries.  
  **Verification**: Report file exists, contains a `correlation` field, and the script exits successfully only when entry count ≥ 20.

---

## Phase 4 – Archiving, Consistency & Resource Monitoring

- [ ] T014 [P] **Archive all research artifacts**  
  `code/utils/archive.py` creates `artifacts/final_archive.tar.gz` containing every file in `artifacts/` (models, metrics, predictions, attribution, alignment, proxy validation, statistical tests, checksum reports). It also writes `artifacts/archive_checksums.json` with SHA‑256 hashes of each archived file.  
  **Verification**: Archive extracts correctly and all listed hashes match.

- [ ] T015 [P] **Single‑Source‑of‑Truth (SSoT) validation**  
  `code/utils/ssot.py` reads all contracts under `specs/.../contracts/`, validates that each artifact (`metrics.json`, `predictions.json`, `attribution_maps.json`, etc.) conforms to its JSON schema, and produces `artifacts/ssot_report.json` indicating overall PASS/FAIL.  
  **Verification**: Report exists and reports “PASS”.

- [ ] T016 [P] **Runtime & memory monitoring**  
  Wrap the full pipeline (from T004 through T015) with a timing utility (`code/utils/timer.py`) that records start/end timestamps and peak resident memory (using `psutil`).  
  - Write `artifacts/runtime_report.json` containing `total_seconds` (assert ≤ 21600).  
  - Write `artifacts/memory_report.json` containing `peak_mb` (assert ≤ 4096).  
  **Verification**: Both JSON files exist and the recorded values satisfy the limits.

- [ ] T017 [P] **Unit & integration test suite**  
  Populate `tests/unit/` with tests for each module (model init, preprocessing, split, validator, attribution) and `tests/integration/` with an end‑to‑end test that runs the full workflow on a tiny sample (first 100 molecules).  
  - Run `pytest --cov > artifacts/coverage_report.txt` and require coverage ≥ 80 % and no failures.  
  **Verification**: Test suite executes, `artifacts/coverage_report.txt` exists with coverage ≥ 80 %, and CI passes.

---

## Dependency & Execution Order Summary

| Task   | Depends On |
|--------|------------|
| T001   | – |
| T002   | T001 |
| T003   | T001 |
| T004   | T003 |
| T005   | T003 |
| T006   | T003 |
| T007   | T004‑T006 |
| T008   | T004, T007 |
| T009   | T008 |
| T010   | – |
| T018   | T002 |
| T027   | T010, T009 |
| T011‑a | T009, T010, T027 |
| T011‑b | T009, T010, T027 |
| T011‑c | T009, T010, T027 |
| T011‑d | T011‑a, T011‑b, T011‑c |
| T011‑e | T011‑d |
| T011‑f | T011‑e |
| T012   | T011‑f |
| T013   | T011‑f |
| T014   | T012‑T013 |
| T015   | T014 |
| T016   | T014‑T015 |
| T017   | T015 |

--- 

*End of `tasks.md`.* 