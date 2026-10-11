# Tasks: Statistical Analysis of Publicly Available COVID‑19 Vaccine Adverse Event Reports  

**Inputs**: `spec.md`, `plan.md`, contracts in `specs/001-statistical-analysis-of-publicly-availab/contracts/`.  
**Goal**: Produce a fully‑verified, CPU‑only pipeline that downloads VAERS 2020‑2023 data, cleans it, computes disproportionality metrics (ROR, PRR, IC) with Benjamini‑Hochberg correction, runs sensitivity and temporal analyses, profiles memory, validates results, and hands off a reproducible report.

---

## Phase 0 – Project scaffolding  

- [ ] **T001** Create the required directory tree and capture a filesystem snapshot.  
  - **Paths**: `src/`, `src/data/`, `src/analysis/`, `src/utils/`, `src/validation/`, `tests/`, `data/`, `data/raw/`, `data/processed/`, `output/`, `output/figures/`, `output/temporal_profiles/`, `contracts/`, `logs/`.  
  - **Action**: Run a script that creates the directories (using `pathlib.Path.mkdir(parents=True, exist_ok=True)`) and then executes `tree -a -L 3 > logs/structure.txt`.  
  - **Verification**: `grep -E "src|data|output|contracts|logs" logs/structure.txt` must return a line for each listed directory; the file must be non‑empty.

- [ ] **T002** Add project‑level stub files with the correct title.  
  - **Files**: `.gitignore` (standard Python ignores) and `README.md` containing the exact project title **“Statistical Analysis of Publicly Available COVID‑19 Vaccine Adverse Event Reports”** plus a one‑sentence description.  
  - **Verification**: `grep -q "Statistical Analysis of Publicly Available COVID-19 Vaccine Adverse Event Reports" README.md` and `test -s .gitignore`.

- [ ] **T003** Configure linting and formatting tools (CPU‑only).   <!-- FAILED-IN-EXECUTION: code/run_lint.py exit=2 --> <!-- FAILED-IN-EXECUTION: code/run_lint.py exit=2 -->
  - **File**: `pyproject.toml` that enables **ruff**, **black**, and **isort** (no GPU‑specific packages).  
  - **Verification**: Run `ruff check .` and `black --check .`; both must exit with status 0. Capture the combined stdout/stderr in `logs/lint.txt`.

---

## Phase 1 – Contracts & core utilities  

- [ ] **T004** Copy the JSON‑Schema contracts from the specification into the project’s contract directory.  
  - **Sources → Destinations**:  
    - `specs/001-statistical-analysis-of-publicly-availab/contracts/dataset.schema.yaml` → `contracts/dataset.schema.yaml`  
    - `specs/001-statistical-analysis-of-publicly-availab/contracts/signal.schema.yaml` → `contracts/signal.schema.yaml`  
    - `specs/001-statistical-analysis-of-publicly-availab/contracts/soc_cluster.schema.yaml` → `contracts/soc_cluster.schema.yaml`  
  - **Verification**: `jsonschema -i data/processed/dummy.csv contracts/dataset.schema.yaml` (header‑only CSV) must run without schema‑parse errors; repeat for the other two schemas.

- [ ] **T005** Implement core utility module `src/utils/config.py` **and** plotting helpers `src/utils/plots.py`.  
  - **config.py** must define:  
    - `SEED = 42`  
    - Path constants `RAW_DIR`, `PROCESSED_DIR`, `OUTPUT_DIR`, `CONTRACTS_DIR` (all `pathlib.Path`).  
    - Metric thresholds `ROR_THRESH = 2.0`, `PRR_THRESH = 1.5`, `IC_THRESH = 0.0`, `BH_ALPHA = 0.05`.  
  - **plots.py** must expose two functions:  
    1. `save_line_plot(df, x, y, title, path)` – creates a Matplotlib line plot and writes a PNG.  
    2. `save_forest_plot(df, metric, ci_low, ci_high, title, path)` – creates a forest‑plot style figure for ROR/PRR/IC.  
  - **Verification**: `python -c "import src.utils.config as cfg; assert cfg.SEED==42"` writes `logs/config_import.txt`. Run the unit test `tests/unit/test_plots.py` (provided) and ensure PNG files appear in `output/figures/`.

