# Tasks: Predicting Molecular Properties from Topological Data Analysis

**Inputs**: Active `spec.md`, `plan.md`, original research idea, existing artifacts, reviewer/verifier feedback.

The goal is to deliver a complete, reproducible, CPU‑only study that satisfies every functional requirement (FR‑001…FR‑009) and success criterion (SC‑001…SC‑005) while respecting platform constraints (real data only, no synthetic fallbacks, no GPU). Tasks are ordered to respect data flow; later tasks depend on outputs of earlier ones.

---

## Phase 1: Setup and first end‑to‑end analysis

- [ ] T001 [US1] *Data ingestion, provenance, and scaffold split creation*  
  - In `code/01_data_ingestion.py`, download the **ESOL** dataset from the verified DeepChem S3 URL `https://deepchemdata.s3-us-west-1.amazonaws.com/datasets/delaney-processed.csv` (the `--url` argument **must** be used).  
  - Verify required columns `smiles` and `logP` (conforms to `dataset.schema.yaml`); abort with a clear Data Gap error if missing.  
  - Compute SHA‑256 checksum of `data/raw/esol.csv` and **idempotently** append it to `data/checksums.txt`.  
  - Perform a priori power analysis (paired t‑test, α = 0.05, power = 0.8, effect size = 0.5) and write `data/processed/power_analysis_report.json` (`min_n`, `actual_n`, `passes`).  
  - Exclude molecules with molecular weight > 1000 Da; log each excluded SMILES to `data/logs/large_molecule_exclusions.log` using idempotent append.  
  - Process remaining records with **chunked CSV iteration** (streaming) to stay within RAM limits.  
  - Count unique Bemis‑Murcko scaffolds; abort if < 100, otherwise write `data/processed/scaffold_counts.json`.  
  - Generate scaffold‑based 5‑fold split (seed 42) and store indices in `data/processed/splits.json`.  
  - Write the filtered, schema‑validated dataset to `data/processed/filtered_esol.csv`.  
  - **Verification**:  
    1. `data/raw/esol.csv` row count ≈ 1128 and first SMILES matches the real ESOL file.  
    2. `data/checksums.txt` contains a single line per checksummed file (no duplicates after re‑run).  
    3. `jq .passes data/processed/power_analysis_report.json` returns `true`.  
    4. `python -c "import pandas as pd; df=pd.read_csv('data/processed/filtered_esol.csv'); assert df.shape[0] >= 128"` succeeds.  
    5. Scaffold exclusivity across folds is confirmed by a quick script.  
    6. `data/logs/large_molecule_exclusions.log` has no duplicate entries after re‑run.

- [ ] T001a *Checksum verification*  
  - Run `code/00_checksum_verify.py` to recompute and compare checksums for all files listed in `data/checksums.txt`.  
  - Abort if any mismatch is detected, ensuring downstream tasks operate on verified inputs.  
  - **Verification**: Script exits with status 0 only when all checksums match; otherwise it prints mismatched paths.

