# Tasks: Predicting Molecular Polarity from SMILES Strings with Machine Learning

**Input**: Design documents from `/specs/001-predict-molecular-polarity/`  
**Prerequisites**: plan.md, spec.md, data-model.md, contracts/

## Phase 1: Data acquisition & descriptor generation

- [ ] T103 **[US1]** **[FR-006]** Fix and validate `code/data/validate.py` so that it derives `expected_input_columns` dynamically from `data/processed/descriptor_names.json`. The script must exit with status 0 on a correct descriptor matrix and non‑zero on any mismatch.  
  - **Verification**: `python code/data/validate.py data/processed/descriptors.parquet` exits 0; deliberately corrupting a column name causes a non‑zero exit.

- [ ] T102 **[US1]** **[FR-006]** Materialize contract validators under `tests/contract/`. Create `tests/contract/validators.py` with Pydantic models for the descriptor matrix and model output, and add `test_dataset_schema.py` & `test_model_output.py` that validate the real artifacts produced later.  
  - **Verification**: `pytest tests/contract/ -q` passes against the real files.

- [ ] T101 **[US1]** **[FR-001, FR-006, FR-008, FR-009]** Download the QM9 dataset using the `qm9pack` library (which internally resolves the canonical HuggingFace URL) and generate a 2‑D descriptor matrix (`data/processed/descriptors.parquet`).   <!-- FAILED-IN-EXECUTION: code/data/generate_descriptors.py exit=1 -->
  - Stream the parquet in batches to keep peak RAM ≤ 6 GB.  
  - Exclude any TPSA‑related descriptors and all SMARTS‑based functional‑group counts.  
  - Log peak memory and total runtime; assert that preprocessing completes within **15 minutes**.  
  - Impute NaN descriptor values with the median of the column; records with > 5 % NaNs are dropped and logged.  
  - Add boolean flags `stereochemistry_flag` (≤ 5 % true) and `flexible_flag` (rotatable‑bond ≥ 5).  
  - Persist the ordered list of descriptor names to `data/processed/descriptor_names.json`.  
  - **Verification**: file exists, ≥ 200 descriptor columns, no TPSA columns, runtime ≤ 15 min, flags within limits, contract check via `T103` passes.

## Phase 2: Feature selection & correlation filtering

- [ ] T105 **[US3]** **[FR-007]** Compute Variance Inflation Factor (VIF) for all descriptors in `data/processed/descriptors.parquet`. Iteratively remove the feature with the highest VIF while any VIF > 5.0, stopping when all remaining VIF ≤ 5.0 **or** when removal would leave fewer than 150 descriptors. In the latter case, switch to L1‑regularized LightGBM (fallback) and retain all features.  
  - Output pruned descriptor matrix (overwrites `descriptors.parquet`), `data/processed/vif_scores.csv`, and a hierarchical Ward‑linkage `data/processed/cluster_map.csv` mapping each descriptor to a cluster ID.  
  - **Verification**: VIF scores conform to `vif_schema.schema.yaml`; at least 150 descriptors remain; fallback flag set correctly if invoked.

- [ ] T113 **[US2]** **[FR-013]** Split the pruned descriptor matrix into deterministic random train/test sets (`code/data/split_data.py`) using the global seed from `code/utils/config.py`.  
  - Compute Pearson correlation |r| on the **training split** for all remaining descriptors against the target dipole moment. Remove any descriptor with |r| > 0.85, ensuring at least 150 descriptors remain; if removal would violate this, abort and raise an error.  
  - Persist the filtered train and test matrices to `data/processed/train.parquet` and `data/processed/test.parquet`.  
  - **Verification**: correlation filter applied only on training data; resulting feature count ≥ 150; no column violates the |r| threshold.

- [ ] T104 **[US2]** **[FR-002, FR-003, FR-013]** Train a LightGBM regression model on the filtered training matrix (`code/model/train.py`).  
  - Use 5‑fold cross‑validation, limit `num_iterations` ≤ 500, log hyperparameters to `code/config.yaml`.  
  - After training, evaluate on the held‑out test set, compute R², RMSE, and baseline R² (mean‑only model).  
  - **Verification**: `data/processed/model.pkl` loads; `data/results/model_metrics.json` conforms to `model_output_schema.schema.yaml`; **validation R² ≥ 0.10** and exceeds baseline; all metrics recorded.

## Phase 3: Interpretability & stability

- [ ] T106 **[US3]** **[FR-004, FR-005, SC-002, SC-003]** Run SHAP analysis on the trained model (`code/model/evaluate.py`).  
  - Use `shap.TreeExplainer` on the test set, aggregate mean absolute SHAP values per descriptor cluster (using `cluster_map.csv`).  
  - Generate `data/results/shap_summary.png` and `data/results/model_predictions.json` (conforming to `model_output.schema.yaml`).  
  - **Verification**: artifacts exist, top‑10 clusters listed, report distinguishes collinear clusters.

