# Tasks: Evaluating the Impact of Data Transformation on Statistical Test Sensitivity  

**Inputs**: `specs/001-evaluating-the-impact-of-data-transformation-sensitivity/spec.md`, `plan.md`, `data-model.md`, `contracts/`  

The checklist implements the complete end‑to‑end study satisfying FR‑001 – FR‑010 and SC‑001 – SC‑004. Tasks are ordered to respect data flow, include required verification steps, and address the latest reviewer concerns (reference power calculation, dual null‑simulation, CI precision, schema consistency, and parallel‑safety). All tasks that have been verified remain unchecked; any task that failed or was flagged is reopened and refined.

---  

- [ ] **T001** Establish checkpointing utilities, pipeline entry point, and schema updates  
  *Files*: `code/utils/checkpointing.py`, `code/main.py`, `specs/001-evaluating-the-impact-of-data-transformation-sensitivity/quickstart.md`, `contracts/*.schema.yaml`  
  *Description*:  
  - `checkpointing.py` provides `save_state`, `load_state`, `delete_checkpoint` with atomic file locking.  
  - `main.py` implements `--stage {download,filter,transform,simulate,aggregate,all}` and `--dry-run` options; prints intended actions without side‑effects.  
  - All `transformation` enums in the contracts (`transformation.schema.yaml`, `aggregated_result.schema.yaml`, `sensitivity_result.schema.yaml`) are extended to include `"baseline"` for the untransformed condition.  
  - `quickstart.md` documents the runnable command `python -m code.main --stage all`.  
  *Verification*:  
  - Importing `code.utils.checkpointing` succeeds.  
  - `python -m code.main --stage download --dry-run` exits 0 and prints a stage summary.  
  *Note*: This task is **not parallel‑safe** because it writes shared code files and updates contract schemas.  

- [ ] **T002** [US1] Download ≥ 50 public datasets (UCI & OpenML) and record SHA‑256 checksums  
  *Files*: `code/data/download_datasets.py`, `code/data/checksum_datasets.py`, `data/openml_ids.txt`, `data/uci_dataset_urls.txt`, `data/datasets.csv`, `data/checksums.csv`, `data/raw/`  
  *Description*:  
  1. `openml_ids.txt` lists 60 verified OpenML dataset IDs; `uci_dataset_urls.txt` lists 15 canonical UCI CSV/ARFF URLs.  
  2. `download_datasets.py` streams each dataset using `datasets.load_dataset(..., streaming=True)` (or `sklearn.datasets.fetch_openml` for OpenML) and writes it to `data/raw/<dataset_id>.parquet` without loading the full file into memory; each file is capped at 5 MB to stay within the free‑tier runner limits.  
  3. After each successful download a checkpoint `results/checkpoints/download_<dataset_id>.json` is written.  
  4. `checksum_datasets.py` computes a streaming SHA‑256 hash for each file and appends a row to `data/checksums.csv`.  
  5. `data/datasets.csv` is initially populated with the columns required by `contracts/dataset.schema.yaml` (except fields that are computed later).  
  6. If fewer than 50 datasets are successfully downloaded, the script raises a `RuntimeError` and exits 1.  
  *Verification*:  
  - `python -m code.data.download_datasets` exits 0 and creates ≥ 50 rows in `data/datasets.csv`.  
  - All `source_url` entries match the `^https?://` pattern and each file has a corresponding SHA‑256 entry in `data/checksums.csv`.  

