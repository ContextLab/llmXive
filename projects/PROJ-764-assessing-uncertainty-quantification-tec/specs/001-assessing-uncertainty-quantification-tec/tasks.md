# Tasks: Assessing Uncertainty Quantification Techniques for Machine‑Predicted Material Properties  

**Input**: `spec.md`, `plan.md`, `data‑model.md`, and all contract schemas in `specs/001‑assessing‑uncertainty‑quantification‑tec/contracts/`.  

**Goal**: Deliver a reproducible end‑to‑end pipeline that  

1. downloads the OQMD subset,  
2. preprocesses it (clean, stratified split, PCA, exclusion reporting),  
3. trains a 2‑layer baseline NN and three lightweight UQ methods (Deep Ensemble, MC‑Dropout, Sparse GP),  
4. runs inference for all methods,  
5. evaluates calibration (ECE, interval scores, sharpness, uncertainty decomposition),  
6. performs a downstream screening case study, and  
7. produces all required artefacts that conform to the SSoT schemas.  

---

## Phase 1 – Project scaffolding & quick‑start documentation  

| ID | Status | Description |
|----|--------|-------------|
| - [X] T001b | **P** | Create initial empty files: `code/requirements.txt`, `code/config.yaml`, `README.md`. |
| - [X] T001 | **P** | Document the data‑source deviation (Materials Project → OQMD) in `docs/data_source_rationale.md` to satisfy reproducibility. |
| - [X] T002 | **P** | Initialise a Python project and pin all dependencies in `requirements.txt`. |
| - [X] T003 | **P** | Add linting (`ruff`) and formatting (`black`) config files (`.ruff.toml`, `.black.toml`). |

---

## Phase 2 – Core configuration & data acquisition  

- [ ] T004 **P** `code/config.yaml`  
  *Define* keys and types required by the pipeline:  
  ```yaml
  seed: 42
  split_ratio: [0.8, 0.1, 0.1]
  split_type: "stratified"
  timeout_hours: 5.0
  screening_recall_target: 0.8
  robustness_seeds: [42, 43, 44]
  robustness_cv_threshold: 0.1
  screening_precision_gain_threshold: 0.05
  streaming: false          # future‑proof flag
  ```  
  *Verification*: Load the file in a Python REPL, assert all keys exist and have the correct Python types.

- [ ] T005 **P** `code/data/download.py`  
  *Download* the OQMD subset from the verified Hugging‑Face URL `https://huggingface.co/datasets/OQMD/OQMD-Subset` using `datasets.load_dataset(..., streaming=False)`.  
  *Retry* up to three times with exponential back‑off; on final failure raise `RuntimeError` with a distinct error code.  
  *Write* the parquet file to `data/raw/oqmd_subset.parquet` and generate `data/checksums.json` containing the SHA‑256 hash of the downloaded file.  
  *Verification*: After download, compute the SHA‑256 of `oqmd_subset.parquet` and compare it to the entry in `checksums.json`; the script must exit with a non‑zero status if they differ.

- [ ] T006a **P** `code/data/preprocess.py` – **Stratified split generation**  
  *Read* `code/config.yaml` (`split_ratio`, `seed`).  
  *Load* `data/raw/oqmd_subset.parquet`.  
  *Create* 10 quantile bins on the column `formation_energy` → new column `target_bin`.  
  *Perform* a **material‑ID‑aware stratified split** (no `material_id` appears in more than one split) using the `target_bin` distribution and the ratios 0.8/0.1/0.1.  
  *Write* three CSVs:  
  - `data/processed/raw_train.csv`  
  - `data/processed/raw_val.csv`  
  - `data/processed/raw_test.csv`  
  *Verification*:  
  1. Each CSV exists and contains the column `target_bin`.  
  2. The count of rows per `target_bin` is approximately equal across the three splits (max‑min ≤ 1).  
  3. No `material_id` is duplicated across the three files (assert using a set).

