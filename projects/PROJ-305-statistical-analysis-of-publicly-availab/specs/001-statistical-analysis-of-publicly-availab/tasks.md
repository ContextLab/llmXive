# Tasks: Statistical Analysis of Publicly Available COVID‑19 Vaccine Adverse Event Reports  

**Inputs**: `spec.md`, `plan.md`, existing contracts in `specs/001-statistical-analysis-of-publicly-availab/contracts/`.  
**Goal**: Produce a fully‑verified, CPU‑only pipeline that downloads VAERS 2020‑2023 data, cleans it, computes disproportionality metrics (ROR, PRR, IC) with BH correction, runs sensitivity and temporal analyses, profiles memory, validates results, and hands off a reproducible report.

---

## Phase 0 – Project scaffolding (must succeed before any code runs)

- [ ] **T001** [  ] Create the required directory tree and a snapshot file.  
  - **Paths**: `src/`, `src/data/`, `src/analysis/`, `src/utils/`, `src/validation/`, `tests/`, `data/`, `data/raw/`, `data/processed/`, `output/`, `output/figures/`, `output/temporal_profiles/`, `contracts/`, `logs/`, `README.md`, `.gitignore`  
  - **Verification**: Run `tree -a -L 3 > logs/structure.txt` and assert that `logs/structure.txt` contains each of the directories listed above (non‑empty lines).

- [ ] **T002** [  ] Add project‑level stub files with the correct title.  
  - **Files**: `.gitignore` (standard Python ignores) and `README.md` containing the exact project title *“Statistical Analysis of Publicly Available COVID‑19 Vaccine Adverse Event Reports”* plus a brief description.  
  - **Verification**: Grep `README.md` for the title string and ensure `.gitignore` exists and is non‑empty.

- [ ] **T003** [  ] Configure linting and formatting tools.  
  - **File**: `pyproject.toml` that enables **ruff**, **black**, and **isort** (no GPU‑specific packages).  
  - **Verification**: Execute `ruff check .` and `black --check .`; both must exit with status 0. Store the command output in `logs/lint.txt`.

---

## Phase 1 – Contracts & core utilities  

- [ ] **T004** [ P ] Copy the JSON‑Schema contracts from the specification into the project’s contract directory.  
  - **Sources**: `specs/001-statistical-analysis-of-publicly-availab/contracts/dataset.schema.yaml` → `contracts/dataset.schema.yaml`  
    `specs/001-statistical-analysis-of-publicly-availab/contracts/signal.schema.yaml` → `contracts/signal.schema.yaml`  
    `specs/001-statistical-analysis-of-publicly-availab/contracts/soc_cluster.schema.yaml` → `contracts/soc_cluster.schema.yaml`  
  - **Verification**: Run `jsonschema -i data/processed/cleaned_vaers.csv contracts/dataset.schema.yaml` on a dummy CSV (header‑only) to confirm the schema file parses; repeat for `signal.schema.yaml` and `soc_cluster.schema.yaml` with appropriate dummy rows.

- [ ] **T005** [  ] Create `src/utils/config.py` containing:  
  - Global `SEED = 42` (used by all random operations)  
  - Path constants (`RAW_DIR`, `PROCESSED_DIR`, `OUTPUT_DIR`, `CONTRACTS_DIR`) built with `pathlib.Path`  
  - Metric thresholds (`ROR_THRESH = 2.0`, `PRR_THRESH = 1.5`, `IC_THRESH = 0.0`) and BH‑alpha (`0.05`).  
  - **Verification**: Import the module in a REPL (`python -c "import src.utils.config as cfg; assert cfg.SEED==42"`); success writes `logs/config_import.txt`.

