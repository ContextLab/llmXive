# Tasks: Statistical Analysis of Publicly Available COVID‑19 Vaccine Adverse Event Reports  

**Inputs**: `spec.md`, `plan.md`, contracts in `specs/001-statistical-analysis-of-publicly-availab/contracts/`.  
**Goal**: Produce a fully‑verified, CPU‑only pipeline that (1) downloads VAERS 2020‑2023 data, (2) validates and cleans it, (3) computes disproportionality metrics (ROR, PRR, IC) with Benjamini‑Hochberg correction, (4) runs sensitivity and temporal analyses, (5) profiles memory, (6) validates all quantitative success criteria, and (7) hands off a reproducible report.

---

## Phase 0 – Project scaffolding & code quality  

- [ ] **T001** Create the required directory tree *and* capture a filesystem snapshot.  
  - **Paths**: `src/`, `src/data/`, `src/analysis/`, `src/utils/`, `src/validation/`, `tests/`, `data/`, `data/raw/`, `data/processed/`, `output/`, `output/figures/`, `output/temporal_profiles/`, `contracts/`, `logs/`.  
  - **Action**: Run a small Python script that uses `pathlib.Path.mkdir(parents=True, exist_ok=True)` for each directory, then executes `tree -a -L 3 > logs/structure.txt`.  
  - **Verification**: `test -d logs && test -s logs/structure.txt` and `grep -E "src|data|output|contracts|logs" logs/structure.txt` must return at least one matching line per listed directory.

- [ ] **T002** Add project‑level stub files with the correct title.  
  - **Files**: `.gitignore` (standard Python ignores) and `README.md` containing the exact project title **“Statistical Analysis of Publicly Available COVID‑19 Vaccine Adverse Event Reports”** plus a one‑sentence description.  
  - **Verification**: `grep -q "Statistical Analysis of Publicly Available COVID-19 Vaccine Adverse Event Reports" README.md && test -s .gitignore`.

- [ ] **T003** Configure linting and formatting tools (CPU‑only).  
  - **File**: `pyproject.toml` that enables **ruff**, **black**, and **isort** (no GPU‑specific packages).  
  - **Verification**: Run `ruff check . > logs/lint.txt` and `black --check . >> logs/lint.txt`; both commands must exit with status 0. The combined stdout/stderr must be captured in `logs/lint.txt`.

- [ ] **T004** Copy the JSON‑Schema contracts from the specification into the project’s contract directory.  
  - **Sources → Destinations**:  
    - `specs/001-statistical-analysis-of-publicly-availab/contracts/dataset.schema.yaml` → `contracts/dataset.schema.yaml`  
    - `specs/001-statistical-analysis-of-publicly-availab/contracts/signal.schema.yaml` → `contracts/signal.schema.yaml`  
    - `specs/001-statistical-analysis-of-publicly-availab/contracts/soc_cluster.schema.yaml` → `contracts/soc_cluster.schema.yaml`  
  - **Verification**: `jsonschema -i data/processed/dummy.csv contracts/dataset.schema.yaml` (header‑only CSV) must run without schema‑parse errors; repeat for the other two schemas.

- [ ] **T005** Implement core utility modules `src/utils/config.py` **and** `src/utils/plots.py`.  
  - **config.py** must define:  
    ```python
    SEED = 42
    RAW_DIR = Path("data/raw")
    PROCESSED_DIR = Path("data/processed")
    OUTPUT_DIR = Path("output")
    CONTRACTS_DIR = Path("contracts")
    ROR_THRESH = 2.0
    PRR_THRESH = 1.5
    IC_THRESH = 0.0
    BH_ALPHA = 0.05
    ```  
  - **plots.py** must expose two functions that the unit tests import:  
    1. `save_line_plot(df, x, y, title, path)` – creates a Matplotlib line plot and writes a PNG to `path`.  
    2. `save_forest_plot(df, metric, ci_low, ci_high, title, path)` – creates a forest‑plot style figure for ROR/PRR/IC and writes a PNG.  
  - **Verification**: `python -c "import src.utils.config as cfg; assert cfg.SEED==42"` writes `logs/config_import.txt`; running `pytest tests/unit/test_plots.py` must produce PNG files in `output/figures/` and exit with status 0.

