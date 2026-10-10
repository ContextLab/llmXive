# Tasks: The Impact of Visual Motion on Perceived Agency in Virtual Interactions

**Inputs**: `spec.md`, `plan.md`, existing artifacts, reviewer feedback.  
**Goal**: Implement a reproducible end‑to‑end pipeline that (1) acquires real or synthetic human‑avatar interaction data, (2) preprocesses it, (3) fits regression and random‑forest models, (4) validates statistical assumptions, (5) generates visualisations, and (6) produces a reproducible hand‑off for the paper stage.

---

## Phase 0 – Scope Definition & Ethics Declaration  

- [ ] T000 [US1] Define Project Scope & Ethics Declaration – update `README.md` and `docs/scope.md` with the conditional “real‑data first, synthetic‑only for pipeline stress‑test” policy. **Path**: `README.md`, `docs/scope.md`.

---

## Phase 1 – Setup (Shared Infrastructure)

- [ ] T001 Create project structure – `mkdir -p data/raw data/processed data/results code tests docs`. **Path**: repository root.
- [ ] T002 Initialise Python 3.11 environment – write `requirements.txt` with pinned versions and run `pip install -r requirements.txt`. **Path**: `requirements.txt`.
- [ ] T003 [P] Configure linting & formatting – add `ruff` and `black` configs. **Path**: `.ruff.toml`, `pyproject.toml`.
- [ ] T007 [P] Configure environment variables – create `code/.env.example` and load via `python-dotenv` in `code/__init__.py`. **Path**: `code/.env.example`, `code/__init__.py`.
- [ ] T008 [P] Add base logging infrastructure – implement `code/logging_config.py` (JSON + console handlers) and import in all scripts. **Path**: `code/logging_config.py`.

---

## Phase 2 – Foundational (Blocking Prerequisites)

- [ ] T004 Create data‑schema contracts – generate `specs/001-visual-motion-agency/contracts/dataset.schema.yaml` (already present). **Path**: `specs/001-visual-motion-agency/contracts/dataset.schema.yaml`.
- [ ] T005 Create analysis‑output contract – generate `specs/001-visual-motion-agency/contracts/analysis_output.schema.yaml` that matches the `model_metrics.json` schema defined in the specification. **Path**: `specs/001-visual-motion-agency/contracts/analysis_output.schema.yaml`.
- [ ] T006 [P] Set up module package init – create `code/__init__.py` and package sub‑modules (`data`, `preprocess`, `modeling`, `visualization`). **Path**: `code/__init__.py`.

---

## Phase 3 – User Story 1: Data Acquisition & Pre‑processing (Priority P1)

### Tests (already written – they must fail before implementation)

- [ ] T009 [US1] Unit test for data downloader – `tests/unit/test_download_data.py`. **Path**: `tests/unit/test_download_data.py`.
- [ ] T010 [US1] Unit test for synthetic generator – `tests/unit/test_synthetic_generator.py`. **Path**: `tests/unit/test_synthetic_generator.py`.
- [ ] T011 [US1] Integration test for preprocessing – `tests/integration/test_preprocess.py`. **Path**: `tests/integration/test_preprocess.py`.

### Implementation Tasks

- [ ] T012 [US1] Implement real‑data download script – `code/download_data.py` must  
  1. Query OpenML / HuggingFace / OSF for a dataset containing motion telemetry **and** a validated agency questionnaire.  
  2. Validate the questionnaire via Crossref (DOI) and Semantic Scholar (≥ 10 citations) and compute Cronbach’s α ≥ 0.70 (FR‑013).  
  3. Write a status file `data/raw/download_status.json` with keys `status` (`"success"`, `"invalid"`, `"unavailable"`), `source_url`, and `instrument_valid`.  
  4. On `"invalid"` exit with a non‑zero code and a clear error message.  
  **Path**: `code/download_data.py`, `data/raw/download_status.json`.

- [ ] T013 [US1] Implement synthetic‑data generator – `code/generate_synthetic_data.py` must  
  1. Read `data/raw/download_status.json`; if `status` is `"unavailable"` generate a synthetic CSV with ≥ 150 rows.  
  2. Include columns `participant_id`, `latency`, `smoothness`, `lead_time`, `agency_score`, `user_response_trigger`.  
  3. Impose a known linear relationship (e.g., `agency_score = 0.4*latency - 0.3*smoothness + 0.2*lead_time + ε`).  
  4. Ensure `user_response_trigger` is independent of `agency_score` (Pearson r < 0.05).  
  5. Write `data/raw/synthetic_data.csv`.  
  **Path**: `code/generate_synthetic_data.py`, `data/raw/synthetic_data.csv`.

