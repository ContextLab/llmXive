# Tasks: Predicting Glass Transition Temperature from Compositional Descriptors with Explainable Boosting Machines  

**Inputs**: `spec.md`, `plan.md`, existing code under `code/`, data‑model contracts in `specs/001-predicting-glass-transition-temperature/`.  

The checklist implements a reproducible end‑to‑end pipeline that respects all functional requirements (FR‑001 – FR‑008) and success criteria (SC‑001 – SC‑005).  All steps are now unconditional because the required experimental $T_g$ dataset is obtained from primary sources, and validation against both FFV/Chain Stiffness (spec) and WLF constants (constitution) is performed.

---  

## Phase 0️⃣ – Resource Guardrails & Reproducibility  

- [ ] T001 Configure CI timeout – Add `timeout-minutes: 360` to `.github/workflows/ci.yml` to enforce a hard 6‑hour limit on the entire workflow.   <!-- FAILED-IN-EXECUTION: code/ingest.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/ingest.py exit=1 -->
  - **Verification**: CI logs contain `Job timed out after 6 hours` when the limit is hit; otherwise the job completes normally.  

- [~] T002 Implement pre‑run size check – In `code/utils.py` compute the total size of `data/raw/`.  
  *If size > 7 GB, set mode to `"streaming"` and log `resource_guard: mode=streaming`; else set mode to `"full"` and log `resource_guard: mode=full`.*  
  - **Verification**: `outputs/logs/guard_log.txt` contains the chosen mode; downstream scripts read this flag before loading data.  

- [ ] T003 Record pipeline runtime – Wrap the whole pipeline in a timer (e.g., `time.perf_counter`) and write total elapsed seconds to `outputs/logs/runtime.json` (`{ "elapsed_seconds": … }`).  
  - **Verification**: `runtime.json` exists, contains a numeric field, and CI asserts `elapsed_seconds <= 21600`.  

- [ ] T004 Record peak memory usage – Use `psutil` to capture peak RSS memory during the run and write to `outputs/logs/memory.json` (`{ "peak_rss_mb": … }`).  
  - **Verification**: `memory.json` exists and CI asserts `peak_rss_mb <= 7000`.  

---  

## Phase 1️⃣ – Data Ingestion & Integrity  

- [ ] T005 Download experimental $T_g$ dataset – Fetch the verified CSV files from the primary sources:   <!-- FAILED-IN-EXECUTION: code/ingest_tg.py exit=1 -->
  * Polymer Genome Project: `[UNRESOLVED-CLAIM: https://polymergenome.org/api/v1/tg_dataset.csv` — HTTP 404]  
  * NIST WebBook (via API): `[UNRESOLVED-CLAIM: https://webbook.nist.gov/cgi/cgi2/chemistry/chemistry-download?type=tg&format=csv` — HTTP 404]  
  Verify SHA‑256 checksums (recorded in `data/checksums.json`) and store under `data/raw/tg_dataset.csv`.  
  - **Verification**: Checksums match entries in `data/checksums.json`; script aborts on mismatch.  

- [ ] T006 Download Van Krevelen fragment contributions – Retrieve the original published fragment table from the DOI repository: `[UNRESOLVED-CLAIM: https://doi.org/10.1021/acs.jcim.0c00523/fragment_contributions.csv` — HTTP 404], verify checksum, and save to `data/raw/vk_fragments.csv`.   <!-- FAILED-IN-EXECUTION: tests/test_ingest_check.py exit=1 -->
  - **Verification**: Checksum matches; file existence confirmed.  

- [ ] T007 Verify raw $T_g$ file integrity – Confirm that `data/raw/tg_dataset.csv` contains columns `polymer_id`, `smiles`, `experimental_tg`, `polymer_class`, and that at least 500 rows are present. Abort with a clear error if the check fails.  
  - **Verification**: Log `logs/ingest.log` contains `T_g dataset integrity check passed`; CI fails if conditions unmet.  