- [ ] T014 *Dataset schema contract test*  
  - `code/tests/test_dataset_schema.py` loads `data/raw/esol.csv` and validates it against `dataset.schema.yaml`.  
  - **Verification**: `pytest code/tests/test_dataset_schema.py` passes. *(Verified; reopens automatically if T001's data changes break it.)*

- [ ] T002 [US1] *Baseline TDA feature computation (10 × 10 persistence images)*  
  - Read `data/processed/filtered_esol.csv`. For each SMILES, build a molecular graph with RDKit and apply the **shortest‑path distance filtration** (FR‑001) via `code/utils/persistence_utils.py`.  
  - Vectorize each persistence diagram to a **10 × 10 persistence image** using **kernel_bandwidth = 1.0** (σ = 1.0) – the default documented in `data-model.md`. Include `target_property` (`logP`) and `target_value` fields per `feature_matrix.schema.yaml`.  
  - Write `data/processed/topological_features_10x10.csv` (columns: `molecule_id` as **string** + 100 float features).  
  - Log invalid SMILES to `data/logs/invalid_smiles.log`; handle disconnected graphs and empty diagrams gracefully (zero‑vector fallback).  
  - **Verification**: (1) CSV contains no NaN; (2) row count matches `filtered_esol.csv`.

- [ ] T003 [P] *Feature‑matrix contract test*  
  - `code/tests/test_feature_matrix.py` loads `topological_features_10x10.csv` and validates it against `feature_matrix.schema.yaml`, ensuring `target_property` and `target_value` are present.  
  - Cast **both** `molecule_id` columns to `str` before any merge with `filtered_esol.csv`.  
  - **Verification**: `pytest code/tests/test_feature_matrix.py` exits 0.

- [ ] T004 [US1] *Traditional descriptors & combined feature matrix*  
  - In `code/03_feature_engineering.py`, compute RDKit traditional descriptors (molecular weight, atom counts, 1024‑bit Morgan fingerprint, radius 2) and write `data/processed/traditional_features.csv`.  
  - Merge the traditional matrix with `topological_features_10x10.csv` on `molecule_id` (both cast to string) → `data/processed/combined_features.csv`.  
  - Ensure no missing values across the merged table.  
  - **Verification**: Row counts of all three CSVs match; `pandas.isnull().sum().sum()` is `0`; script exits 0.

---

## Phase 2: Complete the study and validate its evidence

- [ ] T005 [US2] *Baseline model training and evaluation (including feature importance)*  
  - Load `data/processed/splits.json`. Train **Ridge Regression (α = 1.0)** and **Random Forest (100 trees, max_depth = 10, seed = 42)** on three feature sets: `traditional`, `topological`, `combined`, using the 5‑fold scaffold‑based CV (FR‑003, FR‑004).  
  - Enforce CPU‑only execution with a dependency‑free GPU guard (check for `/dev/nvidia*` or `nvidia-smi`; abort if present) (FR‑008).  
  - Write `reports/metrics/model_metrics.json` conforming to `model_metrics.schema.yaml` (includes per‑fold R²/RMSE, means, and `feature_importance` arrays for traditional and topological descriptors).  
  - Log the training run (seed, split details) to `data/logs/training.log`.  
  - **Verification**: Run `code/tests/validate_model_performance.py` which checks the JSON against the schema and confirms required fields exist.

- [ ] T006 [P] *Model‑metrics contract test*  
  - `code/tests/test_metrics_schema.py` validates `reports/metrics/model_metrics.json` against `model_metrics.schema.yaml`.  
  - **Verification**: `pytest code/tests/test_metrics_schema.py` exits 0.

- [ ] T007 [US3] *Sensitivity sweep of vectorization resolution*  
  - Extend `code/02_tda_computation.py` with a `--grid` CLI argument to generate **20 × 20** and **30 × 30** persistence‑image CSVs (`topological_features_20x20.csv`, `topological_features_30x30.csv`).  
  - Run `code/05_sensitivity_analysis.py` which (a) calls the TDA script for each grid size, (b) retrains the same models (Ridge & RF, three feature sets) on each resolution using the existing splits, and (c) aggregates mean R² and its std per resolution.  
  - Write `reports/metrics/sensitivity_report.json` with entries `{ "grid_size": 10, "r2_mean": ..., "r2_std": ... }` for 10, 20, 30.  
  - **Verification**: JSON contains three objects with numeric `grid_size`, `r2_mean`, and `r2_std`.

- [ ] T013 *Specification amendment — scope reduction to logP*  
  - Create `specs/001-predicting-molecular-properties-from-top/spec_amendment_scope_reduction.md` documenting the decision to limit the study to the single property **logP** from ESOL, with resource and power‑analysis justification.  
  - Update `spec.md` to state “logP only” and modify FR‑005/SC‑003 to reference **N = 1** hypothesis test.  
  - **Verification**: (1) amendment file exists; (2) `code/tests/test_spec_update.py` asserts the presence of “logP only” and the updated N = 1 wording; (3) script exits 0.  
  - **Note**: This task is now a **hard prerequisite** for T008.

- [ ] T008 [US3] *Statistical comparison & Bonferroni correction*  
  - Using per‑fold R² from `model_metrics.json`, perform paired t‑tests (or Wilcoxon if non‑normal) comparing **combined** vs **traditional** models.  
  - Apply the **plain Bonferroni** correction (as mandated by FR‑005) and write `reports/metrics/bonferroni_diagnostics.json`; also insert `bonferroni_adjusted_p` into this diagnostics file (not into `model_metrics.json`).  
  - Write `reports/metrics/fwer_report.json` containing `alpha`, `rejections`, and `fwer_bound`.  
  - **Verification**: Both JSONs exist; `pytest code/tests/test_correction.py` confirms correct Bonferroni logic; `bonferroni_diagnostics.json` contains the adjusted p‑value.

- [ ] T009 [US3] *Collinearity and redundancy diagnostics*  
  - Compute **VIF** for every predictor in `combined_features.csv` (no model restriction) and write `reports/diagnostics/vif_report.json` (include a `flagged` array for VIF > 5).  
  - Compute **mutual information** between traditional and topological feature sets: for each traditional descriptor and each topological feature compute `mutual_info_regression`; report the **average MI** as `average_mi` in `reports/diagnostics/mi_report.json`.  
  - **Verification**: Both JSONs present; VIF report includes `flagged`; MI report contains numeric `average_mi`.

- [ ] T015 [US3] *Redundancy significance reporting*  
  - Parse `reports/diagnostics/mi_report.json` and **log** the reported `average_mi`. If it falls below 0.1, emit a warning (do **not** abort).  
  - **Verification**: `pytest code/tests/test_mi_reporting.py` checks that the script runs without error and that a warning is logged when appropriate.

- [ ] T010 *Resource‑monitor wrapper*  
  - Run the entire pipeline (T001–T009) under `code/07_resource_monitor.py`; record peak RAM and total CPU time in `reports/metrics/resource_usage.json`.  
  - Enforce RAM < 6.3 GB and runtime < 5.4 h (SC‑004).  
  - **Verification**: JSON fields `peak_ram_gb` and `cpu_hours` satisfy the limits; `pytest code/tests/test_resource_limits.py` passes.

- [ ] T011 [US3] *Figures, tables, and summary artifacts*  
  - Generate figures under `reports/figures/`: (a) example Betti curves & persistence images, (b) per‑fold R²/RMSE boxplots per model, (c) sensitivity‑sweep performance curve.  
  - Produce `reports/metrics/summary_table.csv` joining model performance, corrected p‑values, VIF flags, and average MI.  
  - **Verification**: All figure files exist; the CSV reads without error and contains the expected columns.

## Phase 3: Reproducible results and paper handoff

- [ ] T012 [P] *Quickstart documentation & paper‑stage handoff*  
  - Update `specs/001-predicting-molecular-properties-from-top/quickstart.md` with the exact command sequence (including the resource‑monitor wrapper), fixed seed 42, and references to every generated artifact (CSV, JSON, PNG).  
  - Add a **“Paper‑stage handoff”** section listing the artifacts the downstream writing pipeline must consume (`model_metrics.json`, `bonferroni_diagnostics.json`, `fwer_report.json`, `summary_table.csv`, key figures, diagnostics JSONs), and describe negative findings/limitations honestly.  
  - **Verification**: Quickstart renders without broken links; a dry‑run of the documented command sequence reproduces the pipeline from raw data to final artifacts with exit code 0.

---

## Dependencies and requirement coverage

| Requirement | Task(s) | Demonstrating command |
|---|---|---|
| FR-001 (shortest‑path filtration) | T002 | `python code/02_tda_computation.py --grid 10` |
| FR-002 (10×10 baseline + target fields) | T002, T003 | `pytest code/tests/test_feature_matrix.py` |
| FR-003 (models & feature sets) | T004, T005 | `python code/04_model_training.py` |
| FR-004 (scaffold 5‑fold CV, seed 42) | T001, T005 | scaffold‑exclusivity check in T001 |
| FR-005 (Bonferroni) | T008, T013 | `pytest code/tests/test_correction.py` |
| FR-006 (resolution sweep) | T007 | `python code/05_sensitivity_analysis.py` |
| FR-007 (VIF diagnostics) | T009 | `reports/diagnostics/vif_report.json` |
| FR-008 (CPU‑only) | T005 | GPU‑guard using `/dev/nvidia*` or `nvidia-smi` |
| FR-009 (mutual information) | T009, T015 | `pytest code/tests/test_mi_reporting.py` |
| SC‑001…SC‑005 | T005, T007, T008, T010, T009 | see per‑task verification |

**Execution order** (respecting dependencies):  
T001 → T001a → T014 → T002 → T003 → T004 → T005 → T006 → T007 → T013 → T008 → T009 → T015 → T010 → T011 → T012.

All tasks now satisfy the spec, data‑model, and constitutional constraints while remaining fully executable on the CPU‑only GitHub Actions tier.  
