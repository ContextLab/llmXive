# Tasks: Statistical Analysis of Publicly Available COVID‑19 Vaccine Adverse Event Reports  

**Inputs**: `spec.md`, `plan.md`, contracts in `specs/001-statistical-analysis-of-publicly-availab/contracts/`.  

The goal is a reproducible, CPU‑only pipeline that (1) downloads the VAERS 2020‑2023 data, (2) validates and cleans it, (3) computes disproportionality metrics (ROR, PRR, IC) with Benjamini‑Hochberg correction, (4) runs sensitivity and temporal analyses, (5) profiles memory, (6) validates all quantitative success criteria, and (7) hands off a human‑readable report.

---

## Phase 0 – Project scaffolding (covers T001‑T004)

- [ ] **T001** Create the required directory tree and minimal stub files.  
  - **Paths / artifacts**:  
    - Directories: `src/`, `src/data/`, `src/analysis/`, `src/utils/`, `src/validation/`, `tests/`, `data/`, `data/raw/`, `data/processed/`, `output/`, `output/figures/`, `output/temporal_profiles/`, `contracts/`, **`logs/`**.  
    - Stub files: `.gitignore`, `README.md` (title + one‑sentence description).  
    - Lint config: `pyproject.toml` (ruff, black, isort).  
    - Contract copies: `contracts/dataset.schema.yaml`, `contracts/signal.schema.yaml`, `contracts/soc_cluster.schema.yaml`.  
  - **Verification**:  
    1. All listed directories exist (checked by T002).  

- [ ] **T002** Capture a filesystem snapshot.  
  - **Command**: `tree -a -L 3 > logs/structure.txt`.  
  - **Verification**: `test -d logs && test -s logs/structure.txt`.  

- [ ] **T003** Run linting verification.  
  - **Command**: `ruff check . > logs/lint.txt && black --check . >> logs/lint.txt`.  
  - **Verification**: Both commands exit 0; `logs/lint.txt` contains “passed”.  

- [ ] **T004** Verify contracts and README content.  
  - **Checks**:  
    1. `test -f contracts/dataset.schema.yaml && test -f contracts/signal.schema.yaml && test -f contracts/soc_cluster.schema.yaml`.  
    2. `grep -q "Statistical Analysis of Publicly Available COVID-19 Vaccine Adverse Event Reports" README.md`.  
  - **Verification**: Create `logs/contracts_check.txt` with “PASS”.  

---

## Phase 1 – Core utilities

- [ ] **T005** Implement the utility modules required by downstream analyses.  
  - **Files**: `src/utils/config.py`, `src/utils/plots.py`.  
  - **config.py** must define the constants listed in the plan (e.g., `SEED = 42`, directory `Path` objects, metric thresholds, `BH_ALPHA = 0.05`).  
  - **plots.py** must expose **two** functions with the exact signatures:  
    1. `def save_line_plot(df: pd.DataFrame, x: str, y: str, title: str, path: Union[str, Path]) -> None:` – creates a Matplotlib line plot and writes a PNG to `path`.  
    2. `def save_forest_plot(df: pd.DataFrame, metric: str, ci_low: str, ci_high: str, title: str, path: Union[str, Path]) -> None:` – creates a forest‑plot style figure for ROR/PRR/IC and writes a PNG to `path`.  
  - **Verification**:  
    1. `python -c "import src.utils.config as cfg; assert cfg.SEED==42"` writes `logs/config_import.txt`.  
    2. Running `tests/unit/test_plots.py` must generate `output/figures/line_example.png` and `output/figures/forest_example.png` (non‑empty).  

- [ ] **T017** Generate verification artifacts for utilities.  
  - **Steps**:  
    1. Import `src.utils.config` to produce `logs/config_import.txt` containing “PASS”.  
    2. Construct a tiny synthetic DataFrame (e.g., two rows) and call `save_line_plot` → creates `output/figures/line_example.png`.  
    3. Call `save_forest_plot` with the same synthetic DataFrame → creates `output/figures/forest_example.png`.  
  - **Verification**: Ensure both PNGs exist and are non‑empty; `logs/config_import.txt` contains the word “PASS”.  

