# Tasks: Predicting Molecular Descriptors from Quantum Chemical Calculations with Machine Learning

**Inputs**: `spec.md`, `plan.md`, existing data‑model contracts, and reviewer feedback.  
**Goal**: End‑to‑end pipeline that (1) downloads a verified QM9 subset, (2) extracts 2D Morgan fingerprints and 3D graph features, (3) trains separate Random‑Forest regressors with 5‑fold CV on a CPU‑only runner, (4) computes comparative statistics and the “failure boundary”, and (5) produces a reproducible report and run‑book.  

All tasks are written in the canonical checklist format. Tasks marked **[P]** can run in parallel because they touch disjoint files. Story labels (US1‑US3) map to the three user stories in the specification.

---  

## Phase 1 – Project scaffolding & tooling  

- [ ] **T001** [US0] Create the required directory tree.  
  `code/`, `utils/`, `data/raw/`, `data/processed/`, `data/results/`, `tests/`, `docs/`  
  *Verification*: `ls -R` shows all directories; each empty directory contains a `.gitkeep` file.

- [ ] **T002** [US0] Create a fully‑pinned `requirements.txt`.  
  ```text
  rdkit==2024.3.2
  scikit-learn==1.5.0
  pandas==2.2.0
  numpy==1.26.0
  pyarrow==15.0.0
  tqdm==4.66.2
  huggingface_hub==0.23.0
  matplotlib==3.9.0
  seaborn==0.13.0
  scipy==1.13.0
  ```  
  *Verification*: file exists and each line matches the pattern `package==version`; `pip install -r requirements.txt` succeeds in a fresh venv.

- [ ] **T003** [US0] Configure linting/formatting tools.   <!-- FAILED-IN-EXECUTION: code/run_lint.py exit=1 -->
  - Create `ruff.toml` with the default rule set.  
  - Create `pyproject.toml` with `[tool.black] line-length = 88`.  
  *Verification*: `ruff check .` and `black --check .` both exit with code 0; their stdout is saved to `artifacts/metrics/lint_report.txt`.

---  

## Phase 2 – Data acquisition & preprocessing  

- [ ] **T004** [US1] Implement `utils/memory_monitor.py`.  
  Provides `monitor_memory(threshold_gb: float) -> None` that raises `MemoryError` when `tracemalloc` reports > threshold.  
  *Verification*: unit test `tests/test_memory_monitor.py` mocks a 6.6 GB usage and asserts that `MemoryError` is raised; test passes.

- [ ] **T005** [US1] Implement `utils/parsers.py`.  
  Functions:  
  • `xyz_to_molecule(xyz_path: str) -> Molecule` – parses XYZ, validates atom count ≤ 100.  
  • `smiles_to_mol(smiles: str) -> rdkit.Chem.Mol` – validates canonical SMILES.  
  Includes robust error handling (raises `ValueError` on malformed input).  
  *Verification*: `tests/test_parsers.py` checks successful parsing of a known XYZ file and proper exception on a corrupted file; all tests pass.

- [ ] **T006** [US1] Download QM9 from a verified HuggingFace mirror.  
  Script: `code/download_data.py` uses `datasets.load_dataset("qm9", split="train", streaming=False)` and writes the full parquet to `data/raw/qm9_full.parquet`.  
  *Verification*: file exists, size > 1 GB, and a schema validation against `specs/001-predicting-molecular-descriptors-from-qu/contracts/dataset.schema.yaml` succeeds (script prints “SCHEMA OK”).

- [ ] **T007** [US1] Clean and filter the raw dataset.  
  Script: `code/clean_data.py` loads `data/raw/qm9_full.parquet`, drops rows with missing `mu`, `homo`, `lumo`, or `valid == False`, and removes molecules with > 100 atoms. Output: `data/processed/molecules_cleaned.parquet`.  
  *Verification*: row count printed, and a quick‑check `pandas.read_parquet(...).shape[0]` matches the logged count; schema matches `specs/001-predicting-molecular-descriptors-from-qu/contracts/dataset_schema.schema.yaml`.

