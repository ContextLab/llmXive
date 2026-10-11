# Tasks: Predicting Molecular Properties from Topological Data Analysis

**Inputs**: Active `spec.md`, `plan.md`, and contracts under `specs/001-predicting-molecular-properties-from-top/`. Paths are relative to the project directory (`projects/PROJ-444-predicting-molecular-properties-from-top/` unless under `specs/`).

**Revision context**: Prior verification rejected T007, T008a, T008b, T008c (truncated scripts, absent artifacts). This re‑plan consolidates the ingestion work into small, individually verifiable steps, each producing a real file with checkable schema/content. Research scripts must NOT write to `state/` (platform‑owned); checksums are recorded only in `data/checksums.txt`.

## New foundational tasks

- [ ] T000 [P] **Create pinned requirements and select PH library** — Write `code/requirements.txt` with exact version pins for all dependencies, including `gudhi==3.7.0` (selected as the deterministic PH library). Verify that `pip install -r code/requirements.txt` succeeds on a fresh runner.  
  **Verification**: `pip check` passes; `requirements.txt` contains no version ranges.

- [ ] T000a [P] **Document PH library choice** — Add a short comment in `code/requirements.txt` explaining why GUDHI was chosen over alternatives to ensure reproducibility.

## Phase 1: Setup and first end‑to‑end analysis (split into fine‑grained steps)

- [ ] T001a [P] **Download ESOL dataset (URL argument)** — Implement `code/01_data_ingestion.py` with a `--url` CLI argument (default `https://deepchemdata.s3-us-west-1.amazonaws.com/datasets/dataset_esol.csv`). On any fetch failure, raise `SystemExit(1)` with message `"Data Gap: fetch failed. No synthetic fallback."`.  
  **Verification**: Running with `--url [UNRESOLVED-CLAIM: https://invalid.url` — ConnectionError: HTTPSConnectionPool(host='invalid.url%60', port=443): Max retries exceeded with url: / (Caused by NameResolutionError("HTTPSConnection(host='invalid.url%60', port=443): Failed to resolve 'invalid.url%60' ([Errno -2] Name or service not known)"))] exits 1 and creates no data files.

- [ ] T001b [P] **Record SHA256 checksum** — After successful download, compute SHA256 of `data/raw/esol.csv` and append `<sha256>  data/raw/esol.csv` to `data/checksums.txt`. **No state‑file hash is recorded** per platform rule.  
  **Verification**: `data/checksums.txt` contains a line matching the file’s hash.

- [ ] T001c [P] **Power analysis report** — Perform a priori power analysis (paired t‑test, α=0.05, power=0.8, effect size d=0.5, minimum N=128). Write `data/processed/power_analysis_report.json` with keys `min_n`, `actual_n`, `passes`.  
  **Verification**: JSON file exists; `passes` is `true` for ESOL.

- [ ] T001d [P] **Chunked handling of large molecules** — Instead of dropping molecules with molecular weight >1000 Da, process them using the sparse‑matrix fallback from `code/utils/persistence_utils.py` (T015b) in chunked mode to keep RAM usage ≤6 GB. Log any fallback usage in `data/logs/large_molecule_handling.log`.  
  **Verification**: Log file records any large‑molecule processing; no molecules are excluded solely by weight.

- [ ] T001e [P] **Scaffold count and validation** — Count unique Bemis‑Murcko scaffolds on the full (post‑chunked) dataset. If count < 100, exit `SystemExit(1)` with `"Scaffold Insufficient: <count> < 100"`. Write `data/processed/scaffold_counts.json`.  
  **Verification**: JSON file exists; script exits with non‑zero status when scaffold count is insufficient.

- [ ] T001f [P] **Scaffold‑based 5‑fold split** — Generate `data/processed/splits.json` containing five lists of row indices such that no scaffold appears in more than one fold, using seed 42.  
  **Verification**: Splits file exists; a quick script confirms scaffold exclusivity.

