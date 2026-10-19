# Tasks: Quantifying the Impact of Data Cleaning on Statistical Inference  

**Inputs**: `spec.md`, `plan.md`, `research.md`, `data‑model.md`, all contract files, and the latest reviewer feedback.  

The checklist below enumerates the minimal set of research‑stage tasks required to satisfy **every functional requirement (FR‑001 – FR‑028)**, **success criterion (SC‑001 – SC‑014)** and the concrete reviewer action items.  
Each task is written in the canonical `- [ ] T### [P?] [USx?] …` form, lists the exact artifact paths it creates or modifies, and specifies an automated verification step (unit‑test, schema‑validation, or runtime check).  Tasks are ordered to respect data‑flow dependencies.

---

## Phase 0 – Project hygiene (single consolidation task)

- [ ] T001 **Consolidate code base & clean filesystem** –  
  *Move* all utility scripts (`code/run_lint.py`, `code/run_quickstart_validation.py`) into `code/scripts/`; *delete* any orphaned `t*.py` experiment scripts after confirming their logic has been merged into the canonical modules (`analysis.py`, `cleaning.py`, `reporting.py`, `main.py`). Update `.gitignore` to exclude `t*.py` and temporary scratch files.  
  *Verification*: `tests/unit/test_filesystem_hygiene.py` asserts the absence of `t*.py` files, the presence of `code/scripts/`, and that imports in `main.py` succeed.

- [X] T019 **Pin random seeds for reproducibility** – Add a module `code/random_seeds.py` that sets `numpy.random.seed(42)`, `random.seed(42)`, and uses `random_state=42` for all scikit‑learn functions. Import this module at the start of `code/main.py`.  
  *Verification*: `tests/unit/test_random_seeds.py` checks that the seed values are set and that repeated runs produce identical numeric outputs.

---

## Phase 1 – Foundations & power justification

- [X] T002 **Power‑analysis report (US‑003)** – Compute a priori power for (a) a two‑sample t‑test detecting Cohen’s d = 0.5 (α = 0.05, power ≥ 0.8) and (b) a paired Wilcoxon signed‑rank test detecting a medium effect (Cohen = 0.5). Write the calculations and a ≤ 150‑word justification to `power_analysis.txt`.  
  *Verification*: `tests/unit/test_power_analysis.py` checks file existence, parses the reported power values, and asserts they are ≥ 0.8.

- [ ] T003 **Sample‑size justification (US‑003)** – Document the rationale for selecting 10‑15 datasets (≤ 150 words) in `sample_size_justification.md`, citing the meta‑analysis that informed the choice.  
  *Verification*: `tests/unit/test_sample_size_justification.py` confirms the file exists and word count ≤ 150.

- [X] T004 **Cleaned‑metrics JSON‑Schema (FR‑009, FR‑011, FR‑025)** – Create `contracts/cleaned_metrics.schema.yaml` that exactly matches the fields required by the specification (including optional `cohens_d`, `r_squared`, `effect_size_cv`).  
  *Verification*: `tests/contract/test_cleaned_schema.py` validates the schema against a minimal compliant JSON example.

---

## Phase 2 – Data acquisition & baseline analysis

- [ ] T005 **Download & validate raw datasets (FR‑001, FR‑005, FR‑007, FR‑014)** – Implement `code/data_loader.py` to (a) download the 12 verified datasets (direct URLs for the five UCI CSVs and `openml.datasets.get_dataset` for the remainder), (b) compute SHA‑256 checksums, (c) validate each raw file against `contracts/dataset.schema.yaml`, (d) extract the documented outcome column, sample size, and missingness proportion, and (e) write `data/processed/dataset_metadata.json`.   <!-- FAILED-IN-EXECUTION: code/data_loader.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/data_loader.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/data_loader.py exit=1 -->
  *Verification*: `tests/integration/test_data_acquisition.py` checks that all datasets appear, checksums match, and schema validation passes.

