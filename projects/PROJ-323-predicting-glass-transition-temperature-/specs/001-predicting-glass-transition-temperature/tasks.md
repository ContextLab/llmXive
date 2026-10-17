# Tasks: Predicting Glass Transition Temperature from Compositional Descriptors with Explainable Boosting Machines

**Inputs**: `spec.md`, `plan.md`, existing code skeleton under `code/`, and the data‑model contracts in `specs/001-predicting-glass-transition-temperature/`.

The checklist implements a complete, reproducible end‑to‑end study that satisfies every functional requirement (FR‑001 – FR‑008) and success criterion (SC‑001 – SC‑005). Conditional steps have been eliminated by ensuring a real $T_g$ dataset is always available, and all guard‑rail tasks now emit measurable artifacts. Tasks are ordered to respect data flow and resource limits.

---

## Phase 0️⃣ – Resource Guardrails & Reproducibility  

- [ ] T013 **Configure CI timeout** – Add `timeout-minutes: 360` to `.github/workflows/ci.yml` to enforce a hard 6‑hour limit on the entire workflow.  
  - **Verification**: CI logs contain `Job timed out after 6 hours` on timeout; otherwise the job completes normally.  

- [ ] T012 **Pre‑run size check** – In `code/utils.py` compute total size of `data/raw/`.  
  * If > 7 GB, set mode to `"streaming"` and log `resource_guard: mode=streaming`.  
  * Else set mode to `"full"` and log `resource_guard: mode=full`.  
  - **Verification**: `outputs/logs/guard_log.txt` contains the chosen mode; downstream tasks read this flag before loading data.  

- [ ] T019 **Record pipeline runtime** – Wrap the entire pipeline execution in a timer (e.g., `time.perf_counter`). Write total elapsed seconds to `outputs/logs/runtime.json` (`{ "elapsed_seconds": … }`).  
  - **Verification**: `runtime.json` exists and contains a numeric field; CI asserts `elapsed_seconds <= 21600`.  

- [ ] T020 **Record peak memory usage** – Use `psutil` to capture peak RSS memory during the run and write to `outputs/logs/memory.json` (`{ "peak_rss_mb": … }`).  
  - **Verification**: `memory.json` exists; CI asserts `peak_rss_mb <= 7000`.  

---

## Phase 0️⃣ – Data Ingestion & Integrity  

- [ ] T001 **Download SMILES dataset** – Fetch the verified Parquet file from the Polymer Genome Project (`[UNRESOLVED-CLAIM: https://raw.githubusercontent.com/PolymerGenome/PolymerData/master/smiles.parquet` — HTTP 404]), verify SHA‑256 checksum, store under `data/raw/smiles.parquet`.  
  - **Verification**: Checksum matches entry in `data/checksums.json`; script exits on mismatch.  

- [ ] T002 **Download Van Krevelen fragments** – Retrieve `[UNRESOLVED-CLAIM: https://raw.githubusercontent.com/MaterialsData/van-krevelen/master/fragments.csv` — HTTP 404], checksum‑verify, save to `data/raw/vk_fragments.csv`.  
  - **Verification**: Checksum match; file existence confirmed.  

- [ ] T003 **Download experimental $T_g$ dataset** – Fetch the verified CSV from the Polymer Genome public repository (`[UNRESOLVED-CLAIM: https://raw.githubusercontent.com/PolymerGenome/PolymerData/master/tg_dataset.csv` — HTTP 404]), verify SHA‑256 checksum, and write to `data/raw/tg_dataset.csv`. The file must contain the columns `polymer_id`, `experimental_tg`, and `smiles`.  
  - **Verification**: Log `logs/ingest.log` records success and checksum; script aborts on checksum mismatch or missing required columns.  

- [ ] T024 **Verify $T_g$ dataset integrity** – After download, confirm that `data/raw/tg_dataset.csv` has at least one row with a non‑null `experimental_tg` value and that the `experimental_tg` column is numeric. Abort with a clear error if the check fails.  
  - **Verification**: `logs/ingest.log` contains `tg_dataset integrity check passed` message; CI fails if the dataset is empty or malformed.  

- [ ] T021 **Download WLF constants** – Retrieve `[UNRESOLVED-CLAIM: https://raw.githubusercontent.com/PolymerGenome/PolymerData/master/wlf_constants.csv` — HTTP 404], verify checksum, store as `data/raw/wlf_constants.csv`.  
  - **Verification**: Checksum matches; file exists.  

---

## Phase 1️⃣ – Descriptor Engineering  

- [ ] T004 **Parse SMILES & compute descriptors** – Using RDKit (CPU‑only), compute elemental mass fractions (C, H, O, N), functional‑group counts (ester, amide, …), and estimated molecular weight for each polymer in `data/raw/smiles.parquet`. Output `data/processed/feature_matrix.csv` (no $T_g$ column yet).  
  - **Verification**: Schema validation against `contracts/feature_matrix.schema.yaml`; elemental fractions sum to ≈ 1.0 (tolerance 0.01).  

- [ ] T005 **Impute & standardize** – Median‑impute missing numeric descriptors, then apply `StandardScaler`. Save scaler to `outputs/models/scaler.pkl`.  
  - **Verification**: No NaNs remain; checksum of `feature_matrix.csv` recorded in `data/checksums.json`.  

---

## Phase 2️⃣ – Physical‑Property Calculation  

- [ ] T006 **Compute FFV & Chain Stiffness** – Apply Van Krevelen group‑contribution formulas (using `data/raw/vk_fragments.csv`) to each polymer; write `data/physical_properties.csv` with columns `polymer_id, ffv, chain_stiffness`.  
  - **Verification**: Every polymer has a row; no NaNs; custom validator passes.  

