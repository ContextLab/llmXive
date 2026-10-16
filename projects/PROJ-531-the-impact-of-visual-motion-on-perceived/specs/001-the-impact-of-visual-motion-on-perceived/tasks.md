# Tasks: The Impact of Visual Motion on Perceived Agency in Virtual Interactions

**Inputs**: `spec.md`, `plan.md`, existing artifacts, reviewer feedback.  
**Goal**: Implement a reproducible end‑to‑end research pipeline that (1) acquires real or synthetic human‑avatar interaction data, (2) preprocesses and validates it, (3) fits regression and tree‑based models, (4) applies statistical corrections and sensitivity checks, (5) creates visualisations, (6) produces a fully‑validated `model_metrics.json` artifact, and (7) documents a clean hand‑off for the paper stage.

---

## Phase 1 – Scope, Ethics & End‑to‑End Bootstrap  

- [X] T001 [US0] **Define project scope & ethics** – update `README.md` and create `docs/scope.md` that (a) state the “real‑data first, synthetic‑only for pipeline stress‑test” policy, (b) reference the IRB approval document, and (c) cite the feature branch `001-visual-motion-agency`.  
  *Verification*: Both files exist, contain the required sections, and are linked from `quickstart.md`.

- [X] T001b [US0] **Create documented IRB approval file** – place a PDF (or placeholder) `protocols/irb_approval.pdf` with the IRB approval letter or exemption statement.  
  *Verification*: `protocols/irb_approval.pdf` exists and is referenced in `docs/scope.md`.

- [ ] T002 [US1] **Download real dataset & validate instrument** – implement `code/download_data.py` to (1) query OpenML / HuggingFace / OSF for a dataset containing motion telemetry **and** a validated agency questionnaire, (2) verify the questionnaire via Crossref DOI lookup, Semantic Scholar citation count ≥ 10, and Cronbach’s α ≥ 0.70 (FR‑013), (3) save the raw file to `data/raw/real_data.parquet`, (4) write `data/raw/download_status.json` with keys `status` (`"success"` | `"invalid"` | `"unavailable"`), `source_url`, `instrument_valid`, and `use_synthetic` (boolean), and (5) exit with a non‑zero code and clear error message if `status == "invalid"`.  
  *Verification*: Running the script produces `real_data.parquet` (or fails cleanly) **and** a correctly‑structured `download_status.json`.

- [ ] T002a [US1] **Enforce instrument validity** – implement `code/check_instrument_validity.py` that reads `download_status.json`; if `instrument_valid == false` it aborts the pipeline with an informative error.   <!-- FAILED-IN-EXECUTION: code/check_instrument_validity.py exit=1 -->
  *Verification*: Pipeline stops with exit code 1 when an invalid instrument is detected.

- [ ] T003 [US1] **Generate synthetic dataset when real data unavailable** – implement `code/generate_synthetic_data.py` to (1) read `data/raw/download_status.json`; if `status == "unavailable"` or `instrument_valid == false`, generate a synthetic CSV with ≥ 150 rows, (2) columns: `participant_id` (UUID), `latency` (ms), `smoothness` (dimensionless jerk), `lead_time` (ms), `agency_score` (0‑100), `user_response_trigger` (ms), (3) impose a known linear relationship `agency_score = 0.4*latency - 0.3*smoothness + 0.2*lead_time + ε`, (4) ensure `user_response_trigger` is independent of `agency_score` (Pearson r < 0.05, permutation p > 0.10), (5) write the file to `data/raw/synthetic_data.csv` and set `"use_synthetic": true` in `download_status.json`.  
  *Verification*: The CSV exists, contains all required columns, meets the row‑count requirement, and a post‑hoc script confirms the independence condition.

- [ ] T003a [US1] **Update download status after synthetic generation** – modify `download_status.json` to include `"use_synthetic": true` and `"status": "synthetic"` after T003 completes.  
  *Verification*: `download_status.json` reflects the synthetic flag.

---

## Phase 2 – Pre‑processing, Validation & Power Gating  

