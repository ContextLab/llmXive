# Tasks: Evaluating the Statistical Significance of A/B Test Results with Non‑Independent Observations  

**Inputs**: `specs/001-evaluating-a-b-test-significance/spec.md`, `plan.md`, `data-model.md`, contract schemas, existing code and tests.  
**Project root**: `projects/PROJ-239-evaluating-the-statistical-significance-/`

---  

## Phase 0 – Foundational scaffolding (already completed)

- [ ] T001 [P] [US1] Create project skeleton, add `requirements.txt` (numpy, scipy, pandas, statsmodels, pytest, pyyaml) and document the runnable command in `quickstart.md`.  
  *Verification*: `pip install -r requirements.txt` succeeds; `quickstart.md` contains a command that runs the simulation end‑to‑end without error.

- [X] T002 [P] [US1] Implement `code/config.py` with the full simulation schema, default values (`ICC_RANGE = [0.0,0.1,0.2,0.3,0.4,0.5]`, `ALPHA_LEVELS = [0.01,0.05,0.10]`, `N_CLUSTERS = 100`, `N_ITERATIONS = 1000`, `SEED = 42`) and validation helpers (`validate_config`, `validate_alpha_levels`).  
  *Verification*: `python -c "import code.config as cfg; cfg.validate_config()"` exits with status 0.

- [ ] T003 [P] [US1] Create `code/data_generator.py` that draws cluster sizes (log‑normal), generates a random‑intercept outcome `Y_ij = μ + u_i + ε_ij` with a target ICC, and assigns treatment at the cluster level. Handles ICC = 0 and unbalanced clusters.  
  *Verification*: Unit test `tests/unit/test_data_generator.py` checks that the empirical ICC of generated data matches the requested value within ±0.02.

- [ ] T004 [P] [US2] Add `code/estimators.py` containing:  
  * `run_naive_ttest` (standard two‑sample t‑test via `scipy.stats.ttest_ind`)  
  * `run_cluster_robust_ttest` (CR2 estimator from `statsmodels.stats.api`)  
  * `run_block_permutation` (cluster‑level label permutation with 1 000 permutations).  
  *Verification*: `tests/unit/test_estimators.py` asserts correct p‑value ranges on a tiny handcrafted dataset.

- [ ] T005 [ ] [US1 US2] Implement `code/simulation_runner.py` that loops over the configuration grid, calls the three estimators, writes individual run results to `data/derived/simulation_results_raw.csv` (conforms to `simulation_run.schema.yaml`), and additionally records per‑iteration wall‑clock time to `data/timing.csv` and peak memory usage to `data/memory.csv`. The task respects the 6‑hour wall‑clock & 7 GB RAM limits (pre‑run memory check).   <!-- FAILED-IN-EXECUTION: code/simulation_runner.py exit=1 -->
  *Verification*: Integration test `tests/integration/test_end_to_end.py` runs a reduced configuration (2 ICC × 1 α × 10 iterations) and finishes in < 60 s; the generated `timing.csv` and `memory.csv` contain matching rows.

- [ ] T006 [P] [US3] Create `code/analysis.py` that aggregates raw runs into `data/derived/aggregated_metrics.csv` (conforms to `simulation_results.schema.yaml`) using Clopper‑Pearson 95 % CIs and provides a helper `write_config_snapshot()` that stores the exact JSON config used.  
  *Verification*: `tests/integration/test_report_generation.py` checks that the aggregated file contains the expected columns and CI bounds.

---  

## Phase 1 – Missing / incomplete deliverables (to be (re)implemented)

- [ ] T007 [US3] Add a GitHub Actions CI workflow (`.github/workflows/ci.yml`) that:  
  1. Checks out the repository, sets up Python 3.11, installs `-r requirements.txt`.  
  2. Runs `pytest -q`.  
  3. Archives the test log to `data/test_output.log`.  
  *Verification*: The workflow appears in the repository, and a successful run on GitHub Actions produces a green check badge. Locally, `act -j test` completes with exit code 0.

