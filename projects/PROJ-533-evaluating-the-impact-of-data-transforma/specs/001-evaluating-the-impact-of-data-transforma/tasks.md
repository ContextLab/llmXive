# Tasks: Evaluating the Impact of Data Transformation on Statistical Test Sensitivity

**Inputs**: `specs/001-evaluating-the-impact-of-data-transformation-sensitivity/spec.md`, `plan.md`, `data-model.md`, `contracts/`  

The following checklist implements the complete end‑to‑end study while satisfying every functional requirement (FR‑001 – FR‑010) and success criterion (SC‑001 – SC‑004).  Tasks are ordered to respect data flow; later tasks depend on the artifacts produced by earlier ones.

---  

- [ ] **T001** [P] Implement checkpointing utilities and pipeline entry point  
  *Files*: `code/utils/checkpointing.py`, `code/main.py`, `specs/001-evaluating-the-impact-of-data-transformation-sensitivity/quickstart.md`  
  *Description*:  
  • `checkpointing.py` provides `save_state(run_id: str, state: dict) → None`, `load_state(run_id: str) → dict | None`, and `delete_checkpoint(run_id: str) → None` using `portalocker` for file locking and atomic writes (temp file → rename).  
  • `main.py` parses `--stage {download,filter,simulate,aggregate,all}` and `--resume`, orchestrates the pipeline, and records the checkpoint after each major stage.  
  • `quickstart.md` documents the runnable command `python -m code.main --stage all`.  
  *Verification*:  
  - `python -c "from code.utils.checkpointing import save_state, load_state, delete_checkpoint"` runs without ImportError.  
  - A round‑trip `save_state('test', {'a':1}); assert load_state('test')['a']==1; delete_checkpoint('test')` succeeds.  
  - `python -m code.main --stage download --dry-run` prints the stage summary and exits 0.  

- [ ] **T002** [US1] Download ≥ 60 public datasets (≥ 50 from OpenML, ≥ 10 from UCI) and record SHA‑256 checksums  
  *Files*: `code/download_datasets.py`, `data/openml_ids.txt`, `data/uci_dataset_urls.txt`, `data/datasets.csv`, `data/checksums.csv`  
  *Description*:  
  • `openml_ids.txt` lists ≥ 60 verified OpenML dataset IDs; `uci_dataset_urls.txt` lists ≥ 10 canonical UCI CSV/ARFF URLs.  
  • `download_datasets.py` iterates the ID list with `sklearn.datasets.fetch_openml` and downloads UCI files via `requests`.  
  • For each successful download: (i) store raw data as `data/raw/<dataset_id>.parquet`, (ii) verify the source URL matches `^https?://` via `is_source_verified(url)`, (iii) compute SHA‑256 checksum, (iv) append a row to `data/datasets.csv` (conforming to `contracts/dataset.schema.yaml`) and a row to `data/checksums.csv`.  
  • If after processing the full lists fewer than 60 usable datasets are obtained, raise `ConnectionError("Dataset fetch failed: insufficient public datasets found")` and exit 1 (no synthetic fallback).  
  *Verification*:  
  - `python code/download_datasets.py` exits 0.  
  - `pandas.read_csv('data/datasets.csv')` yields ≥ 60 rows, all `source_url` match the URL pattern, and all `checksum_sha256` are 64‑hex strings.  
  - `data/checksums.csv` exists and is non‑empty.  

- [ ] **T003** [US1] Filter datasets, impute missing values, and compute shape statistics  
  *Files*: `code/filter_datasets.py`, `data/imputation_log.csv`, `data/exclusions.csv`, `data/filter_results.csv`, updated `data/datasets.csv` (adds `skewness`, `kurtosis`, `status`, `filter_reason`, `exclusion_details`)  
  *Description*:  
  • For each dataset listed in `data/datasets.csv`:  
    1. Load the dataset (streaming if > 10 000 rows).  
    2. Impute missing values per variable: mean for |skew| ≤ 0.5, median otherwise; log each imputation (`dataset_id, variable, method, rate`) to `imputation_log.csv`.  
    3. Exclude a dataset if any of: overall missing > 10 %, `sample_size` < 30, no continuous variable, or no categorical group label with ≥ 2 levels.  Log exclusions (`dataset_id, reason, details`) to `exclusions.csv`.  
    4. Run Shapiro‑Wilk on each continuous variable; keep the dataset if the **minimum** p‑value < 0.05 (non‑normal).  
    5. Compute average skewness and kurtosis (using the first 10 000 rows when streaming).  
    6. Write per‑dataset results to `filter_results.csv` (`dataset_id, shapiro_p, sample_size, included`).  
    7. Update the corresponding row in `data/datasets.csv` with `skewness`, `kurtosis`, `status`=`processed` or `filtered_out`, and appropriate `filter_reason`/`exclusion_details`.  
  *Verification*:  
  - `python code/filter_datasets.py` exits 0.  
  - `data/imputation_log.csv` and `data/exclusions.csv` contain at least one data row each (or a documented empty‑with‑header state).  
  - All rows in `data/datasets.csv` with `status='processed'` have `shapiro_wilk_p` < 0.05 and `sample_size` ≥ 30.  

