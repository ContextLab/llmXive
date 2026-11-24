# Tasks: Predicting Molecular Properties from Topological Data Analysis

**Inputs**: `spec.md`, `plan.md`, original research idea, existing artifacts, and reviewer feedback.

The goal is to deliver a fully reproducible, CPU‑only study that satisfies every functional requirement (FR‑001 … FR‑009) and success criterion (SC‑001 … SC‑005) while respecting platform constraints (real data only, no synthetic fall‑backs, no GPU).  
Tasks are ordered to respect data flow; later tasks depend on the outputs of earlier ones.

---

## Phase 1 – Setup and first end‑to‑end analysis  

| Goal | Run a minimal pipeline on real inputs and obtain the first set of validated artifacts. |
|------|----------------------------------------------------------------------------------------|

- [X] **T001** [US1] Create the **dataset schema** file.  
  - Write `specs/001-predicting-molecular-properties-from-top/contracts/dataset.schema.yaml` containing the required properties `molecule_id` (string), `smiles` (string), and `logP` (number).  
  - **Verification**: `python -c "import jsonschema, yaml, pathlib; schema=yaml.safe_load(pathlib.Path('specs/001-predicting-molecular-properties-from-top/contracts/dataset.schema.yaml').read_text()); jsonschema.Draft7Validator.check_schema(schema)"` exits 0.

- [ ] **T001a** [US1] Download the **MoleculeNet Lipophilicity** dataset (the canonical dataset required by FR‑001). <!-- FAILED-IN-EXECUTION: code/01_download_lipophilicity.py exit=1 -->
  - Use `deepchem.molnet.load_molnet_dataset('Lipophilicity')` or fetch from the official URL `https://deepchemdata.s3-us-west-1.amazonaws.com/datasets/lipophilicity.csv`.  
  - Save the CSV as `data/raw/lipophilicity.csv`.  
  - Compute its SHA‑256 checksum and append a line `lipophilicity.csv <checksum>` to `data/checksums.txt`.  
  - **Verification**: `sha256sum data/raw/lipophilicity.csv` matches the hash recorded in `data/checksums.txt`.

- [ ] **T001b** [US1] Run **checksum verification**.   <!-- FAILED-IN-EXECUTION: code/00_checksum_verify.py exit=1 -->
  - Execute `python code/00_checksum_verify.py`. It reads `data/checksums.txt`, recomputes hashes, and exits 0 only if all match.  
  - **Verification**: Script prints “All checksums verified” and returns status 0.

- [ ] **T001c** [US1] **Ingest and filter** the raw Lipophilicity CSV.  
  - Run `python code/01_data_ingestion.py` which validates the CSV against the dataset schema, canonicalizes SMILES with RDKit, logs and skips invalid entries, and writes `data/processed/filtered_lipophilicity.csv`.  
  - **Verification**: The output file exists, row count equals the number of valid SMILES, and `pytest code/tests/test_ingestion_schema.py` passes.

- [ ] **T001d** [US1] Generate **scaffold‑based splits** and perform a power analysis.  
  - After ingestion, compute Bemis‑Murcko scaffolds, ensure ≥ 100 distinct scaffolds, and write a 5‑fold scaffold split (seed 42) to `data/processed/splits.json`.  
  - Perform an a‑priori power analysis (paired t‑test, α = 0.05, power = 0.8, effect size = 0.5) and write `data/processed/power_analysis_report.json` with fields `min_n`, `actual_n`, `passes`.  
  - **Verification**: `jq .passes data/processed/power_analysis_report.json` returns `true`; `jq '.[] | length' data/processed/splits.json` yields five non‑overlapping groups.

- [ ] **T002** [US1] Create the **feature‑matrix schema** file.  
  - Write `specs/001-predicting-molecular-properties-from-top/contracts/feature_matrix.schema.yaml` exactly as defined in the spec (requires `molecule_id`, `target_property`, `target_value`, and `pixel_*` fields).  
  - **Verification**: Loading the file with `jsonschema` succeeds.

- [ ] **T003** [US1] Compute **baseline TDA features (10 × 10 persistence images)**.  
  - Read `data/processed/filtered_lipophilicity.csv`. For each SMILES, build a molecular graph with RDKit, apply the shortest‑path distance filtration (FR‑001) via GUDHI, and vectorize to a 10 × 10 persistence image (kernel = 1.0).  
  - Include `target_property = "logP"` and `target_value` (experimental logP) in every row.  
  - Write `data/processed/topological_features_10x10.csv` (columns: `molecule_id` + 100 `pixel_n` values).  
  - Log invalid SMILES to `data/logs/invalid_smiles.log`; handle disconnected graphs and empty diagrams by writing a zero‑vector.  
  - **Verification**: No `NaN` values; row count equals that of `filtered_lipophilicity.csv`; `pytest code/tests/test_feature_matrix.py` passes.

