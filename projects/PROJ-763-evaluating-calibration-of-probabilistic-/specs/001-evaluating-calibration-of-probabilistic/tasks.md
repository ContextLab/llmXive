# Tasks: Evaluating Calibration of Probabilistic Weather Forecasts

**Inputs**: `spec.md`, `plan.md`, data‑model, contracts, and any reviewer feedback.  
All paths are relative to the repository root.  
Tasks are grouped by research phase; each task is a single checkbox item that can be marked complete independently.

---

## Phase 0 – Data acquisition & integrity gate  

- [ ] **T001** **Download SubseasonalRodeo dataset** – Implement `code/src/download.py` to `wget` the verified URL, verify SHA‑256 checksum, and write the raw archive to `data/raw/subseasonal_rodeo.tar.gz`.   <!-- FAILED: unspecified -->
  - *Verification*: script raises an exception (non‑zero exit) if download fails or checksum mismatches.  

- [ ] **T002** **Data Availability Gate** – Within `code/src/download.py` check that the extracted files contain either `probability_value` or `precip_prob` fields. If missing, exit with code 1 and log “Data Availability Gate Failed”. No synthetic fallback.   <!-- FAILED-IN-EXECUTION: code/src/download.py exit=1 -->

- [ ] **T003** **Streaming loader skeleton** – Add `code/src/loader.py` that uses `datasets.load_dataset(..., streaming=True)` to iterate over the extracted Parquet files, yielding records as dictionaries. This loader will be reused by all downstream phases and must respect the gate from T002.  

---

## Phase 1 – Alignment of forecasts and observations  

- [ ] **T004** **Align records** – Implement `code/src/align.py` to join forecast and observation tables on `grid_id`, `lead_time`, and matching dates, discarding any rows with missing values. Output aligned parquet to `data/processed/aligned.parquet`.  
  - *Verification*: schema validation against `contracts/dataset.schema.yaml`.  

- [ ] **T005** **Alignment unit‑test** – Add `tests/unit/test_align.py` that loads a tiny streamed sample (≤ 100 rows) and asserts correct join size and field presence.  

---

## Phase 2 – Baseline calibration assessment (US‑1)  

- [ ] **T006** [US1] **Baseline metric functions** – In `code/src/metrics.py` provide:
  - `compute_brier(aligned_df)`  
  - `compute_crps(aligned_df)`  
  - `compute_reliability_slope(aligned_df)` (linear regression on probability bins for SC‑003)  
  - `compute_pit_ks(aligned_df)` (Kolmogorov‑Smirnov test for SC‑004)  
  - handling of zero‑event bins (return `np.nan` with warning).  

- [ ] **T007** [US1] **Baseline reliability diagram** – Extend `code/src/metrics.py` with `plot_reliability(aligned_df, out_path)` that creates a kernel‑smoothed diagram (`results/reliability_diagram_raw.png`).  

- [ ] **T008** [US1] **Run baseline pipeline** – Create `code/src/run_baseline.py` that calls the loader, alignment (T004), metric functions (T006) and diagram (T007), and writes:
  - `results/results_baseline.csv` (conforms to `contracts/output.schema.yaml` → `results_baseline`, including reliability slope and PIT‑KS p‑value)  
  - `results/reliability_diagram_raw.png`  
  - `results/pit_histogram_raw.png` (PIT histogram & KS statistic).  

- [ ] **T009** **Baseline contract test** – Add `tests/contract/test_baseline_schema.py` that validates `results/results_baseline.csv` against `contracts/output.schema.yaml`.  

- [ ] **T027** **Compute reliability‑slope deviation** – Extend the baseline, isotonic, and Bayesian evaluation scripts to calculate the absolute deviation of the reliability‑slope from 1.0 for each method, outputting `results/reliability_slope_{method}.csv` (columns: `lead_time`, `variable`, `slope_deviation`).  

- [ ] **T028** **Validate reliability‑slope SC‑003** – Add a verification script `code/src/validate_reliability_slope.py` that reads the CSVs produced by T027 and asserts all `slope_deviation` ≤ 0.05. The script fails with a non‑zero exit code if any violation is found, satisfying SC‑003.  

- [ ] **T029** **Compute PIT‑KS test** – Implement a function (e.g., in `metrics.py`) that computes the Kolmogorov‑Smirnov statistic comparing the PIT values to a uniform distribution for each method, writing `results/pit_ks_{method}.json` containing the p‑value.  

- [ ] **T030** **Validate PIT‑KS SC‑004** – Add `code/src/validate_pit_ks.py` that reads the JSON files from T029 and asserts each p‑value > 0.05. The script exits non‑zero on failure, fulfilling SC‑004.  

