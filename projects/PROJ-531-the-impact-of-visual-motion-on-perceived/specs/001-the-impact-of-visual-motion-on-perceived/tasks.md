# Tasks: The Impact of Visual Motion on Perceived Agency in Virtual Interactions

**Inputs**: `spec.md`, `plan.md`, existing artifacts, reviewer feedback.  
**Goal**: Implement a reproducible end‑to‑end research pipeline that (1) acquires real or synthetic human‑avatar interaction data, (2) preprocesses and validates it, (3) fits regression and tree‑based models, (4) performs statistical corrections and sensitivity checks, (5) creates visualisations, (6) produces a complete `model_metrics.json` artifact, and (7) documents a hand‑off for the paper stage.

---

## Phase 0 – Scope Definition & Ethics Declaration  

- [ ] T001 [US0] Define project scope & ethics – update `README.md` and create `docs/scope.md` describing the “real‑data first, synthetic‑only for pipeline stress‑test” policy and IRB‑exemption statement.  
  *Verification*: Both files exist, contain the required sections, and are referenced from `quickstart.md`.

---

## Phase 1 – Data Acquisition  

- [ ] T002 [US1] Implement real‑data download script – `code/download_data.py` must  
  1. Query OpenML / HuggingFace / OSF for a dataset that contains motion telemetry **and** a validated agency questionnaire.  
  2. Validate the questionnaire by (a) checking the DOI via Crossref, (b) confirming ≥ 10 citations via Semantic Scholar, and (c) computing Cronbach’s α ≥ 0.70 (FR‑013).  
  3. Save the raw file to `data/raw/real_data.parquet`.  
  4. Write a status file `data/raw/download_status.json` with keys `status` (`"success"` | `"invalid"` | `"unavailable"`), `source_url`, `instrument_valid`, and `use_synthetic` (boolean).  
  5. Exit with a non‑zero code and a clear error message if `status == "invalid"`.  
  *Verification*: Running the script produces both `real_data.parquet` (or reports failure) and a correctly‑structured `download_status.json`.

- [ ] T003 [US1] Implement synthetic‑data generator – `code/generate_synthetic_data.py` must  
  1. Read `data/raw/download_status.json`; if `status == "unavailable"` or `instrument_valid == false`, generate a synthetic CSV with **≥ 150** rows.  
  2. Columns: `participant_id` (UUID), `latency` (ms), `smoothness` (dimensionless jerk), `lead_time` (ms), `agency_score` (0‑100), `user_response_trigger` (ms).  
  3. Impose a known linear relationship, e.g. `agency_score = 0.4*latency - 0.3*smoothness + 0.2*lead_time + ε`.  
  4. Ensure `user_response_trigger` is independent of `agency_score` (Pearson r < 0.05, permutation p > 0.10).  
  5. Write the file to `data/raw/synthetic_data.csv` and update `download_status.json` with `"use_synthetic": true`.  
  *Verification*: The CSV exists, contains the required columns, meets the row count, and a post‑hoc script confirms the independence of `user_response_trigger`.

---

## Phase 2 – Pre‑processing, Validation & Power Analysis  

- [ ] T004 [US1] Implement preprocessing pipeline – `code/preprocess.py` must  
  1. Load either `data/raw/real_data.parquet` or `data/raw/synthetic_data.csv` based on `download_status.json`.  
  2. Extract motion features: `latency`, `smoothness`; derive `lead_time = user_response_trigger - latency` **only if** three independence checks pass (Pearson r < 0.05, partial‑r < 0.05, permutation p > 0.10).  
  3. Aggregate agency questionnaire items into a continuous score (mean of items) and rescale to 0‑100.  
  4. Remove any row with missing motion or agency values.  
  5. Compute Variance Inflation Factor (VIF) for each motion predictor; exclude any predictor with VIF ≥ 5 and set `vif_pass` accordingly.  
  6. Write the cleaned, analysis‑ready table to `data/processed/analysis_ready.csv` (conforms to `dataset.schema.yaml`).  
  7. Write VIF diagnostics to `data/processed/vif_report.json` (includes per‑feature VIF and boolean `vif_pass`).  
  *Verification*: The CSV contains the required columns, ≥ 100 complete rows, and `vif_report.json` is valid JSON with `vif_pass` true/false.

- [ ] T005 [US1] Power analysis & gating – `code/power_analysis.py` must  
  1. Read `data/processed/analysis_ready.csv`.  
  2. Perform an analytical power calculation (using `statsmodels.stats.power.FTestPower`) for a multiple linear regression with up to three predictors, targeting α = 0.05 and power ≥ 0.80.  
  3. Output `data/processed/modeling_config.json` containing `effective_n`, `detectable_f2`, `power`, `sc001_pass` (≥ 100 rows), `power_pass` (≥ 0.80), and an `abort_flag` that is true when `effective_n < 80`.  
  4. A separate enforcement step (`code/enforce_gates.py`) reads this file and aborts the pipeline with a clear message if `abort_flag` is true.  
  *Verification*: The JSON file exists, fields are correctly typed, and running the enforcement script exits with status 1 when the gate condition is violated.

---

## Phase 3 – Statistical Modeling & Hypothesis Testing  

- [ ] T006 [US2] Fit regression and tree models – `code/model_fitting.py` must  
  1. Read `data/processed/analysis_ready.csv`.  
  2. Fit (a) Ordinary Least Squares (OLS) regression, (b) Ridge regression (`alpha=1.0`), and (c) Random Forest (`n_estimators=200`, `max_depth ≤ 3` if N < 100, otherwise unrestricted).  
  3. Perform 5‑fold cross‑validation for each model, recording mean R², std R², and mean RMSE.  
  4. Write intermediate results to `data/results/ols.json`, `ridge.json`, and `rf.json`.  
  *Verification*: Each JSON contains coefficients (or feature importances), CV metrics, and matches the schema sections for the respective model types.

