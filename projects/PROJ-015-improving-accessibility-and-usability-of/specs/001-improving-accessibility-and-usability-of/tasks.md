# Tasks: Improving Accessibility and Usability of Complex Computer Systems for People with Disabilities  

**Inputs**: `spec.md`, `plan.md`, existing code base, data contracts.  
**Goal**: Deliver a reproducible research pipeline that (1) collects real interaction data via a Streamlit simulator, (2) validates and cleans the data, (3) performs the mandated Repeated Measures ANOVA with Holm‑Bonferroni correction (or Friedman fallback), (4) computes observed power, (5) produces publication‑ready figures, and (6) hands off methods/results to the paper stage.  

---  

## Phase 1 – Project scaffolding & first end‑to‑end run  

- [ ] T001 **Create project layout & quick‑start guide** – Create `projects/PROJ-015-improving-accessibility-and-usability-of/` with sub‑folders `code/`, `data/`, `figures/`, `tests/`, `contracts/`; add `quickstart.md` documenting the command `python -m code.analysis.run_analysis --mode pilot`.  
- [ ] T002 **Pin dependencies** – Populate `requirements.txt` with exact versions of `streamlit`, `scipy`, `pandas`, `numpy`, `pyyaml`, `statsmodels`, `seaborn`, `pytest`. Verification: file exists and each line matches the pattern `package==x.y.z`.  
- [ ] T003 **Implement real‑data loader** – File: `code/analysis/data_loader.py`  
  - Loads all `data/raw/*.json` (or `.csv`) into a `pandas.DataFrame`.  
  - Raises `FileNotFoundError` if the directory is empty **or** if every file has `source: "simulated"` **and** `dev_mode=False`.  
  - Validates each record against `contracts/session.schema.yaml`.  
- [ ] T004 **Add data‑loader failure tests** – File: `tests/unit/test_data_loader_failure.py` asserts the two error conditions above.  
- [ ] T005 **Implement schema validator** – File: `code/analysis/validator.py` with function `validate_session(data: dict) -> bool` that uses `jsonschema` against `contracts/session.schema.yaml`.  
- [ ] T006 **Create Streamlit simulator entry point** – File: `code/app.py` (renamed from the previous `code/simulator/app.py`).  
  - Renders the counterbalanced interface (Traditional ↔ Explainable).  
  - Captures timestamps, error list, explanation‑engagement time, and SUS responses.  
  - Calls `validator.validate_session` before writing a session file to `data/raw/`.  
- [ ] T007 **Implement Latin‑Square counterbalancing** – File: `code/counterbalance.py` exposing `generate_order(num_participants: int) -> List[str]` returning a list of `"Traditional"` / `"Explainable"` orders. Integrated into `code/app.py`.  

*Checkpoint*: Running `python -m code.analysis.run_analysis --mode pilot` on a freshly collected pilot (≥5 real sessions) produces `data/processed/metrics_summary.csv` and a short console summary without errors.  

---  

## Phase 2 – Data cleaning & imputation  

- [ ] T008 **Filter incomplete sessions** – File: `code/analysis/data_cleaner.py` function `remove_incomplete(df)` drops rows where `status == "incomplete"` and logs the count.  
- [ ] T009 **SUS imputation rule** – Same module adds `impute_sus(df)` which:  
  1. Detects rows with exactly one missing SUS item, replaces the missing value with the participant’s mean SUS score, and marks the row as `imputed=True`.  
  2. Marks rows with ≥2 missing items as `status="incomplete"` (handled by `remove_incomplete`).  
- [ ] T010 **Verification of cleaning** – File: `tests/integration/test_cleaning.py` loads a synthetic but schema‑valid raw file, runs the two cleaning steps, and asserts that the resulting dataframe conforms to `contracts/metrics.schema.yaml` and contains no `status="incomplete"` rows.  

---  

## Phase 3 – Statistical analysis engine  

- [ ] T011 **Repeated Measures ANOVA implementation** – File: `code/analysis/anova_engine.py` with function `run_rm_anova(df, subject_col, within_col, dv_col)` using `statsmodels.stats.anova.AnovaRM`. Returns a dict matching `analysis_output.schema.yaml` (including `method_used="Repeated Measures ANOVA"`).  
- [ ] T012 **Normality check & Friedman fallback** – File: `code/analysis/normality.py`  
  - Runs Shapiro‑Wilk on each metric column.  
  - If any metric fails (p < 0.05), `run_friedman(df, subject_col, within_col, dv_col)` from `statsmodels.stats.nonparametric` is invoked instead of ANOVA.  
