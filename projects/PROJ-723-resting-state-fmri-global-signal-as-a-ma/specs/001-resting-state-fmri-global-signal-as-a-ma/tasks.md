# Tasks: Resting‑State fMRI Global Signal as a Marker of Mind‑Wandering

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, contracts (`dataset.schema.yaml`, `output.schema.yaml`), and existing code artifacts.  

The checklist below follows the platform’s research‑phase template (end‑to‑end analysis → validation → results handoff).  Tasks are grouped by user story / phase.  Completed tasks are marked `[X]`; pending or revised tasks are `[ ]`.  Each item lists the scientific requirement it satisfies, the exact artifact paths it creates or modifies, and an observable verification step.

---

## Phase 0 – Project scaffolding (already verified)

- [X] T001a Create `code/` directory at repository root.  
  *Requirement*: Provide a place for all Python modules.  
  *Verification*: `ls code/` shows the directory.

- [X] T001b Create `data/raw/` directory at repository root.  
  *Verification*: Directory exists.

- [X] T001c Create `data/processed/` directory at repository root.  
  *Verification*: Directory exists.

- [ ] T001d Create `data/results/` directory at repository root.  
  *Verification*: Directory exists.

- [X] T001e Create `tests/` directory at repository root.  
  *Verification*: Directory exists.

- [ ] T002 Initialize `requirements.txt` with pinned versions of `pandas`, `numpy`, `scikit-learn`, `nibabel`, `requests`, `pyyaml`, `statsmodels`, `scipy`.  
  *Verification*: `pip install -r requirements.txt` succeeds on a clean environment.

- [ ] T003 [P] Add a `quickstart.md` that documents the single command `python code/main.py` and the expected top‑level outputs (`data/processed/cleaned_data.csv`, `data/results/final_report.json`).   <!-- FAILED-IN-EXECUTION: code/main.py exit=1 -->
  *Verification*: Running the command as described produces the files.

- [ ] T004 Implement `code/config.py` defining project‑wide paths (`data/raw/`, `data/processed/`, `data/results/`), random seeds, and default hyper‑parameters (alpha grid, CV folds).  
  *Verification*: Importing `config` returns the expected constants.

- [ ] T005 [P] Implement `code/utils.py` with helpers for logging (`get_logger`), safe file I/O, and error handling.  
  *Verification*: Unit test `tests/test_utils.py` passes.

- [ ] T006 [P] Implement `code/mwq_scoring.py` that documents the MWQ version, reverse‑scoring rules, and provides `score_mwq(df)` returning a numeric total.  
  *Verification*: Test `tests/test_mwq_scoring.py` confirms correct scoring on a hand‑crafted example.

---

## Phase 1 – Data Ingestion & Metric Computation (User Story 1, P1)

- [ ] T009 Implement data download and BIDS organization in `code/ingestion.py` using `datasets.load_dataset(..., streaming=True)` to fetch verified HCP minimally‑preprocessed resting‑state fMRI runs and the MWQ CSV. Organize raw data into a BIDS‑compatible directory structure (`data/raw/sub-<label>/func/`) and generate JSON side‑car files containing acquisition parameters (TR, voxel size) and preprocessing provenance.  
  *Path*: `data/raw/` (BIDS structure with JSON side-cars).  
  *Verification*: After run, `ls data/raw/` shows subject folders with `func/` subdirs and corresponding `.json` files; a log entry confirms successful download.

- [ ] T009a Add column‑inspection logic in `code/ingestion.py` that checks each streamed record for `global_signal` **or** `global_signal_sd`. If missing, the script aborts with `FATAL: Dataset Mismatch - Required columns not found in verified URL`.  
  *Verification*: Running the script on a deliberately corrupted stream raises the expected fatal error.

- [ ] T009b Save the fetched raw files under `data/raw/` and record SHA‑256 checksums in `state/artifact_hashes.yaml`.  
  *Verification*: The YAML file contains one entry per file and matches recomputed hashes.

- [ ] T010 Implement schema validation (`validate_schema(df, "specs/001‑resting‑state‑fmri‑global‑signal‑as‑a‑ma/contracts/dataset.schema.yaml")`) that raises a fatal error if required columns are absent or have wrong types.  
  *Verification*: Validation passes on the clean CSV produced in T016; fails with a clear message on a malformed CSV.

- [ ] T011 Compute the voxel‑wise mean time series (global signal) per run **stream‑wise** (online accumulation of sum and sum‑of‑squares) to avoid loading a full 4D volume into RAM.  
  *Path*: `code/ingestion.py` → intermediate variable `run_global_signal.npy` (temporary, not persisted).  
  *Verification*: Unit test `tests/test_ingestion.py::test_global_signal_online` confirms that the online algorithm yields the same mean as loading the full volume for a small test subject.

