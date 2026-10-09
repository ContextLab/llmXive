# Tasks: Statistical Analysis of Flight Delay Distributions  

**Inputs**: `spec.md`, `plan.md`, existing research artifacts, contracts, and data‑model definitions.  

The checklist follows the canonical format `- [ ] T### [P?] [USx?] description …` where:  

* `T###` – unique task identifier.  
* `[P]` – can run in parallel with other `[P]` tasks (different files, no ordering constraints).  
* `[USx]` – the user story (US1, US2, US3) that the task satisfies.  
* The indented lines describe concrete outputs, verification steps, and required file paths.  

---  

## Phase 1 – Project scaffolding & first end‑to‑end run  

| # | Task |
|---|------|
- [ ] T001 **Create project directory layout** – `code/`, `tests/`, `data/raw/`, `data/processed/`, `data/results/`, `docs/`.  <br>  *Verification*: `tree` shows all directories; `git status` clean. |
- [ ] T002 **Add `requirements.txt`** with pinned versions of `pandas`, `numpy`, `scipy`, `matplotlib`, `seaborn`, `pyyaml`, `statsmodels`, `pytest`.  <br>  *Verification*: `pip install -r requirements.txt` succeeds without conflicts. |
- [ ] T003 **Create `pyproject.toml`** configuring `ruff` and `black` for the `code/` package.  <br>  *Verification*: `ruff .` and `black .` run without errors. |
- [ ] T004 **Add `code/config.py`** – defines constants `RANDOM_SEED=42`, `BTS_URL="https://transtats.bts.gov/OT_Delay/On_Time_Reporting_CSV.zip"`, `TARGET_YEAR=2022`, `MEMORY_LIMIT_GB=6.5`.  <br>  *Verification*: `python -c "import code.config as cfg; assert cfg.TARGET_YEAR==2022"` passes. |
- [ ] T005 **Implement memory utilities in `code/utils.py`** – `check_memory_limit(limit_gb)` raises `MemoryError` if usage exceeds limit; `log_peak_memory()` writes peak RAM to `data/logs/pipeline.log`.  <br>  *Verification*: Unit test in `tests/unit/test_utils.py` asserts exception on simulated over‑use. |
- [ ] T006 **Add JSON‑Schema contracts** – copy the three schema files into `code/contracts/` (`delay_record.schema.yaml`, `fitted_model.schema.yaml`, `tail_index_estimate.schema.yaml`).  <br>  *Verification*: `jsonschema.validate` against a minimal instance succeeds. |
- [ ] T007 **Set up pytest infrastructure** – create `tests/conftest.py` with common fixtures (e.g., temporary data directory).  <br>  *Verification*: `pytest -q` runs with 0 tests (no errors). |
- [ ] T008 **Configure logging & custom exception** in `code/utils.py` – logger writes INFO to `data/logs/pipeline.log`; define `PipelineError`.  <br>  *Verification*: Running any pipeline step creates the log file with a timestamp. |
- [ ] T009 **Implement streaming CSV loader stub** in `code/data_loader.py` – uses `pandas.read_csv(..., chunksize=100_000)` and writes each chunk to `data/raw/`.  <br>  *Verification*: Unit test confirms that a small public CSV is streamed without loading whole file into memory. |
- [ ] T010 **Run a minimal end‑to‑end smoke test** – orchestrate `code/data_loader.py` → `code/preprocessing.py` on a **sample** of the BTS CSV (first 10 000 rows) and produce `data/processed/sample_cleaned.csv`.  <br>  *Verification*: `ls data/processed/sample_cleaned.csv` and checksum matches expected sample size. |
- [ ] T011 **Create `quickstart.md`** – documents the one‑line command `python -m code.main --year 2022 --mode smoke`.  <br>  *Verification*: The markdown renders a runnable command; the command executes the smoke test from T010. |

---  

## Phase 2 – User Story 1: Data Acquisition & Pre‑processing (US1)  