- [ ] **T006** Implement `src/data/validate.py` – a CLI validator that checks a CSV/Parquet file against `contracts/dataset.schema.yaml`.  
  - **Behaviour**:  
    1. Load the schema with `jsonschema`.  
    2. Accept a file path argument (`--input`).  
    3. Verify required columns `VAX_TYPE`, `SOC_CODE`, `SOC_NAME`, `REPT_DATE` are present.  
    4. Exit with code 1 (`E_SCHEMA_MISSING`) if any are absent; otherwise exit 0.  
  - **Verification**: Run the script on a known‑good cleaned file (`data/processed/cleaned_vaers.parquet`) – expect exit 0 and log `logs/validate_pass.txt`. Run on a deliberately malformed CSV missing `VAX_TYPE` – expect exit 1 and log `logs/validate_fail.txt`.

---

## Phase 2 – Data acquisition & cleaning  

- [ ] **T007** Implement `src/data/download_vaers.py` to fetch the VAERS 2020‑2023 CSV files.  
  - **Details**: Iterate over years `["2020","2021","2022","2023"]`, construct URL `[UNRESOLVED-CLAIM: https://vaers.hhs.gov/data/datasets/VAERSDATA{year}.CSV` — HTTP 404], stream via `requests`, write to `data/raw/VAERS_{year}.csv`. After each download, compute SHA‑256 and compare to a hard‑coded checksum table; abort with exit 2 on mismatch.  
  - **Verification**: After execution, `logs/download_checksums.txt` must list each file with “OK”. Missing file or checksum error should cause the script to exit 2.

- [ ] **T008** Implement `src/data/download_meddra.py` to obtain a verified MedDRA‑to‑SOC mapping.  
  - **Approach**: Use the public CSV `[UNRESOLVED-CLAIM: https://raw.githubusercontent.com/meddra/meddra-mappings/master/meddra_soc.csv` — HTTP 404] (or any other real source) and write it to `data/meddra_soc_mapping.csv`. Verify that the file contains at least the columns `SOC_CODE` and `SOC_NAME`.  
  - **Verification**: Count rows and write the number to `logs/meddra_rows.txt`; ensure the count > 0.

- [ ] **T009** Implement `src/data/clean.py` to filter, map, and merge VAERS data.  
  - **Steps**:  
    1. Load each raw CSV (use `chunksize` if file > 5 GB).  
    2. Keep records with non‑null `VAX_TYPE` and parsable `REPT_DATE`.  
    3. Define three logical groups (baseline now matches the specification):  
       - **COVID‑19** (`VAX_TYPE.str.contains("COVID", case=False)`)  
       - **Non‑COVID** (all records where `VAX_TYPE` does **not** contain “COVID”; this **includes** Flu records)  
       - **Flu‑only** (`VAX_TYPE.str.contains("Influenza", case=False)`) for the sensitivity analysis.  
    4. Load `data/meddra_soc_mapping.csv` and left‑join on `SOC_CODE` to obtain `SOC_NAME`; drop rows with missing `SOC_NAME`.  
    5. Write Parquet files to `data/processed/`: `covid.parquet`, `non_covid.parquet` (includes Flu), `flu.parquet`, and a full merged `cleaned_vaers.parquet`. Also write a human‑readable CSV `cleaned_vaers.csv`.  
  - **Verification**: Unit test `tests/unit/test_clean_filter.py` asserts existence of each Parquet file, that `covid + non_covid == cleaned_vaers` row counts, and that no `SOC_NAME` is null. Log summary to `logs/clean_summary.txt`.

