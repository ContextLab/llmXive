# Tasks: Predicting the Influence of Composition on the Magnetic Hysteresis of Heusler Alloys

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, and the canonical schemas in `contracts/`.

This research implements a reproducible CPU‑only pipeline that (1) aggregates experimental Heusler‑alloy hysteresis data from three distinct sources, (2) standardizes composition and hysteresis units, (3) computes composition‑based descriptors, (4) trains linear‑regression and random‑forest models with rigorous statistical validation, and (5) assembles the mandatory reporting artifacts. The study is framed as exploratory because the dataset may contain fewer than 50 entries.

---

## Phase 1 – Setup and first end‑to‑end analysis  

**Goal**: Verify the technical stack on a tiny real dataset before scaling to the full aggregation.

- [ ] T001 [P1] Establish the project layout, pin dependencies, and document a runnable command.   <!-- FAILED-IN-EXECUTION: code/main.py exit=1 -->
  *Create `code/requirements.txt` with exact package versions, add `quickstart.md` that shows `python -m src.main`, and create the folder hierarchy `code/src/`, `data/raw/`, `data/processed/`, `docs/reports/`.*  
  **Verification**: `quickstart.md` contains a reproducible command; a fresh checkout of the repo followed by `pip install -r code/requirements.txt && python -m src.main --help` prints a help message containing “Setup OK”.

- [ ] T002 [P1] Provide a verified elemental‑property reference file.  
  *Place `data/raw/elemental_properties_v1.csv` (sourced from the NIST Chemistry WebBook) containing electronegativity, atomic radii, valence‑electron count, d‑electron count, atomic mass, electron affinity, and Pettifor scale for all elements appearing in Heusler alloys (Co, Mn, Fe, Ga, Al, etc.).*  
  **Verification**: The CSV header matches the schema expected by `src/features/descriptors.py`; a SHA‑256 checksum entry is added to `data/checksums.txt` and the checksum file is validated by a test in `tests/unit/test_elemental_properties.py`.

- [ ] T003 [P1] Implement a minimal ingestion‑preprocess‑model sanity‑check pipeline on a tiny manual file.   <!-- FAILED-IN-EXECUTION: code/main.py exit=1 -->
  *Create `code/src/ingestion/manual_curator.py` that reads `data/raw/manual_curated.csv` (provided by the spec), and `code/src/preprocessing/preprocess_pipeline.py` that normalizes units (Oe, emu/g) and drops any DFT rows. Add `code/src/models/linear_regressor.py` that fits a scikit‑learn `LinearRegression` on the processed data.*  
  **Verification**: Executing `python -m src.main --demo` produces `data/results/demo_metrics.json` containing numeric `r2` and `mae` fields; the JSON schema is validated by `tests/integration/test_demo_pipeline.py`.

- [ ] T004 [P1] Wire the demo components together in `code/src/main.py`.  
  *The entry point loads the manual file, runs the preprocessing, computes a single descriptor (average electronegativity), fits the linear model, and writes the metrics file.*  
  **Verification**: The command from `quickstart.md` runs without error, creates `data/results/demo_metrics.json`, and the file contains non‑null `r2` and `mae` values that pass the unit test in `tests/unit/test_demo_output.py`.

---

## Phase 2 – Complete the study and validate its evidence  

**Goal**: Build the full end‑to‑end pipeline on the aggregated experimental dataset and perform all required statistical checks.

- [ ] T005 [P2] Aggregate experimental data from three distinct sources.  
  *Sub‑tasks (implemented within the same script `code/src/ingestion/aggregate.py`):*  
  - **T005.A** Create `data/raw/sources_manifest.txt` listing (1) NIST Materials Data Repository URL, (2) DOI and URL of a journal supplement containing Heusler hysteresis tables, (3) reference to a manually curated CSV derived from literature. Each line includes the expected file format.  
  - **T005.B** Implement `code/src/ingestion/nist_fetcher.py`, `code/src/ingestion/journal_supplement_parser.py`, and `code/src/ingestion/manual_curator.py` to download/parse the three sources, store raw files under `data/raw/` and record SHA‑256 hashes in `data/checksums.txt`.  
  - **T005.C** Merge the three raw tables into `data/raw/raw_merged.csv`, de‑duplicate on `alloy_id`, and write a verification JSON `data/processed/data_count_verification.json` containing `total_entries`, per‑source counts, and `target_count`. If `total_entries < 50`, the file must include a `"data_scarcity_warning": true` flag.  
  **Verification**: `raw_merged.csv` exists, contains ≥ 3 source columns, `data_count_verification.json` reports `target_count ≥ 50` or a warning flag, and `sources_manifest.txt` is non‑empty and matches the URLs used by the fetchers.