---

## Phase 3 – Isotonic regression recalibration (US‑2)  

- [ ] **T010** [US2] **Isotonic trainer** – Implement `code/src/isotonic/train.py` that:
  1. Performs a blocked split (years 1‑N train, N+1 test) based on `forecast_date`.  
  2. Verifies no data leakage: assert `max(train_date) < min(test_date)` (SC‑009).
  3. For each `lead_time` × `variable`, fits `sklearn.IsotonicRegression` on the training set.
  4. If samples < 200, pool with nearest adjacent lead‑time or fall back to raw forecast (FR‑004).
  5. Saves model metadata to `results/isotonic_model_meta.json`.  
  - *Verification*: script produces `results/isotonic_model_meta.json` and passes a basic content check.

- [ ] **T011** **Isotonic sensitivity splits** – Extend `code/src/isotonic/train.py` to loop over split ratios `70/30`, `60/40`, `80/20`. For each ratio produce `results/results_isotonic_<ratio>.csv` and corresponding diagram `results/reliability_diagram_isotonic_<ratio>.png`.  
  - *Verification*: ensure all `results_isotonic_<ratio>.csv` and diagrams exist for all three ratios.

- [ ] **T012** **Isotonic evaluation driver** – Create `code/src/run_isotonic.py` that loads the fitted models, applies them to the test split, computes Brier/CRPS (reuse functions from T006), and writes the primary result file `results/results_isotonic.csv`.  
  - *Verification*: `results/results_isotonic.csv` validates against `contracts/output.schema.yaml`.

- [ ] **T013** **Diebold‑Mariano for baseline vs isotonic** – Implement `code/src/compare/dm_isotonic.py` that:
  - Runs Shapiro‑Wilk on daily Brier error differences per lead time/variable.  
  - If p ≥ 0.05, uses HAC‑adjusted DM test; otherwise switches to a 7‑day block bootstrap.  
  - Writes `results/dm_baseline_vs_isotonic.json` conforming to `contracts/metrics.schema.yaml`.  

- [ ] **T014** **Isotonic contract & unit tests** – Add:
  - `tests/unit/test_isotonic.py` (model fitting & minimum‑sample logic)  
  - `tests/contract/test_isotonic_schema.py` (validate `results_isotonic.csv`).  

---

## Phase 4 – Bayesian hierarchical recalibration (US‑3)  

- [ ] **T015** [US3] **Bayesian model definition** – In `code/src/bayesian/model.py` define a hierarchical logistic regression in PyMC:
  - Lead‑time decay prior (`lead_time_decay_coefficient` < 0).  
  - Configurable prior strength (`weak`, `medium`, `strong`).  
  - Include a `flat` prior option for sensitivity.  
  - *Verification*: unit test ensures model can be instantiated and required parameters are present.

- [ ] **T016** **Bayesian sampling driver** – Create `code/src/bayesian/run_sampling.py` that:
  - Accepts a prior‑type argument.  
  - Runs 4 chains with ≥ 2000 draws each (default).  
  - Enforces a 60‑minute wall‑clock timeout.  
  - Computes R‑hat and ESS; if any R‑hat > 1.05 or ESS < 400, marks status `unconverged`.  
  - On timeout or non‑convergence writes fallback results using isotonic metrics to `results/results_fallback.csv` (method=`isotonic`, status=`fallback`).  
  - Otherwise writes `results/results_bayesian.csv` with convergence status `converged`.  
  - *Verification*: `results/results_bayesian.csv` or `results_fallback.csv` validates against schema and contains convergence status.

- [ ] **T017** **Bayesian prior‑sensitivity runs** – Orchestrate three runs of `run_sampling.py` for `weak`, `medium`, `strong` decay, plus a `flat` run. Log each run’s metric values to `results/prior_sensitivity_log.csv` (matches `contracts/metrics.schema.yaml` → `prior_sensitivity_log`).  
  - *Verification*: `results/prior_sensitivity_log.csv` validates against schema; assert physics‑informed Brier < flat Brier (SC‑006).

- [ ] **T018** **Bayesian evaluation driver** – Implement `code/src/run_bayesian.py` that:
  - Loads posterior predictive probabilities, computes Brier/CRPS (reuse T006), and writes the appropriate result file (`results_bayesian.csv` or `results_fallback.csv`).  
  - *Verification*: output files exist and match `contracts/output.schema.yaml`.