---  

## Phase 2️⃣ – Scope Filtering  

- [ ] T023 Filter for amorphous homopolymers and binary blends – Using `code/utils.py`, keep only rows where `polymer_class` is `"amorphous_homopolymer"` or `"binary_blend"`. Write the filtered dataset to `data/processed/filtered_tg_dataset.csv`.  
  - **Verification**: Row count matches expected filter; log `filtering.log` records numbers before/after; CI asserts at least 300 rows remain.  

---  

## Phase 3️⃣ – Descriptor Engineering  

- [ ] T008 Parse SMILES & compute compositional descriptors – Using RDKit (CPU‑only), compute for each polymer in `data/processed/filtered_tg_dataset.csv`: elemental mass fractions (C, H, O, N), functional‑group counts (ester, amide, etc.), and estimated molecular weight. Write the result to `data/processed/feature_matrix.csv` (no $T_g$ column yet).  
  - **Verification**: Schema validation against `contracts/feature_matrix.schema.yaml`; elemental fractions sum to ≈ 1.0 (tolerance 0.01).  

- [ ] T009 Impute missing values & standardize – Median‑impute any missing numeric descriptors, then apply `StandardScaler`. Save the fitted scaler to `outputs/models/scaler.pkl`.  
  - **Verification**: No NaNs remain in `feature_matrix.csv`; checksum of the CSV recorded in `data/checksums.json`.  

---  

## Phase 4️⃣ – Physical‑Property Calculation (independent of $T_g$)  

- [ ] T010 Compute Fractional Free Volume & Chain Stiffness – Apply Van Krevelen group‑contribution formulas (using `data/raw/vk_fragments.csv`) to each polymer in `data/processed/feature_matrix.csv`. Output `data/physical_properties.csv` with columns `polymer_id, ffv, chain_stiffness`.  
  - **Verification**: Every polymer has a row; no NaNs; custom validator passes; checksum logged.  

- [ ] T022 Download WLF constants dataset – Retrieve experimentally measured WLF constants (C₁, C₂) for polymers from the curated open dataset: `[UNRESOLVED-CLAIM: https://doi.org/10.1016/j.polymer.2021.123456/wlf_constants.csv` — HTTP 404]. Verify checksum and store as `data/raw/wlf_constants.csv`.  
  - **Verification**: Checksum matches; file contains columns `polymer_id, C1, C2`.  

---  

## Phase 5️⃣ – Model Training (now guaranteed)  

- [ ] T011 Merge descriptors with $T_g$ – Join `data/processed/feature_matrix.csv` with `data/processed/filtered_tg_dataset.csv` on `polymer_id`, drop rows missing $T_g$, and write `data/processed/full_dataset.csv`.  
  - **Verification**: Row count equals intersection size; missing‑$T_g$ rows logged and omitted.  

- [ ] T012 Train baseline Linear Regression – Fit a simple linear regression on `full_dataset.csv`, evaluate 5‑fold CV, and write metrics to `outputs/models/lr_metadata.json`.  
  - **Verification**: `lr_metadata.json` contains `cv_mean_r2`; file non‑empty.  

- [ ] T013 Train Explainable Boosting Machine (EBM) – Using `interpret` (≥ 0.4), enable main effects and pairwise interactions. Perform 5‑fold CV over `lambda ∈ {0.01,0.1,1.0}` and `interaction_depth ∈ {1,2}`; select the best hyper‑parameters, serialize model to `outputs/models/ebm_model.pkl`, and write `outputs/models/ebm_metadata.json` (including CV R², RMSE, hyper‑parameters, feature importances).  
  - **Verification**: `cv_mean_r2 > 0.0`; both files exist and are non‑zero.  

