# Tasks: Predicting Molecular Permeability Coefficients Using Graph Neural Networks and Publicly Available Datasets

**Inputs**: `spec.md`, `plan.md`, the contracts in `specs/001-predicting-molecular-permeability-coeffi/`, and reviewer feedback.

## Phase 1: Setup and first end-to-end analysis

- [ ] T001 [US1] Implement `code/data/download.py` — a `DataLoader` that fetches a **verified real dataset containing experimental permeability coefficients** (e.g., from Hugging Face `datasets.load_dataset("<verified_permeability_dataset>")`). The loader must FAIL LOUDLY if the dataset does not contain the required `permeability` column; no proxy fallback is permitted. It writes the raw file(s) under `data/raw/` and records SHA‑256 checksums in `data/raw/checksums.json`. Streaming is used for datasets >7 GB. Verification: script exits 0 and `data/raw/` contains real rows; a unit test asserts the required column exists. <!-- FAILED-IN-EXECUTION: code/data/download.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/data/download.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/data/download.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/data/download.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/data/download.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/data/download.py exit=1 -->

- [ ] T002 [US1] Implement `code/data/preprocess.py` — `MoleculeProcessor.process(df)` that parses each SMILES with `rdkit.Chem.MolFromSmiles` (invalid SMILES logged and excluded), computes the required descriptor set (MW, logP, TPSA, HBA, HBD, RotatableBonds, etc.), builds the molecular graph (node and edge feature JSON columns), and **uses the experimental permeability column as the `target`**. Missing descriptor values are median‑imputed; rows missing the target are excluded with a warning. Output conforms to `specs/.../contracts/dataset.schema.yaml` and is written to `data/processed/processed_data.csv`.

- [X] T003 [US1] Implement `code/data/split.py` — performs:
  1. **Retention check (FR‑011)**: abort with `SystemExit(1)` if valid molecule retention < 95 %.
  2. **Bias check (FR‑013)**: compute Pearson |r| between each descriptor and the experimental target; if any |r| > 0.85, set `bias_violation: true` and abort (target must be independent).
  3. **Stratified split (FR‑003)**: if a `polymer_type` column exists, perform an 80/20 stratified split with per‑class absolute percentage‑point difference ≤ 5; otherwise fall back to a random split with a logged warning. Writes `train.csv`, `test.csv`, and `data/results/stratification_report.md`. Verification: script exits 0, reports contain required sections, and `metrics.json` records the checks.

**Checkpoint**: The command chain `python -m code.data.download && python -m code.data.preprocess && python -m code.data.split` must complete without error before any modeling tasks commence.

## Phase 2: Complete the study and validate its evidence

- [ ] T004 [US2] Implement `code/models/gnn.py` (shallow 2‑layer MPNN, CPU‑only, early stopping patience 5, max 50 epochs) and `code/models/rf.py` (RandomForestRegressor, 100 trees, `max_features='sqrt'` on standard descriptors) and `code/models/rf_ablation.py` (RandomForest on graph‑derived ablation features only – FR‑012). Include a CPU feasibility pre‑check that writes `cpu_feasibility_check` (`passed` or `warning`) to `data/results/metrics.json`. <!-- FAILED-IN-EXECUTION: code/models/rf_ablation.py exit=1 -->

- [ ] T005 [US2] Implement `code/analysis/train.py` — trains the three models on `data/processed/train.csv`, saves checkpoints under `data/interim/`, and records `total_training_time_hours` and `peak_memory_gb` in `data/results/training_log.json`. If the GNN does not achieve a validation loss improvement or its test performance is worse than the RF baseline, flag `no_significant_improvement: true` (do not force a positive claim).

- [ ] T006 [US2] Implement `code/analysis/evaluate.py` — predicts on `data/processed/test.csv`, computes RMSE, MAE, R² for each model, writes `data/results/prediction_errors.json` and a consolidated `data/results/metrics.json` that conforms to `results.schema.yaml`.

- [ ] T007 [US2] Implement `code/analysis/statistics.py` — performs a **paired two‑tailed t‑test** between GNN and RF error arrays, computes **Cohen’s d** and its 95 % confidence interval, and conducts a post‑hoc power analysis. The resulting `statistical_test` entry must include `p_value`, `significant` (p < 0.05), `method`, `cohen_d`, `ci_lower`, `ci_upper`, and `power`. Additionally, the task asserts that **Cohen’s d ≥ 0.5**; if not, it records `effect_size_insufficient: true` in the metrics.

- [ ] T008 [US3] Implement `code/analysis/explain.py` — runs SHAP (`shap.TreeExplainer`) on the RF descriptor model to produce a ranked list of descriptors (`feature_importance_rf.json`) and runs GNNExplainer on the trained GNN to produce a ranked list of substructures (`feature_importance_gnn.json`). It also computes a **quantitative overlap metric**: the count of shared top‑5 items between the two rankings, stored as `top5_overlap` in `data/results/interpretability_metrics.json`.

- [ ] T009 [US3] Implement `code/analysis/report.py` — generates `data/results/comparative_report.md` that:
  1. Lists the top‑5 SHAP descriptors and top‑5 GNN substructures.
  2. Reports the `top5_overlap` value and asserts **overlap ≥ 2** as a concrete interpretability success criterion (SC‑003).
  3. Includes sections “Bias Violation”, “Statistical Significance”, and “Effect Size” that reference the values in `metrics.json`.
  4. Renders bar‑chart figures `shap_bar.png` and `gnn_substructures.png` from the importance JSONs.

- [ ] T010 Implement `code/utils/verify_metrics.py` — validates `data/results/metrics.json` against `results.schema.yaml` and checks additional flags (`bias_violation`, `data_integrity_warning`, `effect_size_insufficient`). It exits with status 0 only if all success criteria (SC‑001 – SC‑005) are satisfied.

## Phase 3: Reproducible results and paper handoff

- [ ] T011 Write `results.md` that references every numeric claim to the corresponding entry in `data/results/metrics.json` and includes the required handoff statements (dataset source, experimental target, split strategy, statistical outcomes, interpretability metrics, and any bias or effect‑size warnings).

- [ ] T012 Re‑run the full workflow from download to verification with fixed seeds, confirm that `pytest` passes and that `verify_metrics.py` reports success. Document the reproducibility check in `results.md`.
