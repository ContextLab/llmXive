# Tasks: Assessing Uncertainty Quantification Techniques for Machine-Predicted Material Properties

**Input**: `spec.md`, `plan.md`, `data-model.md`, and all contract schemas in `specs/001-assessing-uncertainty-quantification-tec/contracts/`.

**Goal**: Deliver a reproducible end-to-end pipeline that (1) downloads the real OQMD subset, (2) preprocesses it (clean, Material-ID-stratified split, PCA, exclusion reporting), (3) trains a 2-layer baseline NN and three lightweight UQ methods (Deep Ensemble, MC-Dropout, Sparse GP), (4) runs inference for all methods, (5) evaluates calibration (ECE, interval scores, sharpness, aleatoric/epistemic decomposition, seed robustness), (6) performs the downstream screening case study, and (7) produces all required artifacts conforming to the SSoT schemas.

**Preserved verified work**: project scaffolding (`code/requirements.txt`, `code/config.yaml`, `README.md`, lint/format configs), `code/utils/runtime_logger.py`, lint/format runs, and contract-schema CI validation (former T001–T003, T009, T033a, T034a/b, T035–T037) are complete and are NOT re-tasked. All previously rejected tasks are folded into the consolidated tasks below and reopened.

---

## Phase 1: Setup and first end-to-end analysis

- [ ] T001 [US1] Download and preprocess the real OQMD subset, producing the split and PCA artifacts (`code/data/download.py`, `code/data/preprocess.py`, `code/data/validation.py`)
  *Download* the OQMD subset from the Hugging Face dataset URL named in the spec using `datasets.load_dataset(..., streaming=False)` (or `huggingface_hub` file download if the dataset is not `load_dataset`-addressable). *Retry* up to 3 times with exponential backoff; on final failure RAISE `RuntimeError` with a distinct error code — NEVER fall back to synthetic, mock, or randomly generated data (edge case: corrupted download must fail loudly). *Write* the raw data to `data/raw/oqmd_subset.parquet` and `data/checksums.json` with its SHA-256 hash; the script must exit non-zero if the recomputed hash differs.
  *Preprocess* (`code/data/preprocess.py`): load the raw parquet; create 10 quantile bins on `formation_energy` (column `target_bin`); perform a **material-ID-aware stratified 80/10/10 split** (ratios and `seed=42` from `code/config.yaml`) so no `material_id` appears in more than one split; write `data/processed/raw_train.csv`, `raw_val.csv`, `raw_test.csv`. Then fit `sklearn.decomposition.PCA` (20 components) on the TRAINING features only (excluding targets `formation_energy`, `bulk_modulus`, `band_gap`), assert cumulative explained variance ≥ 0.90, save to `data/processed/pca_transformer.pkl` (pickle protocol 5), and write transformed features to `data/processed/features_train_20pca.csv`, `features_val_20pca.csv`, `features_test_20pca.csv`.
  *Exclusion handling* (FR-010): exclude rows with missing critical features (targets or required descriptors) from all splits; write `data/validation_report.json` conforming to `validation_report.schema.yaml` (`excluded_count`, `missing_columns`, `total_raw_rows`, `remaining_rows`).
  *Verification*: (a) the three split CSVs exist, contain `target_bin`, with per-bin row counts approximately equal across splits and zero `material_id` overlap between splits (set assertion); (b) `pca_transformer.pkl` loads and `explained_variance_ratio_.sum() ≥ 0.90`; (c) `validation_report.json` validates against its schema with `remaining_rows > 0`; (d) SHA-256 of the raw file matches `checksums.json`. Bundle focused pytest unit tests in `code/tests/` covering the split-leakage and hash checks.

