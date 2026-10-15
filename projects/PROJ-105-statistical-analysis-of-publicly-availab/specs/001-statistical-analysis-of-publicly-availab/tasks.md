# Tasks: Statistical Analysis of Flight Delay Distributions  

**Inputs**: `spec.md`, `plan.md`, existing research artifacts, contracts, and data‑model definitions.  

The checklist follows the canonical format `- [ ] T### [P?] [USx?] description …` where:  

* **T###** – unique task identifier.  
* **[P]** – can run in parallel with other `[P]` tasks (different files, no ordering constraints).  
* **[USx]** – the user story (US1, US2, US3) that the task satisfies.  
* Indented continuation lines describe concrete outputs, verification steps, and required file paths.  

---  

## Phase 1 – Data Acquisition & Pre‑processing (US1)

- [ ] **T001** [US1] Download the full‑year 2022 BTS On‑Time Performance CSV via streaming and store the raw archive.  
  - **Implementation**: `code/data_loader.py` uses `requests` streaming download, writes to `data/raw/2022/On_Time_Reporting_CSV.zip`.  
  - **Verification**: SHA‑256 checksum recorded in `data/README.md` matches the official file; `ls data/raw/2022/On_Time_Reporting_CSV.zip` succeeds.

- [ ] **T002** [US1] Extract the ZIP, stream each CSV chunk, compute `total_delay = ArrDelay + DepDelay` (treat NaN as 0), drop negative delays, keep only commercial U.S. flights, and write a cleaned dataset.  
  - **Implementation**: `code/preprocess.py` reads chunks (`chunksize=200_000`), writes to `data/processed/cleaned_delays.csv`.  
  - **Verification**: The output CSV contains columns `flight_id,total_delay_minutes,carrier,origin,destination,is_anomaly,is_data_error,is_zero`; a schema validation against `delay_record.schema.yaml` passes.

- [ ] **T003** [US1] Compute retention rate, flag anomalies (`delay>1440` min) and data errors (`delay>10000` min), create zero‑inflation subset, and record summary metadata.   <!-- FAILED-IN-EXECUTION: code/t003_summary.py exit=1 -->
  - **Outputs**:  
    - `data/results/summary.json` → keys `retention_rate`, `total_records`, `valid_records`.  
    - `data/processed/cleaned_delays_no_zero.csv` (records with `total_delay_minutes==0` removed).  
    - `data/processed/analysis_set.csv` (excludes rows where `is_data_error=True`).  
  - **Verification**: `summary.json["retention_rate"] >= 0.95`; pipeline aborts with `PipelineError("Retention rate below 95 %")` otherwise.

- [ ] **T004** [US1] Perform a component‑wise comparison: generate side‑by‑side histograms for `total_delay`, `ArrDelay`, and `DepDelay`; compute a two‑sample KS test between `total_delay` and each component.  
  - **Implementation**: `code/component_analysis.py` saves `data/results/component_comparison.json` (KS statistics & p‑values) and figures `data/results/figures/total_vs_arr.png`, `data/results/figures/total_vs_dep.png`.  
  - **Verification**: JSON contains `ks_total_arr`, `pvalue_total_arr`, `ks_total_dep`, `pvalue_total_dep`; figures exist and are non‑empty.

## Phase 2 – Parametric Model Fitting & Goodness‑of‑Fit (US2)

- [ ] **T005** [US2] Estimate the tail threshold `x_min` using the Clauset‑et‑al. KS‑minimisation on the cleaned data.  
  - **Implementation**: `code/diagnostics.py` writes `data/results/x_min_estimate.json` with fields `x_min`, `ks_stat`, `confidence_interval`.  
  - **Verification**: JSON validates against a minimal schema (numeric `x_min` and `ks_stat`); unit test checks that varying the grid changes `x_min` deterministically.

- [ ] **T006** [US2] Fit the five candidate distributions (Exponential, Gamma, Log‑Normal, Weibull, Pareto) to the **full** cleaned dataset.  
  - **Implementation**: `code/models.py` performs MLE via `scipy.stats`, writes `data/results/full_model_fits.json` (list of five objects with `name`, `parameters`, `converged`).  
  - **Verification**: All five entries have `converged=True`; schema validation against `fitted_model.schema.yaml` (with `is_valid_tail=False` for now) passes.

- [ ] **T007** [US2] Fit the same five distributions to the **tail** subset (`total_delay_minutes >= x_min`).  
  - **Implementation**: Re‑use `code/models.py` with filtered data, write `data/results/tail_model_fits.json`.  
  - **Verification**: Pareto fit respects the `x_min` threshold; at least three models report `converged=True`.

