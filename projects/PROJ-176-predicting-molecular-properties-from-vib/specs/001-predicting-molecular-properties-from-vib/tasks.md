# Tasks: Predicting Molecular Properties from Vibrational Spectra with Deep Learning  

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, contract schemas, and any existing artifacts.  

The goal is to deliver a fully reproducible CPU‑only pipeline that (1) downloads real QM9 and IR‑spectra datasets, (2) aligns and preprocesses them, (3) trains a 1‑D CNN, (4) evaluates with rigorous statistics, (5) validates on an external dataset, and (6) provides complete verification artifacts. All tasks respect data flow, use only real data, and generate the required files under the project‑owned directories (`code/`, `data/`, `models/`, `results/`, `logs/`, `specs/`).  

## Phase 1 – Data ingestion, alignment, and preprocessing  

- [ ] T101 [P] **Create project skeleton** – create the canonical directory tree (`code/`, `code/data/`, `code/models/`, `code/evaluation/`, `code/utils/`, `tests/`, `data/raw/`, `data/processed/`, `data/external/`, `results/`, `logs/`, `specs/001-predict-molecular-properties/`) and empty `__init__.py` files.   <!-- FAILED-IN-EXECUTION: code/setup_skeleton.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/setup_skeleton.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/setup_skeleton.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/setup_skeleton.py exit=1 -->
  *Verification*: `python -m compileall code/` exits 0 and `find . -type d | sort > results/structure_report.txt`; the report must list all expected directories.  

- [ ] T102 [P] **Materialize contract schemas** – copy the three YAML schema files to the spec folder:  
  - `specs/001-predict-molecular-properties/contracts/dataset.schema.yaml`  
  - `specs/001-predict-molecular-properties/contracts/model_output.schema.yaml`  
  - `specs/001-predict-molecular-properties/contracts/evaluation_results.schema.yaml`  
  *Verification*: `python -c "import yaml, glob; [yaml.safe_load(open(f)) for f in glob.glob('specs/001-predict-molecular-properties/contracts/*.yaml')]"` exits 0 and each file is non‑empty.  

- [ ] T103 [US1] **Download QM9 and IR‑spectra, verify 1:1 correspondence** – fetch the QM9 parquet file (`data/raw/qm9.parquet`) via `qm9pack` and the IR‑spectra parquet file (`data/raw/ir_spectra.parquet`) via `datasets.load_dataset`. Compute InChIKey matches, discard mismatches, and log counts and KS‑test statistics for selection‑bias.  
  *Artifact*: `data/processed/alignment_report.json` (fields: `matched`, `discarded`, `selection_bias_stats`).  
  *Verification*: `code/data/download.py` raises on any fetch failure; after run, `alignment_report.json` exists, `matched >= 129000`, and KS‑test values are present.  

- [ ] T104 [US2] **Preprocess aligned spectra** – for each matched molecule, interpolate the IR spectrum onto a uniform 400–4000 cm⁻¹ grid (1 cm⁻¹ step, length = 3601), apply Gaussian smoothing (σ = 2 cm⁻¹), normalize to unit area, and convert target properties to the required units. Store all arrays together with `InChIKeys` and the KS‑test stats.  
  *Artifact*: `data/processed/aligned_dataset.npz` containing `spectra`, `dipole`, `polarizability`, `gap`, `InChIKeys`, `selection_bias_stats`.  
  *Verification*: loading the NPZ yields `spectra.shape == (N,1,3601)`, `np.allclose(spectra.sum(axis=2), 1.0, atol=1e-6)`, and the embedded `selection_bias_stats` match those in `alignment_report.json`.  

## Phase 2 – Model training, evaluation, and independent validation  

- [ ] T105 [US3] **Train 1‑D CNN** – use the training split of `aligned_dataset.npz` to train the architecture defined in `code/models/cnn_1d.py` (three conv blocks, three regression heads). Optimizer: Adam (lr = 1e‑3), batch size = 64, early stopping (patience = 10, max epochs = 50) on a CPU‑only runner.  
  *Artifacts*: `models/checkpoint_best.pt` and TensorBoard logs under `runs/training/`.  
  *Verification*: after `code/main.py train`, `checkpoint_best.pt` exists, `epoch` ≤ 50, and `val_loss` does not increase for 10 consecutive epochs.  

- [ ] T106 [US4] **Evaluate on held‑out test set** – load `checkpoint_best.pt`, run inference on the test split, and compute per‑property MAE, R², paired‑sample t‑test p‑values (Bonferroni‑adjusted), Two‑One‑Sided Tests (TOST) with equivalence bounds (dipole ± 0.05 D, polarizability ± 0.10 Å³, gap ± 0.05 eV), and Hotelling’s T² for the joint error vector. Save predictions for reproducibility.  
  *Artifacts*: `results/evaluation_metrics.json` (conforms to `evaluation_results.schema.yaml`) and `results/predictions_test.npz`.  
  *Verification*: `code/evaluation/check_metrics.py results/evaluation_metrics.json` exits 0; the JSON contains all required fields (`mae`, `r2`, `tost_p_value`, `ci_lower`, `ci_upper`, `multivariate.hotelling_t2`).  

