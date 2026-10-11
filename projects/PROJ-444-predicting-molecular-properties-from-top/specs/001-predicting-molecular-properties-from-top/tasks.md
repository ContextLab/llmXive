# Tasks: Predicting Molecular Properties from Topological Data Analysis

**Inputs**: Active `spec.md`, `plan.md`, and contracts under `specs/001-predicting-molecular-properties-from-top/`. Paths are relative to the project directory (`projects/PROJ-444-predicting-molecular-properties-from-top/` unless under `specs/`).

**Revision context**: Prior verification rejected T007, T008a, T008b, T008c (truncated scripts, absent artifacts). This re-plan consolidates the pending work into individually verifiable steps, each producing a real file with checkable schema/content. Research scripts must NOT write to `state/` (platform-owned); checksums are recorded only in `data/checksums.txt`.

## Preserved verified work (reference only — do not redo)

- [ ] T005 [Foundational] `code/utils/graph_builder.py` — RDKit graph construction with valence/aromaticity/bond-order validation (verified).
- [ ] T006 [Foundational] `code/utils/persistence_utils.py` — shortest-path filtration and empty-diagram zero-vector handling (verified).
- [ ] T015b [Foundational] Sparse-matrix fallback in `code/utils/persistence_utils.py` for intra-molecule memory spikes (verified).
- [ ] T021 [Foundational] CPU-only enforcement (FR-008) via runtime GPU detection check (verified).
- [ ] T029 [Foundational] `code/07_resource_monitor.py` resource-limit wrapper for SC-004 (verified).
- [ ] T009 [Foundational] Contract schemas (`dataset.schema.yaml`, `feature_matrix.schema.yaml`, `model_metrics.schema.yaml`) (verified).

## Phase 1: Setup and first end-to-end analysis

- [ ] T001 [P] [US1] **Data ingestion with fail-loudly provenance** — Implement `code/01_data_ingestion.py` as a single complete, runnable script that:
  1. Downloads the real MoleculeNet ESOL CSV from `https://deepchemdata.s3-us-west-1.amazonaws.com/datasets/dataset_esol.csv` using `requests` to `data/raw/esol.csv`. On any fetch failure, raise `SystemExit(1)` with message "Data Gap: fetch failed. No synthetic fallback." — NEVER fall back to generated or placeholder data.
  2. Validates the CSV contains the columns `smiles` and `logP` per `specs/001-predicting-molecular-properties-from-top/contracts/dataset.schema.yaml`; exit `SystemExit(1)` if missing.
  3. Computes SHA256 of `data/raw/esol.csv` and appends `<sha256>  data/raw/esol.csv` to `data/checksums.txt` (replaces rejected T007; no `state/` writes — state is platform-owned).
  4. Runs the a priori power analysis (paired t-test, alpha=0.05, power=0.8, effect size d=0.5, minimum N=128) and writes `data/processed/power_analysis_report.json` with keys `min_n`, `actual_n`, `passes`.
  5. Filters molecules with RDKit molecular weight > 1000 Da, writing `data/processed/filtered_esol.csv` and `data/logs/large_molecule_exclusions.log` (input count, excluded count).
  6. Counts unique Bemis-Murcko scaffolds (`rdkit.Chem.Scaffolds.MurckoScaffold`) on the filtered set; exits `SystemExit(1)` with "Scaffold Insufficient: <count> < 100" if < 100; writes `data/processed/scaffold_counts.json`.
  7. Performs the 5-fold scaffold split with seed=42 and writes `data/processed/splits.json` (5 lists of row indices; no scaffold appears in two folds).
  **Verification**: Running `python code/01_data_ingestion.py` exits 0 and all seven artifacts exist with the stated content; running with a bad URL exits 1 without creating fake data. This single script replaces the previously truncated T008a/T008b/T008c/T007 chain so every deliverable is produced by one deterministic, verifiable execution.
  **Dependency**: T005 (RDKit utilities).

- [ ] T002 [US1] **TDA feature computation (primary 10x10 baseline)** — Implement `code/02_tda_computation.py` that reads `data/processed/filtered_esol.csv`, builds graphs via `code/utils/graph_builder.py`, computes persistent homology with shortest-path distance filtration (FR-001) via `code/utils/persistence_utils.py`, and vectorizes diagrams to persistence images with a fixed 10x10 grid, sigma=0.1 (FR-002). Invalid SMILES are logged to `data/logs/invalid_smiles.log` and `data/excluded_smiles_manifest.csv` (`molecule_id`, `error_message`, `original_smiles`); empty diagrams yield zero vectors. **Deliverable**: `data/processed/persistence_images_10x10.csv` with `molecule_id` + 100 float columns `p_img_0`…`p_img_99`, no NaNs. **Verification**: Contract test `code/tests/test_feature_matrix.py` asserts the file exists, schema matches, and every valid molecule has a non-null row; disconnected graphs and linear chains are handled without crashing (US-1 acceptance scenarios 2–3). **Dependency**: T001.

