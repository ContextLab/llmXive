# Tasks: Predicting Molecular Properties from Vibrational Spectra with Deep Learning  

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, contract schemas, and any existing artifacts.  

The goal is to deliver a fully reproducible CPU‑only pipeline that (1) downloads real QM9 and IR‑spectra datasets, (2) aligns and preprocesses them, (3) trains a 1‑D CNN, (4) evaluates with rigorous statistics, (5) validates on an independent dataset, and (6) provides complete verification artifacts. All tasks respect data flow, use only real data, and generate the required files under the project‑owned directories (`code/`, `data/`, `models/`, `results/`, `logs/`, `specs/`).  

## Phase 1 – Project scaffolding, data ingestion & preprocessing  

- [X] T001 [P] **Create project skeleton** – create the canonical directory tree (`code/`, `code/data/`, `code/models/`, `code/evaluation/`, `code/utils/`, `tests/`, `data/raw/`, `data/processed/`, `data/external/`, `results/`, `logs/`, `specs/001-predict-molecular-properties/`) and empty `__init__.py` files.  
  *Verification*: `python -m compileall code/` exits 0 and `find . -type d | sort > results/structure_report.txt`; the report must list all expected directories.  

- [X] T002 [P] **Materialize contract schemas** – copy the three YAML schema files to the spec folder:  
  - `specs/001-predict-molecular-properties/contracts/dataset.schema.yaml`  
  - `specs/001-predict-molecular-properties/contracts/model_output.schema.yaml`  
  - `specs/001-predict-molecular-properties/contracts/evaluation_results.schema.yaml`  
  *Verification*: `python -c "import yaml, glob; [yaml.safe_load(open(f)) for f in glob.glob('specs/001-predict-molecular-properties/contracts/*.yaml')]"` exits 0 and each file is non‑empty.  

- [ ] T003 [US1] **Download QM9 properties and IR‑spectra, verify integrity, fast‑failure on corruption** – implement `code/data/download.py` to:   <!-- FAILED-IN-EXECUTION: code/main.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/data/download.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/main.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/main.py exit=1 -->
  1. Load QM9 via `datasets.load_dataset('lisn519010/QM9', split='train', data_dir='data/raw')` → `data/raw/qm9.parquet`.  
  2. Load IR‑spectra via `datasets.load_dataset('lamblador/QM9-IR', split='train', data_dir='data/raw')` → `data/raw/ir_spectra.parquet`.  
  3. Compute SHA‑256 checksums for both files and compare against known values (recorded in `results/checksums.json`).  
  4. Abort with a clear error message and non‑zero exit code if a file is missing, corrupted, or checksum mismatches.  
  *Artifacts*: `data/raw/qm9.parquet`, `data/raw/ir_spectra.parquet`, `results/checksums.json`.  
  *Verification*: `code/data/download.py` exits 0, `results/checksums.json` contains `"status": "ok"`.  

- [ ] T004 [US1] **Align datasets on InChIKey and discard mismatches** – `code/data/align.py` reads the two parquet files, performs an inner join on `InChIKey`, logs the number of matched and discarded molecules, and writes `data/processed/alignment_report.json`.   <!-- FAILED-IN-EXECUTION: code/data/align.py exit=1 -->
  *Artifacts*: `data/processed/alignment_report.json` (fields: `matched`, `discarded`).  
  *Verification*: `alignment_report.json` exists, `matched >= 129000`, and the script exits 0.  

- [ ] T005 [US1] **Preprocess spectra and filter missing target properties** – `code/data/preprocess.py` for each matched molecule:  
  1. Interpolate intensity onto a uniform 400–4000 cm⁻¹ grid (1 cm⁻¹ step → 3601 points).  
  2. Apply Gaussian smoothing (`sigma = 2 cm⁻¹`).  
  3. Normalize to unit area (tolerance ± 1e‑6).  
  4. Convert dipole (Debye), polarizability (Å³), and gap (eV) to required units.  
  5. Drop any molecule missing any of the three targets.  
  Saves `data/processed/aligned_dataset.npz` containing arrays `spectra`, `dipole`, `polarizability`, `gap`, `InChIKeys`, and a placeholder `selection_bias_stats`.  
  *Verification*: loading the NPZ yields `spectra.shape == (N,1,3601)`, `np.allclose(spectra.sum(axis=2), 1.0, atol=1e-6)`, no NaNs in target arrays, and the file size < 1 GB.  

