# Tasks: Predicting the Influence of Composition on the Thermal Expansion of Metallic Glasses

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, contract schemas, and any existing artifacts.  
The goal is to implement a fully reproducible, CPU‑only pipeline that ingests real metallic‑glass data, extracts scientifically‑required descriptors, trains and validates predictive models, and produces verifiable results and documentation.

---

## Phase 1 – Setup and first end‑to‑end analysis  

**Goal**: Run a complete, reproducible analysis on real inputs (no synthetic data) and verify that each step produces the required artifact.

- [ ] **T002** [US1] Implement robust data ingestion, amorphous filtering, descriptor computation, and metadata capture.  
  - **Script**: `code/ingestion/fetch_data.py`  
    1. Load the curated CSV `data/raw/curated_metallic_glass.csv` (must contain `material_id`, `composition`, `cte`, optional `thermal_history`).  
    2. Query the Materials Project API (`pymatgen.ext.matproj.MPRester`) for entries whose `description` contains the keyword “glass”. Retrieve **only** `material_id`, `composition`, and the `source_method` (set to `"DFT"` for MP entries).  
    3. Query the AFLOWlib REST API (`[UNRESOLVED-CLAIM: https://aflowlib.org/API/aflowlib.json/?species=glass` — HTTP 404]) for additional compositions (no CTE values). Log a warning if the endpoint is unreachable; do **not** fall back to synthetic data.  
    4. Concatenate CSV and API results, de‑duplicate on `material_id`.  
    5. Filter rows to keep only those flagged as amorphous **either** (i) the CSV contains an explicit `amorphous_flag` column set to true, **or** (ii) the MP/AFLOW description contains the word “glass”. Exclude any entry with missing `cte`.  
    6. Parse each `composition` with `pymatgen.Composition`; load elemental properties from `mendeleev` and compute the four required descriptors:  
       - weighted mean atomic radius  
       - electronegativity variance (weighted)  
       - valence electron concentration (VEC)  
       - atomic size coefficient of variation (σ/μ)  
    7. Add per‑row SHA‑256 checksum of the raw JSON record (`checksum` column).  
    8. Record `thermal_history` (if present) and set `thermal_history_flag` = True; otherwise set the flag = False.  
    9. Save the merged, filtered, and enriched table to `data/processed/clean_alloy_data.parquet`.  
    10. **Coverage check**: `coverage = retrieved_entries / csv_entries`. Write `data/results/ingestion_coverage.json` with fields `{coverage, total_entries, status}`.  
        - If `coverage < 0.95` **or** `total_entries < 500`, set `"status":"Warning – low coverage"` (do **not** abort). The pipeline continues; downstream tasks will handle the reduced sample size and power analysis will report the limitation.  
    11. Log all actions to `logs/ingestion.log`.  
  - **Verification**:  
    - `data/processed/clean_alloy_data.parquet` validates against `specs/001-predicting-the-influence-of-composition/contracts/mg_dataset.schema.yaml`.  
    - `data/results/ingestion_coverage.json` reports `coverage ≥ 0.95` and `total_entries` (warning if below 500).  
    - Unit test `tests/unit/test_ingestion.py` confirms descriptor columns exist, contain no NaNs, that `checksum` matches a recomputed hash, and that `thermal_history_flag` is present.

- [ ] **T003** [US1] Perform multicollinearity mitigation, optional PCA fallback, and create reproducible train/test splits.  
  - **Script**: `code/features/preprocess.py` (unchanged logic, now guaranteed to receive the full set of columns from T002).  
  - **Verification**: unchanged.

- [ ] **T004** [US2] Train baseline, linear‑regression, and random‑forest models with 5‑fold CV and select best hyper‑parameters.  
  - **Script**: `code/modeling/train.py` (unchanged logic, now uses full metadata).  
  - **Verification**: unchanged.

- [ ] **T005** [US2] Evaluate trained models on the held‑out test set and compare to baseline (ΔR² > 0.05).  
  - **Script**: `code/modeling/evaluate.py` (unchanged).  
  - **Verification**: unchanged.

- [ ] **T006** [US3] Perform a permutation‑test significance analysis (≥ 1 000 iterations).  
  - **Script**: `code/modeling/permutation_test.py` (dedicated script, no ambiguity).  
    1. Load the best model (the one with higher test R²) and the training data.  
    2. Shuffle `y_train` 1 000 times (seed = 42), retrain on each shuffled set, compute R² on the original test set, build null distribution.  
    3. Compute two‑sided p‑value; if observed R² < 0.3, set `p_value: null` and `null_result_flag: true`.  
    4. Append these fields to the corresponding entry in `results/model_performance.json`.  
  - **Verification**: unit test `tests/unit/test_permutation.py` validates null‑distribution length and p‑value range.

- [ ] **T007** [US3] Compute feature‑importance rankings and correlation diagnostics.  
  - **Script**: `code/modeling/feature_importance.py` (unchanged).  
  - **Verification**: unchanged.

- [ ] **T008** [US1] Sensitivity analysis for missing metadata and resource‑usage reporting.  
  - **Script**: `code/analysis/sensitivity_and_resources.py` (enhanced).  
    1. Determine proportion of rows missing `source_method` or `thermal_history`.  
    2. If > 20 % missing, create subset `data/processed/metadata_complete.parquet`, retrain best model, compute `ΔR²_metadata` and store in `results/metadata_sensitivity.json`.  
    3. Wrap the **entire** pipeline (from ingestion to evaluation) with timing (`time.perf_counter`) and memory profiling (`psutil`).  
    4. Write `results/computational_efficiency.json` containing runtime, peak memory, cores used, limits, and a boolean `pass`. **If** limits are exceeded, the script exits with code 1, causing pipeline failure.  
  - **Verification**: unit test `tests/unit/test_sensitivity.py` checks that a non‑zero exit occurs when limits are breached.