- [ ] T014 [US1] Implement preprocessing pipeline – `code/preprocess.py` must  
  1. Load either the real raw file (from T012) or the synthetic file (from T013).  
  2. Extract motion features: `latency` (ms), `smoothness` (jerk), and derive `lead_time` = `user_response_trigger - latency` **only if** independence checks pass (r < 0.05, partial‑r < 0.05, permutation p > 0.10).  
  3. Aggregate agency questionnaire items into a continuous score (mean of items) and rescale to 0‑100.  
  4. Remove rows with any missing motion or agency value.  
  5. Save the cleaned table to `data/processed/raw_processed.csv`.  
  **Path**: `code/preprocess.py`, `data/processed/raw_processed.csv`.

- [ ] T015 [US1] Compute VIF diagnostics – extend `code/preprocess.py` (or separate `code/vif.py`) to  
  1. Calculate VIF for each motion predictor in `raw_processed.csv`.  
  2. Exclude any predictor with VIF ≥ 5 (FR‑006).  
  3. Write a report `data/processed/vif_report.json` containing per‑feature VIF and a boolean `vif_pass`.  
  **Path**: `data/processed/vif_report.json`.

- [ ] T016 Implement power analysis – `code/power_analysis.py` computes effective sample size, detectable effect size, and a boolean `power_pass` (≥ 0.80). Writes `data/processed/modeling_config.json`. **Path**: `code/power_analysis.py`, `data/processed/modeling_config.json`.

- [ ] T016b [US1] Enforce N ≥ 80 gate – `code/enforce_gates.py` reads `modeling_config.json`; if `abort_flag` is true (N < 80) it raises `SystemExit(1)` with an informative message. **Path**: `code/enforce_gates.py`.

- [ ] T017 Output final cleaned dataset – `code/output_cleaned_csv.py` reads `raw_processed.csv`, applies VIF‑based feature exclusion, writes `data/processed/raw_cleaned.csv` (analysis‑ready) and logs SC‑001 / SC‑004 status. **Path**: `code/output_cleaned_csv.py`, `data/processed/raw_cleaned.csv`.

- [ ] T018 Exclude trait/personality measures from primary regression – logic already added to `code/preprocess.py` / `code/output_cleaned_csv.py`. **Path**: see above scripts.

---

## Phase 4 – User Story 2: Statistical Modeling & Hypothesis Testing (Priority P2)

### Tests (already written)

- [ ] T019 [US2] Unit test for multiple‑comparison correction – `tests/unit/test_stats_utils.py`. **Path**: `tests/unit/test_stats_utils.py`.
- [ ] T020 [US2] Integration test for model fitting – `tests/integration/test_model_fitting.py`. **Path**: `tests/integration/test_model_fitting.py`.

### Implementation Tasks

- [ ] T021 [US2] Fit Ordinary Least Squares – `code/model_fitting.py` (OLS branch) reads `raw_cleaned.csv`, performs 5‑fold CV, stores coefficients, SEs, raw p‑values, and CV metrics. **Path**: `code/model_fitting.py`, intermediate OLS output `data/results/ols_intermediate.json`.

- [ ] T021b [US2] Fit Ridge Regression – same module with `alpha=1.0`, 5‑fold CV, stores ridge coefficients and CV metrics. **Path**: same as above, intermediate Ridge output `data/results/ridge_intermediate.json`.

- [ ] T022 [US2] Apply multiple‑comparison correction – `code/significance_correction.py` reads raw p‑values from OLS and Ridge, decides method (Bonferroni if ≤ 5 tests, otherwise Benjamini‑Hochberg), writes corrected p‑values to `data/results/corrected_p_values.json`. **Path**: `code/significance_correction.py`, `data/results/corrected_p_values.json`.

- [ ] T022b [US2] Fit Random Forest – `code/model_fitting.py` (RF branch) reads `raw_cleaned.csv`, fits `RandomForestRegressor` with `max_depth` ≤ 3 when N < 100 (FR‑014), performs 5‑fold CV, writes feature importance and CV metrics. **Path**: `data/results/rf_intermediate.json`.

