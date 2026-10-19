# Tasks: Quantifying the Impact of Data Cleaning on Statistical Inference  

**Inputs**: `spec.md`, `plan.md`, `research.md`, `data‑model.md`, existing contracts, and any reviewer feedback.  

**Goal**: Deliver a fully reproducible, CPU‑first pipeline that (1) downloads a verified set of public datasets covering all size‑bins and missingness levels, (2) runs baseline statistical tests, (3) applies a factorial cleaning design, (4) records delta‑metrics and robustness flags, (5) performs bootstrap variance estimation, (6) conducts sensitivity and hypothesis‑testing analyses, (7) produces final comparison artefacts and visualisations, and (8) validates every artefact against its JSON‑Schema while respecting all functional requirements (FR‑001 – FR‑028) and success criteria (SC‑001 – SC‑014).  

All tasks follow the canonical checklist format `- [ ] T### [P?] [USx?] description …` with exact artifact paths. Checked boxes (`X`) denote work already completed and verified; unchecked boxes denote work that must still be produced or corrected.

---  

## Phase 0 – Project scaffolding  

- [ ] T001 **Create project layout** – Initialise `code/`, `data/raw/`, `data/processed/`, `tests/` directories and add a `quickstart.md`.  
  *Verification*: `tests/unit/test_scaffolding.py` asserts the directories exist.  

- [ ] T002 **Initialise requirements** – Populate `requirements.txt` with `pandas`, `numpy`, `scipy`, `statsmodels`, `scikit-learn`, `matplotlib`, `seaborn`, `pytest`, `jsonschema`.  
  *Verification*: `pip install -r requirements.txt` succeeds in CI.  

- [ ] T003 **Add config** – `code/config.py` defines `RANDOM_SEED = 42`, `BOOTSTRAP_ITERATIONS = 1000`, and path helpers via `llmxive_toolkit.paths`.  
  *Verification*: Import test `tests/unit/test_config.py` checks constants exist.  

- [ ] T004 **Add lint/format config** – Include `ruff.toml` and `pyproject.toml` for Black formatting.  
  *Verification*: `ruff check .` and `black --check .` pass in CI.  

- [ ] T005 **Add .gitignore** – Exclude `__pycache__/`, `*.pyc`, `data/raw/`, `data/processed/*.tmp`, `output/figures/`, `state/`, temporary scripts.  
  *Verification*: CI ensures no ignored files are committed.  

---  

## Phase 1 – Power analysis & contract authoring  

- [ ] T006 **Power‑analysis report** – Compute a priori power for (a) a two‑sample t‑test detecting Cohen’s d = 0.5 (α = 0.05, power ≥ 0.8) and (b) a paired Wilcoxon signed‑rank test detecting a medium effect (Cohen = 0.5). Write the calculations and justification (≤ 150 words) to `power_analysis.txt`.  
  *Verification*: `tests/unit/test_power_analysis.py` checks file existence and that reported power ≥ 0.8.  

- [ ] T007 **Cleaned‑metrics schema** – Create `contracts/cleaned_metrics.schema.yaml` matching FR‑009/FR‑011/FR‑025 (numeric ≥ 3‑decimal, optional `cohens_d`, `r_squared`, `effect_size_cv`).  
  *Verification*: `tests/contract/test_cleaned_schema.py` validates the schema against a minimal example.  

- [ ] T008 **Bootstrap‑iteration enforcement** – Ensure all bootstrap calls read `config.BOOTSTRAP_ITERATIONS` and no fallback constant appears. Add static‑analysis test.  
  *Verification*: `tests/unit/test_bootstrap_config.py` fails if a fallback is detected.  

- [ ] T024 **Sample‑size justification** – Write `sample_size_justification.md` (≤ 150 words) documenting the rationale for selecting 10‑15 datasets based on prior meta‑analyses.  
  *Verification*: `tests/unit/test_sample_size_justification.py` checks file existence and word count ≤ 150.  

---  

## Phase 2 – Data acquisition & baseline analysis  

- [ ] T009 **Dataset download & validation** – Implement `code/data_loader.py` to (a) download the 12 + verified datasets (direct URLs for the five UCI CSVs, `openml.datasets.get_dataset` for the rest), (b) compute SHA‑256 checksums, (c) validate each file against `contracts/dataset.schema.yaml`, (d) extract documented outcome column, sample size, and missingness proportion, and (e) write `data/processed/dataset_metadata.json`.  
  *Verification*: `tests/integration/test_data_acquisition.py` checks all datasets appear, checksums match, and schema validation passes.  