- [ ] **T006** [  ] Implement `src/data/validate.py` – a CLI that:  
  1. Loads `contracts/dataset.schema.yaml` using `jsonschema`.  
  2. Accepts a CSV or Parquet path argument.  
  3. Validates column presence (`VAX_TYPE`, `SOC_CODE`, `SOC_NAME`, `REPT_DATE`).  
  4. Exits with code `E_SCHEMA_MISSING` (value 1) if required columns are absent, otherwise exits 0.  
  - **Prerequisite**: Contracts must be present (produced by T004).  
  - **Verification**: Run the script on `data/processed/cleaned_vaers.csv` (expected to pass) and on a deliberately malformed CSV (expected to exit 1). Capture return codes in `logs/validate_pass.txt` and `logs/validate_fail.txt`.

- [ ] **T007** [ P ] Implement `src/utils/plots.py` with two helper functions:  
  1. `save_line_plot(df, x, y, title, path)` – creates a Matplotlib line plot and writes a PNG.  
  2. `save_forest_plot(df, metric, ci_low, ci_high, title, path)` – creates a forest‑plot style figure for ROR/PRR/IC.  
  - **Verification**: Unit test `tests/unit/test_plots.py` creates a tiny DataFrame, calls both functions, and asserts that the PNG files exist in `output/figures/`.

---

## Phase 2 – Data acquisition & cleaning  

- [ ] **T008** [ P ] Download the VAERS 2020‑2023 CSV files.  
  - **File**: `src/data/download_vaers.py` that iterates over the list `["2020", "2021", "2022", "2023"]`, builds the URL `[UNRESOLVED-CLAIM: https://vaers.hhs.gov/data/datasets/VAERSDATA{year}.CSV` — HTTP 404], streams with `requests`, writes to `data/raw/VAERS_{year}.csv`, and verifies each file’s SHA‑256 against a hard‑coded checksum table.  
  - **Verification**: After execution, `logs/download_checksums.txt` must list each file with “OK”. A missing or mismatched checksum aborts with exit code 2.

- [ ] **T009** [ P ] Obtain a verified MedDRA‑to‑SOC mapping.  
  - **File**: `src/data/download_meddra.py` that installs the `meddra` PyPI package (or fetches a public CSV from `[UNRESOLVED-CLAIM: https://raw.githubusercontent.com/meddra/meddra-mappings/master/meddra_soc.csv` — HTTP 404]) and writes `data/meddra_soc_mapping.csv`.  
  - **Verification**: Ensure the CSV contains at least columns `SOC_CODE` and `SOC_NAME`; log the row count to `logs/meddra_rows.txt`.

- [ ] **T010** [ P ] Clean, filter, and merge VAERS data.  
  - **File**: `src/data/clean.py` performing the following steps:  
    1. Load each raw CSV (chunked if > 5 GB) into a DataFrame.  
    2. Keep records where `VAX_TYPE` is non‑null and `REPT_DATE` is parsable.  
    3. Create four logical groups:  
       - **COVID‑19** (`VAX_TYPE.str.contains("COVID", case=False)`)  
       - **Flu‑only** (`VAX_TYPE.str.contains("Influenza", case=False)`)  
       - **Non‑COVID & Non‑Flu** (neither of the above)  
       - **All Non‑COVID** (union of Non‑COVID & Non‑Flu).  
    4. Load `data/meddra_soc_mapping.csv` and left‑join on `SOC_CODE` to obtain `SOC_NAME`. Drop rows with missing `SOC_NAME`.  
    5. Write the following Parquet files to `data/processed/`:  
       - `covid.parquet`  
       - `non_covid.parquet` (all non‑COVID)  
       - `flu.parquet`  
       - `cleaned_vaers_full_non_covid.parquet` (COVID + All Non‑COVID, used for disproportionality)  
       - `cleaned_vaers.parquet` (all groups).  
    6. Also write a human‑readable CSV `cleaned_vaers.csv` for quick inspection.  
  - **Verification**: Unit test `tests/unit/test_clean_filter.py` asserts that each output file exists and that row counts match expected logical sums (e.g., `covid + non_covid == cleaned_vaers`). Log results to `logs/clean_summary.txt`.

---

## Phase 3 – Disproportionality signal detection  

