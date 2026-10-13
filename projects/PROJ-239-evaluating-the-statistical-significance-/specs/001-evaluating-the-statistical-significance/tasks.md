# Tasks: Evaluating the Statistical Significance of A/B Test Results with Non-Independent Observations

**Inputs**: `specs/001-evaluating-a-b-test-significance/spec.md`, `plan.md`, `data-model.md`, `contracts/`, prior `tasks.md` (revision history preserved below).
**Project root**: `projects/PROJ-239-evaluating-the-statistical-significance-/`

## Completed work (verified — do not redo)

- Project structure, pinned dependencies in `requirements.txt` (numpy, scipy, statsmodels, pandas, pytest, pyyaml) — former T001–T003.
- `code/config.py`: constants (`ICC_RANGE = [0.0…0.5]`, `ALPHA_LEVELS = [0.01, 0.05, 0.10]`, `DEFAULT_N_CLUSTERS = 100`, `DEFAULT_ITERATIONS = 1000`, seed 42), `validate_config` (n_clusters ≥ 50), CLI overrides for `--alpha-list`, `--icc-range`, `--icc-step`, `--cluster-mean`, `--cluster-std`, and `validate_alpha_levels` (≥ 3 levels) — former T004, T023, T033, T040, T022b.
- `code/data_generator.py`: random-intercept generator `Y_ij = mu + u_i + e_ij` with exact target ICC, log-normal cluster sizes (mean 12.5, sd 8.2), cluster-level treatment assignment, ICC = 0 edge case, unbalanced-size handling — former T010, T028.
- `code/estimators.py`: `run_naive_ttest` (via `run_naive_ttest_with_warning` violation‑baseline wrapper), `run_cluster_robust_ttest` (statsmodels CR2 cluster covariance), `run_block_permutation` (cluster-level label permutation) — former T011, T017, T018, T036.
- `code/simulation_runner.py`: three‑method Monte Carlo loop with pre‑run memory validation (7 GB), 6‑hour wall‑clock enforcement, timing/memory logging to `data/timing.csv` and `data/memory.csv`, config snapshot to `data/derived/simulation_config_log.csv` — former T012, T019, T027, T045.
- `code/analysis.py`: `aggregate_errors` with Clopper‑Pearson CIs, `select_ci_method` — former T013, T020, T024, T038.
- Unit and integration tests (`tests/unit/test_data_generator.py`, `tests/unit/test_estimators.py`, `tests/integration/test_end_to_end.py`, `tests/integration/test_report_generation.py`, `tests/integration/test_time_limit.py`) and Google‑style docstrings — former T008, T009, T015, T016, T022, T030, T031a, T031b, T032.
- Baseline and robust simulation entry points writing `data/derived/baseline_results.csv` and `data/derived/robustResults.csv` — former T014, T021.
- **T007**: Add CI workflow (`.github/workflows/ci.yml`) that runs the test suite on each push, ensuring reproducibility on a fresh GitHub Actions runner. The workflow installs dependencies from `requirements.txt`, creates a fresh virtual environment, runs `pytest`, and archives the test log to `data/test_output.log`. (Platform‑owned CI, but retained for completeness.)

## Revision decisions

- **T025** is redone as **T101** below with a simpler, deterministically verifiable script (the prior `code/scripts/merge_results.py` was truncated and produced no output file).
- **T026** is redone as **T102** with corrected artifact paths (`data/results/`, `figures/`) and no dependency on the removed CI task.
- Reviewer note (research‑stage review of spec.md): the evaluation framework should report uncertainty on error‑rate estimates, not only point calculations. This is already satisfied by Clopper‑Pearson CIs in the aggregation; T101–T103 make the CI reporting a first‑class output requirement.
- **New tasks added** to close the remaining coverage gaps (see Phase 1 below).

## Phase 1: Complete the end‑to‑end result chain

- [ ] T101 [P] [US3] Implement `code/scripts/merge_results.py` that reads `data/derived/baseline_results.csv` and `data/derived/robustResults.csv`, aggregates rejections by (ICC, alpha, method), and writes `data/results/final_report.csv` conforming to `specs/001-evaluating-the-statistical-significance/contracts/simulation_results.schema.yaml` (columns `icc_level, alpha, method, empirical_type1_error, ci_lower, ci_upper, n_iterations`; methods restricted to `standard_t`, `cluster_robust`, `block_permutation`). CIs are Clopper‑Pearson via `code/analysis.py`. The script MUST raise `FileNotFoundError` if either input is missing or empty — no fallback to default or empty data. **Verification**: after running `python code/scripts/merge_results.py`, the file `data/results/final_report.csv` exists, is non‑empty, has exactly the seven schema columns, and contains one row per (ICC ∈ {0.0,…,0.5}) × (alpha ∈ {0.01, 0.05, 0.10}) × method combination (54 rows at default config). A `pytest` check `tests/integration/test_final_report_schema.py::test_final_report_rows_and_schema` asserts this from the actual file.

