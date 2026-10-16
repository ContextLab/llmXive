# Tasks: Predicting Molecular Properties from Vibrational Spectra with Deep Learning  

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, contract schemas, and any existing artifacts.  

The goal is to deliver a fully reproducible CPU‑only pipeline that (1) downloads real QM9 and IR‑spectra datasets, (2) aligns and preprocesses them, (3) trains a 1‑D CNN, (4) evaluates with rigorous statistics, (5) validates on an external dataset, and (6) provides complete verification artifacts. All tasks respect data flow, use only real data, and generate the required files under the project‑owned directories (`code/`, `data/`, `models/`, `results/`, `logs/`, `specs/`).  

## Phase 1 – Data ingestion, alignment, and preprocessing  

- [ ] T101 [P] **Create project skeleton** – create the canonical directory tree (`code/`, `code/data/`, `code/models/`, `code/evaluation/`, `code/utils/`, `tests/`, `data/raw/`, `data/processed/`, `data/external/`, `results/`, `logs/`, `specs/001-predict-molecular-properties/`) and empty `__init__.py` files.  
  *Verification*: `python -m compileall code/` exits 0 and `find . -type d | sort > results/structure_report.txt`; the report must list all expected directories.  

- [ ] T102 [P] **Materialize contract schemas** – copy the three YAML schema files to the spec folder:  
  - `specs/001-predict-molecular-properties/contracts/dataset.schema.yaml`  
  - `specs/001-predict-molecular-properties/contracts/model_output.schema.yaml`  
  - `specs/001-predict-molecular-properties/contracts/evaluation_results.schema.yaml`  
  *Verification*: `python -c "import yaml, glob; [yaml.safe_load(open(f)) for f in glob.glob('specs/001-predict-molecular-properties/contracts/*.yaml')]"` exits 0 and each file is non‑empty.  

- [ ] T103 [US-1] **Download QM9 and IR‑spectra, verify integrity, and enforce fast‑failure on corruption** – fetch the QM9 parquet file (`data/raw/qm9.parquet`) via `datasets.load_dataset('lisn519010/QM9')` and the IR‑spectra parquet file (`data/raw/ir_spectra.parquet`) via `datasets.load_dataset('lamblador/QM9-IR')`. Compute SHA‑256 checksums, compare against expected values, and abort with a clear error message if a file is corrupted or incomplete. Compute InChIKey matches, discard mismatches, and log counts.  
  *Artifact*: `data/processed/alignment_report.json` (fields: `matched`, `discarded`, `integrity_status`, `selection_bias_stats`).  
  *Verification*: `code/data/download.py` exits 0, `alignment_report.json` exists, `integrity_status` is `"ok"`, `matched >= 129000`, and KS‑test values are present.  

- [ ] T104 [US-1] **Preprocess aligned spectra and filter missing properties** – for each matched molecule, interpolate the IR spectrum onto a uniform 400–4000 cm⁻¹ grid (1 cm⁻¹ step, length = 3601), apply Gaussian smoothing (σ = 2 cm⁻¹), normalize to unit area, and convert target properties to the required units (Debye, Å³, eV). Drop any molecule lacking any of the three target properties before saving. Store all arrays together with `InChIKeys` and the KS‑test stats.  
  *Artifact*: `data/processed/aligned_dataset.npz` containing `spectra`, `dipole`, `polarizability`, `gap`, `InChIKeys`, `selection_bias_stats`.  
  *Verification*: loading the NPZ yields `spectra.shape == (N,1,3601)`, `np.allclose(spectra.sum(axis=2), 1.0, atol=1e-6)`, no NaNs in target arrays, and the embedded `selection_bias_stats` match those in `alignment_report.json`.  

## Phase 2 – Model training, evaluation, and independent validation  

- [ ] T105 [US-2] **Train 1‑D CNN with NaN‑loss detection** – use the training split of `aligned_dataset.npz` to train the architecture defined in `code/models/cnn_1d.py` (three conv blocks, three regression heads). Optimizer: Adam (lr = 1e‑3), batch size = 64, early stopping (patience = 10, max epochs = 50) on a CPU‑only runner. The training loop must monitor the loss; if any loss becomes NaN, terminate immediately, log a `"Training Failed"` status, and abort checkpoint saving.  
  *Artifacts*: `models/checkpoint_best.pt`, TensorBoard logs under `runs/training/`, and `logs/training_failure.log` (empty if training succeeds, contains error message otherwise).  
  *Verification*: after `code/main.py train`, `checkpoint_best.pt` exists (or `training_failure.log` indicates failure), `epoch` ≤ 50, and `val_loss` does not increase for 10 consecutive epochs when training succeeds.  