- [ ] T013 **Holm‑Bonferroni correction** – File: `code/analysis/correction.py` providing `holm_bonferroni(p_vals: List[float]) -> List[float]`. Applies to the raw p‑values of all metrics and stores `p_value_adjusted` in the output schema.  
- [ ] T014 **Observed power calculation** – File: `code/analysis/power_analysis.py` with `compute_observed_power(effect_size, n, alpha=0.05)` using `statsmodels.stats.power.FTestPower`. Generates `data/processed/observed_power.csv`.  
- [ ] T015 **End‑to‑end analysis script** – File: `code/analysis/run_analysis.py` (CLI)  
  - Calls `data_loader.load_real_data`, `data_cleaner.remove_incomplete`, `data_cleaner.impute_sus`, `normality.check_normality`, selects ANOVA or Friedman, applies `correction.holm_bonferroni`, computes power, writes `data/processed/analysis_results.json` (conforms to `analysis_output.schema.yaml`) and a concise human‑readable `report_summary.txt`.  
  - Includes a `--mode pilot` flag that bypasses the N ≥ 30 recruitment gate (see Phase 4).  

---  

## Phase 4 – Pilot and recruitment gating  

- [ ] T016 **Pilot eligibility check** – File: `code/analysis/pilot_gate.py` with `check_pilot(df, min_n=5)` raising `ValueError` if fewer than 5 complete human sessions are present. Integrated into `run_analysis.py` when `--mode pilot` is used.  
- [ ] T017 **Full‑study recruitment gate** – File: `code/analysis/full_gate.py` with `check_full_recruitment(pilot_report_path)` that reads `data/pilot_report.md`; if the pilot did not succeed, raises `RuntimeError`. `run_analysis.py` calls this when `--mode full`.  

---  

## Phase 5 – Visualization & results hand‑off  

- [ ] T018 **Figure generation** – File: `code/analysis/visualizer.py` providing four functions (`plot_completion_time`, `plot_error_count`, `plot_sus_score`, `plot_explanation_engagement`) that read `metrics_summary.csv` and save PNGs (`figures/completion_time.png`, etc.) using `seaborn.boxplot` with 95 % CI error bars (300 dpi).  
- [ ] T019 **Create methods & results markdown** – File: `paper/methods_results.md` (generated by `run_analysis.py`) that programmatically inserts tables and figure references directly from the JSON/CSV outputs, ensuring no hand‑typed numbers.  
- [ ] T020 **Checksum verification for hand‑off** – `run_analysis.py` computes SHA‑256 hashes of `metrics_summary.csv`, each figure PNG, and the JSON results; stores them in `state/output_hashes.yaml`. A downstream verification script will reject mismatched hashes, guaranteeing reproducibility.  

---  

## Phase 6 – Test suite for scientific integrity  

- [ ] T021 **Unit tests for ANOVA/Friedman engines** – `tests/unit/test_anova_friedman.py` supplies a tiny synthetic but *real* dataset (generated with a fixed seed) that satisfies the schema and checks that the returned dict conforms to `analysis_output.schema.yaml` and that Holm‑Bonferroni produces monotonic adjusted p‑values.  
- [ ] T022 **Integration test of full pipeline (pilot)** – `tests/integration/test_full_pipeline_pilot.py` runs `python -m code.analysis.run_analysis --mode pilot` on a minimal real‑data fixture (5 human sessions) and asserts that:  
  1. `analysis_results.json` exists and validates against `analysis_output.schema.yaml`.  
  2. All four figure files exist and are non‑empty.  
  3. `report_summary.txt` contains the phrase “Holm‑Bonferroni adjusted p‑values”.  

---  

## Phase 7 – Documentation & cleanup  

- [ ] T023 **Update README with reproducibility instructions** – Add a “Reproduce the study” section that points to `quickstart.md`, explains the `--mode pilot` vs `--mode full` flags, and lists the exact random seeds used for any deterministic steps.  
- [ ] T024 **Remove obsolete duplicated tasks** – All previous `T049` duplicates have been consolidated into the single tasks above (T015, T019, T020). No task identifier is reused.  

---  

### Dependency mapping (summary)

| Spec/Requirement | Task(s) fulfilling it |
|------------------|-----------------------|
| FR‑001 (data collection) | T006, T007 |
| FR‑002 (RM‑ANOVA + Holm) | T011, T013 |
| FR‑003 (interface rendering) | T006 |
| FR‑004 (Latin Square) | T007 |
| FR‑005 (validation & cleaning) | T005, T008, T009 |
| FR‑006 (power analysis) | T014, T017 |
| FR‑007 (real‑data Streamlit) | T006 |
| NFR‑001 (reproducibility) | T023, T020 |
| NFR‑002 (no synthetic data) | T003, T004, T016, T017 |

---  

**All tasks are unchecked except the scaffolding tasks that have already been completed (marked `[X]`).** The remaining tasks constitute the smallest complete, verifiable study that satisfies the specification while respecting CPU‑first execution (all heavy computation is limited to ≤30 participants; any optional GPU‑accelerated steps are omitted).