- [ ] **T004** [US1] Compute **traditional descriptors** and build the **combined feature matrix**.  
  - `code/03_feature_engineering.py` reads `data/processed/filtered_lipophilicity.csv` and `data/processed/topological_features_10x10.csv`.  
  - Compute RDKit descriptors: molecular weight, atom counts, and 1024‑bit Morgan fingerprint (radius 2). Write `data/processed/traditional_features.csv`.  
  - Merge traditional and topological descriptors on `molecule_id` (cast to string) → `data/processed/combined_features.csv`. **Drop the `target` column before merging** to avoid circular prediction.  
  - **Verification**: All three CSVs have identical row counts; `pandas.isnull().sum().sum()` returns `0`.

- [ ] **T005** [US1] Create the **model‑metrics schema** file.  
  - Write `specs/001-predicting-molecular-properties-from-top/contracts/model_metrics.schema.yaml` exactly as in the spec (requires `traditional`, `topological`, `combined`, `feature_importance`, `metadata`).  
  - **Verification**: Loading with `jsonschema` succeeds.

---

## Phase 2 – Complete the study and validate its evidence  

| Goal | Run the full analysis, perform statistical checks, and record diagnostics. |
|------|-----------------------------------------------------------------------------|

- [ ] **T006** [US2] **Train regression models** on the three feature sets with CPU‑only enforcement.  
  - Load `data/processed/splits.json`.  
  - Train Ridge Regression (`alpha=1.0`) and Random Forest (`n_estimators=100`, `max_depth=10`, `random_state=42`) for each feature set (traditional, topological, combined) using 5‑fold scaffold CV (FR‑003, FR‑004).  
  - **CPU‑only guard**: script aborts with an error if `torch.cuda.is_available()` or any `/dev/nvidia*` device is present (FR‑008).  
  - Write `reports/metrics/model_metrics.json` conforming to `model_metrics.schema.yaml`; include per‑fold R², RMSE, means, and feature‑importance arrays.  
  - Log the run (seed, split details) to `data/logs/training.log`.  
  - **Verification**: `pytest code/tests/validate_model_performance.py` exits 0 and the JSON validates; additionally, a test checks that the script exits with non‑zero status when a GPU is artificially detected.

- [ ] **T007** [US2] **Validate the model‑metrics contract** and presence of sensitivity output.  
  - Run `pytest code/tests/test_metrics_schema.py` which validates `reports/metrics/model_metrics.json` against the schema and also asserts that `reports/metrics/sensitivity_report.json` exists.  
  - **Verification**: Test exits 0.

- [ ] **T008** [US3] **Sensitivity sweep of vectorization resolution**.  
  - Extend `code/02_tda_computation.py` with a `--grid` argument. Generate topological feature CSVs for grid sizes 20 × 20 and 30 × 30 (`topological_features_20x20.csv`, `topological_features_30x30.csv`).  
  - Run `code/05_sensitivity_analysis.py` which, for each grid size (10, 20, 30), re‑trains the models (same hyper‑parameters, same splits) and records mean R² and its standard deviation.  
  - Write `reports/metrics/sensitivity_report.json` containing a list of objects `{ "grid_size": <int>, "r2_mean": <float>, "r2_std": <float> }`.  
  - **Verification**: JSON has three entries; `jq length reports/metrics/sensitivity_report.json` returns `3`.

- [ ] **T009** [US3] **Statistical comparison & Bonferroni correction**.  
  - Using per‑fold R² from `model_metrics.json`, perform paired t‑tests (or Wilcoxon if non‑normal) comparing **combined** vs **traditional** models.  
  - Apply the plain Bonferroni correction (FR‑005) and write `reports/metrics/bonferroni_diagnostics.json` containing `raw_p_value`, `adjusted_p_value`, and `significant`.  
  - Also write `reports/metrics/fwer_report.json` with `alpha`, `num_tests`, `rejections`, and `fwer_bound`.  
  - **Verification**: Helper script checks that `adjusted_p_value = min(raw_p_value * num_tests, 1.0)`.

