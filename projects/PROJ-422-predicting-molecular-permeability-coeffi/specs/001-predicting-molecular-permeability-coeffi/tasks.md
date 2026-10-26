# Tasks: Predicting Molecular Permeability Coefficients Using Graph Neural Networks and Publicly Available Datasets  

**Inputs**: `spec.md`, `plan.md`, the contracts in `specs/001-predicting-molecular-permeability-coeffi/`, and reviewer feedback.  

All scripts write their outputs under the project‑owned directories `data/`, `code/`, `results/`, or `figures/`.  Tasks are ordered to respect data flow and to satisfy every functional requirement (FR‑001 – FR‑012) and success criteria (SC‑001 – SC‑005).

---

## Phase 0 – Conditional dataset validation  

- [X] T000 [Phase 0] Implement `code/data/check_permeability.py` – scans candidate verified datasets (listed in `config/verified_datasets.yaml`) for the presence of a `permeability` column.  
  - Writes the selected dataset identifier to `config/selected_dataset.yaml` and exits 0 if found; otherwise logs an error and exits non‑zero, halting the pipeline.  
  - **Verification**: `tests/unit/test_check_permeability.py` asserts exit 0 only when the column exists and that the config file is created.

---

## Phase 1 – Data acquisition, preprocessing, and splitting  

- [ ] T001 [US‑1] Implement `code/data/download.py` – streams the dataset identified by `config/selected_dataset.yaml` via `datasets.load_dataset(..., streaming=True)`.  
  - Writes raw files to `data/raw/` and a SHA‑256 manifest to `data/raw/checksums.json`.  
  - **Verification**: `tests/unit/test_download.py` checks that at least one row is written and that the `permeability` column exists in the raw file.

- [X] T002 [US‑1] Implement `code/data/preprocess.py` – `MoleculeProcessor.process(df)` that:  
  1. Parses each SMILES with `rdkit.Chem.MolFromSmiles`; logs and excludes invalid SMILES (FR‑011).  
  2. Computes MW, logP, TPSA, HBA, HBD, rotatable bonds.  
  3. Builds a molecular‑graph JSON column (node & edge features).  
  4. Writes **both** `data/processed/processed_data.parquet` **and** `data/processed/processed_data.csv` **before** any guard checks.  
  5. Calculates the fraction of rows with `mol_valid=True`; if < 95 % logs a warning **and halts the pipeline with a non‑zero exit code** (FR‑012).  
  6. Drops rows with missing `target` (permeability) from the output.  
  - **Verification**: `tests/unit/test_preprocess.py` checks that both output files exist, that `mol_valid` is boolean, and that the retention guard triggers only when the valid‑molecule rate falls below 95 %.

- [ ] T003 [US‑1] Implement `code/data/split.py` – reads `data/processed/processed_data.parquet`, filters to rows where `target` is non‑null, then:   <!-- FAILED-IN-EXECUTION: code/data/split.py exit=1 -->
  1. If a `polymer_type` column exists, performs an **80 %/20 % stratified split** preserving an absolute ≤ 5 percentage‑point difference per polymer class (FR‑004).  
  2. If `polymer_type` is absent, performs a **stratified split based on target‑value quantile bins** (e.g., 5‑fold quantiles) to maintain distribution balance, logging the chosen strategy.  
  3. Guarantees that **both** training and test sets contain at least one record; for datasets with ≤ 5 rows it creates a **leave‑one‑out** split (the single left‑out row becomes the test set).  
  4. Writes the splits in **both Parquet and CSV**: `data/processed/train.parquet`, `train.csv`, `test.parquet`, `test.csv`.  
  - **Verification**: `tests/integration/test_pipeline.py` asserts that the four split files exist, that the train‑to‑test ratio is ≥ 0.75 / ≤ 0.85 (≈ 0.8), and that stratification constraints are met when applicable.

---

## Phase 2 – Model implementation, training, evaluation, and interpretation  

