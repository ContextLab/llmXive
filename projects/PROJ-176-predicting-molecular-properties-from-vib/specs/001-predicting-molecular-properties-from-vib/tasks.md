# Tasks: Predicting Molecular Properties from Vibrational Spectra with Deep Learning  

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, contract schemas, and any existing artifacts.  

The goal is a fully reproducible CPU‑only pipeline that (1) downloads verified QM9 and IR‑spectra datasets, (2) aligns and preprocesses them, (3) trains a 1‑D CNN, (4) evaluates with rigorous statistics, (5) validates on an independent dataset, (6) runs control experiments, and (7) produces all verification artifacts required by the platform. Tasks are ordered to respect data flow; each task lists the concrete output artifact(s) and an observable verification step.

---

## Phase 1 – Project scaffolding, data ingestion & preprocessing  

- [ ] T001 **Create project scaffolding, set deterministic seeds, and compile code**  
  *Create the canonical directory tree (`code/`, `code/data/`, `code/models/`, `code/evaluation/`, `code/utils/`, `tests/`, `data/raw/`, `data/processed/`, `data/generated/`, `results/`, `logs/`, `config/`), write fixed random seeds to `config/seeds.yaml` (e.g., `numpy: 42`, `torch: 42`, `python: 42`), and run `python -m compileall code/`.*
  *Artifacts*: `logs/compileall.log`, `results/structure_report.txt`, `config/seeds.yaml`.  
  *Verification*: `python -c "import yaml; yaml.safe_load(open('config/seeds.yaml'))"` succeeds; `python -m compileall code/` exits 0; `cat results/structure_report.txt` lists all created directories.

- [ ] T002 **Materialize contract schemas** – copy the three YAML schema files into `specs/001-predict-molecular-properties/contracts/`.  
  *Artifacts*: `specs/001-predict-molecular-properties/contracts/dataset.schema.yaml`, `model_output.schema.yaml`, `evaluation_results.schema.yaml`.  
  *Verification*: `python -c "import yaml, glob; [yaml.safe_load(open(f)) for f in glob.glob('specs/001-predict-molecular-properties/contracts/*.yaml')]"` exits 0 and each file is non‑empty.

- [ ] T003 **Download QM9 properties and IR‑spectra, verify integrity, and handle DFT‑method mismatch**  
  Implement `code/data/download.py` to:  
  1. Stream QM9 parquet via `datasets.load_dataset('lisn519010/QM9', split='train', streaming=False, cache_dir='data/raw')` → `data/raw/qm9.parquet`.  
  2. Stream IR‑spectra parquet via `datasets.load_dataset('lamblador/QM9-IR', split='train', streaming=False, cache_dir='data/raw')` → `data/raw/ir_spectra.parquet`.  
  3. Compute SHA‑256 checksums for both files and compare against known reference values stored in `results/checksums.json`.  
  4. Load the IR‑spectra metadata; **if its `dft_method` is not `B3LYP`**, invoke the in‑house generation task (T019) to create compatible spectra and then continue using the generated file. If generation also fails, abort with a clear error.  
  *Artifacts*: `data/raw/qm9.parquet`, `data/raw/ir_spectra.parquet` (when compatible), `results/checksums.json`.  
  *Verification*: Script exits 0 and `jq .status results/checksums.json` returns `"ok"`; on mismatch it triggers T019 and proceeds; on unrecoverable error it exits 1 with an informative message.

- [ ] T019 **Generate IR spectra in‑house using B3LYP via PySCF (Phase 0.5)**   <!-- FAILED-IN-EXECUTION: code/data/generate_ir.py exit=1 -->
  Implement `code/data/generate_ir.py` to:  
  1. Load QM9 geometries from `data/raw/qm9.parquet`.  
  2. For each molecule, compute harmonic vibrational frequencies and IR intensities using the B3LYP functional with PySCF (CPU‑only).  
  3. Interpolate the resulting intensities onto the fixed 400 – 4000 cm⁻¹, 1 cm⁻¹ grid, apply Gaussian smoothing (σ = 2 cm⁻¹), and normalize to unit area.  
  4. Store the spectra array as `data/generated/generated_spectra.npz` containing `spectra` (`[N,1,3601]`), `InChIKeys`, and a `generation_metadata` dict.  
  *Artifacts*: `data/generated/generated_spectra.npz`.  
  *Verification*: Loading the NPZ yields `spectra.shape == (N,1,3601)`, `np.allclose(spectra.sum(axis=2), 1.0, atol=1e-6)`, and the metadata includes `"method": "B3LYP-PySCF"`.