- [ ] **T010** Implement `src/analysis/disproportionality.py` to compute ROR, PRR, IC and apply the 2‑out‑of‑3 rule (FR‑005).  
  - **Workflow**:  
    1. Read `data/processed/non_covid.parquet` (the spec‑compliant baseline) and `data/processed/covid.parquet`.  
    2. For every SOC with **≥ 5** total reports across both groups, build a 2×2 contingency table (COVID vs. Non‑COVID).  
    3. Apply continuity correction 0.5 to any zero cell.  
    4. Compute ROR, PRR, IC and their 95 % Wald CIs; obtain two‑sided p‑values via Fisher’s exact test (`scipy.stats.fisher_exact`).  
    5. Perform Benjamini‑Hochberg correction (`statsmodels.stats.multitest.multipletests`) on the raw p‑values (α = 0.05).  
    6. Flag a signal if **at least two** of the three metrics meet their thresholds (`ROR>2.0 & lower CI>1.0`, `PRR>1.5 & lower CI>1.0`, `IC>0 & lower CI>0`). Populate `is_signal` and `signal_metrics`.  
    7. Write `output/signals.csv` conforming exactly to `contracts/signal.schema.yaml` and add column `background_rate_status` set to `"UNKNOWN"` for every row.  
    8. Additionally, write `output/soc_cluster_stats.csv` conforming to `contracts/soc_cluster.schema.yaml` containing the aggregated counts and metric values for each SOC.  
    9. Log summary statistics (total SOCs examined, signals found, warnings) to `logs/disproportionality.txt`.  
  - **Verification**: Integration test `tests/integration/test_disproportionality.py` runs the script on the real processed data and asserts that both `output/signals.csv` and `output/soc_cluster_stats.csv` exist, contain the required header columns, and that at least one row has `is_signal = True`.

- [ ] **T011** Implement `src/analysis/sensitivity.py` (FR‑007).  
  - **Steps**:  
    1. Load `output/signals.csv` and `data/processed/covid.parquet`.  
    2. Select the top 5 signals by smallest `p_value_adj`.  
    3. Re‑compute ROR, PRR, IC using **Flu‑only** as the reference group instead of the full non‑COVID baseline.  
    4. Calculate deltas (`ror_delta = ror_flu - ror_non_covid`, etc.) and write `output/sensitivity_analysis.csv` with columns `SOC_CODE, SOC_NAME, ror_delta, prr_delta, ic_delta`.  
    5. Log the operation to `logs/sensitivity.txt`.  
  - **Verification**: Unit test `tests/unit/test_sensitivity.py` runs the function on a tiny synthetic parquet fixture and checks that the three delta columns are present and numeric.

- [ ] **T012** Implement `src/analysis/temporal.py` (FR‑004).  
  - **Steps**:  
    1. Read `output/signals.csv` and select the top 5 signals (or all if fewer).  
    2. Compute the median `REPT_DATE` across the combined COVID + Non‑COVID cohort.  
    3. For each selected SOC, aggregate weekly counts of reports relative to that median (negative weeks = earlier than median, positive = later).  
    4. Call `src.utils.plots.save_line_plot` to produce a PNG per SOC in `output/temporal_profiles/` titled **“Weekly Reporting Time for {SOC_NAME}”** with axis label **“Weeks relative to cohort median reporting date”**.  
    5. If no signals exist, write `output/temporal_profiles/empty_signal_warning.txt`.  
    6. Log creation of each figure to `logs/temporal.txt`.  
  - **Verification**: Integration test `tests/integration/test_temporal_profiles.py` asserts that at least one PNG file exists when signals are present and that the warning file is absent.

- [ ] **T013** Create the pipeline orchestrator `src/main.py` with memory profiling (SC‑004) and end‑to‑end execution.  
  - **Features**:  
    1. Use a `psutil` context manager to record peak RAM usage (GB) for the whole run; write `output/memory_profile.json` (`{"peak_gb": <float>, "status": "OK"}` if ≤ 7 GB, else `"EXCEEDED"`).  
    2. Sequentially invoke the scripts from **T007–T012** (download, mapping, cleaning, disproportionality, sensitivity, temporal).  
    3. After all analyses, call `src/validation/validate_outputs.py`.  
  - **Verification**: Running `python -m src.main` on a small sampled dataset must produce `output/memory_profile.json` with `"status": "OK"` and no uncaught exceptions; log captured in `logs/main_run.txt`.

