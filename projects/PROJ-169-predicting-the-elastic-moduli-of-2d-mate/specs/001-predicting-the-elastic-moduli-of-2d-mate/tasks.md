# Tasks: Structure-Only Surrogate Model for 2D Material Elastic Moduli

**Inputs**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, and the JSON/YAML contracts in `specs/`.  
All tasks write to project‑owned directories (`code/`, `data/`, `docs/`).  
Tasks are ordered to respect data flow; a later task never runs before its prerequisites are satisfied.

---

## Phase 0 – Constitution‑title audit (hard gate)

- [ ] T060c **[P]** Verify that the project title no longer contains forbidden terms and produce a formal audit report.  
  *Creates* `code/utils/verify_constitution_title.py` which (1) scans `constitution.md` for the exact phrase **“Structure‑Only Surrogate Model”**, (2) exits with status 1 if any forbidden term (“First‑Principles”, “Schrödinger”, “Hamiltonian”) is found, and (3) writes `data/results/constitution_title_audit.json` conforming to `contracts/constitution_audit_schema.yaml`.  
  *Verification*: CI runs the script; a non‑zero exit code fails the pipeline, otherwise the JSON file must contain `"status":"PASS"`.

---

## Phase 1 – Data acquisition & preprocessing  

| Task | Description |
|------|-------------|

- [ ] T001 **[P]** Download the raw 2D‑material dataset and apply deterministic source‑selection logic.  
  *Script*: `code/data/loader.py` (uses `matminer.datasets.load_dataset("elastic_tensor_2015")`).  
  *Outputs*: `data/raw/raw_dataset.parquet` and `data/raw/metadata.json` (SHA‑256 checksum, chosen source, fallback flag).  
  *Verification*: `metadata.json` records `"source":"Materials Project"` (or the deterministic fallback) and `"entry_count"` ≥ 1 000; if the count is lower the pipeline proceeds with the actual number (satisfies FR‑011/FR‑012).

- [ ] T002 **[P]** Convert CIF structures to graph representations and store the processed dataset.  
  *Script*: `code/data/graph_builder.py` (parses `structure` column with `pymatgen.CifParser`, builds node features [atomic number, electronegativity, covalent radius, group, period] and edge features [distance, electronegativity difference]).  
  *Outputs*: `data/processed/graphs_v1.parquet` (validated against `contracts/dataset_schema.yaml`).  
  *Verification*: A quick‑load test confirms the parquet file contains the required columns and at least the first row passes `graph.schema.yaml`.

- [ ] T003 **[P]** Generate a family‑aware train/validation/test split with element‑overlap control.  
  *Script*: `code/data/split_generator.py`  
  *Logic*:  
  1. Define **family** = `space_group` + stoichiometry class (derived from `formula`).  
  2. Compute an element‑overlap metric; require max shared‑element proportion ≤ 0.20 across splits.  
  3. Perform a stratified split (70 % train, 15 % val, 15 % test) using `sklearn.model_selection.train_test_split` with `random_state=42` and `stratify=family`.  
  4. Atomically write `data/processed/split_indices.json` (temp file → `os.rename`).  
  *Outputs*: `data/processed/split_indices.json` (conforms to `contracts/split_indices_schema.yaml`).  
  *Verification*: A sanity‑check prints the three split sizes and confirms `family_disjoint=True`.

- [ ] T004 **[P]** Validate the split and record a split‑validation report.  
  *Script*: `code/model/splitter.py` reads `split_indices.json`, checks that no family appears in more than one split, verifies the element‑overlap constraint, and writes `data/results/split_validation.json` according to `contracts/split_validation_schema.yaml`.  
  *Verification*: `split_validation.json` must contain `"family_disjoint": true` and `"passed": true`; the CI will fail otherwise.

---

## Phase 2 – Model training, evaluation & benchmarking  

- [ ] T005 **[P]** Train a lightweight CPU‑only Message‑Passing Neural Network (MPNN).  
  *Script*: `code/model/train.py`  
  *Key points*:  
  * Uses `torch.device("cpu")`.  
  * Architecture ≤ 2 message‑passing layers, hidden dimension ≤ 64.  
  * Records peak memory with `tracemalloc` and `psutil` (must be ≤ 16 GB).  
  * Performs 5‑fold family‑stratified cross‑validation (stores mean ± std of Young’s/shear MAPE and Poisson MAE).  
  * Saves `data/processed/model_v1.pt` (torch checkpoint) and `data/results/training_logs.json` (conforms to `contracts/training_logs_schema.yaml`).  
  *Verification*: `training_logs.json` includes `"peak_memory": {"within_limit": true}` and CV statistics; the script exits with error if memory exceeds the limit.

