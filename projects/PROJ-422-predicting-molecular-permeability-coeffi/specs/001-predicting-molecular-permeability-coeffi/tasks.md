# Tasks: Predicting Molecular Permeability Coefficients Using Graph Neural Networks and Publicly Available Datasets  

**Inputs**: `spec.md`, `plan.md`, the contracts in `specs/001-predicting-molecular-permeability-coeffi/`, and reviewer feedback.  

The tasks are ordered to respect data flow and to satisfy every functional requirement (FR‑001 – FR‑012) and success criteria (SC‑001 – SC‑005). All scripts write their outputs under the project‑owned directories `data/`, `code/`, `results/`, or `figures/`.  

---

## Phase 0 – Conditional dataset validation  

- [ ] **T000** [Phase 0] Implement `code/data/check_permeability.py` – scans candidate verified datasets (listed in `config/verified_datasets.yaml`) for the presence of a `permeability` column.
  - If a dataset with the required column is found, writes its identifier to `config/selected_dataset.yaml` and exits with status 0.  
  - If no such dataset exists, logs an informative error and exits with non‑zero status, halting the entire pipeline.  
  - **Verification**: unit test `tests/unit/test_check_permeability.py` asserts that the script exits 0 only when the column is present and that the config file is created.

## Phase 1 – Data acquisition, preprocessing, and splitting  

- [ ] **T001** [US‑1] Implement `code/data/download.py` – streams the dataset identified by `config/selected_dataset.yaml` via `datasets.load_dataset("<selected>", streaming=True)`.  
  - Writes raw files to `data/raw/` and a SHA‑256 manifest to `data/raw/checksums.json`.  
  - **Verification**: `tests/unit/test_download.py` asserts that at least one row is written and that the `permeability` column exists in the raw file.

- [ ] **T002** [US‑1] Implement `code/data/preprocess.py` – `MoleculeProcessor.process(df)` that:  
  1. Parses each SMILES with `rdkit.Chem.MolFromSmiles`; logs and excludes invalid SMILES (FR‑011).  
  2. Computes the required RDKit descriptors (MW, logP, TPSA, HBA, HBD, rotatable bonds).  
  3. Builds a molecular‑graph JSON column (node & edge features).  
  4. Writes **both** `data/processed/processed_data.parquet` **and** `data/processed/processed_data.csv` **before** any guard checks (so the unit test can see the files).  
  5. After writing, calculates the fraction of rows with `mol_valid=True`; if < 95 % the script logs a warning and exits with a non‑zero code (FR‑012).  
  6. Rows with a missing `permeability` value are excluded from the output (they will not be used for modeling).  
  - **Verification**: `tests/unit/test_preprocess.py` checks that both output files exist, that `mol_valid` is a boolean, and that the retention guard triggers only when the valid‑molecule rate falls below 95 %.

- [ ] **T003** [US‑1] Implement `code/data/split.py` – reads `data/processed/processed_data.parquet`, filters to rows where `target` is non‑null, then:  
  1. If a `polymer_type` column exists, performs an 80/20 **stratified** split preserving an absolute ≤ 5 percentage‑point difference per class (FR‑004).  
  2. If `polymer_type` is absent, falls back to a random 80/20 split with a logged warning.  
  3. Writes `data/processed/train.parquet` and `data/processed/test.parquet`.  
  - **Verification**: `tests/integration/test_pipeline.py` asserts that both split files exist, that the split ratio is ≈ 0.8/0.2, and that stratification constraints are met when applicable.

## Phase 2 – Model implementation, training, evaluation, and interpretation  

- [ ] **T004** [US‑2] Implement `code/models/gnn.py` – a **CPU‑only** 3‑layer Message Passing Neural Network (hidden = 64, global mean pooling) with:  
  - Early‑stopping on validation loss (patience = 5, max epochs = 50).  
  - `device="cpu"` enforced (no CUDA calls).  
  - Saves the trained model via `torch.save` to `code/models/gnn.pt`.  
  - **Verification**: unit test `tests/unit/test_models.py::test_gnn_training` confirms that training finishes within the 6‑hour wall‑time budget on the CI runner and that a checkpoint file is produced.

- [ ] **T005** [US‑2] Implement `code/models/rf.py` – a `RandomForestRegressor` (n_estimators = 200, max_features=`'sqrt'`) trained on the **full descriptor vector** (MW, logP, TPSA, HBA, HBD, rotatable bonds).  
  - Saves the model with `joblib.dump` to `code/models/rf.pkl`.  
  - **Verification**: `tests/unit/test_models.py::test_rf_training` checks that the pickle file exists and that `feature_importances_` has length = 6.

- [ ] **T007** [US‑2] Implement `code/analysis/train.py` – orchestrates training of the two models:  
  1. Loads `data/processed/train.parquet`.  
  2. Trains GNN and RF, recording **total training time (hours)** and **peak memory (GB)** in `results/training_log.json`.  
  3. Writes a flag `no_significant_improvement: true` if the GNN’s test RMSE is not lower than the RF baseline.  
  - **Verification**: integration test runs the script on a small sampled subset and asserts that both model files are present and that `training_log.json` contains the required fields.