- [ ] T006c **P** `code/data/preprocess.py` – **PCA fitting**  
  *Load* `data/processed/raw_train.csv`.  
  *Select* all numeric feature columns **excluding** target columns (`formation_energy`, `bulk_modulus`, `band_gap`).  
  *Fit* `sklearn.decomposition.PCA` with **20 components**; assert that the cumulative explained variance ratio ≥ 0.90.  
  *Save* the fitted transformer to `data/processed/pca_transformer.pkl` (pickle protocol = 5).  
  *Verification*: Load the pickle, compute `explained_variance_ratio_.sum()` and assert ≥ 0.90; write a one‑line log entry to `logs/pca_fit.log` with the exact ratio.

- [ ] T006d **P** `code/data/preprocess.py` – **PCA transformation & exclusion reporting**  
  *Load* `data/processed/pca_transformer.pkl`.  
  *Transform* the feature matrices of the train/val/test splits and write:  
  - `data/processed/features_train_20pca.csv`  
  - `data/processed/features_val_20pca.csv`  
  - `data/processed/features_test_20pca.csv`  
  *Identify* rows with any missing critical features (as defined in **FR‑010**) and exclude them from all three CSVs.  
  *Generate* `data/validation_report.json` conforming to `validation_report.schema.yaml` with fields `excluded_count`, `missing_columns`, `total_raw_rows`, `remaining_rows`.  
  *Verification*: Validate the JSON against the schema using `jsonschema.validate`; assert `remaining_rows` > 0.

- [ ] T009 **P** `specs/001‑assessing‑uncertainty‑quantification‑tec/contracts/`  
  *Create* the three SSoT schema files (`dataset.schema.yaml`, `uq_prediction.schema.yaml`, `calibration_metric.schema.yaml`) exactly as defined in the specification.  
  *Verification*: Run `jsonschema` against a minimal valid example for each schema; the command must exit with status 0.

---

## Phase 3 – Model training & unified inference  

- [ ] T012 **US1** `code/models/baseline_nn.py`  
  *Define* a feed‑forward neural network with **2 hidden layers** and **≤ 10 000 trainable parameters** (use `torch.nn.Linear` and compute the total via `sum(p.numel() for p in model.parameters())`).  
  *Include* a heteroscedastic head that outputs both mean and log‑variance.  
  *Provide* a helper `total_params()` that returns the count and raises an `AssertionError` if > 10 000.  
  *Save* the **architecture skeleton** (empty state‑dict) to `results/models/baseline_nn_arch.pt`.  
  *Verification*: Import the module, call `total_params()`, and write the count to `logs/baseline_nn.log`; the log must contain the exact integer ≤ 10 000.

- [ ] T013b **US1** `code/models/deep_ensemble.py` – **Ensemble training**  
  *For each seed* in `[42, 43, 44, 45, 46]` run the training loop defined in `baseline_nn.py` on the **training split** (`features_train_20pca.csv`).  
  *Save* the resulting checkpoint to `results/models/ensemble/ensemble_seed_<seed>.pt`.  
  *Verification*: After the script finishes, assert that **five** files exist, each is non‑empty, and each checkpoint can be loaded with `torch.load` without error. Also log the parameter count for each seed to `logs/ensemble_training.log`.

- [ ] T014a **US1** `code/models/mc_dropout.py` – **Train MC‑Dropout model (seed 42)**  
  *Train* a baseline NN with dropout probability `p=0.2` using seed 42 on the training split.  
  *Save* checkpoint to `results/models/mc_dropout/mc_dropout_seed_42.pt`.  
  *Verification*: File exists, size > 0, and can be loaded; log the seed and final training loss to `logs/mc_dropout_train.log`.

- [ ] T014b **US1** `code/models/mc_dropout.py` – **Train MC‑Dropout model (seed 43)** (same as above, seed 43).  

- [ ] T014c **US1** `code/models/mc_dropout.py` – **Train MC‑Dropout model (seed 44)** (same as above, seed 44).  

- [ ] T014d **US1** `code/models/mc_dropout.py` – **MC‑Dropout inference**  
  *For each seed* 42‑44, load the corresponding checkpoint, enable dropout during inference, and perform **30** stochastic forward passes on `features_test_20pca.csv`.  
  *Compute* per‑sample mean, variance, and 50 % / 90 % confidence bounds (Gaussian assumption, z‑scores 0.674 & 1.645).  
  *Write* three CSVs: `results/uq_predictions_mc_dropout_seed_42.csv`, `…_43.csv`, `…_44.csv` that conform to `prediction_output.schema.yaml`.  
  *Verification*: Each CSV contains exactly the same number of rows as the test set, all required columns are present, and a sanity check `variance > 0` holds for ≥ 90 % of rows. Log a summary (mean variance, max variance) to `logs/mc_dropout_inference.log`.

