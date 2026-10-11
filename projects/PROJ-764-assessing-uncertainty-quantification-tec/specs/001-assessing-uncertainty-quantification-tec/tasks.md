# Tasks: Assessing Uncertainty Quantification Techniques for Machine‑Predicted Material Properties  

**Input**: `spec.md`, `plan.md`, `data‑model.md`, and all contract schemas in `specs/001‑assessing‑uncertainty‑quantification‑tec/contracts/`.  

**Goal**: Deliver a reproducible end‑to‑end pipeline that (1) downloads the OQMD subset, (2) preprocesses it, (3) trains a 2‑layer baseline NN and three lightweight UQ methods, (4) evaluates calibration, (5) runs a downstream screening case study, and (6) produces all required artefacts compliant with the SSoT schemas.  

> **Checked boxes (`[X]`) indicate work that has already passed verification.**  
> **Unchecked boxes (`[ ]`) are pending – they have been reopened because the verifier found missing or malformed artefacts.**  

---

## Phase 1 – Project scaffolding & quick‑start documentation  

| ID | Status | Description |
|----|--------|-------------|
| - [X] T001b | **P** | Create initial empty files: `code/requirements.txt`, `code/config.yaml`, `README.md`. |
| - [X] T001 | **P** | Document the data‑source deviation (Materials Project → OQMD) in `docs/data_source_rationale.md` to satisfy reproducibility. |
| - [X] T002 | **P** | Initialise a Python project and pin all dependencies in `requirements.txt`. |
| - [X] T003 | **P** | Add linting (`ruff`) and formatting (`black`) config files (`.ruff.toml`, `.black.toml`). |

---

## Phase 2 – Foundational infrastructure (blocking)  

### Core configuration  

- [ ] T004 **P** `code/config.yaml`  
  *Keys & types*: `seed: int (42)`, `split_ratio: [0.8,0.1,0.1]`, `split_type: "stratified"`, `timeout_hours: 5.0`, `screening_recall_target: 0.8`, `robustness_seeds: [42,43,44]`, `robustness_cv_threshold: 0.1`, `screening_precision_gain_threshold: 0.05`.  

### Data download & validation  

- [ ] T005 **P** `code/data/download.py`  
  *Downloads* `https://huggingface.co/datasets/OQMD/OQMD-Subset` via `datasets.load_dataset`.  
  *Retries* up to 3 times with exponential back‑off; on final failure raises `RuntimeError`.  
  *Outputs*: `data/raw/oqmd_subset.parquet` and `data/checksums.json` (SHA‑256).  
  *Validation*: Generates `data/validation_report.json` if structural columns are missing (schema `validation_report.schema.yaml`).  

### **Re‑opened tasks – preprocessing & PCA**  

- [ ] **T006a** **P** `code/data/preprocess.py` – *Stratified split generation*  
  *Read* `code/config.yaml` (`split_ratio`, `seed`).  
  *Load* `data/raw/oqmd_subset.parquet`.  
  *Create* quantile bins on `formation_energy` (10 bins) → column `target_bin`.  
  *Perform* material‑ID‑aware stratified split (80/10/10) ensuring no `material_id` appears in more than one split.  
  *Write* three CSVs: `data/processed/raw_train.csv`, `data/processed/raw_val.csv`, `data/processed/raw_test.csv`.  
  *Verification*: Assert each CSV exists, contains `target_bin`, and that the bin distribution is approximately uniform (max‑min ≤ 1).  

- [ ] **T006c** **P** `code/data/preprocess.py` – *PCA fitting*  
  *Read* `data/processed/raw_train.csv`.  
  *Fit* `sklearn.decomposition.PCA` on all numeric feature columns (excluding target columns).  
  *Retain* exactly **20** components and ensure explained variance > 90 %.  
  *Save* the transformer to `data/processed/pca_transformer.pkl`.  
  *Verification*: Load the pickled object, compute `explained_variance_ratio_.sum()` and assert ≥ 0.90.  