- [ ] **T003** [US1] Filter datasets: impute missing values, apply exclusion criteria, and compute normality metrics  
  *Files*: `code/data/filter_datasets.py`, `data/imputation_log.csv`, `data/exclusions.csv`, `data/datasets.csv` (updated), `data/filter_results.csv`  
  *Description*:  
  1. Stream each dataset from `data/raw/` with `chunksize=10 000`.  
  2. Exclude datasets with > 10 % missing values, `sample_size < 30`, no continuous variable, or no categorical group label (≥ 2 levels). Log exclusions to `data/exclusions.csv`.  
  3. Impute missing values: mean for variables with \|skew\| ≤ 0.5, median otherwise; record each imputation in `data/imputation_log.csv` (method, variable, imputed %).  
  4. Run the Shapiro‑Wilk test on every continuous variable; retain datasets where the **minimum** p‑value across variables is < 0.05. Store `shapiro_wilk_p`, `skewness`, `kurtosis`, and updated `status` (`processed` or `filtered_out`) back into `data/datasets.csv`.  
  5. If fewer than 50 datasets remain with `status='processed'`, raise `ValueError` and exit 1.  
  *Verification*:  
  - `python -m code.data.filter_datasets` exits 0.  
  - All rows with `status='processed'` satisfy the schema constraints (`sample_size ≥ 30`, `missing_pct ≤ 10`, `shapiro_wilk_p < 0.05`).  

- [ ] **T004** [US2] Implement three transformations (Box‑Cox, Yeo‑Johnson, **rank_based**) and store transformed data  
  *Files*: `code/data/transformations.py`, `results/transformations_log.csv`, `data/transformed/`, `code/tests/unit/test_transformations.py`  
  *Description*:  
  - Functions: `apply_boxcox(df, var)`, `apply_yeojohnson(df, var)`, `apply_rank_based(df, var)`.  
  - For Box‑Cox and Yeo‑Johnson, if any values ≤ 0, apply a minimal log‑shift (`df[var] - df[var].min() + 1e-6`) and record the intervention in `results/transformations_log.csv`.  
  - Iterate over every `processed` dataset and every continuous variable; produce three transformed Parquet files per variable named `data/transformed/<dataset_id>_<var>_<method>.parquet` where `<method>` is `box_cox`, `yeo_johnson`, or `rank_based`.  
  - Write a metadata row per transformation to `results/transformations_log.csv` conforming to `contracts/transformation.schema.yaml`.  
  *Verification*:  
  - `pytest code/tests/unit/test_transformations.py -q` passes.  
  - All files in `data/transformed/` validate against `contracts/transformed_data.schema.yaml`.  

- [ ] **T005** [US2] Pilot Type I error estimation on a single filtered dataset (dual null‑simulation)  
  *Files*: `code/analysis/type1_error.py`, `results/type1_error_pilot.csv`, `results/type1_error_pilot_validation.txt`, `results/simulation_seeds.txt`  
  *Description*:  
  - Select the first `processed` dataset.  
  - **Two null‑simulation strategies**:  
    1. Stratified label shuffling (5 000 repeats, fixed seed = 42).  
    2. Residual permutation: fit a null linear model, permute residuals, recombine with fitted values (5 000 repeats, same seed).  
  - For each strategy and each transformation (baseline + three), run the appropriate t‑test or one‑way ANOVA.  
  - Record the proportion of p‑values < 0.05 as `error_rate` for each strategy.  
  - Write detailed results to `results/type1_error_pilot.csv`.  
  - Validation file contains `error_rate`, `seed`, `n_iterations`, and a boolean `pass` indicating whether the pilot error rate falls within the nominal 0.04 – 0.06 window for **both** strategies.  
  - Append the seed record to `results/simulation_seeds.txt`.  
  *Verification*:  
  - `python -m code.analysis.type1_error --pilot` exits 0 and the validation file contains `pass=True`.  