- [ ] T107 [US5] **Control experiment with scrambled spectra** – randomly permute the wavenumber axis of each spectrum, run inference with the same checkpoint, and record MAE/R².  
  *Artifact*: `results/control_metrics.json`.  
  *Verification*: a post‑hoc script confirms that `control_metrics.json` MAE values are statistically higher than those in `evaluation_metrics.json` (e.g., paired t‑test, p < 0.01).  

- [ ] T108 [US6] **Independent validation on external dataset** – if a real external dataset exists under `data/external/` (experimental IR spectra or QM9 recomputed with a different DFT functional), align it, run inference with `checkpoint_best.pt`, compute MAE and R², and set a flag if the MAE increase relative to the internal test set exceeds 20 %.  
  *Artifact*: `results/validation_metrics.json` (includes `mae_increase_flag` boolean).  
  *Verification*: the script aborts with a clear error if `data/external/` is empty; otherwise, the flag is correctly set and the JSON conforms to the same schema as `evaluation_metrics.json` (with only MAE/R² fields).  

## Phase 3 – Verification, profiling, state bookkeeping, and reproducible handoff  

- [ ] T109 [P] **Run full pytest suite** – execute all tests in the `tests/` directory and capture stdout/stderr.  
  *Artifact*: `results/pytest_output.txt`.  
  *Verification*: `pytest -q tests/ 2>&1 | tee results/pytest_output.txt` exits 0 and the file contains the line “=== 0 failures ===”.  

- [ ] T110 [P] **Run static analysis with ruff** – lint the entire `code/` tree, automatically fix fixable issues, and record the final report.  
  *Artifact*: `results/ruff_report.txt`.  
  *Verification*: `ruff check --fix code/ 2>&1 | tee results/ruff_report.txt` runs, then `ruff check code/` returns exit 0 (no remaining issues).  

- [ ] T111 [P] **Generate end‑to‑end runtime and profiling evidence** – wrap the full pipeline (`download → preprocess → train → evaluate → validate`) in a timing wrapper, record total wall‑clock time, and profile CPU/memory usage.  
  *Artifacts*: `results/runtime_verification.json` (fields `duration_seconds`, `passed` – true if ≤ 21600 s), `results/profile_report.txt` (cProfile output), `results/memory_log.txt` (memory‑profiler output).  
  *Verification*: the wrapper script writes `runtime_verification.json` with `passed:true` when the total duration is ≤ 6 h; the profile and memory logs contain non‑empty textual output.  

- [ ] T112 [P] **Update SHA‑256 hashes for major artifacts** – compute hashes for all primary outputs (`aligned_dataset.npz`, `checkpoint_best.pt`, `evaluation_metrics.json`, `validation_metrics.json`, figures once generated, and all log files) and write a human‑readable YAML manifest.  
  *Artifact*: `results/state_hashes.yaml`.  
  *Verification*: `code/utils/update_state.py` runs without error and the YAML contains an entry for each listed artifact with a 64‑character hexadecimal hash.  

- [ ] T113 [P] **Write comprehensive `quickstart.md`** – inside `specs/001-predict-molecular-properties/` create a markdown file that (a) lists exact runnable commands for each pipeline stage, (b) documents the real data source URLs/package names used by `code/data/download.py`, (c) provides a hyper‑parameter table, and (d) enumerates a checklist of required artifacts (`structure_report.txt`, `alignment_report.json`, `aligned_dataset.npz`, `checkpoint_best.pt`, `evaluation_metrics.json`, `validation_metrics.json`, `pytest_output.txt`, `ruff_report.txt`, `runtime_verification.json`, `profile_report.txt`, `state_hashes.yaml`).  
  *Verification*: a helper script parses `quickstart.md`, extracts the listed file paths, and asserts that each file exists and is non‑empty.  

- [ ] T114 [P] **Re‑run the entire documented workflow from a clean slate and generate reproducibility report** – delete `data/processed/`, `models/`, and `results/` directories, then execute the full pipeline using only the commands in `quickstart.md`. Summarise outcomes, any negative findings (e.g., bias‑test failures, missing external validation), and produce a handoff statement for the paper stage.  
  *Artifact*: `results/repro_report.md`.  
  *Verification*: the report includes timestamps, confirms that every checklist item from `quickstart.md` is present, and the orchestrating script exits with status 0.  

## Dependency & Requirement Coverage  

| Spec Requirement | Covered by Task(s) |
|------------------|--------------------|
| FR‑001 / FR‑002 | T103, T104 |
| FR‑003 / FR‑004 | T105 |
| FR‑005 | T106, T107 |
| FR‑006 (runtime limit) | T111 |
| FR‑007 (independent validation) | T108 |
| SC‑001 / SC‑002 / SC‑003 | T106 |
| SC‑004 (pipeline runtime) | T111 |
| SC‑005 (generalizability) | T108 |
| SC‑006 (control experiment) | T107 |
| SC‑007 / SC‑008 (static analysis & tests) | T109, T110 |
| SC‑009 (profile report) | T111 |
| Selection‑bias invariant | T103, T104, T113 |
| State‑hash bookkeeping | T112 |
| Reproducibility handoff | T113, T114 |

All tasks respect the data‑flow order: download → alignment → preprocessing → training → evaluation → control → validation → verification → reporting. The list contains 14 substantive, check‑list tasks, satisfying the required 8–15 range.
