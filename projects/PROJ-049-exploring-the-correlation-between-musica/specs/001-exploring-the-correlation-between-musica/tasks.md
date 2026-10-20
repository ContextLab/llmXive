# Tasks: Exploring the Correlation Between Musical Preference and Personality Traits

**Inputs**: `spec.md`, `plan.md`, existing contracts, and reviewer feedback.  
**Goal**: Deliver a reproducible end‑to‑end analysis that answers the research question using only real, verified datasets, and produces validated statistical artefacts, visualisations, and a final report.

---

## Phase 0 – Project scaffolding (US‑1)

- [ ] **T001** [P] [US‑1] **Create project directory layout**  
  Create the following folders at the repository root: `data/raw/`, `data/processed/`, `results/`, `logs/`, `code/`, `tests/`.  
  **Verification**: Run `python -c "import pathlib, sys; assert all(pathlib.Path(p).is_dir() for p in ['data/raw','data/processed','results','logs','code','tests'])"`; the command must exit with status 0.

- [ ] **T002** [P] [US‑1] **Add package initialisers**  
  Add empty `__init__.py` files in `code/` and `tests/`.  
  **Verification**: `ls code/__init__.py tests/__init__.py` returns the two paths and their size is 0 bytes.

- [ ] **T003** **Pin project dependencies**  
  Create `requirements.txt` containing exact versions for the scientific stack (`pandas==2.2.2`, `numpy==1.26.4`, `scipy==1.13.0`, `statsmodels==0.14.2`, `scikit-learn==1.5.0`, `matplotlib==3.9.0`, `seaborn==0.13.2`, `datasets==2.20.0`, `pytest==8.2.2`, `pyyaml==6.0.2`, `jsonschema==4.23.0`).  
  **Verification**: `pip install -r requirements.txt` completes without error and the installed package versions match the file.

- [ ] **T015** **Install project dependencies**  
  Execute `pip install -r requirements.txt` in the CI environment before any code execution.  
  **Verification**: `pip freeze` contains the exact versions listed in `requirements.txt`.

- [ ] **T017** **Set random seeds for reproducibility**  
  Create `code/seed.py` that sets fixed seeds for `random`, `numpy`, and (if used) `torch`. Ensure all scripts import this module at start‑up.  
  **Verification**: Running any script prints the seed values and subsequent runs produce identical numeric results.

---

## Phase 1 – Power analysis & research documentation (US‑1)

- [ ] **T004** **Run power‑analysis script and embed results**  
  Implement `code/power_analysis.py` that computes the minimum sample size required to detect a Pearson r = 0.10 with a Bonferroni‑adjusted α = 0.001 (two‑tailed). The script writes the integer to `results/power_analysis.txt`, inserts the value into a newly created `research.md` (under a “Sample‑size requirement” heading), and updates the field `required_sample_size` in `state/projects/PROJ-049.yaml`.  
  **Verification**: `results/power_analysis.txt` exists and contains a positive integer; `research.md` contains the same integer; the YAML field is non‑null.

- [ ] **T005** **Draft research.md with dataset provenance**  
  Populate `research.md` with: (1) URLs for the OpenML BFI‑2 dataset (ID 42473) and the HuggingFace `lastfm/lastfm_1k` dataset, (2) a “Real‑First” paragraph explaining that only these verified sources are used, (3) licensing information, and (4) the sample‑size value from T004.  
  **Verification**: `grep -E "openml|lastfm|Real‑First|required sample size" research.md` returns matches for all four items.

---

## Phase 2 – Real‑data acquisition (US‑1)

- [ ] **T006** **Download BFI‑2 and stream Last.fm data**  
  Extend `code/ingest.py` to:  
  1. Download the BFI‑2 CSV from OpenML (ID 42473) with a 300 s timeout, retry up to 3 times, abort with `DataUnavailableError` on permanent failure, and save to `data/raw/bfi2_raw.csv`.  
  2. Stream the `lastfm/lastfm_1k` dataset via `datasets.load_dataset(..., streaming=True)`, write a compressed CSV `data/raw/lastfm_raw.csv`.  
  3. Include a pre‑flight check (`code/check_data_sources.py`) that sends HEAD requests to both URLs; any non‑200 response causes the pipeline to exit with a clear error message.  
  **Verification**: Both raw files exist, their SHA‑256 checksums are logged in `logs/ingestion.log`, and the head‑check script exits with status 0 on a clean run.