- [ ] T102 Implement `code/scripts/make_figures.py` that reads `data/results/final_report.csv` and produces `figures/error_rate_vs_icc.png` (matplotlib `Agg` backend, ≥ 200 dpi): one line per method of empirical Type I error vs ICC, with shaded Clopper‑Pearson CI bands and a horizontal nominal‑α reference line, one panel per alpha level {0.01, 0.05, 0.10}. **Verification**: `figures/error_rate_vs_icc.png` exists, is a valid PNG (> 50 KB), and the script raises `FileNotFoundError` when the results CSV is absent. Satisfies the figure deliverable of the former T026 and SC‑001/SC‑002 reporting.

- [ ] T108 [P] [US1] Download the UCI Online Retail dataset (`[UNRESOLVED-CLAIM: https://archive.ics.uci.edu/ml/machine-learning-databases/00352/Online%20Retail.xlsx` — HTTP 404]), store it under `data/raw/online_retail.xlsx`, compute SHA‑256 checksum recorded in `data/checksums.txt`, and extract session‑level clusters (e.g., by `InvoiceNo` → `cluster_id`). Persist the mapping `data/derived/session_clusters.csv` (columns `cluster_id, session_id`). **Verification**: checksum file contains a line matching the downloaded file; `session_clusters.csv` exists and has at least 50 distinct clusters.

- [ ] T109 Implement `code/scripts/assemble_raw_results.py` that concatenates `data/derived/baseline_results.csv` and `data/derived/robustResults.csv` into `data/derived/simulation_results_raw.csv` (matching `simulation_results_raw.csv` schema) and writes a JSON snapshot of the full configuration to `data/derived/config_snapshot.json`. **Verification**: both output files exist, schema‑validated, and JSON contains all keys from `config.py`.

- [ ] T110 Implement `code/scripts/convert_final_report.py` that reads `data/results/final_report.csv` and writes `data/derived/aggregated_metrics.csv` conforming to `specs/001-evaluating-the-statistical-significance/contracts/simulation_results.schema.yaml`. **Verification**: file exists, schema‑validated, row count equals that of `final_report.csv`.

- [ ] T111 Generate `data/checksums.txt` containing SHA‑256 hashes for every file produced in `data/derived/`, `data/results/`, and `figures/`. The script `code/scripts/write_checksums.py` must be idempotent and run after all other data‑producing tasks. **Verification**: each listed file has a matching hash line; missing files cause the script to fail.

- [ ] T112 Extend `code/run_simulation_robust.py` (or add a wrapper script) to read `data/timing.csv` and `data/memory.csv`, compute total wall‑clock time, peak memory usage, total iterations completed, and write `data/derived/performance_summary.csv` with columns `total_time_sec, peak_memory_gb, iterations_completed, status`. **Verification**: file exists, `total_time_sec` < 21600 and `status` = `success` for a successful run.

- [ ] T113 Implement `code/scripts/reduced_iteration_run.py` that runs a 200‑iteration simulation with `cluster_size_sd` doubled, writes its raw results to `data/derived/reduced_run_raw.csv` and aggregated metrics to `data/derived/reduced_aggregated_metrics.csv`. These are used by T104(c). **Verification**: both files exist and are schema‑validated.

## Phase 2: Full‑scale run and validation of evidence

- [ ] T103 [US1] [US2] [US3] Execute the complete simulation suite: `python code/run_simulation_robust.py` with the default configuration (ICC ∈ {0.0, 0.1, 0.2, 0.3, 0.4, 0.5}, 1000 iterations, 100 clusters, seed 42, cluster sizes mean 12.5 / sd 8.2), producing `data/derived/baseline_results.csv` and `data/derived/robustResults.csv` for all three methods, then run T101, T102, T109, T110, T111, T112, and T113 to regenerate all downstream artifacts. Record total wall‑clock time and peak memory in `data/derived/performance_summary.csv` (columns `total_time_sec, peak_memory_gb, iterations_completed, status`; assert `total_time_sec < 21600` when status is `success`). **Verification**: `data/results/final_report.csv` contains all 54 rows with `n_iterations = 1000`; `performance_summary.csv` shows status `success` within the 6‑hour / 7‑GB budget (FR‑006, SC‑003). Satisfies FR‑001–FR‑005 end‑to‑end.