- [ ] T004 [US1] **Preprocess data** – implement `code/preprocess.py` to (1) load either `data/raw/real_data.parquet` or `data/raw/synthetic_data.csv` based on `download_status.json`, (2) extract motion features `latency` and `smoothness`; derive `lead_time = user_response_trigger - latency` **only if** three independence checks pass (Pearson r < 0.05, partial‑r < 0.05, permutation p > 0.10), (3) aggregate agency questionnaire items into a continuous score (mean, rescaled 0‑100), (4) drop rows with any missing motion or agency values, (5) write the cleaned table to `data/processed/analysis_ready.csv` (conforms to `contracts/dataset.schema.yaml`) and a brief `preprocess_report.json` with row‑count stats.  
  *Verification*: `analysis_ready.csv` contains the required columns and ≥ 100 complete rows; `preprocess_report.json` is valid JSON.

- [ ] T015 [US1] **Compute VIF diagnostics** – implement `code/compute_vif.py` to read `analysis_ready.csv`, compute Variance Inflation Factor for each predictor, exclude any with VIF ≥ 5, and write `data/processed/vif_report.json` (includes per‑feature VIF and boolean `vif_pass`).  
  *Verification*: `vif_report.json` exists, VIF values are numeric, and `vif_pass` correctly reflects the threshold.

- [ ] T016 [US1] **Power analysis** – implement `code/power_analysis.py` to (1) read `analysis_ready.csv`, (2) perform an analytical power calculation for a multiple linear regression with up to three predictors (α = 0.05, target power ≥ 0.80) using `statsmodels.stats.power.FTestPower`, (3) output `data/processed/modeling_config.json` containing `effective_n`, `detectable_f2`, `power`, `sc001_pass` (≥ 100 rows), `power_pass` (≥ 0.80), and an `abort_flag` (true when `effective_n < 80`).  
  *Verification*: `modeling_config.json` exists with correctly typed fields.

- [ ] T016b [US1] **Enforce gates before modeling** – implement `code/enforce_gates.py` that reads `modeling_config.json`; if `abort_flag` is true it aborts the pipeline with a clear message. This task must be executed **before any modeling task**.  
  *Verification*: Pipeline stops with exit code 1 when the gate condition is triggered.

---

## Phase 3 – Modeling, Correction & Sensitivity  

- [ ] T021 [US2] **Fit Ordinary Least Squares regression** – implement `code/fit_ols.py` to read `analysis_ready.csv`, fit OLS, compute coefficients, standard errors, raw p‑values, and write `data/results/ols.json`.  
  *Verification*: `ols.json` contains `coefficients`, `standard_errors`, `p_values`, and a placeholder `cv_metrics` field.

- [ ] T021b [US2] **Fit Ridge regression** – implement `code/fit_ridge.py` (α = 1.0) to produce `data/results/ridge.json` with `alpha`, `coefficients`, and raw p‑values.  
  *Verification*: `ridge.json` includes the required fields.

- [ ] T023b [US2] **Fit Random Forest** – implement `code/fit_rf.py` (n_estimators = 200, `max_depth ≤ 3` if N < 100) to produce `data/results/rf.json` with `max_depth`, `n_estimators`, and `feature_importance`.  
  *Verification*: `rf.json` contains the expected keys.

- [ ] T024 [US2] **5‑fold cross‑validation for all models** – implement `code/cross_validation.py` that loads the three model result files, performs 5‑fold CV on each, and updates their JSON files with `cv_metrics` (`r2_mean`, `r2_std`, `rmse_mean`).  
  *Verification*: Each result JSON now includes a populated `cv_metrics` object.

- [ ] T022 [US2] **Apply multiple‑comparison correction** – implement `code/significance_correction.py` to (1) load raw p‑values from `ols.json` and `ridge.json`, (2) if total tested features ≤ 5 apply Bonferroni, else apply Benjamini‑Hochberg, (3) write corrected p‑values to `data/results/corrected_p.json` and record the method used (`"bonferroni"` or `"benjamini‑hochberg"`).  
  *Verification*: `corrected_p.json` includes both raw and corrected p‑values plus `correction_method`.

- [ ] T023 [US2] **Sensitivity analysis on coefficient thresholds** – implement `code/sensitivity_analysis.py` to bootstrap OLS coefficients (200 resamples), sweep absolute coefficient magnitude thresholds `{0.01, 0.05, 0.1}`, compute significance rates and p‑value variance, and write `data/results/sensitivity_analysis.csv`.  
  *Verification*: CSV has three rows with columns `threshold`, `significance_rate`, `p_value_variance`.

