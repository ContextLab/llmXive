# Tasks: Evaluating the Impact of Data Scaling on Robustness of Statistical Tests  

**Inputs**: `specs/001-evaluating-data-scaling-robustness/spec.md`, `plan.md`, `data-model.md`, `contract` schemas in `specs/001-evaluating-data-scaling-robustness/contracts/`.  

The list below follows the canonical checklist format required by the platform.  
All tasks are ordered to respect data flow; each task’s verification step can be
checked deterministically by the verifier (real files, schema‑conformant
contents, or successful command‑line execution).

---

## Phase 1 – Project scaffolding & core simulation engine  

- [ ] **T001** [P] **Create project scaffolding, linting, and dependency lock**   <!-- FAILED-IN-EXECUTION: code/verify_scaffolding.py exit=1 -->
  - **Files created / updated**: `README.md`, `code/__init__.py`, `code/requirements.txt` (pinned versions), `pyproject.toml` (Black config), `ruff.toml` (ruff lint config), `.pre-commit-config.yaml` (pre‑commit hooks), `code/tests/__init__.py`.  
  - **Verification**:  
    1. All listed files exist.  
    2. `pip install -r code/requirements.txt` succeeds in a fresh venv.  
    3. `ruff check .` returns exit code 0.  
    4. `black --check .` returns exit code 0.  

- [ ] **T002** [P] **Implement synthetic data generator and unit tests (FR‑001)**  
  - **File**: `code/simulation/generator.py` (functions `generate_null`, `generate_alternative`).  
  - **Tests**: `code/tests/unit/test_generator.py` checking:  
    * Null dataset mean difference `< 0.01`.  
    * Alternative dataset mean difference within `±0.05` of the requested effect size.  
    * Skewed data achieves target skewness `±0.1`.  
  - **Verification**: `pytest code/tests/unit/test_generator.py` passes; generated CSVs (if any) conform to `SimulationConfig` schema.  

- [ ] **T003** **Implement scaling algorithms, chi‑squared binning, logging, and unit tests (FR‑002, FR‑003)**  
  - **File**: `code/preprocessing/scaling.py` exposing `standardize`, `min_max_scale`, `robust_scale`.  
  - **File**: `code/analysis/tests.py` exposing `run_t_test`, `run_anova`, `run_chi_squared` (includes binning logic).  
  - **Logging & Preservation**: Each scaling function writes a structured entry to `logs/scaling_<method>.log` (method name, parameters, timestamp) and saves a copy of the **pre‑scaled** dataframe to `data/pre_scaled/<method>/original_<uuid>.csv` before transformation.  
  - **Tests**: `code/tests/unit/test_scaling.py` and `code/tests/unit/test_stat_tests.py` verifying:  
    * Standardization yields mean ≈ 0, std ≈ 1 (tolerance 1e‑5).  
    * Min‑max yields min 0, max 1.  
    * Robust scaling handles zero IQR without NaNs.  
    * Chi‑squared runs without error and returns expected columns.  
  - **Verification**: All pytest modules pass; functions raise on invalid input (no silent fallback).  

---

## Phase 2 – Simulation orchestration & aggregation  

- [ ] **T004** **Build simulation driver, config loader, checkpointing, and produce `results/simulation_results.csv` (FR‑004, FR‑007)**  
  - **Files**:  
    * `code/simulation/config.py` – loads a YAML/JSON matrix of `SimulationConfig` objects and validates against `simulation_config.schema.yaml`.  
    * `code/main.py` – CLI entry point `python -m code.main`. Supports `--smoke` (200 iterations per config) and `--iterations=10000` (full run). Implements checkpoint file `data/checkpoints/sim_checkpoint.json` that records last completed iteration and resumes on restart.  
    * `code/analysis/metrics.py` – helper `write_simulation_results` that streams rows to `results/simulation_results.csv`.  
  - **Verification**:  
    1. `python -m code.main --smoke` finishes within 5 min and creates `results/simulation_results.csv` with at least one row per configuration.  
    2. `python -m code.main --iterations=10000` completes all 10,000 iterations per configuration, and the CSV row count equals `num_configs × 10000`.  
    3. Runtime of the full run is asserted to be ≤ the predefined budget (see T012).  
    4. Running the same command a second time resumes from the checkpoint (row count increases, no duplicate `iteration_id`).  