- [ ] **T014** Implement `src/validation/validate_outputs.py` to enforce all quantitative success criteria.  
  - **Checks**:  
    1. **BH monotonicity (SC‑002)** – confirm that adjusted p‑values are non‑decreasing when sorted by raw p‑value.  
    2. **SC‑001** – compute the proportion of SOCs with finite (non‑NaN/Inf) ROR, PRR, and IC; must be ≥ 0.95.  
    3. **SC‑003** – verify that weekly reporting PNGs exist for the top‑5 signals and that the temporal profile script completed without warnings.  
    4. **SC‑004** – ensure `output/memory_profile.json` reports `"status": "OK"` (peak RAM ≤ 7 GB).  
    5. **SC‑005** – compute the proportion of signals that satisfy the 2‑out‑of‑3 rule; report the value.  
    6. **Background‑rate flag** – ensure every row in `output/signals.csv` has `background_rate_status == "UNKNOWN"`.  
    7. **SOC‑cluster contract** – run `jsonschema` validation of `output/soc_cluster_stats.csv` against `contracts/soc_cluster.schema.yaml`.  
  - **Output**: Write `output/validation.log` containing clear PASS/FAIL lines for each check.  
  - **Verification**: A CI step greps `output/validation.log` for the string “FAIL”; it must find none.

- [ ] **T015** Generate the final human‑readable report and verify CPU‑only compliance.  
  - **Report (`output/report.md`)** must include:  
    1. Memory usage summary (from `memory_profile.json`).  
    2. Validation metrics (copy of PASS lines from `validation.log`).  
    3. Table of the top 10 signals (derived from `output/signals.csv`).  
    4. Embedded figures: forest plots (from `disproportionality.py`) and temporal PNGs.  
    5. Limitations section explicitly stating that temporal analysis is **“Reporting Time”** only, no causal inference, and that background incidence rates are unknown (`background_rate_status = "UNKNOWN"`).  
    6. No occurrence of the prohibited strings “Post‑Vaccination Time”, “Causal”, or “Incidence Rate”.  
  - **CPU‑only check**: Run `src/utils/cpu_check.py` (see below) and ensure `logs/cpu_check.txt` contains “PASS”.  
  - **Verification**: CI runs two checks:  
    - `grep -E "Post‑Vaccination|Causal|Incidence Rate" output/report.md && echo "FAIL"` – must produce no output.  
    - `cat logs/cpu_check.txt` must contain the word “PASS”.  

- [ ] **T016** Documentation polish (quickstart & style).  
  - **Update `README.md`**: Add a **Quickstart** section with the exact commands:  
    ```bash
    pip install -r requirements.txt
    python -m src.main
    ```  
    and a brief description of each output artifact.  
  - **Style enforcement**: Run `ruff --fix .` and `black .`; capture the summary of changes in `logs/style_fix.txt`.  
  - **Verification**: Re‑run the lint commands from **T003**; both must exit with status 0. Additionally, `grep -q "Quickstart" README.md` must succeed.

- [ ] **T017** Generate SOC‑cluster summary and validate against its schema.  
  - **Extension**: The disproportionality script (T010) now also writes `output/soc_cluster_stats.csv` containing, for each SOC, the counts (`covid_count`, `non_covid_count`) and the computed metrics (`ror`, `ror_lower_ci`, `ror_upper_ci`, `prr`, `prr_lower_ci`, `ic`, `ic_lower_ci`, `p_value`, `p_adj`).  
  - **Validation**: `src/validation/validate_outputs.py` (T014) runs `jsonschema` on this file using `contracts/soc_cluster.schema.yaml`.  
  - **Verification**: CI checks that `output/soc_cluster_stats.csv` exists, has a header matching the schema, and that `output/validation.log` contains a PASS line for “SOC‑cluster contract validation”.
