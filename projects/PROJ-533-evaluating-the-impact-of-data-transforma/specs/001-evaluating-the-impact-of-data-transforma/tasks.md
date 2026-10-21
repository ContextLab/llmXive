# Tasks: Evaluating the Impact of Data Transformation on Statistical Test Sensitivity

**Inputs**: `specs/001-evaluating-the-impact-of-data-transforma/spec.md`, `plan.md`, `data-model.md`, `contracts/`

This checklist implements the complete end-to-end study satisfying FR-001–FR-010 and SC-001–SC-004. Prior rejected tasks (checkpointing utilities, dataset download, checksums, filtering, Shapiro-Wilk logic, integration tests) are consolidated into the tasks below; each previously-missing artifact is now explicitly required with its real output file. Tasks are ordered to respect data flow.

---

- [ ] **T001** [P] Implement checkpointing utilities and pipeline entry point
  *Files*: `code/utils/checkpointing.py`, `code/main.py`, `specs/001-evaluating-the-impact-of-data-transforma/quickstart.md`
  *Description*:
  - `checkpointing.py` provides `save_state(run_id: str, state: dict) -> None`, `load_state(run_id: str) -> dict | None`, and `delete_checkpoint(run_id: str) -> None` using `portalocker` for file locking and atomic writes (temp file then rename). The file must be complete and importable — no truncated stubs.
  - `main.py` parses `--stage {download,filter,simulate,aggregate,all}` and `--resume`, orchestrates the pipeline, and records a checkpoint after each dataset/stage.
  - `quickstart.md` documents the runnable command `python -m code.main --stage all`.
  *Verification*:
  - `python -c "from code.utils.checkpointing import save_state, load_state, delete_checkpoint"` runs without ImportError.
  - A round-trip `save_state('test', {'a':1}); assert load_state('test')['a']==1; delete_checkpoint('test')` succeeds.
  - `python -m code.main --stage download --dry-run` prints a stage summary and exits 0.

- [ ] **T002** [US1] Download ≥ 50 public datasets (OpenML + UCI), record verified URLs and SHA-256 checksums
  *Files*: `code/download_datasets.py`, `code/checksum_datasets.py`, `data/openml_ids.txt`, `data/uci_dataset_urls.txt`, `data/datasets.csv`, `data/checksums.csv`
  *Description*:
  - `openml_ids.txt` lists ≥ 60 verified OpenML dataset IDs; `uci_dataset_urls.txt` lists ≥ 10 canonical UCI CSV/ARFF URLs (e.g. `https://raw.githubusercontent.com/...` or `https://archive.ics.uci.edu/...`).
  - `download_datasets.py` iterates the ID list with `sklearn.datasets.fetch_openml` and fetches UCI files via `requests`. For each successful download: (i) store raw data as `data/raw/<dataset_id>.parquet`, (ii) verify the source URL via `is_source_verified(url)` (must match `^https?://` against the verified list) BEFORE writing any row, (iii) append a row to `data/datasets.csv` conforming to `contracts/dataset.schema.yaml`, and (iv) compute the SHA-256 checksum and append to `data/checksums.csv` via `checksum_datasets.py`. Both scripts must be complete, non-truncated implementations with a `__main__` entry point.
  - If after processing the full lists fewer than 50 usable datasets are obtained, raise `ConnectionError("Dataset fetch failed: insufficient public datasets found")` and exit 1 — NO synthetic or mock fallback, ever.
  *Verification*:
  - `python code/download_datasets.py` exits 0 and `python code/checksum_datasets.py` exits 0.
  - `pandas.read_csv('data/datasets.csv')` yields ≥ 50 rows; all `source_url` values match the URL pattern; all `checksum_sha256` are 64-hex strings.
  - `data/checksums.csv` exists and is non-empty, with one row per raw file.

