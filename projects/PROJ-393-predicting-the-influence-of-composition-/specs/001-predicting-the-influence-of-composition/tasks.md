# Tasks: Predicting the Influence of Composition on the Magnetic Hysteresis of Heusler Alloys

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, and the canonical schemas in `contracts/`.

This research implements a reproducible CPU‑only pipeline that (1) aggregates experimental Heusler‑alloy hysteresis data from three distinct sources, (2) standardizes composition and hysteresis units, (3) computes composition‑based descriptors, (4) trains linear‑regression and random‑forest models with rigorous statistical validation, and (5) assembles the mandatory reporting artifacts. The study is framed as exploratory because the dataset may contain fewer than 50 entries.

---

## Phase 1 – Setup and first end‑to‑end analysis  

**Goal**: Verify the technical stack on a tiny real dataset before scaling to the full aggregation.

- [ ] T001 [P1] Establish the project layout, pin dependencies, and document the runnable command.  
  *Create `code/requirements.txt` with exact versions, add `quickstart.md` that shows `python -m src.main`, and create the folder hierarchy `code/src/`, `data/raw/`, `data/processed/`, `docs/reports/`.*  
  **Verification**: `quickstart.md` contains a reproducible command; running it on a fresh checkout prints “Setup OK”.

- [ ] T002 [P1] Provide a verified elemental‑property reference file.  
  *Place `data/raw/elemental_properties_v1.csv` (sourced from the NIST Chemistry WebBook) containing electronegativity, atomic radii, valence‑electron count, d‑electron count, atomic mass, electron affinity, and Pettifor scale for all elements appearing in Heusler alloys (Co, Mn, Fe, Ga, Al, etc.).*  
  **Verification**: The CSV header matches the schema used by the descriptor code; a checksum entry is added to `data/checksums.txt`.

- [ ] T003 [P1] Implement a minimal ingestion‑preprocess‑model sanity‑check pipeline on a tiny manual file.  
  *Create `code/src/ingestion/manual_curator.py` that reads `data/raw/manual_curated.csv` (provided by the spec), and `code/src/preprocessing/preprocess_pipeline.py` that normalizes units (Oe, emu/g) and drops any DFT rows. Add `code/src/models/linear_regressor.py` that fits a scikit‑learn `LinearRegression` on the processed data.*  
  **Verification**: Executing `python -m src.main --demo` produces `data/results/demo_metrics.json` containing numeric `r2` and `mae` fields.

- [ ] T004 [P1] Wire the demo components together in `code/src/main.py`.  
  *The entry point loads the manual file, runs the preprocessing, computes a single descriptor (average electronegativity), fits the linear model, and writes the metrics file.*  
  **Verification**: The command from `quickstart.md` runs without error and the output file exists with non‑null values.

---

## Phase 2 – Complete the study and validate its evidence  

**Goal**: Build the full end‑to‑end pipeline on the aggregated experimental dataset and perform all required statistical checks.

- [ ] T005 [P2] Aggregate experimental data from three distinct sources.  
  *Subtasks:*  
  - **T005.A** Create `data/raw/sources_manifest.txt` listing (1) NIST Materials Data Repository URL, (2) DOI and URL of a journal supplement containing Heusler hysteresis tables, (3) reference to a manually curated CSV derived from literature. Each line includes the expected file format.  
  - **T005.B** Implement `code/src/ingestion/nist_fetcher.py`, `code/src/ingestion/journal_supplement_parser.py`, and `code/src/ingestion/manual_curator.py` to download/parse the three sources, store raw files under `data/raw/` and record SHA‑256 hashes in `data/checksums.txt`.  
  - **T005.C** Merge the three raw tables into `data/raw/raw_merged.csv`, de‑duplicate on `alloy_id`, and write a verification JSON `data/processed/data_count_verification.json` containing `total_entries`, per‑source counts, and `target_count`. If `total_entries < 50`, the file must include a `"data_scarcity_warning": true` flag.  
  **Verification**: `raw_merged.csv` contains ≥ 3 source columns, the count JSON reports `target_count ≥ 50` or a warning flag, and the manifest file exists.

