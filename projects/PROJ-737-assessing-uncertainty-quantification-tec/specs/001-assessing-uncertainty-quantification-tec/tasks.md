# Tasks: Assessing Uncertainty Quantification Techniques for Materials Property Predictions

**Inputs**: `specs/001-assessing-uncertainty-quantification-tec/spec.md`, `plan.md`, `data-model.md`, `contracts/`

This checklist implements the smallest complete, reproducible study satisfying all functional, non-functional, and success-criteria requirements. The four UQ methods are named explicitly (GPR, MC-Dropout, Deep Ensemble, Split-Conformal) — resolving the reviewer's concern that the spec never named the techniques under comparison — and Formation Energy is documented throughout as the qualified proxy for Elastic Modulus per the spec amendment, with the construct-validity caveat carried into the results account. T002 and T003 are reopened for redo: the previous T002 artifacts contained seaborn example data (Iris/Tips/Planets) rather than real materials datasets, and T003's pipeline exited 1.

---

## Phase 1 — Setup and first end-to-end analysis

- [ ] T001 [US1] **Establish code layout, quickstart command, and verify the per-sample schema**
  - Document a runnable command (`python -m code.main`) in `specs/001-assessing-uncertainty-quantification-tec/quickstart.md`, including: the four named UQ methods (GPR, MC-Dropout, Deep Ensemble, Split-Conformal), the uniform 2000-sample training cap, the deterministic sampling rule (fixed seed 42, first-N rows per plan), the rationale for paired Wilcoxon tests, and the qualified note that Formation Energy substitutes for Elastic Modulus (construct-validity caveat: thermodynamic stability vs. mechanical stiffness).
  - Verify `specs/001-assessing-uncertainty-quantification-tec/contracts/per_sample_errors.schema.yaml` contains exactly the columns `sample_id, dataset, method, prediction, lower_bound, upper_bound, ground_truth, abs_error`.
  - **Verification** (from the project root): a short Python check loads the schema YAML, asserts the column set matches, and exits with status 0. Directory creation is not a task — `llmxive_toolkit.paths` creates output folders on demand.

- [ ] T002 [US1] **Download the three real materials datasets via package-based fetches (REDO — previous artifacts contained seaborn example data, not materials datasets)**
  - Implement `code/download.py` fetching REAL materials datasets through `matminer.datasets.load_dataset` (installable package, no guessed raw URLs, no seaborn example data):
    1. **Band Gap** — `load_dataset("matbench_expt_gap")` (experimental band gaps, composition-based) → `data/raw/band_gap.csv`
    2. **Formation Energy** — `load_dataset("matbench_mp_e_form")` (MP formation energies) → `data/raw/formation_energy.csv`
    3. **Thermal Conductivity** — `load_dataset("boltztrap_mp")` (BoltzTraP thermal/electronic transport on MP compounds) → `data/raw/thermal_conductivity.csv`
  - The loader must FAIL LOUDLY: on any fetch error, raise — never fall back to synthetic, mock, seaborn-example, or randomly generated data. No `try/except` that substitutes placeholder CSVs. A failed fetch must abort the run, not substitute stand-in data.
  - After each download, compute the SHA-256 checksum of the written CSV and write `data/raw/<dataset_id>_metadata.json` with `dataset_id`, `source_url` (the matminer dataset name/registry URL — must reference the actual materials dataset, not an unrelated URL), `property_name`, `n_samples_original`, `n_samples_used`, `checksum`.
  - Cap each dataset at 5000 rows deterministically (fixed seed 42, first-N via `itertools.islice` or seeded sample); record the cap in the metadata.
  - **Verification**: `code/tests/test_download.py` loads each metadata JSON, asserts the CSV exists, the checksum matches, `n_samples_used ≤ 5000`, the `source_url`/dataset name refers to the correct materials dataset (explicitly rejecting Iris/Tips/Planets or any seaborn example set), and the CSV contains a composition column and a numeric target column with ≥ 100 non-null rows. Exit status 0.

