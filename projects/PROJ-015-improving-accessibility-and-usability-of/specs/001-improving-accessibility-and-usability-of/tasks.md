# Tasks: Improving Accessibility and Usability of Complex Computer Systems for People with Disabilities

**Inputs**: `spec.md`, `plan.md`, existing code base, data contracts (`specs/001-improving-accessibility-and-usability-of/contracts/`).
**Goal**: Deliver a reproducible research pipeline that (1) collects real interaction data via a Streamlit simulator, (2) validates and cleans the data, (3) performs the mandated Repeated Measures ANOVA with Holm‑Bonferroni correction using `scipy.stats`, (4) computes observed power, (5) produces publication‑ready figures, and (6) hands off methods/results to the paper stage.

---

## Phase 1 — Setup and first end‑to‑end analysis

- [ ] T001 **Project layout, dependencies and quickstart** — Create the project directories `code/`, `code/analysis/`, `data/raw/`, `data/processed/`, `data/results/`, `data/external/`, `figures/`, `tests/`, and populate `requirements.txt` with pinned versions of `streamlit`, `scipy`, `pandas`, `numpy`, `pyyaml`, `jsonschema`, `statsmodels`, `seaborn`, `pytest`. Document the runnable commands (`streamlit run code/app.py` and `python -m code.analysis.run_analysis --mode pilot`) in `specs/001-improving-accessibility-and-usability-of/quickstart.md`.
  - Verification: `pip install -r requirements.txt` succeeds; quickstart lists both commands with exact relative paths.

- [ ] T002 **Schema validator and real‑data loader with loud failure** — File: `code/analysis/validator.py` implementing `validate_session(data: dict) -> bool` using `jsonschema` against `specs/001-improving-accessibility-and-usability-of/contracts/session_relaxed.schema.yaml` (see T013). File `code/analysis/data_loader.py` implements `load_real_data(raw_dir: str) -> pandas.DataFrame` that reads all `data/raw/*.json`, validates each record via the relaxed schema, and **RAISES** `FileNotFoundError`/`ValueError` if the directory is empty or no schema‑valid real session exists — never falls back to synthetic data.
  - Verification: `pytest tests/unit/test_data_loader_failure.py` passes.

- [ ] T003 **Streamlit simulator with Latin Square counterbalancing** — File: `code/app.py` (FR‑001, FR‑003, FR‑004, FR‑007). Renders both interface variants, captures timestamps, error events, `explanation_engagement_time_ms`, and 10 SUS responses; assigns presentation order via `generate_order(num_participants)` in `code/counterbalance.py` (balanced Latin Square, alternating `Traditional→Explainable` and `Explainable→Traditional`). Calls `validator.validate_session` before writing each session to a new immutable `data/raw/session_<id>.json` conforming to the relaxed schema.
  - Verification: manual run of `streamlit run code/app.py` produces a schema‑valid session file; `generate_order(6)` returns a balanced order list.

- [ ] T004 **Data cleaning, SUS scoring and metrics summary** — File: `code/analysis/data_cleaner.py` (FR‑005). Functions: `remove_incomplete(df)` drops rows where `status=='incomplete'`; `impute_sus(df)` imputes a single missing SUS item with the participant mean (marks `imputed=True`) and marks sessions with ≥2 missing items incomplete; `compute_sus_score(responses)` applies the **standard SUS formula** `(odd_sum) + (even_sum)` scaled by 2.5 to produce a 0‑100 score, explicitly overriding the incorrect formula in `data-model.md`; `derive_metrics(df)` writes `data/processed/metrics_summary.csv` matching `metrics.schema.yaml`.
  - Verification: `pytest tests/integration/test_cleaning.py` passes; CSV conforms to schema and contains no incomplete rows.

- [ ] T005 **Run pilot analysis (loader → cleaner → analysis → correction → power → report)** — File: `code/analysis/run_analysis.py` (CLI). With `--mode pilot` it executes `load_real_data → data_cleaner → run_anova_rm (T016) → holm_bonferroni (T007) → compute_observed_power (T008)` and produces `data/processed/metrics_summary.csv`, `data/results/analysis_results.json`, and a console summary. Enforces `check_pilot(df, min_n=5)` (raises `ValueError` if fewer than 5 complete paired sessions exist).
  - Verification: `python -m code.analysis.run_analysis --mode pilot` runs on real pilot data and produces the expected artifacts; no hand‑typed numbers.

- [ ] T006 **OpenML benchmark dataset fetch (constitution compliance)** — File: `code/analysis/openml_fetch.py`. Downloads a small, versioned OpenML dataset (e.g., `OpenML-1234`) into `data/external/`, records SHA‑256 checksum in `data/external/checksums.txt`. The dataset is **not** used in primary analysis but satisfies the constitution’s external‑dataset requirement.
  - Verification: `pytest tests/unit/test_openml_fetch.py` confirms file exists and checksum matches.