- [ ] T006 [P2] Preprocess the merged dataset.  
  *Run `code/src/preprocessing/preprocess_pipeline.py` to:*  
  1. Convert all compositions to atomic fractions with ≥ 4 decimal places (sum = 1.0 ± 0.0001).  
  2. Normalize hysteresis units to Oe and emu/g.  
  3. Drop any row where `is_dft == true`.  
  4. Apply column‑wise **mean imputation** for non‑target fields when missing ≤ 15 %; for columns with >15 % missing, **drop rows** that contain missing values in those columns (preserving all descriptor columns).  
  5. Log imputation rates in `data/processed/imputation_log.json`.  
  **Verification**: `data/processed/alloys_clean.csv` validates against `contracts/alloy_entry.schema.yaml`; `imputation_log.json` shows all rates < 0.15; `data/processed/completeness_report.json` reports per‑source completeness and matches the counts in `data_count_verification.json`.

- [ ] T006a [P2] Generate reproducible train‑test splits from the cleaned data.  
  *Create `code/src/preprocessing/split_generator.py` that reads `data/processed/alloys_clean.csv`, performs a stratified random split (80 % train, 20 % test) using a fixed `random_state=42`, and writes `data/processed/train_split.csv` and `data/processed/test_split.csv`. Record the split ratios and random seed in `data/processed/split_metadata.json`.*  
  **Verification**: Both split files exist, contain non‑overlapping `alloy_id`s, preserve the overall class distribution of the target variable, and `split_metadata.json` matches the intended parameters.

- [ ] T015 [P2] Edge‑case handling in preprocessing.  
  *Extend `preprocess_pipeline.py` to:*  
  - Flag any element symbols not present in `data/raw/elemental_properties_v1.csv` and exclude those rows, logging the missing symbols.  
  - Treat values equal to the strings “not measurable” or “N/A” as missing (subject to the imputation policy).  
  - Preserve numeric zeroes as valid entries.  
  - Write a summary `data/processed/edge_case_log.json` listing excluded rows and reasons.  
  **Verification**: The log file exists, contains entries for unknown elements and “not measurable” cases, and `alloys_clean.csv` contains no such values.

- [ ] T007 [P2] Engineer composition‑based descriptors.  
  *Execute `code/src/features/feature_engineering_pipeline.py` which reads `alloys_clean.csv` and the elemental property table, computes the eight descriptors required by the plan (average electronegativity, VEC, atomic radii variance, average d‑electron count, size mismatch, average atomic mass, electron affinity, Pettifor scale) and one‑hot encodes `synthesis_method` and `crystal_structure`. Output `data/processed/alloys_features.csv`.*  
  **Verification**: The output CSV contains the original columns plus exactly eight numeric descriptor columns and two one‑hot encoding groups; no NaNs remain in descriptor columns; the file validates against `contracts/composition_descriptor.schema.yaml`.

- [ ] T008 [P2] Train regression models with cross‑validation on the **fixed training split**.  
  *Run `code/src/models/training_pipeline.py` which:*  
  1. Reads the fixed training split `data/processed/train_split.csv` (generated by T006a) and the corresponding test split `data/processed/test_split.csv`.  
  2. Performs **5‑fold cross‑validation** **only on the training split** (`random_state=42`).  
  3. Trains a baseline `LinearRegression` and a `RandomForestRegressor` (grid‑search over `n_estimators=[100,200]` and `max_depth=[5,10,None]`).  
  4. Records mean CV R² and MAE for each model in `data/results/model_metrics.json`.  
  5. Saves the fitted model objects under `code/models/`.  
  6. Conducts Isolation‑Forest outlier detection (`contamination=0.1`) on the training split, retrains both models without detected outliers, and writes `data/results/outlier_analysis.json` summarizing the impact.  
  7. After final training, evaluates both models on the **held‑out test split**, appending test‑set R², MAE, and RMSE to `data/results/model_metrics.json` under a `test_set` key.  
  **Verification**: `model_metrics.json` contains entries for both “Linear” and “RandomForest” with `r2_cv`, `mae_cv`, and a nested `test_set` section; `outlier_analysis.json` reports the number of outliers removed and the delta in metrics; model pickle files exist and can be loaded without error (checked by `tests/integration/test_model_loading.py`).

- [ ] T009 [P3] Perform statistical validation of the trained models.  
  *Sub‑tasks (all executed by `code/src/validation/validate_all.py`):*  
  - **T009.A** `null_model_comparison.py` computes an F‑test comparing the Linear model to a null model (mean prediction) on the CV folds, writing `data/results/f_test.json` with `f_statistic`, `p_value`, and `is_significant`.  
  - **T009.B** `bootstrap_validation.py` resamples the full dataset 1000 times, refits the Linear model each time, and records the 95 % confidence interval for R² in `data/results/bootstrap_ci.json`.  
  - **T009.C** `pdp_generator.py` generates Partial Dependence Plots for the top‑3 permutation‑importance features (identified in T008) for both targets, saving PNGs `figures/pdp_coercivity.png` and `figures/pdp_saturation.png`.  
  - **T009.D** `sc006_evaluation.py` evaluates the best‑performing model on the held‑out test set, **asserts** that `r2_test >= 0.6` **and** `p_value_test < 0.05`; if either condition fails the task aborts with an error. It also writes `data/results/sc006_evaluation.json` with `r2_test`, `p_value_test`, and `threshold_met` (true only when both numeric criteria are satisfied).  
  **Verification**: All JSON files exist with the required fields; the two PNGs are non‑empty image files; a unit test suite (`tests/unit/test_validation_outputs.py`) confirms schema compliance for each JSON artifact and that T009.D fails when thresholds are not met.

