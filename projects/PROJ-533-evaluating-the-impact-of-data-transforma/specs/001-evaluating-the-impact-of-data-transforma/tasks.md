# Tasks: Evaluating the Impact of Data Transformation on Statistical Test Sensitivity

**Inputs**: `specs/001-evaluating-the-impact-of-data-transforma/spec.md`, `plan.md`, `data-model.md`, `contracts/`

This checklist implements the complete end-to-end study satisfying FR-001–FR-010 and SC-001–SC-004. Tasks are ordered to respect data flow and aligned with the module structure in `plan.md`.

---

- [ ] **T001** [P] Implement checkpointing utilities and pipeline entry point <!-- FAILED-IN-EXECUTION: code/main.py exit=1 --> <!-- FAILED: unspecified --> <!-- FAILED-IN-EXECUTION: code/main.py exit=-1 (TIMEOUT) --> <!-- FAILED-IN-EXECUTION: code/main.py exit=-1 (TIMEOUT) --> <!-- FAILED-IN-EXECUTION: code/main.py exit=1 -->
  *Files*: `code/utils/checkpointing.py`, `code/main.py`, `specs/001-evaluating-the-impact-of-data-transforma/quickstart.md`, `contracts/*.schema.yaml`
  *Description*:
  - `checkpointing.py` provides `save_state(run_id: str, state: dict) -> None`, `load_state(run_id: str) -> dict | None`, and `delete_checkpoint(run_id: str) -> None` using `portalocker` for file locking and atomic writes.
  - `main.py` parses `--stage {download,filter,simulate,aggregate,all}`, `--resume`, and `--dry-run`. A `--dry-run` must print the intended operations for the selected stage (e.g., listing URLs to be fetched or files to be transformed) and exit 0 without modifying the filesystem.
  - Update all `transformation` enums in `contracts/` (specifically `transformation.schema.yaml`, `aggregated_result.schema.yaml`, and `sensitivity_result.schema.yaml`) to include the value `"baseline"`. This is a mandatory prerequisite for T006, T007, and T008 to ensure that untransformed data results are schema-compliant.
  - `quickstart.md` documents the runnable command `python -m code.main --stage all`.
  *Verification*:
  - `python -c "from code.utils.checkpointing import save_state, load_state, delete_checkpoint"` runs without ImportError.
  - `python -m code.main --stage download --dry-run` prints a stage summary and exits 0.

- [ ] **T002** [US1] Download ≥ 50 public datasets (OpenML + UCI), record verified URLs and SHA-256 checksums <!-- FAILED-IN-EXECUTION: code/data/download_datasets.py exit=-1 (TIMEOUT); code/data/checksum_datasets.py exit=-1 (TIMEOUT) --> <!-- FAILED-IN-EXECUTION: code/data/download_datasets.py exit=-1 (TIMEOUT); code/data/checksum_datasets.py exit=-1 (TIMEOUT) -->
  *Files*: `code/data/download_datasets.py`, `code/data/checksum_datasets.py`, `data/openml_ids.txt`, `data/uci_dataset_urls.txt`, `data/datasets.csv`, `data/checksums.csv`
  *Description*:
  - `openml_ids.txt` lists ≥ 60 verified OpenML IDs; `uci_dataset_urls.txt` lists ≥ 10 canonical UCI CSV/ARFF URLs.
  - `download_datasets.py` fetches data via `sklearn.datasets.fetch_openml` and `requests`. For each successful download: (i) store as `data/raw/<dataset_id>.parquet`, (ii) verify source URL via `is_source_verified(url)`, (iii) append a provisional row to `data/datasets.csv` (conforming to `contracts/dataset.schema.yaml` but allowing nulls for fields computable only during filtering), and (iv) compute SHA-256 via `checksum_datasets.py` and append to `data/checksums.csv`.
  - If fewer than 50 datasets are downloaded, raise `ConnectionError` and exit 1.
  *Verification*:
  - `python -m code.data.download_datasets` exits 0.
  - `pandas.read_csv('data/datasets.csv')` yields ≥ 50 rows; all `source_url` match the pattern.