- [ ] **T005** **Aggregate error‑rate and power metrics into schema‑conformant CSVs (FR‑005, SC‑004)**  
  - **File**: `code/analysis/metrics.py` – functions `aggregate_error_rate` → `results/aggregate_error_rate.csv` and `aggregate_power` → `results/aggregate_power.csv`. Both obey `AggregateMetrics` schema (no extra columns).  
  - **Verification**:  
    1. Unit test `code/tests/unit/test_metrics.py` runs on a miniature `simulation_results.csv` and asserts exact values for `total_iterations`, `rejected_count`, CI bounds (using `statsmodels.stats.proportion.proportion_confint(method='beta')`).  
    2. Additionally asserts that for normal‑distribution configs the empirical error rate deviates from the nominal 0.05 by ≤ 0.005.  
    3. CSV files validate against the JSON‑schema using `jsonschema.validate`.  

- [ ] **T006** **Run alpha‑sensitivity analysis and generate comparative plot (FR‑006)**  
  - **File**: `code/analysis/metrics.py` – `run_sensitivity_analysis` writes `results/sensitivity_analysis.csv` with columns `alpha,scaling_method,test_type,error_rate,power`.  
  - **File**: `code/visualization/plots.py` – `plot_error_rates` reads `aggregate_error_rate.csv` and `sensitivity_analysis.csv`, produces `results/figures/error_rate_vs_alpha.png` (and a separate `power_vs_alpha.png`).  
  - **Verification**:  
    1. CSV contains three distinct alpha rows (0.01, 0.05, 0.10) per scaling method.  
    2. PNG files exist, have non‑zero file size, and the script exits with code 0.  

- [ ] **T012** **Benchmark total simulation runtime against fixed budget (SC‑003)**  
  - **File**: `code/analysis/benchmark.py` – runs the full simulation (`--iterations=10000`) and records wall‑clock time in `results/runtime_benchmark.json`.  
  - **Verification**: Unit test asserts that recorded runtime ≤ the budget (e.g., 6 hours on 2 CPU cores). Failure causes task to fail, enforcing FR‑007.  

- [ ] **T013** **Compute error‑rate inflation and power reduction metrics for non‑normal/heteroscedastic configs (SC‑005)**  
  - **File**: `code/analysis/inflation.py` – compares aggregate error rates (and power) of non‑normal & heteroscedastic configurations against the baseline normal configuration, outputs `results/inflation_metrics.csv` with columns `scaling_method,config_type,error_rate_inflation,power_reduction`.  
  - **Verification**: Unit test validates that inflation values are correctly calculated and that they exceed a minimal detectable threshold, satisfying SC‑005.  

- [ ] **T015** **Validate `TestResult` records against the (to‑be‑updated) schema, including chi‑squared**  
  - **File**: `code/tests/integration/test_result_schema.py` – loads `results/simulation_results.csv` (and real‑world CSVs) and runs `jsonschema.validate` against the `TestResult` schema (which must be extended with a `chi_squared` enum value).  
  - **Verification**: Test passes only if all rows conform; failures surface missing enum.  

- [ ] **T021** **Extend TestResult schema to include chi_squared test type (FR‑003)**  
  - **File**: `specs/001-evaluating-the-impact-of-data-scaling-on/contracts/test_result.schema.yaml` – add `"chi_squared"` to the `enum` of `test_type`.  
  - **Verification**: Load the schema with `jsonschema` and assert that `"chi_squared"` is an allowed value; unit test `code/tests/unit/test_schema_update.py` passes.  

---

## Phase 3 – Real‑world data ingestion & validation  

- [ ] **T007** **Implement streaming ingestion pipeline, fail‑loudly, and build dataset catalog (FR‑008)**  
  - **File**: `code/preprocessing/ingestion.py` – function `stream_dataset(url, dest_path, checksum)` that uses `datasets.load_dataset(..., streaming=True)` or `urllib.request` streaming download, computes SHA‑256 on‑the‑fly, raises `RuntimeError` if checksum mismatches or download fails.  
  - **File**: `data/config/datasets.yaml` – lists at least 10 verified UCI/OpenML datasets with `source_url`, `dataset_id`, and expected `checksum`.  
  - **File**: `results/real_world_ingestion_log.csv` – logs each successful ingestion (`dataset_id, status, timestamp, checksum_verified`).  
  - **File**: `results/real_world_dataset_catalog.csv` – conforms to `RealWorldDataset` schema (one row per dataset).  
  - **Verification**:  
    1. Running `python -m code.preprocess.ingest_all` processes all entries, creates files under `data/raw/`, and writes the log and catalog.  
    2. If any download fails, the script aborts with a non‑zero exit code (no silent fallback).  
    3. The catalog validates against its JSON‑schema.  

- [ ] **T008** **Apply scaling & statistical tests to each real dataset, produce `results/real_world_results.csv` (FR‑009)**  
  - **File**: `code/main_realworld.py` – loads the catalog, streams each dataset, applies the three scaling methods via `scaling.py`, runs t‑test, ANOVA, and chi‑squared (where applicable), writes a flattened CSV with the same schema as `TestResult` (plus `dataset_id`).  
  - **Verification**:  
    1. After execution, `results/real_world_results.csv` exists and contains ≥ 1 row per `(dataset_id, scaling_method, test_type)` combination.  
    2. The CSV validates against an extended `TestResult` schema that includes `dataset_id`.  

