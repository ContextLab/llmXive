# Tasks: Evaluating the Impact of Data Scaling on Robustness of Statistical Tests

**Inputs**: `specs/001-evaluating-data-scaling-robustness/spec.md`, `plan.md`, `data-model.md`, `contracts/`, prior `tasks.md` (preserved work below).

## Preserved completed work (verified; do not redo)

- [ ] T001–T003 Project scaffolding, pinned dependencies in `code/requirements.txt`, lint/format tooling.
- [ ] T004–T007 Configuration (`code/simulation/config.py`), seed schema/validation (`code/simulation/schema.py`, `data/config/seed_schema.json`), `inject_batch_context`, test fixtures, CPU‑only env setup (`code/utils/env.py`).
- [x] T024–T028, T034b, T046–T050 Streaming ingestion, fail‑loudly fetch, dataset verification pipeline (`data/config/datasets.yaml`, `results/real_world_ingestion_log.csv`), real‑data integrity tests.
- [x] T065, T065b, T065c, T070 `CONFIG_MATRIX`, distribution factory, parameter mapper, dynamic config loading.
- [ ] T015–T023 Scaling functions and statistical tests (including chi‑squared binning) – verified implementation exists.
- [x] T060–T062, T028a, T028b, T028d Metrics tests, Clopper‑Pearson CI, simulation loop orchestration with checkpointing and fidelity enforcement.
- [x] T033–T039, T051, T052, T056, T056b, T059, T066 US4 real‑world ingestion, sampling, pipeline reuse (`results/real_world_results.csv`), comparison report.
- [ ] T030 Error‑rate plot in `code/visualization/plots.py` – verified generation.
- [ ] T040–T044 Documentation, vectorization, parallelism, edge‑case tests, quickstart validation.

## Phase 1: Repair the artifact‑producing chain (early end‑to‑end result)

- [ ] T101 [US1] **Implement logger and seed persistence (redo of T005b)** in `code/simulation/logger.py`.
  - Implement `setup_logger`, `save_seed_config` (and confirm `inject_batch_context`) so that: `save_seed_config(batch_id, seed, config_hash)` validates via the existing `validate_seed_config` utility, appends a new key `{batch_id: {seed, timestamp, config_hash}}` to `data/config/seed_config.json` **without overwriting** existing keys (append‑only), raises `RuntimeError` on file‑lock/missing‑file errors, and returns the updated config object.
  - Verification: `pytest code/tests/unit/simulation/test_logger.py` asserting the file is created/populated, append‑only behavior on a second call, and log records contain `batch_id` and `seed`.

- [ ] T102 [US3] **Produce the real simulation results CSV (redo of T028c)** by wiring the existing loop to the writer.
  - In `code/main.py`, ensure the simulation loop (T028a) actually **CALLS** `write_simulation_results` so that a full run writes `results/simulation_results.csv` with **required** columns:
    `result_id, iteration_id, config_id, scaling_method, test_type, p_value, statistic, is_rejected, error_type, ground_truth, seed`.
  - Run a **THIN** end‑to‑end pass first (e.g., `python -m code.main --smoke`, all configs × a small iteration count such as 200) and confirm `results/simulation_results.csv` exists with ≥1 row per config and valid schema — this is the early executable result on which all Phase 2 tasks operate.
  - Verification: `pytest code/tests/unit/simulation/test_main.py` asserting file existence, schema conformity, and non‑null critical columns after the smoke run.

- [ ] T103a [US3] **Calculate error‑rate aggregation (conforms to AggregateMetrics contract)** in `code/analysis/metrics.py`.
  - Input: `results/simulation_results.csv` from T102. Filter rows where `ground_truth == "null"`.
  - Group by `config_id, scaling_method, test_type`. For each group compute:
    - `total_iterations` = count of rows,
    - `rejected_count` = count where `is_rejected` is true,
    - `empirical_error_rate` = `rejected_count / total_iterations`,
    - `confidence_interval_lower`, `confidence_interval_upper` via Clopper‑Pearson (`statsmodels.stats.proportion.proportion_confint` with `method='beta'`),
    - `nominal_alpha` = 0.05 (from config),
    - `deviation` = `empirical_error_rate - nominal_alpha`.
  - Output: write `results/aggregate_error_rate.csv` matching **exactly** the `AggregateMetrics` schema (no extra columns).
  - Verification: `pytest code/tests/unit/analysis/test_metrics.py` checking a known small dataset produces the correct CI values and that the CSV conforms to the schema.