- [ ] T002 [US1] **TDA feature computation (primary 10×10 baseline)** — Reads `data/processed/filtered_esol.csv` (output of T001d), builds graphs via `code/utils/graph_builder.py`, computes persistent homology with shortest‑path distance filtration (FR‑001) via `code/utils/persistence_utils.py`, and vectorises to persistence images with a fixed 10×10 grid, σ=0.1 (FR‑002). Logs invalid SMILES to `data/logs/invalid_smiles.log` and writes `data/processed/persistence_images_10x10.csv` (molecule_id + 100 float columns, no NaNs).  
  **Verification**: `code/tests/test_feature_matrix.py` (added in T002a) validates schema and NaN‑free rows; disconnected and linear molecules are handled without crash.

- [ ] T002a [P] **Create feature‑matrix contract test** — Add `code/tests/test_feature_matrix.py` that loads `persistence_images_10x10.csv` and checks conformity to `feature_matrix.schema.yaml`.  
  **Verification**: `pytest code/tests/test_feature_matrix.py` passes.

- [ ] T003 [US1] **Traditional descriptors & combined matrix** — Compute RDKit traditional descriptors (MW, atom counts, Morgan fingerprint bits) to `data/processed/traditional_descriptors.csv`; merge with `persistence_images_10x10.csv` on `molecule_id` to produce `data/processed/combined_features.csv`.  
  **Verification**: Row counts match filtered dataset; column union present; no NaNs.

- [ ] T004 [US2] **First end‑to‑end model run (thin slice)** — Load `splits.json`, train Ridge (α=1.0) and Random Forest (100 trees, max_depth=10, seed 42) on three feature sets (traditional, topological, combined) targeting `logP` with 5‑fold scaffold CV (FR‑003, FR‑004). Write per‑fold and mean R²/RMSE plus feature importances to `reports/metrics/model_performance.json` (conforms to `model_metrics.schema.yaml`). Log seed and splitter to `data/logs/training.log`; enforce CPU‑only via runtime GPU detection (FR‑008).  
  **Verification**: `code/tests/test_metrics_schema.py` (added in T004a) validates the JSON; three model configurations × two learners present with real scores.

- [ ] T004a [P] **Create metrics‑schema contract test** — Add `code/tests/test_metrics_schema.py` that validates `model_performance.json` against `model_metrics.schema.yaml`.  
  **Verification**: `pytest code/tests/test_metrics_schema.py` passes.

## Phase 2: Complete the study and validate its evidence

- [ ] T005r [US1] **Sensitivity‑sweep vectorisations** — Extend `code/02_tda_computation.py` with a `--grid` argument to also generate `persistence_images_20x20.csv` (400 columns) and `persistence_images_30x30.csv` (900 columns) using σ=0.1.  
  **Verification**: Files exist, molecule IDs align, no NaNs.

- [ ] T006r [US3] **Sensitivity analysis execution** — `code/05_sensitivity_analysis.py` retrains models on the 20×20 and 30×30 topological sets using the same splits, reports R² across resolutions {10,20,30} and coefficient of variation in `reports/metrics/sensitivity_analysis.json`.  
  **Verification**: JSON contains real metrics; CV computed from distinct runs.

- [ ] T007r [US3] **Statistical comparison (Holm‑Bonferroni)** — Perform paired t‑tests (or Wilcoxon) on per‑fold R² between combined vs. traditional models, apply Holm‑Bonferroni correction, write corrected p‑values and methodology block to `reports/metrics/diagnostics_holm.json`.  
  **Verification**: `code/tests/test_correction.py` validates Holm implementation.

- [ ] T007c [US3] **Statistical comparison (plain Bonferroni)** — Duplicate the above comparison using the plain Bonferroni correction as mandated by FR‑005, write results to `reports/metrics/diagnostics_bonferroni.json` and document the deviation in the methodology section.  
  **Verification**: Both correction files exist; unit test ensures Bonferroni logic.

- [ ] T007s [US3] **Family‑wise error rate measurement** — Using the corrected p‑values from T007r/T007c, count the number of hypotheses rejected at α=0.05, compute the empirical FWER bound, and write a summary to `reports/metrics/fwer_report.json` with fields `alpha`, `rejections`, `fwer_bound`.  
  **Verification**: JSON present; values derived from actual p‑values.

- [ ] T008vif [US3] **VIF diagnostics** — Compute Variance Inflation Factor on `combined_features.csv` via `statsmodels`, flag predictors with VIF > 5, and write `reports/diagnostics/vif_report.json`.  
  **Verification**: JSON contains VIF for each predictor and a list of flagged ones.