- [ ] **T003** [US1] Filter datasets: imputation, missing-value and sample-size exclusions, Shapiro-Wilk normality test
  *Files*: `code/filter_datasets.py`, `data/imputation_log.csv`, `data/exclusions.csv`, `data/filter_results.csv`, updated `data/datasets.csv`
  *Description*:
  - For each dataset in `data/datasets.csv` (streaming with `chunksize=10000` if > 10,000 rows):
    1. Compute the overall missing rate; exclude datasets with > 10% missing, `sample_size < 30`, no continuous variable, or no categorical group label with ≥ 2 levels. Every exclusion must be written as a real data row to `data/exclusions.csv` (`dataset_id, reason, details`) — header-only files are a failure.
    2. Impute missing values per variable: mean for |skew| ≤ 0.5, median otherwise; log each imputation (`dataset_id, variable, method, rate`) to `data/imputation_log.csv`.
    3. Run Shapiro-Wilk on each continuous variable; retain the dataset if the minimum p-value < 0.05 (non-normal) and N ≥ 30.
    4. Compute average skewness and kurtosis (first 10,000 rows when streaming).
    5. Write per-dataset results to `data/filter_results.csv` (`dataset_id, shapiro_p, sample_size, included`) and update `data/datasets.csv` with `skewness`, `kurtosis`, `status` (`processed`/`filtered_out`), `filter_reason`, `exclusion_details`.
  - The script must be a complete implementation including all exclusion, imputation, and Shapiro-Wilk logic; truncated files are rejected.
  *Verification*:
  - `python code/filter_datasets.py` exits 0.
  - `data/exclusions.csv` and `data/imputation_log.csv` contain real data rows for every excluded/imputed dataset (or a documented empty-with-header state if genuinely none).
  - All rows in `data/datasets.csv` with `status='processed'` have `shapiro_wilk_p` < 0.05 and `sample_size` ≥ 30.

- [ ] **T004** [US2] Implement the three data-transformation methods
  *Files*: `code/data/transformations.py`, `results/transformations_log.csv`, `code/tests/unit/test_transformations.py`
  *Description*:
  - Provide `apply_boxcox(df, var)`, `apply_yeojohnson(df, var)`, `apply_rank_inverse_normal(df, var)`.
  - Box-Cox: if any value ≤ 0, apply log-shift (`df[var] - df[var].min() + 1e-6`) and record the intervention in `intervention_log`. Optimize λ via `scipy.stats.boxcox_normmax`.
  - Yeo-Johnson: `sklearn.preprocessing.PowerTransformer(method='yeo_johnson')` with per-dataset λ.
  - Rank-based: ranks mapped to `scipy.stats.norm.ppf(rank/(N+1))`.
  - For each variable in each processed dataset, write a record conforming to `contracts/transformation.schema.yaml` to `results/transformations_log.csv`.
  *Verification*:
  - `pytest code/tests/unit/test_transformations.py -q` passes, including a test that log-shift is applied and logged for negative values.
  - Running the three methods on a single filtered dataset produces three `status='success'` records with finite transformed values.

- [ ] **T005** [US2] Pilot Type I error estimation on one filtered dataset (label shuffling, end-to-end)
  *Files*: `code/analyze_type1_error.py`, `results/type1_error_pilot.csv`, `results/type1_error_pilot_validation.csv`, `results/simulation_seeds.txt`
  *Description*:
  - For one dataset with `status='processed'`, shuffle group labels (fixed seed = 42) 2000 times; on each shuffle apply the three transformations (T004) plus the untransformed baseline, run two-sample t-test and one-way ANOVA, and record the proportion of p < 0.05 as `error_rate` per transformation-test pair. This is the primary FR-004 estimator: real data, permuted labels — no simulated stand-in.
  - Write `type1_error_pilot.csv` (`transformation, test_type, error_rate`) and a validation file recording `error_rate, seed, n_iterations, pass` (pass = baseline untransformed error in [0.04, 0.06]).
  - Append `RUN_ID=pilot SEED=42` to `results/simulation_seeds.txt`.
  *Verification*:
  - `python code/analyze_type1_error.py --pilot` exits 0; `type1_error_pilot.csv` is non-empty with the required columns; the validation file contains a boolean `pass` value.