- [ ] **T011** [ P ] Compute ROR, PRR, IC and apply the 2‑out‑of‑3 rule.  
  - **File**: `src/analysis/disproportionality.py` that:  
    1. Reads `data/processed/cleaned_vaers_full_non_covid.parquet`.  
    2. For every SOC with **≥ 5** total reports, builds a 2×2 contingency table (COVID vs. Non‑COVID).  
    3. Applies a continuity correction of **0.5** to any zero cell.  
    4. Calculates ROR, PRR, IC and their 95 % Wald CIs; obtains raw two‑sided p‑values via Fisher’s exact test (`scipy.stats.fisher_exact`).  
    5. Performs Benjamini‑Hochberg correction (`statsmodels.stats.multitest.multipletests`) on the raw p‑values (α = 0.05).  
    6. Flags a signal if **at least two** of the three metrics satisfy their thresholds (FR‑005). Populates `is_signal` and `signal_metrics`.  
    7. Writes `output/signals.csv` conforming exactly to `contracts/signal.schema.yaml` and adds a column `background_rate_status` set to `"UNKNOWN"` for every row.  
    8. Logs summary statistics (total SOCs examined, signals found, any warnings) to `logs/disproportionality.txt`.  
  - **Verification**: Integration test `tests/integration/test_disproportionality.py` runs the script on the real processed data and asserts that `output/signals.csv` exists, has the required header columns, and that at least one row has `is_signal = True`.  

---

## Phase 4 – Sensitivity and temporal profiling  

- [ ] **T012** [ P ] Sensitivity analysis against a Flu‑only baseline.  
  - **File**: `src/analysis/sensitivity.py` that:  
    1. Loads `output/signals.csv` and `data/processed/cleaned_vaers.parquet`.  
    2. Selects the top 5 signals by smallest `p_value_adj`.  
    3. Re‑computes ROR, PRR, IC using **Flu‑only** as the reference group (instead of the full non‑COVID baseline).  
    4. Calculates deltas (`ror_delta = ror_flu - ror_non_covid`, etc.) and writes `output/sensitivity_analysis.csv` with columns `SOC_CODE, SOC_NAME, ror_delta, prr_delta, ic_delta`.  
    5. Logs the operation to `logs/sensitivity.txt`.  
  - **Verification**: Unit test `tests/unit/test_sensitivity.py` runs the function on a tiny synthetic parquet fixture and checks that the delta columns are present and numeric.

- [ ] **T013** [ P ] Temporal profiling of the top candidate SOCs.  
  - **File**: `src/analysis/temporal.py` that:  
    1. Reads `output/signals.csv` and selects the top 5 signals (or all if fewer).  
    2. Computes the median `REPT_DATE` across the combined COVID + Non‑COVID cohort.  
    3. For each selected SOC, aggregates weekly counts of reports relative to that median (negative weeks = earlier than median, positive = later).  
    4. Calls `src.utils.plots.save_line_plot` to produce a PNG per SOC in `output/temporal_profiles/` with the title **“Weekly Reporting Time for {SOC_NAME}”** and axis label **“Weeks relative to cohort median reporting date”**.  
    5. Writes a placeholder warning file `output/temporal_profiles/empty_signal_warning.txt` if no signals exist.  
    6. Logs creation of each figure to `logs/temporal.txt`.  
  - **Verification**: Integration test `tests/integration/test_temporal_profiles.py` asserts that at least one PNG file exists when signals are present and that the warning file is absent.

---

## Phase 5 – Profiling, validation, and final report  

