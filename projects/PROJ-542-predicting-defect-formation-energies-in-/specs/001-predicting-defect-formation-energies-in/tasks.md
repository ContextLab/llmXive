# Tasks: Predicting Defect Formation Energies in Perovskites with Machine Learning  

**Inputs**: `spec.md`, `plan.md`, reviewer comments, existing project skeleton (`src/`, `data/`, `figures/`, `contracts/`).  

The tasks below cover every functional requirement (FR‑001 – FR‑012), success criteria (SC‑001 – SC‑005), and edge‑case handling described in the specification and plan. They are ordered to respect data flow and include an early executable end‑to‑end run.

---

## Phase 1 – Data acquisition, feature engineering, and validation  

| Goal | Run a minimal pipeline that produces a validated feature matrix from real Materials Project data. |
|------|---------------------------------------------------------------------------------------------------|

- [X] **T001** [US‑1] Create a `quickstart.md` that documents the single command to run the full pipeline (`python -m src.pipeline.run`).  
  *File:* `quickstart.md`  
  *Verification:* The command executes on a fresh GitHub Actions runner, prints “Pipeline completed successfully”, and the CI test `src/tests/test_quickstart.py` asserts the success message (fulfills FR‑010 and SC‑004).  

- [ ] **T002** [US‑1] Implement `src/data/download.py` to fetch oxygen‑vacancy defect formation energies for perovskites from the Materials Project API (API key read from `MP_API_KEY`).   <!-- FAILED-IN-EXECUTION: src/data/download.py exit=1 --> <!-- FAILED-IN-EXECUTION: src/data/download.py exit=1 -->
  *File:* `src/data/download.py` → output `data/raw/materials_defects.csv`  
  *Verification:*  
  – If `MP_API_KEY` is missing, the script aborts with a clear error message.  
  – If the API returns zero records, the script aborts with the exact error `"No data found for specified filters."` (FR‑007).  
  – When successful, the CSV is validated against `contracts/raw_dataset.schema.yaml` (FR‑001) and contains ≥ 500 rows.  

- [ ] **T003** [US‑1] Implement `src/data/featurize.py` to compute the twelve compositional descriptors (atomic radius, Pauling electronegativity, oxidation state, valence electron count for A, B, X) using **pymatgen**.  
  *File:* `src/data/featurize.py` → output `data/processed/features.csv`  
  *Verification:*  
  – Rows where any oxidation state cannot be determined are dropped; the script logs the number of excluded rows (FR‑008).  
  – The resulting CSV has exactly 12 descriptor columns plus the target `formation_energy` and no missing values in the target column (FR‑002).  

- [ ] **T004** [US‑1] Add a validation step `src/data/validate.py` that checks dataset size and performs a simple power analysis.  
  *File:* `src/data/validate.py` → log `data/processed/validation.log`  
  *Verification:*  
  – Raises `ValueError` if rows < 50 (FR‑009).  
  – Emits a warning if rows < 500 but continues, logging the achieved statistical power (SC‑005).  

- [ ] **T013** [FR‑006] After featurization, run `src/utils/check_descriptor_gaps.py` to scan the feature matrix for any missing descriptor columns (e.g., absent radius or electronegativity values) and log each gap with row identifiers.  
  *File:* `src/utils/check_descriptor_gaps.py` → appends a “descriptor_gaps.log” in `data/processed/`.  
  *Verification:* The log is created and the CI test asserts that if any gaps are found the pipeline aborts with a clear message, satisfying FR‑006.  

- [ ] **T015** [Constitution‑III] Compute SHA‑256 checksums for `data/raw/materials_defects.csv` immediately after download and write them to `data/checksums/raw_defects.sha256`.  
  *File:* `src/utils/checksum.py` (invoked by the pipeline).  
  *Verification:* CI test confirms the checksum file exists and matches the file content.  

- [ ] **T016** [Constitution‑III] Compute SHA‑256 checksums for `data/processed/features.csv` after featurization (including after any gap‑checking) and write to `data/checksums/features.sha256`.  
  *File:* `src/utils/checksum.py` (second invocation).  
  *Verification:* CI test asserts the checksum file exists and matches the current `features.csv`.  

---

## Phase 2 – Model training, evaluation, and fallback augmentation  

| Goal | Produce cross‑validated models, evaluate on a held‑out test set, and automatically augment descriptors if performance thresholds are not met. |
|------|------------------------------------------------------------------------------------------------------------------------------------------|

- [ ] **T005** [US‑2] Implement `src/models/train.py` to perform **5‑fold GroupKFold** CV (group = full composition string) for **RandomForestRegressor** and **GradientBoostingRegressor** (scikit‑learn, `n_jobs=1`, `random_state=42`).  
  *File:* `src/models/train.py` → outputs `models/rf_cv.pkl`, `models/gb_cv.pkl`, and `data/processed/cv_metrics.json`.  
  *Verification:*  
  – The script runs on CPU‑only runners (no CUDA import).  
  – `cv_metrics.json` conforms to `contracts/model_performance.schema.yaml` (FR‑003).  

- [ ] **T006** [US‑2] Create a deterministic 80/20 **train‑test split** (`src/models/split.py`) that respects GroupKFold groups (no overlap).  
  *File:* `src/models/split.py` → outputs `data/processed/train.csv` and `data/processed/test.csv`.  
  *Verification:* The split logs the number of samples in each set and confirms zero intersection with CV groups (FR‑011).  