- [ ] T020 **Record raw‑file checksums in project state (Constitution III)** – After successful download, update `state/projects/PROJ-256-quantifying-the-impact-of-data-cleaning-.yaml` with a map `artifact_hashes` containing each raw dataset’s SHA‑256 checksum.  
  *Verification*: `tests/unit/test_state_checksum_record.py` confirms the YAML contains the expected hash entries.

- [ ] T021 **Automatic bin‑coverage dataset acquisition (FR‑013)** – After initial download, inspect size bins (`<50`, `50‑200`, `>200`) and missingness levels (`none`, `MCAR`, `MAR`, `MNAR`). If any combination lacks ≥ 1 dataset, automatically fetch an additional public dataset that satisfies the missing criteria, update `dataset_metadata.json`, and re‑run the relevant downstream tasks.  
  *Verification*: `tests/integration/test_bin_coverage_acquisition.py` asserts that after execution every bin‑missingness pair has at least one dataset.

- [ ] T006 **Citation‑validation (Principle II) (US‑003)** – Run `code/citation_validator.py` immediately after data download to verify all external dataset and method citations. Log the outcome to `logs/citation_validation.log`.  
  *Verification*: `tests/unit/test_citation_validation.py` asserts the log contains “Citation validation passed”.

- [ ] T007 **Baseline statistical tests (FR‑001, FR‑010, FR‑018, FR‑008)** – Using `code/analysis.py`, run Welch’s two‑sample t‑test (or standard t‑test when variances equal) for binary outcomes and OLS linear regression for continuous outcomes on the **raw** data. Store per‑dataset results in `data/processed/baseline_metrics.json` conforming to `contracts/baseline_metrics.schema.yaml`.  
  *Verification*: `tests/contract/test_baseline_schema.py` validates the JSON and checks numeric precision (≥ 3‑decimal places).

---

## Phase 3 – Cleaning primitives & factorial pipeline

- [ ] T008 **Cleaning functions with metadata (FR‑002, FR‑003, FR‑004, FR‑010, FR‑011)** – Implement in `code/cleaning.py` the three required primitives:  
  * `apply_iqr_outlier_removal(df, k=1.5)` – returns `(cleaned_df, metadata)` with `rows_removed`.  
  * `apply_imputation(df, strategy)` – supports `mean`, `median`, `knn` (k=5); returns `missing_before`, `missing_after`, `variance_reduction`.  
  * `apply_categorical_recoding(df)` – one‑hot encodes nominal ≤ 10 categories, integer‑label encodes others.  
  Each function must return a metadata dict containing **all** keys required by FR‑010.  
  *Verification*: `tests/unit/test_cleaning.py` checks return types, presence of metadata keys, and that warnings are raised when removal ≥ 50 % or variance reduction ≥ 20 %.

- [ ] T010 **Assumption diagnostics & robust fallback (FR‑018, FR‑006)** – Augment `code/analysis.py` to perform Shapiro‑Wilk normality, Levene homoscedasticity, and linearity (R² ≥ 0.7) checks. Record `assumptions_met`; when violated, automatically switch to the appropriate robust alternative (Welch’s t‑test or rank‑based regression) and populate `robust_test_used`.  
  *Verification*: `tests/unit/test_assumptions.py` forces violations and asserts that robust tests run and the fields are correctly populated.

- [ ] T009 **Factorial experiment driver (FR‑020, FR‑021, FR‑022, FR‑009, FR‑011)** – Extend `code/main.py` to generate the full factorial combination of the three cleaning factors (outlier × imputation × recoding) **plus** the three single‑factor runs. For each variant:  
  1. Apply the selected cleaning steps (using the functions from T008).  
  2. Run the same statistical tests as in T007 (which now include assumption diagnostics from T010).  
  3. Compute delta‑metrics (`effect_size_change`, `ci_overlap`, `p_value_delta`, `direction`).  
  4. Attach the cleaning metadata.  
  5. Compute and store the primary effect‑size metric: `cohens_d` for t‑test variants and `r_squared` for regression variants.  
  6. Write a record to `data/processed/cleaned_metrics.json`.  
  7. **Validate** each entry against `contracts/cleaned_metrics.schema.yaml`.  
  *Verification*: `tests/integration/test_factorial_pipeline.py` confirms the number of variant entries (≤ 200), validates each entry against the schema, and checks that `cohens_d`/`r_squared` fields are present where appropriate.