- [ ] T002 [US1] Implement the baseline heteroscedastic NN and the three UQ methods with correctness tests (`code/models/baseline_nn.py`, `code/models/deep_ensemble.py`, `code/models/mc_dropout.py`, `code/models/sparse_gp.py`)
  *Define* in `baseline_nn.py` a feed-forward network with exactly 2 hidden layers and ≤ 10,000 trainable parameters (`sum(p.numel() for p in model.parameters())`), with a heteroscedastic head outputting mean and log-variance; provide `total_params()` that raises `AssertionError` if the count exceeds 10,000; save the architecture skeleton to `results/models/baseline_nn_arch.pt` (FR-002).
  *Implement* Deep Ensemble training (FR-003): train 5 independently initialized copies (seeds 42–46) on `data/processed/features_train_20pca.csv`, saving `results/models/ensemble/ensemble_seed_<seed>.pt`.
  *Implement* MC-Dropout (FR-004): train baseline-architecture models with dropout p=0.2 for seeds 42, 43, 44, saving `results/models/mc_dropout/mc_dropout_seed_<seed>.pt`; inference performs 30 stochastic forward passes per test sample.
  *Implement* the Sparse GP (FR-005): fit a GPyTorch variational/sparse GP with 500 inducing points and an RBF kernel on the PCA-reduced training features, target `formation_energy`; if optimization fails to converge, retry with 200 inducing points (log the fallback); if that also fails, log a warning and mark the run "partial" for the GP method only — never fabricate GP outputs. Save `results/models/sparse_gp_model.pt`.
  *Verification*: unit tests assert the parameter count ≤ 10,000 and the 2-hidden-layer structure from the state dict; all five ensemble checkpoints and three MC-Dropout checkpoints exist, are non-empty, and load via `torch.load`; the GP model file loads; parameter counts and final losses are logged to `logs/` per model. All training runs on CPU (`device="cpu"`); total ensemble+GP training must stay within the runtime budget.

- [ ] T003 [US1] Run unified UQ inference on the held-out test set and produce schema-conformant prediction CSVs (`code/models/run_single_seed.py`)
  *For each robustness seed* (42, 43, 44): load the test features `data/processed/features_test_20pca.csv`; run (a) ensemble inference over the 5 members, (b) MC-Dropout with 30 stochastic passes using the seed's checkpoint, and (c) Sparse GP inference (seed-independent, run once and reused). *Compute* per sample: point prediction, total variance, aleatoric and epistemic components (FR-008: for NN methods, epistemic = variance of member means, aleatoric = mean of member variances; for the GP, report total variance as proxy with `uncertainty_type='total'`), and 50%/90% Gaussian bounds (z = 0.674 and 1.645). For the Sparse GP, also compute reconstruction variance per test sample (FR-005) and write `results/gp_reconstruction_variance.json` mapping `material_id → variance`.
  *Write* `results/uq_predictions_seed_<seed>.csv` (and per-method files `results/predictions/uq_predictions_ensemble.csv`, `uq_predictions_mc_dropout.csv`, `uq_predictions_sparse_gp.csv`) conforming exactly to `prediction_output.schema.yaml` (columns `material_id`, `method`, `prediction`, `lower_bound_50`, `upper_bound_50`, `lower_bound_90`, `upper_bound_90`, `variance`, `aleatoric_variance`, `epistemic_variance`, `uncertainty_type`, plus `reconstruction_variance` for GP rows).
  *Verification*: row counts equal the test-set size for every method; schema validation passes; `lower_bound_50 ≤ prediction ≤ upper_bound_50` for every row; `variance > 0` for ≥ 90% of rows; for NN methods `variance ≈ aleatoric_variance + epistemic_variance` within 1e-6. This is the first end-to-end executable result: the documented command produces real prediction rows from real downloaded data.

## Phase 2: Complete the study and validate its evidence

- [ ] T004 [US2] Implement and unit-test the calibration metrics (`code/eval/metrics.py`)
  *Implement*: Expected Calibration Error (ECE, 10 bins, binned by predicted total uncertainty), Winkler interval score for arbitrary α (α = 0.5 for 50% intervals, α = 0.1 for 90% intervals), sharpness (mean interval width), and empirical coverage percentage (FR-006). Also implement the aleatoric/epistemic decomposition utilities returning `aleatoric_variance`, `epistemic_variance`, `uncertainty_type` columns.
  *Verification*: focused pytest unit tests on constructed cases with known ground truth — a perfectly calibrated Gaussian predictive distribution must yield ECE ≈ 0 and empirical coverage ≈ nominal; a deliberately over-dispersed one must yield coverage above nominal; decomposition must satisfy variance additivity within 1e-6. No synthetic data enters the research results; these are pure-function correctness tests only.

