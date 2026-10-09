---
description: "Task list for Predicting Molecular Reactivity Using Graph Neural Networks and Public Databases"
---

# Tasks: Predicting Molecular Reactivity Using Graph Neural Networks and Public Databases

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, contracts, and the research question.  
**Goal**: Deliver a reproducible, CPU‑first end‑to‑end pipeline that (1) downloads and preprocesses QM9, (2) trains two lightweight GNNs and a Random‑Forest baseline, (3) performs feature‑attribution and external validation, and (4) archives all artifacts for hand‑off.

---


## Phase 0 – Project Setup & Infrastructure

- [ ] T001 [P] **Create core directories**  
  `data/raw`, `data/processed`, `data/assets`, `code`, `artifacts`, `tests` (add a `.gitkeep` in each).  
  **Verification**: `git ls-files` shows the directories and a `.gitkeep` file inside each.

- [ ] T002 [P] **Add configuration & linting files**  
  - `requirements.txt` (pinned versions of `torch`, `rdkit`, `torch-geometric`, `scikit-learn`, `pandas`, `datasets`, `pyyaml`, `requests`, `black`, `ruff`, `pytest`).  
  - `pyproject.toml` (Black config).  
  - `.flake8` and `ruff.toml` (flake8/ruff settings).  
  **Verification**: All four files are present and `pip install -r requirements.txt` succeeds; `ruff check .` and `black --check .` return no errors.

---


## Phase 1 – Data Acquisition & Integrity

- [X] T003 [P] **Define checksum schema**  
  Create `data/raw/checksums_schema.yaml` describing the JSON structure (`file_path`, `sha256`). Also create an empty `data/raw/checksums.json`.  
  **Verification**: Both files are present and `yamllint` passes on the schema.

- [ ] T004 [US1] **Download QM9 subset & record checksum**  
  Stream the QM9 dataset (≈100 k molecules) via `torch_geometric.datasets.QM9` to `data/raw/qm9_subset.parquet`. Compute its SHA‑256 hash and add an entry to `data/raw/checksums.json` per the schema.  
  **Verification**: `data/raw/qm9_subset.parquet` exists, is non‑empty, and the hash in `checksums.json` matches the computed value.

- [ ] T005 [US1] **Curate reference substructures CSV & checksum**  
  Download the curated reference substructures (DOI cited in `spec.md`) to `data/raw/reference_substructures_raw.csv`. Compute its SHA‑256 and record in `checksums.json`.  
  **Verification**: File exists, checksum entry matches, and the CSV has the required columns (`smiles`, `source_doi`, `description`).

- [ ] T006 [US1] **Curate kinetic dataset CSV & checksum**  
  Download the external kinetic dataset (≥20 molecules, DOI cited in `spec.md`) to `data/raw/kinetic_dataset_raw.csv`. Compute its SHA‑256 and add to `checksums.json`.  
  **Verification**: File exists, checksum entry matches, and the CSV contains the required columns (`smiles`, `reaction_rate`, `reaction_type`, `source_doi`).

- [ ] T007 [P] **Validator script & run**  
  Implement `code/utils/validator.py` that reads `checksums.json`, recomputes SHA‑256 for each listed file, and writes a pass/fail report to `artifacts/validation_report.json`. Run it as a CI step.  
  **Verification**: `artifacts/validation_report.json` reports “all files verified”.

---


## Phase 2 – Preprocessing & Dataset Construction

- [ ] T008 [US1] **Preprocess QM9 to graph objects**  
  `code/data/preprocess.py` streams `qm9_subset.parquet`, converts each SMILES to a `torch_geometric.data.Data` object using RDKit (node features: atomic number, hybridization, formal charge, num_neighbors; edge features: bond type, conjugation, in_ring).  
  *Logs*:  
  - `artifacts/exclusion_report.json` (list & count of invalid SMILES; must be < 0.1 % of total).  
  - `artifacts/memory_adjustment.log` (any batch‑size reductions triggered when RAM > 4 GB).  
  *Output*: `data/processed/graphs_intermediate.pt`.  
  **Verification**: All three files exist, exclusion count < 0.1 %, and the intermediate‑graph file can be loaded with `torch.load`.

- [ ] T009 [US1] **Murcko scaffold split & final graph serialization**  
  `code/data/split.py` loads `graphs_intermediate.pt`, performs Murcko scaffold splitting (80 % train + val, 20 % test), writes split index tensors to `data/processed/splits/train_indices.pt`, `val_indices.pt`, `test_indices.pt`, and creates the final dataset `data/processed/graphs.pt` that conforms to `contracts/dataset.schema.yaml`.  
  **Verification**: All four files exist; loading `graphs.pt` yields a list of graph objects each with a `split` field matching the schema.

---


## Phase 3 – Model Implementation & Training

- [ ] T010 [US2] **Model definitions**  
  Add three Python modules under `code/models/`:  
  - `spectral_gnn.py` (lightweight spectral GNN, CPU‑only).  
  - `hetero_gnn.py` (heterophily‑aware GNN based on VR‑GNN principles, CPU‑only).  
  - `rf_baseline.py` (Random Forest on Morgan fingerprints).  
  Each module exports a `train` function and a `predict` function.  
  **Verification**: Files exist and import without error.

