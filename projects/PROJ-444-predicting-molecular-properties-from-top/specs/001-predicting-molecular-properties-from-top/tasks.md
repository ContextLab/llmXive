# Tasks: Predicting Molecular Properties from Topological Data Analysis  

**Inputs**: Active `spec.md`, `plan.md`, original research idea, existing artifacts, and any reviewer feedback.  

The goal is to deliver a complete, reproducible study that satisfies every functional requirement (FR‑001…FR‑009) and success‑criterion (SC‑001…SC‑005) from the specification while respecting the platform’s constraints (CPU‑only, real data, no synthetic fall‑backs). Tasks are ordered to respect data flow; later tasks depend on the outputs of earlier ones.

---

- [ ] **T001** **[ ]** *Data ingestion, provenance, and split creation*
  - Download the ESOL dataset (default URL `https://deepchemdata.s3-us-west-1.amazonaws.com/datasets/dataset_esol.csv`) in `code/01_data_ingestion.py` with a `--url` argument.  
  - Verify that the CSV contains **exactly** the columns `smiles` and `logP` (conforms to `specs/001-predicting-molecular-properties-from-top/contracts/dataset.schema.yaml`).  
  - Compute and append the SHA‑256 checksum of `data/raw/esol.csv` to `data/checksums.txt`.  
  - Perform a priori power analysis (paired‑t, α = 0.05, power = 0.8, effect size d = 0.5) and write `data/processed/power_analysis_report.json` with keys `min_n`, `actual_n`, `passes`.  
  - **Exclude** molecules with molecular weight > 1000 Da, log each excluded SMILES to `data/logs/large_molecule_exclusions.log`, and process the remaining records using a chunked sparse‑matrix fallback (no exclusion of remaining data).  
  - Count unique Bemis‑Murcko scaffolds; abort with `SystemExit(1)` if < 100, otherwise write `data/processed/scaffold_counts.json`.  
  - Generate a scaffold‑based 5‑fold split (seed 42) and store indices in `data/processed/splits.json`.  
  - Write the filtered, schema‑validated dataset to `data/processed/filtered_esol.csv`.  
  - **Verification**:  
    1. `cat data/checksums.txt` contains a line matching the file’s hash.  
    2. `jq . passes data/processed/power_analysis_report.json` returns `true`.  
    3. `python -c "import pandas as pd; df=pd.read_csv('data/processed/filtered_esol.csv'); assert df.shape[0] >= 128"` succeeds.  
    4. A quick script confirms scaffold exclusivity across the five folds.  
    5. `grep -v '' data/logs/large_molecule_exclusions.log` is non‑empty only if exclusions occurred.

- [X] **T014** **[ ]** *Dataset schema contract test*  
  - Add `code/tests/test_dataset_schema.py` that loads `data/raw/esol.csv` and validates it against `specs/001-predicting-molecular-properties-from-top/contracts/dataset.schema.yaml`.  
  - **Verification**: `pytest code/tests/test_dataset_schema.py` passes.

- [ ] **T002** **[US1]** *Baseline TDA feature computation (10 × 10 persistence images)*   <!-- FAILED-IN-EXECUTION: code/02_tda_computation.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/02_tda_computation.py exit=1 -->
  - Read `data/processed/filtered_esol.csv`.  
  - For each SMILES, build a molecular graph with RDKit, apply the **shortest‑path distance filtration** (FR‑001) via `code/utils/persistence_utils.py`.  
  - Vectorise each persistence diagram to a **10 × 10 persistence image** (σ = 0.1) – the baseline required by FR‑002.  
  - Write `data/processed/persistence_images_10x10.csv` (columns: `molecule_id` + 100 float features).  
  - Log any invalid SMILES to `data/logs/invalid_smiles.log`.  
  - Gracefully handle empty diagrams (write a zero‑vector).  
  - **Verification**:  
    1. The CSV contains no `NaN` values (`pandas.isnull().any().any()` is `False`).  
    2. The file has the same number of rows as `filtered_esol.csv`.  

- [ ] **T003** **[P]** *Feature‑matrix contract test*  
  - Add `code/tests/test_feature_matrix.py` that loads `persistence_images_10x10.csv` and validates it against `specs/001-predicting-molecular-properties-from-top/contracts/feature_matrix.schema.yaml`.  
  - **Verification**: `pytest code/tests/test_feature_matrix.py` passes.

- [ ] **T004** **[US1]** *Traditional descriptors & combined feature matrix*  
  - Compute RDKit‑based traditional descriptors (molecular weight, atom counts, 1024‑bit Morgan fingerprint) and write `data/processed/traditional_descriptors.csv`.  
  - Merge the traditional matrix with `persistence_images_10x10.csv` on `molecule_id` → `data/processed/combined_features.csv`.  
  - Ensure no missing values across the merged table.  
  - **Verification**: Row counts of all three CSVs match; `pandas.isnull().sum().sum()` is `0`.

- [ ] **T005** **[US2]** *Baseline model training and evaluation*  
  - Load `data/processed/splits.json`.  
  - Train **Ridge Regression (α = 1.0)** and **Random Forest (100 trees, max_depth = 10, seed = 42)** on three feature sets: `traditional`, `topological`, `combined`. Use 5‑fold **scaffold‑based CV** (FR‑004) and seed 42 (FR‑004).  
  - Enforce CPU‑only execution (detect CUDA; abort if present – FR‑008).  
  - Write results to `reports/metrics/model_performance.json` conforming to `model_metrics.schema.yaml` (includes per‑fold R², RMSE, mean values, and feature‑importance arrays).  
  - Log the training run (seed, split details) to `data/logs/training.log`.  
  - **Verification**: `pytest code/tests/test_metrics_schema.py` (see T006) passes; the JSON contains three top‑level keys (`traditional`, `topological`, `combined`) each with the required sub‑fields.