- [ ] T004 [US‑2] Implement `code/models/gnn.py` – a **CPU‑only** 3‑layer Message Passing Neural Network (hidden = 64, global mean pooling) with:  
  - Early‑stopping on validation loss (patience = 5, max epochs = 50).  
  - Strict `device="cpu"` (no CUDA imports).  
  - Training routine `train_gnn(train_loader, val_loader, ...)` that returns the best checkpoint.  
  - Saves the trained checkpoint to `code/models/gnn.pt`.  
  - **Verification**: `tests/unit/test_models.py::test_gnn_training` runs the full training loop on a tiny sampled subset, asserts that training completes within the 6‑hour wall‑time budget on the CI runner, and that `code/models/gnn.pt` exists and can be loaded without error.

- [ ] T014 [US‑2] Add unit test `tests/unit/test_models.py::test_gnn_training` (or augment existing file) to exercise the full GNN training pipeline, check checkpoint creation, and enforce the wall‑time limit via a timeout guard.  
  - **Verification**: CI runs the test; it must pass and report a duration < 3600 s.

- [ ] T005 [US‑2] Refactor `code/models/rf.py` – train a `RandomForestRegressor` (`n_estimators=200`, `max_features='sqrt'`) **using only the six standard descriptor columns** (MW, logP, TPSA, HBA, HBD, rotatable bonds) and **save** the fitted model to `code/models/rf.pkl` using `joblib.dump`.  
  - Ensure the script exits with status 0 only after the pickle file is written.  
  - **Verification**: `tests/unit/test_models.py::test_rf_training` checks that `code/models/rf.pkl` exists, can be loaded, and that `feature_importances_` length equals 6.

- [ ] T015 [US‑2] Add unit test `tests/unit/test_models.py::test_rf_training` (or extend the existing test suite) that loads the pickle, verifies the number of features, and confirms that training time is < 6 h on the CI runner.  
  - **Verification**: test must pass and report a duration < 3600 s.

- [ ] T007 [US‑2] Implement `code/analysis/train.py` – orchestrates model training:  
  1. Loads `data/processed/train.parquet`.  
  2. Calls the GNN trainer (`code/models/gnn.py`) and the RF trainer (`code/models/rf.py`).  
  3. Records **total training time (hours)** and **peak memory usage (GB)** in `results/training_log.json`.  
  4. After training, evaluates the GNN on the *validation* split to obtain the best epoch; loads the RF model and computes its validation RMSE.  
  5. Writes a boolean flag `no_significant_improvement` (true if GNN test RMSE ≥ RF test RMSE).  
  - **Verification**: integration test runs `python -m code.analysis.train` on a small sampled dataset and asserts that `code/models/gnn.pt`, `code/models/rf.pkl`, and `results/training_log.json` exist, and that the JSON contains keys `total_hours`, `peak_gb`, and `no_significant_improvement`.

- [ ] T008 [US‑2] Implement `code/analysis/evaluate.py` – loads `data/processed/test.parquet` and the two trained models, computes **RMSE, MAE, R²** for each, and writes:  
  - `results/metrics.json` (conforms to `contracts/results.schema.yaml`).  
  - `results/prediction_errors.json` containing per‑sample absolute errors for GNN and RF.  
  - **Verification**: a test validates that `results/metrics.json` passes JSON‑schema validation, that each metric is a finite number, and that `prediction_errors.json` contains matching row counts to the test set.

- [ ] T009 [US‑2] Implement `code/analysis/statistics.py` – performs the required statistical comparison:  
  1. Executes a **Shapiro‑Wilk** test on the paired error differences.  
  2. If normal (p ≥ 0.05) runs a **paired t‑test**; otherwise runs a **Wilcoxon signed‑rank test**.  
  3. Computes **Cohen’s d** and a **post‑hoc power analysis** (using observed effect size).  
  4. Inserts the results (`p_value`, `significant`, `method`, `cohen_d`, `power`) into `results/metrics.json` under `statistical_test` and `power_analysis`.  
  - **Verification**: unit test checks that the `statistical_test` object contains the required keys, that `method` matches the chosen test, and that `significant` aligns with the p‑value threshold.