- [ ] T006 [P2] Preprocess the merged dataset.  
  *Run `code/src/preprocessing/preprocess_pipeline.py` to (1) convert all compositions to atomic fractions with ≥ 4 decimal precision (sum = 1.0 ± 0.0001), (2) normalize hysteresis units to Oe and emu/g, (3) drop any row where `is_dft == true` or `source_type == "DFT"`, (4) apply column‑wise mean imputation for non‑target fields when missing ≤ 15 % (otherwise perform listwise deletion for that column), and (5) log imputation rates in `data/processed/imputation_log.json`.  
  **Verification**: `data/processed/alloys_clean.csv` passes validation against `contracts/alloy_entry.schema.yaml`; `imputation_log.json` shows all rates < 0.15; a separate `data/processed/completeness_report.json` reports per‑source completeness.

- [ ] T007 [P2] Engineer composition‑based descriptors.  
  *Execute `code/src/features/feature_engineering_pipeline.py` which reads `alloys_clean.csv` and the elemental property table, computes the eight descriptors required by the plan (average electronegativity, VEC, atomic radii variance, average d‑electron count, size mismatch, average atomic mass, electron affinity, Pettifor scale) and one‑hot encodes `synthesis_method` and `crystal_structure`. Output `data/processed/alloys_features.csv`.*  
  **Verification**: The output CSV contains the original columns plus exactly eight numeric descriptor columns and two one‑hot encoding groups; no NaNs remain for descriptor columns.

- [ ] T008 [P2] Train regression models with cross‑validation and perform outlier sensitivity analysis.  
  *Run `code/src/models/training_pipeline.py` which (1) splits the feature matrix into a fixed 5‑fold CV (random_state = 42), (2) trains a baseline `LinearRegression` and a `RandomForestRegressor` (grid‑search over `n_estimators=[100,200]` and `max_depth=[5,10,None]`), (3) records mean CV R² and MAE for each model in `data/results/model_metrics.json`, (4) saves the fitted model objects under `code/models/`, and (5) conducts Isolation‑Forest outlier detection (contamination = 0.1), retrains both models without detected outliers, and writes `data/results/outlier_analysis.json` summarizing the impact.*  
  **Verification**: `model_metrics.json` contains entries for both “Linear” and “RandomForest” with `r2_cv` and `mae_cv`; `outlier_analysis.json` reports the number of outliers and the delta in metrics.

- [ ] T009 [P3] Perform statistical validation of the trained models.  
  *Subtasks:*  
  - **T009.A** `code/src/validation/null_model_comparison.py` computes an F‑test comparing the Linear model to a null model (mean prediction) on the CV folds, writing `data/results/f_test.json` with `f_statistic`, `p_value`, and `is_significant`.  
  - **T009.B** `code/src/validation/bootstrap_validation.py` resamples the full dataset 1000 times, refits the Linear model each time, and records the 95 % confidence interval for R² in `data/results/bootstrap_ci.json`.  
  - **T009.C** `code/src/validation/pdp_generator.py` generates Partial Dependence Plots for the top‑3 permutation‑importance features (as identified in T008) for both targets, saving PNGs `figures/pdp_coercivity.png` and `figures/pdp_saturation.png`.  
  - **T009.D** `code/src/validation/sc006_evaluation.py` evaluates the best‑performing model on the held‑out test set, checks the exploratory benchmark (R² ≥ 0.6 AND p‑value < 0.05), and writes `data/results/sc006_evaluation.json` with `r2_test`, `p_value_test`, and `threshold_met`.  
  **Verification**: All JSON files exist with the required fields; the two PNGs are non‑empty image files.

- [ ] T010 [P3] Conduct microstructure‑stratified analysis (optional if metadata sufficient).  
  *If `synthesis_method` is present for ≥ 20 % of rows, run `code/src/validation/stratified_analysis.py` which groups the data by synthesis method, trains separate Linear and Random‑Forest models within each stratum, and writes `data/results/stratified_metrics.json` containing per‑stratum R² and MAE. If metadata is insufficient, the script writes a short JSON note `"skipped": true` with a reason.*  
  **Verification**: The JSON file exists and either contains the stratified metrics or the skip note.

---

## Phase 3 – Reproducible results and paper handoff  

**Goal**: Assemble the mandatory reporting artifacts, verify full‑pipeline execution under resource limits, and record reproducible hashes for handoff.