- [ ] **T003** [US1] Filter datasets: imputation, missing-value and sample-size exclusions, Shapiro-Wilk normality test
  *Files*: `code/data/filter_datasets.py`, `data/imputation_log.csv`, `data/exclusions.csv`, `data/filter_results.csv`, updated `data/datasets.csv`
  *Description*:
  - For each dataset in `data/datasets.csv` (streaming with `chunksize=10000`):
    1. Exclude datasets with > 10% missing, `sample_size < 30`, no continuous variable, or no categorical group label (≥ 2 levels). Write exclusions to `data/exclusions.csv`.
    2. Impute missing values: mean for |skew| ≤ 0.5, median otherwise; log to `data/imputation_log.csv`.
    3. Run Shapiro-Wilk; retain if min p-value < 0.05 and N ≥ 30.
    4. Compute average skewness and kurtosis.
    5. Update `data/datasets.csv` by populating `shapiro_wilk_p`, `sample_size`, `missing_pct`, `skewness`, `kurtosis`, and `status` (`processed`/`filtered_out`).
  - If fewer than 50 datasets remain with `status='processed'`, raise `ValueError("Insufficient datasets retained after filtering")` and exit 1.
  *Verification*:
  - `python -m code.data.filter_datasets` exits 0.
  - All rows in `data/datasets.csv` with `status='processed'` satisfy schema constraints (`sample_size >= 30`, `missing_pct <= 10`, `shapiro_wilk_p < 0.05`).

- [ ] **T004** [US2] Implement data-transformation methods and persistence
  *Files*: `code/data/transformations.py`, `results/transformations_log.csv`, `data/transformed/`, `code/tests/unit/test_transformations.py`
  *Description*:
  - Provide `apply_boxcox`, `apply_yeojohnson`, and `apply_rank_inverse_normal`.
  - Box-Cox: if values ≤ 0, apply log-shift (`df[var] - df[var].min() + 1e-6`) and record in `results/transformations_log.csv`.
  - For each processed dataset and variable: (i) apply the three transformations, (ii) write the resulting values to `data/transformed/<dataset_id>_<var>_<method>.parquet` conforming to `contracts/transformed_data.schema.yaml`, and (iii) write metadata to `results/transformations_log.csv` per `contracts/transformation.schema.yaml`.
  *Verification*:
  - `pytest code/tests/unit/test_transformations.py -q` passes.
  - Files in `data/transformed/` parse correctly against `transformed_data.schema.yaml`.

- [ ] **T005** [US2] Pilot Type I error estimation on one filtered dataset
  *Files*: `code/analysis/type1_error.py`, `results/type1_error_pilot.csv`, `results/type1_error_pilot_validation.csv`, `results/simulation_seeds.txt`
  *Description*:
  - For one `status='processed'` dataset, shuffle group labels (fixed seed = 42) 5000 times.
  - For each shuffle: run t-test and ANOVA on the untransformed baseline and the three transformations (T004).
  - Record proportion of p < 0.05 as `error_rate`.
  - Write `type1_error_pilot.csv` and a validation file (`error_rate, seed, n_iterations, pass` where pass = baseline in [0.04, 0.06]).
  - Append `RUN_ID=pilot SEED=42` to `results/simulation_seeds.txt`.
  *Verification*:
  - `python -m code.analysis.type1_error --pilot` exits 0; validation file contains `pass=True`.