- [ ] **T006** [US2] Full Type I error estimation across all filtered datasets (dual null‑simulation)  
  *Files*: `code/analysis/type1_error.py`, `results/type1_error_results.csv`, `results/type1_error_validation.txt`, `results/simulation_seeds.txt` (updated)  
  *Description*:  
  - For each `processed` dataset generate 5 000 label‑shuffling replicates (seed = hash(dataset_id) % 2³²) **and** 5 000 residual‑permutation replicates (same seed).  
  - Run t‑test and ANOVA on baseline and all three transformations for each replicate of each strategy.  
  - Emit a `TestResult` row (conforming to `contracts/test_result.schema.yaml`) per shuffle, per residual permutation, transformation, and test type.  
  - Aggregate per‑dataset results into `results/type1_error_results.csv` with columns `dataset_id, transformation, test_type, strategy, error_rate, n_iterations`.  
  - Additionally compute raw significance counts for α ∈ {0.01, 0.02, 0.025, 0.05, 0.075, 0.10} for later sensitivity analysis (FR‑009).  
  *Verification*:  
  - `python -m code.analysis.type1_error` exits 0.  
  - `results/type1_error_results.csv` contains ≥ 4 × 2 × 2 × N_processed rows (baseline + 3 transforms × t‑test + ANOVA × 2 strategies).  

- [ ] **T007** [US4] Simulate alternative datasets, compute empirical power, and generate analytical reference power (CI ≤ 0.02)  
  *Files*: `code/data/simulations.py`, `code/analysis/power_analysis.py`, `data/simulated_metadata.csv`, `data/simulated/`, `results/power/empirical_*.json`, `results/power/reference_*.json`  
  *Description*:  
  1. For each retained real dataset and each effect size **d** ∈ {0.2, 0.5, 0.8}, generate 1 000 simulated datasets preserving the source’s skewness and kurtosis (using `scipy.stats.skewnorm` with fitted parameters). Store metadata in `data/simulated_metadata.csv` (conforms to `contracts/simulated_dataset.schema.yaml`).  
  2. Apply baseline and the three transformations to every simulated dataset (reuse code from T004).  
  3. Run the appropriate parametric test (t‑test or ANOVA) and record a `TestResult` row for each simulation.  
  4. Compute **empirical power** as the proportion of p‑values < 0.05 and write a JSON file `results/power/empirical_<dataset_id>_<d>.json` containing `power`, `ci_lower`, `ci_upper`, `ci_half_width`, and `validation_status`.  
  5. **Reference power**: for each effect size compute the analytical power under normality assumptions using `statsmodels.stats.power.TTestIndPower` (t‑test) or `statsmodels.stats.power.FTestAnovaPower` (ANOVA). Store these values in `results/power/reference_<d>.json`.  
  6. Validate that the empirical CI half‑width ≤ 0.02; set `validation_status` to `"pass"` when satisfied, otherwise `"fail"`.  
  *Verification*:  
  - All expected JSON files exist (3 effect sizes × 4 conditions × 2 tests = 24 files).  
  - Each file contains the required keys and `validation_status` is `"pass"` only when `ci_half_width ≤ 0.02`.  

- [ ] **T008** [US3] Aggregate Type I error and power results with bootstrap confidence intervals (CI ≤ 0.02)  
  *Files*: `code/analysis/aggregation.py`, `results/aggregated_results.csv`  
  *Description*:  
  - Load `results/type1_error_results.csv` and all `results/power/empirical_*.json`.  
  - For each combination of `transformation` (baseline + 3), `test_type` (t‑test, ANOVA), and `metric` (`type1_error`, `power`), compute the mean and a 95 % bootstrap CI using 10 000 resamples (fixed seed = 123).  
  - Calculate `ci_half_width = (ci_upper - ci_lower) / 2`.  
  - Record a row conforming to `contracts/aggregated_result.schema.yaml`; add `validation_status = "pass"` if `ci_half_width ≤ 0.02`.  
  - Write the full table to `results/aggregated_results.csv`.  
  *Verification*:  
  - `python -m code.analysis.aggregation` exits 0 and the CSV contains exactly 16 rows (4 transformations × 2 tests × 2 metrics).  