- [ ] T003 [US1] **Featurize, split, and run a thin end-to-end analysis on a 100-sample subset (REDO — previous run exited 1)**
  - Implement `code/featurize.py`: convert compositions to feature vectors with `matminer` featurizers (fallback to elemental-fraction vectors via `pymatgen` if a featurizer fails — the fallback is a different REAL featurization, not synthetic data). Write `data/processed/<dataset_id>.csv`.
  - Perform a stratified 70/15/15 train/val/test split by target-property range (FR-003); save split indices in `data/processed/<dataset_id>_split.json`.
  - Implement the four UQ methods in `code/models/` — `gpr.py` (sklearn GPR, ≤ 2000 training points), `mc_dropout.py` (torch MLP ≤ 2M params, 50 stochastic passes, `device="cpu"`), `deep_ensemble.py` (ensemble of 3 MLPs, distinct seeds), `conformal.py` (XGBoost + split-conformal calibration hold-out) — each returning point predictions and lower/upper bounds on the test set. Debug the previous exit-1 failure: no step may silently swallow an exception; errors must propagate with a clear traceback so the run either succeeds on real data or fails loudly.
  - Run the thin pipeline on the first 100 rows per dataset: train all four methods, write per-sample rows to `data/results/per_sample_errors.csv` with columns exactly `sample_id, dataset, method, prediction, lower_bound, upper_bound, ground_truth, abs_error`, and write `data/results/pipeline_run.json` conforming to `contracts/pipeline.schema.yaml`.
  - **Verification**: `code/tests/test_thin_pipeline.py` validates `per_sample_errors.csv` against the per-sample schema, validates `pipeline_run.json` against `contracts/pipeline.schema.yaml`, and asserts all four methods produced rows for each dataset subset. The command `python -m code.main --thin` must exit with status 0.

## Phase 2 — Complete the study and validate its evidence

- [ ] T004 [US1] **Full-scale pipeline on all three capped datasets with uniform 2000-sample training cap**
  - Extend `code/pipeline.py` to run download → featurize → split → train all four UQ methods on the full capped datasets (≤ 5000 rows, uniform training cap of 2000 examples for all methods to avoid confounding). Enforce ≥ 200 test samples per dataset (power analysis) and stratified splits.
  - Persist per-sample predictions for all dataset × method combinations in the single `data/results/per_sample_errors.csv` (schema columns exactly as above).
  - Write the UQMethod registry `data/results/uq_methods.csv` with columns `method_id, baseline_model, hyperparams, n_iterations, status, error_msg` (data-model entity), and the pipeline execution log `data/results/pipeline_log.csv` conforming to `contracts/pipeline.schema.yaml` (run_id, timestamp, status, steps, memory_peak_mb, total_duration_seconds).
  - Record cost metrics per run in `data/results/cost_metrics.csv` with columns `dataset_id, method_id, train_time_s, inference_time_s, peak_ram_mb`.
  - Handle method-level failures gracefully (NFR-002): a failed method is recorded in `uq_methods.csv` with `status=failed` and its `error_msg`; remaining methods' results are still saved (partial_success), but dataset-level fetch failures abort (fail-loudly, per T002).
  - **Verification**: `code/tests/test_full_pipeline.py` validates the CSVs against their contracts, asserts every method–dataset combination is present, and asserts n_test ≥ 200 per dataset. Exit 0.

- [ ] T005 [US2] **Compute calibration error, sharpness, and coverage metrics**
  - Implement `code/metrics/evaluation.py` reading `data/results/per_sample_errors.csv` and computing per dataset–method pair: Calibration Error (standard binned ECE over prediction intervals), Sharpness (mean interval width `U − L`), and Coverage Error (`|empirical − nominal|`).
  - Write `data/results/metrics_raw.csv` conforming to `contracts/metrics.schema.yaml` with columns `dataset_id, method_id, metric_type, value, nominal_coverage, timestamp` (ISO-8601 timestamps).
  - **Verification**: `code/tests/test_metrics.py` validates schema compliance, asserts all four methods × three datasets are covered, and that timestamps parse as ISO-8601. Exit 0.