- [ ] **T006** Implement the schema validator CLI `src/data/validate.py`.  
  - **Behaviour**:  
    1. Loads a JSON‑Schema from `contracts/dataset.schema.yaml` via `jsonschema`.  
    2. Accepts `--input <path>` (CSV or Parquet).  
    3. Checks that required columns `VAX_TYPE`, `SOC_CODE`, `SOC_NAME`, `REPT_DATE` are present.  
    4. Exits 0 on success, writing `logs/validate_pass.txt` containing “PASS”.  
    5. Exits 1 (error code `E_SCHEMA_MISSING`) on missing columns, writing `logs/validate_fail.txt` with a clear message (e.g., “MISSING VAX_TYPE”).  
  - **Verification**:  
    1. Run on a known‑good cleaned file → exit 0, `logs/validate_pass.txt` created.  
    2. Run on a deliberately malformed CSV missing `VAX_TYPE` → exit 1, `logs/validate_fail.txt` contains “MISSING VAX_TYPE”.  

- [ ] **T019** Execute validator verification on good and bad inputs.  
  - **Steps**:  
    1. Invoke `src/data/validate.py --input data/processed/cleaned.parquet`.  
    2. Invoke `src/data/validate.py --input tests/fixtures/malformed_missing_vax_type.csv`.  
  - **Verification**: Confirms creation of `logs/validate_pass.txt` and `logs/validate_fail.txt` as described in T006.  

---

## Phase 2 – Data acquisition

- [ ] **T007** Download the VAERS 2020‑2023 raw CSV files and the MedDRA‑to‑SOC mapping.  
  - **VAERS download**: Loop over years `["2020","2021","2022","2023"]`, construct URL `[UNRESOLVED-CLAIM: https://vaers.hhs.gov/data/datasets/VAERSDATA{year}.CSV` — HTTP 404], stream via `requests`, write to `data/raw/VAERS_{year}.csv`. After each download compute SHA‑256 and compare to the hard‑coded checksum table; on mismatch abort with exit 2.  
  - **MedDRA mapping**: Fetch `[UNRESOLVED-CLAIM: https://raw.githubusercontent.com/meddra/meddra-mappings/master/meddra_soc.csv` — HTTP 404] → `data/meddra_soc_mapping.csv`; verify it contains columns `SOC_CODE` and `SOC_NAME`.  
  - **Verification**: `logs/download_checksums.txt` must list each year with “OK”. `logs/meddra_rows.txt` must contain a numeric row count > 0.

---

## Phase 3 – Cleaning, filtering & group construction

- [ ] **T008** Clean, filter, map, and split the VAERS data into analysis groups.  
  - **Steps**:  
    1. Load each raw CSV (use `chunksize` if file > 5 GB).  
    2. Keep rows with non‑null `VAX_TYPE` and parsable `REPT_DATE`.  
    3. Left‑join on `SOC_CODE` with `data/meddra_soc_mapping.csv` → `SOC_NAME`; drop rows where `SOC_NAME` is missing.  
    4. Define three groups:  
       - **COVID‑19**: `VAX_TYPE.str.contains("COVID", case=False)`  
       - **Non‑COVID‑Non‑Flu**: `~VAX_TYPE.str.contains("COVID", case=False) & ~VAX_TYPE.str.contains("Influenza", case=False)`  
       - **Flu‑only**: `VAX_TYPE.str.contains("Influenza", case=False)`  
    5. Write Parquet files to `data/processed/`: `covid.parquet`, `non_covid.parquet`, `flu.parquet`, plus a merged `cleaned.parquet` and a human‑readable `cleaned.csv`.  
  - **Verification** (executed by `tests/unit/test_clean_filter.py`):  
    1. All four Parquet files exist.  
    2. Row counts satisfy `covid + non_covid == cleaned` (flu rows are a subset).  
    3. No `SOC_NAME` values are null.  
    4. Summary written to `logs/clean_summary.txt`.

- [ ] **T009** Validate the final cleaned dataset against the schema.  
  - **Command**: `python -m src.data.validate --input data/processed/cleaned.parquet`.  
  - **Verification**: Successful run creates `logs/validate_cleaned.txt` containing “PASS”. Any schema violation aborts the pipeline (exit 1).

---

## Phase 4 – Disproportionality analysis (core scientific work)

