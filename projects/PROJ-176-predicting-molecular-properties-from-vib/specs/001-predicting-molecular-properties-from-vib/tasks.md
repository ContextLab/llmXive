# Tasks: Predicting Molecular Properties from Vibrational Spectra with Deep Learning  

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, contract schemas, and any existing artifacts.  

The goal is to deliver a fully reproducible CPU‑only pipeline that (1) downloads real QM9 and IR‑spectra datasets, (2) aligns and preprocesses them, (3) trains a 1‑D CNN, (4) evaluates with rigorous statistics, (5) validates on an external dataset, and (6) provides complete verification artifacts. All tasks respect data flow, use only real data, and generate the required files under the project‑owned directories (`code/`, `data/`, `models/`, `results/`, `logs/`, `specs/`).  

## Phase 1 – Data ingestion, alignment, and preprocessing  

- [ ] **T101** [P] Create the canonical project skeleton (directories `code/`, `code/data/`, `code/models/`, `code/evaluation/`, `code/utils/`, `tests/`, `data/raw/`, `data/processed/`, `data/external/`, `data/results/`, `logs/`, plus empty `__init__.py` files).  
  *Verification*: run `python -m compileall code/` (exit 0) and `find code tests data -type d | sort > data/results/structure_report.txt`; the report must list all expected directories.  

- [ ] **T102** [P] Materialize the three contract schemas as real files:  
  - `specs/001-predict-molecular-properties/contracts/dataset.schema.yaml`  
  - `specs/001-predict-molecular-properties/contracts/model_output.schema.yaml`  
  - `specs/001-predict-molecular-properties/contracts/evaluation_results.schema.yaml`  
  *Verification*: `python -c "import yaml,glob; [yaml.safe_load(open(f)) for f in glob.glob('specs/*/contracts/*.yaml')]"` exits 0 and each file is non‑empty.  

- [ ] **T103** [US1] Download the QM9 parquet file and the pre‑computed IR‑spectra parquet file, verify a 1:1 match via `InChIKey`, discard mismatches, and write the aligned identifiers and selection‑bias KS statistics.  
  *Artifact*: `data/processed/alignment_report.json` (contains counts of matched/discarded molecules and KS‑test `statistic`/`p_value`).  
  *Verification*: script `code/data/download.py` must raise on fetch failure; after run, `alignment_report.json` exists and `matched >= 129000`.  

- [ ] **T104** [US2] Preprocess the aligned spectra: interpolate to a fixed 400–4000 cm⁻¹ grid (1 cm⁻¹ step, length = 3601), apply Gaussian smoothing (σ = 2 cm⁻¹), normalize to unit area, and store the final tensors together with targets and `InChIKey`s.  
  *Artifact*: `data/processed/aligned_dataset.npz` (arrays `spectra`, `dipole`, `polarizability`, `gap`, `InChIKeys`, `selection_bias_stats`).  
  *Verification*: load the NPZ and assert `spectra.shape == (N,1,3601)`, `np.allclose(spectra.sum(axis=2), 1.0, atol=1e-6)`, and that `selection_bias_stats` matches the JSON from T103.  

## Phase 2 – Model training, evaluation, and independent validation  

- [ ] **T105** [US3] Train the 1‑D CNN (three conv blocks, three regression heads) on the training split using Adam (lr = 1e‑3), batch size = 64, early stopping (patience = 10, max epochs = 50) on a CPU‑only runner. Save the best checkpoint and TensorBoard logs.  
  *Artifacts*: `models/checkpoint_best.pt`, `runs/training/` (TensorBoard logs).  
  *Verification*: after `code/main.py train`, the checkpoint file exists, `epoch` ≤ 50, and `val_loss` does not increase for 10 consecutive epochs.  

- [ ] **T106** [US4] Evaluate the best checkpoint on the held‑out test set: compute per‑property MAE, R², paired‑sample t‑test p‑values (Bonferroni‑adjusted), Two‑One‑Sided Tests (TOST) with equivalence bounds (dipole ± 0.05 D, polarizability ± 0.10 Å³, gap ± 0.05 eV), and Hotelling’s T² for the joint error vector. Also generate predictions file.  
  *Artifacts*: `data/results/evaluation_metrics.json`, `data/results/predictions_test.npz`.  
  *Verification*: `code/evaluation/check_metrics.py data/results/evaluation_metrics.json` exits 0; the JSON conforms to `evaluation_results.schema.yaml` and contains fields `mae`, `r2`, `tost_p_value`, `ci_lower`, `ci_upper`, and `multivariate.hotelling_t2`.  