- [ ] **T008** [US2] Compute model‑level metrics (AIC, BIC, KS, Anderson‑Darling, tail‑KS, tail‑KS p‑value) for each tail fit and assemble a comparison table.  
  - **Implementation**: `code/models.py` augments each fit with the metrics and writes `data/results/model_comparison.json`.  
  - **Verification**: JSON validates against `fitted_model.schema.yaml`; contains fields `aic`, `bic`, `ks_stat`, `ad_stat`, `tail_ks_stat`, `tail_ks_p_value`, `x_min`. At least three models have finite AIC/BIC.

- [ ] **T009** [US2] Identify the best heavy‑tailed candidate (lowest AIC among Pareto/Log‑Normal) and the best short‑tailed candidate (lowest AIC among Exponential/Gamma/Weibull). Perform Vuong’s non‑nested test to compare them.  
  - **Implementation**: `code/models.py` writes `data/results/vuong_test.json` with keys `heavy_model`, `short_model`, `vuong_statistic`, `p_value`.  
  - **Verification**: `p_value` is a float in `[0,1]`; unit test on a synthetic dataset yields a Vuong statistic > 0 when heavy‑tail is true.

## Phase 3 – Heavy‑Tail Diagnostics & Visualization (US3)

- [ ] **T010** [US3] Apply the Hill estimator to the tail subset, perform stability analysis (sliding window w=10, constraint `k/n ≤ 0.1`), and select the optimal `k`.  
  - **Implementation**: `code/diagnostics.py` writes `data/results/tail_index_estimate.json` conforming to `tail_index_estimate.schema.yaml`.  
  - **Verification**: JSON fields `threshold_k`, `estimated_alpha`, `confidence_interval`, `stability_range` are present; variance of α across the window is reported.

- [ ] **T011** [US3] Generate a log‑log survival plot for the tail data, fit an OLS line, compute R², and embed the value in the tail‑index JSON.  
  - **Implementation**: `code/visualization.py` creates `data/results/figures/log_log_survival.png` and updates `tail_index_estimate.json` with `r_squared_log_log`.  
  - **Verification**: Plot file exists; `tail_index_estimate.json["r_squared_log_log"] >= 0.95` for accepted models.

- [ ] **T012** [US3] Produce a QQ‑plot comparing empirical quantiles of the tail data against the theoretical quantiles of the **selected** heavy‑tailed model, and compute a quantile‑correlation metric to automate validation.  
  - **Implementation**: `code/visualization.py` saves `data/results/figures/qq_plot.png` and writes `data/results/qq_correlation.json` containing `pearson_r`.  
  - **Verification**: PNG file is non‑empty; `pearson_r >= 0.99` is asserted as the automated similarity check (replaces manual visual inspection).

- [ ] **T013** [US3] Conduct a KS goodness‑of‑fit test **only on the tail subset** against the selected heavy‑tailed model’s CDF; store results.  
  - **Implementation**: `code/diagnostics.py` writes `data/results/tail_ks.json` with `ks_statistic`, `p_value`, `x_min_used`.  
  - **Verification**: JSON validates against a minimal schema; `p_value` is a float.

- [ ] **T014** [US3] Implement model‑rejection logic: if `r_squared_log_log < 0.95` **or** Hill estimator variance exceeds the predefined stability threshold, mark the current best model as rejected, update `model_comparison.json` with `"status":"rejected"` and a `"reason"` field, and promote the next best candidate. Write the final accepted model to `data/results/final_model.json`.  
  - **Implementation**: `code/selection.py`.  
  - **Verification**: After execution, `final_model.json` exists and contains `name`, `parameters`, `metrics`; at least one model has `"status":"accepted"`.

## Phase 4 – Reporting, Verification & Handoff

- [ ] **T015** [P] Compile a single consolidated results file `data/results/final_report.json` that merges `summary.json`, `model_comparison.json`, `vuong_test.json`, `tail_index_estimate.json`, `component_comparison.json`, and `final_model.json`.  
  - **Verification**: JSON validates against a composite schema (all required keys present); CI script checks file size > 0.

- [ ] **T016** [P] Generate a reproducible Markdown report `docs/report.md` that programmatically inserts tables, key statistics, and the PNG figures (`log_log_survival.png`, `qq_plot.png`, component histograms).  
  - **Verification**: Rendering the markdown (e.g., via `markdown-it`) displays all tables and images; a CI lint step confirms no broken image links.

- [ ] **T017** [P] Add an integration test `tests/integration/test_full_pipeline.py` that runs the full pipeline (`python -m code.main --year 2022 --mode full`) and asserts the existence and schema compliance of all final artifacts (`final_report.json`, `report.md`, all PNGs).  
  - **Verification**: `pytest -q tests/integration/test_full_pipeline.py` passes on a fresh runner.

