# Tasks: Exploring the Correlation Between Musical Preference and Personality Traits

**Inputs**: `spec.md`, `plan.md`, contracts, and reviewer feedback.  
**Goal**: Deliver a reproducible end‑to‑end analysis that answers the research question using only real, verified datasets, and produce validated statistical artefacts, visualisations, and a final report.

---

## Phase 0 – Project scaffolding & reproducibility  

- [~] **T001** [US‑1] **Create project directory layout**  
  *Create the following folders at the repository root:* `data/raw/`, `data/processed/`, `results/`, `logs/`, `code/`, `tests/`.  
  **Verification**:  
  ```bash
  python - <<'PY'
  import pathlib, sys
  dirs = ['data/raw','data/processed','results','logs','code','tests']
  missing = [d for d in dirs if not pathlib.Path(d).is_dir()]
  assert not missing, f"Missing dirs: {missing}"
  print("OK")
  PY
  ```

- [ ] **T002** **Pin exact dependency versions**   <!-- FAILED-IN-EXECUTION: code/verify_requirements.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/verify_requirements.py exit=1 -->
  Create `requirements.txt` containing the exact versions listed in the plan (pandas, numpy, scipy, statsmodels, scikit‑learn, matplotlib, seaborn, datasets, pytest, pyyaml, jsonschema).  
  **Verification**: Run `pip freeze > installed.txt` and ensure `diff -u requirements.txt installed.txt` reports no version mismatches.

- [~] **T003** **Set deterministic random seeds**  
  Add `code/seed.py` that sets fixed seeds for `random`, `numpy.random`, and (if used) `torch`. All pipeline scripts must import this module as the first line. The script also writes its SHA‑256 hash to `code/seed_hash.txt`.  
  **Verification**:  
  ```bash
  python -c "import hashlib; print(hashlib.sha256(open('code/seed.py','rb').read()).hexdigest())" > current_hash.txt
  diff -u current_hash.txt code/seed_hash.txt
  ```

---

## Phase 1 – Power analysis & research documentation  

- [ ] **T004** **Compute required sample size**   <!-- FAILED-IN-EXECUTION: code/power_analysis.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/power_analysis.py exit=1 -->
  Implement `code/power_analysis.py` that calculates the minimum sample size to detect a Pearson r = 0.10 with Bonferroni‑adjusted α = 0.001 (two‑tailed). The script writes the integer to `results/power_analysis.txt`, updates `research.md` with a line `Required sample size: <n>`, and writes the same value into `state/projects/PROJ-049.yaml` under `required_sample_size`.  
  **Verification**:  
  - `results/power_analysis.txt` exists and contains a positive integer.  
  - `research.md` contains the exact line `Required sample size: <n>`.  
  - `state/projects/PROJ-049.yaml` has a matching `required_sample_size` field.

- [ ] **T005** **Draft `research.md` with provenance and “Real‑First” statement**  
  Create `research.md` that includes:  
  1. URLs for the verified BFI‑2 OpenML dataset (ID 42473) and the HuggingFace `lastfm/lastfm_1k` dataset.  
  2. A paragraph titled **Real‑First** explaining that only these publicly verified sources are used.  
  3. Licensing information for both datasets.  
  4. The required sample size placeholder (filled by T004).  
  **Verification**: `grep -E "openml|lastfm|Real‑First|Required sample size" research.md` returns a match for each of the four items.

---

## Phase 2 – Real‑data acquisition  

- [ ] **T006** **Download BFI‑2 and stream Last.fm data with full hygiene and timing checks**  
  Extend `code/ingest.py` to:  
  1. Perform HEAD requests to both source URLs; abort with a clear error if any response is not 200.  
  2. Download the BFI‑2 CSV (OpenML ID 42473) with a 300 s timeout, retry up to 3 times, compute and log its SHA‑256 checksum, and save to `data/raw/bfi2_raw.csv`.  
  3. Stream the `lastfm/lastfm_1k` dataset via `datasets.load_dataset(..., streaming=True)`, write a compressed CSV `data/raw/lastfm_raw.csv`, and compute its SHA‑256 checksum (saved to `logs/lastfm_checksum.txt`).  
  4. Measure total wall‑clock time; abort if > 300 seconds.  
  5. After merging (see T007), assert the merged dataframe has ≥ 100 rows and that ≤ 5 % of rows have missing demographic fields after imputation.  
  **Verification**:  
  - Both raw files exist and are non‑empty.  
  - `logs/ingestion.log` contains both SHA‑256 hashes and a timing entry ≤ 300 s.  
  - Post‑merge row count and missing‑demographic percentage checks pass (logged).