- [ ] **T107** [US5] Perform a control experiment by scrambling the order of wavenumber points for each spectrum, running inference with the same checkpoint, and recording the resulting MAE/R².  
  *Artifact*: `data/results/control_metrics.json`.  
  *Verification*: MAE in control must be significantly higher than in `evaluation_metrics.json` (simple numeric check in a post‑hoc script).  

- [ ] **T108** [US6] Independent validation: if a real external dataset exists under `data/external/` (experimental IR spectra or QM9 computed with a different DFT functional), evaluate the checkpoint without retraining, compute MAE/R², and flag whether the MAE increase relative to the test set exceeds 20 %.  
  *Artifact*: `data/results/validation_metrics.json` (includes `mae_increase_flag` boolean).  
  *Verification*: script aborts with a clear error if `data/external/` is empty; otherwise, the flag is set correctly.  

## Phase 3 – Verification, profiling, state bookkeeping, and reproducible handoff  

- [ ] **T109** [P] Run the full pytest suite and capture the output.  
  *Artifact*: `data/results/pytest_output.txt`.  
  *Verification*: command `pytest tests/ -v --cov=code 2>&1 | tee data/results/pytest_output.txt` exits 0; the file contains the string “=== 0 failures ===”.  

- [ ] **T110** [P] Run static analysis with ruff, fix any reported issues, and record the final report.  
  *Artifact*: `data/results/ruff_report.txt`.  
  *Verification*: `ruff check --fix code/ 2>&1 | tee data/results/ruff_report.txt` runs, then `ruff check code/` returns exit 0 (no remaining issues).  

- [ ] **T111** [P] Generate end‑to‑end runtime and profiling evidence (addresses the previously rejected T042).  
  *Artifacts*: `data/results/runtime_verification.json` (fields `duration_seconds`, `passed` – true if ≤ 21600 s), `data/results/profile_report.txt` (cProfile output), `data/results/memory_log.txt` (memory_profiler output).  
  *Verification*: a wrapper script runs the full pipeline (`code/main.py download && code/main.py preprocess && code/main.py train && code/main.py evaluate && code/main.py validate`) under `cProfile` and `memory_profiler`; the JSON reports `passed:true`.  

- [ ] **T112** [P] Update project‑wide SHA‑256 hashes for all major artifacts and write them to a human‑readable YAML file.  
  *Artifact*: `data/results/state_hashes.yaml`.  
  *Verification*: `code/utils/update_state.py` runs without error and the YAML contains entries for `aligned_dataset.npz`, `checkpoint_best.pt`, `evaluation_metrics.json`, `validation_metrics.json`, figures (once generated), and all log files.  

- [ ] **T113** [P] Write a comprehensive `quickstart.md` inside the spec folder that (a) lists the exact runnable commands for each pipeline stage, (b) documents the real data sources (URLs/package names) used by `code/data/download.py`, (c) provides a hyper‑parameter table, and (d) enumerates a checklist of required artifacts (`structure_report.txt`, `alignment_report.json`, `aligned_dataset.npz`, `checkpoint_best.pt`, `evaluation_metrics.json`, `validation_metrics.json`, `pytest_output.txt`, `ruff_report.txt`, `runtime_verification.json`, `profile_report.txt`, `state_hashes.yaml`).  
  *Verification*: after generation, a script parses `quickstart.md` and asserts that every listed file exists and is non‑empty.  

- [ ] **T114** [P] Re‑run the entire documented workflow from a clean slate (delete `data/processed/`, `models/`, `data/results/`), then generate a reproducibility report summarising the outcomes, any negative findings (e.g., bias‑test failures, missing external validation), and the handoff statement for the paper stage.  
  *Artifact*: `data/results/repro_report.md`.  
  *Verification*: the report includes timestamps, confirms that all checklist items from `quickstart.md` are present, and exits with status 0 from the orchestrating script.  

---  

### Dependency & Requirement Coverage  

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
| Bias‑audit invariant | T103, T113 (selection_bias_stats) |
| State‑hash bookkeeping | T112 |
| Reproducibility handoff | T113, T114 |

All tasks respect the data flow order: download → alignment → preprocessing → training → evaluation → control → validation → verification → reporting. The list contains 14 substantive, check‑list tasks, satisfying the required 8–15 range.