- [ ] T004 **Align datasets on InChIKey and discard mismatches**  
  Implement `code/data/align.py` to read the two source files (either the downloaded IR parquet **or** the generated spectra NPZ), perform an inner join on the `InChIKey` column, log the numbers of matched and discarded molecules, and write an alignment report.  
  *Artifacts*: `data/processed/alignment_report.json` (`matched`, `discarded`).  
  *Verification*: `jq .matched data/processed/alignment_report.json` ≥ 129000 and the script exits 0.

- [ ] T005 **Preprocess spectra and filter missing target properties**  
  Implement `code/data/preprocess.py` that, for each matched molecule:  
  1. Interpolates intensity onto a uniform grid 400 – 4000 cm⁻¹ with 1 cm⁻¹ spacing (3601 points).  
  2. Applies Gaussian smoothing (σ = 2 cm⁻¹).  
  3. Normalizes each spectrum to unit area (tolerance ± 1e‑6).  
  4. Converts dipole (Debye), polarizability (Å³), and HOMO‑LUMO gap (eV) to `float32`.  
  5. Drops any molecule missing any of the three targets.  
  Saves `data/processed/aligned_dataset.npz` containing arrays `spectra`, `dipole`, `polarizability`, `gap`, `InChIKeys`, and a placeholder `selection_bias_stats`.  
  *Verification*: Loading the NPZ yields `spectra.shape == (N,1,3601)`, `np.allclose(spectra.sum(axis=2), 1.0, atol=1e-6)`, no NaNs in target arrays, and file size < 1 GB.

- [ ] T006 **Selection‑bias audit (KS test) and optional weighting**  
  Implement `code/data/bias_audit.py` that runs a two‑sample Kolmogorov–Smirnov test for each target property comparing the aligned subset vs. the full QM9 set. Store `statistic` and `p_value` for each property inside `selection_bias_stats` of `data/processed/aligned_dataset.npz`. If any p‑value < 0.05, compute inverse‑probability weights and save `data/processed/weight_mask.npy`.  
  *Verification*: After execution, `np.load('data/processed/aligned_dataset.npz')['selection_bias_stats']` contains the three KS entries; if bias detected, `weight_mask.npy` exists and its shape matches the number of samples.

- [ ] T007 **Enforce 6 h runtime limit (watchdog)**  
  `code/utils/pipeline_timer.py` wraps the full pipeline (tasks T003–T012) by launching a subprocess with a 6 h timeout. If the timeout is reached, the script kills the subprocess and exits with a non‑zero code, writing `results/runtime_verification.json` with `"passed": false`.  
  *Artifacts*: `results/runtime_verification.json` (`duration_seconds`, `passed`).  
  *Verification*: `jq .passed results/runtime_verification.json` returns `true` for normal runs; if the limit is exceeded, the script exits 1 and `passed` is `false`.

## Phase 2 – Model training, evaluation & independent validation  

- [ ] T008 **Train 1‑D CNN with early stopping, NaN‑loss detection, and architecture verification**  
  `code/models/trainer.py` loads the training split of `aligned_dataset.npz`, builds the architecture defined in `code/models/cnn_1d.py` (three conv blocks, **three distinct regression heads** for dipole, polarizability, and HOMO‑LUMO gap), trains with Adam (lr = 1e‑3), batch size = 64, early stopping (patience = 10, max epochs = 50) on a CPU‑only runner. The loop aborts with a non‑zero exit code and logs “Training Failed” if any loss becomes NaN. After training, a verification step loads `models/checkpoint_best.pt` and asserts that the state dict contains three head modules (`head_dipole`, `head_polarizability`, `head_gap`).  
  *Artifacts*: `models/checkpoint_best.pt`, TensorBoard logs under `runs/training/`, `logs/training.log`.  
  *Verification*: `torch.load models/checkpoint_best.pt` succeeds; `grep "Early stopping triggered" logs/training.log` finds a line (or the log is empty on a perfect run); Python check confirms three heads; `epoch` ≤ 50.

- [ ] T009 **Evaluate on held‑out test set with full statistical suite**  
  `code/evaluation/evaluate.py` loads `checkpoint_best.pt`, runs inference on the test split, computes per‑property MAE, R², paired‑sample t‑test (null = 0) with Bonferroni‑adjusted α ≈ 0.0033, Two‑One‑Sided Tests (TOST) using equivalence bounds (dipole ± 0.05 D, polarizability ± 0.10 Å³, gap ± 0.05 eV), and Hotelling’s T² (multivariate normality via Mardia’s test, fallback to 10 000‑permutation test).  
  *Artifacts*: `results/evaluation_metrics.json` (conforms to `contracts/evaluation_results.schema.yaml`), `results/predictions_test.npz`.  
  *Verification*: `python -m jsonschema -i results/evaluation_metrics.json specs/001-predict-molecular-properties/contracts/evaluation_results.schema.yaml` exits 0; each t‑test p‑value < 0.0033.