- [ ] T103b [US3] **Calculate power aggregation (conforms to AggregateMetrics contract)** in `code/analysis/metrics.py`.
  - Same as T103a but filter rows where `ground_truth == "alternative"` and treat `rejected_count` as **power** (rejections under the alternative).
  - Output: write `results/aggregate_power.csv` with the same schema as `AggregateMetrics`.
  - Verification: analogous unit test confirming correct power calculation and CI.

- [ ] T104 [US3/US4] **Update `plan.md` for mixed‑effects framing (redo of T053b)**.
  - Edit the "Complexity Tracking" section of `plan.md` (located at `projects/PROJ-541-evaluating-the-impact-of-data-scaling-on/plan.md`) to replace the sentence:
    > "Mixed-effects model is inappropriate for synthetic data where 'dataset' is not a random variable"
    with the exact wording:
    > "Mixed-effects models are used for real‑world data with `dataset_id` as a random effect; for synthetic data `config_id` is treated as a fixed effect (experimental condition) to satisfy FR‑010."
  - Verification: the edited `plan.md` contains the replacement sentence verbatim.

## Phase 2: Complete the study and validate its evidence

- [ ] T105 [US3/US4] **Implement mixed‑effects analysis and significance report** in `code/analysis/metrics.py`.
  - `fit_mixed_effects_model`:
    * Real‑world: fit `deviation ~ scaling_method + (1 | dataset_id)` using `statsmodels` MixedLM on `results/real_world_results.csv`.
    * Synthetic: fit `deviation ~ C(config_id) + scaling_method` (fixed‑effects only). Populate `random_effects_variance = 0.0` with documented justification.
  - `analyze_mixed_effects_significance` extracts the p‑value for `scaling_method`, writes `results/mixed_effect_model.json` conforming to `MixedEffectModelOutput` (including `random_effects_variance`), and creates `results/mixed_effects_significance_report.md` with a table (`scaling_method`, `p_value`, `significant`). If `p_value >= 0.05`, the report explicitly notes **SC‑007 FAILED**.
  - Verification: unit test in `code/tests/unit/analysis/test_metrics.py` asserting JSON matches the contract and the report contains the expected flag.

- [ ] T106 [US3] **Alpha sensitivity analysis** in `code/analysis/metrics.py`.
  - `run_sensitivity_analysis(path='results/simulation_results.csv')` recomputes error rates and power for explicit alpha levels `[0.01, 0.05, 0.10]`, per scaling method and test type, using the same aggregation logic as T103a/b.
  - Output: `results/sensitivity_analysis.csv` with columns `alpha, scaling_method, test_type, error_rate, power`.
  - Verification: test confirming three alpha rows per scaling method and correct counts.

- [ ] T107 [US3] **Generate the simulation validity report** in `code/analysis/metrics.py`.
  - Reads `results/aggregate_error_rate.csv` and `results/aggregate_power.csv`, writes `results/simulation_validity_report.md` containing a table `config_id, scaling_method, measured_error_rate, theoretical_error_rate (0.05), deviation`. Flags any rows where `|deviation| > 0.005` (SC‑004) and summarises inflation under skewed/heteroscedastic conditions (SC‑005).
  - Verification: test ensuring the markdown file exists, contains the required columns, and correctly flags out‑of‑band rows.

- [ ] T108a **Run the full‑scale simulation**.
  - Execute `python -m code.main --iterations=<FR‑004 target>` respecting the time‑limit enforcement (exit code 99 on overrun). This produces the definitive `results/simulation_results.csv`.
  - Verification: post‑run script checks that row count equals `number_of_configs × target_iterations`.

- [ ] T108b **Regenerate all downstream artifacts** after the full run.
  - Sequentially run: `T103a`, `T103b`, `T106`, `T107`, `T030` (error‑rate plot) and verify that each output file’s modification timestamp is newer than the full‑run CSV and that row counts match expectations.
  - Verification: a CI step asserts the timestamps and counts.