- [ ] T007 [US2] Multiple‑comparison correction – `code/significance_correction.py` must  
  1. Load raw p‑values from OLS and Ridge results.  
  2. If the total number of tested features ≤ 5, apply Bonferroni correction; otherwise apply Benjamini‑Hochberg FDR control.  
  3. Write corrected p‑values to `data/results/corrected_p.json` and record the method used (`"bonferroni"` or `"benjamini‑hochberg"`).  
  *Verification*: The JSON includes both raw and corrected p‑values and a top‑level key `correction_method`.

- [ ] T008 [US2] Sensitivity analysis – `code/sensitivity_analysis.py` must  
  1. Bootstrap the OLS coefficient estimates (200 resamples).  
  2. Sweep absolute coefficient magnitude thresholds `{0.01, 0.05, 0.1}` and compute, for each threshold, the proportion of bootstrap samples with a p‑value < 0.05.  
  3. Compute variance of p‑values across bootstraps.  
  4. Write results to `data/results/sensitivity_analysis.csv` with columns `threshold`, `significance_rate`, `p_value_variance`.  
  *Verification*: The CSV has three rows (one per threshold) and numeric values in the expected ranges.

- [ ] T009 [US2] Assemble final metrics artifact – `code/assemble_model_metrics.py` must  
  1. Merge OLS, Ridge, Random Forest results, VIF report, power configuration, and correction metadata.  
  2. Add a top‑level `metadata.association_type = "correlational"` (FR‑008).  
  3. Validate the merged object against `specs/001-visual-motion-agency/contracts/analysis_output.schema.yaml`.  
  4. Write the compliant artifact to `data/results/model_metrics.json`.  
  *Verification*: The JSON validates against the schema (all required fields present, correct types) and `metadata.correction_method` matches the method used in T007.

---

## Phase 4 – Visualization, Interpretation & Reviewer Simulation  

- [ ] T010 [US3] Generate visualisations – `code/visualization.py` must  
  1. Create three scatter plots (`latency vs. agency`, `smoothness vs. agency`, `lead_time vs. agency`).  
  2. Produce a bar chart of feature importance (from the Random Forest).  
  3. Produce a partial dependence plot for the top‑ranked predictor (from the RF model).  
  4. Save all PNGs under `data/results/figures/` with clear filenames.  
  5. Write a summary JSON `data/results/visualization_report.json` containing the file paths and a programmatic “clarity score” (based on figure size, DPI, and label completeness).  
  *Verification*: The PNG files exist, are at least 800 px wide, and the JSON reports a `clarity_score ≥ 0.8`.

- [ ] T011 [US3] Write interpretation summary – `code/interpretation.py` must  
  1. Read `model_metrics.json` and the visualization report.  
  2. Produce a plain‑language markdown file `data/results/interpretation.md` that (a) describes the direction and magnitude of each statistically significant motion predictor, (b) notes any non‑significant findings, and (c) explicitly frames the results as correlational.  
  *Verification*: The markdown file contains a “Results” section with at least one sentence per predictor and a “Limitations” paragraph referencing low outcome variance or collinearity warnings if present.

- [ ] T012 [US3] Simulate reviewer clarity rating – `code/reviewer_simulation.py` must  
  1. Randomly generate 5 mock reviewer scores (1‑5) based on the `clarity_score` from T010 (higher clarity → higher reviewer scores).  
  2. Compute the mean rating and write `data/results/review_summary.json` containing the individual scores, the mean, and a boolean `pass` (true if mean ≥ 4.0).  
  3. If `pass` is false, the pipeline should raise a warning but continue.  
  *Verification*: The JSON file exists, `mean_score` is a float, and `pass` reflects the threshold condition.

---

## Phase 5 – Documentation, Quick‑Start & Project Polish  

- [ ] T013 [US0] Update documentation & quick‑start – modify `README.md` and create `quickstart.md` that (a) list required Python version and how to install dependencies, (b) provide a single command (`bash run_pipeline.sh`) that executes the full pipeline from download to `model_metrics.json`, and (c) show expected outputs (figures, JSON, interpretation).  
  *Verification*: Running the command on a fresh clone produces all artifacts without manual intervention; the README links to the quick‑start guide.

- [ ] T014 [US0] Clean up and ensure reproducibility –  
  1. Pin random seeds in all scripts (`numpy`, `random`, `torch` if used).  
  2. Verify that no script writes to `state/` or other platform‑managed directories.  
  3. Run the full test suite (`pytest`) and confirm zero failures.  
  *Verification*: Test logs show “X passed, 0 failed”; a short note in `README.md` records the seed values used.

---

### Dependency & Execution Order Summary  

1. **Scope** → T001  
2. **Data download** → T002 → (if unavailable/invalid) → T003  
3. **Pre‑process & VIF** → T004  
4. **Power & gating** → T005 (enforced by `code/enforce_gates.py` before proceeding)  
5. **Model fitting** → T006  
6. **Correction** → T007  
7. **Sensitivity** → T008  
8. **Assemble final metrics** → T009  
9. **Visualisations** → T010  
10. **Interpretation** → T011  
11. **Reviewer simulation** → T012  
12. **Docs & reproducibility** → T013, T014  

All tasks respect the data‑flow dependencies; no task that consumes an artifact runs before the artifact is produced. This list contains 14 substantive, checklist‑style tasks that together satisfy every functional and success‑criteria requirement of the specification.