---

## Phase 4 – Resampling, sensitivity & hypothesis testing

- [ ] T011 **Bootstrap confidence intervals (FR‑012, FR‑024, FR‑026)** – Using `code/bootstrap.py`, perform **exactly** `config.BOOTSTRAP_ITERATIONS` (default 1000) resamples for each cleaning variant to obtain a bootstrap CI for the primary effect‑size metric. Write results to `data/processed/bootstrap_metrics.json`. Afterwards, validate the file against `contracts/bootstrap_metrics.schema.yaml`.  
  *Verification*: `tests/unit/test_bootstrap_config.py` fails if any fallback iteration count is present; `tests/unit/test_bootstrap_schema.py` checks schema compliance; `tests/unit/test_bootstrap_precision.py` ensures the `iterations` field equals `config.BOOTSTRAP_ITERATIONS` and that CI bounds have ≥ 3‑decimal precision.

- [ ] T012 **Sensitivity analysis & two‑way ANOVA (FR‑006, FR‑019, FR‑027)** – Compute per‑size‑bin (`<50`, `50‑200`, `>200`) and per‑missingness‑level (`none`, `MCAR`, `MAR`, `MNAR`) averages of `effect_size_change` and `ci_overlap`. Run a two‑way ANOVA; if ANOVA assumptions fail, fall back to Kruskal‑Wallis. Store the results in `data/processed/sensitivity_metrics.json` and **validate** against `contracts/sensitivity_metrics.schema.yaml`.  
  *Verification*: `tests/contract/test_sensitivity_schema.py` validates the JSON; `tests/integration/test_bin_coverage.py` aborts the pipeline if any bin lacks ≥ 1 dataset.

- [ ] T013 **Permutation‑based false‑positive‑rate (FR‑006, FR‑028)** – For every dataset‑variant‑missingness combination, generate **≥ 1000** outcome‑shuffled permutations (using the same `config.BOOTSTRAP_ITERATIONS` count), re‑run the full cleaning‑analysis pipeline, and compute the proportion of tests with p < 0.05. Record `null_fpr_metrics.json` conforming to its schema.  
  *Verification*: `tests/integration/test_null_fpr_generation.py` checks file existence, schema compliance, and iteration count.

- [ ] T014 **Effect‑size stability metric (FR‑022, SC‑012)** – Compute the coefficient of variation (`effect_size_cv`) of the primary effect‑size metric across all cleaning variants for each dataset; store the value in each entry of `cleaned_metrics.json` and enforce `effect_size_cv ≤ 0.2`.  
  *Verification*: `tests/unit/test_effect_size_cv.py` asserts the field exists, is ≤ 0.2, and rounded to ≥ 3‑decimal places.

- [ ] T015 **Hypothesis testing (FR‑017, FR‑021, FR‑028)** –  
  *H1*: For each cleaning factor (outlier removal, imputation, recoding) perform a paired Wilcoxon signed‑rank test on the vector of `effect_size_change` across all datasets. Record test statistic, raw p‑value, Holm‑adjusted p‑value (kept for schema compatibility), and `reject_null` in `data/processed/hypothesis_test_results.json`.  
  *H2*: Compute Spearman correlations between the binary presence of **imputation** and **recoding** and the stability metrics `ci_overlap` and `effect_size_cv`; append these correlation results to the same JSON file.  
  *Validation*: After generation, validate `hypothesis_test_results.json` against `contracts/hypothesis_test_results.schema.yaml`.  
  *Verification*: `tests/unit/test_hypothesis_h1.py` and `tests/unit/test_hypothesis_h2.py` validate schema compliance and that the statistical values are derived from the actual data (no hard‑coded numbers).