- [ ] T107 **[US3]** **[FR-005, SC-003]** Perform full‑dataset bootstrap stability analysis. For each of 100 resamples (sampling **with replacement** the entire dataset to the original size), repeat the full training pipeline (split, train LightGBM, compute SHAP) and record the top‑10 feature clusters. Compute the Jaccard similarity of the top‑10 sets across all resamples.  
  - Write `data/results/stability_report.json` (schema `model_output.schema.yaml`) with `bootstrap_resamples`, `jaccard_similarity`, `top_10_clusters`, and `stability_status` (`stable` if ≥ 0.7).  
  - If Jaccard < 0.7, log a CRITICAL message, write `stability_failed.json`, and exit 1.  
  - **Verification**: JSON conforms to schema; Jaccard ≥ 0.7 recorded.

- [ ] T108 **[US3]** **[FR-012, SC-009]** Validate the top‑10 SHAP clusters by training ten single‑feature LightGBM models (one per cluster's representative descriptor). Record each model’s test R² in `data/results/single_feature_r2.csv`.  
  - **Verification**: CSV has 10 rows; each R² ≥ 0.02; values reported honestly.

## Phase 4: Flexible‑molecule dual‑heuristic check

- [ ] T114 **[US3]** **[FR-009]** Compute a second flexibility heuristic: a torsional‑flexibility score defined as the average absolute proper torsion angle (via RDKit) for each molecule. Flag molecules where this score exceeds the 75th percentile. Compute the Jaccard similarity between the set flagged by `flexible_flag` (rotatable‑bond count) and the set flagged by the torsional score; assert Jaccard ≥ 0.8.  
  - Produce `data/processed/flexible_analysis.json` summarizing counts and Jaccard value.  
  - **Verification**: Jaccard ≥ 0.8; if not, pipeline exits with a critical log.

## Phase 5: Integrity, constraints, and handoff

- [ ] T109 **[US1]** **[FR-006]** Generate `state/manifest.json` containing SHA‑256 checksums for `data/processed/descriptors.parquet`, `vif_scores.csv`, `cluster_map.csv`, `model.pkl`, and `model_metrics.json`. Insert a verification step in `code/main.py` that recomputes these checksums **before** the SHAP stage (i.e., before T106) and aborts on mismatch.  
  - **Verification**: Manifest exists; tampering a tracked file causes pipeline to exit non‑zero.

- [ ] T110 **[US1]** **[SC-004, SC-010]** Execute the full pipeline (`python code/main.py`) on the free‑tier CPU runner. `code/utils/constraints.py` records total runtime and peak RAM in `logs/constraint_metrics.json`. If the full 130 k‑molecule run exceeds the budget, process a fixed‑seed real sample of **100 000** molecules (documented in the log).  
  - **Verification**: Logged runtime ≤ 6 h and RAM ≤ 6 GB; sampling rule recorded if applied.

- [ ] T111 **[US1]** **[SC-007, FR-009]** Write a comprehensive results summary (`specs/001-predicting-molecular-polarity/research.md`) that links every reported number to its source artifact. Include model metrics, SHAP top features, stability Jaccard, single‑feature R², constraint metrics, and the flexible‑molecule error‑analysis report from T114. Also note that FR‑010/FR‑011/SC‑008 are out‑of‑scope pending a spec amendment.  
  - **Verification**: Every figure/table references a file under `data/` or `logs/`; no invented numbers.

- [ ] T112 **[US1]** **[SC-004]** Perform a clean re‑run after deleting `data/processed/` and `data/results/`. Confirm that all unit, contract, and integration tests pass (`pytest tests/ -q`) and that regenerated artifact checksums match those recorded in `state/manifest.json`. Update `quickstart.md` with the exact command `python code/main.py`.  
  - **Verification**: Second run reproduces identical checksums; quickstart command works end‑to‑end.

## Phase 6: Spec amendment flag

- [ ] T115 **[US?]** **[FR-010, FR-011, SC-008]** Initiate and document a spec amendment to remove or annotate FR‑010, FR‑011, and SC‑008 due to conflict with Constitution Principle VI. This task will create a pull request updating `specs/001-predicting-molecular-polarity-from-smile/spec.md` accordingly.  
  - **Verification**: Pull request opened and merged; amendment reflected in spec; issue logged in tracker.

## Execution order

The tasks are ordered to respect all data dependencies:

1. T103 → T102 → T101 → T105 → T113 → T104 → T109 → T106 → T107 → T108 → T114 → T110 → T111 → T112 → T115

A note is included to explain that this ordering follows functional requirements rather than the original plan ordering. 