- [ ] **T004** [US2] Implement the three data‑transformation methods  
  *Files*: `code/data/transformations.py`, `results/transformations_log.csv`  
  *Description*:  
  • Provide functions `apply_boxcox(df, var)`, `apply_yeojohnson(df, var)`, and `apply_rank_inverse_normal(df, var)`.  
  • Box‑Cox: if any value ≤ 0, apply a log‑shift (`df[var] = df[var] - df[var].min() + 1e-6`) and record the intervention in the `intervention_log` field. Optimize λ via `scipy.stats.boxcox_normmax`.  
  • Yeo‑Johnson: use `sklearn.preprocessing.PowerTransformer(method='yeo_johnson')` with per‑dataset λ optimization.  
  • Rank‑based: compute ranks and map to the standard normal quantile (`scipy.stats.norm.ppf(rank/(N+1))`).  
  • For each variable in each processed dataset, create a record conforming to `contracts/transformation.schema.yaml` (`transformation_id, dataset_id, variable_name, method, lambda_param, intervention_log, status`) and append it to `results/transformations_log.csv`.  
  *Verification*:  
  - `pytest tests/unit/test_transformations.py::test_log_shift_applied_on_negative_values -q` passes.  
  - Running the three methods on a single filtered dataset produces three `status='success'` records with finite transformed values.  

- [ ] **T005** [US2] Pilot Type I error estimation on one filtered dataset (null simulation)  
  *Files*: `code/generate_null_data.py`, `code/analyze_type1_error.py`, `results/type1_error_pilot.csv`, `results/type1_error_pilot_validation.csv`, `results/simulation_seeds.txt`  
  *Description*:  
  • `generate_null_data.py` creates a null dataset by permuting group labels (fixed seed = 42) while preserving the marginal distribution of each continuous variable (fit a skew‑normal using the `skewness`/`kurtosis` from T003).  
  • `analyze_type1_error.py --pilot` loads the pilot null dataset, applies the three transformations (T004), runs a two‑sample t‑test and one‑way ANOVA, repeats the label‑shuffling **2000** times, and records the proportion of p < 0.05 as `error_rate`.  
  • Results are written to `type1_error_pilot.csv`; a validation file records `error_rate`, `seed`, `n_iterations`, and a boolean `pass` flag (true if the baseline untransformed error lies in [0.04, 0.06]).  
  • All used seeds are appended to `results/simulation_seeds.txt` (`RUN_ID=pilot SEED=42`).  
  *Verification*:  
  - `python code/analyze_type1_error.py --pilot` exits 0 and produces a non‑empty `type1_error_pilot.csv` with columns `transformation,test_type,error_rate`.  
  - The validation file contains a `pass` column with a boolean value.  

- [ ] **T006** [US2] Full Type I error estimation across all filtered datasets  
  *Files*: `code/analyze_type1_error.py`, `results/type1_error_results.csv`, `results/type1_error_validation.csv`, updated `results/simulation_seeds.txt`  
  *Description*:  
  • For every dataset marked `status='processed'` in `data/datasets.csv`, generate **1000** label‑shuffling null replicates (fixed seed per dataset, recorded).  
  • Apply the three transformations (T004) to each replicate, run t‑test and ANOVA, compute the proportion of significant p‑values per transformation‑test pair, and append rows to `type1_error_results.csv` (`dataset_id, transformation, test_type, error_rate, n_iterations`).  
  • After each dataset the checkpoint is saved via `checkpointing.save_state` to allow resumption.  
  • `type1_error_validation.csv` records a global check that the untransformed baseline error is within the nominal α ± 0.01 range.  
  *Verification*:  
  - Script completes without error (`python code/analyze_type1_error.py` exits 0).  
  - `type1_error_results.csv` contains ≥ 3 × 2 × N_processed rows and `error_rate` values between 0 and 1.  