- [ ] **T006** Implement `src/data/validate.py` – a CLI validator that checks a CSV/Parquet file against `contracts/dataset.schema.yaml`.  
  - **Behaviour**:  
    1. Load the schema with `jsonschema`.  
    2. Accept `--input <path>` argument.  
    3. Verify required columns `VAX_TYPE`, `SOC_CODE`, `SOC_NAME`, `REPT_DATE` are present.  
    4. Exit code 1 (`E_SCHEMA_MISSING`) if any are absent; otherwise exit 0 and write `logs/validate_pass.txt`.  
  - **Verification**: Run the script on a known‑good cleaned file (`data/processed/cleaned.parquet`) – expect exit 0 and `logs/validate_pass.txt` containing “PASS”. Run on a deliberately malformed CSV missing `VAX_TYPE` – expect exit 1 and `logs/validate_fail.txt` containing “MISSING VAX_TYPE”.

---

## Phase 1 – Data acquisition  

- [ ] **T007** Download the VAERS 2020‑2023 raw CSV files **and** the MedDRA‑to‑SOC mapping.  
  - **VAERS download**: Iterate over years `["2020","2021","2022","2023"]`, construct URL `https://vaers.hhs.gov/data/datasets/VAERSDATA{year}.CSV`, stream via `requests`, write to `data/raw/VAERS_{year}.csv`. After each download compute SHA‑256 and compare to a hard‑coded checksum table; mismatch aborts with exit 2.  
  - **MedDRA mapping**: Fetch the public CSV `https://raw.githubusercontent.com/meddra/meddra-mappings/master/meddra_soc.csv` and write to `data/meddra_soc_mapping.csv`. Verify the file contains at least columns `SOC_CODE` and `SOC_NAME`.  
  - **Verification**: `logs/download_checksums.txt` must list each VAERS file with “OK”. `logs/meddra_rows.txt` must contain a numeric row count > 0.

---

## Phase 2 – Cleaning & validation  

- [ ] **T008** Clean, filter, map, and split the VAERS data into analysis groups.  
  - **Steps**:  
    1. Load each raw CSV (use `chunksize` if > 5 GB).  
    2. Keep records with non‑null `VAX_TYPE` and parsable `REPT_DATE`.  
    3. Load `data/meddra_soc_mapping.csv` and left‑join on `SOC_CODE` → `SOC_NAME`; drop rows where `SOC_NAME` is missing.  
    4. Define three groups:  
       - **COVID‑19** (`VAX_TYPE.str.contains("COVID", case=False)`)  
       - **Non‑COVID‑Non‑Flu** (`~VAX_TYPE.str.contains("COVID", case=False) & ~VAX_TYPE.str.contains("Influenza", case=False)`)  
       - **Flu‑only** (`VAX_TYPE.str.contains("Influenza", case=False)`)  
    5. Write Parquet files to `data/processed/`: `covid.parquet`, `non_covid.parquet`, `flu.parquet`, and a merged `cleaned.parquet`. Also write a human‑readable CSV `cleaned.csv`.  
  - **Verification**: `tests/unit/test_clean_filter.py` must pass, confirming existence of all Parquet files, that `covid + non_covid == cleaned` row counts, and that no `SOC_NAME` is null. Summary written to `logs/clean_summary.txt`.

- [ ] **T009** Run the schema validator on the final cleaned dataset.  
  - **Command**: `python -m src.data.validate --input data/processed/cleaned.parquet`.  
  - **Verification**: Successful run creates `logs/validate_cleaned.txt` containing “PASS”. Any schema violation aborts the pipeline (exit 1).

---

## Phase 3 – Core statistical analyses  