- [ ] **T006d** **P** `code/data/preprocess.py` – *PCA transformation & exclusion*  
  *Load* `data/processed/pca_transformer.pkl`.  
  *Transform* train/val/test feature matrices, writing:  
  `data/processed/features_train_20pca.csv`,  
  `data/processed/features_val_20pca.csv`,  
  `data/processed/features_test_20pca.csv`.  
  *Exclude* rows with any missing critical features (as defined in `FR‑010`).  
  *Generate* `data/validation_report.json` conforming to `validation_report.schema.yaml` (fields: `excluded_count`, `missing_columns`, `total_raw_rows`, `remaining_rows`).  
  *Verification*: Validate JSON against the schema and assert `remaining_rows` > 0.  

### Contract definitions (already complete)  

- [ ] T009 **P** `specs/001‑assessing‑uncertainty‑quantification‑tec/contracts/` – create `dataset.schema.yaml`, `uq_prediction.schema.yaml`, `calibration_metric.schema.yaml`.  

---

## Phase 3 – User Story 1: Baseline model & three UQ methods (Priority P1)  

### Baseline neural network (heteroscedastic)  

- [ ] **T012** **US1** `code/models/baseline_nn.py`  
  *Define* a 2‑hidden‑layer feed‑forward network with ≤ 10 000 trainable parameters.  
  *Include* a heteroscedastic head that outputs both mean and log‑variance.  
  *Provide* helper `total_params()` that returns the parameter count and asserts `≤ 10000`.  
  *Save* the architecture (state‑dict skeleton) to `results/models/baseline_nn_arch.pt`.  
  *Verification*: After import, call `total_params()` and log the count to `logs/pipeline.log`.  

### Deep Ensemble  

- [ ] T013 **P** `code/models/deep_ensemble.py` – training loop for a single model (already verified).  

- [ ] **T013b** **US1** `code/models/deep_ensemble.py` – *Execute ensemble training*  
  *Run* the training loop from T013 for **5** independent seeds `[42, 43, 44, 45, 46]`.  
  *Save* each checkpoint to `results/models/ensemble/ensemble_seed_<seed>.pt`.  
  *Verification*: All five files exist, are non‑empty, and each `total_params()` ≤ 10 000 (checked by loading the state dict).  

### Monte‑Carlo Dropout  

- [ ] **T014a** **US1** `code/models/mc_dropout.py` – *Train MC‑Dropout model (seed 42)*  
  *Train* a baseline NN with dropout `p=0.2` using seed 42.  
  *Save* checkpoint to `results/models/mc_dropout/mc_dropout_seed_42.pt`.  

- [ ] **T014b** **US1** `code/models/mc_dropout.py` – *Train MC‑Dropout model (seed 43)* → `mc_dropout_seed_43.pt`.  

- [ ] **T014c** **US1** `code/models/mc_dropout.py` – *Train MC‑Dropout model (seed 44)* → `mc_dropout_seed_44.pt`.  

- [ ] **T014d** **US1** `code/models/mc_dropout.py` – *Inference for MC‑Dropout*  
  *For each seed (42‑44)* load the corresponding checkpoint, enable dropout during inference, and perform **30** stochastic forward passes on the **test set** (`features_test_20pca.csv`).  
  *Compute* mean prediction, variance, and 50 % / 90 % confidence bounds (Gaussian assumption).  
  *Write* three CSVs: `results/uq_predictions_mc_dropout_seed_42.csv`, `…_43.csv`, `…_44.csv`.  
  *Verification*: At least 90 % of rows have `variance > 0`; log a summary to `logs/mc_dropout_inference.log`.  

### Sparse Gaussian Process  

- [ ] **T015** **US1** `code/models/sparse_gp.py` – *Fit sparse GP*  
  *Load* PCA‑reduced training features (`features_train_20pca.csv`).  
  *Fit* a GPyTorch Sparse GP with **500** inducing points and an RBF kernel (CPU mode).  
  *Save* model to `results/models/sparse_gp_model.pt`.  
  *Compute* reconstruction variance for each test sample and store in `results/gp_reconstruction_variance.json`.  
  *Verification*: Assert the model file exists, size > 0, and that the JSON contains a single float per sample.  

### Unified single‑seed runner (orchestrates inference for all methods)  