- [ ] **T006** [US2] Full Type I error estimation across all filtered datasets
  *Files*: `code/analysis/type1_error.py`, `results/type1_error_results.csv`, `results/type1_error_validation.csv`, updated `results/simulation_seeds.txt`
  *Description*:
  - For every `status='processed'` dataset, generate 5000 label-shuffling null replicates (aligning with Plan T021; fixed per-dataset seed recorded in `simulation_seeds.txt`).
  - For each shuffle, run t-test and ANOVA on the baseline and three transformations.
  - Produce rows conforming to `contracts/test_result.schema.yaml` for every shuffle/transformation/test combination.
  - Aggregate these into `results/type1_error_results.csv` (`dataset_id, transformation, test_type, error_rate, n_iterations`).
  - Store raw significance counts for α ∈ {0.01, 0.02, 0.025, 0.05, 0.075, 0.10} for T009.
  *Verification*:
  - `python -m code.analysis.type1_error` exits 0; `type1_error_results.csv` contains ≥ 4 (cond) × 2 (tests) × N_processed rows.

- [ ] **T007** [US4] Simulate alternative datasets and compute power
  *Files*: `code/data/simulations.py`, `code/analysis/power_analysis.py`, `data/simulated_metadata.csv`, `data/simulated/`, `results/power/*.json`
  *Description*:
  - Generate 1000 simulated datasets per effect size (Cohen's d = 0.2, 0.5, 0.8) preserving marginal shape from T003. Record metadata in `simulated_metadata.csv` per `contracts/simulated_dataset.schema.yaml`.
  - For each simulated dataset: apply baseline and three transformations, run t-test/ANOVA, and produce `TestResult` rows per `contracts/test_result.schema.yaml`.
  - Compute empirical power (proportion p < 0.05).
  - For the normal-shape stratum, compute closed-form reference power via `statsmodels.stats.power.TTestPower`.
  - For every combination, compute the 95% bootstrap CI for power and validate that the half-width ≤ 0.02.
  - Write 24 JSON files (3 effects × 4 conditions × 2 tests) to `results/power/` containing `{ "power", "reference_power_normal", "ci_half_width", "validation_status" }`.
  *Verification*:
  - 24 JSON files exist; each contains a `validation_status` based on the ±0.02 half-width target.

- [ ] **T008** [US3] Aggregate Type I error and power with bootstrap confidence intervals
  *Files*: `code/analysis/aggregation.py`, `results/aggregated_results.csv`
  *Description*:
  - Load `type1_error_results.csv` and `results/power/*.json`.
  - For each (transformation, test_type, metric) pair (including baseline), compute the mean and a 95% bootstrap CI (10,000 resamples, fixed seed = 123).
  - Compute `ci_half_width = (ci_upper - ci_lower)/2`; set `validation_status = "pass"` iff ≤ 0.02.
  - Write rows conforming to `contracts/aggregated_result.schema.yaml`.
  *Verification*:
  - `python -m code.analysis.aggregation` exits 0; `aggregated_results.csv` contains exactly 16 rows (4 conditions × 2 tests × 2 metrics).

- [ ] **T009** [US3] Friedman test, Bonferroni post-hoc, and α-sweep sensitivity analysis
  *Files*: `code/analysis/aggregation.py --inference`, `results/friedman_summary.txt`, `results/aggregated/sensitivity_analysis.json`
  *Description*:
  - Perform Friedman chi-square test (`scipy.stats.friedmanchisquare`) on per-dataset outcomes across the four conditions (baseline + 3 transformations), separately for: (i) Type I error rates (t-test), (ii) Type I error rates (ANOVA), (iii) Power outcomes (t-test), (iv) Power outcomes (ANOVA).
  - If degenerate, fall back to pairwise Wilcoxon signed-rank tests with Bonferroni correction.
  - Log statistics and adjusted p-values to `results/friedman_summary.txt`.
  - Sweep α ∈ {0.01, 0.02, 0.025, 0.05, 0.075, 0.10}: recompute error rates from raw counts stored in T006 and write records conforming to `contracts/sensitivity_result.schema.yaml` to `sensitivity_analysis.json`.
  *Verification*:
  - `python -m code.analysis.aggregation --inference` exits 0; `friedman_summary.txt` contains results for both error and power.

- [ ] **T010** [US3] Generate reproducible figures from aggregated results
  *Files*: `code/analysis/visualize_results.py`, `results/figures/error_rates.png`, `results/figures/power_curves.png`, `results/figures/sensitivity_curves.png`
  *Description*:
  - Produce: **error_rates.png** (bar plot of mean Type I error by transformation and test, bootstrap CI error bars, α = 0.05 reference line), **power_curves.png** (power vs. effect size per transformation/test with CI bands), **sensitivity_curves.png** (error rate vs. α per transformation-test pair).
  - Use fixed Matplotlib style and seed for byte-identical output.
  *Verification*:
  - Each PNG exists and is non-empty; second run produces identical `sha256sum`.

- [ ] **T011** Document methods, results, and paper-stage handoff
  *Files*: `specs/001-evaluating-the-impact-of-data-transforma/results.md`
  *Description*:
  - Summarize the pipeline with concrete artifact paths. Report: datasets retained, total simulations, observed CI half-widths (honestly reporting failures), and Friedman test conclusions.
  - State explicitly that Type I error used label shuffling on real data and power used simulated alternatives validated against closed-form references.
  - Define handoff: paper pipeline ingests `results.md`, `aggregated_results.csv`, and the three PNGs.
  *Verification*:
  - File exists and numeric claims match `aggregated_results.csv` and `friedman_summary.txt`.

- [ ] **T012** End-to-end reproducibility, integration tests, and benchmark check
  *Files*: `code/tests/integration/test_pipeline.py`, `results/benchmark.log`
  *Description*:
  - `test_pipeline.py` must be a complete test: load `data/datasets.csv`, assert ≥ 50 rows, run `python -m code.main --stage all --dry-run`, and check that `results/aggregated_results.csv` contains ≥ 1 row.
  - Execute `python -m code.main --stage all` from a clean checkout; run `pytest -q`; record wall-clock time to `results/benchmark.log` (< 6 h).
  - Delete the checkpoint via `delete_checkpoint`.
  - Re-run `python -m code.analysis.type1_error --pilot` and verify byte-identical output to stored pilot CSV.
  *Verification*:
  - Pipeline exits 0; `benchmark.log` shows < 6 h; `pytest` returns 0.

---

### Plan-to-Task Mapping

| Plan ID | Task ID | Status | Notes |
|---------|---------|--------|-------|
| T004    | T001    | Consolidated | Checkpointing and entry point |
| T013    | T002    | Consolidated | Dataset download and provisional metadata |
| T013b   | T002    | Consolidated | Source verification |
| T014    | T002    | Consolidated | Checksum computation |
| T015    | T003    | Consolidated | Imputation and exclusion logging |
| T016    | T003    | Consolidated | Normality and sample-size filtering |
| T017    | T003    | Consolidated | Final dataset count validation |
| T018    | T005    | Diagnostic | Pilot run serves as diagnostic |
| T019    | T007    | Consolidated | Alternative dataset generation |
| T020    | T004    | Consolidated | Transformation implementation and storage |
| T021    | T006    | Consolidated | Primary Type I error estimation (5000 shuffles) |
| T022    | T007    | Consolidated | Power estimation |
| T023    | T008    | Consolidated | Aggregation and 10k bootstrap CIs |
| T024    | T009    | Consolidated | Friedman test and Bonferroni post-hoc |
| T025    | T009    | Consolidated | Alpha-sweep sensitivity analysis |
| T026    | T010    | Consolidated | Visualization |
| T027    | T011    | Consolidated | Reporting and handoff |
| T028    | T012    | Consolidated | Cleanup and final verification |
| T012a   | T012    | Consolidated | Integration testing |

**Dependency graph**

```
T001 → T002 → T003 → T004 → T005 → T006
                ↘          ↘
                 → T007 → T008 → T009 → T010 → T011 → T012
```

**Requirement coverage**: FR-001/FR-010 → T002; FR-002 → T003; FR-003 → T004; FR-004 → T005, T006; FR-005/FR-006 → T007; FR-007 → T008; FR-008 → T009; FR-009 → T010; SC-001 → T002/T003; SC-002 → T006; SC-003 → T007; SC-004 → T008.