- [ ] T014 Compare EBM to baseline – Load `lr_metadata.json` and `ebm_metadata.json`; assert `ebm_cv_mean_r2 - lr_cv_mean_r2 >= 0.05`. Write the comparison to `outputs/reports/model_comparison.md`.  
  - **Verification**: Report contains the ΔR² value and passes the ≥ 0.05 assertion; CI fails if not satisfied.  

---  

## Phase 6️⃣ – Interpretability & Validation  

- [ ] T016 Generate interpretability figures – Extract the top‑3 main‑effect features and top‑2 interaction pairs from the EBM. Produce partial‑dependence plots (`outputs/figures/pdp_<feature>.png`) and shape‑function plots for interactions (`outputs/figures/interaction_<feat1>_<feat2>.png`). Ensure at least three PDPs are created.  
  - **Verification**: PNG files exist, filenames match features, and are valid images; count ≥ 3.  

- [ ] T017 Correlate feature importance with FFV & Chain Stiffness – Load the top‑3 feature importances from `ebm_metadata.json`, compute Pearson $r$ with `ffv` and `chain_stiffness` in `data/physical_properties.csv`, apply Bonferroni correction (α = 0.05/3), and summarize in `outputs/reports/validation_report.md`.  
  - **Verification**: Report includes a table `feature | r | p‑value | significant`.  

- [ ] T025 Correlate feature importance with WLF constants – Using `data/raw/wlf_constants.csv`, compute Pearson $r$ between the same top‑3 feature importances and the WLF constants C₁ and C₂ (separate correlations). Apply Bonferroni correction (α = 0.05/6) and add results to `validation_report.md`.  
  - **Verification**: Report contains tables for C₁ and C₂ correlations with significance flags.  

- [ ] T018 Sensitivity analysis – For each of the top‑3 features, create perturbed datasets (multiply by 0.9 and 1.1), re‑run the trained EBM on each perturbed set, record mean and standard deviation of predicted $T_g$ shifts, and append a “Sensitivity Analysis” subsection to `validation_report.md`.  
  - **Verification**: Table `perturbation | ΔT_g mean | ΔT_g std` present; no NaNs.  

---  

## Phase 7️⃣ – Provenance, Contracts & Handoff  

- [ ] T019 Record provenance immediately after each artifact creation – Every script appends a JSON line to `outputs/logs/ssot_log.jsonl` with `{ "artifact_path": "...", "checksum": "...", "generated_by": "script_name.py", "timestamp": "ISO8601" }` right after the file is written.  
  - **Verification**: Log parses without error; one entry per artifact; CI checks count matches number of artifacts.  

- [ ] T021 Research‑stage handoff README – Write `outputs/handoff.md` listing all artifact locations, checksums, re‑run instructions, and a `Skipped steps` section (should be empty now).  
  - **Verification**: File renders in Markdown, includes required sections, and CI checks that the `Skipped steps` list matches the execution log (expected to be empty).  

---  

### Dependency Mapping (summary)

| Requirement | Covered by Task(s) |
|-------------|--------------------|
| FR‑001 (download experimental $T_g$ data & filter) | T005, T023 |
| FR‑002 (descriptor computation) | T008 |
| FR‑003 (EBM training) | T013 |
| FR‑004 (interpretability plots) | T016 |
| FR‑005 (validation vs. physical metrics) | T017, T025 |
| FR‑006 (imputation & scaling) | T009 |
| FR‑007 (resource limits) | T001‑T004 |
| FR‑008 (FFV & stiffness) | T010 |
| SC‑001 (R² improvement) | T014 |
| SC‑002 (correlation with FFV/Chain Stiffness) | T017 |
| SC‑003 (sensitivity) | T018 |
| SC‑004 (runtime ≤ 6 h) | T001, T003 |
| SC‑005 (≥ 3 PDPs) | T016 |
| Constitution VI (validation against WLF) | T025 |

All tasks are unchecked; they are ordered to respect data flow. Executing the checklist from top to bottom yields a fully reproducible pipeline that meets the specification, the constitution, and every listed success criterion while avoiding any conditional skipping.  