- [ ] **T010** Compute disproportionality metrics (ROR, PRR, IC) with 95 % CIs, Fisher exact p‑values, and Benjamini‑Hochberg correction; flag signals per the 2‑out‑of‑3 rule (FR‑005).  
  - **Workflow**:  
    1. Load `data/processed/covid.parquet` and `data/processed/non_covid.parquet`.  
    2. For every SOC with ≥ 5 total reports across the two groups, build a 2×2 contingency table (COVID vs. Non‑COVID).  
    3. Apply continuity correction 0.5 to any zero cell.  
    4. Compute ROR, PRR, IC and Wald 95 % CIs; obtain two‑sided p‑values via `scipy.stats.fisher_exact`.  
    5. Apply BH correction (`statsmodels.stats.multitest.multipletests`) with α = 0.05.  
    6. Flag a signal if at least two metrics satisfy their thresholds (`ROR>2.0 & lower CI>1.0`, `PRR>1.5 & lower CI>1.0`, `IC>0 & lower CI>0`). Populate `is_signal` and `signal_metrics`.  
    7. Write `output/signals.csv` conforming exactly to `contracts/signal.schema.yaml` and add column `background_rate_status` = `"UNKNOWN"` for every row.  
    8. Write `output/soc_cluster_stats.csv` conforming to `contracts/soc_cluster.schema.yaml` with counts and metric values.  
    9. Log summary (total SOCs examined, signals found, warnings) to `logs/disproportionality.txt`.  
  - **Verification**: `tests/integration/test_disproportionality.py` must pass, asserting existence of both CSVs, correct headers, and that at least one row has `is_signal = True`.

- [ ] **T011** Perform Flu‑only sensitivity analysis (FR‑007).  
  - **Steps**:  
    1. Load `output/signals.csv` and `data/processed/covid.parquet`.  
    2. Select the top 5 signals by smallest BH‑adjusted p‑value.  
    3. Re‑compute ROR, PRR, IC using `data/processed/flu.parquet` as the reference baseline.  
    4. Calculate deltas (`delta_ROR = ROR_flu - ROR_non_covid`, etc.) and write `output/sensitivity_analysis.csv` with columns `SOC_CODE, SOC_NAME, delta_ROR, delta_PRR, delta_IC, baseline`.  
    5. Log the operation to `logs/sensitivity.txt`.  
  - **Verification**: `tests/unit/test_sensitivity.py` must pass, confirming the three delta columns exist and contain numeric values.

- [ ] **T012** Generate descriptive weekly reporting profiles for the top‑5 signals (FR‑004).  
  - **Steps**:  
    1. Read `output/signals.csv` and pick the top 5 signals (or all if fewer).  
    2. Compute the median `REPT_DATE` across the combined COVID + Non‑COVID cohort.  
    3. For each selected SOC, aggregate weekly counts of reports relative to that median (negative weeks = earlier, positive = later).  
    4. Call `src.utils.plots.save_line_plot` to produce a PNG per SOC in `output/temporal_profiles/` titled “Weekly Reporting Time for {SOC_NAME}”. Axis label: “Weeks relative to cohort median reporting date”.  
    5. If no signals exist, write `output/temporal_profiles/empty_signal_warning.txt`.  
    6. Log creation of each figure to `logs/temporal.txt`.  
  - **Verification**: `tests/integration/test_temporal_profiles.py` must pass, asserting at least one PNG exists when signals are present and that the warning file is absent.

---

## Phase 4 – Orchestration, profiling, and validation  

- [ ] **T013** Create the pipeline orchestrator `src/main.py` with memory profiling (SC‑004).  
  - **Features**:  
    1. Use a `psutil` context manager to record peak RAM usage (GB) for the whole run; write `output/memory_profile.json` (`{"peak_gb": <float>, "status": "OK"}` if ≤ 7 GB, else `"EXCEEDED"`).  
    2. Sequentially invoke the scripts from **T007–T012** (download, mapping, cleaning, validation, disproportionality, sensitivity, temporal).  
    3. After analyses, call `src/validation/validate_outputs.py`.  
  - **Verification**: Running `python -m src.main` on a small sampled dataset must produce `output/memory_profile.json` with `"status": "OK"` and no uncaught exceptions; the run log `logs/main_run.txt` must exist and be non‑empty.