- [ ] T006 **[P]** Evaluate the trained surrogate on the held‑out test families, benchmark against a composition‑only baseline, and record inference latency.  
  *Script*: `code/model/eval_runner.py`  
  *Steps*:  
  1. Load `model_v1.pt` and `split_indices.json`.  
  2. Compute predictions for every test material, write `data/results/predictions.json` (schema `contracts/predictions_schema.yaml`).  
  3. Compute surrogate metrics (Young’s & shear MAPE, Poisson MAE) and baseline metrics (linear regression on Magpie descriptors).  
  4. Perform a paired‑bootstrap test (1 000 resamples) with Holm correction; store p‑values.  
  5. Measure per‑material CPU inference time with `time.perf_counter()`, store the array, median, and a boolean `within_limit` (≤ 200 ms) in `data/results/generalization_metrics.json` (schema `contracts/results_schema.yaml`).  
  *Verification*: `generalization_metrics.json` must have `"inference_time":{"within_limit":true}` and `"surrogate"` metrics meeting SC‑006 thresholds (≤ 15 % MAPE, ≤ 0.05 MAE).  

- [ ] T007 **[P]** Perform feature‑importance and ablation analysis to satisfy SC‑005.  
  *Script*: `code/analysis/feature_importance.py`  
  *Procedure*:  
  1. Compute permutation importance for each node‑feature column (drop in Young’s/shear MAPE).  
  2. Retrain the model with each column removed; record ΔMAPE (must be ≥ 2 pp for qualifying descriptors).  
  3. Compute SHAP values using `shap.KernelExplainer` on a 200‑sample subset; perform a permutation test (p < 0.05).  
  4. Select descriptors that (a) rank in the top 5 by permutation importance, (b) have SHAP ranking agreement, and (c) together contribute ≥ 70 % of total importance mass.  
  5. Write `data/results/feature_importance_report.md` summarizing the top 3–5 descriptors, ΔMAPE values, and SHAP plots.  
  *Verification*: The markdown must list at least three descriptors meeting all three criteria; the CI runs a lightweight parser to confirm.

---

## Phase 3 – Supporting scientific artifacts  

- [ ] T008 **[P]** Create the mandatory disclaimer template.  
  *File*: `code/utils/disclaimer_template.py` containing two constants:  
  ```python
  DISCLAIMER_TEXT = (
      "The surrogate model interpolates DFT‑computed elastic tensors; "
      "it does not solve the Schrödinger equation and therefore is not a "
      "first‑principles method."
  )
  FEYNMAN_QUOTE = "The first principle is that you must not fool yourself—and you are the easiest person to fool."
  ```  
  *Verification*: All reporting scripts import `DISCLAIMER_TEXT` and `FEYNMAN_QUOTE`; CI checks that the file exists and the constants match exactly.

- [ ] T009 **[P]** Document an end‑to‑end runnable command in `docs/quickstart.md`.  
  *Content*: a step‑by‑step guide that (1) runs `python -m code.data.loader`, (2) `python -m code.data.graph_builder`, (3) `python -m code.data.split_generator`, (4) `python -m code.model.train`, (5) `python -m code.model.eval_runner`, and (6) `python -m code.analysis.feature_importance`.  
  *Verification*: The CI executes the command sequence on a tiny sampled subset (first 100 materials) to ensure no runtime errors; the script prints the paths of the generated artifacts.

---

### Dependency summary
| Task | Depends on |
|------|------------|
| T060c | – |
| T001 | – |
| T002 | T001 |
| T003 | T002 |
| T004 | T003 |
| T005 | T004 |
| T006 | T005 |
| T007 | T006 |
| T008 | – (independent) |
| T009 | All previous tasks (to guarantee the command works) |

All tasks are unchecked (`[ ]`) so that the verifier can confirm the required artifacts are produced during the next execution pass. Completed infrastructure work from earlier iterations (directory creation, logging scaffolds, etc.) has been folded into the relevant scripts and does not need separate checklist items.