- [ ] **T008** [US‑2] Implement `code/analysis/evaluate.py` – loads `data/processed/test.parquet` and the two trained models, computes **RMSE, MAE, and R²** for each, and writes:  
  - `results/metrics.json` (conforms to `contracts/results.schema.yaml`).  
  - `results/prediction_errors.json` containing per‑sample absolute errors for GNN and RF baseline.  
  - **Verification**: a test validates that `metrics.json` passes JSON‑schema validation and that each metric is a finite number.

- [ ] **T009** [US‑2] Implement `code/analysis/statistics.py` – performs the statistical comparison required by FR‑008:  
  1. Runs a **Shapiro‑Wilk** test on the paired error differences.  
  2. If normal (p ≥ 0.05) executes a **paired t‑test**; otherwise a **Wilcoxon signed‑rank test**.  
  3. Computes **Cohen’s d** and a **post‑hoc power analysis** (using the observed effect size and the test sample size).  
  4. Inserts the results (`p_value`, `significant`, `method`, `cohen_d`, `power`, etc.) into `results/metrics.json`.  
  - **Verification**: a unit test checks that the `statistical_test` object in `metrics.json` contains the required keys and that `significant` matches the p‑value threshold.

- [ ] **T010** [US‑3] Implement `code/analysis/explain.py` – interpretable‑model analysis:  
  1. Runs **SHAP (KernelExplainer)** on the RF baseline, outputs a ranked CSV `results/interpretability/shap_ranked_descriptors.csv` and a bar‑chart PNG `figures/shap_bar.png`.  
  2. Runs **GNNExplainer** on 100 random test molecules, aggregates masks to a global substructure importance ranking, writes `results/interpretability/gnn_substructures.csv` and a heat‑map PNG `figures/gnn_substructures.png`.  
  3. Computes the **overlap‑count metric** (`overlap_top5`) between the top‑5 SHAP descriptors and the top‑5 GNN substructures, stores it (and the boolean `overlap_meets_threshold` ≥ 3) in `results/metrics.json` (fulfilling SC‑003).  
  - **Verification**: test asserts that both CSV files contain at least 5 rows, that the PNGs are generated, and that the overlap fields are present in `metrics.json`.

- [ ] **T011** [US‑3] Implement `code/analysis/report.py` – assembles a human‑readable **comparative report** `results/comparative_report.md` that:  
  1. Summarizes all performance metrics (RMSE, MAE, R²) for GNN and RF.  
  2. Presents the statistical‑test outcome (method, p‑value, significance).  
  3. Lists the top‑5 SHAP descriptors and top‑5 GNN substructures, shows the `overlap_top5` value, and states whether SC‑003 is satisfied.  
  4. Includes warnings for any bias‑check failures (if a future spec amendment adds such a check) and for the `no_significant_improvement` flag.  
  5. Embeds the figures `figures/shap_bar.png` and `figures/gnn_substructures.png`.  
  - **Verification**: a test parses the markdown and confirms that required sections and numeric values are present.

- [ ] **T012** [P] Implement `code/utils/verify_metrics.py` – validates `results/metrics.json` against `contracts/results.schema.yaml` **and** checks that all success criteria (SC‑001 – SC‑005) are met:  
  - Paired‑test significance (p < 0.05).  
  - Power analysis `sufficient: true`.  
  - `bias_warning` is false (or absent).  
  - `overlap_meets_threshold` is true.  
  - Training time ≤ 6 h and peak memory ≤ 7 GB.  
  - Exits with status 0 only if every condition holds.  
  - **Verification**: integration test runs the script after a full pipeline execution and expects a zero exit code.

- [ ] **T013** Implement `run_all.sh` – a reproducible end‑to‑end driver that:  
  1. Sets deterministic seeds (`numpy`, `torch`, `random`).  
  2. Executes the pipeline in order: `check_permeability.py → download.py → preprocess.py → split.py → train.py → evaluate.py → statistics.py → explain.py → report.py → verify_metrics.py`.  
  3. Captures the overall exit status; on success writes a short hand‑off document `results.md` that references the key artefacts (dataset source URL, `results/comparative_report.md`, `results/metrics.json`).  
  - **Verification**: a CI test runs `bash run_all.sh` and asserts that the final exit code is 0 and that `results.md` exists.

---  

## Dependency‑to‑Requirement Mapping  

| Requirement | Task(s) that satisfy it |
|-------------|------------------------|
| FR‑001 (real permeability target) | T000 (ensures dataset has `permeability`), T001 (downloads verified dataset) |
| FR‑002 (SMILES → graph) | T002 |
| FR‑003 (standard descriptors) | T002 |
| FR‑004 (stratified split ≤5 pp diff) | T003 |
| FR‑005 (Random Forest baseline) | T005 |
| FR‑006 (CPU‑only MPNN) | T004 |
| FR‑007 (RMSE/MAE/R²) | T008 |
| FR‑008 (paired statistical test) | T009 |
| FR‑009 (SHAP & GNNExplainer) | T010 |
| FR‑010 (comparative report) | T011 |
| FR‑011 (invalid SMILES handling) | T002 |
| FR‑012 (≥95 % valid molecules) | T002 |
| SC‑001 – SC‑005 | T008, T009, T010, T012, T013 |

---  

*All tasks are unchecked; completed work must be re‑executed to satisfy the pending reviewer failures.*  