- [ ] T106 [US-3] **Evaluate on held‑out test set using spec‑compliant significance threshold** – load `checkpoint_best.pt`, run inference on the test split, and compute per‑property MAE, R², paired‑sample t‑test p‑values (using the spec’s SC‑003 threshold p < 0.01, not a Bonferroni‑adjusted α), Two‑One‑Sided Tests (TOST) with equivalence bounds (dipole ± 0.05 D, polarizability ± 0.10 Å³, gap ± 0.05 eV), and Hotelling’s T² for the joint error vector. Save predictions for reproducibility.  
  *Artifacts*: `results/evaluation_metrics.json` (conforms to `evaluation_results.schema.yaml`) and `results/predictions_test.npz`.  
  *Verification*: `code/evaluation/check_metrics.py results/evaluation_metrics.json` exits 0; the JSON contains all required fields (`mae`, `r2`, `tost_p_value`, `ci_lower`, `ci_upper`, `multivariate.hotelling_t2`), and each paired‑sample t‑test p‑value is < 0.01.  

- [ ] T108 [US-4] **Independent validation on external dataset** – if a real external dataset exists under `data/external/` (experimental IR spectra or QM9 recomputed with a different DFT functional), align it, run inference with `checkpoint_best.pt`, compute MAE and R², and set a flag if the MAE increase relative to the internal test set exceeds 20 %.  
  *Artifact*: `results/validation_metrics.json` (includes `mae_increase_flag` boolean).  
  *Verification*: the script aborts with a clear error if `data/external/` is empty; otherwise, the flag is correctly set and the JSON conforms to the same schema as `evaluation_metrics.json` (with only MAE/R² fields).  

## Phase 3 – Verification, profiling, state bookkeeping, and reproducible handoff  

- [ ] T109 [P] **Run full pytest suite** – execute all tests in the `tests/` directory and capture stdout/stderr.  
  *Artifact*: `results/pytest_output.txt`.  
  *Verification*: `pytest -q tests/ 2>&1 | tee results/pytest_output.txt` exits 0 and the file contains the line “=== 0 failures ===”.  

- [ ] T110 [P] **Run static analysis with ruff** – lint the entire `code/` tree, automatically fix fixable issues, and record the final report.  
  *Artifact*: `results/ruff_report.txt`.  
  *Verification*: `ruff check --fix code/ 2>&1 | tee results/ruff_report.txt` runs, then `ruff check code/` returns exit 0 (no remaining issues).  

- [ ] T111 **Generate end‑to‑end runtime and profiling evidence** – wrap the full pipeline (`download → preprocess → train → evaluate → validate`) in a timing wrapper, record total wall‑clock time, and profile CPU/memory usage.  
  *Artifacts*: `results/runtime_verification.json` (fields `duration_seconds`, `passed` = true if ≤ 21600 s), `results/profile_report.txt` (cProfile output), `results/memory_log.txt` (memory‑profiler output).  
  *Verification*: the wrapper script writes `runtime_verification.json` with `passed:true` when the total duration is ≤ 6 h; the profile and memory logs contain non‑empty textual output.  

- [ ] T112 **Update SHA‑256 hashes for major artifacts** – compute hashes for all primary outputs (`aligned_dataset.npz`, `checkpoint_best.pt`, `evaluation_metrics.json`, `validation_metrics.json`, `quickstart.md`, `state/projects/PROJ-176-predicting-molecular-properties-from-vib.yaml`, and all log files) and write a human‑readable YAML manifest.  
  *Artifact*: `results/state_hashes.yaml`.  
  *Verification*: `code/utils/update_state.py` runs without error and the YAML contains an entry for each listed artifact with a 64‑character hexadecimal hash.  

- [ ] T113 [P] **Write comprehensive `quickstart.md`** – inside `specs/001-predict-molecular-properties/` create a markdown file that (a) lists exact runnable commands for each pipeline stage, (b) documents the real data source URLs/package names used by `code/data/download.py`, (c) provides a hyper‑parameter table, and (d) enumerates a checklist of required artifacts (`structure_report.txt`, `alignment_report.json`, `aligned_dataset.npz`, `checkpoint_best.pt`, `evaluation_metrics.json`, `validation_metrics.json`, `pytest_output.txt`, `ruff_report.txt`, `runtime_verification.json`, `profile_report.txt`, `state_hashes.yaml`).  
  *Verification*: a helper script parses `quickstart.md`, extracts the listed file paths, and asserts that each file exists and is non‑empty.  

- [ ] T114 **Re‑run the entire documented workflow from a clean slate and generate reproducibility report** – delete `data/processed/`, `models/`, and `results/` directories, then execute the full pipeline using only the commands in `quickstart.md`. Summarise outcomes, any negative findings (e.g., bias‑test failures, missing external validation), and produce a handoff statement for the paper stage.  
  *Artifact*: `results/repro_report.md`.  
  *Verification*: the report includes timestamps, confirms that every checklist item from `quickstart.md` is present, and the orchestrating script exits with status 0.  