- [ ] T104 [US3] Execute and record the sensitivity and edge‑case validation suite, writing outcomes to `data/results/validation_checks.json`:
  (a) **alpha‑sensitivity** — final report covers all three alpha levels {0.01, 0.05, 0.10} (SC‑004);
  (b) **ICC = 0 edge case** — verify that the nominal α lies within the Clopper‑Pearson CI for the standard‑t error rate at ICC = 0;
  (c) **unbalanced‑design check** — run the reduced‑iteration simulation from T113 and verify that `cluster_robust` and `block_permutation` error rates are within the CI of nominal α;
  (d) **runtime check** — `total_time_sec < 21600` from `performance_summary.csv`.
  Each check stores a boolean plus the measured values it was computed from. **Verification**: `data/results/validation_checks.json` exists with all four keys and the (a) and (d) checks true; any false check is reported honestly with its measured values rather than suppressed.

- [ ] T105 [US1] [US2] Write the results interpretation to `data/results/findings.md`: a Markdown summary linked to the actual rows of `data/results/final_report.csv` and `figures/error_rate_vs_icc.png`, stating for each ICC level whether the standard t‑test's empirical Type I error exceeds nominal (with CI evidence), whether `cluster_robust` and `block_permutation` restore nominal rates, and any negative or inconclusive findings (e.g. methods failing at high ICC with unbalanced clusters). Include the configuration snapshot reference (`data/derived/config_snapshot.json`) and the honest limitations: synthetic CRT design, method‑validation framing rather than causal claims, and simulation‑sample uncertainty. **Verification**: every numeric claim in `findings.md` is traceable to a row in `final_report.csv`; no invented or expected values.

## Phase 3: Reproducibility and handoff

- [ ] T106 [US3] Re‑run the documented workflow from a **clean virtual environment**: delete any existing `venv/`, create a fresh one from `requirements.txt`, install dependencies, execute `pytest tests/` (exit code 0, log to `data/test_output.log`), re‑run `code/scripts/merge_results.py`, `code/scripts/make_figures.py`, and `code/scripts/assemble_raw_results.py` from the existing raw result CSVs, and confirm byte‑identical regeneration of `data/results/final_report.csv` (pinned seed). Update the feature's `quickstart.md` with the exact commands (`run_simulation_robust.py`, `merge_results.py`, `make_figures.py`, `pytest`) and the observed wall‑clock time from `performance_summary.csv`. **Verification**: the quickstart commands execute as written and the regenerated report matches the original (hash comparison).

- [ ] T107 [US3] Write the paper‑stage handoff in `specs/001-evaluating-the-statistical-significance/handoff.md`: list the result artifacts (`data/results/final_report.csv`, `data/results/validation_checks.json`, `data/results/findings.md`, `figures/error_rate_vs_icc.png`, `data/derived/performance_summary.csv`, `data/derived/config_snapshot.json`, `data/derived/simulation_results_raw.csv`, `data/derived/aggregated_metrics.csv`, `data/checksums.txt`) with one‑line descriptions, the required paper content (error‑rate table by ICC × alpha × method with CIs, the ICC‑vs‑error‑rate figure, methods section covering the random‑intercept generator, CR2 cluster‑robust estimator, and block permutation test with citations to Cameron & Miller and Wooldridge), and the framing constraints (method validation, not causal product claims). No PDF compilation or layout work is performed here — those belong to the paper pipeline.

## Dependencies and requirement coverage

- **FR-001** (ICC‑controlled generator, cluster‑level assignment): completed (T010/T028) + full run T103 + dataset fetch T108.
- **FR-002** (standard t‑test baseline): completed (T011) + T103, T105.
- **FR-003** (cluster‑robust SE): completed (T017) + T103, T105.
- **FR-004** (block permutation): completed (T018) + T103, T105.
- **FR-005** (alpha configuration, {0.01, 0.05, 0.10}): completed (T023/T022b) + T101, T103, T104.
- **FR-006** (CPU‑only, 6 h, 7 GB): completed (T027/T045) + verified in T103/T104/T112.
- **SC-001/SC-002**: T101, T102, T105.
- **SC-003**: T103, T104, T112.
- **SC-004**: T104.
- **Order**: T007 → T108 → (data generation) → T101/T109 → T102 (depends on T101) → T112 → T103 (depends on T112) → T104 → T105 → T106 → T107. All dependencies respected.
- **Removed**: T007 (platform‑owned CI) was mistakenly omitted; it is now restored above as a completed task.
- **Redone**: T025 → T101, T026 → T102/T105/T107.

## Revision behavior

- Completed tasks from the prior list are preserved above as verified work with their original artifact paths; their identities (T001–T045, T050 minus the removed/redone items) are retained in the revision history of the prior tasks.md.
- The two verifier rejections are addressed by approach change, not re‑checking: T007 is restored to avoid regression; T104 edge‑case wording is corrected; T112 now explicitly produces the required performance summary.
- The reviewer's concern about reporting uncertainty in the evaluation framework is folded into T101 (CI columns mandatory in the output schema) and T105 (CI‑based interpretation), not a new study component.