- [ ] T008 [US1] Download the UCI Online Retail dataset (`[UNRESOLVED-CLAIM: https://archive.ics.uci.edu/ml/machine-learning-databases/00352/Online%20Retail.xlsx` — HTTP 404]), store it as `data/raw/online_retail.xlsx`, compute its SHA‑256 checksum recorded in `data/checksums.txt`, and extract session‑level clusters (by `InvoiceNo`). Persist the mapping as `data/derived/session_clusters.csv` (`cluster_id, session_id`).  
  *Verification*: `data/checksums.txt` contains a line matching the file’s SHA‑256; `session_clusters.csv` has ≥ 50 distinct `cluster_id`s.

- [ ] T009 [US1 US2] Execute the full simulation suite (baseline + robust) with the default configuration (`ICC_RANGE`, `ALPHA_LEVELS`, `N_CLUSTERS = 100`, `N_ITERATIONS = 1000`). The runner writes:  
  * `data/derived/baseline_results.csv` (standard t‑test)  
  * `data/derived/robust_results_cluster_robust.csv` (cluster‑robust)  
  * `data/derived/robust_results_block_permutation.csv` (block permutation)  
  *Verification*: Each CSV conforms to `simulation_run.schema.yaml`; total wall‑clock time recorded in `data/derived/performance_summary.csv` is < 21600 s and `status = "success"`.

- [ ] T010 [US1 US2 US3] Merge the three result files and compute empirical Type I error rates with 95 % Clopper‑Pearson CIs, writing the consolidated table to `data/results/final_report.csv`. Columns must exactly match `simulation_results.schema.yaml` (`icc_level,alpha,method,empirical_type1_error,ci_lower,ci_upper,n_iterations`).  
  *Verification*: `pytest tests/integration/test_final_report_schema.py::test_final_report_rows_and_schema` passes; file contains 54 rows (6 ICC × 3 α × 3 methods).

- [ ] T011 [US3] Generate a publication‑ready figure `figures/error_rate_vs_icc.png` (≥ 200 dpi, Agg backend) that plots empirical Type I error vs. ICC for each method, includes shaded CI bands, and a horizontal line at the nominal α for each panel (one panel per α).  
  *Verification*: The PNG exists, size > 50 KB, and a visual inspection script (`tests/integration/test_figure_exists.py`) confirms the file can be opened.

- [ ] T012 [US?] Assemble raw results and configuration snapshot: concatenate the three method‑specific CSVs into `data/derived/simulation_results_raw.csv` (matching `simulation_results_raw.schema.yaml`) and write the JSON config snapshot to `data/derived/config_snapshot.json`.  
  *Verification*: Both files exist; schema validation on the CSV succeeds; JSON contains all keys from `code/config.py`.

- [ ] T013 [US3] Convert `data/results/final_report.csv` into `data/derived/aggregated_metrics.csv` (identical schema) to provide a canonical artifact for downstream reporting.  
  *Verification*: File exists, schema‑validated, row count equals that of `final_report.csv`.

- [ ] T014 [US3] Create `code/scripts/write_checksums.py` that walks `data/derived/`, `data/results/`, and `figures/`, computes SHA‑256 hashes, and writes them to `data/checksums.txt`. The script must be idempotent and fail if any expected file is missing.  
  *Verification*: Running the script updates `data/checksums.txt` with a line for every artifact; a second run produces identical output (hashes unchanged).

- [ ] T015 [US3] Extend `code/run_simulation_robust.py` (or add a wrapper) to read `data/timing.csv` and `data/memory.csv`, compute total wall‑clock time, peak memory usage, total iterations completed, and write `data/derived/performance_summary.csv` (`total_time_sec,peak_memory_gb,iterations_completed,status`).  
  *Verification*: After a successful full run, `performance_summary.csv` shows `total_time_sec < 21600`, `peak_memory_gb ≤ 7`, and `status = "success"`.

- [ ] T016 [US3] Implement `code/scripts/reduced_iteration_run.py` that runs a 200‑iteration simulation with `cluster_size_sd` doubled, writing raw results to `data/derived/reduced_run_raw.csv` and aggregated metrics to `data/derived/reduced_aggregated_metrics.csv`. These files are used for the unbalanced‑design edge‑case checks.  
  *Verification*: Both outputs exist, schema‑validated, and the aggregated error rates are within the nominal CI for ICC = 0.3 (as asserted in the validation suite).