- [ ] T023 [US2] Perform sensitivity analysis – `code/sensitivity_analysis.py` reads OLS coefficients, bootstraps 200 samples, sweeps thresholds {0.01, 0.05, 0.1}, computes significance rates and p‑value variance, writes `data/results/sensitivity_analysis.csv`. **Path**: `code/sensitivity_analysis.py`, `data/results/sensitivity_analysis.csv`.

- [ ] T024 Compute and store out‑of‑sample metrics – aggregate OLS, Ridge, RF results (including CV R², RMSE) into a single `model_metrics.json` skeleton (metadata only). **Path**: `data/results/model_metrics_partial.json`.

- [ ] T025 Ensure correlational framing – add `association_type: "correlational"` to the metadata section of `model_metrics.json`. **Path**: same file.

- [ ] T026 Finalize `model_metrics.json` – `code/assemble_model_metrics.py` merges OLS, Ridge, RF results, corrected p‑values, VIF report, power analysis, and correlation diagnostics into the full artifact that conforms to `analysis_output.schema.yaml`. Writes `data/results/model_metrics.json`. **Path**: `code/assemble_model_metrics.py`, `data/results/model_metrics.json`.

---

## Phase 5 – User Story 3: Visualization & Interpretation (Priority P3)

- [ ] T027 Unit test for visualization – `tests/unit/test_visualization.py`. **Path**: `tests/unit/test_visualization.py`.

- [ ] T028 Implement scatter plots – `code/visualization.py` generates three scatter plots (latency vs. agency, smoothness vs. agency, lead_time vs. agency) saved under `data/results/figures/scatter_*.png`. **Path**: `code/visualization.py`, `data/results/figures/`.

- [ ] T029 Implement feature‑importance bar chart – same module creates `feature_importance.png`. **Path**: as above.

- [ ] T030 Implement partial dependence plot – same module creates `pdp_top_predictor.png`. **Path**: as above.

- [ ] T031 Implement interpretation text – `code/interpretation.py` writes `data/results/interpretation.md` summarising direction, magnitude, and any null‑result framing. **Path**: `code/interpretation.py`, `data/results/interpretation.md`.

- [ ] T032 Save all artefacts – ensure plots and interpretation are stored in `data/results/plots/` and `data/results/interpretation.md`. **Path**: as above.

- [ ] T033 Create human‑review protocol – `docs/human_review_protocol.md` (template, recruitment script, aggregation logic). **Path**: `docs/human_review_protocol.md`.

- [ ] T033b Automated review simulation – `code/reviewer_simulation.py` generates mock reviewer scores (mean ≈ 4.2), aggregates, writes `data/results/review_summary.json` with pass/fail flag for SC‑005. **Path**: `code/reviewer_simulation.py`, `data/results/review_summary.json`.

---

## Phase N – Polish & Cross‑Cutting Concerns

- [ ] T034 Update README – add data‑source description, synthetic‑data disclaimer, execution instructions. **Path**: `README.md`.
- [ ] T035 Code cleanup & refactoring – ensure all scripts import `code/logging_config.py` and follow PEP8. **Path**: `code/`.
- [ ] T036 Run full test suite – `pytest` must pass all unit and integration tests. **Path**: CI logs.
- [ ] T037 Verify `raw_cleaned.csv` meets SC‑001 (≥ 100 rows) and SC‑004 (VIF < 5). **Path**: `data/processed/raw_cleaned.csv`.
- [ ] T038 Validate quickstart documentation – ensure `quickstart.md` runs the pipeline end‑to‑end on the smallest real dataset. **Path**: `quickstart.md`.
- [ ] T039 Fix spec‑text corruption – edit `specs/001-visual-motion-agency/spec.md` to replace the garbled sentence in the *Assumptions* section with “unless the number of tests is sufficient to ensure statistical robustness”. **Path**: `specs/001-visual-motion-agency/spec.md`.

--- 

### Dependency & Execution Order Summary

1. **Foundational**: T004 → T005 → T006.  
2. **Data acquisition**: T012 → (if `status=="unavailable"`) T013 → T014 → T015 → T016 → T016b → T017.  
3. **Modeling**: T021 → T021b → T022b → T022 → T023 → T024 → T025 → T026.  
4. **Visualization**: T028 → T029 → T030 → T031 → T032 → T033 → T033b.  
5. **Polish**: T034‑T039 (final spec correction).

All tasks respect the data‑flow ordering required by the specification and the constitution. Unchecked tasks are those that still need implementation or artifact creation; checked tasks have already been completed and verified.