---

## Phase 3 – Merging & preprocessing (US‑1)

- [ ] **T007** **Merge, map genres, handle missing data, and compute log‑proportion scores**  
  Implement `code/preprocess.py` that performs the following steps in order, writing the final artefact to `data/processed/unified_data.parquet`:  
  1. Inner‑join `bfi2_raw.csv` and `lastfm_raw.csv` on the participant identifier (hash the `user_id` with SHA‑256). Abort with `DataUnavailableError` if the join yields zero rows.  
  2. Load `contracts/genre_lookup.yaml` and map every raw genre tag to one of the ten standardized categories (Rock, Pop, Hip‑Hop, Classical, Electronic, Jazz, Folk, Country, Metal, Other). Unmapped tags go to “Other”.  
  3. For each user compute `total_minutes` (sum of all genre minutes).  
  4. Derive `genre_proportions` = minutes / (total_minutes + 1 minute pseudocount) for each of the ten categories.  
  5. Apply a log‑transform (`log1p`) to each proportion, storing the result as `genre_log`.  
  6. Impute missing numeric demographics (age) with the median, categorical demographics (gender, country) with the mode; alternatively, exclude rows if imputation is not possible, logging the counts and strategy used.  
  7. One‑hot encode `gender` and group rare countries (frequency < 1 %) into an “Other” category, storing the encodings as `gender_onehot` and `country_onehot`.  
  **Verification**:  
  - The parquet file contains all required columns (`user_id`, trait scores, `age`, `gender_onehot`, `country_onehot`, `total_minutes`, `genre_proportions`, `genre_log`).  
  - Schema validation against `contracts/processed_dataset.schema.yaml` passes (using `pandera`).  
  - `logs/preprocess.log` records the number of rows dropped/excluded, the imputation strategy, and the SHA‑256 hash of the output file.

- [ ] **T016** **Verify merged dataset meets SC‑001**  
  Run a validation script that checks the unified dataset contains ≥ 100 rows and that ≤ 5 % of rows have missing demographic covariates after imputation/exclusion. Abort with a clear error if either condition fails.  
  **Verification**: Script exits with status 0 and logs the row count and missing‑demographic percentage.

---

## Phase 4 – Correlation analysis (US‑2)

- [ ] **T008** **Compute Pearson correlations on log‑proportion scores, Bonferroni correction, and effect sizes**  
  In `code/analysis.py` compute for every trait–genre pair (5 × 10):  
  1. Pearson r and two‑tailed p‑value using the `genre_log` columns (log‑transformed proportion scores).  
  2. Adjust p‑values with Bonferroni correction (α = 0.05 / 50 ≈ 0.001) and flag `is_significant`.  
  3. Convert r to Cohen’s d via `d = 2r / sqrt(1‑r²)` and obtain a 95 % confidence interval using Fisher’s z transformation (10 000 bootstrap resamples).  
  Output a CSV `data/processed/correlation_results.csv` that conforms to `contracts/correlation_results.schema.yaml`.  
  **Verification**: The file passes JSON‑Schema validation; a spot‑check on a synthetic subset reproduces expected values within tolerance.

---

## Phase 5 – Regression modelling & diagnostics (US‑2)

- [ ] **T009** **Fit trait‑specific linear regressions with full diagnostics**  
  Using `statsmodels.OLS`, fit five separate models (one per Big‑Five trait) with predictors: all `genre_log` columns, `age`, `gender_onehot`, `country_onehot`. **Do NOT include `total_minutes`**. For each model:  
  1. Compute VIF for all predictors; drop any predictor with VIF > 5, log the action, and re‑fit.  
  2. Run Shapiro‑Wilk test on residuals (normality); flag `residual_normality_pass`.  
  3. Run Breusch‑Pagan test for homoscedasticity; flag `homoscedasticity_pass`.  
  4. Perform linearity checks (e.g., component‑plus‑residual plots) and outlier‑influence checks (Cook’s distance); log any violations.  
  5. Store coefficients, standard errors, raw p‑values, Bonferroni‑adjusted p‑values, and significance flags in `data/processed/regression_results.csv` matching `contracts/regression_results.schema.yaml`.  
  **Verification**: The CSV validates against its schema; `logs/regression.log` contains VIF values, any dropped predictors, and the diagnostic p‑values for each trait.