- [ ] T009 [US2] **Assemble final `model_metrics.json` artifact** – implement `code/assemble_model_metrics.py` to merge OLS, Ridge, Random Forest results, VIF report, power configuration, and correction metadata into a single JSON that conforms to `contracts/analysis_output.schema.yaml`. Populate required top‑level fields (`metadata.timestamp`, `metadata.n_samples`, `metadata.model_types`, `metadata.correction_method`, `metadata.data_source`, `metadata.sc001_pass`, `metadata.vif_pass`, `metadata.power_pass`).  
  *Verification*: The assembled JSON validates against the schema and is written to `data/results/model_metrics.json`.

---

## Phase 4 – Visualization, Interpretation & Reviewer Simulation  

- [ ] T027 [US3] **Generate required visualisations** – implement `code/visualization.py` to (1) create three scatter plots (`latency vs. agency`, `smoothness vs. agency`, `lead_time vs. agency`), (2) produce a Random Forest feature‑importance bar chart, (3) produce a partial dependence plot for the top predictor, (4) save all PNGs under `data/results/figures/` with clear filenames, (5) write `data/results/visualization_report.json` containing file paths and a programmatic `clarity_score` (based on size, DPI, and label completeness).  
  *Verification*: PNG files exist (≥ 800 px wide) and `visualization_report.json` reports `clarity_score ≥ 0.8`.

- [ ] T011 [US3] **Write plain‑language interpretation summary** – implement `code/interpretation.py` to read `model_metrics.json` and `visualization_report.json`, produce `data/results/interpretation.md` that (a) describes direction and magnitude of each statistically significant motion predictor, (b) notes non‑significant findings, (c) frames all results as correlational, and (d) adds a “Limitations” paragraph referencing low outcome variance or VIF warnings if present.  
  *Verification*: The markdown contains a “Results” section with at least one sentence per predictor and a “Limitations” section.

- [ ] T012 [US3] **Simulate reviewer clarity rating** – implement `code/reviewer_simulation.py` to (1) read `clarity_score` from `visualization_report.json`, (2) generate 5 mock reviewer scores (1‑5) where higher clarity yields higher scores, (3) compute the proportion of scores ≥ 4 and require ≥ 80 % to pass, (4) write `data/results/review_summary.json` with `individual_scores`, `proportion_pass`, and boolean `pass`.  
  *Verification*: JSON exists, `proportion_pass` reflects the ≥ 80 % rule, and `pass` matches it.

- [ ] T033b [US3] **Run reviewer simulation (alias)** – a thin wrapper script `code/run_reviewer_simulation.sh` that invokes `reviewer_simulation.py` to satisfy the plan’s reference to T033b.  
  *Verification*: Executing the wrapper produces the same `review_summary.json` as T012.

---

## Phase 5 – Documentation, Quick‑Start & Reproducibility  

- [ ] T013 [US0] **Update documentation & quick‑start guide** – modify `README.md` and create `quickstart.md` that (a) list required Python version and installation steps, (b) provide a single command `bash run_pipeline.sh` that executes the full pipeline from download to `model_metrics.json`, and (c) show expected outputs (figures, JSON, interpretation). Create the `run_pipeline.sh` script that calls tasks in the exact order:  
    1. T001 → T001b → T002 → T002a → (if needed) T003 → T003a → T004 → T015 → T016 → T016b → T021 → T021b → T023b → T024 → T022 → T023 → T009 → T027 → T011 → T012 → T033b → T014.  
  *Verification*: Running `bash run_pipeline.sh` on a fresh clone produces all artifacts without manual intervention; README links to the quick‑start guide.

- [ ] T014 [US0] **Ensure full reproducibility** – (a) pin random seeds in all scripts (`numpy`, `random`, `torch` if used) and list them in `docs/reproducibility.md`, (b) confirm no script writes to platform‑managed directories (`state/`), (c) provide a pytest test suite under `tests/` covering unit and integration cases, (d) run `pytest` as the final step of `run_pipeline.sh` and verify zero failures.  
  *Verification*: Test logs show “X passed, 0 failed”; `reproducibility.md` lists seed values; a scan confirms no prohibited writes.

---

### Dependency & Execution Order Summary (explicit)

1. T001 → T001b → T002 → T002a → (if `use_synthetic`) T003 → T003a → T004 → T015 → T016 → T016b → T021 → T021b → T023b → T024 → T022 → T023 → T009 → T027 → T011 → T012 → T033b → T013 → T014  

All tasks respect the data‑flow dependencies; no task consumes an artifact before it is produced. This revised list now covers every functional requirement (FR‑001 – FR‑014), success criteria (SC‑001 – SC‑005), and constitutional obligations.  