- [ ] **T008** [US1] Stratified random sampling respecting memory limits.  
  Script: `code/sample_data.py` reads the cleaned parquet, stratifies on `atom_count` and absolute dipole magnitude, and iteratively grows the subset until `utils.memory_monitor.monitor_memory(6.5)` would be exceeded. Final subset saved to `data/processed/qm9_subset.parquet`; the selected indices are stored in `data/processed/subset_indices.json`.  
  *Verification*: a log `artifacts/metrics/sampling_log.json` records `subset_size`, `peak_memory_gb`, and KS‑test D‑values < 0.05 for both strata; the file exists and is valid JSON.

- [ ] **T016** [US1] Validate all data‑model contracts.  
  Script: `code/validate_contracts.py` loads each contract YAML (`dataset.schema.yaml`, `dataset_schema.schema.yaml`, `feature_set.schema.yaml`, `evaluation_result.schema.yaml`, etc.) and validates the corresponding Parquet/JSON artifacts using `jsonschema`.  
  *Verification*: script prints “ALL SCHEMAS VALID” and writes `artifacts/metrics/contract_validation.json`; unit test confirms validation passes on the current pipeline outputs.

---  

## Phase 3 – Feature extraction  

- [ ] **T009** [US1] Generate 2D Morgan fingerprints and 3D graph features.  
  Script: `code/extract_features.py` reads `data/processed/qm9_subset.parquet`.  
  • 2D: `rdkit.Chem.AllChem.GetMorganFingerprintAsBitVect(mol, radius=2, nBits=2048)` → saved as `data/processed/features_2d.npy`.  
  • 3D: builds a fixed‑size NumPy structured array (`max_atoms=100`) with fields `atom_num`, `hybridization`, `distances`, `angles`, `dihedrals`; saved as `data/processed/features_3d.npy`.  
  Labels (`mu`, `homo`, `lumo`) are saved to `data/processed/labels.npy`.  
  *Verification*: shapes printed (`(N, 2048)` for 2D, `(N,)` for 3D with dtype check), and a checksum file `artifacts/metrics/feature_checksum.txt` is written.

- [ ] **T017** [US1] Generate SHA‑256 checksums for raw and processed data files.  
  Script: `utils/checksums.py` computes checksums for `data/raw/qm9_full.parquet`, `data/processed/qm9_subset.parquet`, `features_2d.npy`, `features_3d.npy`, `labels.npy` and writes them to `artifacts/metrics/checksums.json`.  
  *Verification*: unit test `tests/test_checksums.py` verifies that the recorded hashes match the files on disk.

---  

## Phase 4 – Model training & CV  

- [ ] **T010** [US2] Train Random Forest regressors with 5‑fold CV.  
  Script: `code/train_models.py` loads the two feature matrices and `labels.npy`, runs `sklearn.model_selection.StratifiedKFold` (stratified by quantiles of the target) for each descriptor (`mu`, `homo`, `lumo`). Hyper‑parameter grid: `n_estimators ∈ {100, 500}`, `max_depth ∈ {10, 20, None}`.  
  Saves:  
  • Models → `artifacts/models/model_2d_mu.pkl`, `model_3d_mu.pkl`, … (one per descriptor).  
  • Per‑fold metrics → `artifacts/metrics/cv_2d.json`, `artifacts/metrics/cv_3d.json`.  
  *Verification*: each JSON contains `fold_mae`, `fold_rmse`, `mean_mae`, `mean_rmse`, `std_mae`; total runtime logged (`runtime_seconds`) and asserted ≤ 6 h.

- [ ] **T011** [US2] Aggregate CV results & enforce stability.  
  Script: `code/aggregate_metrics.py` reads the two CV JSON files, computes the stability ratio `std_mae / mean_mae` for every descriptor. If any ratio > 0.05 the script exits with code 1 and writes `artifacts/metrics/stability_failure.json` describing the offending metric. Otherwise it writes `artifacts/metrics/cv_aggregated.json` containing the combined table.  
  *Verification*: a unit test `tests/test_aggregate_metrics.py` feeds a synthetic high‑variance JSON and asserts the process exits with code 1 and the failure file exists; another test confirms successful aggregation when ratios are ≤ 0.05.

---  

## Phase 5 – Comparative analysis & reporting  