- [ ] T003 [US1] **Traditional descriptors and combined feature matrix** — Implement `code/03_feature_engineering.py` computing RDKit traditional descriptors (MW, atom counts, Morgan fingerprint bits, etc.) to `data/processed/traditional_descriptors.csv`, then merging with `data/processed/persistence_images_10x10.csv` on `molecule_id` to `data/processed/combined_features.csv`. **Verification**: Row counts match the filtered dataset; column sets are the union of inputs; no NaNs. **Dependency**: T002.

- [ ] T004 [US2] **First end-to-end model run (thin slice)** — Implement `code/04_model_training.py` that loads `data/processed/splits.json`, trains Ridge (alpha=1.0) and Random Forest (100 trees, max_depth=10, seed=42) on the three feature sets (traditional-only, topological-only, combined) targeting `logP` with 5-fold scaffold CV (FR-003, FR-004), and writes per-fold and mean R²/RMSE plus feature importances to `reports/metrics/model_performance.json` matching `model_metrics.schema.yaml`. Log `Seed: 42` and `Splitter: ScaffoldSplitter` to `data/logs/training.log` (FR-008 check invoked at start). **Verification**: `pytest code/tests/test_metrics_schema.py` validates the JSON against the contract; three model configurations × two learners are present with real cross-validated scores. **Dependency**: T003.

**Checkpoint**: `python code/01_data_ingestion.py && python code/02_tda_computation.py && python code/03_feature_engineering.py && python code/04_model_training.py` runs end-to-end on the real ESOL data with checkable numerical outputs.

## Phase 2: Complete the study and validate its evidence

- [ ] T005r [US1] **Sensitivity-sweep vectorizations** — Extend `code/02_tda_computation.py` with a resolution argument to also generate `data/processed/persistence_images_20x20.csv` and `data/processed/persistence_images_30x30.csv` (sigma=0.1) from the same diagrams (FR-006 input side). **Verification**: Files exist with 400 and 900 feature columns respectively, same molecule IDs, no NaNs. **Dependency**: T002.

- [ ] T006r [US3] **Sensitivity analysis execution** — Implement `code/05_sensitivity_analysis.py` that retrains the FR-003 models on the 20x20 and 30x30 topological feature sets using the same scaffold splits, then reports R² across resolutions {10, 20, 30} and the coefficient of variation of R² in `reports/metrics/sensitivity_analysis.json` with keys `resolutions`, `r2_scores`, `r2_variance` (FR-006, SC-002). **Verification**: JSON contains real retrained metrics (not copies of the 10x10 run); CV is computed from those scores. **Dependency**: T004, T005r.