- [ ] T006 [US3] **Paired Wilcoxon signed-rank significance testing with Bonferroni correction**
  - Implement `code/stats/significance.py`: for each dataset, generate all 6 unique method pairs and run paired Wilcoxon signed-rank tests on per-sample errors (same test set, paired design — FR-004; no independent-sample t-tests or ANOVA anywhere).
  - Apply Bonferroni correction across all method-pair × dataset combinations (18 tests; adjusted α ≈ 0.00278). Report rank-biserial effect sizes with bootstrap 95% confidence intervals.
  - Write `data/results/statistical_report.csv` conforming to `contracts/stats.schema.yaml` with fields `dataset_id, method_a, method_b, metric_type, p_value, test_type ("wilcoxon_signed_rank"), significant, alpha, correction ("bonferroni")`.
  - **Verification**: `code/tests/test_statistics.py` validates the CSV against the schema, asserts `test_type` is only `wilcoxon_signed_rank`, and that the `significant` flag uses the Bonferroni-adjusted α. Exit 0.

- [ ] T007 [US3] **Conformal coverage sensitivity sweep and trade-off figure**
  - Sweep nominal coverage from 0.80 to 0.99 in steps of exactly 0.01 (SC-004) for the split-conformal method (and interval-producing equivalents for the other methods where applicable). For each level compute empirical coverage and average interval width.
  - Write `data/results/sensitivity_report.csv` with columns `dataset_id, method_id, nominal_coverage, empirical_coverage, avg_interval_width`.
  - Generate `figures/sensitivity_tradeoff.png` (coverage vs. interval width, faceted by method and dataset) with `matplotlib`.
  - **Verification**: `code/tests/test_sensitivity.py` asserts the set of `nominal_coverage` values equals `{0.80, 0.81, …, 0.99}`, validates numeric ranges, and opens the PNG. Exit 0.

- [ ] T008 [US1] **Model-constraint enforcement and performance monitoring**
  - Wrap the full pipeline with a `psutil` resource monitor recording total wall-clock time and peak memory; assert `total_duration_seconds < 3600` and `memory_peak_mb ≤ 2000` (NFR-001) and write `data/results/performance_log.json`.
  - After each training run, assert: Deep Ensemble ≤ 3 sub-models, MC-Dropout ≤ 200 passes, all torch models on `device="cpu"`, no quantization (FR-002). Log any violation to `data/results/model_constraints.log` and abort on limit breach.
  - Validate every generated CSV (per-sample, metrics, statistical, cost, sensitivity, uq_methods, pipeline_log) against its contract; abort on violation with details in `data/results/schema_validation.log`.
  - **Verification**: `code/tests/test_all_validations.py` runs these checks end-to-end; exit 0.

- [ ] T009 [US1] **Reproducibility smoke test with fixed seeds**
  - Ensure all stochastic processes use fixed seeds (`np.random.seed`, `torch.manual_seed`, seeded splits) — NFR-003.
  - Add `code/tests/smoke_test.py` that re-runs the thin pipeline and asserts all metric values in `data/results/metrics_raw.csv` match a stored reference `code/tests/reference/metrics_raw_ref.csv` within 1e-8.
  - **Verification**: the smoke test exits with status 0; any mismatch raises `AssertionError`.

- [ ] T010 [US1] **Summary tables and reliability diagrams**
  - Implement `code/visualize_summary.py` aggregating calibration error, sharpness, and cost metrics into `data/results/summary.csv` with columns `dataset_id, method_id, calibration_error, sharpness, train_time_s, inference_time_s, peak_ram_mb`.
  - Implement `code/visualize_reliability.py` producing `figures/reliability_diagrams.png` (one panel per dataset, all four methods overlaid).
  - **Verification**: `code/tests/test_visualization.py` validates `summary.csv` column names/types and asserts both PNG files exist and are readable. Exit 0.