- [ ] T011 [P3] Generate the mandatory reporting documents.  
  *Subtasks:*  
  - **T011.A** `docs/reports/data_scarcity_warning.md` – created if `data_count_verification.json` reports `total_entries < 50`; the file must state the exact N and warn of reduced statistical power.  
  - **T011.B** `docs/reports/statistical_limitations.md` – always generated; it must contain the required disclaimer that the F‑test validates fit, not physical mechanism, and notes microstructural confounders (text anchored to the actual p‑value from `f_test.json`).  
  - **T011.C** `docs/reports/microstructure_note.md` – always generated; it must list the unique synthesis methods extracted from `data/processed/synthesis_methods_list.txt` (or state “Not specified” if none) and reiterate FR‑010.  
  - **T011.D** `docs/reports/final_report.md` – consolidates all results: dataset size, completeness metrics, descriptor definitions, model CV scores, outlier analysis, stratified analysis (if present), SC‑006 evaluation, bootstrap CI, PDP figures, and embeds the three markdown notes above. The report follows the 11‑section structure defined in the plan.  
  **Verification**: Each markdown file exists, is non‑empty, and contains the required sections/text. The final report includes the embedded PNGs for PDPs and references the JSON metric files.

- [ ] T012 [P3] Execute the full pipeline from a clean environment and verify resource consumption.  
  *Run `python -m src.main --full` which sequentially calls T005–T010, then T011. While running, capture peak memory and total runtime, writing `data/results/resource_consumption.json` with fields `peak_memory_gb`, `total_runtime_seconds`, and `within_limits` (true if memory < 7 GB and runtime < 6 h).*  
  **Verification**: The JSON file reports `within_limits: true`; all expected output files from Phases 1‑3 are present and non‑empty.

- [ ] T013 [P3] Record artifact hashes and update project state for handoff.  
  *Compute SHA‑256 hashes for every file under `data/processed/`, `data/results/`, `docs/reports/`, and the model pickles under `code/models/`. Write a consolidated `state/artifact_hashes.yaml` (managed by the platform) and ensure the latest commit includes this file. No manual edits to platform state files are performed; the script only writes to the project‑owned `state/` directory.*  
  **Verification**: The hash file exists, contains an entry for each artifact, and a CI check confirms the hashes match the on‑disk files.

---

### Dependency & Requirement Coverage Summary

| Spec Requirement | Implementing Task(s) | Evidence Artifact |
|------------------|----------------------|-------------------|
| FR‑001 (3 sources) | T005.A‑C | `sources_manifest.txt`, `raw_merged.csv` |
| FR‑002 (unit/comp normalisation, imputation < 15 %) | T006 | `alloys_clean.csv`, `imputation_log.json` |
| FR‑003 (≥ 5 descriptors) | T007 | `alloys_features.csv` (8 descriptors) |
| FR‑004 (LR + RF, 5‑fold CV) | T008 | `model_metrics.json`, model pickles |
| FR‑005 (F‑test, bootstrap CI, PDP) | T009 | `f_test.json`, `bootstrap_ci.json`, `figures/pdp_*.png` |
| FR‑008 (exclude DFT, data‑scarcity warning) | T006, T011.A | `alloys_clean.csv` (no DFT), `data_scarcity_warning.md` |
| FR‑009 (fit vs mechanism disclaimer) | T011.B | `statistical_limitations.md` |
| FR‑010 (microstructure note) | T011.C | `microstructure_note.md` |
| SC‑001 (F‑test) | T009.A | `f_test.json` |
| SC‑002 (Bootstrap CI) | T009.B | `bootstrap_ci.json` |
| SC‑003 (PDPs) | T009.C | `figures/pdp_*.png` |
| SC‑004 (completeness) | T005.C, T006 | `data_count_verification.json`, `completeness_report.json` |
| SC‑005 (CPU‑only limits) | T012 | `resource_consumption.json` |
| SC‑006 (exploratory benchmark) | T009.D | `sc006_evaluation.json` (referenced in final report) |
| Constitution VI (descriptor consistency) | T002, T007 | `elemental_properties_v1.csv` |

All tasks are ordered to respect data flow: ingestion → preprocessing → feature engineering → modeling → validation → reporting → final reproducibility checks.
