# Tasks: Predicting the Yield Strength of High-Entropy Alloys

**Inputs**: `spec.md`, `plan.md`, existing artifacts, JSON-schema contracts in `specs/001-predicting-the-yield-strength-of-high-en/contracts/`.
**Goal**: Smallest complete study answering the research question — a composition-only Random Forest predictor of single-phase HEA yield strength, validated on a held-out test set and an independent external set, with full statistical rigor (power analysis, VIF, permutation importance with Holm–Bonferroni correction, three-seed stability) and a provenance-tracked report.

**Data source note**: The spec's Zenodo URLs are blank placeholders; the plan names the Materials Project REST API as the canonical source. All data tasks therefore use the real `mp_api` package (package-based fetch) with a required `MP_API_KEY` environment variable. Loaders FAIL LOUDLY on any fetch/validation error — no synthetic fallback, ever. If the primary query returns too few experimental yield-strength records to support the power analysis, the pipeline aborts and reports the exact mismatch for scope revision rather than fabricating data.

---

## Phase 1: Setup and first end-to-end analysis

- [ ] T001 [P1] [US-1] Implement the real data acquisition module `code/data/fetch_heas.py` that queries the Materials Project REST API via the `mp_api` package (requires `MP_API_KEY` env var) for single-phase HEA entries with experimentally measured yield strength, and writes raw records to `data/raw/heas_raw.jsonl` (one JSON object per line: `alloy_id`, `composition`, `yield_strength` in MPa, plus phase/temperature metadata).
  - Implementation: use `mp_api.client.MPRester`; normalize yield strength to MPa; filter to single-phase, room-temperature entries; abort with a clear error (FR-009) if any record lacks required fields — no try/except fallback to synthetic data.
  - Verification: `data/raw/heas_raw.jsonl` exists, is non-empty, every line validates against `contracts/dataset.schema.yaml`, and record count is logged. A unit test in `code/tests/test_fetch.py` confirms the loader raises on a record missing `yield_strength`.

- [ ] T002 [P1] [US-1] Implement the deterministic descriptor calculator `code/data/descriptors.py` computing the five composition-only descriptors — `mixing_entropy`, `atomic_size_mismatch` (δ), `electronegativity_variance` (Δχ), `vec`, `tm_variance` — from a frozen elemental-property reference table `data/raw/elemental_properties.csv` (element, atomic_radius, electronegativity, valence_electrons, melting_point; validate each row against `contracts/elemental_properties.schema.yaml`).
  - Implementation: pure functions, no randomness; unit tests in `code/tests/test_descriptors.py` check known values (e.g., equiatomic CoCrFeMnNi: mixing entropy = 1.369 J/mol/K, VEC = 8.0) to 3 decimals.
  - Verification: `pytest code/tests/test_descriptors.py` passes; descriptor functions raise `KeyError` with a clear message for an element absent from the reference table.

- [ ] T003 [P1] [US-1] Build the processed dataset and run a thin end-to-end analysis: `code/data/build_dataset.py` loads `data/raw/heas_raw.jsonl`, computes descriptors via T002, and writes `data/processed/hea_descriptors.csv` (columns: `alloy_id`, `composition`, the five descriptors, `yield_strength`), validated row-wise against `contracts/descriptor.schema.yaml` and `contracts/hea_schema.schema.yaml`. Then `code/models/train_quick.py` performs a fixed-seed (42) 80/20 split, trains a small RandomForestRegressor (`n_estimators=100`), and writes real held-out R², Pearson r, and p-value to `data/results/quick_metrics.json`.
  - Verification: `data/processed/hea_descriptors.csv` exists with ≥ 1 row per real alloy and all descriptor columns populated; `data/results/quick_metrics.json` contains real computed numbers (no placeholders); the documented command in `quickstart.md` executes end-to-end.

**Checkpoint**: The documented command runs on real Materials Project data and produces checkable numerical outputs. No report writing from expected or invented results.

## Phase 2: Complete the study and validate its evidence

