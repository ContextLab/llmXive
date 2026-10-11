# Tasks: Assessing Uncertainty Quantification Techniques for Materials Property Predictions

**Input**: `specs/001-assessing-uncertainty-quantification-tec/spec.md`, `plan.md`, `data-model.md`, `contracts/`
**Re-plan note**: Updated to resolve all panel concerns, added per‑technique cost recording, cost‑metric significance testing, requirements‑pinning verification, integration test, entry‑point script, and aligned path layout with plan.

## Task format

`- [ ] T### [P?] [USx?] description with exact artifact paths`. Paths are relative to the project directory. `[P]` = independent tasks (no data dependencies).

## Phase 1: Setup and first end‑to‑end analysis

- [X] T001 [US1] Verify project skeleton and data contracts. Ensure directories `data/raw/`, `data/processed/`, `data/results/`, `figures/`, `code/models/`, `code/metrics/`, `code/stats/`, `code/utils/`, `tests/unit/`, `tests/integration/` exist. Define `per_sample_errors.schema.yaml` under `specs/.../contracts/` with columns `sample_id, dataset, method, prediction, lower_bound, upper_bound, ground_truth, abs_error`. Verify that `spec.md` SC‑005 already lists the three datasets; no modification required.

- [ ] T002 [US1] Implement `code/download.py` to fetch the three REAL datasets (OQMD band‑gap, OQMD formation‑energy, AFLOW thermal‑conductivity) and write them to `data/raw/` with SHA256 checksum manifest. The loader must FAIL LOUDLY on any fetch error. No synthetic fallback. Cap each dataset at **5,000** samples (fixed seed 42) and record this cap in the generated metadata file `data/raw/<dataset>_metadata.json`. **Spec amendment**: note that the original fallback clause in Assumptions is overridden by this strict‑fail policy. <!-- FAILED-IN-EXECUTION: code/download.py exit=1 -->

- [ ] T003 [US1] Run a thin end‑to‑end analysis on a 100‑sample subset: featurize using matminer (fallback to pymatgen), stratified 70/15/15 split, train baseline XGBoost and the four UQ methods (GPR, MC Dropout ≤200 passes, Deep Ensemble of 3, Split‑Conformal). Write per‑sample predictions to `data/results/per_sample_errors.csv` conforming to the schema. Record pipeline execution log `data/results/pipeline_run.json` (overall status, memory_peak_mb, total_duration_seconds). <!-- FAILED-IN-EXECUTION: code/main.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/main.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/main.py exit=1 -->

## Phase 2: Complete study and validate evidence

- [ ] T004 [US1] Execute the full pipeline on all three datasets at the 5,000‑sample cap, fixed seeds, and record **per‑technique** cost metrics (training time, inference time, peak RAM) to `data/results/cost_metrics.csv` (columns `dataset, method, train_time_s, inference_time_s, peak_ram_mb`). Also produce the complete `data/results/per_sample_errors.csv` for all 12 dataset × method combos.

- [ ] T005 [P] [US2] Compute Calibration Error, Sharpness, and Coverage Error for every method × dataset from `per_sample_errors.csv`. Write `data/results/metrics_raw.csv` with columns matching `contracts/metrics.schema.yaml` (`dataset_id, method_id, metric_type, value, nominal_coverage, timestamp`). Use `metric_type` values `calibration_error`, `sharpness`, and `coverage_error` only.

- [ ] T006 [P] [US3] Perform paired Wilcoxon Signed‑Rank tests on per‑sample absolute errors for all 6 method pairs within each dataset. Write results as JSON Lines to `data/results/statistical_report.jsonl`, where each line conforms to `contracts/statistics.schema.yaml`. Required fields per line: `test_type` (must be `"wilcoxon_signed_rank"`), `method_pair` (array of two method IDs), `dataset_name`, `p_value`, `significant`, `alpha`, `correction`, and `metric_analyzed` (enum `"calibration_error"` or `"sharpness_cv"`). This satisfies the schema’s mandatory `metric_analyzed` field.

- [ ] T007 [P] [US3] Conduct conformal sensitivity analysis sweeping nominal coverage 0.80–0.99 (step 0.01). Write `data/results/sensitivity_report.csv` and generate figure `figures/sensitivity_tradeoff.png`.

- [ ] T008 [US1] Add reproducibility and edge‑case checks: a smoke test that re‑runs the 100‑sample pipeline and asserts identical metric values under fixed seed; an integration test that runs the full pipeline on a tiny synthetic dataset (e.g., a pandas DataFrame with 20 samples, <100 test samples) and verifies that the statistical report flags “inconclusive”. Store outcomes in `data/results/validation_checks.json`.

- [ ] T009 [US1] Generate the final summary table `results/summary.csv` (repo‑root `results/` directory) aggregating calibration error, sharpness, and cost‑metric p‑values per method × dataset. Produce reliability diagram `figures/reliability_diagrams.png`. Scripts `code/visualize_summary.py` (creates `results/summary.csv`) and `code/visualize_reliability.py` (creates `figures/reliability_diagrams.png`) perform these steps, reading only `data/results/` artifacts.

- [ ] T010 [US1] Write `specs/001-assessing-uncertainty-quantification-tec/quickstart.md` documenting the runnable command, sampling rule, dataset substitution, Wilcoxon rationale, and any skipped methods.

- [ ] T011 [US1] Re‑run the documented workflow from raw data and confirm that all artifacts (`per_sample_errors.csv`, `metrics_raw.csv`, `statistical_report.jsonl`, `sensitivity_report.csv`, `results/summary.csv`, figures) are reproduced with matching values. Record hand‑off information in `specs/.../handoff.md`.

- [ ] T012 [US3] Perform statistical significance testing on **computational‑cost metrics** (train_time_s, inference_time_s, peak_ram_mb) across UQ methods using Welch’s t‑test (allowed by `contracts/statistics.schema.yaml`). Write `data/results/cost_statistical_report.csv` conforming to `contracts/statistics.schema.yaml` (includes required `metric_analyzed` field, e.g., `"train_time"`).

- [ ] T013 [US2] Verify that `requirements.txt` exists at repository root and that every dependency is pinned to an exact version. Run `pip install -r requirements.txt` in a clean environment and assert success; record result in `data/results/requirements_check.json`.

- [ ] T014 [US1] Create `code/main.py` as a thin wrapper that imports and runs `code/pipeline.py`. Ensure the entry point works (`python code/main.py`). Verify via test in `tests/integration/test_main.py`.

- [ ] T015 [US1] Add integration test `tests/integration/test_pipeline.py` that executes the full pipeline on the 5,000‑sample capped datasets and checks that all expected result files are produced.

## Dependencies and requirement coverage

| Requirement | Task(s) |
|---|---|
| FR‑001 / SC‑005 | T001, T002, T004 |
| FR‑002 / NFR‑001 | T003, T004 |
| FR‑003 | T003 |
| FR‑004 / SC‑003 | T006, T012 |
| FR‑005 / SC‑002 | T003, T005 |
| SC‑001 | T003, T004 |
| SC‑004 | T007 |
| NFR‑002 | T003 |
| NFR‑003 | T008, T011 |
| NFR‑003 (pinned deps) | T013 |
| Constitution VI (per‑technique cost) | T004, T012 |
| Constitution VII (cost‑metric significance) | T012 |
| Plan‑structure (repo‑root results) | T009 |
| Entry point | T014 |
| Integration test | T015 |

Execution order respects data flow; parallel‑safe tasks are marked `[P]`.