- [ ] T005 [US2] Compute the full calibration evaluation, reliability diagrams, seed robustness, and method ranking (`code/eval/metrics.py`, `code/eval/ranking.py`, `code/run_seeds.py`)
  *Aggregate* the per-seed prediction CSVs (42, 43, 44) into `results/uq_predictions_aggregated.csv` (with a `seed` column). *For each method and each confidence level* (0.5, 0.9): compute ECE, Winkler interval score, sharpness, and coverage from the REAL predictions and ground-truth test targets. *Compute* the coefficient of variation (CV) of ECE across the three seeds (SC-004); flag instability if CV > 0.1.
  *Write* `results/metrics/calibration_summary.csv` conforming to `calibration_metric.schema.yaml` (`method`, `confidence_level`, `ece_score`, `interval_score`, `sharpness`, `coverage_percentage`, `ece_cv`), and generate one reliability-diagram PNG per method (50% and 90% curves) under `results/reliability_diagrams/`.
  *Rank* methods by lowest ECE (interval score as tie-breaker) and write `results/best_uq_method.txt` containing exactly one of `ensemble`, `mc_dropout`, `sparse_gp`.
  *Verification*: the summary CSV validates against the schema; per-seed ECE values are logged; reliability PNGs exist and are non-empty; the ranking file contains one allowed method name; the full pipeline stage (training + evaluation) stays within the 5-hour wall-clock budget enforced by the orchestrator (T008).