- [ ] T017 [US3] Execute the sensitivity and edge‑case validation suite, producing `data/results/validation_checks.json` containing four keys:  
  * `alpha_coverage` (true if all three α levels appear in `final_report.csv`)  
  * `icc_zero_ci` (true if the nominal α lies within the CI for the standard‑t error at ICC = 0)  
  * `unbalanced_design` (true if the reduced‑iteration run’s robust methods stay within CI)  
  * `runtime_ok` (true if `performance_summary.csv` reports `total_time_sec < 21600`).  
  Each key also records the measured values.  
  *Verification*: `tests/integration/test_validation_checks.py` asserts that all four keys exist and that any false flag is accompanied by its numeric evidence.

- [ ] T018 [US3] Write `data/results/findings.md` summarizing the empirical results: for every ICC level report whether the standard t‑test inflates Type I error, whether each robust method restores the nominal rate, and cite the corresponding rows in `final_report.csv`. Include limitations (synthetic CRT design, cluster‑size distribution, Monte‑Carlo error).  
  *Verification*: A script `tests/integration/test_findings_consistency.py` parses the markdown, extracts the numbers, and cross‑checks them against `final_report.csv`; it passes.

- [ ] T019 [US3] Demonstrate full reproducibility from a clean environment:  
  1. Delete any existing virtual environment (`rm -rf .venv`).  
  2. Create a fresh one, `pip install -r requirements.txt`.  
  3. Run `pytest` (must exit 0).  
  4. Re‑run `code/run_simulation_robust.py`, `code/scripts/merge_results.py`, `code/scripts/make_figures.py`, `code/scripts/write_checksums.py`.  
  5. Verify that `data/results/final_report.csv` is byte‑identical to the original (hash comparison).  
  Update `quickstart.md` with the exact sequence of commands and the observed wall‑clock time from `performance_summary.csv`.  
  *Verification*: The reproducibility script `tests/integration/test_reproducibility.py` performs the steps and asserts hash equality.

- [ ] T020 [US3] Create the paper‑stage handoff file `specs/001-evaluating-the-statistical-significance/handoff.md` that lists all primary artifacts (`final_report.csv`, `validation_checks.json`, `findings.md`, `error_rate_vs_icc.png`, `performance_summary.csv`, `config_snapshot.json`, `simulation_results_raw.csv`, `aggregated_metrics.csv`, `checksums.txt`) with one‑line descriptions, and outlines the methods section (random‑intercept generator, CR2 estimator, block permutation) citing Cameron & Miller and Wooldridge. No PDF generation is performed here.  
  *Verification*: The handoff file exists, contains the required list, and a lint test (`tests/unit/test_handoff_structure.py`) confirms the format.

- [ ] T021 [US3] Add a script `code/scripts/update_state_yaml.py` that computes SHA‑256 hashes of all project‑owned artifacts (`data/`, `figures/`, `code/` outputs) and writes them into `state/projects/PROJ-239-evaluating-the-statistical-significance-.yaml` under `artifact_hashes`, updating the `updated_at` timestamp. Run this script after the final report generation.  
  *Verification*: After execution, the state YAML contains entries for each artifact and the timestamp reflects the latest run; a unit test `tests/unit/test_state_yaml_update.py` validates schema compliance.

---  

### Dependency & Requirement Mapping  

| Spec Requirement | Satisfying Task(s) |
|------------------|--------------------|
| FR‑001 (ICC‑controlled generator) | T003, T008 |
| FR‑002 (standard t‑test) | T004, T009 |
| FR‑003 (cluster‑robust SE) | T004, T009 |
| FR‑004 (block permutation) | T004, T009 |
| FR‑005 (α‑list) | T002, T010 |
| FR‑006 (CPU‑only, ≤6 h, ≤7 GB) | T005, T015, T017 |
| SC‑001 / SC‑002 (error‑rate reporting) | T010, T011, T018 |
| SC‑003 (compute‑time limit) | T015, T017 |
| SC‑004 (≥3 α levels) | T017 |
| Principle V versioning | T021 |

All tasks respect the data‑flow order: generation → simulation (with timing/memory) → aggregation → merging → reporting → validation → reproducibility → handoff → state‑yaml update.

---  

*End of `tasks.md`.*  