---

## Phase 5 – Aggregation, visualisation, and reproducibility

- [ ] T016 **Comparison report & figures (FR‑015, SC‑003)** – Aggregate all delta‑metrics into `data/processed/comparison_report.json` conforming to `contracts/comparison_report.schema.yaml`. Generate:  
  * `output/figures/forest_plot.png` (300 dpi PNG) showing per‑variant p‑value shifts.  
  * `output/figures/heatmap.svg` (SVG) visualising CI‑width changes across size bins and missingness levels.  
  *Verification*: `tests/integration/test_report_generation.py` asserts the JSON validates, both figure files exist, and their formats/resolutions match the specification.

- [ ] T017 **Numeric‑precision & raw‑p‑value enforcement (SC‑002, SC‑007)** – Run a project‑wide scan of all JSON artefacts (`baseline_metrics.json`, `cleaned_metrics.json`, `bootstrap_metrics.json`, `sensitivity_metrics.json`, `hypothesis_test_results.json`, `comparison_report.json`) to ensure every numeric value is rounded to at least three decimal places and that every recorded p‑value is the raw test output (no family‑wise correction).  
  *Verification*: `tests/unit/test_precision.py` fails if any value has fewer than three decimal digits; `tests/unit/test_raw_pvalues.py` checks that no correction flag is set and that the values match the test outputs.

- [ ] T018 **Full‑pipeline smoke test (US‑001, US‑002, US‑003)** – From a clean checkout, execute `python -m code.main --stage full`. The run must (a) download datasets, (b) perform baseline and all cleaning variants, (c) produce every JSON artefact and figure, (d) pass all schema validators, and (e) exit with status 0.  
  *Verification*: `tests/integration/test_full_pipeline_smoke.py` runs the command in an isolated environment and asserts exit code 0 and presence of all expected outputs.

---

### Summary of pending work

| Task ID | Artifact(s) produced / modified | Status |
|--------|--------------------------------|--------|
| T001 | filesystem cleanup, `.gitignore` | ☐ |
| T019 | `code/random_seeds.py`, seed imports | ☐ |
| T002 | `power_analysis.txt` | ☐ |
| T003 | `sample_size_justification.md` | ☐ |
| T004 | `contracts/cleaned_metrics.schema.yaml` | ☐ |
| T005 | dataset download, `data/processed/dataset_metadata.json` | ☐ |
| T020 | update `state/projects/PROJ-256-...yaml` with checksums | ☐ |
| T021 | automatic bin‑coverage acquisition | ☐ |
| T006 | `logs/citation_validation.log` | ☐ |
| T007 | `data/processed/baseline_metrics.json` | ☐ |
| T008 | `code/cleaning.py` (functions + metadata) | ☐ |
| T010 | `code/analysis.py` assumption checks, robust fallback | ☐ |
| T009 | `code/main.py` factorial driver, `data/processed/cleaned_metrics.json` (with `cohens_d`, `r_squared`, schema validation) | ☐ |
| T011 | `data/processed/bootstrap_metrics.json` (bootstrap CI, schema validation) | ☐ |
| T012 | `data/processed/sensitivity_metrics.json` (ANOVA/KW, schema validation) | ☐ |
| T013 | `data/processed/null_fpr_metrics.json` | ☐ |
| T014 | `cleaned_metrics.json` (adds `effect_size_cv`) | ☐ |
| T015 | `data/processed/hypothesis_test_results.json` (Wilcoxon, correlations, schema validation) | ☐ |
| T016 | `data/processed/comparison_report.json`, `output/figures/forest_plot.png`, `output/figures/heatmap.svg` | ☐ |
| T017 | project‑wide numeric‑precision & raw‑p‑value check | ☐ |
| T018 | end‑to‑end smoke‑test execution | ☐ |

All unchecked tasks must be implemented, validated, and pass their associated automated tests before the project can advance to the next stage.  

---  

*End of `tasks.md`*.  