- [ ] T012 **Download full‑year BTS data** (`code/data_loader.py`) – streams the 2022 ZIP, extracts CSVs into `data/raw/2022/`.  <br>  *Verification*: `data/raw/2022/On_Time_Reporting_CSV.zip` exists; its SHA‑256 matches the value recorded in `data/README.md`. |
- [ ] T013 **Parse and clean raw CSV** (`code/preprocessing.py`) – computes `total_delay = ArrDelay + DepDelay` (NaN → 0), removes negative delays, keeps only commercial U.S. flights.  <br>  *Verification*: Output `data/processed/cleaned_delays.csv` contains columns `flight_id,total_delay_minutes,carrier,origin,destination,is_anomaly,is_data_error,is_zero`. |
- [ ] T014 **Flag anomalies & data errors** – `is_anomaly=True` for `delay>1440`; `is_data_error=True` for `delay>10000`. Errors are excluded from the primary analysis set.  <br>  *Verification*: Count of rows where `is_data_error` is true matches manual inspection; those rows are absent from `data/processed/analysis_set.csv`. |
- [ ] T015 **Calculate & record retention rate** – `valid_records / total_downloaded` written to `data/results/summary.json` under key `"retention_rate"`.  <br>  *Verification*: JSON field exists and is ≥ 0.95; if lower, pipeline raises `PipelineError` with message `"Retention rate below 95 %"`. |
- [ ] T016 **Zero‑inflation sensitivity subset** – create `data/processed/cleaned_delays_no_zero.csv` by dropping rows where `total_delay_minutes == 0`.  <br>  *Verification*: Row count of the no‑zero file is ≤ original and `is_zero` column is all `false`. |
- [ ] T017 **Memory‑limit enforcement** – `code/preprocessing.py` calls `utils.check_memory_limit` before loading each chunk; if limit exceeded, raises `PipelineError` with message `"Memory limit exceeded: full dataset cannot be loaded."`.  <br>  *Verification*: Simulated large chunk triggers the exception (unit test). |
- [ ] T018 **Component comparison dataset** – compute separate series for `ArrDelay` and `DepDelay`; store side‑by‑side CSV `data/processed/component_delays.csv`.  <br>  *Verification*: File contains three columns `total_delay,arr_delay,dep_delay`. |
- [ ] T019 **Integration test for full download‑to‑clean pipeline** (`tests/integration/test_us1_pipeline.py`).  <br>  *Verification*: `pytest -q tests/integration/test_us1_pipeline.py` passes, asserting existence and schema compliance of `cleaned_delays.csv` and `summary.json`. |

---  

## Phase 3 – User Story 2: Parametric Model Fitting & Goodness‑of‑Fit (US2)  

- [ ] T020 **Estimate tail threshold `x_min`** (`code/diagnostics.py`) – implements Clauset et al. KS‑minimization over a grid; writes `data/results/x_min_estimate.json` with fields `x_min`, `ks_stat`, `confidence_interval`.  <br>  *Verification*: JSON contains numeric `x_min` and KS statistic; unit test checks that varying the grid changes the output consistently. |
- [ ] T021 **Fit all five distributions to the *full* cleaned set** (`code/models.py`) – Exponential, Gamma, Log‑Normal, Weibull, Pareto (unrestricted).  <br>  *Verification*: `data/results/full_model_fits.json` contains a list of five objects each with `name`, `parameters`, and `converged=True`. |
- [ ] T022 **Fit all five distributions to the *tail* subset** (`delay >= x_min`) – re‑uses `code/models.py` with the threshold from T020.  <br>  *Verification*: `data/results/tail_model_fits.json` contains five entries; Pareto fitting respects `delay >= x_min`. |
- [ ] T023 **Compute model metrics** – for each tail fit calculate AIC, BIC, KS, Anderson‑Darling, tail‑KS, and store in `data/results/model_comparison.json` following `fitted_model.schema.yaml`.  <br>  *Verification*: JSON validates against the schema; at least three models have `converged=True`. |
- [ ] T024 **Component‑distribution KS test** – compare `total_delay` vs `ArrDelay` and `DepDelay` using `scipy.stats.ks_2samp`; results saved to `data/results/component_comparison.json`.  <br>  *Verification*: JSON includes `ks_stat_total_vs_arr`, `pvalue_total_vs_arr`, etc. |
- [ ] T025 **Run Vuong test** – compare the best heavy‑tailed candidate (Pareto or Log‑Normal) against the best short‑tailed candidate (Exponential, Gamma, Weibull) on the tail subset; output `data/results/vuong_test.json` with `p_value`.  <br>  *Verification*: JSON contains `"p_value"` field; unit test checks that a known synthetic dataset yields a Vuong statistic > 0. |
- [ ] T026 **Orchestrate Phase 2 in `code/main.py` (stage 2)** – calls T020 → T022 → T023 → T025 → writes a consolidated `data/results/phase2_complete.marker`.  <br>  *Verification*: Marker file exists after successful run; its timestamp matches end of pipeline. |
- [ ] T027 **Integration test for full modelling pipeline** (`tests/integration/test_us2_models.py`).  <br>  *Verification*: Passes, confirming that `model_comparison.json` contains at least three converged models and that `vuong_test.json` is present. |

---  

## Phase 4 – User Story 3: Heavy‑Tail Diagnostics & Visualization (US3)  