- [ ] T007r [US3] **Statistical comparison with Holm-Bonferroni correction** — Implement `code/06_diagnostics.py` (statistics section) that performs paired t-tests (or Wilcoxon) on per-fold R² between combined vs. traditional-only models, applies the Holm-Bonferroni correction (per plan.md's methodological update replacing plain Bonferroni for correlated tests; document the deviation from FR-005's wording in the report's `methodology` block), and writes corrected p-values to `reports/metrics/diagnostics.json` with keys `corrected_pvalues`, `methodology.correction_method`, `methodology.controlled_alpha` (FR-005, SC-003). **Verification**: Unit test `code/tests/test_correction.py` checks the Holm algorithm against known p-values including the N=1 case. **Dependency**: T004.

- [ ] T008r [US3] **Collinearity and redundancy diagnostics** — Extend `code/06_diagnostics.py` to (a) compute VIF via `statsmodels` on `data/processed/combined_features.csv`, flagging and listing every predictor with VIF > 5 in `reports/metrics/diagnostics.json` under `vif` (FR-007, SC-005), and (b) compute mutual information between the traditional and topological feature sets via `sklearn.feature_selection.mutual_info_regression`, reported under `mutual_information` (FR-009, SC-001 prerequisite). **Verification**: `diagnostics.json` contains a VIF value for every predictor and a numeric MI summary; flagged pairs are listed. **Dependency**: T003, T004.

- [ ] T009r [US2] **Independent checks and resource measurement** — Add unit tests for the graph builder (valid, disconnected, invalid SMILES) and persistence utils (empty diagram → zero vector) in `code/tests/`; run the full pipeline under `code/07_resource_monitor.py` and record peak RAM and CPU time in `reports/metrics/resource_usage.json`, confirming < 6.3 GB RAM and < 5.4 h (SC-004, FR-008). **Verification**: `pytest code/tests/` passes; resource JSON contains measured (not assumed) values from a real run. **Dependency**: T006r, T007r, T008r.

- [ ] T010r [US1/US2/US3] **Result tables and figures from validated outputs** — Generate figures directly from the result artifacts: Betti/persistence-image examples for ring vs. linear molecules, per-fold R²/RMSE comparison across the three feature sets, and the sensitivity sweep plot, saved under `reports/figures/`; and a consolidated results table `reports/metrics/summary_table.csv` joining model performance, corrected p-values, VIF flags, and MI. **Verification**: Every figure/table is produced by a script reading only files created in T004–T008r; no hand-typed numbers. **Dependency**: T009r.

## Phase 3: Reproducible results and paper handoff

- [ ] T011r [P] **Methods/results account and quickstart** — Update `specs/001-predicting-molecular-properties-from-top/quickstart.md` with the TDA methodology (FR-001/FR-002 references), the exact runnable command sequence (ingest → TDA → features → train → sensitivity → diagnostics), the fixed seed 42, and a concise methods/results narrative linking each claim to the actual output files in `reports/metrics/` and `reports/figures/`. Report negative or null findings (e.g., high TDA–descriptor redundancy per FR-009) honestly. **Verification**: Every referenced artifact path exists; the documented command sequence matches the scripts' actual interfaces. **Dependency**: T010r.

- [ ] T012r **Full re-run and paper-stage handoff** — Re-run the documented workflow end-to-end from `data/raw/esol.csv` (checksum-verified against `data/checksums.txt`), confirm all tests and artifact checks pass, and write the paper-stage handoff in `specs/001-predicting-molecular-properties-from-top/quickstart.md`: required figures/tables, the primary claim (whether topological features add predictive signal beyond traditional descriptors, with corrected p-value and MI context), and stated limitations (shortest-path filtration vs. 3D conformation, associative-not-causal design, Holm-Bonferroni conservatism). **Verification**: Fresh run exits 0; `pytest code/tests/` passes; handoff section names the exact result files the paper stage must consume. **Dependency**: T011r.

## Dependencies and requirement coverage

| Requirement | Task(s) | Demonstrating command |
|---|---|---|
| FR-001 (shortest-path PH) | T002 | `python code/02_tda_computation.py` |
| FR-002 (10x10 baseline) | T002 | contract test on `persistence_images_10x10.csv` |
| FR-003/FR-004 (models, scaffold CV, seed 42) | T004 | `python code/04_model_training.py`; `test_metrics_schema.py` |
| FR-005 (multiplicity correction) | T007r | `test_correction.py`; `diagnostics.json` |
| FR-006 (resolution sweep) | T005r, T006r | `sensitivity_analysis.json` |
| FR-007 (VIF) | T008r | `diagnostics.json` `vif` block |
| FR-008 (CPU-only) | T004, T009r | GPU check in training entry; resource run |
| FR-009 (mutual information) | T008r | `diagnostics.json` `mutual_information` |
| SC-001–SC-005 | T004, T006r, T007r, T008r, T009r | respective JSON artifacts |

Execution order: T001 → T002 → T003 → T004 (end-to-end checkpoint) → T005r → {T006r, T007r, T008r} → T009r → T010r → T011r → T012r. T011r is [P] with respect to T009r documentation-wise but sequenced after T010r for content.

## Revision behavior

- Rejected tasks T007/T008a/T008b/T008c are consolidated into T001: one complete ingestion script whose every deliverable is a real file produced in a single deterministic run. No `state/` writes — artifact hashing and project state belong to the platform.
- Verified tasks T005, T006, T009 (schemas), T015b, T021, T029 are preserved as completed reference; their acceptance criteria are unchanged.
- Polish-only tasks from the prior list (lint refactors, cyclomatic complexity, generic docs) are dropped as non-scientific; their surviving substance (reproducibility documentation, full-pipeline re-run) lives in T011r/T012r.