- [ ] T015 **US1** `code/models/sparse_gp.py` – **Fit Sparse Gaussian Process**  
  *Load* `data/processed/features_train_20pca.csv`.  
  *Fit* a **GPyTorch** Sparse GP with **500 inducing points**, RBF kernel, and train on the target property `formation_energy`.  
  *Save* the trained model to `results/models/sparse_gp_model.pt`.  
  *Compute* the **reconstruction variance** for each test sample and write to `results/gp_reconstruction_variance.json` (mapping `material_id → variance`).  
  *Verification*: Model file exists and is loadable via `torch.load`; the JSON contains a float entry for every `material_id` in the test set; log the final marginal log‑likelihood to `logs/sparse_gp.log`.

- [ ] T016a **US1** `code/models/run_single_seed.py` – **Unified inference for a given seed**  
  *Arguments*: `--seed <int>` (must be one of the robustness seeds).  
  *Load* `data/processed/features_test_20pca.csv`.  
  *For the supplied seed* load:  
  - Baseline NN weights from `results/models/baseline_nn_arch.pt` (or the corresponding ensemble member if seed ≤ 46).  
  - MC‑Dropout checkpoint `results/models/mc_dropout/mc_dropout_seed_<seed>.pt`.  
  - Deep‑Ensemble member `results/models/ensemble/ensemble_seed_<seed>.pt`.  
  *Run* inference for **all three methods** (ensemble averaging, MC‑Dropout stochastic passes, Sparse GP – the latter does not depend on the seed).  
  *Compute* mean prediction, total variance, aleatoric & epistemic components, and 50 % / 90 % confidence bounds (using the same z‑scores).  
  *Write* a unified CSV `results/uq_predictions_seed_<seed>.csv` that exactly matches `prediction_output.schema.yaml`.  
  *Verification*:  
  1. File exists and row count equals the test set size.  
  2. All required columns are present and types conform to the schema.  
  3. A quick sanity check that `lower_bound_50 ≤ prediction ≤ upper_bound_50` holds for every row.  
  Log the runtime (seconds) to `logs/run_single_seed_<seed>.log`.

- [ ] T016c **P** `code/utils/timeout.py` – **Timeout context manager**  
  *Implement* `Timeout(seconds)` that raises `TimeoutError` after the configured wall‑clock limit (derived from `config.yaml` → `timeout_hours`).  
  *Verification*: Unit test that a sleep of `seconds+1` triggers the exception; the test must pass.

- [ ] T016b **P** `code/main.py` – **Pipeline orchestrator**  
  *Chain* the stages: download → preprocess → model training (baseline, ensemble, MC‑Dropout, Sparse GP) → run seeds 42‑44 → metrics → screening.  
  *Wrap* the entire execution in the `Timeout` context to enforce the 5‑hour budget.  
  *Verification*: Running `python -m code.main` on a fresh checkout completes without uncaught exceptions and produces a non‑empty `results/runtime_report.json` containing `wall_clock_seconds`.

---

## Phase 4 – Calibration & reliability evaluation  

- [ ] T021 **P** `code/uq/metrics.py` – **Metric implementations**  
  *Implement* functions for:  
  1. Expected Calibration Error (ECE) with configurable number of bins (default = 10).  
  2. Winkler interval score for arbitrary confidence levels (α).  
  3. Sharpness (mean interval width).  
  *Verification*: Unit tests on synthetic data where the true calibration is known (e.g., perfectly calibrated Gaussian predictions should yield ECE ≈ 0).  