- [ ] T006 [US1] **Selection‑bias audit (KS test) and optional weighting** – `code/data/bias_audit.py` runs a two‑sample Kolmogorov–Smirnov test comparing the distribution of each target property in the aligned subset vs. the full QM9 set, stores `statistic` and `p_value` for each property in `data/processed/aligned_dataset.npz` under `selection_bias_stats`. If any p‑value < 0.05, compute inverse‑probability weights and save a weighted training mask `data/processed/weight_mask.npy`.  
  *Verification*: `selection_bias_stats` fields are present and match the values printed to console; `weight_mask.npy` exists only when bias is detected.  

## Phase 2 – Model training, evaluation & independent validation  

- [ ] T007 [US2] **Train 1‑D CNN with early stopping and NaN‑loss detection** – `code/models/trainer.py` loads the training split of `aligned_dataset.npz`, builds the architecture defined in `code/models/cnn_1d.py` (three conv blocks, three regression heads), trains with Adam (lr = 1e‑3), batch size = 64, early stopping (patience = 10, max epochs = 50) on a CPU‑only runner. The loop monitors loss; if any loss becomes NaN, it aborts, logs `"Training Failed"` and exits non‑zero.  
  *Artifacts*: `models/checkpoint_best.pt`, TensorBoard logs under `runs/training/`, `logs/training.log` (empty if training succeeds, contains error otherwise).  
  *Verification*: after successful run, `checkpoint_best.pt` exists, `torch.load` succeeds, `epoch <= 50`, and `logs/training.log` contains the phrase `"Early stopping triggered"` (or is empty on success).  

- [ ] T008 [US3] **Evaluate on held‑out test set with full statistical suite** – `code/evaluation/evaluate.py` loads `checkpoint_best.pt`, runs inference on the test split, computes per‑property MAE, R², paired‑sample t‑test (null = mean = 0) with Bonferroni‑adjusted α ≈ 0.0033, Two‑One‑Sided Tests (TOST) using equivalence bounds (dipole ± 0.05 D, polarizability ± 0.10 Å³, gap ± 0.05 eV), and Hotelling’s T² (multivariate normality checked via Mardia’s test; fallback to 10 000‑permutation test). Saves `results/evaluation_metrics.json` (conforms to `contracts/evaluation_results.schema.yaml`) and `results/predictions_test.npz`.  
  *Verification*: `code/evaluation/check_metrics.py results/evaluation_metrics.json` exits 0; the JSON contains all required fields and each paired‑sample t‑test p‑value < 0.0033.  

- [ ] T009 [US4] **Independent validation on external dataset** – `code/evaluation/validate.py` checks for the presence of `data/external/validation.parquet` (or a HuggingFace dataset `lamblador/QM9-B3LYP`). It aligns on `InChIKey`, applies the same preprocessing pipeline, runs inference with the best checkpoint, computes MAE and R² for each property, and adds a boolean flag `mae_increase_flag` that is true if any property’s MAE exceeds the internal test‑set MAE by > 20 %. Saves `results/validation_metrics.json` (same schema as evaluation, but only MAE/R² plus the flag).  
  *Verification*: script exits 0, the JSON includes `"mae_increase_flag": true/false`, and the file size < 200 KB.  

## Phase 3 – Verification, profiling, state bookkeeping & reproducible handoff  

- [ ] T010 [P] **Run full pytest suite** – execute `pytest -q tests/` and capture stdout/stderr to `results/pytest_output.txt`.  
  *Verification*: command exits 0 and `results/pytest_output.txt` contains the line `=== 0 failures ===`.  