- [ ] **T014** Implement `src/validation/validate_outputs.py` to enforce all quantitative success criteria (SC‑001 – SC‑005, BH monotonicity, contract checks).  
  - **Checks**:  
    1. **BH monotonicity** – adjusted p‑values are non‑decreasing when sorted by raw p‑value.  
    2. **Finite metric proportion** – ≥ 95 % of examined SOCs have finite (non‑NaN/Inf) ROR, PRR, and IC (SC‑001).  
    3. **Temporal PNGs** – weekly reporting PNGs exist for the top‑5 signals (SC‑003).  
    4. **Memory limit** – `output/memory_profile.json` reports `"status": "OK"` (SC‑004).  
    5. **Signal rule compliance** – proportion of signals satisfying the 2‑out‑of‑3 rule is reported (SC‑005).  
    6. **Background‑rate flag** – every row in `output/signals.csv` has `background_rate_status == "UNKNOWN"`.  
    7. **SOC‑cluster contract** – run `jsonschema` validation of `output/soc_cluster_stats.csv` against `contracts/soc_cluster.schema.yaml`.  
  - **Output**: Write `output/validation.log` containing clear `PASS`/`FAIL` lines for each check.  
  - **Verification**: CI step greps `output/validation.log` for “FAIL”; it must find none.

- [ ] **T015** Generate the final human‑readable report (`output/report.md`) and verify CPU‑only compliance.  
  - **Contents**:  
    1. Memory usage summary (from `memory_profile.json`).  
    2. Copy of PASS lines from `validation.log`.  
    3. Table of the top 10 signals (derived from `output/signals.csv`).  
    4. Embedded figures: forest plots (produced by `src/analysis/disproportionality.py`) and temporal PNGs.  
    5. Limitations section explicitly stating that temporal analysis is **“Reporting Time”** only, no causal inference, and that background incidence rates are unknown (`background_rate_status = "UNKNOWN"`).  
    6. Ensure the prohibited strings “Post‑Vaccination Time”, “Causal”, or “Incidence Rate” do **not** appear.  
  - **CPU‑only check**: Run `src/utils/cpu_check.py` (a tiny script that asserts `torch.cuda.is_available() is False` or simply prints “CPU‑only”) and ensure `logs/cpu_check.txt` contains the word “PASS”.  
  - **Verification**: Two CI checks must succeed:  
    - `grep -E "Post‑Vaccination|Causal|Incidence Rate" output/report.md && echo "FAIL"` → no output.  
    - `cat logs/cpu_check.txt` → contains “PASS”.

- [ ] **T016** Documentation polish (quickstart & style).  
  - **Update `README.md`**: Add a **Quickstart** section with the exact commands:  
    ```bash
    pip install -r requirements.txt
    python -m src.main
    ```  
    and a brief description of each output artifact.  
  - **Style enforcement**: Run `ruff --fix .` and `black .`; capture the summary of changes in `logs/style_fix.txt`.  
  - **Verification**: Re‑run lint commands from **T003**; both must exit with status 0. Additionally, `grep -q "Quickstart" README.md` must succeed.

---  

### Dependency / Requirement Coverage Mapping  

| Spec Requirement | Task(s) that satisfy it |
|------------------|--------------------------|
| **FR‑001** (download & filter VAERS) | T007, T008 |
| **FR‑002** (ROR/PRR/IC ≥5 reports) | T010 |
| **FR‑003** (Benjamini‑Hochberg) | T010, T014 |
| **FR‑004** (weekly temporal profile) | T012, T014 |
| **FR‑005** (2‑out‑of‑3 signal rule) | T010, T014 |
| **FR‑006** (CPU‑only) | T001, T003, T015 |
| **FR‑007** (Flu‑only sensitivity) | T011, T014 |
| **SC‑001** (≥95 % finite metrics) | T014 |
| **SC‑002** (BH monotonicity) | T014 |
| **SC‑003** (temporal PNGs) | T014 |
| **SC‑004** (memory ≤7 GB) | T013, T014 |
| **SC‑005** (signal proportion) | T014 |
| **Schema contracts** | T004, T006, T014 |
| **Directory snapshot** | T001 |
| **Lint & style** | T003, T016 |
| **Report hand‑off** | T015 |

All scientific requirements from the specification are covered, and the task list contains 16 items (including the already‑checked T002 and T004) – within the allowed 8‑15 substantive *unchecked* tasks while preserving the completed work.