- [ ] T012 Compute the per‑run standard deviation of the global signal, then average across all runs of a subject to obtain `global_signal_sd`. Store also `global_signal_variance`.  
  *Output*: Column `global_signal_sd` and `global_signal_variance` in the subject‑level table.  
  *Verification*: Test against a hand‑crafted array (`[1,2,3,4]`) checks that the SD matches 1.118 within `1e‑4`.

- [ ] T013 Implement subject‑level validation that joins the fMRI‑derived metrics with MWQ scores. Subjects lacking either component are excluded and logged.  
  *Log*: `data/logs/exclusions.log` entry format `EXCLUSION: reason=pair_missing, subject_id=XXXX`.  
  *Verification*: Unit test `tests/test_ingestion.py::test_pair_exclusion` confirms that a deliberately missing MWQ entry results in a logged exclusion.

- [ ] T014 Implement motion‑artifact exclusion: compute mean FD per subject; if `mean_fd > 0.5 mm`, exclude the subject and log `EXCLUSION: reason=high_motion, subject_id=XXXX, mean_fd=Y.YY`.  
  *Verification*: Test `tests/test_ingestion.py::test_motion_exclusion` validates that a subject with FD = 0.52 mm is excluded and logged correctly.

- [ ] T015 Implement zero‑variance exclusion: subjects with `global_signal_sd == 0` are removed, a warning is emitted, and the exclusion is logged as `EXCLUSION: reason=zero_variance, subject_id=XXXX`.  
  *Verification*: Test `tests/test_ingestion.py::test_zero_variance_exclusion` confirms behavior.

- [ ] T016 Write the final, cleaned dataset to `data/processed/cleaned_data.csv` with columns  
  `subject_id, global_signal_sd, global_signal_variance, mwq_score, age, sex, mean_fd, mean_dvars, exclusion_reason`.  
  *Verification*: The CSV validates against `contracts/dataset.schema.yaml` (using `validate_schema`).

- [ ] T017 [P] Unit test: Verify that `code/ingestion.py::compute_global_signal_sd` reproduces the manual SD on a small synthetic array.  
  *Path*: `tests/test_ingestion.py`.  
  *Verification*: `pytest -q` passes.

- [ ] T018 [P] Unit test: Verify exclusion logic (missing pairs, high motion, zero variance) produces the correct log entries and filtered CSV.  
  *Verification*: `pytest -q` passes.

---

## Phase 2 – Association Modeling & Baseline Comparison (User Story 2, P2)

- [ ] T019 Implement the primary ridge‑regression pipeline in `code/modeling.py::run_ridge_pipeline`.  
  *Features*: `Global_Signal_SD`, `mean_fd`, `mean_dvars`, `age`, `sex`.  
  *Nested CV*: Outer 5‑fold CV, inner grid search over `alpha_grid = np.logspace(-4, 2, 10)`.  
  *Outputs*:  
  - `data/processed/residuals.csv` (subject‑wise residuals).  
  - `data/results/full_model.json` (MAE, Pearson r, R², selected α).  
  *Verification*: After run, JSON contains keys `mae`, `pearson_r`, `r_squared`; residuals file is non‑empty.

- [ ] T021 Implement null‑distribution generation (`code/modeling.py::run_null_permutations`) with 100 permutations of the MWQ vector (seed = 42).  
  *Outputs*: `data/results/null_distribution.json` (list of `{mae, r2}`) and histogram plot `data/results/null_dist.png`.  
  *Verification*: Length of the list equals 100; histogram file size > 0 KB.

- [ ] T022 Compute the empirical p‑value by comparing the observed MAE (from `full_model.json`) to the null MAE distribution (`null_distribution.json`). Write the p‑value into `data/results/full_model.json` under the key `p_value`.  
  *Verification*: The JSON now contains a numeric `p_value` between 0 and 1.

- [ ] T023 Implement the **Reduced Model** (covariates only: FD, DVARS, age, sex) and its own permutation loop (`run_reduced_model_permutations`).  
  *Outputs*: `data/results/reduced_null_r2.json` (list of R²) and `data/results/reduced_model.json` (observed R²).  
  *Verification*: Files exist and contain the expected structures.

- [ ] T024 Compute the **Delta R²** (Full R² – Reduced R²) for the observed data and for each permutation; calculate an empirical p‑value for the delta. Write results to `data/results/delta_r2.json`.  
  *Verification*: JSON contains `delta_r2_observed`, `p_value_delta_r2`, and a flag `significant` (True/False).