- [ ] **T010** [US3] **Collinearity (VIF) and redundancy (mutual information) diagnostics**.  
  - Compute Variance Inflation Factor for every predictor **in the Linear Regression model only** (FR‑007). Write `reports/diagnostics/vif_report.json` with `{ "predictor": <str>, "vif": <float> }` and a `flagged` array for VIF > 5. Include a top‑level field `"model_type": "linear_l2"` to certify the source.  
  - Compute average mutual information between the traditional descriptor matrix and the topological descriptor matrix (FR‑009) using `mutual_info_regression`. Write `reports/diagnostics/mi_report.json` with field `average_mi`.  
  - **Verification**: Tests confirm the presence of `"model_type": "linear_l2"` and that no VIF entries exist for Random Forest; `mi_report.json` contains a numeric `average_mi`.

- [ ] **T011** [US3] **Redundancy significance warning**.  
  - Parse `reports/diagnostics/mi_report.json`; if `average_mi < 0.1` emit a warning to `data/logs/mi_warning.log` (do not abort).  
  - **Verification**: Running the script creates the warning log when appropriate; `code/tests/test_mi_reporting.py` passes.

- [ ] **T012** [US3] **Resource‑monitor wrapper for the full pipeline**.  
  - Execute the entire sequence (T001 → T010) under `code/07_resource_monitor.py`. The wrapper records peak RAM (GB) and total CPU time (hours) to `reports/metrics/resource_usage.json`.  
  - Enforce SC‑004 limits: `peak_ram_gb < 6.3` and `cpu_hours < 5.4`. If limits are exceeded, the wrapper exits with a non‑zero status.  
  - **Verification**: After a successful run, `jq .peak_ram_gb reports/metrics/resource_usage.json` returns a value < 6.3 and `jq .cpu_hours …` < 5.4.

- [ ] **T013** [US3] **Generate figures, tables, and summary artifacts**.  
  - Create figures in `reports/figures/`:  
    1. Example Betti curves and persistence images for a representative molecule.  
    2. Box‑plots of per‑fold R²/RMSE for each model‑feature set.  
    3. Sensitivity‑sweep performance curve (grid size vs. R²).  
  - Produce `reports/metrics/summary_table.csv` joining model performance, Bonferroni‑adjusted p‑values, VIF flags, and average MI.  
  - **Verification**: All PNG/SVG files open without error; the CSV loads in pandas with expected columns (`model`, `feature_set`, `r2_mean`, `rmse_mean`, `adjusted_p`, `vif_flags`, `average_mi`).

---

## Phase 3 – Reproducible results and paper hand‑off  

| Goal | Provide clear documentation and hand‑off artifacts for downstream writing. |
|------|-----------------------------------------------------------------------------|

- [ ] **T014** [US3] **Quickstart documentation & paper‑stage handoff**.  
  - Update `specs/001-predicting-molecular-properties-from-top/quickstart.md` with the exact command sequence (including the resource‑monitor wrapper) that reproduces the pipeline from raw data to final artifacts.  
  - Add a “Paper‑stage handoff” section listing all artifacts the paper pipeline must consume (`model_metrics.json`, `bonferroni_diagnostics.json`, `fwer_report.json`, `summary_table.csv`, all figures, diagnostics JSONs) and a brief note on any negative findings or limitations (e.g., low mutual information, VIF flags).  
  - **Verification**: Rendering the markdown shows no broken links; a dry‑run of the documented commands reproduces all final files with exit code 0.

---  

### Dependencies & requirement coverage

| Requirement | Task(s) |
|-------------|---------|
| FR‑001 (shortest‑path filtration) | T003 |
| FR‑002 (10 × 10 baseline + target fields) | T003 |
| FR‑003 (models & feature sets) | T006 |
| FR‑004 (scaffold CV, seed 42) | T001d |
| FR‑005 (Bonferroni) | T009 |
| FR‑006 (resolution sweep) | T008 |
| FR‑007 (VIF) | T010 |
| FR‑008 (CPU‑only guard) | T006 |
| FR‑009 (mutual information) | T010 |
| SC‑001 (combined vs. traditional R²) | T006 → T009 |
| SC‑002 (stability across resolutions) | T008 |
| SC‑003 (FWER ≤ 0.05) | T009 |
| SC‑004 (resource limits) | T012 |
| SC‑005 (VIF > 5 flag) | T010 |

**Execution order** (respecting data flow):  
T001 → T001a → T001b → T001c → T001d → T002 → T003 → T004 → T005 → T006 → T007 → T008 → T009 → T010 → T011 → T012 → T013 → T014.  

All tasks together constitute a complete, reproducible CPU‑only study that fulfills the specification, data model, and constitutional constraints.  

---  

# End of tasks.md