- [ ] **T016a** **US1** `code/models/run_single_seed.py`  
  *Accept* a seed argument (`--seed`).  
  *Load* pre‑processed test features (`features_test_20pca.csv`).  
  *For the given seed* load:  
    • Baseline NN checkpoint (`baseline_nn_arch.pt` – same architecture, weights from ensemble training if seed ≤ 46).  
    • MC‑Dropout checkpoint `mc_dropout_seed_<seed>.pt`.  
    • If seed ∈ {42,43,44} also load the corresponding Deep‑Ensemble member `ensemble_seed_<seed>.pt`.  
  *Run* inference for each method, compute mean, variance, and confidence bounds (z=0.674 for 50 %, z=1.645 for 90 %).  
  *Write* a unified CSV `results/uq_predictions_seed_<seed>.csv` with columns (ordered): `material_id`, `method`, `prediction`, `lower_bound_50`, `upper_bound_50`, `lower_bound_90`, `upper_bound_90`, `variance`, `aleatoric_variance`, `epistemic_variance`, `uncertainty_type`.  
  *Verification*: File exists, row count matches test set, and schema conforms to `prediction_output.schema.yaml`.  

### Timeout enforcement (already complete)  

- [ ] T016c **P** `code/utils/timeout.py` – context manager `Timeout(seconds)` reading `timeout_hours` from config.  

### Orchestrator (already complete)  

- [ ] T016b **P** `code/main.py` – chains download, preprocess, training, and inference; uses `Timeout` to enforce the 5‑hour wall‑clock budget.  

---

## Phase 4 – User Story 2: Calibration & reliability evaluation (Priority P2)  

### Metric implementation  

- [ ] T021 **P** `code/uq/metrics.py` – implements ECE (quantile binning), Interval Score (Winkler), and Sharpness.  

### Decomposition of uncertainty  

- [ ] T022 **US2** `code/uq/metrics.py` – adds functions to compute aleatoric vs. epistemic variance for Deep Ensembles and MC‑Dropout; returns `uncertainty_type` per row.  

### Aggregation of seed predictions  

- [ ] T025a **P** `code/run_seeds.py` – iterates over `robustness_seeds`, calls `run_single_seed.py`, aggregates CSVs into `results/uq_predictions_aggregated.csv`.  

### Calibration report  

- [ ] **T024** **US2** `code/uq/metrics.py` – *Compute final calibration metrics*  
  *Read* `results/uq_predictions_aggregated.csv`.  
  *For each method* (`ensemble`, `mc_dropout`, `sparse_gp`) compute:  
    • ECE for 50 % and 90 % intervals,  
    • Interval Score (α = 0.5 for 50 %, α = 0.1 for 90 %).  
    • Sharpness (mean interval width).  
    • Coverage percentage (empirical).  
    • Coefficient of variation of ECE across seeds (CV).  
  *Write* `results/metrics/calibration_summary.csv` (columns match `calibration_metric.schema.yaml`).  
  *Verification*: Validate CSV against the schema and assert `ece_cv` ≤ `robustness_cv_threshold` for at least one method; log results.  

### Robustness gate (already complete)  

- [ ] T025c **US2** `results/robustness_report.json` – CV calculation and pass/fail flag (already verified).  

### Reliability diagrams  

- [ ] T023 **US2** `results/reliability_diagrams/` – generate PDF/PNG diagrams per method (already verified).  

### Ranking of methods  

- [ ] T025 **US2** `code/uq/ranking.py` – selects best‑performing method based on lowest ECE (ties broken by interval score).  

---

## Phase 5 – User Story 3: Downstream screening case study (Priority P3)  

### Screening threshold calculation  

- [ ] **T028a** **US3** `code/uq/screening.py` – *Compute formation‑energy threshold* that yields the `screening_recall_target` (default 0.8) on the test set.  
  *Output*: `results/screening_threshold.json` (`{"recall_target": float, "threshold_value": float}`) conforming to `validation_report.schema.yaml`.  
  *Verification*: Raise `ValueError` if the key is missing; assert threshold is finite and between min/max of test energies.  

### Baseline (point‑prediction) screening  

- [ ] **T028b** **US3** `code/uq/screening.py` – *Point‑prediction baseline*  
  *Rank* candidates by mean prediction, select top‑N to meet the recall target using the threshold from T028a.  
  *Write* `results/screening_baseline.csv` (columns: `material_id`, `prediction`, `selected`).  

### Random selection baseline  

