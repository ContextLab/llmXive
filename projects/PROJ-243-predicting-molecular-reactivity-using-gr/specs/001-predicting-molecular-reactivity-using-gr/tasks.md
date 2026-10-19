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

- [ ] T002 [P] **Add configuration & linting files & run checks**  
  - `requirements.txt` (pinned versions of `torch`, `rdkit`, `torch-geometric`, `scikit-learn`, `pandas`, `datasets`, `pyyaml`, `requests`, `black`, `ruff`, `pytest`).  
  - `pyproject.toml` (Black configuration).  
  - `.flake8` (basic flake8 config).  
  - `ruff.toml` (ruff configuration).  
  - Execute `ruff check . --output-format=json > artifacts/ruff_report.json` **and** `black --check . > artifacts/black_report.txt`. Both commands must exit with status 0.  
  **Verification**: Files exist, `pip install -r requirements.txt` succeeds, and both reports contain no errors.

---

## Phase 1 – Data Acquisition & Integrity

- [ ] T003 [P] **Define checksum schema & initialise empty checksum manifest**  
  - Create `data/raw/checksums_schema.yaml` matching `contracts/checksums.schema.yaml`.  
  - Create an **empty** `data/raw/checksums.json` containing `[]` (exact empty array).  
  **Verification**: JSON schema validation against `contracts/checksums.schema.yaml` passes and the file is empty.

- [ ] T004 [US1] **Download QM9 subset & record its checksum**  
  Stream the QM9 dataset (≈100 k molecules) via `torch_geometric.datasets.QM9` to `data/raw/qm9_subset.parquet`. Compute its SHA‑256 hash and **append** an entry to `data/raw/checksums.json` with fields `file_path` and `sha256`.  
  **Verification**: `data/raw/qm9_subset.parquet` exists, is non‑empty, and the hash entry matches the computed value; schema validation succeeds.

- [ ] T005 [US1] **Curate reference substructures CSV & record its checksum**  
  - Download the curated reference substructures (50 rows) to `data/raw/reference_substructures_raw.csv`.  
  - Compute its SHA‑256 hash and **add** a corresponding entry to `data/raw/checksums.json` (`file_path: "data/raw/reference_substructures_raw.csv"`).  
  **Verification**: CSV exists with required columns (`smiles,source_doi,description`) and its checksum entry is present and schema‑valid.

- [ ] T006 [US1] **Curate kinetic dataset CSV & record its checksum**  
  - Download the external kinetic dataset (≥20 molecules) to `data/raw/kinetic_dataset_raw.csv`.  
  - Compute SHA‑256 and append entry to `data/raw/checksums.json`.  
  **Verification**: CSV exists with required columns (`smiles,reaction_rate,reaction_type,source_doi`) and checksum entry is present; schema validation passes.

- [ ] T007 [P] **Validator script & run**  
  Implement `code/utils/validator.py` that reads `checksums.json`, recomputes SHA‑256 for each listed file, and writes a pass/fail report to `artifacts/validation_report.json`. Run it as a CI step.  
  **Verification**: `artifacts/validation_report.json` reports “all files verified”.

---

## Phase 2 – Preprocessing & Dataset Construction

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

## Phase 3 – Model Implementation & Training

- [ ] T010 [US2] **Model definitions**  
  Add three modules under `code/models/`:  
  - `spectral_gnn.py` (lightweight spectral GNN, CPU‑only).  
  - `hetero_gnn.py` (heterophily‑aware GNN based on VR‑GNN, CPU‑only).  
  - `rf_baseline.py` (Random Forest on Morgan fingerprints).  
  Each module exports a `train` function and a `predict` function.  
  **Verification**: Files import without error.

- [ ] T011 [US2] **Training, early‑stopping, evaluation & statistical testing**  
  `code/train/train_and_evaluate.py` loads `graphs.pt`, trains the two GNNs and the RF baseline with early stopping (patience = 5 on validation loss), monitors RAM (reduces batch size if > 4 GB), and saves best weights to `artifacts/models/best_spectral_gnn.pt`, `best_hetero_gnn.pt`, `best_rf.pkl`.  
  - Generates predictions for the test split (`artifacts/predictions.json` conforming to `contracts/model-output.schema.yaml`).  
  - Computes MSE, MAE, Pearson R for each model and writes `artifacts/metrics.json` (conforms to `contracts/metrics.schema.yaml`).  
  - Performs a paired t‑test (GNN vs RF) and a Fisher‑Z test on Pearson R, stores results in `artifacts/metrics.json` under `statistical_tests`.  
  **Verification**: All model checkpoints, prediction file, and metrics file exist and pass schema validation; statistical‑test p‑values are recorded.

---

## Phase 4 – Interpretability & External Validation

- [ ] T012 [US3] **Feature attribution & alignment scoring**  
  `code/interpret/attribution_and_alignment.py` runs GNNExplainer on a random 100‑molecule subset of the test set, outputs `artifacts/attribution_maps.json` (conforms to `contracts/attribution.schema.yaml`).  
  - Compares top‑5 substructures per molecule to `data/raw/reference_substructures_raw.csv`, computes:  
    * `alignment_score` (mean‑max Tanimoto similarity),  
    * `recall_at_k`,  
    * `null_model_score`.  
  - Writes `artifacts/alignment_score.json` and asserts `alignment_score ≥ 0.7`.  
  **Verification**: Files exist, schema validation passes, and the alignment score meets the threshold.

- [ ] T013 [US3] **Kinetic‑dataset proxy validation**  
  `code/interpret/kinetic_validation.py` loads `data/raw/kinetic_dataset_raw.csv` and test‑set predictions from `artifacts/predictions.json`, computes Pearson correlation between predicted HOMO‑LUMO gaps and experimental reaction rates, and writes `artifacts/kinetic_correlation_report.json`.  
  - Fails with a clear error if the kinetic set contains < 20 entries.  
  **Verification**: Report file exists, contains a `correlation` field, and the script exits successfully only when entry count ≥ 20.

---

## Phase 5 – Archiving, Consistency & Resource Monitoring

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
  - Run `pytest --cov` and require ≥ 80 % coverage and no failures.  
  **Verification**: Test suite executes, coverage report is ≥ 80 %, and CI passes.

---

## Dependency & Execution Order Summary

| Task | Depends On |
|------|------------|
| T001 | – |
| T002 | T001 |
| T003 | T001 |
| T004 | T003 |
| T005 | T003 |
| T006 | T003 |
| T007 | T004‑T006 |
| T008 | T004, T007 |
| T009 | T008 |
| T010 | – |
| T011 | T009, T010 |
| T012 | T011 |
| T013 | T011 |
| T014 | T012‑T013 |
| T015 | T014 |
| T016 | T014‑T015 |
| T017 | T015 |

---


*End of `tasks.md`.*