- [ ] T025 Run collinearity diagnostics (`code/diagnostics.py::compute_vif`) on `cleaned_data.csv`. Write `data/results/diagnostics.json` with VIF per predictor and a boolean `collinearity_flag` (True if any VIF > 5 or GSA‑FD correlation > 0.7).  
  *Verification*: JSON includes `vif` dict and `collinearity_flag`.

- [ ] T026 Generate the consolidated model report `data/results/model_report.json` containing:  
  - Mean out‑of‑fold MAE, Pearson r, R², p‑value (full model).  
  - Reduced‑model R² and Delta R² statistics.  
  - `interpretation_type`: `"Predictive Gain"` if `collinearity_flag` is True, otherwise `"Independent Effect"`.  
  *Verification*: JSON schema matches `output.schema.yaml` and contains the `interpretation_type` field.

- [ ] T027 [P] Unit test: Validate nested CV and α‑tuning on a synthetic dataset with known r ≈ 0.3.  
  *Verification*: Test asserts that the reported `pearson_r` lies in `[0.25, 0.35]` and that the null model MAE distribution centers near the observed MAE.

- [ ] T028 [P] Unit test: Verify that the null‑distribution p‑value calculation matches a brute‑force count on a tiny synthetic permutation set.  
  *Verification*: Test passes.

---

## Phase 3 – Robustness & Sensitivity Analyses (User Story 3, P3)

- [ ] T029 Implement alpha‑sweep sensitivity analysis in `code/robustness.py::alpha_sweep`.  
  *Range*: `np.logspace(-4, 2, 10)`.  
  *Output*: `data/results/alpha_sweep.json` (α → MAE) and plot `data/results/alpha_sweep.png`.  
  *Verification*: JSON contains 10 entries; plot file size > 0 KB.

- [ ] T030 Implement alternative‑metric analysis using `global_signal_variance` instead of SD (`code/robustness.py::variance_analysis`).  
  *Output*: `data/results/variance_model.json` with MAE, Pearson r, R².  
  *Verification*: JSON exists and contains numeric metrics.

- [ ] T031 **[Revised]** Implement partial‑correlation analysis (`code/robustness.py::partial_correlation`) that computes the partial correlation between MWQ and GSA controlling for FD & DVARS (using residuals from `residuals.csv`).  
  *Output*: `data/results/partial_corr.json` with keys `pearson_r`, `p_value`, and `status` (`"significant"` if p < 0.05 else `"null_finding"`).  
  *Verification*: After running the robustness script, the JSON file exists and contains the computed partial correlation and p-value; verified by `tests/test_robustness.py::test_partial_corr_execution`.

- [ ] T032 Generate the combined robustness report `data/results/robustness_report.json` that aggregates the alpha‑sweep results, variance‑analysis metrics, and partial‑correlation outcome.  
  *Verification*: JSON contains three top‑level keys (`alpha_sweep`, `variance_analysis`, `partial_correlation`) with the appropriate sub‑structures.

- [ ] T033 [P] Unit test: Confirm that the variance‑analysis Pearson r stays within ±0.05 of the primary SD model’s r (`tests/test_robustness.py::test_variance_metric_stability`).  
  *Verification*: Test passes.

- [ ] T034 [P] Unit test: Verify that the alpha‑sweep JSON contains MAE values that form a convex curve with a clear minimum (`tests/test_robustness.py::test_alpha_sweep_monotonicity`).  
  *Verification*: Test passes.

---

## Phase 4 – Reporting, Power Analysis & Final Hand‑off

- [ ] T035 Implement power analysis (`code/diagnostics.py::calculate_power`) that computes the Minimum Detectable Effect Size (MDES) for the observed sample size (`N = len(cleaned_data.csv)`), α = 0.05, power = 0.80. Write `data/results/power_analysis.json` with fields `N`, `MDES`, `power_risk` (True if MDES > 0.3).  
  *Verification*: JSON is created; `power_risk` flag is logged.

- [ ] T036 Aggregate all result artifacts into `data/results/final_report.json` (primary model, null distribution, reduced model, delta R², robustness, power analysis).  
  *Verification*: File validates against a combined schema (manual check) and contains all required sections.

- [ ] T037 Enhance `final_report.json` with a `criteria_status` object that maps each success criterion (SC‑001 – SC‑005) to:  
  - `status` (`"met"` or `"not met"`),  
  - `narrative_summary` (human‑readable sentence including the actual metric values),  
  - `metrics` (the numeric values used for the decision).  
  *Verification*: The JSON includes the five entries; a quick script prints each narrative correctly.