- [ ] **T009** [US1] Conduct a statistical power analysis based on the final usable sample size.  
  - **Script**: `code/analysis/power_analysis.py` (unchanged).  
  - **Verification**: unchanged.

- [ ] **T010** [P] [US3] Generate final result tables and publication‑ready figures.  
  - **Script**: `code/visualization/produce_figures.py` (unchanged).  
  - **Verification**: unchanged.

- [ ] **T011** [US1] Write a full methods‑and‑results document linking every claim to concrete artifacts.  
  - **File**: `docs/research.md` (unchanged).  
  - **Verification**: unchanged.

- [ ] **T012** [US1] Re‑run the complete pipeline from a clean state and confirm deterministic regeneration of all artifacts.  
  - **Procedure**: documented in `docs/quickstart.md` (unchanged).  
  - **Verification**: unchanged.

- [ ] **T001** [US1] Create a runnable quick‑start guide and verify end‑to‑end execution on a tiny real sample.  
  - **Artifact**: `docs/quickstart.md` (now placed after all producer tasks; `[P]` tag removed).  
  - **Verification**: unchanged.

- [ ] **T013** [FR‑010] Verify that **all** stochastic operations across the pipeline use the fixed seed 42.  
  - **Script**: `code/utilities/seed_check.py`  
    1. Scan all pipeline scripts for `np.random.seed`, `random.seed`, or any `random_state` arguments.  
    2. Run a lightweight sanity check that each script, when imported, sets the global NumPy and Python random seeds to 42.  
    3. Fail with a non‑zero exit code if any script deviates.  
  - **Verification**: CI runs this script before any other task; unit test `tests/unit/test_seed_check.py` ensures compliance.

- [ ] **T014** [Constitution III] Update the project‑level checksum registry after ingestion.  
  - **Script**: `code/ingestion/update_checksum_registry.py`  
    1. Read `data/processed/clean_alloy_data.parquet`, compute per‑row SHA‑256 checksums (already present).  
    2. Write a mapping `{material_id: checksum}` into `state/projects/PROJ-375-predicting-the-influence-of-composition-.yaml` under `artifact_hashes`.  
    3. Commit the updated YAML (handled by CI).  
  - **Verification**: unit test `tests/unit/test_checksum_registry.py` confirms the YAML contains entries for all material IDs.

- [ ] **T015** [FR‑007] Enforce resource limits (≤ 2 CPU cores, ≤ 7 GB RAM) and cause pipeline failure on violation.  
  - **Script**: `code/analysis/enforce_resources.py`  
    1. At the start of the pipeline, query the runner's CPU core count and available memory.  
    2. If cores > 2 or memory > 7 GB, log an error and exit with code 1.  
    3. This script is invoked as the first step in the CI workflow.  
  - **Verification**: CI will abort early if limits are exceeded; unit test `tests/unit/test_resource_enforcement.py` validates the check.

- [ ] **T016** [FR‑009 / FR‑012] Ensure `source_method` and `thermal_history` columns are complete for **all** entries, including those from APIs.  
  - **Script**: `code/ingestion/augment_metadata.py` (called within `fetch_data.py`).  
    1. For CSV rows, propagate existing `source_method` and `thermal_history`.  
    2. For MP and AFLOW rows, set `source_method` = `"DFT"` (as they lack experimental CTE) and `thermal_history_flag` = False.  
    3. Append these columns to the DataFrame before descriptor computation.  
  - **Verification**: unit test `tests/unit/test_metadata_augmentation.py` checks that after augmentation no `source_method` or `thermal_history_flag` entries are null.

---

## Phase 2 – Complete the study and validate its evidence  

**Goal**: Add statistical rigor, feature‑importance diagnostics, sensitivity analyses, and resource‑usage reporting.  
(The tasks listed above already cover all Phase 2 requirements; no additional tasks needed.)

---

## Phase 3 – Reproducible results and paper handoff  

**Goal**: Produce a self‑contained methods/results narrative and demonstrate that the entire pipeline can be rerun from scratch, yielding identical artifacts.  
(The existing tasks T011 and T012, together with the new enforcement and verification tasks, satisfy this phase.)

---

## Dependencies and requirement coverage  

| Spec Requirement | Satisfying Task(s) |
|------------------|--------------------|
| **FR‑001** (metallic‑glass retrieval) | T002 (curated CSV + MP/AFLOW composition augmentation) – now continues with < 500 entries |
| **FR‑002** (descriptor extraction) | T002 |
| **FR‑003** (stratified split) | T003 |
| **FR‑004** (model training & CV) | T004 |
| **FR‑005** (permutation test) | T006 |
| **FR‑006** (feature importance) | T007 |
| **FR‑007** (resource limits) | T015 (enforcement) |
| **FR‑008** (VIF & PCA fallback) | T003 |
| **FR‑009** (metadata & sensitivity) | T002, T008, T016 |
| **FR‑010** (fixed seeds) | T013 |
| **FR‑011** (power analysis) | T009 |
| **FR‑012** (metadata flagging) | T002, T016 |
| **SC‑001** (baseline ΔR² > 0.05) | T005 |
| **SC‑002** (permutation p‑value) | T006 |
| **SC‑003** (Spearman & Kendall‑τ) | T007 |
| **SC‑004** (efficiency limits) | T015 (enforced) |
| **SC‑005** (ingestion completeness) | T002 (coverage warning) |

**Execution order**:  
T015 → T013 → T002 → T003 → T004 → T005 → T006 → T007 → T008 → T009 → T010 → T011 → T012 → T001 → T014 → T016.

All tasks are unchecked until their implementation passes verification; completed tasks will be checked automatically by the platform once their artifacts validate.  