- [ ] T011 [P] **Run static analysis with ruff** – lint the entire `code/` tree, automatically fix fixable issues, and record the final report in `results/ruff_report.txt`.  
  *Verification*: after `ruff check --fix code/` runs, `ruff check code/` returns exit 0 and `results/ruff_report.txt` is non‑empty.  

- [ ] T012 [P] **Generate end‑to‑end runtime, enforce 6 h limit, and profiling evidence** – `code/utils/pipeline_timer.py` wraps the full pipeline (`download → align → preprocess → bias_audit → train → evaluate → validate`). It records wall‑clock time, CPU usage (via `psutil`), and memory peaks (via `memory_profiler`). If the total duration exceeds 6 hours (21 600 s), the script terminates the pipeline with a non‑zero exit code and writes `"passed": false` in `results/runtime_verification.json`.  
  *Artifacts*: `results/runtime_verification.json` (`duration_seconds`, `passed` = true if ≤ 21600 s), `results/profile_report.txt` (cProfile output), `results/memory_log.txt`.  
  *Verification*: `runtime_verification.json` shows `"passed": true` and `"duration_seconds"` ≤ 21600; additionally the existence and non‑emptiness of `profile_report.txt` and `memory_log.txt` are asserted.  

- [ ] T013 [P] **Update SHA‑256 hashes for major artifacts** – `code/utils/update_state.py` computes SHA‑256 for each primary output (`aligned_dataset.npz`, `checkpoint_best.pt`, `evaluation_metrics.json`, `validation_metrics.json`, `quickstart.md`, `state/projects/PROJ-176-predicting-molecular-properties-from-vib.yaml`, and all log files) and writes a human‑readable manifest `results/state_hashes.yaml`.  
  *Verification*: script exits 0 and the YAML contains a 64‑character hex string for every listed artifact.  

- [ ] T014 [P] **Write comprehensive `quickstart.md`** – inside `specs/001-predict-molecular-properties/` create a markdown file that:  
  1. Lists exact runnable commands for each pipeline stage (`python -m code.data.download`, `python -m code.data.align`, etc.).  
  2. Documents the real data source URLs/package names used by `code/data/download.py`.  
  3. Provides a hyper‑parameter table (learning rate, batch size, epochs, etc.).  
  4. Enumerates a checklist of required artifacts (`structure_report.txt`, `alignment_report.json`, `aligned_dataset.npz`, `checkpoint_best.pt`, `evaluation_metrics.json`, `validation_metrics.json`, `pytest_output.txt`, `ruff_report.txt`, `runtime_verification.json`, `profile_report.txt`, `state_hashes.yaml`).  
  *Verification*: a helper script `code/utils/check_quickstart.py` parses `quickstart.md`, extracts the listed file paths, and asserts each exists and is non‑empty.  

- [ ] T016 [P] **Verify all external citations with Reference‑Validator Agent** – `code/utils/validate_citations.py` scans every project file for citation markers, invokes the Reference‑Validator Agent, and writes `results/citation_validation.json` summarizing validation status per citation (must be “verified”).  
  *Verification*: script exits 0 and `citation_validation.json` contains only entries with `"status": "verified"`; any unverified citation causes a non‑zero exit.  

- [ ] T015 **Re‑run the entire documented workflow from a clean slate and generate reproducibility report** – delete `data/processed/`, `models/`, and `results/` directories, assert they are absent, then execute the full pipeline using only the commands in `quickstart.md`. Capture timestamps, any negative findings (e.g., bias‑test failures, missing external validation), and produce `results/repro_report.md` summarising outcomes and confirming that every checklist item from `quickstart.md` is present.  
  *Verification*: the script exits 0, `repro_report.md` lists all required artifacts with their existence status, and the report includes a final line `Reproducibility check: PASS`.  

---  

*All tasks respect the data‑flow ordering; a task that consumes an artifact is listed after the task that produces it.*  