- [ ] **T006** [US2] Full Type I error estimation across all filtered datasets
  *Files*: `code/analyze_type1_error.py`, `results/type1_error_results.csv`, `results/type1_error_validation.csv`, updated `results/simulation_seeds.txt`
  *Description*:
  - For every `status='processed'` dataset, generate 1000 label-shuffling null replicates (fixed per-dataset seed, recorded in `simulation_seeds.txt`), apply the three transformations and baseline, run t-test and ANOVA, and append per-dataset rows (`dataset_id, transformation, test_type, error_rate, n_iterations, p_values_or_counts`) to `type1_error_results.csv`. Store per-shuffle significance counts at each α ∈ {0.01, 0.02, 0.025, 0.05, 0.075, 0.10} so the α-sweep (T009) recomputes from raw counts without re-running.
  - Checkpoint after each dataset via `checkpointing.save_state` for resumption.
  *Verification*:
  - `python code/analyze_type1_error.py` exits 0; `type1_error_results.csv` contains ≥ 4 × 2 × N_processed rows with `error_rate` in [0, 1].

- [ ] **T007** [US4] Simulate alternative datasets with known Cohen's d and compute power against a closed-form reference
  *Files*: `code/simulate_power.py`, `data/simulated_metadata.csv`, `data/simulated/`, `results/power/<effect>_<trans>_<test>.json`, `results/power/calibration_notes.txt`
  *Description*:
  - For each shape stratum (from T003 skewness/kurtosis), generate 1000 simulated datasets per effect size (Cohen's d = 0.2, 0.5, 0.8) preserving marginal shape (skew-normal), with ground-truth group labels. Record metadata conforming to `contracts/simulated_dataset.schema.yaml` in `simulated_metadata.csv`.
  - Apply the three transformations and baseline; run t-test/ANOVA; empirical power = proportion of p < 0.05. This addresses the reviewer's circularity objection: for the normal-shape stratum compute a closed-form reference power via `statsmodels.stats.power.TTestPower` and store it as `reference_power_normal`; validate empirical power against it (within Monte-Carlo CI), and record the derivation in `calibration_notes.txt`.
  - JSON per combination: `{ "power", "reference_power_normal", "n_iterations": 1000, "ci_lower", "ci_upper" }`.
  *Verification*:
  - 4 effect/baseline × 3 transformations × 2 tests of expected JSON files exist (baseline included); each has `power` in [0,1] and non-null `reference_power_normal` for the normal stratum.
  - Unit tests verify simulated skewness > 0.5 for non-normal strata and empirical power within the 95% CI of reference power for the normal stratum.

- [ ] **T008** [US3] Aggregate Type I error and power with bootstrap confidence intervals
  *Files*: `code/aggregate_results.py`, `results/aggregated_results.csv`
  *Description*:
  - Load `type1_error_results.csv` and `results/power/*.json`; for each (transformation, test_type, metric) pair compute the mean and a 95% bootstrap CI (≥ 2000 resamples, fixed seed = 123).
  - Compute `ci_half_width = (ci_upper - ci_lower)/2`; set `validation_status = "pass"` iff ≤ 0.02, else `"fail"` — reported honestly, per the reviewer's note that the ±0.02 target may be unattainable for some combinations; no artificial iteration inflation to force a pass.
  - Write rows conforming to `contracts/aggregated_result.schema.yaml`.
  *Verification*:
  - `python code/aggregate_results.py` exits 0; `aggregated_results.csv` has one row per transformation × test × metric (3 × 2 × 2 = 12 rows) satisfying the schema; any `fail` rows are retained with their actual half-widths.

- [ ] **T009** [US3] Friedman test, Bonferroni post-hoc, and α-sweep sensitivity analysis
  *Files*: `code/aggregate_results.py --inference`, `results/friedman_summary.txt`, `results/aggregated/sensitivity_analysis.json`
  *Description*:
  - Friedman chi-square test (`scipy.stats.friedmanchisquare`) on per-dataset error rates across the three transformations, separately for t-test and ANOVA; if degenerate (tied rankings), fall back to pairwise Wilcoxon signed-rank tests with Bonferroni correction and log the fallback.
  - Log statistic, raw p-value, and Bonferroni-adjusted pairwise p-values to `friedman_summary.txt`.
  - Sweep α ∈ {0.01, 0.02, 0.025, 0.05, 0.075, 0.10}: recompute error rates from the raw per-shuffle counts stored in T006 and write records conforming to `contracts/sensitivity_result.schema.yaml` to `sensitivity_analysis.json`.
  *Verification*:
  - `python code/aggregate_results.py --inference` exits 0; `friedman_summary.txt` contains the χ² statistic, p-value, and adjusted pairwise table; `sensitivity_analysis.json` parses as a list of valid SensitivityResult objects.

- [ ] **T010** [US3] Generate reproducible figures from aggregated results
  *Files*: `code/visualize_results.py`, `results/figures/error_rates.png`, `results/figures/power_curves.png`, `results/figures/sensitivity_curves.png`
  *Description*:
  - Read `aggregated_results.csv` and `sensitivity_analysis.json`. Produce: **error_rates.png** (bar plot of mean Type I error by transformation and test, bootstrap CI error bars, α = 0.05 reference line), **power_curves.png** (power vs. effect size per transformation/test with CI bands), **sensitivity_curves.png** (error rate vs. α per transformation-test pair).
  - Fixed Matplotlib style and fixed seed for byte-identical output across runs.
  *Verification*:
  - Each PNG exists, is non-empty, and a second run produces identical `sha256sum` values.

- [ ] **T011** Document methods, results, and paper-stage handoff
  *Files*: `specs/001-evaluating-the-impact-of-data-transforma/results.md`
  *Description*:
  - Summarize the pipeline with concrete artifact paths (`data/datasets.csv`, `results/type1_error_results.csv`, `results/power/*.json`, `results/aggregated_results.csv`, `results/figures/*.png`).
  - Report: datasets retained after filtering, total null simulations, power simulations per effect size, observed CI half-widths and which rows failed SC-004 (honestly), Friedman test outcome and post-hoc conclusions.
  - State explicitly that Type I error was estimated by label shuffling on real filtered datasets and power on simulated alternatives with known Cohen's d validated against closed-form reference power. List limitations (associational framing, CI half-width shortfalls, compute constraints).
  - State the paper-stage handoff: the paper pipeline ingests `results.md`, `aggregated_results.csv`, and the three PNGs; no further computation is required here.
  *Verification*:
  - File exists and every numeric claim matches the underlying CSV/JSON values (checked by a small verification script).

- [ ] **T012** End-to-end reproducibility, integration tests, and benchmark check
  *Files*: `code/tests/integration/test_pipeline.py`, `results/benchmark.log`
  *Description*:
  - `test_pipeline.py` must be a complete, functional test (no placeholders like `Path(____)`): it loads `data/datasets.csv`, asserts ≥ 50 rows with valid URLs, runs `python -m code.main --stage all --dry-run`, and checks that `results/aggregated_results.csv` contains ≥ 1 row.
  - Execute `python -m code.main --stage all` from a clean checkout; run `pytest -q` (all tests pass); record wall-clock time to `results/benchmark.log` (< 6 h on the 2-core CPU runner).
  - After successful completion, delete the checkpoint via `delete_checkpoint`.
  - Re-run `python code/analyze_type1_error.py --pilot` and verify byte-identical output to the stored pilot CSV (`sha256sum` comparison).
  *Verification*:
  - Pipeline exits 0; `benchmark.log` shows < 6 h; `pytest` returns 0; checkpoint removed; pilot CSV checksum matches the reference.

---

**Dependency graph**

```
T001 → T002 → T003 → T004 → T005 → T006
                ↘          ↘
                 → T007 → T008 → T009 → T010 → T011 → T012
```

**Requirement coverage**: FR-001/FR-010 → T002; FR-002 → T003; FR-003 → T004; FR-004 → T005, T006; FR-005/FR-006 → T007; FR-007 → T008; FR-008 → T009; FR-009 → T010; SC-001 → T002/T003; SC-002 → T006; SC-003 → T007; SC-004 → T008. Reviewer concerns (circular power validation → closed-form reference in T007; unattainable ±0.02 CI target → honest `fail` reporting in T008) are addressed without weakening any test.