- [ ] **T007** [US‑3] Implement `src/models/evaluate.py` to:  
  1. Load the best model (lowest mean CV RMSE).  
  2. Predict on `test.csv`.  
  3. Compute RMSE, MAE, R².  
  4. Bootstrap 10 000 resamples for a 95 % CI of RMSE.  
  5. Perform a paired two‑sided t‑test (α = 0.05) between predictions and DFT values.  
  *File:* `src/models/evaluate.py` → outputs `data/processed/performance.json`, `figures/pred_vs_actual.png`.  
  *Verification:* `performance.json` validates against the model‑performance schema (FR‑004). The scatter plot includes a 1:1 reference line (FR‑005).  

- [ ] **T008** [US‑3] Generate a ranked feature‑importance bar chart (`src/models/feature_importance.py`).  
  *File:* `src/models/feature_importance.py` → output `figures/feature_importance.png`.  
  *Verification:* The chart lists all descriptors in descending order of normalized importance (sum = 1) and matches the `feature_importances` array in `performance.json` (FR‑005).  

- [ ] **T009** [US‑3] **Fallback augmentation** – If the decision rule in T007 fails (RMSE > 0.5 eV **or** R² < 0.70 **or** p‑value ≤ 0.05), automatically:  
  1. Extend `features.csv` with structural descriptors (coordination numbers, average bond lengths, crystal symmetry class) computed via pymatgen.  
  2. Overwrite `data/processed/features.csv` (checksum refreshed).  
  3. Re‑run T005–T008 on the augmented matrix.  
  *File:* `src/data/augment_structural.py` (called from the pipeline).  
  *Verification:* After augmentation, `performance.json` is regenerated, the script logs that augmentation was triggered and the new descriptor count (13 or more), and task T017 verifies the refreshed checksum.  

- [ ] **T017** [Constitution‑III] After fallback augmentation, recompute the SHA‑256 checksum for the overwritten `data/processed/features.csv` and write to `data/checksums/features.sha256` (overwriting the previous entry).  
  *File:* `src/utils/checksum.py` (third invocation).  
  *Verification:* CI test asserts that the new checksum differs from the pre‑augmentation checksum and matches the updated file.  

---

## Phase 3 – Reproducibility, contract validation, runtime enforcement, and handoff  

| Goal | Provide a single notebook that runs the whole study reproducibly, verify all contracts, enforce runtime limits, and prepare the methods/results handoff for the paper stage. |
|------|-------------------------------------------------------------------------------------------------------------------------------------------------|

- **T010** [US‑1] Assemble `src/pipeline.ipynb` that sequentially calls the scripts from T002–T009, displays intermediate tables, and saves all artefacts.  
  *File:* `src/pipeline.ipynb`  
  *Verification:* Running the notebook from a fresh environment reproduces every file listed above and ends with the message “Pipeline completed successfully”.  

- **T011** Add pytest‑based contract tests (`src/tests/test_contracts.py`) that load `data/raw/materials_defects.csv` and `data/processed/performance.json` and validate them against `contracts/raw_dataset.schema.yaml` and `contracts/model_performance.schema.yaml`.  
  *File:* `src/tests/test_contracts.py`  
  *Verification:* All tests pass on CI; any schema violation aborts the run.  

- **T012** Write `paper/methods_results.md` that briefly describes the methodology, cites the exact artefact filenames (`features.csv`, `performance.json`, PNGs), and notes any fallback activation.  
  *File:* `paper/methods_results.md`  
  *Verification:* The markdown includes hyperlinks to the artefacts and a statement that the notebook produces identical outputs, satisfying the handoff requirement (Phase 3).  

- **T014** [SC‑004] Implement `src/utils/timer.py` that wraps the end‑to‑end pipeline execution, logs the elapsed wall‑clock time to `data/processed/runtime.log`, and fails the run if total time exceeds 1800 seconds (30 minutes).  
  *File:* `src/utils/timer.py` (integrated into `src/pipeline.ipynb` and the CI entrypoint).  
  *Verification:* CI test asserts the logged runtime ≤ 1800 s; otherwise the job is marked failed.  

- **T018** [US‑1] Add a CI test `src/tests/test_quickstart.py` that runs the command documented in `quickstart.md` on a clean runner and asserts that the stdout contains “Pipeline completed successfully”. This directly validates T001’s quickstart documentation.  

- **T015** (already listed) ensures checksum creation after download, satisfying Constitution III.  

- **T016** (already listed) ensures checksum creation after featurization, satisfying Constitution III.  

---

### Dependency & Requirement Mapping  

| Requirement | Satisfying Task(s) |
|-------------|--------------------|
| FR‑001, FR‑006, FR‑007 | T002 |
| FR‑002, FR‑008 | T003 |
| FR‑009 | T004 |
| FR‑003 | T005 |
| FR‑011 | T006 |
| FR‑004, SC‑001, SC‑002, SC‑003 | T007 |
| FR‑005 | T008 |
| FR‑012 (fallback) | T009 |
| FR‑010 | T010, T011 |
| SC‑004, SC‑005 | T001, T004, T014 |
| Contract schemas | T011 |
| Documentation & handoff | T012 |
| FR‑006 (explicit gap flagging) | T013 |
| Constitution III (checksums) | T015, T016, T017 |
| Runtime enforcement | T014 |
| Quickstart verification | T018 |

All tasks are unchecked (☐) and ready for implementation. The ordering respects data flow: download → featurize → validate → split → train → evaluate → fallback (if needed) → notebook → tests → handoff.  

--- 

# End of tasks.md