- [ ] **T018** [P] Update `quickstart.md` with commands for (a) a quick smoke run (first 10 k rows) and (b) the full reproducible analysis, including expected runtime and memory limits.  
  - **Verification**: Markdown contains the exact commands and the statements “expected runtime ≤ 6 h, peak RAM ≤ 6.5 GB”; a CI step parses the file to ensure those strings are present.

- [ ] **T019** [P] Record SHA‑256 checksums for every artifact under `data/raw/`, `data/processed/`, and `data/results/` in `data/README.md` under a `## Checksums` section.  
  - **Verification**: A helper script `code/checksums.py` generates the list; CI validates that each listed checksum matches the current file.

- [ ] **T020** [P] Create a handoff document `docs/paper_handoff.md` summarising methods, key findings, limitations, and pointing to `final_report.json` and figure assets for downstream paper preparation.  
  - **Verification**: File exists; contains sections “Methods”, “Results”, “Limitations”, “Disclaimer (Associational only)”, and a link to `final_report.json`.

### New Tasks to Close Remaining Gaps

- [ ] **T021** [FR-007] Insert the mandatory associational‑only disclaimer into `docs/report.md`.  
  - **Implementation**: `code/report_utils.py` appends the line “**Disclaimer:** All findings are associational only.” to the end of the markdown report.  
  - **Verification**: Grep for the phrase “associational only” in `docs/report.md`; fails if absent.

- [ ] **T022** [FR-016] Generate a JSON schema for the `TailIndexEstimate` entity from the existing YAML and save it to `specs/001-statistical-analysis-of-publicly-availab/contracts/tail_index_estimate.schema.json`.  
  - **Implementation**: `code/schema_generator.py` reads the YAML schema and writes the JSON counterpart.  
  - **Verification**: JSON file exists and validates against the original YAML (structural equivalence).

- [ ] **T023** [SC-002] Verify that at least three parametric models converge with finite AIC/BIC scores.  
  - **Implementation**: `code/validation.py` reads `model_comparison.json`, counts models with `converged=True` and finite `aic`/`bic`, writes `data/results/model_convergence_check.json` with the count and a pass flag.  
  - **Verification**: Pass flag is true only if count ≥ 3; CI asserts this.

- [ ] **T024** [SC-004] Verify that the model chosen for tail diagnostics is the one with the lowest AIC in the full comparison.  
  - **Implementation**: `code/validation.py` cross‑checks `model_comparison.json` and `final_model.json`, writes `data/results/best_model_selection_check.json` with a boolean result.  
  - **Verification**: CI asserts the boolean is true.

- [ ] **T025** [SC-003] Verify that the Hill estimator produces a finite `estimated_alpha`.  
  - **Implementation**: `code/validation.py` reads `tail_index_estimate.json`, writes `data/results/hill_finite_check.json` with a boolean indicating finiteness.  
  - **Verification**: CI asserts the boolean is true.

- [ ] **T026** [SC-009] Verify that the variance‑minimization results of the Hill stability analysis are recorded in the output JSON.  
  - **Implementation**: `code/validation.py` ensures `tail_index_estimate.json` contains the `stability_range` object with `start_k` and `end_k`.  
  - **Verification**: CI fails if those fields are missing or empty.

- [ ] **T027** [FR-008] Monitor peak RAM usage during the entire pipeline and assert it does not exceed 7 GB.  
  - **Implementation**: Wrapper script `code/monitor.py` records maximum resident set size and writes `data/results/memory_usage.json` (`peak_mb`).  
  - **Verification**: CI asserts `peak_mb <= 7000`.

- [ ] **T028** [SC-005] Record total runtime of the pipeline and assert it is ≤ 3600 seconds.  
  - **Implementation**: `code/monitor.py` also timestamps start/end, writes `data/results/runtime.json` (`seconds`).  
  - **Verification**: CI asserts `seconds <= 3600`.

- [ ] **T029** [Constitution] Verify that all random number generators are seeded with fixed values.  
  - **Implementation**: `code/seed_check.py` scans `code/` for calls to `numpy.random.seed`, `random.seed`, `torch.manual_seed`, etc., writes `data/results/seed_pin_check.json` with a boolean `pinned`.  
  - **Verification**: CI asserts `pinned` is true.

- [ ] **T030** [SC-005] Record total pipeline runtime and enforce the 3600‑second hard deadline required by SC‑005.  
  - **Implementation**: Extend `code/monitor.py` to raise a `RuntimeError` if `seconds > 3600` after logging the value to `data/results/runtime.json`.  
  - **Verification**: CI step checks that the pipeline exits with a non‑zero code when `seconds` exceeds 3600, otherwise passes.