- [ ] **T012** [US3] Full analysis, statistical testing, and report generation.  
  Script: `code/analyze_results.py` performs the following steps (in order):  
  1. **Baseline** – computes mean‑predictor MAE and a theoretical lower bound (standard deviation of the labels) → `artifacts/metrics/baseline.json`.  
  2. **Predictions** – loads both trained models, predicts on the held‑out test split (indices from `subset_indices.json`), stores per‑molecule absolute errors in `artifacts/metrics/predictions.json`.  
  3. **Statistical tests** – for each descriptor runs Shapiro‑Wilk; if *p* < 0.05 uses Wilcoxon signed‑rank, else paired *t*‑test. Applies Bonferroni correction (α = 0.0167). Results saved to `artifacts/metrics/statistics.json`.  
  4. **Relative Error Increase (REI)** – computes `(MAE_2D – MAE_3D) / MAE_3D` per descriptor → `artifacts/metrics/rei.json`.  
  5. **Failure boundary** – declares a descriptor to have failed the 2D approximation when `REI ≥ 0.10` **AND** `p < 0.0167`. Saves `artifacts/metrics/failure_boundary.json`.  
  6. **Plots** – generates parity plots (`predicted vs. DFT`) for each descriptor and representation, saved as `artifacts/plots/parity_mu_2d.png`, etc.  
  7. **Report** – compiles a markdown summary (`artifacts/report.md`) containing tables of metrics, REI values, statistical conclusions, and embedded plot images.  
  *Verification*: a test `tests/test_analysis.py` loads the final JSON files and asserts that for at least one descriptor the failure condition is evaluated correctly; also checks that `report.md` exists and contains the heading “## Failure Boundary”.

---  

## Phase 6 – Documentation, validation, and integration testing  

- [ ] **T013** [US3] Write `docs/quickstart.md`.  
  Provides a five‑step CLI guide: (1) `pip install -r requirements.txt`, (2) `python code/download_data.py`, (3) `python code/clean_data.py`, (4) `python code/sample_data.py`, (5) `python code/extract_features.py && python code/train_models.py && python code/analyze_results.py`.  
  *Verification*: the markdown file is present and a CI step runs the commands on a tiny cached subset (see T017) without error.

- [ ] **T014** [US3] Implement `scripts/runbook_validator.py`.  
  Parses `docs/quickstart.md`, extracts all `python …` commands, checks that each referenced script exists and is executable. Writes `artifacts/metrics/runbook_validation.json` with `status: "pass"` or a list of missing files.  
  *Verification*: running the validator returns exit code 0 and the JSON shows `"status": "pass"`.

- [ ] **T015** [US3] Add an end‑to‑end integration test.  
  File: `tests/integration/test_full_pipeline.py`. Uses a pre‑generated tiny QM9 slice (`data/raw/qm9_small.parquet`) bundled in the repo to run the whole pipeline (download step is skipped). After execution it asserts that the following artifacts exist and are non‑empty: `features_2d.npy`, `features_3d.npy`, `model_2d_mu.pkl`, `model_3d_mu.pkl`, `cv_aggregated.json`, `failure_boundary.json`, `report.md`.  
  *Verification*: `pytest -q tests/integration/test_full_pipeline.py` exits with code 0.

- [ ] **T018** [US0] Pin random seeds globally for reproducibility.  
  Add a `utils/random_seed.py` exposing `set_global_seed(seed: int = 42)` which sets `numpy.random.seed`, `random.seed`, and `torch.manual_seed` (if torch is imported). All scripts import and call this at start.  
  *Verification*: `tests/test_seed_reproducibility.py` runs two independent executions of `code/extract_features.py` and asserts identical output hashes.

---  

## Dependencies & execution order  

| ID   | Depends on                                   |
|------|----------------------------------------------|
| T001 | –                                            |
| T002 | T001                                          |
| T003 | T001                                          |
| T004 | T001                                          |
| T005 | T001                                          |
| T006 | T002, T003, T004, T005                       |
| T007 | T006                                          |
| T008 | T007                                          |
| T016 | T008                                          |
| T009 | T008                                          |
| T017 | T009                                          |
| T010 | T009                                          |
| T011 | T010                                          |
| T012 | T011                                          |
| T013 | T010, T012 (to reference generated scripts) |
| T014 | T013                                          |
| T015 | T012, T013, T014                             |
| T018 | All script tasks (T004–T012)                 |

All tasks are unchecked (`[ ]`) because the project is being re‑planned; they can be checked off as implementation proceeds. The list respects the scientific requirements (FR‑001 – FR‑007, SC‑001 – SC‑005) and ensures a deterministic, reproducible, and verifiable end‑to‑end study.  