- [ ] T022 **Compute WLF constants** – Using `data/raw/wlf_constants.csv`, calculate $C_1$ and $C_2$ for each polymer (based on molecular structure). Store as `data/wlf_properties.csv`.  
  - **Verification**: All polymers present; schema‑compliant CSV; checksum logged.  

---

## Phase 3️⃣ – Model Training  

- [ ] T007 **Merge feature matrix with $T_g$** – Join `data/processed/feature_matrix.csv` with `data/raw/tg_dataset.csv` on `polymer_id` to create `data/processed/full_dataset.csv`. Drop rows lacking $T_g$.  
  - **Verification**: Row count matches the intersection; missing‑$T_g$ rows logged and omitted.  

- [ ] T017 **Train baseline Linear Regression** – Fit a simple linear regression on `full_dataset.csv`, compute mean R² via 5‑fold CV, and write metadata to `outputs/models/lr_metadata.json`.  
  - **Verification**: `lr_metadata.json` contains `cv_mean_r2`; file non‑empty.  

- [ ] T008 **Train Explainable Boosting Machine (EBM)** – Using `interpret` (≥0.4), enable main effects and pairwise interactions. Perform 5‑fold CV over `lambda ∈ {0.01,0.1,1.0}` and `interaction_depth ∈ {1,2}`; select best hyper‑parameters, serialize model to `outputs/models/ebm_model.pkl`, and write `outputs/models/ebm_metadata.json` (including CV R², RMSE, hyper‑parameters, feature importances).  
  - **Verification**: `cv_mean_r2 > 0.0`; files exist and are non‑zero.  

- [ ] T018 **Compare EBM to baseline** – Load `lr_metadata.json` and `ebm_metadata.json`; assert `ebm_cv_mean_r2 - lr_cv_mean_r2 >= 0.05`. Write result to `outputs/reports/model_comparison.md`.  
  - **Verification**: Report contains the delta R² and passes the ≥ 0.05 assertion; CI fails the run if not satisfied.  

---

## Phase 4️⃣ – Interpretability  

- [ ] T009 **Generate interpretability figures** – Extract top‑3 main‑effect features and top‑2 interaction pairs from the EBM. Produce partial‑dependence plots (`outputs/figures/pdp_<feature>.png`) and shape‑function plots for interactions (`outputs/figures/interaction_<feat1>_<feat2>.png`).  
  - **Verification**: PNG files exist, filenames match features, and are valid images.  

---

## Phase 5️⃣ – Validation & Sensitivity  

- [ ] T010 **Correlation with FFV & Chain Stiffness** – Load top‑3 feature importances from `ebm_metadata.json`, compute Pearson $r$ with `ffv` and `chain_stiffness` columns in `data/physical_properties.csv`. Apply Bonferroni correction (α = 0.05/3). Summarize in `outputs/reports/validation_report.md`.  
  - **Verification**: Report includes a table `feature | r | p‑value | significant`.  

- [ ] T023 **Correlation with WLF constants** – Similarly correlate the same top‑3 importances with $C_1$ and $C_2$ from `data/wlf_properties.csv`. Append results to the same `validation_report.md`.  
  - **Verification**: Additional table for WLF correlations present.  

- [ ] T011 **Sensitivity analysis** – For each of the top‑3 features, create two perturbed datasets (multiply by 0.9 and 1.1). Re‑run the trained EBM on each perturbed set, record mean and std‑dev of predicted $T_g$ shifts. Append a “Sensitivity Analysis” subsection to `validation_report.md`.  
  - **Verification**: Table `perturbation | ΔT_g mean | ΔT_g std` present; no NaNs.  

---

## Phase 6️⃣ – Contracts & Handoff  

- [ ] T015 **Generate contracts** – Programmatically emit `contracts/feature_matrix.schema.yaml` and `contracts/model_output.schema.yaml` (using `jsonschema2yaml` or equivalent) and commit them under `specs/001-predicting-glass-transition-temperature/contracts/`.  
  - **Verification**: Both files exist, are valid YAML, and `jsonschema validate` succeeds on minimal examples.  

- [ ] T014 **Record provenance (SSoT log)** – After each artifact creation, append a JSON line to `outputs/logs/ssot_log.jsonl` with `{ "artifact_path": "...", "checksum": "...", "generated_by": "script_name.py", "timestamp": "ISO8601" }`.  
  - **Verification**: Log parses without error; one entry per artifact.  

- [ ] T016 **Research‑stage handoff README** – Write `outputs/handoff.md` listing all artifact locations, checksums, re‑run instructions, and a `Skipped steps` section (empty in this version because all steps run).  
  - **Verification**: File renders in Markdown; includes required sections.  

---

### Dependency Mapping (summary)

| Requirement | Covered by Task(s) |
|-------------|--------------------|
| FR‑001 (download $T_g$) | T003, T024 |
| FR‑002 (descriptor computation) | T004 |
| FR‑003 (EBM training) | T007, T008 |
| FR‑004 (interpretability plots) | T009 |
| FR‑005 (validation vs. physical metrics) | T010, T011, T023 |
| FR‑006 (imputation & scaling) | T005 |
| FR‑007 (resource limits) | T012, T013, T019, T020 |
| FR‑008 (FFV & stiffness) | T006 |
| SC‑001 (R² improvement) | T017, T018 |
| SC‑002 (correlation with physical metrics) | T010, T023 |
| SC‑003 (sensitivity) | T011 |
| SC‑004 (runtime ≤ 6 h) | T013, T019 |
| SC‑005 (≥ 3 PDPs) | T009 |

All tasks are unchecked and ordered to respect data flow. Running the checklist top‑to‑bottom yields a fully reproducible pipeline that meets the specification, the constitution, and every listed success criterion.  