- [ ] **T007** [US4] Simulate alternative datasets for power analysis (Cohen’s d = 0.2, 0.5, 0.8)  
  *Files*: `code/simulate_power.py`, `data/simulated_metadata.csv`, simulated data files under `data/simulated/`, `results/power/<effect>_<trans>_<test>.json` (one JSON per combination), `results/power/calibration_notes.txt`  
  *Description*:  
  • For each shape stratum defined by `skewness`/`kurtosis` from T003, generate **1000** simulated datasets per effect size (Cohen’s d) preserving the marginal shape (skew‑normal). Ground‑truth group labels are created with the specified mean difference.  
  • Record metadata (`sim_id, source_dataset_id, effect_size, skewness, kurtosis, n_samples, seed_used`) in `simulated_metadata.csv`.  
  • Apply the three transformations (T004) and run t‑test/ANOVA on each simulated dataset; compute empirical power as the proportion of p < 0.05.  
  • For the normal‑shape stratum, compute a closed‑form reference power using `statsmodels.stats.power.tt_solve_power` and store it as `reference_power_normal` in each JSON.  
  • JSON schema: `{ "power": <float>, "reference_power_normal": <float>, "n_iterations": 1000, "ci_lower": <float>, "ci_upper": <float> }`.  
  *Verification*:  
  - All expected JSON files exist (3 effect sizes × 3 transformations × 2 tests = 18 files).  
  - Each JSON contains `power` in [0,1] and a non‑null `reference_power_normal`.  
  - Unit tests verify that simulated skewness exceeds 0.5 for non‑normal strata and that empirical power lies within the 95 % CI of the reference power for the normal stratum.  

- [ ] **T008** [US3] Aggregate Type I error and power results with bootstrap confidence intervals  
  *Files*: `code/aggregate_results.py`, `results/aggregated_results.csv`  
  *Description*:  
  • Load `type1_error_results.csv` and all `results/power/*.json`.  
  • For each (transformation, test_type, metric) pair (excluding the untransformed baseline), compute the mean value and a 95 % bootstrap CI (≥ 2000 resamples, fixed seed = 123).  
  • Calculate `ci_half_width = (ci_upper - ci_lower) / 2`.  
  • Set `validation_status = "pass"` iff `ci_half_width ≤ 0.02`; otherwise `"fail"` (no artificial iteration inflation).  
  • Write rows conforming to `contracts/aggregated_result.schema.yaml` (`agg_id, transformation, test_type, metric, mean_value, ci_lower, ci_upper, ci_half_width, validation_status, n_datasets, n_iterations`).  
  *Verification*:  
  - Running `python code/aggregate_results.py` exits 0.  
  - `aggregated_results.csv` contains one row per transformation × test × metric (3 × 2 × 2 = 12 rows).  
  - All columns satisfy schema constraints; at least one row has `validation_status="fail"` if the half‑width target is unattainable, demonstrating honest reporting.  

- [ ] **T009** [US3] Inferential comparison and sensitivity analysis (Friedman test, Bonferroni post‑hoc, α‑sweep)  
  *Files*: `code/aggregate_results.py --inference`, `results/friedman_summary.txt`, `results/aggregated/sensitivity_analysis.json`  
  *Description*:  
  • Perform a Friedman chi‑square test (`scipy.stats.friedmanchisquare`) on per‑dataset error rates across the three transformations (separate for t‑test and ANOVA).  
  • If the Friedman statistic is non‑degenerate, conduct pairwise Wilcoxon signed‑rank tests with Bonferroni correction; otherwise fall back to pairwise tests only. Log the full output (statistic, p‑value, pairwise adjusted p‑values) to `friedman_summary.txt`.  
  • Fit an optional GEE model (`statsmodels.genmod.generalized_estimating_equations.GEE`) with a stratum cluster to provide an additional confirmatory p‑value (also logged).  
  • Sweep significance thresholds α ∈ {0.01, 0.02, 0.025, 0.05, 0.075, 0.10}; for each α recompute error rates from the raw null results and write a record per (transformation, test_type, α) conforming to `contracts/sensitivity_result.schema.yaml` into `sensitivity_analysis.json`.  
  *Verification*:  
  - `python code/aggregate_results.py --inference` exits 0.  
  - `friedman_summary.txt` contains the Friedman χ² statistic, raw p‑value, and a table of Bonferroni‑adjusted pairwise p‑values.  
  - `sensitivity_analysis.json` parses as a list of valid `SensitivityResult` objects (schema validation passes).  