---

## Phase 3 – Pre‑processing, merging, and feature engineering (atomized)  

- [ ] **T007a** **Merge BFI‑2 and Last.fm on hashed `user_id`**  
  Inner‑join `bfi2_raw.csv` and `lastfm_raw.csv` on a SHA‑256 hash of the original `user_id`. Abort if the join yields zero rows.  
  **Verification**: Confirm `data/processed/merged_interim.parquet` exists and `row_count > 0`.

- [ ] **T007b** **Map raw genre tags to standardized categories**  
  Load `contracts/genre_lookup.yaml` and map every raw genre tag to one of the ten categories (Rock, Pop, Hip‑Hop, Classical, Electronic, Jazz, Folk, Country, Metal, Other). Unmapped tags go to “Other”.  
  **Verification**: Ensure a column `standard_genre` contains only the allowed enum values.

- [ ] **T007c** **Compute total minutes and proportion with correct pseudocount**  
  For each user compute `total_minutes = sum(listening_minutes)` and for each standardized genre compute  
  `genre_proportion = (minutes + 1) / (total_minutes + 1)` (1‑minute pseudocount added to both numerator and denominator).  
  **Verification**: Check that all `genre_proportion` values lie in (0,1] and that the sum across genres equals 1 (within tolerance).

- [ ] **T007d** **Log‑transform and ILR‑transform genre proportions**  
  Apply `np.log1p` to each `genre_proportion` producing `genre_log_<GENRE>`. Then perform an Isometric Log‑Ratio (ILR) transformation to obtain compositional components stored in `genre_ilr_<COMP>` columns.  
  **Verification**: Verify that `genre_ilr_*` columns contain finite numbers and that the ILR transformation can be inverted without loss.

- [ ] **T007e** **Handle missing demographics, one‑hot encode, and document limitation**  
  Impute missing `age` with the median, `gender` and `country` with their modes; exclude rows where imputation is impossible, logging the count and strategy. Group countries with frequency < 1 % into an “Other” category before one‑hot encoding, producing `gender_onehot_*` and `country_onehot_*`. Write a short limitation note about using listening minutes as a proxy to `docs/limitations.txt`.  
  **Verification**:  
  - `data/processed/unified_data.parquet` includes all required columns.  
  - Schema validation against `contracts/processed_dataset.schema.yaml` passes.  
  - `docs/limitations.txt` exists and contains the required narrative.

---

## Phase 4 – Correlation analysis and effect‑size computation  

- [ ] **T008** **Compute Pearson correlations, Bonferroni correction, Cohen’s d, and bootstrap CIs**  
  In `code/analysis.py` calculate for every Big‑Five trait × standardized genre pair (5 × 10):  
  1. Pearson r and two‑tailed p‑value using the `genre_log_<GENRE>` columns.  
  2. Bonferroni‑adjusted p‑value (α = 0.05 / 50 ≈ 0.001) and flag `is_significant`.  
  3. Convert r to Cohen’s d via `d = 2r / sqrt(1‑r²)`.  
  4. Obtain a 95 % confidence interval for r (and consequently for d) using Fisher’s z transformation with 10 000 bootstrap resamples.  
  Write the results to `data/processed/correlation_results.csv` adhering to `contracts/correlation_results.schema.yaml`.  
  **Verification**: Run JSON‑Schema validation; spot‑check a synthetic subset to ensure values fall within tolerance.

---

## Phase 5 – Regression modelling with diagnostics  

- [ ] **T009** **Fit trait‑specific linear regressions, perform diagnostics, and record results**  
  Using `statsmodels.OLS` in `code/regression.py`:  
  1. For each trait, fit a model with predictors `genre_ilr_*`, `age`, all `gender_onehot_*`, and all `country_onehot_*` (exclude `total_minutes`).  
  2. Compute VIF for all predictors; drop any with VIF > 5, log the action, and refit.  
  3. Run Shapiro‑Wilk test on residuals (normality) and Breusch‑Pagan test (homoscedasticity); record pass/fail flags.  
  4. Identify high‑influence points via Cook’s distance (> 4 / n) and log any removals.  
  5. Apply Bonferroni correction to the p‑values of each coefficient.  
  6. Store the final coefficient table (`trait`, `predictor`, `coefficient`, `std_error`, `p_value`, `adjusted_p_value`, `is_significant`) in `data/processed/regression_results.csv` (matches `contracts/regression_results.schema.yaml`).  
  7. Append a diagnostics array to a master JSON file `data/processed/analysis_output.json` that follows `contracts/analysis_output.schema.yaml`, ensuring each entry contains `model_trait`, `issue`, and `action`.  
  **Verification**:  
  - `regression_results.csv` validates against its schema.  
  - `analysis_output.json` contains a `diagnostics` entry for each trait with the required fields (checked via a JSON‑Schema validator).  
  - `logs/regression.log` lists VIF values, dropped predictors, and diagnostic test statistics.