- [ ] **T014** [ P ] Memory profiling and comprehensive validation.  
  - **File**: `src/main.py` (pipeline orchestrator) now includes:  
    1. A `psutil`‑based context manager that records peak RAM usage (GB) for the whole run and writes `output/memory_profile.json` (`{"peak_gb": <float>, "status": "OK"}` if ≤ 7 GB, else `"EXCEEDED"`).  
    2. After the disproportionality, sensitivity, and temporal stages, it calls `src/validation/validate_outputs.py`.  
  - **File**: `src/validation/validate_outputs.py` that performs four checks:  
    - **BH monotonicity** – verifies that adjusted p‑values are non‑decreasing when sorted by raw p‑value.  
    - **SC‑001** – computes the proportion of SOCs with finite ROR/PRR/IC (must be ≥ 0.95).  
    - **SC‑005** – computes the proportion of signals satisfying the 2‑out‑of‑3 rule.  
    - **Background‑rate flag** – ensures every row in `output/signals.csv` has `background_rate_status == "UNKNOWN"`.  
    Results are written to `output/validation.log` with clear PASS/FAIL tags.  
  - **Verification**: Run `python -m src.main` on a small sampled dataset; assert that `output/validation.log` contains the three PASS lines and that `output/memory_profile.json` reports `"status": "OK"`.

- [ ] **T015** [ P ] Generate the final human‑readable report.  
  - **File**: `output/report.md` that includes:  
    1. **Summary** of memory usage (from `memory_profile.json`).  
    2. **Validation metrics** (copy of PASS/FAIL lines from `validation.log`).  
    3. Table of top 10 signals (pulled from `output/signals.csv`).  
    4. Figures: embed the forest plot PNGs (generated by `plots.py`) and the temporal PNGs.  
    5. **Limitations** section explicitly stating that temporal analysis is “Reporting Time” only, no causal inference, and that background incidence rates are unknown (`background_rate_status = "UNKNOWN"`).  
    6. No occurrence of the prohibited strings “Post‑Vaccination Time”, “Causal”, or “Incidence Rate”.  
  - **Verification**: CI step runs `grep -E "Post‑Vaccination|Causal|Incidence Rate" output/report.md && echo "FAIL"`; it must return no matches. Additionally, a sanity check script confirms that the report contains at least three headings and embeds at least one PNG reference.

- [ ] **T018** [  ] CPU‑only environment verification.  
  - **File**: `src/utils/cpu_check.py` that:  
    1. Parses `requirements.txt` to ensure no packages with GPU suffixes (e.g., `torch`, `tensorflow-gpu`).  
    2. Attempts to import common GPU libraries (`torch`, `tensorflow`) and asserts `torch.cuda.is_available()` is `False` (if torch is installed).  
    3. Checks the environment variable `CUDA_VISIBLE_DEVICES` is unset or empty.  
    4. Writes a concise pass/fail report to `logs/cpu_check.txt`.  
  - **Verification**: CI step runs the script and fails the pipeline if the report contains “FAIL”.

---

## Phase 6 – Documentation polish (optional but recommended)

- [ ] **T016** [ P ] Update `README.md` with a **Quickstart** section showing:  

  ```bash
  pip install -r requirements.txt
  python -m src.main
  ```

  and a brief description of each output artifact.  
  - **Verification**: Render the README on GitHub Pages (simulated by `markdownlint`) and ensure the Quickstart block is present.

- [ ] **T017** [ P ] Run `ruff --fix .` and `black .` to enforce style; capture the diff summary in `logs/style_fix.txt`.  
  - **Verification**: Re‑run the lint commands from **T003**; both must exit with status 0.

---

### Dependency & execution order  

| Task | Must finish before |
|------|--------------------|
| T001‑T003 | – |
| T004‑T007 | T001‑T003 |
| T008‑T010 | T004‑T007 |
| T011 | T010 |
| T012‑T013 | T011 |
| T014 | T011‑T013 |
| T015 | T014 |
| T018 | T015 |
| T016‑T017 | T015 (optional, for polishing) |

All tasks marked **[P]** may run in parallel once their prerequisite files exist; tasks without **[P]** are sequentially ordered as shown.  

---  

*All tasks remain unchecked until their concrete artifacts are produced and the verification steps succeed. The list respects the scientific requirements (FR‑001 – FR‑007, SC‑001 – SC‑005) and conforms to the platform’s “no‑fabrication”, “CPU‑only”, and “real‑data” rules.*  