- [ ] T004 [US-1] Perform the statistical power analysis (FR-015, FR-022, SC-009) in `code/analysis/power.py`: target power ≥ 0.80, α = 0.05, effect size derived from R² ≥ 0.6 (Cohen's f² = 1.5) using `statsmodels.stats.power.FTestPower`. Write required minimum N and achieved power to `data/results/power_analysis.json`. Abort with an informative error if actual N < required N — do not proceed on an underpowered dataset (FR-023).
  - Verification: `data/results/power_analysis.json` exists with numeric `required_n` and `achieved_power`; pipeline aborts (non-zero exit, clear message) when N is insufficient.

- [ ] T005 [US-1] Implement the full train/test pipeline `code/models/train_full.py`: fixed-seed 42, 80/20 split into `data/processed/train.parquet` / `data/processed/test.parquet` (schema `contracts/processed_data.schema.yaml`); compute VIF on the training descriptors (statsmodels), drop any descriptor with VIF > 5, record values and removals in `data/results/vif_summary.json` (FR-016, SC-010); train RandomForestRegressor (`n_estimators=500`, `max_features='sqrt'`) with 5-fold CV hyperparameter grid search on the cleaned training matrix; persist the model to `data/results/model_rf.joblib` and CV scores to `data/results/cv_metrics.json` (FR-003).
  - Verification: no descriptor with VIF > 5 remains in the final feature set (asserted in code); `data/results/model_rf.joblib` and `data/results/cv_metrics.json` exist; rerunning with the same seed reproduces identical CV scores.

- [ ] T006 [US-1] Evaluate on the held-out test set and compute descriptor–target correlations: `code/analysis/evaluate.py` predicts on the test set, computes R², Pearson r, two-tailed p-value, MAE, RMSE, and 95% bootstrap confidence intervals (1000 resamples, seeded), writing `data/results/metrics.json` validated against `contracts/metrics.schema.yaml` (FR-004, SC-001–SC-003). In the same module, compute Pearson r and two-tailed p for each descriptor using **training data only**, flag those with |r| > 0.5 and p < 0.01, and write `data/results/descriptor_correlation.json` (FR-014, SC-007).
  - Verification: `data/results/metrics.json` validates against the schema and contains real measured values; `data/results/descriptor_correlation.json` reports per-descriptor r, p, and a boolean flag; success-threshold checks (R² ≥ 0.6, |r| ≥ 0.5, p < 0.05) are reported as pass/fail without weakening thresholds.

- [ ] T007 [US-1] Compute permutation importance with significance testing: `code/analysis/importance.py` runs `sklearn.inspection.permutation_importance` with ≥ 1000 permutations per feature on the held-out test set (FR-005), performs a non-parametric permutation test per feature, applies Holm–Bonferroni correction (α = 0.05), and writes `data/results/perm_importance.json` validated against `contracts/importance.schema.yaml` (FR-006, SC-003).
  - Verification: every feature record has `importance_score`, `raw_p_value`, `holm_bonferroni_p`; features with corrected p < 0.05 are flagged; a unit test in `code/tests/test_importance.py` verifies the Holm–Bonferroni implementation against a hand-computed example.

- [ ] T008 [US-1] Obtain and evaluate the independent external validation set: `code/data/fetch_external.py` performs a second Materials Project query with a disjoint filter (different date range / distinct entry set) to produce `data/external/validation.jsonl`, validated against `contracts/dataset.schema.yaml` (FR-017). Compute descriptors via T002, run inference with the trained model, and write R², |r|, p-value to `data/results/external_metrics.json` (schema `contracts/metrics.schema.yaml`). Document measurement-protocol and processing-condition differences between primary and external datasets, noting confounds, in `data/results/external_provenance.md` (FR-023, FR-024, SC-008).
  - Verification: external set shares no `alloy_id` with the training/test data (asserted); `data/results/external_metrics.json` validates against the schema; the provenance document states comparability limitations honestly.

- [ ] T009 [US-1] Run the stability assessment: `code/analysis/stability.py` executes the full train/evaluate/importance pipeline three times with seeds [111, 222, 333], records the top-5 feature rankings per run in `data/results/stability_rankings.json`, computes the maximum rank difference across runs, and reports whether it is ≤ 1 (FR-021, SC-006). Do not relax the ≤ 1 threshold; if it fails, record the actual maximum difference and the honest failure in the results file.
  - Verification: `data/results/stability_rankings.json` contains three ranked lists and a computed `max_rank_difference`; all three runs use the same real dataset.

- [ ] T010 [US-1] Add independent correctness, sensitivity, and runtime checks: `code/tests/test_pipeline.py` covers (a) schema validation of every artifact against its contract (`dataset`, `descriptor`, `metrics`, `importance`, `manifest`), (b) a sensitivity check varying the test-split fraction (e.g., 0.15/0.20/0.25) recording metric variation in `data/results/sensitivity_analysis.json`, and (c) a runtime assertion that the full pipeline completes within the free-runner budget (≤ 6 h, ≤ 7 GB RAM), recording wall-clock time and peak memory in `data/results/runtime.json`.
  - Verification: `pytest code/tests/` passes; `data/results/sensitivity_analysis.json` and `data/results/runtime.json` contain real measured values; any schema violation fails the test suite loudly.

- [ ] T011 [US-1] Generate the specified tables and figures directly from validated outputs: `code/reporting/figures.py` produces (a) predicted-vs-measured scatter with the 1:1 line and bootstrap CI band (`figures/pred_vs_meas.png`), (b) descriptor–target correlation bar chart with p-value annotations (`figures/descriptor_corr.png`), and (c) permutation-importance ranking with corrected p-value markers (`figures/perm_importance.png`). Each figure is generated from the JSON artifacts of T006–T008, never from hard-coded values.
  - Verification: all three figure files exist and are non-empty; regenerating from unchanged inputs produces byte-identical files (seeded, deterministic).

## Phase 3: Reproducible results and paper handoff

- [ ] T012 [US-1] Assemble the provenance-tracked report and manifest: `code/reporting/report.py` generates `paper/report.md` with all required sections — dataset statistics, power-analysis justification, VIF summary, model performance with CIs, descriptor–target correlations (training only), permutation importance with Holm–Bonferroni p-values, external-validation metrics and protocol documentation, stability assessment, and provenance log (FR-008, SC-004). Every numeric value is emitted programmatically with a provenance ID (e.g., `[PV-metrics-r2]`) linked in `data/results/provenance_linking.json` to its source artifact and generating code block (FR-010, FR-024, SC-011). Write `data/results/manifest.json` (run_id, timestamp, seeds, package versions, SHA-256 checksums of all inputs/outputs) validated against `contracts/manifest.schema.yaml`.
  - Verification: `paper/report.md` contains all nine required sections (regex check in `code/tests/test_report.py`); every number in the report has an entry in `data/results/provenance_linking.json`; `data/results/manifest.json` validates against its schema and checksums match the actual files.

- [ ] T013 [US-1] Re-run the documented workflow end-to-end from its declared inputs and verify all success criteria: `code/verify_success_criteria.py` parses every artifact under `data/results/` and writes `data/results/verification_report.json` with pass/fail for SC-001 through SC-011, reporting failures honestly (e.g., if R² < 0.6 on real data, the report states the actual value and the negative finding). Update `quickstart.md` with the exact runnable commands and expected outputs, and write `data/results/final_handoff.json` (artifact paths, manifest hashes, pointer to `paper/report.md`) for the paper stage — paper layout, PDF compilation, and publication remain with the downstream paper pipeline.
  - Verification: a clean re-run from `data/raw/` reproduces all artifacts with identical checksums (seeded); `data/results/verification_report.json` exists with an entry for every SC; `quickstart.md` documents Prerequisites, Quick Start, and Expected Output sections.

---

## Dependencies and requirement coverage

| Requirement | Task(s) | Demonstrating command |
|---|---|---|
| FR-001 (data acquisition) | T001 | `python -m code.data.fetch_heas` |
| FR-002 (descriptors) | T002, T003 | `pytest code/tests/test_descriptors.py` |
| FR-003 (model training) | T005 | `python -m code.models.train_full` |
| FR-004 (test evaluation) | T006 | `python -m code.analysis.evaluate` |
| FR-005/FR-006 (permutation importance) | T007 | `python -m code.analysis.importance` |
| FR-008/FR-010/FR-024 (report, provenance) | T012 | `python -m code.reporting.report` |
| FR-009 (missing-field abort) | T001, T002 | `pytest code/tests/test_fetch.py` |
| FR-014 (descriptor correlations) | T006 | `data/results/descriptor_correlation.json` |
| FR-015/FR-022/FR-023 (power analysis) | T004 | `python -m code.analysis.power` |
| FR-016 (VIF) | T005 | `data/results/vif_summary.json` |
| FR-017 (external validation) | T008 | `data/results/external_metrics.json` |
| FR-018 (contract validation) | T010, T012 | `pytest code/tests/test_pipeline.py` |
| FR-021 (stability) | T009 | `data/results/stability_rankings.json` |
| SC-001–SC-011 | T013 | `python -m code.verify_success_criteria` |

**Execution order**: T001 → T002 → T003 (first end-to-end result) → T004 → T005 → T006 → T007 → T008 → T009 → T010 → T011 → T012 → T013. T008 depends on the model from T005; T009 depends on the full pipeline of T005–T007; all verification tasks (T010, T013) follow their prerequisites.

## Revision behavior

The previously rejected tasks T008, T060, and T200 (missing `data/raw/heas_raw.csv` and `data/processed/hea_descriptors.csv`) are superseded by T001 and T003 above, which specify the real Materials Project fetch (per plan.md, since the spec's Zenodo URLs are blank), fail-loudly validation, and the concrete artifact paths. Scaffolding, logging-setup, checksum-utility, README-sync, and CI-only tasks from the prior list are folded into the tasks that need them (the platform supplies `llmxive_toolkit` paths/logging; checksums are recorded in T012's manifest). No scientific requirement was dropped: every FR and SC in the active spec maps to at least one task above.