- [ ] **T009** [US3] Friedman test, Bonferroni‑corrected post‑hoc, and α‑sensitivity sweep  
  *Files*: `code/analysis/inference.py`, `results/friedman_summary.txt`, `results/sensitivity_analysis.json`  
  *Description*:  
  - Perform a Friedman chi‑square test (`scipy.stats.friedmanchisquare`) on per‑dataset error rates for each test type (t‑test, ANOVA) and on per‑dataset power estimates.  
  - If the Friedman statistic cannot be computed (e.g., due to ties), fall back to pairwise Wilcoxon signed‑rank tests with Bonferroni correction.  
  - Log the overall statistic, p‑value, and any significant pairwise comparisons to `results/friedman_summary.txt`.  
  - Conduct the α‑sensitivity sweep defined in FR‑009: recompute Type I error rates for α ∈ {0.01, 0.02, 0.025, 0.05, 0.075, 0.10} using the raw counts from T006, and write a JSON array `results/sensitivity_analysis.json` conforming to `contracts/sensitivity_result.schema.yaml`.  
  *Verification*:  
  - `python -m code.analysis.inference` exits 0 and both output files are non‑empty; the summary contains at least one significant comparison (p < 0.05) or a note that none were significant.  

- [ ] **T010** [US3] Generate reproducible figures from aggregated results  
  *Files*: `code/analysis/visualize_results.py`, `results/figures/error_rates.png`, `results/figures/power_curves.png`, `results/figures/sensitivity_curves.png`  
  *Description*:  
  - `error_rates.png`: bar plot of mean Type I error by transformation and test, with 95 % bootstrap CI error bars; α = 0.05 reference line included.  
  - `power_curves.png`: line plot of power vs. effect size (small, medium, large) for each transformation and test, with CI bands.  
  - `sensitivity_curves.png`: line plot of error rate vs. α for each transformation‑test pair.  
  - Use a deterministic Matplotlib style and set `PYTHONHASHSEED=0` to guarantee byte‑identical PNGs across runs.  
  *Verification*:  
  - All three PNG files exist, are non‑empty, and a second execution of the script produces identical SHA‑256 hashes.  

- [ ] **T011** Document methods, results, and handoff to the paper pipeline  
  *Files*: `specs/001-evaluating-the-impact-of-data-transformation-sensitivity/results.md`  
  *Description*:  
  - Summarize the full pipeline, listing key artifact paths.  
  - Report concrete numbers: count of retained datasets, total simulations, observed mean Type I error and power per transformation, bootstrap CI half‑widths (≤ 0.02), and Friedman test outcomes.  
  - Explicitly note that power estimates are compared against both empirical bootstrap results and the analytical reference values from T007.  
  - Define the handoff: the paper‑stage pipeline will ingest `results/aggregated_results.csv`, `results/figures/*.png`, and this `results.md`.  
  *Verification*:  
  - File exists and all numeric statements match values in `results/aggregated_results.csv` and `results/friedman_summary.txt`.  

- [ ] **T012** End‑to‑end reproducibility, integration testing, and benchmark logging  
  *Files*: `code/tests/integration/test_pipeline.py`, `results/benchmark.log`  
  *Description*:  
  - `test_pipeline.py` loads `data/datasets.csv` and asserts ≥ 50 rows, runs `python -m code.main --stage all --dry-run` to verify command generation, then runs the full pipeline (`python -m code.main --stage all`).  
  - After completion it checks that `results/aggregated_results.csv` contains ≥ 1 row and that the three figures exist.  
  - The script records wall‑clock time to `results/benchmark.log` and asserts that total runtime < 6 h on the CI runner.  
  - Finally, it deletes any checkpoint files via `code.utils.checkpointing.delete_checkpoint` and re‑runs the pilot Type I error estimation to confirm byte‑identical output to the stored pilot CSV.  
  *Verification*:  
  - `pytest -q` passes with exit code 0.  
  - `results/benchmark.log` shows a runtime under the 6 h limit.  

---  

### Dependency Graph (simplified)

```
T001 → T002 → T003 → T004 → T005 → T006
                ↘          ↘
                 → T007 → T008 → T009 → T010 → T011 → T012
```

All scientific requirements (FR‑001 – FR‑010, SC‑001 – SC‑004) are covered, and the revised tasks directly address the reviewer’s concerns about a concrete reference power calculation, a dual null‑simulation strategy, proper CI precision, schema consistency, and parallel‑safety.  