- [ ] T008mi [US3] **Mutual information diagnostics** — Compute mutual information between traditional and topological feature sets via `sklearn.feature_selection.mutual_info_regression`, write summary statistics to `reports/diagnostics/mi_report.json`.  
  **Verification**: JSON includes MI value and interpretation note.

- [ ] T008bonf [US3] **Bonferroni‑adjusted p‑value field** — Add the field `bonferroni_adjusted_p` to `reports/metrics/model_performance.json` (as required by the data model) using the values from T007c.  
  **Verification**: JSON schema now includes the new field.

- [ ] T009c [P] **Unit tests for core utilities** — Add `code/tests/test_graph_builder.py` and `code/tests/test_persistence_utils.py` covering valid, disconnected, and invalid SMILES, and empty diagram handling.  
  **Verification**: `pytest code/tests/` passes.

- [ ] T009r [P] **Resource‑monitor wrapper** — Run the full pipeline under `code/07_resource_monitor.py`, record peak RAM and CPU time in `reports/metrics/resource_usage.json`, ensuring < 6.3 GB RAM and < 5.4 h runtime (SC‑004).  
  **Verification**: Resource JSON present; values within limits.

- [ ] T010r [US1/US2/US3] **Result tables and figures** — Generate figures (Betti curves, persistence‑image examples, per‑fold R²/RMSE plots, sensitivity sweep plot) under `reports/figures/`; create `reports/metrics/summary_table.csv` joining model performance, corrected p‑values, VIF flags, and MI.  
  **Verification**: All files exist; scripts read only previously generated artifacts.

- [ ] T011r **Methods/results quickstart documentation** — Update `specs/001-predicting-molecular-properties-from-top/quickstart.md` with the exact command sequence, fixed seed 42, and references to all generated artifacts. Remove the [P] tag (now a regular documentation task) and note that it must run after T010r for content completeness.  
  **Verification**: Quickstart file exists; all referenced paths are valid.

- [ ] T012r **Full re‑run and paper‑stage handoff** — Re‑run the documented workflow from raw data checksum‑verified state, confirm all tests pass, and write the handoff section in `quickstart.md` naming the exact result files the paper stage must consume.  
  **Verification**: Fresh run exits 0; `pytest` passes; handoff section present.

- [ ] T013r [P] **Spec amendment for scope reduction** — Create `specs/001-predicting-molecular-properties-from-top/spec_amendment_scope_reduction.md` documenting the decision to limit the study to the single property `logP` from ESOL, citing resource constraints and power‑analysis outcome, and updating FR‑005/SC‑003 references to N = 1.  
  **Verification**: Amendment file exists; downstream reviewer confirms spec updated.

## Dependencies and requirement coverage (updated)

| Requirement | Task(s) | Demonstrating command |
|---|---|---|
| FR-001 (shortest‑path PH) | T002 | `python code/02_tda_computation.py` |
| FR-002 (10×10 baseline) | T002 | contract test on `persistence_images_10x10.csv` |
| FR-003/FR-004 (models, scaffold CV, seed 42) | T004 | `python code/04_model_training.py`; `pytest code/tests/test_metrics_schema.py` |
| FR-005 (Bonferroni) | T007c | `reports/metrics/diagnostics_bonferroni.json` |
| FR-006 (resolution sweep) | T005r, T006r | `reports/metrics/sensitivity_analysis.json` |
| FR-007 (VIF) | T008vif | `reports/diagnostics/vif_report.json` |
| FR-008 (CPU‑only) | T004, T009r | GPU check in training entry; resource run |
| FR-009 (mutual information) | T008mi | `reports/diagnostics/mi_report.json` |
| SC‑001–SC‑005 | T004, T006r, T007s, T008vif, T009r | respective JSON artifacts |
| Checksum verification (data/checksums.txt) | T001b | `cat data/checksums.txt` |
| Spec amendment for scope reduction | T013r | Presence of `spec_amendment_scope_reduction.md` |
| (others as in original table) |  |  |

Execution order (updated): T000 → T000a → T001a → T001b → T001c → T001d → T001e → T001f → T002 → T002a → T003 → T004 → T004a → T005r → {T006r, T007r, T007c, T007s, T008vif, T008mi, T008bonf} → T009c → T009r → T010r → T011r → T012r → T013r.