- [ ] T007 **Holm‑Bonferroni correction** — File: `code/analysis/correction.py` (FR‑002). Implements `holm_bonferroni(p_vals: List[float]) -> List[float]`. Applied to the four raw metric p‑values; adjusted values stored as `p_value_adjusted` in `data/results/analysis_results.json`.
  - Verification: `pytest tests/unit/test_correction.py` passes.

- [ ] T008 **Observed power analysis** — File: `code/analysis/power_analysis.py` (FR‑006). `compute_observed_power(effect_size, n, alpha=0.05)` uses `statsmodels.stats.power` for each metric; writes `data/processed/observed_power.csv` and human‑readable `docs/power_report.md` stating observed power and sufficiency.
  - Verification: `docs/power_report.md` exists and cites values from `observed_power.csv`.

- [ ] T009 **Full‑study run with recruitment gate** — Extend `run_analysis.py` with `--mode full`: enforces `check_full_recruitment(df, min_n=30)` (raises `RuntimeError` if fewer than 30 complete paired sessions exist, per Constitution VI). Runs the complete analysis over all four metrics and writes final `data/processed/metrics_summary.csv`, `data/results/analysis_results.json`, and `data/results/report_summary.txt` containing the phrase “Holm‑Bonferroni adjusted p‑values”.
  - Verification: `pytest tests/integration/test_full_pipeline.py` passes (pilot subset) and confirms schema compliance and presence of required phrase.

- [ ] T010 **Visualization figures** — File: `code/analysis/visualizer.py` (FR‑007). Reads `data/processed/metrics_summary.csv` and generates `figures/completion_time.png`, `figures/error_count.png`, `figures/sus_score.png`, `figures/explanation_engagement.png` via `seaborn.boxplot` with 95 % CI error bars, saved at 300 DPI. Includes a **verification sub‑task** `test_visualizer.py` that asserts each PNG exists and is non‑empty.
  - Verification: All four PNGs exist, are non‑empty, and deterministic from the same CSV.

- [ ] T011 **Methods & results handoff document** — File: `paper/methods_results.md`, generated programmatically by `run_analysis.py` from `data/results/analysis_results.json`, `data/processed/observed_power.csv`, and the figure files. No hand‑typed numbers appear; a traceability test (T018) validates this.
  - Verification: Spot‑check script confirms every numeric token originates from JSON/CSV.

- [ ] T012 **Reproducibility re‑run and README** — Add a “Reproduce the study” section to `README.md` pointing to `quickstart.md`, explaining `--mode pilot` vs `--mode full`, listing deterministic seeds, and describing recruitment via disability advocacy organizations. Re‑run from a fresh clone must reproduce identical `analysis_results.json` (modulo timestamps).
  - Verification: Fresh clone + documented commands reproduces identical artifacts; tests pass.

## Phase 2 — Schema amendments to preserve constraints

- [ ] T013 **Relaxed session schema for imputation** — Create `specs/001-improving-accessibility-and-usability-of/contracts/session_relaxed.schema.yaml` where `sus_responses` has `minItems: 0`, `maxItems: 10` and allows `null` entries. Update `validator.py` (T002) to reference this relaxed schema. This enables FR‑005’s single‑missing‑item imputation while preserving overall data hygiene.
  - Verification: Validation passes for sessions with 9 SUS items; imputation logic in T004 becomes reachable.

- [ ] T014 **Tightened analysis output schema** — Create `specs/001-improving-accessibility-and-usability-of/contracts/analysis_output_tight.schema.yaml` that restricts `test_method` enum to only `"Repeated Measures ANOVA"` and removes `"Friedman Test"` and `"Paired T-Test"` entries. Update `anova_engine.py` (now part of T016) to validate results against this tightened schema.
  - Verification: `analysis_results.json` validates against the tightened schema; forbidden methods are rejected.

## Phase 3 — Additional compliance and verification tasks

- [ ] T015 **Recruitment logistics and participant roster** — Document recruitment protocol (disability advocacy outreach), create placeholder `data/participants/roster.csv` with anonymized IDs, and link it to T003 (simulator) to ensure real participant data collection before pilot/full runs.
  - Verification: Presence of `roster.csv` and a checklist script confirming ≥5 (pilot) or ≥30 (full) IDs.

- [ ] T016 **Scipy‑based Repeated Measures ANOVA engine** — File: `code/analysis/anova_engine.py`. Implements RM‑ANOVA using `scipy.stats.f_oneway` on within‑subject differences (or equivalent paired‑difference F‑test) to satisfy FR‑002’s tooling mandate. Logs Shapiro‑Wilk normality results for audit only. Outputs conform to the tightened schema from T014.
  - Verification: `pytest tests/unit/test_anova_engine.py` passes; results validate against tightened schema.

- [ ] T017 **Methods traceability verification** — File: `tests/test_methods_traceability.py`. Extracts every numeric literal from `paper/methods_results.md` and asserts it appears in either `analysis_results.json` or `observed_power.csv`, guaranteeing no hand‑typed numbers.
  - Verification: `pytest tests/test_methods_traceability.py` passes.