- [ ] T019 **Citation‑validation (early)** – Run `code/citation_validator.py` immediately after data acquisition to verify all external citations (datasets, methods) before any downstream review points are awarded. Log to `logs/citation_validation.log`.  
  *Verification*: `tests/unit/test_citation_validation.py` ensures the log contains “Citation validation passed”.  

- [ ] T022 **Validate baseline metrics** – After T010 runs, validate `data/processed/baseline_metrics.json` against `contracts/baseline_metrics.schema.yaml`.  
  *Verification*: `tests/contract/test_baseline_schema.py` must pass.  

- [ ] T010 **Baseline statistical tests** – Using `code/analysis.py`, run Welch’s two‑sample t‑test (or standard t‑test when variances equal) for binary outcomes and OLS linear regression for continuous outcomes on the **raw** data. Store per‑dataset results in `data/processed/baseline_metrics.json` with fields required by `contracts/baseline_metrics.schema.yaml`.  
  *Verification*: `tests/contract/test_baseline_schema.py` validates the JSON; numeric precision test ensures ≥ 3‑decimal places.  

- [ ] T033 **Validate dataset metadata** – Validate `data/processed/dataset_metadata.json` against `contracts/dataset.schema.yaml`.  
  *Verification*: `tests/contract/test_dataset_schema.py` must pass.  

---  

## Phase 3 – Cleaning functions & factorial design  

- [ ] T011 **Cleaning primitives** – Implement in `code/cleaning.py` the three required preprocessing steps:  
  * `apply_iqr_outlier_removal(df, k=1.5)` – removes rows outside the IQR × k range, logs `rows_removed`, warns if ≥ 50 % are removed.  
  * `apply_imputation(df, strategy)` – supports `mean`, `median`, `knn` (k=5) strategies; returns `missing_before`, `missing_after`, warns if variance reduction ≥ 20 %.  
  * `apply_categorical_recoding(df)` – one‑hot encodes nominal variables with ≤ 10 categories; integer‑label encodes ordinal or high‑cardinality nominal variables.  
  Each function returns `(cleaned_df, metadata_dict)` with the fields required by FR‑010.  
  *Verification*: `tests/unit/test_cleaning.py` asserts correct behavior and presence of all metadata keys.  

- [ ] T012 **Factorial experiment driver** – In `code/main.py`, generate the full factorial combination of the three cleaning factors (outlier × imputation × recoding) **plus** the single‑factor runs. For each variant, (a) apply the cleaning pipeline, (b) run the same statistical tests as in T010, (c) compute delta‑metrics (`effect_size_change`, `ci_overlap`, `p_value_delta`, `direction`), (d) attach cleaning metadata, and (e) write an entry to `data/processed/cleaned_metrics.json`.  
  *Verification*: `tests/integration/test_factorial_pipeline.py` confirms the number of variant entries (≤ 200) and validates each entry against `contracts/cleaned_metrics.schema.yaml`.  

- [ ] T021 **Validate cleaned metrics** – After T012, validate `data/processed/cleaned_metrics.json` against `contracts/cleaned_metrics.schema.yaml`, ensuring both the primary fields and the nested `metadata` object meet FR‑009 and FR‑011.  
  *Verification*: `tests/contract/test_cleaned_schema.py` must pass.  

---  

## Phase 4 – Assumption checks & robust fallback  

- [ ] T013 **Assumption diagnostics** – Extend `code/analysis.py` to (i) run Shapiro‑Wilk normality (α = 0.05), (ii) Levene’s homoscedasticity test (α = 0.05), and (iii) a linearity check (`R² ≥ 0.7`) for continuous outcomes. Record a boolean `assumptions_met` and, when violated, automatically switch to the appropriate robust alternative (Welch’s t‑test or rank‑based regression). Populate `robust_test_used` accordingly.  
  *Verification*: `tests/unit/test_assumptions.py` forces a violation and asserts the robust alternative runs and `robust_test_used` is populated.  

---  

## Phase 5 – Bootstrap variance estimation  

- [ ] T014 **Bootstrap CI generation** – Using `code/bootstrap.py`, perform **exactly** `config.BOOTSTRAP_ITERATIONS` (default 1000) resamples for each cleaning variant to obtain a bootstrap confidence interval for the primary effect‑size metric. Write results to `data/processed/bootstrap_metrics.json`.  
  *Verification*: `tests/unit/test_bootstrap_precision.py` checks that the `iterations` field equals `config.BOOTSTRAP_ITERATIONS` and that CI bounds have ≥ 3‑decimal precision.  