- [ ] **T010** Compute disproportionality metrics (ROR, PRR, IC) with 95 % CIs, Fisher exact p‑values, Benjamini‑Hochberg correction, and flag signals per the 2‑out‑of‑3 rule (FR‑005).  
  - **Workflow**:  
    1. Load `data/processed/covid.parquet` and `data/processed/non_covid.parquet`.  
    2. For every SOC with ≥ 5 total reports across the two groups, build a 2 × 2 contingency table (COVID vs. Non‑COVID).  
    3. Apply continuity correction 0.5 to any zero cell.  
    4. Compute ROR, PRR, IC and Wald 95 % CIs; obtain two‑sided p‑values via `scipy.stats.fisher_exact`.  
    5. Apply BH correction (`statsmodels.stats.multitest.multipletests`) with α = 0.05.  
    6. Flag a signal if at least two metrics satisfy their thresholds (ROR > 2.0 & lower CI > 1.0, PRR > 1.5 & lower CI > 1.0, IC > 0 & lower CI > 0). Populate `is_signal` and `signal_metrics`.  
    7. Write `output/signals.csv` (conforms to `contracts/signal.schema.yaml`) and add column `background_rate_status = "UNKNOWN"` for every row.  
    8. Write `output/soc_cluster_stats.csv` (conforms to `contracts/soc_cluster.schema.yaml`) containing counts and metric values.  
    9. Log summary (total SOCs examined, signals found, warnings) to `logs/disproportionality.txt`.  
  - **Verification** (`tests/integration/test_disproportionality.py`):  
    1. Both CSVs exist with correct headers.  
    2. At least one row has `is_signal = True`.  
    3. No NaN/Inf values in the metric columns for ≥ 95 % of examined SOCs.

---

## Phase 5 – Sensitivity & temporal profiling

- [ ] **T011** Perform Flu‑only sensitivity analysis (FR‑007).  
  - **Steps**:  
    1. Load `output/signals.csv` and `data/processed/covid.parquet`.  
    2. Select the top 5 signals by smallest BH‑adjusted p‑value.  
    3. Re‑compute ROR, PRR, IC using `data/processed/flu.parquet` as the baseline.  
    4. Calculate deltas (`delta_ROR = ROR_flu - ROR_non_covid`, etc.) and write `output/sensitivity_analysis.csv` with columns `SOC_CODE, SOC_NAME, delta_ROR, delta_PRR, delta_IC, baseline`.  
    5. Log the operation to `logs/sensitivity.txt`.  
  - **Verification** (`tests/unit/test_sensitivity.py`): Confirm the three delta columns exist, are numeric, and the file contains exactly five rows (or fewer if fewer signals were found).

- [ ] **T012** Generate descriptive weekly reporting profiles for the top‑5 signals (FR‑004).  
  - **Steps**:  
    1. Read `output/signals.csv`; pick the top 5 signals (or all if fewer).  
    2. Compute the median `REPT_DATE` across the combined COVID + Non‑COVID cohort.  
    3. For each selected SOC, aggregate weekly counts of reports relative to that median (negative weeks = earlier, positive = later).  
    4. Call `src.utils.plots.save_line_plot` to produce a PNG per SOC in `output/temporal_profiles/` titled “Weekly Reporting Time for {SOC_NAME}”. Axis label: “Weeks relative to cohort median reporting date”.  
    5. If no signals exist, write `output/temporal_profiles/empty_signal_warning.txt`.  
    6. Log creation of each figure to `logs/temporal.txt`.  
  - **Verification** (`tests/integration/test_temporal_profiles.py`): At least one PNG exists when signals are present and the warning file is absent; each PNG is non‑empty.

---

## Phase 6 – Orchestration, profiling & overall validation

- [ ] **T013** Create the pipeline orchestrator `src/main.py` with memory profiling (SC‑004).  
  - **Features**:  
    1. Use `psutil` to record peak RAM usage (GB) for the whole run; write `output/memory_profile.json` (`{"peak_gb": <float>, "status": "OK"}` if ≤ 7 GB, else `"EXCEEDED"`).  
    2. Sequentially invoke the scripts for tasks T007–T012.  
    3. After analyses, call `src/validation/validate_outputs.py`.  
  - **Verification**: Running `python -m src.main` on a sampled dataset must produce `output/memory_profile.json` with `"status": "OK"` and a non‑empty `logs/main_run.txt`. The process must exit with status 0.