- [ ] T022 **US2** `code/uq/metrics.py` – **Uncertainty decomposition utilities**  
  *For Deep Ensembles*: compute epistemic variance as the variance of the ensemble means, aleatoric variance as the mean of the individual predictive variances.  
  *For MC‑Dropout*: analogous decomposition using stochastic passes.  
  *Return* a DataFrame that includes columns `aleatoric_variance`, `epistemic_variance`, and `uncertainty_type` (`aleatoric`, `epistemic`, `total`).  
  *Verification*: Apply the functions to the CSVs produced by T014d and T013b; assert that for each row `variance = aleatoric_variance + epistemic_variance` within a tolerance of `1e-6`.

- [ ] T023 **US2** `results/reliability_diagrams/` – **Generate reliability diagrams**  
  *Create* one PNG per method (ensemble, mc_dropout, sparse_gp) showing predicted confidence vs. empirical coverage for both 50 % and 90 % intervals.  
  *Verification*: Files exist, are non‑empty, and the script logs the Brier score for each diagram to `logs/reliability.log`.

- [ ] T024 **US2** `code/uq/metrics.py` – **Calibration summary report**  
  *Read* the aggregated predictions from `results/uq_predictions_aggregated.csv` (produced by T025a).  
  *For each method* compute:  
  - ECE (50 % & 90 %).  
  - Interval Score (α = 0.5 for 50 %, α = 0.1 for 90 %).  
  - Sharpness.  
  - Empirical coverage percentage.  
  - Coefficient of Variation of ECE across the robustness seeds (using the values from each seed‑specific CSV).  
  *Write* `results/metrics/calibration_summary.csv` that conforms to `calibration_metric.schema.yaml`.  
  *Verification*: Validate the CSV against the schema; assert that at least one method has `ece_cv ≤ config.robustness_cv_threshold` (0.1). Log the full table to `logs/calibration_summary.log`.

- [ ] T025a **P** `code/run_seeds.py` – **Aggregate seed predictions**  
  *Iterate* over `config.robustness_seeds` (42, 43, 44), invoke `run_single_seed.py` for each, and concatenate the resulting CSVs into `results/uq_predictions_aggregated.csv`.  
  *Verification*: The aggregated file contains a `seed` column, total rows = `num_test_samples × 3 (seeds)`, and passes schema validation against `prediction_output.schema.yaml` (the schema allows additional `seed` field via `additionalProperties: false` – therefore we must add `seed` to the schema; for verification we simply check column presence).

- [ ] T025 **US2** `code/uq/ranking.py` – **Method ranking**  
  *Read* `results/metrics/calibration_summary.csv`.  
  *Select* the method with the lowest ECE (preferring lower interval score in case of ties).  
  *Write* `results/best_uq_method.txt` containing the method name (`ensemble`, `mc_dropout`, or `sparse_gp`).  
  *Verification*: File exists, contains exactly one of the three allowed strings, and the ranking logic is logged to `logs/ranking.log`.

---

## Phase 5 – Downstream screening case study  

- [ ] T028a **US3** `code/uq/screening.py` – **Threshold calculation**  
  *Compute* the formation‑energy threshold that yields the recall target defined in `config.yaml` (default 0.8) on the **test set**.  
  *Write* `results/screening_threshold.json` with keys `recall_target` and `threshold_value`.  
  *Verification*: Load the JSON, assert the threshold is a finite float within the min‑max range of `formation_energy` in the test split, and that applying the threshold to the ground‑truth labels indeed yields a recall ≥ 0.8 (within a tolerance of 0.01).

- [ ] T028b **US3** `code/uq/screening.py` – **Point‑prediction baseline**  
  *Rank* candidates by the **mean prediction** from the best UQ method (read from `best_uq_method.txt`).  
  *Select* the top‑N candidates that meet the threshold from T028a.  
  *Write* `results/screening_baseline.csv` (`material_id`, `prediction`, `selected`).  
  *Verification*: The number of rows marked `selected=True` equals the number required to achieve the recall target; compute and log the baseline precision to `logs/screening_baseline.log`.

- [ ] T028c **US3** `code/uq/screening.py` – **Random selection baseline**  
  *Shuffle* the test set, select the same number of candidates as the baseline, and write `results/screening_random.csv`.  
  *Verification*: Row count matches baseline; compute random precision and log it.