- [ ] T025 **Validate bootstrap metrics** – Validate `data/processed/bootstrap_metrics.json` against `contracts/bootstrap_metrics.schema.yaml`.  
  *Verification*: `tests/contract/test_bootstrap_schema.py` must pass.  

---  

## Phase 6 – Sensitivity analysis & robust fallback  

- [ ] T015 **Stratified sensitivity metrics** – Using size‑bin definitions (`<50`, `50‑200`, `>200`) and missingness levels (`none`, `MCAR`, `MAR`, `MNAR`), compute per‑bin averages of `effect_size_change` and `ci_overlap`. Run a two‑way ANOVA (or Kruskal‑Wallis fallback if ANOVA assumptions fail) and store results in `data/processed/sensitivity_metrics.json`.  
  *Verification*: `tests/contract/test_sensitivity_schema.py` validates the JSON; an additional test aborts the pipeline if any bin lacks a dataset.  

- [ ] T032 **Permutation‑based false‑positive‑rate estimation** – For each dataset, cleaning variant, and missingness mechanism, generate at least 1000 outcome‑shuffled permutations, rerun the full cleaning pipeline, and compute the proportion of tests with p < 0.05 to estimate the false‑positive rate. Record results in `data/processed/null_fpr_metrics.json`. The permutation count must equal `config.BOOTSTRAP_ITERATIONS` and no fallback is permitted.  
  *Verification*: `tests/integration/test_null_fpr_generation.py` checks that the file exists, conforms to `contracts/null_fpr_metrics.schema.yaml`, and that `iterations` matches `config.BOOTSTRAP_ITERATIONS`.  

- [ ] T023 **Automatic dataset acquisition** – If after T009 any size‑bin or missingness‑level bin is empty, automatically download a suitable public dataset (using the same verified download logic) to satisfy FR‑013. Update `dataset_metadata.json` accordingly.  
  *Verification*: `tests/integration/test_bin_coverage.py` confirms all bins are populated before proceeding.  

- [ ] T026 **Validate sensitivity metrics** – Validate `data/processed/sensitivity_metrics.json` against `contracts/sensitivity_metrics.schema.yaml`.  
  *Verification*: `tests/contract/test_sensitivity_schema.py` must pass.  

- [ ] T034 **Validate null‑FPR metrics** – After T032, run schema validation of `data/processed/null_fpr_metrics.json` against `contracts/null_fpr_metrics.schema.yaml`.  
  *Verification*: `tests/contract/test_null_fpr_schema.py` must pass.  

- [ ] T031 **Effect‑size stability metric** – Compute the coefficient of variation (`effect_size_cv`) for the primary effect‑size metric across all cleaning variants per dataset, store it in each `cleaned_metrics.json` entry, and enforce that `effect_size_cv ≤ 0.2`.  
  *Verification*: `tests/unit/test_effect_size_cv.py` checks the field exists, is ≤ 0.2, and has ≥ 3‑decimal precision.  

- [ ] T029 **Numeric precision enforcement** – Scan all JSON artefacts (`baseline_metrics.json`, `cleaned_metrics.json`, `bootstrap_metrics.json`, `sensitivity_metrics.json`, `hypothesis_test_results.json`, `comparison_report.json`) and assert that every numeric value is rounded to at least three decimal places (SC‑002).  
  *Verification*: `tests/unit/test_precision.py` fails if any value has fewer than three decimal digits.  

- [ ] T030 **Raw p‑value verification** – Confirm that every p‑value recorded in `baseline_metrics.json` and `cleaned_metrics.json` is the raw value from the statistical test with **no** family‑wise error correction applied (SC‑007).  
  *Verification*: `tests/unit/test_raw_pvalues.py` ensures no correction flag is set and that values match the test output.  

---  

## Phase 7 – Hypothesis testing & two‑way ANOVA  

- [ ] T016 **Wilcoxon signed‑rank tests (H1)** – For each cleaning factor (outlier removal, imputation, recoding) compute a paired Wilcoxon test on the vector of `effect_size_change` across all datasets. Record the test statistic, raw p‑value, Holm‑adjusted p‑value (kept for schema compatibility), and a boolean `reject_null` in `data/processed/hypothesis_test_results.json`.  
  *Verification*: `tests/unit/test_hypothesis_h1.py` checks schema compliance and that the adjustment step is performed.  

- [ ] T017 **Stability correlation tests (H2)** – Compute Spearman correlations between the presence of **imputation** and **categorical recoding** (binary flags) and the two stability metrics `ci_overlap` and `effect_size_cv`. Append these correlation results (coefficient, p‑value) to the same `hypothesis_test_results.json`.  
  *Verification*: `tests/unit/test_hypothesis_h2.py` validates the additional fields against an extended schema.  