- [ ] **T019** **Diebold‑Mariano for isotonic vs Bayesian** – Extend `code/src/compare/dm_bayesian.py` to perform the same normality‑check → DM‑HAC or block‑bootstrap logic for the comparison pair `isotonic_vs_bayesian`. Output `results/dm_isotonic_vs_bayesian.json`.  

- [ ] **T020** **Bayesian contract & unit tests** – Add:
  - `tests/unit/test_bayesian.py` (model building, prior handling, convergence flagging)  
  - `tests/contract/test_bayesian_schema.py` (validate `results_bayesian.csv` / `results_fallback.csv`).  

---

## Phase 5 – Full result aggregation & success‑criterion checks  

- [ ] **T021** **Summary table generation** – Implement `code/src/summary.py` that merges:
  - `results_baseline.csv`, `results_isotonic.csv`, `results_bayesian.csv` (or fallback)  
  - DM test JSON files (baseline‑vs‑isotonic, isotonic‑vs‑bayesian)  
  - Prior‑sensitivity log  
  - Produces `results/summary_table.csv` and a human‑readable `results/README.md` describing which success criteria (SC‑001 – SC‑009) are met.  
  - *Verification*: `results/summary_table.csv` matches schema and `results/README.md` lists all SC statuses.

- [ ] **T022** **Automated success‑criterion validation script** – Add `code/src/validate_sc.py` that parses `summary_table.csv` and the DM/bootstrapped results to assert:
  - SC‑001: DM p‑value < 0.05 **or** bootstrap CI excludes 0.  
  - SC‑002: Bayesian CRPS reduction ≥ 1 % **or** DM p‑value < 0.05.  
  - SC‑003‑SC‑006: metric thresholds (reliability slope ≤ 0.05 deviation, PIT KS > 0.05, prior‑informed better than flat).  
  - SC‑007: Data‑availability gate enforced (checked in T002).  
  - SC‑008: Normality test p‑values logged (DM scripts).  
  - SC‑009: No leakage between train/test dates (verified in split logic).  
  - *Verification*: add a unit test that mocks failing SCs and asserts the script exits with code 1.

- [ ] **T023** **End‑to‑end CI runnable script** – Create `run_pipeline.sh` that sequentially invokes:
  1. `code/src/download.py`  
  2. `code/src/run_baseline.py`  
  3. `code/src/run_isotonic.py`  
  4. `code/src/bayesian/run_sampling.py` (default prior)  
  5. `code/src/run_bayesian.py` (handles fallback internally)  
  6. `code/src/summary.py`  
  7. `code/src/validate_sc.py`  
  - *Runtime Enforcement (FR‑008)*: Script must measure and log wall‑clock time for each step; abort with error if total runtime > 6 h, isotonic step > 30 min, or Bayesian step > 60 min.  
  - *Verification*: script aborts on any non‑zero exit.

---

## Phase 6 – Documentation & reproducible handoff  

- [ ] **T024** **Quick‑start guide** – Write `quickstart.md` documenting:
  - Required environment (`Python 3.11`, `requirements.txt`).  
  - One‑line command to run the full pipeline (`bash run_pipeline.sh`).  
  - How to interpret the `results/` directory.  

- [ ] **T025** **Contract test integration** – Update `tests/__init__.py` (if needed) so that `pytest` automatically discovers all contract tests (T009, T014, T020) during CI.  

- [ ] **T026** **Paper‑stage handoff** – Add `paper/handoff.yaml` summarizing:
  - Dataset source URL and checksum.  
  - All metric CSVs and figures required for manuscript tables/plots.  
  - Version of each model (isotonic, Bayesian) and random seed used.  

---

### Execution order & dependencies  

| Task | Depends on |
|------|------------|
| T001 → T002 → T003 | – |
| T004 | T003 |
| T005 | T004 |
| T006 → T007 → T008 | T004 |
| T009 | T008 |
| T027 | T008 |
| T028 | T027 |
| T029 | T008 |
| T030 | T029 |
| T010 → T011 → T012 | T004 |
| T013 | T012 |
| T014 | T012, T013 |
| T015 → T016 → T018 → T019 | T004 |
| T017 | T015 |
| T020 | T018, T019 |
| T021 → T022 | T008, T012, T016 (or fallback), T013, T019, T017 |
| T023 | All prior tasks |
| T024 → T025 → T026 | T023 (for reproducibility evidence) |

All tasks can be executed in parallel where their dependencies are satisfied.  

**Note**: No task creates synthetic data or fabricates results. Every computation consumes the real SubseasonalRodeo dataset (or the verified NOAA GFS fields within it). All scripts fail loudly on missing fields, checksum errors, or convergence failures, satisfying the “Data Availability Gate” and the strict CPU‑first / GPU‑only policy.