## Phase 3 — Reproducible results and paper handoff

- [ ] T011 [US1] **Methods/results account and paper-stage handoff**
  - Write a concise methods and results account in `specs/001-assessing-uncertainty-quantification-tec/quickstart.md` linked to the actual output rows in `data/results/` and figure files: which of the four named UQ methods (GPR, MC-Dropout, Deep Ensemble, Split-Conformal) achieved lowest calibration error and sharpest intervals per dataset, significance outcomes after Bonferroni, and honest reporting of any null results or partial failures (NFR-002 partial results).
  - Explicitly state the construct-validity limitation: Formation Energy is a proxy for Elastic Modulus (thermodynamic stability vs. mechanical stiffness), so conclusions about elastic-property UQ performance are qualitative; two of the three datasets share an electronic/thermodynamic character, narrowing the physical-diversity claim of the original question.
  - Document the paper-stage handoff: exact commands (`python -m code.main`, `python -m code.main --thin`), locations of all CSVs and figures required for the manuscript, and the pinned `requirements.txt`. Paper layout, PDF compilation, and publication belong to the paper pipeline.
  - **Verification**: `code/tests/test_handoff.py` asserts every artifact path referenced in the handoff exists and that the documented commands parse. Exit 0.

- [ ] T012 [US1] **Final end-to-end verification**
  - Execute the full pipeline (`python -m code.main`) from its declared inputs, then run `code/tests/test_all_validations.py` and the integration test `code/tests/test_full_pipeline.py` confirming: all required CSVs and figures exist and pass schema validation; model-constraint and performance limits hold; the reproducibility smoke test passes.
  - **Verification**: the full command sequence exits with status 0 and prints `READY`; the project is then ready for the next `/speckit.analyze` run.

---

## Dependencies and requirement coverage

- **FR-001 (real datasets)**: T002 (matminer package fetches: matbench_expt_gap, matbench_mp_e_form, boltztrap_mp; fail-loudly, no synthetic or seaborn-example fallback).
- **FR-002 (model constraints)**: T003, T004, T008 (CPU-only, ≤ 2M params, ensemble ≤ 3, MC passes ≤ 200, no quantization).
- **FR-003 (featurization, caps, stratified splits)**: T002, T003.
- **FR-004 (paired Wilcoxon)**: T006; no t-test/ANOVA anywhere.
- **FR-005 / SC-002 (output CSVs with schemas)**: T003–T005, T007, T010.
- **SC-001 (pipeline execution)**: T003, T004, T012.
- **SC-003 (significance)**: T006.
- **SC-004 (sensitivity sweep 0.80–0.99, step 0.01)**: T007.
- **SC-005 (three datasets)**: T002, T004.
- **NFR-001 (time/memory)**: T008. **NFR-002 (graceful partial results)**: T004 (uq_methods status/error_msg). **NFR-003 (seeds, pinned deps)**: T009, T011.
- **US1/US2/US3**: T003–T004 / T005 / T006–T007.

Execution order: T001 → T002 → T003 (thin end-to-end) → T004 → T005 → T006 → T007 → T008 → T009 → T010 → T011 → T012. T006 and T007 depend on T004/T005 outputs; T009 depends on T005; T012 depends on all prior tasks.

## Revision behavior

T002 and T003 were rejected by the independent verifier (T002 downloaded seaborn example data instead of the real materials datasets; T003's pipeline exited 1) and are reopened above with package-based real-data fetches, an explicit rejection of seaborn example sets in the verification step, and a fail-loudly, no-silent-exception requirement in the thin pipeline. Reviewer feedback on the spec's method-naming and the Formation Energy proxy is addressed by naming the four UQ methods explicitly in T001/T003/T011 and by carrying the construct-validity qualification (including the narrowed physical-diversity claim) through T002 and T011. All other tasks remain pending; no completed artifacts are erased.