- [ ] T027 **Validate hypothesis‑test results** – Validate `data/processed/hypothesis_test_results.json` against `contracts/hypothesis_test_results.schema.yaml`.  
  *Verification*: `tests/contract/test_hypothesis_schema.py` must pass.  

---  

## Phase 8 – Final aggregation, visualisation, and hand‑off  

- [ ] T018 **Comparison report & figures** – Aggregate all delta‑metrics into `data/processed/comparison_report.json` (overall means, per‑variant summaries) conforming to `contracts/comparison_report.schema.yaml`. Generate two visualisations:  
  * `output/figures/forest_plot.png` (300 dpi PNG) showing p‑value shifts per variant.  
  * `output/figures/heatmap.svg` (SVG) displaying CI‑width changes across size‑bins and missingness levels.  
  *Verification*: `tests/integration/test_report_generation.py` asserts the JSON validates, both figure files exist, and their resolutions/formats match specifications.  

- [ ] T028 **Validate comparison report** – Validate `data/processed/comparison_report.json` against `contracts/comparison_report.schema.yaml`.  
  *Verification*: `tests/contract/test_comparison_schema.py` must pass.  

---  

## Phase 9 – End‑to‑end reproducibility check  

- [ ] T020 **Full pipeline smoke test** – From a clean checkout, execute `python -m code.main --stage full`. The run must (a) download datasets, (b) perform baseline and all cleaning variants, (c) produce every JSON artefact and figure, (d) pass all schema validators, and (e) exit with status 0.  
  *Verification*: `tests/integration/test_full_pipeline_smoke.py` runs the command in a temporary environment and asserts exit code 0 and presence of all expected outputs.  

---  

### Summary of pending work  

| Task ID | What must be delivered | Current status |
|--------|------------------------|----------------|
| T006 | `power_analysis.txt` (calculations + justification) | ☐ |
| T007 | `contracts/cleaned_metrics.schema.yaml` | ☐ |
| T008 | Bootstrap code uses `config.BOOTSTRAP_ITERATIONS` only | ☐ |
| T009 | `code/data_loader.py` + `dataset_metadata.json` (validated) | ☐ |
| T010 | `baseline_metrics.json` (validated) | ☐ |
| T011 | Cleaning functions with metadata returns | ☐ |
| T012 | Factorial variant generation + `cleaned_metrics.json` (validated) | ☐ |
| T013 | Assumption checks & robust fallback (flags & `robust_test_used`) | ☐ |
| T014 | `bootstrap_metrics.json` (exact 1000 iterations, no fallback) | ☐ |
| T015 | `sensitivity_metrics.json` (two‑way ANOVA) | ☐ |
| T016 | `hypothesis_test_results.json` – Wilcoxon (H1) | ☐ |
| T017 | `hypothesis_test_results.json` – stability correlations (H2) | ☐ |
| T018 | `comparison_report.json`, forest plot, heatmap | ☐ |
| T019 | Citation‑validation log (run early) | ☐ |
| T020 | End‑to‑end smoke‑test success | ☐ |
| T021 | Validation of `cleaned_metrics.json` (FR‑009/FR‑011) | ☐ |
| T022 | Validation of `baseline_metrics.json` (FR‑008) | ☐ |
| T023 | Automatic dataset acquisition for empty bins (FR‑013) | ☐ |
| T024 | `sample_size_justification.md` (FR‑023) | ☐ |
| T025 | Validation of `bootstrap_metrics.json` (FR‑026) | ☐ |
| T026 | Validation of `sensitivity_metrics.json` (FR‑027) | ☐ |
| T027 | Validation of `hypothesis_test_results.json` (FR‑028) | ☐ |
| T028 | Validation of `comparison_report.json` (FR‑015) | ☐ |
| T029 | Enforce ≥ 3‑decimal precision (SC‑002) | ☐ |
| T030 | Verify raw p‑values are uncorrected (SC‑007) | ☐ |
| T031 | Compute `effect_size_cv` ≤ 0.2 (SC‑012, FR‑022) | ☐ |
| T032 | Permutation‑based false‑positive‑rate estimation (`null_fpr_metrics.json`) | ☐ |
| T033 | Validation of `dataset_metadata.json` (FR‑014) | ☐ |
| T034 | Validate `null_fpr_metrics.json` (schema) | ☐ |

All other tasks marked with **[X]** have been completed, pass their respective verification tests, and require no further action.  

---  

*End of `tasks.md`*.  