- [ ] T006 [US3] Run the downstream screening case study comparing UQ-filtered selection against baselines (`code/eval/screening.py`, `code/eval/evaluation.py`)
  *Define* stability via the formation-energy threshold on the test set that achieves the recall target (0.8 from `code/config.yaml`); write `results/screening_threshold.json` (`recall_target`, `threshold_value`) and assert the threshold is finite and within the test-set formation-energy range.
  *Produce three selections of equal size*: (a) point-prediction baseline ranked by mean prediction from the best UQ method (`results/screening_baseline.csv`); (b) random selection with a fixed seed (`results/screening_random.csv`); (c) UQ-enhanced filtering — select candidates whose 90% interval width is ≤ the 10th-percentile width cutoff AND whose prediction meets the threshold, dynamically adjusting the width cutoff to retain the recall target (`results/screening_candidates.csv`). If Sparse GP predictions are missing/failed (partial run), fall back to ensemble + MC-Dropout only and log the fallback — never fabricate GP rows.
  *Evaluate*: combine selections into `results/selection_decisions.csv` (`material_id`, `selected_baseline`, `selected_random`, `selected_uq`); run a bootstrap/permutation significance test (10,000 resamples; McNemar's test as specified in US-3 is also acceptable) comparing UQ precision vs random precision; write `results/screening_significance.json` (`p_value`, `test_statistic`, `method`) and the final `results/screening_results.csv` (`method`, `recall`, `precision`, `precision_gain`, `p_value`, `threshold_met`), where `threshold_met` is true when precision gain ≥ 0.05 OR p-value < 0.05.
  *Verification*: each `material_id` appears exactly once in the decision matrix; selection sizes match across the three strategies; the significance JSON contains finite numerics; the final report contains exactly one row for the best method; all values are computed from real predictions — no placeholders.

- [ ] T007 [P] Add independent correctness, sensitivity, and runtime checks and record actual outcomes (`code/tests/`, `code/utils/timeout.py`, `code/main.py`)
  *Implement* a `Timeout` context manager in `code/utils/timeout.py` that raises `TimeoutError` after the wall-clock limit derived from `config.yaml` (`timeout_hours: 5.0`), with a unit test that a sleep past the limit triggers the exception (FR-009). *Extend* `code/main.py` to chain download → preprocess → training → per-seed inference → metrics → screening inside the Timeout context, and to write `results/runtime_report.json` (wall-clock seconds, peak RAM) via the existing `code/utils/runtime_logger.py`.
  *Run* the full test suite (`pytest code/tests/`) and the end-to-end pipeline; record the actual runtime, the SC-002 outcome against the 5-hour limit, and the SC-005 null-percentage of target columns in the raw data (report alongside `validation_report.json` in `results/runtime_report.json` or `results/metrics/`).
  *Verification*: `python -m code.main` completes without uncaught exceptions on a fresh checkout; `results/runtime_report.json` is non-empty and contains `wall_clock_seconds`; all unit and contract tests pass; artifacts under `results/` validate against their contract schemas.

- [ ] T008 [US2] Generate the final tables and figures directly from validated outputs
  *Produce* from the real computed artifacts: `results/metrics/calibration_summary.csv` (final formatted table), reliability diagrams (already from T005, verified here for completeness), a screening-utility summary table from `results/screening_results.csv`, and a figure comparing aleatoric vs epistemic variance distributions across methods (from the aggregated predictions). Every number in these artifacts must be derived programmatically from `results/` CSVs/JSONs — no hand-typed values.
  *Verification*: each figure file exists and is non-empty; a scripted check re-derives each tabulated value from its source artifact and asserts equality within tolerance.

## Phase 3: Reproducible results and paper handoff

- [ ] T009 [P] Write the methods/results account linked to actual outputs (`specs/001-assessing-uncertainty-quantification-tec/research.md`)
  *Document* the data source and any deviation from the original Materials Project idea (OQMD HF subset), the preprocessing and split protocol, the three UQ methods with their exact hyperparameters, the calibration metrics with their definitions, the screening design, and the actual measured results (ECE/interval scores per method, CV across seeds, screening precision gain and p-value), each linked to the specific output file and cell/row it came from. *Describe honestly* any negative findings (e.g., a method failing calibration), the GP fallback/partial-run path if triggered, and limitations (dataset subset size, Gaussian interval assumption, CPU-scaled model capacity).
  *Verification*: every quantitative claim in the document cites an existing artifact path; no number appears that is not present in `results/`.

- [ ] T010 [P] Re-run the documented workflow end-to-end and document the paper-stage handoff (`specs/001-assessing-uncertainty-quantification-tec/quickstart.md`)
  *Re-run* the full pipeline from its declared inputs (fresh `data/raw/` fetch through final metrics) using the command documented in `quickstart.md`; confirm all tests pass and artifact checks (T007) hold on the re-run. *Document* the paper-stage handoff: the tables and figures to carry into the paper (paths), the key claims each supports, and open limitations for the paper's discussion section. Do NOT task PDF compilation, layout, or publication — those belong to the paper pipeline.
  *Verification*: the quickstart command executes successfully from a clean checkout; the handoff section lists every result artifact the paper stage needs; no research script writes to `state/` or platform-owned paths.

---

## Dependencies and requirement coverage

| Requirement | Task(s) | Demonstrating command |
|---|---|---|
| FR-001 (OQMD download, descriptors, targets) | T001 | `python -m code.data.download` + checksum verification |
| FR-002 (baseline NN, split) | T001, T002 | pytest parameter-count test; split CSV checks |
| FR-003 (Deep Ensemble) | T002, T003 | five `ensemble_seed_*.pt` checkpoints |
| FR-004 (MC-Dropout, 30 passes) | T002, T003 | MC-Dropout prediction CSV checks |
| FR-005 (Sparse GP + PCA + reconstruction variance) | T001, T002, T003 | `sparse_gp_model.pt`, `gp_reconstruction_variance.json` |
| FR-006 (ECE, Winkler, sharpness) | T004, T005 | `calibration_summary.csv` schema validation |
| FR-007 (screening case study) | T006 | `screening_results.csv` |
| FR-008 (aleatoric/epistemic) | T002, T003, T004 | variance-additivity test |
| FR-009 (5h timeout) | T007 | Timeout unit test; `runtime_report.json` |
| FR-010 (missing-data exclusion) | T001 | `validation_report.json` schema validation |
| SC-001–SC-005 | T005, T006, T007 | metrics, screening, runtime artifacts |

**Execution order**: T001 → T002 → T003 → (T004 ∥ T007-timeout) → T005 → T006 → T007 → T008 → T009 → T010. T004's metric unit tests depend only on T002's model definitions and may be developed in parallel with T003.

## Revision behavior

Verified scaffolding, lint/format, runtime logger, and contract-validation work (former T001–T003, T009, T033a, T034a/b, T035–T037) is preserved and not re-tasked. All seven verifier-rejected items (former T006a/c/d, T012, T013b, T014, T016a) are reopened and consolidated into T001–T003 above with their full acceptance criteria intact. Former optional Phase-7 items are folded in: GP inducing-point fallback (T002), per-seed ECE logging in the CV calculation (T005), and finite-threshold validation (T006). Streaming support (former T039) is dropped as out of scope for the current subset size; the loader must fail loudly rather than fall back (see T001).