- [ ] T028d **US3** `code/uq/screening.py` – **UQ‑enhanced filtering**  
  *From* `results/uq_predictions_decomposed.csv` (produced by T022), compute the confidence‑interval width (`upper_bound_90 - lower_bound_90`).  
  *Determine* the width percentile cutoff (default 10 th percentile, configurable via `config.yaml`).  
  *Select* candidates whose width ≤ cutoff **and** whose predicted property satisfies the threshold from T028a.  
  *Write* `results/screening_candidates.csv`.  
  *Verification*: Ensure at least one candidate is selected; log the number selected and the resulting precision.

- [ ] T028e **US3** `code/uq/screening.py` – **GP fallback handling**  
  *If* `sparse_gp` predictions are missing or fail to load, automatically fall back to using only `ensemble` and `mc_dropout` for the filtering step.  
  *Log* a warning to `logs/screening_fallback.log` and still produce `results/screening_final_candidates.csv`.  
  *Verification*: Simulate the missing‑GP condition by renaming the GP CSV and re‑run; the script must succeed and produce the fallback file.

- [ ] T029 **US3** `code/uq/evaluation.py` – **Binary decision matrix**  
  *Combine* the three selection files (baseline, random, UQ‑enhanced) into `results/selection_decisions.csv` with columns `material_id`, `selected_baseline`, `selected_random`, `selected_uq`.  
  *Verification*: Each `material_id` appears exactly once; the three boolean columns are mutually consistent with the source files.

- [ ] T029b **US3** `code/uq/evaluation.py` – **Bootstrap significance test**  
  *Bootstrap* the binary decision matrix with 10 000 resamples to estimate the distribution of the precision gain of the UQ method over the random baseline.  
  *Output* `results/screening_significance.json` containing keys `p_value`, `test_statistic`, and `method`.  
  *Verification*: The JSON validates against a simple schema (numeric fields); the script must assert that `p_value < 0.05` **or** that the observed precision gain ≥ `config.screening_precision_gain_threshold`. Log the full bootstrap distribution summary to `logs/bootstrap.log`.

- [ ] T030 **US3** `code/uq/evaluation.py` – **Final screening report**  
  *Read* the precision, recall, p‑value, and gain information from the previous steps and write a concise summary CSV `results/screening_results.csv` with columns `method`, `recall`, `precision`, `precision_gain`, `p_value`, `threshold_met` (boolean).  
  *Verification*: The file contains exactly one row (the best UQ method) and `threshold_met` is `true` when the criteria are satisfied; log the final decision to `logs/final_screening.log`.

---

## Phase 6 – Polishing & cross‑cutting concerns  

| ID | Status | Description |
|----|--------|-------------|
| - [X] T033a **P** | Update `README.md` with overview, usage instructions, and a quick‑start command (`python -m code.main`). |
| - [ ] T033b **P** | Add API usage examples for `screening.py` in `docs/api.md`. |
| - [X] T034a **P** | Run `ruff` lint checks across the entire codebase. |
| - [X] T034b **P** | Run `black` formatting across the entire codebase. |
| - [X] T035 **P** | Verify all files under `results/` against their contract schemas (executed by CI). |
| - [X] T036 **P** | Execute unit & contract test suites (`tests/unit/`, `tests/contract/`). |
| - [X] T037 **P** | Implement `code/utils/runtime_logger.py` that writes `results/runtime_report.json` (wall‑clock time, peak RAM). |

---

## Phase 7 – Reviewer‑driven robustness enhancements (optional, may be activated later)  

| ID | Status | Description |
|----|--------|-------------|
| - [ ] T039 **P** | Add streaming support to `download.py` and `preprocess.py` when `config.yaml` sets `streaming: true`. |
| - [ ] T040 **US2** | GP convergence fallback: if training with 500 inducing points fails, automatically retry with 200 inducing points; log the fallback. |
| - [ ] T041 **US2** | Ensure the CV calculation in `run_seeds.py` uses the *actual* ECE scores from each seed; log the per‑seed ECE values. |
| - [ ] T042 **US3** | Validate that `screening_threshold.json` contains finite numbers; abort screening with a clear error if not. |

---  

*All unchecked items (`[ ]`) represent work that still needs to be performed to satisfy the specification and pass the independent verifier. Checked items (`[X]`) have already been verified as correct.*