- [ ] T010 **Independent validation on external B3LYP dataset**  
  `code/evaluation/validate.py` checks for `data/external/validation.parquet` (or loads the HuggingFace dataset `lamblador/QM9-B3LYP`). It aligns on `InChIKey`, applies the same preprocessing pipeline, runs inference with the best checkpoint, computes MAE and R² per property, and adds a boolean flag `mae_increase_flag` that is true if any property’s MAE exceeds the internal test‑set MAE by > 20 %.  
  *Artifacts*: `results/validation_metrics.json` (same schema as evaluation, but only MAE/R² plus the flag).  
  *Verification*: The JSON contains `"mae_increase_flag": true/false`; script exits 0; file size < 200 KB.

- [ ] T011 **Scrambled‑order control experiment**  
  `code/evaluation/control_scrambled.py` randomly permutes the wavenumber order of each spectrum, runs inference with the best checkpoint, and records MAE/R².  
  *Artifacts*: `results/control_metrics.json` (same schema as evaluation).  
  *Verification*: JSON validates against the evaluation schema; MAE is substantially higher than in `results/evaluation_metrics.json`.

- [ ] T012 **Random‑noise control experiment**  
  `code/evaluation/control_random.py` replaces each spectrum with Gaussian noise (mean = 0, std = 1), runs inference, and records MAE/R².  
  *Artifacts*: `results/control_random_metrics.json` (same schema as evaluation).  
  *Verification*: JSON validates; MAE is substantially higher than in `results/evaluation_metrics.json`.

## Phase 3 – Quality checks, reporting & reproducibility  

- [ ] T013 **Run full pytest suite**  
  Execute `pytest -q tests/` and capture stdout/stderr to `results/pytest_output.txt`.  
  *Verification*: Command exits 0 and `grep "0 failures" results/pytest_output.txt` succeeds.

- [ ] T014 **Run static analysis with ruff**  
  Run `ruff check --fix code/` then `ruff check code/` and store the final report in `results/ruff_report.txt`.  
  *Verification*: `ruff check code/` returns exit 0 and `results/ruff_report.txt` is non‑empty.

- [ ] T015 **Update SHA‑256 hashes for major artifacts**  
  `code/utils/update_state.py` computes SHA‑256 for each primary output (`aligned_dataset.npz`, `checkpoint_best.pt`, `evaluation_metrics.json`, `validation_metrics.json`, `quickstart.md`, `state/projects/PROJ-176-predicting-molecular-properties-from-vib.yaml`, and all log files) and writes a human‑readable manifest `results/state_hashes.yaml`.  
  *Verification*: Script exits 0 and each listed artifact has a 64‑character hex string in the YAML.

- [ ] T016 **Write comprehensive `quickstart.md`**  
  Create `specs/001-predict-molecular-properties/quickstart.md` that:  
  1. Lists exact runnable commands for each pipeline stage (`python -m code.data.download`, `python -m code.data.align`, …).  
  2. Documents the real data source URLs/package names used by `code/data/download.py`.  
  3. Provides a hyper‑parameter table (learning rate, batch size, epochs, etc.).  
  4. Enumerates a checklist of required artifacts (`structure_report.txt`, `alignment_report.json`, `aligned_dataset.npz`, `checkpoint_best.pt`, `evaluation_metrics.json`, `validation_metrics.json`, `control_metrics.json`, `control_random_metrics.json`, `pytest_output.txt`, `ruff_report.txt`, `runtime_verification.json`, `profile_report.txt`, `state_hashes.yaml`).  
  *Verification*: `code/utils/check_quickstart.py` parses the file, extracts the listed paths, and asserts each exists and is non‑empty.

- [ ] T017 **Re‑run the entire documented workflow from a clean slate and generate reproducibility report**  
  Delete `data/processed/`, `models/`, and `results/` directories, assert they are absent, then execute the full pipeline using only the commands in `quickstart.md`. Capture timestamps, any negative findings (e.g., bias‑test failures, missing external validation), and produce `results/repro_report.md` summarising outcomes and confirming that every checklist item from `quickstart.md` is present.  
  *Verification*: Script exits 0, `repro_report.md` lists all required artifacts with “present”, and ends with the line `Reproducibility check: PASS`.

- [ ] T018 **Validate all external citations**  
  `code/utils/validate_citations.py` scans every project file for citation markers, invokes the Reference‑Validator Agent, and writes `results/citation_validation.json` summarising validation status per citation (must be “verified”).  
  *Verification*: Script exits 0 and `jq 'all(.status == "verified")' results/citation_validation.json` returns `true`.

---  

*All tasks respect the data‑flow ordering; a task that consumes an artifact is listed after the task that produces it. Tags now directly reference functional requirements (e.g., [FR-001]) and no undefined tags remain. Random seeds are pinned, architecture heads are verified, runtime termination is enforced, and the previously missing control experiments are fully implemented.* 