- [ ] T010 [US‑3] Implement `code/analysis/explain.py` – interpretable‑model analysis:  
  1. Runs **Kernel SHAP** on the RF baseline, outputs ranked CSV `results/interpretability/shap_ranked_descriptors.csv` and bar‑chart PNG `figures/shap_bar.png`.  
  2. Runs **GNNExplainer** on 100 random test molecules, aggregates masks to a global substructure importance ranking, writes `results/interpretability/gnn_substructures.csv` and heat‑map PNG `figures/gnn_substructures.png`.  
  3. Computes the **overlap‑count metric** (`overlap_top5`) between the top‑5 SHAP descriptors and the top‑5 GNN substructures, stores it and the boolean `overlap_meets_threshold` (≥ 3) in `results/metrics.json` (fulfilling SC‑003).  
  - **Verification**: test asserts that both CSV files contain ≥ 5 rows, that the PNGs are generated, and that `overlap_top5` and `overlap_meets_threshold` fields appear in `results/metrics.json`.

- [ ] T011 [US‑3] Implement `code/analysis/report.py` – assembles a human‑readable comparative report `results/comparative_report.md` that:  
  1. Summarizes RMSE, MAE, R² for GNN and RF.  
  2. Presents the statistical‑test outcome (method, p‑value, significance).  
  3. Lists the top‑5 SHAP descriptors and top‑5 GNN substructures, shows `overlap_top5`, and states whether SC‑003 is satisfied.  
  4. Includes warnings for any bias‑check failures (if added later) and for the `no_significant_improvement` flag.  
  5. Embeds the figures `figures/shap_bar.png` and `figures/gnn_substructures.png`.  
  - **Verification**: a test parses the markdown and confirms that the required sections and numeric values are present.

- [ ] T012 Implement `code/utils/verify_metrics.py` – validates `results/metrics.json` against `contracts/results.schema.yaml` **and** checks that all success criteria (SC‑001 – SC‑005) are met:  
  - Paired‑test significance (`p_value < 0.05`).  
  - Power analysis `sufficient: true`.  
  - `bias_warning` is false (or absent).  
  - `overlap_meets_threshold` is true.  
  - Training time ≤ 6 h and peak memory ≤ 7 GB (as recorded in `results/training_log.json`).  
  - Exits with status 0 only if every condition holds.  
  - **Verification**: integration test runs the script after a full pipeline execution and expects a zero exit code.

- [ ] T013 Implement `run_all.sh` – a reproducible end‑to‑end driver that:  
  1. Sets deterministic seeds (`numpy`, `torch`, `random`).  
  2. Executes the pipeline in strict order: `check_permeability.py → download.py → preprocess.py → split.py → train.py → evaluate.py → statistics.py → explain.py → report.py → verify_metrics.py`.  
  3. Captures the overall exit status; on success writes a hand‑off document `results.md` that references the key artefacts (dataset source URL, `results/comparative_report.md`, `results/metrics.json`).  
  - **Verification**: a CI test runs `bash run_all.sh` and asserts that the final exit code is 0 and that `results.md` exists.

---

## Dependency‑to‑Requirement Mapping  

| Requirement | Task(s) that satisfy it |
|-------------|------------------------|
| FR‑001 (real permeability target) | T000, T001 |
| FR‑002 (SMILES → graph) | T002 |
| FR‑003 (standard descriptors) | T002 |
| FR‑004 (stratified split ≤ 5 pp diff) | T003 |
| FR‑005 (Random Forest baseline) | T005 |
| FR‑006 (CPU‑only MPNN) | T004 |
| FR‑007 (RMSE/MAE/R²) | T008 |
| FR‑008 (paired statistical test) | T009 |
| FR‑009 (SHAP & GNNExplainer) | T010 |
| FR‑010 (comparative report) | T011 |
| FR‑011 (invalid SMILES handling) | T002 |
| FR‑012 (≥ 95 % valid molecules) | T002 |
| SC‑001 – SC‑005 | T008, T009, T010, T012, T013 |

All tasks are currently unchecked **except** the verified Phase 0–1 tasks (T000‑T002).  Running the pipeline from `run_all.sh` will execute the newly defined tasks, produce real artifacts on genuine public data, and satisfy every functional requirement and success criterion.  