- [ ] **T010** [US3] Generate reproducible figures from aggregated results  
  *Files*: `code/visualize_results.py`, `results/figures/error_rates.png`, `results/figures/power_curves.png`, `results/figures/sensitivity_curves.png`  
  *Description*:  
  • `visualize_results.py` reads `aggregated_results.csv` and `sensitivity_analysis.json`.  
  • Creates:  
    - **error_rates.png** – bar plot of mean Type I error by transformation and test, with error bars showing the bootstrap CI and a horizontal line at α = 0.05.  
    - **power_curves.png** – line plot of power vs. effect size (small, medium, large) for each transformation and test, with shaded CI bands.  
    - **sensitivity_curves.png** – line plot of error rate vs. α for each transformation‑test pair.  
  • All plots use a fixed Matplotlib style and `random.seed(0)` to guarantee byte‑identical output on repeated runs.  
  *Verification*:  
  - Each PNG file exists, is non‑empty, and `sha256sum` of a second run matches the first (deterministic).  

- [ ] **T011** Document methods, results, and paper‑stage handoff  
  *Files*: `specs/001-evaluating-the-impact-of-data-transformation-sensitivity/results.md`  
  *Description*:  
  • Summarize the pipeline, referencing concrete artifact paths (`data/datasets.csv`, `results/type1_error_results.csv`, `results/power/*.json`, `results/aggregated_results.csv`, `results/figures/*.png`).  
  • Report: number of datasets retained after filtering, total number of null simulations, total number of power simulations per effect size, observed CI half‑widths and which rows failed SC‑004, and the outcome of the Friedman test (statistic, p‑value, post‑hoc conclusions).  
  • Explicitly note that Type I error was estimated on simulated null data that matched the marginal shape of real datasets, and that power was measured on simulated alternatives with known Cohen’s d.  
  • List limitations (e.g., CI half‑width > 0.02 for some combos, computational time constraints).  
  • State the handoff: the paper‑stage pipeline should ingest `results.md`, the aggregated CSV, and the three PNG figures; no further computation is required here.  
  *Verification*:  
  - File exists and every numeric claim (e.g., “50 datasets retained”, “CI half‑width = 0.023”) matches the corresponding value in the underlying CSV/JSON files (checked by a simple script).  

- [ ] **T012** End‑to‑end reproducibility and benchmark check  
  *Files*: `results/benchmark.log` (generated by the pipeline), `tests/` (unit + integration), re‑run of pilot for determinism  
  *Description*:  
  • Execute `python -m code.main --stage all` from a clean checkout (no prior checkpoint).  
  • Run the full test suite `pytest -q`; all tests must pass.  
  • The pipeline records wall‑clock time to `results/benchmark.log`; ensure the total time is < 6 hours on the GitHub Actions free‑tier CPU runner.  
  • After successful completion, delete the checkpoint file.  
  • Re‑run the pilot Type I error task (`python code/analyze_type1_error.py --pilot`) and verify that the produced `type1_error_pilot.csv` is byte‑identical to the original pilot output (checksum comparison).  
  *Verification*:  
  - Command exits 0, `benchmark.log` shows `< 6h`, `pytest` returns 0, checkpoint file is removed, and the pilot CSV checksum matches the stored reference (`sha256sum`).  

---  

**Dependency graph**

```
T001 → T002 → T003 → T004 → T005 → T006
                ↘          ↘
                 → T007 → T008 → T009 → T010 → T011 → T012
```

All tasks together constitute a complete, reproducible study that fulfills the specification, the plan, and the reviewer’s concerns (reference power calculation, honest CI half‑width reporting, and CPU‑only feasibility).
