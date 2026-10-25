# Tasks: Statistical Properties of Integer Partitions Into Distinct Prime Summands  

**Input**: `spec.md`, `plan.md`, `research.md` (all under `specs/001-statistical-properties-of-integer-partitions-into-distinct-prime-summands/`)  
**Goal**: Produce a fully reproducible end‑to‑end pipeline that (1) computes exact distinct‑prime partition counts up to \(n_{\max}=50{,}000\), (2) evaluates the pure‑analytic Meinardus asymptotic, (3) engineers prime‑density features, (4) fits a rigorously‑validated OLS regression, (5) reports cross‑validated performance and visualisations, and (6) documents the workflow for external reuse.  

All artefacts are written under the project‑owned directories `data/`, `code/`, `tests/`, or `docs/`.  No task writes outside these locations.

---

## Phase 1 – Foundational data generation  

- [ ] T001 Generate prime list up to 50 000  
  *Create* `code/generate_primes.py` implementing the Sieve of Eratosthenes.  
  *Output* `data/raw/primes_up_to_50000.csv` with a header `prime`.  
  *Verification*: file exists, contains exactly 5 133 rows (π(50 000)=5133), and a SHA‑256 checksum is printed to stdout.

- [ ] T002 Produce reference partition counts for validation ( \(n\le100\) )  
  *Create* `code/generate_reference.py` that runs the same DP algorithm as the main generator but stops at 100.  
  *Output* `tests/data/reference_values.csv` with columns `n,p_P_n`.  
  *Verification*: the first 20 rows match the table in **SC‑003** of the specification; a pytest unit test (`tests/test_reference_validation.py`) asserts exact equality.

- [ ] T003 Compute exact distinct‑prime partition counts for the full range  
  *Create* `code/generate_partitions.py` (see T031 for documentation).  
  *Output* `data/raw/partition_counts.csv` with columns `n,p_P_n`.  
  *Verification*: file has 50 001 rows (including n=0), all `p_P_n` are non‑negative integers, and rows \(n\le100\) match `tests/data/reference_values.csv`.

- [ ] T004 Add comprehensive docstring to `generate_partitions.py` (FR‑012)  
  *Edit* `code/generate_partitions.py` to include a top‑level docstring that (i) writes the generating function \(\displaystyle G(q)=\prod_{p\in\mathbb{P}}(1+q^{p})\), (ii) contrasts it with the unrestricted partition generating function \(\prod_{k\ge1}(1-q^{k})^{-1}\), and (iii) outlines the DP recurrence and memory‑optimisation strategy.  
  *Verification*: `grep -i "generating function"` on the file returns the expected description; the docstring is at least three sentences long.

- [ ] T031 Add comprehensive docstring to `generate_partitions.py` (FR‑012)  
  *Create* or *extend* `code/generate_partitions.py` with the required multi‑sentence docstring describing the generating function, the distinct‑prime constraint, and the DP algorithm. This task ensures the documentation requirement is explicitly captured.  
  *Verification*: same as T004 – docstring presence is verified by grep and length check.

---

## Phase 2 – Analytic baseline and feature engineering  

- [ ] T005 Evaluate the pure‑analytic Meinardus asymptotic \(Q_{\text{as}}(n)\)  
  *Create* `code/compute_baseline.py` that implements the leading‑order term of Meinardus’ theorem for distinct prime parts (no density predictors).  
  *Output* `data/raw/baseline_values.csv` with columns `n,Q_as_n`.  
  *Verification*: all `Q_as_n` > 0; values < \(10^{-10}\) are clamped to \(10^{-10}\) before logging; a pytest test (`tests/test_baseline.py`) checks positivity for a random sample of 100 n‑values.

- [ ] T006 Feature engineering – compute residuals and density predictors  
  *Create* `code/feature_engineering.py` that merges `partition_counts.csv` and `baseline_values.csv`, then adds:  
  • `R_n = log(p_P_n) - log(Q_as_n)` (sentinel ‑9999 when either argument ≤ 0)  
  • `pi_n` = prime‑counting function π(n) (from the prime list)  
  • `inv_log_n = 1 / log(n)` (n ≥ 2)  
  • `cum_density = Σ_{p≤n} 1/p` (cumulative reciprocal‑prime sum)  
  • `gap_n` = length of the prime gap that contains n (distance between the next and previous prime; for a prime n use the gap to the next prime).  
  *Output* `data/processed/features.csv` with columns `n,p_P_n,Q_as_n,R_n,pi_n,inv_log_n,cum_density,gap_n`.  
  *Verification*: no missing values; sentinel ‑9999 appears only where required; a checksum is printed.

- [ ] T016b Ensure `features.csv` contains required columns and add non‑null test (FR‑013)  
  *Create* `tests/test_features_non_null.py` that loads `data/processed/features.csv` and asserts that columns `pi_n`, `inv_log_n`, `cum_density`, and `gap_n` contain no NaN/None values.  
  *Verification*: test file exists and passes after `feature_engineering.py` runs; also validates that `features.csv` has exactly the columns `n,p_P_n,Q_as_n,R_n,pi_n,inv_log_n,cum_density,gap_n`.

- [ ] T007 Unit test for non‑null feature columns (legacy)  
  *Create* `tests/test_feature_validation.py` containing a single test function `test_features_non_null` (duplicate of T016b for backward compatibility).  
  *Verification*: the test file exists and `pytest -q` reports the test as passed after `feature_engineering.py` runs.

---

## Phase 3 – Statistical modelling  