---

## Phase 6 – Visualisation & final report (US‑3)

- [ ] **T010** **Generate heatmap, coefficient bar plot, and results report**  
  1. Create `results/correlation_heatmap.png` (800 × 600 px, 150 dpi) visualising the signed magnitude of Pearson r for all trait‑genre pairs (seaborn heatmap, diverging colormap).  
  2. Create `results/regression_coefficients.png` – a grouped bar chart of significant regression coefficients per trait.  
  3. Build `results/results_report.csv` that includes, for every trait‑genre pair, `cohens_d`, `ci_lower`, `ci_upper`, and a `significance_status` field that contains either `"Significant (adjusted p < 0.001)"` or the exact string `"Non‑significant (adjusted p ≥ 0.001)"`. The file must conform to `contracts/report.schema.yaml`.  
  **Verification**: Both PNG files open without error and have the requested dimensions; the CSV passes schema validation; a unit test (`tests/unit/test_report_completeness.py`) confirms that all 50 trait‑genre combinations are present.

---

## Phase 7 – Contract validation & state bookkeeping

- [ ] **T011** **Validate all pipeline artefacts against contracts**  
  Run a validation script (`code/validate.py`) that checks every output file (`unified_data.parquet`, `correlation_results.csv`, `regression_results.csv`, `results_report.csv`) against its respective JSON‑Schema contract using `pandera`. Abort on any mismatch.  
  **Verification**: The script exits with status 0 on a clean run; any failure is logged to `logs/validation.log`.

- [ ] **T012** **Record artifact hashes and timestamps in project state**  
  After each major phase (data acquisition, preprocessing, analysis, reporting) compute SHA‑256 hashes of the newly generated artefacts and write them, together with an ISO‑8601 `updated_at` timestamp, into `state/projects/PROJ-049.yaml`.  
  **Verification**: The YAML file contains entries for all artefacts with non‑empty `hash` fields and timestamps later than the previous run.

---

## Phase 8 – Documentation & CI tests

- [ ] **T013** **Update README with execution instructions and ethical notes**  
  Add a “Execution Instructions” section describing the single command `python -m code.pipeline` and the required real‑data URLs. Add a “Privacy & Data Handling” section explaining hashing of `user_id`, removal of PII, and licensing compliance.  
  **Verification**: `grep -E "Execution Instructions|Privacy & Data Handling" README.md` returns matches.

- [ ] **T014** **Add CI tests for critical constraints**  
  1. `tests/performance/test_ingestion_time.py::test_ingestion_under_300s` asserts that the combined runtime of tasks T006 (download) is ≤ 300 s on the CI runner.  
  2. `tests/unit/test_schema_validation.py::test_all_outputs_valid` runs the validator from T011 on the artefacts produced by the pipeline.  
  **Verification**: Both tests pass in the CI workflow; failures abort the run.

---

## Dependency mapping (summary)

| Spec/FR | Satisfied by task(s) |
|---------|----------------------|
| FR‑001 | T006 |
| FR‑002 | T007 (genre mapping) |
| FR‑003 | T008 |
| FR‑004 | T009 |
| FR‑005 | T008 (Bonferroni) |
| FR‑006 | T010 |
| FR‑007 | T007 (missing‑data handling) |
| FR‑008 | T007 (total_minutes computed) |
| FR‑009 | T009 (diagnostics) |
| SC‑001 | T001‑T003, T015, T016 (runtime & size checks) |
| SC‑002 | T008 (significance threshold) |
| SC‑004 | T009 (diagnostic pass) |
| SC‑005 | T007 (proportion computation) |
| SC‑006 | T010 (visuals & report) |
| SC‑012 | T008 (Bonferroni) |
| SC‑001 (dataset size) | T016 |

---  

*All tasks are unchecked (`[ ]`) to indicate they must be completed. Once a task is verified, the checkbox can be ticked in the CI run.*  