- [ ] T110 [US4] **Ingest additional public datasets (UCI/OpenML) to satisfy FR‑008**.
  - For each of the eight new datasets (listed in T112‑T119), fetch via `datasets.load_dataset` or direct URL, compute SHA‑256 checksum, store under `data/raw/`, and record metadata in `results/real_world_dataset_catalog.csv` conforming to `RealWorldDataset` contract.
  - Verification: unit test confirming each file exists, checksum matches, and catalog entry validates against the schema.

- [ ] T111 **Power‑vs‑effect‑size table (SC‑002)**.
  - Using the synthetic generator, sweep `effect_size` values `[0.0, 0.2, 0.5, 0.8, 1.0]` (fixed sample size) and compute empirical power from the full‑scale results. Write `results/power_vs_effect_size.csv` with columns `effect_size, scaling_method, power, ci_lower, ci_upper`.
  - Verification: test that the CSV contains a row for each combination and that power values increase with effect size.

- [ ] T112‑T119 **Dataset ingestion tasks** (eight tasks, one per new dataset).
  - Each task fetches a specific dataset, verifies checksum, stores under `data/raw/<dataset_id>.csv`, and updates the catalog (as in T110). Example: T112 fetches the "Wine Quality" dataset from UCI, T113 fetches "Adult" from OpenML, etc.
  - Verification: each task has its own pytest asserting successful download and catalog entry.

- [ ] T120 **Chi‑squared testing (FR‑003)**.
  - Implement chi‑squared test on binned categorical versions of continuous variables within `code/analysis/tests.py`. Produce results in `results/chi_squared_results.csv` adhering to a new contract `chi_squared_result.schema.yaml` (fields: `result_id, config_id, chi2_statistic, p_value, is_rejected, ground_truth, scaling_method, error_type`).
  - Verification: unit test confirming schema compliance and that binning respects the specified number of bins.

- [ ] T122 **Synthetic‑vs‑real consistency metric (SC‑006)**.
  - Compute the mean absolute deviation (MAD) of p‑values between synthetic and real‑world results for each scaling method, write `results/consistency_metric.json` with fields `scaling_method, mad_p_value, passes_threshold` (threshold = 0.02). If any method exceeds the threshold, flag it in the final summary.
  - Verification: test that the JSON matches the schema and that the flag logic works.

## Phase 3: Reproducible results and paper handoff

- [ ] T109 [US3/US4] **Write methods/results account and paper‑stage handoff**.
  - Update `results/summary_report.md` (or `quickstart.md`) documenting:
    * Exact commands to reproduce the smoke run (`python -m code.main --smoke`) and full run (`python -m code.main --iterations=10000`),
    * Locations of seed provenance (`data/config/seed_config.json`) and dataset catalog (`results/real_world_dataset_catalog.csv`),
    * Key findings from T105–T107, including any non‑significant mixed‑effects outcomes,
    * Consistency metric from T122,
    * Limitations: sampled real‑world datasets, any skipped iterations (zero variance, outliers), and the numerical‑precision framing of p‑value invariance.
  - Verification: a CI script `run_all.sh` executes the full workflow from the documented commands and then diffs the regenerated `results/` artifacts against the committed versions (or compares stored hashes). The test passes if all hashes match and the report contains the required sections.

## Dependencies and requirement coverage (updated)

| FR | Covered by Tasks |
|----|------------------|
| FR‑001 | T008–T014 (generator) |
| FR‑002 | T015–T023 (scaling) |
| FR‑003 | T015–T023 (including chi‑squared via T120) |
| FR‑004 | T028a/T028d (iteration fidelity) + T108a (full run) |
| FR‑005 | T103a, T103b (error‑rate & power) |
| FR‑006 | T030 (plot) regenerated in T108b |
| FR‑007 | T028a fidelity enforcement, runtime checks in T108a |
| FR‑008 | T110 + T112‑T119 (total ≥10 datasets) |
| FR‑009 | T051–T066 (real‑world pipeline) |
| FR‑010 | T105 (mixed‑effects) |
| FR‑012 | All tasks respect the spec constraints (no weakening). |

## Execution order (final)

T101 → T102 → T103a → T103b → {T104, T106, T110, T111, T112‑T119} → T107 → T105 → T108a → T108b → T109