- [ ] T011 [US2] **Training, early‑stopping, and evaluation pipeline**  
  `code/train/train_and_evaluate.py` loads `graphs.pt`, trains the two GNNs and the RF baseline with early stopping (patience = 5 on validation loss), monitors RAM (reduces batch size if > 4 GB), saves best weights to `artifacts/models/best_spectral_gnn.pt`, `best_hetero_gnn.pt`, `best_rf.pkl`.  
  After training it:  
  - Generates predictions for the test split and writes `artifacts/predictions.parquet`.  
  - Computes MSE, MAE, Pearson R for each model and writes `artifacts/metrics.json` (conforms to `contracts/metrics.schema.yaml`).  
  - Performs a primary paired t‑test (GNN vs RF) and a Wilcoxon signed‑rank test as sensitivity analysis; results are stored in `artifacts/statistical_tests.json`.  
  **Verification**: All three weight files, `predictions.parquet`, `metrics.json`, and `statistical_tests.json` exist and pass schema validation.

---


## Phase 4 – Interpretability & External Validation

- [ ] T012 [US3] **Feature attribution & alignment scoring**  
  `code/interpret/attribution_and_alignment.py` runs GNNExplainer (or a gradient‑based explainer) on the test set, produces `artifacts/attribution_maps.json adhering to `contracts/attribution.schema.yaml`.  
  It then compares the top‑5 substructures per molecule to the curated reference set (`data/raw/reference_substructures_raw.csv`), computes:  
  - `alignment_score` (mean max Tanimoto similarity),  
  - `recall_at_k`,  
  - `null_model_score`.  
  Results are written to `artifacts/alignment_score.json`. The script asserts `alignment_score ≥ 0.7` (SC‑003).  
  **Verification**: All three files exist; the JSON schema passes; the alignment score meets the threshold.

- [ ] T013 [US3] **Kinetic‑dataset proxy validation**  
  `code/interpret/kinetic_validation.py` loads `data/raw/kinetic_dataset_raw.csv` and the test‑set predictions from `artifacts/predictions.parquet`, computes the Pearson correlation between predicted HOMO‑LUMO gaps and experimental reaction rates, and writes `artifacts/proxy_validation_report.json`.  
  The script fails with a clear error if the kinetic set contains < 20 entries.  
  **Verification**: Report file exists, contains a `correlation_full_dataset` field, and the job exits successfully only when the entry count ≥ 20.

---


## Phase 5 – Archiving, Monitoring & Final Consistency Checks

- [ ] T014 [P] **Archive all research artifacts**  
  `code/utils/archive.py` creates `artifacts/final_archive.tar.gz` containing every file in `artifacts/` (models, metrics, predictions, attribution, alignment, proxy validation, statistical tests, checksum reports). It also writes `artifacts/archive_checksums.json` with SHA‑256 hashes of each archived file.  
  **Verification**: Archive exists, can be extracted, and all listed hashes match.

- [ ] T015 [P] **Single‑Source‑of‑Truth (SSoT) validation**  
  `code/utils/ssot.py` reads the contracts in `specs/.../contracts/`, validates that every artifact (`metrics.json`, `predictions.parquet`, `attribution_maps.json`, etc.) conforms to its JSON schema, and produces `artifacts/ssot_report.json` indicating overall pass/fail.  
  **Verification**: Report exists and reports “PASS”.

- [ ] T017 [P] **Record total pipeline runtime**  
  Wrap the entire end‑to‑end execution (from T004 through T015) with a timing utility that records start and end timestamps, computes total elapsed seconds, and writes `artifacts/runtime_report.json` containing the field `total_seconds`. The task asserts that `total_seconds ≤ 21600` (6 hours).  
  **Verification**: `runtime_report.json` exists and the recorded runtime is ≤ 21600 seconds.

- [ ] T018 [P] **Record peak memory usage**  
  During the full pipeline execution, monitor process memory using `psutil` (or similar), capture the peak resident set size, and write `artifacts/memory_report.json` with the field `peak_mb`. The task asserts that `peak_mb ≤ 4096` (4 GB).  
  **Verification**: `memory_report.json` exists and reports a peak ≤ 4096 MB.

---


## Phase 6 – Tests (optional but recommended for CI)

- [ ] T016 [P] **Unit & integration test suite**  
  Populate `tests/unit/` with tests for each module (model init, preprocessing, split, validator, attribution) and `tests/integration/` with end‑to‑end pipeline tests that run the full workflow on a tiny sample (e.g., first 100 molecules). Ensure `pytest --cov` passes.  
  **Verification**: Test suite runs without failures and coverage ≥ 80 %.

---


## Dependency & Execution Order Summary

| Task | Depends On |
|------|------------|
| T001‑T002 | – |
| T003 | T001‑T002 |
| T004‑T006 | T003 |
| T007 | T004‑T006 |
| T008 | T004, T007 |
| T009 | T008 |
| T010 | – |
| T011 | T009, T010 |
| T012 | T011 |
| T013 | T011 |
| T014 | T012‑T013 |
| T015 | T014 |
| T017 | T014‑T015 |
| T018 | T014‑T015 |
| T016 | T015 (optional) |

---


## Notes

- All scripts run in **CPU‑only** mode (`device='cpu'`). GPU escape is **not** used; memory‑safety logic is explicit.  
- Real data sources are never fabricated; any missing download aborts with a clear error.  
- Checksums are recomputed on every CI run to guarantee data‑hygiene.  
- The pipeline is designed to finish within the GitHub‑Actions free‑tier limits (≤ 6 h runtime, ≤ 4 GB RAM).  

---


*End of `tasks.md`.*  