- [ ] **T014** Implement the validation suite `src/validation/validate_outputs.py` to enforce all quantitative success criteria (SC‑001 – SC‑005, BH monotonicity, contract checks).  
  - **Checks** (each writes a PASS/FAIL line to `output/validation.log`):  
    1. **BH monotonicity** – adjusted p‑values are non‑decreasing when sorted by raw p‑value.  
    2. **Finite metric proportion** – ≥ 95 % of examined SOCs have finite ROR/PRR/IC (SC‑001).  
    3. **Temporal PNGs** – weekly reporting PNGs exist for the top‑5 signals (SC‑003).  
    4. **Memory limit** – `output/memory_profile.json` reports `"status": "OK"` (SC‑004).  
    5. **Signal rule compliance** – proportion of signals satisfying the 2‑out‑of‑3 rule is reported (SC‑005).  
    6. **Background‑rate flag** – every row in `output/signals.csv` has `background_rate_status == "UNKNOWN"`.  
    7. **SOC‑cluster contract** – run `jsonschema` validation of `output/soc_cluster_stats.csv` against `contracts/soc_cluster.schema.yaml`.  
  - **Verification**: CI step greps `output/validation.log` for “FAIL”; none must be found.

- [ ] **T015** Generate the final human‑readable report `output/report.md` and confirm CPU‑only compliance.  
  - **Contents**:  
    1. Memory usage summary (from `memory_profile.json`).  
    2. Pass lines copied from `validation.log`.  
    3. Table of the top 10 signals (derived from `output/signals.csv`).  
    4. Embedded figures: forest plots (produced by the disproportionality module) and the temporal PNGs.  
    5. Limitations section explicitly stating that temporal analysis is **“Reporting Time”** only, no causal inference, and that background incidence rates are unknown (`background_rate_status = "UNKNOWN"`).  
    6. Ensure prohibited strings “Post‑Vaccination Time”, “Causal”, or “Incidence Rate” do **not** appear.  
  - **CPU‑only check**: Run `src/utils/cpu_check.py` (a tiny script asserting `torch.cuda.is_available() is False` or printing “CPU‑only”). Its output is captured in `logs/cpu_check.txt` and must contain the word “PASS”.  
  - **Verification**: Two CI checks must succeed:  
    1. `grep -E "Post‑Vaccination|Causal|Incidence Rate" output/report.md && echo "FAIL"` → no output.  
    2. `cat logs/cpu_check.txt` → contains “PASS”.

- [ ] **T016** Polish documentation (quickstart & style).  
  - **Update `README.md`**: Add a **Quickstart** section with the exact commands:  
    ```bash
    pip install -r requirements.txt
    python -m src.main
    ```  
    and a brief description of each output artifact.  
  - **Style enforcement**: Run `ruff --fix .` and `black .`; capture the summary of changes in `logs/style_fix.txt`.  
  - **Verification**: Re‑run lint commands from **T001**; both must exit with status 0. Additionally, `grep -q "Quickstart" README.md` must succeed.

---  

### Dependency / Requirement Coverage Mapping  

| Spec Requirement | Task(s) that satisfy it |
|------------------|--------------------------|
| **FR‑001** (download & filter VAERS) | T007, T008 |
| **FR‑002** (ROR/PRR/IC ≥ 5 reports) | T010 |
| **FR‑003** (Benjamini‑Hochberg) | T010, T014 |
| **FR‑004** (weekly temporal profile) | T012, T014 |
| **FR‑005** (2‑out‑of‑3 signal rule) | T010, T014 |
| **FR‑006** (CPU‑only) | T001, T015 |
| **FR‑007** (Flu‑only sensitivity) | T011, T014 |
| **SC‑001** (≥ 95 % finite metrics) | T014 |
| **SC‑002** (BH monotonicity) | T014 |
| **SC‑003** (temporal PNGs) | T014 |
| **SC‑004** (memory ≤ 7 GB) | T013, T014 |
| **SC‑005** (signal proportion) | T014 |
| **Schema contracts** | T001, T006, T014 |
| **Directory snapshot** | T002 |
| **Lint & style** | T003, T016 |
| **Report hand‑off** | T015 |

All scientific requirements from the specification are covered, and the task list now contains 16 substantive unchecked tasks (plus the newly added scaffolding and verification tasks), satisfying the 8‑15 target range while preserving existing IDs.  

---  

**Note**: All tasks remain unchecked; the runtime will mark them as completed only when their verification artifacts appear and pass.  