- [ ] T010 [P3] Conduct microstructure‑stratified analysis (optional if metadata sufficient).  
  *If `synthesis_method` is present for ≥ 20 % of rows, run `code/src/validation/stratified_analysis.py` which groups the data by synthesis method, trains separate Linear and Random‑Forest models within each stratum, and writes `data/results/stratified_metrics.json` containing per‑stratum R² and MAE. If metadata is insufficient, the script writes a short JSON note `{ "skipped": true, "reason": "insufficient synthesis metadata" }`.*  
  **Verification**: The JSON file exists and either contains the stratified metrics or the skip note; a test (`tests/unit/test_stratified_analysis.py`) checks that the file matches the expected schema.

---

## Phase 3 – Reproducible results and paper handoff  

**Goal**: Assemble the mandatory reporting artifacts, verify full‑pipeline execution under resource limits, and record reproducible hashes for handoff.

- [ ] T011 [P3] Coordination task for report generation.  
  *Orchestrates execution of the four dedicated report tasks (T011a‑d) and verifies that each markdown file is non‑empty.*  
  **Verification**: After running the sub‑tasks, the coordination script checks file sizes > 0 and reports success.

- [ ] T011a [P3] Generate `data_scarcity_warning.md` if needed.  
  *If `data_count_verification.json` reports `total_entries < 50`, create `docs/reports/data_scarcity_warning.md` stating the exact N, citing the scarcity flag, and discussing reduced statistical power.*  
  **Verification**: File exists, contains the required narrative, and a unit test (`tests/unit/test_data_scarcity.md`) validates its content.

- [ ] T011b [P3] Generate `statistical_limitations.md`.  
  *Create a markdown document that includes the mandatory disclaimer that the F‑test validates statistical fit, not physical mechanism, and embed the actual p‑value from `data/results/f_test.json`.*  
  **Verification**: File exists, contains the disclaimer and the numeric p‑value; passes `tests/unit/test_statistical_limitations.md`.

- [ ] T011c [P3] Generate `microstructure_note.md`.  
  *List the unique synthesis methods extracted from `data/processed/synthesis_methods_list.txt` (or state “Not specified” if none) and repeat FR‑010 verbatim.*  
  **Verification**: File exists, includes the list or the fallback text; passes `tests/unit/test_microstructure_note.md`.

- [ ] T011d [P3] Generate `final_report.md`.  
  *Consolidate dataset size, completeness metrics, descriptor definitions, model CV scores, outlier analysis, stratified analysis (if present), SC‑006 evaluation, bootstrap CI, PDP figures (embedded as markdown image links), and references to the three auxiliary markdown notes. Include a “Reproducibility” section that records the git commit hash and the SHA‑256 checksums of all key artifacts.*  
  **Verification**: File exists, follows the 11‑section structure defined in the plan, includes markdown image links to `figures/pdp_coercivity.png` and `figures/pdp_saturation.png`, and passes `tests/unit/test_final_report_structure.py`.

- [ ] T012 [P3] Execute the full pipeline from a clean environment and verify resource consumption.  
  *Run `python -m src.main --full` which sequentially calls T005–T010, then T011a‑d, then T011. While running, capture peak memory and total runtime, writing `data/results/resource_consumption.json` with fields `peak_memory_gb`, `total_runtime_seconds`, and `within_limits` (true if memory < 7 GB and runtime < 6 h).*  
  **Verification**: The JSON file reports `within_limits: true`; all expected output files from Phases 1‑3 are present and non‑empty; a CI step (`scripts/check_resource_limits.sh`) parses the JSON and fails if limits are exceeded.

- [ ] T013 [P3] Record artifact hashes and update project state for handoff.  
  *Compute SHA‑256 hashes for every file under `data/processed/`, `data/results/`, `docs/reports/`, and the model pickles under `code/models/`. Write a consolidated `state/artifact_hashes.yaml` (managed by the platform) and ensure the latest commit includes this file. No manual edits to platform‑owned state files are performed; the script only writes to the project‑owned `state/` directory.*  
  **Verification**: The hash file exists, contains an entry for each artifact, and a CI check (`scripts/verify_hashes.sh`) confirms that each recorded hash matches the on‑disk file. The repository’s CI reports “Artifact hash verification passed”.

- [ ] T014 [P3] Validate model output artifacts against schemas.  
  *After model training, run `code/src/validation/validate_model_output.py` which loads `data/results/model_metrics.json` (or the combined `model_results.json` if produced) and validates it against `contracts/model_output.schema.yaml` and `contracts/model_result.schema.yaml`. The task fails if any schema violation is detected.*  
  **Verification**: The validation script exits with status 0; a unit test (`tests/unit/test_model_output_schema.py`) confirms successful validation.