- [ ] **T028c** **US3** `code/uq/screening.py` – *Random baseline*  
  *Shuffle* the test set, select the same number of candidates as the point‑prediction baseline, and write `results/screening_random.csv`.  

### UQ‑enhanced candidate filtering  

- [ ] **T028d** **US3** `code/uq/screening.py` – *Narrow‑confidence filtering*  
  *Compute* confidence‑interval width (`upper_90 - lower_90`) for each test sample from `results/uq_predictions_decomposed.csv`.  
  *Define* a width percentile cutoff (default 10 th percentile, configurable via `screening_confidence_percentile` in `config.yaml`).  
  *Select* candidates whose width ≤ cutoff **and** whose predicted property meets the threshold from T028a.  
  *Write* `results/screening_candidates.csv`.  

### Fallback handling for missing GP predictions  

- [ ] **T028e** **US3** `code/uq/screening.py` – *GP fallback*  
  *If* `sparse_gp` predictions are absent or fail to load, re‑run the ranking and filtering using only `ensemble` and `mc_dropout`.  
  *Log* a warning and produce `results/screening_final_candidates.csv`.  

### Precision/recall evaluation  

- [ ] T029 **US3** `code/uq/evaluation.py` – *Generate binary decision matrix* (`results/selection_decisions.csv`) containing flags `selected_uq`, `selected_baseline`, `selected_random` for every test material.  

### Statistical significance (bootstrap)  

- [ ] **T029b** **US3** `code/uq/evaluation.py` – *Bootstrap CI*  
  *Bootstrap* the binary decision matrix (10 000 resamples) to estimate the distribution of precision gain of the UQ method over the random baseline.  
  *Output*: `results/screening_significance.json` (`{"p_value": float, "test_statistic": float, "method": "Bootstrap CI"}`).  
  *Success criterion*: `p_value < 0.05` **or** precision gain ≥ `screening_precision_gain_threshold`.  

### Final screening report  

- [ ] **T030** **US3** `code/uq/evaluation.py` – *Compile final CSV* `results/screening_results.csv` summarising recall, precision, p‑value, and whether the utility threshold was met.  

---

## Phase 6 – Polishing & cross‑cutting concerns  

| ID | Status | Description |
|----|--------|-------------|
| - [X] T033a **P** | Update `README.md` with overview & usage. |
| - [ ] T033b **P** | Add API examples for `screening.py` in `docs/api.md`. |
| - [X] T034a **P** | Run `ruff` lint checks. |
| - [X] T034b **P** | Run `black` formatting. |
| - [X] T035 **P** | Verify all `results/` artefacts against their contract schemas (already executed). |
| - [X] T036 **P** | Execute unit & contract test suites (`tests/unit/`, `tests/contract/`). |
| - [X] T037 **P** | Implement `code/utils/runtime_logger.py` to write `results/runtime_report.json` (wall‑clock time). |

---

## Phase 7 – Reviewer‑driven robustness enhancements  

| ID | Status | Description |
|----|--------|-------------|
| - [ ] T039 **P** | Add streaming support to `download.py` & `preprocess.py` when `config.yaml` sets `streaming: true`. |
| - [ ] T040 **US2** | GP convergence fallback: reduce inducing points to 200, then log warning if still failing. |
| - [ ] T041 **US2** | Ensure CV calculation in `run_seeds.py` uses *actual* ECE scores; log seed success count. |
| - [ ] T042 **US3** | Validate `screening_threshold.json` values are finite; abort screening with clear error if not. |

---

### Execution order (high‑level)

1. **Phase 1 → Phase 2** (foundational tasks must finish before any user story).  
2. **Phase 3** (US1) can start once `T006a‑d` are complete (they produce the processed feature files).  
3. **Phase 4** (US2) runs after US1 artefacts (`*_predictions_*.csv`) are available.  
4. **Phase 5** (US3) runs after calibration outputs and the decomposed prediction file (`results/uq_predictions_decomposed.csv`) exist.  
5. **Phase 6** polishing can be performed anytime after the corresponding phases are successful.  
6. **Phase 7** addresses reviewer concerns and may be interleaved with any phase that touches the affected component.  

---  

*All tasks are expressed as executable checklist items; each unchecked item represents work that still needs to be performed to satisfy the specification and pass the independent verifier.*