---

## Phase 6 – Visualisation and final report  

- [ ] **T010** **Generate visualisations and compile the final results report**  
  1. Produce `results/correlation_heatmap.png` (800 × 600 px, 150 dpi) visualising signed Pearson r values across traits (rows) and genres (columns) using a diverging colormap. Verify dimensions with Pillow (`Image.open(...).size`).  
  2. Produce `results/regression_coefficients.png`, a grouped bar chart showing all significant regression coefficients per trait. Verify dimensions similarly.  
  3. Assemble `results/results_report.csv` that conforms to `contracts/report.schema.yaml`, containing:  
     - `summary_statistics` (total_tests = 50, significant_tests, required_sample_size from T004, actual_sample_size from the processed dataset, a brief power note).  
     - `significant_findings`: the subset of rows from `correlation_results.csv` where `is_significant` = true, including Cohen’s d and 95 % CIs.  
     - `limitations`: the narrative from `docs/limitations.txt`.  
  **Verification**:  
  - PNG files open without error and Pillow reports the requested dimensions.  
  - `results_report.csv` validates against `contracts/report.schema.yaml`.  
  - A unit test (`tests/unit/test_report_completeness.py`) asserts that exactly 50 trait‑genre combinations are present.

---

## Phase 7 – Contract validation and CI integration  

- [ ] **T011** **Validate all pipeline artefacts against their JSON‑Schema contracts**  
  Run `code/validate.py` which loads each output file (`unified_data.parquet`, `correlation_results.csv`, `regression_results.csv`, `results_report.csv`, `analysis_output.json`) and validates them against the corresponding schemas in `specs/.../contracts/`. Abort on any mismatch and write detailed error messages to `logs/validation.log`.  
  **Verification**: The script exits with status 0; `logs/validation.log` is empty on success.

- [ ] **T012** **Update README and add CI tests for runtime and schema compliance**  
  1. Add an “Execution Instructions” section describing the single command `python -m code.pipeline`.  
  2. Add a “Privacy & Data Handling” section explaining hashing of `user_id`, removal of PII, and licensing compliance.  
  3. Add two CI tests under `tests/performance/`:  
     - `test_ingestion_under_300s.py` asserts that the combined runtime of the download step (T006) is ≤ 300 seconds.  
     - `test_all_outputs_valid.py` runs the validator from T011.  
  **Verification**: `grep -E "Execution Instructions|Privacy & Data Handling" README.md` returns matches; CI workflow executes the two new tests and they both pass.

---

## Phase 8 – Quickstart guide  

- [ ] **T013** **Create Quickstart documentation**  
  Write `quickstart.md` that outlines: environment setup (`pip install -r requirements.txt`), data download (`python -m code.ingest`), running the full pipeline (`python -m code.pipeline`), and where to find results. Include code snippets and expected output file locations.  
  **Verification**: `grep -E "pip install|python -m code.ingest|python -m code.pipeline" quickstart.md` returns matches for each command.

---

### Dependency mapping (summary)

| Spec / FR | Satisfied by task(s) |
|-----------|----------------------|
| FR‑001 | T006 |
| FR‑002 | T007b |
| FR‑003 | T007c (corrected pseudocount) |
| FR‑004 | T009 |
| FR‑005 | T008 (Bonferroni) |
| FR‑006 | T010 |
| FR‑007 | T007e |
| FR‑008 | T007c (total_minutes) |
| FR‑009 | T009 (diagnostics) |
| SC‑001 | T006 (runtime, row count, missing‑demographic checks) |
| SC‑002 | T008 (significance threshold) |
| SC‑004 | T009 (diagnostic pass) |
| SC‑005 | T007c (proportion computation) |
| SC‑006 | T010 (visuals & report) |
| SC‑012 | T008 (Bonferroni) |
| Power‑analysis / sample‑size | T004 |
| Quickstart guide | T013 |

---  

*All tasks are initially unchecked (`[ ]`). Once a task is verified in CI, its checkbox may be ticked.*  