- [ ] T008 Fit ordinary‑least‑squares regression with VIF handling (FR‑005)  
  *Create* `code/fit_model.py` that:  
  • Loads `features.csv` (excluding rows with `R_n == -9999`).  
  • Computes Variance‑Inflation‑Factor for each predictor; if any VIF > 5, orthogonalises the offending predictor against the others (or drops the highest‑VIF predictor).  
  • Fits an OLS model `R_n ~ pi_n + inv_log_n + cum_density + gap_n`.  
  • Calculates HAC‑adjusted (Newey‑West) standard errors.  
  • Applies Benjamini‑Hochberg FDR correction to the raw p‑values.  
  • Performs a power analysis targeting α = 0.05, power = 0.80 (accounts for autocorrelation).  
  *Output* `data/processed/model_results.json` conforming to `model_output.schema.yaml` **and containing a top‑level `power_analysis` object** (the schema does not enforce this field).  
  *Verification*: the JSON contains all required schema keys **and** includes a non‑empty `power_analysis` field; a pytest test (`tests/test_model_output.py`) validates the schema and the presence of `power_analysis`.

- [ ] T009 Fit intercept‑only null model for comparison (FR‑005)  
  *Create* `code/fit_null_model.py` that loads the same feature set and fits a regression with only an intercept.  
  *Output* `data/processed/null_model_results.json` (same schema, but only `r_squared` and `mse_cv`).  
  *Verification*: `model_results.json` and `null_model_results.json` are both valid against the schema and the null model’s `r_squared` is ≤ the full model’s `r_squared`.

- [ ] T010 10‑fold time‑series cross‑validation (FR‑006)  
  *Create* `code/cross_validate.py` that uses `sklearn.model_selection.TimeSeriesSplit(n_splits=10)` on the cleaned feature set, refits the OLS model on each training fold, and records the held‑out MSE.  
  *Update* `model_results.json` with fields `cv_mse_per_fold` (list of 10 floats) and `mean_cv_mse`.  
  *Verification*: the JSON contains both fields; a pytest test (`tests/test_cross_validation.py`) checks list length is 10 and that `mean_cv_mse` equals the arithmetic mean of the list.

- [ ] T011 Generate diagnostic visualisation (FR‑007)  
  *Create* `code/visualize.py` that:  
  • Plots `n` vs. raw residuals `R_n` (blue) and the fitted correction term (orange).  
  • Overlays vertical markers at prime‑gap boundaries using `gap_n`.  
  • Saves the figure as `data/processed/residuals_plot.png`.  
  *Verification*: the PNG file is created, its dimensions are ≥ 800 × 600 px, and a pytest image‑hash test (`tests/test_visualization.py`) confirms the file is not empty.

- [ ] T012 Assemble a short analysis report (hand‑off)  
  *Create* `docs/residual_error_term_report.md` summarising:  
  – Methodology (DP algorithm, baseline formula)  
  – Table of selected residual values (e.g., every 5 000 th n)  
  – Results of the regression (coefficients, significance, R²)  
  – Cross‑validation statistics  
  – Visual interpretation of the plot from T011.  
  *Verification*: the markdown file contains the required sections and links to the artefacts (`features.csv`, `model_results.json`, `residuals_plot.png`).

- [ ] T018 Document power‑analysis inclusion (FR‑010)  
  *Create* a short markdown `docs/power_analysis.md` describing the methodology, assumptions, and the fact that the resulting statistics are written into `model_results.json` under a `power_analysis` key (even though the current schema does not formalise it). This satisfies the reporting requirement while the schema update is deferred to a future amendment.  
  *Verification*: the document exists and is referenced from `docs/residual_error_term_report.md`.

---

## Phase 4 – Orchestration, testing, and documentation  

- [ ] T013 End‑to‑end pipeline driver  
  *Create* `code/main.py` that sequentially calls the scripts: `generate_primes.py → generate_partitions.py → compute_baseline.py → feature_engineering.py → fit_model.py → fit_null_model.py → cross_validate.py → visualize.py`.  
  *Verification*: running `python code/main.py` completes without error, prints a summary of artefacts created, and the total wall‑clock time (measured with `time`) is ≤ 6 h on the CI runner.

- [ ] T014 Quick‑start guide  
  *Update* `docs/quickstart.md` with a reproducible command‑line snippet (`python code/main.py`) and a list of required Python packages (pointing to `requirements.txt`).  
  *Verification*: the guide builds successfully when followed on a fresh clone (manual check).

- [ ] T015 Full test suite execution  
  *Add* any missing pytest files so that `pytest -q` runs at least the following tests: `test_reference_validation.py`, `test_partition_logic.py`, `test_feature_validation.py`, `test_baseline.py`, `test_model_output.py`, `test_cross_validation.py`, `test_visualization.py`.  
  *Verification*: CI reports “100 % passed” for all tests.

- [ ] T016 Resource‑monitoring wrapper (SC‑004)  
  *Create* `code/monitor.py` that can be imported by any script to enforce a peak‑RAM limit of 6 GB and a wall‑time limit of 6 h (using `resource` on Unix). Each script should call `monitor.enforce_limits()` at start.  
  *Verification*: when a script exceeds the limits, it aborts with a clear error message; a unit test (`tests/test_monitor.py`) simulates a memory‑heavy operation and expects a `RuntimeError`.

- [ ] T017 Pin random seeds for reproducibility (Constitution I)  
  *Create* `code/seed.py` that defines a function `set_seed(seed: int = 42)` which sets the Python, NumPy, and any other library RNGs. All scripts will import and call this at the start. Update `requirements.txt` if needed.  
  *Verification*: each script prints the seed used; a pytest test (`tests/test_seed.py`) checks that repeated runs produce identical deterministic outputs for a deterministic sub‑routine.

- [ ] T019 Document power‑analysis inclusion (FR‑010) – *moved to T018* (kept for historical completeness)  
  *Note*: This task has been merged into T018; no separate implementation needed.