- [ ] **T006** **[P]** *Model‑metrics contract test*  
  - Add `code/tests/test_metrics_schema.py` that validates `reports/metrics/model_performance.json` against `specs/001-predicting-molecular-properties-from-top/contracts/model_metrics.schema.yaml`.  
  - **Verification**: `pytest code/tests/test_metrics_schema.py` passes.

- [ ] **T007** **[US3]** *Sensitivity‑sweep of vectorisation resolution*  
  - Extend `code/02_tda_computation.py` with a `--grid` CLI argument to also generate **20 × 20** and **30 × 30** persistence‑image CSVs (`persistence_images_20x20.csv`, `persistence_images_30x30.csv`).  
  - Retrain the same models (Ridge & RF, three feature sets) on each resolution using the same splits.  
  - Collate mean R² for each resolution into `reports/metrics/sensitivity_analysis.json` (fields: `grid_size`, `r2_mean`, `r2_std`).  
  - **Verification**: JSON contains three entries (10, 20, 30) and the values are numeric.

- [ ] **T013** **[P]** *Specification amendment – scope reduction to logP*  
  - Create `specs/001-predicting-molecular-properties-from-top/spec_amendment_scope_reduction.md` documenting the decision to limit the study to the single property **logP** from ESOL (resource and power‑analysis justification).  
  - Update the main `spec.md` to reflect the logP‑only scope and modify FR‑005/SC‑003 references to indicate **N = 1** hypothesis test.  
  - **Verification**:  
    1. The amendment file exists.  
    2. A script (`code/tests/test_spec_update.py`) asserts that `spec.md` contains the phrase “logP only” and that FR‑005/SC‑003 mention “N = 1”.  
    3. The script exits with status 0.

- [ ] **T008** **[US3]** *Statistical comparison & Bonferroni correction*  
  - Using per‑fold R² from `model_performance.json`, perform paired **t‑tests** (or Wilcoxon if non‑normal) comparing **combined** vs **traditional** models.  
  - Apply **Bonferroni** correction (recorded in `reports/metrics/diagnostics_bonferroni.json`) to the p‑values as mandated by FR‑005.  
  - Compute the empirical **family‑wise error rate** (FWER) from the corrected p‑values and write `reports/metrics/fwer_report.json` (`alpha`, `rejections`, `fwer_bound`).  
  - Insert the Bonferroni‑adjusted p‑value field `bonferroni_adjusted_p` into `model_performance.json`.  
  - **Verification**: Both diagnostics JSON files exist; a unit test (`code/tests/test_correction.py`) confirms the Bonferroni logic; `model_performance.json` now contains the new field.

- [ ] **T009** **[US3]** *Collinearity and redundancy diagnostics*  
  - Compute **Variance Inflation Factor (VIF)** for every predictor in `combined_features.csv` (using `statsmodels`). Flag any with VIF > 5 and write `reports/diagnostics/vif_report.json` (list of flagged predictors and their VIF values).  
  - Compute **mutual information** between the traditional descriptor set and the topological feature set (`sklearn.feature_selection.mutual_info_regression`) and write summary statistics to `reports/diagnostics/mi_report.json`.  
  - **Verification**: Both JSON files are present; the VIF report includes a non‑empty `flagged` array if any predictor exceeds the threshold.

- [ ] **T015** **[US3]** *Redundancy significance threshold*  
  - Parse `reports/diagnostics/mi_report.json` and assert that the reported mutual information between traditional and topological feature sets exceeds **0.1** (non‑trivial redundancy).  
  - If the threshold is not met, fail the pipeline with a clear error message.  
  - **Verification**: The task exits with status 0 only when MI > 0.1; otherwise `pytest code/tests/test_mi_threshold.py` fails.

- [ ] **T010** **[ ]** *Resource‑monitor wrapper*  
  - Run the **entire pipeline** (tasks T001–T009) under `code/07_resource_monitor.py`. Record peak RAM usage and total CPU time in `reports/metrics/resource_usage.json`.  
  - Ensure RAM < 6.3 GB and total runtime < 5.4 h (SC‑004).  
  - **Verification**: JSON fields `peak_ram_gb` and `cpu_hours` satisfy the limits.

- [ ] **T011** **[US3]** *Figures, tables, and summary artefacts*  
  - Generate visualisations: (a) example Betti curves & persistence images, (b) per‑fold R²/RMSE boxplots for each model, (c) sensitivity‑sweep performance curve. Save PNGs under `reports/figures/`.  
  - Produce a consolidated CSV summary `reports/metrics/summary_table.csv` that joins model performance, corrected p‑values, VIF flags, and mutual‑information values.  
  - **Verification**: All figure files exist; the CSV can be read without error and contains the expected columns.

- [ ] **T012** **[P]** *Quickstart documentation & paper‑stage handoff*  
  - Update `specs/001-predicting-molecular-properties-from-top/quickstart.md` with the exact command sequence (including the resource‑monitor wrapper), fixed seed 42, and clear references to every generated artefact (CSV, JSON, PNG).  
  - Add a **“Paper‑stage handoff”** section that lists the artefacts the downstream writing pipeline must consume (`model_performance.json`, `summary_table.csv`, key figures, diagnostics JSONs).  
  - **Verification**: The quickstart file renders without broken links; a dry‑run (`bash quickstart.sh`) reproduces the full pipeline from raw data to final artefacts with exit code 0.