- [ ] T028 **Hill‑estimator stability analysis** (`code/diagnostics.py`) – loads `x_min`, iterates `k` up to `0.1 × n`, computes Hill estimate for each `k`, calculates variance over a sliding window `w=10`, selects optimal `k`.  <br>  *Verification*: `data/results/tail_index_estimate.json` conforms to `tail_index_estimate.schema.yaml`; includes `threshold_k`, `estimated_alpha`, `confidence_interval`, `stability_range`. |
- [ ] T029 **Generate log‑log survival plot** – uses OLS on log‑log transformed tail data; computes `R²`; saves PNG `data/results/figures/log_log_survival.png` and writes `r_squared_log_log` to the tail‑index JSON.  <br>  *Verification*: Plot file exists; JSON field `r_squared_log_log` ≥ 0.95 for accepted models. |
- [ ] T030 **Generate QQ‑plot for best‑fit model** – overlays empirical quantiles vs theoretical quantiles; saves `data/results/figures/qq_plot.png`.  <br>  *Verification*: PNG file exists; visual inspection confirms alignment (no automated check). |
- [ ] T031 **Tail KS goodness‑of‑fit test** – applies `scipy.stats.kstest` on the tail subset against the CDF of the selected heavy‑tailed model; writes `data/results/tail_ks.json` with `ks_statistic`, `p_value`, `tail_threshold`.  <br>  *Verification*: JSON validates against the schema; p‑value recorded. |
- [ ] T032 **Model rejection logic** – reads `model_comparison.json` and `tail_index_estimate.json`; if `R² < 0.95` **or** Hill estimator is unstable (variance > pre‑defined threshold), marks the model as rejected, updates `model_comparison.json` with `"status": "rejected"` and `"reason"`; selects next‑best candidate.  <br>  *Verification*: After running, at least one model has `"status":"accepted"`; rejected models list reasons. |
- [ ] T033 **Orchestrate Phase 3 in `code/main.py` (stage 3)** – runs T028 → T029 → T030 → T031 → T032; writes `data/results/phase3_complete.marker`.  <br>  *Verification*: Marker file appears; its timestamp is later than Phase 2 marker. |
- [ ] T034 **Integration test for diagnostics pipeline** (`tests/integration/test_us3_diagnostics.py`).  <br>  *Verification*: Passes, confirming existence of all figure files and that `tail_index_estimate.json` validates. |

---  

## Phase 5 – Final Reporting & Verification  

- [ ] T035 **Compile final results JSON** – merge `summary.json`, `model_comparison.json`, `vuong_test.json`, `tail_index_estimate.json`, and `component_comparison.json` into a single `data/results/final_report.json`.  <br>  *Verification*: JSON validates against a composite schema (generated ad‑hoc) and contains all required keys. |
- [ ] T036 **Generate reproducible Markdown report** (`docs/report.md`) – programmatically inserts tables/figures from the final JSON and PNG assets.  <br>  *Verification*: Rendering the markdown shows all tables and images; a CI step checks that the file is non‑empty. |
- [ ] T037 **Run full end‑to‑end pipeline** – execute `python -m code.main --year 2022 --mode full`.  <br>  *Verification*: After run, `data/results/final_report.json` and `docs/report.md` exist; CI logs record total runtime ≤ 6 h and peak RAM ≤ 6.5 GB. |
- [ ] T038 **System‑wide pytest suite** – `pytest -q` must pass all unit and integration tests (≈ 30 tests).  <br>  *Verification*: CI step succeeds with 0 failures. |
- [ ] T039 **Update `quickstart.md`** – add instructions for the full run and for reproducing the report.  <br>  *Verification*: The markdown includes a code block `python -m code.main --year 2022 --mode full` and a note about required runtime/memory. |
- [ ] T040 **Archive data hashes** – compute SHA‑256 for every artifact in `data/raw/`, `data/processed/`, and `data/results/`; write to `data/README.md` under a `## Checksums` section.  <br>  *Verification*: Each listed checksum matches the actual file (checked by a CI script). |
- [ ] T041 **Project handoff to paper stage** – create `docs/paper_handoff.md` summarising methods, key findings, and pointing to `final_report.json` and figure assets.  <br>  *Verification*: File exists; contains required sections (Methods, Results, Limitations, Disclaimer). |

---  

### Dependencies & Execution Order  

1. **Foundational tasks** (T001–T009) must complete before any user‑story work.  
2. **US1** tasks (T012–T019) can run in parallel where marked `[P]`.  
3. **US2** tasks depend on the outputs of US1, specifically `cleaned_delays.csv` and `summary.json`.  
4. **US3** tasks depend on `x_min_estimate.json`, `tail_model_fits.json`, and the Hill estimator output.  
5. Final reporting tasks (T035–T041) require completion markers from Phases 2 and 3.  

---  

### Note on Verification  

All tasks produce **real files** (CSV, JSON, PNG, MD) that are validated either by schema checks, unit‑test assertions, or explicit CI‑stage scripts. No task relies on synthetic or placeholder data; the pipeline aborts with a clear error message if any prerequisite (e.g., full‑year BTS download) is unavailable. This satisfies the specification’s requirement for genuine, reproducible research artifacts.