---

## Phase 4 – Mixed‑effects modeling & consistency checks  

- [ ] **T009** **Fit mixed‑effects model on real‑world results and generate report (FR‑010)**  
  - **File**: `code/analysis/mixed_effects.py` – uses `statsmodels.MixedLM` to fit `deviation ~ scaling_method + (1|dataset_id)` on `results/real_world_results.csv`.  
  - **Outputs**:  
    * `results/mixed_effect_model.json` (conforms to `MixedEffectModelOutput` schema).  
    * `results/mixed_effects_significance_report.md` – table of scaling methods, p‑values, and a bold “SIGNIFICANT” flag when `p < 0.05`. If none are significant, the report notes **SC‑007 FAILED**.  
  - **Verification**: Unit test `code/tests/unit/test_mixed_effects.py` checks JSON fields exist and that the report contains the required table and flag.  

- [ ] **T010** **Compute synthetic‑vs‑real consistency metric (SC‑006)**  
  - **File**: `code/analysis/consistency.py` – aligns synthetic aggregate error rates with real‑world deviations per scaling method, computes mean absolute deviation (MAD) of p‑values, writes `results/consistency_metric.json` with fields `scaling_method, mad_p_value, passes_threshold` (threshold 0.02).  
  - **Verification**: Test `code/tests/unit/test_consistency.py` asserts JSON matches schema and that the `passes_threshold` flag is correct for a known small synthetic sample.  

---

## Phase 5 – Documentation, reproducibility hand‑off & final verification  

- [ ] **T011** **Write reproducible quick‑start guide and full summary report (Phase 3 hand‑off)**  
  - **Files**:  
    * `quickstart.md` – step‑by‑step commands:  
      1. `python -m code.main --smoke` (verify early end‑to‑end).  
      2. `python -m code.main --iterations=10000` (full simulation).  
      3. `python -m code.main_realworld` (real‑world pipeline).  
      4. `python -m code.analysis.run_all` (aggregations, plots, mixed‑effects, consistency).  
    * `results/summary_report.md` – sections: Methods (generator, scaling, tests), Results (tables from `aggregate_error_rate.csv`, `aggregate_power.csv`, `real_world_results.csv`, mixed‑effects p‑values, consistency metric), Limitations (sampling of real datasets, checkpoint‑induced partial runs, numerical‑precision framing).  
  - **Verification**:  
    1. CI script `run_all.sh` executes the four commands above on a fresh runner and then runs `git diff --quiet` against the committed `results/` artifacts; exit 0 indicates reproducibility.  
    2. The markdown files contain required headings (`## Methods`, `## Results`, `## Limitations`).  

- [ ] **T016** **Create CI helper script `run_all.sh`**  
  - **File**: `run_all.sh` – bash script that sequentially runs the four commands listed in T011 with `set -e` and logs timestamps to `logs/run_all.log`.  
  - **Verification**: Script executes without error and produces the expected log file.  

- [ ] **T017** **Create Python entry point `code/analysis/run_all.py`**  
  - **File**: `code/analysis/run_all.py` – imports and invokes functions for aggregation, plotting, mixed‑effects modeling, and consistency metric. Provides a CLI `python -m code.analysis.run_all`.  
  - **Verification**: Running the module completes all downstream steps and exits with code 0.  

- [ ] **T018** **Refactor simulation driver CLI into focused module**  
  - **File**: `code/main.py` – now only parses arguments and delegates to `code/simulation/driver.py`.  
  - **Verification**: CLI still works as before; unit test ensures delegation.  

- [ ] **T019** **Implement dedicated config loader module**  
  - **File**: `code/simulation/config_loader.py` – loads and validates the simulation matrix, separate from `config.py`.  
  - **Verification**: Loader unit test checks proper schema validation and error handling.  

- [ ] **T020** **Implement checkpoint manager module**  
  - **File**: `code/simulation/checkpoint.py` – encapsulates read/write of `data/checkpoints/sim_checkpoint.json`, provides atomic updates.  
  - **Verification**: Integration test confirms that a resumed run continues from the saved iteration without duplication.  

- [ ] **T014** **Persist pre‑scaled copies and emit scaling logs**  
  - **File**: `code/preprocessing/scaling.py` (updated) now writes each original dataframe to `data/pre_scaled/<method>/original_<uuid>.csv` before scaling and appends a structured log entry to `logs/scaling_<method>.log`.  
  - **Verification**: After scaling, both the log file and the pre‑scaled copy exist; log format is validated by a simple parser test.  