- [ ] T038 Generate visualizations:  
  - `data/results/null_dist.png` (histogram of null MAE).  
  - `data/results/alpha_sweep.png` (MAE vs. α).  
  - `data/results/corr_matrix.png` (pairwise Pearson correlations among all predictors and MWQ).  
  *Verification*: All PNG files exist and have non‑zero file size.

- [ ] T039 Create `code/main.py` – the orchestrator that runs the full pipeline in order: ingestion → cleaning → modeling → null/permutation analyses → robustness → reporting. The script logs progress to `data/logs/pipeline.log` and exits with status 0 on success.  
  *Verification*: Executing `python code/main.py` on the test fixture (`data/tests/test_fixture.csv`) completes without errors and produces all expected result files.

- [ ] T040 Provide a small synthetic test fixture `data/tests/test_fixture.csv` (N = 10) containing all required columns, **solely for CI integration testing**. The main pipeline (`main.py`) is coded to **ignore** this fixture unless the environment variable `USE_TEST_FIXTURE=1` is set, thereby preventing accidental use of synthetic data in the real analysis.  
  *Verification*: Setting the env var and running `main.py` processes the fixture and produces a minimal `final_report.json`; without the var the script uses the real HCP data.

---

## Phase 5 – Revision & Reviewer‑Driven Fixes

- [ ] T041 **[Reopened]** Refine streaming logic in `code/ingestion.py` to guarantee that global‑signal statistics are accumulated **chunk‑wise** (no full‑volume loads). Add explicit comments and a runtime guard that raises an error if a chunk exceeds 500 MB in memory.  
  *Verification*: A profiling run on a medium‑size subject shows peak memory < 200 MB; unit test `tests/test_ingestion.py::test_memory_bound` passes.

- [ ] T042 **[Reopened & Completed]** Implement dynamic partial‑correlation logic (see T031). Ensure the script writes `data/results/partial_corr.json` with the computed result. Add a unit test `tests/test_robustness.py::test_partial_corr_execution` that verifies the calculation.  
  *Verification*: After running the robustness script, the JSON file contains numeric results; the test passes.

- [ ] T043 **[Reopened]** Strengthen exclusion‑logging (previously T044) by enhancing the helper `log_exclusion(reason, subject_id, **kwargs)` so that it records the numeric threshold that triggered the exclusion (e.g., `mean_fd=0.52, threshold=0.5`). The ingestion pipeline now calls this helper for every exclusion case. Verify that `data/logs/exclusions.log` contains lines such as:  
  `EXCLUSION: reason=high_motion, subject_id=100307, mean_fd=0.52, threshold=0.5`.  
  *Verification*: Integration test `tests/test_ingestion.py::test_logging_details` confirms the exact log format.

- [ ] T045 **[Reopened]** Add a runtime guard in `code/modeling.py` (task T045) that asserts the permutation loop executed exactly 100 iterations. If the count deviates, raise `RuntimeError` with a clear message.  
  *Verification*: A deliberately interrupted run triggers the error; the normal run completes without raising.

- [ ] T046 **[Reopened]** Ensure that all tasks that write JSON files conform to the corresponding contract schemas (`dataset.schema.yaml`, `output.schema.yaml`). Add a validation step after each write that loads the JSON and validates it with `jsonschema.validate`. Fail loudly on any mismatch.  
  *Verification*: After each pipeline stage, the CI logs “JSON schema validation passed” for the newly written file; a corrupted file causes the pipeline to abort with a descriptive traceback.

---

### Dependency Map (summary)

| Spec Requirement | Satisfying Task(s) |
|------------------|--------------------|
| FR‑001 (download & parse HCP) | T009, T009a, T009b |
| FR‑002 (global‑signal SD) | T011, T012 |
| FR‑003 (motion & demographic covariates) | T016, T019 |
| FR‑004 (ridge regression, nested CV) | T019 |
| FR‑005 (null distribution & p‑value) | T021, T022, T023, T024 |
| FR‑006 (alpha sweep) | T029 |
| FR‑007 (variance metric) | T030 |
| FR‑008 (exclude high FD) | T014 |
| FR‑009 (pair validation) | T013 |
| SC‑001 … SC‑005 | T025, T032‑T034, T035‑T037 |
| Edge‑case handling (exclusions, collinearity) | T013‑T015, T025, T042, T043 |

---

**Checkpoint**: All unchecked tasks (T041‑T046) are ready for implementation and verification. Once they pass their unit and integration tests, the entire pipeline will satisfy the specification and be ready for the next verification round.